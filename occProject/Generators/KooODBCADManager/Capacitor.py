import sys
from math import cos, pi 
import os 
import os.path 

getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")
import sys
if sys.platform.startswith("win"):
    # Windows 전용
    os.add_dll_directory(path)
else:
    # Linux/Unix 계열은 LD_LIBRARY_PATH에 넣으면 됨
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if path not in ld_path.split(":"):
        os.environ["LD_LIBRARY_PATH"] = path + ":" + ld_path
        
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Display.SimpleGui import init_display
from OCC.Core.TColgp import TColgp_Array1OfPnt2d
from OCC.Core.gp import gp_Pnt, gp_Pnt2d, gp_Ax2, gp_Dir, gp_Circ, gp_Ax3, gp_Pln, gp_Trsf, gp_Vec, gp_Ax1
from OCC.Extend.TopologyUtils import TopologyExplorer
import OCC.Core.BRepBuilderAPI as BRepBuilderAPI
from OCC.Core.BRep import BRep_Builder
from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Trsf
import subprocess
from KooAnalysisWeb.Apps import ConvertCAD as convertCAD
import math

from OCC.Core.BRepAlgoAPI import (
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Section,
)

from OCC.Core.Quantity import (
    Quantity_Color,
    Quantity_TOC_RGB,
    Quantity_NOC_BLACK,
    Quantity_NOC_GRAY,
    Quantity_NOC_WHITE,
    Quantity_NOC_RED,
    Quantity_NOC_GREEN,
    Quantity_NOC_BLUE1,
    Quantity_NOC_YELLOW,
    Quantity_NOC_BROWN,
    Quantity_NOC_PINK,
    Quantity_NOC_ORANGE,
    Quantity_NOC_PURPLE,
)

if __name__ =="__main__":
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        # 오프스크린 모드: GUI 함수들을 더미로 정의
        def display_dummy(*args, **kwargs):
            print("[offscreen] display called with", args, kwargs)

        def start_display_dummy():
            print("[offscreen] start_display skipped")

        def add_menu_dummy(name):
            print(f"[offscreen] add_menu('{name}') skipped")

        def add_function_to_menu_dummy(*args, **kwargs):
            print("[offscreen] add_function_to_menu skipped")

        display = display_dummy
        start_display = start_display_dummy
        add_menu = add_menu_dummy
        add_function_to_menu = add_function_to_menu_dummy

    else:
        # 정상 GUI 모드
        from OCC.Display.SimpleGui import init_display
        display, start_display, add_menu, add_function_to_menu = init_display()
#else:
#    display, start_display, add_menu, add_function_to_menu = init_display()
unit = 0.001


if __name__ == "__main__":
    # include the path of occProject\Generators\KooCAEManager
    path = os.path.join(os.getcwd(), "occProject\Generators")
    sys.path.append(path)

from KooCAEManager.KooNode import NodeManager, NodeSetManager, NodeSet, Node
from KooCAEManager.KooBoundaryNode import *
from KooCAEManager.KooDefine import *
from KooCAEManager.KooLoad import *
from KooCAEManager.KooContact import *
from KooCAEManager.KooSegment import *
from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH, KooMeshManagerList
from KooCAEManager.KooPart import KooPartManager, KooPart, KooPartComposite
from KooCAEManager.KooMaterial import *
from KooCAEManager.KooSection import *

from KooCAEManager.KooMeshImporter import KooDynaImporter

