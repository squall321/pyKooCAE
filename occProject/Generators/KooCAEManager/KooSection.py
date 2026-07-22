from __future__ import annotations

import math
if __name__ == "__main__":
    from KooDynaKeyword import *
else:
    from KooCAEManager.KooDynaKeyword import *

from KooCAEManager.KooOperator import *

class KooSection():
    def __init__(self, id, name):
        self.id = id 
        self.name = name 
        self.elform = 0

        self.dynaKeywordString = None
        self.ansysAPDLKeywordString = None
        
    def SetElform(self, elform):
        self.elform = elform

    def SetDynaKeyword(self, dynaKeywordString):
        self.dynaKeywordString = dynaKeywordString

    def SetAnsysAPDLKeyword(self, ansysKeywordString):
        self.ansysAPDLKeywordString = ansysKeywordString
        
class KooSectionBeam(KooSection):
    def __init__(self, id, name):
        super().__init__(id, name)
        self.elform = 1
        self.shrf = 1.0
        self.qririd = 2.0
        self.cst = 0
        self.scoor = 0.0
        self.nsm = 0.0
        self.naupd = 0

        self.options = [0.001,0.001,0.001,0.001,0.0,0.0]
        # 표준단면(CST≠0, card2=SECTION_NN 라벨) 등 수치 모델로 못 담는 카드의
        # 원문 보존(verbatim round-trip). raw_cards 가 있으면 GenerateDynaKeyword 가
        # 재구성 대신 원문 그대로 출력한다. (임무는 낙하각 재배치이지 단면 재정의가 아님)
        self.raw_cards = None      # [card1 원문, card2 원문, ...] (제목줄 제외)
        self.raw_keyword = None    # "*SECTION_BEAM" | "*SECTION_BEAM_TITLE"
        
    def SetWidth(self, width):
        self.options[0] = width
        self.options[1] = width
    
    def SetHeight(self, height):
        self.options[2] = height
        self.options[3] = height
    
    def AddtoDynaKeyword(self, keyword : SectionBeamTitle):
        keyword.AddSectionBeamTitle(self.id, self.name, self.elform, self.shrf, self.qririd, self.cst, self.scoor, self.nsm, self.naupd, self.options)
    
    def GenerateDynaKeyword(self):
        if getattr(self, 'raw_cards', None):
            # 표준단면(CST≠0, SECTION_NN 라벨) 등 — 원문 그대로 왕복(verbatim).
            # CST {:10d} 강제·card2 재구성 금지 (기존: CST 0 + card2 소실 → Error 10246).
            kw = self.raw_keyword if self.raw_keyword else "*SECTION_BEAM"
            keywordString = kw + "\n"
            if kw == "*SECTION_BEAM_TITLE":
                keywordString += "{0}\n".format(self.name)
            for idx, line in enumerate(self.raw_cards):
                if idx == 0:
                    # card1 SECID(첫 10칸)만 현재 id 로 재기입 — MERGE_K 등
                    # OffsetID 경로와의 정합 보장. id 미변경 시 원문과 바이트 동일.
                    keywordString += "{:>10d}".format(self.id) + line[10:] + "\n"
                else:
                    keywordString += line + "\n"
            self.SetDynaKeyword(keywordString)
            return keywordString
        keywordString = "*SECTION_BEAM_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        keywordString += "$$   SECID    ELFORM      SHRF    QRIRID       CST     SCORR       NSM     NAUPD\n"
        formatted_string = "{:10d}{:10d}{:10.3e}{:10.3e}{:10d}{:10.1f}{:10.1f}{:10d}\n".format(self.id, self.elform, self.shrf, self.qririd, self.cst, self.scoor, self.nsm, self.naupd)
        keywordString += formatted_string
        if self.elform == 1 or self.elform == 11:
            keywordString += "$$     TS1       TS2       TT1       TT2     NSLOC     NTLOC\n"             
            formatted_string = ""
            for opt in self.options:
                formatted_string += "{:10.3e}".format(opt)
            formatted_string += "\n"
            keywordString += formatted_string
        elif self.elform == 13:
            width = self.options[0]
            height = self.options[2]
            A = width * height 
            ISS = 1.0/12.0*width*height*height*height
            ITT = 1.0/12.0*height*width*width*width
            if width>=height:
                J=1.0/3.0*width*height*height*height
            else:
                J=1.0/3.0*height*width*width*width
            SA = 5.0/6.0*width*height
            IST= 0.0
            ITORM = 0.0

            keywordString += "$$       A       ISS       ITT         J        SA       IST     ITORM\b"
            formatted_string = ""
            formatted_string += "{:10.3e}".format(A)
            formatted_string += "{:10.3e}".format(ISS)
            formatted_string += "{:10.3e}".format(ITT)
            formatted_string += "{:10.3e}".format(J)
            formatted_string += "{:10.3e}".format(SA)
            formatted_string += "{:10.3e}".format(IST)
            formatted_string += "{:10.3e}".format(ITORM)
            formatted_string += "\n"
            keywordString += formatted_string
            
             
        self.SetDynaKeyword(keywordString)
        return keywordString               
    
    def GenerateAnsysAPDLKeyword(self,mid):
        keywordString = ""
        print("Beam Section is not supported in Ansys APDL format")
        return keywordString

