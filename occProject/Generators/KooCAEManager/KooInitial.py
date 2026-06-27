from __future__ import annotations
from KooCAEManager.KooOperator import KooDynaFloat, KooDynaInt, KooDynaString

class KooInitialStressSolid:
    def __init__(self, eid = [], nint=[], nhisv=[], large=[], iveflg=[], ialeg=[], nthint=[], nthhsv=[], sigxx=[], sigyy=[], sigzz=[], sigxy=[], sigyz=[], sigzx=[], eps=[], hisv1=[], hisv2=[], hisv3=[], hisv4=[], hisv5=[], hisv6=[], hisv7=[], hisv8=[]):
        self.id = 0
        self.eid = eid
        self.nint = nint
        self.nhisv = nhisv
        self.large = large
        self.iveflg = iveflg
        self.ialeg = ialeg
        self.nthint = nthint
        self.nthhsv = nthhsv
        self.sigxx = sigxx
        self.sigyy = sigyy
        self.sigzz = sigzz
        self.sigxy = sigxy
        self.sigyz = sigyz
        self.sigzx = sigzx
        self.eps = eps
        self.hisv1 = hisv1
        self.hisv2 = hisv2
        self.hisv3 = hisv3
        self.hisv4 = hisv4
        self.hisv5 = hisv5
        self.hisv6 = hisv6
        self.hisv7 = hisv7
        self.hisv8 = hisv8

    def SetID(self, id):
        self.id = id
        
    def WritetoDynaKeyword(self, starteid=0):
        keyword = "*INITIAL_STRESS_SOLID\n"
        for i in range(len(self.eid)):
            if i == 0:    
                keyword += "$$     EID      NINT     NHISV    LARGE    IVEFLG     IALEG    NTHINT    NTHHSV\n"
            
            keyword += format(self.eid[i] + starteid, '>10')
            keyword += format(self.nint[i], '>10')
            keyword += format(self.nhisv[i], '>10')
            keyword += format(self.large[i], '>10')
            keyword += format(self.iveflg[i], '>10')
            keyword += format(self.ialeg[i], '>10')
            keyword += format(self.nthint[i], '>10')
            keyword += format(self.nthhsv[i], '>10')
            keyword += "\n"
            keyword += "$$   SIGXX     SIGYY     SIGZZ     SIGXY     SIGYZ     SIGZX       EPS\n"
            if self.nint[i] > 0:
                if self.large[i] == 0:
                    for j in range(self.nint[i]):
                        keyword += format(self.sigxx[i][j], '>10.3e')
                        keyword += format(self.sigyy[i][j], '>10.3e')
                        keyword += format(self.sigzz[i][j], '>10.3e')
                        keyword += format(self.sigxy[i][j], '>10.3e')
                        keyword += format(self.sigyz[i][j], '>10.3e')
                        keyword += format(self.sigzx[i][j], '>10.3e')
                        keyword += format(self.eps[i][j], '>10.3e')
                        keyword += "\n"
                elif self.large[i] == 1 and self.nhisv[i] <=3:
                    numline = 2
                    for j in range(self.nint[i]):
                        keyword += format(self.sigxx[i][j], '>16.3e')
                        keyword += format(self.sigyy[i][j], '>16.3e')
                        keyword += format(self.sigzz[i][j], '>16.3e')
                        keyword += format(self.sigxy[i][j], '>16.3e')
                        keyword += format(self.sigyz[i][j], '>16.3e')
                        keyword += "\n"
                        keyword += format(self.sigzx[i][j], '>16.3e')
                        keyword += format(self.eps[i][j], '>16.3e')
                        keyword += format(self.hisv1[i][j], '>16.3e')
                        keyword += format(self.hisv2[i][j], '>16.3e')
                        keyword += format(self.hisv3[i][j], '>16.3e')
                        keyword += "\n"
                elif self.large[i] == 1 and self.nhisv[i] > 3:
                    numline = 3
                    for j in range(self.nint[i]):
                        keyword += format(self.sigxx[i][j], '>16.3e')
                        keyword += format(self.sigyy[i][j], '>16.3e')
                        keyword += format(self.sigzz[i][j], '>16.3e')
                        keyword += format(self.sigxy[i][j], '>16.3e')
                        keyword += format(self.sigyz[i][j], '>16.3e')
                        keyword += "\n"
                        keyword += format(self.sigzx[i][j], '>16.3e')
                        keyword += format(self.eps[i][j], '>16.3e')
                        keyword += format(self.hisv1[i][j], '>16.3e')
                        keyword += format(self.hisv2[i][j], '>16.3e')
                        keyword += format(self.hisv3[i][j], '>16.3e')
                        keyword += "\n"
                        keyword += format(self.hisv4[i][j], '>16.3e')
                        keyword += format(self.hisv5[i][j], '>16.3e')
                        keyword += format(self.hisv6[i][j], '>16.3e')
                        keyword += format(self.hisv7[i][j], '>16.3e')
                        keyword += format(self.hisv8[i][j], '>16.3e')
                        keyword += "\n"


        return keyword
    
    def WriteStreamDynaKeyword(self, stream, starteid=0):
        stream.write("*INITIAL_STRESS_SOLID\n")
        for i in range(len(self.eid)):
            if i == 0:    
                stream.write("$$     EID      NINT     NHISV    LARGE    IVEFLG     IALEG    NTHINT    NTHHSV\n")
            
            stream.write(format(self.eid[i] + starteid, '>10'))
            stream.write(format(self.nint[i], '>10'))
            stream.write(format(self.nhisv[i], '>10'))
            stream.write(format(self.large[i], '>10'))
            stream.write(format(self.iveflg[i], '>10'))
            stream.write(format(self.ialeg[i], '>10'))
            stream.write(format(self.nthint[i], '>10'))
            stream.write(format(self.nthhsv[i], '>10'))
            stream.write("\n")            
            if self.nint[i] > 0:                
                if self.large[i] == 0:
                    if i == 0:
                        stream.write("$$   SIGXX     SIGYY     SIGZZ     SIGXY     SIGYZ     SIGZX       EPS\n")
                    for j in range(self.nint[i]):
                        stream.write(format(self.sigxx[i][j], '>10.3e'))
                        stream.write(format(self.sigyy[i][j], '>10.3e'))
                        stream.write(format(self.sigzz[i][j], '>10.3e'))
                        stream.write(format(self.sigxy[i][j], '>10.3e'))
                        stream.write(format(self.sigyz[i][j], '>10.3e'))
                        stream.write(format(self.sigzx[i][j], '>10.3e'))
                        stream.write(format(self.eps[i][j], '>10.3e'))
                        stream.write("\n")
                elif self.large[i] == 1 and self.nhisv[i] <=3:
                    if i == 0:
                        stream.write("$$         SIGXX           SIGYY           SIGZZ           SIGXY           SIGYZ\n")
                        stream.write("$$         SIGZX             EPS           HISV1           HISV2           HISV3\n")
                    for j in range(self.nint[i]):
                        stream.write(format(self.sigxx[i][j], '>16.9e'))
                        stream.write(format(self.sigyy[i][j], '>16.9e'))
                        stream.write(format(self.sigzz[i][j], '>16.9e'))
                        stream.write(format(self.sigxy[i][j], '>16.9e'))
                        stream.write(format(self.sigyz[i][j], '>16.9e'))
                        stream.write("\n")
                        stream.write(format(self.sigzx[i][j], '>16.9e'))
                        stream.write(format(self.eps[i][j], '>16.9e'))
                        stream.write(format(self.hisv1[i][j], '>16.9e'))
                        stream.write(format(self.hisv2[i][j], '>16.9e'))
                        stream.write(format(self.hisv3[i][j], '>16.9e'))
                        stream.write("\n")
                elif self.large[i] == 1 and self.nhisv[i] > 3:
                    if i == 0:
                        stream.write("$$         SIGXX           SIGYY           SIGZZ           SIGXY           SIGYZ\n")
                        stream.write("$$         SIGZX             EPS           HISV1           HISV2           HISV3\n")
                        stream.write("$$         HISV4           HISV5           HISV6           HISV7           HISV8\n")
                    for j in range(self.nint[i]):
                        stream.write(format(self.sigxx[i][j], '>16.9e'))
                        stream.write(format(self.sigyy[i][j], '>16.9e'))
                        stream.write(format(self.sigzz[i][j], '>16.9e'))
                        stream.write(format(self.sigxy[i][j], '>16.9e'))
                        stream.write(format(self.sigyz[i][j], '>16.9e'))
                        stream.write("\n")
                        stream.write(format(self.sigzx[i][j], '>16.9e'))
                        stream.write(format(self.eps[i][j], '>16.9e'))
                        stream.write(format(self.hisv1[i][j], '>16.9e'))
                        stream.write(format(self.hisv2[i][j], '>16.9e'))
                        stream.write(format(self.hisv3[i][j], '>16.9e'))
                        stream.write("\n")
                        stream.write(format(self.hisv4[i][j], '>16.9e'))
                        stream.write(format(self.hisv5[i][j], '>16.9e'))
                        stream.write(format(self.hisv6[i][j], '>16.9e'))
                        stream.write(format(self.hisv7[i][j], '>16.9e'))
                        stream.write(format(self.hisv8[i][j], '>16.9e'))
                        stream.write("\n")

