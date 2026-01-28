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

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ
from OCC.Core.GC import GC_MakeArcOfCircle
from KooCAEManager.KooNode import NodeManager
from KooCAEManager.KooElement import ElementManager
from OCC.Core.GeomAPI import (
    GeomAPI_PointsToBSplineSurface
)
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeVertex,
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeShell,
    BRepBuilderAPI_MakeSolid,
    BRepBuilderAPI_Sewing
)
from OCC.Core.BRepPrimAPI import (
    BRepPrimAPI_MakePrism,
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakeSphere,
    BRepPrimAPI_MakeTorus,
    BRepPrimAPI_MakeWedge,
    BRepPrimAPI_MakeRevol,
    BRepPrimAPI_MakeHalfSpace,
    BRepPrimAPI_MakeRevolution,
    BRepPrimAPI_MakeCone,
    BRepPrimAPI_MakeSweep,
    BRepPrimAPI_MakeOneAxis
)

from OCC.Core.TopoDS import (
    TopoDS_Vertex,
    TopoDS_Edge,
    TopoDS_Wire,
    TopoDS_Face,
    TopoDS_Shape,
    TopoDS_Solid,
    TopoDS_Compound,
    TopoDS_CompSolid,
    TopoDS_Shell,
    )


from OCC.Core.TopoDS import topods
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SHELL, TopAbs_FACE, TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX

from OCC.Core.BRepFill import(
BRepFill_Filling,
BRepFill_CurveConstraint,
)
import OCC.Core.GeomAbs as GeomAbs
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.TColgp import TColgp_Array2OfPnt
import math

from OCC.Core.BRep import BRep_Tool
from KooCAEManager.KooGeometry import (
    KooGeomVertex,
    KooGeomEdge,
    KooGeomLine,
    KooGeomArc,
    KooGeomWire,
    KooGeomFace,
    KooGeomFillingFace,
    KooGeomBSplineFace,
    KooGeomShell,
    KooGeomSolid,
    KooGeomPrism
)

class KooBoundary:
    def __init__(self, bid, shapeList = [], timeList = []):
        self.shapeList = shapeList
        self.bid = bid
        self.btype = None
        self.timeList = timeList
        self.hide = False

    def SetHide(self, viewer, hide = True, update = False):
        pass 
    
    def AddShape(self, shape : TopoDS_Shape):
        self.shapeList.append(shape)
    
    def AddShapeList(self, shapeList : list):
        for shape in shapeList:
            self.shapeList.append(shape)
    
    def ClearShapeList(self):
        self.shapeList = []

    def AddTime(self, time):
        self.timeList.append(time)
    
    def AddTimeList(self, timeList : list):
        for time in timeList:
            self.timeList.append(time)
    
    def SetTimeList(self, timeList : list): 
        self.timeList = timeList        
    
    def ClearTimeList(self):
        self.timeList = []

class KooBoundaryDisplacement(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], displacementList = []):
        super(KooBoundaryDisplacement,self).__init__(bid, shapeList, timeList)
        self.btype = "Displacement"
        self.dispList = displacementList        
    
    def AddDisplacement(self,time : float, displacement : gp_Vec):
        self.AddTime(time)
        self.dispList.append(displacement)
    
    def AddDisplacementList(self, timeList : list, displacementList : list):
        self.AddTimeList(timeList)
        for displacement in displacementList:
            self.dispList.append(displacement)
    
    def SetDisplacement(self, displacement : gp_Vec):
        time = 0.0 
        self.AddTime(time)
        self.dispList = [displacement]
    
    def SetDisplacementList(self, timeList : list, displacementList : list):
        self.SetTimeList(timeList)
        self.dispList = displacementList
    
    def ClearDisplacementList(self):
        self.ClearTimeList()
        self.dispList = []    

class KooBoundaryVelocity(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], velocityList = []):
        super(KooBoundaryVelocity).__init__(bid, shapeList, timeList)
        self.velList = velocityList        
        self.btype = "Velocity"
    
    def AddVelocity(self,time : float, velocity : gp_Vec):
        self.AddTime(time)
        self.velList.append(velocity)
    
    def AddVelocityList(self, timeList : list, velocityList : list):
        self.AddTimeList(timeList)
        for velocity in velocityList:
            self.velList.append(velocity)
    
    def SetVelocity(self, velocity : gp_Vec):
        time = 0.0 
        self.AddTime(time)
        self.velList = [velocity]
    
    def SetVelocityList(self, timeList : list, velocityList : list):
        self.SetTimeList(timeList)
        self.velList = velocityList
    
    def ClearVelocityList(self):
        self.ClearTimeList()
        self.velList = []

