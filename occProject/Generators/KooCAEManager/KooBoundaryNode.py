from __future__ import annotations
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
from KooCAEManager.KooOperator import *

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


class KooBoundaryNode:
    def __init__(self, bid, name):
        self.bid = bid
        self.name = name
        self.btype = None
    
    def WritetoDynaKeyword(self, startID):
        pass
    
    def WriteStreamDynaKeyword(self, stream, startID):
        pass
   
class KooBoundaryPrescribedMotionRigid(KooBoundaryNode):
    def __init__(self, bid, name="", node=None, dof=None, vad=0, lcid=None, sf=1.0, vid=0, death=1.0E28, birth=0.0):
        if name == "":
            name = "PrescribedMotionRigid" + str(bid)
        super(KooBoundaryPrescribedMotionRigid,self).__init__(bid,name)
        self.btype = "PrescribedMotionRigid"
        self.node = node
        self.dof = dof
        self.vad = vad
        self.lcid = lcid
        self.sf = sf
        self.vid = vid
        self.death = death
        self.birth = birth
    
    def SetNode(self, node):
        self.node = node
    
    def SetDOF(self, dof):
        # 1 : X, 2 : Y , 3 : Z, 4 : defined VID
        self.dof = dof
    
    def SetVAD(self, vad):
        self.vad = vad
    
    def SetLCID(self, lcid):
        self.lcid = lcid
    
    def SetScaleFactor(self, sf):
        self.sf = sf
    
    def SetVID(self, vid):
        self.vid = vid
    
    def SetDeath(self, death):
        self.death = death
    
    def SetBirth(self, birth):
        self.birth = birth
        
    def WritetoNastranKeyword(self, startID):
        curStr = ""
        return curStr            
                    
    def WritetoDynaKeyword(self, startID = 0, startnid = 0):
        keywords = ""
        bid = self.bid + startID
        keywords += "*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID\n"
        idStr = format(bid, ">10")
        nameStr = format(self.name, ">70")        
        keywords += idStr + nameStr + "\n"
        
        nidstr = format(self.node.id + startnid, ">10")
        dofstr = format(self.dof, ">10")
        vadstr = format(self.vad, ">10")
        lcidstr = format(self.lcid, ">10")
        sfstr = format(self.sf, ">10.3f")
        vidstr = format(self.vid, ">10")
        deathstr = format(self.death, ">10.3E")
        birthstr = format(self.birth, ">10.3E")
        keywords += nidstr + dofstr + vadstr + lcidstr + sfstr + vidstr + deathstr + birthstr + "\n"
        return keywords
    
    def WriteStreamDynaKeyword(self, stream, startID = 0, startnid = 0):
        bid = self.bid + startID
        stream.write("*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID\n")
        idStr = format(bid, ">10")
        nameStr = format(self.name, ">70")
        stream.write(idStr + nameStr + "\n")
        
        nidstr = format(self.node.id + startnid, ">10")
        dofstr = format(self.dof, ">10")
        vadstr = format(self.vad, ">10")
        lcidstr = format(self.lcid, ">10")
        sfstr = format(self.sf, ">10.3f")
        vidstr = format(self.vid, ">10")
        deathstr = format(self.death, ">10.3E")
        birthstr = format(self.birth, ">10.3E")
        stream.write(nidstr + dofstr + vadstr + lcidstr + sfstr + vidstr + deathstr + birthstr + "\n")   
         
