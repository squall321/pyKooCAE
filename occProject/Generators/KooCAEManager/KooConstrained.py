from __future__ import annotations
from KooCAEManager.KooPart import *
from KooCAEManager.KooOperator import *

class KooConstrained:
    def __init__(self, cnsid):
        self.cnsid = cnsid
        self.cnsType = None

class KooConstrainedNodeSet(KooConstrained):
    def __init__(self, cnsid, nsid, dof, tf=1.0e20):
        super(KooConstrainedNodeSet, self).__init__(cnsid)
        self.nsid = nsid
        self.dof = dof
        self.tf = tf
        self.cnsType = "CONSTRAINED_NODE_SET"
        
    def WritetoDynaKeyword(self, startID):
        keyword = "*CONSTRAINED_NODE_SET_ID\n"
        idStr = format(self.cnsid + startID, ">10")
        keyword += idStr + "\n"
        nsidStr = format(self.nsid + startID, ">10")
        dofStr = format(self.dof, ">10")
        tfStr = format(self.tf, ">10.3e")
        keyword +=  nsidStr + dofStr + tfStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*CONSTRAINED_NODE_SET_ID\n")
        idStr = format(self.cnsid + startID, ">10")
        stream.write(idStr + "\n")
        nsidStr = format(self.nsid + startID, ">10")
        dofStr = format(self.dof, ">10")
        tfStr = format(self.tf, ">10.3e")
        stream.write(nsidStr + dofStr + tfStr + "\n")

class KooConstrainedNodalRigidbody(KooConstrained):
    def __init__(self, id, name,pid, cid, nsid, pnode, iprt, drflag, rrflag):
        super(KooConstrainedNodalRigidbody, self).__init__(id)
        self.name = name
        self.pid = pid
        self.cid = cid
        self.nsid = nsid
        self.pnode = pnode
        self.iprt = iprt
        self.drflag = drflag
        self.rrflag = rrflag
        self.cnsType = "CONSTRAINED_NODAL_RIGID_BODY"
        
    def WritetoDynaKeyword(self, startID):
        keyword = "*CONSTRAINED_NODAL_RIGID_BODY_TITLE\n"
        #idStr = format(self.cnsid + startID, ">80")
        nameStr = format(self.name, ">80")
        keyword += nameStr + "\n"
        
        pidStr = format(self.pid, ">10")
        cidStr = format(self.cid, ">10")
        nsidStr = format(self.nsid + startID, ">10")
        pnodeStr = format(self.pnode, ">10")
        iprtStr = format(self.iprt, ">10")
        drflagStr = format(self.drflag, ">10")
        rrflagStr = format(self.rrflag, ">10")
        keyword += nameStr + pidStr + cidStr + nsidStr + pnodeStr + iprtStr + drflagStr + rrflagStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*CONSTRAINED_NODAL_RIGID_BODY_TITLE\n")
        #idStr = format(self.cnsid + startID, ">80")
        #stream.write(idStr + "\n")
        nameStr = format(self.name, ">80")
        stream.write(nameStr + "\n")
        stream.write("$$     PID       CID      NSID     PNODE      IPRT    DRFLAG    RRFLAG\n")
        pidStr = format(self.pid, ">10")
        cidStr = format(self.cid, ">10")
        nsidStr = format(self.nsid + startID, ">10")
        pnodeStr = format(self.pnode, ">10")
        iprtStr = format(self.iprt, ">10")
        drflagStr = format(self.drflag, ">10")
        rrflagStr = format(self.rrflag, ">10")
        stream.write(pidStr + cidStr + nsidStr + pnodeStr + iprtStr + drflagStr + rrflagStr + "\n")
     
        
class KooConstrainedInterpolationBasic:
    def __init__(self, icid):
        self.icid = icid
        self.cnsType = None
        
