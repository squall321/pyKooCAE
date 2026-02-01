import sys 
import os
import cv2
import numpy as np
import math

getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")
if sys.platform.startswith("win"):
    # Windows 전용
    os.add_dll_directory(path)
else:
    # Linux/Unix 계열은 LD_LIBRARY_PATH에 넣으면 됨
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if path not in ld_path.split(":"):
        os.environ["LD_LIBRARY_PATH"] = path + ":" + ld_path
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf, gp_Ax1, gp_Pln
from OCC.Core.TColgp import TColgp_Array1OfPnt
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeOffset
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_WIRE, TopAbs_FACE, TopAbs_SOLID, TopAbs_COMPOUND
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.TopLoc import TopLoc_Location

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeSolid
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell,BRepOffsetAPI_MakeOffsetShape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCC.Core.Law import Law_Linear, Law_Constant
from OCC.Core.BRepFill import brepfill_Shell
from OCC.Core.TopoDS import TopoDS_Shell
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet, BRepFilletAPI_MakeChamfer
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.ChFi2d import ChFi2d_AnaFilletAlgo, ChFi2d_ChamferAPI, ChFi2d_Builder
from OCC.Extend.ShapeFactory import make_wire
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_EDGE

from OCC.Core.STEPControl import STEPControl_Reader

#from KooCAEManager.KooNode import NodeManager
#from KooODBCADManager.WarpageSurface import WarpageSurface

from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCC.Core.Extrema import Extrema_ExtAlgo_Tree
from OCC.Core.BRep import BRep_Tool_PolygonOnTriangulation
from OCC.Core.BRepFill import BRepFill_Filling
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
import random
import subprocess
from KooAnalysisWeb.Apps import ConvertCAD as convertCAD

from KooCAEManager.KooNode import NodeManager
from KooCAEManager.KooElement import ElementManager
from KooCAEManager.KooPart import KooPartManager
from KooCAEManager.KooSection import KooSectionManager
from KooCAEManager.KooMaterial import KooMaterialManager
from KooCAEManager.KooNode import NodeSetManager

from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH

if __name__ == "__main__":
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

class SolderJoint():
    def __init__(self, name, nodeMan : NodeManager = None, elementMan : ElementManager = None, partMan : KooPartManager = None, sectionMan : KooSectionManager = None, materialMan : KooMaterialManager = None, nodeSetMan : NodeSetManager = None, part = None):
        self.meshManager = KooMeshManagerGMSH(nodeMan=nodeMan, elementMan=elementMan, partMan=partMan, sectionMan=sectionMan, materialMan=materialMan, nodeSetMan=nodeSetMan, part=part)
        
        self.name = name
        self.folderPath = os.getcwd()
        if sys.platform.startswith("win"):
            self.evolverExe = ".\\Library\\Evolver\\evolver64.exe"
        else:
            self.evolverExe = self._find_linux_evolver(self.folderPath)
        self.scriptPath = os.path.join(".", "Library", "Evolver", "{fileName}")
        self.scriptName = "tmpScript.txt"
        self.stlFileName = "tmpScript.stl"
        self.script = None
        self.SetName(name)
        self.solder = None
        self.solderType = None
        

        self.S_TENSION = 4.8*1000.0
        self.SOLDER_DENSITY = 0.0090*100.0
        self.GRAVITY = 0.09810
        self.VOLUME = 0.0
        self.detailMode = False
        self.topPointLists = []
        self.bottomPointLists = []
        
        self.maxNID = 0
        self.maxEID = 0
        self.maxPID = 0
        self.maxMID = 0
        self.maxSID = 0
        self.maxNSID = 0 
        self.matID = -1
   
    def SetMaxIDs(self, maxNID, maxEID, maxPID, maxMID, maxSID, maxNSID):
        self.maxNID = maxNID
        self.maxEID = maxEID
        self.maxPID = maxPID
        self.maxMID = maxMID
        self.maxSID = maxSID
        self.maxNSID = maxNSID
        
    def GetMaxIDs(self):
        return self.maxNID, self.maxEID, self.maxPID, self.maxMID, self.maxSID, self.maxNSID
          
    
    def SetMaterialID(self, matID):
        self.matID = matID
    
    def SetDetailMode(self, mode):
        self.detailMode = mode
    
    def SetSurfaceTension(self, tension):
        self.S_TENSION = tension
    
    def SetSolderDensity(self, density):
        self.SOLDER_DENSITY = density
    
    def SetGravity(self, gravity):
        self.GRAVITY = gravity
            
    def SetVolume(self, volume):
        self.VOLUME = volume 
    
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

    def SetFolderPath(self, folderPath):
        self.folderPath = folderPath
        if sys.platform.startswith("win"):
            self.evolverExe = os.path.join(self.folderPath, "Library", "Evolver", "evolver64.exe")
        else:
            self.evolverExe = self._find_linux_evolver(self.folderPath)
        self.scriptPath = os.path.join(self.folderPath, "Library", "Evolver", "{fileName}")
    
    def SetName(self, name):
        self.scriptName = name + ".txt"
        self.stlFileName = self.name + ".stl"
        
    def GetHeightDifference(self, UpdateScript = True):
        if self.script is None or self.script == "":
            print("Script is None")
            return
        cwd = os.path.join(self.folderPath, "Library", "Evolver")
        with open(self.scriptPath.format(fileName=self.scriptName), "w") as f:
            f.write(self.script)
        heightOptimizedPath = filePathOptPath = os.path.join(cwd,"heightOptimized.txt")
        if os.path.exists(heightOptimizedPath):
            os.remove(heightOptimizedPath)
        
        result = subprocess.run([self.evolverExe, self.scriptName], cwd=cwd, stdout=subprocess.PIPE)
        fileNameOutput = self.stlFileName.replace(".stl", ".step")
        filePath = os.path.join(cwd, self.stlFileName)
        filePathOutput = os.path.join(self.folderPath, fileNameOutput)
        solder = convertCAD.ConvertStltoStep(filePath, filePathOutput)
        
        #remove stl, txt, step files
        os.remove(filePath)
        os.remove(self.scriptPath.format(fileName=self.scriptName))
        os.remove(filePathOutput)     
        if os.path.exists(heightOptimizedPath):
            with open(heightOptimizedPath, "r") as f:
                f.readline()
                f.readline()
                solderHeight = float(f.readline())
                f.readline()
                solderHeight2 = float(f.readline())
        else:
            solderHeight = 0.0        
            solderHeight2 = 0.0             
        return solderHeight2 - solderHeight
            
            
    
    def MakeSolder(self, UpdateScript = True):
                
        if self.script is None or self.script == "":
            print("Script is None")
            return
        cwd = os.path.join(self.folderPath, "Library", "Evolver")
        with open(self.scriptPath.format(fileName=self.scriptName), "w") as f:
            f.write(self.script)   
        fileNameOutput = self.stlFileName.replace(".stl", ".step")
        filePath = os.path.join(cwd, self.stlFileName)
        filePathOutput = os.path.join(self.folderPath, fileNameOutput)                 
        try:
            result = subprocess.run([self.evolverExe, self.scriptName], cwd=cwd, stdout=subprocess.PIPE, timeout=5) # wait for the process to terminate 10s
            
        except:
            print("Evolver Error")
                     
            return None
        
        try :
            solder = convertCAD.ConvertStltoStep(filePath, filePathOutput)
        except:
            print("Convert Error")
            # file이 있는지 확인 
            if os.path.exists(filePath):
                os.remove(filePath)
            if os.path.exists(self.scriptPath.format(fileName=self.scriptName)):
                os.remove(self.scriptPath.format(fileName=self.scriptName))
            if os.path.exists(filePathOutput):
                os.remove(filePathOutput)            
            return None 
            
        #remove stl, txt, step files
        if os.path.exists(filePath):
            os.remove(filePath)
        if os.path.exists(self.scriptPath.format(fileName=self.scriptName)):
            os.remove(self.scriptPath.format(fileName=self.scriptName))
        if os.path.exists(filePathOutput):
            os.remove(filePathOutput)            
        self.solder = solder
        return solder    
            
    def GenerateMesh(self, meshSize, meshPath):
        mid = self.matID 
        self.meshManager.SetPath(meshPath)
        self.meshManager.part.SetMaterialID(mid)
        self.meshManager.SetName("SolderJoint_{0}".format(self.name))
        self.meshManager.mesh_shape(self.solder, meshSize,meshSize*1.5,3,None,self.maxNID,self.maxEID)
        self.maxNID, self.maxEID = self.meshManager.GetMaxIDs()
        self.maxPID = self.maxPID + 1
        self.meshManager.part.SetID(self.maxPID)
        
        pass
    