class KooBoundaryPrescribedMotionNode(KooBoundaryNode):
    def __init__(self, bid, name="", node=None, dof=None, vad=0, lcid=None, sf=1.0, vid=0, death=1.0E28, birth=0.0):
        if name == "":
            name = "PrescribedMotionNode" + str(bid)
        super(KooBoundaryPrescribedMotionNode,self).__init__(bid,name)
        self.btype = "PrescribedMotionNode"
        self.node = node
        self.dof = dof
        self.vad = vad
        self.lcid = lcid
        self.sf = sf
        self.vid = vid
        self.death = death
        self.birth = birth
    
    def SetNode(self, node):
        self.node = node
    
    def SetDOF(self, dof):
        # 1 : X, 2 : Y , 3 : Z, 4 : defined VID
        self.dof = dof
    
    def SetVAD(self, vad):
        self.vad = vad
    
    def SetLCID(self, lcid):
        self.lcid = lcid
    
    def SetScaleFactor(self, sf):
        self.sf = sf
    
    def SetVID(self, vid):
        self.vid = vid
    
    def SetDeath(self, death):
        self.death = death
    
    def SetBirth(self, birth):
        self.birth = birth
        
    def WritetoNastranKeyword(self, startID):
        curStr = ""
        return curStr
                    
    def WritetoDynaKeyword(self, startID = 0, startnid = 0):
        keywords = ""
        bid = self.bid + startID
        keywords += "*BOUNDARY_PRESCRIBED_MOTION_NODE_ID\n"
        idStr = format(bid, ">10")
        nameStr = format(self.name, ">70")        
        keywords += idStr + nameStr + "\n"
        
        nidstr = format(self.node.id + startnid, ">10")
        dofstr = format(self.dof, ">10")
        vadstr = format(self.vad, ">10")
        lcidstr = format(self.lcid, ">10")
        sfstr = format(self.sf, ">10.3f")
        vidstr = format(self.vid, ">10")
        deathstr = format(self.death, ">10.3E")
        birthstr = format(self.birth, ">10.3E")
        keywords += nidstr + dofstr + vadstr + lcidstr + sfstr + vidstr + deathstr + birthstr + "\n"
        return keywords
    
    def WriteStreamDynaKeyword(self, stream, startID = 0, startnid = 0):
        bid = self.bid + startID
        stream.write("*BOUNDARY_PRESCRIBED_MOTION_NODE_ID\n")
        idStr = format(bid, ">10")
        nameStr = format(self.name, ">70")
        stream.write(idStr + nameStr + "\n")
        
        nidstr = format(self.node.id + startnid, ">10")
        dofstr = format(self.dof, ">10")
        vadstr = format(self.vad, ">10")
        lcidstr = format(self.lcid, ">10")
        sfstr = format(self.sf, ">10.3f")
        vidstr = format(self.vid, ">10")
        deathstr = format(self.death, ">10.3E")
        birthstr = format(self.birth, ">10.3E")
        stream.write(nidstr + dofstr + vadstr + lcidstr + sfstr + vidstr + deathstr + birthstr + "\n")

class KooBoundaryPrescribedMotionNodes(KooBoundaryNode):
    def __init__(self, bid, name="", node=[], dof=[], vad=[], lcid=[], sf=[], vid=[], death=[], birth=[]):
        if name == "":
            name = "PrescribedMotionNodes" + str(bid)
        super(KooBoundaryPrescribedMotionNode,self).__init__(bid,name)
        self.btype = "PrescribedMotionNodes"
        self.nodes = node
        self.dofs = dof
        self.vads = vad
        self.lcids = lcid
        self.sfs = sf
        self.vids = vid
        self.deaths = death
        self.births = birth
    
    def AddNode(self, node):
        self.nodes.append(node)
    
    def AddDOF(self, dof):
        # 1 : X, 2 : Y , 3 : Z, 4 : defined VID
        self.dofs.append(dof)
    
    def AddVAD(self, vad):
        self.vads.append(vad)
    
    def AddLCID(self, lcid):
        self.lcids.append(lcid)
    
    def AddScaleFactor(self, sf):
        self.sfs.append(sf)
    
    def AddVID(self, vid):
        self.vids.append(vid)
    
    def AddDeath(self, death):
        self.deaths.append(death)
    
    def AddBirth(self, birth):
        self.births.append(birth)
        
    def WritetoNastranKeyword(self, startID):
        curStr = ""
        return curStr
                    
    def WritetoDynaKeyword(self, startID = 0, startnid = 0):
        keywords = ""
        
        keywords += "*BOUNDARY_PRESCRIBED_MOTION_NODE\n"
                
        for i in range(len(self.nodes)):            
            nidstr = format(self.node[i].id + startnid, ">10")
            dofstr = format(self.dofs[i], ">10")
            vadstr = format(self.vads[i], ">10")
            lcidstr = format(self.lcids[i], ">10")
            sfstr = format(self.sfs[i], ">10.3f")
            vidstr = format(self.vids[i], ">10")
            deathstr = format(self.deaths[i], ">10.3E")
            birthstr = format(self.births[i], ">10.3E")
            keywords += nidstr + dofstr + vadstr + lcidstr + sfstr + vidstr + deathstr + birthstr + "\n"
        return keywords
    
    def WriteStreamDynaKeyword(self, stream, startID = 0, startnid = 0):
        stream.write("*BOUNDARY_PRESCRIBED_MOTION_NODE\n")
                
        for i in range(len(self.nodes)):            
            nidstr = format(self.node[i].id + startnid, ">10")
            dofstr = format(self.dofs[i], ">10")
            vadstr = format(self.vads[i], ">10")
            lcidstr = format(self.lcids[i], ">10")
            sfstr = format(self.sfs[i], ">10.3f")
            vidstr = format(self.vids[i], ">10")
            deathstr = format(self.deaths[i], ">10.3E")
            birthstr = format(self.births[i], ">10.3E")
            stream.write(nidstr + dofstr + vadstr + lcidstr + sfstr + vidstr + deathstr + birthstr + "\n")

