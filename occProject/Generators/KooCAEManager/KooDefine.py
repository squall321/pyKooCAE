from __future__ import annotations
from KooCAEManager.KooOperator import *

def _real10(v):
    """10칸 실수 칸 — >10.3f 가 값을 그대로 담으면 예전 출력 그대로, 아니면 10칸 안에서 값에 가장 가까운(같으면 짧은) 표기.
    🔴 *DEFINE_CURVE 머리(SFA·SFO·OFFA·OFFO)를 >10.3f 로만 써 SFO 1.0E-6 → 0.000 → LS-DYNA 가 0 을 기본값 1.0 으로 읽어
       커브가 10⁶ 배였다(1월부터). 0.0012 → 0.001, 1.0E6 → 11칸이라 다음 칸을 밀었다."""
    s = format(v, ">10.3f")
    if len(s) <= 10 and float(s) == v:
        return s
    cands = [format(v, f".{d}f") for d in range(10)] + [format(v, f".{p}e") for p in range(7)] + [repr(float(v))]
    cands = [c for c in cands if len(c) <= 10]
    return format(min(cands, key=lambda c: (abs(float(c) - v), len(c))), ">10")

def _curve_points(rows, lcid):
    """*DEFINE_CURVE 점 카드 → (A1 목록, O1 목록). 빈 칸은 기본값 0.0 이다(R16 점 카드 A1·O1 Default 0.0, Appendix V) —
    부록 V 대로면 빈 줄은 점 (0,0) 이다(실행 확인은 라이선스가 없어 못 함). 예전엔 float('') 로 죽었다(리뷰 G). 빈 줄은 개수를 알린다."""
    a1, o1, blank = [], [], 0
    for points in rows:
        x, y = str(points[0]).strip(), str(points[1]).strip()
        if not x and not y:
            blank += 1
        a1.append(float(x) if x else 0.0)
        o1.append(float(y) if y else 0.0)
    if blank:
        print(f"  Warning: DEFINE_CURVE {lcid} 의 빈 점 카드 {blank}개를 (0,0) 으로 읽었다 — R16 Appendix V"
              f"(A1·O1 기본값 0.0). 블록 끝 빈 줄이라면 지울 것")
    return a1, o1

 
class KooDefine:
    def __init__(self, lcid):
        self.lcid = lcid 
        self.lctype = None
        
    def WritetoDynaKeyword(self, startID):
        pass
    
    def WriteStreamDynaKeyword(self, stream, startID):
        pass

class KooDefineCoordinateSystem:
    def __init__(self, cid=0, XO=0.0, YO=0.0, ZO=0.0, XL=0.0, YL=0.0, ZL=0.0, CIDL=0,XP=0.0,YP=0.0,ZP=0.0):
        self.cid = cid
        self.XO = XO
        self.YO = YO
        self.ZO = ZO
        self.XL = XL
        self.YL = YL
        self.ZL = ZL
        self.CIDL = CIDL
        self.XP = XP
        self.YP = YP
        self.ZP = ZP
            
    
    def WritetoDynaKeyword(self, startID):
        keyword = "*DEFINE_COORDINATE_SYSTEM\n"
        cidStr = format(self.cid + startID, ">10")
        XOStr = format(self.XO, ">10.3f")
        YOStr = format(self.YO, ">10.3f")
        ZOStr = format(self.ZO, ">10.3f")
        XLStr = format(self.XL, ">10.3f")
        YLStr = format(self.YL, ">10.3f")
        ZLStr = format(self.ZL, ">10.3f")
        CIDLStr = format(self.CIDL, ">10")
        keyword += cidStr + XOStr + YOStr + ZOStr + XLStr + YLStr + ZLStr + CIDLStr + "\n"
        XPStr = format(self.XP, ">10.3f")
        YPStr = format(self.YP, ">10.3f")
        ZPStr = format(self.ZP, ">10.3f")
        keyword += XPStr + YPStr + ZPStr + "\n"        
        
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*DEFINE_COORDINATE_SYSTEM\n")
        cidStr = format(self.cid + startID, ">10")
        XOStr = format(self.XO, ">10.3f")
        YOStr = format(self.YO, ">10.3f")
        ZOStr = format(self.ZO, ">10.3f")
        XLStr = format(self.XL, ">10.3f")
        YLStr = format(self.YL, ">10.3f")
        ZLStr = format(self.ZL, ">10.3f")
        CIDLStr = format(self.CIDL, ">10")
        stream.write(cidStr + XOStr + YOStr + ZOStr + XLStr + YLStr + ZLStr + CIDLStr + "\n")
        XPStr = format(self.XP, ">10.3f")
        YPStr = format(self.YP, ">10.3f")
        ZPStr = format(self.ZP, ">10.3f")
        stream.write(XPStr + YPStr + ZPStr + "\n")
    
