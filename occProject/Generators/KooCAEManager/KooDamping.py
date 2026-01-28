from __future__ import annotations
from KooCAEManager.KooOperator import *
class KooDamping:
    def __init__(self, did):
        self.did = did 
        self.dtype = None
        
class KooDampingGlobal(KooDamping):
    def __init__(self,LCID,VALDMP,STX,STY,STZ,SRX,SRY,SRZ):
        super(KooDampingGlobal, self).__init__(0)
        self.dtype = "DAMPING_GLOBAL"
        self.LCID = LCID
        self.VALDMP = VALDMP
        self.STX = STX
        self.STY = STY
        self.STZ = STZ
        self.SRX = SRX
        self.SRY = SRY
        self.SRZ = SRZ
    
    def WritetoDynaKeyword(self):
        keyword = ""    
        keyword += "*DAMPING_GLOBAL\n"
        keyword += format(self.LCID, ">10")
        keyword += format(self.VALDMP, ">10.3f")
        keyword += format(self.STX, ">10.3f")
        keyword += format(self.STY, ">10.3f")
        keyword += format(self.STZ, ">10.3f")
        keyword += format(self.SRX, ">10.3f")
        keyword += format(self.SRY, ">10.3f")
        keyword += format(self.SRZ, ">10.3f")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startPID):
        stream.write("*DAMPING_GLOBAL\n")
        stream.write(format(self.LCID, ">10"))
        stream.write(format(self.VALDMP, ">10.3f"))
        stream.write(format(self.STX, ">10.3f"))
        stream.write(format(self.STY, ">10.3f"))
        stream.write(format(self.STZ, ">10.3f"))
        stream.write(format(self.SRX, ">10.3f"))
        stream.write(format(self.SRY, ">10.3f"))
        stream.write(format(self.SRZ, ">10.3f"))
        stream.write("\n")
    
        
class KooDampingPartStiffness(KooDamping):
    def __init__(self, did, pid, coef):
        super(KooDampingPartStiffness, self).__init__(did)
        self.dtype = "DAMPING_PART_STIFFNESS"
        self.pid = pid
        self.coef = coef            
        
    def WritetoDynaKeyword(self, startPID):
        keyword = ""    
        keyword += "*DAMPING_PART_STIFFNESS\n"
        keyword += format(self.pid + startPID, ">10")
        keyword += format(self.coef, ">10.3f")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startPID):
        stream.write("*DAMPING_PART_STIFFNESS\n")
        stream.write(format(self.pid + startPID, ">10"))
        stream.write(format(self.coef, ">10.3f"))
        stream.write("\n")

class KooDampingPartStiffnessSet(KooDamping):
    def __init__(self, did, psid, coef):
        super(KooDampingPartStiffnessSet, self).__init__(did)
        self.dtype = "DAMPING_PART_STIFFNESS_SET"
        self.psid = psid
        self.coef = coef    
        
    def WritetoDynaKeyword(self, startPSID):
        keyword = ""    
        keyword += "*DAMPING_PART_STIFFNESS_SET\n"
        keyword += format(self.psid + startPSID, ">10")
        keyword += format(self.coef, ">10.3f")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startPSID):
        stream.write("*DAMPING_PART_STIFFNESS_SET\n")
        stream.write(format(self.psid + startPSID, ">10"))
        stream.write(format(self.coef, ">10.3f"))
        stream.write("\n")
    
class KooDampingPartMass(KooDamping):
    def __init__(self, did=0, pid=0, lcid=0, sf=0.0, flag=0, STX=0.0, STY=0.0, STZ=0.0, SRX=0.0, SRY=0.0, SRZ=0.0):
        super(KooDampingPartMass, self).__init__(did)
        self.dtype = "DAMPING_PART_MASS"
        self.pid = pid
        self.lcid = lcid
        self.sf = sf
        self.flag = flag
        self.STX = STX
        self.STY = STY
        self.STZ = STZ
        self.SRX = SRX
        self.SRY = SRY
        self.SRZ = SRZ
        
    def WritetoDynaKeyword(self, startPID):
        keyword = ""    
        keyword += "*DAMPING_PART_MASS\n"
        keyword += format(self.pid + startPID, ">10")
        keyword += format(self.lcid, ">10")
        keyword += format(self.sf, ">10.3f")
        keyword += format(self.flag, ">10")        
        keyword += "\n"
        if self.flag == 1:
            keyword += format(self.STX, ">10.3f")
            keyword += format(self.STY, ">10.3f")
            keyword += format(self.STZ, ">10.3f")
            keyword += format(self.SRX, ">10.3f")
            keyword += format(self.SRY, ">10.3f")
            keyword += format(self.SRZ, ">10.3f")
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startPID):
        stream.write("*DAMPING_PART_MASS\n")
        stream.write(format(self.pid + startPID, ">10"))
        stream.write(format(self.lcid, ">10"))
        stream.write(format(self.sf, ">10.3f"))
        stream.write(format(self.flag, ">10"))        
        stream.write("\n")
        if self.flag == 1:
            stream.write(format(self.STX, ">10.3f"))
            stream.write(format(self.STY, ">10.3f"))
            stream.write(format(self.STZ, ">10.3f"))
            stream.write(format(self.SRX, ">10.3f"))
            stream.write(format(self.SRY, ">10.3f"))
            stream.write(format(self.SRZ, ">10.3f"))
            stream.write("\n")