class KooBoundaryPZEPOT(KooBoundaryNode):
    def __init__(self, bid, nsid, lcid=0, sf=1.0):
        super(KooBoundaryPZEPOT,self).__init__(bid,"PZEPOT" + str(bid))
        self.btype = "PZEPOT"
        self.nsid = nsid
        self.lcid = lcid
        self.sf = sf
        
    def SetNodeSetID(self, nsid):
        self.nsid = nsid
    
    def SetLCID(self, lcid):
        self.lcid = lcid
    
    def SetScaleFactor(self, sf):
        self.sf = sf
    
    
    def WritetoNastranKeyword(self, startID):
        curStr = ""
        return curStr
    
    def WritetoDynaKeyword(self, startID):
        keywords = "*BOUNDARY_PZEPOT\n"
        
        idStr = format(self.bid + startID, ">10")
        nsidStr = format(self.nsid, ">10")  
        lcidStr = format(self.lcid, ">10")
        sfStr = format(self.sf, ">10.3e")
        keywords += idStr + nsidStr + lcidStr + sfStr + "\n"
        return keywords
        

class KooBoundarySPCNode(KooBoundaryNode):
    def __init__(self, bid, node, name ="", cid = 0, dofx=0, dofy=0, dofz=0, dofrx=0, dofry=0, dofrz=0):
        if name == "":
            name = "SPCNode" + str(bid)
        super(KooBoundarySPCNode,self).__init__(bid,name)
        self.btype = "SPCNode"
        self.node = node
        self.cid = cid
        self.dofx = dofx
        self.dofy = dofy
        self.dofz = dofz
        self.dofrx = dofrx
        self.dofry = dofry
        self.dofrz = dofrz
    
    def SetNode(self, node):
        self.node = node
    
    def SetCoordinate(self, cid):
        self.cid = cid
    
    def SetDOF(self, dofx=0, dofy=0, dofz=0, dofrx=0, dofry=0, dofrz=0):
        self.dofx = dofx
        self.dofy = dofy
        self.dofz = dofz
        self.dofrx = dofrx
        self.dofry = dofry
        self.dofrz = dofrz
    
    def WritetoNastranKeyword(self, startID):
        dofStr = ""
        if self.dofx == 1:
            dofStr += "1"
        if self.dofy == 1:
            dofStr += "2"
        if self.dofz == 1:
            dofStr += "3"
        if self.dofrx == 1:
            dofStr += "4"
        if self.dofry == 1:
            dofStr += "5"
        if self.dofrz == 1:
            dofStr += "6"
        bid = self.bid + startID
        bidStr = format(bid, ">8")
        dofStr = format(dofStr, ">8")
        keywords = ""
        keywords += "SPC1    "
        keywords += bidStr  
        keywords += dofStr
        nodestr = format(self.node.id,">8")
        keywords += nodestr
        keywords += "\n"
        return keywords
    
    def WritetoDynaKeyword(self, startID):
        keywords = "*BOUNDARY_SPC_NODE_ID\n"
        #id string for 10 digit
        idStr = format(self.bid + startID, ">10")
        nameStr = self.name
        nameStr = format(nameStr, ">70")
        keywords += idStr + nameStr + "\n"
        
        nidStr = format(self.node.id, ">10")
        cidStr = format(self.cid, ">10")
        dofxStr = format(self.dofx, ">10")
        dofyStr = format(self.dofy, ">10")
        dofzStr = format(self.dofz, ">10")
        dofrxStr = format(self.dofrx, ">10")
        dofryStr = format(self.dofry, ">10")
        dofrzStr = format(self.dofrz, ">10")
        keywords += nidStr + cidStr + dofxStr + dofyStr + dofzStr + dofrxStr + dofryStr + dofrzStr + "\n"
        return keywords
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*BOUNDARY_SPC_NODE_ID\n")
        #id string for 10 digit
        idStr = format(self.bid + startID, ">10")
        nameStr = self.name
        nameStr = format(nameStr, ">70")
        stream.write(idStr + nameStr + "\n")
        
        nidStr = format(self.node.id, ">10")
        cidStr = format(self.cid, ">10")
        dofxStr = format(self.dofx, ">10")
        dofyStr = format(self.dofy, ">10")
        dofzStr = format(self.dofz, ">10")
        dofrxStr = format(self.dofrx, ">10")
        dofryStr = format(self.dofry, ">10")
        dofrzStr = format(self.dofrz, ">10")
        stream.write(nidStr + cidStr + dofxStr + dofyStr + dofzStr + dofrxStr + dofryStr + dofrzStr + "\n")   
    