class KooInitialStressSolidSet:
    def __init__(self, sid = [], nint=[], nhisv=[], large=[], iveflg=[], ialeg=[], nthint=[], nthhsv=[], sigxx=[], sigyy=[], sigzz=[], sigxy=[], sigyz=[], sigzx=[], eps=[]):
        self.id = 0
        self.sid = sid
        self.nint = nint
        self.nhisv = nhisv
        self.large = large
        self.iveflg = iveflg
        self.ialeg = ialeg
        self.nthint = nthint
        self.nthhsv = nthhsv
        self.sigxx = sigxx
        self.sigyy = sigyy
        self.sigzz = sigzz
        self.sigxy = sigxy
        self.sigyz = sigyz
        self.sigzx = sigzx
        self.eps = eps
    
    def SetID(self, id):
        self.id = id
        
    def WritetoDynaKeyword(self):
        keyword = "*INITIAL_STRESS_SOLID_SET\n"
        for i in range(len(self.sid)):
            if i == 0:    
                keyword += "$$   SetID      NINT     NHISV    LARGE    IVEFLG     IALEG    NTHINT    NTHHSV\n"
            
            keyword += format(self.sid[i] + starteid, '>10')
            keyword += format(self.nint[i], '>10')
            keyword += format(self.nhisv[i], '>10')
            keyword += format(self.large[i], '>10')
            keyword += format(self.iveflg[i], '>10')
            keyword += format(self.ialeg[i], '>10')
            keyword += format(self.nthint[i], '>10')
            keyword += format(self.nthhsv[i], '>10')
            keyword += "\n"
            keyword += "$$   SIGXX     SIGYY     SIGZZ     SIGXY     SIGYZ     SIGZX       EPS\n"
            if self.nint[i] > 0:
                for j in range(self.nint[i]):
                    keyword += format(self.sigxx[i][j], '>10.3e')
                    keyword += format(self.sigyy[i][j], '>10.3e')
                    keyword += format(self.sigzz[i][j], '>10.3e')
                    keyword += format(self.sigxy[i][j], '>10.3e')
                    keyword += format(self.sigyz[i][j], '>10.3e')
                    keyword += format(self.sigzx[i][j], '>10.3e')
                    keyword += format(self.eps[i][j], '>10.3e')
                    keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, starteid=0):
        stream.write("*INITIAL_STRESS_SOLID_SET\n")
        for i in range(len(self.sid)):
            if i == 0:    
                stream.write("$$   SetID      NINT     NHISV    LARGE    IVEFLG     IALEG    NTHINT    NTHHSV\n")
            
            stream.write(format(self.sid[i], '>10'))
            stream.write(format(self.nint[i], '>10'))
            stream.write(format(self.nhisv[i], '>10'))
            stream.write(format(self.large[i], '>10'))
            stream.write(format(self.iveflg[i], '>10'))
            stream.write(format(self.ialeg[i], '>10'))
            stream.write(format(self.nthint[i], '>10'))
            stream.write(format(self.nthhsv[i], '>10'))
            stream.write("\n")
            stream.write("$$   SIGXX     SIGYY     SIGZZ     SIGXY     SIGYZ     SIGZX       EPS\n")
            if self.nint[i] > 0:
                for j in range(self.nint[i]):
                    stream.write(format(self.sigxx[i][j], '>10.3e'))
                    stream.write(format(self.sigyy[i][j], '>10.3e'))
                    stream.write(format(self.sigzz[i][j], '>10.3e'))
                    stream.write(format(self.sigxy[i][j], '>10.3e'))
                    stream.write(format(self.sigyz[i][j], '>10.3e'))
                    stream.write(format(self.sigzx[i][j], '>10.3e'))
                    stream.write(format(self.eps[i][j], '>10.3e'))
                    stream.write("\n")  

