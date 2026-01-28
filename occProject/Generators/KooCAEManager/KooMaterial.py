from __future__ import annotations
import math

if __name__ == "__main__":  
    from KooDynaKeyword import *
    from KooOperator import *
else:
    from KooCAEManager.KooDynaKeyword import *
    from KooCAEManager.KooOperator import *
class KooEOS:
    def __init__(self, id):
        self.nastranKeywordString = ""
        self.id = id
        
    def SetDynaKeyword(self, dynaKeywordList):
        if type(dynaKeywordList) == str:
            self.dynaKeywordString = dynaKeywordList
        else:
            self.dynaKeywordString = ""
            for line in dynaKeywordList:
                for word in line:
                    self.dynaKeywordString += word
                self.dynaKeywordString += "\n"         
    
    def SetNastranKeyword(self, nastranKeywordList):
        if type(nastranKeywordList) == str:
            self.nastranKeywordString = nastranKeywordList
        else:
            self.nastranKeywordString = ""
            for line in nastranKeywordList:
                for word in line:
                    self.nastranKeywordString += word
                self.nastranKeywordString += "\n"   
                
    def GenerateDynaKeyword(self):
        print("This function should be implemented in the child class.")
        return None

    def GenerateNastranKeyword(self):
        print("This function should be implemented in the child class.")
        return None
    
        
    def SetAnsysAPDLKeyword(self, ansysKeywordString):
        self.ansysAPDLKeywordString = ansysKeywordString

class KooEOSTabulated(KooEOS):
    def __init__(self, id = 0, gama = 0, e0 = 0, v0 = 0, lcc = "", lct = "", evList=[], CList=[], TList=[]):
        super(KooEOSTabulated, self).__init__(id)
        self.gama = gama
        self.e0 = e0
        self.v0 = v0
        self.lcc = lcc
        self.lct = lct
        self.evList = evList
        self.CList = CList
        self.TList = TList
        
        pass
    
    def AddtoDynaKeyword(self, keyword : EOSTabulated):
        keyword.AddEosTabulated(self.id,self.gama,self.e0,self.v0,self.lcc,self.lct,self.evList,self.CList, self.TList)
        
    def GenerateDynaKeyword(self):
        keyword = ""
        keyword += "*EOS_TABULATED\n"
        keyword += format(self.id, ">10")
        keyword += format(self.gama, ">10.3e")
        keyword += format(self.e0, ">10.3e")
        keyword += format(self.v0, ">10.3e")
        if len(self.lcc) > 0:
            keyword += format(self.lcc, ">10")
        else:
            keyword += format("0", ">10")
        if len(self.lct) > 0:
            keyword += format(self.lct, ">10")
        else:
            keyword += format("0", ">10")
        keyword += "\n"
        for i in range(len(self.evList)):
            keyword += format(self.evList[i], ">16.3e")
            if (i+1) % 5 == 0:
                keyword += "\n"
        for i in range(len(self.CList)):
            keyword += format(self.CList[i], ">16.3e")
            if (i+1) % 5 == 0:
                keyword += "\n"
        for i in range(len(self.TList)):
            keyword += format(self.TList[i], ">16.3e")
            if (i+1) % 5 == 0:
                keyword += "\n"                
        self.SetDynaKeyword(keyword)
        return keyword

class KooEOSLinearPolynomial(KooEOS):
    def __init__(self, id = 0, c0 = 0.0, c1 = 0.0, c2 = 0.0, c3 = 0.0, c4 = 0.0, c5 = 0.0, c6 = 0.0, e0 = 0.0, v0 = 0.0):
        super(KooEOSLinearPolynomial, self).__init__(id)
        self.c0 = c0
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.c5 = c5
        self.c6 = c6
        self.e0 = e0
        self.v0 = v0 
    
    def AddtoDynaKeyword(self, keyword : EosLinearPolynomial):
        keyword.AddEOSLinearPolynomialz(self.id,self.c0,self.c1,self.c2,self.c3,self.c4,self.c5,self.c6,self.e0,self.v0)
    
    def GenerateDynaKeyword(self):
        keyword = ""
        keyword += "*EOS_LINEAR_POLYNOMIAL\n"
        keyword += format(self.id, ">10")
        keyword += format(self.c0, ">10.3e")
        keyword += format(self.c1, ">10.3e")
        keyword += format(self.c2, ">10.3e")
        keyword += format(self.c3, ">10.3e")
        keyword += format(self.c4, ">10.3e")
        keyword += format(self.c5, ">10.3e")
        keyword += format(self.c6, ">10.3e")
        keyword += "\n"
        keyword += format(self.e0, ">10.3e")
        keyword += format(self.v0, ">10.3e")
        keyword += "\n"
        self.SetDynaKeyword(keyword)
        return keyword   

class KooMaterial:
    def __init__(self, id = 0, name = ""):
        self.id = id # material id
        self.name = name # material name

        self.dynaKeywordString = None # material keyword
        self.nastranKeywordString = "" # material keyword
        self.ansysAPDLKeywordString = None # material keyword
    
    def GetE(self):
        return 0.0
    
    def GetRho(self):
        return 0.0

    def GetNu(self):
        return 0.0

    def SetDynaKeyword(self, dynaKeywordList):
        if type(dynaKeywordList) == str:
            self.dynaKeywordString = dynaKeywordList
        else:
            self.dynaKeywordString = ""
            for line in dynaKeywordList:
                for word in line:
                    self.dynaKeywordString += word
                self.dynaKeywordString += "\n"         
    
    def SetNastranKeyword(self, nastranKeywordList):
        if type(nastranKeywordList) == str:
            self.nastranKeywordString = nastranKeywordList
        else:
            self.nastranKeywordString = ""
            for line in nastranKeywordList:
                for word in line:
                    self.nastranKeywordString += word
                self.nastranKeywordString += "\n"   
                
    def GenerateDynaKeyword(self):
        print("This function should be implemented in the child class.")
        return None

    def GenerateNastranKeyword(self):
        print("This function should be implemented in the child class.")
        return None
    
        
    def SetAnsysAPDLKeyword(self, ansysKeywordString):
        self.ansysAPDLKeywordString = ansysKeywordString

class KooMaterialAddErosion(KooMaterial):
    def __init__(self, mid = 0, EXCL=0.0, MXPRES=0.0, MNEPS=0.0, EFFEPS=0.0, VOLEPS=0.0, NUMFIP=1.0, NCS=1.0,MNPRES=0.0, SIGP1=0.0, SIGVM=0.0, MXEPS=0.0, EPSSH=0.0, SIGTH=0.0, IMPULSE=0.0, FAILTM=0.0, IDAM=0.0, LCREGD=0.0, LCFLD=0.0, NSFF=0.0, EPSTHIN=0.0, ENGCRT=0.0, RADCRT=0.0, LCEPS12=0, LCEPS13=0, LCEPSMX=0, DTEFLT=0.0, VOLFRAC=0.5, MXTMP=1.0e20, DTMIN=0.0):        
        super(KooMaterialAddErosion, self).__init__(mid, "Mat{0}".format(mid))
        self.EXCL = EXCL
        self.MXPRES = MXPRES
        self.MNEPS = MNEPS
        self.EFFEPS = EFFEPS
        self.VOLEPS = VOLEPS
        self.NUMFIP = NUMFIP
        self.NCS = NCS
        self.MNPRES = MNPRES
        self.SIGP1 = SIGP1
        self.SIGVM = SIGVM
        self.MXEPS = MXEPS
        self.EPSSH = EPSSH
        self.SIGTH = SIGTH
        self.IMPULSE = IMPULSE
        self.FAILTM = FAILTM
        self.IDAM = IDAM
        self.LCREGD = LCREGD
        self.LCFLD = LCFLD
        self.NSFF = NSFF
        self.EPSTHIN = EPSTHIN
        self.ENGCRT = ENGCRT
        self.RADCRT = RADCRT
        self.LCEPS12 = LCEPS12
        self.LCEPS13 = LCEPS13
        self.LCEPSMX = LCEPSMX
        self.DTEFLT = DTEFLT
        self.VOLFRAC = VOLFRAC
        self.MXTMP = MXTMP
        self.DTMIN = DTMIN
        
    def AddtoDynaKeyword(self, keyword : MatAddErosion):
        keyword.AddMatAddErosion(self.id, self.EXCL, self.MXPRES, self.MNEPS, self.EFFEPS, self.VOLEPS, self.NUMFIP, self.NCS, self.MNPRES, self.SIGP1, self.SIGVM, self.MXEPS, self.EPSSH, self.SIGTH, self.IMPULSE, self.FAILTM, self.IDAM, self.LCREGD, self.LCFLD, self.NSFF, self.EPSTHIN, self.ENGCRT, self.RADCRT, self.LCEPS12, self.LCEPS13, self.LCEPSMX, self.DTEFLT, self.VOLFRAC, self.MXTMP, self.DTMIN)
        
    def GenerateDynaKeyword(self):
        keywordString = "*MAT_ADD_EROSION\n"
        # 10 digit for each float
        keywordString += format(self.id, ">10")
        keywordString += format(self.EXCL, ">10.3e")
        keywordString += format(self.MXPRES, ">10.3e")
        keywordString += format(self.MNEPS, ">10.3e")
        keywordString += format(self.EFFEPS, ">10.3e")
        keywordString += format(self.VOLEPS, ">10.3e")
        keywordString += format(self.NUMFIP, ">10.3e")
        keywordString += format(self.NCS, ">10.3e")
        keywordString += "\n"
        keywordString += format(self.MNPRES, ">10.3e")
        keywordString += format(self.SIGP1, ">10.3e")
        keywordString += format(self.SIGVM, ">10.3e")
        keywordString += format(self.MXEPS, ">10.3e")
        keywordString += format(self.EPSSH, ">10.3e")
        keywordString += format(self.SIGTH, ">10.3e")
        keywordString += format(self.IMPULSE, ">10.3e")
        keywordString += format(self.FAILTM, ">10.3e")
        keywordString += "\n"        
        keywordString += format(self.IDAM, ">10.3e")
        keywordString += format(self.LCREGD, ">10.3e")
        keywordString += "\n"
        keywordString += format(self.LCFLD, ">10.3e")
        keywordString += format(self.NSFF, ">10.3e")
        keywordString += format(self.EPSTHIN, ">10.3e")
        keywordString += format(self.ENGCRT, ">10.3e")
        keywordString += format(self.RADCRT, ">10.3e")        
        keywordString += format(self.LCEPS12, ">10")
        keywordString += format(self.LCEPS13, ">10")
        keywordString += format(self.LCEPSMX, ">10")
        keywordString += "\n"
        keywordString += format(self.DTEFLT, ">10.3e")
        keywordString += format(self.VOLFRAC, ">10.3e")
        keywordString += format(self.MXTMP, ">10.3e")
        keywordString += format(self.DTMIN, ">10.3e")
        keywordString += "\n"
        self.SetDynaKeyword(keywordString)
        return keywordString            
    
