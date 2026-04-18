from __future__ import annotations

if __name__ == "__main__":
    from KooDynaKeyword import *
    from KooOperator import KooDynaFloat, KooDynaInt, KooDynaString
else:
    from KooCAEManager.KooDynaKeyword import *
    from KooCAEManager.KooOperator import KooDynaFloat, KooDynaInt, KooDynaString

class KooControlMppIONodump:
    def __init__(self):
        pass 
    
    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_MPP_IO_NODUMP\n"
        return keyword
    
class KooControlOutput:
    def __init__(self):
        self.NPOPT = 0
        self.NEECHO = 0 
        self.NREFUP = 0 
        self.IACCOP = 0
        self.OPIFS = 0.0
        self.IPNINT = 0
        self.IKEDIT = 100
        self.IFLUSH = 5000
        self.IPRTF = 0
        self.IERODE = 0
        self.TET10S8 = 2
        self.MSGMAX = 50
        self.IPCURV = 0
        self.GMDT = 0.0
        self.IP1DBLT = 0
        self.EOCS = 0
        self.TOLEV = 2
        self.NEWLEG = 0
        self.FRFREQ = 1
        self.MINFO = 0
        self.SOLSIG = 0
        self.MSGFLG = 0
        self.CDETOL = 10.0
        self.IGEOM = 1
        self.PHSCHNG = 0
        self.DEMDEN = 0
        self.ICRFILE = 0
        self.SPC2BND = 0
        self.PENOUT = 0
        self.SHLSIG = 0
        self.HISNOUT = 0
        self.ENGOUT = 0
        self.INSF = 0
        self.ISOLSF = 0
        self.IBSF = 0
        self.ISSF = 0
        self.MLKBAG = 0
    
    def AddtoDynaKeyword(self, keyword : ControlOutput):
        keyword.SetControlOutput(self.NPOPT, self.NEECHO, self.NREFUP, self.IACCOP, self.OPIFS, self.IPNINT, self.IKEDIT, self.IFLUSH, self.IPRTF, self.IERODE, self.TET10S8, self.MSGMAX, self.IPCURV, self.GMDT, self.IP1DBLT, self.EOCS, self.TOLEV, self.NEWLEG, self.FRFREQ, self.MINFO, self.SOLSIG, self.MSGFLG, self.CDETOL, self.IGEOM, self.PHSCHNG, self.DEMDEN, self.ICRFILE, self.SPC2BND, self.PENOUT, self.SHLSIG, self.HISNOUT, self.ENGOUT, self.INSF, self.ISOLSF, self.IBSF, self.ISSF, self.MLKBAG)
        
    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_OUTPUT\n"
        keyword += "$$   NPOPT    NEECHO    NREFUP    IACCOP     OPIFS    IPNINT    IKEDIT     IFLUSH\n"
        keyword += format(self.NPOPT, ">10")
        keyword += format(self.NEECHO, ">10")
        keyword += format(self.NREFUP, ">10")
        keyword += format(self.IACCOP, ">10")
        keyword += format(self.OPIFS, ">10.3f")
        keyword += format(self.IPNINT, ">10")
        keyword += format(self.IKEDIT, ">10")
        keyword += format(self.IFLUSH, ">10")
        keyword += "\n"
        keyword += "$$    IPRTF    IERODE   TET10S8    MSGMAX    IPCURV      GMDT   IP1DBLT      EOCS\n"
        keyword += format(self.IPRTF, ">10")
        keyword += format(self.IERODE, ">10")
        keyword += format(self.TET10S8, ">10")
        keyword += format(self.MSGMAX, ">10")
        keyword += format(self.IPCURV, ">10")
        keyword += format(self.GMDT, ">10.3f")
        keyword += format(self.IP1DBLT, ">10")
        keyword += format(self.EOCS, ">10")
        keyword += "\n"
        keyword += "$$    TOLEV    NEWLEG   FRFREQ     MINFO    SOLSIG    MSGFLG    CDETOL     IGEOM\n"
        keyword += format(self.TOLEV, ">10")
        keyword += format(self.NEWLEG, ">10")
        keyword += format(self.FRFREQ, ">10")
        keyword += format(self.MINFO, ">10")
        keyword += format(self.SOLSIG, ">10")
        keyword += format(self.MSGFLG, ">10")
        keyword += format(self.CDETOL, ">10.3f")
        keyword += format(self.IGEOM, ">10")        
        keyword += "\n"
        keyword += "$$  PHSCHNG    DEMDEN   ICRFILE   SPC2BND    PENOUT   SHLSIG   HISNOUT    ENGOUT\n"
        keyword += format(self.PHSCHNG, ">10")
        keyword += format(self.DEMDEN, ">10")
        keyword += format(self.ICRFILE, ">10")
        keyword += format(self.SPC2BND, ">10")
        keyword += format(self.PENOUT, ">10")
        keyword += format(self.SHLSIG, ">10")
        keyword += format(self.HISNOUT, ">10")
        keyword += format(self.ENGOUT, ">10")
        keyword += "\n"
        keyword += "$$     INSF    ISOLSF      IBSF      ISSF    MLKBAG\n"
        keyword += format(self.INSF, ">10")
        keyword += format(self.ISOLSF, ">10")
        keyword += format(self.IBSF, ">10")
        keyword += format(self.ISSF, ">10")
        keyword += format(self.MLKBAG, ">10")
        keyword += "\n"
        return keyword      
        
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_OUTPUT\n")
        stream.write("$$   NPOPT    NEECHO    NREFUP    IACCOP     OPIFS    IPNINT    IKEDIT     IFLUSH\n")
        stream.write(format(self.NPOPT, ">10"))
        stream.write(format(self.NEECHO, ">10"))
        stream.write(format(self.NREFUP, ">10"))
        stream.write(format(self.IACCOP, ">10"))
        stream.write(format(self.OPIFS, ">10.3f"))
        stream.write(format(self.IPNINT, ">10"))
        stream.write(format(self.IKEDIT, ">10"))
        stream.write(format(self.IFLUSH, ">10"))
        stream.write("\n")
        stream.write("$$    IPRTF    IERODE   TET10S8    MSGMAX    IPCURV      GMDT   IP1DBLT      EOCS\n")
        stream.write(format(self.IPRTF, ">10"))
        stream.write(format(self.IERODE, ">10"))
        stream.write(format(self.TET10S8, ">10"))
        stream.write(format(self.MSGMAX, ">10"))
        stream.write(format(self.IPCURV, ">10"))
        stream.write(format(self.GMDT, ">10.3f"))
        stream.write(format(self.IP1DBLT, ">10"))
        stream.write(format(self.EOCS, ">10"))
        stream.write("\n")
        stream.write("$$    TOLEV    NEWLEG   FRFREQ     MINFO    SOLSIG    MSGFLG    CDETOL     IGEOM\n")
        stream.write(format(self.TOLEV, ">10"))
        stream.write(format(self.NEWLEG, ">10"))
        stream.write(format(self.FRFREQ, ">10"))
        stream.write(format(self.MINFO, ">10"))
        stream.write(format(self.SOLSIG, ">10"))
        stream.write(format(self.MSGFLG, ">10"))
        stream.write(format(self.CDETOL, ">10.3f"))
        stream.write(format(self.IGEOM, ">10"))
        stream.write("\n")
        stream.write("$$  PHSCHNG    DEMDEN   ICRFILE   SPC2BND    PENOUT   SHLSIG   HISNOUT    ENGOUT\n")
        stream.write(format(self.PHSCHNG, ">10"))
        stream.write(format(self.DEMDEN, ">10"))
        stream.write(format(self.ICRFILE, ">10"))
        stream.write(format(self.SPC2BND, ">10"))
        stream.write(format(self.PENOUT, ">10"))
        stream.write(format(self.SHLSIG, ">10"))
        stream.write(format(self.HISNOUT, ">10"))
        stream.write(format(self.ENGOUT, ">10"))
        stream.write("\n")
        stream.write("$$     INSF    ISOLSF      IBSF      ISSF    MLKBAG\n")
        stream.write(format(self.INSF, ">10"))
        stream.write(format(self.ISOLSF, ">10"))
        stream.write(format(self.IBSF, ">10"))
        stream.write(format(self.ISSF, ">10"))
        stream.write(format(self.MLKBAG, ">10"))
        stream.write("\n")                    

