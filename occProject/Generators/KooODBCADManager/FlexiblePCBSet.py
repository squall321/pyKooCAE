import sys
from math import cos, pi 
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
import os.path
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf 

from OCC.Display.SimpleGui import init_display
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

class FlexiblePrintedCircuitBoard:
    def __init__(self):
        self.CenterPoint = gp_Pnt(0,0,0)
        self.LeftRigidLength = 2.9761
        self.LeftRigidWidth = 5.04
        self.RigidLayerThickness = 0.635

        
        self.RightRigidLength = 2.9761
        self.RightRigidWidth = 5.04
        
        self.FlexibleOffset = 0.05
        self.FlexLayerThickness = [] 
        self.FlexLayerThickness.append(0.1)
        self.FlexLayerThickness.append(0.05)
        self.FlexLayerThickness.append(0.1)
        self.FlexLayerThickness.append(0.05)
        self.FlexLayerThickness.append(0.1)
        self.FlexLayerThickness.append(0.05)
        self.FlexLayerThickness.append(0.1)

        self.FlexLayerConsistent = [] 
        self.FlexLayerConsistent.append("Layer")
        self.FlexLayerConsistent.append("AIR")
        self.FlexLayerConsistent.append("Layer")
        self.FlexLayerConsistent.append("AIR")
        self.FlexLayerConsistent.append("Layer")
        self.FlexLayerConsistent.append("AIR")
        self.FlexLayerConsistent.append("Layer")

        self.FlexLayerWidth = 5.04
        self.FlexLayerLength = 20.0
    
    def SetSenterPoint(self, x, y, z):
        self.CenterPoint = gp_Pnt(x,y,z)
    
    def MakeBoxShape(self,xmin, ymin, zmin, xmax, ymax, zmax):
        box = BRepPrimAPI_MakeBox(gp_Pnt(xmin, ymin, zmin), gp_Pnt(xmax, ymax, zmax)).Shape()
        return box

    def MakeLeftRigidLayerShape(self):
        xmin = self.CenterPoint.X() - self.FlexLayerLength/2.0 - self.LeftRigidLength
        ymin = self.CenterPoint.Y() 
        zmin = self.CenterPoint.Z() - self.LeftRigidWidth
        xmax = self.CenterPoint.X() - self.FlexLayerLength/2.0
        ymax = self.CenterPoint.Y() + self.RigidLayerThickness
        zmax = self.CenterPoint.Z()
        return self.MakeBoxShape(xmin, ymin, zmin, xmax, ymax, zmax)

    def MakeRightRigidLayerShape(self):
        xmin = self.CenterPoint.X() + self.FlexLayerLength/2.0
        ymin = self.CenterPoint.Y()
        zmin = self.CenterPoint.Z() - self.RightRigidWidth
        xmax = self.CenterPoint.X() + self.FlexLayerLength/2.0 + self.RightRigidLength  
        ymax = self.CenterPoint.Y() + self.RigidLayerThickness
        zmax = self.CenterPoint.Z()
        return self.MakeBoxShape(xmin, ymin, zmin, xmax, ymax, zmax)
    
    def MakeFlexLayerShape(self):
        shapeList = [] 
        curY = self.CenterPoint.Y() + self.FlexibleOffset
        for i in range(0, len(self.FlexLayerThickness)):

            if self.FlexLayerConsistent[i] == "Layer":
                xmin = self.CenterPoint.X() - self.FlexLayerLength/2.0
                zmin = self.CenterPoint.Z() - self.FlexLayerWidth
                xmax = self.CenterPoint.X() + self.FlexLayerLength/2.0
                zmax = self.CenterPoint.Z()
                ymin = self.CenterPoint.Y() + curY
                ymax = self.CenterPoint.Y() + curY + self.FlexLayerThickness[i]
                shapeList.append(self.MakeBoxShape(xmin, ymin, zmin, xmax, ymax, zmax))
                curY += self.FlexLayerThickness[i]
            else:
                curY += self.FlexLayerThickness[i]
        return shapeList

    def MakeShape(self):
        display.EraseAll()
        shapeList = [] 
        lrl = self.MakeLeftRigidLayerShape()
        rrl = self.MakeRightRigidLayerShape()
        fl = self.MakeFlexLayerShape()

        shapeList.append(lrl)
        shapeList.append(rrl)
        shapeList.extend(fl)
        return shapeList

if __name__ == "__main__":
    fp = FlexiblePrintedCircuitBoard()
    fp.SetSenterPoint(0,0,0)
    shapeList = fp.MakeShape()


    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
    # 오프스크린 모드: GUI 함수들을 더미로 정의
        pass
    else:    
        for shape in shapeList:
            display.DisplayShape(shape, update=True)
        start_display()