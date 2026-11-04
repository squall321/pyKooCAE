"""K-File Import Merger: 외부 .k 파일을 기존 모델에 병합 import.

핵심 동작:
- 새 파일의 PID/NID/EID/SID/NSID/PSID/SSID/CID(접촉)는 기존 max + 1부터 자동 재할당
- MID/EOSID/HGID·곡선 LCID·좌표계 CID 는 그대로 보존 (재료·곡선은 공통 DB — 재질이 곡선 번호를 참조한다)
- 기존 모델에 없는 번호만 새로 추가. 곡선·HOURGLASS 가 같은 번호로 내용이 다르면 기준 덱 것을 남기고 🔴(종료 코드 3)
- 경계 조건은 새 번호로 더한다. 번호를 밀 수 없는 구속·부분 감쇠·강체벽·INTERFACE·하중·초기 조건·원문 블록은
  옮기지 않고 🔴, CONTROL·DATABASE·DAMPING_GLOBAL 은 기준 덱 설정을 쓴다(알림)(v131 M2)
- 새 파일의 *INCLUDE는 모두 인라인 (IGA passthrough 비활성)

사용 케이스:
- 신규 파트 모델링 후 기존 모델에 합치기
- 멀티 모델 통합 (조립 시뮬레이션 빌드)
"""
import os


def import_merge_k(simGenerator, option):
    """가져올 .k 파일을 기존 dynaImporter에 병합.

    Args:
        simGenerator: KooMeshModifier 인스턴스 (self.dynaImporter, self.curDir 보유)
        option: dict
            - ImportFile: 가져올 .k 파일 경로 (필수)
    """
    cur_dir = simGenerator.curDir
    dynaImporter = simGenerator.dynaImporter

    import_file = option.get("ImportFile")
    if not import_file:
        raise ValueError("[IMPORT_MERGE_K] ImportFile 옵션 필수")
    if not os.path.isabs(import_file):
        import_file = os.path.join(cur_dir, import_file)
    if not os.path.exists(import_file):
        raise FileNotFoundError(f"[IMPORT_MERGE_K] 파일 없음: {import_file}")

    print(f"[IMPORT_MERGE_K] 가져올 파일: {import_file}")

    # 1. 별도 importer로 새 모델 로드 (모든 include 인라인 + IGA 자동 보존 비활성)
    new_importer = _build_new_importer()
    new_importer.dynaManager._preserve_include_patterns = []
    new_importer.dynaManager._disable_auto_iga_passthrough = True

    folder = os.path.dirname(import_file)
    base = os.path.basename(import_file)
    new_importer.dynaManager.SetInputPath(import_file)
    new_importer.importDynaFile(import_file, writeLog=False)
    new_importer.importKeywordstoManager()
    new_importer.SyncronizeMaxID()
    print(f"[IMPORT_MERGE_K] 새 모델 로드 완료: parts={len(new_importer.partManager.parts)}, "
          f"nodes={len(new_importer.nodeManager.nodes)}")

    # 2. 기존 모델 maxID 계산
    dynaImporter.SyncronizeMaxID()
    offsets = _compute_offsets(dynaImporter)
    print(f"[IMPORT_MERGE_K] Offset (기존 maxID 기준): {offsets}")

    # 3. 새 매니저들에 OffsetID 적용 (MAT/EOS/HG는 offset 안 함)
    _apply_offsets(new_importer, offsets)

    # 4. MAT/EOS/HG: 기존에 없는 ID만 추가 (병합)
    n_added_mat = _merge_materials(dynaImporter.matManager, new_importer.matManager)
    print(f"[IMPORT_MERGE_K] MAT/EOS 병합: 신규 추가 {n_added_mat}개 (기존 ID는 보존)")

    # 5. 나머지 매니저 병합(번호를 민 것만 — _merge_managers)
    _merge_managers(dynaImporter, new_importer, offsets)

    # 6. 최종 maxID 동기화
    dynaImporter.SyncronizeMaxID()
    print(f"[IMPORT_MERGE_K] 병합 완료. 통합 후 parts={len(dynaImporter.partManager.parts)}, "
          f"nodes={len(dynaImporter.nodeManager.nodes)}")

    # 7. 옮기지 못한 것을 알린다 — 예전엔 가져온 덱의 원문 블록·하중·초기 조건이 경고 없이 사라졌다(v131 M2)
    _report_unmerged(new_importer)
    if _CONFLICTS:
        from KooCAEManager.KooElement import note_content_loss
        print(f"  🔴 [IMPORT_MERGE_K] 같은 번호인데 내용이 다른 정의 — 기준 덱 것을 남겼다: {', '.join(_CONFLICTS)}")
        print("     가져온 덱의 재질·요소가 그 번호를 쓰면 기준 덱 정의를 쓰게 된다. 가져올 덱의 번호를 바꿀 것")
        for c in _CONFLICTS:
            note_content_loss(f"IMPORT_MERGE_K — 번호 충돌 {c}")
        _CONFLICTS.clear()


