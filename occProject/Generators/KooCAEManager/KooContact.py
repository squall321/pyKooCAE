from __future__ import annotations
from KooCAEManager.KooOperator import *

class KooContact:
    def __init__(self, cid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        self.cid = cid 
        self.name = name 
        self.SSID = SSID
        self.MSID = MSID
        self.SSTYP = SSTYP
        self.MSTYP = MSTYP
        self.SBOXID = SBOXID
        self.MBOXID = MBOXID
        self.SPR = SPR
        self.MPR = MPR
        self.FS = FS
        self.FD = FD
        self.DC = DC
        self.VC = VC
        self.VDC = VDC
        self.PENCHK = PENCHK
        self.BT = BT
        self.DT = DT
        self.SFS = SFS
        self.SFM = SFM
        self.SST = SST
        self.MST = MST
        self.SFST = SFST
        self.SFMT = SFMT
        self.FSF = FSF
        self.VSF = VSF
        
        self.OptCardA = []
        self.OptCardB = []
        self.OptCardC = []
        self.OptCardD = []
        self.OptCardE = []
        self.OptCardF = []
    
    def OffsetID(self,offsetid, offsetpid, offsetssid, offsetnsid, offsetpsid):
        self.cid += offsetid
        if self.SSTYP == 0:
            self.SSID += offsetssid
        elif self.SSTYP == 2:
            self.SSID += offsetpsid
        elif self.SSTYP == 3:
            self.SSID += offsetpid
        elif self.SSTYP == 4:
            self.SSID += offsetnsid
        if self.MSTYP == 0:
            self.MSID += offsetssid
        elif self.MSTYP == 2:
            self.MSID += offsetpsid
        elif self.MSTYP == 3:
            self.MSID += offsetpid
        elif self.MSTYP == 4:
            self.MSID += offsetnsid

    def SetOptCardA(self,SOFT=0, SOFSCL=0.1, LCIDAB=0, MAXPAR=1.025, SBOPT=2, DEPTH=2, BSORT=100, FRCFRQ=1):
        self.OptCardA = [int(SOFT), SOFSCL, int(LCIDAB), MAXPAR, int(SBOPT), int(DEPTH), int(BSORT), int(FRCFRQ)]
    
    def SetOptCardB(self,PENMAX=0.0, THKOPT=0, SHLTHK=0, SNLOG=0, ISYM=0, I2D3D=0, SLDTHK=0.0, SLDSTF=0.0):
        self.OptCardB = [PENMAX, THKOPT, SHLTHK, SNLOG, ISYM, I2D3D, SLDTHK, SLDSTF]
    
    def SetOptCardC(self, IGAP=1, IGNORE=0, DPRFACPA1=0.0, DTSTIFPA2=0.0, EDGEK=0.0, FLANGL=0.0, CID_RCF=0):
        self.OptCardC = [IGAP, IGNORE, DPRFACPA1, DTSTIFPA2, EDGEK,"          ", FLANGL, CID_RCF]   
    
    def SetOptCardD(self,Q2TRI=0, DTPCHK=0.0, SFNBR=0.0, FNLSCL=0.0, DNLSCL=0.0, TCSO=0, TIEDID=0, SHLEDG=0):
        self.OptCardD = [Q2TRI, DTPCHK, SFNBR, FNLSCL, DNLSCL, TCSO, TIEDID, SHLEDG]
    
    def SetOptCardE(self,SHAREC=0, CPARM8=0, IPBACK=0, SRNDE=0, FRICSF=1.0, ICOR=0, FTORQ=0, REGION=0):
        self.OptCardE = [SHAREC, CPARM8, IPBACK, SRNDE, FRICSF, ICOR, FTORQ, REGION]
    
    def SetOptCardF(self,PSTIFF=0, IGNROFF=0, FSTOL=2.0, DBINR=0, SSFTYP=0, SWTPR=0, TETFAC=0.0):
        self.OptCardF = [PSTIFF, IGNROFF, "          ", FSTOL, DBINR, SSFTYP, SWTPR, TETFAC]
    
    def WritetoDynaKeyword(self, startID = 0):
        keyword = ""
        keyword += "$$     CID      NAME\n"
        cidStr = format(self.cid + startID, ">10")
        nameStr = format(self.name, ">70")
        keyword += cidStr + nameStr + "\n"
        keyword += "$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n"
        SSIDStr = format(self.SSID, ">10")
        MSIDStr = format(self.MSID, ">10")
        SSTYPStr = format(self.SSTYP, ">10")
        MSTYPStr = format(self.MSTYP, ">10")
        SBOXIDStr = format(self.SBOXID, ">10")
        MBOXIDStr = format(self.MBOXID, ">10")
        SPRStr = format(self.SPR, ">10")
        MPRStr = format(self.MPR, ">10")
        keyword += SSIDStr + MSIDStr + SSTYPStr + MSTYPStr + SBOXIDStr + MBOXIDStr + SPRStr + MPRStr + "\n"
        keyword += "$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n"
        FSStr = format(self.FS, ">10")
        FDStr = format(self.FD, ">10")
        DCStr = format(self.DC, ">10")
        VCStr = format(self.VC, ">10")
        VDCStr = format(self.VDC, ">10")
        PENCHKStr = format(int(self.PENCHK) if self.PENCHK != "" else 0, ">10")
        BTStr = format(self.BT, ">10")
        DTStr = format(self.DT, ">10")
        keyword += FSStr + FDStr + DCStr + VCStr + VDCStr + PENCHKStr + BTStr + DTStr + "\n"        
        keyword += "$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n"
        SFSStr = format(self.SFS if self.SFS != "" else 1.0, ">10")
        SFMStr = format(self.SFM if self.SFM != "" else 1.0, ">10")
        SSTStr = format(self.SST if self.SST != "" else 0.0, ">10")
        MSTStr = format(self.MST if self.MST != "" else 0.0, ">10")
        SFSTStr = format(self.SFST if self.SFST != "" else 1.0, ">10")
        SFMTStr = format(self.SFMT if self.SFMT != "" else 1.0, ">10")
        FSFStr = format(self.FSF if self.FSF != "" else 1.0, ">10")
        VSFStr = format(self.VSF if self.VSF != "" else 1.0, ">10")
        keyword += SFSStr + SFMStr + SSTStr + MSTStr + SFSTStr + SFMTStr + FSFStr + VSFStr + "\n"

        return keyword
    
    def WritetoDynaKeywordOptCard(self):
        if len(self.OptCardA) == 0:
            return ""
        keyword = "$$    SOFT    SOFSCL    LCIDAB    MAXPAR     SBOPT     DEPTH     BSORT    FRCFRQ\n"
        SOFTStr = format(self.OptCardA[0], ">10")
        SOFSCLStr = format(self.OptCardA[1], ">10")
        LCIDABStr = format(self.OptCardA[2], ">10")
        MAXPARStr = format(self.OptCardA[3], ">10")
        SBOPTStr = format(self.OptCardA[4], ">10")
        DEPTHStr = format(self.OptCardA[5], ">10")
        BSORTStr = format(self.OptCardA[6], ">10")
        FRCFRQStr = format(self.OptCardA[7], ">10")
        
        keyword += SOFTStr + SOFSCLStr + LCIDABStr + MAXPARStr + SBOPTStr + DEPTHStr + BSORTStr + FRCFRQStr + "\n"
        
        if len(self.OptCardB) == 0:
            return keyword
        
        keyword += "$$  PENMAX    THKOPT    SHLTHK     SNLOG      ISYM     I2D3D    SLDTHK    SLDSTF\n"
        PENMAXStr = format(self.OptCardB[0], ">10")
        THKOPTStr = format(self.OptCardB[1], ">10")
        SHLTHKStr = format(self.OptCardB[2], ">10")
        SNLOGStr = format(self.OptCardB[3], ">10")
        ISYMStr = format(self.OptCardB[4], ">10")
        I2D3DStr = format(self.OptCardB[5], ">10")
        SLDTHKStr = format(self.OptCardB[6], ">10")
        SLDSTFStr = format(self.OptCardB[7], ">10")

        keyword += PENMAXStr + THKOPTStr + SHLTHKStr + SNLOGStr + ISYMStr + I2D3DStr + SLDTHKStr + SLDSTFStr + "\n"
        
        if len(self.OptCardC) == 0:
            return keyword
        
        keyword += "$$    IGAP    IGNORE DPRFACPA1 DTSTIFPA2               EDGEK    FLANGL   CID_RCF\n"
        IGAPStr = format(self.OptCardC[0], ">10")
        IGNOREStr = format(self.OptCardC[1], ">10")
        DPRFACPA1Str = format(self.OptCardC[2], ">10")
        DTSTIFPA2Str = format(self.OptCardC[3], ">10")
        EDGEKStr = format(self.OptCardC[4], ">10")
        EMPTYStr = format(self.OptCardC[5], ">10")
        FLANGLStr = format(self.OptCardC[6], ">10")
        CID_RCFStr = format(self.OptCardC[7], ">10")
        
        keyword += IGAPStr + IGNOREStr + DPRFACPA1Str + DTSTIFPA2Str + EDGEKStr + EMPTYStr + FLANGLStr + CID_RCFStr + "\n"
        
        if len(self.OptCardD) == 0:
            return keyword
        
        keyword += "$$   Q2TRI    DTPCHK     SFNBR    FNLSCL    DNLSCL      TCSO    TIEDID    SHLEDG\n"
        Q2TRIStr = format(self.OptCardD[0], ">10")
        DTPCHKStr = format(self.OptCardD[1], ">10")
        SFNBRStr = format(self.OptCardD[2], ">10")
        FNLSCLStr = format(self.OptCardD[3], ">10")
        DNLSCLStr = format(self.OptCardD[4], ">10")
        TCSOStr = format(self.OptCardD[5], ">10")
        TIEDIDStr = format(self.OptCardD[6], ">10")
        SHLEDGStr = format(self.OptCardD[7], ">10")
        
        keyword += Q2TRIStr + DTPCHKStr + SFNBRStr + FNLSCLStr + DNLSCLStr + TCSOStr + TIEDIDStr + SHLEDGStr + "\n"
        
        if len(self.OptCardE) == 0:
            return keyword
        
        keyword += "$$  SHAREC    CPARM8    IPBACK     SRNDE    FRICSF      ICOR     FTORQ    REGION\n"        
        
        SHARECStr = format(self.OptCardE[0], ">10")
        CPARM8Str = format(self.OptCardE[1], ">10")
        IPBACKStr = format(self.OptCardE[2], ">10")
        SRNDEStr = format(self.OptCardE[3], ">10")
        FRICSFStr = format(self.OptCardE[4], ">10")
        ICORStr = format(self.OptCardE[5], ">10")
        FTORQStr = format(self.OptCardE[6], ">10")
        REGIONStr = format(self.OptCardE[7], ">10")

        keyword += SHARECStr + CPARM8Str + IPBACKStr + SRNDEStr + FRICSFStr + ICORStr + FTORQStr + REGIONStr + "\n"
        
        if len(self.OptCardF) == 0:
            return keyword
        
        keyword += "$$  PSTIFF   IGNROFF               FSTOL     DBINR    SSFTYP     SWTPR    TETFAC\n"
        PSTIFFStr = format(self.OptCardF[0], ">10")
        IGNROFFStr = format(self.OptCardF[1], ">10")
        EMPTYStr = format(self.OptCardF[2], ">10")
        FSTOLStr = format(self.OptCardF[3], ">10")
        DBINRStr = format(self.OptCardF[4], ">10")
        SSFTYPStr = format(self.OptCardF[5], ">10")
        SWTPRStr = format(self.OptCardF[6], ">10")
        TETFACStr = format(self.OptCardF[7], ">10")
        
        keyword += PSTIFFStr + IGNROFFStr + EMPTYStr + FSTOLStr + DBINRStr + SSFTYPStr + SWTPRStr + TETFACStr + "\n"
        
        return keyword       
        
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("$$     CID      NAME\n")
        cidStr = format(self.cid + startID, ">10")
        nameStr = format(self.name, ">70")
        stream.write(cidStr + nameStr + "\n")
        stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
        SSIDStr = format(self.SSID, ">10")
        MSIDStr = format(self.MSID, ">10")
        SSTYPStr = format(self.SSTYP, ">10")
        MSTYPStr = format(self.MSTYP, ">10")
        SBOXIDStr = format(self.SBOXID, ">10")
        MBOXIDStr = format(self.MBOXID, ">10")
        SPRStr = format(self.SPR, ">10")
        MPRStr = format(self.MPR, ">10")
        stream.write(SSIDStr + MSIDStr + SSTYPStr + MSTYPStr + SBOXIDStr + MBOXIDStr + SPRStr + MPRStr + "\n")
        stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
        FSStr = format(self.FS, ">10")
        FDStr = format(self.FD, ">10")
        DCStr = format(self.DC, ">10")
        VCStr = format(self.VC, ">10")
        VDCStr = format(self.VDC, ">10")
        PENCHKStr = format(int(self.PENCHK) if self.PENCHK != "" else 0, ">10")
        BTStr = format(self.BT, ">10")
        DTStr = format(self.DT, ">10")
        stream.write(FSStr + FDStr + DCStr + VCStr + VDCStr + PENCHKStr + BTStr + DTStr + "\n")
        stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
        SFSStr = format(self.SFS if self.SFS != "" else 1.0, ">10")
        SFMStr = format(self.SFM if self.SFM != "" else 1.0, ">10")
        SSTStr = format(self.SST if self.SST != "" else 0.0, ">10")
        MSTStr = format(self.MST if self.MST != "" else 0.0, ">10")
        SFSTStr = format(self.SFST if self.SFST != "" else 1.0, ">10")
        SFMTStr = format(self.SFMT if self.SFMT != "" else 1.0, ">10")
        FSFStr = format(self.FSF if self.FSF != "" else 1.0, ">10")
        VSFStr = format(self.VSF if self.VSF != "" else 1.0, ">10")
        stream.write(SFSStr + SFMStr + SSTStr + MSTStr + SFSTStr + SFMTStr + FSFStr + VSFStr + "\n")
    
    def WriteStreamDynaKeywordOptCard(self,stream):
        if len(self.OptCardA) == 0:
            return
        stream.write("$$    SOFT    SOFSCL    LCIDAB    MAXPAR     SBOPT     DEPTH     BSORT    FRCFRQ\n")
        SOFTStr = format(self.OptCardA[0], ">10")
        SOFSCLStr = format(self.OptCardA[1], ">10")
        LCIDABStr = format(self.OptCardA[2], ">10")
        MAXPARStr = format(self.OptCardA[3], ">10")
        SBOPTStr = format(self.OptCardA[4], ">10")
        DEPTHStr = format(self.OptCardA[5], ">10")
        BSORTStr = format(self.OptCardA[6], ">10")
        FRCFRQStr = format(self.OptCardA[7], ">10")
        
        stream.write(SOFTStr + SOFSCLStr + LCIDABStr + MAXPARStr + SBOPTStr + DEPTHStr + BSORTStr + FRCFRQStr + "\n")
        
        if len(self.OptCardB) == 0:
            return
        
        stream.write("$$  PENMAX    THKOPT    SHLTHK     SNLOG      ISYM     I2D3D    SLDTHK    SLDSTF\n")
        PENMAXStr = format(self.OptCardB[0], ">10")
        THKOPTStr = format(self.OptCardB[1], ">10")
        SHLTHKStr = format(self.OptCardB[2], ">10")
        SNLOGStr = format(self.OptCardB[3], ">10")
        ISYMStr = format(self.OptCardB[4], ">10")
        I2D3DStr = format(self.OptCardB[5], ">10")
        SLDTHKStr = format(self.OptCardB[6], ">10")
        SLDSTFStr = format(self.OptCardB[7], ">10")

        stream.write(PENMAXStr + THKOPTStr + SHLTHKStr + SNLOGStr + ISYMStr + I2D3DStr + SLDTHKStr + SLDSTFStr + "\n")
        
        if len(self.OptCardC) == 0:
            return
        
        stream.write("$$    IGAP    IGNORE DPRFACPA1 DTSTIFPA2               EDGEK    FLANGL   CID_RCF\n")
        IGAPStr = format(self.OptCardC[0], ">10")
        IGNOREStr = format(self.OptCardC[1], ">10")
        DPRFACPA1Str = format(self.OptCardC[2], ">10")
        DTSTIFPA2Str = format(self.OptCardC[3], ">10")
        EDGEKStr = format(self.OptCardC[4], ">10")
        EMPTYStr = format(self.OptCardC[5], ">10")
        FLANGLStr = format(self.OptCardC[6], ">10")
        CID_RCFStr = format(self.OptCardC[7], ">10")
        
        stream.write(IGAPStr + IGNOREStr + DPRFACPA1Str + DTSTIFPA2Str + EDGEKStr + EMPTYStr + FLANGLStr + CID_RCFStr + "\n")
        
        if len(self.OptCardD) == 0:
            return
        
        stream.write("$$   Q2TRI    DTPCHK     SFNBR    FNLSCL    DNLSCL      TCSO    TIEDID    SHLEDG\n")
        Q2TRIStr = format(self.OptCardD[0], ">10")
        DTPCHKStr = format(self.OptCardD[1], ">10")
        SFNBRStr = format(self.OptCardD[2], ">10")
        FNLSCLStr = format(self.OptCardD[3], ">10")
        DNLSCLStr = format(self.OptCardD[4], ">10")
        TCSOStr = format(self.OptCardD[5], ">10")
        TIEDIDStr = format(self.OptCardD[6], ">10")
        SHLEDGStr = format(self.OptCardD[7], ">10")
        
        stream.write(Q2TRIStr + DTPCHKStr + SFNBRStr + FNLSCLStr + DNLSCLStr + TCSOStr + TIEDIDStr + SHLEDGStr + "\n")
        
        if len(self.OptCardE) == 0:
            return
        
        stream.write("$$  SHAREC    CPARM8    IPBACK     SRNDE    FRICSF      ICOR     FTORQ    REGION\n")        
        
        SHARECStr = format(self.OptCardE[0], ">10")
        CPARM8Str = format(self.OptCardE[1], ">10")
        IPBACKStr = format(self.OptCardE[2], ">10")
        SRNDEStr = format(self.OptCardE[3], ">10")
        FRICSFStr = format(self.OptCardE[4], ">10")
        ICORStr = format(self.OptCardE[5], ">10")
        FTORQStr = format(self.OptCardE[6], ">10")
        REGIONStr = format(self.OptCardE[7], ">10")

        stream.write(SHARECStr + CPARM8Str + IPBACKStr + SRNDEStr + FRICSFStr + ICORStr + FTORQStr + REGIONStr + "\n")
        
        if len(self.OptCardF) == 0:
            return 
        
        stream.write("$$  PSTIFF   IGNROFF               FSTOL     DBINR    SSFTYP     SWTPR    TETFAC\n")
        PSTIFFStr = format(self.OptCardF[0], ">10")
        IGNROFFStr = format(self.OptCardF[1], ">10")
        EMPTYStr = format(self.OptCardF[2], ">10")
        FSTOLStr = format(self.OptCardF[3], ">10")
        DBINRStr = format(self.OptCardF[4], ">10")
        SSFTYPStr = format(self.OptCardF[5], ">10")
        SWTPRStr = format(self.OptCardF[6], ">10")
        TETFACStr = format(self.OptCardF[7], ">10")
        
        stream.write(PSTIFFStr + IGNROFFStr + EMPTYStr + FSTOLStr + DBINRStr + SSFTYPStr + SWTPRStr + TETFACStr + "\n")
        
class KooContactAutomaticGeneral(KooContact):
    def __init__(self, cid, name, SSID, MSID, SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        super(KooContactAutomaticGeneral, self).__init__(cid, name, SSID, MSID, SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
    
    def WritetoDynaKeyword(self, startID=0):
        keyword = "*CONTACT_AUTOMATIC_GENERAL_ID\n"
        keyword += super(KooContactAutomaticGeneral, self).WritetoDynaKeyword(startID)
        keyword += self.WritetoDynaKeywordOptCard()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_AUTOMATIC_GENERAL_ID\n")
        super(KooContactAutomaticGeneral, self).WriteStreamDynaKeyword(stream, startID)
        self.WriteStreamDynaKeywordOptCard(stream)
    
class KooContactAutomaticSingleSurface(KooContact):
    def __init__(self, cid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        super(KooContactAutomaticSingleSurface,self).__init__(cid,name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        
    
    def WritetoDynaKeyword(self, startID=0):
        keyword = "*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID\n"
        keyword += super(KooContactAutomaticSingleSurface,self).WritetoDynaKeyword(startID)
        keyword += self.WritetoDynaKeywordOptCard()
        return keyword
       
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID\n")
        super(KooContactAutomaticSingleSurface,self).WriteStreamDynaKeyword(stream, startID)
        self.WriteStreamDynaKeywordOptCard(stream)
        
        
class KooContactAutomaticSurfacetoSurface(KooContact):
    def __init__(self, cid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        super(KooContactAutomaticSurfacetoSurface,self).__init__(cid,name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
                    
    def WritetoDynaKeyword(self, startID = 0):
        keyword = "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID\n"
        keyword += super(KooContactAutomaticSurfacetoSurface,self).WritetoDynaKeyword(startID)
        keyword += self.WritetoDynaKeywordOptCard()
        return keyword      
    
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID\n")
        super(KooContactAutomaticSurfacetoSurface,self).WriteStreamDynaKeyword(stream, startID)
        self.WriteStreamDynaKeywordOptCard(stream)
    
class KooContactErodingNodestoSurface(KooContact):
    def __init__(self, cid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ):  
        super(KooContactErodingNodestoSurface,self).__init__(cid,name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.SYM = SYM
        self.EROSOP = EROSOP
        self.IADJ = IADJ
    
    def WritetoDynaKeyword(self, startID=0):
        keyword = "*CONTACT_ERODING_NODES_TO_SURFACE_ID\n"
        keyword += super(KooContactErodingNodestoSurface,self).WritetoDynaKeyword(startID) 
        keyword += "$$     SYM    EROSOP      IADJ\n"
        keyword += format(self.SYM, ">10") + format(self.EROSOP, ">10") + format(self.IADJ, ">10") + "\n"
        keyword += self.WritetoDynaKeywordOptCard()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_ERODING_NODES_TO_SURFACE_ID\n")
        super(KooContactErodingNodestoSurface,self).WriteStreamDynaKeyword(stream, startID)
        stream.write("$$     SYM    EROSOP      IADJ\n")
        stream.write(format(self.SYM, ">10") + format(self.EROSOP, ">10") + format(self.IADJ, ">10") + "\n")
        self.WriteStreamDynaKeywordOptCard(stream)

class KooContactErodingSurfacetoSurface(KooContact):
    def __init__(self, cid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ):  
        super(KooContactErodingSurfacetoSurface,self).__init__(cid,name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.SYM = SYM
        self.EROSOP = EROSOP
        self.IADJ = IADJ
    
    def WritetoDynaKeyword(self, startID=0):
        keyword = "*CONTACT_ERODING_SURFACE_TO_SURFACE_ID\n"
        keyword += super(KooContactErodingSurfacetoSurface,self).WritetoDynaKeyword(startID) 
        keyword += "$$     SYM    EROSOP      IADJ\n"
        keyword += format(self.SYM, ">10") + format(self.EROSOP, ">10") + format(self.IADJ, ">10") + "\n"
        keyword += self.WritetoDynaKeywordOptCard()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_ERODING_SURFACE_TO_SURFACE_ID\n")
        super(KooContactErodingSurfacetoSurface,self).WriteStreamDynaKeyword(stream, startID)
        stream.write("$$     SYM    EROSOP      IADJ\n")
        stream.write(format(self.SYM, ">10") + format(self.EROSOP, ">10") + format(self.IADJ, ">10") + "\n")
        self.WriteStreamDynaKeywordOptCard(stream)
        return stream

class KooContactSingleSurface(KooContact):
    def __init__(self, cid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):  
        super(KooContactSingleSurface,self).__init__(cid,name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
    
    def WritetoDynaKeyword(self, startID=0):
        keyword = "*CONTACT_SINGLE_SURFACE_ID\n"
        keyword += super(KooContactSingleSurface,self).WritetoDynaKeyword(startID)
        keyword += self.WritetoDynaKeywordOptCard()
        return keyword

    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_SINGLE_SURFACE_ID\n")
        super(KooContactSingleSurface,self).WriteStreamDynaKeyword(stream, startID)
        self.WriteStreamDynaKeywordOptCard(stream)
        return stream
    
class KooContactTiedShellEdgetoSurfaceBeamOffset(KooContact):
    def __init__(self, cid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):  
        super(KooContactTiedShellEdgetoSurfaceBeamOffset,self).__init__(cid,name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
    
    def WritetoDynaKeyword(self, startID=0):
        keyword = "*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID\n"
        keyword += super(KooContactTiedShellEdgetoSurfaceBeamOffset,self).WritetoDynaKeyword(startID)
        keyword += self.WritetoDynaKeywordOptCard()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID\n")
        super(KooContactTiedShellEdgetoSurfaceBeamOffset,self).WriteStreamDynaKeyword(stream, startID)
        self.WriteStreamDynaKeywordOptCard(stream)
        return stream

class KooContactTiedSurfacetoSurface(KooContact):
    def __init__(self, cid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):      
        super(KooContactTiedSurfacetoSurface,self).__init__(cid,name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
    
    def WritetoDynaKeyword(self, startID=0):
        keyword = "*CONTACT_TIED_SURFACE_TO_SURFACE_ID\n"
        keyword += super(KooContactTiedSurfacetoSurface,self).WritetoDynaKeyword(startID)
        keyword += self.WritetoDynaKeywordOptCard()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_TIED_SURFACE_TO_SURFACE_ID\n")
        super(KooContactTiedSurfacetoSurface,self).WriteStreamDynaKeyword(stream, startID)
        self.WriteStreamDynaKeywordOptCard(stream)
        return stream

class KooContactTiedSurfacetoSurfaceOffset(KooContact):
    def __init__(self, cid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):      
        super(KooContactTiedSurfacetoSurfaceOffset,self).__init__(cid,name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
    
    def WritetoDynaKeyword(self, startID=0):
        keyword = "*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID\n"
        keyword += super(KooContactTiedSurfacetoSurfaceOffset,self).WritetoDynaKeyword(startID)
        keyword += self.WritetoDynaKeywordOptCard()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID\n")
        super(KooContactTiedSurfacetoSurfaceOffset,self).WriteStreamDynaKeyword(stream, startID)
        self.WriteStreamDynaKeywordOptCard(stream)
        return stream

class KooContactFEMPeriTieBreak(KooContact):
    def __init__(self, cid, msid, ssid, ft, fc):
        super(KooContactFEMPeriTieBreak,self).__init__(cid, "", msid, ssid,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
        self.FT = ft
        self.FC = fc
    
    def WritetoDynaKeyword(self, startID=0):
        keyword = "*CONTACT_FEM_PERI_TIE_BREAK_ID\n"
        keyword += "$$     CID      MSID      SSID        FT        FC\n"
        cidStr = format(self.cid + startID, ">10")
        msidStr = format(self.MSID, ">10")
        ssidStr = format(self.SSID, ">10")
        ftStr = format(self.FT, ">10")
        fcStr = format(self.FC, ">10")
        keyword += cidStr + msidStr + ssidStr + ftStr + fcStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_FEM_PERI_TIE_BREAK_ID\n")
        stream.write("$$     CID      MSID      SSID        FT        FC\n")
        cidStr = format(self.cid + startID, ">10")
        msidStr = format(self.MSID, ">10")
        ssidStr = format(self.SSID, ">10")
        ftStr = format(self.FT, ">10")
        fcStr = format(self.FC, ">10")
        stream.write(cidStr + msidStr + ssidStr + ftStr + fcStr + "\n")
        return stream
        
        
class KooContactAddWear:
    def __init__(self, cid, wtype, p1, p2, p3, p4=0.0, p5=0.0, p6=0.0):
        self.cid = cid
        self.wtype = wtype
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        self.p5 = p5
        self.p6 = p6
    
    def WritetoDynaKeyword(self, startID = 0):
        keyword = "*CONTACT_ADD_WEAR_ID\n"
        keyword += "$$     CID     WTYPE       P1       P2       P3       P4       P5       P6\n"
        cidStr = format(self.cid + startID, ">10")
        wtypeStr = format(self.wtype, ">10")
        p1Str = format(self.p1, ">10.3e")
        p2Str = format(self.p2, ">10.3e")
        p3Str = format(self.p3, ">10.3e")
        p4Str = format(self.p4, ">10.3e")
        p5Str = format(self.p5, ">10.3e")
        p6Str = format(self.p6, ">10.3e")
        keyword += cidStr + wtypeStr + p1Str + p2Str + p3Str + p4Str + p5Str + p6Str + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID = 0):
        stream.write("*CONTACT_ADD_WEAR_ID\n")
        stream.write("$$     CID     WTYPE       P1       P2       P3       P4       P5       P6\n")
        cidStr = format(self.cid + startID, ">10")
        wtypeStr = format(self.wtype, ">10")
        p1Str = format(self.p1, ">10.3e")
        p2Str = format(self.p2, ">10.3e")
        p3Str = format(self.p3, ">10.3e")
        p4Str = format(self.p4, ">10.3e")
        p5Str = format(self.p5, ">10.3e")
        p6Str = format(self.p6, ">10.3e")
        stream.write(cidStr + wtypeStr + p1Str + p2Str + p3Str + p4Str + p5Str + p6Str + "\n")
        return stream
        

class KooContactManager:
    def __init__(self):
        self.maxid = 0 
        self.contacts = {}
        self.tmpContacts = {}
        self.rigidContacts = {}
        self.contactsAddWear = {}
        
    def UpdateContactGraph(self, partManager, segManager):
        contactGraph = {} 
        primarytoSecondaries = {} 
        secondarytoPrimaries = {}
        segManager.FindPidfromSegments(partManager)
        for key, contact in self.contacts.items():
            newContact = {} 
            newContact["id"] = contact.cid
            newContact["label"] = contact.name

            if contact.SSTYP == 3 and contact.SSID in partManager.parts:
                newContact["secondary"] = partManager.parts[contact.SSID].id
                partA = partManager.parts[contact.SSID]
            elif contact.SSTYP == 0 and contact.SSID in segManager.segmentSetList:
                segment = segManager.segmentSetList[contact.SSID]
                newContact["secondary"] = partManager.parts[segment.pid].id
                partA = partManager.parts[segment.pid]
                
            else:
                print("only SSTYP = 3 and SSTYPE = 0 is supported in contact graph")
                continue
            if contact.MSTYP == 3 and contact.MSID in partManager.parts:
                newContact["primary"] = partManager.parts[contact.MSID].id            
                partB = partManager.parts[contact.MSID]
            elif contact.MSTYP == 0 and contact.MSID in segManager.segmentSetList:
                segment = segManager.segmentSetList[contact.MSID]
                newContact["primary"] = partManager.parts[segment.pid].id
                partB = partManager.parts[segment.pid]
            else:
                print("only MSTYP = 3 and SSTYPE = 0 is supported in contact graph")
                continue 
            newContact["type"] = type(contact).__name__
            if not partA.elementManager.elements or not partB.elementManager.elements:
                continue
            boundaryBoxA    = partA.elementManager.GetBoundaryBox()
            boundaryBoxB    = partB.elementManager.GetBoundaryBox()
            newContact["overlap_area"] = overlap_areas_xy_yz_zx(boundaryBoxA, boundaryBoxB)
            
            if partB not in primarytoSecondaries:
                primarytoSecondaries[partB.id] = {}
                primarytoSecondaries[partB.id]["id"] = partB.id
                primarytoSecondaries[partB.id]['sids'] = [partA.id]
                primarytoSecondaries[partB.id]['areas'] = [newContact["overlap_area"]]
            else:
                primarytoSecondaries[partB.id]['sids'].append(partA.id)
                primarytoSecondaries[partB.id]['areas'].append(newContact["overlap_area"])
            
            if partA not in secondarytoPrimaries:
                secondarytoPrimaries[partA.id] = {}
                secondarytoPrimaries[partA.id]["id"] = partA.id
                secondarytoPrimaries[partA.id]['sids'] = [partB.id]
                secondarytoPrimaries[partA.id]['areas'] = [newContact["overlap_area"]]
            else:
                secondarytoPrimaries[partA.id]['sids'].append(partB.id)
                secondarytoPrimaries[partA.id]['areas'].append(newContact["overlap_area"])
            
            contactGraph[contact.cid] = newContact
        
        return contactGraph, primarytoSecondaries, secondarytoPrimaries
        
    def OffsetID(self, offsetid, offsetpid, offsetssid, offsetnsid, offsetpsid):
        self.maxid = offsetid
        for contact in self.contacts:
            contact.OffsetID(offsetid, offsetpid, offsetssid, offsetnsid, offsetpsid)

    def OverwritefromContactManager(self, contactManager : KooContactManager):
        self.maxid = max(self.maxid, contactManager.maxid)
        for key, value in contactManager.contacts.items():
            self.contacts[key] = value
        for key, value in contactManager.tmpContacts.items():
            self.tmpContacts[key] = value
        for key, value in contactManager.rigidContacts.items():
            self.rigidContacts[key] = value
        for key, value in contactManager.contactsAddWear.items():
            self.contactsAddWear[key] = value

    def CreateContactAddWear(self, cid, wtype, p1, p2, p3, p4=0.0, p5=0.0, p6=0.0):
        contact = KooContactAddWear(cid, wtype, p1, p2, p3, p4, p5, p6)
        self.contactsAddWear[cid] = contact
        return contact 

    def CreateAutomaticGeneral(self, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactAutomaticGeneral(self.maxid, name, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        self.contacts[self.maxid] = contact
        return contact

    def CreateAutomaticGeneralwithID(self, id, name, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactAutomaticGeneral(id, name, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        self.contacts[id] = contact
        return contact
                             
    def CreateContactAutomaticSingleSurface(self, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactAutomaticSingleSurface(self.maxid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[self.maxid] = contact
        return contact

    def CreateContactAutomaticGeneral(self, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactAutomaticGeneral(self.maxid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[self.maxid] = contact
        return contact

    def CreateContactAutomaticSingleSurfacewithID(self,id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactAutomaticSingleSurface(id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[id] = contact
        return contact
        
    def CreateContactAutomaticSurfacetoSurface(self, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactAutomaticSurfacetoSurface(self.maxid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[self.maxid] = contact
        return contact    

    def CreateContactAutomaticSurfacetoSurfacewithID(self,id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactAutomaticSurfacetoSurface(id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[id] = contact
        return contact

    def CreateContactErodingNodestoSurface(self, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactErodingNodestoSurface(self.maxid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ)
        self.contacts[self.maxid] = contact
        return contact

    def CreateContactErodingNodestoSurfacewithID(self,id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactErodingNodestoSurface(id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ)
        self.contacts[id] = contact
        return contact

    def CreateContactErodingSurfacetoSurface(self, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactErodingSurfacetoSurface(self.maxid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ)
        self.contacts[self.maxid] = contact
        return contact
    
    def CreateContactErodingSurfacetoSurfacewithID(self,id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactErodingSurfacetoSurface(id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ)
        self.contacts[id] = contact
        return contact    
    
    def CreateContactFEMPeriTieBreak(self, msid, ssid, ft, fc):
        self.maxid += 1
        contact = KooContactFEMPeriTieBreak(self.maxid, msid, ssid, ft, fc)
        self.contacts[self.maxid] = contact
        return contact

    def CreateContactFEMPeriTieBreakwithID(self,id, msid, ssid, ft, fc):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactFEMPeriTieBreak(id, msid, ssid, ft, fc)
        self.contacts[id] = contact
        return contact
    
    def CreateContactSingleSurface(self, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactSingleSurface(self.maxid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[self.maxid] = contact
        return contact

    def CreateContactSingleSurfacewithID(self,id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactSingleSurface(id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[id] = contact
        return contact
    
    def CreateContactTiedShellEdgetoSurfaceBeamOffset(self, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactTiedShellEdgetoSurfaceBeamOffset(self.maxid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[self.maxid] = contact
        return contact

    def CreateContactTiedShellEdgetoSurfaceBeamOffsetwithID(self,id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactTiedShellEdgetoSurfaceBeamOffset(id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[id] = contact
        return contact
    
    def CreateContactTiedSurfacetoSurface(self, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactTiedSurfacetoSurface(self.maxid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[self.maxid] = contact
        return contact
    
    def CreateContactTiedSurfacetoSurfacewithID(self,id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactTiedSurfacetoSurface(id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[id] = contact
        return contact
    
    def CreateContactTiedSurfacetoSurfaceOffset(self, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        self.maxid += 1
        name = "Contact_{0}".format(self.maxid)
        contact = KooContactTiedSurfacetoSurfaceOffset(self.maxid, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[self.maxid] = contact
        return contact

    def CreateContactTiedSurfacetoSurfaceOffsetwithID(self,id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF):
        if id > self.maxid:
            self.maxid = id
        contact = KooContactTiedSurfacetoSurfaceOffset(id, name, SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        self.contacts[id] = contact
        return contact
    
    def AddContact(self, contact):
        self.contacts[contact.cid] = contact
        if contact.cid > self.maxid:
            self.maxid = contact.cid
        return contact
    
    def RemoveContactbyID(self, cid):
        del self.contacts[cid]
        
    def RemoveContact(self, contact):
        del self.contacts[contact.cid]
    
    def RemoveContactbyPartID(self, pid):
        cids = list(self.contacts.keys())
        for cid in cids:
            contact = self.contacts[cid]
            if contact.SSID == pid and contact.SSTYP == 3:
                self.RemoveContact(contact)
            elif contact.MSID == pid or contact.MSTYP == 3:
                self.RemoveContact(contact)

    def RemoveAll(self):
        self.maxid = 0 
        self.contacts = {}
        
    def RemoveTiedContactBetweenTwoPart(self, pid1, pid2):
        remcidList = []
        for cid, contact in list(self.contacts.items()):
            if contact.SSID == pid1 and contact.MSID == pid2 or contact.SSID == pid2 and contact.MSID == pid1:
                if contact.SSTYP == 3 and contact.MSTYP == 3:  # Tied surface to surface
                    if type(contact) in [KooContactTiedSurfacetoSurface, KooContactTiedSurfacetoSurfaceOffset]:
                        remcidList.append(cid)
        for cid in remcidList:
            self.RemoveContactbyID(cid)

    def WritetoDynaKeyword(self, startID):
        keyword = ""
        for key in self.contacts:
            keyword += self.contacts[key].WritetoDynaKeyword(startID)
        return keyword
    
    def AddContactAddWearfromDyna(self, contactKeyword):
        parameter = contactKeyword[1]        
        if len(parameter[0]) == 0:
            cid = 0
        else:
            cid = int(parameter[0])
        if len(parameter[1]) == 0:
            wtype = 0
        else:
            wtype = int(parameter[1])
        if len(parameter[2]) == 0:
            p1 = 0.0
        else:
            p1 = float(parameter[2])
        if len(parameter[3]) == 0:
            p2 = 0.0
        else:
            p2 = float(parameter[3])
        if len(parameter[4]) == 0:
            p3 = 0.0
        else:
            p3 = float(parameter[4])
        if len(parameter[5]) == 0:
            p4 = 0.0
        else:
            p4 = float(parameter[5])
        if len(parameter[6]) == 0:
            p5 = 0.0
        else:
            p5 = float(parameter[6])
        if len(parameter[7]) == 0:
            p6 = 0.0
        else:
            p6 = float(parameter[7])
        self.CreateContactAddWear(cid, wtype, p1, p2, p3, p4, p5, p6)                
    
    def AddContactfromDyna(self, contactKeyword):

        parameter = contactKeyword[1]
        SSID = KooDynaInt(parameter[0])
        MSID = KooDynaInt(parameter[1])
        SSTYP = KooDynaInt(parameter[2])
        MSTYP = KooDynaInt(parameter[3])
        SBOXID = KooDynaInt(parameter[4])
        MBOXID = KooDynaInt(parameter[5])
        SPR = KooDynaInt(parameter[6])
        MPR = KooDynaInt(parameter[7])
        
        parameter = contactKeyword[2]
        FS = KooDynaFloat(parameter[0])
        FD = KooDynaFloat(parameter[1])
        DC = KooDynaFloat(parameter[2])
        VC = KooDynaFloat(parameter[3])
        VDC = KooDynaFloat(parameter[4])
        PENCHK = KooDynaInt(parameter[5])
        BT = KooDynaFloat(parameter[6])
        DT = KooDynaFloat(parameter[7],1.0E20)
            
        parameter = contactKeyword[3]
        SFS = KooDynaFloat(parameter[0],1.0)
        SFM = KooDynaFloat(parameter[1],1.0)
        SST = KooDynaFloat(parameter[2],"")
        MST = KooDynaFloat(parameter[3],"")
        SFST = KooDynaFloat(parameter[4],1.0)
        SFMT= KooDynaFloat(parameter[5],1.0)
        FSF = KooDynaFloat(parameter[6],1.0)
        VSF = KooDynaFloat(parameter[7],1.0)
        contact = None
        if contactKeyword[0] == "*CONTACT_AUTOMATIC_GENERAL":
            contact = self.CreateAutomaticGeneral(SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)            
            i = 4 
        elif contactKeyword[0] == "*CONTACT_AUTOMATIC_SINGLE_SURFACE":
            contact = self.CreateContactAutomaticSingleSurface(SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
            i = 4
        elif contactKeyword[0] == "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE":
            contact = self.CreateContactAutomaticSurfacetoSurface(SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF) 
            i = 4
        elif contactKeyword[0] == "*CONTACT_SINGLE_SURFACE":
            contact = self.CreateContactSingleSurface(SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF) 
            i = 4        
        elif contactKeyword[0] == "*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET":
            contact = self.CreateContactTiedShellEdgetoSurfaceBeamOffset(SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
            i = 4
        elif contactKeyword[0] == "*CONTACT_TIED_SURFACE_TO_SURFACE":
            contact = self.CreateContactTiedSurfacetoSurface(SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
            i = 4
        elif contactKeyword[0] == "*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET":
            contact = self.CreateContactTiedSurfacetoSurfaceOffset(SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
            i = 4
        elif contactKeyword[0] == "*CONTACT_ERODING_NODES_TO_SURFACE" or contactKeyword[0] == "*CONTACT_ERODING_SURFACE_TO_SURFACE":
            parameter = contactKeyword[4] 
            i = 5 
            SYM = KooDynaInt(parameter[0])
            EROSOP = KooDynaInt(parameter[1])
            IADJ = KooDynaInt(parameter[2])
            
            if contactKeyword[0] == "*CONTACT_ERODING_NODES_TO_SURFACE":
                contact = self.CreateContactErodingNodestoSurface(SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ)        
            elif contactKeyword[0] == "*CONTACT_ERODING_SURFACE_TO_SURFACE":
                contact = self.CreateContactErodingSurfacetoSurface(SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ)
           
        for j in range(i,len(contactKeyword)):
            curContact = contactKeyword[j]
            if j == i:
                contact.SetOptCardA(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+1:
                contact.SetOptCardB(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+2:
                contact.SetOptCardC(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+3:
                contact.SetOptCardD(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+4:
                contact.SetOptCardE(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+5:
                contact.SetOptCardF(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
       
       
    def AddContactfromDynawithID(self, contactKeyword):
        if contactKeyword[0] == "*CONTACT_FEM_PERI_TIE_BREAK_ID":
            parameter = contactKeyword[1]
            cid = KooDynaInt(parameter[0])
            msid = KooDynaInt(parameter[1])
            ssid = KooDynaInt(parameter[2])
            ft = KooDynaFloat(parameter[3])
            fc = KooDynaFloat(parameter[4])
            self.CreateContactFEMPeriTieBreakwithID(cid, msid, ssid, ft, fc)
            return       
        parameter = contactKeyword[1]
        id = int(parameter[0])
        name = parameter[1]
            
        parameter = contactKeyword[2]
        SSID = KooDynaInt(parameter[0],"")
        MSID = KooDynaInt(parameter[1],"")
        SSTYP = KooDynaInt(parameter[2],"")
        MSTYP = KooDynaInt(parameter[3],"")
        SBOXID = KooDynaInt(parameter[4],"")
        MBOXID = KooDynaInt(parameter[5],"")
        SPR = KooDynaInt(parameter[6],"")
        MPR = KooDynaInt(parameter[7],"")
        
        parameter = contactKeyword[3]
        FS = KooDynaFloat(parameter[0],0.0)
        FD = KooDynaFloat(parameter[1],0.0)
        DC = KooDynaFloat(parameter[2],0.0)
        VC = KooDynaFloat(parameter[3],0.0)
        VDC = KooDynaFloat(parameter[4],0.0)
        PENCHK = KooDynaInt(parameter[5],0)
        BT = KooDynaFloat(parameter[6],0.0)
        DT = KooDynaFloat(parameter[7],1.0E20)
            
        parameter = contactKeyword[4]
        SFS = KooDynaFloat(parameter[0],1.0)
        SFM = KooDynaFloat(parameter[1],1.0)
        SST = KooDynaFloat(parameter[2],"")
        MST = KooDynaFloat(parameter[3],"")
        SFST = KooDynaFloat(parameter[4],1.0)
        SFMT= KooDynaFloat(parameter[5],1.0)
        FSF = KooDynaFloat(parameter[6],1.0)
        VSF = KooDynaFloat(parameter[7],1.0)
        contact = None
        if contactKeyword[0] == "*CONTACT_AUTOMATIC_GENERAL_ID":
            i = 5
            contact = self.CreateAutomaticGeneralwithID(id, name, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        elif contactKeyword[0] == "*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID":
            i = 5
            contact = self.CreateContactAutomaticSingleSurfacewithID(id,name,SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        elif contactKeyword[0] == "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID":
            i = 5
            contact = self.CreateContactAutomaticSurfacetoSurfacewithID(id,name,SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF) 
        elif contactKeyword[0] == "*CONTACT_SINGLE_SURFACE_ID":
            i = 5
            contact = self.CreateContactSingleSurfacewithID(id,name,SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        elif contactKeyword[0] == "*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID":
            i = 5
            contact = self.CreateContactTiedShellEdgetoSurfaceBeamOffsetwithID(id,name,SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        elif contactKeyword[0] == "*CONTACT_TIED_SURFACE_TO_SURFACE_ID":
            i = 5
            contact = self.CreateContactTiedSurfacetoSurfacewithID(id,name,SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        elif contactKeyword[0] == "*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID":
            i = 5
            contact = self.CreateContactTiedSurfacetoSurfaceOffsetwithID(id,name,SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF)
        elif contactKeyword[0] == "*CONTACT_ERODING_NODES_TO_SURFACE_ID" or contactKeyword[0] == "CONTACT_ERODING_SURFACE_TO_SURFACE_ID":
            i = 6
            parameter = contactKeyword[5] 
            if len(parameter[0]) == 0:
                SYM = 0
            else:
                SYM = int(parameter[0])
            if len(parameter[1]) == 0:
                EROSOP = 0
            else:
                EROSOP = int(parameter[1])
            if len(parameter[2]) == 0:
                IADJ = 0
            else:
                IADJ = int(parameter[2])
            if contactKeyword[0] == "*CONTACT_ERODING_NODES_TO_SURFACE_ID":
                contact = self.CreateContactErodingNodestoSurfacewithID(id,name,SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ)
            elif contactKeyword[0] == "*CONTACT_ERODING_SURFACE_TO_SURFACE_ID":
                contact = self.createContactErodingSurfacetoSurfacewithID(id,name,SSID, MSID,SSTYP,MSTYP,SBOXID,MBOXID,SPR,MPR,FS,FD,DC,VC,VDC,PENCHK,BT,DT,SFS,SFM,SST,MST,SFST,SFMT,FSF,VSF, SYM, EROSOP, IADJ)
        
        for j in range(i,len(contactKeyword)):
            curContact = contactKeyword[j]
            if j == i:
                contact.SetOptCardA(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+1:
                contact.SetOptCardB(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+2:
                contact.SetOptCardC(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+3:
                contact.SetOptCardD(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+4:
                contact.SetOptCardE(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
            if j == i+5:
                contact.SetOptCardF(curContact[0], curContact[1], curContact[2], curContact[3], curContact[4], curContact[5], curContact[6], curContact[7])
    
    def ChangePartIDtoPartSetID(self, partid, partsetid = 0):
        if partsetid == 0:
            partsetid = partid
        partSetType = 2
        
        for key in self.contacts:
            contact = self.contacts[key]
            if contact.SSID == partid:
                contact.SSID = partsetid
                contact.SSTYP = partSetType
            if contact.MSID == partid:
                contact.MSID = partsetid
                contact.MSTYP = partSetType
            
            
       
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        for key in self.contacts:
            keyword += self.contacts[key].WritetoDynaKeyword(startID)
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        for key in self.contacts:
            self.contacts[key].WriteStreamDynaKeyword(stream,startID)            
        
    def ConvertAss5ToAstsPartPairs(self, partManager, cid, marginX = 1.5, marginY = 1.5, marginZ = 1.5, absoluteMarginX = 5.0, absoluteMarginY = 5.0, absoluteMarginZ = 0.5):
        genContact = None
        if cid in self.contacts:
            contact = self.contacts[cid]
            if type(contact) in [KooContactAutomaticSingleSurface, KooContactSingleSurface]:
                if contact.MSTYP == 5 or contact.SSTYP == 5:
                    genContact = contact
            elif type(contact) == KooContactAutomaticGeneral:
                genContact = contact
                print("AUTOMATIC_GENERAL (CID={0}) -> S2S decomposition start".format(cid))
        print("ConvertAss5ToAstsPartPairs for Contact ID: {0}".format(cid))
        print("Calculating Bound Box for all Parts in Contact...")

        if genContact is None:
            print("No Contact found or Contact is not *CONTACT_AUTOMATIC_SINGLE_SURFACE, *CONTACT_SINGLE_SURFACE (MSTYP=5), or *CONTACT_AUTOMATIC_GENERAL")
            return 
        
        boundBoxDict = {}
        for id, part in partManager.parts.items():
            if not part.elementManager.elements:
                continue
            minX, maxX, minY, maxY, minZ, maxZ = part.elementManager.GetBoundaryBox()
            xLength = maxX - minX
            yLength = maxY - minY
            zLength = maxZ - minZ
            
            expandX = max(xLength * (marginX - 1.0) / 2.0, absoluteMarginX)
            expandY = max(yLength * (marginY - 1.0) / 2.0, absoluteMarginY)
            expandZ = max(zLength * (marginZ - 1.0) / 2.0, absoluteMarginZ)
            minX -= expandX
            maxX += expandX
            minY -= expandY
            maxY += expandY
            minZ -= expandZ
            maxZ += expandZ
            
            boundBoxDict[id] =[minX, maxX, minY, maxY, minZ, maxZ]
            print("Part ID: {0}, Bound Box: {1}".format(id, boundBoxDict[id]))
        
        print("Finding Part Pairs for Contact...")
        
        pairs = find_contact_pairs_sweep(boundBoxDict, tol=0.0)
    
        SSID = genContact.SSID
        MSID = genContact.MSID
        SSTYP = 3
        MSTYP = 3
        SBOXID = genContact.SBOXID
        SPR = genContact.SPR
        MPR = genContact.MPR
        FS = genContact.FS
        FD = genContact.FD
        DC = genContact.DC
        VC = genContact.VC
        VDC = genContact.VDC
        PENCHK = genContact.PENCHK
        BT = genContact.BT
        DT = genContact.DT
        SFS = genContact.SFS
        SFM = genContact.SFM
        SST = genContact.SST
        MST = genContact.MST
        SFST = genContact.SFST
        SFMT = genContact.SFMT
        FSF = genContact.FSF
        VSF = genContact.VSF
        OptCardA = genContact.OptCardA
        OptCardB = genContact.OptCardB
        OptCardC = genContact.OptCardC
        OptCardD = genContact.OptCardD
        OptCardE = genContact.OptCardE
        OptCardF = genContact.OptCardF
        
        # Tied contact 쌍 수집 (이중 구속 방지)
        tied_types = (KooContactTiedSurfacetoSurface, KooContactTiedSurfacetoSurfaceOffset,
                      KooContactTiedShellEdgetoSurfaceBeamOffset)
        tied_pairs = set()
        for _, contact in self.contacts.items():
            if isinstance(contact, tied_types):
                if contact.SSTYP == 3 and contact.MSTYP == 3:
                    a, b = min(contact.SSID, contact.MSID), max(contact.SSID, contact.MSID)
                    tied_pairs.add((a, b))
                else:
                    print("  Warning: Tied contact CID={0} uses non-part SSTYP={1}/MSTYP={2}, manual check needed".format(
                        contact.cid, contact.SSTYP, contact.MSTYP))
        if tied_pairs:
            print("Tied contact pairs excluded: {0}".format(len(tied_pairs)))

        # Tied 쌍 제외 후 S2S 생성
        created = 0
        for pair in pairs:
            partAID = pair[0]
            partBID = pair[1]
            a, b = min(partAID, partBID), max(partAID, partBID)
            if (a, b) in tied_pairs:
                continue
            partAName = partManager.parts[partAID].name if partAID in partManager.parts else str(partAID)
            partBName = partManager.parts[partBID].name if partBID in partManager.parts else str(partBID)
            newContact = self.CreateContactAutomaticSurfacetoSurface(partAID, partBID, SSTYP, MSTYP, SBOXID, 0, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
            newContact.OptCardA = OptCardA
            newContact.OptCardB = OptCardB
            newContact.OptCardC = OptCardC
            newContact.OptCardD = OptCardD
            newContact.OptCardE = OptCardE
            newContact.OptCardF = OptCardF
            contactName = "S2S_P{0}_{1}_to_P{2}_{3}".format(partAID, partAName.strip(), partBID, partBName.strip())
            newContact.name = contactName[:70]
            print("  CID={0}: Part {1}({2}) <-> Part {3}({4})".format(newContact.cid, partAID, partAName.strip(), partBID, partBName.strip()))
            created += 1

        print("Removing Original Contact ID: {0} ({1})".format(cid, type(genContact).__name__))
        self.RemoveContactbyID(cid)
        print("Contact decomposition completed: {0} S2S created ({1} tied excluded from {2} bbox pairs).".format(
            created, len(pairs) - created, len(pairs)))

    def RemoveDuplicateTiedContacts(self):
        """
        중복된 Tied Contact를 제거합니다.
        SSID/MSID 순서에 상관없이 동일한 페어에 대해 중복된 Tied Contact가 있으면
        먼저 읽힌 것만 남기고 나머지는 삭제합니다.
        """
        tiedContactTypes = (
            KooContactTiedShellEdgetoSurfaceBeamOffset,
            KooContactTiedSurfacetoSurface,
            KooContactTiedSurfacetoSurfaceOffset
        )

        seenPairs = set()
        contactsToRemove = []

        for _, contact in self.contacts.items():
            if isinstance(contact, tiedContactTypes):
                pair = tuple(sorted([contact.SSID, contact.MSID]))

                if pair in seenPairs:
                    contactsToRemove.append(contact)
                else:
                    seenPairs.add(pair)

        for contact in contactsToRemove:
            self.RemoveContact(contact)

        print(f"[RemoveDuplicateTiedContacts] Removed {len(contactsToRemove)} duplicate tied contacts")
        return len(contactsToRemove)