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

from OCC.Core.TColgp import TColgp_Array2OfPnt
from OCC.Core.GeomAPI import GeomAPI_PointsToBSplineSurface
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.gp import gp_Pnt, gp_Vec
import OCC.Core.GeomAbs as GeomAbs

class WarpageSurface:
    def __init__(self):
        self.WarpageFile = None
        self.WarpageMatrix = []
        self.WarpageUnit = 'MicroM'
        self.shape = None

    def SetWarpageUnit(self,unit):
        self.WarpageUnit = unit

    def SetWarpageFile(self,warpageFile):
        self.WarpageFile = warpageFile

    def ImportWarpage(self,path = None, amplification = 1.0):
        if path == None:
            path = os.getcwd()
        if self.WarpageFile != None:
            curPath = os.path.join(path,self.WarpageFile)
            self.WarpageMatrix = self.ImportWarpageFile(curPath)
            if amplification != 1.0:
                for i in range(len(self.WarpageMatrix)):
                    for j in range(len(self.WarpageMatrix[i])):
                        if self.WarpageMatrix[i][j] != 9999:
                            self.WarpageMatrix[i][j] = self.WarpageMatrix[i][j]*amplification
        else:
            print("No Warpage File Specified")
    
    def ImportWarpageFile(self,path):
        if os.path.exists(path):
            with open(path,'r') as f:
                lines = f.readlines()
                lines = [line.strip() for line in lines]
                lines = [line.split('\t') for line in lines]
                lines = [[float(item) for item in line] for line in lines]
                # 6 number of significant figures
                lines = [[round(item,6) for item in line] for line in lines]
             
                #make line order reverse
                lines = lines[::-1]
                self.WarpageMatrix = lines
                return lines
        else:
            print("Warpage File Does Not Exist")
            return None
    def RemoveEmptySpace(self):
        # make all 9999 to smooth
        tmpWarpageMatrix = []
        prevWarpageMatrix = []
        curWarpageMatrix = []
        for i in range(len(self.WarpageMatrix)):
            tmpWarpageMatrix.append([])
            prevWarpageMatrix.append([])
            curWarpageMatrix.append([])

            for j in range(len(self.WarpageMatrix[i])):
                tmpWarpageMatrix[i].append(self.WarpageMatrix[i][j])
                prevWarpageMatrix[i].append(self.WarpageMatrix[i][j])
                curWarpageMatrix[i].append(self.WarpageMatrix[i][j]) 

        n9999 = 1
        while n9999 > 0:

            # If Components of self.WarpageMatrix have 9999 then smooth from neighbors value
            for i in range(len(curWarpageMatrix)):
                for j in range(len(curWarpageMatrix[i])):
                    if tmpWarpageMatrix[i][j] == 9999:
                        tmpijfromim1j = 9999
                        tmpijfromip1j = 9999
                        tmpijfromijm1 = 9999
                        tmpijfromijp1 = 9999
                        
                        if i > 0:
                            tmpijfromim1j = prevWarpageMatrix[i-1][j]
                        if i < len(prevWarpageMatrix)-1:
                            tmpijfromip1j = prevWarpageMatrix[i+1][j]
                        if j > 0:
                            tmpijfromijm1 = prevWarpageMatrix[i][j-1]
                        if j < len(prevWarpageMatrix[i])-1:
                            tmpijfromijp1 = prevWarpageMatrix[i][j+1]

                        #print(i,j,tmpijfromim1j,tmpijfromip1j,tmpijfromijm1,tmpijfromijp1)
                    
                        # do average by the values which are not 9999 and if all are 9999 then keep 9999
                        tmpij = 9999
                        n = 0
                        sum = 0.0 
                        if tmpijfromim1j != 9999:
                            n += 1.0
                            sum += tmpijfromim1j
                        if tmpijfromip1j != 9999:
                            n += 1.0
                            sum += tmpijfromip1j
                        if tmpijfromijm1 != 9999:
                            n += 1.0
                            sum += tmpijfromijm1
                        if tmpijfromijp1 != 9999:
                            n += 1.0
                            sum += tmpijfromijp1
                        if n != 0:
                            tmpij = sum/n
                        else:
                            tmpij = 9999
                        #print(tmpij)
                        curWarpageMatrix[i][j] = float(tmpij)
             # count number of point which have 9999
            n9999 = 0
            prevWarpageMatrix = curWarpageMatrix
            for i in range(len(self.WarpageMatrix)):
                for j in range(len(self.WarpageMatrix[i])):
                    if curWarpageMatrix[i][j] == 9999:
                        n9999 += 1
        self.WarpageMatrix = curWarpageMatrix
        with open('tmpWarpageFixed.txt','w') as f:
            for i in range(len(self.WarpageMatrix)):
                for j in range(len(self.WarpageMatrix[i])):
                    if j != 0:
                        f.write('\t')
                    f.write(str(self.WarpageMatrix[i][j]))
                if i < len(self.WarpageMatrix)-1:               
                    f.write('\n')
    def SmoothWarpage(self):
        tmpWarpageMatrix = []
        prevWarpageMatrix = []
        curWarpageMatrix = []
        for i in range(len(self.WarpageMatrix)):
            tmpWarpageMatrix.append([])
            prevWarpageMatrix.append([])
            curWarpageMatrix.append([])

            for j in range(len(self.WarpageMatrix[i])):
                tmpWarpageMatrix[i].append(self.WarpageMatrix[i][j])
                prevWarpageMatrix[i].append(self.WarpageMatrix[i][j])
                curWarpageMatrix[i].append(self.WarpageMatrix[i][j])       
        
 #calculate max-min of self.WarpageMatrix
        max = -9999
        min = 9999
        imax = 0
        jmax = 0
        for i in range(len(self.WarpageMatrix)):
            for j in range(len(self.WarpageMatrix[i])):
                if curWarpageMatrix[i][j] > max:
                    max = curWarpageMatrix[i][j]
                    imax = i
                    jmax = j
                if curWarpageMatrix[i][j] < min:
                    min = curWarpageMatrix[i][j]
        warpage = max-min

        
        for k in range(5):
            prevWarpageMatrix = curWarpageMatrix
            for i in range(len(self.WarpageMatrix)):
                for j in range(len(self.WarpageMatrix[i])):     
                    n = 0.0
                    sum = 0.0
                    if i != 0:
                        sum += prevWarpageMatrix[i-1][j]
                        n += 1.0
                    if i != len(self.WarpageMatrix)-1:
                        sum += prevWarpageMatrix[i+1][j]
                        n += 1.0
                    if j != 0:
                        sum += prevWarpageMatrix[i][j-1]
                        n += 1.0
                    if j != len(self.WarpageMatrix[i])-1:
                        sum += prevWarpageMatrix[i][j+1]
                        n += 1.0
                    tmpij = sum/n                              
                    curWarpageMatrix[i][j] = float(tmpij)
           
        newmax = -9999
        newmin = 9999
        for i in range(len(curWarpageMatrix)):
            for j in range(len(curWarpageMatrix[i])):
                if curWarpageMatrix[i][j] > newmax:
                    newmax = curWarpageMatrix[i][j]
                if curWarpageMatrix[i][j] < newmin:
                    newmin = curWarpageMatrix[i][j]
        newwarpage = newmax-newmin

        multipliedmin = 9999
        for i in range(len(curWarpageMatrix)):
            for j in range(len(curWarpageMatrix[i])):
                if newwarpage == 0.0:
                    curWarpageMatrix[i][j] = 0.0    
                else:
                    curWarpageMatrix[i][j] = curWarpageMatrix[i][j]*warpage/newwarpage
                if curWarpageMatrix[i][j]<multipliedmin:
                    multipliedmin = curWarpageMatrix[i][j]
        for i in range(len(curWarpageMatrix)):
            for j in range(len(curWarpageMatrix[i])):
                curWarpageMatrix[i][j] = curWarpageMatrix[i][j]-multipliedmin+min
        
        self.WarpageMatrix = curWarpageMatrix
        #write modified file to 'tmpWarpageFixed.txt'
        with open('tmpWarpageFixed.txt','w') as f:
            for i in range(len(self.WarpageMatrix)):
                for j in range(len(self.WarpageMatrix[i])):
                    if j != 0:
                        f.write('\t')
                    f.write(str(self.WarpageMatrix[i][j]))
                if i < len(self.WarpageMatrix)-1:               
                    f.write('\n')
           

    def MakeBSplineSurfacefromBSplineCurves(self,locX,locY,locZ,xLength,yLength):
        unit = 1
        if self.WarpageUnit == 'INCH':
            unit = 25.4
        elif self.WarpageUnit == 'M':
            unit = 1000
        elif self.WarpageUnit == 'MicroM':
            unit = 0.001
        unit = unit
        from OCC.Core.TColgp import TColgp_Array1OfPnt
        from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
        from OCC.Core.GeomAbs import GeomAbs_C2
        from OCC.Core.TColGeom import TColGeom_Array1OfBSplineCurve
        from OCC.Core.GeomFill import GeomFill_BSplineCurves, GeomFill_AppSweep
        from OCC.Core.GeomFill import (
            GeomFill_StretchStyle,
            GeomFill_CoonsStyle,
            GeomFill_CurvedStyle,
        )
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing


        #curve_array = TColGeom_Array1OfBSplineCurve(1, len(self.WarpageMatrix))
        curves = [] 
        for i in range(len(self.WarpageMatrix)):
            control_points = TColgp_Array1OfPnt(1,len(self.WarpageMatrix[i]))
            for j in range(len(self.WarpageMatrix[i])):
                curX = locX + i*xLength/(len(self.WarpageMatrix)-1)
                curY = locY + j*yLength/(len(self.WarpageMatrix[i])-1)
                if self.WarpageMatrix[i][j] == 9999:
                    continue
                curZ = locZ + self.WarpageMatrix[i][j]*unit
                control_points.SetValue(j+1,gp_Pnt(curX,curY,curZ))
            curCurve = GeomAPI_PointsToBSpline(control_points,3,8,GeomAbs_C2,0.001).Curve()
            #curve_array.SetValue(i+1,curCurve)
            curves.append(curCurve)
        sew = BRepBuilderAPI_Sewing()
        for i in range(len(curves)-1):
            curCurve = curves[i]
            nextCurve = curves[i+1]
            surface = GeomFill_BSplineCurves(curCurve,nextCurve,GeomFill_StretchStyle).Surface()
            face_builder = BRepBuilderAPI_MakeFace(surface,1e-6)
            face = face_builder.Face()
            sew.Add(face)
        sew.Perform()
        result = sew.SewedShape()        
        return result

        

       


    def MakeBSplineSurface(self,locX,locY,locZ,xLength,yLength):
        
        unit = 1
        if self.WarpageUnit == 'INCH':
            unit = 25.4
        elif self.WarpageUnit == 'M':
            unit = 1000
        elif self.WarpageUnit == 'MicroM':
            unit = 0.001
        unit = unit
        control_points = TColgp_Array2OfPnt(1, len(self.WarpageMatrix), 1, len(self.WarpageMatrix[0])) 
        minZ = 1.0e99
        maxZ = -1.0e99
        for i in range(len(self.WarpageMatrix)):
            for j in range(len(self.WarpageMatrix[i])):
                curZ = locZ + self.WarpageMatrix[i][j]*unit
                minZ = min(minZ,curZ)
                maxZ = max(maxZ,curZ)
        meanZ = (minZ+maxZ)/2
        for i in range(len(self.WarpageMatrix)):
            for j in range(len(self.WarpageMatrix[i])):
                curX = locX + i*xLength/(len(self.WarpageMatrix)-1)
                curY = locY + j*yLength/(len(self.WarpageMatrix[i])-1)
                if self.WarpageMatrix[i][j] == 9999:
                    continue
                curZ = locZ + self.WarpageMatrix[i][j]*unit - meanZ
                
                #print(i,j,curX,curY,curZ)
                control_points.SetValue(i+1,j+1,gp_Pnt(curX,curY,curZ))
       
       
        surface_builder = GeomAPI_PointsToBSplineSurface(control_points,1,8,GeomAbs.GeomAbs_C2,0.0001)
        
        surface = surface_builder.Surface()
        face_builder = BRepBuilderAPI_MakeFace(surface, 1e-6)
        face = face_builder.Face()

        self.shape = face 

        return surface
    
    
        #extrusion_vector= gp_Vec(0,0,1.0)

    def GetInterpolatedZ(self, xRatio, yRatio):
        x = xRatio * (len(self.WarpageMatrix)-1)
        y = yRatio * (len(self.WarpageMatrix[0])-1)
        i = int(x)
        j = int(y)
        if i == len(self.WarpageMatrix)-1:
            i = len(self.WarpageMatrix)-2
        if j == len(self.WarpageMatrix[0])-1:
            j = len(self.WarpageMatrix[0])-2
        x = x - i
        y = y - j
        z1 = self.WarpageMatrix[i][j]
        z2 = self.WarpageMatrix[i+1][j]
        z3 = self.WarpageMatrix[i][j+1]
        z4 = self.WarpageMatrix[i+1][j+1]
        z = z1*(1-x)*(1-y) + z2*x*(1-y) + z3*(1-x)*y + z4*x*y
        return z



                


    