# ============================================================================
# helpers
# ============================================================================
def _build_new_importer():
    """KooDynaImporter 새 인스턴스 (빈 매니저들로 초기화)."""
    from KooCAEManager.KooMeshImporter import KooDynaImporter
    return KooDynaImporter()


def _compute_offsets(dynaImporter):
    """기존 모델의 maxID 모음. 새 ID는 maxID + 1부터 시작."""
    partMan = dynaImporter.partManager
    nodeMan = dynaImporter.nodeManager
    secMan = dynaImporter.sectionManager
    nodeSetMan = dynaImporter.nodeSetManager
    segMan = dynaImporter.segmentSetManager
    contactMan = dynaImporter.contactManager
    defineMan = dynaImporter.defineManager

    # PartManager.parts의 max EID는 모든 파트의 elementManager 통과해서 계산
    max_eid = 0
    for part in list(partMan.parts.values()) + list(getattr(partMan, 'partsRigid', {}).values()):
        em = getattr(part, 'elementManager', None)
        if em is not None:
            max_eid = max(max_eid, getattr(em, 'maxID', 0))

    return {
        'pid': getattr(partMan, 'maxID', 0),
        'nid': getattr(nodeMan, 'maxID', 0),
        'eid': max_eid,
        'sid': getattr(secMan, 'maxid', 0),
        'nsid': getattr(nodeSetMan, 'maxID', 0),
        # PartSet 번호는 .psid 다 — 예전엔 .sid 를 읽어 늘 0 이라 가져온 셋이 기준 덱 셋 번호와 겹쳤다(v131 M2)
        'psid': max([getattr(partMan, 'maxSID', 0) or 0]
                    + [getattr(ps, 'psid', 0) for ps in getattr(partMan, 'partSets', {}).values()]),
        'ssid': getattr(segMan, 'maxid', 0),
        'cid': getattr(contactMan, 'maxid', 0),
        # 곡선 LCID 는 보존한다 — 재질(LCSS 등)·경계가 번호로 참조해 곡선만 밀면 참조가 틀린다. 예전엔 .id(없는 속성)를 읽어
        # 늘 0 이었고, 병합이 같은 번호의 기준 덱 곡선을 덮어썼다(v131 M2 — _merge_defines 가 막는다)
        'lcid': 0,
        'elem_set_sid': max((getattr(part.elementManager, 'maxSID', 0)
                             for part in partMan.parts.values()), default=0),
    }