class KooMaterialAddPZElectric(KooMaterial):
    def __init__(self, mid, dtype, gpt, aopt, DMat, PXMat, PYMat, PZMat,Pnt,AVec,DVec):
        
        super(KooMaterialAddPZElectric,self).__init__(mid, "Mat{0}".format(mid))
        
        self.dtype = dtype
        self.gpt = gpt
        self.aopt = aopt
        self.DMat = DMat
        self.PXMat = PXMat
        self.PYMat = PYMat
        self.PZMat = PZMat
        self.Pnt = Pnt
        self.AVec = AVec
        self.DVec = DVec
        
    def AddtoDynaKeyword(self, keyword : MatAddPZElectric):
        keyword.AddMatAddPZElectric(self.id, self.dtype, self.gpt, self.aopt, self.DMat, self.PXMat, self.PYMat, self.PZMat, self.Pnt, self.AVec, self.DVec)
    
    def GenerateDynaKeyword(self):
        keywordString = "*MAT_ADD_PZELECTRIC\n"
        keywordString += "$$     MID     DTYPE       GPT      AOPT\n"
        keywordString += format(self.id, ">10")
        keywordString += format(self.dtype, ">10")
        keywordString += format(self.gpt, ">10")
        keywordString += format(self.aopt, ">10")
        keywordString += "\n"   
        keywordString += "$$     DXX       DYY       DZZ       DXY       DXZ       DYZ\n"
        keywordString += format(self.DMat[0][0], ">10.3e")
        keywordString += format(self.DMat[1][1], ">10.3e")
        keywordString += format(self.DMat[2][2], ">10.3e")
        keywordString += format(self.DMat[0][1], ">10.3e")
        keywordString += format(self.DMat[0][2], ">10.3e")
        keywordString += format(self.DMat[1][2], ">10.3e")
        keywordString += "\n"
        keywordString += "$$    PX11      PX22      PX33      PX12      PX13      PX23      PY11      PY22\n"
        keywordString += format(self.PXMat[0][0], ">10.3e")
        keywordString += format(self.PXMat[1][1], ">10.3e")
        keywordString += format(self.PXMat[2][2], ">10.3e")
        keywordString += format(self.PXMat[0][1], ">10.3e")
        keywordString += format(self.PXMat[0][2], ">10.3e")
        keywordString += format(self.PXMat[1][2], ">10.3e")
        keywordString += format(self.PYMat[0][0], ">10.3e")
        keywordString += format(self.PYMat[1][1], ">10.3e")
        keywordString += "\n"
        keywordString += "$$    PY33      PY12      PY13      PY23      PZ11      PZ22      PZ33      PZ12\n"
        keywordString += format(self.PYMat[2][2], ">10.3e")
        keywordString += format(self.PYMat[0][1], ">10.3e")
        keywordString += format(self.PYMat[0][2], ">10.3e")
        keywordString += format(self.PYMat[1][2], ">10.3e")
        keywordString += format(self.PZMat[0][0], ">10.3e")
        keywordString += format(self.PZMat[1][1], ">10.3e")
        keywordString += format(self.PZMat[2][2], ">10.3e")
        keywordString += format(self.PZMat[0][1], ">10.3e")
        keywordString += "\n"
        keywordString += "$$    PZ13      PZ23\n"
        keywordString += format(self.PZMat[0][2], ">10.3e")
        keywordString += format(self.PZMat[1][2], ">10.3e")
        keywordString += "\n"   
        keywordString += "$$      XP        YP        ZP        A1        A2        A3\n"        
        keywordString += format(self.Pnt[0], ">10.3e")
        keywordString += format(self.Pnt[1], ">10.3e")  
        keywordString += format(self.Pnt[2], ">10.3e")
        keywordString += format(self.AVec[0], ">10.3e")
        keywordString += format(self.AVec[1], ">10.3e")
        keywordString += format(self.AVec[2], ">10.3e")
        keywordString += "\n"
        keywordString += "$$                                    D1        D2        D3\n"
        keywordString += format(" ", ">10")
        keywordString += format(" ", ">10")
        keywordString += format(" ", ">10")        
        keywordString += format(self.DVec[0], ">10.3e")
        keywordString += format(self.DVec[1], ">10.3e")
        keywordString += format(self.DVec[2], ">10.3e")
        keywordString += "\n"
        
        
        self.SetDynaKeyword(keywordString)
        return keywordString       
    
class KooMaterialRigid(KooMaterial):
    def __init__(self, id = 0, name = "", rho = 0.0, E = 0.0, nu = 0.3, N = 0, COUPLE = 0, M = 0, ALIASRE = "", CMO = 0.0, CON1 = "", CON2 = "", LCOA1 = 0.0, A2 = 0.0, A3 = 0.0, V1=0.0, V2=0.0,V3=0.0):
        super().__init__(id, name)
        self.rho = rho
        self.E = E
        self.nu = nu
        self.N = N
        self.COUPLE = COUPLE
        self.M = M
        self.ALIASRE = ALIASRE
        self.CMO = CMO
        self.CON1 = CON1
        self.CON2 = CON2
        self.LCOA1 = LCOA1
        self.A2 = A2
        self.A3 = A3        
        self.V1 = V1
        self.V2 = V2
        self.V3 = V3
        
    def GetE(self):
        return self.E

    def GetRho(self):
        return self.rho
    
    def GetNu(self):
        return self.nu
    
    def AddtoDynaKeyword(self, keyword : MatRigidTitle):
        keyword.AddMatRigidTitle(self.id,self.name, self.rho, self.E, self.nu, self.N, self.COUPLE, self.M, self.ALIASRE, self.CMO, self.CON1, self.CON2, self.LCOA1, self.A2, self.A3, self.V1, self.V2, self.V3)
    
    def GenerateDynaKeyword(self):
        keywordString = "*MAT_RIGID_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        if type(self.ALIASRE) == str:
            formatted_string = "{:10d}{:10.3e}{:10.3e}{:10.3e}{:10.3f}{:10.3f}{:10.3f}{:10s}\n".format(self.id, self.rho, self.E, self.nu, self.N, self.COUPLE, self.M, self.ALIASRE)
        else:
            formatted_string = "{:10d}{:10.3e}{:10.3e}{:10.3e}{:10.3f}{:10.3f}{:10.3f}{:10.3f}\n".format(self.id, self.rho, self.E, self.nu, self.N, self.COUPLE, self.M, self.ALIASRE)
        keywordString += formatted_string
        
        if self.CMO == 0.0:
            formatted_string = "{:10.3e}\n".format(self.CMO)
            keywordString += formatted_string
        else:
            CMO = format(self.CMO, ">10.3e")
            CON1 = format(self.CON1, ">10")
            CON2 = format(self.CON2, ">10")
            keywordString += "{0}{1}{2}\n".format(CMO, CON1, CON2)
        
        formatted_string = "{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}\n".format(self.LCOA1, self.A2, self.A3, self.V1, self.V2, self.V3)
        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString       
                
class KooMaterialElastic(KooMaterial):
    def __init__(self, id = 0, name = "", rho = 0.0, E = 0.0, nu = 0.0):
        super().__init__(id, name)        
        self.rho = rho
        self.E = E
        self.nu = nu
        
    def GetE(self):
        return self.E

    def GetRho(self):
        return self.rho
    
    def GetNu(self):
        return self.nu

    def AddtoDynaKeyword(self, keyword : MatElasticTitle):
        keyword.AddMatElasticTitle(self.id,self.name, self.rho, self.E, self.nu)

    def GenerateDynaKeyword(self):
        keywordString = "*MAT_ELASTIC_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        formatted_string = "{:10d}{:10.3e}{:10.3e}{:10.3e}\n".format(self.id, self.rho, self.E, self.nu)
        
        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString

    def GenerateNastranKeyword(self):
        keywordString = "MAT1    "
        mid = self.id
        E = self.E
        G = E / (2 * (1 + self.nu))
        nu = self.nu
        rho = self.rho
        A = 0.0                
        E = format(E, ">8.2e")
        #E = E.replace("e+0", "e+").replace("e-0", "e-")        
        E = E.replace("e","")
        E = " " + E
        
        #E = " " + E
        
        G = format(G, ">8.2e")        
        G = G.replace("e","")
        G = " " + G
        
        nu = format(nu, ">8.2e")
        nu = nu.replace("e","")
        nu = " " + nu
        #nu = nu.replace("e+0", "e+").replace("e-0", "e-")
        #nu = " " + nu
        rho = format(rho, ">8.2e")
        rho = rho.replace("e","")
        rho = " " + rho
        #rho = rho.replace("e+0", "e+").replace("e-0", "e-")
        #rho = " " + rho
        A = format(A, ">8.2e")
        A = A.replace("e","")
        A = " " + A
        #A = A.replace("e+0", "e+").replace("e-0", "e-")
        #A = " " + A
        
        
        keywordString += format(mid, ">8")
        keywordString += E
        keywordString += G
        keywordString += nu
        keywordString += rho
        keywordString += A
        keywordString += "\n"
        self.SetNastranKeyword(keywordString)
        return keywordString
    