class KooControlShell:
    def __init__(self):
        self.WRPANG = 20.0
        self.ESORT = 0
        self.IRNXX = -1
        self.ISTUPD = 0
        self.THEORY = 2
        self.BWC = 2
        self.MITER = 1
        self.PROJ = 0 
        self.ROTASCL = 1.0
        self.INTGRD = 0
        self.LAMSHT = 0
        self.CSTYP6 = 1
        self.THSHEL = 0 
        self.PSTUPD = 0
        self.SIDT4TU = 0
        self.CNTCO = 0
        self.ITSFLG = 0
        self.IRQUAD = 0
        self.W_MODE = ""
        self.STRETCH = ""
        self.ICRQ = 0
        self.NFAIL1 = ""
        self.NFAIL4 = ""
        self.PSNFAIL = 0
        self.KEEPCS = 0
        self.DELFR = 0
        self.DRCPSID = 0
        self.DRCPRM = 1.0
        self.INTPERR = ""
        self.DRCMTH = 0
        self.LISPSID = 0
        self.NLOCDT = 0
        
    def AddtoDynaKeywrod(self, keyword : ControlShell):
        keyword.SetControlShell(self.WRPANG, self.ESORT, self.IRNXX, self.ISTUPD, self.THEORY, self.BWC, self.MITER, self.PROJ, self.ROTASCL, self.INTGRD, self.LAMSHT, self.CSTYP6, self.THSHEL, self.PSTUPD, self.SIDT4TU, self.CNTCO, self.ITSFLG, self.IRQUAD, self.W_MODE, self.STRETCH, self.ICRQ, self.NFAIL1, self.NFAIL4, self.PSNFAIL, self.KEEPCS, self.DELFR, self.DRCPSID, self.DRCPRM, self.INTPERR, self.DRCMTH, self.LISPSID, self.NLOCDT)
    
    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_SHELL\n"
        keyword += "$$   WRPANG     ESORT     IRNXX    ISTUPD    THEORY       BWC     MITER      PROJ\n"
        keyword += format(self.WRPANG, ">10.3f")
        keyword += format(self.ESORT, ">10")
        keyword += format(self.IRNXX, ">10")
        keyword += format(self.ISTUPD, ">10")
        keyword += format(self.THEORY, ">10")
        keyword += format(self.BWC, ">10")
        keyword += format(self.MITER, ">10")
        keyword += format(self.PROJ, ">10")
        keyword += "\n"
        keyword += "$$  ROTASCL   INTGRD    LAMSHT    CSTYP6    THSHEL\n"
        keyword += format(self.ROTASCL, ">10.3f")
        keyword += format(self.INTGRD, ">10")
        keyword += format(self.LAMSHT, ">10")
        keyword += format(self.CSTYP6, ">10")
        keyword += format(self.THSHEL, ">10")        
        keyword += "\n"
        keyword += "$$  PSTUPD   SIDT4TU     CNTCO   ITSFLG    IRQUAD    W_MODE   STRETCH      ICRQ\n"
        keyword += format(self.PSTUPD, ">10")
        keyword += format(self.SIDT4TU, ">10")
        keyword += format(self.CNTCO, ">10")
        keyword += format(self.ITSFLG, ">10")
        keyword += format(self.IRQUAD, ">10")
        if self.W_MODE == "":
            self.W_MODE = "          "            
            keyword += format(self.W_MODE, ">10")
        else:
            keyword += format(self.W_MODE, ">10.3f")
        if self.STRETCH == "":
            self.STRETCH = "          "
            keyword += format(self.STRETCH, ">10")
        else:
            keyword += format(self.STRETCH, ">10.3f")
        keyword += format(self.ICRQ, ">10")        
        keyword += "\n"
        keyword += "$$  NFAIL1    NFAIL4   PSNFAIL   KEEPCS     DELFR   DRCPSID    DRCPRM   INTPERR\n"
        if self.NFAIL1 == "":
            self.NFAIL1 = "          "
        keyword += format(self.NFAIL1, ">10")
        if self.NFAIL4 == "":
            self.NFAIL4 = "          "
        keyword += format(self.NFAIL4, ">10")
        keyword += format(self.PSNFAIL, ">10")
        keyword += format(self.KEEPCS, ">10")
        keyword += format(self.DELFR, ">10")
        keyword += format(self.DRCPSID, ">10")
        keyword += format(self.DRCPRM, ">10.3f")
        if self.INTPERR == "":
            self.INTPERR = "          "
        keyword += format(self.INTPERR, ">10")
        keyword += "$$  DRCMTH   LISPSID    NLOCDT\n"
        keyword += format(self.DRCMTH, ">10")
        keyword += format(self.LISPSID, ">10")
        keyword += format(self.NLOCDT, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_SHELL\n")
        stream.write("$$   WRPANG     ESORT     IRNXX    ISTUPD    THEORY       BWC     MITER      PROJ\n")
        stream.write(format(self.WRPANG, ">10.3f"))
        stream.write(format(self.ESORT, ">10"))
        stream.write(format(self.IRNXX, ">10"))
        stream.write(format(self.ISTUPD, ">10"))
        stream.write(format(self.THEORY, ">10"))
        stream.write(format(self.BWC, ">10"))
        stream.write(format(self.MITER, ">10"))
        stream.write(format(self.PROJ, ">10"))
        stream.write("\n")
        stream.write("$$  ROTASCL   INTGRD    LAMSHT    CSTYP6    THSHEL\n")
        stream.write(format(self.ROTASCL, ">10.3f"))
        stream.write(format(self.INTGRD, ">10"))
        stream.write(format(self.LAMSHT, ">10"))
        stream.write(format(self.CSTYP6, ">10"))
        stream.write(format(self.THSHEL, ">10"))        
        stream.write("\n")
        stream.write("$$  PSTUPD   SIDT4TU     CNTCO   ITSFLG    IRQUAD    W_MODE   STRETCH      ICRQ\n")
        stream.write(format(self.PSTUPD, ">10"))
        stream.write(format(self.SIDT4TU, ">10"))
        stream.write(format(self.CNTCO, ">10"))
        stream.write(format(self.ITSFLG, ">10"))
        stream.write(format(self.IRQUAD, ">10"))
        if self.W_MODE == "":
            self.W_MODE = "          "            
        stream.write(format(self.W_MODE, ">10"))
        if self.STRETCH == "":
            self.STRETCH = "          "
        stream.write(format(self.STRETCH, ">10"))
        stream.write(format(self.ICRQ, ">10"))        
        stream.write("\n")
        stream.write("$$  NFAIL1    NFAIL4   PSNFAIL   KEEPCS     DELFR   DRCPSID    DRCPRM   INTPERR\n")
        if self.NFAIL1 == "":
            self.NFAIL1 = "          "
        stream.write(format(self.NFAIL1, ">10"))
        if self.NFAIL4 == "":
            self.NFAIL4 = "          "
        stream.write(format(self.NFAIL4, ">10"))
        stream.write(format(self.PSNFAIL, ">10"))
        stream.write(format(self.KEEPCS, ">10"))
        stream.write(format(self.DELFR, ">10"))
        stream.write(format(self.DRCPSID, ">10"))
        stream.write(format(self.DRCPRM, ">10.3f"))
        if self.INTPERR == "":
            self.INTPERR = "          "
        stream.write(format(self.INTPERR, ">10"))
        stream.write("$  DRCMTH   LISPSID    NLOCDT\n")
        stream.write(format(self.DRCMTH, ">10"))
        stream.write(format(self.LISPSID, ">10"))
        stream.write(format(self.NLOCDT, ">10"))

class KooControlSolid:
    def __init__(self):
        self.ESORT = 0
        self.FMATRX = 0
        self.NIPTETS = 4
        self.SWLOCL = 1
        self.PSFAIL = 0
        self.T10JTOL = 0.0
        self.ICOH = 0
        self.TET13K = 0
        self.PM1 = ""
        self.PM2 = ""
        self.PM3 = ""
        self.PM4 = ""
        self.PM5 = ""
        self.PM6 = ""
        self.PM7 = ""
        self.PM8 = ""
        self.PM9 = ""
        self.PM10 = ""
        self.TET13V = 0
        self.RINRT = 0
        
    def AddtoDynaKeyword(self, keyword : ControlSolid):
        keyword.SetControlSolid(self.ESORT, self.FMATRX, self.NIPTETS, self.SWLOCL, self.PSFAIL, self.T10JTOL, self.ICOH, self.TET13K, self.PM1, self.PM2, self.PM3, self.PM4, self.PM5, self.PM6, self.PM7, self.PM8, self.PM9, self.PM10, self.TET13V, self.RINRT)
    
    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_SOLID\n"
        keyword += "$$     ESORT    FMATRX   NIPTETS    SWLOCL    PSFAIL   T10JTOL      ICOH     TET13K\n"
        keyword += format(self.ESORT, ">10")
        keyword += format(self.FMATRX, ">10")
        keyword += format(self.NIPTETS, ">10")
        keyword += format(self.SWLOCL, ">10")
        keyword += format(self.PSFAIL, ">10")
        keyword += format(self.T10JTOL, ">10.3f")
        keyword += format(self.ICOH, ">10")
        keyword += format(self.TET13K, ">10")
        keyword += "\n"
        keyword += "$$   PM1     PM2     PM3     PM4     PM5     PM6     PM7     PM8     PM9    PM10\n"
        keyword += format(self.PM1, ">8")
        keyword += format(self.PM2, ">8")
        keyword += format(self.PM3, ">8")
        keyword += format(self.PM4, ">8")
        keyword += format(self.PM5, ">8")
        keyword += format(self.PM6, ">8")
        keyword += format(self.PM7, ">8")
        keyword += format(self.PM8, ">8")
        keyword += format(self.PM9, ">8")
        keyword += format(self.PM10, ">8")
        keyword += "\n"
        keyword += "$$  TET13V     RINRT\n"
        keyword += format(self.TET13V, ">10")
        keyword += format(self.RINRT, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_SOLID\n")
        stream.write("$$     ESORT    FMATRX   NIPTETS    SWLOCL    PSFAIL   T10JTOL      ICOH     TET13K\n")
        stream.write(format(self.ESORT, ">10"))
        stream.write(format(self.FMATRX, ">10"))
        stream.write(format(self.NIPTETS, ">10"))
        stream.write(format(self.SWLOCL, ">10"))
        stream.write(format(self.PSFAIL, ">10"))
        stream.write(format(self.T10JTOL, ">10.3f"))
        stream.write(format(self.ICOH, ">10"))
        stream.write(format(self.TET13K, ">10"))
        stream.write("\n")
        stream.write("$$   PM1     PM2     PM3     PM4     PM5     PM6     PM7     PM8     PM9    PM10\n")
        stream.write(format(self.PM1, ">8"))
        stream.write(format(self.PM2, ">8"))
        stream.write(format(self.PM3, ">8"))
        stream.write(format(self.PM4, ">8"))
        stream.write(format(self.PM5, ">8"))
        stream.write(format(self.PM6, ">8"))
        stream.write(format(self.PM7, ">8"))
        stream.write(format(self.PM8, ">8"))
        stream.write(format(self.PM9, ">8"))
        stream.write(format(self.PM10, ">8"))
        stream.write("\n")
        stream.write("$$  TET13V     RINRT\n")
        stream.write(format(self.TET13V, ">10"))
        stream.write(format(self.RINRT, ">10"))
        stream.write("\n")                            
    

class KooControlBulkViscosity:
    def __init__(self):
        self.Q1 = 1.5
        self.Q2 = 0.06
        self.TYPE = 1
        self.BTYPE = 0
        self.TSTYPE = 0
        
    def AddtoDynaKeyword(self, keyword : ControlBulkViscosity):
        keyword.SetControlBulkViscosity(self.Q1, self.Q2, self.TYPE, self.BTYPE, self.TSTYPE)

    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_BULK_VISCOSITY\n"
        keyword += "$$       Q1        Q2     TYPE    BTYPE   TSTYPE\n"
        keyword += format(self.Q1, ">10.3f")
        keyword += format(self.Q2, ">10.3f")
        keyword += format(self.TYPE, ">10")
        keyword += format(self.BTYPE, ">10")
        keyword += format(self.TSTYPE, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_BULK_VISCOSITY\n")
        stream.write("$$       Q1        Q2     TYPE    BTYPE   TSTYPE\n")
        stream.write(format(self.Q1, ">10.3f"))
        stream.write(format(self.Q2, ">10.3f"))
        stream.write(format(self.TYPE, ">10"))
        stream.write(format(self.BTYPE, ">10"))
        stream.write(format(self.TSTYPE, ">10"))
        stream.write("\n")        

class KooControlTermination:
    def __init__(self):
        self.ENDTIM = 0.0
        self.ENDCYC = 0
        self.DTMIN = 0.0
        self.ENDENG = 0.0
        self.ENDMAS = 1.0E+8
        self.NOSOL = 0
        
    def AddtoDynaKeyword(self, keyword : ControlTermination):
        keyword.SetControlTermination(self.ENDTIM, self.ENDCYC, self.DTMIN, self.ENDENG, self.ENDMAS, self.NOSOL)    
   
    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_TERMINATION\n"
        keyword += "$$  ENDTIM    ENDCYC     DTMIN     ENDENG     ENDMAS     NOSOL\n"
        keyword += format(self.ENDTIM, ">10.3e")
        keyword += format(self.ENDCYC, ">10")
        keyword += format(self.DTMIN, ">10.3e")
        keyword += format(self.ENDENG, ">10.3e")
        keyword += format(self.ENDMAS, ">10.3e")
        keyword += format(self.NOSOL, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_TERMINATION\n")
        stream.write("$$  ENDTIM    ENDCYC     DTMIN     ENDENG     ENDMAS     NOSOL\n")
        stream.write(format(self.ENDTIM, ">10.3e"))
        stream.write(format(self.ENDCYC, ">10"))
        stream.write(format(self.DTMIN, ">10.3e"))
        stream.write(format(self.ENDENG, ">10.3e"))
        stream.write(format(self.ENDMAS, ">10.3e"))
        stream.write(format(self.NOSOL, ">10"))
        stream.write("\n")
        
class KooControlTimeStep:
    def __init__(self,DTINIT,TSSFAC,ISDO=0,TSLIMT=0.0,DT2MS=0.0,LCTM=0,ERODE=0,MS1ST=0,DT2MSF="          ",DT2MSLC="          ",IMSCL=0,RMSCL=0.0,IHDO=0):

        self.DTINIT = DTINIT
        self.TSSFAC =TSSFAC
        self.ISDO = ISDO
        self.TSLIMT = TSLIMT
        self.DT2MS = DT2MS
        self.LCTM = LCTM
        self.ERODE = ERODE
        self.MS1ST = MS1ST
        self.DT2MSF = DT2MSF
        self.DT2MSLC = DT2MSLC
        self.IMSCL = IMSCL
        self.RMSCL = RMSCL
        self.IHDO = IHDO
    
    def AddtoDynaKeyword(self, keyword : ControlTimeStep):
        keyword.SetControlTimeStepwithOptional(self.DTINIT, self.TSSFAC, self.ISDO, self.TSLIMT, self.DT2MS, self.LCTM, self.ERODE, self.MS1ST, self.DT2MSF, self.DT2MSLC, self.IMSCL, self.RMSCL, self.IHDO)
        
    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_TIMESTEP\n"
        keyword += "$$  DTINIT    TSSFAC     ISDO    TSLIMT     DT2MS      LCTM     ERODE     MS1ST\n"
    
        keyword += format(self.DTINIT, ">10.3e")
        keyword += format(self.TSSFAC, ">10.3e")
        keyword += format(self.ISDO, ">10")
        keyword += format(self.TSLIMT, ">10.3e")
        keyword += format(self.DT2MS, ">10.3e")
        keyword += format(self.LCTM, ">10")
        keyword += format(self.ERODE, ">10")
        keyword += format(self.MS1ST, ">10")
        keyword += "\n"
        keyword += "$$  DT2MSF    DT2MSLC     IMSCL     RMSCL      IHDO\n"
        keyword += format(self.DT2MSF, ">10")
        keyword += format(self.DT2MSLC, ">10")
        keyword += format(self.IMSCL, ">10")
        keyword += "          "
        keyword += "          "
        keyword += format(self.RMSCL, ">10.3e")
        keyword += "          "
        keyword += format(self.IHDO, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_TIMESTEP\n")
        stream.write("$$  DTINIT    TSSFAC     ISDO    TSLIMT     DT2MS      LCTM     ERODE     MS1ST\n")
        stream.write(format(self.DTINIT, ">10.3e"))
        stream.write(format(self.TSSFAC, ">10.3e"))
        stream.write(format(self.ISDO, ">10"))
        stream.write(format(self.TSLIMT, ">10.3e"))
        stream.write(format(self.DT2MS, ">10.3e"))
        stream.write(format(self.LCTM, ">10"))
        stream.write(format(self.ERODE, ">10"))
        stream.write(format(self.MS1ST, ">10"))
        stream.write("\n")
        stream.write("$$  DT2MSF    DT2MSLC     IMSCL     RMSCL      IHDO\n")
        stream.write(format(self.DT2MSF, ">10"))
        stream.write(format(self.DT2MSLC, ">10"))
        stream.write(format(self.IMSCL, ">10"))
        stream.write("          ")
        stream.write("          ")
        stream.write(format(self.RMSCL, ">10.3f"))
        stream.write("          ")
        stream.write(format(self.IHDO, ">10"))
        stream.write("\n")
        
class KooControlHourglass:
    def __init__(self, IHQ=0,QH=0.1):
        self.IHQ = IHQ
        self.QH = QH        
        pass

    def AddtoDynaKeyword(self, keyword : ControlHourglass):
        keyword.SetControlHourglass(self.IHQ, self.QH)
        
    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_HOURGLASS\n"
        keyword += "$$     IHQ        QH\n"
        keyword += format(self.IHQ, ">10")
        keyword += format(self.QH, ">10.3f")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_HOURGLASS\n")
        stream.write("$$     IHQ        QH\n")
        stream.write(format(self.IHQ, ">10"))
        stream.write(format(self.QH, ">10.3f"))
        stream.write("\n")
        
class KooControlAccuracy:
    def __init__(self, OSU=0, INN=2, PIDOSU=0, IACC=0):
        self.OSU = OSU
        self.INN = INN
        self.PIDOSU = PIDOSU
        self.IACC = IACC

    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_ACCURACY\n"
        keyword += "$$     OSU       INN    PIDOSU      IACC\n"
        keyword += format(self.OSU, ">10")
        keyword += format(self.INN, ">10")
        keyword += format(self.PIDOSU, ">10")
        keyword += format(self.IACC, ">10")
        keyword += "\n"
        return keyword

    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_ACCURACY\n")
        stream.write("$$     OSU       INN    PIDOSU      IACC\n")
        stream.write(format(self.OSU, ">10"))
        stream.write(format(self.INN, ">10"))
        stream.write(format(self.PIDOSU, ">10"))
        stream.write(format(self.IACC, ">10"))
        stream.write("\n")

class KooControlDynamicRelaxation:
    def __init__(self, NRCYCK=250,DRTOL = 0.001, DRFCRT = 0.995, DRTERM = 1.0E99, TSSFDR = 0.0, IRELAL = 0, EDTTL = 0.0, IDRFLG = 0):
        self.NRCYCK = NRCYCK
        self.DRTOL = DRTOL
        self.DRFCRT = DRFCRT
        self.DRTERM = DRTERM
        self.TSSFDR = TSSFDR
        self.IRELAL = IRELAL
        self.EDTTL = EDTTL
        self.IDRFLG = IDRFLG
        
    def AddtoDynaKeyword(self, keyword : ControlDynamicRelaxation):
        keyword.SetControlDynamicRelaxation(self.NRCYCK, self.DRTOL, self.DRFCRT, self.DRTERM, self.TSSFDR, self.IRELAL, self.EDTTL, self.IDRFLG)
        
    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_DYNAMIC_RELAXATION\n"
        keyword += "$$   NRCYCK     DRTOL    DRFCRT    DRTERM   TSSFDR   IRELAL    EDTTL    IDRFLG\n"
        keyword += format(self.NRCYCK, ">10")
        keyword += format(self.DRTOL, ">10.3f")
        keyword += format(self.DRFCRT, ">10.3f")
        keyword += format(self.DRTERM, ">10.3e")
        keyword += format(self.TSSFDR, ">10.3f")
        keyword += format(self.IRELAL, ">10")
        keyword += format(self.EDTTL, ">10.3f")
        keyword += format(self.IDRFLG, ">10")
        keyword += "\n"
        return keyword
        
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_DYNAMIC_RELAXATION\n")
        stream.write("$$   NRCYCK     DRTOL    DRFCRT    DRTERM   TSSFDR   IRELAL    EDTTL    IDRFLG\n")
        stream.write(format(self.NRCYCK, ">10"))
        stream.write(format(self.DRTOL, ">10.3f"))
        stream.write(format(self.DRFCRT, ">10.3f"))
        stream.write(format(self.DRTERM, ">10.3e"))
        stream.write(format(self.TSSFDR, ">10.3f"))
        stream.write(format(self.IRELAL, ">10"))
        stream.write(format(self.EDTTL, ">10.3f"))
        stream.write(format(self.IDRFLG, ">10"))
        stream.write("\n")

class KooControlEnergy:
    def __init__(self,HGEN=1,RWEN=2,SLNTEN=1,RYLEN=1,IRGEN=2,MATEN=1):
        self.HGEN = HGEN
        self.RWEN = RWEN
        self.SLNTEN = SLNTEN
        self.RYLEN = RYLEN
        self.IRGEN = IRGEN
        self.MATEN = MATEN        
    
    def AddtoDynaKeyword(self, keyword : ControlEnergy):
        keyword.SetControlEnergy(self.HGEN, self.RWEN, self.SLNTEN, self.RYLEN, self.IRGEN, self.MATEN)
    
    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_ENERGY\n"
        keyword += "$$    HGEN      RWEN    SLNTEN     RYLEN     IRGEN     MATEN\n"
        keyword += format(self.HGEN, ">10")
        keyword += format(self.RWEN, ">10")
        keyword += format(self.SLNTEN, ">10")
        keyword += format(self.RYLEN, ">10")
        keyword += format(self.IRGEN, ">10")
        keyword += format(self.MATEN, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_ENERGY\n")
        stream.write("$$    HGEN      RWEN    SLNTEN     RYLEN     IRGEN     MATEN\n")
        stream.write(format(self.HGEN, ">10"))
        stream.write(format(self.RWEN, ">10"))
        stream.write(format(self.SLNTEN, ">10"))
        stream.write(format(self.RYLEN, ">10"))
        stream.write(format(self.IRGEN, ">10"))
        stream.write(format(self.MATEN, ">10"))
        stream.write("\n")
    
class KooControlContact:
    def __init__(self, SLSFAC=0.1, RWPNAL=0.0, ISLCHK=1, SHLTHK=0, PENOPT=1, THKCHG=0, ORIEN=1, ENMASS=0, USRSTR=0, USRFRC=0, NSBCS=100, INTERM=0, XPENE=4.0, SSTHK=0, ECDT=0, TIEDPRJ=0, SFRIC=0.0, DFRIC=0.0, EDC=0.0, VFC=0.0, TH=0.0, TH_SF=0.0, PEN_SF=0.0, PTSCL=1.0, IGNORE=0, FRCENG=0, SKIPRWG=0, OUTSEG=0, SPOTSTP=0, SPOTDEL=0, SPOTHIN=0.0, ISYM=0, NSEROD=0, RWGAPS=0, RWGDTH=0.0, RWKSF=1.0, ICOV=0, SWRADF=0.0, ITHOFF=0, SHLEDG=0, PSTIFF=0, ITHCNT=0, TDCNOF=0, FTALL=0, UNUSED="", SHLTRW=0.0, IGACTC=0):
        self.SLSFAC = SLSFAC
        self.RWPNAL = RWPNAL
        self.ISLCHK = ISLCHK
        self.SHLTHK = SHLTHK
        self.PENOPT = PENOPT
        self.THKCHG = THKCHG
        self.ORIEN = ORIEN
        self.ENMASS = ENMASS
        
        self.USRSTR = USRSTR
        self.USRFRC = USRFRC
        self.NSBCS = NSBCS
        self.INTERM = INTERM
        self.XPENE = XPENE
        self.SSTHK = SSTHK
        self.ECDT = ECDT
        self.TIEDPRJ = TIEDPRJ
        
        self.SFRIC = SFRIC
        self.DFRIC = DFRIC
        self.EDC = EDC
        self.VFC = VFC
        self.TH = TH
        self.TH_SF = TH_SF
        self.PEN_SF = PEN_SF                            
        self.PTSCL = PTSCL         
        
        self.IGNORE = IGNORE
        self.FRCENG = FRCENG
        self.SKIPRWG = SKIPRWG
        self.OUTSEG = OUTSEG
        self.SPOTSTP = SPOTSTP
        self.SPOTDEL = SPOTDEL
        self.SPOTHIN = SPOTHIN
        
        self.ISYM = ISYM
        self.NSEROD = NSEROD
        self.RWGAPS = RWGAPS
        self.RWGDTH = RWGDTH
        self.RWKSF = RWKSF
        self.ICOV = ICOV
        self.SWRADF = SWRADF
        self.ITHOFF = ITHOFF
        
        self.SHLEDG = SHLEDG
        self.PSTIFF = PSTIFF        
        self.ITHCNT = ITHCNT
        self.TDCNOF = TDCNOF
        self.FTALL = FTALL
        self.SHLTRW = SHLTRW
        self.IGACTC = IGACTC
        
       

    def AddtoDynaKeyword(self, keyword : ControlContact):
        keyword.SetControlContact(self.SLSFAC, self.RWPNAL, self.ISLCHK, self.SHLTHK, self.PENOPT, self.THKCHG, self.ORIEN, self.ENMASS, self.USRSTR, self.USRFRC, self.NSBCS, self.INTERM, self.XPENE, self.SSTHK, self.ECDT, self.TIEDPRJ, self.SFRIC, self.DFRIC, self.edc, self.vfc, self.th, self.th_sf, self.pen_sf, self.ignore, self.frceng, self.skiprwg, self.outseg, self.spotstp, self.spotdel, self.spothin, self.isym, self.nserod, self.rwgaps, self.rwgdth, self.rwksf, self.icov, self.swradf, self.ithoff, self.shledg, self.pstiff, self.ithcnt, self.tdcnof, self.ftall, self.unused, self.shltrw, self.igactc)        

    def GenerateDynaKeyword(self):
        keyword = "*CONTROL_CONTACT\n"
        keyword += "$$    SLSFAC    RWPNAL    ISLCHK    SHLTHK    PENOPT    THKCHG     ORIEN    ENMASS\n"
                
        keyword += format(self.SLSFAC, ">10.3e")
        keyword += format(self.RWPNAL, ">10.3e")
        keyword += format(self.ISLCHK, ">10")
        keyword += format(self.SHLTHK, ">10")
        keyword += format(self.PENOPT, ">10")
        keyword += format(self.THKCHG, ">10")
        keyword += format(self.ORIEN, ">10")
        keyword += format(self.ENMASS, ">10")        
        keyword += "\n" 
        keyword += "$$    USRSTR    USRFRC     NSBCS    INTERM     XPENE     SSTHK      ECDT   TIEDPRJ\n"
        keyword += format(self.USRSTR, ">10")
        keyword += format(self.USRFRC, ">10")
        keyword += format(self.NSBCS, ">10")    
        keyword += format(self.INTERM, ">10")
        keyword += format(self.XPENE, ">10.3e")            
        keyword += format(self.SSTHK, ">10")
        keyword += format(self.ECDT, ">10")
        keyword += format(self.TIEDPRJ, ">10")
        keyword += "\n"
        keyword += "$$     SFRIC     DFRIC       edc       vfc        th     th_sf    pen_sf    ignore\n"
        keyword += format(self.SFRIC, ">10.3e")
        keyword += format(self.DFRIC, ">10.3e") 
        keyword += format(self.EDC, ">10.3e")
        keyword += format(self.VFC, ">10.3e")
        keyword += format(self.TH, ">10.3e")
        keyword += format(self.TH_SF, ">10.3e")
        keyword += format(self.PEN_SF, ">10.3e")
        keyword += format(self.PTSCL, ">10.3e")        
        keyword += "\n"
        keyword += "$$  IGNORE    FRCENG   SKIPRWG    OUTSEG   SPOTSTP   SPOTDEL   SPOTHIN      ISYM    NSEROD\n"
        keyword += format(self.IGNORE, ">10")
        keyword += format(self.FRCENG, ">10")
        keyword += format(self.SKIPRWG, ">10")
        keyword += format(self.OUTSEG, ">10")   
        keyword += format(self.SPOTSTP, ">10")  
        keyword += format(self.SPOTDEL, ">10")  
        keyword += format(self.SPOTHIN, ">10.3e")
        keyword += "\n"
        keyword += "$$    ISYM   NSEROD    RWGAPS    RWGDTH     RWKSF      ICOV    SWRADF    ITHOFF\n"
        keyword += format(self.ISYM, ">10")
        keyword += format(self.NSEROD, ">10")
        keyword += format(self.RWGAPS, ">10")
        keyword += format(self.RWGDTH, ">10.3e")
        keyword += format(self.RWKSF, ">10.3e")
        keyword += format(self.ICOV, ">10")
        keyword += format(self.SWRADF, ">10.3e")
        keyword += format(self.ITHOFF, ">10")
        
        keyword += "\n"
        keyword += "$$   SHLEDG    PSTIFF    ITHCNT    TDCNOF     FTALL    UNUSED    SHLTRW    IGACTC\n"
        keyword += format(self.SHLEDG, ">10")
        keyword += format(self.PSTIFF, ">10")
        keyword += format(self.ITHCNT, ">10")
        keyword += format(self.TDCNOF, ">10")
        keyword += format(self.FTALL, ">10")
        keyword += "          "
        keyword += format(self.SHLTRW, ">10")
        keyword += format(self.IGACTC, ">10")
        keyword += "\n"
        return keyword     
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*CONTROL_CONTACT\n")
        stream.write("$$    SLSFAC    RWPNAL    ISLCHK    SHLTHK    PENOPT    THKCHG     ORIEN    ENMASS\n")
                
        stream.write(format(self.SLSFAC, ">10.3e"))
        stream.write(format(self.RWPNAL, ">10.3e"))
        stream.write(format(self.ISLCHK, ">10"))
        stream.write(format(self.SHLTHK, ">10"))
        stream.write(format(self.PENOPT, ">10"))
        stream.write(format(self.THKCHG, ">10"))
        stream.write(format(self.ORIEN, ">10"))
        stream.write(format(self.ENMASS, ">10"))        
        stream.write("\n" )
        stream.write("$$    USRSTR    USRFRC     NSBCS    INTERM     XPENE     SSTHK      ECDT   TIEDPRJ\n")
        stream.write(format(self.USRSTR, ">10"))
        stream.write(format(self.USRFRC, ">10"))
        stream.write(format(self.NSBCS, ">10"))  
        stream.write(format(self.INTERM, ">10"))
        stream.write(format(self.XPENE, ">10.3e"))            
        stream.write(format(self.SSTHK, ">10"))
        stream.write(format(self.ECDT, ">10"))
        stream.write(format(self.TIEDPRJ, ">10"))
        stream.write("\n")
        stream.write("$$     SFRIC     DFRIC       edc       vfc        th     th_sf    pen_sf    ignore\n")
        stream.write(format(self.SFRIC, ">10.3e"))
        stream.write(format(self.DFRIC, ">10.3e"))
        stream.write(format(self.EDC, ">10.3e"))
        stream.write(format(self.VFC, ">10.3e"))
        stream.write(format(self.TH, ">10.3e"))
        stream.write(format(self.TH_SF, ">10.3e"))
        stream.write(format(self.PEN_SF, ">10.3e"))
        stream.write(format(self.PTSCL, ">10.3e"))      
        stream.write("\n")
        stream.write("$$  IGNORE    FRCENG   SKIPRWG    OUTSEG   SPOTSTP   SPOTDEL   SPOTHIN      ISYM    NSEROD\n")
        stream.write(format(self.IGNORE, ">10"))
        stream.write(format(self.FRCENG, ">10"))
        stream.write(format(self.SKIPRWG, ">10"))
        stream.write(format(self.OUTSEG, ">10"))   
        stream.write(format(self.SPOTSTP, ">10"))  
        stream.write(format(self.SPOTDEL, ">10"))  
        stream.write(format(self.SPOTHIN, ">10.3e"))
        stream.write("\n")
        stream.write("$$    ISYM   NSEROD    RWGAPS    RWGDTH     RWKSF      ICOV    SWRADF    ITHOFF\n")
        stream.write(format(self.ISYM, ">10"))
        stream.write(format(self.NSEROD, ">10"))
        stream.write(format(self.RWGAPS, ">10"))
        stream.write(format(self.RWGDTH, ">10.3e"))
        stream.write(format(self.RWKSF, ">10.3e"))
        stream.write(format(self.ICOV, ">10"))
        stream.write(format(self.SWRADF, ">10.3e"))
        stream.write(format(self.ITHOFF, ">10"))
        
        stream.write("\n")
        stream.write("$$   SHLEDG    PSTIFF    ITHCNT    TDCNOF     FTALL    UNUSED    SHLTRW    IGACTC\n")
        stream.write(format(self.SHLEDG, ">10"))
        stream.write(format(self.PSTIFF, ">10"))
        stream.write(format(self.ITHCNT, ">10"))
        stream.write(format(self.TDCNOF, ">10"))
        stream.write(format(self.FTALL, ">10"))
        stream.write("          ")
        stream.write(format(self.SHLTRW, ">10"))
        stream.write(format(self.IGACTC, ">10"))
        stream.write("\n")
        
class KooControlManager:
    def __init__(self):
        self.controlOutput = None
        self.controlShell = None
        self.controlSolid = None
        self.controlBulkViscosity = None
        self.controlTermination = None
        self.controlTimeStep = None
        self.controlHourglass = None
        self.controlenergy = None
        self.controlContact = None
        self.controlMppIONodump = None
        self.controlDynamicRelaxation = None
        self.controlAccuracy = None

    def clear(self):
        self.controlOutput = None
        self.controlShell = None
        self.controlSolid = None
        self.controlBulkViscosity = None
        self.controlTermination = None
        self.controlTimeStep = None
        self.controlHourglass = None
        self.controlenergy = None
        self.controlContact = None
        self.controlMppIONodump = None
        self.controlDynamicRelaxation = None
        self.controlAccuracy = None

    def OverwritefromControlManager(self, controlManager : KooControlManager):
        if controlManager.controlOutput is not None:
            self.controlOutput = controlManager.controlOutput
        if controlManager.controlShell is not None:
            self.controlShell = controlManager.controlShell
        if controlManager.controlSolid is not None:
            self.controlSolid = controlManager.controlSolid        
        if controlManager.controlBulkViscosity is not None:
            self.controlBulkViscosity = controlManager.controlBulkViscosity         
        if controlManager.controlTermination is not None:
            self.controlTermination = controlManager.controlTermination
        if controlManager.controlTimeStep is not None:
            self.controlTimeStep = controlManager.controlTimeStep
        if controlManager.controlHourglass is not None:
            self.controlHourglass = controlManager.controlHourglass
        if controlManager.controlenergy is not None:
            self.controlenergy = controlManager.controlenergy
        if controlManager.controlContact is not None:
            self.controlContact = controlManager.controlContact
        if controlManager.controlMppIONodump is not None:
            self.controlMppIONodump = controlManager.controlMppIONodump
        if controlManager.controlDynamicRelaxation is not None:
            self.controlDynamicRelaxation = controlManager.controlDynamicRelaxation
        if controlManager.controlAccuracy is not None:
            self.controlAccuracy = controlManager.controlAccuracy

    def SetControlBulkViscosity(self,Q1=1.5, Q2=0.06, TYPE=1, BTYPE=0, TSTYPE=0):
        self.controlBulkViscosity : KooControlBulkViscosity = KooControlBulkViscosity()
        self.controlBulkViscosity.Q1 = Q1
        self.controlBulkViscosity.Q2 = Q2
        self.controlBulkViscosity.TYPE = TYPE
        self.controlBulkViscosity.BTYPE = BTYPE
        self.controlBulkViscosity.TSTYPE = TSTYPE   
    
    def SetControlTermination(self,ENDTIM, ENDCYC, DTMIN, ENDENG, ENDMAS, NOSOL):
        self.controlTermination : KooControlTermination = KooControlTermination()
        self.controlTermination.ENDTIM = ENDTIM
        self.controlTermination.ENDCYC = ENDCYC
        self.controlTermination.DTMIN = DTMIN
        self.controlTermination.ENDENG = ENDENG
        self.controlTermination.ENDMAS = ENDMAS
        self.controlTermination.NOSOL = NOSOL
    
    def SetControlTimeStep(self,DTINIT,TSSFAC,ISDO=0,TSLIMT=0.0,DT2MS=0.0,LCTM=0,ERODE=0,MS1ST=0,DT2MSF="          ",DT2MSLC="          ",IMSCL=0,RMSCL=0.0,IHDO=0):
        self.controlTimeStep : KooControlTimeStep = KooControlTimeStep(0.0,0.0)
        self.controlTimeStep = KooControlTimeStep(DTINIT,TSSFAC,ISDO,TSLIMT,DT2MS,LCTM,ERODE,MS1ST,DT2MSF,DT2MSLC,IMSCL,RMSCL,IHDO)
    
    def SetControlHourglass(self,IHQ=0,QH=0.1):
        self.controlHourglass = KooControlHourglass(IHQ,QH)
    
    def SetControlDynamicRelaxation(self,NRCYCK=250,DRTOL = 0.001, DRFCRT = 0.995, DRTERM = 1.0E99, TSSFDR = 0.0, IRELAL = 0, EDTTL = 0.0, IDRFLG = 0):
        self.controlDynamicRelaxation = KooControlDynamicRelaxation(NRCYCK,DRTOL,DRFCRT,DRTERM,TSSFDR,IRELAL,EDTTL,IDRFLG)
        
    def SetControlEnergy(self,HGEN=1,RWEN=2,SLNTEN=1,RYLEN=1,IRGEN=2,MATEN=1):
        self.controlenergy = KooControlEnergy(HGEN,RWEN,SLNTEN,RYLEN,IRGEN,MATEN)

    def SetControlAccuracy(self, OSU=0, INN=2, PIDOSU=0, IACC=0):
        self.controlAccuracy = KooControlAccuracy(OSU, INN, PIDOSU, IACC)
    
    def SetControlContact(self, SLSFAC=0.1, RWPNAL=0.0, ISLCHK=1, SHLTHK=0, PENOPT=1, THKCHG=0, ORIEN=1, ENMASS=0, USRSTR=0, USRFRC=0, NSBCS=100, INTERM=0, XPENE=4.0, SSTHK=0, ECDT=0, TIEDPRJ=0, SFRIC=0.0, DFRIC=0.0, EDC=0.0, VFC=0.0, TH=0.0, TH_SF=0.0, PEN_SF=0.0, PTSCL=1.0, IGNORE=0, FRCENG=0, SKIPRWG=0, OUTSEG=0, SPOTSTP=0, SPOTDEL=0, SPOTHIN=0.0, ISYM=0, NSEROD=0, RWGAPS=0, RWGDTH=0.0, RWKSF=1.0, ICOV=0, SWRADF=0.0, ITHOFF=0, SHLEDG=0, PSTIFF=0, ITHCNT=0, TDCNOF=0, FTALL=0, UNUSED="", SHLTRW=0.0, IGACTC=0):
        self.controlContact = KooControlContact(SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS, USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ, SFRIC, DFRIC, EDC, VFC, TH, TH_SF, PEN_SF, PTSCL, IGNORE, FRCENG, SKIPRWG, OUTSEG, SPOTSTP, SPOTDEL, SPOTHIN, ISYM, NSEROD, RWGAPS, RWGDTH, RWKSF, ICOV, SWRADF, ITHOFF, SHLEDG, PSTIFF, ITHCNT, TDCNOF, FTALL, UNUSED, SHLTRW, IGACTC)
    
    def SetControlMPPIoNodump(self):
        self.controlMppIONodump = KooControlMppIONodump()
    
    def SetControlfromDyna(self, controlKeyword):
        if controlKeyword[0] == "*CONTROL_SHELL":        
            self.controlShell = KooControlShell()
            Line1 = controlKeyword[1]
            self.controlShell.WRPANG = KooDynaFloat(Line1[0],20.0)
            self.controlShell.ESORT = KooDynaInt(Line1[1],0)
            self.controlShell.IRNXX = KooDynaInt(Line1[2],-1)
            self.controlShell.ISTUPD = KooDynaInt(Line1[3],0)
            self.controlShell.THEORY = KooDynaInt(Line1[4],2)
            self.controlShell.BWC = KooDynaInt(Line1[5],2)
            self.controlShell.MITER = KooDynaInt(Line1[6],1)
            self.controlShell.PROJ = KooDynaInt(Line1[7],0)
            if len(controlKeyword) > 2:
                Line2 = controlKeyword[2]
                self.controlShell.ROTASCL = KooDynaFloat(Line2[0],1.0)
                self.controlShell.INTGRD = KooDynaInt(Line2[1],0)
                self.controlShell.LAMSHT = KooDynaInt(Line2[2],0)
                self.controlShell.CSTYP6 = KooDynaInt(Line2[3],1)
                self.controlShell.THSHEL = KooDynaInt(Line2[4],0)
            if len(controlKeyword) > 3:
                Line3 = controlKeyword[3]            
                self.controlShell.PSTUPD = KooDynaInt(Line3[0],0)
                self.controlShell.SIDT4TU = KooDynaInt(Line3[1],0)
                self.controlShell.CNTCO = KooDynaInt(Line3[2],0)
                self.controlShell.ITSFLG = KooDynaInt(Line3[3],0)
                self.controlShell.IRQUAD = KooDynaInt(Line3[4],0)
                self.controlShell.W_MODE = KooDynaFloat(Line3[5],"")
                self.controlShell.STRETCH = KooDynaFloat(Line3[6],"")
                self.controlShell.ICRQ = KooDynaInt(Line3[7],0)
            if len(controlKeyword) > 4:
                Line4 = controlKeyword[4]
                self.controlShell.NFAIL1 = KooDynaInt(Line4[0],"")
                self.controlShell.NFAIL4 = KooDynaInt(Line4[1],"")
                self.controlShell.PSNFAIL = KooDynaInt(Line4[2],0)
                self.controlShell.KEEPCS = KooDynaInt(Line4[3],0)
                self.controlShell.DELFR = KooDynaInt(Line4[4],0)
                self.controlShell.DRCPSID = KooDynaInt(Line4[5],0)
                self.controlShell.DRCPRM = KooDynaFloat(Line4[6],1.0)
                self.controlShell.INTPERR = ""
            if len(controlKeyword) > 5:
                Line5 = controlKeyword[5]
                self.controlShell.DRCMTH = KooDynaInt(Line5[0],0)
                self.controlShell.LISPSID = KooDynaInt(Line5[1],0)
                self.controlShell.NLOCDT = KooDynaInt(Line5[2],0)
        elif controlKeyword[0] == "*CONTROL_SOLID":
            self.controlSolid = KooControlSolid()
            Line1 = controlKeyword[1]
            self.controlSolid.ESORT = KooDynaInt(Line1[0],0)
            self.controlSolid.FMATRX = KooDynaInt(Line1[1],0)
            self.controlSolid.NIPTETS = KooDynaInt(Line1[2],0)
            self.controlSolid.SWLOCL = KooDynaInt(Line1[3],0)
            self.controlSolid.PSFAIL = KooDynaInt(Line1[4],0)
            self.controlSolid.T10JTOL = KooDynaFloat(Line1[5],0.0)
            self.controlSolid.ICOH = KooDynaInt(Line1[6],0)
            self.controlSolid.TET13K = KooDynaInt(Line1[7],0)
            if len(controlKeyword) > 2:
                Line2 = controlKeyword[2] 
                self.PM1 = KooDynaInt(Line2[0],"")
                self.PM2 = KooDynaInt(Line2[1],"")
                self.PM3 = KooDynaInt(Line2[2],"")
                self.PM4 = KooDynaInt(Line2[3],"")
                self.PM5 = KooDynaInt(Line2[4],"")
                self.PM6 = KooDynaInt(Line2[5],"")
                self.PM7 = KooDynaInt(Line2[6],"")
                self.PM8 = KooDynaInt(Line2[7],"")
                self.PM9 = KooDynaInt(Line2[8],"")
                self.PM10 = KooDynaInt(Line2[9],"")
            if len(controlKeyword) > 3:
                Line3 = controlKeyword[3]
                self.TET13V = KooDynaInt(Line3[0],0)
                self.RINRT = KooDynaInt(Line3[1],0)
              
        elif controlKeyword[0] == "*CONTROL_OUTPUT":
            Line1 = controlKeyword[1]
            self.controlOutput = KooControlOutput()
            self.controlOutput.NPOPT = KooDynaInt(Line1[0], 0)
            self.controlOutput.NEECHO = KooDynaInt(Line1[1], 0)
            self.controlOutput.NREFUP = KooDynaInt(Line1[2], 0)
            self.controlOutput.IACCOP = KooDynaInt(Line1[3], 0)
            self.controlOutput.OPIFS = KooDynaFloat(Line1[4], 0.0)
            self.controlOutput.IPNINT = KooDynaInt(Line1[5], 0)
            self.controlOutput.IKEDIT = KooDynaInt(Line1[6], 100)
            self.controlOutput.IFLUSH = KooDynaInt(Line1[7], 5000)
            if len(controlKeyword) > 2:
                Line2 = controlKeyword[2]
                self.controlOutput.IPRTF = KooDynaInt(Line2[0], 0)
                self.controlOutput.IERODE = KooDynaInt(Line2[1], 0)
                self.controlOutput.TET10S8 = KooDynaInt(Line2[2], 2)
                self.controlOutput.MSGMAX = KooDynaInt(Line2[3], 50)
                self.controlOutput.IPCURV = KooDynaInt(Line2[4], 0)
                self.controlOutput.GMDT = KooDynaFloat(Line2[5],0.0)
                self.controlOutput.IP1DBLT = KooDynaInt(Line2[6],0)
                self.controlOutput.EOCS = KooDynaInt(Line2[7],0)
            if len(controlKeyword) > 3:
                Line3 = controlKeyword[3]
                self.controlOutput.TOLEV = KooDynaInt(Line3[0],2)
                self.controlOutput.NEWLEG = KooDynaInt(Line3[1],0)
                self.controlOutput.FRFREQ = KooDynaInt(Line3[2],1)
                self.controlOutput.MINFO = KooDynaInt(Line3[3],0)
                self.controlOutput.SOLSIG = KooDynaInt(Line3[4],0)
                self.controlOutput.MSGFLG = KooDynaInt(Line3[5],0)
                self.controlOutput.CDETOL = KooDynaFloat(Line3[6],10.0)
                self.controlOutput.IGEOM = KooDynaInt(Line3[7],1)
            if len(controlKeyword) > 4:
                Line4 = controlKeyword[4]
                self.controlOutput.PHSCHNG = KooDynaInt(Line4[0],0)
                self.controlOutput.DEMDEN = KooDynaInt(Line4[1],0)
                self.controlOutput.ICRFILE = KooDynaInt(Line4[2],0)
                self.controlOutput.SPC2BND = KooDynaInt(Line4[3],0)
                self.controlOutput.PENOUT = KooDynaInt(Line4[4],0)
                self.controlOutput.SHLSIG = KooDynaInt(Line4[5],0)
                self.controlOutput.HISNOUT = KooDynaInt(Line4[6],0)
                self.controlOutput.ENGOUT = KooDynaInt(Line4[7],0)
            if len(controlKeyword) > 5:
                Line5 = controlKeyword[5]
                self.controlOutput.INSF = KooDynaInt(Line5[0],0)
                self.controlOutput.ISOLSF = KooDynaInt(Line5[1],0)
                self.controlOutput.IBSF = KooDynaInt(Line5[2],0)
                self.controlOutput.ISSF = KooDynaInt(Line5[3],0)
                self.controlOutput.MLKBAG = KooDynaInt(Line5[4],0)
                
        elif controlKeyword[0] == "*CONTROL_BULK_VISCOSITY":
            parameter = controlKeyword[1]
            if len(parameter[0]) == 0:
                parameter[0] = "1.5"
            if len(parameter[1]) == 0:
                parameter[1] = "0.06"
            if len(parameter[2]) == 0:
                parameter[2] = "1"
            if len(parameter[3]) == 0:
                parameter[3] = "0"
            if len(parameter[4]) == 0:
                parameter[4] = "0"
            self.controlBulkViscosity = KooControlBulkViscosity()
            self.controlBulkViscosity.Q1 = KooDynaFloat(parameter[0])
            self.controlBulkViscosity.Q2 = KooDynaFloat(parameter[1])
            self.controlBulkViscosity.TYPE = KooDynaInt(parameter[2])
            self.controlBulkViscosity.BTYPE = KooDynaInt(parameter[3])
            self.controlBulkViscosity.TSTYPE = KooDynaInt(parameter[4])
            
        elif controlKeyword[0] == "*CONTROL_TERMINATION":
            parameter = controlKeyword[1]
            if len(parameter[0]) == 0:
                parameter[0] = "0.0"
            if len(parameter[1]) == 0:
                parameter[1] = "0"
            if len(parameter[2]) == 0:
                parameter[2] = "0.0"
            if len(parameter[3]) == 0:
                parameter[3] = "0.0"
            if len(parameter[4]) == 0:
                parameter[4] = "1.0E+8"
            if len(parameter[5]) == 0:
                parameter[5] = "0"
            self.controlTermination = KooControlTermination()
            self.controlTermination.ENDTIM = KooDynaFloat(parameter[0])
            self.controlTermination.ENDCYC = KooDynaInt(parameter[1])
            self.controlTermination.DTMIN = KooDynaFloat(parameter[2])
            self.controlTermination.ENDENG = KooDynaFloat(parameter[3])
            self.controlTermination.ENDMAS = KooDynaFloat(parameter[4])
            self.controlTermination.NOSOL = KooDynaInt(parameter[5])
        elif controlKeyword[0] == "*CONTROL_TIMESTEP":
            parameter = controlKeyword[1]
            if len(parameter[0]) == 0:
                parameter[0] = "0.0"
            if len(parameter[1]) == 0:
                parameter[1] = "0.0"
            if len(parameter[2]) == 0:
                parameter[2] = "0"
            if len(parameter[3]) == 0:
                parameter[3] = "0.0"
            if len(parameter[4]) == 0:
                parameter[4] = "0.0"
            if len(parameter[5]) == 0:
                parameter[5] = "0"
            if len(parameter[6]) == 0:
                parameter[6] = "0"
            if len(parameter[7]) == 0:
                parameter[7] = "0"            
            
            self.controlTimeStep = KooControlTimeStep(0.0,0.0)                
            self.controlTimeStep.DTINIT = KooDynaFloat(parameter[0])
            self.controlTimeStep.TSSFAC = KooDynaFloat(parameter[1])
            self.controlTimeStep.ISDO = KooDynaInt(parameter[2])
            self.controlTimeStep.TSLIMT = KooDynaFloat(parameter[3])
            self.controlTimeStep.DT2MS = KooDynaFloat(parameter[4])
            self.controlTimeStep.LCTM = KooDynaInt(parameter[5])
            self.controlTimeStep.ERODE = KooDynaInt(parameter[6])
            self.controlTimeStep.MS1ST = KooDynaInt(parameter[7])
            if len(controlKeyword) > 2:
                parameter = controlKeyword[2]
                if len(parameter[0]) == 0:
                    parameter[0] = "          "
                if len(parameter[1]) == 0:
                    parameter[1] = "          "
                if len(parameter[2]) == 0:
                    parameter[2] = "0"
                if len(parameter[5]) == 0:
                    parameter[5] = "0"
                if len(parameter[7]) == 0:
                    parameter[7] = "0"
                    
                self.controlTimeStep.DT2MSF = KooDynaFloat(parameter[0])
                self.controlTimeStep.DT2MSLC = KooDynaInt(parameter[1])
                self.controlTimeStep.IMSCL = KooDynaInt(parameter[2])
                self.controlTimeStep.RMSCL = KooDynaFloat(parameter[5])
                self.controlTimeStep.IHDO = KooDynaInt(parameter[7])                                        
        elif controlKeyword[0] == "*CONTROL_DYNAMIC_RELAXATION":
            parameter = controlKeyword[1] 
            NRCYCK = KooDynaInt(parameter[0], 250)
            DRTOL = KooDynaFloat(parameter[1], 0.001)
            DRFCRT = KooDynaFloat(parameter[2], 0.995)        
            DRTERM = KooDynaFloat(parameter[3], 1.0E99)
            TSSFDR = KooDynaFloat(parameter[4], 0.0)
            IRELAL = KooDynaInt(parameter[5], 0)
            EDTTL = KooDynaFloat(parameter[6], 0.0)
            IDRFLG = KooDynaInt(parameter[7], 0) 
            self.controlDynamicRelaxation = KooControlDynamicRelaxation(NRCYCK, DRTOL, DRFCRT, DRTERM, TSSFDR, IRELAL, EDTTL, IDRFLG)
        
        elif controlKeyword[0] == "*CONTROL_HOURGLASS":
            parameter = controlKeyword[1]
            if len(parameter[0]) == 0:
                parameter[0] = "0"
            if len(parameter[1]) == 0:
                parameter[1] = "0.1"
            self.controlHourglass = KooControlHourglass()
            self.controlHourglass.IHQ = KooDynaInt(parameter[0])
            self.controlHourglass.QH = KooDynaFloat(parameter[1])
        elif controlKeyword[0] == "*CONTROL_ACCURACY":
            parameter = controlKeyword[1]
            self.controlAccuracy = KooControlAccuracy()
            self.controlAccuracy.OSU = KooDynaInt(parameter[0], 0)
            self.controlAccuracy.INN = KooDynaInt(parameter[1], 2)
            self.controlAccuracy.PIDOSU = KooDynaInt(parameter[2], 0)
            self.controlAccuracy.IACC = KooDynaInt(parameter[3], 0)
        elif controlKeyword[0] == "*CONTROL_ENERGY":
            parameter = controlKeyword[1]
            if len(parameter[0]) == 0:
                parameter[0] = "1"
            if len(parameter[1]) == 0:
                parameter[1] = "2"
            if len(parameter[2]) == 0:
                parameter[2] = "1"
            if len(parameter[3]) == 0:
                parameter[3] = "1"
            if len(parameter[4]) == 0:
                parameter[4] = "2"
            if len(parameter[5]) == 0:
                parameter[5] = "1"
                
            self.controlenergy = KooControlEnergy()
            self.controlenergy.HGEN = KooDynaInt(parameter[0])
            self.controlenergy.RWEN = KooDynaInt(parameter[1])
            self.controlenergy.SLNTEN = KooDynaInt(parameter[2])
            self.controlenergy.RYLEN = KooDynaInt(parameter[3])
            self.controlenergy.IRGEN = KooDynaInt(parameter[4])
            self.controlenergy.MATEN = KooDynaInt(parameter[5])                    
        elif controlKeyword[0] == "*CONTROL_CONTACT":
            parameter = controlKeyword[1]
            SLSFAC = KooDynaFloat(parameter[0])
            RWPNAL = KooDynaFloat(parameter[1],0.0)
            ISLCHK = KooDynaInt(parameter[2])  
            SHLTHK = KooDynaInt(parameter[3])
            PENOPT = KooDynaInt(parameter[4])
            THKCHG = KooDynaInt(parameter[5])
            ORIEN = KooDynaInt(parameter[6])
            ENMASS = KooDynaInt(parameter[7])
            parameter = controlKeyword[2]
            USRSTR = KooDynaInt(parameter[0])
            USRFRC = KooDynaInt(parameter[1])
            NSBCS = KooDynaInt(parameter[2])
            INTERM = KooDynaInt(parameter[3])
            XPENE = KooDynaFloat(parameter[4])
            SSTHK = KooDynaInt(parameter[5])
            ECDT = KooDynaInt(parameter[6])
            TIEDPRJ = KooDynaInt(parameter[7])
            if len(controlKeyword)>3:
                parameter = controlKeyword[3]
                SFRIC = KooDynaFloat(parameter[0])
                DFRIC = KooDynaFloat(parameter[1])
                EDC = KooDynaFloat(parameter[2])
                VFC = KooDynaFloat(parameter[3])
                TH = KooDynaFloat(parameter[4])
                TH_SF = KooDynaFloat(parameter[5])
                PEN_SF = KooDynaFloat(parameter[6])
                PTSCL = KooDynaFloat(parameter[7])                
                self.SetControlContact(SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS, USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ, SFRIC, DFRIC, EDC, VFC, TH, TH_SF, PEN_SF, PTSCL)
            if len(controlKeyword)>4:   
                parameter = controlKeyword[4]
                IGNORE = KooDynaInt(parameter[0])
                FRCENG = KooDynaInt(parameter[1])
                SKIPRWG = KooDynaInt(parameter[2])
                OUTSEG = KooDynaInt(parameter[3])
                SPOTSTP = KooDynaInt(parameter[4])
                SPOTDEL = KooDynaInt(parameter[5])
                SPOTHIN = KooDynaFloat(parameter[6])
                
                self.SetControlContact(SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS, USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ, SFRIC, DFRIC, EDC, VFC, TH, TH_SF, PEN_SF, PTSCL, IGNORE, FRCENG, SKIPRWG, OUTSEG, SPOTSTP, SPOTDEL, SPOTHIN)
            if len(controlKeyword)>5:
                parameter = controlKeyword[5]
                ISYM = KooDynaInt(parameter[0])
                NSEROD = KooDynaInt(parameter[1])
                RWGAPS = KooDynaInt(parameter[2])
                RWGDTH = KooDynaFloat(parameter[3])
                RWKSF = KooDynaFloat(parameter[4])
                ICOV = KooDynaInt(parameter[5])
                SWRADF = KooDynaFloat(parameter[6])
                ITHOFF = KooDynaInt(parameter[7])
                
                self.SetControlContact(SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS, USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ, SFRIC, DFRIC, EDC, VFC, TH, TH_SF, PEN_SF, PTSCL, IGNORE, FRCENG, SKIPRWG, OUTSEG, SPOTSTP, SPOTDEL, SPOTHIN, ISYM, NSEROD, RWGAPS, RWGDTH, RWKSF, ICOV, SWRADF, ITHOFF)
            if len(controlKeyword)>6:
                parameter = controlKeyword[6]
                SHLEDG = KooDynaInt(parameter[0])
                PSTIFF = KooDynaInt(parameter[1])
                ITHCNT = KooDynaInt(parameter[2])
                TDCNOF = KooDynaInt(parameter[3])
                FTALL = KooDynaInt(parameter[4])
                SHLTRW = KooDynaFloat(parameter[6])
                IGACTC = KooDynaInt(parameter[7])
                
                self.SetControlContact(SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS, USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ, SFRIC, DFRIC, EDC, VFC, TH, TH_SF, PEN_SF, PTSCL, IGNORE, FRCENG, SKIPRWG, OUTSEG, SPOTSTP, SPOTDEL, SPOTHIN, ISYM, NSEROD, RWGAPS, RWGDTH, RWKSF, ICOV, SWRADF, ITHOFF, SHLEDG, PSTIFF, ITHCNT, TDCNOF, FTALL, "", SHLTRW, IGACTC)
            else:
                self.SetControlContact(SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS, USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ)
        elif controlKeyword[0] == "CONTROL_MPP_IO_NODUMP":
            self.SetControlMPPIoNodump()
            
    
    def WriteStreamDynaKeyword(self, stream):
        if self.controlOutput != None:
            self.controlOutput.WriteStreamDynaKeyword(stream)
        if self.controlBulkViscosity != None:
            self.controlBulkViscosity.WriteStreamDynaKeyword(stream)
        if self.controlTermination != None:
            self.controlTermination.WriteStreamDynaKeyword(stream)
        if self.controlTimeStep != None:
            self.controlTimeStep.WriteStreamDynaKeyword(stream)
        if self.controlHourglass != None:
            self.controlHourglass.WriteStreamDynaKeyword(stream)
        if self.controlenergy != None:
            self.controlenergy.WriteStreamDynaKeyword(stream)
        if self.controlContact != None:
            self.controlContact.WriteStreamDynaKeyword(stream)
        if self.controlMppIONodump != None:
            self.controlMppIONodump.WriteStreamDynaKeyword(stream)
        if self.controlDynamicRelaxation != None:
            self.controlDynamicRelaxation.WriteStreamDynaKeyword(stream)
        if self.controlAccuracy != None:
            self.controlAccuracy.WriteStreamDynaKeyword(stream)
        if self.controlShell is not None:
            self.controlShell.WriteStreamDynaKeyword(stream)
        if self.controlSolid is not None:
            self.controlSolid.WriteStreamDynaKeyword(stream)

    def GenerateDynaKeyword(self):
        keyword = ""
        keyword += self.controlOutput.GenerateDynaKeyword()
        keyword += self.controlBulkViscosity.GenerateDynaKeyword()
        keyword += self.controlTermination.GenerateDynaKeyword()
        keyword += self.controlTimeStep.GenerateDynaKeyword()
        keyword += self.controlHourglass.GenerateDynaKeyword()
        keyword += self.controlenergy.GenerateDynaKeyword()
        keyword += self.controlContact.GenerateDynaKeyword()
        keyword += self.controlMppIONodump.GenerateDynaKeyword()
        keyword += self.controlDynamicRelaxation.GenerateDynaKeyword()
        if self.controlAccuracy is not None:
            keyword += self.controlAccuracy.GenerateDynaKeyword()
        if self.controlShell is not None:
            keyword += self.controlShell.GenerateDynaKeyword()
        if self.controlSolid is not None:
            keyword += self.controlSolid.GenerateDynaKeyword()

        return keyword
        