def _apply_offsets(new_importer, off):
    """새 매니저들의 ID에 offset 적용. MAT/EOS/HG는 건드리지 않음.

    주의: KooPart.OffsetID는 partManager 자체 elementManager만 처리 (각 파트의 elementManager 안 건드림).
    그래서 각 파트의 elementManager.OffsetID는 여기서 직접 호출.
    """
    # 1. NODE
    new_importer.nodeManager.OffsetID(off['nid'])
    # 2. SECTION
    new_importer.sectionManager.OffsetID(off['sid'])
    # 3. PART (PartManager 자체 — PID/PSID/EID/NID)
    #    각 파트 elementManager는 KooPart.OffsetID 내부에서 partManager.elementManager만 처리
    #    → 각 파트 자체 elementManager는 직접 OffsetID 호출
    partMan = new_importer.partManager
    # 각 파트의 elementManager EID 먼저 offset (PartManager.OffsetID 호출 전)
    for part in list(partMan.parts.values()) + list(getattr(partMan, 'partsRigid', {}).values()):
        em = getattr(part, 'elementManager', None)
        if em is not None and hasattr(em, 'OffsetID'):
            try:
                em.OffsetID(off['eid'], off['elem_set_sid'])
            except Exception as e:
                print(f"  Warning: part EID offset 실패 (skip): {e}")
    # PartManager.OffsetID — PID/PSID와 partManager 자체 elementManager 처리
    try:
        # KooPart.OffsetID 내부 elementManager.OffsetID(offsetEID) 호출에 SID 누락 → patch:
        # partManager.elementManager가 비어있을 가능성 큼 → 직접 호출 우회
        if hasattr(partMan, 'elementManager') and partMan.elementManager is not None:
            try:
                partMan.elementManager.OffsetID(off['eid'], off['elem_set_sid'])
            except Exception:
                pass
        # partManager 자체 OffsetID — 우리는 elementManager 부분 이미 처리했으므로
        # PID/PSID 부분만 수동 적용
        for key in partMan.parts:
            partMan.parts[key].id += off['pid']
        for key in getattr(partMan, 'partsRigid', {}):
            partMan.partsRigid[key].id += off['pid']
        for key in getattr(partMan, 'constrainedParts', {}):
            partMan.constrainedParts[key].id += off['pid']
        partMan.maxID += off['pid']
        partMan.maxSID += off['psid']
        for key in getattr(partMan, 'partSets', {}):   # .psid 와 담은 PID — 예전엔 .id 라 여기서 멈춰 셋이 밀리지 않았다(v131 M2)
            ps = partMan.partSets[key]
            if getattr(ps, 'name', '') == f"PartSet_{ps.psid}":   # 이름 없는 셋의 기본 이름은 번호를 따른다(기준 덱 셋과 같은 이름이 되지 않게)
                ps.name = f"PartSet_{ps.psid + off['psid']}"
            ps.psid += off['psid']
            ps.pids = [p + off['pid'] for p in ps.pids]
    except Exception as e:
        print(f"  Warning: PartManager offset 실패: {e}")
    # 파트의 SECID 는 단면 객체를 따라간다 — 단면 번호만 밀고 파트 secid 는 그대로라 기준 덱 단면을 가리켰다(v131 M2).
    # 원문 단면(*SECTION_DISCRETE 등)을 가리키는 파트는 단면 객체가 없다 — 그 원문은 옮기지 못한다고 따로 알린다
    for part in list(partMan.parts.values()) + list(getattr(partMan, 'partsRigid', {}).values()):
        if getattr(part, 'section', None) is not None:
            part.secid = part.section.id

    # 4. NODE SET
    new_importer.nodeSetManager.OffsetID(off['nsid'])
    # 5. SEGMENT SET
    new_importer.segmentSetManager.OffsetID(off['ssid'], off['nid'])
    # 6. CONTACT
    new_importer.contactManager.OffsetID(off['cid'], off['pid'], off['ssid'], off['nsid'], off['psid'])
    # 7. DEFINE
    if hasattr(new_importer.defineManager, 'OffsetID'):
        new_importer.defineManager.OffsetID(off['lcid'], 0)

    # 8. dict re-key — 기존 OffsetID는 .id만 바꾸고 dict key는 유지함.
    #    → OverwriteFrom 시 기존 dict의 같은 key를 덮어쓰는 치명 버그 → 여기서 key를 재할당.
    _rekey_all_managers(new_importer)


