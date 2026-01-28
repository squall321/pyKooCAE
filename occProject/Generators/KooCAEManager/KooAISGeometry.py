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
from OCC.Core.Graphic3d import Graphic3d_NOM_PLASTIC
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf
from KooCAEManager.KooGeometry import (
    KooGeomVertex,
    KooGeomEdge,
    KooGeomLine,
    KooGeomArc,
    KooGeomCircle,
    KooGeomWire,
    KooGeomFace,
    KooGeomCutFace,
    KooGeomFillingFace,
    KooGeomBSplineFace,
    KooGeomShell,
    KooGeomSolid,
    KooGeomPrism,
    KooGeomTextureBox
)
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.Graphic3d import Graphic3d_NOM_ALUMINIUM
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.AIS import AIS_Manipulator, AIS_Shape
from OCC.Core.Graphic3d import Graphic3d_MaterialAspect, Graphic3d_NOM_ALUMINIUM, Graphic3d_NOM_COPPER

cx = [0.929411765,0.235294118,0.721568627,0,0.941176471,0.274509804,0.678431373,0.482352941,0.780392157,1,0.333333333,0.098039216,0.415686275,0.878431373,0,0.82745098,0.823529412,0.545098039,0.941176471,0.466666667,0.498039216,0.501960784,0.901960784,0.858823529,0.941176471,0.2,0,0.678431373,0.870588235,0.529411765,0.529411765,0.803921569,0.411764706,0,0.580392157,0,0,0,1,0.576470588,0.741176471,1,0.647058824,1,0.282352941,0,0.196078431,0.737254902,0.419607843,0.254901961,0.498039216,1,0.91372549,0.933333333,0,0.858823529,0.501960784,0.596078431,0.117647059,0.392156863,0,0.501960784,0.282352941,0,0.847058824,0.698039216,0.941176471,0.980392157,1,0.501960784,0.333333333,0.662745098,0.690196078,0.588235294,0,0.780392157,0.541176471,0,0.294117647,0.180392157,0.545098039,0,1,0.564705882,1,0.6,1,0.250980392,0.603921569,0.729411765,0.37254902,0,1,0,0.62745098,1,0.823529412,0.752941176,1,1,0.854901961,0.133333333,1,1,1,0.862745098,0.933333333,0.980392157,1,0.803921569,0.854901961,0.68627451,0.545098039,0.690196078,0.4,0.866666667,1]
cy = [0.643137255,0.701960784,0.525490196,0.501960784,0.501960784,0.509803922,0.847058824,0.407843137,0.082352941,0.270588235,0.419607843,0.098039216,0.352941176,1,0,0.82745098,0.411764706,0.270588235,0.97254902,0.533333333,1,0.501960784,0.901960784,0.439215686,0.901960784,0.6,0.807843137,1,0.721568627,0.807843137,0.807843137,0.360784314,0.411764706,0.8,0,0,1,0,0.62745098,0.439215686,0.717647059,0.941176471,0.164705882,0.411764706,0.239215686,0.392156863,0.803921569,0.560784314,0.556862745,0.411764706,1,0.647058824,0.588235294,0.909803922,0,0.439215686,0.501960784,0.984313725,0.564705882,0.584313725,1,0,0.819607843,0.980392157,0.749019608,0.133333333,1,0.501960784,0.71372549,0,0.419607843,0.662745098,0.768627451,0.588235294,0.501960784,0.082352941,0.168627451,0.545098039,0,0.545098039,0,1,0.843137255,0.933333333,0,0.196078431,0.549019608,0.878431373,0.803921569,0.333333333,0.619607843,0.749019608,0.6,0,0.321568627,0.388235294,0.705882353,0.752941176,1,0.752941176,0.647058824,0.545098039,1,0,0.498039216,0.862745098,0.509803922,0.980392157,0.078431373,0.521568627,0.439215686,0.933333333,0,0.878431373,0.803921569,0.62745098,0.4]
cz = [0.239215686,0.443137255,0.043137255,0,0.501960784,0.705882353,0.901960784,0.933333333,0.521568627,0,0.184313725,0.439215686,0.803921569,1,0,0.82745098,0.117647059,0.074509804,1,0.6,0,0.501960784,0.980392157,0.576470588,0.549019608,0.4,0.819607843,0.184313725,0.529411765,0.921568627,0.980392157,0.360784314,0.411764706,1,0.82745098,0.803921569,0.498039216,0.545098039,0.478431373,0.858823529,0.419607843,0.960784314,0.164705882,0.705882353,0.545098039,0,0.196078431,0.560784314,0.137254902,0.882352941,0.831372549,0,0.478431373,0.666666667,0.501960784,0.576470588,0,0.596078431,1,0.929411765,1,0,0.8,0.603921569,0.847058824,0.133333333,1,0.447058824,0.756862745,0.501960784,0.184313725,0.662745098,0.870588235,0.588235294,0.501960784,0.521568627,0.88627451,0.545098039,0.509803922,0.341176471,0,0,0,0.564705882,1,0.8,0,0.815686275,0.196078431,0.82745098,0.62745098,1,0,1,0.176470588,0.278431373,0.549019608,0.752941176,0.878431373,0.796078431,0.125490196,0.133333333,0,0,0.31372549,0.862745098,0.933333333,0.823529412,0.576470588,0.247058824,0.839215686,0.933333333,0.545098039,0.901960784,0.666666667,0.866666667,0]
#cx=[0.429411765,0.235294118,0.221568627,0,0.441176471,0.274509804,0.178431373,0.482352941,0.280392157,0.5,0.333333333,0.098039216,0.415686275,0.378431373,0,0.32745098,0.323529412,0.045098039,0.441176471,0.466666667,0.498039216,0.001960784,0.401960784,0.358823529,0.441176471,0.2,0,0.178431373,0.370588235,0.029411765,0.029411765,0.303921569,0.411764706,0,0.080392157,0,0,0,0.5,0.076470588,0.241176471,0.5,0.147058824,0.5,0.282352941,0,0.196078431,0.237254902,0.419607843,0.254901961,0.498039216,0.5,0.41372549,0.433333333,0,0.358823529,0.001960784,0.096078431,0.117647059,0.392156863,0,0.001960784,0.282352941,0,0.347058824,0.198039216,0.441176471,0.480392157,0.5,0.001960784,0.333333333,0.162745098,0.190196078,0.088235294,0,0.280392157,0.041176471,0,0.294117647,0.180392157,0.045098039,0,0.5,0.064705882,0.5,0.1,0.5,0.250980392,0.103921569,0.229411765,0.37254902,0,0.5,0,0.12745098,0.5,0.323529412,0.252941176,0.5,0.5,0.354901961,0.133333333,0.5,0.5,0.5,0.362745098,0.433333333,0.480392157,0.5,0.303921569,0.354901961,0.18627451,0.045098039,0.190196078,0.4,0.366666667,0.5]
#cy=[0.143137255,0.201960784,0.025490196,0.001960784,0.001960784,0.009803922,0.347058824,0.407843137,0.082352941,0.270588235,0.419607843,0.098039216,0.352941176,0.5,0,0.32745098,0.411764706,0.270588235,0.47254902,0.033333333,0.5,0.001960784,0.401960784,0.439215686,0.401960784,0.1,0.307843137,0.5,0.221568627,0.307843137,0.307843137,0.360784314,0.411764706,0.3,0,0,0.5,0,0.12745098,0.439215686,0.217647059,0.441176471,0.164705882,0.411764706,0.239215686,0.392156863,0.303921569,0.060784314,0.056862745,0.411764706,0.5,0.147058824,0.088235294,0.409803922,0,0.439215686,0.001960784,0.484313725,0.064705882,0.084313725,0.5,0,0.319607843,0.480392157,0.249019608,0.133333333,0.5,0.001960784,0.21372549,0,0.419607843,0.162745098,0.268627451,0.088235294,0.001960784,0.082352941,0.168627451,0.045098039,0,0.045098039,0,0.5,0.343137255,0.433333333,0,0.196078431,0.049019608,0.378431373,0.303921569,0.333333333,0.119607843,0.249019608,0.1,0,0.321568627,0.388235294,0.205882353,0.252941176,0.5,0.252941176,0.147058824,0.045098039,0.5,0,0.498039216,0.362745098,0.009803922,0.480392157,0.078431373,0.021568627,0.439215686,0.433333333,0,0.378431373,0.303921569,0.12745098,0.4]
#cz=[0.239215686,0.443137255,0.043137255,0,0.001960784,0.205882353,0.401960784,0.433333333,0.021568627,0,0.184313725,0.439215686,0.303921569,0.5,0,0.32745098,0.117647059,0.074509804,0.5,0.1,0,0.001960784,0.480392157,0.076470588,0.049019608,0.4,0.319607843,0.184313725,0.029411765,0.421568627,0.480392157,0.360784314,0.411764706,0.5,0.32745098,0.303921569,0.498039216,0.045098039,0.478431373,0.358823529,0.419607843,0.460784314,0.164705882,0.205882353,0.045098039,0,0.196078431,0.060784314,0.137254902,0.382352941,0.331372549,0,0.478431373,0.166666667,0.001960784,0.076470588,0,0.096078431,0.5,0.429411765,0.5,0,0.3,0.103921569,0.347058824,0.133333333,0.5,0.447058824,0.256862745,0.001960784,0.184313725,0.162745098,0.370588235,0.088235294,0.001960784,0.021568627,0.38627451,0.045098039,0.009803922,0.341176471,0,0,0,0.064705882,0.5,0.3,0,0.315686275,0.196078431,0.32745098,0.12745098,0.5,0,0.5,0.176470588,0.278431373,0.049019608,0.252941176,0.378431373,0.296078431,0.125490196,0.133333333,0,0,0.31372549,0.362745098,0.433333333,0.323529412,0.076470588,0.247058824,0.339215686,0.433333333,0.045098039,0.401960784,0.166666667,0.366666667,0]
class KooAISManipulator(AIS_Manipulator):
    def __init__(self):
        super(KooAISManipulator,self).__init__()
        self.name = "Manipulator"
        self.locationX = 0.0
        self.locationY = 0.0
        self.locationZ = 0.0
        self.rotationX = 0.0
        self.rotationY = 0.0
        self.rotationZ = 0.0