class KooDefineCoordinateSystemTitle(KooDefineCoordinateSystem):
    def __init__(self, cid=0, XO=0.0, YO=0.0, ZO=0.0, XL=0.0, YL=0.0, ZL=0.0, CIDL=0,XP=0.0,YP=0.0,ZP=0.0,name=""):
        super(KooDefineCoordinateSystemTitle,self).__init__(cid, XO, YO, ZO, XL, YL, ZL, CIDL, XP, YP, ZP)
        self.name = name
    
    def WritetoDynaKeyword(self, startID):
        keyword = "*DEFINE_COORDINATE_SYSTEM_TITLE\n"
        keyword += self.name + "\n"
        cidStr = format(self.cid + startID, ">10")
        XOStr = format(self.XO, ">10.3f")
        YOStr = format(self.YO, ">10.3f")
        ZOStr = format(self.ZO, ">10.3f")
        XLStr = format(self.XL, ">10.3f")
        YLStr = format(self.YL, ">10.3f")
        ZLStr = format(self.ZL, ">10.3f")
        CIDLStr = format(self.CIDL, ">10")
        keyword += cidStr + XOStr + YOStr + ZOStr + XLStr + YLStr + ZLStr + CIDLStr + "\n"
        XPStr = format(self.XP, ">10.3f")
        YPStr = format(self.YP, ">10.3f")
        ZPStr = format(self.ZP, ">10.3f")
        keyword += XPStr + YPStr + ZPStr + "\n"        
        return keyword

    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*DEFINE_COORDINATE_SYSTEM_TITLE\n")
        stream.write(self.name + "\n")
        cidStr = format(self.cid + startID, ">10")
        XOStr = format(self.XO, ">10.3f")
        YOStr = format(self.YO, ">10.3f")
        ZOStr = format(self.ZO, ">10.3f")
        XLStr = format(self.XL, ">10.3f")
        YLStr = format(self.YL, ">10.3f")
        ZLStr = format(self.ZL, ">10.3f")
        CIDLStr = format(self.CIDL, ">10")
        stream.write(cidStr + XOStr + YOStr + ZOStr + XLStr + YLStr + ZLStr + CIDLStr + "\n")
        XPStr = format(self.XP, ">10.3f")
        YPStr = format(self.YP, ">10.3f")
        ZPStr = format(self.ZP, ">10.3f")
        stream.write(XPStr + YPStr + ZPStr + "\n")
    

    
class KooDefineCurve(KooDefine):
    def __init__(self,LCID,SIDR=0,SFA=1.0,SFO=1.0,OFFA=0.0,OFFO=0.0,DATTYP=0,LCINT=0,A1=None,O1=None,name=""):
        super(KooDefineCurve,self).__init__(LCID)
        
        if name != "":
            self.name = name
            self.lctype = "DEFINE_CURVE_TITLE"
        else:
            self.name = ""
            self.lctype = "DEFINE_CURVE"
        
        
        self.sidr = SIDR
        self.sfa = SFA
        self.sfo = SFO
        self.offa = OFFA
        self.offo = OFFO
        self.dattyp = DATTYP
        self.lcint = LCINT
        if A1 is not None:
            self.a1 = A1
        else:
            self.a1 = []
        if O1 is not None:
            self.o1 = O1
        else:
            self.o1 = []
    
    def AddCurvePoint(self, a1Point, o1Point):
        self.a1.append(a1Point)
        self.o1.append(o1Point)
    
    def AddCurve(self, a1List, o1List):
        self.a1 = a1List
        self.o1 = o1List
        
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        if self.name != "":
            keyword += "*DEFINE_CURVE_TITLE\n"
            keyword += self.name + "\n"
        else:
            keyword += "*DEFINE_CURVE\n"
        idStr = format(self.lcid + startID, ">10")
        sidrStr = format(self.sidr, ">10")
        sfaStr = _real10(self.sfa)
        sfoStr = _real10(self.sfo)
        offaStr = _real10(self.offa)
        offoStr = _real10(self.offo)
        dattypStr = format(self.dattyp, ">10")
        lcintStr = format(self.lcint, ">10")
        
        keyword += idStr + sidrStr + sfaStr + sfoStr + offaStr + offoStr + dattypStr + lcintStr + "\n"
        for i in range(len(self.a1)):
            # 20 digit 
            #+1.0000000000000E+00
            a1Str = format(self.a1[i], ">20.13e")
            o1Str = format(self.o1[i], ">20.13e")
            keyword += a1Str + o1Str + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        if self.name != "":
            stream.write("*DEFINE_CURVE_TITLE\n")
            stream.write(self.name + "\n")
        else:
            stream.write("*DEFINE_CURVE\n")
        idStr = format(self.lcid + startID, ">10")
        sidrStr = format(self.sidr, ">10")
        sfaStr = _real10(self.sfa)
        sfoStr = _real10(self.sfo)
        offaStr = _real10(self.offa)
        offoStr = _real10(self.offo)
        dattypStr = format(self.dattyp, ">10")
        lcintStr = format(self.lcint, ">10")
        
        stream.write(idStr + sidrStr + sfaStr + sfoStr + offaStr + offoStr + dattypStr + lcintStr + "\n")
        for i in range(len(self.a1)):
            # 20 digit 
            #+1.0000000000000E+00
            a1Str = format(self.a1[i], ">20.13e")
            o1Str = format(self.o1[i], ">20.13e")
            stream.write(a1Str + o1Str + "\n")
    
