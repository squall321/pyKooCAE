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

import scipy.integrate
import scipy.optimize
from KooODBCADManager.Module import Module
if __name__ == "__main__":
    path = os.path.join(os.getcwd(), "occProject\Generators")
    sys.path.append(path)
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
    
    
    
class ConnectorFlexible(Module):
    def __init__(self,id=0, name="", Pstart2D=None, Pend2D=None, numPoints = 100, desired_length = 7):
        super().__init__(0, "ConnectorFlexible")
                
        
        self.desired_length = desired_length
        self.points = [] 
        self.minConstraints =[] 
        self.maxConstraints =[]
        self.numPoints = numPoints
        self.points3D = []
        self.pstart3D = None
        self.pend3D = None
        self.zdir = None
        
        if Pstart2D is not None and Pend2D is not None:         
            # 시작점과 끝점을 통과하는 직선 생성 (2차원)
            Xstart = Pstart2D[0]
            Ystart = Pstart2D[1]
            Xend = Pend2D[0]
            Yend = Pend2D[1]
            self.length = math.sqrt((Xend-Xstart)**2 + (Yend-Ystart)**2)
            for i in range(numPoints):
                x = Xstart + (Xend - Xstart) / (numPoints-1) *i
                y = Ystart + (Yend - Ystart) / (numPoints-1) *i
                self.points.append((x, y))
                self.minConstraints.append(None)
                self.maxConstraints.append(None)
        else:
            for i in range(numPoints):
                self.points.append(None)
                self.minConstraints.append(None)
                self.maxConstraints.append(None)
    
    def Set3DInformation(self, pstart3D, pend3D, xdir = None, ydir = None, zdir = None):
        self.pstart3D = pstart3D
        self.pend3D = pend3D
        if zdir is not None:
            self.zdir = zdir                
        
        if self.zdir is not None:
            vstarttoend = np.array([pend3D[0] - pstart3D[0], pend3D[1] - pstart3D[1], pend3D[2] - pstart3D[2]])
            if xdir is None:
                xdir = self.normalize(vstarttoend)
            self.xdir = np.array(xdir)
            
            zdir = self.normalize(np.array(self.zdir))
            if ydir is None:
                ydir = np.cross(zdir, xdir)
                ydir = self.normalize(ydir)
            self.ydir = np.array(ydir)
            
            self.length = np.linalg.norm(vstarttoend)
            xLength = xdir[0] * vstarttoend[0] + xdir[1] * vstarttoend[1] + xdir[2] * vstarttoend[2]
            yLength = zdir[0] * vstarttoend[0] + zdir[1] * vstarttoend[1] + zdir[2] * vstarttoend[2]
            Xstart = 0.0
            Ystart = 0.0
            Xend = xLength
            Yend = yLength
            self.length = math.sqrt((Xend-Xstart)**2 + (Yend-Ystart)**2)
            self.points = [] 
            self.minConstraints =[]
            self.maxConstraints =[]
            for i in range(self.numPoints):
                x = Xstart + (Xend - Xstart) / (self.numPoints-1) *i
                y = Ystart + (Yend - Ystart) / (self.numPoints-1) *i
                self.points.append((x, y))
                self.minConstraints.append(None)
                self.maxConstraints.append(None)
            
    def AddMinConstraints(self, xrangeMin, xrangeMax, yMin):
        for i in range(len(self.points)):
            if self.points[i][0] >= xrangeMin and self.points[i][0] <= xrangeMax:
                self.minConstraints[i] = yMin
                
    def AddMaxConstraints(self, xrangeMin, xrangeMax, yMax):
        for i in range(len(self.points)):
            if self.points[i][0] >= xrangeMin and self.points[i][0] <= xrangeMax:
                self.maxConstraints[i] = yMax
    
    def OptimizeCurve(self, p1, p2, desired_length, y_min_constraint_list, y_max_constraint_list, n_degree=3, initial_slope = None, final_slope = None):
        """
        sin(nx), cos(nx) (n=1,2,3,...)  x, x^2 선형 결합으로 특정 길이와 경계를 만족하는 곡선 추정
        y 값의 최소/최대 범위를 입력으로 받으며, 최대 n 차수까지 적용 가능
        """    
        num_coeffs = 2*n_degree + 3  # 3 for polynomial 
        
        init_coeffs = np.random.randn(num_coeffs)
        init_coeffs[0] = p1[1] 
        init_coeffs[1] = (p2[1]-p1[1])/(p2[0]-p1[0])
        init_coeffs[2] = 0.0
        Lx = p2[0] - p1[0]
        
        def curve_function(coeffs, x):
            result = coeffs[0] + coeffs[1] * x/Lx + coeffs[2] * x*x/Lx/Lx
            
            for n in range(1, n_degree + 1):
                freq = 2 ** n
                result += coeffs[2*n+1] * np.sin(freq * x/Lx)
                result += coeffs[2*n+2] * np.cos(freq * x/Lx)
                
            return result 
    
        def derivative_function(coeffs, x):
            result = coeffs[1]/Lx + 2*coeffs[2]*x/Lx/Lx
            
            for n in range(1, n_degree + 1):
                freq = 2 ** n
                result += coeffs[2*n+1] * freq * np.cos(freq * x/Lx)/Lx
                result -= coeffs[2*n+2] * freq * np.sin(freq * x/Lx)/Lx
                
            return result
        
        # 아크 길이 제약조건
        def arc_length_constraint(coeffs):
            def integrand(x):
                return np.sqrt(1 + derivative_function(coeffs, x) ** 2)
            actual_length, _ = scipy.integrate.quad(integrand, p1[0], p2[0])
            return abs(actual_length - desired_length)
        
        def point_constraints(coeffs):
            return [curve_function(coeffs, p1[0]) - p1[1], curve_function(coeffs, p2[0]) - p2[1]]
        
        def slope_constraints(coeffs):
            return [derivative_function(coeffs, p1[0])-initial_slope, derivative_function(coeffs, p2[0])-final_slope]
        
        def boundary_constraints(coeffs, i):
            x_vals = np.linspace(p1[0], p2[0], len(self.points))
            x_val_i = x_vals[i]
            y_val_i = curve_function(coeffs, x_val_i)
            
            y_min_const = y_min_constraint_list[i]
            y_max_const = y_max_constraint_list[i]
            if y_min_const is None:
                y_min_const = -1.0e99
            if y_max_const is None:
                y_max_const = 1.0e99
            
            return [y_val_i - y_min_const, y_max_const - y_val_i]
        
        constraints = [
            {"type": "eq", "fun": lambda coeffs: arc_length_constraint(coeffs)},
            {"type": "eq", "fun": lambda coeffs: point_constraints(coeffs)[0]},
            {"type": "eq", "fun": lambda coeffs: point_constraints(coeffs)[1]}
        ]
        if initial_slope is not None:
            constraints.append({"type": "eq", "fun": lambda coeffs: slope_constraints(coeffs)[0]})                               
        if final_slope is not None:
            constraints.append({"type": "eq", "fun": lambda coeffs: slope_constraints(coeffs)[1]})
        
        constraintsBoundary = [] 
        for i in range(len(self.points)):
            constraintsBoundary.append({"type": "ineq", "fun": lambda coeffs: boundary_constraints(coeffs, i)[0]})
            constraintsBoundary.append({"type": "ineq", "fun": lambda coeffs: boundary_constraints(coeffs, i)[1]})
        
        constraints = constraints + constraintsBoundary
        result = scipy.optimize.minimize(
            #lambda coeffs: arc_length_constraint(coeffs), 
            lambda coeffs: np.sum(coeffs ** 2),  # 최소한의 곡률 변화 유도
            init_coeffs,
            constraints=constraints,
            #method='SLSQP',
            #options={'ftol': 1e-9, 'maxiter': 1000, 'disp': True} 
        )
        
        optimized_coeffs = result.x
        x_vals = np.linspace(p1[0], p2[0], len(self.points))
        y_vals = [curve_function(optimized_coeffs, x) for x in x_vals]
        self.points = [(x_vals[i], y_vals[i]) for i in range(len(x_vals))]
        
        optimizedLength = self.ArcLength2D(x_vals, y_vals)
        print("Optimized Length : ", optimizedLength)
        print("Desired Length : ", desired_length)
        return x_vals, y_vals, optimized_coeffs
        
    def GeneratePoints(self, ndegree = 3, desired_length = None, point1 = None, point2 = None, initial_slope = None, final_slope = None):
        if desired_length is not None:
            self.desired_length = desired_length
        if point1 is not None:
            self.points[0] = point1
        if point2 is not None:
            self.points[-1] = point2
        if point1 is not None and point2 is not None:
            Xstart = point1[0]
            Ystart = point1[1]
            Xend = point2[0]
            Yend = point2[1] 
            self.points = []
            for i in range(self.numPoints):
                x = Xstart + (Xend - Xstart) / (self.numPoints-1) *i
                y = Ystart + (Yend - Ystart) / (self.numPoints-1) *i
                self.points.append((x, y))
        return self.OptimizeCurve(self.points[0], self.points[-1], self.desired_length, self.minConstraints, self.maxConstraints, ndegree, initial_slope, final_slope)
    
    def normalize(self, v):
        return v / np.linalg.norm(v)
    
    def ArcLength2D(self, x, y):
        dx = np.diff(x)
        dy = np.diff(y)
        segment_lengths = np.sqrt(dx**2 + dy**2)
        total_length = np.sum(segment_lengths)
        return total_length
    
    def ComputeRotationMatrix(self, v2d, v3d):
        v2d = self.normalize(np.array([v2d[0], v2d[1], 0])) # 2D 벡터 (z=0)
        v3d = self.normalize(np.array(v3d)) # 3D 방향 벡터 정규화
        n3d = self.normalize(np.array(self.zdir))
        
        x_axis = v3d
        y_axis = n3d
        z_axis = np.cross(x_axis, y_axis)
        
        if np.linalg.norm(z_axis) < 1e-6:
            z_axis = np.cross(x_axis, np.array([0, 0, 1]))
            
        z_axis = self.normalize(z_axis)
        y_axis = self.normalize(np.cross(z_axis, x_axis))
        
        R = np.column_stack((x_axis, y_axis, z_axis))
        return R
    
    def Map2DCurveTo3D(self, x, y):
        X1 = self.pstart3D[0]
        Y1 = self.pstart3D[1]
        Z1 = self.pstart3D[2]
        Xn = self.pend3D[0]
        Yn = self.pend3D[1]
        Zn = self.pend3D[2]
        
        v2d = (x[-1] - x[0], y[-1] - y[0])
        v3d = (Xn - X1, Yn - Y1, Zn - Z1)
        v3d = self.xdir
        
        curve_length = self.ArcLength2D(x, y)
        v3d_unit = self.normalize(v3d)
        #Xn_adj, Yn_adj, Zn_adj = np.array([X1, Y1, Z1]) + curve_length * v3d_unit
        
    
        
        R = self.ComputeRotationMatrix(v2d, v3d)
        
        x_shifted = x - x[0]
        y_shifted = y - y[0]
        curve_2d = np.vstack((x_shifted, y_shifted, np.zeros_like(x)))
        
        curve_3d = R @ curve_2d
        curve_3d[0, :] += X1
        curve_3d[1, :] += Y1
        curve_3d[2, :] += Z1
        
        X_end, Y_end, Z_end = curve_3d[:, -1]
        
        
    
        scale_factors = np.linspace(0, 1, len(x))
        
        return curve_3d[0, :], curve_3d[1, :], curve_3d[2, :]#, Xn_adj, Yn_adj, Zn_adj
    
    def Generate3DPoints(self, update = False,  ndegree = 2, desired_length_ratio = 1.0, point3D_init = None, point3D_final = None, initial_slope = 0.0, final_slope = 0.0):        
        
        if update:            
            desired_length = self.length * desired_length_ratio
            if point3D_init is not None and point3D_final is not None:
                self.Set3DInformation(point3D_init, point3D_final)
            x_vals, y_vals, optimized_coeffs = self.GeneratePoints(ndegree, desired_length, self.points[0], self.points[-1], initial_slope, final_slope)
        else:
            x_vals = [p[0] for p in self.points]
            y_vals = [p[1] for p in self.points]            
        return self.Map2DCurveTo3D(x_vals, y_vals)
        
        
        
    
        
        
if __name__ == "__main__":
    connector = ConnectorFlexible(0, "ConnectorFlexible", (0, 0), (8.96, 0.33),100,9.05)
    connector.AddMaxConstraints(0, 4.5, 0.1)    
    
    x_vals, y_vals, optimized_coeffs = connector.GeneratePoints(2) 
    import matplotlib.pyplot as plt
    
    length = 0.0 
    for i in range(len(x_vals)-1):
        delx = x_vals[i+1] - x_vals[i]
        dely = y_vals[i+1] - y_vals[i]
        length += math.sqrt(delx*delx+dely*dely)
        #print("Length : ", length)
    print("Length : ", length)
    
    
    
    
    
    plt.plot(x_vals, y_vals)    
    plt.show()
        
        