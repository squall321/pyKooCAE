"""K-File Decomposer: 단일 .k 파일을 그룹 단위로 분해하여 다중 파일 출력.

출력 구조:
    output_dir/
    ├── master.k                    (모든 *INCLUDE 모음)
    ├── controls.k                  (모델 독립 설정: CONTROL/DATABASE)
    ├── globals.k                   (모델 의존 전역: SET/DEFINE/PARAMETER/RIGIDWALL)
    ├── materials.k                 (MAT/EOS/HG 공통)
    ├── sections.k                  (SECTION + 미인터프리트 SECTION_* raw)
    ├── inter_group_contacts.k      (그룹 간 contact)
    └── groups/
        ├── <group1>.k              (parts + nodes + elements + intra contacts)
        ├── <group2>.k
        └── default.k

핵심 설계:
- 그룹당 단일 파일: parts/nodes/elements/intra contacts 통합 (LS-PrePost로 단독 로드 가능)
- SECTION은 별도 sections.k (그룹 간 중복 정의 방지)
- 공유 노드는 사용 그룹 모두에 중복 출력 (policy: duplicate)
- Material은 공통 materials.k (default DB)
- igaParts 포함 (FEM_TO_IGA 결과 모델도 분해 가능)
"""
import os
import json
import fnmatch
from io import StringIO
from collections import defaultdict


# ============================================================================
# 메인 진입점
# ============================================================================
def decompose_k_file(dynaImporter, cur_dir, input_filename, option):
    """K 파일 분해 진입.

    Args:
        dynaImporter: KooDynaImporter (importDynaFile 완료 상태)
        cur_dir: 현재 작업 디렉토리
        input_filename: 입력 파일명 (decompose_manifest용)
        option: dict (KooMeshModifier ImportOption에서 파싱된 옵션)
    """
    decomposer = KFileDecomposer(dynaImporter, cur_dir, input_filename, option)
    decomposer.run()