class KooMaterialPlasticKinematic(KooMaterial):
    def __init__(self, id = 0, name = "", rho = 0.0, E = 0.0, nu = 0.0, sigy = 0.0, etan = 0.0, beta = 0.0, src = 0.0, srp = 0.0, fs = 1.0e20, vp = 0.0):
        super().__init__(id, name)
        self.rho = rho
        self.E = E
        self.nu = nu
        self.sigy = sigy
        self.etan = etan
        self.beta = beta
        self.src = src
        self.srp = srp
        self.fs = fs
        self.vp = vp
        
    def GetE(self):
        return self.E

    def GetRho(self):
        return self.rho
    
    def GetNu(self):
        return self.nu
    
    def AddtoDynakeyword(self, keyword : MatPlasticKinematicTitle):
        keyword.AddMatPlasticKinematic(self.id,self.name, self.rho, self.E, self.nu, self.sigy, self.etan, self.beta, self.src, self.srp, self.fs, self.vp)
        
    def GenerateDynaKeyword(self):
        keywordString = "*MAT_PLASTIC_KINEMATIC_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        keywordString += format(self.id, ">10")
        keywordString += format(self.rho, ">10.3e")
        keywordString += format(self.E, ">10.3e")
        keywordString += format(self.nu, ">10.3e")
        keywordString += format(self.sigy, ">10.3e")
        keywordString += format(self.etan, ">10.3e")
        keywordString += format(self.beta, ">10.3e")
        keywordString += "\n"
        keywordString += format(self.src, ">10.3e")
        keywordString += format(self.srp, ">10.3e")
        keywordString += format(self.fs, ">10.3e")
        keywordString += format(self.vp, ">10.3e")
        keywordString += "\n"
        self.SetDynaKeyword(keywordString)
        return keywordString        


class KooMaterialViscoelastic(KooMaterial):
    
    def __init__(self, id = 0, name = "", rho = 0.0, K = 0.0, G0 = 0.0, GI = 0.0, BETA = 0.0):
        super().__init__(id, name)
        self.rho = rho
        self.K = K
        self.G0 = G0
        self.GI = GI
        self.BETA = BETA
    
    def GetE(self):
        E0 = 9*self.K*self.G0/(3*self.K+self.G0)
        return E0

    def GetRho(self):
        return self.rho
    
    def GetNu(self):
        nu = (3*self.K-self.GetE())/(6*self.K)
        return nu
    
    def AddtoDynaKeyword(self, keyword : MatViscoelasticTitle):
        keyword.AddMatViscoelasticTitle(self.id,self.name, self.rho, self.K, self.G0, self.GI, self.BETA)
    
    def GenerateDynaKeyword(self):
        keywordString = "*MAT_VISCOELASTIC_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        formatted_string = "{:10d}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}\n".format(self.id, self.rho, self.K, self.G0, self.GI, self.BETA)

        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString
    
    def GenerateNastranKeyword(self):
        # MAT1 , K, G0 to E , it is temporary
        keywordString = "MAT1    "
        mid = self.id
        E0 = 9*self.K*self.G0/(3*self.K+self.G0)
        nu = (3*self.K-E0)/(6*self.K)
        rho = self.rho
        A = 0.0 
        E = format(E0, ">8.2e")
        E = E.replace("e","")
        E = " " + E
        
        G = format(self.G0, ">8.2e")
        G = G.replace("e","")
        G = " " + G
        
        nu = format(nu, ">8.2e")
        nu = nu.replace("e","")
        nu = " " + nu
        
        rho = format(rho, ">8.2e")
        rho = rho.replace("e","")
        rho = " " + rho
        
        A = format(A, ">8.2e")
        A = A.replace("e","")
        A = " " + A
        
        keywordString += format(mid, ">8")
        keywordString += E
        keywordString += G
        keywordString += nu
        keywordString += rho
        keywordString += A
        keywordString += "\n"
        self.SetNastranKeyword(keywordString)
        return keywordString
            
        
class KooMaterialOrientedCrack(KooMaterial):
    def __init__(self, id = 0, RO = 0.0, E = 0.0, PR = 0.0, SIGY = 0.0, ETAN = 0.0, FS = 0.0, PRF = 0.0, SOFT = 0.0, CVELO = 0.0):
        super().__init__(id, "Mat{0}".format(id))        
        self.RO = RO
        self.E = E
        self.PR = PR
        self.SIGY = SIGY
        self.ETAN = ETAN
        self.FS = FS
        self.PRF = PRF
        self.SOFT = SOFT
        self.CVELO = CVELO
    
    def GetE(self):
        return self.E

    def GetRho(self):
        return self.RO
    
    def GetNu(self):
        return self.PR
    
    def AddtoDynaKeyword(self, keyword : MatOrientedCrack):
        keyword.AddMatOrientedCrack(self.id,self.RO, self.E, self.PR, self.SIGY, self.ETAN, self.FS, self.PRF, self.SOFT, self.CVELO)

    def GenerateDynaKeyword(self):
        keywordString = "*MAT_ORIENTED_CRACK\n"
        # 10 digit for each float
        formatted_string = "{:10d}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}\n".format(self.id, self.RO, self.E, self.PR, self.SIGY, self.ETAN, self.FS, self.PRF)
        keywordString += formatted_string
        formatted_string = "{:10.3e}{:10.3e}\n".format(self.SOFT, self.CVELO)
        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString

class KooMaterialCohesiveMixedMode(KooMaterial):
    def __init__(self, id = 0, name = "", RO = 0.0, ROFLG = 0, INTFAIL = 0.0, EN = 0.0, ET = 0.0, GIC = 0.0, GIIC = 0.0, XMU = 0.0, T = 0.0, S = 0.0, UND = 0.0, UTD = 0.0, GAMMA = 0.0):
        super().__init__(id, name)
        self.RO = RO
        self.ROFLG = ROFLG
        self.INTFAIL = INTFAIL
        self.EN = EN
        self.ET = ET
        self.GIC = GIC
        self.GIIC = GIIC
        self.XMU = XMU
        self.T = T
        self.S = S
        self.UND = UND
        self.UTD = UTD
        self.GAMMA = GAMMA

    def GetRO(self):
        return self.RO

    def GetROFLG(self):
        return self.ROFLG

    def GetINTFAIL(self):
        return self.INTFAIL

    def GetEN(self):
        return self.EN

    def GetET(self):
        return self.ET

    def GetGIC(self):
        return self.GIC

    def GetGIIC(self):
        return self.GIIC

    def GetXMU(self):
        return self.XMU

    def GetT(self):
        return self.T

    def GetS(self):
        return self.S

    def GetUND(self):
        return self.UND

    def GetUTD(self):
        return self.UTD

    def GetGAMMA(self):
        return self.GAMMA
    
    def AddtoDynaKeyword(self, keyword : MatCohesiveMixedModeTitle):
        keyword.AddMatCohesiveMixedModeTitle(self.id,self.name, self.RO, self.ROFLG, self.INTFAIL, self.EN, self.ET, self.GIC, self.GIIC, self.XMU, self.T, self.S, self.UND, self.UTD, self.GAMMA)

    def GenerateDynaKeyword(self):
        keywordString = "*MAT_COHESIVE_MIXED_MODE_TITLE\n"
        keywordString += "$$   TITLE\n"
        keywordString += "{}\n".format(self.name)
        keywordString += "$$     MID        RO     ROFLG   INTFAIL        EN        ET       GIC      GIIC\n"
        keywordString += "{:10d}{:10.3e}{:10d}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}\n".format(self.id, self.RO, self.ROFLG, self.INTFAIL, self.EN, self.ET, self.GIC, self.GIIC)
        keywordString += "$$     XMU        T         S       UND       UTD     GAMMA\n"
        keywordString += "{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}\n".format(self.XMU, self.T, self.S, self.UND, self.UTD, self.GAMMA)
        self.SetDynaKeyword(keywordString)
        return keywordString

class KooMaterialElasticPeri(KooMaterial):
    def __init__(self, id = 0, name = "", R0 = 0.0, E = 0.0, GT = 0.0, GS = 0.0):
        super().__init__(id, name)
        self.R0 = R0
        self.E = E
        self.GT = GT
        self.GS = GS
        
    def GetE(self):
        return self.E

    def GetRho(self):
        return self.R0
    
    def GetNu(self):
        return 0.3
    
    def AddtoDynaKeyword(self, keyword : MatElasticPeri):
        keyword.AddMatElasticPeri(self.id,self.name, self.R0, self.E, self.GT, self.GS)
        
    def GenerateDynaKeyword(self):
        keywordString = "*MAT_ELASTIC_PERI_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        keywordString += "$$     MID        RO         E        GT        GS\n"
        formatted_string = "{:10d}{:10.3e}{:10.3e}{:10.3e}{:10.3e}\n".format(self.id, self.R0, self.E, self.GT, self.GS)
        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString    
    
