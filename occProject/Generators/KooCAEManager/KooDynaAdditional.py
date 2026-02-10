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
        pass
    
    def WriteDynaKeyword(self):
        keyword = ""
        keyword += "*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID\n"
        keyword += format(self.ID, ">10")
        keyword += format(self.name, ">70")
        keyword += "\n"
        keyword += format(self.NSID, ">10")
        keyword += format(self.NSIDEX, ">10")
        keyword += format(self.BOXID, ">10")
        keyword += format(self.BIRTH, ">10.3e")
        keyword += format(self.DEATH, ">10.3e")
        keyword += "\n"
        keyword += format(self.XT, ">10.3e")
        keyword += format(self.YT, ">10.3e")
        keyword += format(self.ZT, ">10.3e")
        keyword += format(self.XH, ">10.3e")
        keyword += format(self.YH, ">10.3e")
        keyword += format(self.ZH, ">10.3e")
        keyword += format(self.FRIC, ">10.3e")
        keyword += "\n"
        keyword += format(self.XHEV, ">10.3e")
        keyword += format(self.YHEV, ">10.3e")
        keyword += format(self.ZHEV, ">10.3e")
        keyword += format(self.LENL, ">10.3e")
        keyword += format(self.LENM, ">10.3e")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID\n")
        stream.write(format(self.ID, ">10"))
        stream.write(format(self.name, ">70"))
        stream.write("\n")
        stream.write(format(self.NSID, ">10"))
        stream.write(format(self.NSIDEX, ">10"))
        stream.write(format(self.BOXID, ">10"))
        stream.write(format(self.BIRTH, ">10.3e"))
        stream.write(format(self.DEATH, ">10.3e"))
        stream.write("\n")
        stream.write(format(self.XT, ">10.3e"))
        stream.write(format(self.YT, ">10.3e"))
        stream.write(format(self.ZT, ">10.3e"))
        stream.write(format(self.XH, ">10.3e"))
        stream.write(format(self.YH, ">10.3e"))
        stream.write(format(self.ZH, ">10.3e"))
        stream.write(format(self.FRIC, ">10.3e"))
        stream.write("\n")
        stream.write(format(self.XHEV, ">10.3e"))
        stream.write(format(self.YHEV, ">10.3e"))
        stream.write(format(self.ZHEV, ">10.3e"))
        stream.write(format(self.LENL, ">10.3e"))
        stream.write(format(self.LENM, ">10.3e"))
        stream.write("\n")

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
        pass 
    
    def WriteDynaKeyword(self):
        keyword = ""
        keyword += "*RIGIDWALL_PLANAR_MOVING_FORCES_ID\n"
        keyword += format(self.ID, ">10")
        keyword += "\n"
        keyword += format(self.NSID, ">10")
        keyword += format(self.NSIDEX, ">10")
        keyword += format(self.BOXID, ">10")
        keyword += format(self.OFFSET, ">10.3e")
        keyword += format(self.BIRTH, ">10.3e")
        keyword += format(self.DEATH, ">10.3e")
        keyword += format(self.RWKSF, ">10.3e")
        keyword += "\n"
        keyword += format(self.XT, ">10.3e")
        keyword += format(self.YT, ">10.3e")
        keyword += format(self.ZT, ">10.3e")
        keyword += format(self.XH, ">10.3e")
        keyword += format(self.YH, ">10.3e")
        keyword += format(self.ZH, ">10.3e")
        keyword += format(self.FRIC, ">10.3e")
        keyword += format(self.WVEL, ">10.3e")
        keyword += "\n"
        keyword += format(self.MASS, ">10.3e")
        keyword += format(self.V0, ">10.3e")
        keyword += "\n"
        keyword += format(self.SOFT, ">10")
        keyword += format(self.SSID, ">10")
        keyword += format(self.N1, ">10")
        keyword += format(self.N2, ">10")
        keyword += format(self.N3, ">10")
        keyword += format(self.N4, ">10")
        keyword += "\n"
        return keyword  
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*RIGIDWALL_PLANAR_MOVING_FORCES_ID\n")
        stream.write(format(self.ID, ">10"))
        stream.write("\n")
        stream.write(format(self.NSID, ">10"))
        stream.write(format(self.NSIDEX, ">10"))
        stream.write(format(self.BOXID, ">10"))
        stream.write(format(self.OFFSET, ">10.3e"))
        stream.write(format(self.BIRTH, ">10.3e"))
        stream.write(format(self.DEATH, ">10.3e"))
        stream.write(format(self.RWKSF, ">10.3e"))
        stream.write("\n")
        stream.write(format(self.XT, ">10.3e"))
        stream.write(format(self.YT, ">10.3e"))
        stream.write(format(self.ZT, ">10.3e"))
        stream.write(format(self.XH, ">10.3e"))
        stream.write(format(self.YH, ">10.3e"))
        stream.write(format(self.ZH, ">10.3e"))
        stream.write(format(self.FRIC, ">10.3e"))
        stream.write(format(self.WVEL, ">10.3e"))
        stream.write("\n")
        stream.write(format(self.MASS, ">10.3e"))
        stream.write(format(self.V0, ">10.3e"))
        stream.write("\n")
        stream.write(format(self.SOFT, ">10"))
        stream.write(format(self.SSID, ">10"))
        stream.write(format(self.N1, ">10"))
        stream.write(format(self.N2, ">10"))
        stream.write(format(self.N3, ">10"))
        stream.write(format(self.N4, ">10"))
        stream.write("\n")              
        
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
        kw += f"{self.swset:>10}{self.code:>10}{self.time1:>10.1f}{self.time2:>10.1e}"
        kw += f"{self.time3:>10.1f}{self.entno:>10}{self.relsw:>10}{self.paired:>10}\n"
        kw += "$     nrbf      ncsf       rwf     dtmax       D2R       R2D    offset\n"
        kw += f"{self.nrbf:>10}{self.ncsf:>10}{self.rwf:>10}{self.dtmax:>10.1f}"
        kw += f"{len(self.d2r_pids):>10}{len(self.r2d_pids):>10}{self.offset:>10.1f}\n"
        for pid, lrb in self.d2r_pids:
            kw += f"{pid:>10}{lrb:>10}      PART\n"
        for pid in self.r2d_pids:
            kw += f"{pid:>10}      PART\n"
        return kw

    def WriteStreamDynaKeyword(self, stream):
        stream.write(self.WriteDynaKeyword())