def _rekey_all_managers(new_importer):
    """OffsetID 후 ID와 dict key 일치시키기.

    KooDynaImporter의 매니저 dict들은 {id: object} 구조인데
    기존 OffsetID는 object.id만 변경하고 dict key는 안 바꿈.
    Overwrite 시 기존 모델의 같은 key를 덮어쓰는 치명 버그.
    여기서 모든 매니저의 dict를 재구성하여 key를 새 id로 일치시킴.
    """
    # NodeManager
    nm = new_importer.nodeManager
    nm.nodes = {n.id: n for n in nm.nodes.values()}
    # PartManager
    pm = new_importer.partManager
    pm.parts = {p.id: p for p in pm.parts.values()}
    if hasattr(pm, 'partsRigid'):
        pm.partsRigid = {p.id: p for p in pm.partsRigid.values()}
    if hasattr(pm, 'constrainedParts'):
        pm.constrainedParts = {p.id: p for p in pm.constrainedParts.values()}
    if hasattr(pm, 'partSets'):
        pm.partSets = {ps.psid: ps for ps in pm.partSets.values()}
    # 각 part의 elementManager
    for part in list(pm.parts.values()) + list(getattr(pm, 'partsRigid', {}).values()):
        em = getattr(part, 'elementManager', None)
        if em is not None:
            em.elements = {e.id: e for e in em.elements.values()}
            if hasattr(em, 'sets'):
                from KooCAEManager.KooElement import element_set_key   # 셋 종류마다 SID 가 따로다(리뷰 H)
                em.sets = {element_set_key(s): s for s in em.sets.values()}
    # SectionManager
    secm = new_importer.sectionManager
    secm.sections = {s.id: s for s in secm.sections.values()}
    # NodeSetManager
    nsm = new_importer.nodeSetManager
    if hasattr(nsm, 'nodeSets'):
        nsm.nodeSets = {ns.sid: ns for ns in nsm.nodeSets.values()}
    elif hasattr(nsm, 'sets'):
        nsm.sets = {ns.sid: ns for ns in nsm.sets.values()}
    elif hasattr(nsm, 'nodeSetList'):
        nsm.nodeSetList = {ns.sid: ns for ns in nsm.nodeSetList.values()}
    # SegmentSetManager
    sgm = new_importer.segmentSetManager
    if hasattr(sgm, 'segmentSetList'):
        sgm.segmentSetList = {ss.sid: ss for ss in sgm.segmentSetList.values()}
    # ContactManager
    cm = new_importer.contactManager
    cm.contacts = {c.cid: c for c in cm.contacts.values()}
    if hasattr(cm, 'rigidContacts'):
        cm.rigidContacts = {c.cid: c for c in cm.rigidContacts.values()}
    # MaterialManager는 OffsetID 안 했으므로 (MID 보존) 재구성 불필요


def _merge_materials(target_mat_mgr, new_mat_mgr):
    """기존 MaterialManager에 없는 MID만 추가 (충돌 방지)."""
    n_added = 0
    for mid, mat in new_mat_mgr.materials.items():
        if mid not in target_mat_mgr.materials:
            target_mat_mgr.materials[mid] = mat
            n_added += 1
    for eid, eos in getattr(new_mat_mgr, 'eos', {}).items():
        if eid not in getattr(target_mat_mgr, 'eos', {}):
            target_mat_mgr.eos[eid] = eos
            n_added += 1
    for hid, hg in getattr(new_mat_mgr, 'addErosions', {}).items():
        if hid not in getattr(target_mat_mgr, 'addErosions', {}):
            target_mat_mgr.addErosions[hid] = hg
            n_added += 1
    for pid_, pz in getattr(new_mat_mgr, 'addPZElectric', {}).items():   # MID 키(*MAT_ADD_PZELECTRIC) — 예전엔 빠졌다(v131 M2)
        if pid_ not in getattr(target_mat_mgr, 'addPZElectric', {}):
            target_mat_mgr.addPZElectric[pid_] = pz
            n_added += 1
    target_mat_mgr.maxid = max(getattr(target_mat_mgr, 'maxid', 0),
                                getattr(new_mat_mgr, 'maxid', 0))
    return n_added