class KooConstrainedInterpolation(KooConstrainedInterpolationBasic):
    def __init__(self, icid, dnid, ddof=123456, cidd="", ityp=0, idnsw=1, fgm=0, inid = [], idof = [], twghtx = [], twghty = [], twghtz = [], rwghtx = [], rwghty = [], rwghtz = []):
        super(KooConstrainedInterpolation, self).__init__(icid)
        self.dnid = dnid
        self.ddof = ddof
        self.cidd = cidd
        self.ityp = ityp
        self.idnsw = idnsw
        self.fgm = fgm
        self.inid = inid
        self.idof = idof
        self.twghtx = twghtx
        self.twghty = twghty
        self.twghtz = twghtz
        self.rwghtx = rwghtx
        self.rwghty = rwghty
        self.rwghtz = rwghtz
        self.cnsType = "CONSTRAINED_INTERPOLATION"
    
    def WritetoDynaKeyword(self, startNID):
        keyword = "*CONSTRAINED_INTERPOLATION\n"
        idStr = format(self.icid, ">10")
        dnidStr = format(self.dnid + startNID, ">10")
        ddofStr = format(self.ddof, ">10")
        ciddStr = format(self.cidd, ">10")
        itypStr = format(self.ityp, ">10")
        idnswStr = format(self.idnsw, ">10")
        fgmStr = format(self.fgm, ">10")
        keyword += idStr + dnidStr + ddofStr + ciddStr + itypStr + idnswStr + fgmStr + "\n"
        
        for i in range(len(self.inid)):
            inidStr = format(self.inid[i] + startNID, ">10")
            idofStr = format(self.idof[i], ">10")
            twghtxStr = format(self.twghtx[i], ">10.3e")
            twghtyStr = format(self.twghty[i], ">10.3e")
            twghtzStr = format(self.twghtz[i], ">10.3e")
            rwghtxStr = format(self.rwghtx[i], ">10.3e")
            rwghtyStr = format(self.rwghty[i], ">10.3e")
            rwghtzStr = format(self.rwghtz[i], ">10.3e")
            keyword += inidStr + idofStr + twghtxStr + twghtyStr + twghtzStr + rwghtxStr + rwghtyStr + rwghtzStr + "\n"
        return keyword

    def WriteStreamDynaKeyword(self, stream, startNID):
        stream.write("*CONSTRAINED_INTERPOLATION\n")
        idStr = format(self.icid, ">10")
        dnidStr = format(self.dnid + startNID, ">10")
        ddofStr = format(self.ddof, ">10")
        ciddStr = format(self.cidd, ">10")
        itypStr = format(self.ityp, ">10")
        idnswStr = format(self.idnsw, ">10")
        fgmStr = format(self.fgm, ">10")
        stream.write(idStr + dnidStr + ddofStr + ciddStr + itypStr + idnswStr + fgmStr + "\n") 
        
        for i in range(len(self.inid)):
            inidStr = format(self.inid[i] + startNID, ">10")
            idofStr = format(self.idof[i], ">10")
            twghtxStr = format(self.twghtx[i], ">10.3e")
            if self.twghty[i] == self.twghtx[i]:
                twghtyStr = "          "
            else:
                twghtyStr = format(self.twghty[i], ">10.3e")
            if self.twghtz[i] == self.twghtx[i]:
                twghtzStr = "          "
            else:
                twghtzStr = format(self.twghtz[i], ">10.3e")
            if self.rwghtx[i] == self.twghtx[i]:
                rwghtxStr = "          "
            else:
                rwghtxStr = format(self.rwghtx[i], ">10.3e")
            if self.rwghty[i] == self.twghtx[i]:
                rwghtyStr = "          "
            else:
                rwghtyStr = format(self.rwghty[i], ">10.3e")
            if self.rwghtz[i] == self.twghtx[i]:
                rwghtzStr = "          "
            else:
                rwghtzStr = format(self.rwghtz[i], ">10.3e")
            stream.write(inidStr + idofStr + twghtxStr + twghtyStr + twghtzStr + rwghtxStr + rwghtyStr + rwghtzStr + "\n")   

class KooConstrainedJointSpherical(KooConstrained):
    def __init__(self, cnsid, n1, n2, n3, n4, n5, n6, rps, damp):
        super(KooConstrainedJointSpherical, self).__init__(cnsid)
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4
        self.n5 = n5
        self.n6 = n6
        self.rps = rps
        self.damp = damp
        self.cnsType = "CONSTRAINED_JOINT_SPHERICAL"
    
    def WritetoDynaKeyword(self, startID):
        keyword = "*CONSTRAINED_JOINT_SPHERICAL\n"
        keyword += "$$      N1        N2        N3        N4        N5        N6       RPS      DAMP\n"
        n1Str = format(self.n1 + startID, ">10")
        n2Str = format(self.n2 + startID, ">10")
        n3Str = format(self.n3 + startID, ">10")
        n4Str = format(self.n4 + startID, ">10")
        n5Str = format(self.n5 + startID, ">10")
        n6Str = format(self.n6 + startID, ">10")
        rpsStr = format(self.rps, ">10.3e")
        dampStr = format(self.damp, ">10.3e")
        keyword += n1Str + n2Str + n3Str + n4Str + n5Str + n6Str + rpsStr + dampStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*CONSTRAINED_JOINT_SPHERICAL\n")
        stream.write("$$      N1        N2        N3        N4        N5        N6       RPS      DAMP\n")
        n1Str = format(self.n1 + startID, ">10")
        n2Str = format(self.n2 + startID, ">10")
        n3Str = format(self.n3 + startID, ">10")
        n4Str = format(self.n4 + startID, ">10")
        n5Str = format(self.n5 + startID, ">10")
        n6Str = format(self.n6 + startID, ">10")
        rpsStr = format(self.rps, ">10.3e")
        dampStr = format(self.damp, ">10.3e")
        stream.write(n1Str + n2Str + n3Str + n4Str + n5Str + n6Str + rpsStr + dampStr + "\n")