class KooAISGeomVertex(KooGeomVertex):
    def __init__(self, id=0, pnt = gp_Pnt(0,0,0)):
        super(KooAISGeomVertex,self).__init__(id,pnt)
        self.aisShape = None
        self.material = None
        self.texture = None
        self.color = Quantity_Color(0.0,0.0,0.0,Quantity_TOC_RGB)
        self.transparency = 0.0
        self.name = "Vertex{id}".format(id = self.id)

    def SetTransparency(self, transparency):
        self.transparency = transparency

    def SetfromKooGeomVertex(self, vertex : KooGeomVertex):
        self.pnt = vertex.pnt
        self.id = vertex.id
        self.vertex = vertex.vertex
        self.hide = vertex.hide
        self.node = None
        self.name = "Vertex{id}".format(id = self.id)
        
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:               
                self.trShape = self.vertex 
                self.aisShape = viewer._display.DisplayShape(self.vertex,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.vertex,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)

    def Transform(self, viewer, trsf : gp_Trsf, update = False):
        self.Erase(viewer, update)
        self.Display(viewer, update, trsf)

    def SetHide(self, viewer, hide = True, update = False):
        self.hide = hide
        if self.hide == True:
            self.Erase(viewer,update)
        else:
            self.Display(viewer,update) 

    def Erase(self, viewer, update = False):
        if self.aisShape != None:
            for shape in self.aisShape:
                viewer._display.Context.Erase(shape,update)