class KooDynaAdditionalManager:
    def __init__(self):
        self.maxRWID = 0
        self.rigidwalls = {}
        self.hourglasses = {}
        self.maxInterface = 0
        self.interfaces = {}
        self.d2r_automatics = {}

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

    def CreateRigidwallPlanarMovingForces(self, NSID=0, NSIDEX=0, BOXID=0,OFFSET=0.0,BIRTH=0.0,DEATH=1.0e20,RWKSF=1.0,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,WVEL=0.0,MASS=0.0,V0=0.0, SOFT=0,SSID=0,N1=0,N2=0,N3=0,N4=0):
        self.maxRWID = self.maxRWID + 1
        rigidwall = KooRigidwallPlanarMovingForces(self.maxRWID, NSID, NSIDEX, BOXID,OFFSET,BIRTH,DEATH,RWKSF,XT,YT,ZT,XH,YH,ZH,FRIC,WVEL,MASS,V0, SOFT,SSID,N1,N2,N3,N4)
        self.rigidwalls[self.maxRWID] = rigidwall
        return rigidwall
    
    def CreateRigidwallPlanarMovingForceswithID(self, ID=0, NSID=0, NSIDEX=0, BOXID=0,OFFSET=0.0,BIRTH=0.0,DEATH=1.0e20,RWKSF=1.0,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,WVEL=0.0,MASS=0.0,V0=0.0, SOFT=0,SSID=0,N1=0,N2=0,N3=0,N4=0):        
        if ID > self.maxRWID:
            self.maxRWID = ID            
        rigidwall = KooRigidwallPlanarMovingForces(ID, NSID, NSIDEX, BOXID,OFFSET,BIRTH,DEATH,RWKSF,XT,YT,ZT,XH,YH,ZH,FRIC,WVEL,MASS,V0, SOFT,SSID,N1,N2,N3,N4)
        self.rigidwalls[ID] = rigidwall
        return rigidwall
    
    def CreateRigidwallGeometricFlatDisplay(self, NSID=0,NSIDEX=0,BOXID=0,BIRTH=0.0,DEATH=1.0E20,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,XHEV=0.0,YHEV=0.0,ZHEV=0.0,LENL=0.0,LENM=0.0): 
        self.maxRWID = self.maxRWID + 1
        rigidwall = KooRigidWallGeometricFlatDisplay(self.maxRWID, NSID,NSIDEX,BOXID,BIRTH,DEATH,XT,YT,ZT,XH,YH,ZH,FRIC,XHEV,YHEV,ZHEV,LENL,LENM)
        self.rigidwalls[self.maxRWID] = rigidwall
        return rigidwall
    
    def CreateRigidwallGeometricFlatDisplaywithID(self, ID=0, name = "",NSID=0,NSIDEX=0,BOXID=0,BIRTH=0.0,DEATH=1.0E20,XT=0.0,YT=0.0,ZT=0.0,XH=0.0,YH=0.0,ZH=0.0,FRIC=0.0,XHEV=0.0,YHEV=0.0,ZHEV=0.0,LENL=0.0,LENM=0.0):
        if ID > self.maxRWID:
            self.maxRWID = ID
        rigidwall = KooRigidWallGeometricFlatDisplay(ID, name,NSID,NSIDEX,BOXID,BIRTH,DEATH,XT,YT,ZT,XH,YH,ZH,FRIC,XHEV,YHEV,ZHEV,LENL,LENM)
        self.rigidwalls[ID] = rigidwall
        return rigidwall  

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
                                          d2r_pids, r2d_pids, offset=0.0):
        d2r = KooDeformableToRigidAutomatic(
            swset, code, 0.0, 1e20, 0.0, entno, relsw, paired,
            0, 0, 0, 0.0, d2r_pids, r2d_pids, offset)
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
            return rigidWall
        elif additionalKeyword[0] == "*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY":
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
            XT = KooDynaFloat(secondLine[0],0.0)
            YT = KooDynaFloat(secondLine[1],0.0)
            ZT = KooDynaFloat(secondLine[2],0.0)
            XH = KooDynaFloat(secondLine[3],0.0)
            YH = KooDynaFloat(secondLine[4],0.0)
            ZH = KooDynaFloat(secondLine[5],0.0)
            FRIC = KooDynaFloat(secondLine[6],0.0)
            XHEV = KooDynaFloat(thirdLine[0],0.0)
            YHEV = KooDynaFloat(thirdLine[1],0.0)
            ZHEV = KooDynaFloat(thirdLine[2],0.0)
            LENL = KooDynaFloat(thirdLine[3],0.0)
            LENM = KooDynaFloat(thirdLine[4],0.0)
            
            rigidWall = self.CreateRigidwallGeometricFlatDisplay(NSID,NSIDEX,BOXID,BIRTH,DEATH,XT,YT,ZT,XH,YH,ZH,FRIC,XHEV,YHEV,ZHEV,LENL,LENM)
            return rigidWall
        elif additionalKeyword[0] == "*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID":
            zeroLine = additionalKeyword[1]
            ID = int(zeroLine[0])
            name = zeroLine[1]
            firstLine = additionalKeyword[2]            
            secondLine = additionalKeyword[3]           
            thirdLine = additionalKeyword[4]
            #fourthLine = additionalKeyword[5]
            if len(firstLine)<7:
                firstLine += [""]*(7-len(firstLine))
            if len(secondLine)<8:
                secondLine += [""]*(8-len(secondLine))
            if len(thirdLine)<2:
                thirdLine += [""]*(2-len(thirdLine))
            #if len(fourthLine)<6:
            #    fourthLine += [""]*(6-len(fourthLine))
            NSID = KooDynaInt(firstLine[0],0)
            NSIDEX = KooDynaInt(firstLine[1],0)
            BOXID = KooDynaInt(firstLine[2],0)
            OFFSET = KooDynaFloat(firstLine[3],0.0)
            BIRTH = KooDynaFloat(firstLine[4],0.0)
            DEATH = KooDynaFloat(firstLine[5],1.0e20)
            XT = KooDynaFloat(secondLine[0],0.0)
            YT = KooDynaFloat(secondLine[1],0.0)
            ZT = KooDynaFloat(secondLine[2],0.0)
            XH = KooDynaFloat(secondLine[3],0.0)
            YH = KooDynaFloat(secondLine[4],0.0)
            ZH = KooDynaFloat(secondLine[5],0.0)
            FRIC = KooDynaFloat(secondLine[6],0.0)
            XHEV = KooDynaFloat(thirdLine[0],0.0)
            YHEV = KooDynaFloat(thirdLine[1],0.0)
            ZHEV = KooDynaFloat(thirdLine[2],0.0)
            LENL = KooDynaFloat(thirdLine[3],0.0)
            LENM = KooDynaFloat(thirdLine[4],0.0)
            
            rigidWall = self.CreateRigidwallGeometricFlatDisplaywithID(ID,name,NSID,NSIDEX,BOXID,BIRTH,DEATH,XT,YT,ZT,XH,YH,ZH,FRIC,XHEV,YHEV,ZHEV,LENL,LENM)
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
        for key in self.interfaces:
            interface = self.interfaces[key]
            interface.WriteStreamDynaKeyword(stream)
        for key in self.d2r_automatics:
            self.d2r_automatics[key].WriteStreamDynaKeyword(stream)
