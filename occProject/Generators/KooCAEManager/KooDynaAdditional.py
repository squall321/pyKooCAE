from __future__ import annotations
from KooCAEManager.KooOperator import *

class KooHourglass:
    def __init__(self, HGID, IHQ=5, QM=0.1, IBQ="", Q1=1.5, Q2=0.06, QBVDC="QM", QW="QM"):
        self.HGID = HGID
        self.IHQ = IHQ
        self.QM = QM
        self.IBQ = IBQ
        self.Q1 = Q1
        self.Q2 = Q2
        self.QBVDC = QBVDC
        self.QW = QW
        pass   
    
    def WriteDynaKeyword(self):
        keyword = ""
        keyword += "*HOURGLASS\n"
        keyword += format(self.HGID, ">10")
        keyword += format(self.IHQ, ">10")
        keyword += format(self.QM, ">10.3f")
        if type(self.IBQ) == str:
            keyword += format(self.IBQ, ">10")
        else:
            keyword += format(self.IBQ, ">10d")            
        keyword += format(self.Q1, ">10.3f")
        keyword += format(self.Q2, ">10.3f")
        if type(self.QBVDC) == str:
            keyword += format(self.QBVDC, ">10")
        else:
            keyword += format(self.QBVDC, ">10.3f")
        if type(self.QW) == str:
            keyword += format(self.QW, ">10")
        else:
            keyword += format(self.QW, ">10.3f")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*HOURGLASS\n")
        stream.write(format(self.HGID, ">10"))
        stream.write(format(self.IHQ, ">10"))
        stream.write(format(self.QM, ">10.3f"))
        if type(self.IBQ) == str:
            stream.write(format(self.IBQ, ">10"))
        else:
            stream.write(format(self.IBQ, ">10d"))            
        stream.write(format(self.Q1, ">10.3f"))
        stream.write(format(self.Q2, ">10.3f"))
        if type(self.QBVDC) == str:
            stream.write(format(self.QBVDC, ">10"))
        else:
            stream.write(format(self.QBVDC, ">10.3f"))
        if type(self.QW) == str:
            stream.write(format(self.QW, ">10"))
        else:
            stream.write(format(self.QW, ">10.3f"))
        stream.write("\n")
        
    
def _rw_num(v):
    """강체벽 기록기의 실수 칸 — 덱 값 그대로(10칸 최대 정밀도). 예전엔 10.4f·10.3e 로 잘랐다(누적 체인 묶음 W1, 2026-11-08)."""
    from KooCAEManager.KooDefine import _real10
    return _real10(float(v) if not isinstance(v, str) else KooDynaFloat(v, 0.0))


class KooRigidWallGeometricFlatDisplay:
    def __init__(self, ID=0, name = "",NSID=0,NSIDEX=0,BOXID=0,BIRTH=0.0,DEATH=1.0E20,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,XHEV=0.0,YHEV=0.0,ZHEV=0.0,LENL=0.0,LENM=0.0):
        self.ID = ID
        self.name = name
        self.NSID = NSID
        self.NSIDEX = NSIDEX
        self.BOXID = BOXID
        self.BIRTH = BIRTH
        self.DEATH = DEATH
        self.XT = XT
        self.YT = YT
        self.ZT = ZT
        self.XH = XH
        self.YH = YH
        self.ZH = ZH
        self.FRIC = FRIC
        self.XHEV = XHEV
        self.YHEV = YHEV
        self.ZHEV = ZHEV
        self.LENL = LENL
        self.LENM = LENM
        self.kw = "*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID"   # 읽은 종류(번호 없는 꼴은 _ID 없이 쓴다)
        self.display = None   # DISPLAY 카드(PID, RO, E, PR) — 덱에 있었으면 그대로 쓴다
        pass
    
    def _keyword_text(self):
        """읽은 종류·제목 그대로, DISPLAY 카드까지 쓴다 — 예전엔 늘 _ID 로 썼고 DISPLAY 카드를 버렸으며 실수를 10.3e(유효숫자 4자리)로
        잘랐다(누적 체인 묶음 W1)."""
        n = lambda v: format(v, ">10")
        out = [self.kw]
        if self.kw.endswith("_ID"):
            out.append(n(self.ID) + str(self.name or "").strip()[:70])
        out.append(n(self.NSID) + n(self.NSIDEX) + n(self.BOXID) + _rw_num(self.BIRTH) + _rw_num(self.DEATH))
        out.append("".join(_rw_num(v) for v in (self.XT, self.YT, self.ZT, self.XH, self.YH, self.ZH, self.FRIC)))
        out.append("".join(_rw_num(v) for v in (self.XHEV, self.YHEV, self.ZHEV, self.LENL, self.LENM)))
        if "_DISPLAY" in self.kw and self.display is not None:
            pid, ro, e, pr = self.display
            out.append(n(pid) + _rw_num(ro) + _rw_num(e) + _rw_num(pr))
        return "\n".join(out) + "\n"

    def WriteDynaKeyword(self):
        return self._keyword_text()

    def WriteStreamDynaKeyword(self, stream):
        stream.write(self._keyword_text())