class Capacitor():
    @staticmethod
    def _find_linux_evolver(basePath=None):
        """리눅스에서 evolver 경로를 찾는다. /opt/Evolver → Library fallback → which evolver"""
        candidates = ["/opt/Evolver/evolver"]
        if basePath is not None:
            for i in range(5):
                prefix = os.path.join(basePath, *(['..'] * i)) if i > 0 else basePath
                candidates.append(os.path.join(prefix, "Library", "Evolver", "evolver"))
        else:
            candidates.append(os.path.join(".", "Library", "Evolver", "evolver"))
        for c in candidates:
            if os.path.exists(c):
                return c
        import shutil
        found = shutil.which("evolver")
        if found:
            return found
        print("evolver not found")
        sys.exit()

    def __init__(self, id = 0, name = "Capacitor", matMan : KooMaterialManager = None, secMan : KooSectionManager = None, nodeSetMan : NodeSetManager = None, bndMan : KooBoundaryNodeManager = None, loadMan : KooLoadManager = None, defineMan : KooDefineManager = None, contactMan : KooContactManager = None, segMan : KooSegmentSetManager = None):
        self.id = id
        self.name = name
        self.xOrigin = 0.0
        self.yOrigin = 0.0
        self.zOrigin = 0.0
        self.rotation = 0 
        self.mirror = False
        self.isTop = True
        
        self.lpw = 877.0*unit
        self.lph = 800.0*unit
        self.rpw = 870.0*unit
        self.rph = 800.0*unit
        self.piw = 495.0*unit
        self.pt = 30.0*unit
        self.cbw = 1800.0*unit
        self.cbh = 500.0*unit
        self.cbt = 600.0*unit
        self.ltw = 300.0*unit
        self.ltt = 10.0*unit
        self.rtw = 300.0*unit
        self.rtt = 10.0*unit
        self.lbw = 20.0*unit
        self.lbt = 10.0*unit
        self.rbw = 20.0*unit
        self.rbt = 10.0*unit
        self.lfw = 20.0*unit
        self.lft = 10.0*unit
        self.rfw = 20.0*unit
        self.rft = 10.0*unit
        self.lst = 30.0*unit
        self.lsv = 700.0
        self.rst = 30.0*unit
        self.rsv = 700.0
        self.tens = 4.8*unit
        self.Ndi = None
        self.tdi = None
        self.ldi = None
        self.tel = None
        self.epsilon = None
        self.solderWidthRatio = 0.8
        self.solderThicknessRatio = 0.5
        self.solderBottomWidthRatio = 0.4
        self.sgValue = 8
        self.tilt = 0
        self.compound = None
        
        self.shapeSolders = [] 
        self.shapePads = [] 
        self.shapeCeramicBody = []
        self.shapeDielectrics = []
        self.shapeElectrodes = []
        self.shapeTerminals = []
        self.shapeBarriers = []
        self.shapeFinishes = []
        
        self.meshSolders = [] 
        self.meshPads = [] 
        self.meshCeramicBody = []
        self.meshDielectrics = []
        self.meshElectrodes = []
        self.meshTerminals = []
        self.meshBarriers = []
        self.meshFinishes = []
        

        self.meshGenerationMode = False
        self.meshPath = os.getcwd()         
        self.meshSize = 0.1
        self.meshSizeSolder = 0.1
        self.meshSizeBody = 0.1
        self.numberofElementinX = 10
        self.numberofElementinY = 5
        self.numberofElementinZ = 3
        
        self.maxNID = 0
        self.maxEID = 0 
        self.maxPID = 0 
        self.maxMID = 0 
        self.maxSID = 0     
        self.maxNSID = 0
        if matMan != None:
            self.materialManager = matMan
        else:
            self.materialManager = KooMaterialManager()
        if secMan != None:
            self.sectionManager = secMan
        else:
            self.sectionManager = KooSectionManager()   
        if nodeSetMan != None:
            self.nodeSetManager = nodeSetMan
        else:
            self.nodeSetManager = NodeSetManager()
            
        if bndMan != None:
            self.boundaryNodeManager = bndMan
        else:
            self.boundaryNodeManager = KooBoundaryNodeManager()
        
        if loadMan != None:
            self.loadManager = loadMan
        else:
            self.loadManager = KooLoadManager()
        
        if defineMan != None:
            self.defineManager = defineMan
        else:
            self.defineManager = KooDefineManager()
            
        if contactMan != None:
            self.contactManager = contactMan
        else:
            self.contactManager = KooContactManager()
        
        if segMan != None:  
            self.segmentManager = segMan
        else:
            self.segmentManager = KooSegmentSetManager()
        self.dynaAddScript = ""            
        
        self.nodeManager = None
        
        self.partMan = None

        self.midPad = 1            
        self.midTerminal = 1
        self.midBarrier = 1
        self.midFinish = 1
        self.midSolder = 1
        self.midDielectric = 1
        self.midElectrode = 1
        self.midCeramicBody = 1
        
        self.leftVoltage = None
        self.rightVoltage = None
        self.leftVoltageCurve = None
        self.rightVoltageCurve = None

    def SetManagersfromKooDynaImporter(self, dynaImporter : KooDynaImporter):
        self.materialManager = dynaImporter.materialManager
        self.sectionManager = dynaImporter.sectionManager
        self.nodeSetManager = dynaImporter.nodeSetManager
        self.boundaryNodeManager = dynaImporter.boundaryNodeManager
        self.loadManager = dynaImporter.loadManager
        self.defineManager = dynaImporter.defineManager
        self.contactManager = dynaImporter.contactManager
        self.segmentManager = dynaImporter.segmentManager
        
    def GetMaxIDs(self):
        return self.maxNID, self.maxEID, self.maxPID, self.maxSID, self.maxMID, self.maxNSID
    
    def SetMaxIDs(self, maxNID, maxEID, maxPID, maxSID, maxMID, maxNSID):
        self.maxNID = maxNID
        self.maxEID = maxEID
        self.maxPID = maxPID
        self.maxSID = maxSID
        self.maxMID = maxMID
        self.maxNSID = maxNSID
        
    def SetMeshPath(self, path):
        self.meshGenerationMode = True
        self.meshPath = os.path.join(os.getcwd() , path)
        self.meshPath = self.meshPath.replace(".\\","")

    def SetMeshSize(self, size):
        self.meshGenerationMode = True
        self.meshSize = size
    
    def SetMeshSizeSolder(self, size):
        self.meshGenerationMode = True
        self.meshSizeSolder = size
        
    def SetMeshSizeBody(self, size):
        self.meshGenerationMode = True
        self.meshSizeBody = size
        
    def SetNumberofElementsforMLCC(self, numX, numY, numZ):
        self.meshGenerationMode = True
        self.numberofElementinX = numX
        self.numberofElementinY = numY
        self.numberofElementinZ = numZ
        
    def SetMaterialID(self, matidPad, matidTerminal, matidBarrier, matidFinish, matidSolder, matidDielectric, matidElectrode, matidCeramicBody):
        self.midPad = matidPad
        self.midTerminal = matidTerminal
        self.midBarrier = matidBarrier
        self.midFinish = matidFinish
        self.midSolder = matidSolder
        self.midDielectric = matidDielectric
        self.midElectrode = matidElectrode
        self.midCeramicBody = matidCeramicBody   
    
    def SetPiezoelectricMaterial(self, DMat, PXMat, PYMat, PZMat, mode = "E", gpt = 8,aopt=0):
        Pnt = [0, 0, 0]
        AVec = [0, 0, 1]
        DVec = [0, 0, 1]
        self.materialManager.CreateAddPZElectricMaterial(self.midDielectric,mode,gpt,aopt,DMat,PXMat,PYMat,PZMat,Pnt,AVec,DVec)
    
    def SetVoltageValue(self, leftVoltage, rightVoltage):
        self.leftVoltage = leftVoltage
        self.rightVoltage = rightVoltage
    
    def SetVoltageCurve(self, leftVoltageCurve, rightVoltageCurve):
        self.leftVoltageCurve = leftVoltageCurve
        self.rightVoltageCurve = rightVoltageCurve
        
    def SetDynaScript(self, script):
        self.dynaAddScript = script    
    
    def SetProperties(self,lpw = None, lph = None, rpw = None, rph = None, piw = None, pt = None, cbw = None, cbh = None, cbt = None, ltw = None, ltt = None, rtw = None, rtt = None, lbw = None, lbt = None, rbw = None, rbt = None, lfw = None, lft = None, rfw = None, rft = None, lst = None, lsv = None, rst = None, rsv = None, tens = None, solderWidthRatio = None, solderThicknessRatio = None, solderBottomWidthRatio = None, sgValue = None, tilt = None, Ndi = None, tdi = None, tel = None, epsilon = None, ldi = None):
        if lpw is not None:
            self.lpw = lpw
        if lph is not None:
            self.lph = lph
        if rpw is not None:
            self.rpw = rpw
        if rph is not None:
            self.rph = rph
        if piw is not None:
            self.piw = piw
        if pt is not None:
            self.pt = pt
        if cbw is not None:
            self.cbw = cbw
        if cbh is not None:
            self.cbh = cbh
        if cbt is not None:
            self.cbt = cbt
        if ltw is not None:
            self.ltw = ltw
        if ltt is not None:
            self.ltt = ltt
        if rtw is not None:
            self.rtw = rtw
        if rtt is not None:
            self.rtt = rtt
        if lbw is not None:
            self.lbw = lbw
        if lbt is not None:
            self.lbt = lbt
        if rbw is not None:
            self.rbw = rbw
        if rbt is not None:
            self.rbt = rbt
        if lfw is not None:
            self.lfw = lfw
        if lft is not None:
            self.lft = lft
        if rfw is not None:
            self.rfw = rfw
        if rft is not None:
            self.rft = rft
        if lst is not None:
            self.lst = lst
        if lsv is not None:
            self.lsv = lsv
        if rst is not None:
            self.rst = rst
        if rsv is not None:
            self.rsv = rsv
        if tens is not None:
            self.tens = tens
        if solderWidthRatio is not None:
            self.solderWidthRatio = solderWidthRatio
        if solderThicknessRatio is not None:
            self.solderThicknessRatio = solderThicknessRatio
        if solderBottomWidthRatio is not None:
            self.solderBottomWidthRatio = solderBottomWidthRatio
        if sgValue is not None:
            self.sgValue = sgValue
        if tilt is not None:
            self.tilt = tilt                 
        if Ndi is not None:
            self.Ndi = Ndi
        if tdi is not None:
            self.tdi = tdi
        if ldi is not None:
            self.ldi = ldi
        if tel is not None:
            self.tel = tel
        if epsilon is not None:
            self.epsilon = epsilon
            

    def GetLeftTotalThickness(self):
        ltt = self.ltt
        lbt = self.lbt
        lft = self.lft 
        lst = self.lst
        pt = self.pt 
        totalthick = ltt+lbt+lft+lst+pt
        return totalthick
    def GetRightTotalThickness(self):
        rtt = self.rtt
        rbt = self.rbt
        rft = self.rft 
        rst = self.rst
        pt = self.pt 
        totalthick = rtt+rbt+rft+rst+pt
        return totalthick
    def GetTotalThickness(self):
        ltt = self.ltt
        lbt = self.lbt
        lft = self.lft 
        lst = self.lst
        rtt = self.rtt
        rbt = self.rbt
        rft = self.rft 
        rst = self.rst
        pt = self.pt 
        totalthick = max(ltt,rtt)
        totalthick += max(lbt,rbt)
        totalthick += max(lft,rft)
        totalthick += max(lst,rst)
        totalthick += pt
        return totalthick
    def MakeFillet(self,box,indexList,fillet):
        fbox = BRepFilletAPI_MakeFillet(box)
        expl = list(TopologyExplorer(box).edges())
        for i in indexList:
            fbox.Add(fillet,fillet,expl[i])
        fbox.Build()
        if fbox.IsDone():
            return fbox
        else:
            print('Fillet Failed')
            return box 

    def MakeLeftPad(self):
        lpw = self.lpw
        lph = self.lph
        piw = self.piw
        pt = self.pt
        pl1 = gp_Pnt(-piw/2.0,lph/2.0,0.0)
        pl2 = gp_Pnt(-lpw-piw/2.0,-lph/2.0,pt)
        return BRepPrimAPI_MakeBox(pl1,pl2)
    
    def MakeRightPad(self):
        rpw = self.rpw
        rph = self.rph
        piw = self.piw
        pt = self.pt
        pr1 = gp_Pnt(piw/2.0,rph/2.0,0.0)
        pr2 = gp_Pnt(rpw+piw/2.0,-rph/2.0,pt)
        return BRepPrimAPI_MakeBox(pr1,pr2)
    
    def MakeCeramicBodyDetail(self):
        unit = 1
        L = self.cbw
        W = self.cbh
        H = self.cbt        
        mode = -1
        if self.ldi is None:    
            ldi = 250*unit
        else:
            ldi = self.ldi*unit
        if self.Ndi is None or self.tdi is None or self.tel is None:
            mode = 12
        else:
            Ndi = self.Ndi
            tdi = self.tdi*unit
            tel = self.tel*unit
            epsilon = self.epsilon
            
        if self.epsilon is not None:
            epsilon = self.epsilon
        if mode ==1:
            epsilon = 1660 
            Ndi = 381
            tdi = 0.599*unit
            tel = 0.462*unit
        elif mode == 2:
            epsilon = 2110 
            Ndi = 291
            tdi = 0.583*unit
            tel = 0.681*unit
        elif mode == 3:
            epsilon = 3443 
            Ndi = 281
            tdi = 0.925*unit
            tel = 0.524*unit
        elif mode == 12:
            epsilon = 1660
            Ndi = 39
            tdi = 5.99*unit
            tel = 4.62*unit
        elif mode == 22:
            epsilon = 2110 
            Ndi = 28
            tdi = 5.83*unit
            tel = 6.81*unit
        elif mode == 32:
            epsilon = 3443 
            Ndi = 20
            tdi = 9.25*unit
            tel = 5.24*unit

        H = tel*(Ndi+1)+ Ndi*tdi
        self.cbt = H
        '''
        L = self.cbw
        W = self.cbh
        H = self.cbt        
        epsilon = 2500 
        #Ndi = 39
        Ndi = 381
        

        ldi = 0.1*unit
        #tdi = 2*unit
        tdi = 0.599*unit
        tel = (H-Ndi*tdi)/(Ndi+1)
        '''
        epsilon0 = 8.854187818e-12
        Nel = Ndi + 1
        Ldi = L - ldi
        C = epsilon0*epsilon*W*(Ndi*(L-ldi)/tdi+H/ldi)
        unitstr = "F"
        if unit == 1:
            unitstr = "uF"
        print(str(C) + unitstr)
        print(str(H) + "mm")
        layers = [ ]
        zCurrent = self.GetTotalThickness()
        for i in range(0,Nel,2):
            
            layer = [] 
            pnts = []
            pnts.append(gp_Pnt(-L/2.0,-W/2.0,zCurrent))
            pnts.append(gp_Pnt(-L/2.0+ldi,-W/2.0,zCurrent))
            pnts.append(gp_Pnt(-L/2.0+ldi,W/2.0,zCurrent))
            pnts.append(gp_Pnt(-L/2.0,W/2.0,zCurrent))
            pnts.append(gp_Pnt(-L/2.0,-W/2.0,zCurrent))
            wire = BRepBuilderAPI.BRepBuilderAPI_MakePolygon()
            for pnt in pnts:
                wire.Add(pnt)
            wire.Close()
            face = BRepBuilderAPI.BRepBuilderAPI_MakeFace(wire.Wire())
            shape1 = BRepPrimAPI_MakePrism(face.Face(),gp_Vec(0,0,tel)).Shape()
            shape1 = BRepPrimAPI_MakeBox(gp_Pnt(-L/2.0,-W/2.0,zCurrent),ldi,W,tel).Shape()
            pnts = [] 
            pnts.append(gp_Pnt(-L/2.0+ldi,-W/2.0,zCurrent))
            pnts.append(gp_Pnt(L/2.0,-W/2.0,zCurrent))
            pnts.append(gp_Pnt(L/2.0,W/2.0,zCurrent))
            pnts.append(gp_Pnt(-L/2.0+ldi,W/2.0,zCurrent))
            pnts.append(gp_Pnt(-L/2.0+ldi,-W/2.0,zCurrent))
            wire = BRepBuilderAPI.BRepBuilderAPI_MakePolygon()
            for pnt in pnts:
                wire.Add(pnt)
            wire.Close()
            face = BRepBuilderAPI.BRepBuilderAPI_MakeFace(wire.Wire())
            shape2 = BRepPrimAPI_MakePrism(face.Face(),gp_Vec(0,0,tel)).Shape()    
            shape2 = BRepPrimAPI_MakeBox(gp_Pnt(-L/2.0+ldi,-W/2.0,zCurrent),Ldi,W,tel).Shape()
            pnts = []
            pnts.append(gp_Pnt(-L/2.0,-W/2.0,tel+zCurrent))
            pnts.append(gp_Pnt(L/2.0,-W/2.0,tel+zCurrent))
            pnts.append(gp_Pnt(L/2.0,W/2.0,tel+zCurrent))
            pnts.append(gp_Pnt(-L/2.0,W/2.0,tel+zCurrent))
            pnts.append(gp_Pnt(-L/2.0,-W/2.0,tel+zCurrent))
            wire = BRepBuilderAPI.BRepBuilderAPI_MakePolygon()
            for pnt in pnts:
                wire.Add(pnt)
            wire.Close()
            face = BRepBuilderAPI.BRepBuilderAPI_MakeFace(wire.Wire())
            shape3 = BRepPrimAPI_MakePrism(face.Face(),gp_Vec(0,0,tdi)).Shape()
            shape3 = BRepPrimAPI_MakeBox(gp_Pnt(-L/2.0,-W/2.0,tel+zCurrent),L,W,tdi).Shape()

            pnts = [] 
            pnts.append(gp_Pnt(-L/2.0,-W/2.0,tdi+tel+zCurrent))
            pnts.append(gp_Pnt(L/2.0-ldi,-W/2.0,tdi+tel+zCurrent))
            pnts.append(gp_Pnt(L/2.0-ldi,W/2.0,tdi+tel+zCurrent))
            pnts.append(gp_Pnt(-L/2.0,W/2.0,tdi+tel+zCurrent))
            pnts.append(gp_Pnt(-L/2.0,-W/2.0,tdi+tel+zCurrent))    
            wire = BRepBuilderAPI.BRepBuilderAPI_MakePolygon()
            for pnt in pnts:
                wire.Add(pnt)
            wire.Close()
            face = BRepBuilderAPI.BRepBuilderAPI_MakeFace(wire.Wire())
            shape4 = BRepPrimAPI_MakePrism(face.Face(),gp_Vec(0,0,tel)).Shape()
            shape4 = BRepPrimAPI_MakeBox(gp_Pnt(-L/2.0,-W/2.0,tdi+tel+zCurrent),Ldi,W,tel).Shape()
            
            pnts = [] 
            pnts.append(gp_Pnt(L/2.0-ldi,-W/2.0,tdi+tel+zCurrent))
            pnts.append(gp_Pnt(L/2.0,-W/2.0,tdi+tel+zCurrent))
            pnts.append(gp_Pnt(L/2.0,W/2.0,tdi+tel+zCurrent))
            pnts.append(gp_Pnt(L/2.0-ldi,W/2.0,tdi+tel+zCurrent))
            pnts.append(gp_Pnt(L/2.0-ldi,-W/2.0,tdi+tel+zCurrent))
            wire = BRepBuilderAPI.BRepBuilderAPI_MakePolygon()
            for pnt in pnts:
                wire.Add(pnt)
            wire.Close()
            face = BRepBuilderAPI.BRepBuilderAPI_MakeFace(wire.Wire())
            shape5 = BRepPrimAPI_MakePrism(face.Face(),gp_Vec(0,0,tel)).Shape()
            shape5 = BRepPrimAPI_MakeBox(gp_Pnt(L/2.0-ldi,-W/2.0,tdi+tel+zCurrent),ldi,W,tel).Shape()

            pnts = [] 
            pnts.append(gp_Pnt(-L/2.0,-W/2.0,tdi + 2.0*tel + zCurrent))
            pnts.append(gp_Pnt(L/2.0,-W/2.0,tdi + 2.0*tel + zCurrent))
            pnts.append(gp_Pnt(L/2.0,W/2.0,tdi + 2.0*tel + zCurrent))
            pnts.append(gp_Pnt(-L/2.0,W/2.0,tdi + 2.0*tel + zCurrent))
            pnts.append(gp_Pnt(-L/2.0,-W/2.0,tdi + 2.0*tel + zCurrent))    
            wire = BRepBuilderAPI.BRepBuilderAPI_MakePolygon()
            for pnt in pnts:
                wire.Add(pnt)
            wire.Close()
            face = BRepBuilderAPI.BRepBuilderAPI_MakeFace(wire.Wire())
            shape6 = BRepPrimAPI_MakePrism(face.Face(),gp_Vec(0,0,tdi)).Shape()
            shape6 = BRepPrimAPI_MakeBox(gp_Pnt(-L/2.0,-W/2.0,tdi + 2.0*tel + zCurrent),L,W,tdi).Shape()

            dishapeList = [shape1,shape3,shape5]
            if i < Nel - 2:
                dishapeList.append(shape6)
            elshapeList = [shape2,shape4]

            zCurrent = zCurrent + tdi + tdi + tel + tel
            layer.append(dishapeList)
            layer.append(elshapeList)
            layers.append(layer)
        compoundDi = TopoDS_Compound()
        compoundEl = TopoDS_Compound()
        builderDi = BRep_Builder()
        builderEl = BRep_Builder()
        builderDi.MakeCompound(compoundDi)
        builderEl.MakeCompound(compoundEl)

        for layer in layers:
            for shape in layer[0]:
                builderDi.Add(compoundDi,shape)
            for shape in layer[1]:
                builderEl.Add(compoundEl,shape)
        
        return compoundDi,compoundEl
        

    def MakeCeramicBody(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        # total thickness
        totalThickness = self.GetTotalThickness()
        plb3 = gp_Pnt(-cbw/2.0,-cbh/2.0,totalThickness)
        prt3 = gp_Pnt(cbw/2.0,cbh/2.0,totalThickness+cbt)
        box = BRepPrimAPI_MakeBox(plb3,prt3)
        return box
        
    def MakeLeftTerminal(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        ltt = self.ltt
        ltw = self.ltw
        totalThickness = self.GetLeftTotalThickness()
        plb1 = gp_Pnt(-cbw/2.0-ltt,cbh/2.0+ltt,totalThickness+cbt+ltt)
        plb2 = gp_Pnt(-cbw/2.0+ltw+ltt,-cbh/2.0-ltt,totalThickness-ltt)
        return BRepPrimAPI_MakeBox(plb1,plb2)
    
    def MakeRightTerminal(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        rtt = self.rtt
        rtw = self.rtw
        totalThickness = self.GetRightTotalThickness()
        prb1 = gp_Pnt(cbw/2.0+rtt,cbh/2.0+rtt,totalThickness+cbt+rtt)
        prb2 = gp_Pnt(cbw/2.0-rtw-rtt,-cbh/2.0-rtt,totalThickness-rtt)
        return BRepPrimAPI_MakeBox(prb1,prb2)

    def MakeLeftBarrier(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        ltt = self.ltt
        ltw = self.ltw
        lbt = self.lbt
        lbw = self.lbw
        totalthickness = self.GetLeftTotalThickness()
        pl51 = gp_Pnt(-cbw/2.0-ltt-lbt,cbh/2.0+ltt+lbt,totalthickness+cbt+ltt+lbt)
        pl52 = gp_Pnt(-cbw/2.0+ltw+lbw+ltt+lbt,-cbh/2.0-ltt-lbt,totalthickness-ltt-lbt)
        return BRepPrimAPI_MakeBox(pl51,pl52)
    
    def MakeRightBarrier(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        rtt = self.rtt
        rtw = self.rtw
        rbt = self.rbt
        rbw = self.rbw
        totalthickness = self.GetRightTotalThickness()
        pr51 = gp_Pnt(cbw/2.0+rtt+rbt,cbh/2.0+rtt+rbt,totalthickness+cbt+rtt+rbt)
        pr52 = gp_Pnt(cbw/2.0-rtw-rbw-rtt-rbt,-cbh/2.0-rtt-rbt,totalthickness-rtt-rbt)
        return BRepPrimAPI_MakeBox(pr51,pr52)
    
    def MakeLeftFinish(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        ltt = self.ltt
        ltw = self.ltw
        lbt = self.lbt
        lbw = self.lbw
        lft = self.lft
        lfw = self.lfw
        totalthickness = self.GetLeftTotalThickness()
        pl61 = gp_Pnt(-cbw/2.0-ltt-lbt-lft,cbh/2.0+ltt+lbt+lft,totalthickness+cbt+ltt+lbt+lft)
        pl62 = gp_Pnt(-cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft,-cbh/2.0-ltt-lbt-lft,totalthickness-ltt-lbt-lft)
        box = BRepPrimAPI_MakeBox(pl61,pl62).Shape()
        fillet = 10*unit
        return self.MakeFillet(box,[0,1,2,3,4,5,6,7,8,9,10,11],fillet)
    
    def MakeRightFinish(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        rtt = self.rtt
        rtw = self.rtw
        rbt = self.rbt
        rbw = self.rbw
        rft = self.rft
        rfw = self.rfw
        totalthickness = self.GetRightTotalThickness()
        pr61 = gp_Pnt(cbw/2.0+rtt+rbt+rft,cbh/2.0+rtt+rbt+rft,totalthickness+cbt+rtt+rbt+rft)
        pr62 = gp_Pnt(cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft,-cbh/2.0-rtt-rbt-rft,totalthickness-rtt-rbt-rft)
        box = BRepPrimAPI_MakeBox(pr61,pr62).Shape()
        fillet = 10*unit
        return self.MakeFillet(box,[0,1,2,3,4,5,6,7,8,9,10,11],fillet)       

    def MakeMLCC(self,detailMode = False):
        if __name__ =="__main__":
            display.EraseAll()
        
        # Generate Geometry Components
        lp = self.MakeLeftPad()
        rp = self.MakeRightPad()
        if detailMode == True:
            ## Display Ceramic Body
            rreal = 255.0 / 255.0
            greal = 69.0 / 255.0
            breal = 0 / 255.0
            color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)
            cd,ce = self.MakeCeramicBodyDetail()
            if __name__ == "__main__":
                display.DisplayShape(cd,None,None,color)
            rreal = 25.0 / 255.0
            greal = 25.0 / 255.0
            breal = 112.0 / 255.0
            color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)            
            if __name__ == "__main__":
                display.DisplayShape(ce,None,None,color)
        cb = self.MakeCeramicBody()
        lt = self.MakeLeftTerminal()
        rt = self.MakeRightTerminal()
        lb = self.MakeLeftBarrier()
        rb = self.MakeRightBarrier()
        lf = self.MakeLeftFinish()
        rf = self.MakeRightFinish()
        if __name__ == "__main__":
            display.DisplayShape(lp.Shape())
            display.DisplayShape(rp.Shape())
        ## Display Ceramic Body
        rreal = 145.0 / 255.0
        greal = 102.0 / 255.0
        breal = 83.0 / 255.0
        color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)
        if detailMode == False:
            if __name__ == "__main__":
                display.DisplayShape(cb.Shape(),None,None,color)
        ## Cut Operatior of Terminal 'by' Ceramic Body
        clt = BRepAlgoAPI_Cut(lt.Shape(),cb.Shape())
        crt = BRepAlgoAPI_Cut(rt.Shape(),cb.Shape())
        ## Display Left/Right Terminal
        rreal = 26.0 / 255.0
        greal = 52.0 / 255.0
        breal = 109.0  / 255.0
        color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)
        if __name__ == "__main__":
            display.DisplayShape(clt.Shape(),None,None,color,update=True)
            display.DisplayShape(crt.Shape(),None,None,color,update=True)
        ## Display Left/Right Barrier
        clb = BRepAlgoAPI_Cut(lb.Shape(),cb.Shape())
        crb = BRepAlgoAPI_Cut(rb.Shape(),cb.Shape())
        clb =   BRepAlgoAPI_Cut(clb.Shape(),lt.Shape())
        crb =   BRepAlgoAPI_Cut(crb.Shape(),rt.Shape())
        rreal = 245.0 / 255.0
        greal = 104.0 / 255.0
        breal = 12.0 / 255.0
        color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)
        if __name__ == "__main__":
            display.DisplayShape(clb.Shape(),None,None,color,update=True)
            display.DisplayShape(crb.Shape(),None,None,color,update=True)

        ## Display Left/Right Finish 
        ## Cut Operation of finish 'by' Ceramic Body, Terminal and Barrier 
        clf = BRepAlgoAPI_Cut(lf.Shape(),cb.Shape())
        crf = BRepAlgoAPI_Cut(rf.Shape(),cb.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lt.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rt.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lb.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rb.Shape())

        rreal = 181.0/255.0
        greal = 178.0/255.0
        breal = 189.0/255.0
        color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)
        if __name__ == "__main__":
            display.DisplayShape(clf.Shape(),None,None,color,update=True)        
            display.DisplayShape(crf.Shape(),None,None,color,update=True)

        if detailMode == False:
            compoundList = [lp.Shape(),rp.Shape(),cb.Shape(),lt.Shape(),rt.Shape(),lb.Shape(),rb.Shape(),lf.Shape(),rf.Shape(),clt.Shape(),crt.Shape(),clb.Shape(),crb.Shape(),clf.Shape(),crf.Shape()]
        else:
            compoundList = [lp.Shape(),rp.Shape(),cd,ce,lt.Shape(),rt.Shape(),lb.Shape(),rb.Shape(),lf.Shape(),rf.Shape(),clt.Shape(),crt.Shape(),clb.Shape(),crb.Shape(),clf.Shape(),crf.Shape()]
        return compoundList
    def MakeSolderScript(self,fileName,direction,solderWidthRatio,solderThicknessRatio,solderBottomWidthRatio,tens,SG,tilt):
        evolverScript = "//Capacitor \n"
        evolverScript += "Evolver_Version ""2.11""\n"
        evolverScript += "// Physical dimensions of the chip\n"
        evolverScript += "parameter lpw = {lpw} // leftPadWidth\n"
        evolverScript += "parameter lph = {lph} // leftPadHeight\n"
        evolverScript += "parameter pt = {pt} // padThickness\n"
        evolverScript += "parameter piw = {piw} // padIntervalWidth\n"        
        evolverScript += "parameter rpw = {rpw} // rightPadWidth\n"
        evolverScript += "parameter rph = {rph} // rightPadHeight\n"
        evolverScript += "parameter cbw = {cbw} // ceramicBodyWidth\n"
        evolverScript += "parameter cbh = {cbh} // ceramicBodyHeight\n"
        evolverScript += "parameter cbt = {cbt} // ceramicBodyThickness\n"
        evolverScript += "parameter ltw = {ltw} // leftTerminalWidth\n"
        evolverScript += "parameter ltt = {ltt} // leftTerminalThickness\n"
        evolverScript += "parameter rtw = {rtw} // rightTerminalWidth\n"
        evolverScript += "parameter rtt = {rtt} // rightTerminalThickness\n"
        evolverScript += "parameter lbw = {lbw} // leftBarrierWidth\n"
        evolverScript += "parameter lbt = {lbt} // leftBarrierThickness\n"
        evolverScript += "parameter rbw = {rbw} // rightBarrierWidth\n"
        evolverScript += "parameter rbt = {rbt} // rightBarrierThickness\n"
        evolverScript += "parameter lfw = {lfw} // leftFinishWidth\n"
        evolverScript += "parameter lft = {lft} // leftFinishThickness\n"
        evolverScript += "parameter rfw = {rfw} // rightFinishWidth\n"
        evolverScript += "parameter rft = {rft} // rightFinishThickness\n"
        evolverScript += "parameter lst = {lst} // leftSolderThickness\n"
        evolverScript += "parameter lsv = {lsv} // leftSolderVolume\n"
        evolverScript += "parameter rst = lst // rightSolderThickness\n"
        evolverScript += "parameter rsv = {rsv} // rightSolderVolume\n"
        evolverScript += "parameter v1 = lsv*1000*1000*1000\n"
        evolverScript += "parameter v2 = rsv*1000*1000*1000\n"
        #evolverScript += "parameter v1 = lsv\n"
        #evolverScript += "parameter v2 = rsv\n"
        evolverScript += "parameter leftTotalThickness = ltt + lbt + lft + lst + pt// left total thickness\n"
        evolverScript += "parameter rightTotalThickness = rtt + rbt + rft + rst + pt// right total thickness\n"
        evolverScript += "// solder\n"
        evolverScript += "parameter solderWidthRatio = {solderWidthRatio} // solderWidthRatio\n"
        evolverScript += "parameter solderThicknessRatio = {solderThicknessRatio} // solderThicknessRatio\n"
        evolverScript += "parameter solderBottomWidthRatio = {solderBottomWidthRatio} // solderBottonWidth\n"
        evolverScript += "parameter PW_x = lpw\n"
        evolverScript += "parameter PW_y = lph\n"
        evolverScript += "parameter TENS = {tens}*1000\n"
        #evolverScript += "parameter TENS = {tens}\n"
        evolverScript += "parameter SG = {SG}\n"
        evolverScript += "parameter tilt = {tilt}\n"
        evolverScript += "#define st sin(tilt*pi/180)\n"
        evolverScript += "#define ct cos(tilt*pi/180)\n"
        evolverScript += "parameter x0 = 0\n"
        evolverScript += "parameter zl0 = leftTotalThickness+cbt/2.0\n"
        evolverScript += "parameter zr0 = rightTotalThickness+cbt/2.0\n"
        evolverScript += "parameter z0 = 0\n"
        evolverScript += "#define CHIPLX    (ct*(x-x0)-st*(z-zl0))\n"
        evolverScript += "#define CHIPLY    (y)\n"
        evolverScript += "#define CHIPLZ    (st*(x-x0)+ct*(z-zl0))+zl0\n" 
        evolverScript += "#define CHIPRX    (ct*(x-x0)-st*(z-zr0))\n"
        evolverScript += "#define CHIPRY    (y)\n"
        evolverScript += "#define CHIPRZ    (st*(x-x0)+ct*(z-zr0))+zr0\n"
        evolverScript += "gravity_constant  9.81\n"
        evolverScript += "scale_limit  1/TENS\n"
        evolverScript += "// Left Pad\n"
        evolverScript += "constraint 1 // +x face of left pad\n"
        evolverScript += "formula : x = -piw/2.0\n"
        evolverScript += "constraint 2 // -x face of left pad\n"
        evolverScript += "formula : x = -lpw-piw/2.0\n"
        evolverScript += "constraint 3 // +y face of left pad\n"
        evolverScript += "formula : y = lph/2.0\n"
        evolverScript += "constraint 4 // -y face of left pad\n"
        evolverScript += "formula : y = -lph/2.0\n"
        evolverScript += "constraint 5 // +z face of left pad\n"
        evolverScript += "formula : z = pt\n"
        evolverScript += "constraint 6 // -z face of left pad\n"
        evolverScript += "formula : z = 0\n"
        evolverScript += "// Left Finish\n"
        evolverScript += "constraint 7 // +x face of left finish\n"
        evolverScript += "formula : CHIPLX = -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft\n"
        evolverScript += "constraint 8 // -x face of left finish\n"
        evolverScript += "formula : CHIPLX = -cbw/2.0-ltt-lbt-lft\n"
        evolverScript += "constraint 9 // +y face of left finish\n"
        evolverScript += "formula : CHIPLY = cbh/2.0+ltt+lbt+lft\n"
        evolverScript += "constraint 10 // -y face of left finish\n"
        evolverScript += "formula : CHIPLY = -cbh/2.0-ltt-lbt-lft\n"
        evolverScript += "constraint 11 // +z face of left finish\n"
        evolverScript += "formula : CHIPLZ = leftTotalThickness + cbt + ltt + lbt + lft\n"
        evolverScript += "constraint 12 // -z face of left finish\n"
        evolverScript += "formula : CHIPLZ = leftTotalThickness - ltt - lbt - lft\n"
        evolverScript += "// Right Pad\n"
        evolverScript += "constraint 1001 // +x face of right pad\n"
        evolverScript += "formula : x = rpw+piw/2.0\n"
        evolverScript += "constraint 1002 // -x face of right pad\n"
        evolverScript += "formula : x = piw/2.0\n"
        evolverScript += "constraint 1003 // +y face of right pad\n"
        evolverScript += "formula : y = rph/2.0\n"
        evolverScript += "constraint 1004 // -y face of right pad\n"
        evolverScript += "formula : y = -rph/2.0\n"
        evolverScript += "constraint 1005 // +z face of right pad\n"
        evolverScript += "formula : z = pt\n"
        evolverScript += "constraint 1006 // -z face of right pad\n"
        evolverScript += "formula : z = 0\n"
        evolverScript += "// Right Finish\n"
        evolverScript += "constraint 1007 // +x face of right finish\n"
        evolverScript += "formula : CHIPRX = cbw/2.0 - rtw - rbw - rfw - rtt - rbt - rft\n"
        evolverScript += "constraint 1008 // -x face of right finish\n"
        evolverScript += "formula : CHIPRX = cbw/2.0 + rtt + rbt + rft\n"
        evolverScript += "constraint 1009 // +y face of right finish\n"
        evolverScript += "formula : CHIPRY = cbh/2.0 + rtt + rbt + rft\n"
        evolverScript += "constraint 1010 // -y face of right finish\n"
        evolverScript += "formula : CHIPRY = -cbh/2.0 - rtt - rbt - rft\n"
        evolverScript += "constraint 1011 // +z face of right finish\n"
        evolverScript += "formula : CHIPRZ = rightTotalThickness + cbt + rtt + rbt + rft\n"
        evolverScript += "constraint 1012 // -z face of right finish\n"
        evolverScript += "formula : CHIPRZ = rightTotalThickness - rtt - rbt - rft\n"
        evolverScript += "// Constraint for solder on chip\n"
        evolverScript += "// Left pad\n"        
        evolverScript += "constraint 101 nonpositive // to keep solder within pos y bound\n"
        evolverScript += "formula : x+piw/2.0\n"
        evolverScript += "constraint 102 nonnegative\n"
        evolverScript += "formula : x+piw/2.0+lpw\n"
        evolverScript += "constraint 103 nonpositive\n"
        evolverScript += "formula : y-lph/2.0\n"
        evolverScript += "constraint 104 nonnegative\n"
        evolverScript += "formula : y+lph/2.0\n"
        evolverScript += "constraint 105 nonpositive\n"
        evolverScript += "formula : z-pt\n"
        evolverScript += "constraint 106 nonnegative\n"
        evolverScript += "formula : z\n"
        evolverScript += "// Left Finish\n"
        evolverScript += "constraint 107 nonpositive // +x face of left finish\n"
        evolverScript += "formula : CHIPLX + cbw/2.0 - ltw - lbw - lfw - ltt - lbw - lft\n"
        evolverScript += "constraint 108 nonnegative // -x face of left finish\n"
        evolverScript += "formula : CHIPLX + cbw/2.0 + ltt + lbt + lft\n"
        evolverScript += "constraint 109 nonpositive // +y face of left finish\n"
        evolverScript += "formula : CHIPLY - cbh/2.0 - ltt - lbt - lft\n"
        evolverScript += "constraint 110 nonnegative // -y face of left finish\n"
        evolverScript += "formula : CHIPLY + cbh/2.0 + ltt + lbt + lft\n"
        evolverScript += "constraint 111 nonpositive // +z face of left finish\n"
        evolverScript += "formula : CHIPLZ - leftTotalThickness - cbt - ltt - lbt - lft\n"
        evolverScript += "constraint 112 nonnegative // -z face of left finish\n"
        evolverScript += "formula : CHIPLZ - leftTotalThickness + ltt + lbt + lft\n"
        evolverScript += "// Right Pad\n"
        evolverScript += "constraint 1101 nonpositive // +x face of right pad\n"
        evolverScript += "formula : x - rpw - piw/2.0\n"
        evolverScript += "constraint 1102 nonnegative // -x face of right pad\n"
        evolverScript += "formula : x - piw/2.0\n"
        evolverScript += "constraint 1103 nonpositive // +y face of right pad\n"
        evolverScript += "formula : y - rph/2.0\n"
        evolverScript += "constraint 1104 nonnegative // -y face of right pad\n"
        evolverScript += "formula : y + rph/2.0\n"
        evolverScript += "constraint 1105 nonpositive // +z face of right pad\n"
        evolverScript += "formula : z - pt\n"
        evolverScript += "constraint 1106 nonnegative // -z face of right pad\n"
        evolverScript += "formula : z\n"
        evolverScript += "// Right Finish\n"
        evolverScript += "constraint 1107 nonnegative // +x face of right finish\n"
        evolverScript += "formula : CHIPRX - cbw/2.0 + rtw + rbw + rfw + rtt + rbt + rft\n"
        evolverScript += "constraint 1108 nonpositive // -x face of right finish\n"
        evolverScript += "formula : CHIPRX - cbw/2.0 - rtt - rbt - rft\n"
        evolverScript += "constraint 1109 nonpositive // +y face of right finish\n"
        evolverScript += "formula : CHIPRY - cbh/2.0 - rtt - rbt - rft\n"
        evolverScript += "constraint 1110 nonnegative // -y face of right finish\n"
        evolverScript += "formula : CHIPRY + cbh/2.0 + rtt + rbt + rft\n"
        evolverScript += "constraint 1111 nonpositive // +z face of right finish\n"
        evolverScript += "formula : CHIPRZ - rightTotalThickness - cbt - rtt - rbt - rft\n"
        evolverScript += "constraint 1112 nonnegative // -z face of right finish\n"
        evolverScript += "formula : CHIPRZ - rightTotalThickness + rtt + rbt + rft\n"
        evolverScript += "// Initial Shape Specification\n"
        evolverScript += "// Note that numbering of elements is not continous to keep the same \n"
        evolverScript += "// elements after loading, start Evolver with the -i option\n"
        evolverScript += "// given as coordinates\n"
        evolverScript += "vertices\n"

        evolverScript += "//left pad\n"
        evolverScript += "1 -lpw-piw/2.0    -lph/2.0    0.0 fixed\n"
        evolverScript += "2 -piw/2.0    -lph/2.0     0.0 fixed\n"
        evolverScript += "3 -piw/2.0    lph/2.0     0.0 fixed\n"
        evolverScript += "4 -lpw-piw/2.0    lph/2.0     0.0 fixed\n"
        evolverScript += "5 -lpw-piw/2.0    -lph/2.0    pt fixed\n"
        evolverScript += "6 -piw/2.0    -lph/2.0     pt fixed\n"
        evolverScript += "7 -piw/2.0    lph/2.0     pt fixed\n"
        evolverScript += "8 -lpw-piw/2.0    lph/2.0     pt fixed\n"

        evolverScript += "//left finish \n"
        evolverScript += "9 -cbw/2.0-ltt-lbt-lft    -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft fixed\n"
        evolverScript += "10 -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft    -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft fixed\n"
        evolverScript += "11 -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft    cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft fixed\n"
        evolverScript += "12 -cbw/2.0-ltt-lbt-lft    cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft fixed\n"
        evolverScript += "13 -cbw/2.0-ltt-lbt-lft    -cbh/2.0-ltt-lbt-lft    leftTotalThickness+cbt+ltt+lbt+lft fixed\n"
        evolverScript += "14 -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft    -cbh/2.0-ltt-lbt-lft    leftTotalThickness+cbt+ltt+lbt+lft fixed\n"
        evolverScript += "15 -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft    cbh/2.0+ltt+lbt+lft    leftTotalThickness+cbt+ltt+lbt+lft fixed\n"
        evolverScript += "16 -cbw/2.0-ltt-lbt-lft    cbh/2.0+ltt+lbt+lft    leftTotalThickness+cbt+ltt+lbt+lft fixed\n"

        evolverScript += "//right pad\n"
        evolverScript += "1001 rpw+piw/2.0    -rph/2.0    0.0 fixed\n"
        evolverScript += "1002 piw/2.0    -rph/2.0     0.0 fixed\n"
        evolverScript += "1003 piw/2.0    rph/2.0     0.0 fixed\n"
        evolverScript += "1004 rpw+piw/2.0    rph/2.0     0.0 fixed\n"
        evolverScript += "1005 rpw+piw/2.0    -rph/2.0    pt fixed\n"
        evolverScript += "1006 piw/2.0    -rph/2.0     pt fixed\n"
        evolverScript += "1007 piw/2.0    rph/2.0     pt fixed\n"
        evolverScript += "1008 rpw+piw/2.0    rph/2.0     pt fixed\n"
        evolverScript += "//right finish\n"
        evolverScript += "1009 cbw/2.0+rtt+rbt+rft    -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft fixed\n"
        evolverScript += "1010 cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft    -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft fixed\n"
        evolverScript += "1011 cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft    cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft fixed\n"
        evolverScript += "1012 cbw/2.0+rtt+rbt+rft    cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft fixed\n"
        evolverScript += "1013 cbw/2.0+rtt+rbt+rft    -cbh/2.0-rtt-rbt-rft    rightTotalThickness+cbt+rtt+rbt+rft fixed\n"
        evolverScript += "1014 cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft   -cbh/2.0-rtt-rbt-rft    rightTotalThickness+cbt+rtt+rbt+rft fixed\n"
        evolverScript += "1015 cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft    cbh/2.0+rtt+rbt+rft    rightTotalThickness+cbt+rtt+rbt+rft fixed\n"
        evolverScript += "1016 cbw/2.0+rtt+rbt+rft    cbh/2.0+rtt+rbt+rft    rightTotalThickness+cbt+rtt+rbt+rft fixed\n"


        evolverScript += "//left solder\n"
        evolverScript += "101 -lpw-piw/2.0    -lph/2.0    pt    constraints 5   105\n"
        evolverScript += "102 -lpw*(1.0-solderBottomWidthRatio)-piw/2.0    -lph/2.0     pt    constraints 5   105\n"
        evolverScript += "103 -lpw*(1.0-solderBottomWidthRatio)-piw/2.0    lph/2.0    pt    constraints 5   105\n"
        evolverScript += "104 -lpw-piw/2.0    lph/2.0    pt    constraints 5   105\n"
        evolverScript += "105 -cbw/2.0-ltt-lbt-lft   -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft  constraints 12  8   10\n"
        evolverScript += "106 -cbw/2.0-ltt-lbt-lft+solderWidthRatio*(ltw+lbw+lfw+2.0*ltt+2.0*lbt+2.0*lft)   -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft  constraints 12\n"
        evolverScript += "107 -cbw/2.0-ltt-lbt-lft+solderWidthRatio*(ltw+lbw+lfw+2.0*ltt+2.0*lbt+2.0*lft)   cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft  constraints 12\n"
        evolverScript += "108 -cbw/2.0-ltt-lbt-lft   cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft  constraints 12  8   9\n"
        evolverScript += "109 -cbw/2.0-ltt-lbt-lft   -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft+solderThicknessRatio*(cbt+2.0*ltt+2.0*lbt+2.0*lft)  constraints 8   10\n"
        evolverScript += "110 -cbw/2.0-ltt-lbt-lft   cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft+solderThicknessRatio*(cbt+2.0*ltt+2.0*lbt+2.0*lft)  constraints 8    9\n"

        evolverScript += "//right solder\n"
        evolverScript += "1101  rpw+piw/2.0   -rph/2.0  pt  constraints 1005   1105\n"
        evolverScript += "1102  rpw*(1.0-solderBottomWidthRatio)+piw/2.0   -rph/2.0  pt  constraints 1005   1105\n"
        evolverScript += "1103  rpw*(1.0-solderBottomWidthRatio)+piw/2.0   rph/2.0  pt  constraints 1005   1105\n"
        evolverScript += "1104  rpw+piw/2.0   rph/2.0  pt  constraints 1005   1105\n"
        evolverScript += "1105  cbw/2.0+rtt+rbt+rft   -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft  constraints 1012  1008   1010\n"
        evolverScript += "1106  cbw/2.0+rtt+rbt+rft-solderWidthRatio*(rtw+rbw+rfw+2.0*rtt+2.0*rbt+2.0*rft)   -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft  constraints 1012\n"
        evolverScript += "1107  cbw/2.0+rtt+rbt+rft-solderWidthRatio*(rtw+rbw+rfw+2.0*rtt+2.0*rbt+2.0*rft)  cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft  constraints 1012\n"
        evolverScript += "1108  cbw/2.0+rtt+rbt+rft   cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft  constraints 1012  1008   1009\n"
        evolverScript += "1109  cbw/2.0+rtt+rbt+rft   -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft+solderThicknessRatio*(cbt+2.0*rtt+2.0*rbt+2.0*rft)  constraints 1008   1010\n"
        evolverScript += "1110  cbw/2.0+rtt+rbt+rft   cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft+solderThicknessRatio*(cbt+2.0*rtt+2.0*rbt+2.0*rft)  constraints 1008    1009\n"

        evolverScript += "100001    x0  -1000 zl0\n"
        evolverScript += "100002    x0  1000  zl0\n"
        evolverScript += "100003    x0  -1000 zr0\n"
        evolverScript += "100004    x0  1000  zr0\n"
        evolverScript += "edges\n"
        evolverScript += "100001    100001  100002\n"
        evolverScript += "100002    100003  100004\n"
        evolverScript += "//left pad \n"
        evolverScript += "1  1  2   fixed   no_refine\n"
        evolverScript += "2  2  3   fixed   no_refine\n"
        evolverScript += "3  3  4   fixed   no_refine\n"
        evolverScript += "4  4  1   fixed   no_refine\n"
        evolverScript += "5  5  6   fixed   no_refine\n"
        evolverScript += "6  6  7   fixed   no_refine\n"
        evolverScript += "7  7  8   fixed   no_refine\n"
        evolverScript += "8  8  5   fixed   no_refine\n"
        evolverScript += "9  1  5   fixed   no_refine\n"
        evolverScript += "10  2  6   fixed   no_refine\n"
        evolverScript += "11  3  7   fixed   no_refine\n"
        evolverScript += "12  4  8   fixed   no_refine\n"
        evolverScript += "//left finish\n" 
        evolverScript += "13  9  10   fixed   no_refine\n"
        evolverScript += "14  10  11   fixed   no_refine\n"
        evolverScript += "15  11  12   fixed   no_refine\n"
        evolverScript += "16  12  9   fixed   no_refine\n"
        evolverScript += "17  13  14   fixed   no_refine\n"
        evolverScript += "18  14  15   fixed   no_refine\n"
        evolverScript += "19  15  16   fixed   no_refine\n"
        evolverScript += "20  16  13   fixed   no_refine\n"
        evolverScript += "21  9  13   fixed   no_refine\n"
        evolverScript += "22  10  14   fixed   no_refine\n"
        evolverScript += "23  11  15   fixed   no_refine\n"
        evolverScript += "24  12  16   fixed   no_refine\n"
        evolverScript += "// right pad\n"
        evolverScript += "1001  1001  1002   fixed   no_refine\n"
        evolverScript += "1002  1002  1003   fixed   no_refine\n"
        evolverScript += "1003  1003  1004   fixed   no_refine\n"
        evolverScript += "1004  1004  1001   fixed   no_refine\n"
        evolverScript += "1005  1005  1006   fixed   no_refine\n"
        evolverScript += "1006  1006  1007   fixed   no_refine\n"
        evolverScript += "1007  1007  1008   fixed   no_refine\n"
        evolverScript += "1008  1008  1005   fixed   no_refine\n"
        evolverScript += "1009  1001  1005   fixed   no_refine\n"
        evolverScript += "1010  1002  1006   fixed   no_refine\n"
        evolverScript += "1011  1003  1007   fixed   no_refine\n"
        evolverScript += "1012  1004  1008   fixed   no_refine\n"
        evolverScript += "// right finish\n"
        evolverScript += "1013  1009  1010   fixed   no_refine\n"
        evolverScript += "1014  1010  1011   fixed   no_refine\n"
        evolverScript += "1015  1011  1012   fixed   no_refine\n"
        evolverScript += "1016  1012  1009   fixed   no_refine\n"
        evolverScript += "1017  1013  1014   fixed   no_refine\n"
        evolverScript += "1018  1014  1015   fixed   no_refine\n"
        evolverScript += "1019  1015  1016   fixed   no_refine\n"
        evolverScript += "1020  1016  1013   fixed   no_refine\n"
        evolverScript += "1021  1009  1013   fixed   no_refine\n"
        evolverScript += "1022  1010  1014   fixed   no_refine\n"
        evolverScript += "1023  1011  1015   fixed   no_refine\n"
        evolverScript += "1024  1012  1016   fixed   no_refine\n"
        evolverScript += "// left solder below\n"
        evolverScript += "101   101 102 constraints 5   105 106\n"
        evolverScript += "102   102 103 constraints 5   105 106\n"
        evolverScript += "103   103 104 constraints 5   105 106\n"
        evolverScript += "104   104 101 constraints 5   105 106\n"
        evolverScript += "105 101 109\n"
        evolverScript += "106 104 110\n"
        evolverScript += "107 109 110 constraints 8 108\n"
        evolverScript += "109 106 102\n"
        evolverScript += "111 107 103\n"
        evolverScript += "112 106 107 constraints 12 112\n"
        evolverScript += "114 108 105 constraints 12 8\n"
        evolverScript += "108 109 106 constraints 10 110\n"
        evolverScript += "115 105 106 constraints 12 10\n"
        evolverScript += "116 105 109 constraints 8 10\n"
        evolverScript += "110 110 107 constraints 9 109\n"
        evolverScript += "113 107 108 constraints 12 9 \n"
        evolverScript += "117 108 110 constraints 8 9 \n"
        evolverScript += "// right solder below\n"
        evolverScript += "1101 1101 1102 constraints 1005 1105 1106 \n"
        evolverScript += "1102 1102 1103 constraints 1005 1105 1106 \n"
        evolverScript += "1103 1103 1104 constraints 1005 1105 1106 \n"
        evolverScript += "1104 1104 1101 constraints 1005 1105 1106 \n"
        evolverScript += "1105 1101 1109 \n"
        evolverScript += "1106 1104 1110 \n"
        evolverScript += "1107 1109 1110 constraints 1008 1108 \n"
        evolverScript += "1109 1106 1102 \n"
        evolverScript += "1111 1107 1103 \n"
        evolverScript += "1112 1106 1107 constraints 1012 1112 \n"
        evolverScript += "1114 1108 1105 constraints 1012 1008 \n"
        evolverScript += "1108 1109 1106 constraints 1010 1110 \n"
        evolverScript += "1115 1105 1106 constraints 1012 1010 \n"
        evolverScript += "1116 1105 1109 constraints 1008 1010 \n"
        evolverScript += "1110 1110 1107 constraints 1009 1109 \n"
        evolverScript += "1113 1107 1108 constraints 1012 1009  \n"
        evolverScript += "1117 1108 1110 constraints 1008 1009  \n"
        evolverScript += "faces\n"
        evolverScript += "// left pad\n"
        evolverScript += "/*\n"
        evolverScript += "1 -4 -3 -2 -1 color red fixed no_refine\n"
        evolverScript += "2 5 6 7 8 color red fixed no_refine\n"
        evolverScript += "3 1 10 -5 -9 color red fixed no_refine\n"
        evolverScript += "4 2 11 -6 -10 color red fixed no_refine\n"
        evolverScript += "5 3 12 -7 -11 color red fixed no_refine\n"
        evolverScript += "6 4 9 -8 -12 color red fixed no_refine\n"
        evolverScript += "// left finish\n" 
        evolverScript += "7 -16 -15 -14 -13 color lightred fixed no_refine\n"
        evolverScript += "8 17 18 19 20 color lightred fixed no_refine\n"
        evolverScript += "9 13 22 -17 -21 color lightred fixed no_refine\n"
        evolverScript += "10 14 23 -18 -22 color lightred fixed no_refine\n"
        evolverScript += "11 15 24 -19 -23 color lightred fixed no_refine\n"
        evolverScript += "12 16 21 -20 -24 color lightred fixed no_refine\n"
        evolverScript += "// right pad\n"
        evolverScript += "1001 1001 1002 1003 1004 color red fixed no_refine\n"
        evolverScript += "1002 -1008 -1007 -1006 -1005 color red fixed no_refine\n"
        evolverScript += "1003 1009 1005 -1010 -1001 color red fixed no_refine\n"
        evolverScript += "1004 1010 1006 -1011 -1002 color red fixed no_refine\n"
        evolverScript += "1005 1011 1007 -1012 -1003 color red fixed no_refine\n"
        evolverScript += "1006 1012 1008 -1009 -1004 color red fixed no_refine\n"
        evolverScript += "// right finish\n"
        evolverScript += "1007 1013 1014 1015 1016 color lightred fixed no_refine\n"
        evolverScript += "1008 -1020 -1019 -1018 -1017 color lightred fixed no_refine\n"
        evolverScript += "1009 1021 1017 -1022 -1013 color lightred fixed no_refine\n"
        evolverScript += "1010 1022 1018 -1023 -1014 color lightred fixed no_refine\n"
        evolverScript += "1011 1023 1019 -1024 -1015 color lightred fixed no_refine\n"
        evolverScript += "1012 1024 1020 -1021 -1016 color lightred fixed no_refine\n"
        evolverScript += "*/\n"
        if direction == "left":
            evolverScript += "//left solder \n"
            evolverScript += "// 밑면 \n"
            evolverScript += "101 -104 -103 -102 -101 color blue constraints 5 105 \n"
            evolverScript += "// 좌측면\n"
            evolverScript += "102 104 105 107 -106 color blue constraints 107\n"
            evolverScript += "103 -105 101 -109 -108 color blue\n"
            evolverScript += "104 106 110 111 103 color blue \n"
            evolverScript += "105 -112 109 102 -111 color red constraints 12 112\n"
            evolverScript += "//측면 하단\n"
            evolverScript += "106 108 -115 116 color blue constraints 10 110 \n"
            evolverScript += "//측면 상단\n"
            evolverScript += "107 -117 -113 -110 color blue constraints 9 109\n"
            evolverScript += "//내부 수직면\n"
            evolverScript += "108 -116 -114 117 -107 color blue constraints 8 108\n"
            evolverScript += "109 115 112 113 114 color blue constraints 12 112\n"
        elif direction == "right":
            evolverScript += "//right solder \n"
            evolverScript += "// 밑면 \n"
            evolverScript += "1101 1101 1102 1103 1104 color blue constraints 1005 1105 \n"
            evolverScript += "// 좌측면\n"
            evolverScript += "1102 1106 -1107 -1105 -1104 color blue constraints 1107\n"
            evolverScript += "1103 1108 1109 -1101 1105 color blue\n"
            evolverScript += "1104 -1103 -1111 -1110 -1106 color blue \n"
            evolverScript += "1105 1111 -1102 -1109 1112 color red constraints 1012 1112\n"
            evolverScript += "//측면 하단\n"
            evolverScript += "1106 -1116 1115 -1108 color blue constraints 1010 1110 \n"
            evolverScript += "//측면 상단\n"
            evolverScript += "1107 1110 1113 1117 color blue constraints 1009 1109\n"
            evolverScript += "//내부 수직면\n"
            evolverScript += "1108 1107 -1117 1114 1116 color blue constraints 1008 1108\n"
            evolverScript += "1109 -1114 -1113 -1112 -1115 color blue constraints 1012 1112\n"
        
        evolverScript += "bodies\n"
        if direction == "left":
            evolverScript += "3 101 102 103 104 105 106 107 108 109 volume v1\n"
        elif direction == "right":
            evolverScript += "4 1101 1102 1103 1104 1105 1106 1107 1108 1109 volume v2\n"
        evolverScript += "read\n"
        evolverScript += "//typical evolution\n"
        evolverScript += """gogo :={{ r; g 15; r; g10;\n"""
        evolverScript += "conj_grad;\n"
        evolverScript += "t 10;\n"
        evolverScript += "u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;\n"
        evolverScript += "t 10;\n"
        evolverScript += "u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;\n"
        evolverScript += "}}\n"
        evolverScript += "gogo\n"
        evolverScript += "t 10;\n"
        evolverScript += "u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;\n"
        evolverScript += "g 10;\n"
        evolverScript += "optimize 1\n"
        evolverScript += "read \"stl.cmd\"\n"
        evolverScript += "stl >>> \"{stlFileName}\"\n"
        evolverScript += "q\n"
        evolverScript += "q\n"
        return evolverScript.format(stlFileName = fileName,
                                    lpw = self.lpw, 
                                    lph = self.lph,
                                    pt = self.pt,
                                    piw = self.piw,
                                    rpw = self.rpw,
                                    rph = self.rph,
                                    cbw = self.cbw,
                                    cbh = self.cbh,
                                    cbt = self.cbt,
                                    ltw = self.ltw,
                                    ltt = self.ltt,
                                    rtw = self.rtw,
                                    rtt = self.rtt,
                                    lbw = self.lbw,
                                    lbt = self.lbt,
                                    rbw = self.rbw,
                                    rbt = self.rbt,
                                    lfw = self.lfw,
                                    lft = self.lft,
                                    rfw = self.rfw,
                                    rft = self.rft,
                                    lst = self.lst,
                                    lsv = self.lsv,
                                    rsv = self.rsv,
                                    solderWidthRatio = solderWidthRatio,
                                    solderThicknessRatio = solderThicknessRatio,
                                    solderBottomWidthRatio = solderBottomWidthRatio,
                                    tens=tens,
                                    SG=SG,
                                    tilt=tilt)
    def MakeLeftSolder(self,folderPath):
        fileName = "leftSolder.stl"
        script = self.MakeSolderScript(fileName, "left", self.tens, self.solderWidthRatio, self.solderThicknessRatio, self.solderBottomWidthRatio, self.sgValue, self.tilt)
        if sys.platform.startswith("win"):
            evolverExe = os.path.join(folderPath, "Library", "Evolver", "evolver64.exe")
        else:
            evolverExe = self._find_linux_evolver(folderPath)
        scriptName = os.path.join(folderPath, "Library", "Evolver", "tmpScript.txt")
        cwd = os.path.join(folderPath, "Library", "Evolver")
        with open(scriptName, "w") as f:
            f.write(script)
        
        result = subprocess.run([evolverExe,"tmpScript.txt"],cwd=cwd, stdout=subprocess.PIPE)

        fileNameOutput = fileName.replace(".stl",".step")
        filePath = os.path.join(cwd,fileName)
        filePathOutput = os.path.join(folderPath,fileNameOutput)
        leftSolder = convertCAD.ConvertStltoStep(filePath,filePathOutput)
        '''
        trsf = gp_Trsf()
        pnt = gp_Pnt(0,0,0)
        dir = gp_Dir(0,1,1)
        axis = gp_Ax1(pnt,dir)
        trsf.SetMirror(axis)
        transformed_shape = BRepBuilderAPI.BRepBuilderAPI_Transform(leftSolder,trsf).Shape()
        '''
        if __name__ == "__main__":
            display.DisplayShape(leftSolder,None,None)
        return leftSolder
    
    def MakeRightSolder(self,folderPath):
        fileName = "rightSolder.stl"
        script = self.MakeSolderScript(fileName, "right", self.tens, self.solderWidthRatio, self.solderThicknessRatio, self.solderBottomWidthRatio, self.sgValue, self.tilt)
        if sys.platform.startswith("win"):
            evolverExe = os.path.join(folderPath, "Library", "Evolver", "evolver64.exe")
        else:
            evolverExe = self._find_linux_evolver(folderPath)
        scriptName = os.path.join(folderPath, "Library", "Evolver", "tmpScript.txt")
        cwd = os.path.join(folderPath, "Library", "Evolver")
        with open(scriptName, "w") as f:
            f.write(script)
        
        result = subprocess.run([evolverExe,"tmpScript.txt"],cwd=cwd, stdout=subprocess.PIPE)
   
        fileNameOutput = fileName.replace(".stl",".step")
        filePath = os.path.join(cwd,fileName)
        filePathOutput = os.path.join(folderPath,fileNameOutput)
        rightSolder = convertCAD.ConvertStltoStep(filePath,filePathOutput)
        '''trsf = gp_Trsf()
        pn = gp_Pnt(0,0,0)
        dir = gp_Dir(0,1,1)
        axis = gp_Ax1(pn,dir)
        trsf.SetMirror(axis)
        
        transformed_shape = BRepBuilderAPI.BRepBuilderAPI_Transform(rightSolder,trsf).Shape()
        '''
        if __name__ == "__main__":
            display.DisplayShape(rightSolder,None,None)
        return rightSolder
    
    def MakeMLCCShape(self,compound, detailMode = False):
        builder = BRep_Builder()
        lp = self.MakeLeftPad()
        rp = self.MakeRightPad()
        if detailMode: 
            cd,ce = self.MakeCeramicBodyDetail()
        else:
            cd = None
            ce = None 
        cb = self.MakeCeramicBody()
        lt = self.MakeLeftTerminal()
        rt = self.MakeRightTerminal()
        lb = self.MakeLeftBarrier()
        rb = self.MakeRightBarrier()
        lf = self.MakeLeftFinish()
        rf = self.MakeRightFinish()

        builder.Add(compound,lp.Shape())
        builder.Add(compound,rp.Shape())
        
        self.shapePads = [lp.Shape(),rp.Shape()]
        if detailMode:
            #combine compound and TopoDSCompound cd             
            builder.Add(compound,cd)
            builder.Add(compound,ce)
        else:
            builder.Add(compound,cb.Shape())

        clt = BRepAlgoAPI_Cut(lt.Shape(),cb.Shape())
        crt = BRepAlgoAPI_Cut(rt.Shape(),cb.Shape())
        builder.Add(compound,clt.Shape())
        builder.Add(compound,crt.Shape())
        
        self.shapeTerminals = [clt.Shape(),crt.Shape()]

        clb = BRepAlgoAPI_Cut(lb.Shape(),cb.Shape())
        crb = BRepAlgoAPI_Cut(rb.Shape(),cb.Shape())
        clb =   BRepAlgoAPI_Cut(clb.Shape(),lt.Shape())
        crb =   BRepAlgoAPI_Cut(crb.Shape(),rt.Shape())
        builder.Add(compound,clb.Shape())
        builder.Add(compound,crb.Shape())
        
        self.shapeBarriers = [clb.Shape(),crb.Shape()]

        clf = BRepAlgoAPI_Cut(lf.Shape(),cb.Shape())
        crf = BRepAlgoAPI_Cut(rf.Shape(),cb.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lt.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rt.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lb.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rb.Shape())
        builder.Add(compound,clf.Shape())
        builder.Add(compound,crf.Shape())
        self.shapeFinishes = [clf.Shape(),crf.Shape()]
        self.shapeCeramicBody = [cb.Shape()]
        self.shapeElectrodes = [ce]
        self.shapeDielectrics = [cd]
        
        self.compound = compound
        return compound, cd, ce 

    def GetCompound(self, detailMode = False):
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        shapeLeft = self.MakeLeftSolder("")
        builder.Add(compound,shapeLeft)
        shapeRight = self.MakeRightSolder("")
        builder.Add(compound,shapeRight)
        self.shapeSolders = [shapeLeft,shapeRight]
        compound, cd, ce = self.MakeMLCCShape(compound,detailMode)
        
        return compound

    def GetShapes(self):
        compound = self.GetCompound()
        shapes = []
        for i in range(1,compound.NbShapes()+1):
            shapes.append(compound.Shape(i))
        return shapes
    
    def WriteCapFile(self,MLCCFileName,detailMode = False, folderPath=""):
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        shapeLeft = self.MakeLeftSolder(folderPath)
        builder.Add(compound,shapeLeft)
        shapeRight = self.MakeRightSolder(folderPath)
        builder.Add(compound,shapeRight)
        self.shapeSolders = [shapeLeft,shapeRight]
        compound, cd, ce = self.MakeMLCCShape(compound,detailMode)
        
        # Assuming you have a compound named 'my_compound' and a scaling factor of 1000
        scaling_factor = 0.001
        # Create a scaling transformation
        scaling_transform = gp_Trsf()
        scaling_transform.SetScale(gp_Pnt(0, 0, 0), scaling_factor)

        # Apply the transformation to the compound
        transform_builder = BRepBuilderAPI_Transform(compound, scaling_transform)
        scaled_compound = transform_builder.Shape()

        self.compound = scaled_compound
        step_writer = STEPControl_Writer()
        step_writer.Transfer(scaled_compound,STEPControl_AsIs)
        if len(MLCCFileName) == 0:
            MLCCFileName = self.name
            if detailMode == True:
                MLCCFileName += "_detail"
            else:
                MLCCFileName += "_simple"
            MLCCFileName += ".step"
        step_writer.Write(MLCCFileName)

        cdName = MLCCFileName.replace(".step","_cd.step")
        ceName = MLCCFileName.replace(".step","_ce.step")
        if detailMode:
            transform_builder_cd = BRepBuilderAPI_Transform(cd, scaling_transform)
            scaled_cd = transform_builder_cd.Shape()
            step_writer_cd = STEPControl_Writer()
            step_writer_cd.Transfer(scaled_cd,STEPControl_AsIs)
            step_writer_cd.Write(cdName)
            transform_builder_ce = BRepBuilderAPI_Transform(ce, scaling_transform)
            scaled_ce = transform_builder_ce.Shape()
            step_writer_ce = STEPControl_Writer()
            step_writer_ce.Transfer(scaled_ce,STEPControl_AsIs)
            step_writer_ce.Write(ceName)                                        
                                    

    def Set0402(self):
        xValue = 400 
        yValue = 200
        zValue = 200 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set0603(self):
        xValue = 600 
        yValue = 300
        zValue = 300 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set0805(self):
        xValue = 800 
        yValue = 500
        zValue = 500 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1206(self):
        xValue = 1200 
        yValue = 600
        zValue = 600 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1005(self):
        xValue = 1000 
        yValue = 500
        zValue = 500 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1210(self):
        xValue = 1200 
        yValue = 1000
        zValue = 600 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1806(self):
        xValue = 1800 
        yValue = 600
        zValue = 600 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1812(self):
        xValue = 1800 
        yValue = 1200
        zValue = 1200 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1825(self):
        xValue = 1800 
        yValue = 2500
        zValue = 2500 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set2220(self):
        xValue = 2200 
        yValue = 2000
        zValue = 2000 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set2225(self):
        xValue = 2200 
        yValue = 2500
        zValue = 2500 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set3640(self):
        xValue = 3600 
        yValue = 4000
        zValue = 4000 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def SetXXYY(self,XX,YY):
        xValue = XX*100
        yValue = YY*100
        zValue = yValue
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
        
    def SetCapSizebyXYZ(self, xValue, yValue, zValue):
        self.lpw = xValue*3.0/5.0
        self.lph = xValue*4.0/5.0
        self.rpw = xValue*3.0/5.0
        self.rph = xValue*4.0/5.0
        self.piw = xValue/4.0
        self.pt = 30.0
        self.cbw = xValue
        self.cbh = yValue
        self.cbt = zValue
        self.ltw = xValue/8.0
        self.ltt = 10.0
        self.rtw = xValue/8.0
        self.rtt = 10.0
        self.lbw = 20.0
        self.lbt = 10.0
        self.rbw = 20.0
        self.rbt = 10.0
        self.lfw = 20.0
        self.lft = 10.0
        self.rfw = 20.0
        self.rft = 10.0
        self.lst = 30.0
        self.lsv = math.pow(xValue*yValue*zValue,1./3.0)/3 *0.0002
        self.rst = self.lst
        self.rsv = self.lsv
        pass  
      
    def GetCombinedTransform(self):
        rotation = self.rotation
        mirror = self.mirror
        originX = self.xOrigin
        originY = self.yOrigin
        originZ = self.zOrigin
        totalThickness = self.totalThickness
        isTop = self.isTop
         
        trsf = gp_Trsf()
        axZ = gp_Ax1(gp_Pnt(0.0,0.0,0.0),gp_Dir(0.0,0.0,1.0))
        trsf.SetRotation(axZ,-rotation*3.141592/180.0)
        trsf2 = gp_Trsf()    

        if rotation == 90 or rotation == 270:
            if mirror:
                trsf2.SetMirror(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(0,1,0)))
        else:
            if mirror:
                trsf2.SetMirror(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(1,0,0)))               
        trsf3 = gp_Trsf()
        if isTop:
            trsf3.SetTranslation(gp_Vec(originX,originY,originZ))
        else:
            trsf3.SetTranslation(gp_Vec(originX,originY,originZ-totalThickness))
        
        trsf4 = gp_Trsf()
        if isTop == False:
            trsf4.SetMirror(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(0,0,1)))
            
        combinedTrsf = trsf.Multiplied(trsf2)
        combinedTrsf = combinedTrsf.Multiplied(trsf4)
        combinedTrsf = combinedTrsf.Multiplied(trsf3)
        return combinedTrsf
    

    def GenerateMesh(self, detailMode = False, partManager : KooPartManager = None):
        self.GeneratePadMesh()
        self.GenerateFinishMesh()
        self.GenerateBarrierMesh()
        self.GenerateTerminalMesh()
        self.GenerateSolderMesh()        
        if detailMode == False:
            self.GenerateCeramicBodyMesh()
        
            
            
            
        self.CreatePartsforPackage(partManager, detailMode)
        self.CombineNodeManager()
        
        if detailMode == True:
            self.GenerateElectrodeDielectricMesh()

    def GeneratePadMesh(self):
        matMan = self.materialManager
        secMan = self.sectionManager
        nodeSetMan = self.nodeSetManager
        
        for i in range(2):
            meshManager = KooMeshManagerGMSH(materialMan=matMan, sectionMan=secMan, nodeSetMan=nodeSetMan)
            meshManager.SetPath(self.meshPath)
            if i == 0:
                meshManager.SetName("LeftPadMesh")
            elif i == 1:
                meshManager.SetName("RightPadMesh")
                
            meshManager.mesh_shape(self.shapePads[i],self.meshSize, self.meshSize, 3, None, self.maxNID, self.maxEID)
            
            self.maxPID = self.maxPID + 1
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetMaterialID(self.midPad)
            self.meshPads.append(meshManager)
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
    
            
    
    def GenerateBarrierMesh(self):
        matMan = self.materialManager
        secMan = self.sectionManager
        nodeSetMan = self.nodeSetManager
        
        for i in range(2):
            meshManager = KooMeshManagerGMSH(materialMan=matMan, sectionMan=secMan, nodeSetMan=nodeSetMan)
            meshManager.SetPath(self.meshPath)
            if i == 0:
                meshManager.SetName("LeftBarrierMesh")
            elif i == 1:
                meshManager.SetName("RightBarrierMesh")
            
            meshManager.mesh_shape(self.shapeBarriers[i],self.meshSize, self.meshSize, 3, None, self.maxNID, self.maxEID)
            
            self.maxPID = self.maxPID + 1
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetMaterialID(self.midBarrier)
            self.meshBarriers.append(meshManager)
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
            
    def GenerateTerminalMesh(self):
        matMan = self.materialManager
        secMan = self.sectionManager
        nodeSetMan = self.nodeSetManager
        
        for i in range(2):
            meshManager = KooMeshManagerGMSH(materialMan=matMan, sectionMan=secMan, nodeSetMan=nodeSetMan)
            meshManager.SetPath(self.meshPath)
            if i == 0:
                meshManager.SetName("LeftTerminalMesh")
            elif i == 1:
                meshManager.SetName("RightTerminalMesh")
                
            meshManager.mesh_shape(self.shapeTerminals[i],self.meshSize, self.meshSize, 3, None, self.maxNID, self.maxEID)
            
            self.maxPID = self.maxPID + 1
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetMaterialID(self.midTerminal)
            self.meshTerminals.append(meshManager)            
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
    
    def GenerateFinishMesh(self):
        matMan = self.materialManager
        secMan = self.sectionManager
        nodeSetMan = self.nodeSetManager
        
        for i in range(2):
            meshManager = KooMeshManagerGMSH(materialMan=matMan, sectionMan=secMan, nodeSetMan=nodeSetMan)
            meshManager.SetPath(self.meshPath)
            if i == 0:
                meshManager.SetName("LeftFinishMesh")
            elif i == 1:
                meshManager.SetName("RightFinishMesh")
                
            meshManager.mesh_shape(self.shapeFinishes[i],self.meshSize, self.meshSize, 3, None, self.maxNID, self.maxEID)
            
            self.maxPID = self.maxPID + 1
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetMaterialID(self.midFinish)
            self.meshFinishes.append(meshManager)
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
    
    def GenerateSolderMesh(self):
        matMan = self.materialManager
        secMan = self.sectionManager
        nodeSetMan = self.nodeSetManager
        
        for i in range(2):
            meshManager = KooMeshManagerGMSH(materialMan=matMan, sectionMan=secMan, nodeSetMan=nodeSetMan)
            meshManager.SetPath(self.meshPath)
            if i == 0:
                meshManager.SetName("LeftSolderMesh")
            elif i == 1:
                meshManager.SetName("RightSolderMesh")
                
            meshManager.mesh_shape(self.shapeSolders[i],self.meshSize, self.meshSize, 3, None, self.maxNID, self.maxEID)
            
            self.maxPID = self.maxPID + 1
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetMaterialID(self.midSolder)            
            self.meshSolders.append(meshManager)
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
    
    def GenerateCeramicBodyMesh(self):
        matMan = self.materialManager
        secMan = self.sectionManager
        nodeSetMan = self.nodeSetManager
        
        for i in range(1):
            meshManager = KooMeshManagerGMSH(materialMan=matMan, sectionMan=secMan, nodeSetMan=nodeSetMan)
            meshManager.SetPath(self.meshPath)
            meshManager.SetName("CeramicBodyMesh")
            
            meshManager.mesh_shape(self.shapeCeramicBody[i],self.meshSizeBody, self.meshSizeBody, 3, None, self.maxNID, self.maxEID)
            
            self.maxPID = self.maxPID + 1
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetMaterialID(self.midCeramicBody)
            self.meshCeramicBody.append(meshManager)
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()

    def GenerateElectrodeDielectricMesh(self):
        print("Generate Detail MLCC Mesh")
        matMan : KooMaterialManager = self.materialManager
        secMan : KooSectionManager = self.sectionManager
        nodeSetMan : NodeSetManager = self.nodeSetManager
        nodeMan : NodeManager = self.nodeManager
        partMan : KooPartManager = self.partMan
        defineMan : KooDefineManager = self.defineManager
        elementManDielectric : ElementManager = ElementManager(nodeMan)
        elementManElectrode : ElementManager = ElementManager(nodeMan)
        
        boundaryNodeMan : KooBoundaryNodeManager = self.boundaryNodeManager
        
        if self.midElectrode in matMan.materials:
            materialElectrode = matMan.materials[self.midElectrode]
        else:
            materialElectrode = None 
        if self.midDielectric in matMan.materials:
            materialDielectric = matMan.materials[self.midDielectric]
        else:
            materialDielectric = None
            
        sectionElectrode = secMan.CreateSolidSection("ElectrodeSection")
        sectionDielectric = secMan.CreateSolidSection("DielectricSection")
        
        partDielectric : KooPart = KooPart(nodeMan, elementManDielectric, materialDielectric, sectionDielectric, nodeSetMan)
        partElectrode : KooPart = KooPart(nodeMan, elementManElectrode, materialElectrode, sectionElectrode, nodeSetMan)
        
        partDielectric = partMan.CreatePartfromKooPart(partDielectric)
        partElectrode = partMan.CreatePartfromKooPart(partElectrode)
        
        nodeSet0V = nodeSetMan.CreateNodeSet("0V")
        nodeSetxV = nodeSetMan.CreateNodeSet("xV")
        
        if self.leftVoltage is not None:
            boundary0V = boundaryNodeMan.CreatePZEPOT(nodeSet0V.sid,0,self.leftVoltage)
        if self.rightVoltage is not None:
            boundaryxV = boundaryNodeMan.CreatePZEPOT(nodeSetxV.sid,0,self.rightVoltage)
        
        if self.leftVoltageCurve is not None:
            A1 = []
            O1 = [] 
            for i in range(len(self.leftVoltageCurve)):
                A1.append(self.leftVoltageCurve[i][0])
                O1.append(self.leftVoltageCurve[i][1])
            leftCurve = defineMan.CreateDefineCurve(0,1.0,1.0,0,0,0,0,A1,O1)
            lcid = leftCurve.lcid
            if self.leftVoltage is not None:
                boundary0V = boundaryNodeMan.CreatePZEPOT(nodeSet0V.sid,lcid,self.leftVoltage)
            else:
                boundary0V = boundaryNodeMan.CreatePZEPOT(nodeSet0V.sid,lcid,1.0)
            
        if self.rightVoltageCurve is not None:
            A1 = []
            O1 = [] 
            for i in range(len(self.rightVoltageCurve)):
                A1.append(self.rightVoltageCurve[i][0])
                O1.append(self.rightVoltageCurve[i][1])
            rightCurve = defineMan.CreateDefineCurve(0,1.0,1.0,0,0,0,0,A1,O1)
            lcid = rightCurve.lcid
            if self.rightVoltage is not None:
                boundaryxV = boundaryNodeMan.CreatePZEPOT(nodeSetxV.sid,lcid,self.rightVoltage)
            else:
                boundaryxV = boundaryNodeMan.CreatePZEPOT(nodeSetxV.sid,lcid,1.0)
            
        
        maxEID = 0 
        for id in partMan.parts:
            curPart = partMan.parts[id]
            maxEID = max(maxEID, curPart.elementManager.GetMaxID())
        self.maxEID = maxEID
        elementManDielectric.SetMaxID(self.maxEID)
        elementManElectrode.SetMaxID(self.maxEID)
        if materialElectrode == None:
            partElectrode.mid = self.midElectrode
        if materialDielectric == None:
            partDielectric.mid = self.midDielectric
        L = self.cbw
        W = self.cbh
        H = self.cbt
        ldi = self.ldi
        Ndi = self.Ndi
        tdi = self.tdi
        tel = self.tel
        H = tel*(Ndi+1) + Ndi*tdi
        Nel = Ndi + 1
        Ldi = L - ldi
        
        nodeList = [] 
        numElemLdi = self.numberofElementinX
        numElemldi = self.numberofElementinX * (ldi/Ldi)
        # 반올림
        numElemldi = round(numElemldi)
        numElemY = self.numberofElementinY
        numElemZ = self.numberofElementinZ
        xList = [] 
        yList = [] 
        zList = []
        xCurrent = -L/2.0
        xList.append(xCurrent) 
        for i in range(1, numElemldi + 1):
            xCurrent = xCurrent + ldi/(numElemldi)
            xList.append(xCurrent)
        for i in range(1, numElemLdi + 1):
            xCurrent = xCurrent + (L-2.0*ldi)/(numElemLdi)
            xList.append(xCurrent)
        for i in range(1, numElemldi + 1):
            xCurrent = xCurrent + ldi/(numElemldi)
            xList.append(xCurrent)
            
        for i in range(numElemY + 1):
            yList.append(-W/2.0 + i*W/(numElemY))
        zCurrent = self.GetTotalThickness()
        zList.append(zCurrent)
        for i in range(0,Nel,2):
            for j in range(1, numElemZ + 1):
                zCurrent = zCurrent + tel/(numElemZ)
                zList.append(zCurrent)
            for j in range(1, numElemZ + 1):
                zCurrent = zCurrent + tdi/(numElemZ)
                zList.append(zCurrent)
            for j in range(1, numElemZ + 1):
                zCurrent = zCurrent + tel/(numElemZ)
                zList.append(zCurrent)
            for j in range(1, numElemZ + 1):
                zCurrent = zCurrent + tdi/(numElemZ)
                zList.append(zCurrent)
                
        numX = len(xList)
        numY = len(yList)
        numZ = len(zList)
        nodeTensor = []
        for k in range(numZ):
            curZLayerLoc = k % (4*numElemZ)
            curZLayer = curZLayerLoc // numElemZ
            curZLayerLocNodePos = curZLayerLoc % numElemZ
            nodeMap = [] 
            for j in range(numY):
                nodeVec = []
                for i in range(numX):
                    node = nodeMan.CreateNode(xList[i],yList[j],zList[k])
                    
                    if curZLayer == 0:       
                        if k == numZ - 1:
                            pass                 
                        elif i == numElemldi:
                            nodeSetxV.AddNode(node)                        
                        elif i != 0:
                            if curZLayerLocNodePos == 0:
                                if i >= numElemldi:
                                    nodeSetxV.AddNode(node)
                        
                    if curZLayer == 1:
                        if curZLayerLocNodePos == 0:
                            if i >= numElemldi:
                                nodeSetxV.AddNode(node)
                    
                    if curZLayer == 2:
                        if curZLayerLocNodePos == 0:
                            if i <= numElemldi + numElemLdi:
                                nodeSet0V.AddNode(node)
                        else:
                            if i == numElemldi + numElemLdi:
                                nodeSet0V.AddNode(node)
                    if curZLayer == 3:
                        if curZLayerLocNodePos == 0:
                            if i <= numElemldi + numElemLdi:
                                nodeSet0V.AddNode(node)
                                                            
                    nodeVec.append(node)
                nodeMap.append(nodeVec)
            nodeTensor.append(nodeMap)
        
        for k in range(numZ - 1):
            curZLayerLoc = k % (4*numElemZ)
            curZLayer = curZLayerLoc // numElemZ
            for i in range(numX - 1):
                if i < numElemldi:
                    curXLayer = 0 
                elif i >= numElemldi and i < numElemldi + numElemLdi:
                    curXLayer = 1
                else:
                    curXLayer = 2
                
                if curZLayer == 1 or curZLayer == 3:
                    curPart = partDielectric
                elif curZLayer == 0:
                    if curXLayer == 0:
                        curPart = partDielectric
                    else:
                        curPart = partElectrode
                elif curZLayer == 2:
                    if curXLayer == 2:
                        curPart = partDielectric
                    else:
                        curPart = partElectrode
                elemMan = curPart.elementManager
                for j in range(numY - 1):
                    
                    node1 = nodeTensor[k][j][i]
                    node2 = nodeTensor[k][j][i+1]
                    node3 = nodeTensor[k][j+1][i+1]
                    node4 = nodeTensor[k][j+1][i]
                    node5 = nodeTensor[k+1][j][i]
                    node6 = nodeTensor[k+1][j][i+1]
                    node7 = nodeTensor[k+1][j+1][i+1]
                    node8 = nodeTensor[k+1][j+1][i]
                    elem = elemMan.CreateHexahedronLinearElement(node1,node2,node3,node4,node5,node6,node7,node8)                       
                    elemid = elem.id
                    elementManDielectric.SetMaxID(elemid)
                    elementManElectrode.SetMaxID(elemid)
        print("Finish Generate Detail MLCC Mesh")
        
    def CreatePartsforPackage(self, partMan : KooPartManager = None, detailMode = False):
        if partMan == None:
            partMan : KooPartManager = KooPartManager()
        
        maxPartID = partMan.maxID
            
        for meshManager in self.meshPads:
            curpid = maxPartID + meshManager.part.id
            partMan.AddPartfromKooPart(curpid, meshManager.part)
            maxPartID = partMan.maxID
        for meshManager in self.meshBarriers:
            curpid = maxPartID + meshManager.part.id
            partMan.AddPartfromKooPart(curpid, meshManager.part)
            maxPartID = partMan.maxID
        for meshManager in self.meshTerminals:
            curpid = maxPartID + meshManager.part.id
            partMan.AddPartfromKooPart(curpid, meshManager.part)
            maxPartID = partMan.maxID
        for meshManager in self.meshFinishes:
            curpid = maxPartID + meshManager.part.id
            partMan.AddPartfromKooPart(curpid, meshManager.part)
            maxPartID = partMan.maxID
        for meshManager in self.meshSolders:
            curpid = maxPartID + meshManager.part.id
            partMan.AddPartfromKooPart(curpid, meshManager.part)
            maxPartID = partMan.maxID
        if detailMode == False:
            for meshManager in self.meshCeramicBody:
                curpid = maxPartID + meshManager.part.id
                partMan.AddPartfromKooPart(curpid, meshManager.part)
                maxPartID = partMan.maxID
                
        self.partMan = partMan 
        return partMan        
            
    
    def CombineNodeManager(self):
        self.nodeManager : NodeManager = NodeManager()
        for i in self.partMan.parts:
            part : KooPart = self.partMan.parts[i]
            self.nodeManager.AddNodesfromAnotherManager(part.nodeManager)
            # part의 node manager 통합 
            part.nodeManager = self.nodeManager
            part.elementManager.nodeManager = self.nodeManager

    def ExportDynaMesh(self, filePath):            
        with open(filePath, 'w') as f:
            f.write("*KEYWORD\n")
            if self.dynaAddScript != "":
                f.write(self.dynaAddScript)
            if self.nodeManager == None:
                self.CombineNodeManager()
            addString = self.nodeManager.WritetoDynaKeyword(0)
            f.write(addString)
                                                    
            for i in self.partMan.parts:
                part : KooPart = self.partMan.parts[i]
                addString = part.WritetoDynaPart()
                f.write(addString)
                addString = part.WritetoDynaElements(0,0)
                f.write(addString)                

            addString = self.partMan.elementManager.WritetoDynaKeyword(0,0,0)
            f.write(addString)
            for i in self.partMan.constrainedParts:
                part = self.partMan.constrainedParts[i]
                addString = part.WritetoDynaPart()
                f.write(addString)
            addString = self.defineManager.WritetoDynaKeyword(0)
            f.write(addString)                            
            addString = self.nodeSetManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.segmentManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.materialManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.sectionManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.boundaryNodeManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.loadManager.WritetoDynaKeyword(0)
            f.write(addString)
            addString = self.contactManager.WritetoDynaKeyword(0)
            f.write(addString)
            
            f.write("*END")
            f.close()
        pass   