class KooAISGeomEdge(KooGeomEdge):
    def __init__(self, id=0,edge=None):
        super(KooAISGeomEdge,self).__init__(id,edge)
        self.aisShape = None
        self.material = None
        self.texture = None
        self.color = None
        self.transparency = 0.0
        self.linewidth = 5
        self.name = "Edge{id}".format(id = self.id)

    def SetTransparency(self, transparency):
        self.transparency = transparency

    def SetfromKooGeomEdge(self, edge : KooGeomEdge):
        self.id = edge.id
        self.vertices = edge.vertices
        self.nodes = edge.nodes
        self.elements = edge.elements
        self.type = edge.type
        self.hide = edge.hide               
        self.edge = edge.edge
        self.name = "edge{id}".format(id = self.id)


    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.edge
                self.aisShape = viewer._display.DisplayShape(self.edge,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.edge,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)
            self.aisShape[0].SetWidth(self.linewidth)

    def Transform(self, viewer, trsf : gp_Trsf, update = False):
        self.Erase(viewer, update)
        self.Display(viewer, update, trsf)

    def SetHide(self, viewer, hide = True, update = False):
        self.hide = hide
        if self.hide == True:
            self.Erase(viewer,update)
        else:
            self.Display(viewer,update)
        
    def Erase(self, viewer, update = False):
        if self.aisShape != None:
            for shape in self.aisShape:
                viewer._display.Context.Erase(shape,update)

class KooAISGeomLine(KooGeomLine):
    def __init__(self, id=0, vertex1=None,vertex2=None):
        super(KooAISGeomLine,self).__init__(id,vertex1,vertex2)
        self.aisShape = None
        self.material = None
        self.texture = None
        
        self.color = Quantity_Color(0.8,0.0,0.0,Quantity_TOC_RGB)
        # color with transparency        
        self.transparency = 0.0
        self.linewidth = 3
        self.name = "Line{id}".format(id = self.id)

    def SetTransparency(self, transparency):
        if transparency == 0.5:
            self.color = Quantity_Color(0.9,0.9,0.9,Quantity_TOC_RGB)
        else:
            self.color = Quantity_Color(0.8,0.0,0.0,Quantity_TOC_RGB)
        self.transparency = transparency

    def SetfromKooGeomLine(self, line : KooGeomLine):       
        self.id = line.id
        self.vertices = line.vertices
        self.nodes = line.nodes
        self.elements = line.elements
        self.type = line.type
        self.hide = line.hide               
        self.edge = line.edge
        self.name = "Line{id}".format(id = self.id)

    
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.edge
                self.aisShape = viewer._display.DisplayShape(self.edge,self.material,self.texture,self.color,self.transparency,update)
                
            else:                
                self.trShape = BRepBuilderAPI_Transform(self.edge,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)
            self.aisShape[0].SetWidth(self.linewidth)    

    def Transform(self, viewer, trsf : gp_Trsf, update = False):
        self.Erase(viewer, update)
        self.Display(viewer, update, trsf)

    def SetHide(self, viewer, hide = True, update = False):
        self.hide = hide
        if self.hide == True:
            self.Erase(viewer,update)
        else:
            self.Display(viewer,update)
    
    def Erase(self, viewer, update = False):
        if self.aisShape != None:
            for shape in self.aisShape:
                viewer._display.Context.Erase(shape,update)

