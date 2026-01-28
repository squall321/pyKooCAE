from __future__ import annotations
import math
import numpy as np

from KooCAEManager.KooOperator import KooDynaFloat, KooDynaInt, KooDynaString
    
class KooLoadBody:
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        self.lcid = lcid
        self.sf = sf
        self.lciddr = lciddr
        self.xc = xc
        self.yc = yc
        self.zc = zc
        self.cid = cid
    
    def WritetoDynaKeyword(self):
        keyword = ""
        keyword += format(self.lcid, ">10")
        keyword += format(self.sf, ">10.3f")
        if self.lciddr == "":
            keyword += "          "
        else:
            keyword += format(self.lciddr, ">10")
        keyword += format(self.xc, ">10.3f")
        keyword += format(self.yc, ">10.3f")
        keyword += format(self.zc, ">10.3f")
        keyword += format(self.cid, ">10")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write(format(self.lcid, ">10"))
        stream.write(format(self.sf, ">10.3f"))
        if self.lciddr == "":
            stream.write("          ")
        else:
            stream.write(format(self.lciddr, ">10"))
        stream.write(format(self.xc, ">10.3f"))
        stream.write(format(self.yc, ">10.3f"))
        stream.write(format(self.zc, ">10.3f"))
        stream.write(format(self.cid, ">10"))
        stream.write("\n")
            