class KooInitialVelocity:
    def __init__(self, nsid, nsidex, boxid=0, irigid=0, icid=0, Vx=0.0, Vy=0.0, Vz=0.0, Vxr=0.0, Vyr=0.0, Vzr=0.0, Vxe=0.0, Vye=0.0, Vze=0.0, Vxre=0.0, Vyre=0.0, Vzre=0.0):
        self.id = 0 
        self.nsid = nsid
        self.nsidex = nsidex
        self.boxid = boxid
        self.irigid = irigid
        self.icid = icid
        self.Vx = Vx
        self.Vy = Vy
        self.Vz = Vz
        self.Vxr = Vxr
        self.Vyr = Vyr
        self.Vzr = Vzr
        self.Vxe = Vxe
        self.Vye = Vye
        self.Vze = Vze
        self.Vxre = Vxre
        self.Vyre = Vyre
        self.Vzre = Vzre
    
    def SetID(self, id):
        self.id = id 
    
    def WritetoDynaKeyword(self, startnid):
        keyword = "*INITIAL_VELOCITY\n"
        keyword += format(self.nsid, '>10')
        keyword += format(self.nsidex, '>10')
        keyword += format(self.boxid, '>10')
        keyword += format(self.irigid, '>10')
        keyword += format(self.icid, '>10')
        keyword += "\n"
        keyword += format(self.Vx, '>10.3e')
        keyword += format(self.Vy, '>10.3e')
        keyword += format(self.Vz, '>10.3e')        
        keyword += format(self.Vxr, '>10.3e')
        keyword += format(self.Vyr, '>10.3e')        
        keyword += format(self.Vzr, '>10.3e')
        keyword += "\n"
        if self.nsidex > 0 :
            keyword += format(self.Vxe, '>10.3e')
            keyword += format(self.Vye, '>10.3e')
            keyword += format(self.Vze, '>10.3e')
            keyword += format(self.Vxre, '>10.3e')
            keyword += format(self.Vyre, '>10.3e')
            keyword += format(self.Vzre, '>10.3e')
            keyword += "\n"
        return keyword        
    
    def WriteStreamDynaKeyword(self, stream, startnid):
        stream.write("*INITIAL_VELOCITY\n")
        stream.write(format(self.nsid, '>10'))
        stream.write(format(self.nsidex, '>10'))
        stream.write(format(self.boxid, '>10'))
        stream.write(format(self.irigid, '>10'))
        stream.write(format(self.icid, '>10'))
        stream.write("\n")
        stream.write(format(self.Vx, '>10.3e'))
        stream.write(format(self.Vy, '>10.3e'))
        stream.write(format(self.Vz, '>10.3e') )       
        stream.write(format(self.Vxr, '>10.3e'))
        stream.write(format(self.Vyr, '>10.3e'))        
        stream.write(format(self.Vzr, '>10.3e'))
        stream.write("\n")
        if self.nsidex > 0 :
            stream.write(format(self.Vxe, '>10.3e'))
            stream.write(format(self.Vye, '>10.3e'))
            stream.write(format(self.Vze, '>10.3e'))
            stream.write(format(self.Vxre, '>10.3e'))
            stream.write(format(self.Vyre, '>10.3e'))
            stream.write(format(self.Vzre, '>10.3e'))
            stream.write("\n")
        