class KooAISGeomArc(KooGeomArc):
    def __init__(self, id=0, vstart=None,vend=None,vcenter=None,counterclockwise=True):
        super(KooAISGeomArc,self).__init__(id,vstart,vend,vcenter,counterclockwise)
        self.aisShape = None
        self.material = None
        self.texture = None
        self.color = Quantity_Color(0.8,0.0,0.0,Quantity_TOC_RGB)

        self.transparency = 0.0
        self.linewidth = 3
        self.name = "Arc{id}".format(id = self.id)

    def SetTransparency(self, transparency):
        if transparency == 0.5:
            self.color = Quantity_Color(0.9,0.9,0.9,Quantity_TOC_RGB)
        else:
            self.color = Quantity_Color(0.8,0.0,0.0,Quantity_TOC_RGB)

        self.transparency = transparency

    def SetfromKooGeomLine(self, arc : KooGeomArc):       
        self.id = arc.id
        self.radius = arc.radius
        self.vertices = arc.vertices
        self.nodes = arc.nodes
        self.elements = arc.elements
        self.type = arc.type
        self.hide = arc.hide               
        self.edge = arc.edge   
        self.name = "Arc{id}".format(id = self.id)

    
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.edge
                self.aisShape = viewer._display.DisplayShape(self.edge,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.edge,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)
            self.aisShape[0].SetWidth(self.linewidth)
    
    def Transform(self, viewer, trsf : gp_Trsf, update = False):
        self.Erase(viewer, update)
        self.Display(viewer, update, trsf)

    def SetHide(self, viewer, hide = True, update = False):
        self.hide = hide
        if self.hide == True:
            self.Erase(viewer,update)
        else:
            self.Display(viewer,update)
    
    def Erase(self, viewer, update = False):
        if self.aisShape != None:
            for shape in self.aisShape:
                viewer._display.Context.Erase(shape,update)
    
class KooAISGeomCircle(KooGeomCircle):
    def __init__(self, id=0, vstart = None, vend = None):
        super(KooAISGeomCircle,self).__init__(id,vstart,vend)
        self.aisShape = None
        self.material = None
        self.texture = None
        self.color = Quantity_Color(0.8,0.0,0.0,Quantity_TOC_RGB)
        self.transparency = 0.0
        self.linewidth = 3
        self.name = "Circle{id}".format(id = self.id)
    
    def SetTransparency(self, transparency):
        if transparency == 0.5:
            self.color = Quantity_Color(0.9,0.9,0.9,Quantity_TOC_RGB)
        else:
            self.color = Quantity_Color(0.8,0.0,0.0,Quantity_TOC_RGB)
        self.transparency = transparency

    def SetfromKooGeomCircle(self, circle : KooGeomCircle):
        self.id = circle.id
        self.vertices = circle.vertices
        self.nodes = circle.nodes
        self.elements = circle.elements
        self.type = circle.type
        self.hide = circle.hide               
        self.edge = circle.edge
        self.name = "Circle{id}".format(id = self.id)

    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.edge
                self.aisShape = viewer._display.DisplayShape(self.edge,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.edge,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)
            self.aisShape[0].SetWidth(self.linewidth)
    
    def Transform(self, viewer, trsf : gp_Trsf, update = False):
        self.Erase(viewer, update)
        self.Display(viewer, update, trsf)

    def SetHide(self, viewer, hide = True, update = False):
        self.hide = hide
        if self.hide == True:
            self.Erase(viewer,update)
        else:
            self.Display(viewer,update)
    
    def Erase(self, viewer, update = False):
        if self.aisShape != None:
            for shape in self.aisShape:
                viewer._display.Context.Erase(shape,update)

    def WriteODB(self, stream):
        x = self.vertices[0].pnt.X()
        y = self.vertices[0].pnt.Y()
        r = self.radius
        stream.write("Cylinder,{0},{1},{2}\n".format(x,y,r))