def _merge_managers(target_importer, new_importer, off=None):
    """MaterialManager 외 매니저 병합. 번호를 민 매니저만 OverwritefromXxx 로 합친다. 곡선·경계·HOURGLASS 는 기준 덱 것을
    덮지 않게 따로 합치고, 번호를 밀 수 없는 구속·감쇠·강체벽 등과 설정(CONTROL·DATABASE)은 옮기지 않는다 — 예전엔 모두
    Overwrite 로 합쳐 같은 번호의 기준 덱 정의·설정을 덮었고, 구속·감쇠·강체벽은 기준 덱 파트·셋을 가리켰다(v131 M2).
    옮기지 않은 것은 _report_unmerged 가 알린다."""
    off = off or {}
    _merge_defines(target_importer.defineManager, new_importer.defineManager)
    _merge_boundaries(target_importer.boundaryNodeManager, new_importer.boundaryNodeManager, off)
    _merge_hourglasses(target_importer.additionalManager, new_importer.additionalManager)
    pairs = [
        ('nodeManager', 'OverwritefromNodeManager'),
        ('partManager', 'OverwritefromPartManager'),
        ('sectionManager', 'OverwritefromSectionManager'),
        ('nodeSetManager', 'OverwritefromNodeSetManager'),
        ('segmentSetManager', 'OverwritefromSegmentSetManager'),
        ('contactManager', 'OverwritefromContactManager'),
    ]
    for mgr_name, method_name in pairs:
        target = getattr(target_importer, mgr_name, None)
        new = getattr(new_importer, mgr_name, None)
        if target is None or new is None:
            continue
        method = getattr(target, method_name, None)
        if method is None:
            print(f"  Warning: {mgr_name}에 {method_name} 메서드 없음 (skip)")
            continue
        try:
            method(new)
        except Exception as e:
            print(f"  Warning: {mgr_name} 병합 실패 (skip): {e}")


# 기준 덱 설정을 쓰므로 옮기지 않아도 되는 것(알리기만 한다). *PARAMETER 는 읽을 때 값을 이미 넣었다
_SETTINGS_PREFIX = ("CONTROL_", "DATABASE_", "TITLE", "PARAMETER", "DAMPING_GLOBAL")
_SKIP = {"_INCLUDE_PASSTHROUGH", "INCLUDE", "KEYWORD", "END"}
# 해석은 하지만 병합하지 않는 것 — 정수로 지닌 PID·NSID·NID·SSID 를 밀 수 없어 합치면 기준 덱 파트·셋을 가리킨다
_NOT_MERGED_PREFIX = ("LOAD_", "INITIAL_", "CONSTRAINED_", "DAMPING_", "RIGIDWALL_", "INTERFACE_", "DEFORMABLE_TO_RIGID",
                      "BOUNDARY_NON_REFLECTING")
_CONFLICTS = []   # 같은 번호·다른 내용(곡선·HOURGLASS) — import_merge_k 끝에서 🔴 로 알린다


def _card_text(obj, title=False):
    """같은 번호의 두 정의가 같은 내용인지 보는 카드 글 — 키워드 줄·주석·(제목 카드면) 제목 줄은 뺀다."""
    from io import StringIO
    st = StringIO()
    try:
        obj.WriteStreamDynaKeyword(st, 0)
    except TypeError:
        obj.WriteStreamDynaKeyword(st)
    lines = [ln for ln in st.getvalue().splitlines() if not ln.startswith(("*", "$"))]
    return "\n".join(lines[1:] if title else lines)


def _merge_defines(target, new):
    """곡선·좌표계 — 번호를 보존해 없는 번호만 더한다. 같은 번호·같은 내용은 하나로, 다르면 기준 덱 것을 남기고 알린다."""
    for key, d in new.defines.items():
        cur = target.defines.get(key)
        if cur is None:
            target.defines[key] = d
            target.maxid = max(target.maxid, getattr(d, 'lcid', 0) or 0)
            continue
        t = str(getattr(d, 'lctype', '')).endswith('_TITLE') or str(getattr(cur, 'lctype', '')).endswith('_TITLE')
        try:
            same = _card_text(cur, t) == _card_text(d, t)
        except Exception:
            same = False
        if not same:
            _CONFLICTS.append(f"곡선 LCID {key}")
    for key, c in new.defineCoordinateSystems.items():
        cur = target.defineCoordinateSystems.get(key)
        if cur is None:
            target.defineCoordinateSystems[key] = c
            target.maxcid = max(target.maxcid, getattr(c, 'cid', 0) or 0)
        else:
            try:
                same = _card_text(cur) == _card_text(c)
            except Exception:
                same = False
            if not same:
                _CONFLICTS.append(f"좌표계 CID {key}")


