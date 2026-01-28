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

from KooCAEManager.KooBoundary import (
    KooBoundaryDisplacement,
    KooBoundaryVelocity,
    KooBoundaryAcceleration,    
    KooBoundaryForce,
    KooBoundaryPressure,
    KooBoundaryTemperature,
    KooBoundaryHeatGeneration,    
    KooBoundaryHeatFlux,    
    KooBoundaryConvection,
    KooBoundaryRadiation,    

)

class KooBoundaryManager():
    def __init__(self):
        self.maxboundaryid = 0 
        self.boundaryDict = {}
        self.boundaryDispList = []
        self.boundaryVelList = [] 
        self.boundaryAccList = []
        self.boundaryForceList = []
        self.boundaryPressureList = []
        self.boundaryTemperatureList = []
        self.boundaryHeatFluxList = []
        self.boundaryHeatGenerationList = [] 
        self.boundaryConvectionList = []
        self.boundaryRadiationList = []


    def AddBoundary(self, boundary):
        self.maxboundaryid += 1
        boundary.bid = self.maxboundaryid
        self.boundaryDict[self.maxboundaryid] = boundary
        if type(boundary) == KooBoundaryDisplacement:
            self.boundaryDispList.append(boundary)
        elif type(boundary) == KooBoundaryVelocity:
            self.boundaryVelList.append(boundary)
        elif type(boundary) == KooBoundaryAcceleration:
            self.boundaryAccList.append(boundary)
        elif type(boundary) == KooBoundaryForce:
            self.boundaryForceList.append(boundary)
        elif type(boundary) == KooBoundaryPressure:
            self.boundaryPressureList.append(boundary)
        elif type(boundary) == KooBoundaryTemperature:
            self.boundaryTemperatureList.append(boundary)
        elif type(boundary) == KooBoundaryHeatGeneration:
            self.boundaryHeatGenerationList.append(boundary)    
        elif type(boundary) == KooBoundaryHeatFlux:
            self.boundaryHeatFluxList.append(boundary)
        elif type(boundary) == KooBoundaryConvection:
            self.boundaryConvectionList.append(boundary)
        elif type(boundary) == KooBoundaryRadiation:
            self.boundaryRadiationList.append(boundary)        
        return boundary

    def RemoveBoundary(self, bid):
        boundary = self.boundaryDict[bid]
        if type(boundary) == KooBoundaryDisplacement:
            self.boundaryDispList.remove(boundary)
        elif type(boundary) == KooBoundaryVelocity:
            self.boundaryVelList.remove(boundary)
        elif type(boundary) == KooBoundaryAcceleration:
            self.boundaryAccList.remove(boundary)
        elif type(boundary) == KooBoundaryForce:
            self.boundaryForceList.remove(boundary)
        elif type(boundary) == KooBoundaryPressure:
            self.boundaryPressureList.remove(boundary)
        elif type(boundary) == KooBoundaryTemperature:
            self.boundaryTemperatureList.remove(boundary)
        elif type(boundary) == KooBoundaryHeatFlux:
            self.boundaryHeatFluxList.remove(boundary)
        elif type(boundary) == KooBoundaryHeatGeneration:
            self.boundaryHeatGenerationList.remove(boundary)
        elif type(boundary) == KooBoundaryConvection:
            self.boundaryConvectionList.remove(boundary)
        elif type(boundary) == KooBoundaryRadiation:
            self.boundaryRadiationList.remove(boundary)        
        del self.boundaryDict[bid]
        
    def RemoveAll(self):
        self.maxboundaryid = 0 
        self.boundaryDict = {}
        self.boundaryDispList = []
        self.boundaryVelList = [] 
        self.boundaryAccList = []
        self.boundaryForceList = []
        self.boundaryPressureList = []
        self.boundaryTemperatureList = []
        self.boundaryHeatFluxList = []
        self.boundaryHeatGenerationList = [] 
        self.boundaryConvectionList = []
        self.boundaryRadiationList = []
        
    