class KooSectionShell(KooSection):
    def __init__(self, id, name):
        super().__init__(id, name)      

        self.elform = -16
        self.shrf = 1.0
        self.nip = 2
        self.propt = 0.0
        self.qrIrid = 0.0
        self.icomp = 0
        self.setyp = 1

        self.T1 = 0.0
        self.T2 = 0.0
        self.T3 = 0.0
        self.T4 = 0.0

        self.nloc = 0.0
        self.marea = 0.0
        self.idof = 0.0
        self.edgset = ""

    def SetThickness(self, thickness):
        self.T1 = thickness
        self.T2 = thickness
        self.T3 = thickness
        self.T4 = thickness

    def SetEachThickness(self, t1, t2, t3, t4):
        self.T1 = t1
        self.T2 = t2
        self.T3 = t3
        self.T4 = t4
    
    def SetElform(self, elform):
        self.elform = elform

    def AddtoDynaKeyword(self, keyword : SectionShellTitle):
        keyword.AddSectionShellTitle(self.id, self.name, self.elform, self.shrf, self.nip, self.propt, self.qrIrid, self.icomp, self.setyp, self.T1, self.T2, self.T3, self.T4, self.nloc, self.marea, self.idof, self.edgset)

    def GenerateDynaKeyword(self):
        keywordString = "*SECTION_SHELL_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        formatted_string = "{:10d}{:10d}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10d}{:10d}\n".format(self.id, self.elform, self.shrf, self.nip, self.propt, self.qrIrid, self.icomp, self.setyp)
        keywordString += formatted_string
        formatted_string = "{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10}\n".format(self.T1, self.T2, self.T3, self.T4,self.nloc,self.marea,self.idof,self.edgset)
        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString
    
    def GenerateAnsysAPDLKeyword(self,mid):
        keywordString = "sectype,{0}, SHELL,, SECTION_{1}\n".format(self.id, self.id)
        keywordString += "secdata,{0},{1},{2},{3}\n".format(self.T1,mid,"0.0","3")
        keywordString += "secoffset,MID\n"        
        return keywordString

    