class KooConstrainedJointSphericalID(KooConstrained):
    def __init__(self, cnsid, id, title, n1, n2, n3, n4, n5, n6, rps, damp):
        super(KooConstrainedJointSphericalID, self).__init__(cnsid)
        self.id = id
        self.title = title
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4
        self.n5 = n5
        self.n6 = n6
        self.rps = rps
        self.damp = damp
        self.cnsType = "CONSTRAINED_JOINT_SPHERICAL_ID"
    
    def WritetoDynaKeyword(self, startID):
        keyword = "*CONSTRAINED_JOINT_SPHERICAL_ID\n"
        keyword += "$$      ID                                                               TITLE\n"
        idStr = format(self.id, ">10")
        titleStr = format(self.title, ">70")
        keyword += idStr + titleStr + "\n"
        keyword += "$$      N1        N2        N3        N4        N5        N6       RPS      DAMP\n"
        n1Str = format(self.n1 + startID, ">10")
        n2Str = format(self.n2 + startID, ">10")
        n3Str = format(self.n3 + startID, ">10")
        n4Str = format(self.n4 + startID, ">10")
        n5Str = format(self.n5 + startID, ">10")
        n6Str = format(self.n6 + startID, ">10")
        rpsStr = format(self.rps, ">10.3e")
        dampStr = format(self.damp, ">10.3e")
        keyword += n1Str + n2Str + n3Str + n4Str + n5Str + n6Str + rpsStr + dampStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*CONSTRAINED_JOINT_SPHERICAL_ID\n")
        stream.write("$$      ID                                                               TITLE\n")
        idStr = format(self.id, ">10")
        titleStr = format(self.title, ">70")
        stream.write(idStr + titleStr + "\n")
        stream.write("$$      N1        N2        N3        N4        N5        N6       RPS      DAMP\n")
        n1Str = format(self.n1 + startID, ">10")
        n2Str = format(self.n2 + startID, ">10")
        n3Str = format(self.n3 + startID, ">10")
        n4Str = format(self.n4 + startID, ">10")
        n5Str = format(self.n5 + startID, ">10")
        n6Str = format(self.n6 + startID, ">10")
        rpsStr = format(self.rps, ">10.3e")
        dampStr = format(self.damp, ">10.3e")        
        stream.write(n1Str + n2Str + n3Str + n4Str + n5Str + n6Str + rpsStr + dampStr + "\n")

class KooConstrainedRigidbodyBasic:
    def __init__(self, crbsid):
        self.ic = crbsid
        self.cnsType = None

class KooConstrainedRigidbody(KooConstrainedInterpolationBasic):
    def __init__(self, crbsid, PIDLList, PIDCList, IFLAGList):
        super(KooConstrainedRigidbody, self).__init__(crbsid)
        self.PIDLList = PIDLList
        self.PIDCList = PIDCList
        self.IFLAGList = IFLAGList
        self.cnsType = "CONSTRAINED_RIGID_BODY"
        
    def WritetoDynaKeyword(self, startID):
        keyword = "*CONSTRAINED_RIGID_BODY\n"
        keyword += "$$    PIDL      PIDC     IFLAG\n"
        for i in range(len(self.PIDLList)):
            pidlStr = format(self.PIDLList[i] + startID, ">10")
            pidcStr = format(self.PIDCList[i] + startID, ">10")
            iflagStr = format(self.IFLAGList[i], ">10")
            keyword += pidlStr + pidcStr + iflagStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*CONSTRAINED_RIGID_BODY\n")
        stream.write("$$    PIDL      PIDC     IFLAG\n")
        for i in range(len(self.PIDLList)):
            pidlStr = format(self.PIDLList[i] + startID, ">10")
            pidcStr = format(self.PIDCList[i] + startID, ">10")
            iflagStr = format(self.IFLAGList[i], ">10")
            stream.write(pidlStr + pidcStr + iflagStr + "\n")
            