class KooBoundarySPCNodes(KooBoundaryNode):
    def __init__(self, bid, name = "", nodes = [], cids = [], dofxs = [], dofys = [], dofzs = [], dofrxs = [], dofrys = [], dofrzs = []):
        if name == "":
            name = "SPCNode" + str(bid)
        super(KooBoundarySPCNodes,self).__init__(bid,name)
        self.btype = "SPCNode"
        self.nodes = nodes
        self.cids = cids
        self.dofxs = dofxs
        self.dofys = dofys
        self.dofzs = dofzs
        self.dofrxs = dofrxs
        self.dofrys = dofrys
        self.dofrzs = dofrzs
    
    def AddNode(self, node):
        self.nodes.append(node)        
    
    def AddCoordinate(self, cid):
        self.cids.append(cid)  
    
    def AddDOF(self, dofx=0, dofy=0, dofz=0, dofrx=0, dofry=0, dofrz=0):
        self.dofxs.append(dofx)
        self.dofys.append(dofy)
        self.dofzs.append(dofz)
        self.dofrxs.append(dofrx)        
        self.dofrys.append(dofry)
        self.dofrzs.append(dofrz)
    
    def WritetoNastranKeyword(self, startID):
        for i in range(len(self.nodes)):
            dofStr = ""
            if self.dofxs[i] == 1:
                dofStr += "1"
            if self.dofys[i] == 1:
                dofStr += "2"
            if self.dofzs[i] == 1:
                dofStr += "3"
            if self.dofrxs[i] == 1:
                dofStr += "4"
            if self.dofrys[i] == 1:
                dofStr += "5"
            if self.dofrzs[i] == 1:
                dofStr += "6"            
            keywords = ""
            keywords += "SPC1    "
            bidStr = format(self.bid, ">8")
            keywords += bidStr  
            keywords += dofStr
            nodestr = format(self.nodes[i].id + startID,">8")
            keywords += nodestr
            keywords += "\n"
        return keywords
    
    def WritetoDynaKeyword(self, startID):
        keywords = "*BOUNDARY_SPC_NODE\n"
        #id string for 10 digit
        for i in range(len(self.nodes)):
            nidStr = format(self.nodes[i].id, ">10")
            cidStr = format(self.cids[i], ">10")
            dofxStr = format(self.dofxs[i], ">10")
            dofyStr = format(self.dofys[i], ">10")
            dofzStr = format(self.dofzs[i], ">10")
            dofrxStr = format(self.dofrxs[i], ">10")
            dofryStr = format(self.dofrys[i], ">10")
            dofrzStr = format(self.dofrzs[i], ">10")
            keywords += nidStr + cidStr + dofxStr + dofyStr + dofzStr + dofrxStr + dofryStr + dofrzStr + "\n"
        return keywords
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*BOUNDARY_SPC_NODE\n")
        #id string for 10 digit
        for i in range(len(self.nodes)):
            nidStr = format(self.nodes[i].id, ">10")
            cidStr = format(self.cids[i], ">10")
            dofxStr = format(self.dofxs[i], ">10")
            dofyStr = format(self.dofys[i], ">10")
            dofzStr = format(self.dofzs[i], ">10")
            dofrxStr = format(self.dofrxs[i], ">10")
            dofryStr = format(self.dofrys[i], ">10")
            dofrzStr = format(self.dofrzs[i], ">10")
            stream.write(nidStr + cidStr + dofxStr + dofyStr + dofzStr + dofrxStr + dofryStr + dofrzStr + "\n")
            