class KooDefineManager:
    def __init__(self):
        self.maxid = 0 
        self.defines = {} 
        
        self.maxcid = 0 
        self.defineCoordinateSystems = {}
    
    def OffsetID(self, offsetid, offsetcid):
        for key in self.defines:
            define = self.defines[key]
            define.lcid += offsetid
        self.maxid += offsetid
        for key in self.defineCoordinateSystems:
            coord = self.defineCoordinateSystems[key]
            coord.cid += offsetcid
        self.maxcid += offsetcid

    def OverwritefromDefineManager(self, defineManager: KooDefineManager):
        self.maxid = max(self.maxid, defineManager.maxid)
        self.maxcid = max(self.maxcid, defineManager.maxcid)
        for key, value in defineManager.defines.items():
            self.defines[key] = value
        for key, value in defineManager.defineCoordinateSystems.items():
            self.defineCoordinateSystems[key] = value

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
           
    def CreateDefineCurve(self, SIDR=0,SFA=1.0,SFO=1.0,OFFA=0.0,OFFO=0.0,DATTYP=0,LCINT=0,A1=None,O1=None):
        self.maxid += 1
        define = KooDefineCurve(self.maxid,SIDR,SFA,SFO,OFFA,OFFO,DATTYP,LCINT,A1,O1)
        self.defines[self.maxid] = define
        return define
    
    def CreateDefineCurvewithID(self, LCID,SIDR=0,SFA=1.0,SFO=1.0,OFFA=0.0,OFFO=0.0,DATTYP=0,LCINT=0,A1=None,O1=None,name = ""):
        define = KooDefineCurve(LCID,SIDR,SFA,SFO,OFFA,OFFO,DATTYP,LCINT,A1,O1, name)
        self.defines[LCID] = define
        if LCID > self.maxid:
            self.maxid = LCID
        return define
    
    def CreateDefineCoordinateSystem(self, XO=0.0, YO=0.0, ZO=0.0, XL=0.0, YL=0.0, ZL=0.0, CIDL=0,XP=0.0,YP=0.0,ZP=0.0,name=""):
        self.maxcid += 1
        if name != "":
            define = KooDefineCoordinateSystemTitle(self.maxcid,XO,YO,ZO,XL,YL,ZL,CIDL,XP,YP,ZP,name)
        else:
            define = KooDefineCoordinateSystem(self.maxcid,XO,YO,ZO,XL,YL,ZL,CIDL,XP,YP,ZP)
        self.defineCoordinateSystems[self.maxcid] = define
        if self.maxcid > self.maxcid:
            self.maxcid = self.maxcid
        return define
    
    def CreateDefineCoordinateSystemwithID(self, CID,XO=0.0, YO=0.0, ZO=0.0, XL=0.0, YL=0.0, ZL=0.0, CIDL=0,XP=0.0,YP=0.0,ZP=0.0,name=""):
        if name != "":
            define = KooDefineCoordinateSystemTitle(CID,XO,YO,ZO,XL,YL,ZL,CIDL,XP,YP,ZP,name)
        else:
            define = KooDefineCoordinateSystem(CID,XO,YO,ZO,XL,YL,ZL,CIDL,XP,YP,ZP)
        self.defineCoordinateSystems[CID] = define
        if CID > self.maxcid:
            self.maxcid = CID
        return define
    
    def AddDefine(self, define):
        self.defines[define.lcid] = define
        if define.lcid > self.maxid:
            self.maxid = define.lcid        
        return define
    
    def AddDefinefromDyna(self, dynaDefine):
        if dynaDefine[0] == "*DEFINE_COORDINATE_SYSTEM_TITLE":
            parameters = dynaDefine[1] 
            name = parameters[0]
            firstLine = parameters[1]
            cid = int(firstLine[0])
            XO = KooDynaFloat(firstLine[1])
            YO = KooDynaFloat(firstLine[2])
            ZO = KooDynaFloat(firstLine[3])
            XL = KooDynaFloat(firstLine[4])
            YL = KooDynaFloat(firstLine[5])
            ZL = KooDynaFloat(firstLine[6])
            CIDL = KooDynaInt(firstLine[7])
            secondLine = parameters[1]
            XP = KooDynaFloat(secondLine[0])
            YP = KooDynaFloat(secondLine[1])
            ZP = KooDynaFloat(secondLine[2])
            define = self.CreateDefineCoordinateSystemwithID(cid,XO,YO,ZO,XL,YL,ZL,CIDL,XP,YP,ZP,name)
        if dynaDefine[0] == "*DEFINE_COORDINATE_SYSTEM":
            parameters = dynaDefine[1] 
            firstLine = parameters[0]
            cid = int(firstLine[0])
            XO = KooDynaFloat(firstLine[1])
            YO = KooDynaFloat(firstLine[2])
            ZO = KooDynaFloat(firstLine[3])
            XL = KooDynaFloat(firstLine[4])
            YL = KooDynaFloat(firstLine[5])
            ZL = KooDynaFloat(firstLine[6])
            CIDL = KooDynaInt(firstLine[7])
            secondLine = parameters[1]
            XP = KooDynaFloat(secondLine[0])
            YP = KooDynaFloat(secondLine[1])
            ZP = KooDynaFloat(secondLine[2])
            define = self.CreateDefineCoordinateSystemwithID(cid,XO,YO,ZO,XL,YL,ZL,CIDL,XP,YP,ZP)
        if dynaDefine[0] == "*DEFINE_CURVE":
            parameters = dynaDefine[1] 
            firstLine = parameters[0]
            LCID = int(firstLine[0])
            SIDR = KooDynaInt(firstLine[1])
            SFA = KooDynaFloat(firstLine[2])
            SFO = KooDynaFloat(firstLine[3])
            OFFA = KooDynaFloat(firstLine[4])
            OFFO = KooDynaFloat(firstLine[5])
            DATTYP = KooDynaInt(firstLine[6])
            LCINT = KooDynaInt(firstLine[7])
            A1, O1 = _curve_points(parameters[1:], LCID)
            define = self.CreateDefineCurvewithID(LCID,SIDR,SFA,SFO,OFFA,OFFO,DATTYP,LCINT,A1,O1)
        if dynaDefine[0] == "*DEFINE_CURVE_TITLE":
            parameters = dynaDefine[1] 
            name = parameters[0][0]
            firstLine = parameters[1]
            LCID = int(firstLine[0])            
            SIDR = KooDynaInt(firstLine[1])
            SFA = KooDynaFloat(firstLine[2])
            SFO = KooDynaFloat(firstLine[3])
            OFFA = KooDynaFloat(firstLine[4])
            OFFO = KooDynaFloat(firstLine[5])
            DATTYP = KooDynaInt(firstLine[6])
            LCINT = KooDynaInt(firstLine[7])
            A1, O1 = _curve_points(parameters[2:], LCID)
            define = self.CreateDefineCurvewithID(LCID,SIDR,SFA,SFO,OFFA,OFFO,DATTYP,LCINT,A1,O1,name)
                            
            
            
        
    
    def RemoveDefinebyID(self, lcid):
        del self.defines[lcid]
    
    def RemoveDefine(self, define):
        del self.defines[define.lcid]
        
    def RemoveAll(self):
        self.maxid = 0 
        self.defines = {}
    
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        for key in self.defines:
            keyword += self.defines[key].WritetoDynaKeyword(startID)
        return keyword
        
    def WriteStreamDynaKeyword(self, stream, startID):
        for key in self.defines:
            self.defines[key].WriteStreamDynaKeyword(stream, startID)
    