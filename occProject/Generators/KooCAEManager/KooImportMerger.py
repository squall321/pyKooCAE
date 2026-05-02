"""K-File Import Merger: 외부 .k 파일을 기존 모델에 병합 import.

핵심 동작:
- 새 파일의 PID/NID/EID/SID/NSID/PSID/SSID/CID/DefineID는 기존 max + 1부터 자동 재할당
- MID/EOSID/HGID는 그대로 보존 (재료는 공통 DB)
- 기존 모델에 없는 MID만 새로 추가 (충돌 없는 병합)
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

    # 5. 나머지 매니저는 OverwritefromXxx로 통합 병합
    _merge_managers(dynaImporter, new_importer)

    # 6. 최종 maxID 동기화
    dynaImporter.SyncronizeMaxID()
    print(f"[IMPORT_MERGE_K] 병합 완료. 통합 후 parts={len(dynaImporter.partManager.parts)}, "
          f"nodes={len(dynaImporter.nodeManager.nodes)}")


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
        'psid': max((getattr(ps, 'sid', 0) for ps in getattr(partMan, 'partSets', {}).values()), default=0),
        'ssid': getattr(segMan, 'maxid', 0),
        'cid': getattr(contactMan, 'maxid', 0),
        'lcid': max((getattr(d, 'id', 0) for d in getattr(defineMan, 'defines', {}).values()), default=0)
                if hasattr(defineMan, 'defines') else 0,
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
        for key in getattr(partMan, 'partSets', {}):
            partMan.partSets[key].id += off['psid']
    except Exception as e:
        print(f"  Warning: PartManager offset 실패: {e}")

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
        pm.partSets = {ps.id: ps for ps in pm.partSets.values()}
    # 각 part의 elementManager
    for part in list(pm.parts.values()) + list(getattr(pm, 'partsRigid', {}).values()):
        em = getattr(part, 'elementManager', None)
        if em is not None:
            em.elements = {e.id: e for e in em.elements.values()}
            if hasattr(em, 'sets'):
                em.sets = {s.sid: s for s in em.sets.values()}
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
    target_mat_mgr.maxid = max(getattr(target_mat_mgr, 'maxid', 0),
                                getattr(new_mat_mgr, 'maxid', 0))
    return n_added


def _merge_managers(target_importer, new_importer):
    """MaterialManager 외 모든 매니저를 OverwritefromXxx로 병합."""
    pairs = [
        ('nodeManager', 'OverwritefromNodeManager'),
        ('partManager', 'OverwritefromPartManager'),
        ('sectionManager', 'OverwritefromSectionManager'),
        ('nodeSetManager', 'OverwritefromNodeSetManager'),
        ('segmentSetManager', 'OverwritefromSegmentSetManager'),
        ('contactManager', 'OverwritefromContactManager'),
        ('defineManager', 'OverwritefromDefineManager'),
        ('boundaryNodeManager', 'OverwritefromBoundaryNodeManager'),
        ('dampingManager', 'OverwritefromDampingManager'),
        ('constrainedManager', 'OverwritefromConstrainedManager'),
        ('controlManager', 'OverwritefromControlManager'),
        ('databaseManager', 'OverwritefromDatabaseManager'),
        ('additionalManager', 'OverwritefromDynaAdditionalManager'),
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