class KooBoundarySPCNodeSet(KooBoundaryNode):
    def __init__(self, bid, nset, name ="" , cid = 0, dofx=0, dofy=0, dofz=0, dofrx=0, dofry=0, dofrz=0):            
        if name == "":
            name = "SPCNodeSet" + str(bid)
        super(KooBoundarySPCNodeSet,self).__init__(bid,name)
        self.btype = "SPCNodeSet"
        self.nset = nset
        self.cid = cid
        self.dofx = dofx
        self.dofy = dofy
        self.dofz = dofz
        self.dofrx = dofrx
        self.dofry = dofry
        self.dofrz = dofrz
        
    def SetNodeSet(self, nset):
        self.nset = nset

    def SetCoordinate(self, cid):
        self.cid = cid
        
    def SetDOF(self, dofx=0, dofy=0, dofz=0, dofrx=0, dofry=0, dofrz=0):
        self.dofx = dofx
        self.dofy = dofy
        self.dofz = dofz
        self.dofrx = dofrx
        self.dofry = dofry
        self.dofrz = dofrz
        
    def WritetoNastranKeyword(self, startID):
        dofStr = ""
        if self.dofx == 1:
            dofStr += "1"
        if self.dofy == 1:
            dofStr += "2"
        if self.dofz == 1:
            dofStr += "3"
        if self.dofrx == 1:
            dofStr += "4"
        if self.dofry == 1:
            dofStr += "5"
        if self.dofrz == 1:
            dofStr += "6"
        dofStr = format(dofStr, ">8")
        bid = self.bid + startID
        bidStr = format(bid, ">8")
        keywords = ""
        for node in self.nset.nodes:
            keywords += "SPC1    "
            keywords += bidStr  
            keywords += dofStr
            nodestr = format(node,">8")
            keywords += nodestr
            keywords += "\n"
        return keywords
        
    def WritetoDynaKeyword(self, startID):
        keywords = "*BOUNDARY_SPC_SET_ID\n"
        #id string for 10 digit
        idStr = format(self.bid + startID, ">10")
        nameStr = format(self.name, ">70")
        keywords += idStr + nameStr + "\n"
        
        nidStr = format(self.nset.sid, ">10")
        cidStr = format(self.cid, ">10")
        dofxStr = format(self.dofx, ">10")
        dofyStr = format(self.dofy, ">10")
        dofzStr = format(self.dofz, ">10")
        dofrxStr = format(self.dofrx, ">10")
        dofryStr = format(self.dofry, ">10")
        dofrzStr = format(self.dofrz, ">10")
        keywords += nidStr + cidStr + dofxStr + dofyStr + dofzStr + dofrxStr + dofryStr + dofrzStr + "\n"
        return keywords
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*BOUNDARY_SPC_SET_ID\n")
        #id string for 10 digit
        idStr = format(self.bid + startID, ">10")
        nameStr = format(self.name, ">70")
        stream.write(idStr + nameStr + "\n")
        
        nidStr = format(self.nset.sid, ">10")
        cidStr = format(self.cid, ">10")
        dofxStr = format(self.dofx, ">10")
        dofyStr = format(self.dofy, ">10")
        dofzStr = format(self.dofz, ">10")
        dofrxStr = format(self.dofrx, ">10")
        dofryStr = format(self.dofry, ">10")
        dofrzStr = format(self.dofrz, ">10")
        stream.write(nidStr + cidStr + dofxStr + dofyStr + dofzStr + dofrxStr + dofryStr + dofrzStr + "\n")                                    

