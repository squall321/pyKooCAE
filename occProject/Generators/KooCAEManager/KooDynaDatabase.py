from __future__ import annotations
from KooCAEManager.KooOperator import KooDynaFloat, KooDynaInt, KooDynaString

class KooDatabase:
    def __init__(self):
        pass
    def WriteDynaKeyword(self):
        keyword = ""
        return keyword

class KooDatabaseBasic(KooDatabase):
    def __init__(self, DT=0.0, BINARY=1, LCUR=0, IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseBasic, self).__init__()
        self.DT = DT
        self.BINARY = BINARY
        self.LCUR = LCUR
        self.IOOPT = IOOPT
        self.OPTION1 = OPTION1
        self.OPTION2 = OPTION2
        self.OPTION3 = OPTION3
        self.OPTION4 = OPTION4
    
    def WritetoDynaKeyword(self):
        keyword = ""
        keyword += format(self.DT, ">10.3e")
        keyword += format(self.BINARY, ">10")
        if self.LCUR == 0:
            keyword += "          "
        else:
            keyword += format(self.LCUR, ">10")
        keyword += format(self.IOOPT, ">10")
        if self.OPTION1 == 0:
            keyword += "          "
        else:
            keyword += format(self.OPTION1, ">10")
        if self.OPTION2 == 0:
            keyword += "          "
        else:
            keyword += format(self.OPTION2, ">10")
        if self.OPTION3 == 0:
            keyword += "          "
        else:
            keyword += format(self.OPTION3, ">10")
        if self.OPTION4 == 0:
            keyword += "          "
        else:
            keyword += format(self.OPTION4, ">10")                    
        keyword += "\n"
        return keyword

    def WriteStreamDynaKeyword(self, stream):
        stream.write(format(self.DT, ">10.3e"))
        stream.write(format(self.BINARY, ">10"))
        if self.LCUR == 0:
            stream.write("          ")
        else:
            stream.write(format(self.LCUR, ">10"))
        stream.write(format(self.IOOPT, ">10"))
        if self.OPTION1 == 0:
            stream.write("          ")
        else:
            stream.write(format(self.OPTION1, ">10"))
        if self.OPTION2 == 0:
            stream.write("          ")
        else:
            stream.write(format(self.OPTION2, ">10"))
        if self.OPTION3 == 0:
            stream.write("          ")
        else:
            stream.write(format(self.OPTION3, ">10"))
        if self.OPTION4 == 0:
            stream.write("          ")
        else:
            stream.write(format(self.OPTION4, ">10"))
        stream.write("\n")
        
                