# ============================================================================
# 클래스
# ============================================================================
class KFileDecomposer:
    def __init__(self, dynaImporter, cur_dir, input_filename, option):
        self.dynaImporter = dynaImporter
        self.cur_dir = cur_dir
        self.input_filename = input_filename or "model.k"
        self.option = option or {}

        # 옵션
        self.output_dir = self._resolve_output_dir(self.option.get("OutputDir", "decomposed_output"))
        self.default_group_name = self.option.get("DefaultGroupName", "default")
        self.groups_subdir = self.option.get("GroupsSubdir", "groups")
        self.separate_materials = self.option.get("SeparateMaterials", False)
        self.shared_nodes_policy = self.option.get("SharedNodesPolicy", "duplicate")
        self.emit_group_sets = self.option.get("EmitGroupSets", True)
        self.model_independent_split = self.option.get("ModelIndependentSplit", True)
        self.group_boundary_policy = self.option.get("GroupBoundaryPolicy", "inline")

        # 그룹 정의 로드 (GroupFromFile은 파일 읽어서 patterns/parts로 변환)
        self.groups_def = self._load_groups(self.option.get("Groups", []))

        # 분류 결과
        self.pid_to_group = {}              # {pid: group_name}
        self.node_to_groups = defaultdict(set)  # {nid: set(group_names)}

    # --------------------------------------------------------------------
    # 진입
    # --------------------------------------------------------------------
    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        groups_dir = os.path.join(self.output_dir, self.groups_subdir) if self.groups_subdir else self.output_dir
        os.makedirs(groups_dir, exist_ok=True)

        print(f"[DECOMPOSE_K] 출력 폴더: {self.output_dir}")
        print(f"[DECOMPOSE_K] 그룹 정의: {len(self.groups_def)}개 + default")

        # 1. 파트 → 그룹
        self._classify_parts()
        # 2. 노드 → 그룹 (요소 사용 기반)
        self._classify_nodes()

        # 3. 그룹별 파일 출력 (단일 파일에 nodes+elements+parts+intra contacts 통합)
        # SECTION은 별도 sections.k에 모음 (중복 정의 방지)
        all_groups = self._all_group_names()
        for grp in all_groups:
            self._write_group_file(grp, groups_dir)

        # 4. 공통 파일들 출력
        self._write_sections_file()
        self._write_materials_file()
        self._write_inter_group_contacts_file()
        self._write_globals_file()
        self._write_controls_file()

        # 5. master.k
        self._write_master_file(all_groups)

        # 6. manifest
        self._write_manifest()

        print(f"[DECOMPOSE_K] 완료. master.k → {os.path.join(self.output_dir, 'master.k')}")

    # --------------------------------------------------------------------
    # 옵션 helper
    # --------------------------------------------------------------------
    def _resolve_output_dir(self, raw):
        if os.path.isabs(raw):
            return raw
        return os.path.join(self.cur_dir, raw)

    def _load_groups(self, groups_raw):
        """옵션 Groups 리스트를 정규화. GroupFromFile은 실제 파일 읽기."""
        normalized = []
        for g in groups_raw:
            entry = {
                "name": g.get("name", "unnamed"),
                "patterns": list(g.get("patterns", [])),
                "parts": list(g.get("parts", [])),
            }
            from_file = g.get("from_file")
            if from_file:
                fp = from_file if os.path.isabs(from_file) else os.path.join(self.cur_dir, from_file)
                if os.path.exists(fp):
                    with open(fp, 'r') as f:
                        for raw in f:
                            line = raw.strip()
                            if not line or line.startswith('#') or line.startswith('$'):
                                continue
                            # 콤마 분리도 지원
                            for tok in line.split(','):
                                tok = tok.strip()
                                if not tok:
                                    continue
                                if any(c in tok for c in "*?[]"):
                                    entry["patterns"].append(tok)
                                else:
                                    entry["parts"].append(tok)
                else:
                    print(f"  Warning: GroupFromFile 경로 없음: {fp}")
            normalized.append(entry)
        return normalized

    def _all_group_names(self):
        names = [g["name"] for g in self.groups_def]
        if self.default_group_name not in names:
            names.append(self.default_group_name)
        return names

    # --------------------------------------------------------------------
    # 1. 파트 → 그룹
    # --------------------------------------------------------------------
    def _classify_parts(self):
        partMan = self.dynaImporter.partManager
        all_parts = (
            list(partMan.parts.values())
            + list(getattr(partMan, 'partsRigid', {}).values())
            + list(getattr(partMan, 'igaParts', {}).values())
        )
        for part in all_parts:
            grp = self._assign_group(part.name)
            self.pid_to_group[part.id] = grp
        # 통계
        from collections import Counter
        stats = Counter(self.pid_to_group.values())
        for g, n in sorted(stats.items()):
            print(f"  group '{g}': {n} parts")

    def _assign_group(self, part_name):
        """파트 이름을 그룹에 할당 (등록 순서 우선, 첫 매칭)."""
        for grp in self.groups_def:
            if part_name in grp["parts"]:
                return grp["name"]
            for pat in grp["patterns"]:
                if fnmatch.fnmatch(part_name, pat):
                    return grp["name"]
        return self.default_group_name

    # --------------------------------------------------------------------
    # 2. 노드 → 그룹 (요소 사용 기반, duplicate policy)
    # --------------------------------------------------------------------
    def _classify_nodes(self):
        partMan = self.dynaImporter.partManager
        all_parts_dict = {
            **partMan.parts,
            **getattr(partMan, 'partsRigid', {}),
            **getattr(partMan, 'igaParts', {}),
        }
        for pid, part in all_parts_dict.items():
            grp = self.pid_to_group.get(pid, self.default_group_name)
            elem_mgr = getattr(part, 'elementManager', None)
            if elem_mgr is None:
                continue  # IGA 파트는 elementManager 없을 수 있음 → skip (노드 추적 불가)
            for elem in elem_mgr.elements.values():
                for node in getattr(elem, 'nodes', []):
                    if node is None:
                        continue
                    nid = getattr(node, 'id', None)
                    if nid is None:
                        continue
                    self.node_to_groups[nid].add(grp)
        # 공유 노드 통계
        n_shared = sum(1 for s in self.node_to_groups.values() if len(s) > 1)
        print(f"  shared nodes (across groups): {n_shared}")

    def _node_belongs_to_group(self, nid, grp):
        """노드를 이 그룹의 nodes 출력에 포함할지 (duplicate policy)."""
        groups = self.node_to_groups.get(nid, set())
        if not groups:
            return False
        if self.shared_nodes_policy == "duplicate":
            return grp in groups
        elif self.shared_nodes_policy == "first_group":
            # 가장 처음 등록된 그룹에만
            for candidate in self._all_group_names():
                if candidate in groups:
                    return candidate == grp
            return False
        else:
            # 알 수 없는 정책 → duplicate fallback
            return grp in groups

    # --------------------------------------------------------------------
    # 3. 그룹 파일 출력
    # --------------------------------------------------------------------
    def _write_group_file(self, group_name, groups_dir):
        """nodes + elements + parts + intra contacts 통합 (SECTION은 별도 sections.k)."""
        out_path = os.path.join(groups_dir, f"{group_name}.k")

        # 그룹의 PID 목록
        group_pids = [pid for pid, g in self.pid_to_group.items() if g == group_name]
        partMan = self.dynaImporter.partManager
        # parts / partsRigid / igaParts 통합 lookup
        def _lookup_part(pid):
            return (
                partMan.parts.get(pid)
                or getattr(partMan, 'partsRigid', {}).get(pid)
                or getattr(partMan, 'igaParts', {}).get(pid)
            )
        group_parts = [_lookup_part(pid) for pid in group_pids]
        group_parts = [p for p in group_parts if p is not None]

        # 사용된 SECID 수집
        section_ids = set()
        for part in group_parts:
            if getattr(part, 'secid', 0):
                section_ids.add(part.secid)

        # Intra-group contacts
        intra_contacts = self._select_intra_group_contacts(group_name)

        with open(out_path, 'w') as f:
            f.write("*KEYWORD\n$ KOO_DECOMPOSED_NO_AUTO_PASSTHROUGH\n")
            f.write(f"$$ ===== Group: {group_name} =====\n$$\n")

            # --- Parts ---
            # (SECTION은 별도 sections.k에 통합 출력 — 중복 정의 방지)
            f.write("$$ --- Parts ---\n")
            for part in group_parts:
                # WriteStreamDynaPart는 단일 파트 출력
                stream = StringIO()
                if hasattr(part, 'WriteStreamDynaPart'):
                    part.WriteStreamDynaPart(stream, 0)
                f.write(stream.getvalue())

            # --- Nodes ---
            self._write_group_nodes(f, group_name, header="$$ --- Nodes ---")

            # --- Elements ---
            f.write("$$ --- Elements ---\n")
            for part in group_parts:
                stream = StringIO()
                if hasattr(part, 'WriteStreamDynaElements') and len(part.elementManager.elements) > 0:
                    part.WriteStreamDynaElements(stream, 0, 0)
                f.write(stream.getvalue())

            # --- Intra-group contacts ---
            if intra_contacts:
                f.write("$$ --- Intra-group contacts ---\n")
                for contact in intra_contacts:
                    stream = StringIO()
                    if hasattr(contact, 'WriteStreamDynaKeyword'):
                        contact.WriteStreamDynaKeyword(stream, 0)
                    f.write(stream.getvalue())

            f.write("*END\n")

        print(f"  → {out_path}")

    def _write_group_nodes(self, f, group_name, header=""):
        """이 그룹에 속한 노드 출력 (duplicate policy)."""
        if header:
            f.write(header + "\n")
        nodeMan = self.dynaImporter.nodeManager
        f.write("*NODE\n$$   NID               X               Y               Z      TC      RC\n")
        for nid, node in nodeMan.nodes.items():
            if not self._node_belongs_to_group(nid, group_name):
                continue
            tc = getattr(node, 'tc', 0)
            rc = getattr(node, 'rc', 0)
            f.write(f"{nid:>8}{node.x:>16.8e}{node.y:>16.8e}{node.z:>16.8e}{tc:>8}{rc:>8}\n")

    def _write_sections_file(self):
        """sections.k — 정식 SECTION + 미인터프리트 SECTION_* raw 통합 (중복 정의 방지).

        SECTION_IGA_SOLID 같은 미인터프리트 SECTION 변형도 globals.k 대신 여기에 모음.
        master.k 로드 시 SID 충돌 가능성 차단.
        """
        out_path = os.path.join(self.output_dir, "sections.k")
        secMan = self.dynaImporter.sectionManager
        # 정식 SECTION 또는 raw SECTION_* 둘 중 하나라도 있어야 출력
        has_formal = bool(getattr(secMan, 'sections', None))
        raw_section_blocks = list(self._iter_uninterpreted_filtered(prefix="SECTION_"))
        if not has_formal and not raw_section_blocks:
            return
        with open(out_path, 'w') as f:
            f.write("*KEYWORD\n$ KOO_DECOMPOSED_NO_AUTO_PASSTHROUGH\n")
            if has_formal:
                stream = StringIO()
                if hasattr(secMan, 'WriteStreamDynaKeyword'):
                    secMan.WriteStreamDynaKeyword(stream)
                content = stream.getvalue()
                if content.strip():
                    f.write(content)
            if raw_section_blocks:
                f.write("$\n$--- Uninterpreted SECTION_* (raw, preserved) ---\n$\n")
                for kw_name, block in raw_section_blocks:
                    f.write(f"*{kw_name}\n")
                    for line in block:
                        f.write(line if line.endswith('\n') else line + '\n')
            f.write("*END\n")
        print(f"  → {out_path}")

    def _iter_uninterpreted_filtered(self, prefix=None, exclude_prefix=None):
        """미인터프리트 raw 키워드 (kw_name, block) 페어 yield. prefix/exclude_prefix로 필터링."""
        dyna_mgr = self.dynaImporter.dynaManager
        raw_dict = getattr(dyna_mgr, '_raw_keyword_dict', None) or {}
        interpreted = getattr(self.dynaImporter, 'keywordInterpreted', {}) or {}
        SKIP = {"_INCLUDE_PASSTHROUGH", "INCLUDE", "KEYWORD", "END"}
        for kw_name, blocks in raw_dict.items():
            if kw_name in SKIP:
                continue
            if interpreted.get(kw_name, False):
                continue
            if prefix is not None and not kw_name.startswith(prefix):
                continue
            if exclude_prefix is not None and kw_name.startswith(exclude_prefix):
                continue
            for block in blocks:
                yield (kw_name, block)

    # --------------------------------------------------------------------
    # 4. Contact 분류 (intra vs inter)
    # --------------------------------------------------------------------
    def _select_intra_group_contacts(self, group_name):
        """양면이 모두 group_name인 contact만 반환."""
        result = []
        for contact in self._iter_all_contacts():
            ss_groups, ms_groups = self._contact_groups(contact)
            if ss_groups == {group_name} and ms_groups == {group_name}:
                result.append(contact)
        return result

    def _iter_all_contacts(self):
        ctMan = self.dynaImporter.contactManager
        for c in ctMan.contacts.values():
            yield c
        for c in getattr(ctMan, 'rigidContacts', {}).values():
            yield c

    def _contact_groups(self, contact):
        """contact의 SS/MS측 그룹 set 반환."""
        ss = self._resolve_side_groups(contact.SSID, contact.SSTYP)
        ms = self._resolve_side_groups(contact.MSID, contact.MSTYP)
        return ss, ms

    def _resolve_side_groups(self, sid, styp):
        """SSID/MSID + SSTYP/MSTYP → 관련 그룹 집합."""
        if styp == 3:
            # PID 직접
            grp = self.pid_to_group.get(sid)
            return {grp} if grp else set()
        if styp == 2:
            # SET_PART → PID 목록 → 그룹 집합
            partMan = self.dynaImporter.partManager
            partSet = partMan.partSets.get(sid) if hasattr(partMan, 'partSets') else None
            if partSet is None:
                return set()
            pids = getattr(partSet, 'partList', None) or getattr(partSet, 'parts', [])
            groups = set()
            for pid in pids:
                g = self.pid_to_group.get(pid if isinstance(pid, int) else getattr(pid, 'id', 0))
                if g:
                    groups.add(g)
            return groups
        if styp == 0:
            # SET_SEGMENT → segment의 노드를 통해 그룹 결정
            segMan = self.dynaImporter.segmentSetManager
            seg_set = None
            for attr in ('segmentSetList', 'segmentSets', 'sets'):
                container = getattr(segMan, attr, None)
                if isinstance(container, dict) and sid in container:
                    seg_set = container[sid]
                    break
            if seg_set is None:
                return set()
            groups = set()
            # 1. 미리 채워진 pid 시도
            pid_attr = getattr(seg_set, 'pid', 0)
            if pid_attr:
                g = self.pid_to_group.get(pid_attr)
                if g:
                    groups.add(g)
            # 2. segments 리스트 순회 (각 segment = [nid1, nid2, nid3, nid4] 같은 노드 리스트)
            #    노드의 node_to_groups를 통해 그룹 결정
            for seg in getattr(seg_set, 'segments', []):
                # seg는 노드 리스트 또는 (id, nids) 형태일 수 있음 — 안전하게 iter
                try:
                    nids_iter = seg if hasattr(seg, '__iter__') else []
                except TypeError:
                    nids_iter = []
                for nid in nids_iter:
                    if isinstance(nid, int) and nid in self.node_to_groups:
                        groups |= self.node_to_groups[nid]
            return groups
        if styp == 4:
            # SET_NODE → 노드의 사용 그룹들
            nodeSetMan = self.dynaImporter.nodeSetManager
            nset = None
            for attr in ('nodeSets', 'sets', 'nodeSetList'):
                container = getattr(nodeSetMan, attr, None)
                if isinstance(container, dict) and sid in container:
                    nset = container[sid]
                    break
            if nset is None:
                return set()
            groups = set()
            nodes = getattr(nset, 'nodes', []) or getattr(nset, 'nids', [])
            for n in nodes:
                nid = n if isinstance(n, int) else getattr(n, 'id', None)
                if nid is not None:
                    groups |= self.node_to_groups.get(nid, set())
            return groups
        return set()

    # --------------------------------------------------------------------
    # 5. 공통 파일들 출력
    # --------------------------------------------------------------------
    def _write_materials_file(self):
        """materials.k — MAT/EOS/HG 공통."""
        if self.separate_materials:
            return  # 그룹별 분리 시 (현재 미구현, 옵션 hook만)
        out_path = os.path.join(self.output_dir, "materials.k")
        with open(out_path, 'w') as f:
            f.write("*KEYWORD\n$ KOO_DECOMPOSED_NO_AUTO_PASSTHROUGH\n")
            stream = StringIO()
            matMan = self.dynaImporter.matManager
            if hasattr(matMan, 'WriteStreamDynaKeyword'):
                matMan.WriteStreamDynaKeyword(stream, 0)
            content = stream.getvalue()
            if content.strip():
                f.write(content)
            f.write("*END\n")
        print(f"  → {out_path}")

    def _write_inter_group_contacts_file(self):
        """inter_group_contacts.k — 양면 다른 그룹 contact."""
        out_path = os.path.join(self.output_dir, "inter_group_contacts.k")
        contacts = []
        for contact in self._iter_all_contacts():
            ss, ms = self._contact_groups(contact)
            # 같은 그룹 한 개에 한정되지 않으면 inter
            if not (ss == ms and len(ss) == 1):
                contacts.append(contact)
        if not contacts:
            return
        with open(out_path, 'w') as f:
            f.write("*KEYWORD\n$ KOO_DECOMPOSED_NO_AUTO_PASSTHROUGH\n")
            for contact in contacts:
                stream = StringIO()
                if hasattr(contact, 'WriteStreamDynaKeyword'):
                    contact.WriteStreamDynaKeyword(stream, 0)
                f.write(stream.getvalue())
            f.write("*END\n")
        print(f"  → {out_path} ({len(contacts)} contacts)")

    def _write_globals_file(self):
        """globals.k — SET_*, DEFINE_*, PARAMETER, RIGIDWALL 등 모델 의존 전역."""
        out_path = os.path.join(self.output_dir, "globals.k")
        with open(out_path, 'w') as f:
            f.write("*KEYWORD\n$ KOO_DECOMPOSED_NO_AUTO_PASSTHROUGH\n")
            # SET_PART (partSets)
            partMan = self.dynaImporter.partManager
            if hasattr(partMan, 'partSets') and partMan.partSets:
                for ps in partMan.partSets.values():
                    stream = StringIO()
                    if hasattr(ps, 'WriteStreamDynaKeyword'):
                        ps.WriteStreamDynaKeyword(stream)
                    f.write(stream.getvalue())
            # SET_NODE
            nodeSetMan = self.dynaImporter.nodeSetManager
            stream = StringIO()
            if hasattr(nodeSetMan, 'WriteStreamDynaKeyword'):
                nodeSetMan.WriteStreamDynaKeyword(stream, 0)
            f.write(stream.getvalue())
            # SET_SEGMENT
            segMan = self.dynaImporter.segmentSetManager
            stream = StringIO()
            if hasattr(segMan, 'WriteStreamDynaKeyword'):
                segMan.WriteStreamDynaKeyword(stream, 0)
            f.write(stream.getvalue())
            # DEFINE_*
            defMan = self.dynaImporter.defineManager
            stream = StringIO()
            if hasattr(defMan, 'WriteStreamDynaKeyword'):
                defMan.WriteStreamDynaKeyword(stream, 0)
            f.write(stream.getvalue())
            # LOAD/INITIAL/BOUNDARY/RIGIDWALL → loadManager, initialManager, boundaryNodeManager
            for mgr_name in ('loadManager', 'initialManager', 'boundaryNodeManager', 'constrainedManager', 'dampingManager', 'additionalManager'):
                mgr = getattr(self.dynaImporter, mgr_name, None)
                if mgr is None:
                    continue
                stream = StringIO()
                try:
                    if hasattr(mgr, 'WriteStreamDynaKeyword'):
                        # 인자 가변 — 가장 단순한 호출 시도
                        try:
                            mgr.WriteStreamDynaKeyword(stream, 0)
                        except TypeError:
                            mgr.WriteStreamDynaKeyword(stream)
                except Exception as e:
                    print(f"  Warning: {mgr_name} 출력 실패 (skip): {e}")
                f.write(stream.getvalue())
            # 미인터프리트 키워드 raw 보존 (RIGIDWALL_PLANAR 단순형 등)
            self._write_uninterpreted_raw(f)
            f.write("*END\n")
        print(f"  → {out_path}")

    def _write_uninterpreted_raw(self, f):
        """KooDynaImporter가 모르는 키워드를 raw text로 보존 (globals.k에 추가).

        SECTION_* 키워드는 제외 (sections.k에서 별도 처리하여 중복 정의 방지).
        """
        try:
            wrote_header = False
            for kw_name, block in self._iter_uninterpreted_filtered(exclude_prefix="SECTION_"):
                if not wrote_header:
                    f.write("$\n$--- Uninterpreted keywords (raw, preserved) ---\n$\n")
                    wrote_header = True
                f.write(f"*{kw_name}\n")
                for line in block:
                    f.write(line if line.endswith('\n') else line + '\n')
        except Exception as e:
            print(f"  Warning: uninterpreted raw 출력 실패 (skip): {e}")

    def _write_controls_file(self):
        """controls.k — CONTROL_*, DATABASE_* 등 모델 독립 설정."""
        if not self.model_independent_split:
            return
        out_path = os.path.join(self.output_dir, "controls.k")
        with open(out_path, 'w') as f:
            f.write("*KEYWORD\n$ KOO_DECOMPOSED_NO_AUTO_PASSTHROUGH\n")
            ctrlMan = self.dynaImporter.controlManager
            stream = StringIO()
            if hasattr(ctrlMan, 'WriteStreamDynaKeyword'):
                ctrlMan.WriteStreamDynaKeyword(stream)
            f.write(stream.getvalue())
            dbMan = self.dynaImporter.databaseManager
            stream = StringIO()
            if hasattr(dbMan, 'WriteStreamDynaKeyword'):
                dbMan.WriteStreamDynaKeyword(stream)
            f.write(stream.getvalue())
            f.write("*END\n")
        print(f"  → {out_path}")

    # --------------------------------------------------------------------
    # 6. master.k (IGA/preserved include 보존 포함)
    # --------------------------------------------------------------------
    def _write_master_file(self, all_groups):
        master_path = os.path.join(self.output_dir, "master.k")
        # IGA/preserved passthrough include들을 출력 폴더로 복사
        copied_includes = self._copy_passthrough_includes()
        with open(master_path, 'w') as f:
            f.write("*KEYWORD\n$ KOO_DECOMPOSED_NO_AUTO_PASSTHROUGH\n")
            f.write("*TITLE\nDecomposedModel\n")
            for fname in ("controls.k", "globals.k", "materials.k", "sections.k"):
                if os.path.exists(os.path.join(self.output_dir, fname)):
                    f.write(f"*INCLUDE\n{fname}\n")
            for grp in all_groups:
                rel = f"{self.groups_subdir}/{grp}.k" if self.groups_subdir else f"{grp}.k"
                if os.path.exists(os.path.join(self.output_dir, rel)):
                    f.write(f"*INCLUDE\n{rel}\n")
            inter = "inter_group_contacts.k"
            if os.path.exists(os.path.join(self.output_dir, inter)):
                f.write(f"*INCLUDE\n{inter}\n")
            # passthrough include 참조 (IGA/preserved)
            if copied_includes:
                f.write("$$ --- Preserved passthrough includes (IGA/PARAMETER_LOCAL/user-specified) ---\n")
                for base in copied_includes:
                    f.write(f"*INCLUDE\n{base}\n")
            f.write("*END\n")
        print(f"  → {master_path} (passthrough includes preserved: {len(copied_includes)})")

    def _copy_passthrough_includes(self):
        """IGA/preserved passthrough include 파일들을 output_dir로 복사.

        Returns:
            복사된 파일들의 basename 리스트
        """
        import shutil
        passthrough = getattr(self.dynaImporter.dynaManager, '_include_passthrough_data', [])
        copied = []
        for entry in passthrough:
            src = entry.get('file', '')
            if not src or not os.path.exists(src):
                continue
            base = os.path.basename(src)
            dst = os.path.join(self.output_dir, base)
            if os.path.abspath(src) != os.path.abspath(dst):
                try:
                    shutil.copy2(src, dst)
                except Exception as e:
                    print(f"  Warning: passthrough 파일 복사 실패 {base}: {e}")
                    continue
            copied.append(base)
        return copied

    # --------------------------------------------------------------------
    # 7. Manifest
    # --------------------------------------------------------------------
    def _write_manifest(self):
        # 미인터프리트 키워드 목록 (raw로 globals.k에 보존됨)
        dyna_mgr = self.dynaImporter.dynaManager
        raw_dict = getattr(dyna_mgr, '_raw_keyword_dict', {}) or {}
        interpreted = getattr(self.dynaImporter, 'keywordInterpreted', {}) or {}
        SKIP = {"_INCLUDE_PASSTHROUGH", "INCLUDE", "KEYWORD", "END"}
        uninterpreted = []
        for kw_name, blocks in raw_dict.items():
            if kw_name in SKIP or interpreted.get(kw_name, False):
                continue
            target = "sections.k (raw)" if kw_name.startswith("SECTION_") else "globals.k (raw)"
            uninterpreted.append({
                "keyword": kw_name,
                "block_count": len(blocks),
                "preserved_in": target,
            })

        manifest = {
            "input_file": self.input_filename,
            "output_dir": self.output_dir,
            "groups": self._all_group_names(),
            "default_group_name": self.default_group_name,
            "shared_nodes_policy": self.shared_nodes_policy,
            "pid_to_group": {str(k): v for k, v in self.pid_to_group.items()},
            "n_parts": len(self.pid_to_group),
            "n_shared_nodes": sum(1 for s in self.node_to_groups.values() if len(s) > 1),
            "uninterpreted_keywords": uninterpreted,
            "uninterpreted_note": (
                "These keywords were preserved as raw text. KooMeshModifier cannot "
                "modify them yet. To enable modification, add a parser to "
                "KooDynaAdditional.SetAdditionalfromDyna and KooMeshImporter.importAdditional."
            ) if uninterpreted else None,
        }
        out_path = os.path.join(self.output_dir, "decompose_manifest.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"  → {out_path}")
        if uninterpreted:
            print(f"  [INFO] Uninterpreted keywords (preserved as raw): {len(uninterpreted)}")
            for entry in uninterpreted[:5]:
                print(f"    - *{entry['keyword']} ({entry['block_count']} blocks)")