class KooDampingPartMassSet(KooDamping):
    def __init__(self, did, psid, lcid, sf, flag, STX, STY, STZ, SRX, SRY, SRZ):
        super(KooDampingPartMassSet, self).__init__(did)
        self.dtype = "DAMPING_PART_MASS_SET"
        self.psid = psid
        self.lcid = lcid
        self.sf = sf
        self.flag = flag
        self.STX = STX
        self.STY = STY
        self.STZ = STZ
        self.SRX = SRX
        self.SRY = SRY
        self.SRZ = SRZ

    def WritetoDynaKeyword(self, startPSID):
        keyword = ""    
        keyword += "*DAMPING_PART_MASS_SET\n"
        keyword += format(self.psid + startPSID, ">10")
        keyword += format(self.lcid, ">10")
        keyword += format(self.sf, ">10.3f")
        keyword += format(self.flag, ">10")        
        keyword += "\n"
        if self.flag == 1:
            keyword += format(self.STX, ">10.3f")
            keyword += format(self.STY, ">10.3f")
            keyword += format(self.STZ, ">10.3f")
            keyword += format(self.SRX, ">10.3f")
            keyword += format(self.SRY, ">10.3f")
            keyword += format(self.SRZ, ">10.3f")
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startPSID):
        stream.write("*DAMPING_PART_MASS_SET\n")
        stream.write(format(self.psid + startPSID, ">10"))
        stream.write(format(self.lcid, ">10"))
        stream.write(format(self.sf, ">10.3f"))
        stream.write(format(self.flag, ">10"))        
        stream.write("\n")
        if self.flag == 1:
            stream.write(format(self.STX, ">10.3f"))
            stream.write(format(self.STY, ">10.3f"))
            stream.write(format(self.STZ, ">10.3f"))
            stream.write(format(self.SRX, ">10.3f"))
            stream.write(format(self.SRY, ">10.3f"))
            stream.write(format(self.SRZ, ">10.3f"))
            stream.write("\n")
            
    