class KooSectionSolid(KooSection):
    def __init__(self,id,name):
        super().__init__(id, name)
        self.elform = 1
        self.aet = ""
        self.cohoff = ""
        self.gaskett = ""
    
    def SetElform(self, elform, aet = "", cohoff = "", gaskett = ""):
        self.elform = elform
        self.aet = aet
        self.cohoff = cohoff
        self.gaskett = gaskett
        
    def AddtoDynaKeyword(self, keyword : SectionSolidTitle):
        keyword.AddSectionSolidTitle(self.id, self.name, self.elform, self.aet, self.cohoff, self.gaskett)

    def GenerateDynaKeyword(self):
        keywordString = "*SECTION_SOLID_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        formatted_string = "{:10d}{:10d}".format(self.id, self.elform)        
        keywordString += formatted_string
        if type(self.aet) == int:
            formatted_string = "{:10d}".format(self.aet)
            keywordString += formatted_string
        else:
            keywordString += "          "
        keywordString += "          "
        keywordString += "          "
        keywordString += "          "
        
        if type(self.cohoff) == float:
            formatted_string = "{:10.3e}".format(self.cohoff)
            keywordString += formatted_string
        else:
            keywordString += "          "
        if type(self.gaskett) == float:
            formatted_string = "{:10.3e}".format(self.gaskett)
            keywordString += formatted_string
        else:
            keywordString += "          "
        keywordString += "\n"
        self.SetDynaKeyword(keywordString)
        return keywordString 
   

class KooSectionSolidPeri(KooSection):
    def __init__(self, id, name):
        super().__init__(id, name)
        self.elform = 48
        self.dr = 1.01
        self.ptype = 1
        
    def SetElform(self, elform, dr = 1.01, ptype = 1):
        self.elform = elform
        self.dr = dr
        self.ptype = ptype
    
    def AddtoDynaKeyword(self, keyword : SectionSolidPeriTitle):
        keyword.AddSectionSolidPeriTitle(self.id, self.name, self.elform, self.dr, self.ptype)
        
    def GenerateDynaKeyword(self):
        keywordString = "*SECTION_SOLID_PERI_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        formatted_string = "{:10d}{:10d}\n".format(self.id, self.elform) 
        keywordString += formatted_string           
        formatted_string = "{:10.3e}{:10d}\n".format(self.dr, self.ptype) 
        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString
    
class KooSectionIGASolid(KooSection):
    def __init__(self, id, name, ir=0):
        super().__init__(id, name)
        self.elform = 0  # IGA는 항상 0
        self.ir = ir  # Integration rule (0=reduced Gauss, 1=Full Gauss)

    def SetIR(self, ir):
        self.ir = ir

    def GenerateDynaKeyword(self):
        keywordString = "*SECTION_IGA_SOLID\n"
        # 10 digit for each value
        formatted_string = "{:10d}{:10d}{:10d}\n".format(self.id, self.elform, self.ir)
        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString

    def WriteStreamDynaKeyword(self, stream):
        stream.write(self.GenerateDynaKeyword())

class KooSectionTShell(KooSection):
    def __init__(self, id, name):
        super().__init__(id, name)
        self.elform = 1
        self.shrf = 1.0
        self.nip = 2
        self.propt = 1
        self.qr = 0.0
        self.icomp = 0
        self.tshear = 0
        self.bList = []
        
    def SetElform(self, elform):
        self.elform = elform
    
    def SetShrf(self, shrf):
        self.shrf = shrf
        
    def SetNip(self, nip):
        self.nip = nip
        
    def SetPropt(self, propt):
        self.propt = propt
        
    def SetQr(self, qr):
        self.qr = qr
        
    def SetIcomp(self, icomp):
        self.icomp = icomp
        
    def SetTshear(self, tshear):
        self.tshear = tshear
        
    def AddB(self, b):
        self.bList.append(b)
        
    def AddBList(self, bList):
        self.bList = bList
    
    def AddtoDynaKeyword(self, keyword : SectionTShellTitle):
        keyword.AddSectionTShellTitle(self.name, self.id, self.elform, self.shrf, self.nip, self.propt, self.qr, self.icomp, self.tshear, self.bList)        

    def GenerateDynaKeyword(self):
        keywordString = "*SECTION_TSHELL_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        formatted_string = "{:10d}{:10d}{:10.3e}{:10d}{:10d}{:10.3e}{:10d}{:10d}\n".format(self.id, self.elform, self.shrf, self.nip, self.propt, self.qr, self.icomp, self.tshear)
        keywordString += formatted_string
        i = 0 
        for b in self.bList:
            formatted_string = "{:10.3e}".format(b)
            keywordString += formatted_string
            i = i + 1
            if i % 8 == 0:
                keywordString += "\n"
        if i % 8 != 0:
            keywordString += "\n"
        self.SetDynaKeyword(keywordString)
        return keywordString           