class CapacitorManager():
    def __init__(self):
        self.maxid = 0
        self.capacitors = {}
        self.folderPath = ""
        self.dynaAddScript = ""
        
    def SetFolderPath(self, folderPath):
        self.folderPath = folderPath
    
    def AddCapacitorbySize(self,xLength,yLength,zLength,name = ""):
        self.maxid = self.maxid + 1
        if len(name) == 0:
            name = "Capacitor{0}".format(self.maxid)
            
        newCapacitor : Capacitor = Capacitor(self.maxid,name)
        newCapacitor.SetCapSizebyXYZ(xLength,yLength,zLength)
        self.capacitors[self.maxid] = newCapacitor
              
        return newCapacitor  
            
    def ImportCapacitor(self, filePath):
        f = open(filePath, 'r')
        line = f.readline()
        
        while True:
            if not line: break
            if line[0] == '#':
                line = f.readline()
                continue
            elif "**addscript" in line.lower():
                line = line.replace('\n','')
                svector = line.split(',')
                addOpt = "LSDyna"
                if len(svector) > 1:
                    addOpt = svector[1]
                    
                addScript = ""
                while True:
                    line = f.readline()
                    if not line: break
                    line = line.replace('\n','')
                    if "**endscript" in line.lower():
                        break
                    elif line[0] == "$":
                        continue
                    
                    addScript = addScript + line + "\n"
                if addOpt.lower() == "lsdyna":
                    self.dynaAddScript = addScript
                else:
                    print("AddScript Option is not supported")
                line = f.readline()
                
                
            elif line[0] == '*':
                line = line.replace('\n','')
                svector = line.split(',')
                if '*end' in svector[0].lower():
                    break
                elif '*capacitor' in svector[0].lower():
                    line = f.readline()
                    xLength = 0.0
                    yLength = 0.0
                    zLength = 0.0                    
                    # position information
                    xOrigin = 0.0
                    yOrigin = 0.0
                    zOrigin = 0.0
                    rotation = 0 
                    mirror = False 
                    isTop = True 
                    
                    # meshgenerawtion information
                    meshGenerationMode = False 
                    meshPath = ""
                    meshSize = 0.1                    
                    meshSizeSolder = 0.1
                    meshSizeBody = 0.1
                    numberofElementinX = 10
                    numberofElementinY = 5
                    numberofElementinZ = 3 
                    
                    
                    lpw = None
                    lph = None
                    rpw = None
                    rph = None
                    piw = None
                    pt = None
                    cbw = None
                    cbh = None
                    cbt = None
                    ltw = None
                    ltt = None
                    rtw = None
                    rtt = None
                    lbw = None
                    lbt = None
                    rbw = None
                    rbt = None
                    lfw = None
                    lft = None
                    rfw = None
                    rft = None
                    lst = None
                    lsv = None
                    rst = None
                    rsv = None
                    tens = None
                    solderWidthRatio = None
                    solderThicknessRatio = None
                    solderBottomWidthRatio = None
                    sgValue = None
                    tilt = None
                    Ndi = None
                    tdi = None
                    tel = None
                    epsilon = None
                    ldi = None
                    
                    matidPad = 1
                    matidTerminal = 2
                    matidBarrier = 3
                    matidFinish = 4
                    matidSolder = 5
                    matidDielectric = 6
                    matidElectrode = 7
                    matidCeramicBody = 8
                    DMat = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]] 
                    PXMat = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
                    PYMat = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
                    PZMat = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]

                    leftVoltageCurve = None
                    rightVoltageCurve = None
                    leftVoltageValue = None
                    rightVoltageValue = None
                
                        
                    if len(svector) >=2:
                        capName = svector[1]
                    else:
                        capName = ""
                    while True:
                        line = f.readline()
                        line = line.replace('\n','')
                        if not line : break
                        svector = line.split(',')
                        if svector[0][0] == '*':
                            print("Capacitor End")
                            break
                        elif svector[0][0] == '#':
                            continue
                        elif svector[0].lower() == "location":
                            xOrigin = float(svector[1])
                            yOrigin = float(svector[2])
                            zOrigin = float(svector[3])
                        elif svector[0].lower() == "translation":
                            xOrigin = float(svector[1])
                            yOrigin = float(svector[2])
                            zOrigin = float(svector[3])
                        elif svector[0].lower() == "rotation":
                            rotation = int(svector[1])
                        elif svector[0].lower() == "mirror":
                            if svector[1].lower() == "true":
                                mirror = True
                            else:
                                mirror = False
                        elif svector[0].lower() == "istop":
                            if svector[1].lower() == "true":
                                isTop = True
                            else:
                                isTop = False
                        elif svector[0].lower() == "meshpath":
                            meshPath = svector[1]
                        elif svector[0].lower() == "meshsize":
                            meshGenerationMode = True
                            meshSize = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "meshsizesolder":
                            meshGenerationMode = True 
                            meshSizeSolder = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "meshsizebody":
                            meshGenerationMode = True
                            meshSizeBody = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "numberofelementmlcc":
                            meshGenerationMode = True
                            numberofElementinX = int(svector[1])
                            numberofElementinY = int(svector[2])
                            numberofElementinZ = int(svector[3])                            
                        elif svector[0].lower() == "materialid":
                            curPos = svector[1]
                            if curPos.lower() == "pad":
                                matidPad = KooDynaInt(svector[2])
                            elif curPos.lower() == "terminal":
                                matidTerminal = KooDynaInt(svector[2])
                            elif curPos.lower() == "barrier":
                                matidBarrier = KooDynaInt(svector[2])
                            elif curPos.lower() == "finish":
                                matidFinish = KooDynaInt(svector[2])
                            elif curPos.lower() == "solder":
                                matidSolder = KooDynaInt(svector[2])
                            elif curPos.lower() == "dielectric":
                                matidDielectric = KooDynaInt(svector[2])    
                            elif curPos.lower() == "electrode":
                                matidElectrode = KooDynaInt(svector[2])
                            elif curPos.lower() == "ceramicbody":
                                matidCeramicBody = KooDynaInt(svector[2])
                        elif svector[0].lower() == "dxx":
                            DMat[0][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "dyy":
                            DMat[1][1] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "dzz":
                            DMat[2][2] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "dxy":
                            DMat[0][1] = KooDynaFloat(svector[1])
                            DMat[1][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "dxz":
                            DMat[0][2] = KooDynaFloat(svector[1])
                            DMat[2][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "dyz":
                            DMat[1][2] = KooDynaFloat(svector[1])
                            DMat[2][1] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "px11":
                            PXMat[0][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "px22":
                            PXMat[1][1] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "px33":
                            PXMat[2][2] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "px12":
                            PXMat[0][1] = KooDynaFloat(svector[1])
                            PXMat[1][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "px13":
                            PXMat[0][2] = KooDynaFloat(svector[1])
                            PXMat[2][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "px23":
                            PXMat[1][2] = KooDynaFloat(svector[1])
                            PXMat[2][1] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "py11":
                            PYMat[0][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "py22":
                            PYMat[1][1] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "py33":
                            PYMat[2][2] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "py12":
                            PYMat[0][1] = KooDynaFloat(svector[1])
                            PYMat[1][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "py13":
                            PYMat[0][2] = KooDynaFloat(svector[1])
                            PYMat[2][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "py23":
                            PYMat[1][2] = KooDynaFloat(svector[1])
                            PYMat[2][1] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "pz11":
                            PZMat[0][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "pz22":
                            PZMat[1][1] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "pz33":
                            PZMat[2][2] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "pz12":
                            PZMat[0][1] = KooDynaFloat(svector[1])
                            PZMat[1][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "pz13":
                            PZMat[0][2] = KooDynaFloat(svector[1])
                            PZMat[2][0] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "pz23":
                            PZMat[1][2] = KooDynaFloat(svector[1])
                            PZMat[2][1] = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "leftvoltagevalue":
                            leftVoltageValue = KooDynaFloat(svector[1])
                        elif svector[0].lower() == "rightvoltagevalue":
                            rightVoltageValue = KooDynaFloat(svector[1])  
                        elif "voltagecurve" in svector[0].lower(): 
                            mode = "right"
                            if "right" in svector[0].lower():
                                rightVoltageCurve = []
                            if "left" in svector[0].lower():
                                leftVoltageCurve = []
                                mode = "left"
                            while True: 
                                line = f.readline()
                                if not line: break
                                line = line.replace('\n','')
                                if "end" in line.lower():
                                    break
                                elif "#" in line:
                                    continue
                                elif "$" in line:
                                    continue
                                svector = line.split(',')
                                if len(svector) == 2:
                                    curTime = KooDynaFloat(svector[0])
                                    curVoltage = KooDynaFloat(svector[1])
                                    if "right" in mode:
                                        rightVoltageCurve.append([curTime,curVoltage])
                                    if "left" in mode:
                                        leftVoltageCurve.append([curTime,curVoltage])
                                                             
                        elif svector[0].lower() == "xsize":
                            xLength = float(svector[1])
                        elif svector[0].lower() == "ysize":
                            yLength = float(svector[1])
                            if zLength == 0.0:
                                zLength = float(svector[1])
                        elif svector[0].lower() == "zsize":
                            zLength = float(svector[1])
                        elif svector[0].lower() == "lpw":
                            lpw = float(svector[1])
                        elif svector[0].lower() == "lph":
                            lph = float(svector[1])
                        elif svector[0].lower() == "rpw":
                            rpw = float(svector[1])
                        elif svector[0].lower() == "rph":
                            rph = float(svector[1])
                        elif svector[0].lower() == "piw":
                            piw = float(svector[1])
                        elif svector[0].lower() == "pt":
                            pt = float(svector[1])
                        elif svector[0].lower() == "cbw":
                            cbw = float(svector[1])
                        elif svector[0].lower() == "cbh":
                            cbh = float(svector[1])
                        elif svector[0].lower() == "cbt":
                            cbt = float(svector[1])
                        elif svector[0].lower() == "ltw":
                            ltw = float(svector[1])
                        elif svector[0].lower() == "ltt":
                            ltt = float(svector[1])
                        elif svector[0].lower() == "rtw":
                            rtw = float(svector[1])
                        elif svector[0].lower() == "rtt":  
                            rtt = float(svector[1])
                        elif svector[0].lower() == "lbw":
                            lbw = float(svector[1])
                        elif svector[0].lower() == "lbt":
                            lbt = float(svector[1])
                        elif svector[0].lower() == "rbw":
                            rbw = float(svector[1])
                        elif svector[0].lower() == "rbt":
                            rbt = float(svector[1])
                        elif svector[0].lower() == "lfw":
                            lfw = float(svector[1])
                        elif svector[0].lower() == "lft":
                            lft = float(svector[1])
                        elif svector[0].lower() == "rfw":
                            rfw = float(svector[1])
                        elif svector[0].lower() == "rft":
                            rft = float(svector[1])
                        elif svector[0].lower() == "lst":
                            lst = float(svector[1])
                        elif svector[0].lower() == "lsv":
                            lsv = float(svector[1])
                        elif svector[0].lower() == "rst":
                            rst = float(svector[1])
                        elif svector[0].lower() == "rsv":
                            rsv = float(svector[1])
                        elif svector[0].lower() == "tens":
                            tens = float(svector[1])
                        elif svector[0].lower() == "swr":
                            solderWidthRatio = float(svector[1])
                        elif svector[0].lower() == "str":
                            solderThicknessRatio = float(svector[1])
                        elif svector[0].lower() == "sbr":
                            solderBottomWidthRatio = float(svector[1])
                        elif svector[0].lower() == "sg":
                            sgValue = float(svector[1])
                        elif svector[0].lower() == "tilt":
                            tilt = float(svector[1])   
                        elif svector[0].lower() == "ndi":
                            Ndi = int(svector[1])
                        elif svector[0].lower() == "tdi":
                            tdi = float(svector[1])
                        elif svector[0].lower() == "tel":
                            tel = float(svector[1])
                        elif svector[0].lower() == "epsilon":
                            epsilon = float(svector[1])
                        elif svector[0].lower() == "ldi":
                            ldi = float(svector[1])
                        else:   
                            print("Unknown Property {0}".format(svector[0]))                            
                                                     
                    
                    newCapacitor = self.AddCapacitorbySize(xLength,yLength,zLength,capName)
                    newCapacitor.xOrigin = xOrigin 
                    newCapacitor.yOrigin = yOrigin  
                    newCapacitor.zOrigin = zOrigin
                    newCapacitor.rotation = rotation
                    newCapacitor.mirror = mirror
                    newCapacitor.isTop = isTop
                    
                    newCapacitor.SetMeshPath(meshPath)
                    newCapacitor.SetMeshSize(meshSize)
                    newCapacitor.SetMeshSizeSolder(meshSizeSolder)
                    newCapacitor.SetMeshSizeBody(meshSizeBody)
                    newCapacitor.SetNumberofElementsforMLCC(numberofElementinX,numberofElementinY,numberofElementinZ)                    
                    newCapacitor.SetMaterialID(matidPad,matidBarrier,matidTerminal,matidFinish,matidSolder,matidDielectric,matidElectrode,matidCeramicBody)
                    newCapacitor.SetPiezoelectricMaterial(DMat, PXMat, PYMat, PZMat)
                    newCapacitor.SetProperties(lpw,lph,rpw,rph,piw,pt,cbw,cbh,cbt,ltw,ltt,rtw,rtt,lbw,lbt,rbw,rbt,lfw,lft,rfw,rft,lst,lsv,rst,rsv,tens,solderWidthRatio,solderThicknessRatio,solderBottomWidthRatio,sgValue,tilt,Ndi,tdi,tel,epsilon,ldi)
                    
                    newCapacitor.SetVoltageValue(leftVoltageValue,rightVoltageValue)
                    newCapacitor.SetVoltageCurve(leftVoltageCurve,rightVoltageCurve)
                    print("Imported {0} : (X,Y,Z)=({1},{2},{3})".format(newCapacitor.name,xLength,yLength,zLength))
                    
    def GenerateCapacitors(self, detailMode = True):
        
        for id in self.capacitors:
            curCap : Capacitor = self.capacitors[id]
            curCap.MakeMLCC(detailMode)
            print("Generated {0}".format(curCap.name))
            #if __name__ == "__main__":
            #    start_display()
    
    def ExportShapes(self, detailMode = True):
        folderPath = self.folderPath
        for id in self.capacitors:
            curCap : Capacitor = self.capacitors[id]
            curCap.WriteCapFile("",detailMode,folderPath)
            print("Exported {0}".format(curCap.name))
            
    def ExportMeshes(self,detailMode = True):
        folderPath = self.folderPath
        for id in self.capacitors:
            curCap : Capacitor = self.capacitors[id]
            curCap.SetDynaScript(self.dynaAddScript)
            curCap.GenerateMesh(detailMode, None)
            if detailMode == True:
                filePath = folderPath + "\\" + curCap.name + "_detail.k"
            else:
                filePath = folderPath + "\\" + curCap.name + "_simple.k"
            curCap.ExportDynaMesh(filePath)
            print("Exported {0}".format(curCap.name))
        print("Exported All Meshes")
            
    def GetShapebyID(self, id):
        curCap : Capacitor = self.capacitors[id]
        return curCap.GetShapes()
        



if __name__ =="__main__":
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd,"occProject\\Generators\\dist\\Capacitor"))
    curPath = os.getcwd()
    capMan = CapacitorManager()
    capMan.SetFolderPath(curPath)
    #capMan.ImportCapacitor("Cap0603Mesh.txt")
    #capMan.ImportCapacitor("Cap0603MeshSmall.txt")
    #capMan.ImportCapacitor("Cap0603MeshSmallPiezoMaterial.txt")
    capMan.ImportCapacitor("Cap0603MeshSmallPiezoMaterialVoltage.txt")

    capMan.GenerateCapacitors()
    capMan.ExportShapes()
    capMan.ExportMeshes()
    
    #cwd = os.getcwd()
    
    #capForm = Capacitor()
    #capForm.Set1005()
    #capForm.MakeMLCC(True)
    #capForm.WriteCapFile("MLCCTest.step",True,cwd)
    
    
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        pass
    else:        
        start_display()