class KooDatabaseBndout(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseBndout, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_BNDOUT\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_BNDOUT\n")
        super().WriteStreamDynaKeyword(stream)
        
class KooDatabaseElout(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseElout, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_ELOUT\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_ELOUT\n")
        super().WriteStreamDynaKeyword(stream)
        
class KooDatabaseRbdout(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseRbdout, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_RBDOUT\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_RBDOUT\n")
        super().WriteStreamDynaKeyword(stream)
    

class KooDatabaseRcforc(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseRcforc, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_RCFORC\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_RCFORC\n")
        super().WriteStreamDynaKeyword(stream)

class KooDatabaseRwforc(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseRwforc, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_RWFORC\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_RWFORC\n")
        super().WriteStreamDynaKeyword(stream)
    
class KooDatabaseNodfor(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseNodfor, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_NODFOR\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_NODFOR\n")
        super().WriteStreamDynaKeyword(stream)

class KooDatabaseNodout(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseNodout, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_NODOUT\n"
        
        keyword += format(self.DT, ">10.3e")
        keyword += format(self.BINARY, ">10")
        if self.LCUR == 0:
            keyword += "          "
        else:
            keyword += format(self.LCUR, ">10")
        keyword += format(self.IOOPT, ">10")
        if self.OPTION1 == 0.0 or self.OPTION1 == "":
            keyword += "          "
        else:
            keyword += format(self.OPTION1, ">10.3e")
        if self.OPTION2 == 0 or self.OPTION2 == "":
            keyword += "          "
        else:
            keyword += format(self.OPTION2, ">10")
        if self.OPTION3 == 0 or self.OPTION3 == "":
            keyword += "          "
        else:
            keyword += format(self.OPTION3, ">10")
        if self.OPTION4 == 0 or self.OPTION4 == "":
            keyword += "          "
        else:
            keyword += format(self.OPTION4, ">10")                    
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_NODOUT\n")
        stream.write(format(self.DT, ">10.3e"))
        stream.write(format(self.BINARY, ">10"))
        if self.LCUR == 0:
            stream.write("          ")
        else:
            stream.write(format(self.LCUR, ">10"))
        stream.write(format(self.IOOPT, ">10"))
        if self.OPTION1 == 0.0 or self.OPTION1 == "":
            stream.write("          ")
        else:
            stream.write(format(self.OPTION1, ">10.3e"))
        if self.OPTION2 == 0 or self.OPTION2 == "":
            stream.write("          ")
        else:
            stream.write(format(self.OPTION2, ">10"))
        if self.OPTION3 == 0 or self.OPTION3 == "":
            stream.write("          ")
        else:
            stream.write(format(self.OPTION3, ">10"))
        if self.OPTION4 == 0 or self.OPTION4 == "":
            stream.write("          ")
        else:
            stream.write(format(self.OPTION4, ">10"))
        stream.write("\n")

class KooDatabaseGlstat(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseGlstat, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_GLSTAT\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_GLSTAT\n")
        super().WriteStreamDynaKeyword(stream)

class KooDatabaseMatsum(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseMatsum, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_MATSUM\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_MATSUM\n")
        super().WriteStreamDynaKeyword(stream)
    
class KooDatabaseSleout(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseSleout, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_SLEOUT\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_SLEOUT\n")
        super().WriteStreamDynaKeyword(stream)
    
class KooDatabaseSpcforc(KooDatabaseBasic):
    def __init__(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        super(KooDatabaseSpcforc, self).__init__(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
    
    def WritetoDynaKeyword(self):        
        keyword = "*DATABASE_SPCFORC\n"
        keyword += super().WritetoDynaKeyword()                
        return keyword
        
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_SPCFORC\n")
        super().WriteStreamDynaKeyword(stream)
    
class KooDatabaseExtentBinary(KooDatabase):
    def __init__(self, NEIPH,NEIPS,MAXINT,STRFLG,SIGFLG,EPSFLG,RLTFLG,ENGFLG,CMPFLG,IEVERP,BEAMIP,DCOMP,SHGE,STSSZ,N3THDT,IALEMAT):
        super(KooDatabaseExtentBinary,self).__init__()
        self.NEIPH = NEIPH
        self.NEIPS = NEIPS
        self.MAXINT = MAXINT
        self.STRFLG = STRFLG
        self.SIGFLG = SIGFLG
        self.EPSFLG = EPSFLG
        self.RLTFLG = RLTFLG
        self.ENGFLG = ENGFLG
        self.CMPFLG = CMPFLG
        self.IEVERP = IEVERP
        self.BEAMIP = BEAMIP
        self.DCOMP = DCOMP
        self.SHGE = SHGE
        self.STSSZ = STSSZ
        self.N3THDT = N3THDT
        self.IALEMAT = IALEMAT
            
    def WritetoDynaKeyword(self):
        keyword = ""
        keyword += "*DATABASE_EXTENT_BINARY\n"
        keyword += format(self.NEIPH, ">10")
        keyword += format(self.NEIPS, ">10")
        keyword += format(self.MAXINT, ">10")
        keyword += format(self.STRFLG, ">10")
        keyword += format(self.SIGFLG, ">10")
        keyword += format(self.EPSFLG, ">10")
        keyword += format(self.RLTFLG, ">10")        
        keyword += format(self.ENGFLG, ">10")
        keyword += "\n"
        keyword += format(self.CMPFLG, ">10")
        keyword += format(self.IEVERP, ">10")
        keyword += format(self.BEAMIP, ">10")
        keyword += format(self.DCOMP, ">10")
        keyword += format(self.SHGE, ">10")
        keyword += format(self.STSSZ, ">10")
        keyword += format(self.N3THDT, ">10")
        keyword += format(self.IALEMAT, ">10")
        keyword += "\n"
        return keyword     
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_EXTENT_BINARY\n")
        stream.write(format(self.NEIPH, ">10"))
        stream.write(format(self.NEIPS, ">10"))
        stream.write(format(self.MAXINT, ">10"))
        stream.write(format(self.STRFLG, ">10"))
        stream.write(format(self.SIGFLG, ">10"))
        stream.write(format(self.EPSFLG, ">10"))
        stream.write(format(self.RLTFLG, ">10")        )
        stream.write(format(self.ENGFLG, ">10"))
        stream.write("\n")
        stream.write(format(self.CMPFLG, ">10"))
        stream.write(format(self.IEVERP, ">10"))
        stream.write(format(self.BEAMIP, ">10"))
        stream.write(format(self.DCOMP, ">10"))
        stream.write(format(self.SHGE, ">10"))
        stream.write(format(self.STSSZ, ">10"))
        stream.write(format(self.N3THDT, ">10"))
        stream.write(format(self.IALEMAT, ">10"))
        stream.write("\n")
    
class KooDatabaseExtentIntfor(KooDatabase):
    def __init__(self, NGLBV=1, NVELO=1, NPRESU=1, NSHEAR=1, NFORC=1, NGAPC=1, NFAIL=0, IEVERF=0, NWEAR=0, NWUSR=0, NHUF=0, NTIED=0, NENG=0, NPEN=0):
        super(KooDatabaseExtentIntfor,self).__init__()
        self.NGLBV = NGLBV
        self.NVELO = NVELO
        self.NPRESU = NPRESU
        self.NSHEAR = NSHEAR
        self.NFORC = NFORC
        self.NGAPC = NGAPC
        self.NFAIL = NFAIL
        self.IEVERF = IEVERF
        self.NWEAR = NWEAR
        self.NWUSR = NWUSR
        self.NHUF = NHUF
        self.NTIED = NTIED
        self.NENG = NENG
        self.NPEN = NPEN
        
    def WritetoDynaKeyword(self):
        keyword = ""
        keyword += "*DATABASE_EXTENT_INTFOR\n"
        keyword += format(self.NGLBV, ">10")
        keyword += format(self.NVELO, ">10")
        keyword += format(self.NPRESU, ">10")
        keyword += format(self.NSHEAR, ">10")
        keyword += format(self.NFORC, ">10")
        keyword += format(self.NGAPC, ">10")
        keyword += format(self.NFAIL, ">10")
        keyword += format(self.IEVERF, ">10")
        keyword += "\n"
        keyword += format(self.NWEAR, ">10")
        keyword += format(self.NWUSR, ">10")
        keyword += format(self.NHUF, ">10")
        keyword += format(self.NTIED, ">10")
        keyword += format(self.NENG, ">10")
        keyword += format(self.NPEN, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_EXTENT_INTFOR\n")
        stream.write(format(self.NGLBV, ">10"))
        stream.write(format(self.NVELO, ">10"))
        stream.write(format(self.NPRESU, ">10"))
        stream.write(format(self.NSHEAR, ">10"))
        stream.write(format(self.NFORC, ">10"))
        stream.write(format(self.NGAPC, ">10"))
        stream.write(format(self.NFAIL, ">10"))
        stream.write(format(self.IEVERF, ">10"))
        stream.write("\n")
        stream.write(format(self.NWEAR, ">10"))
        stream.write(format(self.NWUSR, ">10"))
        stream.write(format(self.NHUF, ">10"))
        stream.write(format(self.NTIED, ">10"))
        stream.write(format(self.NENG, ">10"))
        stream.write(format(self.NPEN, ">10"))
        stream.write("\n")
    
        
class KooDatabaseHistoryNode(KooDatabase):
    def __init__(self, nodes = []):
        super(KooDatabaseHistoryNode, self).__init__()
        self.nodes = nodes
    
    def AddNodeID(self, nodeID):
        self.nodes.append(nodeID)
        
    def WritetoDynaKeyword(self):
        keyword = "*DATABASE_HISTORY_NODE\n"
        i = 0 
        for node in self.nodes:
            keyword += format(node, ">10")
            i = i + 1
            if i % 8 == 0:
                keyword += "\n"
        if i % 8 != 0:
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_HISTORY_NODE\n")
        i = 0 
        for node in self.nodes:
            stream.write(format(node, ">10"))
            i = i + 1
            if i % 8 == 0:
                stream.write("\n")
        if i % 8 != 0:
            stream.write("\n")

class KooDatabaseHistoryBeam(KooDatabase):
    def __init__(self, beams = []):
        super(KooDatabaseHistoryBeam, self).__init__()
        self.beams = beams
    
    def AddBeamID(self, beamID):
        self.beams.append(beamID)
        
    def WritetoDynaKeyword(self):
        keyword = "*DATABASE_HISTORY_BEAM\n"
        i = 0 
        for beam in self.beams:
            keyword += format(beam, ">10")
            i = i + 1
            if i % 8 == 0:
                keyword += "\n"
        if i % 8 != 0:
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_HISTORY_BEAM\n")
        i = 0 
        for beam in self.beams:
            stream.write(format(beam, ">10"))
            i = i + 1
            if i % 8 == 0:
                stream.write("\n")
        if i % 8 != 0:
            stream.write("\n")
    
class KooDatabaseHistoryBeamSet(KooDatabase):
    def __init__(self, beamsets = []):
        super(KooDatabaseHistoryBeamSet, self).__init__()
        self.beamsets = beamsets
    
    def AddBeamSetID(self, beamsetID):
        self.beamsets.append(beamsetID)
        
    def WritetoDynaKeyword(self):
        keyword = "*DATABASE_HISTORY_BEAM_SET\n"
        i = 0 
        for beamset in self.beamsets:
            keyword += format(beamset, ">10")
            i = i + 1
            if i % 8 == 0:
                keyword += "\n"
        if i % 8 != 0:
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_HISTORY_BEAM_SET\n")
        i = 0 
        for beamset in self.beamsets:
            stream.write(format(beamset, ">10"))
            i = i + 1
            if i % 8 == 0:
                stream.write("\n")
        if i % 8 != 0:
            stream.write("\n")

class KooDatabaseHistoryShell(KooDatabase):
    def __init__(self, shells = []):
        super(KooDatabaseHistoryShell, self).__init__()
        self.shells = shells
    
    def AddShellID(self, shellID):
        self.shells.append(shellID)
        
    def WritetoDynaKeyword(self):
        keyword = "*DATABASE_HISTORY_SHELL\n"
        i = 0 
        for shell in self.shells:
            keyword += format(shell, ">10")
            i = i + 1
            if i % 8 == 0:
                keyword += "\n"
        if i % 8 != 0:
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_HISTORY_SHELL\n")
        i = 0 
        for shell in self.shells:
            stream.write(format(shell, ">10"))
            i = i + 1
            if i % 8 == 0:
                stream.write("\n")
        if i % 8 != 0:
            stream.write("\n")

class KooDatabaseHistoryShellSet(KooDatabase):
    def __init__(self, shellsets = []):
        super(KooDatabaseHistoryShellSet, self).__init__()
        self.shellsets = shellsets
    
    def AddShellSetID(self, shellsetID):
        self.shellsets.append(shellsetID)
        
    def WritetoDynaKeyword(self):
        keyword = "*DATABASE_HISTORY_SHELL_SET\n"
        i = 0 
        for shellset in self.shellsets:
            keyword += format(shellset, ">10")
            i = i + 1
            if i % 8 == 0:
                keyword += "\n"
        if i % 8 != 0:
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_HISTORY_SHELL_SET\n")
        i = 0 
        for shellset in self.shellsets:
            stream.write(format(shellset, ">10"))
            i = i + 1
            if i % 8 == 0:
                stream.write("\n")
        if i % 8 != 0:
            stream.write("\n")

class KooDatabaseHistorySolid(KooDatabase):
    def __init__(self, solids = []):
        super(KooDatabaseHistorySolid, self).__init__()
        self.solids = solids
    
    def AddSolidID(self, solidID):
        self.solids.append(solidID)
        
    def WritetoDynaKeyword(self):
        keyword = "*DATABASE_HISTORY_SOLID\n"
        i = 0 
        for solid in self.solids:
            keyword += format(solid, ">10")
            i = i + 1
            if i % 8 == 0:
                keyword += "\n"
        if i % 8 != 0:
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_HISTORY_SOLID\n")
        i = 0 
        for solid in self.solids:
            stream.write(format(solid, ">10"))
            i = i + 1
            if i % 8 == 0:
                stream.write("\n")
        if i % 8 != 0:
            stream.write("\n")

class KooDatabaseHistorySolidSet(KooDatabase):
    def __init__(self, solidsets = []):
        super(KooDatabaseHistorySolidSet, self).__init__()
        self.solidsets = solidsets
    
    def AddSolidSetID(self, solidsetID):
        self.solidsets.append(solidsetID)
        
    def WritetoDynaKeyword(self):
        keyword = "*DATABASE_HISTORY_SOLID_SET\n"
        i = 0 
        for solidset in self.solidsets:
            keyword += format(solidset, ">10")
            i = i + 1
            if i % 8 == 0:
                keyword += "\n"
        if i % 8 != 0:
            keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_HISTORY_SOLID_SET\n")
        i = 0 
        for solidset in self.solidsets:
            stream.write(format(solidset, ">10"))
            i = i + 1
            if i % 8 == 0:
                stream.write("\n")
        if i % 8 != 0:
            stream.write("\n")    
                        

class KooDatabaseBinary(KooDatabase):
    def __init__(self, DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID):
        super(KooDatabaseBinary, self).__init__()
        self.DTCYCL = DTCYCL
        self.LCDT = LCDT
        self.BEAM = BEAM
        self.NPLTC = NPLTC
        self.PSETID = PSETID
        self.CID = CID
        
    def WritetoDynaKeyword(self):
        keyword = ""
        #keyword += "*DATABASE_BINARY\n"        
        keyword += format(self.DTCYCL, ">10.3e")
        keyword += format(self.LCDT, ">10")
        keyword += format(self.BEAM, ">10")
        keyword += format(self.NPLTC, ">10")
        keyword += format(self.PSETID, ">10")
        keyword += format(self.CID, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        #stream.write("*DATABASE_BINARY\n")
        stream.write(format(self.DTCYCL, ">10.3e"))
        stream.write(format(self.LCDT, ">10"))
        stream.write(format(self.BEAM, ">10"))
        stream.write(format(self.NPLTC, ">10"))
        stream.write(format(self.PSETID, ">10"))
        stream.write(format(self.CID, ">10"))
        stream.write("\n")
    
class KooDatabaseBinaryD3plot(KooDatabaseBinary):
    def __init__(self, DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID):
        super(KooDatabaseBinaryD3plot, self).__init__(DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID)
    
    def WritetoDynaKeyword(self):
        keyword = ""
        keyword += "*DATABASE_BINARY_D3PLOT\n"
        keyword += super().WritetoDynaKeyword()        
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_BINARY_D3PLOT\n")
        super().WriteStreamDynaKeyword(stream)

class KooDatabaseBinaryD3thdt(KooDatabaseBinary):
    def __init__(self, DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID):
        super(KooDatabaseBinaryD3thdt, self).__init__(DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID)
    
    def WritetoDynaKeyword(self):
        keyword = ""
        keyword += "*DATABASE_BINARY_D3THDT\n"
        keyword += super().WritetoDynaKeyword()        
        return keyword   
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_BINARY_D3THDT\n")
        super().WriteStreamDynaKeyword(stream)

class KooDatabaseBinaryD3dump(KooDatabaseBinary):
    def __init__(self, DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID):
        super(KooDatabaseBinaryD3dump, self).__init__(DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID)
    
    def WritetoDynaKeyword(self):
        keyword = ""
        keyword += "*DATABASE_BINARY_D3DUMP\n"
        keyword += super().WritetoDynaKeyword()        
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_BINARY_D3DUMP\n")
        super().WriteStreamDynaKeyword(stream)

class KooDatabaseBinaryIntfor(KooDatabaseBinary):
    def __init__(self, DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID, IOOPT, name = ""):
        super(KooDatabaseBinaryIntfor, self).__init__(DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID)
        self.IOOPT = IOOPT
        self.name = name

    def WriteDynaKeyword(self):
        if self.name == "":
            keyword = "*DATABASE_BINARY_INTFOR\n"
        else:
            keyword = "*DATABASE_BINARY_INTFOR_FILE\n"
            keyword += format(self.name, ">80")
            keyword += "\n"
        keyword += super().WriteDynaKeyword()
        keyword += format(self.IOOPT, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        if self.name == "":
            stream.write("*DATABASE_BINARY_INTFOR\n")
        else:
            stream.write("*DATABASE_BINARY_INTFOR_FILE\n")
            stream.write(format(self.name, ">80"))
            stream.write("\n")
        super().WriteStreamDynaKeyword(stream)
        stream.write(format(self.IOOPT, ">10"))
        stream.write("\n")
        
class KooDatabaseNodalForceGroup(KooDatabase):
    def __init__(self, nsid, cid):
        super(KooDatabaseNodalForceGroup, self).__init__()
        self.nsid = nsid
        self.cid = cid
    
    def WritetoDynaKeyword(self):
        keyword = "*DATABASE_NODAL_FORCE_GROUP\n"
        keyword += format(self.nsid, ">10")
        keyword += format(self.cid, ">10")
        keyword += "\n"
        return keyword    
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*DATABASE_NODAL_FORCE_GROUP\n")
        stream.write(format(self.nsid, ">10"))
        stream.write(format(self.cid, ">10"))
        stream.write("\n")

class KooDatabaseManager:
    def __init__(self):        
        self.database= {}    
        
    def clear(self):
        self.database.clear()

    def OverwritefromDatabaseManager(self, databaseManager):        
        for key, value in databaseManager.database.items():
            self.database[key] = value

    def SetDatabaseBinaryD3plot(self, DTCYCL, LCDT, BEAM, MPLTC, PSETID, CID):
        databaseBinaryD3plot = KooDatabaseBinaryD3plot(DTCYCL, LCDT, BEAM, MPLTC, PSETID, CID)
        self.database["BINARY_D3PLOT"] = databaseBinaryD3plot    
    
    def SetDatabaseBinaryD3thdt(self, DTCYCL, LCDT, BEAM, MPLTC, PSETID, CID):
        databaseBinaryD3thdt = KooDatabaseBinaryD3thdt(DTCYCL, LCDT, BEAM, MPLTC, PSETID, CID)
        self.database["BINARY_D3THDT"] = databaseBinaryD3thdt
    
    def SetDatabaseBinaryD3dump(self, DTCYCL, LCDT, BEAM, MPLTC, PSETID, CID):
        databaseBinaryD3dump = KooDatabaseBinaryD3dump(DTCYCL, LCDT, BEAM, MPLTC, PSETID, CID)
        self.database["BINARY_D3DUMP"] = databaseBinaryD3dump

    def SetDatabaseBinaryIntfor(self, DTCYCL, LCDT, BEAM, MPLTC, PSETID, CID, IOOPT, name = ""):
        databaseBinaryIntfor = KooDatabaseBinaryIntfor(DTCYCL, LCDT, BEAM, MPLTC, PSETID, CID, IOOPT, name)
        self.database["BINARY_INTFOR"] = databaseBinaryIntfor

    def SetDatabaseExtentBinary(self, NEIPH=0,NEIPS=0,MAXINT=3,STRFLG=0,SIGFLG=1,EPSFLG=1,RLTFLG=1,ENGFLG=1,CMPFLG=0,IEVERP=0,BEAMIP=0,DCOMP=1,SHGE=1,STSSZ=1,N3THDT=2,IALEMAT=1):    
        databaseExtentBinary = KooDatabaseExtentBinary(NEIPH,NEIPS,MAXINT,STRFLG,SIGFLG,EPSFLG,RLTFLG,ENGFLG,CMPFLG,IEVERP,BEAMIP,DCOMP,SHGE,STSSZ,N3THDT,IALEMAT)
        self.database['EXTENT_BINARY'] = databaseExtentBinary
    
    def SetDatabaseExtentIntfor(self, NGLBV=1, NVELO=1, NPRESU=1, NSHEAR=1, NFORC=1, NGAPC=1, NFAIL=0, IEVERF=0, NWEAR=0, NWUSR=0, NHUF=0, NTIED=0, NENG=0, NPEN=0):
        databaseExtentIntfor = KooDatabaseExtentIntfor(NGLBV, NVELO, NPRESU, NSHEAR, NFORC, NGAPC, NFAIL, IEVERF, NWEAR, NWUSR, NHUF, NTIED, NENG, NPEN)
        self.database['EXTENT_INTFOR'] = databaseExtentIntfor
    
    def SetDatabaseBndout(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseBndout = KooDatabaseBndout(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["BNDOUT"] = databaseBndout
        
    def SetDatabaseElout(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseElout = KooDatabaseElout(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["ELOUT"] = databaseElout
    
    def SetDatabaseSpcforc(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseSpcforc = KooDatabaseSpcforc(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["SPCFORC"] = databaseSpcforc            
    
    def SetDatabaseRbdout(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseRbdout = KooDatabaseRbdout(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["RBOUT"] = databaseRbdout
    
    def SetDatabaseRcforc(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseRcforc = KooDatabaseRcforc(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["RCFORC"] = databaseRcforc
    
    def SetDatabaseRwforc(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseRwforc = KooDatabaseRwforc(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["RWFORC"] = databaseRwforc
    
    def SetDatabaseNodfor(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseNodfor = KooDatabaseNodfor(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["NODFOR"] = databaseNodfor        
        
    def SetDatabaseNodout(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseNodout = KooDatabaseNodout(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["NODOUT"] = databaseNodout
        
    def SetDatabaseGlstat(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseGlstat = KooDatabaseGlstat(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["GLSTAT"] = databaseGlstat
        
    def SetDatabaseMatsum(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseMatsum = KooDatabaseMatsum(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["MATSUM"] = databaseMatsum
        
    def SetDatabaseSleout(self, DT=0.0, BINARY=1, LCUR="", IOOPT=0, OPTION1=0, OPTION2=0, OPTION3=0, OPTION4=0):
        databaseSleout = KooDatabaseSleout(DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4)
        self.database["SLEOUT"] = databaseSleout
    
    def SetDatabaseHistoryNode(self, nodes = []):
        databaseHistoryNode = KooDatabaseHistoryNode(nodes)
        self.database["HISTORY_NODE"] = databaseHistoryNode
    
    def SetDatabaseHistoryBeam(self, beams = []):
        databaseHistoryBeam = KooDatabaseHistoryBeam(beams)
        self.database["HISTORY_BEAM"] = databaseHistoryBeam
        
    def SetDatabaseHistoryBeamSet(self, beamsets = []):
        databaseHistoryBeamSet = KooDatabaseHistoryBeamSet(beamsets)
        self.database["HISTORY_BEAM_SET"] = databaseHistoryBeamSet
    
    def SetDatabaseHistoryShell(self, shells = []):
        databaseHistoryShell = KooDatabaseHistoryShell(shells)
        self.database["HISTORY_SHELL"] = databaseHistoryShell
    
    def SetDatabaseHistoryShellSet(self, shellsets = []):
        databaseHistoryShellSet = KooDatabaseHistoryShellSet(shellsets)
        self.database["HISTORY_SHELL_SET"] = databaseHistoryShellSet
    
    def SetDatabaseHistorySolid(self, solids = []):
        databaseHistorySolid = KooDatabaseHistorySolid(solids)
        self.database["HISTORY_SOLID"] = databaseHistorySolid
    
    def SetDatabaseHistorySolidSet(self, solidsets = []):
        databaseHistorySolidSet = KooDatabaseHistorySolidSet(solidsets)
        self.database["HISTORY_SOLID_SET"] = databaseHistorySolidSet
    
    def SetDatabaseNodalForceGroup(self, nsid, cid):
        databaseNodalForceGroup = KooDatabaseNodalForceGroup(nsid, cid)
        self.database["NODAL_FORCE_GROUP"] = databaseNodalForceGroup
            
    def SetDatabasefromDyna(self, databaseKeyword):
        if databaseKeyword[0] == "DATABASE_RBDOUT" or databaseKeyword[0] == "*DATABASE_BNDOUT" or databaseKeyword[0] == "*DATABASE_SPCFORC" or databaseKeyword[0] == "*DATABASE_RCFORC" or databaseKeyword[0] == "*DATABASE_RWFORC" or databaseKeyword[0] == "*DATABASE_NODFOR" or databaseKeyword[0] == "*DATABASE_NODOUT" or databaseKeyword[0] == "*DATABASE_GLSTAT" or databaseKeyword[0] == "*DATABASE_MATSUM" or databaseKeyword[0] == "*DATABASE_SLEOUT" or databaseKeyword[0] == "*DATABASE_ELOUT":
            keyword = databaseKeyword[1]
            if len(keyword[0].strip()) == 0:
                keyword[0] = 0.0
            else:
                keyword[0] = float(keyword[0])
            if len(keyword[1].strip()) == 0:
                keyword[1] = 1
            else:
                keyword[1] = int(keyword[1])
            if len(keyword[2].strip()) == 0:
                keyword[2] = 0
            else:
                keyword[2] = int(keyword[2])
            if len(keyword[3].strip()) == 0:
                keyword[3] = 0
            else:
                keyword[3] = int(keyword[3])
            if databaseKeyword[0] == "*DATABASE_NODOUT":
                if len(keyword) >4:
                    if len(keyword[4].strip()) == 0:
                        keyword[4] = ""
                    else:
                        keyword[4] = float(keyword[4])                    
                else:
                    keyword.append("")
            else:
                
                if len(keyword) >4:
                    if len(keyword[4].strip()) == 0:
                        keyword[4] = ""
                    else:
                        keyword[4] = int(keyword[4])                    
                else:
                    keyword.append("")
            if len(keyword) >5:
                if len(keyword[5].strip()) == 0:
                    keyword[5] = ""
                else:
                    keyword[5] = int(keyword[5])
            else:
                keyword.append("")
            if len(keyword) >6:
                if len(keyword[6].strip()) == 0:
                    keyword[6] = ""
                else:
                    keyword[6] = int(keyword[6])
            else:
                keyword.append("")
            if len(keyword) >7:                                    
                if len(keyword[7].strip()) == 0:
                    keyword[7] = ""
                else:
                    keyword[7] = int(keyword[7])
            else:
                keyword.append("")
            if databaseKeyword[0] == "*DATABASE_RBDOUT":
                self.SetDatabaseRbdout(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])                
            elif databaseKeyword[0] == "*DATABASE_BNDOUT":
                self.SetDatabaseBndout(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
            elif databaseKeyword[0] == "*DATABASE_ELOUT":
                self.SetDatabaseElout(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
            elif databaseKeyword[0] == "*DATABASE_SPCFORC":
                self.SetDatabaseSpcforc(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
            elif databaseKeyword[0] == "*DATABASE_RCFORC":
                self.SetDatabaseRcforc(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
            elif databaseKeyword[0] == "*DATABASE_RWFORC":
                self.SetDatabaseRwforc(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
            elif databaseKeyword[0] == "*DATABASE_NODFOR":
                self.SetDatabaseNodfor(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
            elif databaseKeyword[0] == "*DATABASE_NODOUT":
                self.SetDatabaseNodout(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
            elif databaseKeyword[0] == "*DATABASE_GLSTAT":
                self.SetDatabaseGlstat(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
            elif databaseKeyword[0] == "*DATABASE_MATSUM":
                self.SetDatabaseMatsum(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
            elif databaseKeyword[0] == "*DATABASE_SLEOUT":
                self.SetDatabaseSleout(keyword[0],keyword[1],keyword[2],keyword[3],keyword[4],keyword[5],keyword[6],keyword[7])
                
        if databaseKeyword[0] == "*DATABASE_EXTENT_BINARY":
            keyword = databaseKeyword[1]
            if len(keyword[0].strip()) == 0:
                keyword[0] = "0"
            if len(keyword[1].strip()) == 0:
                keyword[1] = "0"
            if len(keyword[2].strip()) == 0:
                keyword[2] = "3"
            if len(keyword[3].strip()) == 0:
                keyword[3] = "0"
            if len(keyword[4].strip()) == 0:
                keyword[4] = "1"
            if len(keyword[5].strip()) == 0:
                keyword[5] = "1"
            if len(keyword[6].strip()) == 0:
                keyword[6] = "1"
            if len(keyword[7].strip()) == 0:
                keyword[7] = "1"
            NEIPH = int(keyword[0])
            NEIPS = int(keyword[1])
            MAXINT = int(keyword[2])
            STRFLG = int(keyword[3])
            SIGFLG = int(keyword[4])
            EPSFLG = int(keyword[5])
            RLTFLG = int(keyword[6])
            ENGFLG = int(keyword[7])
            
                
            keyword = databaseKeyword[2]
            if len(keyword[0].strip()) == 0:
                keyword[0] = "0"
            if len(keyword[1].strip()) == 0:
                keyword[1] = "0"
            if len(keyword[2].strip()) == 0:
                keyword[2] = "0"
            if len(keyword[3].strip()) == 0:
                keyword[3] = "1"
            if len(keyword[4].strip()) == 0:
                keyword[4] = "1"
            if len(keyword[5].strip()) == 0:
                keyword[5] = "1"
            if len(keyword[6].strip()) == 0:
                keyword[6] = "2"
            if len(keyword[7].strip()) == 0:
                keyword[7] = "1"
            
            CMPFLG = int(keyword[0])
            IEVERP = int(keyword[1])
            BEAMIP = int(keyword[2])
            DCOMP = int(keyword[3])
            SHGE = int(keyword[4])
            STSSZ = int(keyword[5])
            N3THDT = int(keyword[6])
            IALEMAT = int(keyword[7])
            self.SetDatabaseExtentBinary(NEIPH,NEIPS,MAXINT,STRFLG,SIGFLG,EPSFLG,RLTFLG,ENGFLG,CMPFLG,IEVERP,BEAMIP,DCOMP,SHGE,STSSZ,N3THDT,IALEMAT)                
        elif databaseKeyword[0] == "*DATABASE_EXTENT_INTFOR":
            keyword = databaseKeyword[1]
            if len(keyword[0].strip()) == 0:
                keyword[0] = "1"
            if len(keyword[1].strip()) == 0:
                keyword[1] = "1"
            if len(keyword[2].strip()) == 0:
                keyword[2] = "1"
            if len(keyword[3].strip()) == 0:
                keyword[3] = "1"
            if len(keyword[4].strip()) == 0:
                keyword[4] = "1"
            if len(keyword[5].strip()) == 0:
                keyword[5] = "1"
            if len(keyword[6].strip()) == 0:
                keyword[6] = "0"
            if len(keyword[7].strip()) == 0:
                keyword[7] = "0"
            keyword2 = databaseKeyword[2]
            if len(keyword2[0].strip()) == 0:
                keyword2[0] = "0"
            if len(keyword2[1].strip()) == 0:
                keyword2[1] = "0"
            if len(keyword2[2].strip()) == 0:
                keyword2[2] = "0"
            if len(keyword2[3].strip()) == 0:
                keyword2[3] = "0"
            if len(keyword2[4].strip()) == 0:
                keyword2[4] = "0"
            if len(keyword2[5].strip()) == 0:
                keyword2[5] = "0"

            nglbv = int(keyword[0])
            nvelo = int(keyword[1])
            npresu = int(keyword[2])
            nshear = int(keyword[3])
            nforc = int(keyword[4])
            ngapc = int(keyword[5])
            nfail = int(keyword[6])
            ieverf = int(keyword[7])
            nwear = int(keyword2[0])
            nwusr = int(keyword2[1])
            nhuf = int(keyword2[2])
            ntied = int(keyword2[3])
            neng = int(keyword2[4])
            npen = int(keyword2[5])
            self.SetDatabaseExtentIntfor(nglbv, nvelo, npresu, nshear, nforc, ngapc, nfail, ieverf, nwear, nwusr, nhuf, ntied, neng, npen)                         
                
        elif databaseKeyword[0] == "*DATABASE_BINARY_D3PLOT" or databaseKeyword[0] == "*DATABASE_BINARY_D3THDT" or databaseKeyword[0] == "*DATABASE_BINARY_D3DUMP" or databaseKeyword[0] == "*DATABASE_BINARY_INTFOR" or databaseKeyword[0] == "*DATABASE_BINARY_INTFOR_FILE":
            if databaseKeyword[0] == "*DATABASE_BINARY_INTFOR_FILE":
                keyword = databaseKeyword[2]
            else:
                keyword = databaseKeyword[1]
            #remove space            
            if len(keyword) < 6:    
                keyword.extend(["0"] * (6 - len(keyword)))
            if len(keyword[0].strip()) == 0:

                keyword[0] = "0"
            if len(keyword[1].strip()) == 0:
                keyword[1] = "0"
            if len(keyword[2].strip()) == 0:
                keyword[2] = "0"
            if len(keyword[3].strip()) == 0:
                keyword[3] = "0"
            if len(keyword[4].strip()) == 0:
                keyword[4] = "0"
            if len(keyword[5].strip()) == 0:
                keyword[5] = "0"
                
            # check keyword[0] can be changed as float
            
            DTCYCL = float(keyword[0])

            LCDT = int(keyword[1])
            BEAM = int(keyword[2])
            NPLTC = int(keyword[3])
            PSETID = int(keyword[4])
            CID = int(keyword[5])                        
            
            if databaseKeyword[0] == "*DATABASE_BINARY_D3PLOT":
                self.SetDatabaseBinaryD3plot(DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID)
            elif databaseKeyword[0] == "*DATABASE_BINARY_D3THDT":
                self.SetDatabaseBinaryD3thdt(DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID)
            elif databaseKeyword[0] == "*DATABASE_BINARY_D3DUMP":
                self.SetDatabaseBinaryD3dump(DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID)
            elif databaseKeyword[0] == "*DATABASE_BINARY_INTFOR":
                if len(databaseKeyword) < 3:
                    IOOPT = 0
                    name = ""
                else:
                    keyword = databaseKeyword[2]
                    if len(keyword[0].strip()) == 0:
                        keyword[0] = "0"
                    IOOPT = KooDynaInt(keyword[0])
                    name = ""
                self.SetDatabaseBinaryIntfor(DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID, IOOPT, name)
            elif databaseKeyword[0] == "*DATABASE_BINARY_INTFOR_FILE":
                name = databaseKeyword[1]
                keyword = databaseKeyword[3]
                if len(keyword[0].strip()) == 0:
                    keyword[0] = "0"
                IOOPT = int(keyword[0])
                self.SetDatabaseBinaryIntfor(DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID, IOOPT, name)
                
        elif databaseKeyword[0] == "*DATABASE_HISTORY_NODE" or databaseKeyword[0] == "*DATABASE_HISTORY_BEAM" or databaseKeyword[0] == "*DATABASE_HISTORY_BEAM_SET" or databaseKeyword[0] == "*DATABASE_HISTORY_SHELL" or databaseKeyword[0] == "*DATABASE_HISTORY_SHELL_SET" or databaseKeyword[0] == "*DATABASE_HISTORY_SOLID" or databaseKeyword[0] == "*DATABASE_HISTORY_SOLID_SET":            
            keyword = databaseKeyword[1]
            nodes = [] 
            for i in range(0,len(keyword)):                
                if len(keyword[i].strip()) > 0:                 
                    nodes.append(int(keyword[i]))
            if databaseKeyword[0] == "*DATABASE_HISTORY_NODE":
                self.SetDatabaseHistoryNode(nodes)
            elif databaseKeyword[0] == "*DATABASE_HISTORY_BEAM":
                self.SetDatabaseHistoryBeam(nodes)
            elif databaseKeyword[0] == "*DATABASE_HISTORY_BEAM_SET":
                self.SetDatabaseHistoryBeamSet(nodes)
            elif databaseKeyword[0] == "*DATABASE_HISTORY_SHELL":
                self.SetDatabaseHistoryShell(nodes)
            elif databaseKeyword[0] == "*DATABASE_HISTORY_SHELL_SET":
                self.SetDatabaseHistoryShellSet(nodes)
            elif databaseKeyword[0] == "*DATABASE_HISTORY_SOLID":
                self.SetDatabaseHistorySolid(nodes)
            elif databaseKeyword[0] == "*DATABASE_HISTORY_SOLID_SET":
                self.SetDatabaseHistorySolidSet(nodes)
                    
        elif databaseKeyword[0] == "*DATABASE_NODAL_FORCE_GROUP":
            keyword = databaseKeyword[1]
            if len(keyword[0].strip()) == 0:
                keyword[0] = "0"
            if len(keyword[1].strip()) == 0:
                keyword[1] = "0"
            NSID = KooDynaInt(keyword[0])
            CID = KooDynaInt(keyword[1])
            self.SetDatabaseNodalForceGroup(NSID, CID)
            
        
    def GenerateDynaKeyword(self):
        keyword = ""
        for key in self.database:
            keyword += self.database[key].WritetoDynaKeyword()        
        return keyword

    def WriteStreamDynaKeyword(self, stream):
        for key in self.database:
            self.database[key].WriteStreamDynaKeyword(stream)