class KooSectionManager():
    def __init__(self):
        self.maxid = 0
        self.sections = {}

    def OffsetID(self, offsetID):
        for key in self.sections:
            section = self.sections[key]
            section.id += offsetID
        self.maxid += offsetID

    def OverwritefromSectionManager(self, sectionManager: KooSectionManager):
        self.maxid = max(self.maxid, sectionManager.maxid)
        for key, value in sectionManager.sections.items():
            self.sections[key] = value

    def AddSection(self, section):
        if section.id in self.sections:
            print("Section ID is already used. ID is reassigned.")
            section.id = self.maxid + 1

        if section.id > self.maxid:
            self.maxid = section.id
        elif section.id == 0:
            self.maxid += 1
            section.id = self.maxid

        self.sections[section.id] = section
        return section
        
    def FindSectionfromID(self, id):
        if id not in self.sections:
            return None
        return self.sections[id]

    def CreateBeamSection(self, name, elform = 1):
        sec = KooSectionBeam(0, name)
        sec.SetElform(elform)
        self.AddSection(sec)
        return sec

    def CreateShellSection(self, name, thickness, elform = -16):
        sec = KooSectionShell(0, name)
        sec.SetThickness(thickness)
        sec.SetElform(elform)
        self.AddSection(sec)
        return sec
    
    def CreateShellSectionEachThickness(self, name, t1, t2, t3, t4, elform = -16):
        sec = KooSectionShell(0, name)
        sec.SetEachThickness(t1, t2, t3, t4)
        sec.SetElform(elform)
        self.AddSection(sec)
        return sec

    def CreateSolidSection(self, name, elform = 1):
        sec = KooSectionSolid(0, name)
        sec.SetElform(elform)
        self.AddSection(sec)
        return sec
    
    def CreateSolidSectionPeri(self, name, elform = 48, dr = 1.01, ptype = 1):
        sec = KooSectionSolidPeri(0, name)
        sec.SetElform(elform, dr, ptype)
        self.AddSection(sec)
        return sec
    
    def CreateTShellSection(self, name, elform = 1, shrf = 1.0, nip = 2, propt = 1, qr = 0.0, icomp = 0, tshear = 0):
        sec = KooSectionTShell(0, name)
        sec.SetElform(elform)
        sec.SetShrf(shrf)
        sec.SetNip(nip)
        sec.SetPropt(propt)
        sec.SetQr(qr)
        sec.SetIcomp(icomp)
        sec.SetTshear(tshear)
        self.AddSection(sec)
        return sec

    def CreateIGASection(self, name, ir=0):
        """
        IGA 전용 섹션 생성 및 자동 ID 할당

        Args:
            name: 섹션 이름
            ir: Integration rule (0=reduced Gauss, 1=Full Gauss)

        Returns:
            KooSectionIGASolid instance (ID 자동 할당됨)
        """
        sec = KooSectionIGASolid(0, name, ir)
        self.AddSection(sec)
        return sec
    
    @staticmethod
    def _beam_card2_is_label(card_slices):
        """card2 첫 필드가 수치가 아니면(표준단면 SECTION_NN 라벨 등) True."""
        first = str(card_slices[0]).strip() if len(card_slices) > 0 else ""
        if first == "":
            return False
        try:
            float(first)
            return False
        except ValueError:
            return True

    def AddSectionfromDyna(self, dynaSection):
        if dynaSection[0] == "*SECTION_BEAM":
            firstLine = dynaSection[1]
            curid = KooDynaInt(firstLine[0],0)
            if curid != 0:
                curname = "Section{0}".format(curid)
                sec = KooSectionBeam(curid, curname)
                self.AddSection(sec)
            else:
                curname = "NewSection"
                sec = self.CreateBeamSection(curname, 1)

            sec.elform = KooDynaInt(firstLine[1],1)
            sec.shrf = KooDynaFloat(firstLine[2],1.0)
            sec.qririd = KooDynaFloat(firstLine[3],2.0)
            sec.cst = KooDynaInt(firstLine[4],0)
            sec.scoor = KooDynaFloat(firstLine[5],0.0)
            sec.nsm = KooDynaFloat(firstLine[6],0.0)
            sec.naupd = KooDynaInt(firstLine[7],0)

            options = []
            _cards = dynaSection[2:]
            if _cards and (self._beam_card2_is_label(_cards[0]) or sec.elform not in (1, 11)):
                # 표준단면(CST≠0, card2=SECTION_NN 라벨) 또는 수치 모델 범위(1/11: TS치수)
                # 밖의 elform — 재구성 불가 → card1 포함 원문 그대로 보존(verbatim round-trip).
                # (기존: card2 소실 + CST '1.0'→0 재작성 → LS-DYNA Error 10246)
                sec.raw_keyword = "*SECTION_BEAM"
                sec.raw_cards = ["".join(str(v) for v in line).rstrip("\n") for line in dynaSection[1:]]
            elif sec.elform == 1 or sec.elform == 11:
                secondLine = dynaSection[2]
                for opt in secondLine:
                    options.append(KooDynaFloat(opt,0.0))
            sec.options = options
        if dynaSection[0] == "*SECTION_BEAM_TITLE":
            zeroLine = dynaSection[1]
            firstLine = dynaSection[2]
            curid = KooDynaInt(firstLine[0],0)
            if curid != 0:
                curname = zeroLine[0]
                sec = KooSectionBeam(curid, curname)
                self.AddSection(sec)
            else:
                curname = "NewSection"
                sec = self.CreateBeamSection(curname, 1)

            sec.elform = KooDynaInt(firstLine[1],1)
            sec.shrf = KooDynaFloat(firstLine[2],1.0)
            sec.qririd = KooDynaFloat(firstLine[3],2.0)
            sec.cst = KooDynaInt(firstLine[4],0)
            sec.scoor = KooDynaFloat(firstLine[5],0.0)
            sec.nsm = KooDynaFloat(firstLine[6],0.0)
            sec.naupd = KooDynaInt(firstLine[7],0)

            options = []
            _cards = dynaSection[3:]
            if _cards and (self._beam_card2_is_label(_cards[0]) or sec.elform not in (1, 11)):
                # 표준단면 등 — 제목줄 제외 card1 부터 원문 보존(verbatim round-trip)
                sec.raw_keyword = "*SECTION_BEAM_TITLE"
                sec.raw_cards = ["".join(str(v) for v in line).rstrip("\n") for line in dynaSection[2:]]
            elif sec.elform == 1 or sec.elform == 11:
                secondLine = dynaSection[3]
                for opt in secondLine:
                    options.append(KooDynaFloat(opt,0.0))
            sec.options = options
           
        if dynaSection[0] == "*SECTION_SHELL":
            firstLine = dynaSection[1]
            secondLine = dynaSection[2]
            curid = KooDynaInt(firstLine[0],0)
            if curid != 0:                
                curname = "Section{0}".format(curid)
                sec = KooSectionShell(curid, curname)
                self.AddSection(sec)                       
            else:
                curname = "NewSection"
                sec = self.CreateShellSection(curname, 0.0)
            
            sec.elform = KooDynaInt(firstLine[1],-16)
            sec.shrf = KooDynaFloat(firstLine[2],1.0)
            sec.nip = KooDynaInt(firstLine[3],2)
            sec.propt = KooDynaFloat(firstLine[4],0.0)
            sec.qrIrid = KooDynaFloat(firstLine[5],0.0)
            sec.icomp = KooDynaInt(firstLine[6],0)
            sec.setyp = KooDynaInt(firstLine[7],1)
            
            sec.T1 = KooDynaFloat(secondLine[0],0.0)
            sec.T2 = KooDynaFloat(secondLine[1],sec.T1)
            sec.T3 = KooDynaFloat(secondLine[2],sec.T1)
            sec.T4 = KooDynaFloat(secondLine[3],sec.T1)            
            sec.nloc = KooDynaFloat(secondLine[4],0.0)
            sec.marea = KooDynaFloat(secondLine[5],0.0)
            sec.idof = KooDynaFloat(secondLine[6],0.0)
            sec.edgset = secondLine[7]
            
            return sec
        elif dynaSection[0] == "*SECTION_SHELL_TITLE":
            zeroLine = dynaSection[1]
            firstLine = dynaSection[2]
            secondLine = dynaSection[3]
            curid = KooDynaInt(firstLine[0],0)
            if curid != 0:
                curname = zeroLine[0]
                sec = KooSectionShell(curid, curname)
                self.AddSection(sec)
            else:
                curname = "NewSection"
                sec = self.CreateShellSection(curname, 0.0)
                                   
            sec.elform = KooDynaInt(firstLine[1],-16)
            sec.shrf = KooDynaFloat(firstLine[2],1.0)
            sec.nip = KooDynaInt(firstLine[3],2)
            sec.propt = KooDynaFloat(firstLine[4],0.0)
            sec.qrIrid = KooDynaFloat(firstLine[5],0.0)
            sec.icomp = KooDynaInt(firstLine[6],0)
            sec.setyp = KooDynaInt(firstLine[7],1)
            
            sec.T1 = KooDynaFloat(secondLine[0],0.0)
            sec.T2 = KooDynaFloat(secondLine[1],sec.T1)
            sec.T3 = KooDynaFloat(secondLine[2],sec.T1)
            sec.T4 = KooDynaFloat(secondLine[3],sec.T1)            
            sec.nloc = KooDynaFloat(secondLine[4],0.0)
            sec.marea = KooDynaFloat(secondLine[5],0.0)
            sec.idof = KooDynaFloat(secondLine[6],0.0)
            sec.edgset = secondLine[7]
            
            return sec
        elif dynaSection[0] == "*SECTION_SOLID":
            firstLine = dynaSection[1]
            curid = KooDynaInt(firstLine[0],0)
            if curid != 0:                
                curname = "Section{0}".format(curid)
                sec = KooSectionSolid(curid, curname)
                self.AddSection(sec)
            else:
                sec = self.CreateSolidSection("NewSolidSection")
            
            sec.elform = KooDynaInt(firstLine[1],1)
            sec.aet = KooDynaInt(firstLine[2],0)
            sec.cohoff = KooDynaFloat(firstLine[3],0.0)
            sec.gaskett = KooDynaFloat(firstLine[4],0.0)
           
            return sec
        elif dynaSection[0] == "*SECTION_SOLID_TITLE":
            zeroLine = dynaSection[1]
            firstLine = dynaSection[2]
            curid = KooDynaInt(firstLine[0],0)
            if curid != 0:
                curname = zeroLine[0]
                sec = KooSectionSolid(curid, curname)
                self.AddSection(sec)
            else:
                sec = self.CreateSolidSection("NewSolidSection")                
                                    
            sec.elform = KooDynaInt(firstLine[1],1)
            sec.aet = KooDynaInt(firstLine[2],0)
            sec.cohoff = KooDynaFloat(firstLine[3],0.0)
            sec.gaskett = KooDynaFloat(firstLine[4],0.0)
            
            return sec
        elif dynaSection[0] == "*SECTION_SOLID_PERI":
            firstLine = dynaSection[1]
            secondLine = dynaSection[2]
            curid = KooDynaInt(firstLine[0],0)
            if curid != 0:
                curname = "SectionPeri{0}".format(curid)                        
                sec = KooSectionSolidPeri(curid, curname)            
                self.AddSection(sec)
            else:
                sec = self.CreateSolidSectionPeri("NewSolidPeriSection")                
                
            sec.elform = KooDynaInt(firstLine[1],48)
            sec.dr = KooDynaFloat(secondLine[0],1.01)
            sec.ptype = KooDynaInt(secondLine[1],1)
            
        elif dynaSection[0] == "*SECTION_SOLID_PERI_TITLE":
            firstLine = dynaSection[2]
            secondLine = dynaSection[3]
            curid = KooDynaInt(firstLine[0],0)
            if curid != 0:
                curname = dynaSection[1][0]
                sec = KooSectionSolidPeri(curid, curname)            
                self.AddSection(sec)
            else:
                sec = self.CreateSolidSectionPeri("NewSolidPeriSection")                        
            sec.elform = KooDynaInt(firstLine[1],48)
            sec.dr = KooDynaFloat(secondLine[0],1.01)
            sec.ptype = KooDynaInt(secondLine[1],1)
        
        elif dynaSection[0] == "*SECTION_TSHELL":
            firstLine = dynaSection[1]
            curid = KooDynaInt(firstLine[0],0)
            elform = KooDynaInt(firstLine[1],1)
            shrf = KooDynaFloat(firstLine[2],1.0)
            nip = KooDynaInt(firstLine[3],2)
            qr = KooDynaFloat(firstLine[4],0.0)
            icomp = KooDynaInt(firstLine[5],0)
            tshear = KooDynaInt(firstLine[6],0)
            
            if curid != 0:
                curname = "Section{0}".format(curid)
                sec = KooSectionTShell(curid, curname)
                self.AddSection(sec)
            else:
                curname = "NewSection"
                sec = self.CreateTShellSection(curname, 1)
            
            if icomp == 1:
                for i in range(2,len(dynaSection)):
                    for j in range(0,8):
                        if len(dynaSection[i]) <= j:
                            break
                        sec.AddB(KooDynaFloat(dynaSection[i][j],0.0))
                    
        elif dynaSection[0] == "*SECTION_TSHELL_TITLE":
            zeroLine = dynaSection[1]
            firstLine = dynaSection[2]
            curid = KooDynaInt(firstLine[0],0)
            elform = KooDynaInt(firstLine[1],1)
            shrf = KooDynaFloat(firstLine[2],1.0)
            nip = KooDynaInt(firstLine[3],2)
            qr = KooDynaFloat(firstLine[4],0.0)
            icomp = KooDynaInt(firstLine[5],0)
            tshear = KooDynaInt(firstLine[6],0)
            
            if curid != 0:
                curname = zeroLine[0]
                sec = KooSectionTShell(curid, curname)
                self.AddSection(sec)
            else:
                curname = "NewSection"
                sec = self.CreateTShellSection(curname, 1)
            
            if icomp == 1:
                for i in range(3,len(dynaSection)):
                    for j in range(0,8):
                        if len(dynaSection[i]) <= j:
                            break
                        sec.AddB(KooDynaFloat(dynaSection[i][j],0.0))
            
        return None

    
    def WritetoDynaKeyword(self, startID):
        keywordString = ""
        for id in self.sections:
            sec = self.sections[id]
            sec.id = startID + id
            sec.GenerateDynaKeyword()
            keywordString += sec.dynaKeywordString
        return keywordString
    
    def WriteStreamDynaKeyword(self, stream):
        for id in self.sections:
            sec = self.sections[id]
            sec.GenerateDynaKeyword()
            stream.write(sec.dynaKeywordString)
    
if __name__ == "__main__":
    secManager = KooSectionManager()
    sec = secManager.CreateShellSection("ShellSection", 0.1)
    sec.GenerateDynaKeyword()
    print(sec.dynaKeywordString)
    sec = secManager.CreateShellSectionEachThickness("ShellSectionEachThickness", 0.1, 0.2, 0.3, 0.4)
    sec.GenerateDynaKeyword()
    print(sec.dynaKeywordString)
    print(secManager.WritetoDynaKeyword(1))

    sec = KooSectionSolid(0, "SolidSection")
    sec.SetElform(1)
    secManager.AddSection(sec)
    sec.GenerateDynaKeyword()
    print(sec.dynaKeywordString)
    print(secManager.WritetoDynaKeyword(1))
    sec = secManager.FindSectionfromID(1)
    print(sec.dynaKeywordString)
    sec = secManager.FindSectionfromID(2)
    print(sec.dynaKeywordString)
    sec = secManager.FindSectionfromID(3)
    print(sec.dynaKeywordString)