class KooAISGeomWire(KooGeomWire):
    def __init__(self, id=0, edges=[]):
        super(KooAISGeomWire,self).__init__(id,edges)
        self.aisShape = None
        self.material = None
        self.texture = None
        self.color = None
        self.transparency = 0.0 
        self.name = "Wire{id}".format(id = self.id)

    def SetTransparency(self, transparency):
        self.transparency = transparency

    def SetfromKooGeomWire(self, wire : KooGeomWire):
        self.id = wire.id
        self.edges = wire.edges        
        self.wire = wire.wire
        self.type = wire.type
        self.hide = wire.hide    
        self.name = "Wire{id}".format(id = self.id)    

    def Display(self, viewer, update=False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.wire
                self.aisShape = viewer._display.DisplayShape(self.wire,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.wire,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)
    
    def Transform(self, viewer, trsf : gp_Trsf, update = False):
        self.Erase(viewer, update)
        self.Display(viewer, update, trsf)

    def SetHide(self, viewer, hide = True, update = False):
        self.hide = hide
        if self.hide == True:
            self.Erase(viewer,update)
        else:
            self.Display(viewer,update)
        
    def Erase(self, viewer, update = False):
        if self.aisShape != None:
            for shape in self.aisShape:
                if type(shape) == AIS_Shape:
                    viewer._display.Context.Erase(shape,update)
                else:
                    for i in range(len(shape)):
                        viewer._display.Context.Erase(shape[i],update)

class KooAISGeomFace(KooGeomFace):
    def __init__(self, id=0, wires = []):
        super(KooAISGeomFace,self).__init__(id,wires)
        self.aisShape = None
        # material as metal        
        # material which is not glare, and comparely dark        

        self.material = Graphic3d_MaterialAspect(Graphic3d_NOM_PLASTIC)
        self.material.SetAmbientColor(Quantity_Color(0.0,0.0,0.0,Quantity_TOC_RGB))
        self.material.SetDiffuseColor(Quantity_Color(0.0,0.0,0.0,Quantity_TOC_RGB))
        self.material.SetSpecularColor(Quantity_Color(0.0,0.0,0.0,Quantity_TOC_RGB))
        self.material.SetShininess(0.0)
        self.material.SetTransparency(0.0)
        self.material.SetEmissiveColor(Quantity_Color(0.0,0.0,0.0,Quantity_TOC_RGB))
        self.texture = None
        #self.color = None
        #curid = self.id%117
        self.color = Quantity_Color(cx[self.id%117],cy[self.id%117],cz[self.id%117],Quantity_TOC_RGB)
        self.color = None
        self.transparency = 0.0
        self.name = "Face{id}".format(id = self.id)

    def SetColorbyID(self):
        curid = self.id%117
        self.color = Quantity_Color(cx[curid],cy[curid],cz[curid],Quantity_TOC_RGB)

    def SetTransparency(self, transparency):
        self.transparency = transparency

    def SetfromKooGeomFace(self, face : KooGeomFace):
        self.id = face.id
        self.wire = face.wire
        self.face = face.face
        self.wires = face.wires
        self.type = face.type
        self.hide = face.hide    
        self.name = "Face{id}".format(id = self.id)    

    
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.face
                self.aisShape = viewer._display.DisplayShape(self.face,self.material,self.texture,self.color,self.transparency,update)
            else:                
                self.trShape = BRepBuilderAPI_Transform(self.face,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)

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
        if self.aisShape != None:
            for shape in self.aisShape:
                if type(shape) == AIS_Shape:
                    viewer._display.Context.Erase(shape,update)
                else:
                    for i in range(len(shape)):
                        viewer._display.Context.Erase(shape[i],update)

    def WriteODB(self, stream):
        ifinal = len(self.wire.edges)
        i = 0
        for edge in self.wire.edges:
            if type(edge) == KooAISGeomArc:
                v1 = edge.vertices[0].pnt
                v2 = edge.vertices[1].pnt
                if i == 0:
                    stream.write("OB {0} {1} I\n".format(v1.X(), v1.Y()))
                else:
                    stream.write("OS {0} {1}\n".format(v1.X(), v1.Y()))
                if i == ifinal-1:
                    stream.write("OS {0} {1}\nOE\n".format(v2.X(), v2.Y()))
            elif type(edge) == KooAISGeomLine:
                v1 = edge.vertices[0].pnt
                v2 = edge.vertices[1].pnt
                if i == 0:
                    stream.write("OB {0} {1} I\n".format(v1.X(), v1.Y()))
                else:
                    stream.write("OS {0} {1}\n".format(v1.X(), v1.Y()))
                if i == ifinal-1:
                    stream.write("OS {0} {1}\nOE\n".format(v2.X(), v2.Y()))
            i = i + 1
        for wire in self.wires:
            ifinal = len(wire.edges)
            i = 0
            for edge in wire.edges:
                if type(edge) == KooAISGeomArc:
                    v1 = edge.vertices[0].pnt
                    v2 = edge.vertices[1].pnt
                    if i == 0:
                        stream.write("OB {0} {1} I\n".format(v1.X(), v1.Y()))
                    else:
                        stream.write("OS {0} {1}\n".format(v1.X(), v1.Y()))
                    if i == ifinal-1:
                        stream.write("OS {0} {1}\nOE\n".format(v2.X(), v2.Y()))
                elif type(edge) == KooAISGeomLine:
                    v1 = edge.vertices[0].pnt
                    v2 = edge.vertices[1].pnt
                    if i == 0:
                        stream.write("OB {0} {1} I\n".format(v1.X(), v1.Y()))
                    else:
                        stream.write("OS {0} {1}\n".format(v1.X(), v1.Y()))
                    if i == ifinal-1:
                        stream.write("OS {0} {1}\nOE\n".format(v2.X(), v2.Y()))
                i = i + 1

class KooAISGeomCutFace(KooGeomCutFace):
    def __init__(self, id=0, baseFace = None, toolFace = None):
        super(KooAISGeomCutFace,self).__init__(id,baseFace,toolFace)
        self.aisShape = None
        self.material = Graphic3d_MaterialAspect(Graphic3d_NOM_PLASTIC)
        self.material.SetAmbientColor(Quantity_Color(0.0,0.0,0.0,Quantity_TOC_RGB))
        self.material.SetDiffuseColor(Quantity_Color(0.0,0.0,0.0,Quantity_TOC_RGB))
        self.material.SetSpecularColor(Quantity_Color(0.0,0.0,0.0,Quantity_TOC_RGB))
        self.material.SetShininess(0.0)
        self.material.SetTransparency(0.0)
        self.material.SetEmissiveColor(Quantity_Color(0.0,0.0,0.0,Quantity_TOC_RGB))
        self.texture = None
        self.color = Quantity_Color(cx[self.id%117],cy[self.id%117],cz[self.id%117],Quantity_TOC_RGB)
        self.color = None
        self.transparency = 0.0
        self.name = "CutFace{id}".format(id = self.id)

    def SetTransparency(self, transparency):
        self.transparency = transparency

    def SetColorbyID(self):
        curid = self.id%117
        self.color = Quantity_Color(cx[curid],cy[curid],cz[curid],Quantity_TOC_RGB)


    def SetfromKooGeomCutFace(self, face : KooGeomCutFace):
        self.id = face.id
        self.wire = face.wire
        self.wires = face.wires
        self.baseFace = face.baseFace
        self.toolFace = face.toolFace
        self.face = face.face
        self.type = face.type
        self.hide = face.hide
        self.name = "CutFace{id}".format(id = self.id)
    
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.face
                self.aisShape = viewer._display.DisplayShape(self.face,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.face,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)

    def Transform(self, viewer, trsf : gp_Trsf, update = False):
        self.Erase(viewer, update)
        self.Display(viewer, update, trsf)

    def SetHide(self, viewer, hide = True, update = False):
        self.hide = hide
        if self.hide == True:
            self.Erase(viewer,update)
        else:
            self.Display(viewer,update)

    def Erase(self, viewer, update = False):
        if self.aisShape != None:
            for shape in self.aisShape:
                if type(shape) == AIS_Shape:
                    viewer._display.Context.Erase(shape,update)
                else:
                    for i in range(len(shape)):
                        viewer._display.Context.Erase(shape[i],update)        

    def WriteODB(self, stream):        
        for wire in self.wires:
            ifinal = len(wire.edges)
            i = 0
            for edge in wire.edges:
                #if type(edge) == KooAISGeomLine or type(edge) == KooAISGeomArc:
                if type(edge) == KooAISGeomLine:
                    v1 = edge.vertices[0].pnt
                    v2 = edge.vertices[1].pnt
                    if i == 0:
                        stream.write("OB {0} {1} I\n".format(v1.X(), v1.Y()))
                    else:
                        stream.write("OS {0} {1}\n".format(v1.X(), v1.Y()))
                    if i == ifinal-1:
                        stream.write("OS {0} {1}\nOE\n".format(v2.X(), v2.Y()))
                elif type(edge) == KooAISGeomArc:
                    print("Developing...")
                    pntList = edge.GetNVertices(20)
                    for j in range(len(pntList)):
                        pnt = pntList[j] 
                        if j == 0 and i == 0:
                            stream.write("OAB {0} {1} I\n".format(pnt.X(), pnt.Y()))
                        elif j == len(pntList)-1 and i == ifinal-1:
                            stream.write("OAS {0} {1}\nOE\n".format(pnt.X(), pnt.Y()))                        
                        else:
                            if j < len(pntList)-1:
                                stream.write("OAS {0} {1}\n".format(pnt.X(), pnt.Y()))


                elif type(edge) == KooAISGeomCircle:
                    pntList = edge.GetNVertices(10)
                    for j in range(len(pntList)):
                        pnt = pntList[j]
                        if j == 0:
                            stream.write("OB {0} {1} I\n".format(pnt.X(), pnt.Y()))
                        elif j == len(pntList)-1:
                            pnt = pntList[0]
                            stream.write("OS {0} {1}\nOE\n".format(pnt.X(), pnt.Y()))
                        else:
                            stream.write("OS {0} {1}\n".format(pnt.X(), pnt.Y()))

                i = i + 1

class KooAISGeomFillingFace(KooGeomFillingFace):
    def __init__(self, id=0, wire = None, pnts = []):
        super(KooAISGeomFillingFace,self).__init__(id,wire,pnts)
        self.aisShape = None
        self.material = None
        self.texture = None
        self.color = None
        self.transparency = 0.0
        self.name = "FillingFace{id}".format(id = self.id)   

    def SetTransparency(self, transparency):
        self.transparency = transparency     

    def SetfromKooGeomFillingFace(self, face : KooGeomFillingFace):
        self.id = face.id
        self.wire = face.wire
        self.face = face.face
        self.Degree = face.Degree
        self.NbPtsOnCur = face.NbPtsOnCur
        self.NbIter = face.NbIter
        self.Anisotropie = face.Anisotropie
        self.Tol2d = face.Tol2d
        self.Tol3d = face.Tol3d
        self.TolAng = face.TolAng
        self.TolCurv = face.TolCurv
        self.MaxDeg = face.MaxDeg
        self.MaxSegments = face.MaxSegments
        self.pnts = face.pnts
        self.hide = face.hide
        self.name = "FillingFace{id}".format(id = self.id)
    
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.face
                self.aisShape = viewer._display.DisplayShape(self.face,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.face,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)
    
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
        if self.aisShape != None:
            for shape in self.aisShape:
                for i in range(len(shape)):
                    viewer._display.Context.Erase(shape[i],update)
       
class KooAISGeomBSplineFace(KooGeomBSplineFace):
    def __init__(self, id = 0, pointsMatrix = None):
        super(KooAISGeomBSplineFace,self).__init__(id,pointsMatrix)
        self.aisShape = None
        self.material = None
        self.texture = None
        self.color = None
        self.transparency = 0.0
        self.name = "BSplineFace{id}".format(id = self.id)

    def SetTransparency(self, transparency):
        self.transparency = transparency

    def SetfromKooGeomBSplineFace(self, face : KooGeomBSplineFace):
        self.id = face.id
        self.type = face.type
        self.pointsMatrix = face.pointsMatrix
        self.face = face.face
        self.wire = face.wire  
        self.wires = face.wires              
        self.hide = face.hide
        self.DegMin = face.DegMin
        self.DegMax = face.DegMax
        self.Continuity = face.Continuity
        self.Tol3D = face.Tol3D
        self.TolSurfacetoFace = face.TolSurfacetoFace
        self.name = "BSplineFace{id}".format(id = self.id)

    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.face
                self.aisShape = viewer._display.DisplayShape(self.face,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.face,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)

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
        if self.aisShape != None:
            for shape in self.aisShape:
                for i in range(len(shape)):
                    viewer._display.Context.Erase(shape[i],update)                

class KooAISGeomShell(KooGeomShell):
    def __init__(self, id, faces = []):
        super(KooAISGeomShell,self).__init__(id,faces)
        self.aisShape = None
        self.material = None
        self.texture = None
        self.color = None
        self.transparency = 0.0
        self.name = "Shell{id}".format(id = self.id)

    def SetTransparency(self, transparency):
        self.transparency = transparency

    def SetfromKooGeomShell(self, shell : KooGeomShell):
        self.id = shell.id
        self.faces = shell.faces
        self.shell = shell.shell
        self.type = shell.type
        self.hide = shell.hide        
        self.name = "Shell{id}".format(id = self.id)
    
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.shell
                self.aisShape = viewer._display.DisplayShape(self.shell,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.shell, trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)                
    
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
        if self.aisShape != None:
            for shape in self.aisShape:
                for i in range(len(shape)):
                    viewer._display.Context.Erase(shape[i],update)

class KooAISGeomSolid(KooGeomSolid):
    def __init__(self, id, shell = None):
        super(KooAISGeomSolid,self).__init__(id,shell)
        self.aisShape = None
        
        self.material = Graphic3d_MaterialAspect(Graphic3d_NOM_COPPER)
        self.texture = None
        #curid = self.id%117        
        self.color = Quantity_Color(cx[self.id%117],cy[self.id%117],cz[self.id%117],Quantity_TOC_RGB)
        self.color = None
        self.transparency = 0.0
        self.name = "Solid{id}".format(id = self.id)

    def SetTransparency(self, transparency):
        self.transparency = transparency

    def SetfromKooGeomSolid(self, solid : KooGeomSolid):
        self.id = solid.id
        self.shell = solid.shell
        self.solid = solid.solid
        self.type = solid.type
        self.hide = solid.hide        
        self.name = "Solid{id}".format(id = self.id)
    
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.solid
                self.aisShape = viewer._display.DisplayShape(self.solid,self.material,self.texture,self.color,self.transparency,update)                
                '''
                edge_color = Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB)  # Red color
                line_aspect = Prs3d_LineAspect(edge_color, Aspect_TOL_SOLID, 1)
                self.aisShape.SetAttributes(line_aspect)
                '''
            
                
            else:
                self.trShape = BRepBuilderAPI_Transform(self.solid,trsf).Shape()                
                
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)                
                
                
                '''
                # Customize edge color
                edge_color = Quantity_Color(0.0, 0.0, 1.0, Quantity_TOC_RGB)  # Red color
                from OCC.Core.Prs3d import Prs3d_LineAspect
                from OCC.Core.Aspect import Aspect_TOL_SOLID
                from OCC.Core.Quantity import Quantity_NOC_RED

                from OCC.Core.Graphic3d import Graphic3d_AspectFillArea3d, Graphic3d_MaterialAspect, Graphic3d_NOM_BRASS
                from OCC.Core.Aspect import Aspect_IS_SOLID, Aspect_TOL_SOLID



                material_aspect = Graphic3d_MaterialAspect(Graphic3d_NOM_BRASS)

                # Create Graphic3d_AspectFillArea3d
                from OCC.Core.Aspect import Aspect_InteriorStyle
                asint = Aspect_InteriorStyle(Aspect_IS_SOLID)
                theEdgeLineType = Aspect_TOL_SOLID
                fill_area_aspect = Graphic3d_AspectFillArea3d(asint,self.color, edge_color, theEdgeLineType, 1.0, material_aspect, material_aspect)
                fill_area_aspect.SetEdgeColor(edge_color)

                # Assuming ais_shape is your AIS_Shape object
                # Set the aspect to the AIS shape
                aisShape = self.aisShape[0] 
                drawer = aisShape.Attributes()

                # Access the ShadingAspect
                shading_aspect = drawer.ShadingAspect()
                

                shading_aspect.SetAspect(fill_area_aspect)
                drawer.SetShadingAspect(shading_aspect)
                aisShape.SetAttributes(drawer)

                viewer._display.Context.Redisplay(self.aisShape[0],True)
                '''

                


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
        if self.aisShape != None:
            for shape in self.aisShape:
                #for i in range(len(shape)):
                viewer._display.Context.Erase(shape,update)