class KooMaterialPiecewiseLinearPlasticity(KooMaterial):
    def __init__(self, id = 0, name = "", rho = 0.0, E = 0.0, nu = 0.0, sigy = 0.0, etan = 0.0, fail = 0.0, tdel = 0.0, c = 0.0, p = 0.0, lcss = 0.0, lcsr = 0.0, vp = 0.0, eps = [], es = []):
        super().__init__(id, name)        
        self.rho = rho
        self.E = E
        self.nu = nu
        self.sigy = sigy
        self.etan = etan
        self.fail = fail
        self.tdel = tdel
        self.c = c
        self.p = p
        self.lcss = lcss
        self.lcsr = lcsr
        self.vp = vp
        self.eps = eps
        self.es = es
        
    def GetE(self):
        return self.E

    def GetRho(self):
        return self.rho
    
    def GetNu(self):
        return self.nu
    
    def AddtoDynaKeyword(self, keyword : MatPiecewiseLinearPlasticityTitle):
        keyword.AddMatPiecewiseLinearPlasticityTitle(self.id,self.name, self.rho, self.E, self.nu, self.sigy, self.etan, self.fail, self.tdel, self.c, self.p, self.lcss, self.lcsr, self.vp, self.eps, self.es)

    def GenerateDynaKeyword(self):
        keywordString = "*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        formatted_string = "{:10d}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}\n".format(self.id, self.rho, self.E, self.nu, self.sigy, self.etan, self.fail, self.tdel)
        keywordString += formatted_string
        formatted_string = "{:10.3e}{:10.3e}{:10d}{:10d}{:10.3e}\n".format(self.c, self.p, self.lcss, self.lcsr, self.vp)
        keywordString += formatted_string
        formatted_string = ""
        # print eps which has size of larger than 8
        for i in range(0, len(self.eps), 8):
            for j in range(i, i+8):
                if j < len(self.eps):
                    formatted_string += "{:10.3e}".format(self.eps[j])
            formatted_string += "\n"
        keywordString += formatted_string
        formatted_string = ""
        # print es which has size of larger than 8
        for i in range(0, len(self.es), 8):
            for j in range(i, i+8):
                if j < len(self.es):
                    formatted_string += "{:10.3e}".format(self.es[j])
            formatted_string += "\n"
        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString
    
class KooMaterialLowDensityFoam(KooMaterial):
    def __init__(self, id = 0, name = "", rho = 0.0, E = 0.0, LCID = 0, TC = 0.0, HU = 0.0, BETA = 0.0, DAMP = 0.0, SHAPE = 0.0, FAIL = 0.0, BVFLAG = 0.0, ED = 0.0, BETA1 = 0.0, KCON = 0.0, REF = 0.0):
        super().__init__(id, name)        
        self.rho = rho
        self.E = E
        self.LCID = LCID
        self.TC = TC
        self.HU = HU
        self.BETA = BETA
        self.DAMP = DAMP
        self.SHAPE = SHAPE
        self.FAIL = FAIL
        self.BVFLAG = BVFLAG
        self.ED = ED
        self.BETA1 = BETA1
        self.KCON = KCON
        self.REF = REF
    
    def GetE(self):
        return self.E

    def GetRho(self):
        return self.rho
    
    def GetNu(self):
        return 0.49
    
    def AddtoDynaKeyword(self, keyword : MatLowDensityFoamTitle):
        keyword.AddMatLowDensityFoamTitle(self.id,self.name, self.rho, self.E, self.LCID, self.TC, self.HU, self.BETA, self.DAMP, self.SHAPE, self.FAIL, self.BVFLAG, self.ED, self.BETA1, self.KCON, self.REF)

    def GenerateDynaKeyword(self):
        keywordString = "*MAT_LOW_DENSITY_FOAM_TITLE\n"
        keywordString += "{0}\n".format(self.name)
        # 10 digit for each float
        keywordString += "$$     MID        RO         E      LCID        TC        HU      BETA      DAMP\n"
        formatted_string = "{:10d}{:10.3e}{:10.3e}{:10d}{:10.3e}{:10.3e}{:10.3e}{:10.3e}\n".format(self.id, self.rho, self.E, self.LCID, self.TC, self.HU, self.BETA, self.DAMP)
        keywordString += formatted_string
        keywordString += "$$   SHAPE      FAIL    BVFLAG        ED     BETA1      KCON       REF\n"
        formatted_string = "{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}{:10.3e}\n".format(self.SHAPE, self.FAIL, self.BVFLAG, self.ED, self.BETA1, self.KCON, self.REF)
        keywordString += formatted_string
        self.SetDynaKeyword(keywordString)
        return keywordString