class KooConstrainedRigidBodySet(KooConstrainedRigidbodyBasic):
    def __init__(self, crbsid, pidlList, pidcList, iflagList):
        super(KooConstrainedRigidBodySet, self).__init__(crbsid)
        self.PIDLList = pidlList
        self.PIDCList = pidcList
        self.IFLAGList = iflagList
        self.cnsType = "CONSTRAINED_RIGID_BODY_SET"
        
    def WritetoDynaKeyword(self, startID):
        keyword = "*CONSTRAINED_RIGID_BODY_SET\n"
        keyword += "$$    PIDL      PIDC     IFLAG\n"
        for i in range(len(self.PIDLList)):
            pidlStr = format(self.PIDLList[i] + startID, ">10")
            pidcStr = format(self.PIDCList[i] + startID, ">10")
            iflagStr = format(self.IFLAGList[i], ">10")
            keyword += pidlStr + pidcStr + iflagStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*CONSTRAINED_RIGID_BODY_SET\n")
        stream.write("$$    PIDL      PIDC     IFLAG\n")
        for i in range(len(self.PIDLList)):
            pidlStr = format(self.PIDLList[i] + startID, ">10")
            pidcStr = format(self.PIDCList[i] + startID, ">10")
            iflagStr = format(self.IFLAGList[i], ">10")
            stream.write(pidlStr + pidcStr + iflagStr + "\n")


class ConstrainedExtraNodesNode(KooConstrained):
    def __init__(self, cnsid, pid, nid, iflag):
        super(ConstrainedExtraNodesNode, self).__init__(cnsid)
        self.pid = pid
        self.nid = nid
        self.iflag = iflag
        self.cnsType = "CONSTRAINED_EXTRA_NODES_NODE"
        
    def WritetoDynaKeyword(self, startID):
        keyword = "*CONSTRAINED_EXTRA_NODES_NODE\n"
        keyword += "$$    PID       NID     IFLAG\n"
        pidStr = format(self.pid, ">10")
        nidStr = format(self.nid, ">10")
        iflagStr = format(self.iflag, ">10")
        keyword += pidStr + nidStr + iflagStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*CONSTRAINED_EXTRA_NODES_NODE\n")
        stream.write("$$    PID       NID     IFLAG\n")
        pidStr = format(self.pid, ">10")
        nidStr = format(self.nid, ">10")
        iflagStr = format(self.iflag, ">10")
        stream.write(pidStr + nidStr + iflagStr + "\n") 

class ConstrainedExtraNodesSet(KooConstrained):
    def __init__(self, cnsid, pid, nsid, iflag):
        super(ConstrainedExtraNodesSet, self).__init__(cnsid)
        self.pid = pid
        self.nsid = nsid
        self.iflag = iflag
        self.cnsType = "CONSTRAINED_EXTRA_NODES_SET"
        
    def WritetoDynaKeyword(self, startID):
        keyword = "*CONSTRAINED_EXTRA_NODES_SET\n"
        keyword += "$$    PID       NSID     IFLAG\n"
        pidStr = format(self.pid, ">10")
        nsidStr = format(self.nsid, ">10")
        iflagStr = format(self.iflag, ">10")
        keyword += pidStr + nsidStr + iflagStr + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        stream.write("*CONSTRAINED_EXTRA_NODES_SET\n")
        stream.write("$$    PID       NSID     IFLAG\n")
        pidStr = format(self.pid, ">10")
        nsidStr = format(self.nsid, ">10")
        iflagStr = format(self.iflag, ">10")
        stream.write(pidStr + nsidStr + iflagStr + "\n")