class KooBoundaryAcceleration(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], accelerationList = []):
        super(KooBoundaryAcceleration).__init__(bid, shapeList, timeList)
        self.accList = accelerationList        
        self.btype = "Acceleration"
    
    def AddAcceleration(self,time : float, acceleration : gp_Vec):
        self.AddTime(time)
        self.accList.append(acceleration)
    
    def AddAccelerationList(self, timeList : list, accelerationList : list):
        self.AddTimeList(timeList)
        for acceleration in accelerationList:
            self.accList.append(acceleration)
    
    def SetAcceleration(self, acceleration : gp_Vec):
        time = 0.0 
        self.AddTime(time)
        self.accList = [acceleration]
    
    def SetAccelerationList(self, timeList : list, accelerationList : list):
        self.SetTimeList(timeList)
        self.accList = accelerationList
    
    def ClearAccelerationList(self):
        self.ClearTimeList()
        self.accList = []

class KooBoundaryForce(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], forceList = []):
        super(KooBoundaryForce).__init__(bid, shapeList, timeList)
        self.forceList = forceList        
        self.btype = "Force"
    
    def AddForce(self,time : float, force : gp_Vec):
        self.AddTime(time)
        self.forceList.append(force)
    
    def AddForceList(self, timeList : list, forceList : list):
        self.AddTimeList(timeList)
        for force in forceList:
            self.forceList.append(force)
    
    def SetForce(self, force : gp_Vec):
        time = 0.0 
        self.AddTime(time)
        self.forceList = [force]
    
    def SetForceList(self, timeList : list, forceList : list):
        self.SetTimeList(timeList)
        self.forceList = forceList
    
    def ClearForceList(self):
        self.ClearTimeList()
        self.forceList = []

class KooBoundaryPressure(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], pressureList = []):
        super(KooBoundaryPressure).__init__(bid, shapeList, timeList)
        self.pressureList = pressureList        
        self.btype = "Pressure"
    
    def AddPressure(self,time : float, pressure : float):
        self.AddTime(time)
        self.pressureList.append(pressure)
    
    def AddPressureList(self, timeList : list, pressureList : list):
        self.AddTimeList(timeList)
        for pressure in pressureList:
            self.pressureList.append(pressure)
    
    def SetPressure(self, pressure : float):
        time = 0.0 
        self.AddTime(time)
        self.pressureList = [pressure]
    
    def SetPressureList(self, timeList : list, pressureList : list):
        self.SetTimeList(timeList)
        self.pressureList = pressureList
    
    def ClearPressureList(self):
        self.ClearTimeList()
        self.pressureList = []

class KooBoundaryTemperature(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], temperatureList = []):
        super(KooBoundaryTemperature).__init__(bid, shapeList, timeList)
        self.temperatureList = temperatureList        
        self.btype = "Temperature"
    
    def AddTemperature(self,time : float, temperature : float):
        self.AddTime(time)
        self.temperatureList.append(temperature)
    
    def AddTemperatureList(self, timeList : list, temperatureList : list):
        self.AddTimeList(timeList)
        for temperature in temperatureList:
            self.temperatureList.append(temperature)
    
    def SetTemperature(self, temperature : float):
        time = 0.0 
        self.AddTime(time)
        self.temperatureList = [temperature]
    
    def SetTemperatureList(self, timeList : list, temperatureList : list):
        self.SetTimeList(timeList)
        self.temperatureList = temperatureList
    
    def ClearTemperatureList(self):
        self.ClearTimeList()
        self.temperatureList = []    


class KooBoundaryHeatGeneration(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], heatgenerationList = []):
        super(KooBoundaryHeatGeneration).__init__(bid, shapeList, timeList)
        self.heatgenerationList = heatgenerationList        
        self.btype = "HeatGeneration"
    
    def AddHeatGeneration(self,time : float, heatgeneration : float):
        self.AddTime(time)
        self.heatgenerationList.append(heatgeneration)
    
    def AddHeatGenerationList(self, timeList : list, heatgenerationList : list):
        self.AddTimeList(timeList)
        for heatgeneration in heatgenerationList:
            self.heatgenerationList.append(heatgeneration)
    
    def SetHeatGeneration(self, heatgeneration : float):
        time = 0.0 
        self.AddTime(time)
        self.heatgenerationList = [heatgeneration]
    
    def SetHeatGenerationList(self, timeList : list, heatgenerationList : list):
        self.SetTimeList(timeList)
        self.heatgenerationList = heatgenerationList
    
    def ClearHeatGenerationList(self):
        self.ClearTimeList()
        self.heatgenerationList = []    
    
