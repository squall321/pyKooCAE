import os
import sys
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
import numpy as np
import math
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Ax2, gp_Dir, gp_Pnt
from OCC.Core.TopoDS import TopoDS_Shell
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeSolid
from OCC.Core.BRepFill import BRepFill_Filling
from OCC.Core.GeomAbs import GeomAbs_C0, GeomAbs_G1, GeomAbs_G2

from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.BRepFill import brepfill_Shell


if __name__ == "__main__":
    path = os.path.join(os.getcwd(), "occProject\Generators")
    sys.path.append(path)    

    # 디스플레이 초기화
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
    
from KooODBCADManager.Module import Module
    
class MotorCoilModule(Module):
    def __init__(self, id, name):
        super().__init__(id, name) 
        self.H = 1.8
        self.W = 0.3
        self.R = 0.45
        self.w = 0.3
        self.T = 3.1
        self.tcoil = 0.0
        self.tdielectric = 0.0
        self.n = 190
        self.rho = 1.68e-5
        self.Resistance = 0.0
        
    def SetDilectricThickness(self): 
        t = (self.T - self.n * self.tcoil)/(self.n - 1)
        self.tdielectric = t
        
    def SetResistance(self, resistance):
        self.Resistance = resistance
        
        self.tcoil = 2.0 * self.rho * self.n *(math.pi*self.R + self.H + self.W) / (self.w *self.Resistance) 
        self.SetDilectricThickness()
                       
    def MakeEightPointBox(self, p1, p2, p3, p4, p5, p6, p7, p8):
        e1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
        e2 = BRepBuilderAPI_MakeEdge(p2, p4).Edge()
        e3 = BRepBuilderAPI_MakeEdge(p4, p3).Edge()
        e4 = BRepBuilderAPI_MakeEdge(p3, p1).Edge()
        
        e5 = BRepBuilderAPI_MakeEdge(p5, p6).Edge()
        e6 = BRepBuilderAPI_MakeEdge(p6, p8).Edge()
        e7 = BRepBuilderAPI_MakeEdge(p8, p7).Edge()
        e8 = BRepBuilderAPI_MakeEdge(p7, p5).Edge()
                
        wire1 = BRepBuilderAPI_MakeWire()
        wire1.Add(e1)
        wire1.Add(e2)
        wire1.Add(e3)
        wire1.Add(e4)

        wire2 = BRepBuilderAPI_MakeWire()
        wire2.Add(e5)
        wire2.Add(e6)
        wire2.Add(e7)
        wire2.Add(e8)
        
        try:
            face1 = BRepBuilderAPI_MakeFace(wire1.Wire()).Face()
            face2 = BRepBuilderAPI_MakeFace(wire2.Wire()).Face()
        except:                
            filling = BRepFill_Filling()
            filling.Add(e1, GeomAbs_C0)
            filling.Add(e2, GeomAbs_C0)  
            filling.Add(e3, GeomAbs_C0)
            filling.Add(e4, GeomAbs_C0)
            filling.Build()
            face1 = filling.Face()
        
            filling = BRepFill_Filling()
            filling.Add(e5, GeomAbs_C0)
            filling.Add(e6, GeomAbs_C0)
            filling.Add(e7, GeomAbs_C0)
            filling.Add(e8, GeomAbs_C0)
            filling.Build()
            face2 = filling.Face()
        builder = BRep_Builder()
            
        shell1 = TopoDS_Shell()
        builder.MakeShell(shell1)
        builder.Add(shell1, face1)
        builder = BRep_Builder()
        shell2 = TopoDS_Shell()
        builder.MakeShell(shell2)
        builder.Add(shell2, face2)
        
        shell_builder = brepfill_Shell(wire1.Shape(), wire2.Shape())
        solid_builder = BRepBuilderAPI_MakeSolid()
        solid_builder.Add(shell1)
        solid_builder.Add(shell2)
        solid_builder.Add(shell_builder)
        solid_builder.Build()
        solid = solid_builder.Shape()

        self.maxShapeID += 1    
        self.shapes[self.maxShapeID] = solid
        
        
            
            
                
    def GenerateBottomWire(self):
        xInternal, yInternal, xExternal, yExternal, zInternalTmp, zExternalTmp = self.GetXYZPointsforRaceTrackCoil()
        zInternal = [z for z in zInternalTmp]
        zExternal = [z for z in zExternalTmp]
        
        zInternalptcoil = [z + self.tcoil for z in zInternalTmp]
        zExternalptcoil = [z + self.tcoil for z in zExternalTmp]
        
        p1 = gp_Pnt(xInternal[0], yInternal[0], zInternal[0])
        p2 = gp_Pnt(xExternal[0], yExternal[0], zExternal[0])
        
        p5 = gp_Pnt(xInternal[0], yInternal[0], zInternalptcoil[0])
        p6 = gp_Pnt(xExternal[0], yExternal[0], zExternalptcoil[0])
        
        dxInternal = 0.0
        dyInternal = -self.tcoil*2
        dzInternal = -self.tcoil*2
        dxExternal = 0.0
        dyExternal = -self.tcoil*2
        dzExternal = -self.tcoil*2
        
        p1offset = gp_Pnt(xInternal[0] + dxInternal, yInternal[0] + dyInternal, zInternal[0] + dzInternal)
        p2offset = gp_Pnt(xExternal[0] + dxExternal, yExternal[0] + dyExternal, zExternal[0] + dzExternal)
        
        p5offset = gp_Pnt(xInternal[0] + dxInternal, yInternal[0] + dyInternal, zInternalptcoil[0] + dzInternal)
        p6offset = gp_Pnt(xExternal[0] + dxExternal, yExternal[0] + dyExternal, zExternalptcoil[0] + dzExternal)
        
        self.MakeEightPointBox(p1, p2, p5, p6, p1offset, p2offset, p5offset, p6offset)
        
        dxInternal = 0.0
        dyInternal = -max(self.T, self.H, self.W)*5
        dzInternal = 0.0
        dxExternal = 0.0
        dyExternal = -max(self.T, self.H, self.W)*5
        dzExternal = 0.0
        p1offset2 = gp_Pnt(xInternal[0] + dxInternal, yInternal[0] + dyInternal, zInternal[0] + dzInternal)
        p2offset2 = gp_Pnt(xExternal[0] + dxExternal, yExternal[0] + dyExternal, zExternal[0] + dzExternal)
        
        p5offset2 = gp_Pnt(xInternal[0] + dxInternal, yInternal[0] + dyInternal, zInternalptcoil[0] + dzInternal)
        p6offset2 = gp_Pnt(xExternal[0] + dxExternal, yExternal[0] + dyExternal, zExternalptcoil[0] + dzExternal)
        
        self.MakeEightPointBox(p1offset, p2offset, p1offset2, p2offset2, p5offset, p6offset, p5offset2, p6offset2)
            
        
        
    
    def GenerateTopWire(self, zOffset = 0.0):
        xInternal, yInternal, xExternal, yExternal, zInternalTmp, zExternalTmp = self.GetXYZPointsforRaceTrackCoil()
        
        zInternal = [z + zOffset for z in zInternalTmp]
        zExternal = [z + zOffset for z in zExternalTmp]
        
        zInternalptcoil = [z + self.tcoil + zOffset for z in zInternalTmp]
        zExternalptcoil = [z + self.tcoil + zOffset for z in zExternalTmp]
        
        p1 = gp_Pnt(xInternal[0], yInternal[0], zInternal[0])
        p2 = gp_Pnt(xExternal[0], yExternal[0], zExternal[0])
        
        p5 = gp_Pnt(xInternal[0], yInternal[0], zInternalptcoil[0])
        p6 = gp_Pnt(xExternal[0], yExternal[0], zExternalptcoil[0])
        
        dxInternal = 0.0
        dyInternal = self.tcoil
        dzInternal = 0.0
        dxExternal = 0.0
        dyExternal = self.tcoil
        dzExternal = 0.0
        
        p1offset = gp_Pnt(xInternal[0] + dxInternal, yInternal[0] + dyInternal, zInternal[0] + dzInternal)
        p2offset = gp_Pnt(xExternal[0] + dxExternal, yExternal[0] + dyExternal, zExternal[0] + dzExternal)
        
        p5offset = gp_Pnt(xInternal[0] + dxInternal, yInternal[0] + dyInternal, zInternalptcoil[0] + dzInternal)
        p6offset = gp_Pnt(xExternal[0] + dxExternal, yExternal[0] + dyExternal, zExternalptcoil[0] + dzExternal)
        
        self.MakeEightPointBox(p1, p2, p5, p6, p1offset, p2offset, p5offset, p6offset)
        
        dxInternal = 0.0
        dyInternal = 0.0
        dzInternal = self.tcoil*2
        
        dxExternal = 0.0
        dyExternal = 0.0
        dzExternal = self.tcoil*2
        
        p5voffset = gp_Pnt(p5.X() + dxInternal, p5.Y() + dyInternal, p5.Z() + dzInternal)
        p6voffset = gp_Pnt(p6.X() + dxExternal, p6.Y() + dyExternal, p6.Z() + dzExternal)
        
        p5offsetvoffset = gp_Pnt(p5offset.X() + dxInternal, p5offset.Y() + dyInternal, p5offset.Z() + dzInternal)
        p6offsetvoffset = gp_Pnt(p6offset.X() + dxExternal, p6offset.Y() + dyExternal, p6offset.Z() + dzExternal)
        
        self.MakeEightPointBox(p5, p6, p5voffset, p6voffset, p5offset, p6offset, p5offsetvoffset, p6offsetvoffset)
        
        dxInternal = 0.0
        dyInternal = 0.0
        dzInternal = self.tcoil*2
        
        dxExternal = 0.0
        dyExternal = 0.0
        dzExternal = self.tcoil*2
        
        p1boffset = gp_Pnt(p1.X() + dxInternal, p1.Y() + dyInternal, p1.Z() + dzInternal)
        p2boffset = gp_Pnt(p2.X() + dxExternal, p2.Y() + dyExternal, p2.Z() + dzExternal)
        
        p1 = p1boffset
        p2 = p2boffset
        p3 = p5voffset
        p4 = p6voffset
        
        dxInternal = 0.0
        dyInternal = -max(self.T, self.H, self.W)*5
        dzInternal = 0.0
        
        dxExternal = 0.0
        dyExternal = -max(self.T, self.H, self.W)*5
        dzExternal = 0.0
        
        p1offset2 = gp_Pnt(p1.X() + dxInternal, p1.Y() + dyInternal, p1.Z() + dzInternal)
        p2offset2 = gp_Pnt(p2.X() + dxExternal, p2.Y() + dyExternal, p2.Z() + dzExternal)
        p3offset2 = gp_Pnt(p3.X() + dxInternal, p3.Y() + dyInternal, p3.Z() + dzInternal)
        p4offset2 = gp_Pnt(p4.X() + dxExternal, p4.Y() + dyExternal, p4.Z() + dzExternal)
        
        self.MakeEightPointBox(p1, p2, p3, p4, p1offset2, p2offset2, p3offset2, p4offset2)
        
        
        
            
        
    def GenerateRaceTrackCoilOneTurn(self, zOffset = 0.0):
        xInternal, yInternal, xExternal, yExternal, zInternalTmp, zExternalTmp = self.GetXYZPointsforRaceTrackCoil()
        
        zInternal = [z + zOffset for z in zInternalTmp]
        zExternal = [z + zOffset for z in zExternalTmp]
        
        zInternalptcoil = [z + self.tcoil + zOffset for z in zInternalTmp]
        zExternalptcoil = [z + self.tcoil + zOffset for z in zExternalTmp]
        
        for i in range(len(xInternal)):  
            
            if i == len(xInternal) - 1:
                ip1 = 0 
            else:
                ip1 = i + 1
                
            if i == len(xInternal) - 1:                
                p1 = gp_Pnt(xInternal[i], yInternal[i], zInternal[i])
                p2 = gp_Pnt(xExternal[i], yExternal[i], zInternal[i])
                p3 = gp_Pnt(xExternal[0], yExternal[0], zInternal[0] + self.tcoil + self.tdielectric)
                p4 = gp_Pnt(xInternal[0], yInternal[0], zInternal[0] + self.tcoil + self.tdielectric)

                p5 = gp_Pnt(xInternal[i], yInternal[i], zInternalptcoil[i])
                p6 = gp_Pnt(xExternal[i], yExternal[i], zInternalptcoil[i])
                p7 = gp_Pnt(xExternal[0], yExternal[0], zInternalptcoil[0] + self.tcoil + self.tdielectric)
                p8 = gp_Pnt(xInternal[0], yInternal[0], zInternalptcoil[0] + self.tcoil + self.tdielectric)
            else:
                p1 = gp_Pnt(xInternal[i], yInternal[i], zInternal[i])
                p2 = gp_Pnt(xExternal[i], yExternal[i], zExternal[i])
                p3 = gp_Pnt(xExternal[i+1], yExternal[i+1], zExternal[i+1])
                p4 = gp_Pnt(xInternal[i+1], yInternal[i+1], zInternal[i+1])
                
                p5 = gp_Pnt(xInternal[i], yInternal[i], zInternalptcoil[i])
                p6 = gp_Pnt(xExternal[i], yExternal[i], zExternalptcoil[i])
                p7 = gp_Pnt(xExternal[i+1], yExternal[i+1], zExternalptcoil[i+1])
                p8 = gp_Pnt(xInternal[i+1], yInternal[i+1], zInternalptcoil[i+1])
                
                '''if i == 18:
                    testList = [] 
                    testList.append([p1.X(), p1.Y(), p1.Z()])
                    testList.append([p2.X(), p2.Y(), p2.Z()])
                    testList.append([p3.X(), p3.Y(), p3.Z()])
                    testList.append([p4.X(), p4.Y(), p4.Z()])
                    testList.append([p5.X(), p5.Y(), p5.Z()])
                    testList.append([p6.X(), p6.Y(), p6.Z()])
                    testList.append([p7.X(), p7.Y(), p7.Z()])
                    testList.append([p8.X(), p8.Y(), p8.Z()])
                    for j in range(len(testList)):
                        print(testList[j][0], ",", testList[j][1], ",", testList[j][2])'''
                    
        
                

            
            edge1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
            edge2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
            edge3 = BRepBuilderAPI_MakeEdge(p3, p4).Edge()
            edge4 = BRepBuilderAPI_MakeEdge(p4, p1).Edge()
            
            edge5 = BRepBuilderAPI_MakeEdge(p5, p6).Edge()
            edge6 = BRepBuilderAPI_MakeEdge(p6, p7).Edge()
            edge7 = BRepBuilderAPI_MakeEdge(p7, p8).Edge()
            edge8 = BRepBuilderAPI_MakeEdge(p8, p5).Edge()
            
            wire1 = BRepBuilderAPI_MakeWire()
            wire1.Add(edge1)
            wire1.Add(edge2)
            wire1.Add(edge3)
            wire1.Add(edge4)
                        
            wire2 = BRepBuilderAPI_MakeWire()
            wire2.Add(edge5)
            wire2.Add(edge6)
            wire2.Add(edge7)
            wire2.Add(edge8)
            # surface from wire1 and wire2
                        
            # BRepFill_Filling을 사용하여 면 생성
            
            if zInternal[i] == zInternal[ip1]:
                face1 = BRepBuilderAPI_MakeFace(wire1.Wire()).Face()
                face2 = BRepBuilderAPI_MakeFace(wire2.Wire()).Face()
            else:
                
                filling = BRepFill_Filling()
                filling.Add(edge1, GeomAbs_C0)
                filling.Add(edge2, GeomAbs_C0)  
                filling.Add(edge3, GeomAbs_C0)
                filling.Add(edge4, GeomAbs_C0)
                filling.Build()
                face1 = filling.Face()
            
                filling = BRepFill_Filling()
                filling.Add(edge5, GeomAbs_C0)
                filling.Add(edge6, GeomAbs_C0)
                filling.Add(edge7, GeomAbs_C0)
                filling.Add(edge8, GeomAbs_C0)
                filling.Build()
                face2 = filling.Face()
                    
            builder = BRep_Builder()
            
            shell1 = TopoDS_Shell()
            builder.MakeShell(shell1)
            builder.Add(shell1, face1)
            builder = BRep_Builder()
            shell2 = TopoDS_Shell()
            builder.MakeShell(shell2)
            builder.Add(shell2, face2)
            
            shell_builder = brepfill_Shell(wire1.Shape(), wire2.Shape())
            solid_builder = BRepBuilderAPI_MakeSolid()
            solid_builder.Add(shell1)
            solid_builder.Add(shell2)
            solid_builder.Add(shell_builder)
            solid_builder.Build()
            solid = solid_builder.Shape()
            self.maxShapeID += 1
            self.shapes[self.maxShapeID] = solid            
        print("Generate Race Track Coil One Turn Done : ", zOffset)
            
        
    def GetXYZPointsforRaceTrackCoil(self):
        num_point_circle = 5 
        xinternal = [] 
        yinternal = [] 
        xexternal = []
        yexternal = []      
        zinternal = [] 
        zexternal = []
        # theta is 0 to pi/2.0
        for i in range(num_point_circle):
            curTheta = i * math.pi / (2.0 * (num_point_circle))
            xinternal.append(self.W/2.0+(self.R-self.w/2.0)*math.cos(curTheta))
            yinternal.append(self.H/2.0+(self.R-self.w/2.0)*math.sin(curTheta))
            xexternal.append(self.W/2.0+(self.R+self.w/2.0)*math.cos(curTheta))
            yexternal.append(self.H/2.0+(self.R+self.w/2.0)*math.sin(curTheta))
            zinternal.append(0.0)
            zexternal.append(0.0)
        
        xinternal.append(self.W/2.0)
        yinternal.append(self.H/2.0 + self.R - self.w/2.0)
        xexternal.append(self.W/2.0)
        yexternal.append(self.H/2.0 + self.R + self.w/2.0)
        zinternal.append(0.0)
        zexternal.append(0.0)
        
        #theta is pi/2.0 to pi
        for i in range(num_point_circle):
            curTheta = i * math.pi / (2.0 * (num_point_circle)) + math.pi / 2.0
            xinternal.append(-self.W/2.0+(self.R-self.w/2.0)*math.cos(curTheta))
            yinternal.append(self.H/2.0+(self.R-self.w/2.0)*math.sin(curTheta))
            xexternal.append(-self.W/2.0+(self.R+self.w/2.0)*math.cos(curTheta))
            yexternal.append(self.H/2.0+(self.R+self.w/2.0)*math.sin(curTheta))
            zinternal.append(0.0)
            zexternal.append(0.0)
        
        xinternal.append(-self.W/2.0 - self.R + self.w/2.0)
        yinternal.append(self.H/2.0)
        xexternal.append(-self.W/2.0 - self.R - self.w/2.0)
        yexternal.append(self.H/2.0)
        zinternal.append(0.0)
        zexternal.append(0.0)
        
        #theta is pi to 3*pi/2.0
        for i in range(num_point_circle):
            curTheta = i * math.pi / (2.0 * (num_point_circle)) + math.pi
            xinternal.append(-self.W/2.0+(self.R-self.w/2.0)*math.cos(curTheta))
            yinternal.append(-self.H/2.0+(self.R-self.w/2.0)*math.sin(curTheta))
            xexternal.append(-self.W/2.0+(self.R+self.w/2.0)*math.cos(curTheta))
            yexternal.append(-self.H/2.0+(self.R+self.w/2.0)*math.sin(curTheta))
            zinternal.append(0.0)
            zexternal.append(0.0)
        
        xinternal.append(-self.W/2.0)
        yinternal.append(-self.H/2.0 - self.R + self.w/2.0)
        xexternal.append(-self.W/2.0)
        yexternal.append(-self.H/2.0 - self.R - self.w/2.0)
        zinternal.append(0.0)
        zexternal.append(0.0)
        
        dz = self.tdielectric/(num_point_circle)
        
        #theta is 3*pi/2.0 to 2*pi
        for i in range(num_point_circle):
            curTheta = i * math.pi / (2.0 * (num_point_circle)) + 3 * math.pi / 2.0
            xinternal.append(self.W/2.0+(self.R-self.w/2.0)*math.cos(curTheta))
            yinternal.append(-self.H/2.0+(self.R-self.w/2.0)*math.sin(curTheta))
            xexternal.append(self.W/2.0+(self.R+self.w/2.0)*math.cos(curTheta))
            yexternal.append(-self.H/2.0+(self.R+self.w/2.0)*math.sin(curTheta))
            zinternal.append(dz*i)
            zexternal.append(dz*i)
            
        
        xinternal.append(self.W/2.0 + self.R - self.w/2.0)
        yinternal.append(-self.H/2.0)
        xexternal.append(self.W/2.0 + self.R + self.w/2.0)
        yexternal.append(-self.H/2.0)    
        zinternal.append(self.tdielectric)
        zexternal.append(self.tdielectric)
        
        
        return xinternal, yinternal, xexternal, yexternal, zinternal, zexternal
        
                       
    
    def GenerateRacetrackCoils(self):
        self.GenerateBottomWire()
        offsetDelta = self.tdielectric + self.tcoil
        for i in range(self.n):
            zOffset = i * offsetDelta
            self.GenerateRaceTrackCoilOneTurn(zOffset)
        self.GenerateTopWire(zOffset + offsetDelta)    
        
        
    def GetXYZPointsforCircularCoil(self, turn = 1):
        num_point_circle = 16
        num_total_point = num_point_circle * turn
        
        num_total_point = int(num_total_point)+1        
        angle_total = 2 * math.pi * turn
        
        xinternal = []
        yinternal = []
        xexternal = []
        yexternal = []
        zinternal = []
        zexternal = []
        
        for i in range(num_total_point):
            curTheta = i * angle_total / (num_total_point-1)
            
            xinternal.append((self.R - self.w/2.0) * math.cos(curTheta))
            yinternal.append((self.R - self.w/2.0) * math.sin(curTheta))
            zinternal.append(self.T * i / (num_total_point-1))
        
        for i in range(num_total_point):
            curTheta = i * angle_total / (num_total_point-1)
            
            xexternal.append((self.R + self.w/2.0) * math.cos(curTheta))
            yexternal.append((self.R + self.w/2.0) * math.sin(curTheta))
            zexternal.append(self.T * i / (num_total_point-1))
                    
        return xinternal, yinternal, xexternal, yexternal, zinternal, zexternal
    
    def GenerateCircularCoilnTurn(self, turn):
        xinternal, yinternal, xexternal, yexternal, zInternalTmp, zExternalTmp = self.GetXYZPointsforCircularCoil(turn)
        zInternal = [z for z in zInternalTmp]
        zExternal = [z for z in zExternalTmp]
        
        zInternalptcoil = [z + self.tcoil for z in zInternalTmp]
        zExternalptcoil = [z + self.tcoil for z in zExternalTmp]
        
        for i in range(len(xinternal)-1):
            p1 = gp_Pnt(xinternal[i], yinternal[i], zInternal[i])
            p2 = gp_Pnt(xexternal[i], yexternal[i], zExternal[i])
            p3 = gp_Pnt(xinternal[i], yinternal[i], zInternalptcoil[i])
            p4 = gp_Pnt(xexternal[i], yexternal[i], zExternalptcoil[i])
            
            p5 = gp_Pnt(xinternal[i+1], yinternal[i+1], zInternal[i+1])
            p6 = gp_Pnt(xexternal[i+1], yexternal[i+1], zExternal[i+1])
            p7 = gp_Pnt(xinternal[i+1], yinternal[i+1], zInternalptcoil[i+1])
            p8 = gp_Pnt(xexternal[i+1], yexternal[i+1], zExternalptcoil[i+1])
            
            self.MakeEightPointBox(p1, p2, p3, p4, p5, p6, p7, p8)
            
    def GenerateBottomCircleWire(self):
        xinternal, yinternal, xexternal, yexternal, zInternalTmp, zExternalTmp = self.GetXYZPointsforCircularCoil(self.n)        
        zInternal = [z for z in zInternalTmp]
        zExternal = [z for z in zExternalTmp]
        
        zInternalptcoil = [z + self.tcoil for z in zInternalTmp]
        zExternalptcoil = [z + self.tcoil for z in zExternalTmp]
        
        p1 = gp_Pnt(xinternal[0], yinternal[0], zInternal[0])
        p2 = gp_Pnt(xexternal[0], yexternal[0], zExternal[0])
        
        p3 = gp_Pnt(xinternal[0], yinternal[0], zInternalptcoil[0])
        p4 = gp_Pnt(xexternal[0], yexternal[0], zExternalptcoil[0])
        
        dxInternal = 0.0
        dyInternal = -max(self.T, self.H, self.W)*5
        dzInternal = 0.0
        
        dxExternal = 0.0
        dyExternal = -max(self.T, self.H, self.W)*5
        dzExternal = 0.0
        
        p1offset = gp_Pnt(xinternal[0] + dxInternal, yinternal[0] + dyInternal, zInternal[0] + dzInternal)
        p2offset = gp_Pnt(xexternal[0] + dxExternal, yexternal[0] + dyExternal, zExternal[0] + dzExternal)

        p3offset = gp_Pnt(xinternal[0] + dxInternal, yinternal[0] + dyInternal, zInternalptcoil[0] + dzInternal)
        p4offset = gp_Pnt(xexternal[0] + dxExternal, yexternal[0] + dyExternal, zExternalptcoil[0] + dzExternal)
        
        self.MakeEightPointBox(p1, p2, p3, p4, p1offset, p2offset, p3offset, p4offset)       
            
    def GenerateTopCircleWirenTurn(self):
        xinternal, yinternal, xexternal, yexternal, zInternalTmp, zExternalTmp = self.GetXYZPointsforCircularCoil(self.n)  
        zInternal = [z for z in zInternalTmp]
        zExternal = [z for z in zExternalTmp]
        
        zInternalptcoil = [z + self.tcoil for z in zInternalTmp]
        zExternalptcoil = [z + self.tcoil for z in zExternalTmp]
        
        p1 = gp_Pnt(xinternal[-1], yinternal[-1], zInternal[-1])
        p2 = gp_Pnt(xexternal[-1], yexternal[-1], zExternal[-1])
        
        p3 = gp_Pnt(xinternal[-1], yinternal[-1], zInternalptcoil[-1])
        p4 = gp_Pnt(xexternal[-1], yexternal[-1], zExternalptcoil[-1])
        
        
        v12 = gp_Vec(p2, p1)
        v42 = gp_Vec(p2, p4)
        
        v12.Normalize()
        v42.Normalize()
        
        #normal to the plane
        normalVec = v12.Crossed(v42)
        normalVec.Normalize()
        distance = self.T * 5
        
        p1offset = gp_Pnt(p1.X() + normalVec.X() * distance, p1.Y() + normalVec.Y() * distance, p1.Z() + normalVec.Z() * distance)
        p2offset = gp_Pnt(p2.X() + normalVec.X() * distance, p2.Y() + normalVec.Y() * distance, p2.Z() + normalVec.Z() * distance)
        
        p3offset = gp_Pnt(p3.X() + normalVec.X() * distance, p3.Y() + normalVec.Y() * distance, p3.Z() + normalVec.Z() * distance)
        p4offset = gp_Pnt(p4.X() + normalVec.X() * distance, p4.Y() + normalVec.Y() * distance, p4.Z() + normalVec.Z() * distance)
        
        self.MakeEightPointBox(p1, p2, p3, p4, p1offset, p2offset, p3offset, p4offset)
        
        
        
        
            
    
    def GenerateCircularCoil(self):
        self.GenerateBottomCircleWire() 
        self.GenerateCircularCoilnTurn(self.n)
        self.GenerateTopCircleWirenTurn()
    
    
    def GenerateShape(self):
        # Racetrack coil if self.R > 0.0
        # Rectangular coil if self.R == 0.0
        # Circular coil if self.H = self.W = 0.0
        if self.R > 0.0 and self.H > 0.0 and self.W > 0.0:
            coil = self.GenerateRacetrackCoils()
        elif self.R > 0.0 and self.H == 0.0 and self.W == 0.0:
            coil = self.GenerateCircularCoil()
    
if __name__ == "__main__":
    module = MotorCoilModule(1, "Motor Coil")
    
    
    mode = "Circular"
    mode = "Racetrack"
    if mode == "Racetrack":
        module.SetResistance(8)
    elif mode == "Circular":
        module.n = 15.5
        module.H = 0
        module.W = 0
        module.SetResistance(0.04)
        
        module.n = 190
        module.H = 0
        module.W = 0
        module.SetResistance(5)
    
    
    module.GenerateShape()
    
    # write shapes 
    from OCC.Core.TopoDS import TopoDS_Compound
    from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    for shape in module.shapes.values():
        builder.Add(compound, shape)
    step_writer = STEPControl_Writer()
    step_writer.Transfer(compound, STEPControl_AsIs)    
    fileName = "MotorCoil.stp"
    status = step_writer.Write(fileName)
    
    print("Write STEP File Done : ", fileName)
    
    
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        pass
    else:        
        for shape in module.shapes.values():
            display.DisplayShape(shape, update=False)                    
        start_display()