class KooConstrainedManager:
    def __init__(self):
        self.maxCNSID = 0
        self.maxICID = 0
        self.maxCNRBID = 0
        self.maxCRBID = 0 
        self.maxCENID = 0
        self.maxCESID = 0
        self.maxCJSID = 0
        self.maxCJSIDID = 0
        self.constrainedNodeSetList = {}
        self.constrainedInterpolationList = {}
        self.constrainedNodalRigidbodyList = {}
        self.constrainedRigidbodyList = {}
        self.constrainedExtraNodesNodeList = {}
        self.constrainedExtraNodesSetList = {}
        self.constrainedJointSphericalList = {}
        self.constrainedJointSphericalIDList = {}
    def OverwritefromConstrainedManager(self, constrainedManager: KooConstrainedManager):
        self.maxCNSID = max(self.maxCNSID, constrainedManager.maxCNSID)
        self.maxICID = max(self.maxICID, constrainedManager.maxICID)
        self.maxCNRBID = max(self.maxCNRBID, constrainedManager.maxCNRBID)
        self.maxCRBID = max(self.maxCRBID, constrainedManager.maxCRBID)
        self.maxCENID = max(self.maxCENID, constrainedManager.maxCENID)
        self.maxCESID = max(self.maxCESID, constrainedManager.maxCESID)
        self.maxCJSID = max(self.maxCJSID, constrainedManager.maxCJSID)
        self.maxCJSIDID = max(self.maxCJSIDID, constrainedManager.maxCJSIDID)
        for key, value in constrainedManager.constrainedNodeSetList.items():
            self.constrainedNodeSetList[key] = value
        for key, value in constrainedManager.constrainedInterpolationList.items():
            self.constrainedInterpolationList[key] = value
        for key, value in constrainedManager.constrainedNodalRigidbodyList.items():
            self.constrainedNodalRigidbodyList[key] = value
        for key, value in constrainedManager.constrainedRigidbodyList.items():
            self.constrainedRigidbodyList[key] = value
        for key, value in constrainedManager.constrainedExtraNodesNodeList.items():
            self.constrainedExtraNodesNodeList[key] = value
        for key, value in constrainedManager.constrainedExtraNodesSetList.items():
            self.constrainedExtraNodesSetList[key] = value
        for key, value in constrainedManager.constrainedJointSphericalList.items():
            self.constrainedJointSphericalList[key] = value
        for key, value in constrainedManager.constrainedJointSphericalIDList.items():
            self.constrainedJointSphericalIDList[key] = value
    
    def CreateConstrainedNodeSet(self, nsid, dof, tf=1.0e20):
        self.maxCNSID += 1
        cnsid = self.maxCNSID
        cns = KooConstrainedNodeSet(cnsid, nsid, dof, tf)
        self.constrainedNodeSetList[cnsid] = cns
        return cns
    
    def CreateConstrainedNodeSetwithID(self, cnsid, nsid, dof, tf=1.0e20):       
        self.maxCNSID = max(self.maxCNSID, cnsid)
        cns = KooConstrainedNodeSet(cnsid, nsid, dof, tf)
        self.constrainedNodeSetList[cnsid] = cns
        return cns
    
    def CreateConstrainedNodalRigidbody(self, name,pid, cid, nsid, pnode, iprt, drflag, rrflag):
        self.maxCNRBID += 1
        cnrb = KooConstrainedNodalRigidbody(self.maxCNRBID, name,pid, cid, nsid, pnode, iprt, drflag, rrflag)
        self.constrainedNodalRigidbodyList[self.maxCNRBID] = cnrb
    
    def CreateConstrainedNodalRigidbodywithID(self, cnsid, name,pid, cid, nsid, pnode, iprt, drflag, rrflag):
        self.maxCNRBID = max(self.maxCNRBID, cnsid)
        cnrb = KooConstrainedNodalRigidbody(cnsid, name,pid, cid, nsid, pnode, iprt, drflag, rrflag)
        self.constrainedNodalRigidbodyList[cnsid] = cnrb
        
    def CreateConstrainedInterpolation(self, icid, dnid, ddof=123456, cidd="", ityp=0, idnsw=1, fgm=0, inid = [], idof = [], twghtx = [], twghty = [], twghtz = [], rwghtx = [], rwghty = [], rwghtz = []):
        self.maxICID = max(self.maxICID, icid)
        ci = KooConstrainedInterpolation(icid, dnid, ddof, cidd, ityp, idnsw, fgm, inid, idof, twghtx, twghty, twghtz, rwghtx, rwghty, rwghtz)
        self.constrainedInterpolationList[icid] = ci
        
    def CreateConstrainedRigidbody(self, PIDLList, PIDCList, IFLAGList):
        self.maxCRBID += 1
        crb = KooConstrainedRigidbody(self.maxCRBID, PIDLList, PIDCList, IFLAGList)
        self.constrainedRigidbodyList[self.maxCRBID] = crb
        return crb
    
    def CreateConstrainedRigidbodySet(self, pidlList, pidcList, iflagList):
        self.maxCRBID += 1
        crbs = KooConstrainedRigidBodySet(self.maxCRBID, pidlList, pidcList, iflagList)
        self.constrainedRigidbodyList[self.maxCRBID] = crbs
        return crbs

    def CreateConstrainedExtraNodesNode(self, pid, nid, iflag):
        self.maxCENID += 1
        cen = ConstrainedExtraNodesNode(self.maxCENID, pid, nid, iflag)
        self.constrainedExtraNodesNodeList[self.maxCENID] = cen
        return cen
    
    def CreateConstrainedExtraNodesSet(self, pid, nsid, iflag):
        self.maxCESID += 1
        ces = ConstrainedExtraNodesSet(self.maxCESID, pid, nsid, iflag)
        self.constrainedExtraNodesSetList[self.maxCESID] = ces
        return ces

    def CreateConstrainedJointSpherical(self, n1, n2, n3, n4, n5, n6, rps, damp):
        self.maxCJSID += 1
        cjs = KooConstrainedJointSpherical(self.maxCJSID, n1, n2, n3, n4, n5, n6, rps, damp)
        self.constrainedJointSphericalList[self.maxCJSID] = cjs
        return cjs
    
    def CreateConstrainedJointSphericalID(self, id, title, n1, n2, n3, n4, n5, n6, rps, damp):
        self.maxCJSID += 1
        cjs = KooConstrainedJointSphericalID(self.maxCJSID, id, title, n1, n2, n3, n4, n5, n6, rps, damp)
        self.constrainedJointSphericalIDList[self.maxCJSID] = cjs
        return cjs
        
    def SetConstrained(self, constrainedKeyword):
        if "*CONSTRAINED_NODE_SET_ID" in constrainedKeyword[0]:
            firstLine = constrainedKeyword[1]
            cnsid = KooDynaInt(firstLine[0])
            secondLine = constrainedKeyword[2]
            nsid = KooDynaInt(secondLine[0])
            dof = KooDynaInt(secondLine[1])
            tf = KooDynaFloat(secondLine[2], 1.0E20)
            cns = self.CreateConstrainedNodeSetwithID(cnsid, nsid, dof, tf) 
        elif "*CONSTRAINED_NODE_SET" in constrainedKeyword[0]:
            firstLine = constrainedKeyword[1]
            nsid = KooDynaInt(firstLine[0])
            dof = KooDynaInt(firstLine[1])
            tf = KooDynaFloat(firstLine[2], 1.0E20)
            cns = self.CreateConstrainedNodeSet(nsid, dof, tf)
        
        elif "*CONSTRAINED_NODAL_RIGID_BODY_TITLE" in constrainedKeyword[0]:
            firstLine = constrainedKeyword[1]
            name = KooDynaString(firstLine[0])
            secondLine = constrainedKeyword[2]            
            pid = KooDynaInt(secondLine[0])
            cid = KooDynaInt(secondLine[1])
            nsid = KooDynaInt(secondLine[2])
            pnode = KooDynaInt(secondLine[3])
            IPRT = KooDynaInt(secondLine[4])
            DRFLAG = KooDynaInt(secondLine[5])
            RRFLAG = KooDynaInt(secondLine[6])
            
            cns = self.CreateConstrainedNodalRigidbody(name, pid, cid, nsid, pnode, IPRT, DRFLAG, RRFLAG)
        elif "*CONSTRAINED_NODAL_RIGID_BODY" in constrainedKeyword[0]:            
            secondLine = constrainedKeyword[1]
            pid = KooDynaInt(secondLine[0])
            cid = KooDynaInt(secondLine[1])
            nsid = KooDynaInt(secondLine[2])
            pnode = KooDynaInt(secondLine[3])
            IPRT = KooDynaInt(secondLine[4])
            DRFLAG = KooDynaInt(secondLine[5])
            RRFLAG = KooDynaInt(secondLine[6])
            self.CreateConstrainedNodalRigidbody("None", pid, cid, nsid, pnode, IPRT, DRFLAG, RRFLAG)
            
        elif "*CONSTRAINED_INTERPOLATION" in constrainedKeyword[0]:
            firstLine = constrainedKeyword[1]
            icid = KooDynaInt(firstLine[0])
            dnid = KooDynaInt(firstLine[1])
            ddof = KooDynaInt(firstLine[2], 123456)
            cidd = KooDynaInt(firstLine[3],"")
            ityp = KooDynaInt(firstLine[4])
            idnsw = KooDynaInt(firstLine[5])
            fgm = KooDynaInt(firstLine[6])
            
            inidList = []
            idofList = [] 
            twghtxList = [] 
            twghtyList = []
            twghtzList = []
            rwghtxList = []
            rwghtyList = []
            rwghtzList = []
            
            for i in range(2, len(constrainedKeyword)):
                line = constrainedKeyword[i]
                inid = KooDynaInt(line[0])
                idof = KooDynaInt(line[1])
                twghtx = KooDynaFloat(line[2],1.0)
                twghty = KooDynaFloat(line[3], twghtx)
                twghtz = KooDynaFloat(line[4], twghtx)
                rwghtx = KooDynaFloat(line[5], twghtx)
                rwghty = KooDynaFloat(line[6], twghtx)
                rwghtz = KooDynaFloat(line[7], twghtx)
                inidList.append(inid)
                idofList.append(idof)
                twghtxList.append(twghtx)
                twghtyList.append(twghty)
                twghtzList.append(twghtz)
                rwghtxList.append(rwghtx)
                rwghtyList.append(rwghty)
                rwghtzList.append(rwghtz)
            self.CreateConstrainedInterpolation(icid, dnid, ddof, cidd, ityp, idnsw, fgm, inidList, idofList, twghtxList, twghtyList, twghtzList, rwghtxList, rwghtyList, rwghtzList)
                
        elif "*CONSTRAINED_JOINT_SPHERICAL_ID" in constrainedKeyword[0]:
            firstLine = constrainedKeyword[1]
            id = KooDynaInt(firstLine[0])
            title = KooDynaString(firstLine[1])
            secondLine = constrainedKeyword[2]  
            n1 = KooDynaInt(secondLine[0])
            n2 = KooDynaInt(secondLine[1])
            n3 = KooDynaInt(secondLine[2])
            n4 = KooDynaInt(secondLine[3])
            n5 = KooDynaInt(secondLine[4])
            n6 = KooDynaInt(secondLine[5])
            rps = KooDynaFloat(secondLine[6], 1.0)
            damp = KooDynaFloat(secondLine[7], 1.0)
            self.CreateConstrainedJointSphericalID(id, title, n1, n2, n3, n4, n5, n6, rps, damp)

        elif "*CONSTRAINED_JOINT_SPHERICAL" in constrainedKeyword[0]:
            firstLine = constrainedKeyword[1]
            n1 = KooDynaInt(firstLine[0])
            n2 = KooDynaInt(firstLine[1])
            n3 = KooDynaInt(firstLine[2])
            n4 = KooDynaInt(firstLine[3])
            n5 = KooDynaInt(firstLine[4])   
            n6 = KooDynaInt(firstLine[5])
            rps = KooDynaFloat(firstLine[6], 1.0)
            damp = KooDynaFloat(firstLine[7], 1.0)
            self.CreateConstrainedJointSpherical(n1, n2, n3, n4, n5, n6, rps, damp)

        elif "*CONSTRAINED_RIGID_BODY" in constrainedKeyword[0]:
            PIDList = [] 
            PIDCList = []
            IFLAGList = []
            for i in range(1, len(constrainedKeyword)):
                line = constrainedKeyword[i]
                pidl = KooDynaInt(line[0])
                pidc = KooDynaInt(line[1])
                iflag = KooDynaInt(line[2])
                PIDList.append(pidl)
                PIDCList.append(pidc)
                IFLAGList.append(iflag)
            
            self.CreateConstrainedRigidbody(PIDList, PIDCList, IFLAGList)
        elif "*CONSTRAINED_RIGID_BODY_SET" in constrainedKeyword[0]:
            PIDList = [] 
            PIDCList = []
            IFLAGList = []
            for i in range(1, len(constrainedKeyword)):
                line = constrainedKeyword[i]
                pidl = KooDynaInt(line[0])
                pidc = KooDynaInt(line[1])
                iflag = KooDynaInt(line[2])
                PIDList.append(pidl)
                PIDCList.append(pidc)
                IFLAGList.append(iflag)
            
            self.CreateConstrainedRigidbodySet(PIDList, PIDCList, IFLAGList)         
        elif "*CONSTRAINED_EXTRA_NODES_NODE" in constrainedKeyword[0]:
            firstLine = constrainedKeyword[1]
            pid = KooDynaInt(firstLine[0])
            nid = KooDynaInt(firstLine[1])
            iflag = KooDynaInt(firstLine[2])
            self.CreateConstrainedExtraNodesNode(pid, nid, iflag)
        elif "*CONSTRAINED_EXTRA_NODES_SET" in constrainedKeyword[0]:
            firstLine = constrainedKeyword[1]
            pid = KooDynaInt(firstLine[0])
            nsid = KooDynaInt(firstLine[1])
            iflag = KooDynaInt(firstLine[2])
            self.CreateConstrainedExtraNodesSet(pid, nsid, iflag)
            
    def WriteStreamDynaKeyword(self, stream, startID):
        #print("Writing Constrained")
        for cnsid in self.constrainedNodeSetList:
            cns = self.constrainedNodeSetList[cnsid]
            cns.WriteStreamDynaKeyword(stream, startID)
        #print(len(self.constrainedInterpolationList), " Constrained Interpolation")
            
        for icid in self.constrainedInterpolationList:
            ci = self.constrainedInterpolationList[icid]
            ci.WriteStreamDynaKeyword(stream, startID)
        #print(len(self.constrainedInterpolationList), " Constrained Nodal Rigidbody")
            
        for cnrbid in self.constrainedNodalRigidbodyList:
            cnrb = self.constrainedNodalRigidbodyList[cnrbid]
            cnrb.WriteStreamDynaKeyword(stream, startID)
        #print(len(self.constrainedNodalRigidbodyList), " Constrained Nodal Rigidbody")
        
        for crbid in self.constrainedRigidbodyList:
            crb = self.constrainedRigidbodyList[crbid]
            crb.WriteStreamDynaKeyword(stream, startID)
        #print("Writing Constrained Done")

        for cjsid in self.constrainedJointSphericalList:
            cjs = self.constrainedJointSphericalList[cjsid]
            cjs.WriteStreamDynaKeyword(stream, startID)
        for cjsidid in self.constrainedJointSphericalIDList:
            cjsid = self.constrainedJointSphericalIDList[cjsidid]
            cjsid.WriteStreamDynaKeyword(stream, startID)

        for cenid in self.constrainedExtraNodesNodeList:
            cen = self.constrainedExtraNodesNodeList[cenid]
            cen.WriteStreamDynaKeyword(stream, startID)
        for cesid in self.constrainedExtraNodesSetList:
            ces = self.constrainedExtraNodesSetList[cesid]
            ces.WriteStreamDynaKeyword(stream, startID)
            
        #print("Writing Constrained Done")

    def GenerateConstrainedRigidbodyfromPIDList(self, pidList, iflag):
        pidL = pidList[0]
        pidLList = []
        pidCList = []
        iflagList = []
        for pidC in pidList[1:]:
            pidLList.append(pidL)
            pidCList.append(pidC)
            iflagList.append(iflag)
        crb = self.CreateConstrainedRigidbody(pidLList, pidCList, iflagList)
        
    def GenerageConstraintforAllRigidBodies(self, partMan : KooPartManager, iflag = 1):
        rigidList = []
        for pid in partMan.parts:
            part : KooPart = partMan.parts[pid]
            mat = part.material
            if type(mat) is KooMaterialRigid:
                rigidList.append(pid)
                
        if len(rigidList) == 0:
            print("There is no rigid body in the part manager.")
            return
        
        pidL = rigidList[0]
        
        pidLList = [] 
        pidCList = [] 
        iflagList = []
        for pidC in rigidList[1:]:
            pidLList.append(pidL)
            pidCList.append(pidC)
            iflagList.append(iflag)
        
        crb = self.CreateConstrainedRigidbody(pidLList, pidCList, iflagList)
    
    def RemoveAllConstrainedRigidBodies(self):
        self.constrainedRigidbodyList.clear()
        self.maxCRBID = 0 
        
    def RemoveAllConstrainedExtraNodesNodes(self):
        self.constrainedExtraNodesNodeList.clear()
        self.maxCENID = 0
        
    def RemoveAllConstrainedExtraNodesSets(self):
        self.constrainedExtraNodesSetList.clear()
        self.maxCESID = 0
        
    def RemoveAllConstrainedJointSpherical(self):
        self.constrainedJointSphericalList.clear()
        self.maxCJSID = 0
        
    def RemoveAllConstrainedJointSphericalID(self):
        self.constrainedJointSphericalIDList.clear()
        self.maxCJSIDID = 0
        
    def ChangeConstrainedNodalRigidBodytoBeam(self, cnrbIDs, newPart : KooPart, nodesetMan : NodeSetManager):        
        nodeMan = newPart.nodeManager
        elemMan = newPart.elementManager
        for id in cnrbIDs:
            if id in self.constrainedNodalRigidbodyList:
                cnrb : KooConstrainedNodalRigidbody= self.constrainedNodalRigidbodyList[id]                 
                nodeset : NodeSet = nodesetMan.nodeSets[cnrb.nsid]
                centerX = 0.0
                centerY = 0.0
                centerZ = 0.0
                numNodes = len(nodeset.nodes)
                for nid in nodeset.nodes:
                    n =nodeset.nodes[nid]
                    centerX += n.x
                    centerY += n.y
                    centerZ += n.z
                centerX /= numNodes
                centerY /= numNodes 
                centerZ /= numNodes
                
                n1 = nodeMan.CreateNode(centerX, centerY, centerZ)
                for nid in nodeset.nodes:
                    n2 = nodeset.nodes[nid]                    
                    
                    v1 = [n1.x-n2.x, n1.y-n2.y, n1.z-n2.z]
                    if v1[0] == 0 and v1[1] == 0 and v1[2] == 0:
                        continue
                    nz = [0,0,1]
                    v2 = find_perpendicular_component(v1, nz)
                                                                              
                    distance = np.sqrt((n1.x-n2.x)**2 + (n1.y-n2.y)**2 + (n1.z-n2.z)**2)
                                    
                    
                    p3x = n1.x + v2[0]*distance
                    p3y = n1.y + v2[1]*distance
                    p3z = n1.z + v2[2]*distance
                    n3 = nodeMan.CreateNode(p3x, p3y, p3z)
                    elemMan.CreateLineQuadraticElement(n1, n2, n3)
        
        for id in cnrbIDs:
            #remove id in self.constrainedParts[id]
            if id in self.constrainedNodalRigidbodyList:
                del self.constrainedNodalRigidbodyList[id]
                    
                