class KooBoundaryHeatFlux(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], heatfluxList = []):
        super(KooBoundaryHeatFlux).__init__(bid, shapeList, timeList)
        self.heatfluxList = heatfluxList        
        self.btype = "HeatFlux"
    
    def AddHeatFlux(self,time : float, heatflux : float):
        self.AddTime(time)
        self.heatfluxList.append(heatflux)
    
    def AddHeatFluxList(self, timeList : list, heatfluxList : list):
        self.AddTimeList(timeList)
        for heatflux in heatfluxList:
            self.heatfluxList.append(heatflux)
    
    def SetHeatFlux(self, heatflux : float):
        time = 0.0 
        self.AddTime(time)
        self.heatfluxList = [heatflux]
    
    def SetHeatFluxList(self, timeList : list, heatfluxList : list):
        self.SetTimeList(timeList)
        self.heatfluxList = heatfluxList
    
    def ClearHeatFluxList(self):
        self.ClearTimeList()
        self.heatfluxList = []
    
class KooBoundaryConvection(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], convectionList = [], temperatureList = []):
        super(KooBoundaryConvection).__init__(bid, shapeList, timeList)
        self.convectionList = convectionList        
        self.temperatureList = temperatureList
        self.btype = "Convection"
    
    def AddConvection(self,time : float, convection : float, temperature : float):
        self.AddTime(time)
        self.convectionList.append(convection)
        self.temperatureList.append(temperature)
    
    def AddConvectionList(self, timeList : list, convectionList : list, temperatureList : list):
        self.AddTimeList(timeList)        
        for convection in convectionList:
            self.convectionList.append(convection)
        for temperature in temperatureList:
            self.temperatureList.append(temperature)
    
    def SetConvection(self, convection : float, temperature : float):
        time = 0.0 
        self.AddTime(time)
        self.convectionList = [convection]
        self.temperatureList = [temperature]        
    
    def SetConvectionList(self, timeList : list, convectionList : list, temperatureList : list):
        self.SetTimeList(timeList)
        self.convectionList = convectionList
        self.temperatureList = temperatureList
    
    def ClearConvectionList(self):
        self.ClearTimeList()
        self.convectionList = []
        self.temperatureList = []

class KooBoundaryRadiation(KooBoundary):
    def __init__(self, bid, shapeList = [], timeList = [], radiationList = [], temperatureList = []):
        super(KooBoundaryRadiation).__init__(bid, shapeList, timeList)
        self.radiationList = radiationList        
        self.temperatureList = temperatureList
        self.btype = "Radiation"
    
    def AddRadiation(self,time : float, radiation : float, temperature : float):
        self.AddTime(time)
        self.radiationList.append(radiation)
        self.temperatureList.append(temperature)
    
    def AddRadiationList(self, timeList : list, radiationList : list, temperatureList : list):
        self.AddTimeList(timeList)        
        for radiation in radiationList:
            self.radiationList.append(radiation)
        for temperature in temperatureList:
            self.temperatureList.append(temperature)
    
    def SetRadiation(self, radiation : float, temperature : float):
        time = 0.0 
        self.AddTime(time)
        self.radiationList = [radiation]
        self.temperatureList = [temperature]        
    
    def SetRadiationList(self, timeList : list, radiationList : list, temperatureList : list):
        self.SetTimeList(timeList)
        self.radiationList = radiationList
        self.temperatureList = temperatureList
    
    def ClearRadiationList(self):
        self.ClearTimeList()
        self.radiationList = []
        self.temperatureList = []
        






'''
class KooBoundaryVertex:
    def __init__(self, bid, vertexList = [] ):
        self.vList = vertexList
        self.bid = bid
    
    def AddVertex(self, vertex : TopoDS_Vertex):
        self.vList.append(vertex)
    
    def AddVertexList(self, vertexList : list):
        for vertex in vertexList:
            self.vList.append(vertex)
    
    def ClearVertexList(self):
        self.vList = []

class KooBoundaryEdge: 
    def __init__(self, bid, edgeList = []):
        self.eList = edgeList
        self.bid = bid        
    
    def AddEdge(self, edge : TopoDS_Edge):
        self.eList.append(edge)

    def AddEdgeList(self, edgeList : list):
        for edge in edgeList:
            self.eList.append(edge)

    def ClearEdgeList(self):
        self.eList = [] 

class KooBoundaryFace:
    def __init__(self, bid, faceList = []):
        self.fList = faceList
        self.bid = bid
    
    def AddFace(self, face : TopoDS_Face):
        self.fList.append(face)
    
    def AddFaceList(self, faceList : list):
        for face in faceList:
            self.fList.append(face)
        
    def ClearFaceList(self):    
        self.fList = []
    
class KooBoundarySolid:
    def __init__(self, bid, solidList = []):
        self.sList = solidList
        self.bid = bid
    
    def AddSolid(self, solid : TopoDS_Solid):
        self.sList.append(solid)
    
    def AddSolidList(self, solidList : list):
        for solid in solidList:
            self.sList.append(solid)
        
    def ClearSolidList(self):
        self.sList = []
'''    