class KooDampingManager: 
    def __init__(self):
        self.maxid = 0
        self.dampings = {}

    def OffsetID(self, offsetID):
        for key in self.dampings:
            damping = self.dampings[key]
            damping.id += offsetID

    def OverwritefromDampingManager(self, dampingManager : KooDampingManager):
        self.maxid = max(self.maxid, dampingManager.maxid)
        for key, value in dampingManager.dampings.items():
            self.dampings[key] = value

    def SetGlobalDamping(self, LCID, VALDMP, STX, STY, STZ, SRX, SRY, SRZ):
        damping = KooDampingGlobal(LCID, VALDMP, STX, STY, STZ, SRX, SRY, SRZ)
        self.dampings[0] = damping
        return damping
        
    def CreateDampingPartStiffness(self, pid, coef):
        self.maxid += 1
        damping = KooDampingPartStiffness(self.maxid, pid, coef)
        self.dampings[self.maxid] = damping
        return damping

    def CreateDampingPartStiffnessSet(self, psid, coef):
        self.maxid += 1
        damping = KooDampingPartStiffnessSet(self.maxid, psid, coef)
        self.dampings[self.maxid] = damping
        return

    def CreateDampingPartMass(self, pid=0, lcid=0, sf=0.0, flag=0, STX=0.0, STY=0.0, STZ=0.0, SRX=0.0, SRY=0.0, SRZ=0.0):
        self.maxid += 1
        damping = KooDampingPartMass(self.maxid, pid, lcid, sf, flag, STX, STY, STZ, SRX, SRY, SRZ)
        self.dampings[self.maxid] = damping
        return damping

    def CreateDampingPartMassSet(self, psid=0, lcid=0, sf=0.0, flag=0, STX=0.0, STY=0.0, STZ=0.0, SRX=0.0, SRY=0.0, SRZ=0.0):
        self.maxid += 1
        damping = KooDampingPartMassSet(self.maxid, psid, lcid, sf, flag, STX, STY, STZ, SRX, SRY, SRZ)
        self.dampings[self.maxid] = damping
        return

    def SetDampingfromDyna(self, dampingKeyword):
        if dampingKeyword[0] == "*DAMPING_GLOBAL":
            keyword = dampingKeyword[1]
            if len(keyword[0]) == 0:
                keyword[0] = "0"
            if len(keyword[1]) == 0:
                keyword[1] = "0.0"
            if len(keyword[2]) == 0:
                keyword[2] = "0.0"
            if len(keyword[3]) == 0:
                keyword[3] = "0.0"
            if len(keyword[4]) == 0:
                keyword[4] = "0.0"
            if len(keyword[5]) == 0:
                keyword[5] = "0.0"
            if len(keyword[6]) == 0:
                keyword[6] = "0.0"
            if len(keyword[7]) == 0:
                keyword[7] = "0.0"
                
                
            LCID = KooDynaInt(keyword[0])
            VALDMP = KooDynaFloat(keyword[1])
            STX = KooDynaFloat(keyword[2])
            STY = KooDynaFloat(keyword[3])
            STZ = KooDynaFloat(keyword[4])
            SRX = KooDynaFloat(keyword[5])
            SRY = KooDynaFloat(keyword[6])
            SRZ = KooDynaFloat(keyword[7])
            self.SetGlobalDamping(LCID, VALDMP, STX, STY, STZ, SRX, SRY, SRZ)
        
        elif dampingKeyword[0] == "*DAMPING_PART_STIFFNESS":
            keyword = dampingKeyword[1] 
            pid = KooDynaInt(keyword[0])
            coef = KooDynaFloat(keyword[1])
            self.CreateDampingPartStiffness(pid, coef)
            
        elif dampingKeyword[0] == "*DAMPING_PART_STIFFNESS_SET":
            keyword = dampingKeyword[1]
            psid = KooDynaInt(keyword[0])
            coef = KooDynaFloat(keyword[1])
            self.CreateDampingPartStiffnessSet(psid, coef)
            
        elif dampingKeyword[0] == "*DAMPING_PART_MASS" or dampingKeyword[0] == "*DAMPING_PART_MASS_SET":
            keyword = dampingKeyword[1]
            if len(keyword[0]) == 0:
                keyword[0] = "0"
            if len(keyword[1]) == 0:
                keyword[1] = "0"
            if len(keyword[2]) == 0:
                keyword[2] = "0.0"
            if len(keyword[3]) == 0:
                keyword[3] = "0"
                
            pid = KooDynaInt(keyword[0])
            lcid = KooDynaInt(keyword[1])
            sf = KooDynaFloat(keyword[2])
            flag = KooDynaInt(keyword[3])
            if flag == 1:
                keyword = dampingKeyword[2]
                if len(keyword[0]) == 0:
                    keyword[0] = "0.0"
                if len(keyword[1]) == 0:
                    keyword[1] = "0.0"
                if len(keyword[2]) == 0:
                    keyword[2] = "0.0"
                if len(keyword[3]) == 0:
                    keyword[3] = "0.0"
                if len(keyword[4]) == 0:
                    keyword[4] = "0.0"
                if len(keyword[5]) == 0:
                    keyword[5] = "0.0"
                
                STX = KooDynaFloat(keyword[0])
                STY = KooDynaFloat(keyword[1])
                STZ = KooDynaFloat(keyword[2])
                SRX = KooDynaFloat(keyword[3])
                SRY = KooDynaFloat(keyword[4])
                SRZ = KooDynaFloat(keyword[5])
            else:
                STX = 0.0
                STY = 0.0
                STZ = 0.0
                SRX = 0.0
                SRY = 0.0
                SRZ = 0.0
            
            if dampingKeyword[0] == "*DAMPING_PART_MASS":
                self.CreateDampingPartMass(pid, lcid, sf, flag, STX, STY, STZ, SRX, SRY, SRZ)
            elif dampingKeyword[0] == "*DAMPING_PART_MASS_SET":
                self.CreateDampingPartMassSet(pid, lcid, sf, flag, STX, STY, STZ, SRX, SRY, SRZ)
        
        
    
    def GenerateDynaKeyword(self, startPID):
        keyword = ""
        for key in self.dampings:
            damping = self.dampings[key]
            keyword += damping.WritetoDynaKeyword(startPID)
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startPID):
        for key in self.dampings:
            damping = self.dampings[key]
            damping.WriteStreamDynaKeyword(stream,startPID)