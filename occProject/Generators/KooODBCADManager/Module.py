import os
import sys
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
import numpy as np
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Ax2, gp_Dir, gp_Pnt
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Extend.TopologyUtils import TopologyExplorer


if __name__ == "__main__":
    path = os.path.join(os.getcwd(), "occProject\Generators")
    sys.path.append(path)
    

class Module():
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.shapes = {}
        self.maxShapeID = 0
        
    def Transform(self, trsf : gp_Trsf):
        for sid in self.shapes:
            curShape = self.shapes[sid]
            self.shapes[sid] = BRepBuilderAPI_Transform(curShape, trsf, True).Shape()           
        
class ImpactModule(Module):
    def __init__(self, id, name):
        super().__init__(id, name)        
        
class SphereImpactModule(ImpactModule):
    def __init__(self, id, name, radius=1.0, center=(0.0, 0.0, 0.0)):
        super().__init__(id, name)
        self.radius = radius
        self.center = center
        self.meshSize = 0.1 
    
    def SetMeshSize(self, size):
        self.meshSize = size    
        
    def GenerateShape(self):
        
        sphere = BRepPrimAPI_MakeSphere(self.radius).Shape()
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(self.center[0], self.center[1], self.center[2]))
        sphere = BRepBuilderAPI_Transform(sphere, trsf, True).Shape()
        self.maxShapeID += 1
        self.shapes[self.maxShapeID] = sphere
        return sphere

class CylinderwithMassImpactModule(ImpactModule):
    def __init__(self, id, name, radius = 1, outerRadius = 1.2, heightFront = 0.5, heightBack = 1.0, center = (0.0, 0.0, 0.0), zDir = (0.0, 0.0, 1.0), backRadius = 1.2):
        super().__init__(id, name)
        self.radius = radius
        self.outerRadius = outerRadius
        self.backRadius = backRadius
        self.heightFront = heightFront
        self.heightBack = heightBack
        self.center = center
        normlizedzDir = np.linalg.norm(zDir)
        zDir = (zDir[0]/normlizedzDir, zDir[1]/normlizedzDir, zDir[2]/normlizedzDir)
        self.zDir = zDir    
        self.meshSize = 0.1
        
        self.shapesFront = {} 
        self.shapesBack = {}
        
        
    def SetMeshSize(self, size):
        self.meshSize = size
        
    def GenerateShape(self):
        # normal to zDir = (z1, z2, z3)
        # find normal to zDir 
        xDir = self.perpendicular_vector(self.zDir)        
        zDirVec = gp_Dir(self.zDir[0], self.zDir[1], self.zDir[2])
        xDirVec = gp_Dir(xDir[0], xDir[1], xDir[2])
        axis = gp_Ax2(gp_Pnt(self.center[0], self.center[1], self.center[2]), zDirVec, xDirVec)
        cylinder = BRepPrimAPI_MakeCylinder(axis, self.outerRadius, self.heightFront).Shape()
        
        #fillet buttom of cylinder 
        filletRadius = self.outerRadius - self.radius
        
        fillet = BRepFilletAPI_MakeFillet(cylinder)
        
        i = 0
        for e in TopologyExplorer(cylinder).edges():
            i += 1
            if i == 3:
                fillet.Add(filletRadius, e)
            
        fillet.Build()   
        blended_cylinder = fillet.Shape()    
        
        zDirwithAmpHeightFront = (self.zDir[0]* self.heightFront, self.zDir[1]* self.heightFront, self.zDir[2] * self.heightFront)     
        
        axisBack = gp_Ax2(gp_Pnt(self.center[0] + zDirwithAmpHeightFront[0], self.center[1] + zDirwithAmpHeightFront[1], self.center[2] + zDirwithAmpHeightFront[2]), zDirVec, xDirVec)
        cylinderBack = BRepPrimAPI_MakeCylinder(axisBack, self.backRadius, self.heightBack).Shape()
        
        
        filletBackRadius = self.backRadius - self.outerRadius
        if filletBackRadius < 0:
            filletBackRadius = 0
        
        if filletBackRadius > 0:
            filletBack = BRepFilletAPI_MakeFillet(cylinderBack)
            i = 0
            for e in TopologyExplorer(cylinderBack).edges():
                i += 1
                if i == 3:
                    filletBack.Add(filletBackRadius, e)
            filletBack.Build()
            cylinderBack = filletBack.Shape()  
            
        
        self.maxShapeID += 1
        self.shapes[self.maxShapeID] = blended_cylinder
        self.shapesFront[self.maxShapeID] = blended_cylinder
        self.maxShapeID += 1
        self.shapes[self.maxShapeID] = cylinderBack
        self.shapesBack[self.maxShapeID] = cylinderBack
        
        
        
        return blended_cylinder
               
        
        
        
    
    def perpendicular_vector(self, z):
        # z = (z1, z2, z3)
        z1, z2, z3 = z
        if z3 != 0:
            v = np.array([1, 1, -(z1 + z2) / z3])
        elif z2 != 0:
            v = np.array([1, -z1 / z2, 0])
        else:
            v = np.array([0, 1, 0])
        return v / np.linalg.norm(v)  # Normalize the vector    
            
    
    
    
if __name__ == "__main__":
    sphereModule = SphereImpactModule(1, "SphereModule")
    sphereModule.SetMeshSize(0.01)
    sphere = sphereModule.GenerateShape()
    
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
    
        display.DisplayShape(sphere, update=True)
        start_display()
    