class KooAISGeomPrism(KooGeomPrism):
    def __init__(self, id=0, baseGeomFace = None, direction = gp_Vec(0,0,1), thickness = 1.0):
        super(KooAISGeomPrism,self).__init__(id,baseGeomFace,direction,thickness)
        self.aisShape = None
        self.material = None
        self.texture = None
        self.color = None
        self.transparency = 0.0
        self.name = "Prism{id}".format(id = self.id)
    
    def SetTransparency(self, transparency):
        self.transparency = transparency

    def SetfromKooGeomPrism(self, prism : KooGeomPrism):
        self.id = prism.id
        self.shell = prism.shell
        self.solid = prism.solid
        self.type = prism.type
        self.hide = prism.hide
        self.name = "Prism{id}".format(id = self.id)        
    
    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.solid
                self.aisShape = viewer._display.DisplayShape(self.solid,self.material,self.texture,self.color,self.transparency,update)
            else:
                self.trShape = BRepBuilderAPI_Transform(self.solid,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)
    
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
        if self.aisShape != None:
            for shape in self.aisShape:
                #for i in range(len(shape)):
                viewer._display.Context.Erase(shape,update)

class Texture(object):
    """
    This class encapsulates the necessary texture properties:
    Filename, toScaleU, etc.
    """

    def __init__(self, filename):
        
        self._filename = filename
        self._toScaleU = 1.0
        self._toScaleV = 1.0
        self._toRepeatU = 1.0
        self._toRepeatV = 1.0
        self._originU = 0.0
        self._originV = 0.0

    def TextureScale(self, toScaleU, toScaleV):
        self._toScaleU = toScaleU
        self._toScaleV = toScaleV

    def TextureRepeat(self, toRepeatU, toRepeatV):
        self._toRepeatU = toRepeatU
        self._toRepeatV = toRepeatV

    def TextureOrigin(self, originU, originV):
        self._originU = originU
        self._originV = originV

    def GetProperties(self):
        return (
            self._filename,
            self._toScaleU,
            self._toScaleV,
            self._toRepeatU,
            self._toRepeatV,
            self._originU,
            self._originV,
        )