if __name__ == '__main__':
    aWarpage = WarpageSurface()
    aWarpage.SetWarpageUnit('MM')
    #aWarpage.SetWarpageFile("ArrayWarpageDistort.txt")
    #aWarpage.SetWarpageFile("ArrayWarpage9999.txt")
    #aWarpage.SetWarpageFile("tmpWarpageFixed.txt")
    aWarpage.SetWarpageFile("ArrayWarpage.txt")
    #aWarpage.SetWarpageFile("ArrayWarpageComplex1.txt")
    aWarpage.ImportWarpage()
    aWarpage.RemoveEmptySpace()
    aWarpage.SmoothWarpage()

   # face = aWarpage.MakeBSplineSurface(0,0,0,30,10)
    face = aWarpage.MakeBSplineSurface(0,0,0,10,10)
    #face = aWarpage.MakeBSplineSurfacefromBSplineCurves(0,0,0,2,2)
    '''
    from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer            
    fileName = "BSplineSweptShell.stp"
    step_writer = STEPControl_Writer()
    step_writer.Transfer(face, STEPControl_AsIs)
    status = step_writer.Write(fileName)
    '''
    # spline to face 
    face = BRepBuilderAPI_MakeFace(face, 1e-6).Face()
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCC.Core.gp import gp_Vec
    
    # 2. Extrude할 벡터 설정 (예: +Z 방향으로 20만큼)
    extrude_vec = gp_Vec(0, 0, 0.5)
    # 3. Extrude 실행
    solid = BRepPrimAPI_MakePrism(face, extrude_vec).Shape()
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

        display.DisplayShape(solid, update=True)
        display.FitAll()
        start_display()