class KooInitialVelocityNode:
    def __init__(self, nodes = [], Vxs = [], Vys = [], Vzs = [], Vxrs = [], Vyrs = [], Vzrs = [], icids = []):
        self.id = 0
        self.nodes = nodes
        self.Vxs = Vxs
        self.Vys = Vys
        self.Vzs = Vzs
        self.Vxrs = Vxrs
        self.Vyrs = Vyrs
        self.Vzrs = Vzrs
        self.icids = icids            
        pass 
    
    def SetID(self, id):
        self.id = id
    
    def AddNode(self, node, Vx, Vy, Vz, Vxr, Vyr, Vzr, icid):
        self.nodes.append(node)
        self.Vxs.append(Vx)
        self.Vys.append(Vy)
        self.Vzs.append(Vz)
        self.Vxrs.append(Vxr)
        self.Vyrs.append(Vyr)
        self.Vzrs.append(Vzr)
        self.icids.append(icid)
        pass
    
    def WritetoDynaKeyword(self, startnid):
        keyword = "*INITIAL_VELOCITY_NODE\n"
        for i in range(len(self.nodes)):
            keyword += format(startnid + self.nodes[i], '>10')
            keyword += format(self.Vxs[i], '>10.3e')
            keyword += format(self.Vys[i], '>10.3e')
            keyword += format(self.Vzs[i], '>10.3e')
            keyword += format(self.Vxrs[i], '>10.3e')
            keyword += format(self.Vyrs[i], '>10.3e')
            keyword += format(self.Vzrs[i], '>10.3e')
            keyword += format(self.icids[i], '>10')
            keyword += "\n"
        return keyword
        
    def WriteStreamDynaKeyword(self, stream, startnid):
        stream.write("*INITIAL_VELOCITY_NODE\n")
        for i in range(len(self.nodes)):
            stream.write(format(startnid + self.nodes[i], '>10'))
            stream.write(format(self.Vxs[i], '>10.3e'))
            stream.write(format(self.Vys[i], '>10.3e'))
            stream.write(format(self.Vzs[i], '>10.3e'))
            stream.write(format(self.Vxrs[i], '>10.3e'))
            stream.write(format(self.Vyrs[i], '>10.3e'))
            stream.write(format(self.Vzrs[i], '>10.3e'))
            stream.write(format(self.icids[i], '>10'))
            stream.write("\n")
            