# SMD Type
class SolderMaskedDefined(SolderJoint):
    def __init__(self, name, nodeMan : NodeManager = None, elementMan : ElementManager = None, partMan : KooPartManager = None, sectionMan : KooSectionManager = None, materialMan : KooMaterialManager = None, nodeSetMan : NodeSetManager = None, part = None):
        super(SolderMaskedDefined, self).__init__(name, nodeMan=nodeMan, elementMan=elementMan, partMan=partMan, sectionMan=sectionMan, materialMan=materialMan, nodeSetMan=nodeSetMan, part=part)
        self.bottom_point = [0, 0, 0]
        self.bottom_radius = 0.125
        self.bottom_normal = [0, 0, 1]
        self.top_point = [0, 0, 0.125]
        self.top_radius = 0.125
        self.top_normal = [0, 0, 1]
        self.bottomMaskThickness = 0.01
        self.topMaskThickness = 0.01
        self.solderType = "SMD"
    
    def SetBottomfromTwoPointsandCenter(self, point1, point2, pointCenter):
        x1, y1, z1 = point1.X(), point1.Y(), point1.Z()
        x2, y2, z2 = point2.X(), point2.Y(), point2.Z()
        xc, yc, zc = pointCenter.X(), pointCenter.Y(), pointCenter.Z()
        self.bottom_point = [xc, yc, zc]
        self.bottom_radius = math.sqrt((x1-xc)**2 + (y1-yc)**2 + (z1-zc)**2)
        ptc1 = gp_Vec(x1-xc, y1-yc, z1-zc)
        ptc2 = gp_Vec(x2-xc, y2-yc, z2-zc)
        normal = ptc1.Crossed(ptc2)
        normal.Normalize()
        self.bottom_normal = [normal.X(), normal.Y(), normal.Z()] 
        
    def SetTopfromTwoPointsandCenter(self, point1, point2, pointCenter):
        x1, y1, z1 = point1.X(), point1.Y(), point1.Z()
        x2, y2, z2 = point2.X(), point2.Y(), point2.Z()
        xc, yc, zc = pointCenter.X(), pointCenter.Y(), pointCenter.Z()
        self.top_point = [xc, yc, zc]
        self.top_radius = math.sqrt((x1-xc)**2 + (y1-yc)**2 + (z1-zc)**2)
        ptc1 = gp_Vec(x1-xc, y1-yc, z1-zc)
        ptc2 = gp_Vec(x2-xc, y2-yc, z2-zc)
        normal = ptc1.Crossed(ptc2)
        normal.Normalize()
        self.top_normal = [normal.X(), normal.Y(), normal.Z()]
        
            
    def SetBottom(self, point, radius, normal):
        self.bottom_point = point
        self.bottom_radius = radius
        self.bottom_normal = normal
        
    def SetTop(self, point, radius, normal):
        self.top_point = point
        self.top_radius = radius
        self.top_normal = normal
            
    def SetMaskThicknessTopBottom(self, bottomMaskThickness, topMaskThickness):
        self.bottomMaskThickness = bottomMaskThickness
        self.topMaskThickness = topMaskThickness
    
    def SetMaskThickness(self, thickness):
        self.bottomMaskThickness = thickness
        self.topMaskThickness = thickness
    
    def SetScriptforHeight(self, force, minDistance = 0.0):
        return self.SetScriptOptimizingHeight(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, force, minDistance)
    
    def isNonWet(self,dh):
        distance = math.sqrt((self.top_point[0]-self.bottom_point[0])**2 + (self.top_point[1]-self.bottom_point[1])**2 + (self.top_point[2]-self.bottom_point[2])**2)
        if distance + dh > 1.5*self.bottom_radius + 1.5*self.top_radius:
            print("Distance between top and bottom is larger than sum of radius")
            return True
        else:
            return False
    
    def UpdateTopBallScript(self, dh):
        self.SetScriptTopBall(self.top_point, self.top_radius, self.bottom_radius, self.top_normal,self.S_TENSION, self.SOLDER_DENSITY, -self.GRAVITY, self.VOLUME, self.topMaskThickness, dh)
    
    def UpdateBottomBallScript(self):
        self.SetScriptBottomBall(self.bottom_point, self.bottom_radius, self.top_radius, self.bottom_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.bottomMaskThickness)
        
        
    def SetScriptTopBall(self, top_point, top_radius, bottom_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, topMaskThickness = 0.01, dh = 0.0):
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]        
        
        ntx, nty, ntz = top_normal
        ntNormal = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntNormal
        nty /= ntNormal
        ntz /= ntNormal
        xt = xt + ntx*dh
        yt = yt + nty*dh
        zt = zt + ntz*dh
        tmt = topMaskThickness
        ax, ay, az = 1, 1, 1
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        xb = xt - ntx*top_radius
        yb = yt - nty*top_radius
        zb = zt - ntz*top_radius
        
        xpt = xt - ntx*tmt
        ypt = yt - nty*tmt
        zpt = zt - ntz*tmt
        
        height = top_radius
                
            
        script = ""
        script += "// bga-10.fe\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}     // cm\n"
        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        script += "// configuration parameters\n"
        
        
        if tmt == 0.0:
            script += "// upper top \n"
            script += "constraint 1\n"
            script += "formula : ({ntx})*(x-({xt}))+({nty})*(y-({yt}))+({ntz})*(z-({zt})) = 0\n"    
            script += "// metal mask cylinder\n"
            script += "constraint 3\n"
            script += "formula : (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"
            script += "// upper pad rim\n"
            script += "boundary 1 parameters 1\n"
            script += "x1: {xt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
            script += "x2: {yt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
            script += "x3: {zt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
                
            script += "vertices\n"
            
            script += "// lower vertices\n"        
            script += "1 {xb}+({top_radius})*cos(0*pi/3)*({utx})+({top_radius})*sin(0*pi/3)*({vtx}) {yb}+({top_radius})*cos(0*pi/3)*({uty})+({top_radius})*sin(0*pi/3)*({vty}) {zb}+({top_radius})*cos(0*pi/3)*({utz})+({top_radius})*sin(0*pi/3)*({vtz})\n"
            script += "2 {xb}+({top_radius})*cos(1*pi/3)*({utx})+({top_radius})*sin(1*pi/3)*({vtx}) {yb}+({top_radius})*cos(1*pi/3)*({uty})+({top_radius})*sin(1*pi/3)*({vty}) {zb}+({top_radius})*cos(1*pi/3)*({utz})+({top_radius})*sin(1*pi/3)*({vtz})\n"
            script += "3 {xb}+({top_radius})*cos(2*pi/3)*({utx})+({top_radius})*sin(2*pi/3)*({vtx}) {yb}+({top_radius})*cos(2*pi/3)*({uty})+({top_radius})*sin(2*pi/3)*({vty}) {zb}+({top_radius})*cos(2*pi/3)*({utz})+({top_radius})*sin(2*pi/3)*({vtz})\n"
            script += "4 {xb}+({top_radius})*cos(3*pi/3)*({utx})+({top_radius})*sin(3*pi/3)*({vtx}) {yb}+({top_radius})*cos(3*pi/3)*({uty})+({top_radius})*sin(3*pi/3)*({vty}) {zb}+({top_radius})*cos(3*pi/3)*({utz})+({top_radius})*sin(3*pi/3)*({vtz})\n"
            script += "5 {xb}+({top_radius})*cos(4*pi/3)*({utx})+({top_radius})*sin(4*pi/3)*({vtx}) {yb}+({top_radius})*cos(4*pi/3)*({uty})+({top_radius})*sin(4*pi/3)*({vty}) {zb}+({top_radius})*cos(4*pi/3)*({utz})+({top_radius})*sin(4*pi/3)*({vtz})\n"
            script += "6 {xb}+({top_radius})*cos(5*pi/3)*({utx})+({top_radius})*sin(5*pi/3)*({vtx}) {yb}+({top_radius})*cos(5*pi/3)*({uty})+({top_radius})*sin(5*pi/3)*({vty}) {zb}+({top_radius})*cos(5*pi/3)*({utz})+({top_radius})*sin(5*pi/3)*({vtz})\n"
            
            script += "// metal mask top vertices\n"
            script += "11 0*pi/3 boundary 1 fixed\n"
            script += "12 1*pi/3 boundary 1 fixed\n"
            script += "13 2*pi/3 boundary 1 fixed\n"
            script += "14 3*pi/3 boundary 1 fixed\n"
            script += "15 4*pi/3 boundary 1 fixed\n"
            script += "16 5*pi/3 boundary 1 fixed\n"
            
            script += "edges  // defined by endpoints\n"
            script += "// lower edges\n"
            script += "1 1 2\n"
            script += "2 2 3\n"
            script += "3 3 4\n"
            script += "4 4 5\n"
            script += "5 5 6\n"
            script += "6 6 1\n"
            
            script += "// mask top edges\n"
            script += "11 11 12 boundary 1 fixed\n"
            script += "12 12 13 boundary 1 fixed\n"
            script += "13 13 14 boundary 1 fixed\n"
            script += "14 14 15 boundary 1 fixed\n"
            script += "15 15 16 boundary 1 fixed\n"
            script += "16 16 11 boundary 1 fixed\n"
            
            script += "//vertical edges between bottom and metal mask bottom\n"
            script += "21 1 11\n"
            script += "22 2 12\n"
            script += "23 3 13\n"
            script += "24 4 14\n"
            script += "25 5 15\n"
            script += "26 6 16\n"
            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces bottom mask\n"
            script += "1 1 22 -11 -21 tension S_TENSION \n"
            script += "2 2 23 -12 -22 tension S_TENSION \n"
            script += "3 3 24 -13 -23 tension S_TENSION \n"
            script += "4 4 25 -14 -24 tension S_TENSION \n"
            script += "5 5 26 -15 -25 tension S_TENSION \n"
            script += "6 6 21 -16 -26 tension S_TENSION \n"
            
            script += "// lower pad\n"
            script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension S_TENSION\n"
            script += "// upper pad\n"
            script += "8  11  12  13 14 15 16 fixed color green tension 0 constraint 1\n"
            script += "bodies // defined by oriented face list\n"
            volumeBottom = bottom_radius**3
            volumeTop = top_radius**3
            volumeRatio = volumeTop/(volumeBottom+volumeTop)
            if VOLUME<=0.0:
                script += "1 1 2 3 4 5 6 7 8 volume 1.3*pi*({top_radius})^2*({volume_ratio})*height density SOLDER_DENSITY\n"
                volume = 1.3*math.pi*top_radius**2*volumeRatio*height
                print("Volume: ", volume)
            else:
                volume = VOLUME*volumeRatio
                script += "1 1 2 3 4 5 6 7 8 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=volume)
                print("Volume: ", volume)                
            pass
        else:
                    
            script += "// upper top \n"
            script += "constraint 1\n"
            script += "formula : ({ntx})*(x-({xt}))+({nty})*(y-({yt}))+({ntz})*(z-({zt})) = 0\n"    
            script += "// metal mask cylinder\n"
            script += "constraint 3\n"
            script += "formula : (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"
            script += "// metal mask top\n"
            script += "constraint 5\n"
            script += "formula : ({ntx})*(x-({xpt}))+({nty})*(y-({ypt}))+({ntz})*(z-({zpt})) = 0\n"
            
            script += "// upper pad rim\n"
            script += "boundary 1 parameters 1\n"
            script += "x1: {xt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
            script += "x2: {yt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
            script += "x3: {zt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
            
            script += "// upper pad mask\n"
            script += "boundary 3 parameters 1\n"
            script += "x1: {xpt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
            script += "x2: {ypt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
            script += "x3: {zpt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
            
            script += "vertices\n"
            
            script += "// lower vertices\n"        
            script += "1 {xb}+({top_radius})*cos(0*pi/3)*({utx})+({top_radius})*sin(0*pi/3)*({vtx}) {yb}+({top_radius})*cos(0*pi/3)*({uty})+({top_radius})*sin(0*pi/3)*({vty}) {zb}+({top_radius})*cos(0*pi/3)*({utz})+({top_radius})*sin(0*pi/3)*({vtz})\n"
            script += "2 {xb}+({top_radius})*cos(1*pi/3)*({utx})+({top_radius})*sin(1*pi/3)*({vtx}) {yb}+({top_radius})*cos(1*pi/3)*({uty})+({top_radius})*sin(1*pi/3)*({vty}) {zb}+({top_radius})*cos(1*pi/3)*({utz})+({top_radius})*sin(1*pi/3)*({vtz})\n"
            script += "3 {xb}+({top_radius})*cos(2*pi/3)*({utx})+({top_radius})*sin(2*pi/3)*({vtx}) {yb}+({top_radius})*cos(2*pi/3)*({uty})+({top_radius})*sin(2*pi/3)*({vty}) {zb}+({top_radius})*cos(2*pi/3)*({utz})+({top_radius})*sin(2*pi/3)*({vtz})\n"
            script += "4 {xb}+({top_radius})*cos(3*pi/3)*({utx})+({top_radius})*sin(3*pi/3)*({vtx}) {yb}+({top_radius})*cos(3*pi/3)*({uty})+({top_radius})*sin(3*pi/3)*({vty}) {zb}+({top_radius})*cos(3*pi/3)*({utz})+({top_radius})*sin(3*pi/3)*({vtz})\n"
            script += "5 {xb}+({top_radius})*cos(4*pi/3)*({utx})+({top_radius})*sin(4*pi/3)*({vtx}) {yb}+({top_radius})*cos(4*pi/3)*({uty})+({top_radius})*sin(4*pi/3)*({vty}) {zb}+({top_radius})*cos(4*pi/3)*({utz})+({top_radius})*sin(4*pi/3)*({vtz})\n"
            script += "6 {xb}+({top_radius})*cos(5*pi/3)*({utx})+({top_radius})*sin(5*pi/3)*({vtx}) {yb}+({top_radius})*cos(5*pi/3)*({uty})+({top_radius})*sin(5*pi/3)*({vty}) {zb}+({top_radius})*cos(5*pi/3)*({utz})+({top_radius})*sin(5*pi/3)*({vtz})\n"
            
            script += "// metal mask bottom vertices\n"
            script += "11 0*pi/3 boundary 3 fixed\n"
            script += "12 1*pi/3 boundary 3 fixed\n"
            script += "13 2*pi/3 boundary 3 fixed\n"
            script += "14 3*pi/3 boundary 3 fixed\n"
            script += "15 4*pi/3 boundary 3 fixed\n"
            script += "16 5*pi/3 boundary 3 fixed\n"   
            
            script += "// metal mask top vertices\n"
            script += "21 0*pi/3 boundary 1 fixed\n"
            script += "22 1*pi/3 boundary 1 fixed\n"
            script += "23 2*pi/3 boundary 1 fixed\n"
            script += "24 3*pi/3 boundary 1 fixed\n"
            script += "25 4*pi/3 boundary 1 fixed\n"
            script += "26 5*pi/3 boundary 1 fixed\n"
            
            script += "edges  // defined by endpoints\n"
            script += "// lower edges\n"
            script += "1 1 2\n"
            script += "2 2 3\n"
            script += "3 3 4\n"
            script += "4 4 5\n"
            script += "5 5 6\n"
            script += "6 6 1\n"
            
            script += "// mask bottom edges\n"
            script += "11 11 12 boundary 3 fixed\n"
            script += "12 12 13 boundary 3 fixed\n"
            script += "13 13 14 boundary 3 fixed\n"
            script += "14 14 15 boundary 3 fixed\n"
            script += "15 15 16 boundary 3 fixed\n"
            script += "16 16 11 boundary 3 fixed\n"
            
            script += "// mask top edges\n"
            script += "21 21 22 boundary 1 fixed\n"
            script += "22 22 23 boundary 1 fixed\n"
            script += "23 23 24 boundary 1 fixed\n"
            script += "24 24 25 boundary 1 fixed\n"
            script += "25 25 26 boundary 1 fixed\n"
            script += "26 26 21 boundary 1 fixed\n"
            
            script += "//vertical edges between bottom and metal mask bottom\n"
            script += "31 1 11\n"
            script += "32 2 12\n"
            script += "33 3 13\n"
            script += "34 4 14\n"
            script += "35 5 15\n"
            script += "36 6 16\n"
            
            script += "//vertical edges between metal mask bottom and top\n"
            script += "41 11 21 no_refine\n"
            script += "42 12 22 no_refine\n"
            script += "43 13 23 no_refine\n"
            script += "44 14 24 no_refine\n"
            script += "45 15 25 no_refine\n"
            script += "46 16 26 no_refine\n"
            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces bottom mask\n"
            script += "1 1 32 -11 -31 tension S_TENSION \n"
            script += "2 2 33 -12 -32 tension S_TENSION \n"
            script += "3 3 34 -13 -33 tension S_TENSION \n"
            script += "4 4 35 -14 -34 tension S_TENSION \n"
            script += "5 5 36 -15 -35 tension S_TENSION \n"
            script += "6 6 31 -16 -36 tension S_TENSION \n"
            
            script += "// lateral faces top mask\n"
            script += "7 11 42 -21 -41 tension S_TENSION no_refine\n"
            script += "8 12 43 -22 -42 tension S_TENSION no_refine\n"
            script += "9 13 44 -23 -43 tension S_TENSION no_refine\n"
            script += "10 14 45 -24 -44 tension S_TENSION no_refine\n"
            script += "11 15 46 -25 -45 tension S_TENSION no_refine\n"
            script += "12 16 41 -26 -46 tension S_TENSION no_refine\n"
            
            script += "// lower pad\n"
            script += "13 -6 -5 -4 -3 -2 -1 color red tension S_TENSION\n"
            script += "// upper pad\n"
            script += "14 21 22 23 24 25 26 fixed color green tension 0 constraint 1\n"
            script += "bodies\n"
            volumeBottom = bottom_radius**3
            volumeTop = top_radius**3
            volumeRatio = volumeTop/(volumeBottom+volumeTop)
            if VOLUME<=0.0:
                script += "1 1 2 3 4 5 6 7 8 9 10 11 12 13 14 volume 1.3*pi*({top_radius})^2*({volume_ratio})*height density SOLDER_DENSITY\n"
                volume = 1.3*math.pi*top_radius**2*volumeRatio*height
                print("Volume: ", volume)
            else:
                volume = VOLUME*volumeRatio
                script += "1 1 2 3 4 5 6 7 8 9 10 11 12 13 14 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=volume)
                print("Volume: ", volume)
                
                
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        #script += "read \"xyztorque.cmd\"\n"
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        script += "g 100\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "q\n"
        script += "q\n"
            
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, xpt=xpt, ypt=ypt, zpt=zpt, height=height, stlFileName=self.stlFileName, volume_ratio=volumeRatio, top_radius = top_radius)
        
        self.script = script
    
    def SetScriptBottomBall(self, bottom_point, bottom_radius, top_radius, bottom_normal, S_TENSION, SOLDER_DENSITY, GRAVITY, VOLUME, bottomMaskThickness):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        nbx /= nbLength
        nby /= nbLength
        nbz /= nbLength
        bmt = bottomMaskThickness
        
        xmb = xb + nbx*bmt
        ymb = yb + nby*bmt
        zmb = zb + nbz*bmt
        
        ax, ay, az = 1, 1, 1
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
        
        xt = xb + nbx*bottom_radius
        yt = yb + nby*bottom_radius
        zt = zb + nbz*bottom_radius
        
        height = bottom_radius
        script  = ""
        script += "// bga-10.fe\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}     // cm\n"
        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        
        script += "// configuration parameters\n"
        
        if bmt == 0.0:
            script += "// lower pad\n"
            script += "constraint 1\n"
            script += "formula : ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
            script += "// metal mask bottom\n"
            script += "constraint 3\n"
            script += "formula : (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
            
            script += "// lower pad rim\n"
            script += "boundary 1 parameters 1\n"
            script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
            script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
            script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
                
            script += "vertices\n"
            
            script += "// lower pad internal\n"
            script += "1 0*pi/3 boundary 1 fixed\n"
            script += "2 1*pi/3 boundary 1 fixed\n"
            script += "3 2*pi/3 boundary 1 fixed\n"
            script += "4 3*pi/3 boundary 1 fixed\n"
            script += "5 4*pi/3 boundary 1 fixed\n"
            script += "6 5*pi/3 boundary 1 fixed\n"                        
            
            script += "// top vertex\n"
            script += "11 {xt}+({bottom_radius})*cos(0*pi/3)*({ubx})+({bottom_radius})*sin(0*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(0*pi/3)*({uby})+({bottom_radius})*sin(0*pi/3)*({vby}) {zt}+({bottom_radius})*cos(0*pi/3)*({ubz})+({bottom_radius})*sin(0*pi/3)*({vbz})\n"
            script += "12 {xt}+({bottom_radius})*cos(1*pi/3)*({ubx})+({bottom_radius})*sin(1*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(1*pi/3)*({uby})+({bottom_radius})*sin(1*pi/3)*({vby}) {zt}+({bottom_radius})*cos(1*pi/3)*({ubz})+({bottom_radius})*sin(1*pi/3)*({vbz})\n"
            script += "13 {xt}+({bottom_radius})*cos(2*pi/3)*({ubx})+({bottom_radius})*sin(2*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(2*pi/3)*({uby})+({bottom_radius})*sin(2*pi/3)*({vby}) {zt}+({bottom_radius})*cos(2*pi/3)*({ubz})+({bottom_radius})*sin(2*pi/3)*({vbz})\n"
            script += "14 {xt}+({bottom_radius})*cos(3*pi/3)*({ubx})+({bottom_radius})*sin(3*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(3*pi/3)*({uby})+({bottom_radius})*sin(3*pi/3)*({vby}) {zt}+({bottom_radius})*cos(3*pi/3)*({ubz})+({bottom_radius})*sin(3*pi/3)*({vbz})\n"
            script += "15 {xt}+({bottom_radius})*cos(4*pi/3)*({ubx})+({bottom_radius})*sin(4*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(4*pi/3)*({uby})+({bottom_radius})*sin(4*pi/3)*({vby}) {zt}+({bottom_radius})*cos(4*pi/3)*({ubz})+({bottom_radius})*sin(4*pi/3)*({vbz})\n"
            script += "16 {xt}+({bottom_radius})*cos(5*pi/3)*({ubx})+({bottom_radius})*sin(5*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(5*pi/3)*({uby})+({bottom_radius})*sin(5*pi/3)*({vby}) {zt}+({bottom_radius})*cos(5*pi/3)*({ubz})+({bottom_radius})*sin(5*pi/3)*({vbz})\n"
            
            
            script += "edges  // defined by endpoints\n"
            script += "// lower pad internal\n"
            script += "1 1 2 boundary 1 fixed\n"
            script += "2 2 3 boundary 1 fixed\n"
            script += "3 3 4 boundary 1 fixed\n"
            script += "4 4 5 boundary 1 fixed\n"
            script += "5 5 6 boundary 1 fixed\n"
            script += "6 6 1 boundary 1 fixed\n"
            
            script += "// lower pad bottom\n"
            script += "11 11 12\n"
            script += "12 12 13\n"
            script += "13 13 14\n"
            script += "14 14 15\n"
            script += "15 15 16\n"
            script += "16 16 11\n"
            
            script += "//vertical edges between low pad internal and low pad bottom\n"
            script += "21 1 11\n"
            script += "22 2 12\n"
            script += "23 3 13\n"
            script += "24 4 14\n"
            script += "25 5 15\n"
            script += "26 6 16\n"
            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces between low pad internal and low pad bottom\n"
            script += "1 1 22 -11 -21 tension S_TENSION \n" 
            script += "2 2 23 -12 -22 tension S_TENSION \n"
            script += "3 3 24 -13 -23 tension S_TENSION \n"
            script += "4 4 25 -14 -24 tension S_TENSION \n"
            script += "5 5 26 -15 -25 tension S_TENSION \n"
            script += "6 6 21 -16 -26 tension S_TENSION \n"
            
            
            script += "// lower pad internal\n"
            script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
            script += "// upper\n"
            script += "8  11  12  13 14 15 16 color green tension S_TENSION\n"
            script += "bodies // defined by oriented face list\n"
            
            volumeBottom = bottom_radius**3
            volumeTop = top_radius**3
            volumeRatio = volumeBottom/(volumeTop+volumeBottom)
            if VOLUME <= 0.0:
                script += "1 1 2 3 4 5 6 7 8 volume 1.3*pi*({bottom_radius})^2*({volume_ratio})*height density SOLDER_DENSITY\n"
                
                volume = 1.3*math.pi*bottom_radius**2*height*volumeRatio
                print("Volume: ", volume)
            else:
                volume = VOLUME*volumeRatio
                script += "1 1 2 3 4 5 6 7 8 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=volume)
                print("Volume: ", volume)
            
        else:
            
            script += "// lower pad\n"
            script += "constraint 1\n"
            script += "formula : ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
            script += "// metal mask bottom\n"
            script += "constraint 3\n"
            script += "formula : (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
            script += "//lower pad bottom \n"
            script += "// lower pad mask\n"
            
            script += "// lower pad rim\n"
            script += "boundary 1 parameters 1\n"
            script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
            script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
            script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
            
            script += "// lower pad mask\n"
            script += "boundary 3 parameters 1\n"
            script += "x1: {xmb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
            script += "x2: {ymb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
            script += "x3: {zmb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
            
            script += "boundary 5 parameters 1\n"
            script += "x1: {xmb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
            script += "x2: {ymb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
            script += "x3: {zmb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
            
                
            script += "vertices\n"
            
            script += "// lower pad bottom\n"
            script += "1 0*pi/3 boundary 1 fixed\n"
            script += "2 1*pi/3 boundary 1 fixed\n"
            script += "3 2*pi/3 boundary 1 fixed\n"
            script += "4 3*pi/3 boundary 1 fixed\n"
            script += "5 4*pi/3 boundary 1 fixed\n"
            script += "6 5*pi/3 boundary 1 fixed\n"
            
            script += "// lower pad top\n"
            script += "11 0*pi/3 boundary 5 fixed\n"   
            script += "12 1*pi/3 boundary 5 fixed\n"
            script += "13 2*pi/3 boundary 5 fixed\n"
            script += "14 3*pi/3 boundary 5 fixed\n"
            script += "15 4*pi/3 boundary 5 fixed\n"
            script += "16 5*pi/3 boundary 5 fixed\n"
                        
            script += "// top vertex\n"
            script += "31 {xt}+({bottom_radius})*cos(0*pi/3)*({ubx})+({bottom_radius})*sin(0*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(0*pi/3)*({uby})+({bottom_radius})*sin(0*pi/3)*({vby}) {zt}+({bottom_radius})*cos(0*pi/3)*({ubz})+({bottom_radius})*sin(0*pi/3)*({vbz})\n"
            script += "32 {xt}+({bottom_radius})*cos(1*pi/3)*({ubx})+({bottom_radius})*sin(1*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(1*pi/3)*({uby})+({bottom_radius})*sin(1*pi/3)*({vby}) {zt}+({bottom_radius})*cos(1*pi/3)*({ubz})+({bottom_radius})*sin(1*pi/3)*({vbz})\n"
            script += "33 {xt}+({bottom_radius})*cos(2*pi/3)*({ubx})+({bottom_radius})*sin(2*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(2*pi/3)*({uby})+({bottom_radius})*sin(2*pi/3)*({vby}) {zt}+({bottom_radius})*cos(2*pi/3)*({ubz})+({bottom_radius})*sin(2*pi/3)*({vbz})\n"
            script += "34 {xt}+({bottom_radius})*cos(3*pi/3)*({ubx})+({bottom_radius})*sin(3*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(3*pi/3)*({uby})+({bottom_radius})*sin(3*pi/3)*({vby}) {zt}+({bottom_radius})*cos(3*pi/3)*({ubz})+({bottom_radius})*sin(3*pi/3)*({vbz})\n"
            script += "35 {xt}+({bottom_radius})*cos(4*pi/3)*({ubx})+({bottom_radius})*sin(4*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(4*pi/3)*({uby})+({bottom_radius})*sin(4*pi/3)*({vby}) {zt}+({bottom_radius})*cos(4*pi/3)*({ubz})+({bottom_radius})*sin(4*pi/3)*({vbz})\n"
            script += "36 {xt}+({bottom_radius})*cos(5*pi/3)*({ubx})+({bottom_radius})*sin(5*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(5*pi/3)*({uby})+({bottom_radius})*sin(5*pi/3)*({vby}) {zt}+({bottom_radius})*cos(5*pi/3)*({ubz})+({bottom_radius})*sin(5*pi/3)*({vbz})\n"
            
            
            script += "edges  // defined by endpoints\n"
            script += "// lower pad internal\n"
            script += "1 1 2 boundary 1 fixed\n"
            script += "2 2 3 boundary 1 fixed\n"
            script += "3 3 4 boundary 1 fixed\n"
            script += "4 4 5 boundary 1 fixed\n"
            script += "5 5 6 boundary 1 fixed\n"
            script += "6 6 1 boundary 1 fixed\n"
            
            script += "// lower pad bottom\n"
            script += "11 11 12 boundary 5 fixed\n"
            script += "12 12 13 boundary 5 fixed\n"
            script += "13 13 14 boundary 5 fixed\n"
            script += "14 14 15 boundary 5 fixed\n"
            script += "15 15 16 boundary 5 fixed\n"
            script += "16 16 11 boundary 5 fixed\n"
            
            script += "// upper edges\n"
            script += "31 31 32\n"
            script += "32 32 33\n"
            script += "33 33 34\n"
            script += "34 34 35\n"
            script += "35 35 36\n"
            script += "36 36 31\n"
            
            script += "//vertical edges between low pad bottom and low pad top\n"
            script += "41 1 11 no_refine fixed\n"
            script += "42 2 12 no_refine fixed\n"
            script += "43 3 13 no_refine fixed\n"
            script += "44 4 14 no_refine fixed\n"
            script += "45 5 15 no_refine fixed\n"
            script += "46 6 16 no_refine fixed\n"
            
            script += "//vertical edges between low pad top and upper pad\n"
            script += "51 11 31\n"
            script += "52 12 32\n"
            script += "53 13 33\n"
            script += "54 14 34\n"
            script += "55 15 35\n"
            script += "56 16 36\n"

            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces between low pad internal and low pad bottom\n"
            script += "1 1 42 -11 -41 tension S_TENSION no_refine\n" 
            script += "2 2 43 -12 -42 tension S_TENSION no_refine\n"
            script += "3 3 44 -13 -43 tension S_TENSION no_refine\n"
            script += "4 4 45 -14 -44 tension S_TENSION no_refine\n"
            script += "5 5 46 -15 -45 tension S_TENSION no_refine\n"
            script += "6 6 41 -16 -46 tension S_TENSION no_refine\n"
            
            
            script += "// lateral faces between low pad bottom and low pad top\n"
            script += "11 11 52 -31 -51 tension S_TENSION\n"
            script += "12 12 53 -32 -52 tension S_TENSION\n"
            script += "13 13 54 -33 -53 tension S_TENSION\n"
            script += "14 14 55 -34 -54 tension S_TENSION\n"
            script += "15 15 56 -35 -55 tension S_TENSION\n"
            script += "16 16 51 -36 -56 tension S_TENSION\n"                                
                            
            script += "// lower pad internal\n"
            script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
            script += "// upper\n"
            script += "8  31  32  33 34 35 36 color green tension S_TENSION\n"
            script += "bodies // defined by oriented face list\n"
            volumeBottom = bottom_radius**3
            volumeTop = top_radius**3
            volumeRatio = volumeBottom/(volumeTop+volumeBottom)
            if VOLUME <= 0.0:
                script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 volume 1.3*pi*({bottom_radius})^2*({volume_ratio})*height density SOLDER_DENSITY\n"
                
                volume = 1.3*math.pi*bottom_radius**2*height*volumeRatio
                print("Volume: ", volume)
            else:
                volume = VOLUME*volumeRatio
                script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=volume)
                print("Volume: ", volume)
        
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        #script += "read \"xyztorque.cmd\"\n"
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        script += "g 100\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "q\n"
        script += "q\n"
        
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, xmb=xmb, ymb=ymb, zmb=zmb, height=height, stlFileName=self.stlFileName, volume_ratio=volumeRatio, bmt = bmt)
        self.script = script 
            
    
    def UpdateScript(self, dh = 0.0):                
        if self.topMaskThickness == 0.0 and self.bottomMaskThickness == 0.0:
            self.SetScriptwithoutMask(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, dh)
        elif self.topMaskThickness == 0.0:
            self.SetScriptwithBottomMask(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.bottomMaskThickness, dh)
        elif self.bottomMaskThickness == 0.0:
            self.SetScriptwithTopMask(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.topMaskThickness, dh)
        else:
            self.SetScriptwithMask(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.topMaskThickness, self.bottomMaskThickness, dh)
            #self.SecScriptwithMaskOptimizingHeight(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.topMaskThickness, self.bottomMaskThickness)
    
    def SetScriptwithBottomMask(self,bottom_point, bottom_radius, bottom_normal, top_point, top_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, bottomMaskThickness = 0.01, dh = 0.0):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]
        ntx, nty, ntz = top_normal
        nbx, nby, nbz = bottom_normal
        ntLength = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntLength
        nty /= ntLength
        ntz /= ntLength
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        ntx /= nbLength
        nty /= nbLength
        ntz /= nbLength
        
        xt = xt + ntx*dh
        yt = yt + nty*dh
        zt = zt + ntz*dh
        ax = 1
        ay = 1
        az = 1
        
        # cross product (ntx, nty, ntz) and (ax, ay, az)
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
        
        bmt = bottomMaskThickness
        
        xmb = xb + nbx*bmt
        ymb = yb + nby*bmt
        zmb = zb + nbz*bmt
        
        
        height = np.sqrt((xt-xb)**2 + (yt-yb)**2 + (zt-zb)**2) 
         
        x_offset = xt - xb
        y_offset = yt - yb
        #angle between top and bottom        
        tilt = nbx*ntx + nby*nty + nbz*ntz
        tilt /= (math.sqrt(nbx**2 + nby**2 + nbz**2) * math.sqrt(ntx**2 + nty**2 + ntz**2))
        if tilt > 1.0:
            tilt = 1.0
        elif tilt < -1.0:
            tilt = -1.0
        tilt = math.acos(tilt) * 180.0 / math.pi
        
        
        
        script = ""
        script += "// bga-10.fe\n"
        script += "// Simple ball grid array joint.\n"
        script += "// Circular, tilting, non-coaxial wetted pads. With gravity.\n"
        script += "// Same as bga-8.fe, but with 2D lateral movement of upper pad\n"
        script += "// and tilting.\n"
        script += "// Upper pad represented with boundary.\n"
        script += "// Liquid entirely bounded by facets.\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "// physical constants, in cgs units\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}     // cm\n"
        script += "parameter height_bottom_mask = {bmt}     // cm\n"
        script += "parameter x_offset = {x_offset}      // offset in x of upper pad\n"
        script += "parameter y_offset = {y_offset}   // offset in y of upper pad\n"
        script += "parameter tilt = {tilt}         // tilt about x-axis, degrees\n"

        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        script += "// configuration parameters\n"        
        script += "// lower pad\n"
        script += "constraint 1\n"
        script += "formula: ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
        script += "// upper pad\n"
        script += "constraint 2\n"
        script += "formula: ({ntx})*(x-({xt}))+({nty})*(y-({yt}))+({ntz})*(z-({zt})) = 0\n"    
        script += "// metal mask bottom\n"
        script += "constraint 3\n"
        script += "formula: (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
              
        script += "// lower pad rim\n"
        script += "boundary 1 parameters 1\n"
        script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"   
        script += "// upper pad rim\n"
        script += "boundary 2 parameters 1\n"
        script += "x1: {xt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: {yt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: {zt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        script += "boundary 3 parameters 1\n"
        script += "x1: {xb}\n"
        script += "x2: {yb}\n"
        script += "x3: {zb}\n"
        script += "boundary 4 parameters 1\n"
        script += "x1: {xt}\n"
        script += "x2: {yt}\n"
        script += "x3: {zt}\n"
        
        script += "// lower pad mask\n"
        script += "boundary 5 parameters 1\n"
        script += "x1: {xmb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {ymb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zmb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
        
        script += "vertices\n"
        script += "// lower pad\n"
        script += "1 0*pi/3 boundary 1 fixed\n"
        script += "2 1*pi/3 boundary 1 fixed\n"
        script += "3 2*pi/3 boundary 1 fixed\n"
        script += "4 3*pi/3 boundary 1 fixed\n"
        script += "5 4*pi/3 boundary 1 fixed\n"
        script += "6 5*pi/3 boundary 1 fixed\n"

        script += "// upper pad\n"
        script += "8 0*pi/3 boundary 2 fixed\n"
        script += "9 1*pi/3 boundary 2 fixed\n"
        script += "10 2*pi/3 boundary 2 fixed\n"
        script += "11 3*pi/3 boundary 2 fixed\n"
        script += "12 4*pi/3 boundary 2 fixed\n"
        script += "13 5*pi/3 boundary 2 fixed\n"
        
        script += "// lower mask\n"
        script += "21 0*pi/3 boundary 5 fixed\n"
        script += "22 1*pi/3 boundary 5 fixed\n"
        script += "23 2*pi/3 boundary 5 fixed\n"
        script += "24 3*pi/3 boundary 5 fixed\n"
        script += "25 4*pi/3 boundary 5 fixed\n"
        script += "26 5*pi/3 boundary 5 fixed\n"
        
        script += "edges  // defined by endpoints\n"
        script += "// lower pad edges\n"
        script += "1 1 2 boundary 1 fixed\n"
        script += "2 2 3 boundary 1 fixed\n"
        script += "3 3 4 boundary 1 fixed\n"
        script += "4 4 5 boundary 1 fixed\n"
        script += "5 5 6 boundary 1 fixed\n"
        script += "6 6 1 boundary 1 fixed\n"
        
        script += "// lower mask edges\n"
        script += "11 21 22 boundary 5 fixed\n"
        script += "12 22 23 boundary 5 fixed\n"
        script += "13 23 24 boundary 5 fixed\n"
        script += "14 24 25 boundary 5 fixed\n"
        script += "15 25 26 boundary 5 fixed\n"
        script += "16 26 21 boundary 5 fixed\n"
        
        script += "// upper pad edges\n"
        script += "31 8 9 boundary 2 fixed\n"
        script += "32 9 10 boundary 2 fixed\n"
        script += "33 10 11 boundary 2 fixed\n"
        script += "34 11 12 boundary 2 fixed\n"
        script += "35 12 13 boundary 2 fixed\n"
        script += "36 13 8 boundary 2 fixed\n"
        
        script += "// vertical edges between bottom and metal mask bottom\n"
        script += "41 1 21 no_refine\n"
        script += "42 2 22 no_refine\n"
        script += "43 3 23 no_refine\n"
        script += "44 4 24 no_refine\n"
        script += "45 5 25 no_refine\n"
        script += "46 6 26 no_refine\n"
        
        script += "// vertical edges between metal mask bottom and metal mask top\n"
        script += "51 21 8\n"
        script += "52 22 9\n"
        script += "53 23 10\n"
        script += "54 24 11\n"
        script += "55 25 12\n"
        script += "56 26 13\n"
        
        script += "faces // defined by oriented edge loops to have outward normal\n"
        script += "// lateral faces bottom mask\n"
        script += "1 1 42 -11 -41 tension S_TENSION no_refine\n"
        script += "2 2 43 -12 -42 tension S_TENSION no_refine\n"
        script += "3 3 44 -13 -43 tension S_TENSION no_refine\n"
        script += "4 4 45 -14 -44 tension S_TENSION no_refine\n"
        script += "5 5 46 -15 -45 tension S_TENSION no_refine\n"
        script += "6 6 41 -16 -46 tension S_TENSION no_refine\n"
        
        script += "// lateral faces solder\n"
        script += "11 11 52 -31 -51 tension S_TENSION\n"
        script += "12 12 53 -32 -52 tension S_TENSION\n"
        script += "13 13 54 -33 -53 tension S_TENSION\n"
        script += "14 14 55 -34 -54 tension S_TENSION\n"
        script += "15 15 56 -35 -55 tension S_TENSION\n"
        script += "16 16 51 -36 -56 tension S_TENSION\n"
                  
        script += "// lower pad\n"
        script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
        script += "// upper pad\n"
        script += "8  31  32  33 34 35 36 fixed color green tension 0 constraint 2\n"
        script += "bodies // defined by oriented face list\n"
        if VOLUME <= 0.0:
            script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
            print("Current Volume is 0.0, so it is calculated by formula")
            volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
            
            print("Volume: ", volume)
        else:
            script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
            print("Volume is defined by user")
            print("Volume: ", VOLUME)
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        script += "read \"xyztorque.cmd\"\n"
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "q\n"
        script += "q\n"    
                
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, top_radius=top_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, stlFileName=self.stlFileName, height=height, VOLUME=VOLUME, xmb=xmb, ymb=ymb, zmb=zmb, bmt=bmt, x_offset=x_offset, y_offset=y_offset, tilt=tilt)
        self.script = script
    
    def SetScriptwithTopMask(self,bottom_point, bottom_radius, bottom_normal, top_point, top_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, topMaskThickness = 0.01, dh = 0.0):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]
        ntx, nty, ntz = top_normal
        nbx, nby, nbz = bottom_normal
        ntLength = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntLength
        nty /= ntLength
        ntz /= ntLength
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        ntx /= nbLength
        nty /= nbLength
        ntz /= nbLength
        xt = xt + ntx*dh
        yt = yt + nty*dh
        zt = zt + ntz*dh
        
        ax = 1
        ay = 1
        az = 1
        
        # cross product (ntx, nty, ntz) and (ax, ay, az)
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
        
        tmt = topMaskThickness
        
        xmt = xt - ntx*tmt
        ymt = yt - nty*tmt
        zmt = zt - ntz*tmt
        
        
        height = np.sqrt((xt-xb)**2 + (yt-yb)**2 + (zt-zb)**2) 
         
        x_offset = xt - xb
        y_offset = yt - yb
        #angle between top and bottom        
        tilt = nbx*ntx + nby*nty + nbz*ntz
        tilt /= (math.sqrt(nbx**2 + nby**2 + nbz**2) * math.sqrt(ntx**2 + nty**2 + ntz**2))
        if tilt > 1.0:
            tilt = 1.0
        elif tilt < -1.0:
            tilt = -1.0
        tilt = math.acos(tilt) * 180.0 / math.pi
        
        
        
        script = ""
        script += "// bga-10.fe\n"
        script += "// Simple ball grid array joint.\n"
        script += "// Circular, tilting, non-coaxial wetted pads. With gravity.\n"
        script += "// Same as bga-8.fe, but with 2D lateral movement of upper pad\n"
        script += "// and tilting.\n"
        script += "// Upper pad represented with boundary.\n"
        script += "// Liquid entirely bounded by facets.\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "// physical constants, in cgs units\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}     // cm\n"
        script += "parameter height_top_mask = {tmt}     // cm\n"
        script += "parameter x_offset = {x_offset}      // offset in x of upper pad\n"
        script += "parameter y_offset = {y_offset}   // offset in y of upper pad\n"
        script += "parameter tilt = {tilt}         // tilt about x-axis, degrees\n"

        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        script += "// configuration parameters\n"        
        script += "// lower pad\n"
        script += "constraint 1\n"
        script += "formula: ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
        script += "// upper pad\n"
        script += "constraint 2\n"
        script += "formula: ({ntx})*(x-({xt}))+({nty})*(y-({yt}))+({ntz})*(z-({zt})) = 0\n"    
        script += "// metal mask bottom\n"
        script += "constraint 3\n"
        script += "formula: (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
        script += "// metal mask top\n"
        script += "constraint 4\n"
        script += "formula: (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"        
              
        script += "// lower pad rim\n"
        script += "boundary 1 parameters 1\n"
        script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"   
        script += "// upper pad rim\n"
        script += "boundary 2 parameters 1\n"
        script += "x1: {xt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: {yt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: {zt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        script += "boundary 3 parameters 1\n"
        script += "x1: {xb}\n"
        script += "x2: {yb}\n"
        script += "x3: {zb}\n"
        script += "boundary 4 parameters 1\n"
        script += "x1: {xt}\n"
        script += "x2: {yt}\n"
        script += "x3: {zt}\n"
        
        script += "boundary 6 parameters 1\n"
        script += "x1: {xmt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: {ymt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: {zmt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        
        script += "vertices\n"
        script += "// lower pad\n"
        script += "1 0*pi/3 boundary 1 fixed\n"
        script += "2 1*pi/3 boundary 1 fixed\n"
        script += "3 2*pi/3 boundary 1 fixed\n"
        script += "4 3*pi/3 boundary 1 fixed\n"
        script += "5 4*pi/3 boundary 1 fixed\n"
        script += "6 5*pi/3 boundary 1 fixed\n"

        script += "// upper pad\n"
        script += "8 0*pi/3 boundary 2 fixed\n"
        script += "9 1*pi/3 boundary 2 fixed\n"
        script += "10 2*pi/3 boundary 2 fixed\n"
        script += "11 3*pi/3 boundary 2 fixed\n"
        script += "12 4*pi/3 boundary 2 fixed\n"
        script += "13 5*pi/3 boundary 2 fixed\n"
        
        script += "// upper mask\n"
        script += "28 0*pi/3 boundary 6 fixed\n"
        script += "29 1*pi/3 boundary 6 fixed\n"
        script += "30 2*pi/3 boundary 6 fixed\n"
        script += "31 3*pi/3 boundary 6 fixed\n"
        script += "32 4*pi/3 boundary 6 fixed\n"
        script += "33 5*pi/3 boundary 6 fixed\n"
        

        script += "edges  // defined by endpoints\n"
        script += "// lower pad edges\n"
        script += "1 1 2 boundary 1 fixed\n"
        script += "2 2 3 boundary 1 fixed\n"
        script += "3 3 4 boundary 1 fixed\n"
        script += "4 4 5 boundary 1 fixed\n"
        script += "5 5 6 boundary 1 fixed\n"
        script += "6 6 1 boundary 1 fixed\n"
                
        script += "// upper mask edges\n"
        script += "21 28 29 boundary 6 fixed\n"
        script += "22 29 30 boundary 6 fixed\n"
        script += "23 30 31 boundary 6 fixed\n"
        script += "24 31 32 boundary 6 fixed\n"
        script += "25 32 33 boundary 6 fixed\n"
        script += "26 33 28 boundary 6 fixed\n"
                
        script += "// upper pad edges\n"
        script += "31 8 9 boundary 2 fixed\n"
        script += "32 9 10 boundary 2 fixed\n"
        script += "33 10 11 boundary 2 fixed\n"
        script += "34 11 12 boundary 2 fixed\n"
        script += "35 12 13 boundary 2 fixed\n"
        script += "36 13 8 boundary 2 fixed\n"
        
        script += "// vertical edges between bottom and metal mask top\n"
        script += "41 1 28 \n"
        script += "42 2 29 \n"
        script += "43 3 30 \n"
        script += "44 4 31 \n"
        script += "45 5 32 \n"
        script += "46 6 33 \n"
                
        script += "// vertical edges between metal mask top and top\n"
        script += "61 28 8 no_refine\n"
        script += "62 29 9 no_refine\n"
        script += "63 30 10 no_refine\n"
        script += "64 31 11 no_refine\n"
        script += "65 32 12 no_refine\n"
        script += "66 33 13 no_refine\n"
                        
        script += "faces // defined by oriented edge loops to have outward normal\n"
        script += "// lateral faces solder\n"
        script += "1 1 42 -21 -41 tension S_TENSION\n"
        script += "2 2 43 -22 -42 tension S_TENSION\n"
        script += "3 3 44 -23 -43 tension S_TENSION\n"
        script += "4 4 45 -24 -44 tension S_TENSION\n"
        script += "5 5 46 -25 -45 tension S_TENSION\n"
        script += "6 6 41 -26 -46 tension S_TENSION\n"
                
        script += "// lateral faces top mask\n"
        script += "21 21 62 -31 -61 tension S_TENSION no_refine\n"
        script += "22 22 63 -32 -62 tension S_TENSION no_refine\n"
        script += "23 23 64 -33 -63 tension S_TENSION no_refine\n"
        script += "24 24 65 -34 -64 tension S_TENSION no_refine\n"
        script += "25 25 66 -35 -65 tension S_TENSION no_refine\n"
        script += "26 26 61 -36 -66 tension S_TENSION no_refine\n"           
                  
        script += "// lower pad\n"
        script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
        script += "// upper pad\n"
        script += "8  31  32  33 34 35 36 fixed color green tension 0 constraint 2\n"
        script += "bodies // defined by oriented face list\n"
        if VOLUME <= 0.0:
            script += "1 1 2 3 4 5 6 7 8 21 22 23 24 25 26 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
            print("Current Volume is 0.0, so it is calculated by formula")
            volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
            
            print("Volume: ", volume)
        else:
            script += "1 1 2 3 4 5 6 7 8 21 22 23 24 25 26 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
            print("Volume is defined by user")
            print("Volume: ", VOLUME)
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        script += "read \"xyztorque.cmd\"\n"
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "q\n"
        script += "q\n"    
                
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, top_radius=top_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, stlFileName=self.stlFileName, height=height, VOLUME=VOLUME, xmt=xmt, ymt=ymt, zmt=zmt, tmt=tmt, x_offset=x_offset, y_offset=y_offset, tilt=tilt)
        self.script = script
    
    def SetScriptwithMask(self,bottom_point, bottom_radius, bottom_normal, top_point, top_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, topMaskThickness = 0.01, bottomMaskThickness = 0.01, dh = 0.0):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]
        ntx, nty, ntz = top_normal
        nbx, nby, nbz = bottom_normal
        ntLength = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntLength
        nty /= ntLength
        ntz /= ntLength
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        ntx /= nbLength
        nty /= nbLength
        ntz /= nbLength
        xt = xt + ntx*dh
        yt = yt + nty*dh
        zt = zt + ntz*dh
        
        ax = 1
        ay = 1
        az = 1
        
        # cross product (ntx, nty, ntz) and (ax, ay, az)
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
        
        bmt = bottomMaskThickness
        tmt = topMaskThickness
        
        xmb = xb + nbx*bmt
        ymb = yb + nby*bmt
        zmb = zb + nbz*bmt
        
        xmt = xt - ntx*tmt
        ymt = yt - nty*tmt
        zmt = zt - ntz*tmt
        
        
        height = np.sqrt((xt-xb)**2 + (yt-yb)**2 + (zt-zb)**2) 
         
        x_offset = xt - xb
        y_offset = yt - yb
        #angle between top and bottom        
        tilt = nbx*ntx + nby*nty + nbz*ntz
        tilt /= (math.sqrt(nbx**2 + nby**2 + nbz**2) * math.sqrt(ntx**2 + nty**2 + ntz**2))
        if tilt > 1.0:
            tilt = 1.0
        elif tilt < -1.0:
            tilt = -1.0
        tilt = math.acos(tilt) * 180.0 / math.pi
        
        
        
        script = ""
        script += "// bga-10.fe\n"
        script += "// Simple ball grid array joint.\n"
        script += "// Circular, tilting, non-coaxial wetted pads. With gravity.\n"
        script += "// Same as bga-8.fe, but with 2D lateral movement of upper pad\n"
        script += "// and tilting.\n"
        script += "// Upper pad represented with boundary.\n"
        script += "// Liquid entirely bounded by facets.\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "// physical constants, in cgs units\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}     // cm\n"
        script += "parameter height_bottom_mask = {bmt}     // cm\n"
        script += "parameter height_top_mask = {tmt}     // cm\n"
        script += "parameter x_offset = {x_offset}      // offset in x of upper pad\n"
        script += "parameter y_offset = {y_offset}   // offset in y of upper pad\n"
        script += "parameter tilt = {tilt}         // tilt about x-axis, degrees\n"

        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        script += "// configuration parameters\n"        
        script += "// lower pad\n"
        script += "constraint 1\n"
        script += "formula: ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
        script += "// upper pad\n"
        script += "constraint 2\n"
        script += "formula: ({ntx})*(x-({xt}))+({nty})*(y-({yt}))+({ntz})*(z-({zt})) = 0\n"    
        script += "// metal mask bottom\n"
        script += "constraint 3\n"
        script += "formula: (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
        script += "// metal mask top\n"
        script += "constraint 4\n"
        script += "formula: (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"        
              
        script += "// lower pad rim\n"
        script += "boundary 1 parameters 1\n"
        script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"   
        script += "// upper pad rim\n"
        script += "boundary 2 parameters 1\n"
        script += "x1: {xt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: {yt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: {zt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        script += "boundary 3 parameters 1\n"
        script += "x1: {xb}\n"
        script += "x2: {yb}\n"
        script += "x3: {zb}\n"
        script += "boundary 4 parameters 1\n"
        script += "x1: {xt}\n"
        script += "x2: {yt}\n"
        script += "x3: {zt}\n"
        
        script += "// lower pad mask\n"
        script += "boundary 5 parameters 1\n"
        script += "x1: {xmb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {ymb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zmb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
        script += "boundary 6 parameters 1\n"
        script += "x1: {xmt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: {ymt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: {zmt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        
        script += "vertices\n"
        script += "// lower pad\n"
        script += "1 0*pi/3 boundary 1 fixed\n"
        script += "2 1*pi/3 boundary 1 fixed\n"
        script += "3 2*pi/3 boundary 1 fixed\n"
        script += "4 3*pi/3 boundary 1 fixed\n"
        script += "5 4*pi/3 boundary 1 fixed\n"
        script += "6 5*pi/3 boundary 1 fixed\n"

        script += "// upper pad\n"
        script += "8 0*pi/3 boundary 2 fixed\n"
        script += "9 1*pi/3 boundary 2 fixed\n"
        script += "10 2*pi/3 boundary 2 fixed\n"
        script += "11 3*pi/3 boundary 2 fixed\n"
        script += "12 4*pi/3 boundary 2 fixed\n"
        script += "13 5*pi/3 boundary 2 fixed\n"
        
        script += "// lower mask\n"
        script += "21 0*pi/3 boundary 5 fixed\n"
        script += "22 1*pi/3 boundary 5 fixed\n"
        script += "23 2*pi/3 boundary 5 fixed\n"
        script += "24 3*pi/3 boundary 5 fixed\n"
        script += "25 4*pi/3 boundary 5 fixed\n"
        script += "26 5*pi/3 boundary 5 fixed\n"
        
        script += "// upper mask\n"
        script += "28 0*pi/3 boundary 6 fixed\n"
        script += "29 1*pi/3 boundary 6 fixed\n"
        script += "30 2*pi/3 boundary 6 fixed\n"
        script += "31 3*pi/3 boundary 6 fixed\n"
        script += "32 4*pi/3 boundary 6 fixed\n"
        script += "33 5*pi/3 boundary 6 fixed\n"
        

        script += "edges  // defined by endpoints\n"
        script += "// lower pad edges\n"
        script += "1 1 2 boundary 1 fixed\n"
        script += "2 2 3 boundary 1 fixed\n"
        script += "3 3 4 boundary 1 fixed\n"
        script += "4 4 5 boundary 1 fixed\n"
        script += "5 5 6 boundary 1 fixed\n"
        script += "6 6 1 boundary 1 fixed\n"
        
        script += "// lower mask edges\n"
        script += "11 21 22 boundary 5 fixed\n"
        script += "12 22 23 boundary 5 fixed\n"
        script += "13 23 24 boundary 5 fixed\n"
        script += "14 24 25 boundary 5 fixed\n"
        script += "15 25 26 boundary 5 fixed\n"
        script += "16 26 21 boundary 5 fixed\n"
        
        script += "// upper mask edges\n"
        script += "21 28 29 boundary 6 fixed\n"
        script += "22 29 30 boundary 6 fixed\n"
        script += "23 30 31 boundary 6 fixed\n"
        script += "24 31 32 boundary 6 fixed\n"
        script += "25 32 33 boundary 6 fixed\n"
        script += "26 33 28 boundary 6 fixed\n"
                
        script += "// upper pad edges\n"
        script += "31 8 9 boundary 2 fixed\n"
        script += "32 9 10 boundary 2 fixed\n"
        script += "33 10 11 boundary 2 fixed\n"
        script += "34 11 12 boundary 2 fixed\n"
        script += "35 12 13 boundary 2 fixed\n"
        script += "36 13 8 boundary 2 fixed\n"
        
        script += "// vertical edges between bottom and metal mask bottom\n"
        script += "41 1 21 no_refine\n"
        script += "42 2 22 no_refine\n"
        script += "43 3 23 no_refine\n"
        script += "44 4 24 no_refine\n"
        script += "45 5 25 no_refine\n"
        script += "46 6 26 no_refine\n"
        
        script += "// vertical edges between metal mask bottom and metal mask top\n"
        script += "51 21 28\n"
        script += "52 22 29\n"
        script += "53 23 30\n"
        script += "54 24 31\n"
        script += "55 25 32\n"
        script += "56 26 33\n"
        
        script += "// vertical edges between metal mask top and top\n"
        script += "61 28 8 no_refine\n"
        script += "62 29 9 no_refine\n"
        script += "63 30 10 no_refine\n"
        script += "64 31 11 no_refine\n"
        script += "65 32 12 no_refine\n"
        script += "66 33 13 no_refine\n"
                        
        script += "faces // defined by oriented edge loops to have outward normal\n"
        script += "// lateral faces bottom mask\n"
        script += "1 1 42 -11 -41 tension S_TENSION no_refine\n"
        script += "2 2 43 -12 -42 tension S_TENSION no_refine\n"
        script += "3 3 44 -13 -43 tension S_TENSION no_refine\n"
        script += "4 4 45 -14 -44 tension S_TENSION no_refine\n"
        script += "5 5 46 -15 -45 tension S_TENSION no_refine\n"
        script += "6 6 41 -16 -46 tension S_TENSION no_refine\n"
        
        script += "// lateral faces solder\n"
        script += "11 11 52 -21 -51 tension S_TENSION\n"
        script += "12 12 53 -22 -52 tension S_TENSION\n"
        script += "13 13 54 -23 -53 tension S_TENSION\n"
        script += "14 14 55 -24 -54 tension S_TENSION\n"
        script += "15 15 56 -25 -55 tension S_TENSION\n"
        script += "16 16 51 -26 -56 tension S_TENSION\n"
        
        script += "// lateral faces top mask\n"
        script += "21 21 62 -31 -61 tension S_TENSION no_refine\n"
        script += "22 22 63 -32 -62 tension S_TENSION no_refine\n"
        script += "23 23 64 -33 -63 tension S_TENSION no_refine\n"
        script += "24 24 65 -34 -64 tension S_TENSION no_refine\n"
        script += "25 25 66 -35 -65 tension S_TENSION no_refine\n"
        script += "26 26 61 -36 -66 tension S_TENSION no_refine\n"           
                  
        script += "// lower pad\n"
        script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
        script += "// upper pad\n"
        script += "8  31  32  33 34 35 36 fixed color green tension 0 constraint 2\n"
        script += "bodies // defined by oriented face list\n"
        if VOLUME <= 0.0:
            script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 21 22 23 24 25 26 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
            print("Current Volume is 0.0, so it is calculated by formula")
            volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
            
            print("Volume: ", volume)
        else:
            script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 21 22 23 24 25 26 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
            print("Volume is defined by user")
            print("Volume: ", VOLUME)
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        script += "read \"xyztorque.cmd\"\n"
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "q\n"
        script += "q\n"    
                
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, top_radius=top_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, stlFileName=self.stlFileName, height=height, VOLUME=VOLUME, xmt=xmt, ymt=ymt, zmt=zmt, xmb=xmb, ymb=ymb, zmb=zmb, bmt=bmt, tmt=tmt, x_offset=x_offset, y_offset=y_offset, tilt=tilt)
        self.script = script
        
    def SetScriptwithoutMask(self,bottom_point, bottom_radius, bottom_normal, top_point, top_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, dh = 0.0):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]
        ntx, nty, ntz = top_normal
        nbx, nby, nbz = bottom_normal
        ntLength = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntLength
        nty /= ntLength
        ntz /= ntLength
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        ntx /= nbLength
        nty /= nbLength
        ntz /= nbLength
        xt = xt + ntx*dh
        yt = yt + nty*dh
        zt = zt + ntz*dh
        
        
        ax = 1
        ay = 1
        az = 1
        
        # cross product (ntx, nty, ntz) and (ax, ay, az)
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
        
        height = np.sqrt((xt-xb)**2 + (yt-yb)**2 + (zt-zb)**2)
         
        x_offset = xt - xb
        y_offset = yt - yb
        #angle between top and bottom        
        tilt = nbx*ntx + nby*nty + nbz*ntz
        tilt /= (math.sqrt(nbx**2 + nby**2 + nbz**2) * math.sqrt(ntx**2 + nty**2 + ntz**2))
        if tilt > 1.0:
            tilt = 1.0
        elif tilt < -1.0:
            tilt = -1.0
        tilt = math.acos(tilt) * 180.0 / math.pi
        
        
        
        script = ""
        script += "// bga-10.fe\n"
        script += "// Simple ball grid array joint.\n"
        script += "// Circular, tilting, non-coaxial wetted pads. With gravity.\n"
        script += "// Same as bga-8.fe, but with 2D lateral movement of upper pad\n"
        script += "// and tilting.\n"
        script += "// Upper pad represented with boundary.\n"
        script += "// Liquid entirely bounded by facets.\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "// physical constants, in cgs units\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}     // cm\n"
        script += "parameter x_offset = {x_offset}      // offset in x of upper pad\n".format(x_offset=x_offset)
        script += "parameter y_offset = {y_offset}   // offset in y of upper pad\n".format(y_offset=y_offset)
        script += "parameter tilt = {tilt}         // tilt about x-axis, degrees\n".format(tilt=tilt)

        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        script += "// configuration parameters\n"        
        script += "// lower pad\n"
        script += "constraint 1\n"
        script += "formula: ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
        script += "// upper pad\n"
        script += "constraint 2\n"
        script += "formula: ({ntx})*(x-({xt}))+({nty})*(y-({yt}))+({ntz})*(z-({zt})) = 0\n"    
        script += "// lower pad rim\n"
        script += "boundary 1 parameters 1\n"
        script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"   
        script += "// upper pad rim\n"
        script += "boundary 2 parameters 1\n"
        script += "x1: {xt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: {yt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: {zt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        script += "boundary 3 parameters 1\n"
        script += "x1: {xb}\n"
        script += "x2: {yb}\n"
        script += "x3: {zb}\n"
        script += "boundary 4 parameters 1\n"
        script += "x1: {xt}\n"
        script += "x2: {yt}\n"
        script += "x3: {zt}\n"
        script += "vertices\n"
        script += "// lower pad\n"
        script += "1 0*pi/3 boundary 1 fixed\n"
        script += "2 1*pi/3 boundary 1 fixed\n"
        script += "3 2*pi/3 boundary 1 fixed\n"
        script += "4 3*pi/3 boundary 1 fixed\n"
        script += "5 4*pi/3 boundary 1 fixed\n"
        script += "6 5*pi/3 boundary 1 fixed\n"
        script += "// center of lower pad\n"
        #script += "7 0 boundary 3 fixed\n"
        script += "// upper pad\n"
        script += "8 0*pi/3 boundary 2 fixed\n"
        script += "9 1*pi/3 boundary 2 fixed\n"
        script += "10 2*pi/3 boundary 2 fixed\n"
        script += "11 3*pi/3 boundary 2 fixed\n"
        script += "12 4*pi/3 boundary 2 fixed\n"
        script += "13 5*pi/3 boundary 2 fixed\n"
        script += "// center of upper pad\n"
        #script += "14 0 boundary 4 fixed\n"
        script += "edges  // defined by endpoints\n"
        script += "// lower pad edges\n"
        script += "1 1 2 boundary 1 fixed\n"
        script += "2 2 3 boundary 1 fixed\n"
        script += "3 3 4 boundary 1 fixed\n"
        script += "4 4 5 boundary 1 fixed\n"
        script += "5 5 6 boundary 1 fixed\n"
        script += "6 6 1 boundary 1 fixed\n"
        script += "// upper pad edges\n"
        script += "7 8 9 boundary 2 fixed\n"
        script += "8 9 10 boundary 2 fixed\n"
        script += "9 10 11 boundary 2 fixed\n"
        script += "10 11 12 boundary 2 fixed\n"
        script += "11 12 13 boundary 2 fixed\n"
        script += "12 13 8 boundary 2 fixed\n"
        script += "// vertical edges\n"
        script += "13 1 8\n"
        script += "14 2 9\n"
        script += "15 3 10\n"
        script += "16 4 11\n"
        script += "17 5 12\n"
        script += "18 6 13\n"        
        script += "faces // defined by oriented edge loops to have outward normal\n"
        script += "// lateral faces\n"
        script += "1 1 14  -7 -13 tension S_TENSION\n"  
        script += "2 2 15  -8 -14 tension S_TENSION\n"
        script += "3 3 16  -9 -15 tension S_TENSION\n"
        script += "4 4 17 -10 -16 tension S_TENSION\n"
        script += "5 5 18 -11 -17 tension S_TENSION\n"
        script += "6 6 13 -12 -18 tension S_TENSION\n"
        script += "// lower pad\n"
        script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
        script += "// upper pad\n"
        script += "8  7  8  9 10 11 12 fixed color green tension 0 constraint 2\n"
        script += "bodies // defined by oriented face list\n"
        if VOLUME <= 0.0:
            script += "1 1 2 3 4 5 6 7 8 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
            print("Current Volume is 0.0, so it is calculated by formula")
            volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
            
            print("Volume: ", volume)
        else:
            script += "1 1 2 3 4 5 6 7 8 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
            print("Volume is defined by user")
            print("Volume: ", VOLUME)
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        script += "read \"xyztorque.cmd\"\n"
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "q\n"
        script += "q\n"    
                
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, top_radius=top_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, stlFileName=self.stlFileName, height=height, VOLUME=VOLUME)
        self.script = script
        
    def SetScriptwithMaskOptimizingHeight(self, bottom_point, bottom_radius, bottom_normal, top_point, top_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, topMaskThickness = 0.01, bottomMaskThickness = 0.01, force = 0.0):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]
        ntx, nty, ntz = top_normal
        ntLength = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntLength
        nty /= ntLength
        ntz /= ntLength
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        ntx /= nbLength
        nty /= nbLength
        ntz /= nbLength
        
        ax = 1
        ay = 1
        az = 1
        
        # cross product (ntx, nty, ntz) and (ax, ay, az)
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
        
        bmt = bottomMaskThickness
        tmt = topMaskThickness
       
        
        height = np.sqrt((xt-xb)**2 + (yt-yb)**2 + (zt-zb)**2) 
         
        x_offset = xt - xb
        y_offset = yt - yb
        #angle between top and bottom        
        tilt = nbx*ntx + nby*nty + nbz*ntz
        tilt /= (math.sqrt(nbx**2 + nby**2 + nbz**2) * math.sqrt(ntx**2 + nty**2 + ntz**2))
        if tilt > 1.0:
            tilt = 1.0
        elif tilt < -1.0:
            tilt = -1.0
        tilt = math.acos(tilt) * 180.0 / math.pi
        
            
        
        script = ""
        script += "// bga-10.fe\n"
        script += "// Simple ball grid array joint.\n"
        script += "// Circular, tilting, non-coaxial wetted pads. With gravity.\n"
        script += "// Same as bga-8.fe, but with 2D lateral movement of upper pad\n"
        script += "// and tilting.\n"
        script += "// Upper pad represented with boundary.\n"
        script += "// Liquid entirely bounded by facets.\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "// physical constants, in cgs units\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}// cm\n"
        script += "parameter ntx = {ntx}     // cm\n"
        script += "parameter nty = {nty}     // cm\n"
        script += "parameter ntz = {ntz}     // cm\n"
        script += "parameter xt = {xt} - height*ntx    // cm\n"
        script += "parameter yt = {yt} - height*nty    // cm\n"
        #script += "parameter zt = {zt} - height*ntz    // cm\n"
        script += "optimizing_parameter zt = {zt} pdelta=1.0e-5 scale=1.0    // cm\n"
        
        script += "parameter height_bottom_mask = {bmt}     // cm\n"
        script += "parameter height_top_mask = {tmt}     // cm\n"
        script += "parameter x_offset = {x_offset}      // offset in x of upper pad\n"
        script += "parameter y_offset = {y_offset}   // offset in y of upper pad\n"
        script += "parameter tilt = {tilt}         // tilt about x-axis, degrees\n"
        
        script += "parameter force={force} // Newton\n"
        
        
        script += "//Gravity consideration\n"
        script += "quantity pad_energy energy method vertex_scalar_integral\n"
        script += "scalar_integrand : z*{force}\n"

        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        script += "// configuration parameters\n"        
        script += "// lower pad\n"
        script += "constraint 1\n"
        script += "formula: ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
        script += "// upper pad\n"
        script += "constraint 2\n"
        script += "formula: ({ntx})*(x-(xt))+({nty})*(y-(yt))+({ntz})*(z-(zt)) = 0\n"    
        script += "// metal mask bottom\n"
        script += "constraint 3\n"
        script += "formula: (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
        script += "// metal mask top\n"
        script += "constraint 4\n"
        script += "formula: (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"        
        
        script += "//Constraints for height\n"
        script += "constraint 5\n"
        script += "formula: z=zt\n"
              
        script += "// lower pad rim\n"
        script += "boundary 1 parameters 1\n"
        script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"   
        script += "// upper pad rim\n"
        script += "boundary 2 parameters 1\n"
        script += "x1: xt + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: yt + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: zt + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        script += "boundary 3 parameters 1\n"
        script += "x1: {xb}\n"
        script += "x2: {yb}\n"
        script += "x3: {zb}\n"
        script += "boundary 4 parameters 1\n"
        script += "x1: xt\n"
        script += "x2: yt\n"
        script += "x3: zt\n"
        
        script += "// lower pad mask\n"
        script += "boundary 5 parameters 1\n"
        script += "x1: {xb} + {nbx}*{bmt} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + {nby}*{bmt} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zb} + {nbz}*{bmt} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
        script += "boundary 6 parameters 1\n"
        script += "x1: xt - {ntx}*{tmt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: yt - {nty}*{tmt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: zt - {ntz}*{tmt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        
        script += "vertices\n"
        script += "// lower pad\n"
        script += "1 0*pi/3 boundary 1 fixed\n"
        script += "2 1*pi/3 boundary 1 fixed\n"
        script += "3 2*pi/3 boundary 1 fixed\n"
        script += "4 3*pi/3 boundary 1 fixed\n"
        script += "5 4*pi/3 boundary 1 fixed\n"
        script += "6 5*pi/3 boundary 1 fixed\n"

        script += "// upper pad\n"
        script += "8 0*pi/3 boundary 2 fixed\n"
        script += "9 1*pi/3 boundary 2 fixed\n"
        script += "10 2*pi/3 boundary 2 fixed\n"
        script += "11 3*pi/3 boundary 2 fixed\n"
        script += "12 4*pi/3 boundary 2 fixed\n"
        script += "13 5*pi/3 boundary 2 fixed\n"
        
        script += "// lower mask\n"
        script += "21 0*pi/3 boundary 5 fixed\n"
        script += "22 1*pi/3 boundary 5 fixed\n"
        script += "23 2*pi/3 boundary 5 fixed\n"
        script += "24 3*pi/3 boundary 5 fixed\n"
        script += "25 4*pi/3 boundary 5 fixed\n"
        script += "26 5*pi/3 boundary 5 fixed\n"
        
        script += "// upper mask\n"
        script += "28 0*pi/3 boundary 6 fixed\n"
        script += "29 1*pi/3 boundary 6 fixed\n"
        script += "30 2*pi/3 boundary 6 fixed\n"
        script += "31 3*pi/3 boundary 6 fixed\n"
        script += "32 4*pi/3 boundary 6 fixed\n"
        script += "33 5*pi/3 boundary 6 fixed\n"
        script += "99 0 0 zt constraint 5 fixed bare pad_energy\n"        

        script += "edges  // defined by endpoints\n"
        script += "// lower pad edges\n"
        script += "1 1 2 boundary 1 fixed\n"
        script += "2 2 3 boundary 1 fixed\n"
        script += "3 3 4 boundary 1 fixed\n"
        script += "4 4 5 boundary 1 fixed\n"
        script += "5 5 6 boundary 1 fixed\n"
        script += "6 6 1 boundary 1 fixed\n"
        
        script += "// lower mask edges\n"
        script += "11 21 22 boundary 5 fixed\n"
        script += "12 22 23 boundary 5 fixed\n"
        script += "13 23 24 boundary 5 fixed\n"
        script += "14 24 25 boundary 5 fixed\n"
        script += "15 25 26 boundary 5 fixed\n"
        script += "16 26 21 boundary 5 fixed\n"
        
        script += "// upper mask edges\n"
        script += "21 28 29 boundary 6 fixed\n"
        script += "22 29 30 boundary 6 fixed\n"
        script += "23 30 31 boundary 6 fixed\n"
        script += "24 31 32 boundary 6 fixed\n"
        script += "25 32 33 boundary 6 fixed\n"
        script += "26 33 28 boundary 6 fixed\n"
                
        script += "// upper pad edges\n"
        script += "31 8 9 boundary 2 fixed\n"
        script += "32 9 10 boundary 2 fixed\n"
        script += "33 10 11 boundary 2 fixed\n"
        script += "34 11 12 boundary 2 fixed\n"
        script += "35 12 13 boundary 2 fixed\n"
        script += "36 13 8 boundary 2 fixed\n"
        
        script += "// vertical edges between bottom and metal mask bottom\n"
        script += "41 1 21 no_refine\n"
        script += "42 2 22 no_refine\n"
        script += "43 3 23 no_refine\n"
        script += "44 4 24 no_refine\n"
        script += "45 5 25 no_refine\n"
        script += "46 6 26 no_refine\n"
        
        script += "// vertical edges between metal mask bottom and metal mask top\n"
        script += "51 21 28\n"
        script += "52 22 29\n"
        script += "53 23 30\n"
        script += "54 24 31\n"
        script += "55 25 32\n"
        script += "56 26 33\n"
        
        script += "// vertical edges between metal mask top and top\n"
        script += "61 28 8 no_refine\n"
        script += "62 29 9 no_refine\n"
        script += "63 30 10 no_refine\n"
        script += "64 31 11 no_refine\n"
        script += "65 32 12 no_refine\n"
        script += "66 33 13 no_refine\n"
        
        
                        
        script += "faces // defined by oriented edge loops to have outward normal\n"
        script += "// lateral faces bottom mask\n"
        script += "1 1 42 -11 -41 tension S_TENSION no_refine\n"
        script += "2 2 43 -12 -42 tension S_TENSION no_refine\n"
        script += "3 3 44 -13 -43 tension S_TENSION no_refine\n"
        script += "4 4 45 -14 -44 tension S_TENSION no_refine\n"
        script += "5 5 46 -15 -45 tension S_TENSION no_refine\n"
        script += "6 6 41 -16 -46 tension S_TENSION no_refine\n"
        
        script += "// lateral faces solder\n"
        script += "11 11 52 -21 -51 tension S_TENSION\n"
        script += "12 12 53 -22 -52 tension S_TENSION\n"
        script += "13 13 54 -23 -53 tension S_TENSION\n"
        script += "14 14 55 -24 -54 tension S_TENSION\n"
        script += "15 15 56 -25 -55 tension S_TENSION\n"
        script += "16 16 51 -26 -56 tension S_TENSION\n"
        
        script += "// lateral faces top mask\n"
        script += "21 21 62 -31 -61 tension S_TENSION no_refine\n"
        script += "22 22 63 -32 -62 tension S_TENSION no_refine\n"
        script += "23 23 64 -33 -63 tension S_TENSION no_refine\n"
        script += "24 24 65 -34 -64 tension S_TENSION no_refine\n"
        script += "25 25 66 -35 -65 tension S_TENSION no_refine\n"
        script += "26 26 61 -36 -66 tension S_TENSION no_refine\n"           
                  
        script += "// lower pad\n"
        script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
        script += "// upper pad\n"
        script += "8  31  32  33 34 35 36 fixed color green tension 0 constraint 2\n"
        script += "bodies // defined by oriented face list\n"
        if VOLUME <= 0.0:
            script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 21 22 23 24 25 26 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
            print("Current Volume is 0.0, so it is calculated by formula")
            volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
            
            print("Volume: ", volume)
        else:
            script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 21 22 23 24 25 26 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
            print("Volume is defined by user")
            print("Volume: ", VOLUME)
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        script += "read \"xyztorque.cmd\"\n"
        
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
     
        script += "logfile \"heightOptimized.txt\"\n"
        script += "print zt\n"
        script += "logfile\n"
        
        
        script += "q\n"
        script += "q\n"    
     
        
                
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, top_radius=top_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, stlFileName=self.stlFileName, height=1.0e-5, VOLUME=VOLUME, bmt=bmt, tmt=tmt, x_offset=x_offset, y_offset=y_offset, tilt=tilt, force=force)
        self.script = script    
        
    def SetScriptOptimizingHeight(self, bottom_point, bottom_radius, bottom_normal, top_point, top_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, force = 0.0, minDistance = 0.0):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]
        
        ntx, nty, ntz = top_normal
        ntLength = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntLength
        nty /= ntLength
        ntz /= ntLength
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        ntx /= nbLength
        nty /= nbLength
        ntz /= nbLength
        
        ax = 1
        ay = 1
        az = 1
        
        # cross product (ntx, nty, ntz) and (ax, ay, az)
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
                
        height = np.sqrt((xt-xb)**2 + (yt-yb)**2 + (zt-zb)**2) 
         
        x_offset = xt - xb
        y_offset = yt - yb
        #angle between top and bottom        
        tilt = nbx*ntx + nby*nty + nbz*ntz
        tilt /= (math.sqrt(nbx**2 + nby**2 + nbz**2) * math.sqrt(ntx**2 + nty**2 + ntz**2))
        if tilt > 1.0:
            tilt = 1.0
        elif tilt < -1.0:
            tilt = -1.0
        tilt = math.acos(tilt) * 180.0 / math.pi
                
        
        script = ""        
        script += "// bga-10.fe\n"
        script += "// Simple ball grid array joint.\n"
        script += "// Circular, tilting, non-coaxial wetted pads. With gravity.\n"
        script += "// Same as bga-8.fe, but with 2D lateral movement of upper pad\n"
        script += "// and tilting.\n"
        script += "// Upper pad represented with boundary.\n"
        script += "// Liquid entirely bounded by facets.\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "// physical constants, in cgs units\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}// cm\n"
        script += "parameter ntx = {ntx}     // cm\n"
        script += "parameter nty = {nty}     // cm\n"
        script += "parameter ntz = {ntz}     // cm\n"
        script += "parameter xt = {xt} - height*ntx    // cm\n"
        script += "parameter yt = {yt} - height*nty    // cm\n"
        #script += "parameter zt = {zt} - height*ntz    // cm\n"
        script += "optimizing_parameter zt = {zt} pdelta=1.0e-5 scale=1.0    // cm\n"
        
        script += "parameter x_offset = {x_offset}      // offset in x of upper pad\n"
        script += "parameter y_offset = {y_offset}   // offset in y of upper pad\n"
        script += "parameter tilt = {tilt}         // tilt about x-axis, degrees\n"
        
        script += "parameter force={force} // Newton\n"
        
        
        script += "//Gravity consideration\n"
        script += "quantity pad_energy energy method vertex_scalar_integral\n"
        script += "scalar_integrand : z*{force}\n"

        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        script += "// configuration parameters\n"        
        script += "// lower pad\n"
        script += "constraint 1\n"
        script += "formula: ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
        script += "// upper pad\n"
        script += "constraint 2\n"
        script += "formula: ({ntx})*(x-(xt))+({nty})*(y-(yt))+({ntz})*(z-(zt)) = 0\n"    
        script += "// metal mask bottom\n"
        script += "constraint 3\n"
        script += "formula: (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
        script += "// metal mask top\n"
        script += "constraint 4\n"
        script += "formula: (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"        
        
        script += "//Constraints for height\n"
        script += "constraint 5\n"
        script += "formula: z=zt\n"
              
        script += "// lower pad rim\n"
        script += "boundary 1 parameters 1\n"
        script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"   
        script += "// upper pad rim\n"
        script += "boundary 2 parameters 1\n"
        script += "x1: xt + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: yt + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: zt + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        script += "boundary 3 parameters 1\n"
        script += "x1: {xb}\n"
        script += "x2: {yb}\n"
        script += "x3: {zb}\n"
        script += "boundary 4 parameters 1\n"
        script += "x1: xt\n"
        script += "x2: yt\n"
        script += "x3: zt\n"
        
        script += "vertices\n"
        script += "// lower pad\n"
        script += "1 0*pi/3 boundary 1 fixed\n"
        script += "2 1*pi/3 boundary 1 fixed\n"
        script += "3 2*pi/3 boundary 1 fixed\n"
        script += "4 3*pi/3 boundary 1 fixed\n"
        script += "5 4*pi/3 boundary 1 fixed\n"
        script += "6 5*pi/3 boundary 1 fixed\n"

        script += "// upper pad\n"
        script += "8 0*pi/3 boundary 2 fixed\n"
        script += "9 1*pi/3 boundary 2 fixed\n"
        script += "10 2*pi/3 boundary 2 fixed\n"
        script += "11 3*pi/3 boundary 2 fixed\n"
        script += "12 4*pi/3 boundary 2 fixed\n"
        script += "13 5*pi/3 boundary 2 fixed\n"
        
        script += "99 0 0 zt constraint 5 fixed bare pad_energy\n"        

        script += "edges  // defined by endpoints\n"
        script += "// lower pad edges\n"
        script += "1 1 2 boundary 1 fixed\n"
        script += "2 2 3 boundary 1 fixed\n"
        script += "3 3 4 boundary 1 fixed\n"
        script += "4 4 5 boundary 1 fixed\n"
        script += "5 5 6 boundary 1 fixed\n"
        script += "6 6 1 boundary 1 fixed\n"
        
        script += "// upper pad edges\n"
        script += "31 8 9 boundary 2 fixed\n"
        script += "32 9 10 boundary 2 fixed\n"
        script += "33 10 11 boundary 2 fixed\n"
        script += "34 11 12 boundary 2 fixed\n"
        script += "35 12 13 boundary 2 fixed\n"
        script += "36 13 8 boundary 2 fixed\n"
        
        script += "// vertical edges between bottom and metal mask bottom\n"
        script += "41 1 8 \n"
        script += "42 2 9 \n"
        script += "43 3 10 \n"
        script += "44 4 11 \n"
        script += "45 5 12 \n"
        script += "46 6 13 \n"
                               
        script += "faces // defined by oriented edge loops to have outward normal\n"
        script += "// lateral faces bottom mask\n"
        script += "1 1 42 -31 -41 tension S_TENSION \n"
        script += "2 2 43 -32 -42 tension S_TENSION \n"
        script += "3 3 44 -33 -43 tension S_TENSION \n"
        script += "4 4 45 -34 -44 tension S_TENSION \n"
        script += "5 5 46 -35 -45 tension S_TENSION \n"
        script += "6 6 41 -36 -46 tension S_TENSION \n"
        
        script += "// lower pad\n"
        script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
        script += "// upper pad\n"
        script += "8  31  32  33 34 35 36 fixed color green tension 0 constraint 2\n"
        script += "bodies // defined by oriented face list\n"
        if VOLUME <= 0.0:
            script += "1 1 2 3 4 5 6 7 8 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
            print("Current Volume is 0.0, so it is calculated by formula")
            volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
            
            print("Volume: ", volume)
        else:
            script += "1 1 2 3 4 5 6 7 8 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
            print("Volume is defined by user")
            print("Volume: ", VOLUME)
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        script += "read \"xyztorque.cmd\"\n"
        
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        script += "g 100\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "logfile \"heightOptimized.txt\"\n"
        script += "print {initzt}\n"                
        script += "print sqrt((zt-({zb}))^2+(yt-({yb}))^2+(xt-({xb}))^2)\n"
        
        script += "logfile\n"
        
        
        script += "q\n"
        script += "q\n"    
     
        
                
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, top_radius=top_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, stlFileName=self.stlFileName, height=1.0e-5, VOLUME=VOLUME, x_offset=x_offset, y_offset=y_offset, tilt=tilt, force=force, initzt=height)
        self.script = script     
            
        
