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

from OCC.Core.AIS import AIS_Axis, AIS_ViewCube
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec, gp_Ax1
from OCC.Core.Quantity import Quantity_Color,Quantity_TOC_RGB, Quantity_NOC_RED, Quantity_NOC_BLUE1, Quantity_NOC_RED1, Quantity_NOC_GREEN1
from OCC.Core.Geom import Geom_Line

class KooViewCube():

    def __init__(self):

        self.view_cube = AIS_ViewCube()
        self.view_cube.SetSize(100)

    def Display(self, viewer, update = False):

        viewer._display.Context.Display(self.view_cube, update)
    
    def Hide(self, viewer ,update = False):
        viewer._display.Context.Erase(self.view_cube, update)


class KooGridPlane():

    def __init__(self):

        self.gridSize = 20
        self.axisLength = 1050
        self.centerX = 0
        self.centerY = 0
        self.xaxis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0))
        self.xaxisColor = Quantity_Color(Quantity_NOC_RED1)
        self.yaxis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0))
        self.yaxisColor = Quantity_Color(Quantity_NOC_GREEN1)
        self.gridlines = [] 
        self.aisGridLines = [] 

    def GetGridLines(self, gridsize = 20):
        self.gridlines = []
        self.gridSize = gridsize
        gridInterval = self.axisLength / self.gridSize
        for i in range(-self.gridSize,self.gridSize,1):
            xline = Geom_Line(gp_Pnt(self.centerX+0,self.centerY+i*gridInterval,0),self.xaxis.Direction())
            yline = Geom_Line(gp_Pnt(self.centerX+i*gridInterval,self.centerY,0),self.yaxis.Direction())            
            self.gridlines.append(xline)
            self.gridlines.append(yline)
            #print(xline,yline)

    def DisplayGridLines(self, viewer, gridsize = 20,update=False):
        self.GetGridLines(gridsize)
        for line in self.gridlines:
            newAisLine = viewer._display.DisplayShape(line,update=update,color=Quantity_Color(0.5,0.5,0.5, Quantity_TOC_RGB),transparency=0.8)
            newAisLine[0].Selection(0)
            #from OCC.Core.AIS import AIS_Shape
            #ais = AIS_Shape()
            #ais.Selection(-1)
            self.aisGridLines.append(newAisLine)

    def SetGridCenter(self, centerX, centerY):
        self.centerX = centerX
        self.centerY = centerY
    
    def GetNearGridPoint(self, x, y):
        interval = self.axisLength/self.gridSize
        return [round(x/interval)*interval,round(y/interval)*interval]

    def SetAxisLengthfromScreenSize(self, screenSize):
        candidateAxisLength = [
            1.0e-6,2.0e-6,5.0e-6,
            1.0e-5,2.0e-5,5.0e-5,
            1.0e-4,2.0e-4,5.0e-4,
            1.0e-3,2.0e-3,5.0e-3,
            1.0e-2,2.0e-2,5.0e-2,
            1.0e-1,2.0e-1,5.0e-1,
            1.0,2.0,5.0,
            1.0e+1,2.0e+1,5.0e+1,
            1.0e+2,2.0e+2,5.0e+2,
            1.0e+3,2.0e+3,5.0e+3,
            1.0e+4,2.0e+4,5.0e+4,
            1.0e+5,2.0e+5,5.0e+5,
            1.0e+6,2.0e+6,5.0e+6,
            1.0e+7,2.0e+7,5.0e+7,
            1.0e+8,2.0e+8,5.0e+8,
            1.0e+9,2.0e+9,5.0e+9,
            1.0e+10,2.0e+10,5.0e+10,]

        for axisLength in candidateAxisLength:
            if screenSize < axisLength:
                self.axisLength = axisLength*1.0

                interval = self.axisLength/self.gridSize
                #print(self.centerX,self.centerY)
                self.centerX = int(self.centerX/interval)*interval
                self.centerY = int(self.centerY/interval)*interval
                #print(interval,self.centerX,self.centerY)
                return
        return 1.0e+7


            
    def DisplayAxis(self, viewer,update=False):
        self.aisXAxis = AIS_Axis(self.xaxis,self.axisLength/5.0)
        self.aisXAxis.SetColor(self.xaxisColor)
        self.aisXAxis.SetWidth(5)
        self.aisYAxis = AIS_Axis(self.yaxis,self.axisLength/5.0)
        self.aisYAxis.SetColor(self.yaxisColor)
        self.aisYAxis.SetWidth(5)
        viewer._display.Context.Display(self.aisXAxis,update)
        viewer._display.Context.Display(self.aisYAxis,update)


    def Display(self, viewer, gridsize = 20,update=False):
        self.DisplayGridLines(viewer, gridsize,update)
        self.DisplayAxis(viewer,update)
    
    def RemoveFromView(self, viewer,update=False):
        viewer._display.Context.Remove(self.aisXAxis,update)
        viewer._display.Context.Remove(self.aisYAxis,update)
        for aisLine in self.aisGridLines:
            viewer._display.Context.Remove(aisLine[0],update)
        self.aisGridLines = []



class KooAxis3D():
    def __init__(self, x : gp_Ax1 = None, y : gp_Ax1 = None, z : gp_Ax1 = None):
        self.xaxis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0))
        self.xaxisColor = Quantity_Color(Quantity_NOC_RED1)
        self.yaxis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0))
        self.yaxisColor = Quantity_Color(Quantity_NOC_GREEN1)
        self.zaxis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))
        self.zaxisColor = Quantity_Color(Quantity_NOC_BLUE1)
        if x is not None:
            self.xaxis = x
        if y is not None:
            self.yaxis = y
        if z is not None:
            self.zaxis = z

        self.axisLength = 500
        
    def DisplayAxis(self, viewer, update = False,axisLength = 0):
        if axisLength != 0:
            self.axisLength = axisLength
        self.aisXAxis = AIS_Axis(self.xaxis,self.axisLength)
        self.aisXAxis.SetColor(self.xaxisColor)
        self.aisXAxis.SetWidth(5)
        self.aisYAxis = AIS_Axis(self.yaxis,self.axisLength)
        self.aisYAxis.SetColor(self.yaxisColor)
        self.aisYAxis.SetWidth(5)
        self.aisZAxis = AIS_Axis(self.zaxis,self.axisLength)
        self.aisZAxis.SetColor(self.zaxisColor)
        self.aisZAxis.SetWidth(5)
        viewer._display.Context.Display(self.aisXAxis,update)
        viewer._display.Context.Display(self.aisYAxis,update)
        viewer._display.Context.Display(self.aisZAxis,update)

    def RemoveFromView(self, viewer, update = False):
        viewer._display.Context.Remove(self.aisXAxis,update)
        viewer._display.Context.Remove(self.aisYAxis,update)
        viewer._display.Context.Remove(self.aisZAxis,update)