class KooInitialVelocityGeneration:
    def __init__(self, ID, STYP, OMEGA=0.0, VX=0.0, VY=0.0, VZ=0.0, IVATN=0, ICID=0, XC=0.0, YC=0.0, ZC=0.0, NX=0.0, NY=0.0, NZ=0.0, PHASE=0, IRIGID=0):
        self.ID = ID
        self.STYP = STYP
        self.OMEGA = OMEGA
        self.VX = VX
        self.VY = VY
        self.VZ = VZ
        self.IVATN = IVATN
        self.ICID = ICID
        self.XC = XC
        self.YC = YC
        self.ZC = ZC
        self.NX = NX
        self.NY = NY
        self.NZ = NZ
        self.PHASE = PHASE
        self.IRIGID = IRIGID
    
    def SetID(self, id):
        self.id = id
    
    def WritetoDynaKeyword(self, startnid=0):
        keyword = "*INITIAL_VELOCITY_GENERATION\n"
        keyword += format(self.ID + startnid, '>10')
        keyword += format(self.STYP, '>10')
        keyword += format(self.OMEGA, '>10.3e')
        keyword += format(self.VX, '>10.3e')
        keyword += format(self.VY, '>10.3e')
        keyword += format(self.VZ, '>10.3e')
        keyword += format(self.IVATN, '>10')
        keyword += format(self.ICID, '>10')
        keyword += "\n"
        keyword += format(self.XC, '>10.4f')
        keyword += format(self.YC, '>10.4f')
        keyword += format(self.ZC, '>10.4f')
        if abs(self.NX +999.0) < 1.0e-6:
            keyword += format(self.NX, '>10.3f')
            keyword += format(int(self.NY), '>10')
            keyword += format(int(self.NZ), '>10')
        else:
            keyword += format(self.NX, '>10.3f')
            keyword += format(float(self.NY), '>10.3f')
            keyword += format(float(self.NZ), '>10.3f')
        keyword += format(self.PHASE, '>10')
        keyword += format(self.IRIGID, '>10')
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startnid=0):
        stream.write("*INITIAL_VELOCITY_GENERATION\n")
        stream.write(format(self.ID + startnid, '>10'))
        stream.write(format(self.STYP, '>10'))
        stream.write(format(self.OMEGA, '>10.3e'))
        stream.write(format(self.VX, '>10.3e'))
        stream.write(format(self.VY, '>10.3e'))
        stream.write(format(self.VZ, '>10.3e'))
        stream.write(format(self.IVATN, '>10'))
        stream.write(format(self.ICID, '>10'))
        stream.write("\n")        
        stream.write(format(self.XC, '>10.4f'))
        stream.write(format(self.YC, '>10.4f'))
        stream.write(format(self.ZC, '>10.4f'))
        if abs(self.NX +999.0) < 1.0e-6:
            stream.write(format(self.NX, '>10.3f'))
            stream.write(format(int(self.NY), '>10'))
            stream.write(format(int(self.NZ), '>10'))
        else:
            stream.write(format(self.NX, '>10.3f'))
            stream.write(format(float(self.NY), '>10.3f'))
            stream.write(format(float(self.NZ), '>10.3f'))
        stream.write(format(self.PHASE, '>10'))
        stream.write(format(self.IRIGID, '>10'))
        stream.write("\n")
    
class KooInitialTemperatureSet:
    """*INITIAL_TEMPERATURE_SET — 노드셋 초기온도 (T2/T3 열해석 초기조건). NSID=0 → 전 노드."""
    def __init__(self, nsid=0, temp=0.0, loc=0):
        self.id = 0
        self.nsid = nsid    # 노드셋 ID (0 = 전 노드)
        self.temp = temp    # 초기 온도 [°C]
        self.loc = loc      # 0 = both surfaces (shell), solid 무관

    def SetID(self, id):
        self.id = id

    def GenerateDynaKeyword(self):
        keyword = "*INITIAL_TEMPERATURE_SET\n"
        keyword += "$$    NSID      TEMP       LOC\n"
        keyword += format(self.nsid, ">10")
        keyword += format(self.temp, ">10.3f")
        keyword += format(self.loc, ">10")
        keyword += "\n"
        return keyword

    def WriteStreamDynaKeyword(self, stream, startnid=0):
        stream.write(self.GenerateDynaKeyword())