class KooRigidwallPlanarMovingForces:
    def __init__(self, ID=0, NSID=0, NSIDEX=0, BOXID=0,OFFSET=0.0,BIRTH=0.0,DEATH=1.0e20,RWKSF=1.0,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,WVEL=0.0,MASS=0.0,V0=0.0,SOFT=0,SSID=0,N1=0,N2=0,N3=0,N4=0):
        self.ID = ID
        self.NSID = NSID
        self.NSIDEX = NSIDEX
        self.BOXID = BOXID
        self.OFFSET = OFFSET
        self.BIRTH = BIRTH
        self.DEATH = DEATH
        self.RWKSF = RWKSF
        self.XT = XT
        self.YT = YT
        self.ZT = ZT
        self.XH = XH
        self.YH = YH
        self.ZH = ZH
        self.FRIC = FRIC
        self.WVEL = WVEL
        self.MASS = MASS
        self.V0 = V0        
        self.SOFT = SOFT
        self.SSID = SSID
        self.N1 = N1
        self.N2 = N2
        self.N3 = N3
        self.N4 = N4
        self.kw = "*RIGIDWALL_PLANAR_MOVING_FORCES_ID"   # 읽은 종류 — KMM 이 만드는 벽(DROP 바닥 등)은 이 꼴
        self.title = ""
        pass 
    
    def _keyword_text(self):
        """읽은 종류·제목 그대로 쓴다(KMM 이 만드는 벽은 MOVING_FORCES_ID). 예전엔 모든 평면 벽을 MOVING_FORCES_ID(MASS 0)로 바꾸고
        제목을 버렸고, 카드 1 의 OFFSET·BIRTH·DEATH·RWKSF 와 카드 2 의 WVEL 을 쓰지 않아 덱 값이 기본값이 됐으며(DROP 의 RW_BIRTH·RW_DEATH·
        RWKSF 도 출력에 없었다) 실수를 10.4f 로 잘랐다(누적 체인 묶음 W1, 2026-11-08)."""
        n = lambda v: format(v, ">10")
        kw = self.kw
        out = [kw]
        if kw.endswith("_ID"):
            out.append(n(self.ID) + str(self.title or "").strip()[:70])
        out.append(n(self.NSID) + n(self.NSIDEX) + n(self.BOXID)
                   + "".join(_rw_num(v) for v in (self.OFFSET, self.BIRTH, self.DEATH, self.RWKSF)))
        out.append("".join(_rw_num(v) for v in (self.XT, self.YT, self.ZT, self.XH, self.YH, self.ZH, self.FRIC, self.WVEL)))
        if "_MOVING" in kw:
            out.append(_rw_num(self.MASS) + _rw_num(self.V0))
        if "_FORCES" in kw:
            out.append(n(self.SOFT) + n(self.SSID) + n(self.N1) + n(self.N2) + n(self.N3) + n(self.N4))
        return "\n".join(out) + "\n"

    def WriteDynaKeyword(self):
        return self._keyword_text()

    def WriteStreamDynaKeyword(self, stream):
        stream.write(self._keyword_text())


class KooInterfaceSpringbackLSDyna:
    def __init__(self,ID, PSID=1,NSHV=0,FTYPE=0,FTENSR=0,NTHHSV=0,RFLAG=0,INTSTRN=0, OPTC1="0", SLDO=0, NCYC="",FSPLIT=0,NGFLAG=0,CFLAG=0,HFLAG="",OPTC2="",DTWRT="",OPTC3="",NMWRT="",IVFLG=0):
        self.ID = ID 
        self.PSID = PSID
        self.NSHV = NSHV
        self.FTYPE = FTYPE
        self.FTENSR = FTENSR
        self.NTHHSV = NTHHSV
        self.RFLAG = RFLAG
        self.INTSTRN = INTSTRN
        self.OPTC1 = OPTC1
        self.SLDO = SLDO
        self.NCYC = NCYC
        self.FSPLIT = FSPLIT
        self.NGFLAG = NGFLAG
        self.CFLAG = CFLAG
        self.HFLAG = HFLAG
        self.OPTC2 = OPTC2
        self.DTWRT = DTWRT
        self.OPTC3 = OPTC3
        self.NMWRT = NMWRT
        self.IVFLG = IVFLG
        
    def WriteDynaKeyword(self):
        keyword = ""
        keyword += "*INTERFACE_SPRINGBACK_LSDYNA\n"

        keyword += format(self.PSID, ">10")
        keyword += format(self.NSHV, ">10")
        keyword += format(self.FTYPE, ">10")
        keyword += format("          ", ">10")
        keyword += format(self.FTENSR, ">10")
        keyword += format(self.NTHHSV, ">10")
        keyword += format(self.RFLAG, ">10")
        keyword += format(self.INTSTRN, ">10")
        keyword += "\n"
        
        if self.OPTC1 == "OPTCARD":
            keyword += format(self.OPTC1, ">10")
            keyword += format(self.SLDO, ">10")
            keyword += format(self.NCYC, ">10")
            keyword += format(self.FSPLIT, ">10")
            keyword += format(self.NGFLAG, ">10")
            keyword += format(self.CFLAG, ">10")
            keyword += format(self.HFLAG, ">10")
            keyword += "\n"
            
        if self.OPTC2 == "OPTCARD":
            keyword += format(self.OPTC2, ">10")
            keyword += format(self.DTWRT, ">10")
            keyword += "\n"
            
        if self.OPTC3 == "OPTCARD":
            keyword += format(self.OPTC3, ">10")
            keyword += format(self.NMWRT, ">10")
            keyword += format(self.IVFLG, ">10")
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*INTERFACE_SPRINGBACK_LSDYNA\n")
        stream.write(format(self.PSID, ">10"))
        stream.write(format(self.NSHV, ">10"))
        stream.write(format(self.FTYPE, ">10"))
        stream.write(format("          ", ">10"))
        stream.write(format(self.FTENSR, ">10"))
        stream.write(format(self.NTHHSV, ">10"))
        stream.write(format(self.RFLAG, ">10"))
        stream.write(format(self.INTSTRN, ">10"))
        stream.write("\n")

        if self.OPTC1 == "OPTCARD":
            stream.write(format(self.OPTC1, ">10"))
            stream.write(format(self.SLDO, ">10"))
            stream.write(format(self.NCYC, ">10"))
            stream.write(format(self.FSPLIT, ">10"))
            stream.write(format(self.NGFLAG, ">10"))
            stream.write(format(self.CFLAG, ">10"))
            stream.write(format(self.HFLAG, ">10"))
            stream.write("\n")

        if self.OPTC2 == "OPTCARD":
            stream.write(format(self.OPTC2, ">10"))
            stream.write(format(self.DTWRT, ">10"))
            stream.write("\n")

        if self.OPTC3 == "OPTCARD":
            stream.write(format(self.OPTC3, ">10"))
            stream.write(format(self.NMWRT, ">10"))
            stream.write(format(self.IVFLG, ">10"))
            stream.write("\n")