# None SMD Type
class NonSolderMaskedDefined(SolderJoint):
    def __init__(self, name, nodeMan : NodeManager = None, elementMan : ElementManager = None, partMan : KooPartManager = None, sectionMan : KooSectionManager = None, materialMan : KooMaterialManager = None, nodeSetMan : NodeSetManager = None, part = None):
        super(NonSolderMaskedDefined, self).__init__(name, nodeMan, elementMan, partMan, sectionMan, materialMan, nodeSetMan, part)
        self.bottom_point = [0, 0, 0]
        self.bottom_radius = 0.125
        self.bottom_normal = [0.0, 0.0, 1.0]
        self.top_point = [0, 0, 0.125]
        self.top_radius = 0.125
        self.top_normal = [0.0, 0.0, 1.0]
        self.topMaskThickness = 0.01
        self.bottomPadThickness = 0.01
        self.solderType = "NSMD"

    def SetBottomfromTwoPointsandCenter(self, point1, point2, pointCenter):
        x1, y1, z1 = point1.X(), point1.Y(), point1.Z()
        x2, y2, z2 = point2.X(), point2.Y(), point2.Z()
        xc, yc, zc = pointCenter.X(), pointCenter.Y(), pointCenter.Z()
        self.bottom_point = [xc, yc, zc]
        self.bottom_radius = math.sqrt((x1-xc)**2 + (y1-yc)**2 + (z1-zc)**2)
        ptc1 = gp_Vec(x1-xc, y1-yc, z1-zc)
        ptc2 = gp_Vec(x2-xc, y2-yc, z2-zc)
        normal = ptc1.Crossed(ptc2)
        normal.Normalize()
        self.bottom_normal = [normal.X(), normal.Y(), normal.Z()] 
        
    def SetTopfromTwoPointsandCenter(self, point1, point2, pointCenter):
        x1, y1, z1 = point1.X(), point1.Y(), point1.Z()
        x2, y2, z2 = point2.X(), point2.Y(), point2.Z()
        xc, yc, zc = pointCenter.X(), pointCenter.Y(), pointCenter.Z()
        self.top_point = [xc, yc, zc]
        self.top_radius = math.sqrt((x1-xc)**2 + (y1-yc)**2 + (z1-zc)**2)
        ptc1 = gp_Vec(x1-xc, y1-yc, z1-zc)
        ptc2 = gp_Vec(x2-xc, y2-yc, z2-zc)
        normal = ptc1.Crossed(ptc2)
        normal.Normalize()
        self.top_normal = [normal.X(), normal.Y(), normal.Z()]
        
            
    def SetBottom(self, point, radius, normal):
        self.bottom_point = point
        self.bottom_radius = radius
        self.bottom_normal = normal
        
    def SetTop(self, point, radius, normal):
        self.top_point = point
        self.top_radius = radius
        self.top_normal = normal
            
    def SetMaskThicknessTop(self, topMaskThickness):
        self.topMaskThickness = topMaskThickness
    
    def SetPadThicknessBottom(self, thickness):
        self.bottomPadThickness = thickness
    
    def SetScriptforHeight(self, force, minDistance = 0.0):
        return self.SetScriptOptimizingHeight(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, force, minDistance)
    
    def isNonWet(self,dh):
        distance = math.sqrt((self.top_point[0]-self.bottom_point[0])**2 + (self.top_point[1]-self.bottom_point[1])**2 + (self.top_point[2]-self.bottom_point[2])**2)
        if distance + dh > 1.5*self.bottom_radius + 1.5*self.top_radius:
            print("Distance between top and bottom is larger than sum of radius")
            return True
        else:
            return False
    
    def UpdateTopBallScript(self, dh):
        self.SetScriptTopBall(self.top_point, self.top_radius, self.bottom_radius, self.top_normal,self.S_TENSION, self.SOLDER_DENSITY, -self.GRAVITY, self.VOLUME, self.topMaskThickness, dh)
    
    def UpdateBottomBallScript(self):
        self.SetScriptBottomBall(self.bottom_point, self.bottom_radius, self.top_radius, self.bottom_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.bottomPadThickness)
        
    def UpdateScript(self, dh):                
                            
        if self.topMaskThickness == 0.0 and self.bottomPadThickness == 0.0:
            self.SetScriptwithMask(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.topMaskThickness, self.bottomPadThickness, dh)
            pass
        elif self.topMaskThickness == 0.0:
            self.SetScriptwithMask(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.topMaskThickness, self.bottomPadThickness, dh)
            pass
        elif self.bottomPadThickness == 0.0:
            self.SetScriptwithMask(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.topMaskThickness, self.bottomPadThickness, dh)
            pass
        else:
            self.SetScriptwithMask(self.bottom_point, self.bottom_radius, self.bottom_normal, self.top_point, self.top_radius, self.top_normal, self.S_TENSION, self.SOLDER_DENSITY, self.GRAVITY, self.VOLUME, self.topMaskThickness, self.bottomPadThickness, dh)
        
    def SetScriptTopBall(self, top_point, top_radius, bottom_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, topMaskThickness = 0.01, dh = 0.0):
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]        
        
        ntx, nty, ntz = top_normal
        ntNormal = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntNormal
        nty /= ntNormal
        ntz /= ntNormal
        xt = xt + ntx*dh
        yt = yt + nty*dh
        zt = zt + ntz*dh
        tmt = topMaskThickness
        ax, ay, az = 1, 1, 1
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        xb = xt - ntx*top_radius
        yb = yt - nty*top_radius
        zb = zt - ntz*top_radius
        
        xpt = xt - ntx*tmt
        ypt = yt - nty*tmt
        zpt = zt - ntz*tmt
        
        height = top_radius
                
            
        script = ""
        script += "// bga-10.fe\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}     // cm\n"
        script += "gravity_constant 0     // cm/sec^2\n"
        script += "// configuration parameters\n"
        
        
        if tmt == 0.0:
            script += "// upper top \n"
            script += "constraint 1\n"
            script += "formula : ({ntx})*(x-({xt}))+({nty})*(y-({yt}))+({ntz})*(z-({zt})) = 0\n"    
            script += "// metal mask cylinder\n"
            script += "constraint 3\n"
            script += "formula : (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"
            script += "// upper pad rim\n"
            script += "boundary 1 parameters 1\n"
            script += "x1: {xt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
            script += "x2: {yt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
            script += "x3: {zt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
                
            script += "vertices\n"
            
            script += "// lower vertices\n"        
            script += "1 {xb}+({top_radius})*cos(0*pi/3)*({utx})+({top_radius})*sin(0*pi/3)*({vtx}) {yb}+({top_radius})*cos(0*pi/3)*({uty})+({top_radius})*sin(0*pi/3)*({vty}) {zb}+({top_radius})*cos(0*pi/3)*({utz})+({top_radius})*sin(0*pi/3)*({vtz})\n"
            script += "2 {xb}+({top_radius})*cos(1*pi/3)*({utx})+({top_radius})*sin(1*pi/3)*({vtx}) {yb}+({top_radius})*cos(1*pi/3)*({uty})+({top_radius})*sin(1*pi/3)*({vty}) {zb}+({top_radius})*cos(1*pi/3)*({utz})+({top_radius})*sin(1*pi/3)*({vtz})\n"
            script += "3 {xb}+({top_radius})*cos(2*pi/3)*({utx})+({top_radius})*sin(2*pi/3)*({vtx}) {yb}+({top_radius})*cos(2*pi/3)*({uty})+({top_radius})*sin(2*pi/3)*({vty}) {zb}+({top_radius})*cos(2*pi/3)*({utz})+({top_radius})*sin(2*pi/3)*({vtz})\n"
            script += "4 {xb}+({top_radius})*cos(3*pi/3)*({utx})+({top_radius})*sin(3*pi/3)*({vtx}) {yb}+({top_radius})*cos(3*pi/3)*({uty})+({top_radius})*sin(3*pi/3)*({vty}) {zb}+({top_radius})*cos(3*pi/3)*({utz})+({top_radius})*sin(3*pi/3)*({vtz})\n"
            script += "5 {xb}+({top_radius})*cos(4*pi/3)*({utx})+({top_radius})*sin(4*pi/3)*({vtx}) {yb}+({top_radius})*cos(4*pi/3)*({uty})+({top_radius})*sin(4*pi/3)*({vty}) {zb}+({top_radius})*cos(4*pi/3)*({utz})+({top_radius})*sin(4*pi/3)*({vtz})\n"
            script += "6 {xb}+({top_radius})*cos(5*pi/3)*({utx})+({top_radius})*sin(5*pi/3)*({vtx}) {yb}+({top_radius})*cos(5*pi/3)*({uty})+({top_radius})*sin(5*pi/3)*({vty}) {zb}+({top_radius})*cos(5*pi/3)*({utz})+({top_radius})*sin(5*pi/3)*({vtz})\n"
            
            script += "// metal mask top vertices\n"
            script += "11 0*pi/3 boundary 1 fixed\n"
            script += "12 1*pi/3 boundary 1 fixed\n"
            script += "13 2*pi/3 boundary 1 fixed\n"
            script += "14 3*pi/3 boundary 1 fixed\n"
            script += "15 4*pi/3 boundary 1 fixed\n"
            script += "16 5*pi/3 boundary 1 fixed\n"
            
            script += "edges  // defined by endpoints\n"
            script += "// lower edges\n"
            script += "1 1 2\n"
            script += "2 2 3\n"
            script += "3 3 4\n"
            script += "4 4 5\n"
            script += "5 5 6\n"
            script += "6 6 1\n"
            
            script += "// mask top edges\n"
            script += "11 11 12 boundary 1 fixed\n"
            script += "12 12 13 boundary 1 fixed\n"
            script += "13 13 14 boundary 1 fixed\n"
            script += "14 14 15 boundary 1 fixed\n"
            script += "15 15 16 boundary 1 fixed\n"
            script += "16 16 11 boundary 1 fixed\n"
            
            script += "//vertical edges between bottom and metal mask bottom\n"
            script += "21 1 11\n"
            script += "22 2 12\n"
            script += "23 3 13\n"
            script += "24 4 14\n"
            script += "25 5 15\n"
            script += "26 6 16\n"
            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces bottom mask\n"
            script += "1 1 22 -11 -21 tension S_TENSION \n"
            script += "2 2 23 -12 -22 tension S_TENSION \n"
            script += "3 3 24 -13 -23 tension S_TENSION \n"
            script += "4 4 25 -14 -24 tension S_TENSION \n"
            script += "5 5 26 -15 -25 tension S_TENSION \n"
            script += "6 6 21 -16 -26 tension S_TENSION \n"
            
            script += "// lower pad\n"
            script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension S_TENSION\n"
            script += "// upper pad\n"
            script += "8  11  12  13 14 15 16 fixed color green tension 0 constraint 1\n"
            script += "bodies // defined by oriented face list\n"
            volumeBottom = bottom_radius**3
            volumeTop = top_radius**3
            volumeRatio = volumeTop/(volumeBottom+volumeTop)
            if VOLUME<=0.0:
                script += "1 1 2 3 4 5 6 7 8 volume 1.3*pi*({top_radius})^2*({volume_ratio})*height density SOLDER_DENSITY\n"
                volume = 1.3*math.pi*top_radius**2*volumeRatio*height
                print("Volume: ", volume)
            else:
                volume = VOLUME*volumeRatio
                script += "1 1 2 3 4 5 6 7 8 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=volume)
                print("Volume: ", volume)                
            pass
        else:
                    
            script += "// upper top \n"
            script += "constraint 1\n"
            script += "formula : ({ntx})*(x-({xt}))+({nty})*(y-({yt}))+({ntz})*(z-({zt})) = 0\n"    
            script += "// metal mask cylinder\n"
            script += "constraint 3\n"
            script += "formula : (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"
            script += "// metal mask top\n"
            script += "constraint 5\n"
            script += "formula : ({ntx})*(x-({xpt}))+({nty})*(y-({ypt}))+({ntz})*(z-({zpt})) = 0\n"
            
            script += "// upper pad rim\n"
            script += "boundary 1 parameters 1\n"
            script += "x1: {xt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
            script += "x2: {yt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
            script += "x3: {zt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
            
            script += "// upper pad mask\n"
            script += "boundary 3 parameters 1\n"
            script += "x1: {xpt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
            script += "x2: {ypt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
            script += "x3: {zpt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
            
            script += "vertices\n"
            
            script += "// lower vertices\n"        
            script += "1 {xb}+({top_radius})*cos(0*pi/3)*({utx})+({top_radius})*sin(0*pi/3)*({vtx}) {yb}+({top_radius})*cos(0*pi/3)*({uty})+({top_radius})*sin(0*pi/3)*({vty}) {zb}+({top_radius})*cos(0*pi/3)*({utz})+({top_radius})*sin(0*pi/3)*({vtz})\n"
            script += "2 {xb}+({top_radius})*cos(1*pi/3)*({utx})+({top_radius})*sin(1*pi/3)*({vtx}) {yb}+({top_radius})*cos(1*pi/3)*({uty})+({top_radius})*sin(1*pi/3)*({vty}) {zb}+({top_radius})*cos(1*pi/3)*({utz})+({top_radius})*sin(1*pi/3)*({vtz})\n"
            script += "3 {xb}+({top_radius})*cos(2*pi/3)*({utx})+({top_radius})*sin(2*pi/3)*({vtx}) {yb}+({top_radius})*cos(2*pi/3)*({uty})+({top_radius})*sin(2*pi/3)*({vty}) {zb}+({top_radius})*cos(2*pi/3)*({utz})+({top_radius})*sin(2*pi/3)*({vtz})\n"
            script += "4 {xb}+({top_radius})*cos(3*pi/3)*({utx})+({top_radius})*sin(3*pi/3)*({vtx}) {yb}+({top_radius})*cos(3*pi/3)*({uty})+({top_radius})*sin(3*pi/3)*({vty}) {zb}+({top_radius})*cos(3*pi/3)*({utz})+({top_radius})*sin(3*pi/3)*({vtz})\n"
            script += "5 {xb}+({top_radius})*cos(4*pi/3)*({utx})+({top_radius})*sin(4*pi/3)*({vtx}) {yb}+({top_radius})*cos(4*pi/3)*({uty})+({top_radius})*sin(4*pi/3)*({vty}) {zb}+({top_radius})*cos(4*pi/3)*({utz})+({top_radius})*sin(4*pi/3)*({vtz})\n"
            script += "6 {xb}+({top_radius})*cos(5*pi/3)*({utx})+({top_radius})*sin(5*pi/3)*({vtx}) {yb}+({top_radius})*cos(5*pi/3)*({uty})+({top_radius})*sin(5*pi/3)*({vty}) {zb}+({top_radius})*cos(5*pi/3)*({utz})+({top_radius})*sin(5*pi/3)*({vtz})\n"
            
            script += "// metal mask bottom vertices\n"
            script += "11 0*pi/3 boundary 3 fixed\n"
            script += "12 1*pi/3 boundary 3 fixed\n"
            script += "13 2*pi/3 boundary 3 fixed\n"
            script += "14 3*pi/3 boundary 3 fixed\n"
            script += "15 4*pi/3 boundary 3 fixed\n"
            script += "16 5*pi/3 boundary 3 fixed\n"   
            
            script += "// metal mask top vertices\n"
            script += "21 0*pi/3 boundary 1 fixed\n"
            script += "22 1*pi/3 boundary 1 fixed\n"
            script += "23 2*pi/3 boundary 1 fixed\n"
            script += "24 3*pi/3 boundary 1 fixed\n"
            script += "25 4*pi/3 boundary 1 fixed\n"
            script += "26 5*pi/3 boundary 1 fixed\n"
            
            script += "edges  // defined by endpoints\n"
            script += "// lower edges\n"
            script += "1 1 2\n"
            script += "2 2 3\n"
            script += "3 3 4\n"
            script += "4 4 5\n"
            script += "5 5 6\n"
            script += "6 6 1\n"
            
            script += "// mask bottom edges\n"
            script += "11 11 12 boundary 3 fixed\n"
            script += "12 12 13 boundary 3 fixed\n"
            script += "13 13 14 boundary 3 fixed\n"
            script += "14 14 15 boundary 3 fixed\n"
            script += "15 15 16 boundary 3 fixed\n"
            script += "16 16 11 boundary 3 fixed\n"
            
            script += "// mask top edges\n"
            script += "21 21 22 boundary 1 fixed\n"
            script += "22 22 23 boundary 1 fixed\n"
            script += "23 23 24 boundary 1 fixed\n"
            script += "24 24 25 boundary 1 fixed\n"
            script += "25 25 26 boundary 1 fixed\n"
            script += "26 26 21 boundary 1 fixed\n"
            
            script += "//vertical edges between bottom and metal mask bottom\n"
            script += "31 1 11\n"
            script += "32 2 12\n"
            script += "33 3 13\n"
            script += "34 4 14\n"
            script += "35 5 15\n"
            script += "36 6 16\n"
            
            script += "//vertical edges between metal mask bottom and top\n"
            script += "41 11 21 no_refine\n"
            script += "42 12 22 no_refine\n"
            script += "43 13 23 no_refine\n"
            script += "44 14 24 no_refine\n"
            script += "45 15 25 no_refine\n"
            script += "46 16 26 no_refine\n"
            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces bottom mask\n"
            script += "1 1 32 -11 -31 tension S_TENSION \n"
            script += "2 2 33 -12 -32 tension S_TENSION \n"
            script += "3 3 34 -13 -33 tension S_TENSION \n"
            script += "4 4 35 -14 -34 tension S_TENSION \n"
            script += "5 5 36 -15 -35 tension S_TENSION \n"
            script += "6 6 31 -16 -36 tension S_TENSION \n"
            
            script += "// lateral faces top mask\n"
            script += "7 11 42 -21 -41 tension 0 no_refine fixed\n"
            script += "8 12 43 -22 -42 tension 0 no_refine fixed\n"
            script += "9 13 44 -23 -43 tension 0 no_refine fixed\n"
            script += "10 14 45 -24 -44 tension 0 no_refine fixed\n"
            script += "11 15 46 -25 -45 tension 0 no_refine fixed\n"
            script += "12 16 41 -26 -46 tension 0 no_refine fixed\n"
            
            script += "// lower pad\n"
            script += "13 -6 -5 -4 -3 -2 -1 fixed color red tension S_TENSION\n"
            script += "// upper pad\n"
            script += "14 21 22 23 24 25 26 fixed color green tension 0 constraint 1\n"
            script += "bodies\n"
            volumeBottom = bottom_radius**3
            volumeTop = top_radius**3
            volumeRatio = volumeTop/(volumeBottom+volumeTop)
            if VOLUME<=0.0:
                script += "1 1 2 3 4 5 6 7 8 9 10 11 12 13 14 volume 1.3*pi*({top_radius})^2*({volume_ratio})*height density SOLDER_DENSITY\n"
                volume = 1.3*math.pi*top_radius**2*volumeRatio*height
                print("Volume: ", volume)
            else:
                volume = VOLUME*volumeRatio
                script += "1 1 2 3 4 5 6 7 8 9 10 11 12 13 14 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=volume)
                print("Volume: ", volume)
                
                
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        #script += "read \"xyztorque.cmd\"\n"
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        script += "g 100\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "q\n"
        script += "q\n"
            
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, xpt=xpt, ypt=ypt, zpt=zpt, height=height, stlFileName=self.stlFileName, volume_ratio=volumeRatio, top_radius = top_radius)
        
        self.script = script
        
        
        
        
            
    def SetScriptBottomBall(self, bottom_point, bottom_radius, top_radius, bottom_normal,S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, bottom_pad_thickness = 0.01):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        nbx /= nbLength
        nby /= nbLength
        nbz /= nbLength
        bpt = bottom_pad_thickness
        
        ax, ay, az = 1, 1, 1
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
        
        xt = xb + nbx*bottom_radius
        yt = yb + nby*bottom_radius
        zt = zb + nbz*bottom_radius
        
        
        xpb = xb - nbx*bpt
        ypb = yb - nby*bpt
        zpb = zb - nbz*bpt
        height = bottom_radius
        script  = ""
        script += "// bga-10.fe\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}     // cm\n"
        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        
        script += "// configuration parameters\n"
        
        if bottom_pad_thickness == 0.0:
            script += "// lower pad\n"
            script += "constraint 1\n"
            script += "formula : ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
            script += "// metal mask bottom\n"
            script += "constraint 3\n"
            script += "formula : (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
            
            script += "// lower pad rim\n"
            script += "boundary 1 parameters 1\n"
            script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
            script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
            script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
                
            script += "vertices\n"
            
            script += "// lower pad internal\n"
            script += "1 0*pi/3 boundary 1 fixed\n"
            script += "2 1*pi/3 boundary 1 fixed\n"
            script += "3 2*pi/3 boundary 1 fixed\n"
            script += "4 3*pi/3 boundary 1 fixed\n"
            script += "5 4*pi/3 boundary 1 fixed\n"
            script += "6 5*pi/3 boundary 1 fixed\n"                        
            
            script += "// top vertex\n"
            script += "11 {xt}+({bottom_radius})*cos(0*pi/3)*({ubx})+({bottom_radius})*sin(0*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(0*pi/3)*({uby})+({bottom_radius})*sin(0*pi/3)*({vby}) {zt}+({bottom_radius})*cos(0*pi/3)*({ubz})+({bottom_radius})*sin(0*pi/3)*({vbz})\n"
            script += "12 {xt}+({bottom_radius})*cos(1*pi/3)*({ubx})+({bottom_radius})*sin(1*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(1*pi/3)*({uby})+({bottom_radius})*sin(1*pi/3)*({vby}) {zt}+({bottom_radius})*cos(1*pi/3)*({ubz})+({bottom_radius})*sin(1*pi/3)*({vbz})\n"
            script += "13 {xt}+({bottom_radius})*cos(2*pi/3)*({ubx})+({bottom_radius})*sin(2*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(2*pi/3)*({uby})+({bottom_radius})*sin(2*pi/3)*({vby}) {zt}+({bottom_radius})*cos(2*pi/3)*({ubz})+({bottom_radius})*sin(2*pi/3)*({vbz})\n"
            script += "14 {xt}+({bottom_radius})*cos(3*pi/3)*({ubx})+({bottom_radius})*sin(3*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(3*pi/3)*({uby})+({bottom_radius})*sin(3*pi/3)*({vby}) {zt}+({bottom_radius})*cos(3*pi/3)*({ubz})+({bottom_radius})*sin(3*pi/3)*({vbz})\n"
            script += "15 {xt}+({bottom_radius})*cos(4*pi/3)*({ubx})+({bottom_radius})*sin(4*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(4*pi/3)*({uby})+({bottom_radius})*sin(4*pi/3)*({vby}) {zt}+({bottom_radius})*cos(4*pi/3)*({ubz})+({bottom_radius})*sin(4*pi/3)*({vbz})\n"
            script += "16 {xt}+({bottom_radius})*cos(5*pi/3)*({ubx})+({bottom_radius})*sin(5*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(5*pi/3)*({uby})+({bottom_radius})*sin(5*pi/3)*({vby}) {zt}+({bottom_radius})*cos(5*pi/3)*({ubz})+({bottom_radius})*sin(5*pi/3)*({vbz})\n"
            
            
            script += "edges  // defined by endpoints\n"
            script += "// lower pad internal\n"
            script += "1 1 2 boundary 1 fixed\n"
            script += "2 2 3 boundary 1 fixed\n"
            script += "3 3 4 boundary 1 fixed\n"
            script += "4 4 5 boundary 1 fixed\n"
            script += "5 5 6 boundary 1 fixed\n"
            script += "6 6 1 boundary 1 fixed\n"
            
            script += "// lower pad bottom\n"
            script += "11 11 12\n"
            script += "12 12 13\n"
            script += "13 13 14\n"
            script += "14 14 15\n"
            script += "15 15 16\n"
            script += "16 16 11\n"
            
            script += "//vertical edges between low pad internal and low pad bottom\n"
            script += "21 1 11\n"
            script += "22 2 12\n"
            script += "23 3 13\n"
            script += "24 4 14\n"
            script += "25 5 15\n"
            script += "26 6 16\n"
            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces between low pad internal and low pad bottom\n"
            script += "1 1 22 -11 -21 tension S_TENSION \n" 
            script += "2 2 23 -12 -22 tension S_TENSION \n"
            script += "3 3 24 -13 -23 tension S_TENSION \n"
            script += "4 4 25 -14 -24 tension S_TENSION \n"
            script += "5 5 26 -15 -25 tension S_TENSION \n"
            script += "6 6 21 -16 -26 tension S_TENSION \n"
            
            
            script += "// lower pad internal\n"
            script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
            script += "// upper\n"
            script += "8  11  12  13 14 15 16 color green tension S_TENSION\n"
            script += "bodies // defined by oriented face list\n"
            
            volumeBottom = bottom_radius**3
            volumeTop = top_radius**3
            volumeRatio = volumeBottom/(volumeTop+volumeBottom)
            if VOLUME <= 0.0:
                script += "1 1 2 3 4 5 6 7 8 volume 1.3*pi*({bottom_radius})^2*({volume_ratio})*height density SOLDER_DENSITY\n"
                
                volume = 1.3*math.pi*bottom_radius**2*height*volumeRatio
                print("Volume: ", volume)
            else:
                volume = VOLUME*volumeRatio
                script += "1 1 2 3 4 5 6 7 8 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=volume)
                print("Volume: ", volume)
            
        else:
            
            script += "// lower pad\n"
            script += "constraint 1\n"
            script += "formula : ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
            script += "// metal mask bottom\n"
            script += "constraint 3\n"
            script += "formula : (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
            script += "//lower pad bottom \n"
            script += "constraint 5\n"
            script += "formula : ({nbx})*(x-({xpb}))+({nby})*(y-({ypb}))+({nbz})*(z-({zpb})) = 0\n"
            
            script += "// lower pad rim\n"
            script += "boundary 1 parameters 1\n"
            script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
            script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
            script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
            
            script += "// lower pad mask\n"
            script += "boundary 3 parameters 1\n"
            script += "x1: {xpb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
            script += "x2: {ypb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
            script += "x3: {zpb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
            
            script += "// lower pad radius offset \n"
            script += "boundary 5 parameters 1\n"
            script += "x1: {xb} + ({bottom_radius}+{bpt})*cos(p1)*({ubx}) + ({bottom_radius}+{bpt})*sin(p1)*({vbx})\n"        
            script += "x2: {yb} + ({bottom_radius}+{bpt})*cos(p1)*({uby}) + ({bottom_radius}+{bpt})*sin(p1)*({vby})\n"
            script += "x3: {zb} + ({bottom_radius}+{bpt})*cos(p1)*({ubz}) + ({bottom_radius}+{bpt})*sin(p1)*({vbz})\n"
                
            script += "vertices\n"
            
            script += "// lower pad internal\n"
            script += "1 0*pi/3 boundary 1 fixed\n"
            script += "2 1*pi/3 boundary 1 fixed\n"
            script += "3 2*pi/3 boundary 1 fixed\n"
            script += "4 3*pi/3 boundary 1 fixed\n"
            script += "5 4*pi/3 boundary 1 fixed\n"
            script += "6 5*pi/3 boundary 1 fixed\n"
            
            script += "// lower pad bottom\n"
            script += "11 0*pi/3 boundary 3 fixed\n"   
            script += "12 1*pi/3 boundary 3 fixed\n"
            script += "13 2*pi/3 boundary 3 fixed\n"
            script += "14 3*pi/3 boundary 3 fixed\n"
            script += "15 4*pi/3 boundary 3 fixed\n"
            script += "16 5*pi/3 boundary 3 fixed\n"
            
            script += "// lower pad external\n"
            script += "21 0*pi/3 boundary 5 fixed\n"
            script += "22 1*pi/3 boundary 5 fixed\n"
            script += "23 2*pi/3 boundary 5 fixed\n"
            script += "24 3*pi/3 boundary 5 fixed\n"
            script += "25 4*pi/3 boundary 5 fixed\n"
            script += "26 5*pi/3 boundary 5 fixed\n"
            
            script += "// top vertex\n"
            script += "31 {xt}+({bottom_radius})*cos(0*pi/3)*({ubx})+({bottom_radius})*sin(0*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(0*pi/3)*({uby})+({bottom_radius})*sin(0*pi/3)*({vby}) {zt}+({bottom_radius})*cos(0*pi/3)*({ubz})+({bottom_radius})*sin(0*pi/3)*({vbz})\n"
            script += "32 {xt}+({bottom_radius})*cos(1*pi/3)*({ubx})+({bottom_radius})*sin(1*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(1*pi/3)*({uby})+({bottom_radius})*sin(1*pi/3)*({vby}) {zt}+({bottom_radius})*cos(1*pi/3)*({ubz})+({bottom_radius})*sin(1*pi/3)*({vbz})\n"
            script += "33 {xt}+({bottom_radius})*cos(2*pi/3)*({ubx})+({bottom_radius})*sin(2*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(2*pi/3)*({uby})+({bottom_radius})*sin(2*pi/3)*({vby}) {zt}+({bottom_radius})*cos(2*pi/3)*({ubz})+({bottom_radius})*sin(2*pi/3)*({vbz})\n"
            script += "34 {xt}+({bottom_radius})*cos(3*pi/3)*({ubx})+({bottom_radius})*sin(3*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(3*pi/3)*({uby})+({bottom_radius})*sin(3*pi/3)*({vby}) {zt}+({bottom_radius})*cos(3*pi/3)*({ubz})+({bottom_radius})*sin(3*pi/3)*({vbz})\n"
            script += "35 {xt}+({bottom_radius})*cos(4*pi/3)*({ubx})+({bottom_radius})*sin(4*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(4*pi/3)*({uby})+({bottom_radius})*sin(4*pi/3)*({vby}) {zt}+({bottom_radius})*cos(4*pi/3)*({ubz})+({bottom_radius})*sin(4*pi/3)*({vbz})\n"
            script += "36 {xt}+({bottom_radius})*cos(5*pi/3)*({ubx})+({bottom_radius})*sin(5*pi/3)*({vbx}) {yt}+({bottom_radius})*cos(5*pi/3)*({uby})+({bottom_radius})*sin(5*pi/3)*({vby}) {zt}+({bottom_radius})*cos(5*pi/3)*({ubz})+({bottom_radius})*sin(5*pi/3)*({vbz})\n"
            
            
            script += "edges  // defined by endpoints\n"
            script += "// lower pad internal\n"
            script += "1 1 2 boundary 1 fixed\n"
            script += "2 2 3 boundary 1 fixed\n"
            script += "3 3 4 boundary 1 fixed\n"
            script += "4 4 5 boundary 1 fixed\n"
            script += "5 5 6 boundary 1 fixed\n"
            script += "6 6 1 boundary 1 fixed\n"
            
            script += "// lower pad bottom\n"
            script += "11 11 12 boundary 3 fixed\n"
            script += "12 12 13 boundary 3 fixed\n"
            script += "13 13 14 boundary 3 fixed\n"
            script += "14 14 15 boundary 3 fixed\n"
            script += "15 15 16 boundary 3 fixed\n"
            script += "16 16 11 boundary 3 fixed\n"
            
            script += "// lower pad external\n"
            script += "21 21 22 boundary 5 \n"
            script += "22 22 23 boundary 5 \n"
            script += "23 23 24 boundary 5 \n"
            script += "24 24 25 boundary 5 \n"
            script += "25 25 26 boundary 5 \n"
            script += "26 26 21 boundary 5 \n"
            
            script += "// upper edges\n"
            script += "31 31 32\n"
            script += "32 32 33\n"
            script += "33 33 34\n"
            script += "34 34 35\n"
            script += "35 35 36\n"
            script += "36 36 31\n"
            
            script += "//vertical edges between low pad internal and low pad bottom\n"
            script += "41 1 11 no_refine\n"
            script += "42 2 12 no_refine\n"
            script += "43 3 13 no_refine\n"
            script += "44 4 14 no_refine\n"
            script += "45 5 15 no_refine\n"
            script += "46 6 16 no_refine\n"
            
            script += "//vertical edges between low pad bottom and low pad external\n"
            script += "51 11 21 no_refine\n"
            script += "52 12 22 no_refine\n"
            script += "53 13 23 no_refine\n"
            script += "54 14 24 no_refine\n"
            script += "55 15 25 no_refine\n"
            script += "56 16 26 no_refine\n"
            
            script += "//vertical edges between low pad external and top vertex\n"
            script += "61 21 31\n"
            script += "62 22 32\n"
            script += "63 23 33\n"
            script += "64 24 34\n"
            script += "65 25 35\n"
            script += "66 26 36\n"
            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces between low pad internal and low pad bottom\n"
            script += "1 1 42 -11 -41 tension S_TENSION no_refine fixed\n" 
            script += "2 2 43 -12 -42 tension S_TENSION no_refine fixed\n"
            script += "3 3 44 -13 -43 tension S_TENSION no_refine fixed\n"
            script += "4 4 45 -14 -44 tension S_TENSION no_refine fixed\n"
            script += "5 5 46 -15 -45 tension S_TENSION no_refine fixed\n"
            script += "6 6 41 -16 -46 tension S_TENSION no_refine fixed\n"
            
            
            script += "// lateral faces between low pad bottom and low pad external\n"
            script += "11 11 52 -21 -51 tension S_TENSION no_refine\n"
            script += "12 12 53 -22 -52 tension S_TENSION no_refine\n"
            script += "13 13 54 -23 -53 tension S_TENSION no_refine\n"
            script += "14 14 55 -24 -54 tension S_TENSION no_refine\n"
            script += "15 15 56 -25 -55 tension S_TENSION no_refine\n"
            script += "16 16 51 -26 -56 tension S_TENSION no_refine\n"
                    
            script += "// lateral faces between low pad external and top vertex\n"
            script += "21 21 62 -31 -61 tension S_TENSION \n"
            script += "22 22 63 -32 -62 tension S_TENSION \n"
            script += "23 23 64 -33 -63 tension S_TENSION \n"
            script += "24 24 65 -34 -64 tension S_TENSION \n"
            script += "25 25 66 -35 -65 tension S_TENSION \n"
            script += "26 26 61 -36 -66 tension S_TENSION \n"
                            
            script += "// lower pad internal\n"
            script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
            script += "// upper\n"
            script += "8  31  32  33 34 35 36 color green tension S_TENSION\n"
            script += "bodies // defined by oriented face list\n"
            volumeBottom = bottom_radius**3
            volumeTop = top_radius**3
            volumeRatio = volumeBottom/(volumeTop+volumeBottom)
            if VOLUME <= 0.0:
                script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 21 22 23 24 25 26 volume 1.3*pi*({bottom_radius})^2*({volume_ratio})*height density SOLDER_DENSITY\n"
                
                volume = 1.3*math.pi*bottom_radius**2*height*volumeRatio
                print("Volume: ", volume)
            else:
                volume = VOLUME*volumeRatio
                script += "1 1 2 3 4 5 6 7 8 11 12 13 14 15 16 21 22 23 24 25 26 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=volume)
                print("Volume: ", volume)
        
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        #script += "read \"xyztorque.cmd\"\n"
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        script += "g 100\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "q\n"
        script += "q\n"
        
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, xpb=xpb, ypb=ypb, zpb=zpb, height=height, bottom_pad_thickness=bottom_pad_thickness, stlFileName=self.stlFileName, volume_ratio=volumeRatio, bpt = bpt)
        self.script = script 
        
            
    
    def SetScriptwithMask(self,bottom_point, bottom_radius, bottom_normal, top_point, top_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, topMaskThickness = 0.01, bottomPadThickness = 0.01, dh = 0.0):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]
        ntx, nty, ntz = top_normal
        nbx, nby, nbz = bottom_normal
        ntLength = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntLength
        nty /= ntLength
        ntz /= ntLength
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        ntx /= nbLength
        nty /= nbLength
        ntz /= nbLength
        xt = xt + ntx*dh
        yt = yt + nty*dh
        zt = zt + ntz*dh
        
        ax = 1
        ay = 1
        az = 1
        
        # cross product (ntx, nty, ntz) and (ax, ay, az)
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
        
        bpt = bottomPadThickness
        tmt = topMaskThickness
        
        xpb = xb - nbx*bpt
        ypb = yb - nby*bpt
        zpb = zb - nbz*bpt
        
        xmt = xt - ntx*tmt
        ymt = yt - nty*tmt
        zmt = zt - ntz*tmt
        
        
        height = np.sqrt((xt-xb)**2 + (yt-yb)**2 + (zt-zb)**2) 
         
        x_offset = xt - xb
        y_offset = yt - yb
        #angle between top and bottom        
        tilt = nbx*ntx + nby*nty + nbz*ntz
        tilt /= (math.sqrt(nbx**2 + nby**2 + nbz**2) * math.sqrt(ntx**2 + nty**2 + ntz**2))
        if tilt > 1.0:
            tilt = 1.0
        elif tilt < -1.0:
            tilt = -1.0
        tilt = math.acos(tilt) * 180.0 / math.pi
        
        
        self.topPointLists = []
        self.bottomPointLists = []
        
        for i in range(1):
            p1 = i*math.pi/3.0
            curXbot = xb +bottom_radius*math.cos(p1)*(ubx) + (bottom_radius)*math.sin(p1)*(vbx)
            curYbot = yb +bottom_radius*math.cos(p1)*(uby) + (bottom_radius)*math.sin(p1)*(vby)
            curZbot = zb +bottom_radius*math.cos(p1)*(ubz) + (bottom_radius)*math.sin(p1)*(vbz)
            
            curXtop = xt +top_radius*math.cos(p1)*(utx) + (top_radius)*math.sin(p1)*(vtx)
            curYtop = yt +top_radius*math.cos(p1)*(uty) + (top_radius)*math.sin(p1)*(vty)
            curZtop = zt +top_radius*math.cos(p1)*(utz) + (top_radius)*math.sin(p1)*(vtz)
            #self.topPointLists.append(gp_Pnt(curXtop, curYtop, curZtop))
            #self.bottomPointLists.append(gp_Pnt(curXbot, curYbot, curZbot))
            self.topPointLists.append(gp_Pnt(xt, yt, zt))
            self.bottomPointLists.append(gp_Pnt(xb, yb, zb))
        script = ""
        script += "// bga-10.fe\n"
        script += "// Simple ball grid array joint.\n"
        script += "// Circular, tilting, non-coaxial wetted pads. With gravity.\n"
        script += "// Same as bga-8.fe, but with 2D lateral movement of upper pad\n"
        script += "// and tilting.\n"
        script += "// Upper pad represented with boundary.\n"
        script += "// Liquid entirely bounded by facets.\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "// physical constants, in cgs units\n"        
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"    
        script += "parameter height = {height}     // cm\n"
        script += "parameter x_offset = {x_offset}      // offset in x of upper pad\n"
        script += "parameter y_offset = {y_offset}   // offset in y of upper pad\n"
        script += "parameter tilt = {tilt}         // tilt about x-axis, degrees\n"        
        script += "// configuration parameters\n"        
        script += "// lower pad\n"
        script += "constraint 1\n"
        script += "formula: ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
        script += "// upper pad\n"
        script += "constraint 2\n"
        script += "formula: ({ntx})*(x-({xt}))+({nty})*(y-({yt}))+({ntz})*(z-({zt})) = 0\n"    
        script += "// metal mask bottom\n"
        script += "constraint 3\n"
        script += "formula: (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
        script += "// metal mask top\n"
        script += "constraint 4\n"
        script += "formula: (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"  
        script += "// lower pad bottom\n"
        script += "constraint 5\n"
        script += "formula: ({nbx})*(x-({xpb}))+({nby})*(y-({ypb}))+({nbz})*(z-({zpb})) = 0\n"              
            
        script += "// lower pad rim\n"
        script += "boundary 1 parameters 1\n"
        script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"   
        script += "// upper pad rim\n"
        script += "boundary 2 parameters 1\n"
        script += "x1: {xt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: {yt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: {zt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"

        script += "// lower pad mask\n"
        script += "boundary 5 parameters 1\n"
        script += "x1: {xpb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {ypb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zpb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"
        script += "boundary 6 parameters 1\n"
        script += "x1: {xmt} + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: {ymt} + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: {zmt} + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        
        script += "// lower pad radius offset\n"
        script += "boundary 7 parameters 1\n"
        script += "x1: {xb} + ({bottom_radius}+{bpt})*cos(p1)*({ubx}) + ({bottom_radius}+{bpt})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + ({bottom_radius}+{bpt})*cos(p1)*({uby}) + ({bottom_radius}+{bpt})*sin(p1)*({vby})\n"
        script += "x3: {zb} + ({bottom_radius}+{bpt})*cos(p1)*({ubz}) + ({bottom_radius}+{bpt})*sin(p1)*({vbz})\n"
        if bpt == 0.0 and tmt == 0.0:            
            script += "vertices\n"
            
            script += "// lower pad internal\n"
            script += "1 0*pi/3 boundary 1 fixed\n"
            script += "2 1*pi/3 boundary 1 fixed\n"
            script += "3 2*pi/3 boundary 1 fixed\n"
            script += "4 3*pi/3 boundary 1 fixed\n"
            script += "5 4*pi/3 boundary 1 fixed\n"
            script += "6 5*pi/3 boundary 1 fixed\n"
            
            script += "// lower pad bottom\n"
            script += "11 0*pi/3 boundary 2 fixed\n"
            script += "12 1*pi/3 boundary 2 fixed\n"
            script += "13 2*pi/3 boundary 2 fixed\n"
            script += "14 3*pi/3 boundary 2 fixed\n"
            script += "15 4*pi/3 boundary 2 fixed\n"
            script += "16 5*pi/3 boundary 2 fixed\n"
                                                                
            
            script += "edges  // defined by endpoints\n"
            script += "// lower pad internal edges\n"
            script += "1 1 2 boundary 1 fixed\n"
            script += "2 2 3 boundary 1 fixed\n"
            script += "3 3 4 boundary 1 fixed\n"
            script += "4 4 5 boundary 1 fixed\n"
            script += "5 5 6 boundary 1 fixed\n"
            script += "6 6 1 boundary 1 fixed\n"
            
            script += "// lower pad bottom edges\n"
            script += "11 11 12 boundary 2 fixed\n"
            script += "12 12 13 boundary 2 fixed\n"
            script += "13 13 14 boundary 2 fixed\n"
            script += "14 14 15 boundary 2 fixed\n"
            script += "15 15 16 boundary 2 fixed\n"
            script += "16 16 11 boundary 2 fixed\n"                        
            
            script += "// vertical edges between low pad internal and low pad bottom\n"
            script += "21 1 11\n"
            script += "22 2 12\n"
            script += "23 3 13\n"
            script += "24 4 14\n"
            script += "25 5 15\n"
            script += "26 6 16\n"            
                            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces between low pad internal and low pad bottom\n"
            script += "1 1 22 -11 -21 tension S_TENSION \n"
            script += "2 2 23 -12 -22 tension S_TENSION \n"
            script += "3 3 24 -13 -23 tension S_TENSION \n"
            script += "4 4 25 -14 -24 tension S_TENSION \n"
            script += "5 5 26 -15 -25 tension S_TENSION \n"
            script += "6 6 21 -16 -26 tension S_TENSION \n"
            
            script += "// lower pad\n"
            script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
            script += "// upper pad\n"
            script += "8  11  12 13 14 15 16 fixed color green tension 0 constraint 2\n"
            script += "bodies // defined by oriented face list\n"
            if VOLUME <= 0.0:
                script += "1 1 2 3 4 5 6 7 8 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
                print("Current Volume is 0.0, so it is calculated by formula")
                volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
                
                print("Volume: ", volume)
            else:
                script += "1 1 2 3 4 5 6 7 8 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
                print("Volume is defined by user")
                print("Volume: ", VOLUME)
                
        elif bpt != 0.0 and tmt == 0.0:
            script += "vertices\n"
            
            script += "// lower pad internal\n"
            script += "1 0*pi/3 boundary 1 fixed\n"
            script += "2 1*pi/3 boundary 1 fixed\n"
            script += "3 2*pi/3 boundary 1 fixed\n"
            script += "4 3*pi/3 boundary 1 fixed\n"
            script += "5 4*pi/3 boundary 1 fixed\n"
            script += "6 5*pi/3 boundary 1 fixed\n"
            
            script += "// lower pad bottom\n"
            script += "11 0*pi/3 boundary 5 fixed\n"
            script += "12 1*pi/3 boundary 5 fixed\n"
            script += "13 2*pi/3 boundary 5 fixed\n"
            script += "14 3*pi/3 boundary 5 fixed\n"
            script += "15 4*pi/3 boundary 5 fixed\n"
            script += "16 5*pi/3 boundary 5 fixed\n"
                    
            
            script += "// lower pad external\n"
            script += "21 0*pi/3 boundary 7\n"
            script += "22 1*pi/3 boundary 7\n"
            script += "23 2*pi/3 boundary 7\n"
            script += "24 3*pi/3 boundary 7\n"
            script += "25 4*pi/3 boundary 7\n"
            script += "26 5*pi/3 boundary 7\n"
                 
            script += "// upper pad\n"
            script += "41 0*pi/3 boundary 2 fixed\n"
            script += "42 1*pi/3 boundary 2 fixed\n"
            script += "43 2*pi/3 boundary 2 fixed\n"
            script += "44 3*pi/3 boundary 2 fixed\n"
            script += "45 4*pi/3 boundary 2 fixed\n"
            script += "46 5*pi/3 boundary 2 fixed\n"
                                
            script += "edges  // defined by endpoints\n"
            script += "// lower pad internal edges\n"
            script += "1 1 2 boundary 1 fixed\n"
            script += "2 2 3 boundary 1 fixed\n"
            script += "3 3 4 boundary 1 fixed\n"
            script += "4 4 5 boundary 1 fixed\n"
            script += "5 5 6 boundary 1 fixed\n"
            script += "6 6 1 boundary 1 fixed\n"
            
            script += "// lower pad bottom edges\n"
            script += "11 11 12 boundary 5 fixed\n"
            script += "12 12 13 boundary 5 fixed\n"
            script += "13 13 14 boundary 5 fixed\n"
            script += "14 14 15 boundary 5 fixed\n"
            script += "15 15 16 boundary 5 fixed\n"
            script += "16 16 11 boundary 5 fixed\n"
            
            script += "// lower pad external edges\n"
            script += "21 21 22 boundary 7 \n"
            script += "22 22 23 boundary 7 \n"
            script += "23 23 24 boundary 7 \n"
            script += "24 24 25 boundary 7 \n"
            script += "25 25 26 boundary 7 \n"
            script += "26 26 21 boundary 7 \n"
                                 
            script += "// upper pad edges\n"
            script += "41 41 42 boundary 2 fixed\n"
            script += "42 42 43 boundary 2 fixed\n"
            script += "43 43 44 boundary 2 fixed\n"
            script += "44 44 45 boundary 2 fixed\n"
            script += "45 45 46 boundary 2 fixed\n"
            script += "46 46 41 boundary 2 fixed\n"
                
            
            script += "// vertical edges between low pad internal and low pad bottom\n"
            script += "51 1 11 no_refine\n"
            script += "52 2 12 no_refine\n"
            script += "53 3 13 no_refine\n"
            script += "54 4 14 no_refine\n"
            script += "55 5 15 no_refine\n"
            script += "56 6 16 no_refine\n"
            
            script += "// vertical edges between low pad bottom and low pad external\n"
            script += "61 11 21 no_refine\n"
            script += "62 12 22 no_refine\n"
            script += "63 13 23 no_refine\n"
            script += "64 14 24 no_refine\n"
            script += "65 15 25 no_refine\n"
            script += "66 16 26 no_refine\n"
            
            script += "// vertical edges between low pad external and upper pad edge\n"
            script += "71 21 41 \n"
            script += "72 22 42 \n"
            script += "73 23 43 \n"
            script += "74 24 44 \n"
            script += "75 25 45 \n"
            script += "76 26 46 \n"
            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces between low pad internal and low pad bottom\n"
            script += "1 1 52 -11 -51 tension S_TENSION no_refine \n"
            script += "2 2 53 -12 -52 tension S_TENSION no_refine \n"
            script += "3 3 54 -13 -53 tension S_TENSION no_refine \n"
            script += "4 4 55 -14 -54 tension S_TENSION no_refine \n"
            script += "5 5 56 -15 -55 tension S_TENSION no_refine \n"
            script += "6 6 51 -16 -56 tension S_TENSION no_refine \n"
            
            script += "// lateral faces between low pad bottom and low pad external\n"
            script += "11 11 62 -21 -61 tension S_TENSION no_refine \n"
            script += "12 12 63 -22 -62 tension S_TENSION no_refine \n"
            script += "13 13 64 -23 -63 tension S_TENSION no_refine \n"
            script += "14 14 65 -24 -64 tension S_TENSION no_refine \n"
            script += "15 15 66 -25 -65 tension S_TENSION no_refine \n"
            script += "16 16 61 -26 -66 tension S_TENSION no_refine \n"
                    
            script += "// lateral faces solder\n"
            script += "21 21 72 -41 -71 tension S_TENSION \n"
            script += "22 22 73 -42 -72 tension S_TENSION \n"
            script += "23 23 74 -43 -73 tension S_TENSION \n"
            script += "24 24 75 -44 -74 tension S_TENSION \n"
            script += "25 25 76 -45 -75 tension S_TENSION \n"
            script += "26 26 71 -46 -76 tension S_TENSION \n"
                    
            
            script += "// lower pad\n"
            script += "41 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
            script += "// upper pad\n"
            script += "42  41  42  43 44 45 46 fixed color green tension 0 constraint 2\n"
            script += "bodies // defined by oriented face list\n"
            if VOLUME <= 0.0:
                script += "1 1 2 3 4 5 6 11 12 13 14 15 16 21 22 23 24 25 26 41 42 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
                print("Current Volume is 0.0, so it is calculated by formula")
                volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
                
                print("Volume: ", volume)
            else:
                script += "1 1 2 3 4 5 6 11 12 13 14 15 16 21 22 23 24 25 26 41 42  volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
                print("Volume is defined by user")
                print("Volume: ", VOLUME)
                
        elif bpt == 0.0 and tmt != 0.0:
            script += "vertices\n"
            
            script += "// lower pad internal\n"
            script += "1 0*pi/3 boundary 1 fixed\n"
            script += "2 1*pi/3 boundary 1 fixed\n"
            script += "3 2*pi/3 boundary 1 fixed\n"
            script += "4 3*pi/3 boundary 1 fixed\n"
            script += "5 4*pi/3 boundary 1 fixed\n"
            script += "6 5*pi/3 boundary 1 fixed\n"
            
            script += "// upper mask\n"
            script += "31 0*pi/3 boundary 6 fixed\n"
            script += "32 1*pi/3 boundary 6 fixed\n"
            script += "33 2*pi/3 boundary 6 fixed\n"
            script += "34 3*pi/3 boundary 6 fixed\n"
            script += "35 4*pi/3 boundary 6 fixed\n"
            script += "36 5*pi/3 boundary 6 fixed\n"
            
            script += "// upper pad\n"
            script += "41 0*pi/3 boundary 2 fixed\n"
            script += "42 1*pi/3 boundary 2 fixed\n"
            script += "43 2*pi/3 boundary 2 fixed\n"
            script += "44 3*pi/3 boundary 2 fixed\n"
            script += "45 4*pi/3 boundary 2 fixed\n"
            script += "46 5*pi/3 boundary 2 fixed\n"
            
        
            
            script += "edges  // defined by endpoints\n"
            script += "// lower pad internal edges\n"
            script += "1 1 2 boundary 1 fixed\n"
            script += "2 2 3 boundary 1 fixed\n"
            script += "3 3 4 boundary 1 fixed\n"
            script += "4 4 5 boundary 1 fixed\n"
            script += "5 5 6 boundary 1 fixed\n"
            script += "6 6 1 boundary 1 fixed\n"
            
            script += "// upper mask\n"
            script += "31 31 32 boundary 6 fixed\n"
            script += "32 32 33 boundary 6 fixed\n"
            script += "33 33 34 boundary 6 fixed\n"
            script += "34 34 35 boundary 6 fixed\n"
            script += "35 35 36 boundary 6 fixed\n"
            script += "36 36 31 boundary 6 fixed\n"
            
            script += "// upper pad edges\n"
            script += "41 41 42 boundary 2 fixed\n"
            script += "42 42 43 boundary 2 fixed\n"
            script += "43 43 44 boundary 2 fixed\n"
            script += "44 44 45 boundary 2 fixed\n"
            script += "45 45 46 boundary 2 fixed\n"
            script += "46 46 41 boundary 2 fixed\n"
                
            
            script += "// vertical edges between low pad internal and low pad bottom\n"
            script += "51 1 31\n"
            script += "52 2 32\n"
            script += "53 3 33\n"
            script += "54 4 34\n"
            script += "55 5 35\n"
            script += "56 6 36\n"
            
            script += "// vertical edges between upper mask and upper pad edge\n"
            script += "81 31 41 no_refine\n"
            script += "82 32 42 no_refine\n"
            script += "83 33 43 no_refine\n"
            script += "84 34 44 no_refine\n"
            script += "85 35 45 no_refine\n"
            script += "86 36 46 no_refine\n"
                            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces between low pad internal and low pad bottom\n"
            script += "1 1 52 -31 -51 tension S_TENSION\n"
            script += "2 2 53 -32 -52 tension S_TENSION\n"
            script += "3 3 54 -33 -53 tension S_TENSION\n"
            script += "4 4 55 -34 -54 tension S_TENSION\n"
            script += "5 5 56 -35 -55 tension S_TENSION\n"
            script += "6 6 51 -36 -56 tension S_TENSION\n"
            
            script += "// lateral faces top mask\n"
            script += "31 31 82 -41 -81 tension S_TENSION no_refine\n"
            script += "32 32 83 -42 -82 tension S_TENSION no_refine\n"
            script += "33 33 84 -43 -83 tension S_TENSION no_refine\n"
            script += "34 34 85 -44 -84 tension S_TENSION no_refine\n"
            script += "35 35 86 -45 -85 tension S_TENSION no_refine\n"
            script += "36 36 81 -46 -86 tension S_TENSION no_refine\n"
                                
            script += "// lower pad\n"
            script += "41 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
            script += "// upper pad\n"
            script += "42  41  42  43 44 45 46 fixed color green tension 0 constraint 2\n"
            script += "bodies // defined by oriented face list\n"
            if VOLUME <= 0.0:
                script += "1 1 2 3 4 5 6 31 32 33 34 35 36 41 42 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
                print("Current Volume is 0.0, so it is calculated by formula")
                volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
                
                print("Volume: ", volume)
            else:
                script += "1 1 2 3 4 5 6 31 32 33 34 35 36 41 42  volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
                print("Volume is defined by user")
                print("Volume: ", VOLUME)
        else:                                                
            
            script += "vertices\n"
            
            script += "// lower pad internal\n"
            script += "1 0*pi/3 boundary 1 fixed\n"
            script += "2 1*pi/3 boundary 1 fixed\n"
            script += "3 2*pi/3 boundary 1 fixed\n"
            script += "4 3*pi/3 boundary 1 fixed\n"
            script += "5 4*pi/3 boundary 1 fixed\n"
            script += "6 5*pi/3 boundary 1 fixed\n"
            
            script += "// lower pad bottom\n"
            script += "11 0*pi/3 boundary 5 fixed\n"
            script += "12 1*pi/3 boundary 5 fixed\n"
            script += "13 2*pi/3 boundary 5 fixed\n"
            script += "14 3*pi/3 boundary 5 fixed\n"
            script += "15 4*pi/3 boundary 5 fixed\n"
            script += "16 5*pi/3 boundary 5 fixed\n"
                    
            
            script += "// lower pad external\n"
            script += "21 0*pi/3 boundary 7\n"
            script += "22 1*pi/3 boundary 7\n"
            script += "23 2*pi/3 boundary 7\n"
            script += "24 3*pi/3 boundary 7\n"
            script += "25 4*pi/3 boundary 7\n"
            script += "26 5*pi/3 boundary 7\n"
                    
            script += "// upper mask\n"
            script += "31 0*pi/3 boundary 6 fixed\n"
            script += "32 1*pi/3 boundary 6 fixed\n"
            script += "33 2*pi/3 boundary 6 fixed\n"
            script += "34 3*pi/3 boundary 6 fixed\n"
            script += "35 4*pi/3 boundary 6 fixed\n"
            script += "36 5*pi/3 boundary 6 fixed\n"
            
            script += "// upper pad\n"
            script += "41 0*pi/3 boundary 2 fixed\n"
            script += "42 1*pi/3 boundary 2 fixed\n"
            script += "43 2*pi/3 boundary 2 fixed\n"
            script += "44 3*pi/3 boundary 2 fixed\n"
            script += "45 4*pi/3 boundary 2 fixed\n"
            script += "46 5*pi/3 boundary 2 fixed\n"
            
        
            
            script += "edges  // defined by endpoints\n"
            script += "// lower pad internal edges\n"
            script += "1 1 2 boundary 1 fixed\n"
            script += "2 2 3 boundary 1 fixed\n"
            script += "3 3 4 boundary 1 fixed\n"
            script += "4 4 5 boundary 1 fixed\n"
            script += "5 5 6 boundary 1 fixed\n"
            script += "6 6 1 boundary 1 fixed\n"
            
            script += "// lower pad bottom edges\n"
            script += "11 11 12 boundary 5 fixed\n"
            script += "12 12 13 boundary 5 fixed\n"
            script += "13 13 14 boundary 5 fixed\n"
            script += "14 14 15 boundary 5 fixed\n"
            script += "15 15 16 boundary 5 fixed\n"
            script += "16 16 11 boundary 5 fixed\n"
            
            script += "// lower pad external edges\n"
            script += "21 21 22 boundary 7 \n"
            script += "22 22 23 boundary 7 \n"
            script += "23 23 24 boundary 7 \n"
            script += "24 24 25 boundary 7 \n"
            script += "25 25 26 boundary 7 \n"
            script += "26 26 21 boundary 7 \n"
                    
            script += "// upper mask\n"
            script += "31 31 32 boundary 6 fixed\n"
            script += "32 32 33 boundary 6 fixed\n"
            script += "33 33 34 boundary 6 fixed\n"
            script += "34 34 35 boundary 6 fixed\n"
            script += "35 35 36 boundary 6 fixed\n"
            script += "36 36 31 boundary 6 fixed\n"
            
            script += "// upper pad edges\n"
            script += "41 41 42 boundary 2 fixed\n"
            script += "42 42 43 boundary 2 fixed\n"
            script += "43 43 44 boundary 2 fixed\n"
            script += "44 44 45 boundary 2 fixed\n"
            script += "45 45 46 boundary 2 fixed\n"
            script += "46 46 41 boundary 2 fixed\n"
                
            
            script += "// vertical edges between low pad internal and low pad bottom\n"
            script += "51 1 11 no_refine\n"
            script += "52 2 12 no_refine\n"
            script += "53 3 13 no_refine\n"
            script += "54 4 14 no_refine\n"
            script += "55 5 15 no_refine\n"
            script += "56 6 16 no_refine\n"
            
            script += "// vertical edges between low pad bottom and low pad external\n"
            script += "61 11 21 no_refine\n"
            script += "62 12 22 no_refine\n"
            script += "63 13 23 no_refine\n"
            script += "64 14 24 no_refine\n"
            script += "65 15 25 no_refine\n"
            script += "66 16 26 no_refine\n"
            
            script += "// vertical edges between low pad external and upper mask\n"
            script += "71 21 31 \n"
            script += "72 22 32 \n"
            script += "73 23 33 \n"
            script += "74 24 34 \n"
            script += "75 25 35 \n"
            script += "76 26 36 \n"
            
            script += "// vertical edges between upper mask and upper pad edge\n"
            script += "81 31 41 no_refine\n"
            script += "82 32 42 no_refine\n"
            script += "83 33 43 no_refine\n"
            script += "84 34 44 no_refine\n"
            script += "85 35 45 no_refine\n"
            script += "86 36 46 no_refine\n"
                            
            script += "faces // defined by oriented edge loops to have outward normal\n"
            script += "// lateral faces between low pad internal and low pad bottom\n"
            script += "1 1 52 -11 -51 tension S_TENSION no_refine \n"
            script += "2 2 53 -12 -52 tension S_TENSION no_refine \n"
            script += "3 3 54 -13 -53 tension S_TENSION no_refine \n"
            script += "4 4 55 -14 -54 tension S_TENSION no_refine \n"
            script += "5 5 56 -15 -55 tension S_TENSION no_refine \n"
            script += "6 6 51 -16 -56 tension S_TENSION no_refine \n"
            
            script += "// lateral faces between low pad bottom and low pad external\n"
            script += "11 11 62 -21 -61 tension S_TENSION no_refine \n"
            script += "12 12 63 -22 -62 tension S_TENSION no_refine \n"
            script += "13 13 64 -23 -63 tension S_TENSION no_refine \n"
            script += "14 14 65 -24 -64 tension S_TENSION no_refine \n"
            script += "15 15 66 -25 -65 tension S_TENSION no_refine \n"
            script += "16 16 61 -26 -66 tension S_TENSION no_refine \n"
                    
            script += "// lateral faces solder\n"
            script += "21 21 72 -31 -71 tension S_TENSION \n"
            script += "22 22 73 -32 -72 tension S_TENSION \n"
            script += "23 23 74 -33 -73 tension S_TENSION \n"
            script += "24 24 75 -34 -74 tension S_TENSION \n"
            script += "25 25 76 -35 -75 tension S_TENSION \n"
            script += "26 26 71 -36 -76 tension S_TENSION \n"
                    
            script += "// lateral faces top mask\n"
            script += "31 31 82 -41 -81 tension S_TENSION no_refine\n"
            script += "32 32 83 -42 -82 tension S_TENSION no_refine\n"
            script += "33 33 84 -43 -83 tension S_TENSION no_refine\n"
            script += "34 34 85 -44 -84 tension S_TENSION no_refine\n"
            script += "35 35 86 -45 -85 tension S_TENSION no_refine\n"
            script += "36 36 81 -46 -86 tension S_TENSION no_refine\n"
                                
            script += "// lower pad\n"
            script += "41 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
            script += "// upper pad\n"
            script += "42  41  42  43 44 45 46 fixed color green tension 0 constraint 2\n"
            script += "bodies // defined by oriented face list\n"
            if VOLUME <= 0.0:
                script += "1 1 2 3 4 5 6 11 12 13 14 15 16 21 22 23 24 25 26 31 32 33 34 35 36 41 42 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
                print("Current Volume is 0.0, so it is calculated by formula")
                volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
                
                print("Volume: ", volume)
            else:
                script += "1 1 2 3 4 5 6 11 12 13 14 15 16 21 22 23 24 25 26 31 32 33 34 35 36 41 42  volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
                print("Volume is defined by user")
                print("Volume: ", VOLUME)
            
            
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        script += "read \"xyztorque.cmd\"\n"
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        script += "g 100\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
        script += "q\n"
        script += "q\n"    
                
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, top_radius=top_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, stlFileName=self.stlFileName, height=height, VOLUME=VOLUME, xmt=xmt, ymt=ymt, zmt=zmt, xpb=xpb, ypb=ypb, zpb=zpb, bpt=bpt, tmt=tmt, x_offset=x_offset, y_offset=y_offset, tilt=tilt)
        self.script = script
                
        
    def SetScriptOptimizingHeight(self, bottom_point, bottom_radius, bottom_normal, top_point, top_radius, top_normal, S_TENSION=4.800, SOLDER_DENSITY=0.0090, GRAVITY=9810, VOLUME = 0.0, force = 0.0, minDistance = 0.0):
        xb = bottom_point[0]
        yb = bottom_point[1]
        zb = bottom_point[2]
        xt = top_point[0]
        yt = top_point[1]
        zt = top_point[2]
        
    
        ntx, nty, ntz = top_normal
        ntLength = math.sqrt(ntx**2 + nty**2 + ntz**2)
        ntx /= ntLength
        nty /= ntLength
        ntz /= ntLength
        nbx, nby, nbz = bottom_normal
        nbLength = math.sqrt(nbx**2 + nby**2 + nbz**2)
        ntx /= nbLength
        nty /= nbLength
        ntz /= nbLength
        
        ax = 1
        ay = 1
        az = 1
        
        # cross product (ntx, nty, ntz) and (ax, ay, az)
        utx, uty, utz = np.cross([ntx, nty, ntz], [ax, ay, az])
        amputop = math.sqrt(utx**2 + uty**2 + utz**2)
        utx = utx/amputop
        uty = uty/amputop
        utz = utz/amputop
        vtx, vty, vtz = np.cross([ntx, nty, ntz], [utx, uty, utz])
        ampvtop = math.sqrt(vtx**2 + vty**2 + vtz**2)
        vtx = vtx/ampvtop
        vty = vty/ampvtop
        vtz = vtz/ampvtop
        
        ubx, uby, ubz = np.cross([nbx, nby, nbz], [ax, ay, az])
        ampubottom = math.sqrt(ubx**2 + uby**2 + ubz**2)
        ubx = ubx/ampubottom
        uby = uby/ampubottom
        ubz = ubz/ampubottom
        vbx, vby, vbz = np.cross([nbx, nby, nbz], [ubx, uby, ubz])
        ampvbottom = math.sqrt(vbx**2 + vby**2 + vbz**2)
        vbx = vbx/ampvbottom
        vby = vby/ampvbottom
        vbz = vbz/ampvbottom
                
        height = np.sqrt((xt-xb)**2 + (yt-yb)**2 + (zt-zb)**2) 
         
        x_offset = xt - xb
        y_offset = yt - yb
        #angle between top and bottom        
        tilt = nbx*ntx + nby*nty + nbz*ntz
        tilt /= (math.sqrt(nbx**2 + nby**2 + nbz**2) * math.sqrt(ntx**2 + nty**2 + ntz**2))
        if tilt > 1.0:
            tilt = 1.0
        elif tilt < -1.0:
            tilt = -1.0
        tilt = math.acos(tilt) * 180.0 / math.pi
        
        
        script = ""        
        script += "// bga-10.fe\n"
        script += "// Simple ball grid array joint.\n"
        script += "// Circular, tilting, non-coaxial wetted pads. With gravity.\n"
        script += "// Same as bga-8.fe, but with 2D lateral movement of upper pad\n"
        script += "// and tilting.\n"
        script += "// Upper pad represented with boundary.\n"
        script += "// Liquid entirely bounded by facets.\n"
        script += "evolver_version ""2.11c""  // minimum Evolver version needed\n"
        script += "// physical constants, in cgs units\n"
        script += "parameter S_TENSION = {S_TENSION}    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter S_TENSION2 = {S_TENSION}*1000.0    // liquid solder surface tension, erg/cm^2\n"
        script += "parameter SOLDER_DENSITY = {SOLDER_DENSITY} // grams/cm^3\n"
        script += "parameter height = {height}// cm\n"
        script += "parameter ntx = {ntx}     // cm\n"
        script += "parameter nty = {nty}     // cm\n"
        script += "parameter ntz = {ntz}     // cm\n"
        script += "parameter xt = {xt} - height*ntx    // cm\n"
        script += "parameter yt = {yt} - height*nty    // cm\n"
        #script += "parameter zt = {zt} - height*ntz    // cm\n"
        script += "optimizing_parameter zt = {zt} pdelta=1.0e-5 scale=1.0    // cm\n"
        
        script += "parameter x_offset = {x_offset}      // offset in x of upper pad\n"
        script += "parameter y_offset = {y_offset}   // offset in y of upper pad\n"
        script += "parameter tilt = {tilt}         // tilt about x-axis, degrees\n"
        
        script += "parameter force={force} // Newton\n"
        
        
        script += "//Gravity consideration\n"
        script += "quantity pad_energy energy method vertex_scalar_integral\n"
        script += "scalar_integrand : z*{force}\n"

        script += "gravity_constant {GRAVITY}     // cm/sec^2\n"
        script += "// configuration parameters\n"        
        script += "// lower pad\n"
        script += "constraint 1\n"
        script += "formula: ({nbx})*(x-({xb}))+({nby})*(y-({yb}))+({nbz})*(z-({zb})) = 0\n"
        script += "// upper pad\n"
        script += "constraint 2\n"
        script += "formula: ({ntx})*(x-(xt))+({nty})*(y-(yt))+({ntz})*(z-(zt)) = 0\n"    
        script += "// metal mask bottom\n"
        script += "constraint 3\n"
        script += "formula: (({ubx})*x+({uby})*y+({ubz})*z)*(({ubx})*x+({uby})*y+({ubz})*z)+(({vbx})*x+({vby})*y+({vbz})*z)*(({vbx})*x+({vby})*y+({vbz})*z) = ({bottom_radius})^2\n"
        script += "// metal mask top\n"
        script += "constraint 4\n"
        script += "formula: (({utx})*x+({uty})*y+({utz})*z)*(({utx})*x+({uty})*y+({utz})*z)+(({vtx})*x+({vty})*y+({vtz})*z)*(({vtx})*x+({vty})*y+({vtz})*z) = ({top_radius})^2\n"        
        
        script += "//Constraints for height\n"
        script += "constraint 5\n"
        script += "formula: z=zt\n"
              
        script += "// lower pad rim\n"
        script += "boundary 1 parameters 1\n"
        script += "x1: {xb} + ({bottom_radius})*cos(p1)*({ubx}) + ({bottom_radius})*sin(p1)*({vbx})\n"
        script += "x2: {yb} + ({bottom_radius})*cos(p1)*({uby}) + ({bottom_radius})*sin(p1)*({vby})\n"
        script += "x3: {zb} + ({bottom_radius})*cos(p1)*({ubz}) + ({bottom_radius})*sin(p1)*({vbz})\n"   
        script += "// upper pad rim\n"
        script += "boundary 2 parameters 1\n"
        script += "x1: xt + ({top_radius})*cos(p1)*({utx}) + ({top_radius})*sin(p1)*({vtx})\n"
        script += "x2: yt + ({top_radius})*cos(p1)*({uty}) + ({top_radius})*sin(p1)*({vty})\n"
        script += "x3: zt + ({top_radius})*cos(p1)*({utz}) + ({top_radius})*sin(p1)*({vtz})\n"
        script += "boundary 3 parameters 1\n"
        script += "x1: {xb}\n"
        script += "x2: {yb}\n"
        script += "x3: {zb}\n"
        script += "boundary 4 parameters 1\n"
        script += "x1: xt\n"
        script += "x2: yt\n"
        script += "x3: zt\n"
        
        script += "vertices\n"
        script += "// lower pad\n"
        script += "1 0*pi/3 boundary 1 fixed\n"
        script += "2 1*pi/3 boundary 1 fixed\n"
        script += "3 2*pi/3 boundary 1 fixed\n"
        script += "4 3*pi/3 boundary 1 fixed\n"
        script += "5 4*pi/3 boundary 1 fixed\n"
        script += "6 5*pi/3 boundary 1 fixed\n"

        script += "// upper pad\n"
        script += "8 0*pi/3 boundary 2 fixed\n"
        script += "9 1*pi/3 boundary 2 fixed\n"
        script += "10 2*pi/3 boundary 2 fixed\n"
        script += "11 3*pi/3 boundary 2 fixed\n"
        script += "12 4*pi/3 boundary 2 fixed\n"
        script += "13 5*pi/3 boundary 2 fixed\n"
        
        script += "99 0 0 zt constraint 5 fixed bare pad_energy\n"        

        script += "edges  // defined by endpoints\n"
        script += "// lower pad edges\n"
        script += "1 1 2 boundary 1 fixed\n"
        script += "2 2 3 boundary 1 fixed\n"
        script += "3 3 4 boundary 1 fixed\n"
        script += "4 4 5 boundary 1 fixed\n"
        script += "5 5 6 boundary 1 fixed\n"
        script += "6 6 1 boundary 1 fixed\n"
        
        script += "// upper pad edges\n"
        script += "31 8 9 boundary 2 fixed\n"
        script += "32 9 10 boundary 2 fixed\n"
        script += "33 10 11 boundary 2 fixed\n"
        script += "34 11 12 boundary 2 fixed\n"
        script += "35 12 13 boundary 2 fixed\n"
        script += "36 13 8 boundary 2 fixed\n"
        
        script += "// vertical edges between bottom and metal mask bottom\n"
        script += "41 1 8 \n"
        script += "42 2 9 \n"
        script += "43 3 10 \n"
        script += "44 4 11 \n"
        script += "45 5 12 \n"
        script += "46 6 13 \n"
                               
        script += "faces // defined by oriented edge loops to have outward normal\n"
        script += "// lateral faces bottom mask\n"
        script += "1 1 42 -31 -41 tension S_TENSION \n"
        script += "2 2 43 -32 -42 tension S_TENSION \n"
        script += "3 3 44 -33 -43 tension S_TENSION \n"
        script += "4 4 45 -34 -44 tension S_TENSION \n"
        script += "5 5 46 -35 -45 tension S_TENSION \n"
        script += "6 6 41 -36 -46 tension S_TENSION \n"
        
        script += "// lower pad\n"
        script += "7 -6 -5 -4 -3 -2 -1 fixed color red tension 0 constraint 1\n"
        script += "// upper pad\n"
        script += "8  31  32  33 34 35 36 fixed color green tension 0 constraint 2\n"
        script += "bodies // defined by oriented face list\n"
        if VOLUME <= 0.0:
            script += "1 1 2 3 4 5 6 7 8 volume 1.3*pi*({bottom_radius}+{top_radius})^2/4.0*height density SOLDER_DENSITY\n"
            print("Current Volume is 0.0, so it is calculated by formula")
            volume = 1.3*math.pi*(bottom_radius+top_radius)**2/4.0*height
            
            print("Volume: ", volume)
        else:
            script += "1 1 2 3 4 5 6 7 8 volume {VOLUME} density SOLDER_DENSITY\n".format(VOLUME=VOLUME)
            print("Volume is defined by user")
            print("Volume: ", VOLUME)
        script += "read\n"
        script += "hessian_normal\n"
        script += "// Read in force and torque commands.\n"
        script += "read \"xyztorque.cmd\"\n"
        
        script += "// Typical evolution\n"
        script += "gogo := {{ u; g 5; r; g 5; r; g 5; hessian; hessian }}\n"
        script += "g 100\n"
        if self.detailMode == True:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"            
        else:
            script += "r\n"
            script += "u 2\n"
            script += "g 10\n"
            script += "u\n"
            script += "g 2\n"
          
        script += "read \"stl.cmd\"\n"
        script += "stl >>> \"{stlFileName}\"\n"
             
        script += "logfile \"heightOptimized.txt\"\n"
        script += "print {initzt}\n"
        #script += "print zt\n"
        script += "print sqrt((zt-({zb}))^2+(yt-({yb}))^2+(xt-({xb}))^2)\n"
        
        script += "logfile\n"
        
        
        script += "q\n"
        script += "q\n"    
     
        
                
        script = script.format(xb=xb, yb=yb, zb=zb, xt=xt, yt=yt, zt=zt, nbx=nbx, nby=nby, nbz=nbz, ntx=ntx, nty=nty, ntz=ntz, S_TENSION=S_TENSION, SOLDER_DENSITY=SOLDER_DENSITY, GRAVITY=GRAVITY, bottom_radius=bottom_radius, top_radius=top_radius, ubx=ubx, uby=uby, ubz=ubz, vbx=vbx, vby=vby, vbz=vbz, utx=utx, uty=uty, utz=utz, vtx=vtx, vty=vty, vtz=vtz, stlFileName=self.stlFileName, height=1.0e-5, VOLUME=VOLUME, x_offset=x_offset, y_offset=y_offset, tilt=tilt, force=force, initzt=top_point[2] - bottom_point[2])
        self.script = script     
        
    
    
    
if __name__ == "__main__":
    
    smd = SolderMaskedDefined(name="solder")
    bottom_point = [0, 0, 0]
    bottom_radius = 0.125
    bottom_normal = [0.01, 0.02, 1]
    top_point =  [0.005, -0.01, 0.12]
    top_radius = 0.125
    top_normal = [0.4, 0.02, 1]
    S_TENSION = 480.0
    SOLDER_DENSITY = 9.0
    GRAVITY = 981.0
    smd.SetFolderPath(os.getcwd())    
    smd.SetBottom(bottom_point, bottom_radius, bottom_normal)
    smd.SetTop(top_point, top_radius, top_normal)
    smd.SetSurfaceTension(S_TENSION)
    smd.SetSolderDensity(SOLDER_DENSITY)
    smd.SetGravity(GRAVITY)
    smd.SetVolume(0.0)
    smd.UpdateScript()
    solder =smd.MakeSolder()
    
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        pass
    else:
        display.DisplayShape(solder)
        start_display()
    
    