class KooInitialManager:
    def __init__(self):
        self.maxid = 0
        self.inits = {}
        
    def OverwritefromInitialManager(self, initialManager: KooInitialManager):
        self.maxid = max(self.maxid, initialManager.maxid)
        for key, value in initialManager.inits.items():
            self.inits[key] = value

    def CreateInitialStressSolid(self, eid = [], nint=[], nhisv=[], large=[], iveflg=[], ialeg=[], nthint=[], nthhsv=[], sigxx=[], sigyy=[], sigzz=[], sigxy=[], sigyz=[], sigzx=[], eps=[], hisv1=[], hisv2=[], hisv3=[], hisv4=[], hisv5=[], hisv6=[], hisv7=[], hisv8=[]):
        self.maxid += 1
        self.inits[self.maxid] = KooInitialStressSolid(eid, nint, nhisv, large, iveflg, ialeg, nthint, nthhsv, sigxx, sigyy, sigzz, sigxy, sigyz, sigzx, eps, hisv1, hisv2, hisv3, hisv4, hisv5, hisv6, hisv7, hisv8)
        self.inits[self.maxid].SetID(self.maxid)
        return self.inits[self.maxid]
    
    def CreateInitialStressSolidSet(self, sid = [], nint=[], nhisv=[], large=[], iveflg=[], ialeg=[], nthint=[], nthhsv=[], sigxx=[], sigyy=[], sigzz=[], sigxy=[], sigyz=[], sigzx=[], eps=[]):
        self.maxid += 1
        self.inits[self.maxid] = KooInitialStressSolidSet(sid, nint, nhisv, large, iveflg, ialeg, nthint, nthhsv, sigxx, sigyy, sigzz, sigxy, sigyz, sigzx, eps)
        self.inits[self.maxid].SetID(self.maxid)
        return self.inits[self.maxid]
        
    def CreateInitialVelocity(self, nsid, nsidex, boxid, irigid, icid, Vx, Vy, Vz, Vxr, Vyr, Vzr, Vxe, Vye, Vze, Vxre, Vyre, Vzre):
        self.maxid += 1
        self.inits[self.maxid] = KooInitialVelocity(nsid, nsidex, boxid, irigid, icid, Vx, Vy, Vz, Vxr, Vyr, Vzr, Vxe, Vye, Vze, Vxre, Vyre, Vzre)
        self.inits[self.maxid].SetID(self.maxid)
        return self.inits[self.maxid]
    
    def CreateInitialVelocityNode(self, nodes = [], Vxs = [], Vys = [], Vzs = [], Vxrs = [], Vyrs = [], Vzrs = [], icids = []):
        self.maxid += 1
        self.inits[self.maxid] = KooInitialVelocityNode(nodes, Vxs, Vys, Vzs, Vxrs, Vyrs, Vzrs, icids)
        self.inits[self.maxid].SetID(self.maxid)
        return self.inits[self.maxid]

    def CreateInitialVelocityGeneration(self, ID, STYP, OMEGA=0.0, VX=0.0, VY=0.0, VZ=0.0, IVATN=0, ICID=0, XC=0.0, YC=0.0, ZC=0.0, NX=0.0, NY=0.0, NZ=0.0, PHASE=0, IRIGID=0):
        self.maxid += 1
        self.inits[self.maxid] = KooInitialVelocityGeneration(ID, STYP, OMEGA, VX, VY, VZ, IVATN, ICID, XC, YC, ZC, NX, NY, NZ, PHASE, IRIGID)
        self.inits[self.maxid].SetID(self.maxid)
        return self.inits[self.maxid]
    
    def CreateInitialTemperatureSet(self, nsid=0, temp=0.0, loc=0):
        self.maxid += 1
        self.inits[self.maxid] = KooInitialTemperatureSet(nsid, temp, loc)
        self.inits[self.maxid].SetID(self.maxid)
        return self.inits[self.maxid]

    def ClearInitial(self):
        self.inits.clear()

    def RemoveInitial(self, id):
        if id in self.inits:
            del self.inits[id]
        
            
    def AddInitialfromDyna(self, initKeyword):
        if initKeyword[0] == "*INITIAL_STRESS_SOLID":
            eid = []
            nint = []
            nhisv = []
            large = []
            iveflg = []
            ialeg = []
            nthint = []
            nthhsv = []
            sigxx = []
            sigyy = []
            sigzz = []
            sigxy = []
            sigyz = []
            sigzx = []
            eps = []
            hisv1 = [] 
            hisv2 = [] 
            hisv3 = [] 
            hisv4 = []
            hisv5 = [] 
            hisv6 = []
            hisv7 = [] 
            hisv8 = [] 

            i = 1  # 헤더는 0번째로 가정
            while i < len(initKeyword):
                svector = initKeyword[i]
                eid.append(KooDynaInt(svector[0]))
                nint_val = KooDynaInt(svector[1])
                nint.append(nint_val)
                nhisv.append(KooDynaInt(svector[2]))
                if nhisv[-1] > 3:
                    numline = 3
                else:
                    numline = 2
                large.append(KooDynaInt(svector[3]))
                iveflg.append(KooDynaInt(svector[4]))
                ialeg.append(KooDynaInt(svector[5]))
                nthint.append(KooDynaInt(svector[6]))
                nthhsv.append(KooDynaInt(svector[7]))

                sigxx.append([])
                sigyy.append([])
                sigzz.append([])
                sigxy.append([])
                sigyz.append([])
                sigzx.append([])
                eps.append([])
                hisv1.append([])
                hisv2.append([])
                hisv3.append([])
                hisv4.append([])
                hisv5.append([])
                hisv6.append([])
                hisv7.append([])
                hisv8.append([])

                if large[-1] == 0:
                    for j in range(nint_val):
                        if i + j + 1 < len(initKeyword):  # 안전성 체크
                            svector2 = initKeyword[i + j + 1]
                            sigxx[-1].append(KooDynaFloat(svector2[0]))
                            sigyy[-1].append(KooDynaFloat(svector2[1]))
                            sigzz[-1].append(KooDynaFloat(svector2[2]))
                            sigxy[-1].append(KooDynaFloat(svector2[3]))
                            sigyz[-1].append(KooDynaFloat(svector2[4]))
                            sigzx[-1].append(KooDynaFloat(svector2[5]))
                            eps[-1].append(KooDynaFloat(svector2[6]))

                    i += nint_val + 1  # 헤더 포함하여 다음 블록으로 이동
                elif large[-1] == 1 and nhisv[-1] <= 3:
                    for j in range(0,numline*nint_val,numline):                        
                        svector2 = initKeyword[i + j + 1]
                        sigxx[-1].append(KooDynaFloat(svector2[0]))
                        sigyy[-1].append(KooDynaFloat(svector2[1]))
                        sigzz[-1].append(KooDynaFloat(svector2[2]))
                        sigxy[-1].append(KooDynaFloat(svector2[3]))
                        sigyz[-1].append(KooDynaFloat(svector2[4]))
                        svector3 = initKeyword[i + j + 2]
                        sigzx[-1].append(KooDynaFloat(svector3[0]))
                        eps[-1].append(KooDynaFloat(svector3[1]))
                        hisv1[-1].append(KooDynaFloat(svector3[2]))
                        hisv2[-1].append(KooDynaFloat(svector3[3]))
                        hisv3[-1].append(KooDynaFloat(svector3[4]))
                    i += numline * nint_val + 1  # 헤더 포함하여 다음 블록으로 이동
                elif large[-1] == 1:
                    for j in range(0,numline*nint_val,numline):
                        vector2 = initKeyword[i + j + 1]
                        sigxx[-1].append(KooDynaFloat(svector2[0]))
                        sigyy[-1].append(KooDynaFloat(svector2[1]))
                        sigzz[-1].append(KooDynaFloat(svector2[2]))
                        sigxy[-1].append(KooDynaFloat(svector2[3]))
                        sigyz[-1].append(KooDynaFloat(svector2[4]))
                        svector3 = initKeyword[i + j + 2]
                        sigzx[-1].append(KooDynaFloat(svector3[0]))
                        eps[-1].append(KooDynaFloat(svector3[1]))
                        hisv1[-1].append(KooDynaFloat(svector3[2]))
                        hisv2[-1].append(KooDynaFloat(svector3[3]))
                        hisv3[-1].append(KooDynaFloat(svector3[4]))
                        svector4 = initKeyword[i + j + 3]
                        hisv4[-1].append(KooDynaFloat(svector4[0]))
                        hisv5[-1].append(KooDynaFloat(svector4[1]))
                        hisv6[-1].append(KooDynaFloat(svector4[2]))
                        hisv7[-1].append(KooDynaFloat(svector4[3]))
                        hisv8[-1].append(KooDynaFloat(svector4[4]))
                    i += numline * nint_val + 1  # 헤더 포함하여 다음 블록으로 이동

            self.CreateInitialStressSolid(eid, nint, nhisv, large, iveflg, ialeg, nthint, nthhsv, sigxx, sigyy, sigzz, sigxy, sigyz, sigzx, eps, hisv1, hisv2, hisv3, hisv4, hisv5, hisv6, hisv7, hisv8)

        elif initKeyword[0] == "*INITIAL_STRESS_SOLID_SET":
            sid = []
            nint = []
            nhisv = []
            large = []
            iveflg = []
            ialeg = []
            nthint = []
            nthhsv = []
            sigxx = []
            sigyy = []
            sigzz = []
            sigxy = []
            sigyz = []
            sigzx = []
            eps = []

            i = 1  # 첫 줄은 헤더라고 가정
            while i < len(initKeyword):
                svector = initKeyword[i]
                
                sid_val = KooDynaInt(svector[0])
                nint_val = KooDynaInt(svector[1])  # 수동 증가를 위해 값으로 저장

                sid.append(sid_val)
                nint.append(nint_val)
                nhisv.append(KooDynaInt(svector[2]))
                large.append(KooDynaInt(svector[3]))
                iveflg.append(KooDynaInt(svector[4]))
                ialeg.append(KooDynaInt(svector[5]))
                nthint.append(KooDynaInt(svector[6]))
                nthhsv.append(KooDynaInt(svector[7]))

                sigxx.append([])
                sigyy.append([])
                sigzz.append([])
                sigxy.append([])
                sigyz.append([])
                sigzx.append([])
                eps.append([])

                for j in range(nint_val):
                    if i + j + 1 < len(initKeyword):  # 인덱스 초과 방지
                        svector2 = initKeyword[i + j + 1]
                        sigxx[-1].append(KooDynaFloat(svector2[0]))
                        sigyy[-1].append(KooDynaFloat(svector2[1]))
                        sigzz[-1].append(KooDynaFloat(svector2[2]))
                        sigxy[-1].append(KooDynaFloat(svector2[3]))
                        sigyz[-1].append(KooDynaFloat(svector2[4]))
                        sigzx[-1].append(KooDynaFloat(svector2[5]))
                        eps[-1].append(KooDynaFloat(svector2[6]))

                i += nint_val + 1  # 블록 단위로 점프

            self.CreateInitialStressSolidSet(sid, nint, nhisv, large, iveflg, ialeg, nthint, nthhsv, sigxx, sigyy, sigzz, sigxy, sigyz, sigzx, eps)
              
        elif initKeyword[0] == "*INITIAL_VELOCITY":
            svector = initKeyword[1]
            nsid = KooDynaInt(svector[0])
            nsidex = KooDynaInt(svector[1])
            boxid = KooDynaInt(svector[2])
            irigid = KooDynaInt(svector[3])
            icid = KooDynaInt(svector[4])
            svector = initKeyword[2]
            Vx = KooDynaFloat(svector[0])
            Vy = KooDynaFloat(svector[1])
            Vz = KooDynaFloat(svector[2])
            Vxr = KooDynaFloat(svector[3])
            Vyr = KooDynaFloat(svector[4])
            Vzr = KooDynaFloat(svector[5])
            if nsidex > 0:
                svector = initKeyword[3]
                Vxe= KooDynaFloat(svector[0])   
                Vye= KooDynaFloat(svector[1])
                Vze= KooDynaFloat(svector[2])
                Vxre= KooDynaFloat(svector[3])
                Vyre= KooDynaFloat(svector[4])
                Vzre= KooDynaFloat(svector[5])  
            else:
                Vxe= 0.0
                Vye= 0.0
                Vze= 0.0
                Vxre= 0.0
                Vyre= 0.0
                Vzre= 0.0
            
            self.CreateInitialVelocity(nsid, nsidex, boxid, irigid, icid, Vx, Vy, Vz, Vxr, Vyr, Vzr, Vxe, Vye, Vze, Vxre, Vyre, Vzre)
            
            
        elif initKeyword[0] == "*INITIAL_VELOCITY_NODE":
            nodes = []
            Vxs = []
            Vys = []
            Vzs = []
            Vxrs = []
            Vyrs = []
            Vzrs = []
            icids = []
            for i in range(1, len(initKeyword)):
                svector = initKeyword[i]
                curNodeid = KooDynaInt(svector[0], None)
                vx = KooDynaFloat(svector[1])
                vy = KooDynaFloat(svector[2])
                vz = KooDynaFloat(svector[3])
                vxr = KooDynaFloat(svector[4])
                vyr = KooDynaFloat(svector[5])
                vzr = KooDynaFloat(svector[6])
                icid = KooDynaInt(svector[7])
                if curNodeid is not None:
                    nodes.append(curNodeid)
                    Vxs.append(vx)
                    Vys.append(vy)
                    Vzs.append(vz)
                    Vxrs.append(vxr)
                    Vyrs.append(vyr)
                    Vzrs.append(vzr)
                    icids.append(icid)                                       
                
            self.CreateInitialVelocityNode(nodes, Vxs, Vys, Vzs, Vxrs, Vyrs, Vzrs, icids)            
        elif initKeyword[0] == "*INITIAL_VELOCITY_GENERATION":
            firstLine = initKeyword[1]
            secondLine = initKeyword[2]
            id = KooDynaInt(firstLine[0])
            styp = KooDynaInt(firstLine[1])
            omega = KooDynaFloat(firstLine[2])
            vx = KooDynaFloat(firstLine[3])
            vy = KooDynaFloat(firstLine[4])
            vz = KooDynaFloat(firstLine[5])
            ivatn = KooDynaInt(firstLine[6])
            icid = KooDynaInt(firstLine[7])
            
            xc = KooDynaFloat(secondLine[0])
            yc = KooDynaFloat(secondLine[1])
            zc = KooDynaFloat(secondLine[2])
            nx = KooDynaFloat(secondLine[3])
            ny = KooDynaFloat(secondLine[4])
            nz = KooDynaFloat(secondLine[5])
            phase = KooDynaInt(secondLine[6])
            irigid = KooDynaInt(secondLine[7])
            
            self.CreateInitialVelocityGeneration(id, styp, omega, vx, vy, vz, ivatn, icid, xc, yc, zc, nx, ny, nz, phase, irigid)
                
    def WritetoDynaKeyword(self, startnid=0):
        keyword = ""
        for i in self.inits:
            keyword += self.inits[i].WritetoDynaKeyword(startnid)
        return keyword
            
    def WriteStreamDynaKeyword(self, stream, startnid=0):
        for i in self.inits:
            self.inits[i].WriteStreamDynaKeyword(stream, startnid)