def _d2r_num(v):
    """DEFORMABLE_TO_RIGID_AUTOMATIC 실수 필드를 10칸 안에서 손실 없이 쓴다.

    기존 출력(0.0 -> "       0.0", 1e20 -> "   1.0e+20")을 보존하면서, 1e-7 처럼
    ">10.1f" 로는 0.0 이 돼버리던 작은 값을 지수표기로 살린다.
    """
    f = float(v)
    if f == 0.0:
        return format(0.0, ">10.1f")          # 기존과 동일한 "       0.0"
    if 0.1 <= abs(f) < 1.0e5:
        s = format(f, ">10.1f")               # 사람이 읽기 쉬운 범위는 고정소수점 유지
        if float(s) == f:
            return s
    # 지수표기는 손실 없는 최단 유효숫자. .1e 고정이면 1.25e-3 이 1.3e-03 으로 조용히 바뀌었다(10-07 감사).
    # 1e20 → "   1.0e+20", 1e-7 → "   1.0e-07" 는 그대로라 기존 덱과 바이트 동일.
    for _prec in (1, 2, 3):
        s = format(f, ">10.{0}e".format(_prec))
        if float(s) == f:
            return s
    return format(f, ">10.3e")


class KooDeformableToRigidAutomatic:
    """*DEFORMABLE_TO_RIGID_AUTOMATIC 키워드 클래스"""
    def __init__(self, swset, code, time1, time2, time3, entno, relsw, paired,
                 nrbf, ncsf, rwf, dtmax, d2r_pids, r2d_pids, offset=0.0):
        self.swset = swset
        self.code = code
        self.time1 = time1
        self.time2 = time2
        self.time3 = time3
        self.entno = entno
        self.relsw = relsw
        self.paired = paired
        self.nrbf = nrbf
        self.ncsf = ncsf
        self.rwf = rwf
        self.dtmax = dtmax
        self.d2r_pids = d2r_pids   # list of (pid, lrb)
        self.r2d_pids = r2d_pids   # list of pid
        self.offset = offset

    def WriteDynaKeyword(self):
        kw = "*DEFORMABLE_TO_RIGID_AUTOMATIC\n"
        kw += "$    swset      code     time1     time2     time3     entno     relsw    paired\n"
        # 🔴 예전에는 time1/time3/dtmax/offset 이 ">10.1f" 였다. 그래서 1e-7 같은 작은 값이
        # 0.0 으로 반올림돼 **출력에서 조용히 사라졌다**(time2 만 ">10.1e" 라 살아남았다).
        # 세부 옵션을 열면서 드러난 기존 결함이라 함께 고친다. 0.0 은 _d2r_num 이 "0.0" 으로
        # 내보내므로 기존 덱은 바이트 동일하다.
        kw += f"{self.swset:>10}{self.code:>10}{_d2r_num(self.time1)}{_d2r_num(self.time2)}"
        kw += f"{_d2r_num(self.time3)}{self.entno:>10}{self.relsw:>10}{self.paired:>10}\n"
        kw += "$     nrbf      ncsf       rwf     dtmax       D2R       R2D    offset\n"
        kw += f"{self.nrbf:>10}{self.ncsf:>10}{self.rwf:>10}{_d2r_num(self.dtmax)}"
        kw += f"{len(self.d2r_pids):>10}{len(self.r2d_pids):>10}{_d2r_num(self.offset)}\n"
        for pid, lrb in self.d2r_pids:
            kw += f"{pid:>10}{lrb:>10}      PART\n"
        for pid in self.r2d_pids:
            kw += f"{pid:>10}      PART\n"
        return kw

    def WriteStreamDynaKeyword(self, stream):
        stream.write(self.WriteDynaKeyword())


class KooBoundaryNonReflecting:
    """*BOUNDARY_NON_REFLECTING — 비반사 경계 (응력파 흡수)"""
    def __init__(self, ssid, ad=0.0, as_val=0.0):
        self.ssid = ssid   # Segment Set ID
        self.ad = ad        # dilatational wave (0=on)
        self.as_val = as_val  # shear wave (0=on)

    def WriteStreamDynaKeyword(self, stream):
        stream.write("*BOUNDARY_NON_REFLECTING\n")
        stream.write(f"{self.ssid:>10}{self.ad:>10.1f}{self.as_val:>10.1f}\n")


