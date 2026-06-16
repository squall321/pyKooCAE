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
import math
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Ax2, gp_Dir, gp_Pnt, gp_Ax1
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeRevol
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.GC import GC_MakeArcOfCircle, GC_MakeSegment
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
    def __init__(self, id, name, radius = 1, outerRadius = 1.2, heightFront = 0.5, heightBack = 1.0, center = (0.0, 0.0, 0.0), zDir = (0.0, 0.0, 1.0), backRadius = 1.2, midRadius = 0, heightMid = 0):
        # midRadius/heightMid == 0 → 2단(front+back) 동작 (하위호환).
        # > 0 → 3단(front 고무팁 + mid 중간단 + back 본체).
        super().__init__(id, name)
        self.radius = radius
        self.outerRadius = outerRadius
        self.backRadius = backRadius
        self.heightFront = heightFront
        self.heightBack = heightBack
        self.midRadius = midRadius
        self.heightMid = heightMid
        self.center = center
        normlizedzDir = np.linalg.norm(zDir)
        zDir = (zDir[0]/normlizedzDir, zDir[1]/normlizedzDir, zDir[2]/normlizedzDir)
        self.zDir = zDir
        self.meshSize = 0.1

        self.shapesFront = {}
        self.shapesBack = {}
        self.shapesMid = {}
        
        
    def SetMeshSize(self, size):
        self.meshSize = size

    def _make_convex_front(self, center, xDir, zDir, r_small, r_big, h):
        """바닥 r_small → 볼록 1/4호 → 상단 r_big (높이 h)인 회전체.

        프로파일(축 포함 평면): 축바닥 → 바닥외주(r_small) → 볼록호 → 상단외주(r_big) → 축상단 → 닫힘.
        zDir 축 중심으로 회전. r_big>r_small일 때만 호, 아니면 직선 실린더로 fallback.
        '⌀20 실린더 바닥 R6 필렛' 과 동일 형상 (필렛=revolve 동치, 메시 검증됨).
        """
        cx, cy, cz = center
        ux, uy, uz = xDir
        wx, wy, wz = zDir
        def P(r, z):
            return gp_Pnt(cx + r*ux + z*wx, cy + r*uy + z*wy, cz + r*uz + z*wz)
        if r_big <= r_small:
            # 확장 없음 → 직선 실린더
            axis = gp_Ax2(gp_Pnt(cx, cy, cz), gp_Dir(wx, wy, wz), gp_Dir(ux, uy, uz))
            return BRepPrimAPI_MakeCylinder(axis, r_big if r_big > 0 else r_small, h).Shape()
        p0 = P(0.0, 0.0)              # 축 바닥
        p1 = P(r_small, 0.0)         # 바닥 외주
        p2 = P(r_big, h)             # 상단 외주
        p3 = P(0.0, h)              # 축 상단
        # 볼록 호 중간점 (45도 위치, 바깥으로 부푼 쪽)
        rm = r_small + (r_big - r_small) * math.sin(math.radians(45))
        zm = h * (1.0 - math.cos(math.radians(45)))
        pmid = P(rm, zm)
        arc = GC_MakeArcOfCircle(p1, pmid, p2).Value()
        e_arc = BRepBuilderAPI_MakeEdge(arc).Edge()
        e_bottom = BRepBuilderAPI_MakeEdge(GC_MakeSegment(p0, p1).Value()).Edge()
        e_top = BRepBuilderAPI_MakeEdge(GC_MakeSegment(p2, p3).Value()).Edge()
        e_axis = BRepBuilderAPI_MakeEdge(GC_MakeSegment(p3, p0).Value()).Edge()
        wire = BRepBuilderAPI_MakeWire(e_bottom, e_arc, e_top, e_axis).Wire()
        face = BRepBuilderAPI_MakeFace(wire).Face()
        revol_axis = gp_Ax1(gp_Pnt(cx, cy, cz), gp_Dir(wx, wy, wz))
        return BRepPrimAPI_MakeRevol(face, revol_axis).Shape()

    def GenerateShape(self):
        # normal to zDir = (z1, z2, z3)
        # find normal to zDir
        xDir = self.perpendicular_vector(self.zDir)
        zDirVec = gp_Dir(self.zDir[0], self.zDir[1], self.zDir[2])
        xDirVec = gp_Dir(xDir[0], xDir[1], xDir[2])
        # front: 바닥 radius → 볼록 1/4호 → 상단 outerRadius (revolve). 필렛 동치, 메시 검증됨.
        blended_cylinder = self._make_convex_front(
            self.center, xDir, self.zDir, self.radius, self.outerRadius, self.heightFront)

        use_mid = (self.midRadius > 0 and self.heightMid > 0)

        # mid 단 (3단일 때만) — front 끝 위치에서 시작, midRadius × heightMid
        cylinderMid = None
        if use_mid:
            zAmpFront = (self.zDir[0]*self.heightFront, self.zDir[1]*self.heightFront, self.zDir[2]*self.heightFront)
            axisMid = gp_Ax2(gp_Pnt(self.center[0]+zAmpFront[0], self.center[1]+zAmpFront[1], self.center[2]+zAmpFront[2]), zDirVec, xDirVec)
            cylinderMid = BRepPrimAPI_MakeCylinder(axisMid, self.midRadius, self.heightMid).Shape()
            # front→mid 단차 fillet
            filletMidRadius = self.midRadius - self.outerRadius
            if filletMidRadius < 0:
                filletMidRadius = 0
            # 단 높이의 49% 클램프 (OCC fillet build 실패 방지)
            filletMidRadius = min(filletMidRadius, self.heightMid * 0.49)
            if filletMidRadius > 0:
                filletMid = BRepFilletAPI_MakeFillet(cylinderMid)
                i = 0
                for e in TopologyExplorer(cylinderMid).edges():
                    i += 1
                    if i == 3:
                        filletMid.Add(filletMidRadius, e)
                filletMid.Build()
                cylinderMid = filletMid.Shape()

        # back 단 시작 위치: 2단이면 front 끝, 3단이면 mid 끝
        backOffset = self.heightFront + (self.heightMid if use_mid else 0.0)
        zDirwithAmpHeightFront = (self.zDir[0]*backOffset, self.zDir[1]*backOffset, self.zDir[2]*backOffset)

        axisBack = gp_Ax2(gp_Pnt(self.center[0] + zDirwithAmpHeightFront[0], self.center[1] + zDirwithAmpHeightFront[1], self.center[2] + zDirwithAmpHeightFront[2]), zDirVec, xDirVec)
        cylinderBack = BRepPrimAPI_MakeCylinder(axisBack, self.backRadius, self.heightBack).Shape()


        # back 단차 fillet 기준: 2단이면 outerRadius, 3단이면 midRadius
        prevRadius = self.midRadius if use_mid else self.outerRadius
        filletBackRadius = self.backRadius - prevRadius
        if filletBackRadius < 0:
            filletBackRadius = 0
        filletBackRadius = min(filletBackRadius, self.heightBack * 0.49)

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
        if use_mid:
            self.maxShapeID += 1
            self.shapes[self.maxShapeID] = cylinderMid
            self.shapesMid[self.maxShapeID] = cylinderMid
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
    