class KooLoadBodyX(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyX,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_X\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_X\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyY(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyY,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_Y\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_Y\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyZ(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyZ,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_Z\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_Z\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyRX(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyRX,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_RX\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_RX\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyRY(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyRY,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_RY\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_RY\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyRZ(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        super(KooLoadBodyRZ,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_RZ\n"
        keyword += super().WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_RZ\n")
        super().WriteStreamDynaKeyword(stream)

class KooLoadBodyVector(KooLoadBody):
    def __init__(self, lcid, sf =1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0, fx = 0.0, fy = 0.0, fz = 0.0): 
        super(KooLoadBodyVector,self).__init__(lcid, sf, lciddr, xc, yc, zc, cid)
        self.fx = fx
        self.fy = fy
        self.fz = fz
    
    def WritetoDynaKeyword(self):
        keyword = "*LOAD_BODY_VECTOR\n"
        keyword += super().WritetoDynaKeyword()
        keyword += format(self.fx, ">10.3f")
        keyword += format(self.fy, ">10.3f")
        keyword += format(self.fz, ">10.3f")
        keyword += "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream):
        stream.write("*LOAD_BODY_VECTOR\n")
        super().WriteStreamDynaKeyword(stream)
        stream.write(format(self.fx, ">10.3f"))
        stream.write(format(self.fy, ">10.3f"))
        stream.write(format(self.fz, ">10.3f"))
        stream.write("\n")
    
class KooLoad:
    def __init__(self,lid, name):
         self.lid = lid
         self.name = name
         self.ltype = None
    
    def WritetoNastranKeyword(self, startID,loadcaseID=1):
        return ""     
    
    def WritetoDynaKeyword(self, startID):
        return ""

    def WriteStreamDynaKeyword(self, stream, startID):
        return ""
    
class KooLoadNodalPoint(KooLoad):
    def __init__(self, lid, name,lcid=None,cid = 0, fx = 0.0, fy = 0.0, fz = 0.0, node = 0):
        super(KooLoadNodalPoint,self).__init__(lid, name)
        self.ltype = "LOAD_NODE_POINT"
        self.lcid = lcid
        self.cid = cid
        self.fx = fx
        self.fy = fy
        self.fz = fz
        self.m1 = 0
        self.m2 = 0
        self.m3 = 0
        self.node = node
    
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        
        keyword += "*LOAD_NODE_POINT\n"
        keyword += "$#     nid       dof      lcid        sf       cid        m1        m2        m3\n"
        if self.fx != 0.0:
            keyword += format(self.node + startID, ">10")
            keyword += "         1"
            keyword += format(self.lcid, ">10")
            keyword += format(self.fx, ">10.3f")
            keyword += format(self.cid, ">10")
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                keyword += format(self.m1, ">10")
                keyword += format(self.m2, ">10")
                keyword += format(self.m3, ">10")
            keyword += "\n"
        if self.fy != 0.0:
            keyword += format(self.node + startID, ">10")
            keyword += "         2"
            keyword += format(self.lcid, ">10")
            keyword += format(self.fy, ">10.3f")
            keyword += format(self.cid, ">10")
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                keyword += format(self.m1, ">10")
                keyword += format(self.m2, ">10")
                keyword += format(self.m3, ">10")
            keyword += "\n"
        if self.fz != 0.0:
            keyword += format(self.node + startID, ">10")
            keyword += "         3"
            keyword += format(self.lcid, ">10")
            keyword += format(self.fz, ">10.3f")
            keyword += format(self.cid, ">10")
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                keyword += format(self.m1, ">10")
                keyword += format(self.m2, ">10")
                keyword += format(self.m3, ">10")
            keyword += "\n"
            
        
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*LOAD_NODE_POINT\n")
        stream.write("$#     nid       dof      lcid        sf       cid        m1        m2        m3\n")
        if self.fx != 0.0:
            stream.write(format(self.node + startID, ">10"))
            stream.write("         1")
            stream.write(format(self.lcid, ">10"))
            stream.write(format(self.fx, ">10.3f"))
            stream.write(format(self.cid, ">10"))
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                stream.write(format(self.m1, ">10"))
                stream.write(format(self.m2, ">10"))
                stream.write(format(self.m3, ">10"))
            stream.write("\n")
        if self.fy != 0.0:
            stream.write(format(self.node + startID, ">10"))
            stream.write("         2")
            stream.write(format(self.lcid, ">10"))
            stream.write(format(self.fy, ">10.3f"))
            stream.write(format(self.cid, ">10"))
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                stream.write(format(self.m1, ">10"))
                stream.write(format(self.m2, ">10"))
                stream.write(format(self.m3, ">10"))
            stream.write("\n")
        if self.fz != 0.0:
            stream.write(format(self.node + startID, ">10"))
            stream.write("         3")
            stream.write(format(self.lcid, ">10"))
            stream.write(format(self.fz, ">10.3f"))
            stream.write(format(self.cid, ">10"))
            if self.m1 != 0 or self.m2 != 0 or self.m3 != 0:
                stream.write(format(self.m1, ">10"))
                stream.write(format(self.m2, ">10"))
                stream.write(format(self.m3, ">10"))
            stream.write("\n")
    
    def WritetoNastranKeyword(self, startID, loadcaseID=1):
        return super().WritetoNastranKeyword(startID, loadcaseID) 
    
class KooLoadNodes(KooLoad):
    def __init__(self, lid, name, lcid = None,cid = 0, fx = 0.0, fy = 0.0, fz = 0.0, boundaries = [], nodeManager = None):
        super(KooLoadNodes,self).__init__(lid, name)
        self.ltype = "LOAD_NODES"
        self.lcid = lcid
        self.cid = cid
        self.fx = fx
        self.fy = fy
        self.fz = fz
        self.boundaries = boundaries
        self.nodeManager = nodeManager
        
        self.TransfertoNodalForce()
        
    def OffsetID(self, offsetNID):
        for boundary in self.boundaries:
            for i in range(len(boundary)):
                boundary[i] += offsetNID
    
    def calculate_tri_area(self,n1, n2, n3):
        # Calculate the area of the triangle
        area = 0.5 * np.linalg.norm(np.cross([n2.x - n1.x, n2.y - n1.y, n2.z - n1.z], [n3.x - n1.x, n3.y - n1.y, n3.z - n1.z]))
    
        return area
    
    def calculate_quad_area(self,n1, n2, n3, n4):
        # Calculate the diagonal vectors
        d1 = np.array([n3.x - n1.x, n3.y - n1.y, n3.z - n1.z])
        d2 = np.array([n4.x - n2.x, n4.y - n2.y, n4.z - n2.z])
    
        # Calculate the cross product of the two diagonal vectors
        cross_product = np.cross(d1, d2)
        
        # Calculate the area of the quadrilateral
        area = 0.5 * np.linalg.norm(cross_product)
    
        return area
  
    def TransfertoNodalForce(self):
        areaList = [] 
        nidtoForceRatio = {}
        totArea = 0.0
        self.nidList = []
        self.fxList = []
        self.fyList = []
        self.fzList = []
        
        for segment in self.boundaries:
            if len(segment) == 3:
                n1 = self.nodeManager.nodes[segment[0]]
                n2 = self.nodeManager.nodes[segment[1]]
                n3 = self.nodeManager.nodes[segment[2]]
                if segment[0] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[0]] = 0.0
                if segment[1] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[1]] = 0.0
                if segment[2] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[2]] = 0.0
                    
                area = self.calculate_tri_area(n1, n2, n3)
                if area < 0:
                    area = -area
                areaList.append(area)
                nidtoForceRatio[segment[0]] += area
                nidtoForceRatio[segment[1]] += area
                nidtoForceRatio[segment[2]] += area
                
                totArea += area
            elif len(segment) == 4:
                n1 = self.nodeManager.nodes[segment[0]]
                n2 = self.nodeManager.nodes[segment[1]]
                n3 = self.nodeManager.nodes[segment[2]]
                n4 = self.nodeManager.nodes[segment[3]]
                if segment[0] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[0]] = 0.0
                if segment[1] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[1]] = 0.0
                if segment[2] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[2]] = 0.0
                if segment[3] not in nidtoForceRatio.keys():
                    nidtoForceRatio[segment[3]] = 0.0
               
                area = self.calculate_quad_area(n1, n2, n3, n4)
                if area < 0:
                    area = -area
                nidtoForceRatio[segment[0]] += area
                nidtoForceRatio[segment[1]] += area
                nidtoForceRatio[segment[2]] += area
                nidtoForceRatio[segment[3]] += area
                
                areaList.append(area)
                totArea += area   
        for nid in nidtoForceRatio.keys():
            nidtoForceRatio[nid] = nidtoForceRatio[nid] / totArea
        
        for nid in nidtoForceRatio.keys():
            #n = self.nodeManager.nodes[nid]
            self.nidList.append(nid)
            self.fxList.append(self.fx * nidtoForceRatio[nid])
            self.fyList.append(self.fy * nidtoForceRatio[nid])
            self.fzList.append(self.fz * nidtoForceRatio[nid])
            
            
    def WritetoNastranKeyword(self, startID,loadcaseID=1):        
        keyword = ""
        for i in range(len(self.nidList)):
            keyword += "FORCE   "
            keyword += format(loadcaseID, ">8")
            keyword += format(self.nidList[i], ">8")
            keyword += format(self.cid, ">8")
            fx = self.fxList[i]
            fy = self.fyList[i]
            fz = self.fzList[i]

            amp = math.sqrt(fx*fx + fy*fy + fz*fz)
            ampStr = format(amp, ">8.2e")
            if amp>0:
                ampStr = " "    + ampStr
            if amp == 0.0:
                ampStr = " 0.0e+00"
            ampStr = ampStr.replace("e", "")
            fxStr = format(fx/amp, ">8.2e")
            if fx>0:
                fxStr = " "    + fxStr
            if fx == 0.0:
                fxStr = " 0.00e+00"
            fxStr = fxStr.replace("e", "")
            fyStr = format(fy/amp, ">8.2e")
            if fy>0:
                fyStr = " "    + fyStr
            if fy == 0.0:
                fyStr = " 0.00e+00"
            fyStr = fyStr.replace("e", "")
            fzStr = format(fz/amp, ">8.2e")
            if fz>0:
                fzStr = " "    + fzStr
            if fz == 0.0:
                fzStr = " 0.00e+00"
            fzStr = fzStr.replace("e", "")
            keyword += ampStr
            keyword += fxStr
            keyword += fyStr
            keyword += fzStr
            
            
            keyword += "\n"
                     
        return keyword
    
    def WritetoDynaKeyword(self, startID):        
        keyword = ""
        keyword += "*LOAD_NODE_POINT\n"
        keyword += "$#     nid       dof      lcid        sf       cid        m1        m2        m3\n"
        for i in range(len(self.nidList)):
            nidStr = format(self.nidList[i] + startID, ">10")
            lcidStr = format(self.lcid, ">10")
            fx =self.fxList[i]
            fy =self.fyList[i]
            fz =self.fzList[i]
            cidStr = format(self.cid, ">10")
            if fx != 0.0:                
                keyword += nidStr
                keyword += "         1"
                keyword += lcidStr
                keyword += format(fx, ">10.3e")
                keyword += cidStr
                # m1 m2 m3 for follower force
                keyword += "         0         0         0\n"
            if fy != 0.0:
                keyword += nidStr
                keyword += "         2"
                keyword += lcidStr
                keyword += format(fy, ">10.3e")
                keyword += cidStr
                # m1 m2 m3 for follower force
                keyword += "         0         0         0\n"
            if fz != 0.0:
                keyword += nidStr
                keyword += "         3"
                keyword += lcidStr
                keyword += format(fz, ">10.3e")
                keyword += cidStr                
                # m1 m2 m3 for follower force
                keyword += "         0         0         0\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        for i in range(len(self.nidList)):
            nidStr = format(self.nidList[i] + startID, ">10")
            lcidStr = format(self.lcid, ">10")
            fx =self.fxList[i]
            fy =self.fyList[i]
            fz =self.fzList[i]
            cidStr = format(self.cid, ">10")
            if fx != 0.0:
                stream.write("*LOAD_NODE_POINT\n")
                stream.write("$#     nid       dof      lcid        sf       cid        m1        m2        m3\n")
                stream.write(nidStr)
                stream.write("         1")
                stream.write(lcidStr)
                stream.write(format(fx, ">10.3e"))
                stream.write(cidStr)
                # m1 m2 m3 for follower force
                stream.write("         0         0         0\n")
            if fy != 0.0:
                stream.write("*LOAD_NODE_POINT\n")
                stream.write("$#     nid       dof      lcid        sf       cid        m1        m2        m3\n")
                stream.write(nidStr)
                stream.write("         2")
                stream.write(lcidStr)
                stream.write(format(fy, ">10.3e"))
                stream.write(cidStr)
                # m1 m2 m3 for follower force
                stream.write("         0         0         0\n")
            if fz != 0.0:
                stream.write("*LOAD_NODE_POINT\n")
                stream.write("$#     nid       dof      lcid        sf       cid        m1        m2        m3\n")
                stream.write(nidStr)
                stream.write("         3")
                stream.write(lcidStr)
                stream.write(format(fz, ">10.3e"))
                stream.write(cidStr)               
                # m1 m2 m3 for follower force
                stream.write("         0         0         0\n")
        
class KooLoadSegment(KooLoad):
    def __init__(self, lid, name,lcid=None,SF=1.0,AT=0.0,N1=None,N2=None,N3=None,N4=None,N5=None,N6=None,N7=None,N8=None):        
        super(KooLoadSegment,self).__init__(lid, name)
        self.ltype = "LOAD_SEGMENT_ID"
        self.lcid = lcid
        self.sf = SF
        self.at = AT
        self.n1 = N1
        self.n2 = N2
        self.n3 = N3
        self.n4 = N4
        self.n5 = N5
        self.n6 = N6
        self.n7 = N7
        self.n8 = N8
        
    def SetNodes(self, n1=None, n2=None, n3=None, n4=None, n5=None, n6=None, n7=None, n8=None):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4
        self.n5 = n5
        self.n6 = n6
        self.n7 = n7
        self.n8 = n8
        
    def WritetoNastranKeyword(self, startID,loadcaseID=1):
        keyword = "" 
        
        keyword += "PLOAD   "
        sfstr = format(self.sf, ">8.2e")
        sfstr = sfstr.replace("e", "")
        if self.sf>0:
            sfstr = " " + sfstr
        keyword += sfstr
        keyword += format(self.n1.id, ">8")
        keyword += format(self.n2.id, ">8")
        keyword += format(self.n3.id, ">8")
        if self.n4 is not None:
            if self.n4.id != self.n3.id:
                keyword += format(self.n4.id, ">8")
        keyword += "\n"
        return keyword
        
        
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        keyword += "*LOAD_SEGMENT_ID\n"
        idStr = format(self.lid + startID, ">10")
        lcidStr = format(self.lcid, ">10")
        sfStr = format(self.sf, ">10.3e")
        atStr = format(self.at, ">10.3e")
        
        keyword += idStr + lcidStr + sfStr + atStr
        if self.n1 is not None:            
            n1Str = format(self.n1, ">10")
            keyword += n1Str
        if self.n2 is not None:
            n2Str = format(self.n2, ">10")
            keyword += n2Str
        if self.n3 is not None:
            n3Str = format(self.n3, ">10")
            keyword += n3Str
        if self.n4 is not None:
            n4Str = format(self.n4, ">10")
            keyword += n4Str
        if self.n5 is not None:
            n5Str = format(self.n5, ">10")
            keyword += n5Str
        if self.n6 is not None:
            n6Str = format(self.n6, ">10")
            keyword += "\n" + n6Str
        if self.n7 is not None:
            n7Str = format(self.n7, ">10")
            keyword += n7Str
        if self.n8 is not None:
            n8Str = format(self.n8, ">10")
            keyword += n8Str + "\n"
        
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*LOAD_SEGMENT_ID\n")
        idStr = format(self.lid + startID, ">10")
        lcidStr = format(self.lcid, ">10")
        sfStr = format(self.sf, ">10.3e")
        atStr = format(self.at, ">10.3e")
        keyword = idStr + lcidStr + sfStr + atStr
        if self.n1 is not None:            
            n1Str = format(self.n1, ">10")
            keyword += n1Str
        if self.n2 is not None:
            n2Str = format(self.n2, ">10")
            keyword += n2Str
        if self.n3 is not None:
            n3Str = format(self.n3, ">10")
            keyword += n3Str
        if self.n4 is not None:
            n4Str = format(self.n4, ">10")
            keyword += n4Str
        if self.n5 is not None:
            n5Str = format(self.n5, ">10")
            keyword += n5Str
        if self.n6 is not None:
            n6Str = format(self.n6, ">10")
            keyword += "\n" + n6Str
        if self.n7 is not None:
            n7Str = format(self.n7, ">10")
            keyword += n7Str
        if self.n8 is not None:
            n8Str = format(self.n8, ">10")
            keyword += n8Str + "\n"
        stream.write(keyword)
            
    
class KooLoadSegmentSet(KooLoad):
    def __init__(self, lid, name, segmentSet = None, lcid = 0, sf= 0.0, at = 0.0):
        super(KooLoadSegmentSet,self).__init__(lid, name)
        self.ltype = "LOAD_SEGMENT_SET_ID"
        self.segmentSet = segmentSet
        self.lcid = lcid
        self.sf = sf
        self.at = at
        
    def AddSegmentSet(self, segmentSet, lcid, sf, at):
        self.segmentSet = segmentSet
        self.lcid = lcid
        self.sf = sf
        self.at = at     
           
    def WritetoNastranKeyword(self, startID,loadcaseID=1):
        keyword = ""
        segments = self.segmentSet.segments
        sfstr = format(self.sf, ">8.2e")
        sfstr = sfstr.replace("e", "")    
        if self.sf>0:
            sfstr = " " + sfstr
        for segment in segments:
            keyword += "PLOAD   "
            keyword += format(loadcaseID, ">8")
            keyword += sfstr
            if len(segment) >= 3:
                for i in range(3):
                    keyword += format(segment[i], ">8")
            if len(segment) >= 4:
                if segment[3] != segment[2]:
                    keyword += format(segment[3], ">8")
            keyword += "\n"            
        
        return keyword
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        keyword += "*LOAD_SEGMENT_SET_ID\n"
        idStr = format(self.lid + startID, ">10")
        nameStr = format(self.name, ">70")        
        keyword += "$#     ID                                                                  NAME\n"
        keyword += idStr + nameStr + "\n"
        keyword += "$#     SID      LCID        SF        AT\n"        
        
         
        sidStr = format(self.segmentSet.sid, ">10")
        lcidStr = format(self.lcid, ">10")
        sfStr = format(self.sf, ">10.3e")
        atStr = format(self.at, ">10.3e")
        keyword += sidStr + lcidStr + sfStr + atStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*LOAD_SEGMENT_SET_ID\n")
        idStr = format(self.lid + startID, ">10")
        nameStr = format(self.name, ">70")        
        keyword = "$#     ID                                                                  NAME\n"
        keyword += idStr + nameStr + "\n"
        keyword += "$#     SID      LCID        SF        AT\n"        
        
        sidStr = format(self.segmentSet.sid, ">10")
        lcidStr = format(self.lcid, ">10")
        sfStr = format(self.sf, ">10.3e")
        atStr = format(self.at, ">10.3e")
        keyword += sidStr + lcidStr + sfStr + atStr + "\n"
        stream.write(keyword)
        
class KooLoadManager:    
    def __init__(self):
        self.maxid = 0 
        self.loads = {}
        self.bodyLoads = []

    def OffsetID(self, offsetLCID, offsetNID):
        for key in self.loads:
            load = self.loads[key]
            load.lcid += offsetLCID
            if type(load) is KooLoadNodalPoint:
                load.node += offsetNID
            elif type(load) is KooLoadNodes:                
                load.OffsetID(offsetNID)

    def OverwritefromLoadManager(self, loadManager : KooLoadManager):
        self.maxid = max(self.maxid, loadManager.maxid)
        for key, value in loadManager.loads.items():
            self.loads[key] = value
        for bodyLoad in loadManager.bodyLoads:
            self.bodyLoads.append(bodyLoad)

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

    def CreateLoadBodyX(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyX(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyY(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyY(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyZ(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyZ(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyRX(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyRX(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyRY(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyRY(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyRZ(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0):
        load = KooLoadBodyRZ(lcid, sf, lciddr, xc, yc, zc, cid)
        self.bodyLoads.append(load)
        return load
    
    def CreateLoadBodyVector(self, lcid, sf = 1.0, lciddr = "", xc = 0.0, yc = 0.0, zc = 0.0, cid = 0, fx = 0.0, fy = 0.0, fz = 0.0):
        load = KooLoadBodyVector(lcid, sf, lciddr, xc, yc, zc, cid, fx, fy, fz)
        self.bodyLoads.append(load)
        return load    
    
    def CreateLoadNodalPoint(self, name, lcid=None, cid = 0, fx = 0.0, fy = 0.0, fz = 0.0, nodeid = 0):
        self.maxid += 1
        load = KooLoadNodalPoint(self.maxid,name,lcid,cid,fx,fy,fz,nodeid)
        self.loads[self.maxid] = load
        return load
        
    def CreateLoadNodes(self, name, lcid=None, cid = 0, fx = 0.0, fy = 0.0, fz = 0.0, boundaries = [], nodeManager = None):
        self.maxid += 1
        load = KooLoadNodes(self.maxid, name, lcid, cid, fx, fy, fz, boundaries, nodeManager) 
        self.loads[self.maxid] = load
        return load        
    
    def CreateLoadSegment(self, name, lcid=None, SF=1.0, AT=0.0, N1=None, N2=None, N3=None, N4=None, N5=None, N6=None, N7=None, N8=None):
        self.maxid += 1
        load = KooLoadSegment(self.maxid, name, lcid, SF, AT, N1, N2, N3, N4, N5, N6, N7, N8)
        self.loads[self.maxid] = load
        return load
    
    def CreateLoadSegmentwithID(self, lid, name, lcid=None, SF=1.0, AT=0.0, N1=None, N2=None, N3=None, N4=None, N5=None, N6=None, N7=None, N8=None):
        load = KooLoadSegment(lid, name, lcid, SF, AT, N1, N2, N3, N4, N5, N6, N7, N8)
        self.loads[lid] = load
        if lid > self.maxid:
            self.maxid = lid
        return load

    def CreateLoadSegmentSet(self, name, sid, lcid=None, SF=1.0, AT=0.0):
        self.maxid += 1
        load = KooLoadSegmentSet(self.maxid, name, sid, lcid, SF, AT)
        self.loads[self.maxid] = load
        return load

    def CreateLoadSegmentSetwithID(self, lid, name, sid = 0, lcid= 0, SF = 0.0, AT = 0.0):
        load = KooLoadSegmentSet(lid, name, sid, lcid, SF, AT)
        self.loads[lid] = load
        if lid > self.maxid:
            self.maxid = lid
        return load

    def AddLoad(self, load):
        self.load[load.lid] = load
        if load.lid > self.maxid:
            self.maxid = load.lid
        return load

    def RemoveLoadbyID(self, lid):
        del self.loads[lid]

    def RemoveLoad(self, load):
        del self.loads[load.lid]
    
    def RemoveAll(self):
        self.maxid = 0 
        self.loads = {}
        
    def WritetoNastranKeyword(self, startID,loadcaseID=1):
        keyword = ""
        for key in self.loads:
            keyword += self.loads[key].WritetoNastranKeyword(startID,loadcaseID)
        return keyword
    
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        for key in self.loads:
            keyword += self.loads[key].WritetoDynaKeyword(startID)
        for load in self.bodyLoads:
            keyword += load.WritetoDynaKeyword()
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        for key in self.loads:
            self.loads[key].WriteStreamDynaKeyword(stream, startID)
        for load in self.bodyLoads:
            load.WriteStreamDynaKeyword(stream)
    
    def AddLoadfromDyna(self, dynaLoad, nodeManager,nodeSetManager,segmentSetManager):
        if dynaLoad[0] == "*LOAD_BODY_X" or dynaLoad[0] == "*LOAD_BODY_Y" or dynaLoad[0] == "*LOAD_BODY_Z" or dynaLoad[0] == "*LOAD_BODY_RX" or dynaLoad[0] == "*LOAD_BODY_RY" or dynaLoad[0] == "*LOAD_BODY_RZ" or dynaLoad[0] == "*LOAD_BODY_VECTOR":
            parameters = dynaLoad[1]
            lcid = KooDynaInt(parameters[0])
            sf = KooDynaFloat(parameters[1])
            lciddr = KooDynaInt(parameters[2],"")
            xc = KooDynaFloat(parameters[3])
            yc = KooDynaFloat(parameters[4])
            zc = KooDynaFloat(parameters[5])
            cid = KooDynaInt(parameters[6])
            if dynaLoad[0] == "*LOAD_BODY_X":
                load = self.CreateLoadBodyX(lcid, sf, lciddr, xc, yc, zc, cid) 
            elif dynaLoad[0] == "*LOAD_BODY_Y":
                load = self.CreateLoadBodyY(lcid, sf, lciddr, xc, yc, zc, cid)
            elif dynaLoad[0] == "*LOAD_BODY_Z":
                load = self.CreateLoadBodyZ(lcid, sf, lciddr, xc, yc, zc, cid)
            elif dynaLoad[0] == "*LOAD_BODY_RX":
                load = self.CreateLoadBodyRX(lcid, sf, lciddr, xc, yc, zc, cid)
            elif dynaLoad[0] == "*LOAD_BODY_RY":
                load = self.CreateLoadBodyRY(lcid, sf, lciddr, xc, yc, zc, cid)
            elif dynaLoad[0] == "*LOAD_BODY_RZ":
                load = self.CreateLoadBodyRZ(lcid, sf, lciddr, xc, yc, zc, cid) 
            elif dynaLoad[0] == "*LOAD_BODY_VECTOR": 
                parameters = dynaLoad[2] 
                fx = float(parameters[0])
                fy = float(parameters[1])
                fz = float(parameters[2])
                load = self.CreateLoadBodyVector(lcid, sf, lciddr, xc, yc, zc, cid, fx, fy, fz)
                
        if dynaLoad[0] == "*LOAD_NODE_POINT":
            parameters = dynaLoad[1]
            for i in range(len(parameters)):
                firstLine = parameters[i]
                if len(firstLine[0]) == 0:
                    firstLine[0] = "0"
                if len(firstLine[1]) == 0:
                    firstLine[1] = "0"
                if len(firstLine[2]) == 0:
                    firstLine[2] = "0"
                if len(firstLine[3]) == 0:
                    firstLine[3] = "0.0"
                if len(firstLine[4]) == 0:
                    firstLine[4] = "0"

                    
                    
                nid = KooDynaInt(firstLine[0])
                dof = KooDynaInt(firstLine[1])
                lcid = KooDynaInt(firstLine[2])
                sf = KooDynaFloat(firstLine[3])
                cid = KooDynaInt(firstLine[4])
                m1 = KooDynaFloat(firstLine[5],"")
                m2 = KooDynaFloat(firstLine[6],"")
                m3 = KooDynaFloat(firstLine[7],"")
                if dof == 1:
                    load = self.CreateLoadNodalPoint("",lcid,cid,sf,0.0,0.0,nid)                                                  
                elif dof == 2:
                    load = self.CreateLoadNodalPoint("",lcid,cid,0.0,sf,0.0,nid)
                elif dof == 3:
                    load = self.CreateLoadNodalPoint("",lcid,cid,0.0,0.0,sf,nid)     
                       
        if dynaLoad[0] == "*LOAD_SEGMENT":
            parameters = dynaLoad[1]
            for i in range(len(parameters)):
                curParameters = parameters[i]
                firstLine = curParameters
                lcid = firstLine[0]
                sf = firstLine[1]
                at = firstLine[2]                
                n1 = int(firstLine[3])
                n2 = int(firstLine[4])
                if len(firstLine[5])>0:
                    n3 = int(firstLine[5])
                else:
                    n3 = 0
                if len(firstLine[6])>0:
                    n4 = int(firstLine[6])
                else:
                    n4 = 0
                if len(firstLine[7])>0:
                    n5 = int(firstLine[7])
                    i = i + 1 
                    curParameters = parameters[i]
                    secondLine = curParameters
                    if len(secondLine[0])>0:
                        n6 = int(secondLine[0])
                    else:
                        n6 = 0
                    if len(secondLine[1])>0:
                        n7 = int(secondLine[1])
                    else:
                        n7 = 0
                    if len(secondLine[2])>0:
                        n8 = int(secondLine[2])
                    else:
                        n8 = 0                     
                else:
                    n5 = 0
                    n6 = 0 
                    n7 = 0 
                    n8 = 0 
                if n1 == 0:
                    N1 = None
                else:
                    N1 = nodeManager.nodes[n1]
                if n2 == 0:
                    N2 = None
                else:
                    N2 = nodeManager.nodes[n2]
                if n3 == 0:
                    N3 = None
                else:
                    N3 = nodeManager.nodes[n3]
                if n4 == 0:
                    N4 = None
                else:
                    N4 = nodeManager.nodes[n4]
                if n5 == 0:
                    N5 = None
                else:
                    N5 = nodeManager.nodes[n5]
                if n6 == 0:
                    N6 = None
                else:
                    N6 = nodeManager.nodes[n6]                    
                if n7 == 0:
                    N7 = None
                else:
                    N7 = nodeManager.nodes[n7]
                if n8 == 0:
                    N8 = None
                else:
                    N8 = nodeManager.nodes[n8]
                load = self.CreateLoadSegment("",lcid,sf,at,N1,N2,N3,N4,N5,N6,N7,N8)
            pass
        
        if dynaLoad[0] == "*LOAD_SEGMENT_ID":
            parameters = dynaLoad[1]
            for i in range(len(parameters)):
                curParameters = parameters[i]
                nameIDLine = curParameters
                lid = int(nameIDLine[0])
                name = nameIDLine[1]
                i = i + 1                        
                curParameters = parameters[i]
                firstLine = curParameters
                lcid = firstLine[0]
                sf = firstLine[1]
                at = firstLine[2]                
                n1 = int(firstLine[3])
                n2 = int(firstLine[4])
                if len(firstLine[5])>0:
                    n3 = int(firstLine[5])
                else:
                    n3 = 0
                if len(firstLine[6])>0:
                    n4 = int(firstLine[6])
                else:
                    n4 = 0
                if len(firstLine[7])>0:
                    n5 = int(firstLine[7])
                    i = i + 1 
                    curParameters = parameters[i]
                    secondLine = curParameters
                    if len(secondLine[0])>0:
                        n6 = int(secondLine[0])
                    else:
                        n6 = 0
                    if len(secondLine[1])>0:
                        n7 = int(secondLine[1])
                    else:
                        n7 = 0
                    if len(secondLine[2])>0:
                        n8 = int(secondLine[2])
                    else:
                        n8 = 0                     
                else:
                    n5 = 0
                    n6 = 0 
                    n7 = 0 
                    n8 = 0 
                if n1 == 0:
                    N1 = None
                else:
                    N1 = nodeManager.nodes[n1]
                if n2 == 0:
                    N2 = None
                else:
                    N2 = nodeManager.nodes[n2]
                if n3 == 0:
                    N3 = None
                else:
                    N3 = nodeManager.nodes[n3]
                if n4 == 0:
                    N4 = None
                else:
                    N4 = nodeManager.nodes[n4]
                if n5 == 0:
                    N5 = None
                else:
                    N5 = nodeManager.nodes[n5]
                if n6 == 0:
                    N6 = None
                else:
                    N6 = nodeManager.nodes[n6]                    
                if n7 == 0:
                    N7 = None
                else:
                    N7 = nodeManager.nodes[n7]
                if n8 == 0:
                    N8 = None
                else:
                    N8 = nodeManager.nodes[n8]
                load = self.CreateLoadSegmentwithID(lid,name,lcid,sf,at,N1,N2,N3,N4,N5,N6,N7,N8)
            pass
        
        if dynaLoad[0] == "*LOAD_SEGMENT_SET":
            parameters = dynaLoad[1]
            curParameters = parameters[0]
            firstLine = curParameters
            SSID = int(firstLine[0])
            lcid = int(firstLine[1])
            sf = float(firstLine[2])
            at = float(firstLine[3])
            segmentSet = segmentSetManager.segmentSetList[SSID]
            load = self.CreateLoadSegmentSet("",segmentSet,lcid,sf,at)                
            
        if dynaLoad[0] == "*LOAD_SEGMENT_SET_ID":
            parameters = dynaLoad[1]
            curParameters = parameters[0]
            firstLine = curParameters
            lid = int(firstLine[0])
            name = firstLine[1]
            curParameters = parameters[1]
            secondLine = curParameters
            SSID = int(secondLine[0])
            lcid = int(secondLine[1])
            sf = float(secondLine[2])
            at = float(secondLine[3])
            segmentSet = segmentSetManager.segmentSetList[SSID]
            load = self.CreateLoadSegmentSetwithID(lid,name,segmentSet,lcid,sf,at)            
            
        
    
    
    
            
        
        