
'''import os
os.add_dll_directory("D:\OpenCASCADE-7.7.0-vc14-64\pythonoccenv310\Library\OCC")'''
import os

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

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf

from KooCAEManager.KooBoundary import (
    KooBoundary,
    KooBoundaryDisplacement,
    KooBoundaryVelocity,
    KooBoundaryAcceleration,
    KooBoundaryForce,
    KooBoundaryPressure,
    KooBoundaryTemperature,
    KooBoundaryHeatFlux,
    KooBoundaryHeatGeneration,
    KooBoundaryConvection,
    KooBoundaryRadiation
)


from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.Graphic3d import Graphic3d_NOM_ALUMINIUM
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.AIS import AIS_Manipulator, AIS_Shape

class KooAISBoundaryDisplacement(KooBoundaryDisplacement):
    def __init__(self, id=0, shapeList = [],timeList = [], dispList = []):
        super(KooAISBoundaryDisplacement,self).__init__(id, shapeList, timeList, dispList)        
        self.aisShape = []
        self.trShape = [] 
        self.material = None
        self.texture = None
        self.color = Quantity_Color(0.1, 0.7, 0.1, Quantity_TOC_RGB)
        self.transparency = 0.0
        self.linewidth = 5
        self.name = "Boundary{id}".format(id=self.bid)
    
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.shapeList
                self.aisShape = [] 
                for shape in self.shapeList:
                    ais_shape = viewer._display.DisplayShape(shape,self.material,self.texture,self.color,self.transparency,update)
                    self.aisShape.append(ais_shape)
            else:
                self.trShape = [] 
                self.aisShape = []
                for shape in self.shapeList:
                    tr_shape = BRepBuilderAPI_Transform(shape,trsf).Shape()
                    self.trShape.append(tr_shape)
                    ais_shape = viewer._display.DisplayShape(tr_shape,self.material,self.texture,self.color,self.transparency,update)
                    self.aisShape.append(ais_shape)
    
    def Transform(self, viewer, trsf : gp_Trsf, update = False):
        self.Erase(viewer, update)
        self.Display(viewer, update, trsf)
    
    def SetHide(self, viewer, hide = True, update = False):
        self.hide = hide 
        if self.hide == True:
            self.Erase(viewer, update)  
        else:
            self.Display(viewer, update)
    
    def Erase(self, viewer, update = False):
        for shape in self.aisShape:
            for s in shape:
                if type(s) == AIS_Shape:
                    viewer._display.Context.Erase(s,update)
                else:
                    for i in range(len(s)):
                        viewer._display.Context.Erase(s[i],update)
                    
    

