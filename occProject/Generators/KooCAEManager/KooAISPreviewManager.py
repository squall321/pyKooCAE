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

## QT Viewer
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
from OCC.Display.backend import load_backend

load_backend("pyqt5")
from OCC.Display.backend import get_qt_modules

QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()
from OCC.Display.qtDisplay import qtViewer3d

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
from OCC.Core.TopAbs import(
    TopAbs_COMPOUND,
    TopAbs_COMPSOLID,
    TopAbs_SOLID,
    TopAbs_SHELL,
    TopAbs_FACE,
    TopAbs_WIRE,
    TopAbs_EDGE,
    TopAbs_VERTEX,
) 
from KooCAEManager.KooAISGeometryManager import (
    KooViewer,
)

class KooAISPreviewManager:

    def __init__(self,parent = None, viewer = None):
        self.VertexList = []
        self.EdgeList = []
        self.WireList = []
        self.FaceList = []
        self.ShellList = []
        self.SolidList = []
        self.parent = parent
        if viewer == None:
            self.viewer = KooViewer(self.parent)
        else:
            self.viewer = viewer 

    def AddVertex(self, vertex : TopoDS_Vertex, update = False):
        aisShape = self.viewer._display.DisplayShape(vertex,update=update)
        self.VertexList.append(aisShape)
    
    def AddEdge(self, edge : TopoDS_Edge, update = False):
        aisShape = self.viewer._display.DisplayShape(edge, update=update)
        self.EdgeList.append(aisShape)
    
    def AddWire(self, wire : TopoDS_Wire, update = False):
        aisShape = self.viewer._display.DisplayShape(wire, update=update)
        self.WireList.append(aisShape)
    
    def AddFace(self, face : TopoDS_Face, update = False):
        aisShape = self.viewer._display.DisplayShape(face, update=update)
        self.FaceList.append(aisShape)
    
    def AddShell(self, shell : TopoDS_Shell, update = False):
        aisShape = self.viewer._display.DisplayShape(shell, update=update)
        self.ShellList.append(aisShape)
    
    def AddSolid(self, solid : TopoDS_Solid, update = False):
        aisShape = self.viewer._display.DisplayShape(solid, update=update)
        self.SolidList.append(aisShape)

    def ClearAll(self, update = False):
        for vertex in self.VertexList:
            for i in range(len(vertex)):
                self.viewer._display.Context.Erase(vertex[i],update)
        for edge in self.EdgeList:
            for i in range(len(edge)):
                self.viewer._display.Context.Erase(edge[i],update)
        for wire in self.WireList:
            for i in range(len(wire)):
                self.viewer._display.Context.Erase(wire[i],update)
        for face in self.FaceList:
            for i in range(len(face)):
                self.viewer._display.Context.Erase(face[i],update)
        for shell in self.ShellList:
            for i in range(len(shell)):
                self.viewer._display.Context.Erase(shell[i],update)
        for solid in self.SolidList:
            for i in range(len(solid)):
                self.viewer._display.Context.Erase(solid[i],update)

        self.VertexList.clear()
        self.EdgeList.clear()
        self.WireList.clear()
        self.FaceList.clear()
        self.ShellList.clear()
        self.SolidList.clear()