class KooMaterialManager():
    def __init__(self):
        self.maxid = 0
        self.materials = {}
        self.tmpMaterials = {}
        self.rigidMaterials = {}
        self.eos = {}
        self.addErosions = {}
        self.addPZElectric = {}

    def OffsetID(self, offsetID):
        for key in self.materials:
            material = self.materials[key]
            material.id += offsetID
        for key in self.tmpMaterials:
            material = self.tmpMaterials[key]
            material.id += offsetID
        for key in self.rigidMaterials:
            material = self.rigidMaterials[key]
            material.id += offsetID
        for key in self.eos:
            eos = self.eos[key]
            eos.id += offsetID
        for key in self.addErosions:
            addErosion = self.addErosions[key]
            addErosion.id += offsetID
        for key in self.addPZElectric:
            addPZElectric = self.addPZElectric[key]
            addPZElectric.id += offsetID
        self.maxid += offsetID

    def OverwritefromMaterialManager(self, materialManager : KooMaterialManager):
        self.maxid = max(self.maxid, materialManager.maxid)
        for key, value in materialManager.materials.items():
            self.materials[key] = value
        for key, value in materialManager.tmpMaterials.items():
            self.tmpMaterials[key] = value
        for key, value in materialManager.rigidMaterials.items():
            self.rigidMaterials[key] = value
        for key, value in materialManager.eos.items():
            self.eos[key] = value
        for key, value in materialManager.addErosions.items():
            self.addErosions[key] = value
        for key, value in materialManager.addPZElectric.items():
            self.addPZElectric[key] = value

    def GenerateAddErosionusingDtmin(self, dtmin = 1.0e-6):
        for matid in self.materials:
            if matid in self.addErosions:
                continue
            else:
                self.CreateAddErosionMaterial(mid=matid,DTMIN=dtmin)
                
    def GenerateRigidMaterialswithOffsetID(self, offsetID):
        self.rigidMaterials = {}\
        
        for matid in self.materials:
            mat = self.materials[matid]
            E = mat.GetE()
            nu = mat.GetNu()
            rho = mat.GetRho()
            name = "Rigid" + mat.name
            newRigidMat = KooMaterialRigid(matid + offsetID, name, rho, E, nu)
            self.rigidMaterials[matid] = newRigidMat            
            self.maxid = max(self.maxid, matid + offsetID)
        for matid in self.rigidMaterials:
            self.materials[matid + offsetID] = self.rigidMaterials[matid]
        
    def GenerateRigidMaterials(self, curMIDExcept=[]):
        self.rigidMaterials = {}
        for matid in self.materials:
            isRigid = True
            for curMID in curMIDExcept:
                if curMID == matid:
                    isRigid = False
                    break
            if isRigid == False:
                continue
            mat = self.materials[matid]
            E = mat.GetE()
            nu = mat.GetNu()
            rho = mat.GetRho()
            name = "Rigid" + mat.name
            newRigidMat = KooMaterialRigid(matid, name, rho, E, nu)
            self.rigidMaterials[matid] = newRigidMat
            
    def ExchangetoRigid(self,curMIDExcept = []):
        self.GenerateRigidMaterials(curMIDExcept)
        self.tmpMaterials = self.materials
        self.materials = self.rigidMaterials
    
    def ExchangetoOriginal(self):
        self.materials = self.tmpMaterials
        self.tmpMaterials = {}
        self.rigidMaterials = {}
        
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
    
    def AddMaterial(self, material):
        '''if material.id in self.materials:
            material.id = self.maxid + 1
            self.maxid += 1'''
        if material.id == 0:
            material.id = self.maxid + 1
            self.maxid += 1
        else:
            self.maxid = max(self.maxid, material.id)


        self.materials[material.id] = material

    def CloneMaterial(self, source_material, name_suffix=''):
        """
        Material 복제 및 자동 ID 할당

        Args:
            source_material: 원본 Material 객체
            name_suffix: 이름에 추가할 접미사 (예: '_IGA')

        Returns:
            새로 생성된 Material (ID 자동 할당됨)
        """
        import copy

        # 원본 Material 복제 (deep copy)
        cloned = copy.deepcopy(source_material)

        # ID를 0으로 설정하면 AddMaterial이 자동 할당
        cloned.id = 0

        # 이름에 접미사 추가
        cloned.name = source_material.name + name_suffix

        # dynaKeywordString 초기화 (재생성 필요)
        cloned.dynaKeywordString = None

        # Manager에 추가 (ID 자동 할당)
        self.AddMaterial(cloned)

        return cloned
    
    def RemoveMaterialbyID(self, id):
        if id in self.materials:
            del self.materials[id]
        
    def FindMaterialfromID(self, id):
        if id not in self.materials:
            print(str(id) + " is not in the material list.") 
            return None
        return self.materials[id]
    
    def CreateEOSTabulated(self, id, gama = 0, e0 = 0, v0 = 0, lcc = "", lct = "", evList=[], CList=[], TList=[]):
        eos = KooEOSTabulated(id, gama, e0, v0, lcc, lct, evList, CList, TList)
        self.eos[id] = eos
        return eos
    
    def CreateEOSLinearPolynomial(self, id = 0, c0 = 0.0, c1 = 0.0, c2 = 0.0, c3 = 0.0, c4 = 0.0, c5 = 0.0, c6 = 0.0, e0 = 0.0, v0 = 0.0):
        eos = KooEOSLinearPolynomial(id, c0, c1, c2, c3, c4, c5, c6, e0, v0)
        self.eos[id] = eos
        return eos
    
    def CreateAddErosionMaterial(self, mid = 0, EXCL=0.0, MXPRES=0.0, MNEPS=0.0, EFFEPS=0.0, VOLEPS=0.0, NUMFIP=1.0, NCS=1.0,MNPRES=0.0, SIGP1=0.0, SIGVM=0.0, MXEPS=0.0, EPSSH=0.0, SIGTH=0.0, IMPULSE=0.0, FAILTM=0.0, IDAM=0.0, LCREGD=0.0, LCFLD=0.0, NSFF=0.0, EPSTHIN=0.0, ENGCRT=0.0, RADCRT=0.0, LCEPS12=0, LCEPS13=0, LCEPSMX=0, DTEFLT=0.0, VOLFRAC=0.5, MXTMP=1.0e20, DTMIN=0.0):        
        addErosion = KooMaterialAddErosion(mid, EXCL, MXPRES, MNEPS, EFFEPS, VOLEPS, NUMFIP, NCS,MNPRES, SIGP1, SIGVM, MXEPS, EPSSH, SIGTH, IMPULSE, FAILTM, IDAM, LCREGD, LCFLD, NSFF, EPSTHIN, ENGCRT, RADCRT, LCEPS12, LCEPS13, LCEPSMX, DTEFLT, VOLFRAC, MXTMP, DTMIN)
        self.addErosions[mid] = addErosion
        return addErosion

    def CreateAddPZElectricMaterial(self, mid = 0, dtype = "S", gpt = 8, aopt = 0, DMat = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]], PXMat = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]], PYMat = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]], PZMat = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]], Pnt = [0.0,0.0,0.0], AVec = [0.0,0.0,0.0], DVec = [0.0,0.0,0.0]):
        addPZElectric = KooMaterialAddPZElectric(mid, dtype, gpt, aopt, DMat, PXMat, PYMat, PZMat, Pnt, AVec, DVec)
        self.addPZElectric[mid] = addPZElectric
        return addPZElectric
    
    def CreateRigidMaterial(self, name, rho, E, nu, N = 0, COUPLE = 0, M = 0, ALIASRE = "", CMO = 0.0, CON1 = "", CON2 = "", LCOA1 = 0.0, A2 = 0.0, A3 = 0.0, V1=0.0, V2=0.0,V3=0.0):
        mat = KooMaterialRigid(0, name, rho, E, nu, N, COUPLE, M, ALIASRE, CMO, CON1, CON2, LCOA1, A2, A3, V1, V2, V3)
        self.AddMaterial(mat)
        return mat
        
    def CreateElasticMaterial(self, name, rho, E, nu):
        mat = KooMaterialElastic(0, name, rho, E, nu)
        self.AddMaterial(mat)
        return mat       
    
    def CreatePlasticKinematicMaterial(self, name, rho, E, nu, sigy, etan, beta, src, srp, fs, vp):
        mat = KooMaterialPlasticKinematic(0, name, rho, E, nu, sigy, etan, beta, src, srp, fs, vp)
        self.AddMaterial(mat)
        return mat
    
    def CreateViscoelasticMaterial(self, name, rho, K, G0, GI, BETA):
        mat = KooMaterialViscoelastic(0, name, rho, K, G0, GI, BETA)
        self.AddMaterial(mat)
        return mat
    
    def CreateCohesiveMixedModeMaterial(self, name, RO, ROFLG, INTFAIL, EN, ET, GIC, GIIC, XMU, T, S, UND, UTD, GAMMA): 
        mat = KooMaterialCohesiveMixedMode(0, name, RO, ROFLG, INTFAIL, EN, ET, GIC, GIIC, XMU, T, S, UND, UTD, GAMMA)
        self.AddMaterial(mat)
        return mat

    def AddEOSfromDyna(self, eosMaterial):
        if eosMaterial[0] == "*EOS_LINEAR_POLYNOMIAL":
            firstLine = eosMaterial[1]
            secondLine = eosMaterial[2]
            mid = KooDynaInt(firstLine[0])
            c0 = KooDynaFloat(firstLine[1])
            c1 = KooDynaFloat(firstLine[2])
            c2 = KooDynaFloat(firstLine[3])
            c3 = KooDynaFloat(firstLine[4])
            c4 = KooDynaFloat(firstLine[5])
            c5 = KooDynaFloat(firstLine[6])
            c6 = KooDynaFloat(firstLine[7])
            e0 = KooDynaFloat(secondLine[0])
            v0 = KooDynaFloat(secondLine[1])
            self.CreateEOSLinearPolynomial(mid, c0, c1, c2, c3, c4, c5, c6, e0, v0)    
        
        elif eosMaterial[0] == "*EOS_TABULATED":
           
            firstLine = eosMaterial[1]
            
            mid = KooDynaInt(firstLine[0])
            gama = KooDynaFloat(firstLine[1])
            e0 = KooDynaFloat(firstLine[2])
            v0 = KooDynaFloat(firstLine[3])
            lcc = KooDynaString(firstLine[4])
            lct = KooDynaString(firstLine[5])           
            curLine = eosMaterial[2]
            curLine.extend(eosMaterial[3])
            
            evList = []
            for i in range(0, len(curLine)):
                evList.append(KooDynaFloat(curLine[i]))
            curLine = eosMaterial[4]
            curLine.extend(eosMaterial[5])
            CList = []
            for i in range(0, len(curLine)):
                CList.append(KooDynaFloat(curLine[i]))
            curLine = eosMaterial[6]
            curLine.extend(eosMaterial[7])
            TList = []
            for i in range(0, len(curLine)):
                TList.append(KooDynaFloat(curLine[i]))
            self.CreateEOSTabulated(mid, gama, e0, v0, lcc, lct, evList, CList, TList)
    
    def AddMaterialfromDyna(self, dynaMaterial,forcedid = 0):
        if dynaMaterial[0] == "*MAT_ADD_EROSION":  
            curDynaMaterial = dynaMaterial[1]
            firstLine = curDynaMaterial[0]
            if len(dynaMaterial) > 2:
                secondLine = curDynaMaterial[1]
            else:
                secondLine = ["" for i in range(0,8)]
            if len(curDynaMaterial) > 3:
                thirdLine = curDynaMaterial[2]
            else:
                thirdLine = ["" for i in range(0,8)]
            if len(curDynaMaterial) > 4:
                fourthLine = curDynaMaterial[3]
            else:
                fourthLine = ["" for i in range(0,8)]
            if len(curDynaMaterial) > 5:
                fifthLine = curDynaMaterial[4]
            else:
                fifthLine = ["" for i in range(0,8)]
            mid = KooDynaInt(firstLine[0])            
            EXCL = KooDynaFloat(firstLine[1])
            MXPRES = KooDynaFloat(firstLine[2])
            MNEPS = KooDynaFloat(firstLine[3])
            EFFEPS = KooDynaFloat(firstLine[4])
            VOLEPS = KooDynaFloat(firstLine[5])
            NUMFIP = KooDynaFloat(firstLine[6],1.0)
            NCS = KooDynaFloat(firstLine[7],1.0)
            MNPRES = KooDynaFloat(secondLine[0],0.0)
            SIGP1 = KooDynaFloat(secondLine[1],0.0)
            SIGVM = KooDynaFloat(secondLine[2],0.0)
            MXEPS = KooDynaFloat(secondLine[3],0.0)
            EPSSH = KooDynaFloat(secondLine[4],0.0)
            SIGTH = KooDynaFloat(secondLine[5],0.0)
            IMPULSE = KooDynaFloat(secondLine[6],0.0)
            FAILTM = KooDynaFloat(secondLine[7],0.0)
            IDAM = KooDynaFloat(thirdLine[0],0.0)
            LCREGD = KooDynaFloat(thirdLine[1],0.0)
            LCFLD = KooDynaFloat(thirdLine[2],0.0)
            NSFF = KooDynaFloat(thirdLine[3],0.0)
            EPSTHIN = KooDynaFloat(fourthLine[0],0.0)
            ENGCRT = KooDynaFloat(fourthLine[1],0.0)
            RADCRT = KooDynaFloat(fourthLine[2],0.0)
            LCEPS12 = KooDynaInt(fourthLine[3],0)
            LCEPS13 = KooDynaInt(fourthLine[4],0)
            LCEPSMX = KooDynaInt(fourthLine[5],0)
            DTEFLT = KooDynaFloat(fifthLine[0],0.0)
            VOLFRAC = KooDynaFloat(fifthLine[1],0.5)
            MXTMP = KooDynaFloat(fifthLine[2],1.0E20)
            DTMIN = KooDynaFloat(fifthLine[3],0.0)
            if forcedid != 0:
                mid = forcedid
            mat = self.CreateAddErosionMaterial(mid, EXCL, MXPRES, MNEPS, EFFEPS, VOLEPS, NUMFIP, NCS,MNPRES, SIGP1, SIGVM, MXEPS, EPSSH, SIGTH, IMPULSE, FAILTM, IDAM, LCREGD, LCFLD, NSFF, EPSTHIN, ENGCRT, RADCRT, LCEPS12, LCEPS13, LCEPSMX, DTEFLT, VOLFRAC, MXTMP, DTMIN)                    
        elif dynaMaterial[0] == "*MAT_ADD_PZELECTRIC":
            curDynaMaterial = dynaMaterial[1]
            firstLine = curDynaMaterial[0]
            secondLine = curDynaMaterial[1]
            thirdLine = curDynaMaterial[2]
            fourthLine = curDynaMaterial[3]
            fifthLine = curDynaMaterial[4]
            sixthLine = curDynaMaterial[5]
            seventhLine = curDynaMaterial[6]
            mid = KooDynaInt(firstLine[0])
            dtype = KooDynaString(firstLine[1],"S")
            gpt = KooDynaInt(firstLine[2],8)
            aopt = KooDynaInt(firstLine[3],0)
            DXX = KooDynaFloat(secondLine[0],0.0)
            DYY = KooDynaFloat(secondLine[1],0.0)
            DZZ = KooDynaFloat(secondLine[2],0.0)
            DXY = KooDynaFloat(secondLine[3],0.0)
            DXZ = KooDynaFloat(secondLine[4],0.0)
            DYZ = KooDynaFloat(secondLine[5],0.0)
            PX11 = KooDynaFloat(thirdLine[0],0.0)
            PX22 = KooDynaFloat(thirdLine[1],0.0)
            PX33 = KooDynaFloat(thirdLine[2],0.0)
            PX12 = KooDynaFloat(thirdLine[3],0.0)
            PX13 = KooDynaFloat(thirdLine[4],0.0)
            PX23 = KooDynaFloat(thirdLine[5],0.0)
            PY11 = KooDynaFloat(thirdLine[6],0.0)
            PY22 = KooDynaFloat(thirdLine[7],0.0)
            PY33 = KooDynaFloat(fourthLine[0],0.0)
            PY12 = KooDynaFloat(fourthLine[1],0.0)
            PY13 = KooDynaFloat(fourthLine[2],0.0)
            PY23 = KooDynaFloat(fourthLine[3],0.0)
            PZ11 = KooDynaFloat(fourthLine[4],0.0)
            PZ22 = KooDynaFloat(fourthLine[5],0.0)
            PZ33 = KooDynaFloat(fourthLine[6],0.0)
            PZ12 = KooDynaFloat(fourthLine[7],0.0)
            PZ13 = KooDynaFloat(fifthLine[0],0.0)
            PZ23 = KooDynaFloat(fifthLine[1],0.0)
            XP = KooDynaFloat(sixthLine[0],0.0)
            YP = KooDynaFloat(sixthLine[1],0.0)
            ZP = KooDynaFloat(sixthLine[2],0.0)
            A1 = KooDynaFloat(sixthLine[3],0.0)
            A2 = KooDynaFloat(sixthLine[4],0.0)
            A3 = KooDynaFloat(sixthLine[5],0.0)
            D1 = KooDynaFloat(seventhLine[3],0.0)
            D2 = KooDynaFloat(seventhLine[4],0.0)
            D3 = KooDynaFloat(seventhLine[5],0.0)
            
            DMat = [[DXX,DXY,DXZ],[DXY,DYY,DYZ],[DXZ,DYZ,DZZ]]
            PXMat = [[PX11,PX12,PX13],[PX12,PX22,PX23],[PX13,PX23,PX33]]
            PYMat = [[PY11,PY12,PY13],[PY12,PY22,PY23],[PY13,PY23,PY33]]
            PZMat = [[PZ11,PZ12,PZ13],[PZ12,PZ22,PZ23],[PZ13,PZ23,PZ33]]
            Pnt = [XP,YP,ZP]
            AVec = [A1,A2,A3]
            DVec = [D1,D2,D3]
            if forcedid != 0:
                mid = forcedid
            self.CreateAddPZElectricMaterial(mid, dtype, gpt, aopt, DMat, PXMat, PYMat, PZMat, Pnt, AVec, DVec)           
                
        elif dynaMaterial[0] == "*MAT_ELASTIC_TITLE":
            if type(dynaMaterial[1]) == list:
                name = dynaMaterial[1][0]
            else:
                name = dynaMaterial[1]            
            firstLine = dynaMaterial[2]            
            if type(firstLine) == list:                
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10])            
        
            id = KooDynaInt(firstLine[0])                            
            rho = KooDynaFloat(firstLine[1],0.0)
            E = KooDynaFloat(firstLine[2],0.0)
            nu = KooDynaFloat(firstLine[3],0.0)
            if forcedid != 0:
                id = forcedid
           
            mat = KooMaterialElastic(id, name, rho, E, nu)
            self.AddMaterial(mat)
        elif dynaMaterial[0] == "*MAT_RIGID":
            firstLine = dynaMaterial[1]
            if type(firstLine) == list:
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10,10,10])
            id = KooDynaInt(firstLine[0])            
            name = "Rigid{0}".format(id)
            rho = KooDynaFloat(firstLine[1],0.0)
            E = KooDynaFloat(firstLine[2],0.0)
            nu = KooDynaFloat(firstLine[3],0.0)
            N = KooDynaFloat(firstLine[4],0.0)
            COUPLE = KooDynaFloat(firstLine[5],0.0)
            M = KooDynaFloat(firstLine[6],0.0)
            ALIASRE = KooDynaString(firstLine[7],"")
            secondLine = dynaMaterial[2]
            if type(secondLine) == list:
                pass
            else:
                secondLine = self.parse_whole(secondLine, [10,10,10])
            CMO = KooDynaFloat(secondLine[0],0.0)
            if len(secondLine) < 3: 
                CON1 = 0
                CON2 = 0
            else:
                CON1 = KooDynaString(secondLine[1],"")
                CON2 = KooDynaString(secondLine[2],"")
            thirdLine = dynaMaterial[3]
            if type(thirdLine) == list:
                pass
            else:
                thirdLine = self.parse_whole(thirdLine, [10,10,10,10,10,10])
            LCOA1 = KooDynaFloat(thirdLine[0],0.0)
            A2 = KooDynaFloat(thirdLine[1],0.0)
            A3 = KooDynaFloat(thirdLine[2],0.0)
            V1 = KooDynaFloat(thirdLine[3],0.0)
            V2 = KooDynaFloat(thirdLine[4],0.0)
            V3 = KooDynaFloat(thirdLine[5],0.0)            
            mat = KooMaterialRigid(id, name, rho, E, nu, N, COUPLE, M, ALIASRE, CMO, CON1, CON2, LCOA1, A2, A3, V1, V2, V3)
            self.AddMaterial(mat)
        elif dynaMaterial[0] == "*MAT_RIGID_TITLE":
            name = dynaMaterial[1][0]
            firstLine = dynaMaterial[2]
            if type(firstLine) == list:
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10,10,10])
            id = KooDynaInt(firstLine[0])               
            rho = KooDynaFloat(firstLine[1],0.0)
            E = KooDynaFloat(firstLine[2],0.0)
            nu = KooDynaFloat(firstLine[3],0.0)
            N = KooDynaFloat(firstLine[4],0.0)
            COUPLE = KooDynaFloat(firstLine[5],0.0)
            M = KooDynaFloat(firstLine[6],0.0)
            ALIASRE = KooDynaString(firstLine[7],"")
            secondLine = dynaMaterial[3]
            if type(secondLine) == list:
                pass
            else:
                secondLine = self.parse_whole(secondLine, [10,10,10])
            CMO = KooDynaFloat(secondLine[0],0.0)
            if len(secondLine) < 3: 
                CON1 = 0
                CON2 = 0
            else:       
                CON1 = KooDynaString(secondLine[1],"")
                CON2 = KooDynaString(secondLine[2],"")
            thirdLine = dynaMaterial[4]
            if type(thirdLine) == list:
                pass
            else:
                thirdLine = self.parse_whole(thirdLine, [10,10,10,10,10,10])
            LCOA1 = KooDynaFloat(thirdLine[0],0.0)
            A2 = KooDynaFloat(thirdLine[1],0.0)
            A3 = KooDynaFloat(thirdLine[2],0.0)
            V1 = KooDynaFloat(thirdLine[3],0.0)
            V2 = KooDynaFloat(thirdLine[4],0.0)
            V3 = KooDynaFloat(thirdLine[5],0.0)
            
            mat = KooMaterialRigid(id, name, rho, E, nu, N, COUPLE, M, ALIASRE, CMO, CON1, CON2, LCOA1, A2, A3, V1, V2, V3)
            self.AddMaterial(mat)
                                
        elif dynaMaterial[0] == "*MAT_ELASTIC":            
            firstLine = dynaMaterial[1]
            if type(firstLine) == list:
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10])            
            id = KooDynaInt(firstLine[0])            
            name = "Elastic{0}".format(id)            
            rho = KooDynaFloat(firstLine[1],0.0)
            E = KooDynaFloat(firstLine[2],0.0)
            nu = KooDynaFloat(firstLine[3],0.0)
            if forcedid != 0:
                id = forcedid            
            mat = KooMaterialElastic(id, name, rho, E, nu)
            self.AddMaterial(mat)
        elif dynaMaterial[0] == "*MAT_PLASTIC_KINEMATIC_TITLE":
            firstLine = dynaMaterial[1]
            if type(firstLine) == list:
                name = firstLine[0]
            else:
                name = firstLine
            secondLine = dynaMaterial[2]
            if type(secondLine) == list:
                pass
            else:
                secondLine = self.parse_whole(secondLine, [10,10,10,10,10,10,10])
            mid = KooDynaInt(secondLine[0])
            if len(secondLine[1].strip()) == 0:
                RO = 0.0
            else:
                RO = float(secondLine[1])
            if len(secondLine[2].strip()) == 0:
                E = 0.0
            else:
                E = float(secondLine[2])
            if len(secondLine[3].strip()) == 0:
                PR = 0.0
            else:
                PR = float(secondLine[3])
            if len(secondLine[4].strip()) == 0:
                SIGY = 0.0
            else:
                SIGY = float(secondLine[4])
            if len(secondLine[5].strip()) == 0:
                ETAN = 0.0
            else:
                ETAN = float(secondLine[5])
            if len(secondLine[6].strip()) == 0:
                BETA = 0.0
            else:
                BETA = float(secondLine[6])
            thirdLine = dynaMaterial[3]
            if type(thirdLine) == list:
                pass
            else:
                thirdLine = self.parse_whole(thirdLine, [10,10,10,10])
            if len(thirdLine[0].strip()) == 0:
                SRC = 0.0
            else:
                SRC = float(thirdLine[0])
            if len(thirdLine[1].strip()) == 0:
                SRP = 0.0
            else:
                SRP = float(thirdLine[1])
            if len(thirdLine[2].strip()) == 0:
                FS = 1.0E20
            else:
                FS = float(thirdLine[2])
            if len(thirdLine[3].strip()) == 0:
                VP = 0.0
            else:
                VP = float(thirdLine[3])
            mat = KooMaterialPlasticKinematic(mid, name, RO, E, PR, SIGY, ETAN, BETA, SRC, SRP, FS, VP)
            self.AddMaterial(mat)
        elif dynaMaterial[0] == "*MAT_PLASTIC_KINEMATIC":
            firstLine = dynaMaterial[1]
            if type(firstLine) == list:
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10,10])            
            mid = KooDynaInt(firstLine[0])
            name = "PlasticKinematic{0}".format(firstLine[0])
            RO = KooDynaFloat(firstLine[1],0.0)
            E = KooDynaFloat(firstLine[2],0.0)
            PR = KooDynaFloat(firstLine[3],0.0)
            SIGY = KooDynaFloat(firstLine[4],0.0)
            ETAN = KooDynaFloat(firstLine[5],0.0)
            BETA = KooDynaFloat(firstLine[6],0.0)
            secondLine = dynaMaterial[2]
            if type(secondLine) == list:
                pass
            else:
                secondLine = self.parse_whole(secondLine, [10,10,10,10])
            SRC= KooDynaFloat(secondLine[0],0.0)
            SRP = KooDynaFloat(secondLine[1],0.0)
            FS = KooDynaFloat(secondLine[2],1.0E20)
            VP = KooDynaFloat(secondLine[3],0.0)
            mat = KooMaterialPlasticKinematic(mid, name, RO, E, PR, SIGY, ETAN, BETA, SRC, SRP, FS, VP)
            self.AddMaterial(mat)
            
        elif dynaMaterial[0] == "*MAT_VISCOELASTIC_TITLE":
            if type(dynaMaterial[1]) == list:
                name = dynaMaterial[1][0]
            else:
                name = dynaMaterial[1]
            firstLine = dynaMaterial[2]
            if type(firstLine) == list:
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10])
            id = KooDynaInt(firstLine[0])
            rho = KooDynaFloat(firstLine[1],0.0)
            K = KooDynaFloat(firstLine[2],0.0)
            G0 = KooDynaFloat(firstLine[3],0.0)
            GI = KooDynaFloat(firstLine[4],0.0)
            BETA = KooDynaFloat(firstLine[5],0.0)
            
            if forcedid != 0:
                id = forcedid
            mat = KooMaterialViscoelastic(id, name, rho, K, G0, GI, BETA)
            self.AddMaterial(mat)
        elif dynaMaterial[0] == "*MAT_VISCOELASTIC":
            firstLine = dynaMaterial[1]
            if type(firstLine) == list:
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10]) 
            id = KooDynaInt(firstLine[0])
            name = "Viscoelastic{0}".format(id)
            rho = KooDynaFloat(firstLine[1],0.0)
            K = KooDynaFloat(firstLine[2],0.0)
            G0 = KooDynaFloat(firstLine[3],0.0)
            GI = KooDynaFloat(firstLine[4],0.0)
            BETA = KooDynaFloat(firstLine[5],0.0)
            if forcedid != 0:
                id = forcedid
            mat = KooMaterialViscoelastic(id, name, rho, K, G0, GI, BETA)
            self.AddMaterial(mat)           
        elif dynaMaterial[0] == "*MAT_ORIENTED_CRACK":
            firstLine = dynaMaterial[1]
            if type(firstLine) == list:
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10,10,10])
            mid = KooDynaInt(firstLine[0])
            RO = KooDynaFloat(firstLine[1])
            E = KooDynaFloat(firstLine[2])
            PR = KooDynaFloat(firstLine[3])
            SIGY = KooDynaFloat(firstLine[4])
            ETAN = KooDynaFloat(firstLine[5])
            FS = KooDynaFloat(firstLine[6])
            PRF = KooDynaFloat(firstLine[7])
            secondLine = dynaMaterial[2]
            if type(secondLine) == list:
                pass
            else:
                secondLine = self.parse_whole(secondLine, [10,10])
            SOFT = KooDynaFloat(secondLine[0])
            CVELO = KooDynaFloat(secondLine[1])
            if forcedid != 0:
                mid = forcedid
            mat = KooMaterialOrientedCrack(mid, RO, E, PR, SIGY, ETAN, FS, PRF, SOFT, CVELO)
            self.AddMaterial(mat)      
        elif dynaMaterial[0] ==  "*MAT_COHESIVE_MIXED_MODE_TITLE":
            name = dynaMaterial[1] 
            firstLine = dynaMaterial[2] 
            secondList = dynaMaterial[3]
            if type(firstLine) == list:
                name = firstLine[0]
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10,10,10])
                secondLine = self.parse_whole(secondList, [10,10,10,10,10,10])
            mid = KooDynaInt(firstLine[0])
            RO = KooDynaFloat(firstLine[1])
            ROFLG = KooDynaInt(firstLine[2])
            INTFAIL = KooDynaFloat(firstLine[3])
            EN = KooDynaFloat(firstLine[4])
            ET = KooDynaFloat(firstLine[5])
            GIC = KooDynaFloat(firstLine[6])
            GIIC = KooDynaFloat(firstLine[7])
            XMU = KooDynaFloat(secondLine[0])
            T = KooDynaFloat(secondLine[1])
            S = KooDynaFloat(secondLine[2])
            UND = KooDynaFloat(secondLine[3])
            UTD = KooDynaFloat(secondLine[4])
            GAMMA = KooDynaFloat(secondLine[5])
            mat = KooMaterialCohesiveMixedMode(mid, name, RO, ROFLG, INTFAIL, EN, ET, GIC, GIIC, XMU, T, S, UND, UTD, GAMMA)
            self.AddMaterial(mat)
        elif dynaMaterial[0] == "*MAT_COHESIVE_MIXED_MODE":
            firstLine = dynaMaterial[1] 
            secondList = dynaMaterial[3]
            if type(firstLine) == list:
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10,10,10])
                secondLine = self.parse_whole(secondList, [10,10,10,10,10,10])
            mid = KooDynaInt(firstLine[0])
            name = "CohesiveMixedMode{0}".format(mid)
            RO = KooDynaFloat(firstLine[1])
            ROFLG = KooDynaInt(firstLine[2])
            INTFAIL = KooDynaFloat(firstLine[3])
            EN = KooDynaFloat(firstLine[4])
            ET = KooDynaFloat(firstLine[5])
            GIC = KooDynaFloat(firstLine[6])
            GIIC = KooDynaFloat(firstLine[7])
            XMU = KooDynaFloat(secondLine[0])
            T = KooDynaFloat(secondLine[1])
            S = KooDynaFloat(secondLine[2])
            UND = KooDynaFloat(secondLine[3])
            UTD = KooDynaFloat(secondLine[4])
            GAMMA = KooDynaFloat(secondLine[5])
            mat = KooMaterialCohesiveMixedMode(mid, name, RO, ROFLG, INTFAIL, EN, ET, GIC, GIIC, XMU, T, S, UND, UTD, GAMMA)
            self.AddMaterial(mat)
        elif dynaMaterial[0] == "*MAT_ELASTIC_PERI_TITLE":
            name = dynaMaterial[1]
            firstLine = dynaMaterial[2]
            
            if type(firstLine) == list:
                name = dynaMaterial[1][0]
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10])
            mid = KooDynaInt(firstLine[0])
            RO = KooDynaFloat(firstLine[1])
            E = KooDynaFloat(firstLine[2])
            GT = KooDynaFloat(firstLine[3])
            GS = KooDynaFloat(firstLine[4], 1.0E20)
            if forcedid != 0:
                mid = forcedid
            mat = KooMaterialElasticPeri(mid,name, RO, E, GT, GS)
            self.AddMaterial(mat)
        elif dynaMaterial[0] == "*MAT_ELASTIC_PERI":
            firstLine = dynaMaterial[1]
            if type(firstLine) == list:
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10])
            mid = KooDynaInt(firstLine[0])
            name = "ElasticPeri{0}".format(mid)
            RO = KooDynaFloat(firstLine[1])
            E = KooDynaFloat(firstLine[2])
            GT = KooDynaFloat(firstLine[3])
            GS = KooDynaFloat(firstLine[4])
            if forcedid != 0:
                mid = forcedid
            mat = KooMaterialElasticPeri(mid,name,RO, E, GT, GS)
            self.AddMaterial(mat)                         
                       
        elif dynaMaterial[0] == "*MAT_LOW_DENSITY_FOAM_TITLE":
            name = dynaMaterial[1]
            firstLine = dynaMaterial[2]
            secondLine = dynaMaterial[3]
            if type(firstLine) == list:
                name = dynaMaterial[1][0]
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10,10,10])
                secondLine = self.parse_whole(secondLine, [10,10,10,10,10,10,10])
            id = KooDynaInt(firstLine[0])
            rho = KooDynaFloat(firstLine[1])
            E = KooDynaFloat(firstLine[2])
            LCID = KooDynaInt(firstLine[3])
            TC = KooDynaFloat(firstLine[4])
            HU = KooDynaFloat(firstLine[5])
            BETA = KooDynaFloat(firstLine[6])
            DAMP = KooDynaFloat(firstLine[7])
            SHAPE = KooDynaFloat(secondLine[0]) 
            FAIL = KooDynaFloat(secondLine[1]) 
            BVFLAG = KooDynaFloat(secondLine[2])    
            ED = KooDynaFloat(secondLine[3])    
            BETA1 = KooDynaFloat(secondLine[4])
            KCON = KooDynaFloat(secondLine[5])
            REF = KooDynaFloat(secondLine[6])

            if forcedid != 0:
                id = forcedid
           
            mat = KooMaterialLowDensityFoam(id, name, rho, E, LCID, TC, HU, BETA, DAMP, SHAPE, FAIL, BVFLAG, ED, BETA1, KCON, REF)
            #print(str(id) + "mat is added")
            self.AddMaterial(mat)  
            #print(str(mat.id) + "mat is added")
        elif dynaMaterial[0] == "*MAT_LOW_DENSITY_FOAM":
            firstLine = dynaMaterial[1]
            secondLine = dynaMaterial[2]
            firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10,10,10])
            secondLine = self.parse_whole(secondLine, [10,10,10,10,10,10,10])
            id = KooDynaInt(firstLine[0])
            name = "LowDensityFoam{0}".format(id)
            rho = KooDynaFloat(firstLine[1])
            E = KooDynaFloat(firstLine[2])
            LCID = KooDynaInt(firstLine[3])
            TC = KooDynaFloat(firstLine[4])
            HU = KooDynaFloat(firstLine[5])
            BETA = KooDynaFloat(firstLine[6])
            DAMP = KooDynaFloat(firstLine[7])
            SHAPE = KooDynaFloat(secondLine[0]) 
            FAIL = KooDynaFloat(secondLine[1]) 
            BVFLAG = KooDynaFloat(secondLine[2])    
            ED = KooDynaFloat(secondLine[3])    
            BETA1 = KooDynaFloat(secondLine[4])
            KCON = KooDynaFloat(secondLine[5])
            REF = KooDynaFloat(secondLine[6])

            if forcedid != 0:
                id = forcedid
            
            mat = KooMaterialLowDensityFoam(id, name, rho, E, LCID, TC, HU, BETA, DAMP, SHAPE, FAIL, BVFLAG, ED, BETA1, KCON, REF)
            self.AddMaterial(mat)  

        elif dynaMaterial[0] == "*MAT_PIECEWISE_LINEAR_PLASTICITY" or dynaMaterial[0] == "*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE":
            if dynaMaterial[0] == "*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE":                
                name = dynaMaterial[1]
                firstLine = dynaMaterial[2]
                secondLine = dynaMaterial[3]
                imin = 4
            else:
                firstLine = dynaMaterial[1]
                secondLine = dynaMaterial[2]
                imin = 3
            if type(firstLine) == list:
                name = dynaMaterial[1][0]
                pass
            else:
                firstLine = self.parse_whole(firstLine, [10,10,10,10,10,10,10,10])
                secondLine = self.parse_whole(secondLine, [10,10,10,10,10])            
            
            id = KooDynaInt(firstLine[0])
            rho = KooDynaFloat(firstLine[1])
            E = KooDynaFloat(firstLine[2])
            nu = KooDynaFloat(firstLine[3])
            sigy = KooDynaFloat(firstLine[4])
            etan = KooDynaFloat(firstLine[5])
            fail = KooDynaFloat(firstLine[6])
            tdel = KooDynaFloat(firstLine[7])
            c = KooDynaFloat(secondLine[0])
            p = KooDynaFloat(secondLine[1])
            lcss = KooDynaInt(secondLine[2])
            lcsr = KooDynaInt(secondLine[3])
            vp = KooDynaFloat(secondLine[4])
            if imin == 3:
                name = "PiecewiseLinearPlasticity{0}".format(id)
            eps = []
            es = []
            
            for i in range(imin,len(dynaMaterial)):
                curLine = dynaMaterial[i]
                if type(curLine) == list:
                    pass
                else:
                    curLine = self.parse_whole(curLine, [10,10,10,10,10,10,10,10])
                for j in range(len(curLine)):
                    if i % 2 == 0:
                        eps.append(KooDynaFloat(curLine[j]))
                    else:
                        es.append(KooDynaFloat(curLine[j]))
            if forcedid != 0:
                id = forcedid
            mat = KooMaterialPiecewiseLinearPlasticity(id, name, rho, E, nu, sigy, etan, fail, tdel, c, p, lcss, lcsr, vp, eps, es)
            self.AddMaterial(mat)            
        
        else:
            print("Material Type which is not supported.")
            print("We will copy the material as it is.")
            id = 0
            if forcedid == 0:
                print("ID is not provided. We will use imported ID.")
                if "TITLE" in dynaMaterial[0]:
                    id = KooDynaInt(dynaMaterial[2][0])
                else:
                    id = KooDynaInt(dynaMaterial[1][0])

            else:
                id = forcedid
            print("ID : {0}".format(id))
            
            for i in range(0, len(dynaMaterial)):
                print(dynaMaterial[i])
            
            mat = KooMaterial(id, "Material{0}".format(id))
            mat.SetDynaKeyword(dynaMaterial)
            self.AddMaterial(mat)
            
        #print(dynaMaterial[0], "is added.")
        return mat
    
    def WritetoDynaRigidKeyword(self, startID):
        if len(self.rigidMaterials) == 0:
            self.GenerateRigidMaterials()
        keywordString = ""
        for id in self.rigidMaterials:
            mat = self.rigidMaterials[id]
            mat.id = startID + id            
            mat.GenerateDynaKeyword()
            keywordString += mat.dynaKeywordString
        return keywordString
    
    def WritetoDynaKeyword(self, startID):
        keywordString = ""
        for id in self.materials:
            mat = self.materials[id]
            mat.id = startID + id
            if type(mat) == KooMaterial:
                pass
            else:
                mat.GenerateDynaKeyword()
            keywordString += mat.dynaKeywordString
        for id in self.addErosions:
            addErosion = self.addErosions[id]
            addErosion.GenerateDynaKeyword()
            keywordString += addErosion.dynaKeywordString
        for eosid in self.eos:
            eos = self.eos[eosid]
            eos.GenerateDynaKeyword()
            keywordString += eos.dynaKeywordString
        for pzid in self.addPZElectric:
            pzz = self.addPZElectric[pzid]
            pzz.GenerateDynaKeyword()
            keywordString += pzz.dynaKeywordString
        return keywordString
     
    def WriteStreamDynaKeyword(self,stream, startID):
        for id in self.materials:
            mat = self.materials[id]
            mat.id = startID + id
            if type(mat) == KooMaterial:
                pass
            else:
                mat.GenerateDynaKeyword()
            stream.write(mat.dynaKeywordString)
        for id in self.addErosions:
            addErosion = self.addErosions[id]
            addErosion.GenerateDynaKeyword()
            stream.write(addErosion.dynaKeywordString)
        for eosid in self.eos:
            eos = self.eos[eosid]
            eos.GenerateDynaKeyword()
            stream.write(eos.dynaKeywordString)            
    
    def WritetoNastranKeyword(self, startID):
        keywordString = ""
        for id in self.materials:
            mat = self.materials[id]
            mat.id = startID + id
            if type(mat) == KooMaterial:
                pass
            else:
                mat.GenerateNastranKeyword()
            keywordString += mat.nastranKeywordString
        return keywordString
    
    def ImportMaterial(self, filePath):
        with open(filePath, "r") as file:
            line = file.readline() 
            while True:
                if not line:
                    break
                elif "**End" in line:
                    break
                elif "**Material" in line:
                    svector = line.split(",")
                    mid = int(svector[1])
                    line = file.readline() 
                    line = line.replace("\n","")
                    mat = [] 
                    while True:
                        if not line:
                            break
                        elif "**" in line:
                            break
                        elif "$" in line:
                            pass
                        else:
                            
                            mat.append(line)
                        line = file.readline()
                        line = line.replace("\n","")
                    self.AddMaterialfromDyna(mat,mid)
                    continue
                line = file.readline()





        
    

if __name__ == "__main__":
    mat = KooMaterialElastic(1, "Steel", 7800, 210e9, 0.3)
    print(mat.rho)
    print(mat.E)
    print(mat.nu)
    print(mat.name)
    print(mat.id)
    mat.AddtoDynaKeyword(MatElasticTitle())
    print(mat.dynaKeywordString)
    mat.GenerateDynaKeyword()
    print(mat.dynaKeywordString)

    matManager = KooMaterialManager()
    matManager.CreateElasticMaterial("Steel", 7800, 210e9, 0.3)

    curKeyword = matManager.WritetoDynaKeyword(1)
    print(curKeyword)