class KooAISGeomTextureBox(KooGeomTextureBox):
    def __init__(self, id=0, texturePath = "", xLoc = 0.0, yLoc = 0.0, zLoc = 0.0, dx = 1.0, dy = 1.0, dz = 1.0):
        super(KooAISGeomTextureBox,self).__init__(id,texturePath,xLoc,yLoc,zLoc,dx,dy,dz)
        self.aisShape = None
        if not os.path.isfile(self.textureImagePath):
            self.texture = None
        else:
            self.texture = Texture(self.textureImagePath)        

        self.material = None
        self.color = None
        self.transparency = 0.5
        self.name = "TextureBox{id}".format(id = self.id)
        # edge color
        # self.edgeColor = Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB)  # White, matching a common background

    
    def SetTransparency(self, transparency):
        self.transparency = transparency+0.5
    
    def SetfromKooGeomTextureBox(self, textureBox : KooGeomTextureBox):
        self.id = textureBox.id
        self.texturePath = textureBox.texturePath
        self.xLoc = textureBox.xLoc
        self.yLoc = textureBox.yLoc
        self.zLoc = textureBox.zLoc
        self.dx = textureBox.dx
        self.dy = textureBox.dy
        self.dz = textureBox.dz
        self.hide = textureBox.hide
        self.name = "TextureBox{id}".format(id = self.id)

    def Display(self, viewer, update = False, trsf : gp_Trsf = None):
        if self.hide == False:
            if trsf == None:
                self.trShape = self.solid
                self.aisShape = viewer._display.DisplayShape(self.solid,self.material,self.texture,self.color,self.transparency,update)                

            else:
                self.trShape = BRepBuilderAPI_Transform(self.solid,trsf).Shape()
                self.aisShape = viewer._display.DisplayShape(self.trShape,self.material,self.texture,self.color,self.transparency,update)
            '''from OCC.Core.Prs3d import Prs3d_LineAspect
            from OCC.Core.Aspect import Aspect_TOL_SOLID

            line_aspect = Prs3d_LineAspect(self.edgeColor, Aspect_TOL_SOLID, 0.5)  # Width is 0.5
            viewer._display.Context.SetAspect(line_aspect, self.ais_shape, False)'''

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
        if self.aisShape != None:
            for shape in self.aisShape:
                #for i in range(len(shape)):
                viewer._display.Context.Erase(shape,update)