class KooDynaAdditionalManager:
    def __init__(self):
        self.maxRWID = 0
        self.rigidwalls = {}
        self.hourglasses = {}
        self.maxInterface = 0
        self.interfaces = {}
        self.d2r_automatics = {}
        self.non_reflecting_boundaries = []

    def OverwritefromDynaAdditionalManager(self, dynaAdditionalManager: KooDynaAdditionalManager):

        self.maxRWID = max(self.maxRWID, dynaAdditionalManager.maxRWID)        
        for key, value in dynaAdditionalManager.rigidwalls.items():
            self.rigidwalls[key] = value
        for key, value in dynaAdditionalManager.hourglasses.items():
            self.hourglasses[key] = value
        maxInterfaceKey = 0 
        for key, value in dynaAdditionalManager.interfaces.items():
            self.interfaces[key + self.maxInterface] = value
            maxInterfaceKey = max(maxInterfaceKey, key+self.maxInterface)
        self.maxInterface = maxInterfaceKey
        for key, value in dynaAdditionalManager.d2r_automatics.items():
            self.d2r_automatics[key] = value

    def _free_rigidwall_id(self, ID):
        """번호를 지정해 만드는 강체벽이 이미 있는 번호를 쓰면 먼저 있던 벽을 새 번호로 옮긴다 — 번호 없는 *RIGIDWALL_PLANAR 가 자동
        번호 1 을 받은 뒤 *RIGIDWALL_PLANAR_ID 1 이 같은 키를 덮어 벽 하나가 rc 0 으로 사라졌다(v131 리뷰 R6)."""
        if ID in self.rigidwalls:
            self.maxRWID = max(self.maxRWID, ID, *self.rigidwalls.keys()) + 1
            old = self.rigidwalls[ID]
            setattr(old, "ID" if hasattr(old, "ID") else "id", self.maxRWID)   # 강체벽 클래스는 번호를 .ID 로 지닌다
            # 제자리에서 번호만 바꾼다 — 끝으로 옮기면 벽 차례가 바뀌어 D2R CODE 1·3 의 ENTNO·RWFORC(R16: 정의 차례)가 다른 벽을 가리켰다(리뷰 R7)
            items = [(self.maxRWID if k == ID else k, v) for k, v in self.rigidwalls.items()]
            self.rigidwalls.clear()
            self.rigidwalls.update(items)
            print(f"  Warning: 강체벽 번호 {ID} 가 겹쳐 먼저 있던 벽을 {self.maxRWID} 로 옮긴다(번호 없는 벽이 자동 번호를 받았거나 덱에 같은 번호가 둘)")

    def CreateRigidwallPlanarMovingForces(self, NSID=0, NSIDEX=0, BOXID=0,OFFSET=0.0,BIRTH=0.0,DEATH=1.0e20,RWKSF=1.0,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,WVEL=0.0,MASS=0.0,V0=0.0, SOFT=0,SSID=0,N1=0,N2=0,N3=0,N4=0):
        self.maxRWID = self.maxRWID + 1
        rigidwall = KooRigidwallPlanarMovingForces(self.maxRWID, NSID, NSIDEX, BOXID,OFFSET,BIRTH,DEATH,RWKSF,XT,YT,ZT,XH,YH,ZH,FRIC,WVEL,MASS,V0, SOFT,SSID,N1,N2,N3,N4)
        self.rigidwalls[self.maxRWID] = rigidwall
        return rigidwall
    
    def CreateRigidwallPlanarMovingForceswithID(self, ID=0, NSID=0, NSIDEX=0, BOXID=0,OFFSET=0.0,BIRTH=0.0,DEATH=1.0e20,RWKSF=1.0,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,WVEL=0.0,MASS=0.0,V0=0.0, SOFT=0,SSID=0,N1=0,N2=0,N3=0,N4=0):        
        if ID > self.maxRWID:
            self.maxRWID = ID            
        rigidwall = KooRigidwallPlanarMovingForces(ID, NSID, NSIDEX, BOXID,OFFSET,BIRTH,DEATH,RWKSF,XT,YT,ZT,XH,YH,ZH,FRIC,WVEL,MASS,V0, SOFT,SSID,N1,N2,N3,N4)
        self._free_rigidwall_id(ID)
        self.rigidwalls[ID] = rigidwall
        return rigidwall
    
    def CreateRigidwallGeometricFlatDisplay(self, NSID=0,NSIDEX=0,BOXID=0,BIRTH=0.0,DEATH=1.0E20,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,XHEV=0.0,YHEV=0.0,ZHEV=0.0,LENL=0.0,LENM=0.0): 
        self.maxRWID = self.maxRWID + 1
        rigidwall = KooRigidWallGeometricFlatDisplay(self.maxRWID, "", NSID,NSIDEX,BOXID,BIRTH,DEATH,XT,YT,ZT,XH,YH,ZH,FRIC,XHEV,YHEV,ZHEV,LENL,LENM)   # 이름 칸을 비워 넘긴다 — 예전엔 NSID 가 이름 자리로 밀렸다
        self.rigidwalls[self.maxRWID] = rigidwall
        return rigidwall
    
    def CreateRigidwallGeometricFlatDisplaywithID(self, ID=0, name = "",NSID=0,NSIDEX=0,BOXID=0,BIRTH=0.0,DEATH=1.0E20,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,XHEV=0.0,YHEV=0.0,ZHEV=0.0,LENL=0.0,LENM=0.0):
        if ID > self.maxRWID:
            self.maxRWID = ID
        rigidwall = KooRigidWallGeometricFlatDisplay(ID, name,NSID,NSIDEX,BOXID,BIRTH,DEATH,XT,YT,ZT,XH,YH,ZH,FRIC,XHEV,YHEV,ZHEV,LENL,LENM)
        self._free_rigidwall_id(ID)
        self.rigidwalls[ID] = rigidwall
        return rigidwall  

    def CreateBoundaryNonReflecting(self, ssid, ad=0.0, as_val=0.0):
        """비반사 경계 생성. solid 요소 외부면 Segment Set에 적용."""
        nr = KooBoundaryNonReflecting(ssid, ad, as_val)
        self.non_reflecting_boundaries.append(nr)
        return nr

    def CreateHourglass(self, HGID, IHQ=5, QM=0.1, IBQ="", Q1=1.5, Q2=0.06, QBVDC="QM", QW="QM"):
        hourglass = KooHourglass(HGID, IHQ, QM, IBQ, Q1, Q2, QBVDC, QW)
        self.hourglasses[HGID] = hourglass
        return hourglass

    def CreateInterfaceSpringbackLSDyna(self, PSID=1,NSHV=0,FTYPE=0,FTENSR=0,NTHHSV=0,RFLAG=0,INTSTRN=0, OPTC1="0", SLDO=0, NCYC="",FSPLIT=0,NGFLAG=0,CFLAG=0,HFLAG="",OPTC2="",DTWRT="",OPTC3="",NMWRT="",IVFLG=0):
        self.maxInterface = self.maxInterface + 1
        interface = KooInterfaceSpringbackLSDyna(self.maxInterface, PSID, NSHV, FTYPE, FTENSR, NTHHSV, RFLAG, INTSTRN, OPTC1, SLDO, NCYC, FSPLIT, NGFLAG, CFLAG, HFLAG, OPTC2, DTWRT, OPTC3, NMWRT, IVFLG)
        self.interfaces[self.maxInterface] = interface
        return interface

    def CreateDeformableToRigidAutomatic(self, swset, code, entno, relsw, paired,
                                          d2r_pids, r2d_pids, offset=0.0,
                                          time1=0.0, time2=1e20, time3=0.0,
                                          nrbf=0, ncsf=0, rwf=0, dtmax=0.0):
        """*DEFORMABLE_TO_RIGID_AUTOMATIC 카드 생성.

        time1/time2/time3/nrbf/ncsf/rwf/dtmax 는 예전에 리터럴로 박혀 있어
        시나리오에서 바꿀 수 없었다. 기본값을 그 리터럴과 동일하게 두었으므로
        인자를 주지 않으면 기존 덱과 바이트 동일하다.
        swset/code/relsw/paired 는 쌍 스위치 메커니즘이라 호출부가 고정으로 넘긴다.
        """
        d2r = KooDeformableToRigidAutomatic(
            swset, code, time1, time2, time3, entno, relsw, paired,
            nrbf, ncsf, rwf, dtmax, d2r_pids, r2d_pids, offset)
        self.d2r_automatics[swset] = d2r
        return d2r

    def SetAdditionalfromDyna(self, additionalKeyword):
        if additionalKeyword[0] == "*INTERFACE_SPRINGBACK_LSDYNA":            
            if len(additionalKeyword) == 2:
                firstLine = additionalKeyword[1]
                secondLine = ["", "", "", "", "", "", ""]
                thirdLine = ["", ""]
                fourthLine = ["", "", ""]
            elif len(additionalKeyword) == 3:
                firstLine = additionalKeyword[1]
                secondLine = additionalKeyword[2]
                thirdLine = ["", ""]
                fourthLine = ["", "", ""]
            elif len(additionalKeyword) == 4:
                firstLine = additionalKeyword[1]
                secondLine = additionalKeyword[2]
                thirdLine = additionalKeyword[3]                
                fourthLine = ["", "", ""]
            elif len(additionalKeyword) == 5:
                firstLine = additionalKeyword[1]
                secondLine = additionalKeyword[2]
                thirdLine  = additionalKeyword[3]
                fourthLine = additionalKeyword[4]
            
            PSID = KooDynaInt(firstLine[0], 0)
            if PSID == 0:
                TypeError("Invalid PSID")
            NSHV = KooDynaInt(firstLine[1], 0)
            FTYPE = KooDynaInt(firstLine[2], 0)            
            FTENSR = KooDynaInt(firstLine[4], 0)
            NTHHSV = KooDynaInt(firstLine[5], 0)
            RFLAG = KooDynaInt(firstLine[6], 0)
            INTSTRN = KooDynaInt(firstLine[7], 0)
            
            OPTC1= KooDynaString(secondLine[0], "")
            SLDO = KooDynaInt(secondLine[1], 0)
            NCYC = KooDynaInt(secondLine[2], "")
            FSPLIT = KooDynaInt(secondLine[3], 0)
            NGFLAG = KooDynaInt(secondLine[4], 0)
            CFLAG = KooDynaInt(secondLine[5], 0)
            HFLAG = KooDynaInt(secondLine[6], "")
            OPTC2 = KooDynaString(thirdLine[0], "")
            DTWRT = KooDynaString(thirdLine[1], "")
            OPTC3 = KooDynaString(fourthLine[0], "")
            NMWRT = KooDynaString(fourthLine[1], "")
            IVFLG = KooDynaString(fourthLine[2], 0)
            
            interface = self.CreateInterfaceSpringbackLSDyna(PSID, NSHV, FTYPE, FTENSR, NTHHSV, RFLAG, INTSTRN, OPTC1, SLDO, NCYC, FSPLIT, NGFLAG, CFLAG, HFLAG, OPTC2, DTWRT, OPTC3, NMWRT, IVFLG)
            return interface

        elif additionalKeyword[0] == "*HOURGLASS":
            firstLine = additionalKeyword[1] 
            HGID = KooDynaInt(firstLine[0])
            IHQ = KooDynaInt(firstLine[1],5)
            QM = KooDynaFloat(firstLine[2],0.1)
            IBQ = KooDynaInt(firstLine[3],"")
            Q1 = KooDynaFloat(firstLine[4],1.5)
            Q2 = KooDynaFloat(firstLine[5],0.06)
            QBVDC = KooDynaFloat(firstLine[6],"QM")
            QW = KooDynaFloat(firstLine[7],"QM")
            
            hourglass = self.CreateHourglass(HGID, IHQ, QM, IBQ, Q1, Q2, QBVDC, QW)         
            return hourglass        
        
        elif additionalKeyword[0] == "*RIGIDWALL_PLANAR":
            # 단순 *RIGIDWALL_PLANAR — Card 1: NSID/NSIDEX/BOXID/OFFSET/BIRTH/DEATH/RWKSF
            #                          Card 2: XT/YT/ZT/XH/YH/ZH/FRIC/WVEL
            # MOVING_FORCES 옵션 없음 → MASS=V0=SOFT=SSID=N1..N4=0으로 처리
            firstLine = additionalKeyword[1] if len(additionalKeyword) > 1 else []
            secondLine = additionalKeyword[2] if len(additionalKeyword) > 2 else []
            if len(firstLine) < 7:
                firstLine = list(firstLine) + [""] * (7 - len(firstLine))
            if len(secondLine) < 8:
                secondLine = list(secondLine) + [""] * (8 - len(secondLine))
            NSID = KooDynaInt(firstLine[0], 0)
            NSIDEX = KooDynaInt(firstLine[1], 0)
            BOXID = KooDynaInt(firstLine[2], 0)
            OFFSET = KooDynaFloat(firstLine[3], 0.0)
            BIRTH = KooDynaFloat(firstLine[4], 0.0)
            DEATH = KooDynaFloat(firstLine[5], 1.0e20)
            RWKSF = KooDynaFloat(firstLine[6], 1.0)
            XT = KooDynaFloat(secondLine[0], 0.0)
            YT = KooDynaFloat(secondLine[1], 0.0)
            ZT = KooDynaFloat(secondLine[2], 0.0)
            XH = KooDynaFloat(secondLine[3], 0.0)
            YH = KooDynaFloat(secondLine[4], 0.0)
            ZH = KooDynaFloat(secondLine[5], 0.0)
            FRIC = KooDynaFloat(secondLine[6], 0.0)
            WVEL = KooDynaFloat(secondLine[7], 0.0)
            rigidWall = self.CreateRigidwallPlanarMovingForces(
                NSID, NSIDEX, BOXID, OFFSET, BIRTH, DEATH, RWKSF,
                XT, YT, ZT, XH, YH, ZH, FRIC, WVEL,
                0.0, 0.0, 0, 0, 0, 0, 0, 0
            )
            rigidWall.kw = "*RIGIDWALL_PLANAR"   # 읽은 종류 그대로 쓴다(예전엔 MOVING_FORCES_ID MASS 0 으로 바꿨다)
            return rigidWall
        elif additionalKeyword[0] == "*RIGIDWALL_PLANAR_ID":
            # *RIGIDWALL_PLANAR_ID — ID/name 카드 + Card 1/2 (MOVING_FORCES 없음)
            zeroLine = additionalKeyword[1] if len(additionalKeyword) > 1 else [0]
            ID = KooDynaInt(zeroLine[0], 0)
            firstLine = additionalKeyword[2] if len(additionalKeyword) > 2 else []
            secondLine = additionalKeyword[3] if len(additionalKeyword) > 3 else []
            if len(firstLine) < 7:
                firstLine = list(firstLine) + [""] * (7 - len(firstLine))
            if len(secondLine) < 8:
                secondLine = list(secondLine) + [""] * (8 - len(secondLine))
            NSID = KooDynaInt(firstLine[0], 0)
            NSIDEX = KooDynaInt(firstLine[1], 0)
            BOXID = KooDynaInt(firstLine[2], 0)
            OFFSET = KooDynaFloat(firstLine[3], 0.0)
            BIRTH = KooDynaFloat(firstLine[4], 0.0)
            DEATH = KooDynaFloat(firstLine[5], 1.0e20)
            RWKSF = KooDynaFloat(firstLine[6], 1.0)
            XT = KooDynaFloat(secondLine[0], 0.0)
            YT = KooDynaFloat(secondLine[1], 0.0)
            ZT = KooDynaFloat(secondLine[2], 0.0)
            XH = KooDynaFloat(secondLine[3], 0.0)
            YH = KooDynaFloat(secondLine[4], 0.0)
            ZH = KooDynaFloat(secondLine[5], 0.0)
            FRIC = KooDynaFloat(secondLine[6], 0.0)
            WVEL = KooDynaFloat(secondLine[7], 0.0)
            rigidWall = self.CreateRigidwallPlanarMovingForceswithID(
                ID, NSID, NSIDEX, BOXID, OFFSET, BIRTH, DEATH, RWKSF,
                XT, YT, ZT, XH, YH, ZH, FRIC, WVEL,
                0.0, 0.0, 0, 0, 0, 0, 0, 0
            )
            rigidWall.kw = "*RIGIDWALL_PLANAR_ID"
            rigidWall.title = str(zeroLine[1]).strip() if len(zeroLine) > 1 else ""
            return rigidWall
        elif additionalKeyword[0] == "*RIGIDWALL_PLANAR_MOVING_FORCES":
            firstLine = additionalKeyword[1]
            secondLine = additionalKeyword[2]
            thirdLine = additionalKeyword[3]
            fourthLine = additionalKeyword[4]
            if len(firstLine)<7:
                firstLine += [""]*(7-len(firstLine))
            if len(secondLine)<8:
                secondLine += [""]*(8-len(secondLine))
            if len(thirdLine)<2:
                thirdLine += [""]*(2-len(thirdLine))
            if len(fourthLine)<6:
                fourthLine += [""]*(6-len(fourthLine))
                
            NSID = KooDynaInt(firstLine[0],0)
            NSIDEX = KooDynaInt(firstLine[1],0)
            BOXID = KooDynaInt(firstLine[2],0)
            OFFSET = KooDynaFloat(firstLine[3],0.0)
            BIRTH = KooDynaFloat(firstLine[4],0.0)
            DEATH = KooDynaFloat(firstLine[5],1.0e20)
            RWKSF = KooDynaFloat(firstLine[6],1.0)
            
            XT = KooDynaFloat(secondLine[0],0.0)            
            YT = KooDynaFloat(secondLine[1],0.0)
            ZT = KooDynaFloat(secondLine[2],0.0)
            XH = KooDynaFloat(secondLine[3],0.0)
            YH = KooDynaFloat(secondLine[4],0.0)
            ZH = KooDynaFloat(secondLine[5],0.0)
            FRIC = KooDynaFloat(secondLine[6],0.0)
            WVEL = KooDynaFloat(secondLine[7],0.0)

            MASS = KooDynaFloat(thirdLine[0],0.0)
            V0 = KooDynaFloat(thirdLine[1],0.0)
            SOFT = KooDynaInt(fourthLine[0],0)
            SSID = KooDynaInt(fourthLine[1],0)
            N1 = KooDynaInt(fourthLine[2],0)
            N2 = KooDynaInt(fourthLine[3],0)
            N3 = KooDynaInt(fourthLine[4],0)
            N4 = KooDynaInt(fourthLine[5],0)

            rigidWall = self.CreateRigidwallPlanarMovingForces(NSID, NSIDEX, BOXID,OFFSET,BIRTH,DEATH,RWKSF,XT,YT,ZT,XH,YH,ZH,FRIC,WVEL,MASS,V0, SOFT,SSID,N1,N2,N3,N4)    
            rigidWall.kw = "*RIGIDWALL_PLANAR_MOVING_FORCES"
             
            return rigidWall
        elif additionalKeyword[0] == "*RIGIDWALL_PLANAR_MOVING_FORCES_ID":
            zeroLine = additionalKeyword[1]
            ID = int(zeroLine[0])
            firstLine = additionalKeyword[2]            
            secondLine = additionalKeyword[3]           
            thirdLine = additionalKeyword[4]
            fourthLine = additionalKeyword[5]
            if len(firstLine)<7:
                firstLine += [""]*(7-len(firstLine))
            if len(secondLine)<8:
                secondLine += [""]*(8-len(secondLine))
            if len(thirdLine)<2:
                thirdLine += [""]*(2-len(thirdLine))
            if len(fourthLine)<6:
                fourthLine += [""]*(6-len(fourthLine))
                
            NSID = KooDynaInt(firstLine[0],0)
            NSIDEX = KooDynaInt(firstLine[1],0)
            BOXID = KooDynaInt(firstLine[2],0)
            OFFSET = KooDynaFloat(firstLine[3],0.0)
            BIRTH = KooDynaFloat(firstLine[4],0.0)
            DEATH = KooDynaFloat(firstLine[5],1.0e20)
            RWKSF = KooDynaFloat(firstLine[6],1.0)
            
            XT = KooDynaFloat(secondLine[0],0.0)            
            YT = KooDynaFloat(secondLine[1],0.0)
            ZT = KooDynaFloat(secondLine[2],0.0)
            XH = KooDynaFloat(secondLine[3],0.0)
            YH = KooDynaFloat(secondLine[4],0.0)
            ZH = KooDynaFloat(secondLine[5],0.0)
            FRIC = KooDynaFloat(secondLine[6],0.0)
            WVEL = KooDynaFloat(secondLine[7],0.0)

            MASS = KooDynaFloat(thirdLine[0],0.0)
            V0 = KooDynaFloat(thirdLine[1],0.0)
            SOFT = KooDynaInt(fourthLine[0],0)
            SSID = KooDynaInt(fourthLine[1],0)
            N1 = KooDynaInt(fourthLine[2],0)
            N2 = KooDynaInt(fourthLine[3],0)
            N3 = KooDynaInt(fourthLine[4],0)
            N4 = KooDynaInt(fourthLine[5],0)
            rigidWall = self.CreateRigidwallPlanarMovingForceswithID(ID,NSID, NSIDEX, BOXID,OFFSET,BIRTH,DEATH,RWKSF,XT,YT,ZT,XH,YH,ZH,FRIC,WVEL,MASS,V0, SOFT,SSID,N1,N2,N3,N4)    
            rigidWall.kw = "*RIGIDWALL_PLANAR_MOVING_FORCES_ID"
            rigidWall.title = str(zeroLine[1]).strip() if len(zeroLine) > 1 else ""
            return rigidWall
        elif additionalKeyword[0] in ("*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY", "*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID"):
            # R16 카드 1 = NSID·NSIDEX·BOXID·BIRTH·DEATH(OFFSET 칸 없음) — 예전엔 OFFSET 이 있다고 읽어 BIRTH 자리에 DEATH(1E20)가 들어가
            # 벽이 켜지지 않았다. 번호 없는 꼴은 DISPLAY 카드가 없으면 IndexError, DISPLAY 카드(PID·RO·E·PR)는 버렸다(누적 체인 묶음 W1)
            kw = additionalKeyword[0]
            cards = list(additionalKeyword[1:])
            ID, name = None, ""
            if kw.endswith("_ID"):
                zeroLine = cards.pop(0) if cards else ["0"]
                ID = KooDynaInt(zeroLine[0], 0)
                name = str(zeroLine[1]).strip() if len(zeroLine) > 1 else ""
            card = lambda c, w: (list(cards[c]) if c < len(cards) else []) + [""] * w
            c1, c2, c3 = card(0, 5), card(1, 7), card(2, 5)
            NSID, NSIDEX, BOXID = KooDynaInt(c1[0], 0), KooDynaInt(c1[1], 0), KooDynaInt(c1[2], 0)
            BIRTH, DEATH = KooDynaFloat(c1[3], 0.0), KooDynaFloat(c1[4], 1.0e20)
            XT, YT, ZT, XH, YH, ZH, FRIC = (KooDynaFloat(c2[q], 0.0) for q in range(7))
            XHEV, YHEV, ZHEV, LENL, LENM = (KooDynaFloat(c3[q], 0.0) for q in range(5))
            if ID is None:
                rigidWall = self.CreateRigidwallGeometricFlatDisplay(NSID, NSIDEX, BOXID, BIRTH, DEATH, XT, YT, ZT, XH, YH, ZH, FRIC,
                                                                     XHEV, YHEV, ZHEV, LENL, LENM)
            else:
                rigidWall = self.CreateRigidwallGeometricFlatDisplaywithID(ID, name, NSID, NSIDEX, BOXID, BIRTH, DEATH, XT, YT, ZT, XH, YH, ZH,
                                                                           FRIC, XHEV, YHEV, ZHEV, LENL, LENM)
            rigidWall.kw = kw
            if len(cards) > 3 and any(str(x).strip() for x in cards[3]):
                c4 = card(3, 4)
                rigidWall.display = (KooDynaInt(c4[0], 0), KooDynaFloat(c4[1], 0.0), KooDynaFloat(c4[2], 0.0), KooDynaFloat(c4[3], 0.0))
            return rigidWall
        elif additionalKeyword[0] == "*DEFORMABLE_TO_RIGID_AUTOMATIC":
            # Card 1: SWSET, CODE, TIME1, TIME2, TIME3, ENTNO, RELSW, PAIRED
            card1 = additionalKeyword[1]
            if len(card1) < 8:
                card1 += [""] * (8 - len(card1))
            swset = KooDynaInt(card1[0], 0)
            code = KooDynaInt(card1[1], 0)
            entno = KooDynaInt(card1[5], 0)
            relsw = KooDynaInt(card1[6], 0)
            paired = KooDynaInt(card1[7], 0)
            # Card 2: NRBF, NCSF, RWF, DTMAX, D2R, R2D, OFFSET
            card2 = additionalKeyword[2]
            if len(card2) < 7:
                card2 += [""] * (7 - len(card2))
            d2r_count = KooDynaInt(card2[4], 0)
            r2d_count = KooDynaInt(card2[5], 0)
            offset = KooDynaFloat(card2[6], 0.0)
            # Card 3: D2R PIDs
            d2r_pids = []
            card_idx = 3
            for j in range(d2r_count):
                if card_idx < len(additionalKeyword):
                    card3 = additionalKeyword[card_idx]
                    pid = KooDynaInt(card3[0], 0)
                    lrb = KooDynaInt(card3[1], 0) if len(card3) > 1 else 0
                    d2r_pids.append((pid, lrb))
                    card_idx += 1
            # Card 4: R2D PIDs
            r2d_pids = []
            for j in range(r2d_count):
                if card_idx < len(additionalKeyword):
                    card4 = additionalKeyword[card_idx]
                    pid = KooDynaInt(card4[0], 0)
                    r2d_pids.append(pid)
                    card_idx += 1
            d2r = self.CreateDeformableToRigidAutomatic(
                swset=swset, code=code, entno=entno, relsw=relsw, paired=paired,
                d2r_pids=d2r_pids, r2d_pids=r2d_pids, offset=offset)
            return d2r
        return None
            
        
    def WritetoDynaKeyword(self):        
        keyword = ""
        for key in self.rigidwalls:
            rigidwall = self.rigidwalls[key]
            keyword += rigidwall.WriteDynaKeyword()
        for key in self.hourglasses:
            hourglass = self.hourglasses[key]
            keyword += hourglass.WriteDynaKeyword()
        for key in self.interfaces:
            interface = self.interfaces[key]
            keyword += interface.WriteDynaKeyword()
        for key in self.d2r_automatics:
            keyword += self.d2r_automatics[key].WriteDynaKeyword()
        return keyword

    def WriteStreamDynaKeyword(self, stream):
        for key in self.rigidwalls:
            rigidwall = self.rigidwalls[key]
            rigidwall.WriteStreamDynaKeyword(stream)
        for key in self.hourglasses:
            hourglass = self.hourglasses[key]
            hourglass.WriteStreamDynaKeyword(stream)
        for nr in self.non_reflecting_boundaries:
            nr.WriteStreamDynaKeyword(stream)
        for key in self.interfaces:
            interface = self.interfaces[key]
            interface.WriteStreamDynaKeyword(stream)
        for key in self.d2r_automatics:
            self.d2r_automatics[key].WriteStreamDynaKeyword(stream)
