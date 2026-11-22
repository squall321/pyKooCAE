from __future__ import annotations
import math
import numpy as np

from KooCAEManager.KooOperator import KooDynaFloat, KooDynaInt, KooDynaString
from KooCAEManager.KooDefine import _real10   # SF 1.0E-4 를 >10.3f 로 쓰면 0.000 → LS-DYNA 기본값 1(하중 10⁴ 배)


def _e10(v):
    """하중 실수 칸(SF·AT) — '>10.3e' 가 값을 그대로 담으면 예전 출력 그대로(바이트 동일), 아니면 _real10(10칸 최대 정밀도).
    유효숫자 4자리를 넘는 SF(1.23456 → 1.235e+00)가 깎이던 것(남은 결함 A9)."""
    s = format(v, ">10.3e")
    try:
        return s if float(s) == float(v) else _real10(float(v))
    except (TypeError, ValueError, OverflowError):
        return s
    
class KooLoadBody:
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        self.lcid = lcid
        self.sf = sf
        self.lciddr = lciddr
        self.xc = xc
        self.yc = yc
        self.zc = zc
        self.cid = cid
    
    def WritetoDynaKeyword(self):
        keyword = ""
        keyword += format(self.lcid, ">10")
        keyword += _real10(self.sf)
        if self.lciddr == "":
            keyword += "          "
        else:
            keyword += format(self.lciddr, ">10")
        keyword += _real10(self.xc)
        keyword += _real10(self.yc)
        keyword += _real10(self.zc)
        keyword += format(self.cid, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write(format(self.lcid, ">10"))
        stream.write(_real10(self.sf))
        if self.lciddr == "":
            stream.write("          ")
        else:
            stream.write(format(self.lciddr, ">10"))
        stream.write(_real10(self.xc))
        stream.write(_real10(self.yc))
        stream.write(_real10(self.zc))
        stream.write(format(self.cid, ">10"))
        stream.write("\n")
            
class KooLoadBodyX(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyX,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_X\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_X\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyY(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyY,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_Y\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_Y\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyZ(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyZ,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_Z\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_Z\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyRX(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyRX,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_RX\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_RX\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyRY(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyRY,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_RY\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_RY\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyRZ(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyRZ,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_RZ\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_RZ\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyParts:
    """*LOAD_BODY_GENERALIZED_SET_PART — 특정 파트 셋에 base acceleration body load 적용.

    LS-DYNA R16 Vol I, 33-31~33-34 참조. `*LOAD_BODY_PARTS_<dir>`는 비정식
    가공 키워드라 input phase에서 reject되므로 정식 카드로 emit한다.
    `*LOAD_BODY_PARTS`는 deck당 1회 제약(33-25)이라 회로별 분리 시나리오
    부적합 → `*LOAD_BODY_GENERALIZED_SET_PART`로 emit해야 다중 part set 가능.

    카드:
        *LOAD_BODY_GENERALIZED_SET_PART
        $#  N1/SID        N2      LCID    DRLCID        XC        YC        ZC
                <psid>         0    <lcid>  <drlcid>       0.0       0.0       0.0
        $#      AX        AY        AZ       OMX       OMY       OMZ       CID    ANGTYP
                <ax>      <ay>      <az>       0.0       0.0       0.0         0         0

    direction별 (X/Y/Z) sf가 AX/AY/AZ에 들어가고 나머지는 0.
    drsf는 기존 호환 위해 인자로 받지만 generalized 카드는 동등 필드 없음 — DRLCID 사용.
    """
    def __init__(self, direction, psid, lcid, sf=1.0, drlcid=0, drsf=1.0):
        self.direction = direction.upper()  # 'X' | 'Y' | 'Z'
        self.psid = psid
        self.lcid = lcid
        self.sf = sf
        self.drlcid = drlcid
        self.drsf = drsf

    def WriteStreamDynaKeyword(self, stream):
        ax, ay, az = 0.0, 0.0, 0.0
        if self.direction == "X":
            ax = float(self.sf)
        elif self.direction == "Y":
            ay = float(self.sf)
        elif self.direction == "Z":
            az = float(self.sf)
        stream.write("*LOAD_BODY_GENERALIZED_SET_PART\n")
        stream.write("$#  N1/SID        N2      LCID    DRLCID        XC        YC        ZC\n")
        stream.write(format(int(self.psid), ">10"))
        stream.write(format(0, ">10"))
        stream.write(format(int(self.lcid), ">10"))
        stream.write(format(int(self.drlcid), ">10"))
        stream.write(format(0.0, ">10.4e"))
        stream.write(format(0.0, ">10.4e"))
        stream.write(format(0.0, ">10.4e"))
        stream.write("\n")
        stream.write("$#      AX        AY        AZ       OMX       OMY       OMZ       CID    ANGTYP\n")
        stream.write(format(ax, ">10.4e"))
        stream.write(format(ay, ">10.4e"))
        stream.write(format(az, ">10.4e"))
        stream.write(format(0.0, ">10.4e"))
        stream.write(format(0.0, ">10.4e"))
        stream.write(format(0.0, ">10.4e"))
        stream.write(format(0, ">10"))
        stream.write(format(0, ">10"))
        stream.write("\n")


class KooLoadThermalVariable:
    """*LOAD_THERMAL_VARIABLE — 노드 온도장 부여 (T1 균일온도 열응력, 구조 only).

    Vol I 33_LOAD.pdf p.33-168. T = TB + TS·f(t). NSID=0이면 전체 노드.
    LCID는 (time, factor) 곡선. 구조 explicit 해석에서 CTE와 결합해 열변형/응력 발생.
    Card1: NSID, NSIDEX, BOXID / Card2: TS, TB, LCID, TSE, TBE, LCIDE, LCIDR, LCIDEDR
    """
    def __init__(self, ts=1.0, tb=0.0, lcid=0, nsid=0, nsidex=0, boxid=0):
        self.ts = ts      # scale (T = tb + ts*f(t))
        self.tb = tb      # base temperature (t=0 기준온도)
        self.lcid = lcid  # (time, factor) 곡선
        self.nsid = nsid
        self.nsidex = nsidex
        self.boxid = boxid

    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_THERMAL_VARIABLE\n")
        stream.write("$#    nsid    nsidex     boxid\n")
        stream.write(format(int(self.nsid), ">10"))
        stream.write(format(int(self.nsidex), ">10"))
        stream.write(format(int(self.boxid), ">10"))
        stream.write("\n")
        stream.write("$#      ts        tb      lcid\n")
        stream.write(format(float(self.ts), ">10.3e"))
        stream.write(format(float(self.tb), ">10.3e"))
        stream.write(format(int(self.lcid), ">10"))
        stream.write("\n")


class KooLoadThermalD3plot:
    """*LOAD_THERMAL_D3PLOT — 선행 thermal d3plot 온도장 로드 (T2/T3 pass2).

    Vol I 33_LOAD.pdf p.33-159. 필드 없음 — 실행라인에 `T=<rootname>` 필요(Runner 처리).
    """
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_THERMAL_D3PLOT\n")


class KooLoadHeatGenerationSetSolid:
    """*LOAD_HEAT_GENERATION_SET_SOLID — 체적 발열원 (IC 칩, P2부터).

    Vol I 33_LOAD.pdf p.33-67. SID=요소 set ID. MULT=q'''[mW/mm³] (총W/체적).
    LCID=0이면 MULT 상수, >0이면 (time, q''') 곡선.
    """
    def __init__(self, sid=0, lcid=0, mult=0.0, wblcid=0, cblcid=0, tblcid=0):
        self.sid = sid
        self.lcid = lcid
        self.mult = mult
        self.wblcid = wblcid
        self.cblcid = cblcid
        self.tblcid = tblcid

    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_HEAT_GENERATION_SET_SOLID\n")
        stream.write("$#     sid      lcid      mult    wblcid    cblcid    tblcid\n")
        stream.write(format(int(self.sid), ">10"))
        stream.write(format(int(self.lcid), ">10"))
        stream.write(format(float(self.mult), ">10.3e"))
        stream.write(format(int(self.wblcid), ">10"))
        stream.write(format(int(self.cblcid), ">10"))
        stream.write(format(int(self.tblcid), ">10"))
        stream.write("\n")


class KooLoadBodyVector(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0, fx = 0.0, fy = 0.0, fz = 0.0): 
        super(KooLoadBodyVector,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
        self.fx = fx
        self.fy = fy
        self.fz = fz
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_VECTOR\n"
        keyword += super().WritetoDynaKeyword()
        keyword += _real10(self.fx)
        keyword += _real10(self.fy)
        keyword += _real10(self.fz)
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_VECTOR\n")
        super().WriteStreamDynaKeyword(stream)
        stream.write(_real10(self.fx))
        stream.write(_real10(self.fy))
        stream.write(_real10(self.fz))
        stream.write("\n")
    
class KooLoad:
    def __init__(self,lid, name):
         self.lid = lid
         self.name = name
         self.ltype = None
    
    def WritetoNastranKeyword(self, startID,loadcaseID=1):
        return ""     
    
    def WritetoDynaKeyword(self, startID):
        return ""

    def WriteStreamDynaKeyword(self, stream, startID):
        return ""
    
class KooLoadNodalPoint(KooLoad):
    def __init__(self, lid, name,lcid=None,cid = 0, fx = 0.0, fy = 0.0, fz = 0.0, node = 0):
        super(KooLoadNodalPoint,self).__init__(lid, name)
        self.ltype = "LOAD_NODE_POINT"
        self.lcid = lcid
        self.cid = cid
        self.fx = fx
        self.fy = fy
        self.fz = fz
        self.m1 = 0
        self.m2 = 0
        self.m3 = 0
        self.node = node
    
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        
        keyword += "*LOAD_NODE_POINT\n"
        keyword += "$#     nid       dof      lcid        sf       cid        m1        m2        m3\n"
        if self.fx != 0.0:
            keyword += format(self.node + startID, ">10")
            keyword += "         1"
            keyword += format(self.lcid, ">10")
            keyword += _real10(self.fx)
            keyword += format(self.cid, ">10")
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                keyword += format(self.m1, ">10")
                keyword += format(self.m2, ">10")
                keyword += format(self.m3, ">10")
            keyword += "\n"
        if self.fy != 0.0:
            keyword += format(self.node + startID, ">10")
            keyword += "         2"
            keyword += format(self.lcid, ">10")
            keyword += _real10(self.fy)
            keyword += format(self.cid, ">10")
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                keyword += format(self.m1, ">10")
                keyword += format(self.m2, ">10")
                keyword += format(self.m3, ">10")
            keyword += "\n"
        if self.fz != 0.0:
            keyword += format(self.node + startID, ">10")
            keyword += "         3"
            keyword += format(self.lcid, ">10")
            keyword += _real10(self.fz)
            keyword += format(self.cid, ">10")
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                keyword += format(self.m1, ">10")
                keyword += format(self.m2, ">10")
                keyword += format(self.m3, ">10")
            keyword += "\n"
            
        
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*LOAD_NODE_POINT\n")
        stream.write("$#     nid       dof      lcid        sf       cid        m1        m2        m3\n")
        if self.fx != 0.0:
            stream.write(format(self.node + startID, ">10"))
            stream.write("         1")
            stream.write(format(self.lcid, ">10"))
            stream.write(_real10(self.fx))
            stream.write(format(self.cid, ">10"))
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                stream.write(format(self.m1, ">10"))
                stream.write(format(self.m2, ">10"))
                stream.write(format(self.m3, ">10"))
            stream.write("\n")
        if self.fy != 0.0:
            stream.write(format(self.node + startID, ">10"))
            stream.write("         2")
            stream.write(format(self.lcid, ">10"))
            stream.write(_real10(self.fy))
            stream.write(format(self.cid, ">10"))
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                stream.write(format(self.m1, ">10"))
                stream.write(format(self.m2, ">10"))
                stream.write(format(self.m3, ">10"))
            stream.write("\n")
        if self.fz != 0.0:
            stream.write(format(self.node + startID, ">10"))
            stream.write("         3")
            stream.write(format(self.lcid, ">10"))
            stream.write(_real10(self.fz))
            stream.write(format(self.cid, ">10"))
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                stream.write(format(self.m1, ">10"))
                stream.write(format(self.m2, ">10"))
                stream.write(format(self.m3, ">10"))
            stream.write("\n")
    
    def WritetoNastranKeyword(self, startID, loadcaseID=1):
        return super().WritetoNastranKeyword(startID, loadcaseID) 
    
class KooLoadNodes(KooLoad):
    def __init__(self, lid, name, lcid = None,cid = 0, fx = 0.0, fy = 0.0, fz = 0.0, boundaries = [], nodeManager = None):
        super(KooLoadNodes,self).__init__(lid, name)
        self.ltype = "LOAD_NODES"
        self.lcid = lcid
        self.cid = cid
        self.fx = fx
        self.fy = fy
        self.fz = fz
        self.boundaries = boundaries
        self.nodeManager = nodeManager
        
        self.TransfertoNodalForce()
        
    def OffsetID(self, offsetNID):
        for boundary in self.boundaries:
            for i in range(len(boundary)):
                boundary[i] += offsetNID
    
    def calculate_tri_area(self,n1, n2, n3):
        # Calculate the area of the triangle
        area = 0.5 * np.linalg.norm(np.cross([n2.x - n1.x, n2.y - n1.y, n2.z - n1.z], [n3.x - n1.x, n3.y - n1.y, n3.z - n1.z]))
    
        return area
    
    def calculate_quad_area(self,n1, n2, n3, n4):
        # Calculate the diagonal vectors
        d1 = np.array([n3.x - n1.x, n3.y - n1.y, n3.z - n1.z])
        d2 = np.array([n4.x - n2.x, n4.y - n2.y, n4.z - n2.z])
    
        # Calculate the cross product of the two diagonal vectors
        cross_product = np.cross(d1, d2)
        
        # Calculate the area of the quadrilateral
        area = 0.5 * np.linalg.norm(cross_product)
    
        return area
  
    def TransfertoNodalForce(self):
        areaList = [] 
        nidtoForceRatio = {}
        totArea = 0.0
        self.nidList = []
        self.fxList = []
        self.fyList = []
        self.fzList = []
        
        for segment in self.boundaries:
            if len(segment) == 3:
                n1 = self.nodeManager.nodes[segment[0]]
                n2 = self.nodeManager.nodes[segment[1]]
                n3 = self.nodeManager.nodes[segment[2]]
                if segment[0] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[0]] = 0.0
                if segment[1] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[1]] = 0.0
                if segment[2] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[2]] = 0.0
                    
                area = self.calculate_tri_area(n1, n2, n3)
                if area < 0:
                    area = -area
                areaList.append(area)
                nidtoForceRatio[segment[0]] += area
                nidtoForceRatio[segment[1]] += area
                nidtoForceRatio[segment[2]] += area
                
                totArea += area
            elif len(segment) == 4:
                n1 = self.nodeManager.nodes[segment[0]]
                n2 = self.nodeManager.nodes[segment[1]]
                n3 = self.nodeManager.nodes[segment[2]]
                n4 = self.nodeManager.nodes[segment[3]]
                if segment[0] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[0]] = 0.0
                if segment[1] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[1]] = 0.0
                if segment[2] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[2]] = 0.0
                if segment[3] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[3]] = 0.0
               
                area = self.calculate_quad_area(n1, n2, n3, n4)
                if area < 0:
                    area = -area
                nidtoForceRatio[segment[0]] += area
                nidtoForceRatio[segment[1]] += area
                nidtoForceRatio[segment[2]] += area
                nidtoForceRatio[segment[3]] += area
                
                areaList.append(area)
                totArea += area   
        for nid in nidtoForceRatio.keys():
            nidtoForceRatio[nid] = nidtoForceRatio[nid] / totArea
        
        for nid in nidtoForceRatio.keys():
            #n = self.nodeManager.nodes[nid]
            self.nidList.append(nid)
            self.fxList.append(self.fx * nidtoForceRatio[nid])
            self.fyList.append(self.fy * nidtoForceRatio[nid])
            self.fzList.append(self.fz * nidtoForceRatio[nid])
            
            
    def WritetoNastranKeyword(self, startID,loadcaseID=1):        
        keyword = ""
        for i in range(len(self.nidList)):
            keyword += "FORCE   "
            keyword += format(loadcaseID, ">8")
            keyword += format(self.nidList[i], ">8")
            keyword += format(self.cid, ">8")
            fx = self.fxList[i]
            fy = self.fyList[i]
            fz = self.fzList[i]

            amp = math.sqrt(fx*fx + fy*fy + fz*fz)
            ampStr = format(amp, ">8.2e")
            if amp>0:
                ampStr = " "    + ampStr
            if amp == 0.0:
                ampStr = " 0.0e+00"
            ampStr = ampStr.replace("e", "")
            fxStr = format(fx/amp, ">8.2e")
            if fx>0:
                fxStr = " "    + fxStr
            if fx == 0.0:
                fxStr = " 0.00e+00"
            fxStr = fxStr.replace("e", "")
            fyStr = format(fy/amp, ">8.2e")
            if fy>0:
                fyStr = " "    + fyStr
            if fy == 0.0:
                fyStr = " 0.00e+00"
            fyStr = fyStr.replace("e", "")
            fzStr = format(fz/amp, ">8.2e")
            if fz>0:
                fzStr = " "    + fzStr
            if fz == 0.0:
                fzStr = " 0.00e+00"
            fzStr = fzStr.replace("e", "")
            keyword += ampStr
            keyword += fxStr
            keyword += fyStr
            keyword += fzStr
            
            
            keyword += "\n"
                     
        return keyword
    
    def WritetoDynaKeyword(self, startID):        
        keyword = ""
        keyword += "*LOAD_NODE_POINT\n"
        keyword += "$#     nid       dof      lcid        sf       cid        m1        m2        m3\n"
        for i in range(len(self.nidList)):
            nidStr = format(self.nidList[i] + startID, ">10")
            lcidStr = format(self.lcid, ">10")
            fx =self.fxList[i]
            fy =self.fyList[i]
            fz =self.fzList[i]
            cidStr = format(self.cid, ">10")
            if fx != 0.0:                
                keyword += nidStr
                keyword += "         1"
                keyword += lcidStr
                keyword += format(fx, ">10.3e")
                keyword += cidStr
                # m1 m2 m3 for follower force
                keyword += "         0         0         0\n"
            if fy != 0.0:
                keyword += nidStr
                keyword += "         2"
                keyword += lcidStr
                keyword += format(fy, ">10.3e")
                keyword += cidStr
                # m1 m2 m3 for follower force
                keyword += "         0         0         0\n"
            if fz != 0.0:
                keyword += nidStr
                keyword += "         3"
                keyword += lcidStr
                keyword += format(fz, ">10.3e")
                keyword += cidStr                
                # m1 m2 m3 for follower force
                keyword += "         0         0         0\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        for i in range(len(self.nidList)):
            nidStr = format(self.nidList[i] + startID, ">10")
            lcidStr = format(self.lcid, ">10")
            fx =self.fxList[i]
            fy =self.fyList[i]
            fz =self.fzList[i]
            cidStr = format(self.cid, ">10")
            if fx != 0.0:
                stream.write("*LOAD_NODE_POINT\n")
                stream.write("$#     nid       dof      lcid        sf       cid        m1        m2        m3\n")
                stream.write(nidStr)
                stream.write("         1")
                stream.write(lcidStr)
                stream.write(format(fx, ">10.3e"))
                stream.write(cidStr)
                # m1 m2 m3 for follower force
                stream.write("         0         0         0\n")
            if fy != 0.0:
                stream.write("*LOAD_NODE_POINT\n")
                stream.write("$#     nid       dof      lcid        sf       cid        m1        m2        m3\n")
                stream.write(nidStr)
                stream.write("         2")
                stream.write(lcidStr)
                stream.write(format(fy, ">10.3e"))
                stream.write(cidStr)
                # m1 m2 m3 for follower force
                stream.write("         0         0         0\n")
            if fz != 0.0:
                stream.write("*LOAD_NODE_POINT\n")
                stream.write("$#     nid       dof      lcid        sf       cid        m1        m2        m3\n")
                stream.write(nidStr)
                stream.write("         3")
                stream.write(lcidStr)
                stream.write(format(fz, ">10.3e"))
                stream.write(cidStr)               
                # m1 m2 m3 for follower force
                stream.write("         0         0         0\n")
        
class KooLoadSegment(KooLoad):
    def __init__(self, lid, name,lcid=None,SF=1.0,AT=0.0,N1=None,N2=None,N3=None,N4=None,N5=None,N6=None,N7=None,N8=None):        
        super(KooLoadSegment,self).__init__(lid, name)
        self.ltype = "LOAD_SEGMENT_ID"
        self.lcid = lcid
        self.sf = SF
        self.at = AT
        self.n1 = N1
        self.n2 = N2
        self.n3 = N3
        self.n4 = N4
        self.n5 = N5
        self.n6 = N6
        self.n7 = N7
        self.n8 = N8
        
    def SetNodes(self, n1=None, n2=None, n3=None, n4=None, n5=None, n6=None, n7=None, n8=None):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4
        self.n5 = n5
        self.n6 = n6
        self.n7 = n7
        self.n8 = n8
        
    def WritetoNastranKeyword(self, startID,loadcaseID=1):
        keyword = "" 
        
        keyword += "PLOAD   "
        sfstr = format(self.sf, ">8.2e")
        sfstr = sfstr.replace("e", "")
        if self.sf>0:
            sfstr = " " + sfstr
        keyword += sfstr
        keyword += format(self.n1.id, ">8")
        keyword += format(self.n2.id, ">8")
        keyword += format(self.n3.id, ">8")
        if self.n4 is not None:
            if self.n4.id != self.n3.id:
                keyword += format(self.n4.id, ">8")
        keyword += "\n"
        return keyword
        
        
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        keyword += "*LOAD_SEGMENT_ID\n"
        idStr = format(self.lid + startID, ">10")
        lcidStr = format(self.lcid, ">10")
        sfStr = format(self.sf, ">10.3e")
        atStr = format(self.at, ">10.3e")
        
        keyword += idStr + lcidStr + sfStr + atStr
        if self.n1 is not None:            
            n1Str = format(self.n1, ">10")
            keyword += n1Str
        if self.n2 is not None:
            n2Str = format(self.n2, ">10")
            keyword += n2Str
        if self.n3 is not None:
            n3Str = format(self.n3, ">10")
            keyword += n3Str
        if self.n4 is not None:
            n4Str = format(self.n4, ">10")
            keyword += n4Str
        if self.n5 is not None:
            n5Str = format(self.n5, ">10")
            keyword += n5Str
        if self.n6 is not None:
            n6Str = format(self.n6, ">10")
            keyword += "\n" + n6Str
        if self.n7 is not None:
            n7Str = format(self.n7, ">10")
            keyword += n7Str
        if self.n8 is not None:
            n8Str = format(self.n8, ">10")
            keyword += n8Str + "\n"
        
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        # *LOAD_SEGMENT_ID = ID 카드(ID·HEADING) + 카드 1(LCID SF AT N1~N5) + N5 ≠ 0 이면 카드 2(N6~N8). 예전 기록기는 ID 를 LCID 줄에
        # 붙여 칸이 밀렸고, 절점 객체·글자 SF 를 포맷하다 죽었다(남은 결함 A7)
        nid = lambda n: 0 if n is None else getattr(n, "id", n)
        stream.write("*LOAD_SEGMENT_ID\n")
        stream.write("$#      ID                                                                 HEADING\n")
        stream.write(format(self.lid + startID, ">10") + str(self.name or "").strip()[:70] + "\n")
        stream.write("$#    LCID        SF        AT        N1        N2        N3        N4        N5\n")
        n5 = nid(self.n5)
        stream.write(format(self.lcid, ">10") + _e10(self.sf) + _e10(self.at)
                     + "".join(format(nid(n), ">10") for n in (self.n1, self.n2, self.n3, self.n4))
                     + (format(n5, ">10") if n5 else "") + "\n")
        if n5:
            stream.write("$#      N6        N7        N8\n")
            stream.write("".join(format(nid(n), ">10") for n in (self.n6, self.n7, self.n8)) + "\n")


class _SegmentSetRef:
    """하중이 KMM 이 읽지 않는 세그먼트 셋(*SET_SEGMENT_GENERAL 등)을 가리킬 때 SSID 만 든 자리 표시.
    세트 원문은 미해석 원문 블록으로 그대로 나가므로 하중은 같은 SSID 로 쓰면 뜻이 같다(2026-11-03, 예전엔 KeyError)."""
    def __init__(self, sid):
        self.sid = sid
        self.segments = []


def _segment_set_or_ref(segmentSetManager, SSID, keyword):
    segmentSet = segmentSetManager.segmentSetList.get(SSID)
    if segmentSet is None:
        print(f"  {keyword}: SSID {SSID} 는 KMM 이 읽지 않는 세트(*SET_SEGMENT_GENERAL 등)라 SSID 만 그대로 쓴다 — 세트 원문은 그대로 나간다")
        segmentSet = _SegmentSetRef(SSID)
        # 이 번호를 예약한다 — KMM 이 새로 만드는 세그먼트 셋이 같은 번호를 받지 않게(리뷰 W 🟡8)
        segmentSetManager.maxid = max(getattr(segmentSetManager, "maxid", 0) or 0, SSID)
    return segmentSet


class KooLoadSegmentSet(KooLoad):
    def __init__(self, lid, name, segmentSet = None, lcid = 0, sf= 0.0, at = 0.0):
        super(KooLoadSegmentSet,self).__init__(lid, name)
        self.ltype = "LOAD_SEGMENT_SET_ID"
        self.segmentSet = segmentSet
        self.lcid = lcid
        self.sf = sf
        self.at = at
        
    def AddSegmentSet(self, segmentSet, lcid, sf, at):
        self.segmentSet = segmentSet
        self.lcid = lcid
        self.sf = sf
        self.at = at     
           
    def WritetoNastranKeyword(self, startID,loadcaseID=1):
        keyword = ""
        segments = self.segmentSet.segments
        sfstr = format(self.sf, ">8.2e")
        sfstr = sfstr.replace("e", "")    
        if self.sf>0:
            sfstr = " " + sfstr
        for segment in segments:
            keyword += "PLOAD   "
            keyword += format(loadcaseID, ">8")
            keyword += sfstr
            if len(segment) >= 3:
                for i in range(3):
                    keyword += format(segment[i], ">8")
            if len(segment) >= 4:
                if segment[3] != segment[2]:
                    keyword += format(segment[3], ">8")
            keyword += "\n"            
        
        return keyword
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        keyword += "*LOAD_SEGMENT_SET_ID\n"
        idStr = format(self.lid + startID, ">10")
        nameStr = format(self.name, ">70")        
        keyword += "$#     ID                                                                  NAME\n"
        keyword += idStr + nameStr + "\n"
        keyword += "$#     SID      LCID        SF        AT\n"        
        
         
        sidStr = format(self.segmentSet.sid, ">10")
        lcidStr = format(self.lcid, ">10")
        sfStr = format(self.sf, ">10.3e")
        atStr = format(self.at, ">10.3e")
        keyword += sidStr + lcidStr + sfStr + atStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*LOAD_SEGMENT_SET_ID\n")
        idStr = format(self.lid + startID, ">10")
        nameStr = format(self.name, ">70")        
        keyword = "$#     ID                                                                  NAME\n"
        keyword += idStr + nameStr + "\n"
        keyword += "$#     SID      LCID        SF        AT\n"        
        
        sidStr = format(self.segmentSet.sid, ">10")
        lcidStr = format(self.lcid, ">10")
        sfStr = _e10(self.sf)
        atStr = _e10(self.at)
        keyword += sidStr + lcidStr + sfStr + atStr + "\n"
        stream.write(keyword)
        
class KooLoadManager:    
    def __init__(self):
        self.maxid = 0 
        self.loads = {}
        self.bodyLoads = []

    def OffsetID(self, offsetLCID, offsetNID):
        for key in self.loads:
            load = self.loads[key]
            load.lcid += offsetLCID
            if type(load) is KooLoadNodalPoint:
                load.node += offsetNID
            elif type(load) is KooLoadNodes:                
                load.OffsetID(offsetNID)

    def OverwritefromLoadManager(self, loadManager : KooLoadManager):
        self.maxid = max(self.maxid, loadManager.maxid)
        for key, value in loadManager.loads.items():
            self.loads[key] = value
        for bodyLoad in loadManager.bodyLoads:
            self.bodyLoads.append(bodyLoad)

    def parse_whole(self, curString, chunkList):
        chunk_size = len(chunkList)
        chunks = []

        start = 0
        for i in range(0,chunk_size):
            end = start + chunkList[i]
            chunks.append(curString[start:end])            
            start = end

        for i in range(0,chunk_size):
            if '\n' in chunks[i]:
                chunks[i] = chunks[i].replace('\n','')
            
        return chunks 

    def CreateLoadBodyX(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyX(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyY(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyY(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyZ(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyZ(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyRX(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyRX(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyRY(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyRY(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyRZ(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyRZ(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyVector(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0, fx = 0.0, fy = 0.0, fz = 0.0):
        load = KooLoadBodyVector(lcid, sf, lciddr, xc, yc, zc, cid, fx, fy, fz)
        self.bodyLoads.append(load)
        return load

    def CreateLoadBodyParts(self, direction, psid, lcid, sf=1.0, drlcid=0, drsf=1.0):
        """*LOAD_BODY_GENERALIZED_SET_PART 카드 추가 (direction X/Y/Z → AX/AY/AZ)."""
        load = KooLoadBodyParts(direction, psid, lcid, sf, drlcid, drsf)
        self.bodyLoads.append(load)
        return load

    def CreateLoadThermalVariable(self, ts=1.0, tb=0.0, lcid=0, nsid=0, nsidex=0, boxid=0):
        """*LOAD_THERMAL_VARIABLE 추가 — T = tb + ts·f(t) 노드 온도장 (T1 열응력)."""
        load = KooLoadThermalVariable(ts, tb, lcid, nsid, nsidex, boxid)
        self.bodyLoads.append(load)
        return load

    def CreateLoadThermalD3plot(self):
        """*LOAD_THERMAL_D3PLOT 추가 — 선행 thermal d3plot 온도 로드 (pass2)."""
        load = KooLoadThermalD3plot()
        self.bodyLoads.append(load)
        return load

    def CreateLoadHeatGenerationSetSolid(self, sid=0, lcid=0, mult=0.0, wblcid=0, cblcid=0, tblcid=0):
        """*LOAD_HEAT_GENERATION_SET_SOLID 추가 — 체적 발열원 q'''[mW/mm³] (IC 칩)."""
        load = KooLoadHeatGenerationSetSolid(sid, lcid, mult, wblcid, cblcid, tblcid)
        self.bodyLoads.append(load)
        return load


    def CreateLoadNodalPoint(self, name, lcid=None, cid = 0, fx = 0.0, fy = 0.0, fz = 0.0, nodeid = 0):
        self.maxid += 1
        load = KooLoadNodalPoint(self.maxid,name,lcid,cid,fx,fy,fz,nodeid)
        load._auto_lid = True   # KMM 이 매긴 번호 — 덱 ID 하중과 겹치면 옮긴다(_StoreWithID)
        self.loads[self.maxid] = load
        return load
        
    def CreateLoadNodes(self, name, lcid=None, cid = 0, fx = 0.0, fy = 0.0, fz = 0.0, boundaries = [], nodeManager = None):
        self.maxid += 1
        load = KooLoadNodes(self.maxid, name, lcid, cid, fx, fy, fz, boundaries, nodeManager) 
        load._auto_lid = True   # KMM 이 매긴 번호 — 덱 ID 하중과 겹치면 옮긴다(_StoreWithID)
        self.loads[self.maxid] = load
        return load        
    
    def CreateLoadSegment(self, name, lcid=None, SF=1.0, AT=0.0, N1=None, N2=None, N3=None, N4=None, N5=None, N6=None, N7=None, N8=None):
        self.maxid += 1
        load = KooLoadSegment(self.maxid, name, lcid, SF, AT, N1, N2, N3, N4, N5, N6, N7, N8)
        load._auto_lid = True   # KMM 이 매긴 번호 — 덱 ID 하중과 겹치면 옮긴다(_StoreWithID)
        self.loads[self.maxid] = load
        return load
    
    def CreateLoadSegmentwithID(self, lid, name, lcid=None, SF=1.0, AT=0.0, N1=None, N2=None, N3=None, N4=None, N5=None, N6=None, N7=None, N8=None):
        load = KooLoadSegment(lid, name, lcid, SF, AT, N1, N2, N3, N4, N5, N6, N7, N8)
        return self._StoreWithID(lid, load)

    def _StoreWithID(self, lid, load):
        """덱 ID 하중을 담는다. 같은 열쇠에 하중이 있으면 덮지 않는다 — 예전엔 덮어 앞 하중이 rc 0 으로 빠졌다(*LOAD_NODE_POINT 가
        번호 1 을 받은 뒤 *LOAD_SEGMENT_SET_ID 1 등). 앞 하중이 KMM 이 번호를 매긴 것이면 그쪽을 새 번호로 옮기고, 덱 ID 끼리
        겹치면 새 하중을 새 열쇠에 둔다(쓰는 ID 는 덱 그대로)."""
        if lid in self.loads:
            key = max(self.maxid, max(self.loads)) + 1
            old = self.loads[lid]
            if getattr(old, "_auto_lid", False):
                old.lid = key
                self.loads[key] = old
                self.loads[lid] = load
            else:
                self.loads[key] = load
            self.maxid = max(self.maxid, key)
        else:
            self.loads[lid] = load
        if lid > self.maxid:
            self.maxid = lid
        return load

    def CreateLoadSegmentSet(self, name, sid, lcid=None, SF=1.0, AT=0.0):
        self.maxid += 1
        load = KooLoadSegmentSet(self.maxid, name, sid, lcid, SF, AT)
        load._auto_lid = True   # KMM 이 매긴 번호 — 덱 ID 하중과 겹치면 옮긴다(_StoreWithID)
        self.loads[self.maxid] = load
        return load

    def CreateLoadSegmentSetwithID(self, lid, name, sid = 0, lcid= 0, SF = 0.0, AT = 0.0):
        load = KooLoadSegmentSet(lid, name, sid, lcid, SF, AT)
        return self._StoreWithID(lid, load)

    def AddLoad(self, load):
        self.load[load.lid] = load
        if load.lid > self.maxid:
            self.maxid = load.lid
        return load

    def RemoveLoadbyID(self, lid):
        del self.loads[lid]

    def RemoveLoad(self, load):
        del self.loads[load.lid]
    
    def RemoveAll(self):
        self.maxid = 0 
        self.loads = {}
        
    def WritetoNastranKeyword(self, startID,loadcaseID=1):
        keyword = ""
        for key in self.loads:
            keyword += self.loads[key].WritetoNastranKeyword(startID,loadcaseID)
        return keyword
    
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        for key in self.loads:
            keyword += self.loads[key].WritetoDynaKeyword(startID)
        for load in self.bodyLoads:
            keyword += load.WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        for key in self.loads:
            self.loads[key].WriteStreamDynaKeyword(stream, startID)
        for load in self.bodyLoads:
            load.WriteStreamDynaKeyword(stream)
    
    def AddLoadfromDyna(self, dynaLoad, nodeManager,nodeSetManager,segmentSetManager):
        if dynaLoad[0] == "*LOAD_BODY_X" or dynaLoad[0] == "*LOAD_BODY_Y" or dynaLoad[0] == "*LOAD_BODY_Z" or dynaLoad[0] == "*LOAD_BODY_RX" or dynaLoad[0] == "*LOAD_BODY_RY" or dynaLoad[0] == "*LOAD_BODY_RZ" or dynaLoad[0] == "*LOAD_BODY_VECTOR":
            parameters = dynaLoad[1]
            lcid = KooDynaInt(parameters[0])
            sf = KooDynaFloat(parameters[1])
            lciddr = KooDynaInt(parameters[2],"")
            xc = KooDynaFloat(parameters[3])
            yc = KooDynaFloat(parameters[4])
            zc = KooDynaFloat(parameters[5])
            cid = KooDynaInt(parameters[6])
            if dynaLoad[0] == "*LOAD_BODY_X":
                load = self.CreateLoadBodyX(lcid, sf, lciddr, xc, yc, zc, cid) 
            elif dynaLoad[0] == "*LOAD_BODY_Y":
                load = self.CreateLoadBodyY(lcid, sf, lciddr, xc, yc, zc, cid)
            elif dynaLoad[0] == "*LOAD_BODY_Z":
                load = self.CreateLoadBodyZ(lcid, sf, lciddr, xc, yc, zc, cid)
            elif dynaLoad[0] == "*LOAD_BODY_RX":
                load = self.CreateLoadBodyRX(lcid, sf, lciddr, xc, yc, zc, cid)
            elif dynaLoad[0] == "*LOAD_BODY_RY":
                load = self.CreateLoadBodyRY(lcid, sf, lciddr, xc, yc, zc, cid)
            elif dynaLoad[0] == "*LOAD_BODY_RZ":
                load = self.CreateLoadBodyRZ(lcid, sf, lciddr, xc, yc, zc, cid) 
            elif dynaLoad[0] == "*LOAD_BODY_VECTOR": 
                parameters = dynaLoad[2] 
                fx = float(parameters[0])
                fy = float(parameters[1])
                fz = float(parameters[2])
                load = self.CreateLoadBodyVector(lcid, sf, lciddr, xc, yc, zc, cid, fx, fy, fz)
                
        if dynaLoad[0] == "*LOAD_NODE_POINT":
            parameters = dynaLoad[1]
            for i in range(len(parameters)):
                firstLine = parameters[i]
                if len(firstLine[0]) == 0:
                    firstLine[0] = "0"
                if len(firstLine[1]) == 0:
                    firstLine[1] = "0"
                if len(firstLine[2]) == 0:
                    firstLine[2] = "0"
                if len(firstLine[3]) == 0:
                    firstLine[3] = "0.0"
                if len(firstLine[4]) == 0:
                    firstLine[4] = "0"

                    
                    
                nid = KooDynaInt(firstLine[0])
                dof = KooDynaInt(firstLine[1])
                lcid = KooDynaInt(firstLine[2])
                sf = KooDynaFloat(firstLine[3])
                cid = KooDynaInt(firstLine[4])
                m1 = KooDynaFloat(firstLine[5],"")
                m2 = KooDynaFloat(firstLine[6],"")
                m3 = KooDynaFloat(firstLine[7],"")
                if dof == 1:
                    load = self.CreateLoadNodalPoint("",lcid,cid,sf,0.0,0.0,nid)                                                  
                elif dof == 2:
                    load = self.CreateLoadNodalPoint("",lcid,cid,0.0,sf,0.0,nid)
                elif dof == 3:
                    load = self.CreateLoadNodalPoint("",lcid,cid,0.0,0.0,sf,nid)     
                       
        if dynaLoad[0] == "*LOAD_SEGMENT" or dynaLoad[0] == "*LOAD_SEGMENT_ID":
            # 개체 = (_ID 면 ID 카드) + 카드 1(LCID SF AT N1~N5) + N5 ≠ 0 일 때만 카드 2(N6~N8). 예전엔 루프 변수를 늘려도 카드 2 를
            # 건너뛰지 못해 새 세그먼트로 읽었고, 빈 N 칸에서 int('') 로 죽었고, LCID·SF·AT 가 글자로 남아 쓸 때 죽었다(남은 결함 A7)
            rows = [r for r in dynaLoad[1] if any(str(x).strip() for x in r)]
            k, lid, name = 0, None, ""
            if dynaLoad[0] == "*LOAD_SEGMENT_ID" and rows:
                lid, name, k = KooDynaInt(rows[0][0]), str(rows[0][1]).strip() if len(rows[0]) > 1 else "", 1
            while k < len(rows):
                c1 = (list(rows[k]) + [""] * 8)[:8]
                k += 1
                ids = [KooDynaInt(x) for x in c1[3:8]]
                if ids[4] != 0:
                    c2 = (list(rows[k]) + [""] * 3)[:3] if k < len(rows) else ["", "", ""]
                    k += 1
                    ids += [KooDynaInt(x) for x in c2]
                else:
                    ids += [0, 0, 0]
                missing = [n for n in ids if n and n not in nodeManager.nodes]
                if missing:
                    print(f"🔴 {dynaLoad[0]}: 없는 절점 {missing[:4]} 을 가리켜 세그먼트 하중 하나를 옮기지 못했다")
                    from KooCAEManager.KooElement import note_content_loss
                    note_content_loss(f"{dynaLoad[0]} 없는 절점", 1)
                else:
                    N = [nodeManager.nodes[n] if n else None for n in ids]
                    lcid, sf, at = KooDynaInt(c1[0]), KooDynaFloat(c1[1], 1.0), KooDynaFloat(c1[2], 0.0)
                    if lid is None:
                        load = self.CreateLoadSegment("", lcid, sf, at, *N)
                    else:
                        load = self.CreateLoadSegmentwithID(lid, name, lcid, sf, at, *N)
                if lid is not None and k < len(rows):   # _ID 한 블록의 여러 개체 — ID 카드가 되풀이되는지 알 수 없다(A5 와 같다)
                    print(f"🔴 *LOAD_SEGMENT_ID 블록 하나에 카드 {len(rows)}줄 — ID 카드가 개체마다 되풀이되는지 알 수 없어 첫 개체만 "
                          f"읽었다(나머지 카드는 출력에서 빠진다). 개체마다 *LOAD_SEGMENT_ID 키워드 줄을 따로 쓰면 모두 읽는다")
                    from KooCAEManager.KooElement import note_content_loss
                    note_content_loss("*LOAD_SEGMENT_ID 한 블록의 여러 개체(첫 개체만 읽음)", 1)
                    break

        if dynaLoad[0] == "*LOAD_SEGMENT_SET":
            parameters = dynaLoad[1]
            curParameters = parameters[0]
            firstLine = curParameters
            # 빈 SF·AT 는 R16 기본값 1.0·0.0 — 예전엔 float('') 로 죽었다(KooRemapper 회귀 덱, 2026-11-09)
            SSID = KooDynaInt(firstLine[0])
            lcid = KooDynaInt(firstLine[1])
            sf = KooDynaFloat(firstLine[2], 1.0)
            at = KooDynaFloat(firstLine[3], 0.0)
            segmentSet = _segment_set_or_ref(segmentSetManager, SSID, "*LOAD_SEGMENT_SET")
            load = self.CreateLoadSegmentSet("",segmentSet,lcid,sf,at)                
            
        if dynaLoad[0] == "*LOAD_SEGMENT_SET_ID":
            parameters = dynaLoad[1]
            curParameters = parameters[0]
            firstLine = curParameters
            lid = int(firstLine[0])
            name = firstLine[1]
            curParameters = parameters[1]
            secondLine = curParameters
            SSID = KooDynaInt(secondLine[0])
            lcid = KooDynaInt(secondLine[1])
            sf = KooDynaFloat(secondLine[2], 1.0)
            at = KooDynaFloat(secondLine[3], 0.0)
            segmentSet = _segment_set_or_ref(segmentSetManager, SSID, "*LOAD_SEGMENT_SET_ID")
            load = self.CreateLoadSegmentSetwithID(lid,name,segmentSet,lcid,sf,at)            
            
        
    
    
    
            
        
        