def _merge_hourglasses(target, new):
    """*HOURGLASS — HGID 는 재질처럼 보존한다(파트가 번호로 참조). 없는 번호만 더하고, 같은 번호·다른 내용은 알린다."""
    for key, hg in new.hourglasses.items():
        cur = target.hourglasses.get(key)
        if cur is None:
            target.hourglasses[key] = hg
        elif _card_text(cur) != _card_text(hg):
            _CONFLICTS.append(f"HOURGLASS HGID {key}")


def _merge_boundaries(target, new, off):
    """경계 조건 — 가져온 조건은 기준 덱 번호 뒤 새 번호로 더한다(예전엔 같은 번호의 기준 덱 조건을 덮어썼다). 절점·절점 셋은
    객체라 오프셋을 따라가고, 정수로 지닌 참조(PZEPOT NSID·강체 PID)는 여기서 민다. 곡선 LCID 는 보존이라 그대로다."""
    from KooCAEManager.KooBoundaryNode import KooBoundaryPZEPOT, KooBoundaryPrescribedMotionRigid, _PartRef
    target.maxid = max([target.maxid or 0] + [k for k in target.boundaries if isinstance(k, int)])
    for b in list(new.boundaries.values()):
        if isinstance(b, KooBoundaryPZEPOT):
            b.nsid += off.get('nsid', 0)
        if isinstance(b, KooBoundaryPrescribedMotionRigid) and isinstance(b.node, _PartRef):
            b.node.id += off.get('pid', 0)
        target.maxid += 1
        b.bid = target.maxid
        target.boundaries[b.bid] = b


def _report_unmerged(new_importer):
    """가져온 덱에서 병합하지 못한 것을 알린다 — 원문 블록(KMM 이 해석하지 않는 키워드)과, 해석했지만 병합하지 않는 하중·초기
    조건·구속·부분 감쇠·강체벽·INTERFACE. 모델 카드는 🔴 + 종료 코드 3(카드 소실 장부), 설정(CONTROL·DATABASE·TITLE·PARAMETER·
    DAMPING_GLOBAL)은 기준 덱 것을 쓰므로 알리기만 한다(v131 M2)."""
    from KooCAEManager.KooElement import note_content_loss
    mgr = new_importer.dynaManager
    raw = getattr(mgr, "_raw_keyword_dict", None) or {}
    interpreted = getattr(new_importer, "keywordInterpreted", {}) or {}
    counts = {k: len(v) for k, v in raw.items()}
    for k in getattr(mgr, "_empty_keyword_names", None) or []:   # 데이터 카드 없는 키워드
        counts.setdefault(k, 0)
    lost, settings = [], []
    for kw, n in counts.items():
        if kw in _SKIP or kw.startswith("INCLUDE"):
            continue
        if kw.startswith(_SETTINGS_PREFIX):
            settings.append((kw, n))
        elif not interpreted.get(kw, False) or kw.startswith(_NOT_MERGED_PREFIX):
            lost.append((kw, n))
    if settings:
        print(f"[IMPORT_MERGE_K] 가져온 덱의 설정 카드는 옮기지 않는다(기준 덱 설정을 쓴다): "
              f"{', '.join('*' + k for k, _ in settings)}")
    if lost:
        print(f"  🔴 [IMPORT_MERGE_K] 가져온 덱의 다음 카드는 옮기지 못했다 — 병합 결과에 없다: "
              f"{', '.join(f'*{k}({n})' if n else '*' + k for k, n in lost)}")
        print("     원문 키워드(KMM 이 해석하지 않는 것)와 하중·초기 조건·구속·부분 감쇠·강체벽·INTERFACE 는 참조 번호를 함께 밀 수 "
              "없어 옮기지 않는다. 가져올 덱에서 빼거나 병합 뒤 직접 넣을 것")
        for kw, n in lost:
            note_content_loss(f"IMPORT_MERGE_K — 가져온 덱 *{kw}", max(n, 1))