class KooBoundaryNodeManager:
    def __init__(self):
        self.maxid = 0 
        self.boundaries = {}        

    def OffsetID(self, offsetID):
        for key in self.boundaries:
            boundary = self.boundaries[key]
            boundary.id += offsetID

    def OverwritefromBoundaryNodeManager(self, boundaryNodeManager : KooBoundaryNodeManager):
        self.maxid = max(self.maxid, boundaryNodeManager.maxid)
        for key, value in boundaryNodeManager.boundaries.items():
            self.boundaries[key] = value

    def parse_whole(self, curString, chunkList):
        chunk_size = len(chunkList)
        chunks = []

        start = 0
        for i in range(0,chunk_size):
            end = start + chunkList[i]
            chunks.append(curString[start:end])            
            start = end

        for i in range(0,chunk_size):
            if '\n' in chunks[i]:
                chunks[i] = chunks[i].replace('\n','')
            
        return chunks 
    
    def CreatePZEPOT(self, nsid, lcid=0, sf=1.0):
        self.maxid += 1
        boundary = KooBoundaryPZEPOT(self.maxid, nsid, lcid, sf)
        self.AddBoundary(boundary)
        return boundary
    
    def CreateBoundarySPCNode(self,node,cid=0,dofx=0,dofy=0,dofz=0,dofrx=0,dofry=0,dofrz=0,name=""):
        self.maxid += 1
        boundary = KooBoundarySPCNode(self.maxid,node,name,cid,dofx,dofy,dofz,dofrx,dofry,dofrz)
        self.AddBoundary(boundary)
        return boundary

    def CreateBoundarySPCNodes(self, nodes=[], cids=[], dofxs=[], dofys=[], dofzs=[], dofrxs=[], dofrys=[], dofrzs=[], name=""):
        self.maxid += 1
        boundary = KooBoundarySPCNodes(self.maxid,name,nodes,cids,dofxs,dofys,dofzs,dofrxs,dofrys,dofrzs)
        self.AddBoundary(boundary)
        return boundary

    def CreateBoundarySPCNodeSet(self,nset,cid=0,dofx=0,dofy=0,dofz=0,dofrx=0,dofry=0,dofrz=0,name=""):
        self.maxid += 1
        boundary = KooBoundarySPCNodeSet(self.maxid,nset,name,cid,dofx,dofy,dofz,dofrx,dofry,dofrz)
        self.AddBoundary(boundary)
        return boundary
    
    def CreateBoundarySPCNodeSetwithID(self, bid, name, nset, cid=0, dofx=0, dofy=0, dofz=0, dofrx=0, dofry=0, dofrz=0):
        boundary = KooBoundarySPCNodeSet(bid,nset,name,cid,dofx,dofy,dofz,dofrx,dofry,dofrz)
        self.AddBoundary(boundary)
        return boundary

    def CreateBoundaryPrescribedMotionNode(self, name, node, dof, vad = 0, lcid = None, sf = 1.0, vid = 0, death = 1.0E28, birth = 0.0):
        self.maxid += 1
        boundary = KooBoundaryPrescribedMotionNode(self.maxid,name,node,dof,vad,lcid,sf,vid,death,birth)
        self.AddBoundary(boundary)
        return boundary

    def CreateBoundaryPrescribedMotionNodes(self,node=[],dof=[],vad=[],lcid=[],sf=[],vid=[],death=[],birth=[],name=""):
        self.maxid += 1
        boundary = KooBoundaryPrescribedMotionNodes(self.maxid,name,node,dof,vad,lcid,sf,vid,death,birth)
        self.AddBoundary(boundary)
        return boundary
    
    def CreateBoundaryPrescribedMotionNodewithID(self, bid, name, node, dof, vad=0, lcid=None, sf=1.0, vid=0, death=1.0E28, birth=0.0):
        boundary = KooBoundaryPrescribedMotionNode(bid,name,node,dof,vad,lcid,sf,vid,death,birth)
        self.AddBoundary(boundary)
        return boundary
    
    def CreateBoundaryPrescribedMotionRigid(self, node, dof, vad=0, lcid=None, sf=1.0, vid=0, death=1.0E28, birth=0.0, name=""):
        self.maxid += 1
        boundary = KooBoundaryPrescribedMotionRigid(self.maxid,name,node,dof,vad,lcid,sf,vid,death,birth)
        self.AddBoundary(boundary)
        return boundary
    
    def CreateBoundaryPrescribedMotionRigidwithID(self, bid, name, node, dof, vad=0, lcid=None, sf=1.0, vid=0, death=1.0E28, birth=0.0):
        boundary = KooBoundaryPrescribedMotionRigid(bid,name,node,dof,vad,lcid,sf,vid,death,birth)
        self.AddBoundary(boundary)
        return boundary
    

    def AddBoundary(self, boundary):                
        self.boundaries[boundary.bid] = boundary
        if boundary.bid > self.maxid:
            self.maxid = boundary.bid          
        return boundary

    def RemoveBoundary(self, bid):
        boundary = self.boundaries[bid]                        
        del self.boundaries[bid]
    
    def RemoveBoundaryfromNodeSetIDList(self, nsids):
        delboundaryList =[]
        for nsid in nsids:
            for bid, boundary in self.boundaries.items():
                if type(boundary) == KooBoundarySPCNodeSet and boundary.nset.sid == nsid:                
                    delboundaryList.append(bid)
        for bid in delboundaryList:
            self.RemoveBoundary(bid)

    def RemoveAll(self):
        self.maxid = 0 
        self.boundaries = {}
    
    def AddBoundaryNodefromDyna(self, dynaBoundaryNode, nodeManager, nodeSetManager):
        # 공통 헬퍼: 라인 구조 유효성 + 안전 파싱
        def _line_valid(line, min_len=1):
            if line is None:
                return False
            if not isinstance(line, (list, tuple)):
                return False
            if len(line) < min_len:
                return False
            # 완전 빈 라인(모든 필드가 공백/None)은 무효
            return any((f is not None and str(f).strip() != "") for f in line)

        def _fget(line, idx, default=""):
            if line is None or idx >= len(line):
                return default
            v = line[idx]
            return v if v is not None else default

        def _ki(line, idx, default=0):
            return KooDynaInt(str(_fget(line, idx, "")), default)

        def _kf(line, idx, default=0.0):
            return KooDynaFloat(str(_fget(line, idx, "")), default)

        def _get_node_or_none(nid):
            if nid in nodeManager.nodes:
                return nodeManager.nodes[nid]
            if nid != 0:
                print(f"[WARNING] BOUNDARY 참조 노드 미발견 nid={nid} — 스킵")
            return None

        def _get_nset_or_none(nsid):
            if nsid in nodeSetManager.nodeSets:
                return nodeSetManager.nodeSets[nsid]
            if nsid != 0:
                print(f"[WARNING] BOUNDARY 참조 노드셋 미발견 nsid={nsid} — 스킵")
            return None

        # dynaBoundaryNode 자체가 비어있거나 헤더 없는 경우 방어
        if not dynaBoundaryNode or len(dynaBoundaryNode) == 0:
            return
        header = dynaBoundaryNode[0]

        if header == "*BOUNDARY_PZEPOT":
            for i in range(1, len(dynaBoundaryNode)):
                parameters = dynaBoundaryNode[i]
                if not _line_valid(parameters, min_len=4):
                    continue
                bid = _ki(parameters, 0)
                nsid = _ki(parameters, 1)
                lcid = _ki(parameters, 2)
                sf = _kf(parameters, 3)
                boundary = KooBoundaryPZEPOT(bid,nsid,lcid,sf)
                self.AddBoundary(boundary)

        elif header == "*BOUNDARY_SPC_NODE":
            boundary = self.CreateBoundarySPCNodes()
            for i in range(1,len(dynaBoundaryNode)):
                dynaBoundary = dynaBoundaryNode[i]
                if not _line_valid(dynaBoundary, min_len=1):
                    continue
                nid = _ki(dynaBoundary, 0)
                if nid == 0:
                    continue
                cid = _ki(dynaBoundary, 1)
                dofx = _ki(dynaBoundary, 2)
                dofy = _ki(dynaBoundary, 3)
                dofz = _ki(dynaBoundary, 4)
                dofrx = _ki(dynaBoundary, 5)
                dofry = _ki(dynaBoundary, 6)
                dofrz = _ki(dynaBoundary, 7)
                node = _get_node_or_none(nid)
                if node is None:
                    continue
                boundary.AddNode(node)
                boundary.AddCoordinate(cid)
                boundary.AddDOF(dofx,dofy,dofz,dofrx,dofry,dofrz)

        elif header == "*BOUNDARY_SPC_NODE_ID":
            if len(dynaBoundaryNode) < 3:
                return
            parameters = dynaBoundaryNode[1]
            if not _line_valid(parameters, min_len=1):
                return
            id_ = _ki(parameters, 0)
            name = _fget(parameters, 1, "SPC_NODE_ID")
            secondLine = dynaBoundaryNode[2]
            if not _line_valid(secondLine, min_len=1):
                return
            nid = _ki(secondLine, 0)
            if nid == 0:
                return
            cid = _ki(secondLine, 1)
            dofx = _ki(secondLine, 2)
            dofy = _ki(secondLine, 3)
            dofz = _ki(secondLine, 4)
            dofrx = _ki(secondLine, 5)
            dofry = _ki(secondLine, 6)
            dofrz = _ki(secondLine, 7)
            node = _get_node_or_none(nid)
            if node is None:
                return
            self.CreateBoundarySPCNode(node,cid,dofx,dofy,dofz,dofrx,dofry,dofrz,name)

        elif header == "*BOUNDARY_SPC_SET":
            if len(dynaBoundaryNode) < 2:
                return
            firstLine = dynaBoundaryNode[1]
            if not _line_valid(firstLine, min_len=1):
                return
            nsid = _ki(firstLine, 0)
            cid = _ki(firstLine, 1)
            dofx = _ki(firstLine, 2)
            dofy = _ki(firstLine, 3)
            dofz = _ki(firstLine, 4)
            dofrx = _ki(firstLine, 5)
            dofry = _ki(firstLine, 6)
            dofrz = _ki(firstLine, 7)
            nset = _get_nset_or_none(nsid)
            if nset is None:
                return
            self.CreateBoundarySPCNodeSet(nset,cid,dofx,dofy,dofz,dofrx,dofry,dofrz)

        elif header == "*BOUNDARY_SPC_SET_ID":
            if len(dynaBoundaryNode) < 3:
                return
            parameters = dynaBoundaryNode[1]
            if not _line_valid(parameters, min_len=1):
                return
            bid = _ki(parameters, 0)
            name = _fget(parameters, 1, "SPC_SET_ID")
            secondLine = dynaBoundaryNode[2]
            if not _line_valid(secondLine, min_len=1):
                return
            nsid = _ki(secondLine, 0)
            cid = _ki(secondLine, 1)
            dofx = _ki(secondLine, 2)
            dofy = _ki(secondLine, 3)
            dofz = _ki(secondLine, 4)
            dofrx = _ki(secondLine, 5)
            dofry = _ki(secondLine, 6)
            dofrz = _ki(secondLine, 7)
            nset = _get_nset_or_none(nsid)
            if nset is None:
                return
            self.CreateBoundarySPCNodeSetwithID(bid,name,nset,cid,dofx,dofy,dofz,dofrx,dofry,dofrz)

        elif header == "*BOUNDARY_PRESCRIBED_MOTION_NODE":
            boundary = self.CreateBoundaryPrescribedMotionNode()
            # 이전 코드는 [2:]부터 순회해서 [1]을 놓치는 구조였음 — [1:]로 통일
            for i in range(1, len(dynaBoundaryNode)):
                firstLine = dynaBoundaryNode[i]
                if not _line_valid(firstLine, min_len=1):
                    continue
                typeid = _ki(firstLine, 0)
                if typeid == 0:
                    continue
                dof = _ki(firstLine, 1)
                vad = _ki(firstLine, 2)
                lcid = _ki(firstLine, 3)
                sf = _kf(firstLine, 4, 1.0)
                vid = _ki(firstLine, 5)
                death = _kf(firstLine, 6, 1.0E28)
                birth = _kf(firstLine, 7, 0.0)
                node = _get_node_or_none(typeid)
                if node is None:
                    continue
                boundary.AddNode(node)
                boundary.AddDOF(dof)
                boundary.AddVAD(vad)
                boundary.AddLCID(lcid)
                boundary.AddScaleFactor(sf)
                boundary.AddVID(vid)
                boundary.AddDeath(death)
                boundary.AddBirth(birth)

        elif header == "*BOUNDARY_PRESCRIBED_MOTION_NODE_ID":
            if len(dynaBoundaryNode) < 3:
                return
            firstLine = dynaBoundaryNode[1]
            if not _line_valid(firstLine, min_len=1):
                return
            bid = _ki(firstLine, 0)
            name = _fget(firstLine, 1, "PMNODE_ID")
            secondLine = dynaBoundaryNode[2]
            if not _line_valid(secondLine, min_len=1):
                return
            typeid = _ki(secondLine, 0)
            if typeid == 0:
                return
            dof = _ki(secondLine, 1)
            vad = _ki(secondLine, 2)
            lcid = _ki(secondLine, 3)
            sf = _kf(secondLine, 4, 1.0)
            vid = _ki(secondLine, 5)
            death = _kf(secondLine, 6, 1.0E28)
            birth = _kf(secondLine, 7, 0.0)
            node = _get_node_or_none(typeid)
            if node is None:
                return
            self.CreateBoundaryPrescribedMotionNodewithID(bid,name,node,dof,vad,lcid,sf,vid,death,birth)

        elif header == "*BOUNDARY_PRESCRIBED_MOTION_RIGID":
            if len(dynaBoundaryNode) < 2:
                return
            firstLine = dynaBoundaryNode[1]
            if not _line_valid(firstLine, min_len=1):
                return
            typeid = _ki(firstLine, 0)
            if typeid == 0:
                return
            dof = _ki(firstLine, 1)
            vad = _ki(firstLine, 2)
            lcid = _ki(firstLine, 3)
            sf = _kf(firstLine, 4, 1.0)
            vid = _ki(firstLine, 5)
            death = _kf(firstLine, 6, 1.0E28)
            birth = _kf(firstLine, 7, 0.0)
            node = _get_node_or_none(typeid)
            if node is None:
                return
            name = "PrescribedMotionNode" + str(typeid)
            self.CreateBoundaryPrescribedMotionRigid(node,dof,vad,lcid,sf,vid,death,birth,name)

        elif header == "*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID":
            if len(dynaBoundaryNode) < 3:
                return
            firstLine = dynaBoundaryNode[1]
            if not _line_valid(firstLine, min_len=1):
                return
            bid = _ki(firstLine, 0)
            name = _fget(firstLine, 1, "PMRIGID_ID")
            secondLine = dynaBoundaryNode[2]
            if not _line_valid(secondLine, min_len=1):
                return
            typeid = _ki(secondLine, 0)
            if typeid == 0:
                return
            dof = _ki(secondLine, 1)
            vad = _ki(secondLine, 2)
            lcid = _ki(secondLine, 3)
            sf = _kf(secondLine, 4, 1.0)
            vid = _ki(secondLine, 5)
            death = _kf(secondLine, 6, 1.0E28)
            birth = _kf(secondLine, 7, 0.0)
            node = _get_node_or_none(typeid)
            if node is None:
                return
            self.CreateBoundaryPrescribedMotionRigidwithID(bid,name,node,dof,vad,lcid,sf,vid,death,birth)
                
    
    def WritetoNastranKeyword(self, startID):
        keywords = ""
        for bid in self.boundaries:
            keywords += self.boundaries[bid].WritetoNastranKeyword(startID)
        return keywords
        
    def WritetoDynaKeyword(self, startID):
        keywords = ""
        for bid in self.boundaries:
            keywords += self.boundaries[bid].WritetoDynaKeyword(startID)
        return keywords
    
    def WriteStreamDynaKeyword(self, stream, startID):
        for bid in self.boundaries:
            self.boundaries[bid].WriteStreamDynaKeyword(stream, startID)
