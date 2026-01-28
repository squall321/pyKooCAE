import os
import numpy as np 
#from dynareadout import key_file_parse

    
def process_entry(entry):
    # Convert each element to float, handling non-float cases
    try:
        return [float(x) if x else 0 for x in entry]
    except ValueError:
        return [0] * len(entry)
    
class DynaKeyword():

    def __init__(self, name): 
        self.name = name
        self.parameters = []        
    
    def addParameter(self, parameter):
        self.parameters.append(parameter)

    def setIthJthKth(self,ith,jth,kth,value):
        self.parameters[ith][jth][kth] = value
    
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
    
    def writeParameter(self, stream, ith):
        if ith >= len(self.parameters):
            return
        
        formatted_elements = [f"{str(element):>10}" for element in self.parameters[ith]]
        result = ''.join(formatted_elements)
        stream.write(result)
        if result[len(result)-1] != '\n':
            stream.write("\n")

    def writeParameters(self, stream):
        for parameter in self.parameters:
            formatted_elements = [f"{str(element):>10}" for element in parameter]
            result = ''.join(formatted_elements)
            stream.write(result)
            if result[len(result)-1] != '\n':
                stream.write("\n")

    def write(self, stream):
        stream.write("*")
        stream.write(self.name)
        stream.write("\n")
        self.writeParameters(stream)

class BoundaryPrescribedMotionNode(DynaKeyword):
    def __init__(self):
        super(BoundaryPrescribedMotionNode,self).__init__("BOUNDARY_PRESCRIBED_MOTION_NODE")
    
    def parse(self, boundaryPrescribedMotionNodeKeywords):
        for i in range(len(boundaryPrescribedMotionNodeKeywords)):
            curParameter = boundaryPrescribedMotionNodeKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddBoundaryPrescribedMotionNode(self, nid, dof, vad, lcid, sf, vid, death, birth):
        parameterList = []
        parameterList.append([nid, dof, vad, lcid, sf, vid, death, birth])
        self.parameters.append(parameterList)        
    
    def getBoundaryPrescribedMotionNodeList(self):
        boundaryPrescribedMotionNodeList = []
        for i in range(len(self.parameters)):
            curBDPrescribedMotionNode = []
            curBDPrescribedMotionNode.append("*BOUNDARY_PRESCRIBED_MOTION_NODE")
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curBDPrescribedMotionNode.append(curParameter[j])
            boundaryPrescribedMotionNodeList.append(curBDPrescribedMotionNode)
        return boundaryPrescribedMotionNodeList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_PRESCRIBED_MOTION_NODE\n")
            stream.write("$$     NID       DOF       VAD      LCID        SF       VID     DEATH     BIRTH\n")
            for j in range(len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                
class BoundaryPrescribedMotionNodeID(DynaKeyword):
    def __init__(self):
        super(BoundaryPrescribedMotionNodeID,self).__init__("BOUNDARY_PRESCRIBED_MOTION_NODE_ID")
    
    def parse(self, boundaryPrescribedMotionNodeKeywords):
        for i in range(len(boundaryPrescribedMotionNodeKeywords)):
            curParameter = boundaryPrescribedMotionNodeKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)            
            parameters = self.parse_whole(curParameter[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)    
            self.parameters.append(parameterList)
    
    def AddBoundaryPrescribedMotionNodeID(self, bid, title, nid, dof, vad, lcid, sf, vid, death, birth):
        parameterList = []
        parameterList.append([bid, title])
        parameterList.append([nid, dof, vad, lcid, sf, vid, death, birth])
        self.parameters.append(parameterList)
        
    def getBoundaryPrescribedMotionNodeIDList(self):
        boundaryPrescribedMotionNodeIDList = []
        for i in range(len(self.parameters)):
            curBDPrescribedMotionNodeID = []
            curBDPrescribedMotionNodeID.append("*BOUNDARY_PRESCRIBED_MOTION_NODE_ID")
            curBDPrescribedMotionNodeID.append(self.parameters[i][0])
            curBDPrescribedMotionNodeID.append(self.parameters[i][1])
            boundaryPrescribedMotionNodeIDList.append(curBDPrescribedMotionNodeID)
        return boundaryPrescribedMotionNodeIDList           

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_PRESCRIBED_MOTION_NODE_ID\n")
            stream.write("$$      ID                                                                 TITLE\n")
            formatted_elements = f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            stream.write("$$     NID       DOF       VAD      LCID        SF       VID     DEATH     BIRTH\n")
            for j in range(1,len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                
class BoundaryPrescribedMotionRigid(DynaKeyword):
    def __init__(self):
        super(BoundaryPrescribedMotionRigid,self).__init__("BOUNDARY_PRESCRIBED_MOTION_RIGID")

    def parse(self, boundaryPrescribedMotionRigidKeywords):
        for i in range(len(boundaryPrescribedMotionRigidKeywords)):
            curParameter = boundaryPrescribedMotionRigidKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddBoundaryPrescribedMotionRigid(self, typeid, dof, vad, lcid, sf, vid, death, birth):
        parameterList = []
        parameterList.append([typeid, dof, vad, lcid, sf, vid, death, birth])
        self.parameters.append(parameterList)
    
    def getBoundaryPrescribedMotionRigidList(self):
        boundaryPrescribedMotionRigidList = [] 
        for i in range(len(self.parameters)):
            curBDPrescribedMotionRigid = []
            curBDPrescribedMotionRigid.append("*BOUNDARY_PRESCRIBED_MOTION_RIGID")
            curBDPrescribedMotionRigid.append(self.parameters[i][0])
            boundaryPrescribedMotionRigidList.append(curBDPrescribedMotionRigid)
        return boundaryPrescribedMotionRigidList               
            
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_PRESCRIBED_MOTION_RIGID\n")
            stream.write("$$  TYPEID       DOF       VAD      LCID        SF       VID     DEATH     BIRTH\n")
            for j in range(len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class BoundaryPrescribedMotionRigidID(DynaKeyword):
    def __init__(self):
        super(BoundaryPrescribedMotionRigidID,self).__init__("BOUNDARY_PRESCRIBED_MOTION_RIGID_ID")
    
    def parse(self, boundaryPrescribedMotionRigidKeywords):
        for i in range(len(boundaryPrescribedMotionRigidKeywords)):
            curParameter = boundaryPrescribedMotionRigidKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            parameters = self.parse_whole(curParameter[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def AddBoundaryPrescribedMotionRigidID(self, id, title, typeid, dof, vad, lcid, sf, vid, death, birth):
        parameterList = []
        parameterList.append([id, title])
        parameterList.append([typeid, dof, vad, lcid, sf, vid, death, birth])
        self.parameters.append(parameterList)  
        
    def getBoundaryPrescribedMotionRigidIDList(self):
        boundaryPrescribedMotionRigidList = [] 
        for i in range(len(self.parameters)):
            curBDPrescribedMotionRigid = []
            curBDPrescribedMotionRigid.append("*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID")
            curBDPrescribedMotionRigid.append(self.parameters[i][0])
            curBDPrescribedMotionRigid.append(self.parameters[i][1]) 
            boundaryPrescribedMotionRigidList.append(curBDPrescribedMotionRigid)
        return boundaryPrescribedMotionRigidList            
           
    
    def ID(self,ith):
        return self.parameters[ith][0][0]

    def HEADING(self,ith):
        return self.parameters[ith][0][1]

    def TYPEID(self,ith):
        return self.parameters[ith][1][0]
    
    def DOF(self,ith):
        return self.parameters[ith][1][1]
    
    def VAD(self,ith):
        return self.parameters[ith][1][2]
    
    def LCID(self,ith):
        return self.parameters[ith][1][3]
    
    def SF(self,ith):
        return self.parameters[ith][1][4]
    
    def VID(self,ith):
        return self.parameters[ith][1][5]
    
    def DEATH(self,ith):
        return self.parameters[ith][1][6]
    
    def BIRTH(self,ith):
        return self.parameters[ith][1][7]
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID\n")
            stream.write("$$      ID   HEADING\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[0]]
            result = ''.join(formatted_elements)            
            stream.write(result)
            stream.write("\n")
            stream.write("$$  TYPEID       DOF       VAD      LCID        SF       VID     DEATH     BIRTH\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[1]]
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")

class BoundaryPrescribedMotionSet(DynaKeyword):
    def __init__(self):
        super(BoundaryPrescribedMotionSet,self).__init__("BOUNDARY_PRESCRIBED_MOTION_SET")

    def parse(self, boundaryPrescribedMotionSetKeywords):
        for i in range(len(boundaryPrescribedMotionSetKeywords)):
            curParameter = boundaryPrescribedMotionSetKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_PRESCRIBED_MOTION_SET\n")
            stream.write("$$  TYPEID       DOF       VAD      LCID        SF       VID     DEATH     BIRTH\n")
            for j in range(len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class BoundaryPrescribedMotionSetID(DynaKeyword):
    def __init__(self):
        super(BoundaryPrescribedMotionSetID,self).__init__("BOUNDARY_PRESCRIBED_MOTION_SET_ID")
    
    def parse(self, boundaryPrescribedMotionSetKeywords):
        for i in range(len(boundaryPrescribedMotionSetKeywords)):
            curParameter = boundaryPrescribedMotionSetKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def write(self,stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_PRESCRIBED_MOTION_SET_ID\n")
            stream.write("$$      ID                                                                 TITLE\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            stream.write("$$  TYPEID       DOF       VAD      LCID        SF       VID     DEATH     BIRTH\n")
            for j in range(1,len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                
class BoundaryPZEPOT(DynaKeyword):
    def __init__(self):
        super(BoundaryPZEPOT,self).__init__("BOUNDARY_PZEPOT")
        
    def parse(self, boundaryPZEPOTKeywords):
        for i in range(len(boundaryPZEPOTKeywords)):
            curParameter = boundaryPZEPOTKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10])        
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getBoundaryPZEPOTList(self):
        boundaryPZEPOTList = []
        for i in range(len(self.parameters)):
            curBoundaryPZEPOT = []
            curBoundaryPZEPOT.append("*BOUNDARY_PZEPOT")
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curBoundaryPZEPOT.append(curParameter[j])
            boundaryPZEPOTList.append(curBoundaryPZEPOT)
        return boundaryPZEPOTList

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_PZEPOT\n")
            stream.write("$$      ID      NSID      LCID        SF\n")
            for j in range(len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")                    

class BoundarySPCNode(DynaKeyword):
    def __init__(self):
        super(BoundarySPCNode,self).__init__("BOUNDARY_SPC_NODE")

    def parse(self, boundarySPCNodeKeywords):
        for i in range(len(boundarySPCNodeKeywords)):
            curParameter = boundarySPCNodeKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getBoundarySpcNodeList(self):
        boundarySpcNodeList = []        
        for i in range(len(self.parameters)):
            curBoundarySpcNode = []
            curBoundarySpcNode.append("*BOUNDARY_SPC_NODE")
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curBoundarySpcNode.append(curParameter[j])
            boundarySpcNodeList.append(curBoundarySpcNode)
        return boundarySpcNodeList            
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_SPC_NODE\n")
            stream.write("$$    NSID       CID      DOFX      DOFY      DOFZ     DOFRX     DOFRY     DOFRZ\n")
            for j in range(len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class BoundarySPCNodeID(DynaKeyword):
    def __init__(self):
        super(BoundarySPCNodeID,self).__init__("BOUNDARY_SPC_NODE_ID")
    
    def parse(self, boundarySPCNodeKeywords):
        for i in range(len(boundarySPCNodeKeywords)):
            curParameter = boundarySPCNodeKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10,70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getBoundarySpcNodeIDList(self):
        boundarySpcNodeIDList = []        
        for i in range(len(self.parameters)):
            curBoundarySpcNodeID = []
            curBoundarySpcNodeID.append("*BOUNDARY_SPC_NODE_ID")            
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curBoundarySpcNodeID.append(curParameter[j])
            boundarySpcNodeIDList.append(curBoundarySpcNodeID)
        return boundarySpcNodeIDList   
        
    def write(self,stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_SPC_NODE_ID\n")
            stream.write("$$      ID                                                                 TITLE\n")
            #ID and TITLE
            formatted_elements = f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            stream.write("$$     NID       CID      DOFX      DOFY      DOFZ     DOFRX     DOFRY     DOFRZ\n")
            for j in range(1,len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class BoundarySPCSet(DynaKeyword):
    def __init__(self):
        super(BoundarySPCSet,self).__init__("BOUNDARY_SPC_SET")
    
    def parse(self, boundarySPCSetKeywords):
        for i in range(len(boundarySPCSetKeywords)):
            curParameter = boundarySPCSetKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)            
    
    def AddBoundarySPCSet(self, nsid, cid, dofx, dofy, dofz, dofrx, dofry, dofrz):
        parameterList = []
        parameterList.append([nsid, cid, dofx, dofy, dofz, dofrx, dofry, dofrz])
        self.parameters.append(parameterList)

    def AddBoundarySPCSetList(self, nsidList, cidList, dofxList, dofyList, dofzList, dofrxList, dofryList, dofrzList):        
        parameterList = []
        for i in range(len(nsidList)):
            parameterList.append([nsidList[i], cidList[i], dofxList[i], dofyList[i], dofzList[i], dofrxList[i], dofryList[i], dofrzList[i]])
        self.parameters.append(parameterList)
        
    def getBoundarySpcSetList(self):
        boundarySpcSetList = []
        for i in range(len(self.parameters)):
            curBoundarySpcSet = []
            curBoundarySpcSet.append("*BOUNDARY_SPC_SET")
            curParameter = self.parameters[i]
            curBoundarySpcSet.append(curParameter[0])
            boundarySpcSetList.append(curBoundarySpcSet)
        return boundarySpcSetList

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_SPC_SET\n")            
            stream.write("$$    NSID       CID      DOFX      DOFY      DOFZ     DOFRX     DOFRY     DOFRZ\n")
            for j in range(0,len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class BoundarySPCSetID(DynaKeyword):
    def __init__(self):
        super(BoundarySPCSetID,self).__init__("BOUNDARY_SPC_SET_ID")
    
    def parse(self, boundarySPCSetKeywords):
        for i in range(len(boundarySPCSetKeywords)):
            curParameter = boundarySPCSetKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddBoundarySPCSetID(self, bsid, bsTitle, nsid, cid, dofx, dofy, dofz, dofrx, dofry, dofrz):
        parameterList = []
        parameterList.append([bsid, bsTitle])
        parameterList.append([nsid, cid, dofx, dofy, dofz, dofrx, dofry, dofrz])
        self.parameters.append(parameterList)
    
    def AddBoundarySPCSetIDList(self, bsid, bsTitle, nsidList, cidList, dofxList, dofyList, dofzList, dofrxList, dofryList, dofrzList):
        parameterList = []
        parameterList.append([bsid, bsTitle])
        for i in range(len(nsidList)):
            parameterList.append([nsidList[i], cidList[i], dofxList[i], dofyList[i], dofzList[i], dofrxList[i], dofryList[i], dofrzList[i]])
        self.parameters.append(parameterList)
    
    def getBoundarySpcSetIDList(self):
        boundarySpcSetIDList = []
        for i in range(len(self.parameters)):
            curBoundarySpcSetID = []
            curBoundarySpcSetID.append("*BOUNDARY_SPC_SET_ID")
            curParameter = self.parameters[i]
            curBoundarySpcSetID.append(curParameter[0])
            curBoundarySpcSetID.append(curParameter[1])
            boundarySpcSetIDList.append(curBoundarySpcSetID)
        return boundarySpcSetIDList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*BOUNDARY_SPC_SET_ID\n")
            stream.write("$$      ID                                                               HEADING\n")
            fe1 = f"{str(curParameter[0][0]):>10}"
            fe2 = f"{str(curParameter[0][1]):<70}"
            result = fe1 + fe2            
            stream.write(result)
            stream.write("\n")
            stream.write("$$    NSID       CID      DOFX      DOFY      DOFZ     DOFRX     DOFRY     DOFRZ\n")
            for j in range(1,len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ConstrainedJointSpherical(DynaKeyword):
    def __init__(self):
        super(ConstrainedJointSpherical,self).__init__("CONSTRAINED_JOINT_SPHERICAL")
    
    def parse(self, constrainedJointSphericalKeywords):
        for i in range(len(constrainedJointSphericalKeywords)):
            curParameter = constrainedJointSphericalKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getConstrainedJointSphericalList(self):
        constrainedJointSphericalList = []
        for i in range(len(self.parameters)):
            curConstrainedJointSpherical = []
            curConstrainedJointSpherical.append("*CONSTRAINED_JOINT_SPHERICAL")
            curParameter = self.parameters[i]
            curConstrainedJointSpherical.append(curParameter[0])
            constrainedJointSphericalList.append(curConstrainedJointSpherical)
        return constrainedJointSphericalList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_JOINT_SPHERICAL\n")
            stream.write("$$      N1        N2        N3        N4        N5        N6       RPS      DAMP\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[0]]
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")
            
class ConstrainedJointSphericalID(DynaKeyword):
    def __init__(self):
        super(ConstrainedJointSphericalID,self).__init__("CONSTRAINED_JOINT_SPHERICAL_ID")

    def parse(self, constrainedJointSphericalKeywords):
        for i in range(len(constrainedJointSphericalKeywords)):
            curParameter = constrainedJointSphericalKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            parameters = self.parse_whole(curParameter[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getConstrainedJointSphericalIDList(self):
        constrainedJointSphericalIDList = []
        for i in range(len(self.parameters)):
            curConstrainedJointSphericalID = []
            curConstrainedJointSphericalID.append("*CONSTRAINED_JOINT_SPHERICAL_ID")
            curParameter = self.parameters[i]
            curConstrainedJointSphericalID.append(curParameter[0])
            curConstrainedJointSphericalID.append(curParameter[1])
            constrainedJointSphericalIDList.append(curConstrainedJointSphericalID)
        return constrainedJointSphericalIDList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_JOINT_SPHERICAL_ID\n")
            stream.write("$$      ID                                                               TITLE\n")
            formatted_elements = f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            stream.write("$$      N1        N2        N3        N4        N5        N6       RPS      DAMP\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[1]]
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")
    


class ConstrainedNodalRigidBody(DynaKeyword):
    def __init__(self):
        super(ConstrainedNodalRigidBody,self).__init__("CONSTRAINED_NODAL_RIGID_BODY")

    def parse(self, constrainedNodalRigidBodyKeywords):
        for i in range(len(constrainedNodalRigidBodyKeywords)):
            curParameter = constrainedNodalRigidBodyKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getConstrainedNodalRigidBodyList(self):
        constrainedNodalRigidBodyList = []
        for i in range(len(self.parameters)):
            curConstrainedNodalRigidBody = []
            curConstrainedNodalRigidBody.append("*CONSTRAINED_NODAL_RIGID_BODY")
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curConstrainedNodalRigidBody.append(curParameter[j])
            constrainedNodalRigidBodyList.append(curConstrainedNodalRigidBody)
        return constrainedNodalRigidBodyList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_NODAL_RIGID_BODY\n")
            stream.write("$$     PID       CID      NSID     PNODE      IPRT    DRFLAG    RRFLAG\n")
            for j in range(len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")            

class ConstrainedNodalRigidBodyTitle(DynaKeyword):
    def __init__(self):
        super(ConstrainedNodalRigidBodyTitle,self).__init__("CONSTRAINED_NODAL_RIGID_BODY_TITLE")
    
    def parse(self, constrainedNodalRigidBodyKeywords): 
        for i in range(len(constrainedNodalRigidBodyKeywords)):
            curParameter = constrainedNodalRigidBodyKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [80])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getConstrainedNodalRigidBodyTitleList(self):
        constrainedNodalRigidBodyTitleList = []
        for i in range(len(self.parameters)):
            curConstrainedNodalRigidBodyTitle = []
            curConstrainedNodalRigidBodyTitle.append("*CONSTRAINED_NODAL_RIGID_BODY_TITLE")
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curConstrainedNodalRigidBodyTitle.append(curParameter[j])
            constrainedNodalRigidBodyTitleList.append(curConstrainedNodalRigidBodyTitle)            
        return constrainedNodalRigidBodyTitleList
            
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_NODAL_RIGID_BODY_TITLE\n")
            stream.write("$$                                                                 TITLE\n")
            formatted_elements = f"{str(curParameter[0][0]):<80}\n"
            stream.write(formatted_elements)
            stream.write("$$     PID       CID      NSID     PNODE      IPRT    DRFLAG    RRFLAG\n")                                
            for j in range(1,len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ConstrainedExtraNodesNode(DynaKeyword):
    def __init__(self):
        super(ConstrainedExtraNodesNode,self).__init__("CONSTRAINED_EXTRA_NODES_NODE")
    
    def parse(self, constrainedExtraNodesNodeKeywords):
        for i in range(len(constrainedExtraNodesNodeKeywords)):
            curParameter = constrainedExtraNodesNodeKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddConstrainedExtraNodesNode(self, pid, nid, iflag):
        parameterList = []
        parameterList.append([pid, nid, iflag])
        self.parameters.append(parameterList)
    
    def getConstrainedExtraNodesNodeList(self):
        constrainedExtraNodesNodeList = []
        for i in range(len(self.parameters)):
            curConstrainedExtraNodesNode = []
            curConstrainedExtraNodesNode.append("*CONSTRAINED_EXTRA_NODES_NODE")
            curParameter = self.parameters[i]
            curConstrainedExtraNodesNode.append(curParameter[0])
            constrainedExtraNodesNodeList.append(curConstrainedExtraNodesNode)
        return constrainedExtraNodesNodeList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_EXTRA_NODES_NODE\n")
            stream.write("$$     PID       NID     IFLAG\n")

            for j in range(len(curParameter)):

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ConstrainedExtraNodesSet(DynaKeyword):
    def __init__(self):
        super(ConstrainedExtraNodesSet,self).__init__("CONSTRAINED_EXTRA_NODES_SET")
    
    def parse(self, constrainedExtraNodesSetKeywords):
        for i in range(len(constrainedExtraNodesSetKeywords)):
            curParameter = constrainedExtraNodesSetKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddConstrainedExtraNodesSet(self, pid, nsid, iflag):
        parameterList = []
        parameterList.append([pid, nsid, iflag])
        self.parameters.append(parameterList)
    
    def getConstrainedExtraNodesSetList(self):
        constrainedExtraNodesSetList = []
        for i in range(len(self.parameters)):
            curConstrainedExtraNodesSet = []
            curConstrainedExtraNodesSet.append("*CONSTRAINED_EXTRA_NODES_SET")
            curParameter = self.parameters[i]
            curConstrainedExtraNodesSet.append(curParameter[0])
            constrainedExtraNodesSetList.append(curConstrainedExtraNodesSet)
        return constrainedExtraNodesSetList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_EXTRA_NODES_SET\n")
            stream.write("$$     PID      NSID     IFLAG\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[0]]
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")

class ConstrainedNodeSet(DynaKeyword):
    def __init__(self):
        super(ConstrainedNodeSet,self).__init__("CONSTRAINED_NODE_SET")
    
    def parse(self, constrainedNodeSetKeywords):
        for i in range(len(constrainedNodeSetKeywords)):
            curParameter = constrainedNodeSetKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddConstrainedNodeSet(self, nsid, dof, tf):
        parameterList = []
        parameterList.append([nsid, dof, tf])
        self.parameters.append(parameterList)
        
    def getConstrainedNodeSetList(self):
        constrainedNodeSetList = []
        for i in range(len(self.parameters)):
            curConstrainedNodeSet = []
            curConstrainedNodeSet.append("*CONSTRAINED_NODE_SET")
            curParameter = self.parameters[i]
            curConstrainedNodeSet.append(curParameter[0])
            constrainedNodeSetList.append(curConstrainedNodeSet)
        return constrainedNodeSetList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_NODE_SET\n")
            stream.write("$$    NSID       DOF        TF\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[0]]
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")

class ConstrainedNodeSetID(DynaKeyword):
    def __init__(self):
        super(ConstrainedNodeSetID,self).__init__("CONSTRAINED_NODE_SET_ID")
    
    def parse(self, constrainedNodeSetKeywords):
        for i in range(len(constrainedNodeSetKeywords)):
            curParameter = constrainedNodeSetKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curParameter[1], [10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getConstrainedNodeSetIDList(self):
        constrainedNodeSetIDList = []
        for i in range(len(self.parameters)):
            curConstrainedNodeSetID = []
            curConstrainedNodeSetID.append("*CONSTRAINED_NODE_SET_ID")
            curParameter = self.parameters[i]
            curConstrainedNodeSetID.append(curParameter[0])
            curConstrainedNodeSetID.append(curParameter[1])
            constrainedNodeSetIDList.append(curConstrainedNodeSetID)
        return constrainedNodeSetIDList
        
    def AddConstrainedNodeSetID(self, cid, nsid, dof, tf):
        parameterList = []
        parameterList.append([cid])
        parameterList.append([nsid, dof, tf])
        self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_NODE_SET_ID\n")
            stream.write("$$      ID\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[0]]
            result = ''.join(formatted_elements)            
            stream.write(result)
            stream.write("\n")
            stream.write("$$    NSID       DOF        TF\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[1]]
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")

# RBE3
class ConstrainedInterpolation(DynaKeyword):
    def __init__(self):
        super(ConstrainedInterpolation,self).__init__("CONSTRAINED_INTERPOLATION")

    def parse(self, constrainedInterpolationKeywords):
        for i in range(len(constrainedInterpolationKeywords)):
            curParameter = constrainedInterpolationKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def AddConstrainedInterpolation(self, icid, dnid, ddof, cidd, ityp, idnsw, fgm, inidList, idofList, twghtXList="", twghtYList="", twghtZList="", rwghtXList="", rwghtYList="", rwghtZList=""):
        parameterList = []
        parameterList.append([icid, dnid, ddof, cidd, ityp, idnsw, fgm])
        for i in range(len(inidList)):
            curinid = 0
            if len(inidList)-1>=i:
                curinid = inidList[i]
            curidof = 0
            if len(idofList)-1>=i:
                curidof = idofList[i]
            curtwghtX = ""
            if len(twghtXList)-1>=i:
                curtwghtX = twghtXList[i]
            curtwghtY = ""
            if len(twghtYList)-1>=i:
                curtwghtY = twghtYList[i]
            curtwghtZ = ""
            if len(twghtZList)-1>=i:
                curtwghtZ = twghtZList[i]
            currwghtX = ""
            if len(rwghtXList)-1>=i:
                currwghtX = rwghtXList[i]
            currwghtY = ""
            if len(rwghtYList)-1>=i:
                currwghtY = rwghtYList[i]
            currwghtZ = ""
            if len(rwghtZList)-1>=i:
                currwghtZ = rwghtZList[i]
            parameterList.append([curinid, curidof, curtwghtX, curtwghtY, curtwghtZ, currwghtX, currwghtY, currwghtZ])
        self.parameters.append(parameterList)      
        
    def getConstrainedInterpolationList(self):
        constrainedInterpolationList = []
        for i in range(len(self.parameters)):
            curConstrainedInterpolation = []
            curConstrainedInterpolation.append("*CONSTRAINED_INTERPOLATION")
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curConstrainedInterpolation.append(curParameter[j])
            constrainedInterpolationList.append(curConstrainedInterpolation)
        return constrainedInterpolationList  
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_INTERPOLATION\n")
            stream.write("$$    ICID      DNID      DDOF      CIDD      ITYP     IDNSW       FGM\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[0]]
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")
            stream.write("$$    INID      IDOF    TWGHTX    TWGHTY    TWGHTZ    RWGHTX    RWGHTY    RWGHTZ\n")
                    
            for j in range(1,len(curParameter)):                
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                
class ConstrainedRigidBodies(DynaKeyword):
    def __init__(self):
        super(ConstrainedRigidBodies,self).__init__("CONSTRAINED_RIGID_BODIES")
        
    def parse(self, constrainedRigidBodiesKeywords):
        for i in range(len(constrainedRigidBodiesKeywords)):
            curParameter = constrainedRigidBodiesKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10])
                
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddConstrainedRigidBodies(self, pidls, pidcs, iflags):
        parameterList = []
        for i in range(len(pidls)):
            curpidl = pidls[i]
            curpidc = pidcs[i]
            curiflag = iflags[i]
            parameterList.append([curpidl, curpidc, curiflag])
            
        self.parameters.append(parameterList)
        
            
    def getConstrainedRigidBodiesList(self):
        constrainedRigidBodiesList = []
        for i in range(len(self.parameters)):
            curConstrainedRigidBodies = []
            curConstrainedRigidBodies.append("*CONSTRAINED_RIGID_BODIES")
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curConstrainedRigidBodies.append(curParameter[j])
            constrainedRigidBodiesList.append(curConstrainedRigidBodies)
        return constrainedRigidBodiesList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_RIGID_BODIES\n")
            stream.write("$$    PIDL      PIDC     IFLAG\n")   
            for j in range(len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                
class ConstrainedRigidBodiesSet(DynaKeyword):
    def __init__(self):
        super(ConstrainedRigidBodiesSet,self).__init__("CONSTRAINED_RIGID_BODIES_SET")
        
    def parse(self, constrainedRigidBodiesSetKeywords):
        for i in range(len(constrainedRigidBodiesSetKeywords)):
            curParameter = constrainedRigidBodiesSetKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddConstrainedRigidBodiesSet(self, pidls, pidcs, iflags):
        parameterList = []
        for i in range(len(pidls)):
            curpidl = pidls[i]
            curpidc = pidcs[i]
            curiflag = iflags[i]
            parameterList.append([curpidl, curpidc, curiflag])
        self.parameters.append(parameterList)
        
    def getConstrainedRigidBodiesSetList(self):
        constrainedRigidBodiesSetList = []
        for i in range(len(self.parameters)):
            curConstrainedRigidBodiesSet = []
            curConstrainedRigidBodiesSet.append("*CONSTRAINED_RIGID_BODIES_SET")
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curConstrainedRigidBodiesSet.append(curParameter[j])
            constrainedRigidBodiesSetList.append(curConstrainedRigidBodiesSet)
        return constrainedRigidBodiesSetList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONSTRAINED_RIGID_BODIES_SET\n")
            stream.write("$$    PIDL      PIDC     IFLAG\n")
            for j in range(len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                         
            
class ContactAddWear(DynaKeyword):
    def __init__(self):
        super(ContactAddWear,self).__init__("CONTACT_ADD_WEAR") 
    
    def parse(self, contactAddWearKeywords):
        for i in range(len(contactAddWearKeywords)):
            curParameter = contactAddWearKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getContactAddWearList(self):
        contactAddWearList = []
        for i in range(len(self.parameters)):
            curContactAddWear = []
            curContactAddWear.append("*CONTACT_ADD_WEAR")
            curParameter = self.parameters[i]
            for j in range(len(curParameter)):
                curContactAddWear.append(curParameter[j])
            contactAddWearList.append(curContactAddWear)
        return contactAddWearList    
            
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ADD_WEAR\n")
            stream.write("$$     CID     WTYPE        P1        P2        P3        P4        P5        P6\n")
            for j in range(len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
            stream.write("\n")                
                                 

class ContactAutomaticSingleSurface(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticSingleSurface,self).__init__("CONTACT_AUTOMATIC_SINGLE_SURFACE")

    def parse(self, contactAutomaticSingleSurfaceKeywords):
        for i in range(len(contactAutomaticSingleSurfaceKeywords)):
            curParameter = contactAutomaticSingleSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getAutomaticSingleSurfaceList(self):
        automaticSingleSurfaceList = []
        for i in range(len(self.parameters)):
            curAutomaticSingleSurface = []
            curAutomaticSingleSurface.append("*CONTACT_AUTOMATIC_SINGLE_SURFACE")
            parameter = self.parameters[i]
            curAutomaticSingleSurface.append(parameter[0])
            curAutomaticSingleSurface.append(parameter[1])
            curAutomaticSingleSurface.append(parameter[2])
            automaticSingleSurfaceList.append(curAutomaticSingleSurface)
        return automaticSingleSurfaceList
                

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_SINGLE_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactAutomaticSingleSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticSingleSurfaceID,self).__init__("CONTACT_AUTOMATIC_SINGLE_SURFACE_ID")
    
    def parse(self, contactAutomaticSingleSurfaceKeywords):
        for i in range(len(contactAutomaticSingleSurfaceKeywords)):
            curParameter = contactAutomaticSingleSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getAutomaticSingleSurfaceIDList(self):
        automaticSingleSurfaceList = []
        for i in range(len(self.parameters)):
            curAutomaticSingleSurface = []
            curAutomaticSingleSurface.append("*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID")
            parameter = self.parameters[i]
            curAutomaticSingleSurface.append(parameter[0])
            curAutomaticSingleSurface.append(parameter[1])
            curAutomaticSingleSurface.append(parameter[2])
            curAutomaticSingleSurface.append(parameter[3])
            automaticSingleSurfaceList.append(curAutomaticSingleSurface)
        return automaticSingleSurfaceList
    
    def AddAutomaticSingleSurfaceID(self, id, name, ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr, fs, fd, dc, vc, vdc, penchk, bt, dt, sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf):
        parameterList = [] 
        parameterList.append([id, name])        
        parameterList.append([ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr])
        parameterList.append([fs, fd, dc, vc, vdc, penchk, bt, dt])
        parameterList.append([sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf])
        self.parameters.append(parameterList)

        
    def write(self,stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactAutomaticSurfaceToSurface(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticSurfaceToSurface,self).__init__("CONTACT_AUTOMATIC_SURFACE_TO_SURFACE")

    def parse(self, contactAutomaticSurfaceToSurfaceKeywords):
        for i in range(len(contactAutomaticSurfaceToSurfaceKeywords)):
            curParameter = contactAutomaticSurfaceToSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getAutomaticSurfacetoSurfaceList(self):
        automaticSurfacetoSurfaceList = []
        for i in range(len(self.parameters)):
            curAutomaticSurfacetoSurface = []
            curAutomaticSurfacetoSurface.append("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE")
            parameter = self.parameters[i]
            curAutomaticSurfacetoSurface.append(parameter[0])
            curAutomaticSurfacetoSurface.append(parameter[1])
            curAutomaticSurfacetoSurface.append(parameter[2])
            automaticSurfacetoSurfaceList.append(curAutomaticSurfacetoSurface)
        return automaticSurfacetoSurfaceList
    

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactAutomaticSurfaceToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticSurfaceToSurfaceID,self).__init__("CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID")
    
    def parse(self, contactAutomaticSurfaceToSurfaceKeywords):
        for i in range(len(contactAutomaticSurfaceToSurfaceKeywords)):
            curParameter = contactAutomaticSurfaceToSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddAutomaticSurfacetoSurfaceID(self, id, name, ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr, fs, fd, dc, vc, vdc, penchk, bt, dt, sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf):
        parameterList = [] 
        parameterList.append([id, name])        
        parameterList.append([ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr])
        parameterList.append([fs, fd, dc, vc, vdc, penchk, bt, dt])
        parameterList.append([sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf])
        self.parameters.append(parameterList)
        
    def getAutomaticSurfacetoSurfaceIDList(self):
        automaticSurfacetoSurfaceList = []
        for i in range(len(self.parameters)):
            curAutomaticSurfacetoSurface = []
            curAutomaticSurfacetoSurface.append("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID")
            parameter = self.parameters[i]
            curAutomaticSurfacetoSurface.append(parameter[0])
            curAutomaticSurfacetoSurface.append(parameter[1])
            curAutomaticSurfacetoSurface.append(parameter[2])
            curAutomaticSurfacetoSurface.append(parameter[3])
            automaticSurfacetoSurfaceList.append(curAutomaticSurfacetoSurface)
        return automaticSurfacetoSurfaceList
        
    def write(self,stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                
class ContactAutomaticSurfaceToSurfaceOffset(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticSurfaceToSurfaceOffset,self).__init__("CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET")
    
    def parse(self, contactAutomaticSurfaceToSurfaceOffsetKeywords):
        for i in range(len(contactAutomaticSurfaceToSurfaceOffsetKeywords)):
            curParameter = contactAutomaticSurfaceToSurfaceOffsetKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactAutomaticSurfaceToSurfaceOffsetID(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticSurfaceToSurfaceOffsetID,self).__init__("CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET_ID")

    def parse(self, contactAutomaticSurfaceToSurfaceOffsetKeywords):
        for i in range(len(contactAutomaticSurfaceToSurfaceOffsetKeywords)):
            curParameter = contactAutomaticSurfaceToSurfaceOffsetKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddAutomaticSurfacetoSurfaceOffsetID(self, id, name, ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr, fs, fd, dc, vc, vdc, penchk, bt, dt, sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf):
        parameterList = []  
        parameterList.append([id, name])
        parameterList.append([ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr])
        parameterList.append([fs, fd, dc, vc, vdc, penchk, bt, dt])
        parameterList.append([sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf])
        self.parameters.append(parameterList)

    def write(self,stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")                                

class ContactAutomaticGeneral(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticGeneral,self).__init__("CONTACT_AUTOMATIC_GENERAL")
        
    def parse(self, contactAutomaticGeneralKeywords):
        for i in range(len(contactAutomaticGeneralKeywords)):
            curParameter = contactAutomaticGeneralKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getAutomaticGeneralList(self):
        automaticGeneralList = []
        for i in range(len(self.parameters)):
            curAutomaticGeneral = []
            curAutomaticGeneral.append("*CONTACT_AUTOMATIC_GENERAL")    
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                curAutomaticGeneral.append(parameter[j])
            automaticGeneralList.append(curAutomaticGeneral)
        return automaticGeneralList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_GENERAL\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 3:
                    stream.write("$$    SOFT    SOFSCL    LCIDAB    MAXPAR     SBOPT     DEPTH     BSORT    FRCFRQ\n")
                elif j == 4:
                    stream.write("$$  PENMAX    THKOPT    SHLTHK     SNLOG      ISYM     I2D3D    SLDTHK    SLDSTF\n")
                elif j == 5:
                    stream.write("$$    IGAP    IGNORE    DPRFAC    DTSTIF                        FLANGL   CID_RCF\n")
                elif j == 6:
                    stream.write("$$   Q2TRI    DTPCHK     SFNBR    FNLSCL    DNLSCL      TCSO    TIEDID    SHLEDG\n")
                elif j == 7:
                    stream.write("$$  SHAREC    CPARM8    IPBACK     SRNDE    FRICSF      ICOR     FTORQ    REGION\n")
                elif j == 8:
                    stream.write("$$  PSTIFF   IGNROFF     FSTOL   TWODBNR    SSFTYP     SWTPR    TETFAC\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactAutomaticGeneralID(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticGeneralID,self).__init__("CONTACT_AUTOMATIC_GENERAL_ID")
        
    def parse(self, contactAutomaticGeneralKeywords):
        for i in range(len(contactAutomaticGeneralKeywords)):
            curParameter = contactAutomaticGeneralKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)

            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getAutomaticGeneralIDList(self):
        automaticGeneralList = []
        for i in range(len(self.parameters)):
            curAutomaticGeneral = []
            curAutomaticGeneral.append("*CONTACT_AUTOMATIC_GENERAL_ID")
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                curAutomaticGeneral.append(parameter[j])
            automaticGeneralList.append(curAutomaticGeneral)
        return automaticGeneralList
    
    def AddContactAutomaticGeneralID(self, id, name, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[id, name], [SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])


    def CID(self,ith):
        return self.parameters[ith][0][0]
    
    def TITLE(self,ith):
        return self.parameters[ith][0][1]
    
    def SSID(self,ith):
        return self.parameters[ith][1][0]
    
    def MSID(self,ith):
        return self.parameters[ith][1][1]
    
    def SSTYP(self,ith):
        return self.parameters[ith][1][2]
    
    def MSTYP(self,ith):
        return self.parameters[ith][1][3]
    
    def SBOXID(self,ith):
        return self.parameters[ith][1][4]
    
    def MBOXID(self,ith):
        return self.parameters[ith][1][5]
    
    def SPR(self,ith):
        return self.parameters[ith][1][6]
    
    def MPR(self,ith):
        return self.parameters[ith][1][7]
    
    def FS(self,ith):
        return self.parameters[ith][2][0]
    
    def FD(self,ith):
        return self.parameters[ith][2][1]
    
    def DC(self,ith):
        return self.parameters[ith][2][2]
    
    def VC(self,ith):
        return self.parameters[ith][2][3]
    
    def VDC(self,ith):
        return self.parameters[ith][2][4]
    
    def PENCHK(self,ith):
        return self.parameters[ith][2][5]
    
    def BT(self,ith):
        return self.parameters[ith][2][6]
    
    def DT(self,ith):
        return self.parameters[ith][2][7]
    
    def SFS(self,ith):
        return self.parameters[ith][3][0]
    
    def SFM(self,ith):
        return self.parameters[ith][3][1]
    
    def SST(self,ith):
        return self.parameters[ith][3][2]
    
    def MST(self,ith):
        return self.parameters[ith][3][3]
    
    def SFST(self,ith):
        return self.parameters[ith][3][4]
    
    def SFMT(self,ith):
        return self.parameters[ith][3][5]

    def FSF(self,ith):
        return self.parameters[ith][3][6]
    
    def VSF(self,ith):
        return self.parameters[ith][3][7]
    
    def SOFT(self,ith):
        return self.parameters[ith][4][0]
    
    def SOFSCL(self,ith):
        return self.parameters[ith][4][1]

    def LCIDAB(self,ith):
        return self.parameters[ith][4][2]
    
    def MAXPAR(self,ith):
        return self.parameters[ith][4][3]
    
    def SBOPT(self,ith):
        return self.parameters[ith][4][4]
    
    def DEPTH(self,ith):
        return self.parameters[ith][4][5]
    
    def BSORT(self,ith):
        return self.parameters[ith][4][6]
    
    def FRCFRQ(self,ith):
        return self.parameters[ith][4][7]
    
    def PENMAX(self,ith):
        return self.parameters[ith][5][0]
    
    def THKOPT(self,ith):
        return self.parameters[ith][5][1]
    
    def SHLTHK(self,ith):
        return self.parameters[ith][5][2]
    
    def SNLOG(self,ith):
        return self.parameters[ith][5][3]

    def ISYM(self,ith):
        return self.parameters[ith][5][4]
    
    def I2D3D(self,ith):
        return self.parameters[ith][5][5]
    
    def SLDTHK(self,ith):
        return self.parameters[ith][5][6]
    
    def SLDSTF(self,ith):
        return self.parameters[ith][5][7]
    
    def IGAP(self,ith):
        return self.parameters[ith][6][0]
    
    def IGNORE(self,ith):
        return self.parameters[ith][6][1]
    
    def DPRFAC(self,ith):
        return self.parameters[ith][6][2]
    
    def DTSTIF(self,ith):
        return self.parameters[ith][6][3]
    
    def FLANGL(self,ith):
        return self.parameters[ith][6][6]
    
    def CID_RCF(self,ith):
        return self.parameters[ith][6][7]
    
    def Q2TRI(self,ith):
        return self.parameters[ith][7][0]
    
    def DTPCHK(self,ith):
        return self.parameters[ith][7][1]
    
    def SFNBR(self,ith):
        return self.parameters[ith][7][2]
    
    def FNLSCL(self,ith):
        return self.parameters[ith][7][3]
    
    def DNLSCL(self,ith):
        return self.parameters[ith][7][4]
    
    def TCSO(self,ith):
        return self.parameters[ith][7][5]
    
    def TIEDID(self,ith):
        return self.parameters[ith][7][6]

    def SHLEDG(self,ith):
        return self.parameters[ith][7][7]
    
    def SHAREC(self,ith):
        return self.parameters[ith][8][0]
    
    def CPARM8(self,ith):
        return self.parameters[ith][8][1]
    
    def IPBACK(self,ith):
        return self.parameters[ith][8][2]
    
    def SRNDE(self,ith):
        return self.parameters[ith][8][3]
    
    def FRICSF(self,ith):
        return self.parameters[ith][8][4]
    
    def ICOR(self,ith):
        return self.parameters[ith][8][5]
    
    def FTORQ(self,ith):
        return self.parameters[ith][8][6]
    
    def REGION(self,ith):
        return self.parameters[ith][8][7]
    
    def PSTIFF(self,ith):
        return self.parameters[ith][9][0]
    
    def IGNROFF(self,ith):
        return self.parameters[ith][9][1]
    
    def FSTOL(self,ith):
        return self.parameters[ith][9][3]
    
    def TWODBNR(self,ith):
        return self.parameters[ith][9][4]
    
    def SSFTYP(self,ith):
        return self.parameters[ith][9][5]
    
    def SWTPR(self,ith):
        return self.parameters[ith][9][6]
    
    def TETFAC(self,ith):
        return self.parameters[ith][9][7]
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_GENERAL_ID\n")
            stream.write("$$     CID     TITLE\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[0]]
            result = ''.join(formatted_elements)            
            stream.write(result)
            stream.write("\n")            
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 4:
                    stream.write("$$    SOFT    SOFSCL    LCIDAB    MAXPAR     SBOPT     DEPTH     BSORT    FRCFRQ\n")
                elif j == 5:
                    stream.write("$$  PENMAX    THKOPT    SHLTHK     SNLOG      ISYM     I2D3D    SLDTHK    SLDSTF\n")
                elif j == 6:
                    stream.write("$$    IGAP    IGNORE    DPRFAC    DTSTIF                        FLANGL   CID_RCF\n")
                elif j == 7:
                    stream.write("$$   Q2TRI    DTPCHK     SFNBR    FNLSCL    DNLSCL      TCSO    TIEDID    SHLEDG\n")
                elif j == 8:
                    stream.write("$$  SHAREC    CPARM8    IPBACK     SRNDE    FRICSF      ICOR     FTORQ    REGION\n")
                elif j == 9:
                    stream.write("$$  PSTIFF   IGNROFF     FSTOL   TWODBNR    SSFTYP     SWTPR    TETFAC\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactAutomaticNodesToSurface(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticNodesToSurface,self).__init__("CONTACT_AUTOMATIC_NODES_TO_SURFACE")
    
    def parse(self, contactAutomaticNodesToSurfaceKeywords):
        for i in range(len(contactAutomaticNodesToSurfaceKeywords)):
            curParameter = contactAutomaticNodesToSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_NODES_TO_SURFACE\n")            
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactAutomaticNodesToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactAutomaticNodesToSurfaceID,self).__init__("CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID")
    
    def parse(self, contactAutomaticNodesToSurfaceKeywords):
        for i in range(len(contactAutomaticNodesToSurfaceKeywords)):
            curParameter = contactAutomaticNodesToSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactFEMPERITieBreakID(DynaKeyword):
    def __init__(self):
        super(ContactFEMPERITieBreakID,self).__init__("CONTACT_FEM_PERI_TIE_BREAK_ID")
    
    def parse(self, contactFEMPERITieBreakKeywords):
        for i in range(len(contactFEMPERITieBreakKeywords)):
            curParameter = contactFEMPERITieBreakKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 10, 10, 10, 10])
            self.parameters.append(parameters)
    
    def AddContactFEMPERITieBreakID(self, cid, msid, ssid, tensile, compressive):                                
        # 10.3e for float 
        tensile = "{:.3e}".format(tensile)
        compressive = "{:.3e}".format(compressive)
        parameterList = [cid, msid, ssid, tensile, compressive]
        self.parameters.append(parameterList)
        
    def getContactFEMPERITieBreakIDList(self):
        contactFEMPERITieBreakIDList = []
        for i in range(len(self.parameters)):
            curContactFEMPERITieBreakID = []
            curContactFEMPERITieBreakID.append("*CONTACT_FEM_PERI_TIE_BREAK_ID")
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                curContactFEMPERITieBreakID.append(parameter[j])
            contactFEMPERITieBreakIDList.append(curContactFEMPERITieBreakID)
        return contactFEMPERITieBreakIDList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_FEM_PERI_TIE_BREAK_ID\n")
            stream.write("$$     CID      MSID      SSID        FT        FC\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter]
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")
        
class ContactNodesToSurface(DynaKeyword):
    def __init__(self):
        super(ContactNodesToSurface,self).__init__("CONTACT_NODES_TO_SURFACE")
    
    def parse(self, contactNodesToSurfaceKeywords):
        for i in range(len(contactNodesToSurfaceKeywords)):
            curParameter = contactNodesToSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_NODES_TO_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 3:
                    stream.write("$$    SOFT    SOFSCL    LCIDAB    MAXPAR     SBOPT     DEPTH     BSORT    FRCFRQ\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactNodesToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactNodesToSurfaceID,self).__init__("CONTACT_NODES_TO_SURFACE_ID")
    
    def parse(self, contactNodesToSurfaceKeywords):
        for i in range(len(contactNodesToSurfaceKeywords)):
            curParameter = contactNodesToSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self,stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_NODES_TO_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 4:
                    stream.write("$$    SOFT    SOFSCL    LCIDAB    MAXPAR     SBOPT     DEPTH     BSORT    FRCFRQ\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactOneWaySurfaceToSurface(DynaKeyword):
    def __init__(self):
        super(ContactOneWaySurfaceToSurface,self).__init__("CONTACT_ONE_WAY_SURFACE_TO_SURFACE")
    
    def parse(self, contactOneWaySurfaceToSurfaceKeywords):
        for i in range(len(contactOneWaySurfaceToSurfaceKeywords)):
            curParameter = contactOneWaySurfaceToSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self,stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ONE_WAY_SURFACE_TO_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactOneWaySurfaceToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactOneWaySurfaceToSurfaceID,self).__init__("CONTACT_ONE_WAY_SURFACE_TO_SURFACE_ID")
    
    def parse(self, contactOneWaySurfaceToSurfaceKeywords):
        for i in range(len(contactOneWaySurfaceToSurfaceKeywords)):
            curParameter = contactOneWaySurfaceToSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self,stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ONE_WAY_SURFACE_TO_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactSingleSurface(DynaKeyword):
    def __init__(self):
        super(ContactSingleSurface,self).__init__("CONTACT_SINGLE_SURFACE")
    
    def parse(self, contactSingleSurfaceKeywords):
        for i in range(len(contactSingleSurfaceKeywords)):
            curParameter = contactSingleSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getContactSingleSurfaceList(self):
        currentSingleSurfaceList = []
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            curSingleSurface = []
            curSingleSurface.append("*CONTACT_SINGLE_SURFACE")
            for j in range(len(curParameter)):
                curSingleSurface.append(curParameter[j])
            currentSingleSurfaceList.append(curSingleSurface)
        return currentSingleSurfaceList                

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_SINGLE_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactSingleSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactSingleSurfaceID,self).__init__("CONTACT_SINGLE_SURFACE_ID")
    
    def parse(self, contactSingleSurfaceKeywords):
        for i in range(len(contactSingleSurfaceKeywords)):
            curParameter = contactSingleSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddContactSingleSurfaceID(self, id, name, ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr, fs, fd, dc, vc, vdc, penchk, bt, dt, sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf, soft):
        parameterList = []
        parameterList.append([id, name])
        parameterList.append([ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr])
        parameterList.append([fs, fd, dc, vc, vdc, penchk, bt, dt])
        parameterList.append([sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf])
        parameterList.append([soft])        
        self.parameters.append(parameterList)
        
    def getContactSingleSurfaceIDList(self):
        currentSingleSurfaceIDList = []
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            curSingleSurfaceID = []
            curSingleSurfaceID.append("*CONTACT_SINGLE_SURFACE_ID")
            for j in range(len(curParameter)):
                curSingleSurfaceID.append(curParameter[j])
            currentSingleSurfaceIDList.append(curSingleSurfaceID)
        return currentSingleSurfaceIDList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_SINGLE_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactSurfaceToSurface(DynaKeyword):
    def __init__(self):
        super(ContactSurfaceToSurface,self).__init__("CONTACT_SURFACE_TO_SURFACE")
    
    def parse(self, contactSurfaceToSurfaceKeywords):
        for i in range(len(contactSurfaceToSurfaceKeywords)):
            curParameter = contactSurfaceToSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_SURFACE_TO_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactSurfaceToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactSurfaceToSurfaceID,self).__init__("CONTACT_SURFACE_TO_SURFACE_ID")
    
    def parse(self, contactSurfaceToSurfaceKeywords):
        for i in range(len(contactSurfaceToSurfaceKeywords)):
            curParameter = contactSurfaceToSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self,stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_SURFACE_TO_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")               

class ContactSurfaceToSurfaceInterference(DynaKeyword):
    def __init__(self):
        super(ContactSurfaceToSurfaceInterference,self).__init__("CONTACT_SURFACE_TO_SURFACE_INTERFERENCE")
    
    def parse(self, contactSurfaceToSurfaceInterferenceKeywords):
        for i in range(len(contactSurfaceToSurfaceInterferenceKeywords)):
            curParameter = contactSurfaceToSurfaceInterferenceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_SURFACE_TO_SURFACE_INTERFERENCE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 3:
                    stream.write("$$   LCID1     LCID2\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactSurfaceToSurfaceInterferenceID(DynaKeyword):
    def __init__(self):
        super(ContactSurfaceToSurfaceInterferenceID,self).__init__("CONTACT_SURFACE_TO_SURFACE_INTERFERENCE_ID")
    
    def parse(self, contactSurfaceToSurfaceInterferenceKeywords):
        for i in range(len(contactSurfaceToSurfaceInterferenceKeywords)):
            curParameter = contactSurfaceToSurfaceInterferenceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_SURFACE_TO_SURFACE_INTERFERENCE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)

            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 4:
                    stream.write("$$   LCID1     LCID2\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactTiedNodesToSurface(DynaKeyword):
    def __init__(self):
        super(ContactTiedNodesToSurface,self).__init__("CONTACT_TIED_NODES_TO_SURFACE")
    
    def parse(self, contactTiedNodesToSurfaceKeywords):
        for i in range(len(contactTiedNodesToSurfaceKeywords)):
            curParameter = contactTiedNodesToSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_NODES_TO_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")    
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)                
                stream.write(result)
                stream.write("\n")

class ContactTiedNodesToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactTiedNodesToSurfaceID,self).__init__("CONTACT_TIED_NODES_TO_SURFACE_ID")
    
    def parse(self, contactTiedNodesToSurfaceKeywords):
        for i in range(len(contactTiedNodesToSurfaceKeywords)):
            curParameter = contactTiedNodesToSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_NODES_TO_SURFACE_ID\n")
            stream.write("$$     CID                                                                 TITLE\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)

            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")                    
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")                    
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")                    

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)                
                stream.write(result)
                stream.write("\n")

class ContactTiedShellEdgeToSurface(DynaKeyword):
    def __init__(self):
        super(ContactTiedShellEdgeToSurface,self).__init__("CONTACT_TIED_SHELL_EDGE_TO_SURFACE")

    def parse(self, contactTiedShellEdgeToSurfaceKeywords):
        for i in range(len(contactTiedShellEdgeToSurfaceKeywords)):
            curParameter = contactTiedShellEdgeToSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddContactTiedShellEdgeToSurface(self, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])        


    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SHELL_EDGE_TO_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")                    
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")                    
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")                    

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)                
                stream.write(result)
                stream.write("\n")

class ContactTiedShellEdgeToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactTiedShellEdgeToSurfaceID,self).__init__("CONTACT_TIED_SHELL_EDGE_TO_SURFACE_ID")
    
    def parse(self, contactTiedShellEdgeToSurfaceKeywords):
        for i in range(len(contactTiedShellEdgeToSurfaceKeywords)):
            curParameter = contactTiedShellEdgeToSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)

            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactTiedShellEdgeToSurfaceBeamOffset(DynaKeyword):
    def __init__(self):
        super(ContactTiedShellEdgeToSurfaceBeamOffset,self).__init__("CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET")
    
    def parse(self, contactTiedShellEdgeToSurfaceBeamOffsetKeywords):
        for i in range(len(contactTiedShellEdgeToSurfaceBeamOffsetKeywords)):
            curParameter = contactTiedShellEdgeToSurfaceBeamOffsetKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getContactTiedShellEdgeToSurfaceBeamOffsetList(self):
        currentTiedShellEdgeToSurfaceBeamOffsetList = []
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            curTiedShellEdgeToSurfaceBeamOffset = []
            curTiedShellEdgeToSurfaceBeamOffset.append("*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET")
            for j in range(len(curParameter)):
                curTiedShellEdgeToSurfaceBeamOffset.append(curParameter[j])
            currentTiedShellEdgeToSurfaceBeamOffsetList.append(curTiedShellEdgeToSurfaceBeamOffset)
        return currentTiedShellEdgeToSurfaceBeamOffsetList
    
    def AddContactTiedShellEdgeToSurfaceBeamOffset(self, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
    
class ContactTiedShellEdgeToSurfaceBeamOffsetID(DynaKeyword):
    def __init__(self):
        super(ContactTiedShellEdgeToSurfaceBeamOffsetID,self).__init__("CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID")

    def parse(self, contactTiedShellEdgeToSurfaceBeamOffsetKeywords):
        for i in range(len(contactTiedShellEdgeToSurfaceBeamOffsetKeywords)):
            curParameter = contactTiedShellEdgeToSurfaceBeamOffsetKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getContactTiedShellEdgeToSurfaceBeamOffsetIDList(self):
        currentTiedShellEdgeToSurfaceBeamOffsetIDList = []
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            curTiedShellEdgeToSurfaceBeamOffsetID = []
            curTiedShellEdgeToSurfaceBeamOffsetID.append("*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID")
            for j in range(len(curParameter)):
                curTiedShellEdgeToSurfaceBeamOffsetID.append(curParameter[j])
            currentTiedShellEdgeToSurfaceBeamOffsetIDList.append(curTiedShellEdgeToSurfaceBeamOffsetID)
        return currentTiedShellEdgeToSurfaceBeamOffsetIDList
        
    def AddContactTiedShellEdgeToSurfaceBeamOffsetID(self, id, name, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[id, name], [SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")                

class ContactTiedSurfaceToSurface(DynaKeyword):
    def __init__(self):
        super(ContactTiedSurfaceToSurface,self).__init__("CONTACT_TIED_SURFACE_TO_SURFACE")
    
    def parse(self, contactTiedSurfaceToSurfaceKeywords):
        for i in range(len(contactTiedSurfaceToSurfaceKeywords)):
            curParameter = contactTiedSurfaceToSurfaceKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getContactTiedSurfaceToSurfaceList(self):
        currentTiedSurfaceToSurfaceList = []
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            curTiedSurfaceToSurface = []
            curTiedSurfaceToSurface.append("*CONTACT_TIED_SURFACE_TO_SURFACE")
            for j in range(len(curParameter)):
                curTiedSurfaceToSurface.append(curParameter[j])
            currentTiedSurfaceToSurfaceList.append(curTiedSurfaceToSurface)
        return currentTiedSurfaceToSurfaceList                        

    def AddContactTiedSurfaceToSurface(self, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SURFACE_TO_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
    
class ContactTiedSurfaceToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactTiedSurfaceToSurfaceID,self).__init__("CONTACT_TIED_SURFACE_TO_SURFACE_ID")

    def parse(self, contactTiedSurfaceToSurfaceKeywords):
        for i in range(len(contactTiedSurfaceToSurfaceKeywords)):
            curParameter = contactTiedSurfaceToSurfaceKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getContactTiedSurfaceToSurfaceIDList(self):
        currentTiedSurfaceToSurfaceIDList = []
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            curTiedSurfaceToSurfaceID = []
            curTiedSurfaceToSurfaceID.append("*CONTACT_TIED_SURFACE_TO_SURFACE_ID")
            for j in range(len(curParameter)):
                curTiedSurfaceToSurfaceID.append(curParameter[j])
            currentTiedSurfaceToSurfaceIDList.append(curTiedSurfaceToSurfaceID)
        return currentTiedSurfaceToSurfaceIDList         
            
    def AddContactTiedSurfaceToSurfaceID(self, id, name, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[id, name], [SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SURFACE_TO_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")                

class ContactTiedSurfaceToSurfaceOffset(DynaKeyword):
    def __init__(self):
        super(ContactTiedSurfaceToSurfaceOffset,self).__init__("CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET")

    def parse(self, contactTiedSurfaceToSurfaceOffsetKeywords):
        for i in range(len(contactTiedSurfaceToSurfaceOffsetKeywords)):
            curParameter = contactTiedSurfaceToSurfaceOffsetKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddContactTiedSurfaceToSurfaceOffset(self, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])

    def getContactTiedSurfaceToSurfaceOffsetList(self):
        currentTiedSurfaceToSurfaceOffsetList = []
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            curTiedSurfaceToSurfaceOffset = []
            curTiedSurfaceToSurfaceOffset.append("*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET")
            for j in range(len(curParameter)):
                curTiedSurfaceToSurfaceOffset.append(curParameter[j])
            currentTiedSurfaceToSurfaceOffsetList.append(curTiedSurfaceToSurfaceOffset)
        return currentTiedSurfaceToSurfaceOffsetList


    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactTiedSurfaceToSurfaceOffsetID(DynaKeyword):
    def __init__(self):
        super(ContactTiedSurfaceToSurfaceOffsetID,self).__init__("CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID")

    def parse(self, contactTiedSurfaceToSurfaceOffsetKeywords):
        for i in range(len(contactTiedSurfaceToSurfaceOffsetKeywords)):            
            curParameter = contactTiedSurfaceToSurfaceOffsetKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddContactTiedSurfaceToSurfaceOffsetID(self, id, name, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[id, name], [SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])

    def getContactTiedSurfaceToSurfaceOffsetIDList(self):
        currentTiedSurfaceToSurfaceOffsetIDList = []
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            curTiedSurfaceToSurfaceOffsetID = []
            curTiedSurfaceToSurfaceOffsetID.append("*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID")
            for j in range(len(curParameter)):
                curTiedSurfaceToSurfaceOffsetID.append(curParameter[j])
            currentTiedSurfaceToSurfaceOffsetIDList.append(curTiedSurfaceToSurfaceOffsetID)
        return currentTiedSurfaceToSurfaceOffsetIDList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                
class ContactTiedSurfaceToSurfaceConstrainedOffset(DynaKeyword):
    def __init__(self):
        super(ContactTiedSurfaceToSurfaceConstrainedOffset,self).__init__("CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET")
    
    def parse(self, contactTiedSurfaceToSurfaceConstrainedOffsetKeywords):
        for i in range(len(contactTiedSurfaceToSurfaceConstrainedOffsetKeywords)):
            curParameter = contactTiedSurfaceToSurfaceConstrainedOffsetKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddContactTiedSurfaceToSurfaceConstrainedOffset(self, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                
class ContactTiedSurfaceToSurfaceConstrainedOffsetID(DynaKeyword):
    def __init__(self):
        super(ContactTiedSurfaceToSurfaceConstrainedOffsetID,self).__init__("CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID")
        
    def parse(self, contactTiedSurfaceToSurfaceConstrainedOffsetKeywords):
        for i in range(len(contactTiedSurfaceToSurfaceConstrainedOffsetKeywords)):
            curParameter = contactTiedSurfaceToSurfaceConstrainedOffsetKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddContactTiedSurfaceToSurfaceConstrainedOffsetID(self, id, name, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        self.parameters.append([[id, name], [SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR], [FS, FD, DC, VC, VDC, PENCHK, BT, DT], [SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF]])
                            
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID\n")    
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")                       
                    
class ContactErodingSingleSurface(DynaKeyword):
    def __init__(self):
        super(ContactErodingSingleSurface,self).__init__("CONTACT_ERODING_SINGLE_SURFACE")

    def parse(self, contactErodingSingleSurfaceKeywords):
        for i in range(len(contactErodingSingleSurfaceKeywords)):
            curParameter = contactErodingSingleSurfaceKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ERODING_SINGLE_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 3:
                    stream.write("$$     SYM     EROSOP      IADJ\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactErodingSingleSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactErodingSingleSurfaceID,self).__init__("CONTACT_ERODING_SINGLE_SURFACE_ID")
    
    def parse(self, contactErodingSingleSurfaceKeywords):
        for i in range(len(contactErodingSingleSurfaceKeywords)):
            curParameter = contactErodingSingleSurfaceKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ERODING_SINGLE_SURFACE\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 3:
                    stream.write("$$     SYM     EROSOP      IADJ\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")
                
class ContactErodingNodesToSurface(DynaKeyword):
    def __init__(self):
        super(ContactErodingNodesToSurface,self).__init__("CONTACT_ERODING_NODES_TO_SURFACE")
    
    def parse(self, contactErodingNodesToSurfaceKeywords):
        for i in range(len(contactErodingNodesToSurfaceKeywords)):
            curParameter = contactErodingNodesToSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getErodingNodesToSurfaceList(self):
        contactList = [] 
        for i in range(len(self.parameters)):
            curContactList = []
            curContactList.append("*CONTACT_ERODING_NODES_TO_SURFACE")
            curParameter = self.parameters[i]
            curContactList.append(curParameter[0])
            curContactList.append(curParameter[1])
            curContactList.append(curParameter[2])
            curContactList.append(curParameter[3])
            contactList.append(curContactList)
        return contactList
            
            
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ERODING_NODES_TO_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 3:
                    stream.write("$$     SYM     EROSOP      IADJ\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactErodingNodesToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactErodingNodesToSurfaceID,self).__init__("CONTACT_ERODING_NODES_TO_SURFACE_ID")
    
    def parse(self, contactErodingNodesToSurfaceKeywords):
        for i in range(len(contactErodingNodesToSurfaceKeywords)):
            curParameter = contactErodingNodesToSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getErodingNodesToSurfaceIDList(self):
        contactList = [] 
        for i in range(len(self.parameters)):
            curContactList = []
            curContactList.append("*CONTACT_ERODING_NODES_TO_SURFACE")
            curParameter = self.parameters[i]
            curContactList.append(curParameter[0])
            curContactList.append(curParameter[1])
            curContactList.append(curParameter[2])
            curContactList.append(curParameter[3])
            curContactList.append(curParameter[4])
            contactList.append(curContactList)
        return contactList      
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ERODING_NODES_TO_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)

            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 4:
                    stream.write("$$     SYM     EROSOP      IADJ\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactErodingSurfaceToSurface(DynaKeyword):
    def __init__(self):
        super(ContactErodingSurfaceToSurface,self).__init__("CONTACT_ERODING_SURFACE_TO_SURFACE")   
    
    def parse(self, contactErodingSurfaceToSurfaceKeywords):
        for i in range(len(contactErodingSurfaceToSurfaceKeywords)):
            curParameter = contactErodingSurfaceToSurfaceKeywords[i]
            parameterList = [] 
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getErodingSurfaceToSurfaceList(self):
        contactList = []
        for i in range(len(self.parameters)):
            curContactList = []
            curContactList.append("*CONTACT_ERODING_SURFACE_TO_SURFACE")
            curParameter = self.parameters[i]
            curContactList.append(curParameter[0])
            curContactList.append(curParameter[1])
            curContactList.append(curParameter[2])
            curContactList.append(curParameter[3])
            contactList.append(curContactList)
        return contactList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ERODING_SURFACE_TO_SURFACE\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 3:
                    stream.write("$$     SYM     EROSOP      IADJ\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactErodingSurfaceToSurfaceID(DynaKeyword):
    def __init__(self):
        super(ContactErodingSurfaceToSurfaceID,self).__init__("CONTACT_ERODING_SURFACE_TO_SURFACE_ID")   
    
    def parse(self, contactErodingSurfaceToSurfaceKeywords):
        for i in range(len(contactErodingSurfaceToSurfaceKeywords)):
            curParameter = contactErodingSurfaceToSurfaceKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getErodingSurfaceToSurfaceIDList(self):
        contactList = []
        for i in range(len(self.parameters)):
            curContactList = []
            curContactList.append("*CONTACT_ERODING_SURFACE_TO_SURFACE_ID")
            curParameter = self.parameters[i]
            curContactList.append(curParameter[0])
            curContactList.append(curParameter[1])
            curContactList.append(curParameter[2])
            curContactList.append(curParameter[3])
            curContactList.append(curParameter[4])
            contactList.append(curContactList)
        return contactList
    
            

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ERODING_SURFACE_TO_SURFACE_ID\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)

            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 4:
                    stream.write("$$     SYM     EROSOP      IADJ\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactErodingSurfaceToSurfaceTitle(DynaKeyword):
    def __init__(self):
        super(ContactErodingSurfaceToSurfaceTitle,self).__init__("CONTACT_ERODING_SURFACE_TO_SURFACE_TITLE")   
    
    def parse(self, contactErodingSurfaceToSurfaceTitleKeywords):
        for i in range(len(contactErodingSurfaceToSurfaceTitleKeywords)):
            curParameter = contactErodingSurfaceToSurfaceTitleKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_ERODING_SURFACE_TO_SURFACE_TITLE\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)

            for j in range(1,len(curParameter)):
                if j == 1:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 2:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 3:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                elif j == 4:
                    stream.write("$$     SYM     EROSOP      IADJ\n")

                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ContactForceTransducerPenalty(DynaKeyword):
    def __init__(self):
        super(ContactForceTransducerPenalty,self).__init__("CONTACT_FORCE_TRANSDUCER_PENALTY")
    
    def parse(self, contactForceTransducerPenaltyKeywords):
        for i in range(len(contactForceTransducerPenaltyKeywords)):
            curParameter = contactForceTransducerPenaltyKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [80])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]            
            stream.write("*CONTACT_FORCE_TRANSDUCER_PENALTY\n")
            stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
            formatted_elements = [f"{str(element):>10}" for element in curParameter[0]]
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")

            for j in range(1,len(curParameter)):
                formatted_elements =f"{str(curParameter[j][0]):<80}\n"
                stream.write(formatted_elements)

class ContactForceTransducerPenaltyID(DynaKeyword):
    def __init__(self):
        super(ContactForceTransducerPenaltyID,self).__init__("CONTACT_FORCE_TRANSDUCER_PENALTY_ID")
    
    def parse(self, contactForceTransducerPenaltyKeywords):
        for i in range(len(contactForceTransducerPenaltyKeywords)):
            curParameter = contactForceTransducerPenaltyKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 70])
            parameterList.append(parameters)
            parameters = self.parse_whole(curParameter[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(2,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]            
            stream.write("*CONTACT_FORCE_TRANSDUCER_PENALTY_ID\n")
            stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
            formatted_elements =f"{str(curParameter[0][0]):>10}{str(curParameter[0][1]):<70}\n"
            stream.write(formatted_elements)
            formatted_elements = [f"{str(element):>10}" for element in curParameter[1]]
            result = ''.join(formatted_elements)
            result = result + "\n"
            stream.write(result)
            for j in range(2,len(curParameter)):
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                result = result + "\n"
                stream.write(result)

class ContactSlidingOnly(DynaKeyword):
    def __init__(self):
        super(ContactSlidingOnly,self).__init__("CONTACT_SLIDING_ONLY")

    def parse(self, contactSlidingOnlyKeywords):
        for i in range(len(contactSlidingOnlyKeywords)):
            curParameter = contactSlidingOnlyKeywords[i]
            parameterList = []
            for j in range(0,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    # 맞는지 확인 필요 
    def AddContactSlidingOnly(self, SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF):
        parameterList = [] 
        parameterList.append([SSID, MSID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR])
        parameterList.append([FS, FD, DC, VC, VDC, PENCHK, BT, DT])
        parameterList.append([SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF])
        self.parameters.append(parameterList) 

    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTACT_SLIDING_ONLY\n")
            for j in range(len(curParameter)):
                if j == 0:
                    stream.write("$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR\n")
                elif j == 1:
                    stream.write("$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT\n")
                elif j == 2:
                    stream.write("$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF\n")
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")                


class ControlAccuracy(DynaKeyword):
    def __init__(self):
        super(ControlAccuracy,self).__init__("CONTROL_ACCURACY")
     
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def OSU(self):
        return self.parameters[0][0]
    
    def INN(self):
        return self.parameters[0][1]
    
    def PIDOSU(self):
        return self.parameters[0][2]
    
    def IACC(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*CONTROL_ACCURACY\n")
        stream.write("$$     OSU       INN    PIDOSU      IACC\n")
        self.writeParameters(stream)

class ControlAdapt(DynaKeyword):
    def __init__(self):
        super(ControlAdapt,self).__init__("CONTROL_ADAPT")
    
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        
    def write(self, stream):
        stream.write("*CONTROL_ADAPT\n")        
        stream.write("$$ ADPFREQ    ADPTOL    ADPTYP    MAXLVL    TBIRTH    TDEATH     LCADP\n")
        self.writeParameters(stream)

class ControlAdaptive(DynaKeyword):
    def __init__(self):
        super(ControlAdaptive,self).__init__("CONTROL_ADAPTIVE")
    
    def parse(self, controlAdaptiveKeywords):
        for i in range(len(controlAdaptiveKeywords)):
            curParameter = controlAdaptiveKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(curParameter)):
                parameters = self.parse_whole(curParameter[j], [10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTROL_ADAPTIVE\n")
            ADPTYP = 1
            if len(curParameter[0])>=3:
                if curParameter[0][2] != "":
                    pass
                else:
                    ADPTYP = int(curParameter[0][2])
            
            # h-adaptivity for shells
            if ADPTYP == 1 or ADPTYP == 2 or ADPTYP == 4:
                stream.write("$$ ADPFREQ    ADPTOL    ADPTYP    MAXLVL    TBIRTH    TDEATH     LCADP    IOFLAG\n")
            elif ADPTYP == 7:
                stream.write("$$ ADPFREQ              ADPTYP              TBIRTH    TDEATH     LCADP")
            elif ADPTYP == 8 or ADPTYP == -8:
                stream.write("$$ ADPFREQ    ADPTOL    ADPTYP    MAXLVL    TBIRTH    TDEATH     LCADP\n")

                
            formatted_elements = [f"{str(element):>10}" for element in curParameter[0]]
            
                
            result = ''.join(formatted_elements)
            stream.write(result)
            stream.write("\n")
            for j in range(1,len(curParameter)):
                if j == 1:
                    if ADPTYP == 1 or ADPTYP == 2 or ADPTYP == 4:                        
                        stream.write("$$ ADPSIZE    ADPASS    IREFLG    ADPENE     ADPTH    MEMORY    ORIENT     MAXEL\n")                        
                    elif ADPTYP == 7:
                        stream.write("$$                                ADPENE              MEMORY\n")
                    elif ADPTYP == 8 or ADPTYP == -8:
                        stream.write("$$ ADPSIZE    ADPASS                                  MEMORY               MAXEL\n")                        
                if j == 2:
                    if ADPTYP == 1 or ADPTYP == 2 or ADPTYP == 4:
                        stream.write("$$ IADPN90    IADPGH    NCFREQ    IADPCL    ADPCTL    CBIRTH    CDEATH     LCLVL\n")   
                    elif ADPTYP == 7 or ADPTYP == 8 or ADPTYP == -8:
                        stream.write("$$   EMPTY\n")
                        stream.write("\n")
                        continue
                if j == 3:
                    if ADPTYP == 1 or ADPTYP == 2:
                        stream.write("$$                                                   D3TRACE              IFSAND\n")
                    elif ADPTYP == 4:
                        stream.write("$$                                          ADPERR   D3TRACE\n")
                    elif ADPTYP == 7:
                        stream.write("$$                                                   D3TRACE    IADPCF\n")
                    elif ADPTYP == 8 or ADPTYP == -8:
                        stream.write("$$    CNLA                                   MMM2D   D3TRACE\n")
                if j == 4:
                        stream.write("$$ INMEMRY")
               
                formatted_elements = [f"{str(element):>10}" for element in curParameter[j]]
                result = ''.join(formatted_elements)
                stream.write(result)
                stream.write("\n")

class ControlALE(DynaKeyword):
    def __init__(self):
        super(ControlALE,self).__init__("CONTROL_ALE")
    
    def parse(self, control_ale_keywords):
        for i in range(len(control_ale_keywords)):
            curParameter = control_ale_keywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curParameter[0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curParameter[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(curParameter) > 2:
                parameters = self.parse_whole(curParameter[2], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            if len(curParameter) > 3:
                parameters = self.parse_whole(curParameter[3], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            curParameter = self.parameters[i]
            stream.write("*CONTROL_ALE\n")
            stream.write("$$     DCT      NADV      METH      AFAC      BFAC      CFAC      DFAC      EFAC\n")
            for k in range(len(curParameter[0])):
                formatted_elements = f"{str(curParameter[0][k]):>10}"
                stream.write(formatted_elements)
            stream.write("\n")
            stream.write("$$   START       END     AAFAC     VFACT      PRIT       EBC      PREF   NSIDEBC\n")
            
            for k in range(len(curParameter[1])):
                formatted_elements = f"{str(curParameter[1][k]):>10}"
                stream.write(formatted_elements)
            stream.write("\n")
            if len(curParameter) > 2:
                stream.write("$$    NCPL      NBKT    IMASCL    CHECKR    BEAMIN   MMGPREF    PDIFMX   DTMUFAC\n")                    
                for k in range(len(curParameter[2])):
                    formatted_elements = f"{str(curParameter[2][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")
            if len(curParameter) > 3:
                stream.write("$$ OPTIMPP    IALEDR    BNDFLX    MINMAS\n")
                for k in range(len(curParameter[3])):
                    formatted_elements = f"{str(curParameter[3][k]):>10}"
                    stream.write(formatted_elements)
            stream.write("\n")

class ControlBulkViscosity(DynaKeyword):
    def __init__(self):
        super(ControlBulkViscosity,self).__init__("CONTROL_BULK_VISCOSITY")
      
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        
    def SetControlBulkViscosity(self, Q1, Q2, TYPE, BTYPE, TSTYPE):
        self.parameters = []
        self.parameters.append([Q1, Q2, TYPE, BTYPE, TSTYPE])
        
    def getControlBulkViscosity(self):
        parameter = []
        parameter.append("*CONTROL_BULK_VISCOSITY")
        parameter.append(self.parameters[0])
        return parameter
    
    def write(self, stream):
        stream.write("*CONTROL_BULK_VISCOSITY\n")
        stream.write("$$      Q1        Q2      TYPE     BTYPE    TSTYPE")
        self.writeParameters(stream)   

class ControlContact(DynaKeyword):
    def __init__(self):
        super(ControlContact,self).__init__("CONTROL_CONTACT")
           
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
        for i in range(len(lines[0])):
            parameters = self.parse_whole(lines[0][i], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
            
    
    def AddControlContact(self, SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS, USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ, SFRIC, DFRIC, EDC, VFC, TH, TH_SF, PEN_SF, PTSCL, IGNORE, FRCENG, SKIPRWG, OUTSEG, SPOTSTP, SPOTDEL, SPOTHIN, ISYM, NSEROD, RWGAPS, RWGDTH, RWKSF, ICOV, SWRADF, ITHOFF, SHLEDG, PSTIFF, ITHCNT, TDCNOF, FTALL, UNUSED, SHLTRW, IGACTC):
        self.parameters = []
        self.parameters.append([SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS])
        self.parameters.append([USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ])
        self.parameters.append([SFRIC, DFRIC, EDC, VFC, TH, TH_SF, PEN_SF, PTSCL])
        self.parameters.append([IGNORE, FRCENG, SKIPRWG, OUTSEG, SPOTSTP, SPOTDEL, SPOTHIN])
        self.parameters.append([ISYM, NSEROD, RWGAPS, RWGDTH, RWKSF, ICOV, SWRADF, ITHOFF])
        self.parameters.append([SHLEDG, PSTIFF, ITHCNT, TDCNOF, FTALL, UNUSED, SHLTRW, IGACTC])
        
        
    
    def SetControlContact(self, SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS, USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ, SFRIC, DFRIC, EDC, VFC, TH, TH_SF, PEN_SF, PTSCL, IGNORE, FRCENG, SKIPRWG, OUTSEG, SPOTSTP, SPOTDEL, SPOTHIN, ISYM, NSEROD, RWGAPS, RWGDTH, RWKSF, ICOV, SWRADF, ITHOFF, SHLEDG, PSTIFF, ITHCNT, TDCNOF, FTALL, UNUSED, SHLTRW, IGACTC):
        self.AddControlContact(SLSFAC, RWPNAL, ISLCHK, SHLTHK, PENOPT, THKCHG, ORIEN, ENMASS, USRSTR, USRFRC, NSBCS, INTERM, XPENE, SSTHK, ECDT, TIEDPRJ, SFRIC, DFRIC, EDC, VFC, TH, TH_SF, PEN_SF, PTSCL, IGNORE, FRCENG, SKIPRWG, OUTSEG, SPOTSTP, SPOTDEL, SPOTHIN, ISYM, NSEROD, RWGAPS, RWGDTH, RWKSF, ICOV, SWRADF, ITHOFF, SHLEDG, PSTIFF, ITHCNT, TDCNOF, FTALL, UNUSED, SHLTRW, IGACTC)
    
    def getControlContact(self):
        parameter = []
        parameter.append("*CONTROL_CONTACT")
        parameter.append(self.parameters[0])
        parameter.append(self.parameters[1])
        if len(self.parameters) > 2:
            parameter.append(self.parameters[2])
        if len(self.parameters) > 3:
            parameter.append(self.parameters[3])
        if len(self.parameters) > 4:
            parameter.append(self.parameters[4])
        if len(self.parameters) > 5:
            parameter.append(self.parameters[5])
        return parameter

    def SLSFAC(self):
        return self.parameters[0][0]
    
    def RWPNAL(self):
        return self.parameters[0][1]
    
    def ISLCHK(self):
        return self.parameters[0][2]
    
    def SHLTHK(self):
        return self.parameters[0][3]
    
    def PENOPT(self):
        return self.parameters[0][4]
    
    def THKCHG(self):
        return self.parameters[0][5]
    
    def ORIEN(self):
        return self.parameters[0][6]
    
    def ENMASS(self):
        return self.parameters[0][7]
    
    def USRSTR(self):
        return self.parameters[1][0]
    
    def USRFRC(self):
        return self.parameters[1][1]
    
    def NSBCS(self):
        return self.parameters[1][2]
    
    def INTERM(self):
        return self.parameters[1][3]
    
    def XPENE(self):
        return self.parameters[1][4]
    
    def SSTHK(self):
        return self.parameters[1][5]
    
    def ECDT(self):
        return self.parameters[1][6]
    
    def TIEDPRJ(self):
        return self.parameters[1][7]
    
    def write(self, stream):
        stream.write("*CONTROL_CONTACT\n")
        stream.write("$$  SLSFAC    RWPNAL    ISLCHK    SHLTHK    PENOPT    THKCHG     ORIEN    ENMASS\n")
        self.writeParameter(stream,0)
        stream.write("$$  USRSTR    USRFRC     NSBCS    INTERM     XPENE     SSTHK      ECDT   TIEDPRJ\n")
        self.writeParameter(stream,1)
        if len(self.parameters) > 2:
            stream.write("$$   SFRIC     DFRIC       EDC       VFC        TH     TH_SF    PEN_SF    IGNORE\n")        
            self.writeParameter(stream,2)
        if len(self.parameters) > 3:
            stream.write("$$   FRCENG   SKIPRWG    OUTSEG   SPOTSTP   SPOTDEL   SPOTHIN      ISYM    NSEROD\n")
            self.writeParameter(stream,3)


class ControlCPU(DynaKeyword):
    def __init__(self):
        super(ControlCPU,self).__init__("CONTROL_CPU")
    
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10])
        self.parameters.append(parameters)
    
    def write(self, stream):
        stream.write("*CONTROL_CPU\n")
        stream.write("$$  CPUTIM     IGLST\n")
        self.writeParameters(stream)
        
class ControlDynamicRelaxation(DynaKeyword):
    def __init__(self):
        super(ControlDynamicRelaxation,self).__init__("CONTROL_DYNAMIC_RELAXATION")
        
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        
    def SetControlDynamicRelaxation(self, NRCYCK, DRTOL, DRFCTR, DRTERM, TSSFDR, IRELAL, EDTTL, IDRFLG):
        self.parameters = []
        self.parameters.append([NRCYCK, DRTOL, DRFCTR, DRTERM, TSSFDR, IRELAL, EDTTL, IDRFLG])    
        
    def getControlDynamicRelaxation(self):
        parameter = []
        parameter.append("*CONTROL_DYNAMIC_RELAXATION")
        parameter.append(self.parameters[0])
        return parameter
            
    def write(self, stream):
        stream.write("*CONTROL_DYNAMIC_RELAXATION\n")
        stream.write("$$  NRCYCK     DRTOL    DRFCTR    DRTERM    TSSFDR    IRELAL     EDTTL    IDRFLG\n")
        self.writeParameters(stream)

class ControlEnergy(DynaKeyword):
    def __init__(self):
        super(ControlEnergy,self).__init__("CONTROL_ENERGY")
   
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def HGEN(self):
        return self.parameters[0][0]

    def RWEN(self):
        return self.parameters[0][1]
    
    def SLNTEN(self):
        return self.parameters[0][2]
    
    def RYLEN(self):
        return self.parameters[0][3]

    def IRGEN(self):
        return self.parameters[0][4]
    
    def MATEN(self):
        return self.parameters[0][5]

    def getControlEnergy(self):
        parameter = [] 
        parameter.append("*CONTROL_ENERGY")
        parameter.append(self.parameters[0])
        return parameter
    
    def SetControlEnergy(self, HGEN, RWEN, SLNTEN, RYLEN, IRGEN, MATEN):
        self.parameters = []
        self.parameters.append([HGEN, RWEN, SLNTEN, RYLEN, IRGEN, MATEN])
    
    def write(self, stream):
        stream.write("*CONTROL_ENERGY\n")
        stream.write("$$    HGEN      RWEN    SLNTEN     RYLEN     IRGEN     MATEN\n")
        self.writeParameters(stream)

class ControlHourglass(DynaKeyword):
    def __init__(self):
        super(ControlHourglass,self).__init__("CONTROL_HOURGLASS")
      
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10])
        self.parameters.append(parameters)
    
    def AddControlHourglass(self, IHQ, QH):
        self.parameters = []
        self.parameters.append([IHQ, QH])        
    
    def SetControlHourglass(self, IHQ, QH):
        self.parameters = []
        self.parameters.append([IHQ, QH])
    
    def getControlHourglass(self):
        parameter = [] 
        parameter.append("*CONTROL_HOURGLASS")
        parameter.append(self.parameters[0])
        return parameter

    def IHQ(self):
        return self.parameters[0][0]

    def QH(self):
        return self.parameters[0][1]
    
    def write(self, stream):
        stream.write("*CONTROL_HOURGLASS\n")
        stream.write("$$     IHQ        QH\n")
        self.writeParameters(stream)  

class ControlImplicitAuto(DynaKeyword):
    def __init__(self):
        super(ControlImplicitAuto,self).__init__("CONTROL_IMPLICIT_AUTO")

    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        IAUTO = parameters[0]
        if len(IAUTO) > 0 and int(IAUTO) == 3:
            parameters = self.parse_whole(lines[0][1], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)

    def write(self, stream):
        stream.write("*CONTROL_IMPLICIT_AUTO\n")
        stream.write("$$   IAUTO    ITEOPT    ITEWIN     DTMIN     DTMAX     DTEXP     KFAIL    KCYCLE\n")
        self.writeParameters(stream)
        IAUTO = self.parameters[0][0]
        if len(IAUTO) > 0 and int(IAUTO) == 3:
            stream.write("$$   HCMIN     HCMAX     HMMIN     HMMAX    HNTMAX    HNRMAX    HRTMAX    HRRMAX\n")
            self.writeParameter(stream,1)   

class ControlImplicitDynamics(DynaKeyword):
    def __init__(self):
        super(ControlImplicitDynamics,self).__init__("CONTROL_IMPLICIT_DYNAMICS")
    
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        ALPHA = parameters[7]
        if len(ALPHA) >0 and float(ALPHA) <= -1.0:
            parameters = self.parse_whole(lines[0][1], [10, 10])
            self.parameters.append(parameters)
    
    def write(self, stream):
        stream.write("*CONTROL_IMPLICIT_DYNAMICS\n")
        stream.write("$$   IMASS     GAMMA      BETA    TDYBIR    TDYDTH    TDYBUR     IRATE     ALPHA\n")
        self.writeParameters(stream)     
        ALPHA = self.parameters[0][7]
        if len(ALPHA) >0 and float(ALPHA) <= -1.0:
            stream.write("$$    PSID     ANGLE\n")
            self.writeParameter(stream,1)                        


class ControlImplicitEigenvalue(DynaKeyword):
    def __init__(self):
        super(ControlImplicitEigenvalue,self).__init__("CONTROL_IMPLICIT_EIGENVALUE")

    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        EIGMTH = parameters[6]
        if len(lines[0]) >1:
            parameters = self.parse_whole(lines[0][1], [10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
        if len(lines[0]) >2:
            if len(EIGMTH) > 0 and int(EIGMTH) == 101:
                parameters = self.parse_whole(lines[0][2], [10, 10, 10, 10, 10])
                self.parameters.append(parameters)
            elif len(EIGMTH) > 0 and int(EIGMTH) == 102:
                parameters = self.parse_whole(lines[0][2], [10, 10, 10, 10, 10, 10])
                self.parameters.append(parameters)
            elif len(EIGMTH) > 0 and int(EIGMTH) == 111:
                parameters = self.parse_whole(lines[0][2], [10, 10, 10, 10, 10, 10])
                self.parameters.append(parameters)

    def write(self, stream):
        stream.write("*CONTROL_IMPLICIT_EIGENVALUE\n")
        stream.write("$$    NEIG    CENTER     LFLAG    LFTEND     RFLAG    RHTEND    EIGMTH    SHFSCL\n")
        formatted_elements = [f"{str(element):>10}" for element in self.parameters[0]]
        stream.write(''.join(formatted_elements))
        stream.write("\n")
        if len(self.parameters) > 1:
            stream.write("$$  ISOLID     IBEAM    ISHELL   ITSHELL    MSTRES    EVDUMP   MSTRSCL\n")
            formatted_elements = [f"{str(element):>10}" for element in self.parameters[1]]
            stream.write(''.join(formatted_elements))
            stream.write("\n")
        EIGMTH = self.parameters[0][6] 
        if len(self.parameters) > 2:
            
            if len(EIGMTH)>0 and int(EIGMTH) == 101:
                IPARM1,IPARM2,IPARM3,IPARM4,RPARM1 = self.parse_whole(self.parameters[2],[10, 10, 10, 10, 10])
            if len(EIGMTH)>0 and int(EIGMTH) == 102:
                IPARM1,IPARM2,EMPTY1,EMPTY2,RPARM1,RPARM2 = self.parse_whole(self.parameters[2],[10, 10, 10, 10, 10, 10])
            if len(EIGMTH)>0 and int(EIGMTH) == 111:
                IPARM1,IPARM2,IPARM3,IPARM4,IPARM5,IPARM6 = self.parse_whole(self.parameters[2],[10, 10, 10, 10, 10, 10]) 

class ControlImplicitGeneral(DynaKeyword):
    def __init__(self):
        super(ControlImplicitGeneral,self).__init__("CONTROL_IMPLICIT_GENERAL")
    
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)

    def write(self, stream):
        stream.write("*CONTROL_IMPLICIT_GENERAL\n")
        stream.write("$$  IMFLAG       DT0    IMFORM      NSBS       IGS     CNSTN      FORM    ZERO_V\n")
        self.writeParameters(stream)

class ControlImplicitSolution(DynaKeyword):
    def __init__(self):
        super(ControlImplicitSolution,self).__init__("CONTROL_IMPLICIT_SOLUTION")
    
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        for i in range(1,len(lines[0])):
            parameters = self.parse_whole(lines[0][i], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
    
    def write(self, stream):
        stream.write("*CONTROL_IMPLICIT_SOLUTION\n")
        stream.write("$$  NSOLVR    ILIMIT    MAXREF     DCTOL     ECTOL     RCTOL     LSTOL    ABSTOL\n")
        parameters = self.parameters[0]
        formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}{str(parameters[6]):>10}{str(parameters[7]):>10}\n"
        stream.write(formatted_elements)
        card21mode = False
        if len(self.parameters)>1:
            #check whether self.parameters[1][0] is number or not
            try:
                val = int(self.parameters[1][0])
            except:
                val = None
            
            if val is not None:
                if len(self.parameters[1][0]) > 0 and int(self.parameters[1][0]) < 0:
                    card21mode = True
        if card21mode:        
            for i in range(1,len(self.parameters)):
                parameters = self.parameters[i]
                if i == 1:
                    stream.write("$$   DNORM    DIVERG     ISTIF   NLPRINT    NLNORM   D3ITCTL     CPCHK\n")
                    formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}{str(parameters[6]):>10}\n"
                elif i == 2:
                    stream.write("$$   DMTOL     EMTOL     RMTOL     EMPTY     NTTOL     NRTOL     RTTOL      RTOL\n")                    
                    formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}{str(parameters[6]):>10}{str(parameters[7]):>10}\n"
                elif i == 3:
                    stream.write("$$  ARCCTL    ARCDIR    ARCLEN    ARCMTH    ARCDMP    ARCPSI    ARCALF    ARCTIM\n")
                    formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}{str(parameters[6]):>10}{str(parameters[7]):>10}\n"
                elif i == 4:    
                    stream.write("$$   LSMTD     LSDIR      IRAD      SRAD      AWGT      SRED\n")
                    formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}\n"
                else:
                    continue
                stream.write(formatted_elements)
        else:
            for i in range(1,len(self.parameters)):
                parameters = self.parameters[i]
                if i == 1:
                    stream.write("$$   DNORM    DIVERG     ISTIF   NLPRINT    NLNORM   D3ITCTL     CPCHK\n")
                    formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}{str(parameters[6]):>10}\n"
                elif i == 2:
                    stream.write("$$  ARCCTL    ARCDIR    ARCLEN    ARCMTH    ARCDMP    ARCPSI    ARCALF    ARCTIM\n")
                    formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}{str(parameters[6]):>10}{str(parameters[7]):>10}\n"
                elif i == 3:    
                    stream.write("$$   LSMTD     LSDIR      IRAD      SRAD      AWGT      SRED\n")
                    formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}\n"
                else:
                    continue
                stream.write(formatted_elements)

class ControlImplicitSolver(DynaKeyword):
    def __init__(self):
        super(ControlImplicitSolver,self).__init__("CONTROL_IMPLICIT_SOLVER")
    
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        for i in range(1,len(lines[0])):
            if i == 1:
                parameters = self.parse_whole(lines[0][i], [10, 10, 10, 10, 10, 10, 10, 10])
            elif i == 2:
                parameters = self.parse_whole(lines[0][i], [10, 10, 10])
            self.parameters.append(parameters)
    
    def write(self, stream):
        stream.write("*CONTROL_IMPLICIT_SOLVER\n")
        stream.write("$$  NSOLVR    LPRINT     NEGEV     ORDER      DRCM    DRCPRM   AUTOSPC   AUTOTOL\n")
        parameters = self.parameters[0]
        formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}{str(parameters[6]):>10}{str(parameters[7]):>10}\n"
        stream.write(formatted_elements)
        for i in range(1,len(self.parameters)):
            parameters = self.parameters[i]
            if i == 1:
                stream.write("$$  LCPACK    MTXDMP   IPARM1   RPARM1   RPARM2   EMPTY1   EMPTY2   RPARM5\n")
                formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}{str(parameters[5]):>10}{str(parameters[6]):>10}{str(parameters[7]):>10}\n"                                
            elif i == 2:
                stream.write("$$  EMXDMP    RDCMEM    ABSMEM\n")
                formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}\n"
            else:
                continue
            stream.write(formatted_elements)
     
class ControlMppIoNodump(DynaKeyword):
    def __init__(self):
        super(ControlMppIoNodump,self).__init__("CONTROL_MPP_IO_NODUMP")
        
    def getControlMppIONoDump(self):
        return ["*CONTROL_MPP_IO_NODUMP"]

    def write(self,stream):
        stream.write("*CONTROL_MPP_IO_NODUMP\n")        

class ControlOutput(DynaKeyword):
    def __init__(self):
        super(ControlOutput,self).__init__("CONTROL_OUTPUT")
       
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        if len(lines[0]) > 1:            
            parameters = self.parse_whole(lines[0][1], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
        if len(lines[0]) > 2:            
            parameters = self.parse_whole(lines[0][2], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
        if len(lines[0]) > 3:            
            parameters = self.parse_whole(lines[0][3], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
        if len(lines[0]) > 4:
            parameters = self.parse_whole(lines[0][4], [10, 10, 10, 10, 10])
            self.parameters.append(parameters)
            
    
    def SetControlOutput(self, NPOPT, NEECHO, NREFUP, IACCOP, OPIFS, IPNINT, IKEDIT, IFLUSH, IPRTF, IERODE, TET10S8, MSGMAX, IPCURV, GMDT, IP1DBLT, EOCS, TOLEV, NEWLEG, FRFREQ, MINFO, SOLSIG, MSGFLG, CDETOL, IGEOM, PHSCHNG, DEMDEN, ICRFILE, SPC2BND, PENOUT, SHLSIG, HISNOUT, ENGOUT, INSF, ISOLSF, IBSF, ISSF, MLKBAG):
        self.parameters = []
        self.parameters.append([NPOPT, NEECHO, NREFUP, IACCOP, OPIFS, IPNINT, IKEDIT, IFLUSH])
        self.parameters.append([IPRTF, IERODE, TET10S8, MSGMAX, IPCURV, GMDT, IP1DBLT, EOCS])
        self.parameters.append([TOLEV, NEWLEG, FRFREQ, MINFO, SOLSIG, MSGFLG, CDETOL, IGEOM])
        self.parameters.append([PHSCHNG, DEMDEN, ICRFILE, SPC2BND, PENOUT, SHLSIG, HISNOUT, ENGOUT])
        self.parameters.append([INSF, ISOLSF, IBSF, ISSF, MLKBAG])
        
    
            
    def getControlOutput(self):
        parameter = []
        parameter.append("*CONTROL_OUTPUT")
        for i in range(len(self.parameters)):
            parameter.append(self.parameters[i])            
        return parameter
        
    def NPOPT(self):
        return self.parameters[0][0]
    
    def NEECHO(self):
        return self.parameters[0][1]
    
    def NREFUP(self):
        return self.parameters[0][2]
    
    def IACCOP(self):
        return self.parameters[0][3]
    
    def OPIFS(self):
        return self.parameters[0][4]
    
    def IPNINT(self):
        return self.parameters[0][5]
    
    def IKEDIT(self):
        return self.parameters[0][6]
    
    def IFLUSH(self):
        return self.parameters[0][7]
    
    def IPRTF(self):
        return self.parameters[1][0]
    
    def IERODE(self):
        return self.parameters[1][1]
    
    def TET10S8(self):
        return self.parameters[1][2]
    
    def MSGMAX(self):
        return self.parameters[1][3]
    
    def IPCURV(self):
        return self.parameters[1][4]
    
    def GMDT(self):
        return self.parameters[1][5]
    
    def IP1DBLT(self):
        return self.parameters[1][6]
    
    def EOCS(self):
        return self.parameters[1][7]
    
    def write(self, stream):
        stream.write("*CONTROL_OUTPUT\n")
        stream.write("$$   NPOPT    NEECHO    NREFUP    IACCOP     OPIFS    IPNINT    IKEDIT    IFLUSH\n")
        self.writeParameter(stream,0)
        if len(self.parameters) > 1:
            stream.write("$$   IPRTF    IERODE   TET10S8    MSGMAX    IPCURV      GMDT   IP1DBLT      EOCS\n")
            self.writeParameter(stream,1)            
        if len(self.parameters) > 2:
            stream.write("$$   TOLEV    NEWLEG    FRFREQ     MINFO    SOLSIG    MSGFLG    CDETOL     IGEOM\n")
            self.writeParameter(stream,2)
        if len(self.parameters) > 3:
            stream.write("$$ PHSCHNG    DEMDEN   ICRFILE   SPC2BND    PENOUT    SHLSIG   HISNOUT    ENGOUT\n")
            self.writeParameter(stream,3)
        if len(self.parameters) > 4:
            stream.write("$$     INSF    ISOLSF       IBSF      ISSF    MLKBAG\n")
            self.writeParameter(stream,4)

class ControlParallel(DynaKeyword):
    def __init__(self):
        super(ControlParallel,self).__init__("CONTROL_PARALLEL")
        
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)

    def NCPU(self):
        return self.parameters[0][0]

    def NUMRHS(self):
        return self.parameters[0][1]
    
    def ACCU(self):
        return self.parameters[0][2]
    
    def PARA(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*CONTROL_PARALLEL\n")
        stream.write("$$    NCPU    NUMRHS      ACCU      PARA\n")
        self.writeParameters(stream)

class ControlRigid(DynaKeyword):
    def __init__(self):
        super(ControlRigid,self).__init__("CONTROL_RIGID")

    def parse(self, crKeyword):        
        parameter = self.parse_whole(crKeyword[0][0],[10,10,10,10,10,10,10,10])                
        self.parameters.append(parameter)
        if len(crKeyword[0])>1:
            parameter = self.parse_whole(crKeyword[0][1],[10,10,10,10,10,10,10,10])                
            self.parameters.append(parameter)

    def LMF(self):
        return self.parameters[0][0]
    
    def JNTF(self):
        return self.parameters[0][1]
    
    def ORTHMD(self):
        return self.parameters[0][2]
    
    def PARTM(self):
        return self.parameters[0][3]
    
    def SPARSE(self):
        return self.parameters[0][4]
    
    def METALF(self):
        return self.parameters[0][5]
    
    def PLOTEL(self):
        return self.parameters[0][6]
    
    def RBSMS(self):
        return self.parameters[0][7]
    
    def NORBIC(self):
        if len(self.parameters) == 2:
            return self.parameters[1][0]

    def GJADSTF(self):
        if len(self.parameters) == 2:
            return self.parameters[1][1]
        
    def GJADVSC(self):
        if len(self.parameters) == 2:
            return self.parameters[1][2]
        
    def TJADSTF(self):
        if len(self.parameters) == 2:
            return self.parameters[1][3]
        
    def TJADVSC(self):
        if len(self.parameters) == 2:
            return self.parameters[1][4]        
           
    def write(self, stream):
        stream.write("*CONTROL_RIGID\n")
        stream.write("$$     LMF      JNTF    ORTHMD     PARTM     SPARSE   METALF    PLOTEL     RBSMS\n")
        self.writeParameter(stream,0)
        if len(self.parameters) == 2:
            stream.write("$$  NORBIC   GJADSTF   GJADVSC   TJADSTF   TJADVSC\n")
            self.writeParameter(stream,1)

class ControlShell(DynaKeyword):
    def __init__(self):
        super(ControlShell,self).__init__("CONTROL_SHELL")
           
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        #parameters = lines[0][1].parse_whole([10, 10, 10, 10, 10])
        if len(lines[0])>1:
            parameters = self.parse_whole(lines[0][1], [10, 10, 10, 10, 10])
            self.parameters.append(parameters)
        if len(lines[0])>2:
            parameters = self.parse_whole(lines[0][2], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)            
        
        if len(lines[0])>3:
            parameters = self.parse_whole(lines[0][3], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
        if len(lines[0])>4:
            parameters = self.parse_whole(lines[0][4], [10, 10, 10])
            
    def SetControlShell(self, WRPANG, ESORT, IRNXX, ISTUPD, THEORY, BWC, MITER, PROJ, ROTASCL, INTGRD, LAMSHT, CSTYP6, THSHEL,PSSTUPD,SIDT4TU,CNTCO,ITSFLG,IRQUAD,W_MODE,STRETCH,ICRQ,NFAIL1,NFAIL4,PSNFAIL,KEEPCS,DELFR,DRCPSID,DRCPRM,INTPERR,DRCMTH,LISPSID,NLOCDT):
        self.parameters = []
        self.parameters.append([WRPANG, ESORT, IRNXX, ISTUPD, THEORY, BWC, MITER, PROJ])
        self.parameters.append([ROTASCL, INTGRD, LAMSHT, CSTYP6, THSHEL])
        self.parameters.append([PSSTUPD,SIDT4TU,CNTCO,ITSFLG,IRQUAD,W_MODE,STRETCH,ICRQ])
        self.parameters.append([NFAIL1,NFAIL4,PSNFAIL,KEEPCS,DELFR,DRCPSID,DRCPRM,INTPERR])
        self.parameters.append([DRCMTH,LISPSID,NLOCDT])
        
    def getControlShell(self):
        parameter = []
        parameter.append("*CONTROL_SHELL")
        parameter.append(self.parameters[0])
        if len(self.parameters) > 1:
            parameter.append(self.parameters[1])
        if len(self.parameters) > 2:
            parameter.append(self.parameters[2])
        if len(self.parameters) > 3:
            parameter.append(self.parameters[3])
        if len(self.parameters) > 4:
            parameter.append(self.parameters[4])        
        return parameter                
    
    def WRPANG(self):
        return self.parameters[0][0]

    def ESORT(self):
        return self.parameters[0][1]

    def IRNXX(self):
        return self.parameters[0][2]
    
    def ISTUPD(self):
        return self.parameters[0][3]

    def THEORY(self):
        return self.parameters[0][4]
    
    def BWC(self):
        return self.parameters[0][5]
    
    def MITER(self):
        return self.parameters[0][6]
    
    def PROJ(self):
        return self.parameters[0][7]
    
    def ROTASCL(self):
        return self.parameters[1][0]
    
    def INTGRD(self):
        return self.parameters[1][1]
    
    def LAMSHT(self):
        return self.parameters[1][2]
    
    def CSTYP6(self):
        return self.parameters[1][3]
    
    def THSHEL(self):
        return self.parameters[1][4]
    
    def write(self, stream):
        stream.write("*CONTROL_SHELL\n")
        stream.write("$$  WRPANG     ESORT     IRNXX    ISTUPD    THEORY       BWC     MITER      PROJ\n")
        self.writeParameter(stream,0)
        if len(self.parameters) > 1:
            stream.write("$$ ROTASCL    INTGRD    LAMSHT    CSTYP6    THSHEL\n")
            self.writeParameter(stream,1)
        if len(self.parameters) > 2:
            stream.write("$$ PSSTUPD   SIDT4TU     CNTCO    ITSFLG    IRQUAD    W-MODE   STRETCH      ICRQ\n")
            self.writeParameter(stream,2)
        if len(self.parameters) > 3:
            stream.write("$$  NFAIL1    NFAIL4   PSNFAIL    KEEPCS     DELFR   DRCPSID    DRCPRM   INTPERR\n")
            self.writeParameter(stream,3)
        if len(self.parameters) > 4:
            stream.write("$$  DRCMTH   LISPSID    NLOCDT\n")
            self.writeParameter(stream,4)
            
class ControlSolid(DynaKeyword):
    def __init__(self):
        super(ControlSolid,self).__init__("CONTROL_SOLID")

    def parse(self, csKeyword):
        parameter = self.parse_whole(csKeyword[0][0],[10,10,10,10,10,10,10,10])
        self.parameters.append(parameter)
        if len(csKeyword[0])>1:
            parameter = self.parse_whole(csKeyword[0][1],[8,8,8,8,8,8,8,8,8,8])
            self.parameters.append(parameter)
        if len(csKeyword[0])>2:
            parameter = self.parse_whole(csKeyword[0][2],[10,10])
            self.parameters.append(parameter)
    
    def SetControlSolid(self, ESORT, FMATRX, NIPTETS, SWLOCL, PSFAIL, T10JTOL, ICOH, TET13K, PM1, PM2, PM3, PM4, PM5, PM6, PM7, PM8, PM9, PM10, TET13V, RINRT):
        self.parameters = []
        parameters = [ESORT, FMATRX, NIPTETS, SWLOCL, PSFAIL, T10JTOL, ICOH, TET13K]
        self.parameters.append(parameters)        
        parameters = [PM1, PM2, PM3, PM4, PM5, PM6, PM7, PM8, PM9, PM10]
        self.parameters.append(parameters)
        parameters = [TET13V, RINRT]
        self.parameters.append(parameters)                             
    
    def getControlSolid(self):
        parameter = []
        parameter.append("*CONTROL_SOLID")
        parameter.append(self.parameters[0])
        if len(self.parameters) > 1:
            parameter.append(self.parameters[1])
        if len(self.parameters) > 2:
            parameter.append(self.parameters[2])
        return parameter
               
    def ESORT(self):
        return self.parameters[0][0]
    
    def FMATRX(self):
        return self.parameters[0][1]
    
    def NIPTETS(self):
        return self.parameters[0][2]
    
    def SWLOCL(self):
        return self.parameters[0][3]
    
    def PSFAIL(self):
        return self.parameters[0][4]
    
    def T10JTOL(self):
        return self.parameters[0][5]
    
    def ICOH(self):
        return self.parameters[0][6]
    
    def TET13K(self):
        return self.parameters[0][7]
    
    def PM(self,ith):
        if len(self.parameters) > 1:
            if ith >=0 and ith < len(self.parameters[1]):
                return self.parameters[1][ith]
            else:
                return None
    def TET13V(self):
        if len(self.parameters) > 2:
            return self.parameters[2][0]
        
    def write(self, stream):
        stream.write("*CONTROL_SOLID\n")
        stream.write("$$   ESORT    FMATRX   NIPTETS    SWLOCL    PSFAIL   T10JTOL      ICOH    TET13K\n")
        self.writeParameter(stream,0)
        if len(self.parameters) > 1:
            stream.write("$$   PM1     PM2     PM3     PM4     PM5     PM6     PM7     PM8     PM9    PM10\n")
            self.writeParameter(stream,1)
        if len(self.parameters) > 2:
            stream.write("$$  TET13V     RINRT\n")
            self.writeParameter(stream,2)

class ControlSolution(DynaKeyword):
    def __init__(self):
        super(ControlSolution,self).__init__("CONTROL_SOLUTION")

    def parse(self, cskeyword):        
        parameter = self.parse_whole(cskeyword[0][0],[10,10,10,10,10,10,10])
        self.parameters.append(parameter)
    
    def SOLNF(self):
        return self.parameters[0][0]
    
    def NLQ(self):
        return self.parameters[0][1]
    
    def ISNAN(self):
        return self.parameters[0][2]
    
    def LCINT(self):
        return self.parameters[0][3]
    
    def LCACC(self):
        return self.parameters[0][4]
    
    def NCDCF(self):
        return self.parameters[0][5]
    
    def NOCOPY(self):
        return self.parameters[0][6]
    
    def write(self, stream):
        stream.write("*CONTROL_SOLUTION\n")
        stream.write("$$   SOLNF       NLQ     ISNAN     LCINT     LCACC     NCDCF    NOCOPY\n")
        self.writeParameter(stream,0)

class ControlTermination(DynaKeyword):
    def __init__(self):
        super(ControlTermination,self).__init__("CONTROL_TERMINATION")
       
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        
    def getControlTermination(self):
        parameters = [] 
        parameters.append("*CONTROL_TERMINATION")
        parameters.append(self.parameters[0])
        return parameters

    def SetControlTermination(self, ENDTIM, ENDCYC, DTMIN, ENDENG, ENDMAS, NOSOL):
        self.parameters = []
        parameters = [ENDTIM, ENDCYC, DTMIN, ENDENG, ENDMAS, NOSOL]
        self.parameters.append(parameters)

    def ENDTIM(self):
        return self.parameters[0][0]

    def ENDCYC(self):
        return self.parameters[0][1]
    
    def DTMIN(self):
        return self.parameters[0][2]
    
    def ENDENG(self):
        return self.parameters[0][3]
    
    def ENDMAS(self):
        return self.parameters[0][4]
    
    def NOSOL(self):
        return self.parameters[0][5]
    
    def write(self, stream):
        stream.write("*CONTROL_TERMINATION\n")
        stream.write("$$  ENDTIM    ENDCYC     DTMIN    ENDENG    ENDMAS     NOSOL\n")
        self.writeParameters(stream)        

class ControlTimeStep(DynaKeyword):
    def __init__(self):
        super(ControlTimeStep,self).__init__("CONTROL_TIMESTEP")
        
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        #parameters = lines[0][1].parse_whole([10, 10, 10, 10, 10, 10])
        if len(lines[0])>1:
            parameters = self.parse_whole(lines[0][1], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
            
    def getControlTimeStep(self):
        parameters = []
        parameters.append("*CONTROL_TIMESTEP")
        parameters.append(self.parameters[0])
        if len(self.parameters) > 1:
            parameters.append(self.parameters[1])
        return parameters

    def SetControlTimeStep(self,DTINIT,TSSFAC,ISDO,TSLIMT,DT2MS,LCTM,ERODE,MS1ST):
        self.parameters = []
        parameters = [DTINIT,TSSFAC,ISDO,TSLIMT,DT2MS,LCTM,ERODE,MS1ST]
        self.parameters.append(parameters)
        
    def SetControlTimeStepwithOptional(self, DTINIT,TSSFAC,ISDO,TSLIMT,DT2MS,LCTM,ERODE,MS1ST,DT2MSF,DT2MSLC,IMSCL,RMSCL,IHDO):
        self.parameters = []
        parameters = [DTINIT,TSSFAC,ISDO,TSLIMT,DT2MS,LCTM,ERODE,MS1ST]
        self.parameters.append(parameters)
        parameters = [DT2MSF,DT2MSLC,IMSCL,"          ","          ",RMSCL,"          ",IHDO]
        self.parameters.append(parameters)      

    def DTINIT(self):
        return self.parameters[0][0]

    def TSSFAC(self):
        return self.parameters[0][1]
    
    def ISDO(self):
        return self.parameters[0][2]
    
    def TSLIMT(self):
        return self.parameters[0][3]
    
    def DT2MS(self):
        return self.parameters[0][4]
    
    def LCTM(self):
        return self.parameters[0][5]
    
    def ERODE(self):
        return self.parameters[0][6]
    
    def MSIST(self):
        return self.parameters[0][7]
    
    def DT2MSF(self):
        return self.parameters[1][0]
    
    def DT2MSLC(self):
        return self.parameters[1][1]
    
    def IMSCL(self):
        return self.parameters[1][2]
    
    def RMSCL(self):
        return self.parameters[1][5]
    
    def write(self, stream):
        stream.write("*CONTROL_TIMESTEP\n")
        stream.write("$$  DTINIT    TSSFAC      ISDO    TSLIMT     DT2MS      LCTM     ERODE     MSIST\n")        
        self.writeParameter(stream,0)
        if len(self.parameters) > 1:
            stream.write("$$  DT2MSF   DT2MSLC     IMSCL                         RMSCL                IHD0\n")
            self.writeParameter(stream,1)        

class DampingGlobal(DynaKeyword):
    def __init__(self):
        super(DampingGlobal,self).__init__("DAMPING_GLOBAL")
    
    def parse(self, lines):
        self.parameters = []
        parameters = [] 
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)

    def getDampingGlobal(self):
        dampingGlobal = [] 
        dampingGlobal.append("*DAMPING_GLOBAL")
        dampingGlobal.append(self.parameters[0])
        return dampingGlobal
    
    def write(self, stream):
        stream.write("*DAMPING_GLOBAL\n")
        stream.write("$$    LCID    VALDMP       STX       STY       STZ       SRX       SRY       SRZ\n")
        curParameter = self.parameters[0]
        for i in range(len(curParameter)):
            formatted_elements = f"{str(curParameter[i]):>10}"
            stream.write(formatted_elements)
        stream.write("\n")
        

class DampingPartMass(DynaKeyword):
    def __init__(self):
        super(DampingPartMass,self).__init__("DAMPING_PART_MASS")
    
    def parse(self, lines):
        for i in range(len(lines)):
            parameters = [] 
            parameters.append(self.parse_whole(lines[i][0], [10, 10, 10, 10]))
            if len(parameters[0]) == 4:
                FLAG = int(parameters[0][3])
                if FLAG == 1:                    
                    parameters.append(self.parse_whole(lines[i][1], [10, 10, 10, 10, 10, 10]))
            self.parameters.append(parameters)
    
    def getDampingPartMass(self):
        dampingList = [] 
        for i in range(len(self.parameters)):
            parameters = []
            parameters.append("*DAMPING_PART_MASS")
            parameters.append(self.parameters[i][0])
            if len(self.parameters[i]) == 2:
                parameters.append(self.parameters[i][1])
            dampingList.append(parameters)
        return dampingList
                            
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DAMPING_PART_MASS\n")
            stream.write("$$     PID      LCID        SF     FLAG\n")            
            curParameter = parameter[0]
            for j in range(len(curParameter)):
                formatted_elements = f"{str(curParameter[j]):>10}"
                stream.write(formatted_elements)
            stream.write("\n")
            if len(curParameter) == 4:
                if len(curParameter[3]) == 0:
                    continue
                FLAG = int(curParameter[3])
                if FLAG == 1:
                    stream.write("$$     STX       STY       STZ       SRX       SRY       SRZ\n")
                    curParameter = parameter[1]
                    for j in range(len(curParameter)):
                        formatted_elements = f"{str(curParameter[j]):>10}"
                        stream.write(formatted_elements)
                    stream.write("\n")

class DampingPartMassSet(DynaKeyword):
    def __init__(self):
        super(DampingPartMassSet,self).__init__("DAMPING_PART_MASS_SET")
        
    def parse(self, lines):
        for i in range(len(lines)):
            parameters = [] 
            parameters.append(self.parse_whole(lines[i][0], [10, 10, 10, 10]))
            if len(parameters[0]) == 4:
                FLAG = int(parameters[0][3])
                if FLAG == 1:                    
                    parameters.append(self.parse_whole(lines[i][1], [10, 10, 10, 10]))
            self.parameters.append(parameters)
    
    def getDampingPartMassSet(self):
        dampingList = [] 
        for i in range(len(self.parameters)):
            parameters = []
            parameters.append("*DAMPING_PART_MASS_SET")
            parameters.append(self.parameters[i][0])
            if len(self.parameters[i]) == 2:
                parameters.append(self.parameters[i][1])
            dampingList.append(parameters)
        return dampingList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DAMPING_PART_MASS_SET\n")
            stream.write("$$    PSID      LCID        SF     FLAG\n")
            curParameter = parameter[0]
            for j in range(len(curParameter)):
                formatted_elements = f"{str(curParameter[j]):>10}"
                stream.write(formatted_elements)
            stream.write("\n")
            if len(curParameter) == 4:
                if len(curParameter[3]) == 0:
                    continue
                FLAG = int(curParameter[3])
                if FLAG == 1:
                    stream.write("$$     STX       STY       STZ       SRX       SRY       SRZ\n")
                    curParameter = parameter[1]
                    for j in range(len(curParameter)):
                        formatted_elements = f"{str(curParameter[j]):>10}"
                        stream.write(formatted_elements)
                    stream.write("\n")
            

class DampingPartStiffness(DynaKeyword):
    def __init__(self):
        super(DampingPartStiffness,self).__init__("DAMPING_PART_STIFFNESS")
    
    def parse(self, lines):
        for i in range(len(lines)):
            parameters = []
            parameters = self.parse_whole(lines[i][0], [10, 10])
            self.parameters.append(parameters)
    
    def getDampingPartStiffness(self):
        dampingList = []
        for i in range(len(self.parameters)):
            parameters = []
            parameters.append("*DAMPING_PART_STIFFNESS")
            parameters.append(self.parameters[i])
            dampingList.append(parameters)
        return dampingList            
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DAMPING_PART_STIFFNESS\n")
            stream.write("$$     PID      COEF\n")
            for j in range(len(parameter)):
                formatted_elements = f"{str(parameter[j]):>10}"
                stream.write(formatted_elements)
            stream.write("\n")

class DampingPartStiffnessSet(DynaKeyword):
    def __init__(self):
        super(DampingPartStiffnessSet,self).__init__("DAMPING_PART_STIFFNESS_SET")
        
    def parse(self, lines):
        for i in range(len(lines)):
            parameters = []
            parameters = self.parse_whole(lines[i][0], [10, 10])
    
    def getDampingPartStiffnessSet(self):
        dampingList = []
        for i in range(len(self.parameters)):
            parameters = []
            parameters.append("*DAMPING_PART_STIFFNESS_SET")
            parameters.append(self.parameters[i])
            dampingList.append(parameters)
        return dampingList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DAMPING_PART_STIFFNESS_SET\n")
            stream.write("$$    PSID      COEF\n")
            for j in range(len(parameter)):
                formatted_elements = f"{str(parameter[j]):>10}"
                stream.write(formatted_elements)
            stream.write("\n")

class DatabaseBndout(DynaKeyword):
    def __init__(self):
        super(DatabaseBndout,self).__init__("DATABASE_BNDOUT")
       
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseBndout(self):
        parameters = []
        parameters.append("*DATABASE_BNDOUT")
        parameters.append(self.parameters[0])
        return parameters
    
    def DT(self):
        return self.parameters[0][0]

    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def OPTION1(self):
        return self.parameters[0][4]
    
    def OPTION2(self):
        return self.parameters[0][5]
    
    def OPTION3(self):
        return self.parameters[0][6]
    
    def OPTION4(self):
        return self.parameters[0][7]
    
    def write(self, stream):
        stream.write("*DATABASE_BNDOUT\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT   OPTION1   OPTION2   OPTION3   OPTION4\n")
        self.writeParameters(stream)

class DatabaseCrossSectionSet(DynaKeyword):
    def __init__(self):
        super(DatabaseCrossSectionSet,self).__init__("DATABASE_CROSS_SECTION_SET")
    
    def parse(self, lines):
        for i in range(len(lines)):
            spaceVector = []
            parameterList = [] 
            for j in range(len(lines[i])):
                parameters = self.parse_whole(lines[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_CROSS_SECTION_SET\n")            
            for j in range(len(parameter)):
                stream.write("$$    NSID      HSID      BSID      SSID      TSID      DSID        ID     ITYPE\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseCrossSectionSetID(DynaKeyword):
    def __init__(self):
        super(DatabaseCrossSectionSetID,self).__init__("DATABASE_CROSS_SECTION_SET_ID")
    
    def parse(self, dbCrossSectionSet):
        for i in range(len(dbCrossSectionSet)):
            spaceVector = []
            parameterList = [] 
            parameters = self.parse_whole(dbCrossSectionSet[i][0], [10, 70])

            for j in range(1,len(dbCrossSectionSet[i])):
                parameters = self.parse_whole(dbCrossSectionSet[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_CROSS_SECTION_SET_ID\n")            
            for j in range(len(parameter)):
                if j == 0:
                    stream.write("$$      ID   HEADING\n")
                elif j == 1:
                    stream.write("$$    NSID      HSID      BSID      SSID      TSID      DSID        ID     ITYPE\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseCrossSectionPlane(DynaKeyword):
    def __init__(self):
        super(DatabaseCrossSectionPlane,self).__init__("DATABASE_CROSS_SECTION_PLANE")
    
    def parse(self, dbCrossSectionPlaneID):
        for i in range(len(dbCrossSectionPlaneID)):
            parameterList = [] 
            parameters = self.parse_whole(dbCrossSectionPlaneID[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(dbCrossSectionPlaneID[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_CROSS_SECTION_PLANE\n")            
            for j in range(len(parameter)):
                if j == 0:
                    stream.write("$$    PSID       XCT       YCT       ZCT       XCH       YCH       ZCH    RADIUS\n")
                elif j == 1:
                    stream.write("$$    XHEV      YHEV      ZHEV      LENL      LENM        ID     ITYPE\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseCrossSectionPlaneID(DynaKeyword):
    def __init__(self):
        super(DatabaseCrossSectionPlaneID,self).__init__("DATABASE_CROSS_SECTION_PLANE_ID")

    def parse(self, dbCrossSectionPlaneID):
        for i in range(len(dbCrossSectionPlaneID)):
            parameterList = [] 
            parameters = self.parse_whole(dbCrossSectionPlaneID[i][0], [10, 70])
            parameterList.append(parameters)
            parameters = self.parse_whole(dbCrossSectionPlaneID[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(dbCrossSectionPlaneID[i][2], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_CROSS_SECTION_PLANE_ID\n")
            stream.write("$$      ID\n")
            for j in range(len(parameter)):
                if j == 0:
                    stream.write("$$    CSID   HEADING\n")
                elif j == 1:
                    stream.write("$$    PSID       XCT       YCT       ZCT       XCH       YCH       ZCH    RADIUS\n")
                elif j == 2:
                    stream.write("$$    XHEV      YHEV      ZHEV      LENL      LENM        ID     ITYPE\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseDeforc(DynaKeyword):
    def __init__(self):
        super(DatabaseDeforc,self).__init__("DATABASE_DEFORC")
    
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)

    def DT(self):
        return self.parameters[0][0]
    
    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*DATABASE_DEFORC\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)
        

class DatabaseElout(DynaKeyword):
    def __init__(self):
        super(DatabaseElout,self).__init__("DATABASE_ELOUT")
        
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)

    def AddDatabaseElout(self, DT, BINARY, LCUR, IOOPT, OPTION1="", OPTION2="", OPTION3="", OPTION4=""):
        self.parameters = []
        parameters = [DT, BINARY, LCUR, IOOPT, OPTION1, OPTION2, OPTION3, OPTION4]
        self.parameters.append(parameters)
    
    def getDatabaseElout(self):
        parameters = []
        parameters.append("*DATABASE_ELOUT")
        parameters.append(self.parameters[0])
        return parameters

    def DT(self):
        return self.parameters[0][0]

    def BINARY(self):
        return self.parameters[0][1]

    def LCUR(self):
        return self.parameters[0][2]

    def IOOPT(self):
        return self.parameters[0][3]

    def OPTION1(self):
        return self.parameters[0][4]
    
    def OPTION2(self):
        return self.parameters[0][5]
    
    def OPTION3(self):
        return self.parameters[0][6]
    
    def OPTION4(self):
        return self.parameters[0][7]
    
    def write(self, stream):
        stream.write("*DATABASE_ELOUT\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT   OPTION1   OPTION2   OPTION3   OPTION4\n")
        self.writeParameters(stream)

class DatabaseFrequencyBinaryD3SSD(DynaKeyword):
    def __init__(self):
        super(DatabaseFrequencyBinaryD3SSD,self).__init__("DATABASE_FREQUENCY_BINARY_D3SSD")
    
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10])
        self.parameters.append(parameters)
        parameters = self.parse_whole(lines[0][1], [10, 10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def write(self, stream):
        stream.write("*DATABASE_FREQUENCY_BINARY_D3SSD\n")
        parameters = self.parameters[0]
        formatted_elements = f"{str(parameters[0]):>10}\n"
        stream.write(formatted_elements)
        stream.write("$$    FMIN      FMAX     NFREQ    FSPACE    LCFREQ")
        parameters = self.parameters[1]
        formatted_elements = f"{str(parameters[0]):>10}{str(parameters[1]):>10}{str(parameters[2]):>10}{str(parameters[3]):>10}{str(parameters[4]):>10}\n"
        stream.write(formatted_elements)

class DatabaseGlstat(DynaKeyword):
    def __init__(self):
        super(DatabaseGlstat,self).__init__("DATABASE_GLSTAT")
       
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseGlstat(self):
        parameters = []
        parameters.append("*DATABASE_GLSTAT")
        parameters.append(self.parameters[0])
        return parameters
        
    def DT(self):
        return self.parameters[0][0]
    
    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*DATABASE_GLSTAT\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)

class DatabaseMatsum(DynaKeyword):
    def __init__(self):
        super(DatabaseMatsum,self).__init__("DATABASE_MATSUM")
       
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseMatsum(self):
        parameters = []
        parameters.append("*DATABASE_MATSUM")
        parameters.append(self.parameters[0])
        return parameters
    
    def DT(self):
        return self.parameters[0][0]
    
    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*DATABASE_MATSUM\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)

class DatabaseNcforc(DynaKeyword):
    def __init__(self):
        super(DatabaseNcforc,self).__init__("DATABASE_NCFORC")
        
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)

    def DT(self):
        return self.parameters[0][0]

    def BINARY(self):
        return self.parameters[0][1]

    def LCUR(self):
        return self.parameters[0][2]

    def IOOPT(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*DATABASE_NCFORC\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)

class DatabaseNodalForceGroup(DynaKeyword):
    def __init__(self):
        super(DatabaseNodalForceGroup,self).__init__("DATABASE_NODAL_FORCE_GROUP")
        
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10])
        self.parameters.append(parameters)       
    
    def getDatabaseNodalForceGroup(self):
        parameters = []
        parameters.append("*DATABASE_NODAL_FORCE_GROUP")
        parameters.append(self.parameters[0])
        return parameters
    
    def write(self, stream):
        stream.write("*DATABASE_NODAL_FORCE_GROUP\n")
        stream.write("$$    NSID       CID\n")
        self.writeParameters(stream)

class DatabaseNodfor(DynaKeyword):
    def __init__(self):
        super(DatabaseNodfor,self).__init__("DATABASE_NODFOR")
    
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseNodfor(self):
        parameters = []
        parameters.append("*DATABASE_NODFOR")
        parameters.append(self.parameters[0])
        return parameters
    
    def write(self, stream):
        stream.write("*DATABASE_NODFOR\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT   OPTION1   OPTION2   OPTION3   OPTION4\n")
        self.writeParameters(stream)        
    
class DatabaseNodout(DynaKeyword):
    def __init__(self):       
        super(DatabaseNodout,self).__init__("DATABASE_NODOUT")
      
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseNodout(self):
        parameters = []
        parameters.append("*DATABASE_NODOUT")
        parameters.append(self.parameters[0])
        return parameters    

    def AddDatabaseNodout(self, DT, BINARY, LCUR, IOOPT, DTHF="", BINHF=""):
        
        parameter = [DT, BINARY, LCUR, IOOPT, DTHF, BINHF]
        self.parameters.append(parameter)

    def DT(self):
        return self.parameters[0][0]
    
    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def DTHF(self):
        return self.parameters[0][4]
    
    def BINHF(self):
        return self.parameters[0][5]
    
    def write(self, stream):
        stream.write("*DATABASE_NODOUT\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT      DTHF     BINHF\n")
        self.writeParameters(stream)

class DatabaseRbdout(DynaKeyword):
    def __init__(self):
        super(DatabaseRbdout,self).__init__("DATABASE_RBDOUT")
          
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)
        
    def getDatabaseRbdout(self):
        parameters = []
        parameters.append("*DATABASE_RBDOUT")
        parameters.append(self.parameters[0])
        return parameters
    
    def AddDatabaseRbdout(self, DT, BINARY, LCUR, IOOPT):
        parameter = [DT, BINARY, LCUR, IOOPT]
        self.parameters.append(parameter)            

    def DT(self):
        return self.parameters[0][0]
    
    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*DATABASE_RBDOUT\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)

class DatabaseRcforc(DynaKeyword):
    def __init__(self):
        super(DatabaseRcforc,self).__init__("DATABASE_RCFORC")
    
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseRcforce(self):
        parameters = []
        parameters.append("*DATABASE_RCFORC")
        parameters.append(self.parameters[0])
        return parameters

    def DT(self):
        return self.parameters[0][0]
    
    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*DATABASE_RCFORC\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)

class DatabaseRwforc(DynaKeyword):
    def __init__(self):
        super(DatabaseRwforc,self).__init__("DATABASE_RWFORC")
        
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseRwforc(self):
        parameters = []
        parameters.append("*DATABASE_RWFORC")
        parameters.append(self.parameters[0])
        return parameters
    
    def DT(self):
        return self.parameters[0][0]
    
    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*DATABASE_RWFORC\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)

class DatabaseSecforc(DynaKeyword):
    def __init__(self):
        super(DatabaseSecforc,self).__init__("DATABASE_SECFORC")
            
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def DT(self):
        return self.parameters[0][0]
    
    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*DATABASE_SECFORC\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)
    
class DatabaseSpcforc(DynaKeyword):
    def __init__(self):
        super(DatabaseSpcforc,self).__init__("DATABASE_SPCFORC")
        
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseSpcforc(self):
        parameters = []
        parameters.append("*DATABASE_SPCFORC")
        parameters.append(self.parameters[0])
        return parameters
    
    def write(self, stream):
        stream.write("*DATABASE_SPCFORC\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)

class DatabaseSleout(DynaKeyword):
    def __init__(self):
        super(DatabaseSleout,self).__init__("DATABASE_SLEOUT")
        
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10])
        self.parameters.append(parameters)
        
    def getDatabaseSleout(self):
        parameters = []
        parameters.append("*DATABASE_SLEOUT")
        parameters.append(self.parameters[0])
        return parameters    
    
    def DT(self):
        return self.parameters[0][0]
    
    def BINARY(self):
        return self.parameters[0][1]
    
    def LCUR(self):        
        return self.parameters[0][2]
    
    def IOOPT(self):
        return self.parameters[0][3]
    
    def write(self, stream):
        stream.write("*DATABASE_SLEOUT\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT\n")
        self.writeParameters(stream)        

class DatabaseSwforc(DynaKeyword):
    def __init__(self):
        super(DatabaseSwforc,self).__init__("DATABASE_SWFORC")
        
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def write(self, stream):
        stream.write("*DATABASE_SWFORC\n")
        stream.write("$$      DT    BINARY      LCUR     IOOPT   OPTION1   OPTION2   OPTION3   OPTION4\n")        
        self.writeParameters(stream)

class DatabaseBinaryD3plot(DynaKeyword):
    def __init__(self):
        super(DatabaseBinaryD3plot,self).__init__("DATABASE_BINARY_D3PLOT")
           
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)

    def AddDatabaseBinaryD3plot(self, DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID=0):
        self.parameters = []
        parameters = [DTCYCL, LCDT, BEAM, NPLTC, PSETID,CID]
        self.parameters.append(parameters)

    def getDatabaseBinaryD3plot(self):
        parameters = [] 
        parameters.append("*DATABASE_BINARY_D3PLOT")
        parameters.append(self.parameters[0])
        return parameters

    def DTCYCL(self):
        return self.parameters[0][0]

    def LCDT(self):
        return self.parameters[0][1]
    
    def BEAM(self):
        return self.parameters[0][2]
    
    def NPLTC(self):
        return self.parameters[0][3]
    
    def PSETID(self):
        return self.parameters[0][4]

    def CID(self):
        return self.parameters[0][5]
    
    def write(self, stream):
        stream.write("*DATABASE_BINARY_D3PLOT\n")
        stream.write("$$  DTCYCL      LCDT      BEAM     NPLTC    PSETID       CID\n")
        self.writeParameters(stream)

class DatabaseBinaryD3thdt(DynaKeyword):
    def __init__(self):
        super(DatabaseBinaryD3thdt,self).__init__("DATABASE_BINARY_D3THDT")
    
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        
    def AddDatabaseBinaryD3thdt(self, DTCYCL, LCDT, BEAM, NPLTC, PSETID, CID=0):
        self.parameters = []
        parameters = [DTCYCL, LCDT, BEAM, NPLTC, PSETID,CID]
        self.parameters.append(parameters)
    
    def getDatabaseBinaryD3thdt(self):
        parameters = [] 
        parameters.append("*DATABASE_BINARY_D3THDT")
        parameters.append(self.parameters[0])
        return parameters

    def DTCYCL(self):
        return self.parameters[0][0]

    def LCDT(self):
        return self.parameters[0][1]

    def BEAM(self):
        return self.parameters[0][2]
    
    def NPLTC(self):
        return self.parameters[0][3]
    
    def PSETID(self):
        return self.parameters[0][4]

    def CID(self):
        return self.parameters[0][5]
    
    def write(self, stream):
        stream.write("*DATABASE_BINARY_D3THDT\n")
        stream.write("$$  DTCYCL      LCDT      BEAM     NPLTC    PSETID       CID\n")
        self.writeParameters(stream)

class DatabaseBinaryD3Dump(DynaKeyword):
    def __init__(self):
        super(DatabaseBinaryD3Dump,self).__init__("DATABASE_BINARY_D3DUMP")
      
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseBinaryD3dump(self):
        parameter = [] 
        parameter.append("*DATABASE_BINARY_D3DUMP")
        parameter.append(self.parameters[0])
        return parameter

    def DTCYCL(self):
        return self.parameters[0][0]

    def NR(self):
        return self.parameters[0][1]
    
    def write(self, stream):
        stream.write("*DATABASE_BINARY_D3DUMP\n")
        stream.write("$$  DTCYCL        NR\n")
        self.writeParameters(stream)

class DatabaseBinaryRunrsf(DynaKeyword):
    def __init__(self):
        super(DatabaseBinaryRunrsf,self).__init__("DATABASE_BINARY_RUNRSF")
      
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10])
        self.parameters.append(parameters)

    def DTCYCL(self):
        return self.parameters[0][0]

    def LCDTNR(self):
        return self.parameters[0][1]
    
    def write(self, stream):
        stream.write("*DATABASE_BINARY_RUNRSF\n")
        stream.write("$$  DTCYCL    LCDTNR\n")
        self.writeParameters(stream)

class DatabaseBinaryIntfor(DynaKeyword):
    def __init__(self):
        super(DatabaseBinaryIntfor,self).__init__("DATABASE_BINARY_INTFOR")
      
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10])
        if len(lines[0]) > 1:
            parameters = self.parse_whole(lines[0][1], [10])
        self.parameters.append(parameters)    

    def getDatabaseBinaryIntfor(self):
        parameters = []
        parameters.append("*DATABASE_BINARY_INTFOR")
        parameters.append(self.parameters[0])
        if len(self.parameters) > 1:
            parameters.append(self.parameters[1])
        return parameters
        
    def DTCYCL(self):
        return self.parameters[0][0]

    def LCID(self):
        return self.parameters[0][1]
    
    def write(self, stream):
        stream.write("*DATABASE_BINARY_INTFOR\n")
        stream.write("$$  DTCYCL      LCID      BEAM     NPLTC    PSETID       CID\n")
        
        self.writeParameters(stream)

class DatabaseBinaryIntforFile(DynaKeyword):
    def __init__(self):
        super(DatabaseBinaryIntforFile,self).__init__("DATABASE_BINARY_INTFOR_FILE")
    
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10])
        parameters = self.parse_whole(lines[0][0], [80])
        self.parameters.append(parameters)
        parameters = self.parse_whole(lines[0][1], [10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        parameters = self.parse_whole(lines[0][2], [10])
        self.parameters.append(parameters)        

    def getDatabaseBinaryIntforFile(self):
        parameters = []
        parameters.append("*DATABASE_BINARY_INTFOR_FILE")
        parameters.append(self.parameters[0])
        parameters.append(self.parameters[1])
        parameters.append(self.parameters[2])
        return parameters
    
    def write(self, stream):
        stream.write("*DATABASE_BINARY_INTFOR_FILE\n")
        stream.write("$$                                                                      FILENAME\n")
        self.writeParameter(stream,0)
        stream.write("$$  DTCYCL      LCID      BEAM     NPLTC    PSETID       CID\n")
        self.writeParameter(stream,1)
        stream.write("$$   IOOPT\n")
        self.writeParameter(stream,2)
             
class DatabaseExtentBinary(DynaKeyword):
    def __init__(self):
        super(DatabaseExtentBinary,self).__init__("DATABASE_EXTENT_BINARY")
       
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        #parameters = lines[0][1].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
        parameters = self.parse_whole(lines[0][1], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getDatabaseExtentBinary(self):
        parameters = []
        parameters.append("*DATABASE_EXTENT_BINARY")
        parameters.append(self.parameters[0])
        parameters.append(self.parameters[1])
        return parameters    
    
    def NEIPH(self):
        return self.parameters[0][0]
    
    def NEIPS(self):
        return self.parameters[0][1]
    
    def MAXINT(self):
        return self.parameters[0][2]
    
    def STRFLG(self):
        return self.parameters[0][3]
    
    def SIGFLG(self):
        return self.parameters[0][4]
    
    def EPSFLG(self):
        return self.parameters[0][5]
    
    def RLTFLG(self):
        return self.parameters[0][6]
    
    def ENGFLG(self):
        return self.parameters[0][7]
    
    def CMPFLG(self):
        return self.parameters[1][0]
    
    def IEVERP(self):
        return self.parameters[1][1]
    
    def BEAMIP(self):
        return self.parameters[1][2]
    
    def DCOMP(self):
        return self.parameters[1][3]
    
    def SHGE(self):
        return self.parameters[1][4]
    
    def STSSZ(self):
        return self.parameters[1][5]
    
    def N3THDT(self):
        return self.parameters[1][6]
    
    def IALEMAT(self):
        return self.parameters[1][7]
    
    def write(self, stream):
        stream.write("*DATABASE_EXTENT_BINARY\n")
        stream.write("$$   NEIPH     NEIPS    MAXINT    STRFLG    SIGFLG    EPSFLG    RLTFLG    ENGFLG\n")
        self.writeParameter(stream,0)
        stream.write("$$  CMPFLG    IEVERP    BEAMIP     DCOMP      SHGE     STSSZ    N3THDT   IALEMAT\n")
        self.writeParameter(stream,1)

class DatabaseExtentIntfor(DynaKeyword):
    def __init__(self):
        super(DatabaseExtentIntfor,self).__init__("DATABASE_EXTENT_INTFOR")
    
    def parse(self, lines):
        parameters = self.parse_whole(lines[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        parameters = self.parse_whole(lines[0][1], [10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
        
    def getDatabaseExtentIntfor(self):
        parameters = []
        parameters.append("*DATABASE_EXTENT_INTFOR")
        parameters.append(self.parameters[0])
        parameters.append(self.parameters[1])
        return parameters    
    
    def write(self, stream):
        stream.write("*DATABASE_EXTENT_INTFOR\n")
        stream.write("$$   NGLBV     NVELO    NPRESU    NSHEAR     NFORC     NGAPC     NFAIL    IEVERF\n")
        self.writeParameter(stream,0)
        stream.write("$$   NWEAR     NWUSR      NHUF     NTIED      NENG      NPEN\n")
        self.writeParameter(stream,1)
        
class DatabaseFormat(DynaKeyword):
    def __init__(self):
        super(DatabaseFormat,self).__init__("DATABASE_FORMAT")
       
    def parse(self, lines):
        #parameters = lines[0][0].parse_whole([10, 10])
        parameters = self.parse_whole(lines[0][0], [10, 10])
        self.parameters.append(parameters)
    
    def IFORM(self):
        return self.parameters[0][0]
    
    def IBINARY(self):
        return self.parameters[0][1]
    
    def write(self, stream):
        stream.write("*DATABASE_FORMAT\n")
        stream.write("$$   IFORM   IBINARY\n")
        self.writeParameters(stream)

class DatabaseHistoryNode(DynaKeyword):
    def __init__(self):
        super(DatabaseHistoryNode,self).__init__("DATABASE_HISTORY_NODE")

    def parse(self, databaseHistoryNodeKeywords):
        for i in range(len(databaseHistoryNodeKeywords)):
            spaceVector = []
            parameterList = [] 
            for j in range(len(databaseHistoryNodeKeywords[i])):
                if j == 0:
                    curStrVector = str(databaseHistoryNodeKeywords[i][j])
                    length = len(curStrVector)/10
                    spaceVector = [10] * int(length)
                parameters = self.parse_whole(databaseHistoryNodeKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getDatabaseHistoryNode(self):
        historyNodeList = [] 
        historyNodeList.append("*DATABASE_HISTORY_NODE")
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                historyNodeList.append(parameter[j])            
        return historyNodeList           

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_HISTORY_NODE\n")
            stream.write("$$     ID1       ID2       ID3       ID4       ID5       ID6       ID7       ID8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseHistoryBeam(DynaKeyword):
    def __init__(self):
        super(DatabaseHistoryBeam,self).__init__("DATABASE_HISTORY_BEAM")
    
    def parse(self, databaseHistoryBeamKeywords):
        for i in range(len(databaseHistoryBeamKeywords)):
            spaceVector = []
            parameterList = []
            for j in range(len(databaseHistoryBeamKeywords[i])):
                if j == 0:
                    curStrVector = str(databaseHistoryBeamKeywords[i][j])
                    length = len(curStrVector)/10
                    spaceVector = [10] * int(length)
                parameters = self.parse_whole(databaseHistoryBeamKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getDatabaseHistoryBeam(self):
        historyBeamList = []
        historyBeamList.append("*DATABASE_HISTORY_BEAM")
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                historyBeamList.append(parameter[j])
        return historyBeamList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_HISTORY_BEAM\n")
            stream.write("$$     ID1       ID2       ID3       ID4       ID5       ID6       ID7       ID8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseHistoryBeamSet(DynaKeyword):
    def __init__(self):
        super(DatabaseHistoryBeamSet,self).__init__("DATABASE_HISTORY_BEAM_SET")

    def parse(self, databaseHistoryBeamSetKeywords):
        for i in range(len(databaseHistoryBeamSetKeywords)):
            spaceVector = []
            parameterList = []
            for j in range(len(databaseHistoryBeamSetKeywords[i])):
                if j == 0:
                    curStrVector = str(databaseHistoryBeamSetKeywords[i][j])
                    length = len(curStrVector)/10
                    spaceVector = [10] * int(length)
                parameters = self.parse_whole(databaseHistoryBeamSetKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getDatabaseHistoryBeamSet(self):
        historyBeamSetList = []
        historyBeamSetList.append("*DATABASE_HISTORY_BEAM_SET")
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                historyBeamSetList.append(parameter[j])
        return historyBeamSetList    
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_HISTORY_BEAM_SET\n")
            stream.write("$$     ID1       ID2       ID3       ID4       ID5       ID6       ID7       ID8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")   

class DatabaseHistoryShell(DynaKeyword):
    def __init__(self):
        super(DatabaseHistoryShell,self).__init__("DATABASE_HISTORY_SHELL")
    
    def parse(self, databaseHistoryShellKeywords):
        for i in range(len(databaseHistoryShellKeywords)):
            spaceVector = []
            parameterList = []
            for j in range(len(databaseHistoryShellKeywords[i])):
                if j == 0:
                    curStrVector = str(databaseHistoryShellKeywords[i][j])
                    length = len(curStrVector)/10
                    spaceVector = [10] * int(length)
                parameters = self.parse_whole(databaseHistoryShellKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getDatabaseHistoryShell(self):
        historyShellList = []
        historyShellList.append("*DATABASE_HISTORY_SHELL")
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                historyShellList.append(parameter[j])
        return historyShellList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_HISTORY_SHELL\n")
            stream.write("$$     ID1       ID2       ID3       ID4       ID5       ID6       ID7       ID8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseHistoryShellSet(DynaKeyword):
    def __init__(self):
        super(DatabaseHistoryShellSet,self).__init__("DATABASE_HISTORY_SHELL_SET")
    
    def parse(self, databaseHistoryShellKeywords):
        for i in range(len(databaseHistoryShellKeywords)):
            spaceVector = []
            parameterList = []
            for j in range(len(databaseHistoryShellKeywords[i])):
                if j == 0:
                    curStrVector = str(databaseHistoryShellKeywords[i][j])
                    length = len(curStrVector)/10
                    spaceVector = [10] * int(length)
                parameters = self.parse_whole(databaseHistoryShellKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getDatabaseHistoryShellSet(self):
        historyShellSetList = []
        historyShellSetList.append("*DATABASE_HISTORY_SHELL_SET")
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                historyShellSetList.append(parameter[j])
        return historyShellSetList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_HISTORY_SHELL_SET\n")
            stream.write("$$     ID1       ID2       ID3       ID4       ID5       ID6       ID7       ID8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseHistorySolid(DynaKeyword):
    def __init__(self):
        super(DatabaseHistorySolid,self).__init__("DATABASE_HISTORY_SOLID")

    def parse(self, databaseHistorySolidKeywords):
        for i in range(len(databaseHistorySolidKeywords)):
            spaceVector = []
            parameterList = []
            for j in range(len(databaseHistorySolidKeywords[i])):
                if j == 0:
                    curStrVector = str(databaseHistorySolidKeywords[i][j])
                    length = len(curStrVector)/10
                    spaceVector = [10] * int(length)
                parameters = self.parse_whole(databaseHistorySolidKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getDatabaseHistorySolid(self):
        historySolidList = []
        historySolidList.append("*DATABASE_HISTORY_SOLID")
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                historySolidList.append(parameter[j])
        return historySolidList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_HISTORY_SOLID\n")
            stream.write("$$     ID1       ID2       ID3       ID4       ID5       ID6       ID7       ID8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseHistorySolidSet(DynaKeyword):
    def __init__(self):
        super(DatabaseHistorySolidSet,self).__init__("DATABASE_HISTORY_SOLID_SET")

    def parse(self, databaseHistorySolidKeywords):
        for i in range(len(databaseHistorySolidKeywords)):
            spaceVector = []
            parameterList = []
            for j in range(len(databaseHistorySolidKeywords[i])):
                if j == 0:
                    curStrVector = str(databaseHistorySolidKeywords[i][j])
                    length = len(curStrVector)/10
                    spaceVector = [10] * int(length)
                parameters = self.parse_whole(databaseHistorySolidKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getDatabaseHistorySolidSet(self):
        historySolidSetList = []
        historySolidSetList.append("*DATABASE_HISTORY_SOLID_SET")
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                historySolidSetList.append(parameter[j])
        return historySolidSetList
                    
            
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_HISTORY_SOLID_SET\n")
            stream.write("$$     ID1       ID2       ID3       ID4       ID5       ID6       ID7       ID8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DatabaseHistoryNodeSet(DynaKeyword):
    def __init__(self):
        super(DatabaseHistoryNodeSet,self).__init__("DATABASE_HISTORY_NODE_SET")

    def parse(self, databaseHistoryNodeSetKeywords):
        for i in range(len(databaseHistoryNodeSetKeywords)):
            spaceVector = []
            parameterList = [] 
            for j in range(len(databaseHistoryNodeSetKeywords[i])):
                if j == 0:
                    curStrVector = str(databaseHistoryNodeSetKeywords[i][j])
                    length = len(curStrVector)/10
                    spaceVector = [10] * int(length)
                parameters = self.parse_whole(databaseHistoryNodeSetKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getDatabaseHistoryNodeSet(self):
        historyNodeSetList = []
        historyNodeSetList.append("*DATABASE_HISTORY_NODE_SET")
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            for j in range(len(parameter)):
                historyNodeSetList.append(parameter[j])
        return historyNodeSetList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DATABASE_HISTORY_NODE_SET\n")
            stream.write("$$     ID1       ID2       ID3       ID4       ID5       ID6       ID7       ID8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DefineBox(DynaKeyword):
    def __init__(self):
        super(DefineBox,self).__init__("DEFINE_BOX")
    
    def parse(self, defineBoxKeywords):
        for i in range(len(defineBoxKeywords)):
            parameterList = [] 
            parameters = self.parse_whole(defineBoxKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DEFINE_BOX\n")
            stream.write("$$   BOXID      XMIN      XMAX      YMIN      YMAX      ZMIN      ZMAX\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DefineCoordinateSystem(DynaKeyword):
    def __init__(self):
        super(DefineCoordinateSystem,self).__init__("DEFINE_COORDINATE_SYSTEM")
    
    def parse(self, defineCoordinateSystemKeywords):
        for i in range(len(defineCoordinateSystemKeywords)):
            parameterList = []
            parameters = self.parse_whole(defineCoordinateSystemKeywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(defineCoordinateSystemKeywords[i][1], [10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getDefineCoordinateSystemList(self):
        defineCoordinateSystemList = []
        for i in range(len(self.parameters)):
            curDefineCoordinateSystem = []
            curDefineCoordinateSystem.append("*DEFINE_COORDINATE_SYSTEM")
            curDefineCoordinateSystem.append(self.parameters[i])
            defineCoordinateSystemList.append(curDefineCoordinateSystem)
        return defineCoordinateSystemList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DEFINE_COORDINATE_SYSTEM\n")
            stream.write("$$     CID        XO        YO        ZO        XL        YL        ZL      CIDL\n")            
            formatted_elements =  f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"            
            stream.write(formatted_elements)
            stream.write("$$      XP        YP        ZP\n")    
            formatted_elements =  f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}\n"
            stream.write(formatted_elements)

class DefineCoordinateSystemTitle(DynaKeyword):
    def __init__(self):
        super(DefineCoordinateSystemTitle,self).__init__("DEFINE_COORDINATE_SYSTEM_TITLE")
    
    def parse(self, defineCoordinateSystemKeywords):
        for i in range(len(defineCoordinateSystemKeywords)):
            curDefineCoordinateSystem = defineCoordinateSystemKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curDefineCoordinateSystem[0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(curDefineCoordinateSystem[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curDefineCoordinateSystem[2], [10, 10, 10])       
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddDefineCoordinateSystemTitle(self, title, CID, XO, YO, ZO, XL, YL, ZL, CIDL, XP, YP, ZP):
        parameterList = []
        parameterList.append(title)
        parameterList.append([CID, XO, YO, ZO, XL, YL, ZL, CIDL])
        parameterList.append([XP, YP, ZP])
        self.parameters.append(parameterList)


    def getDefineCoordinateSystemTitleList(self):
        defineCoordinateSystemTitleList = []
        for i in range(len(self.parameters)):
            curDefineCoordinateSystemTitle = []
            curDefineCoordinateSystemTitle.append("*DEFINE_COORDINATE_SYSTEM_TITLE")
            curDefineCoordinateSystemTitle.append(self.parameters[i])
            defineCoordinateSystemTitleList.append(curDefineCoordinateSystemTitle)
        return defineCoordinateSystemTitleList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DEFINE_COORDINATE_SYSTEM_TITLE\n")
            stream.write("$$                                                                         80 characters TITLE\n")
            if "\n" in parameter[0][0]:
                stream.write("{name}".format(name=parameter[0][0]))
            else:
                stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$    CID        XO        YO        ZO        XL        YL        ZL      CIDL\n")
            formatted_elements =  f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"            
            stream.write(formatted_elements)
            stream.write("$$      XP        YP        ZP\n")    
            formatted_elements =  f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}\n"
            stream.write(formatted_elements)

class DefineCurve(DynaKeyword):
    def __init__(self):
        super(DefineCurve,self).__init__("DEFINE_CURVE")
    
    def parse(self, defineCurveKeywords):
        for i in range(len(defineCurveKeywords)):
            curDefineCurve = defineCurveKeywords[i]            
            parameterList = []
            parameters = self.parse_whole(curDefineCurve[0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1, len(curDefineCurve)):
                parameters = self.parse_whole(curDefineCurve[j], [20, 20])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddDefineCurve(self, LCID, SIDR, SFA, SFO, OFFA, OFFO, DATTYP, LCINT, A1List, O1List):
        parameterList = [] 
        parameterList.append([LCID, SIDR, SFA, SFO, OFFA, OFFO, DATTYP, LCINT])        
        for i in range(len(A1List)):
            parameters = [A1List[i], O1List[i]]
            parameterList.append(parameters)
        self.parameters.append(parameterList)
    
    def getDefineCurveList(self):        
        defineCurveList = []         
        for i in range(len(self.parameters)):            
            curDefineCurve = []             
            curDefineCurve.append("*DEFINE_CURVE")            
            curDefineCurve.append(self.parameters[i])
            defineCurveList.append(curDefineCurve)
        return defineCurveList    

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DEFINE_CURVE\n")
            for j in range(len(parameter)):
                if j == 0:
                    stream.write("$$    LCID      SIDR       SFA       SFO      OFFA      OFFO    DATTYP     LCINT\n")
                elif j == 1:
                    stream.write("$$                A1                  O1\n")            

                for k in range(len(parameter[j])):
                    if j == 0:
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                    else:
                        formatted_elements = f"{str(parameter[j][k]):>20}"
                    stream.write(formatted_elements)
                stream.write("\n")

class DefineCurveTitle(DynaKeyword):
    def __init__(self):
        super(DefineCurveTitle,self).__init__("DEFINE_CURVE_TITLE")
    
    def parse(self, defineCurveKeywords):
        for i in range(len(defineCurveKeywords)):
            curDefineCurve = defineCurveKeywords[i]            
            parameterList = []
            parameters = self.parse_whole(curDefineCurve[0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(curDefineCurve[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(2, len(curDefineCurve)):
                parameters = self.parse_whole(curDefineCurve[j], [20, 20])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def AddDefineCurveTitle(self, title, LCID, SIDR, SFA, SFO, OFFA, OFFO, DATTYP, LCINT, A1List, O1List):
        parameterList = [] 
        parameterList.append(title)
        parameterList.append([LCID, SIDR, SFA, SFO, OFFA, OFFO, DATTYP, LCINT])        
        for i in range(len(A1List)):
            parameters = [A1List[i], O1List[i]]
            parameterList.append(parameters)
        self.parameters.append(parameterList)
        
    def getDefineCurveList(self):        
        defineCurveList = []         
        for i in range(len(self.parameters)):            
            curDefineCurve = []             
            curDefineCurve.append("*DEFINE_CURVE_TITLE")                        
            curDefineCurve.append(self.parameters[i])
            defineCurveList.append(curDefineCurve)
        return defineCurveList    

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*DEFINE_CURVE_TITLE\n")
            stream.write("$$                                                                         TITLE\n")
            if "\n" in parameter[0][0]:
                stream.write("{name}".format(name=parameter[0][0]))
            else:
                stream.write("{name}\n".format(name=parameter[0][0]))            
            for j in range(1,len(parameter)):
                if j == 1: 
                    stream.write("$$    LCID      SIDR       SFA       SFO      OFFA      OFFO    DATTYP     LCINT\n")
                elif j == 2:
                    stream.write("$$                A1                  O1\n")
                
                for k in range(len(parameter[j])):                    
                    if j == 1:
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                    else:
                        formatted_elements = f"{str(parameter[j][k]):>20}"
                    stream.write(formatted_elements)
                stream.write("\n")

class ElementMass(DynaKeyword):
    def __init__(self):
        super(ElementMass,self).__init__("ELEMENT_MASS")
    
    def parse(self, elementMassKeywords):
        for i in range(len(elementMassKeywords)):
            parameterList = [] 
            for j in range(len(elementMassKeywords[i])):                                
                parameters = self.parse_whole(elementMassKeywords[i][j], [8,8,16,8])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*ELEMENT_MASS\n")
            stream.write("$$   EID      ID            MASS     PID\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>8}"
                    stream.write(formatted_elements)
                stream.write("\n")

class ElementMassNodeSet(DynaKeyword):
    def __init__(self):
        super(ElementMassNodeSet,self).__init__("ELEMENT_MASS_NODE_SET")
    
    def parse(self, elementMassNodeSetKeywords):
        for i in range(len(elementMassNodeSetKeywords)):
            parameterList = [] 
            for j in range(len(elementMassNodeSetKeywords[i])):                                
                parameters = self.parse_whole(elementMassNodeSetKeywords[i][j], [8,8,16,8])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*ELEMENT_MASS_NODE_SET\n")
            stream.write("$$   EID      ID            MASS     PID\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>8}"
                    stream.write(formatted_elements)
                stream.write("\n")

class ElementBeam(DynaKeyword):
    def __init__(self):
        super(ElementBeam,self).__init__("ELEMENT_BEAM")
    
    def parse(self, elementBeamKeywords):
        for i in range(len(elementBeamKeywords)):
            spaceVector = []
            parameterList = [] 
            for j in range(len(elementBeamKeywords[i])):
                if j == 0:
                    curStrVector = str(elementBeamKeywords[i][j])
                    length = len(curStrVector)/8
                    spaceVector = [8] * int(length)
                parameters = self.parse_whole(elementBeamKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*ELEMENT_BEAM\n")
            stream.write("$$   EID     PID      N1      N2      N3     RT1     RR1     RT2     RR2   LOCAL\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>8}"
                    stream.write(formatted_elements)
                stream.write("\n")

class ElementShell(DynaKeyword):
    def __init__(self):
        super(ElementShell,self).__init__("ELEMENT_SHELL")

    def parse(self, elementShellKeywords):
        for i in range(len(elementShellKeywords)):
            spaceVector = []
            parameterList = [] 
            for j in range(len(elementShellKeywords[i])):
                if j == 0:
                    curStrVector = str(elementShellKeywords[i][j])
                    length = len(curStrVector)/8
                    spaceVector = [8] * int(length)
                #parameters = elementShellKeywords[i][j].parse_whole(spaceVector)
                parameters = self.parse_whole(elementShellKeywords[i][j], spaceVector)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def EID(self,ith,jth):
        return self.parameters[ith][jth][0]
    
    def PID(self,ith,jth):
        return self.parameters[ith][jth][1]
    
    def N(self,ith,jth):
        return self.parameters[ith][jth][2:]

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*ELEMENT_SHELL\n")
            stream.write("$$   EID     PID      N1      N2      N3      N4      N5      N6      N7      N8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>8}"
                    stream.write(formatted_elements)
                stream.write("\n")

class ElementShellThickness(DynaKeyword):
    def __init__(self):
        super(ElementShellThickness,self).__init__("ELEMENT_SHELL_THICKNESS")
    
    def parse(self, elementShellThickKeywords):
        for i in range(len(elementShellThickKeywords)):
            spaceVector1 = []
            spaceVector2 = []
            spaceVector3 = [] 
            parameterList = []
            mode = 1
            if len(elementShellThickKeywords[i])>1:
                curStrVector = str(elementShellThickKeywords[i][0])
                length = len(curStrVector)/8
                spaceVector1 = [8] * int(length)
                parameters1 = self.parse_whole(elementShellThickKeywords[i][0], spaceVector1)
                if length > 7 and int(parameters1[6])>0:
                    mode = 2
            if mode == 1:
                for j in range(0,len(elementShellThickKeywords[i]),2):
                    if j == 0:
                        curStrVector = str(elementShellThickKeywords[i][j])
                        length = len(curStrVector)/8
                        spaceVector1 = [8] * int(length)
                        curStrVector2 = str(elementShellThickKeywords[i][j+1])
                        length2 = len(curStrVector2)/16
                        spaceVector2 = [16] * int(length2)
                    parameters1 = self.parse_whole(elementShellThickKeywords[i][j], spaceVector1)
                    parameters2 = self.parse_whole(elementShellThickKeywords[i][j+1], spaceVector2)
                    parameterList.append(parameters1)
                    parameterList.append(parameters2)
            else:
                for j in range(0,len(elementShellThickKeywords[i]),3):
                    if j == 0:
                        curStrVector = str(elementShellThickKeywords[i][j])
                        length = len(curStrVector)/8
                        spaceVector1 = [8] * int(length)
                        spaceVector2 = [16,16,16,16,16]
                        spaceVector3 = [16,16,16,16]
                    parameters1 = self.parse_whole(elementShellThickKeywords[i][j], spaceVector1)
                    parameters2 = self.parse_whole(elementShellThickKeywords[i][j+1], spaceVector2)
                    parameters3 = self.parse_whole(elementShellThickKeywords[i][j+2], spaceVector3)
                    parameterList.append(parameters1)
                    parameterList.append(parameters2)
                    parameterList.append(parameters3)                    

            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            mode = 1 
            if len(parameter[0]) > 6 and int(parameter[0][6])>0:
                mode = 2
            if mode == 1:
                stream.write("*ELEMENT_SHELL_THICKNESS\n")
                stream.write("$$   EID     PID      N1      N2      N3      N4      N5      N6      N7      N8\n")
                stream.write("$$         THIC1           THIC2           THIC3           THIC4      BETAorMCID\n")
                for j in range(len(parameter)):
                    for k in range(len(parameter[j])):
                        if j%2 == 0:
                            formatted_elements = f"{str(parameter[j][k]):>8}"
                        else:
                            formatted_elements = f"{str(parameter[j][k]):>16}"
                        stream.write(formatted_elements)
                    stream.write("\n")
            else:
                stream.write("*ELEMENT_SHELL_THICKNESS\n")
                stream.write("$$   EID     PID      N1      N2      N3      N4      N5      N6      N7      N8\n")
                stream.write("$$         THIC1           THIC2           THIC3           THIC4      BETAorMCID\n")
                stream.write("$$         THIC5           THIC6           THIC7           THIC8\n")
                for j in range(len(parameter)):
                    for k in range(len(parameter[j])):
                        if j%3 == 0:
                            formatted_elements = f"{str(parameter[j][k]):>8}"
                        else:
                            formatted_elements = f"{str(parameter[j][k]):>16}"
                        stream.write(formatted_elements)
                    stream.write("\n")
                
class ElementSolid(DynaKeyword):
    def __init__(self):
        super(ElementSolid,self).__init__("ELEMENT_SOLID")
    
    
    def parse(self, elementSolidKeywords):
        for i in range(len(elementSolidKeywords)):
            spaceVector = []
            parameterList = [] 
            mode = 1
            for j in range(len(elementSolidKeywords[i])):
                if j == 0:
                    curStrVector = str(elementSolidKeywords[i][j])
                    length = int(len(curStrVector)/8)
                    spaceVector = [8] * length
                    mode = 1
                    parameters = self.parse_whole(elementSolidKeywords[i][j], spaceVector)
                if j == 1:
                    curStrVector = str(elementSolidKeywords[i][j])
                    length2 = int(len(curStrVector)/8)
                    spaceVector2 = [8] * length2
                    if length2 != length:
                        mode = 2
                    parameters = self.parse_whole(elementSolidKeywords[i][j], spaceVector2)
                elif j%2 == 0:
                    parameters = self.parse_whole(elementSolidKeywords[i][j], spaceVector)
                else:
                    parameters = self.parse_whole(elementSolidKeywords[i][j], spaceVector2)
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*ELEMENT_SOLID\n")
            stream.write("$$   EID     PID      N1      N2      N3      N4      N5      N6      N7      N8\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>8}"
                    stream.write(formatted_elements)
                stream.write("\n")

class EOSTabulated(DynaKeyword):
    def __init__(self):
        super(EOSTabulated,self).__init__("EOS_TABULATED")

    def parse(self, eosTabulatedKeywords):
        for i in range(len(eosTabulatedKeywords)):
            parameterList = [] 
            
            parameters = self.parse_whole(eosTabulatedKeywords[i][0], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(parameters[4]) == 0 or len(parameters[5]) == 0:
                for j in range(1, len(eosTabulatedKeywords[i])):
                    parameters = self.parse_whole(eosTabulatedKeywords[i][j], [16,16,16,16,16])
                    parameterList.append(parameters)
            self.parameters.append(parameterList)    
    
    def AddEosTabulated(self, EID, GAMA, E0, V0, LCC, LCT, EV, C, T):
        parameterList = []
        parameterList.append([EID, GAMA, E0, V0, LCC, LCT])
        for i in range(5):
            parameterList.append(EV[i])
        for i in range(5,10):
            parameterList.append(EV[i])
        for i in range(0,5):
            parameterList.append(C[i])
        for i in range(5,10):
            parameterList.append(C[i])
        for i in range(0,5):
            parameterList.append(T[i])
        for i in range(5,10):
            parameterList.append(T[i])
        self.parameters.append(parameterList)                   

    def getEOSList(self):
        eosList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curEosList = []
            curEosList.append("*EOS_TABULATED")
            for j in range(len(parameter)):
                curEosList.append(parameter[j])
            eosList.append(curEosList)
        return eosList
    
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*EOS_TABULATED\n")
            stream.write("$$   EOSID      GAMA        E0        V0       LCC        LCT\n")
            for k in range(len(parameter[0])):
                formatted_elements = f"{str(parameter[0][k]):>10}"                    
                stream.write(formatted_elements)
            stream.write("\n")
            for j in range(1,len(parameter)):                
                if j == 1:                        
                    stream.write("$$           EV1             EV2             EV3             EV4             EV5\n")
                if j == 2:
                    stream.write("$$           EV6             EV7             EV8             EV9            EV10\n")
                if j == 3:
                    stream.write("$$            C1              C2              C3              C4              C5\n")
                if j == 4:
                    stream.write("$$            C6              C7              C8              C9             C10\n")
                if j == 5:
                    stream.write("$$            T1              T2              T3              T4              T5\n")
                if j == 6:
                    stream.write("$$            T6              T7              T8              T9             T10\n")
                for k in range(len(parameter[j])):                    
                    formatted_elements = f"{str(parameter[j][k]):>16}"
                    stream.write(formatted_elements)
                stream.write("\n")

class FrequencyDomainSSD(DynaKeyword):
    def __init__(self):
        super(FrequencyDomainSSD,self).__init__("FREQUENCY_DOMAIN_SSD")

    def parse(self, frequencyDomainSSDKeywords):        
        parameterList = [] 
        parameters = self.parse_whole(frequencyDomainSSDKeywords[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        parameterList.append(parameters)
        parameters = self.parse_whole(frequencyDomainSSDKeywords[0][1], [10, 10, 10, 10, 10, 10])
        parameterList.append(parameters)
        parameters = self.parse_whole(frequencyDomainSSDKeywords[0][2], [10, 10, 10, 10, 10, 10, 10, 10])
        parameterList.append(parameters)
        for i in range(3, len(frequencyDomainSSDKeywords[0])):
            parameters = self.parse_whole(frequencyDomainSSDKeywords[0][i], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)            
        self.parameters.append(parameterList)

    def write(self, stream):
        parameters = self.parameters[0]
        stream.write("*FREQUENCY_DOMAIN_SSD\n") 
        stream.write("$$   MDMIN     MDMAX     FNMIN     FNMAX    RESTMD    RESTDP    LCFLAG    RELATV\n")   
        formatted_elements = f"{str(parameters[0][0]):>10}{str(parameters[0][1]):>10}{str(parameters[0][2]):>10}{str(parameters[0][3]):>10}{str(parameters[0][4]):>10}{str(parameters[0][5]):>10}{str(parameters[0][6]):>10}{str(parameters[0][7]):>10}\n"
        stream.write(formatted_elements)
        stream.write("$$   DAMPF     LCDAM     LCTYP    DMPMAS    DMPSTF    DMPFLG\n")
        formatted_elements = f"{str(parameters[1][0]):>10}{str(parameters[1][1]):>10}{str(parameters[1][2]):>10}{str(parameters[1][3]):>10}{str(parameters[1][4]):>10}{str(parameters[1][5]):>10}\n"
        stream.write(formatted_elements)
        stream.write("$$   EMPTY   ISTRESS    MEMORY      NERP    STRTYP      NOUT     NOTYP      NOVA\n")                
        formatted_elements = f"{str(parameters[2][0]):>10}{str(parameters[2][1]):>10}{str(parameters[2][2]):>10}{str(parameters[2][3]):>10}{str(parameters[2][4]):>10}{str(parameters[2][5]):>10}{str(parameters[2][6]):>10}{str(parameters[2][7]):>10}\n"
        stream.write(formatted_elements)        
        stream.write("$$     NID      NTYP       DOF       VAD       LC1       LC2        SF       VID\n") 
        for i in range(3, len(parameters)):        
            formatted_elements = f"{str(parameters[i][0]):>10}{str(parameters[i][1]):>10}{str(parameters[i][2]):>10}{str(parameters[i][3]):>10}{str(parameters[i][4]):>10}{str(parameters[i][5]):>10}{str(parameters[i][6]):>10}{str(parameters[i][7]):>10}\n"
            stream.write(formatted_elements)

class Hourglass(DynaKeyword):
    def __init__(self):
        super(Hourglass,self).__init__("HOURGLASS")
    
    def parse(self, hourglassKeywords):
        parameters = self.parse_whole(hourglassKeywords[0][0], [10, 10, 10, 10, 10, 10, 10, 10])
        self.parameters.append(parameters)
    
    def getHourglass(self):
        parameterList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curHourglass = []
            curHourglass.append("*HOURGLASS")
            curHourglass.append(parameter)
            parameterList.append(curHourglass)
        return parameterList    
    
    def write(self, stream):
        stream.write("*HOURGLASS\n")        
        stream.write("$$    HGID       IHQ        QM       IBQ        Q1        Q2     QBVDC        QW\n")
        for j in range(len(self.parameters[0])):
            formatted_elements = f"{str(self.parameters[0][j]):>10}"
            stream.write(formatted_elements)
        stream.write("\n")
        
class InitialStressSolid(DynaKeyword):
    def __init__(self):
        super(InitialStressSolid,self).__init__("INITIAL_STRESS_SOLID")

    def parse(self, initialStressSolidKeywords):
        for i in range(len(initialStressSolidKeywords)):
            parameterList = []
            j = 0
            parameterList = []

            while j < len(initialStressSolidKeywords[i]):
                parameters1 = self.parse_whole(initialStressSolidKeywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters1)

                if len(parameters1[1]) > 0:
                    nint = int(parameters1[1])
                    nhisv = int(parameters1[2])
                    large = int(parameters1[3])                    
                else:
                    nint = 1
                    nhisv = 0
                    large = 0 
                
                if large == 0:
                    for k in range(j+1, j+1+nint):
                        if k < len(initialStressSolidKeywords[i]):
                            parameter = self.parse_whole(initialStressSolidKeywords[i][k], [10, 10, 10, 10, 10, 10, 10, 10])
                            parameterList.append(parameter)
                    j += nint + 1  # j 수동 증가
                elif large == 1:
                    numLine = 2 
                    if nhisv >3:
                        numLine = 3                         
                    for k in range(j+1, j+1+numLine*nint, numLine):
                        parameterA = self.parse_whole(initialStressSolidKeywords[i][k], [16, 16, 16, 16, 16])                        
                        parameterList.append(parameterA)
                        parameterB = self.parse_whole(initialStressSolidKeywords[i][k+1], [16, 16, 16, 16, 16])
                        parameterList.append(parameterB)
                        if nhisv >3: 
                            parameterC = self.parse_whole(initialStressSolidKeywords[i][k+2], [16, 16, 16, 16, 16])
                            parameterList.append(parameterC)

                    j += numLine*nint + 1  # j 수동 증가

            self.parameters.append(parameterList)

            
    def getInitialStressSolid(self):
        initStressSolidList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curInitStressSolid = []
            curInitStressSolid.append("*INITIAL_STRESS_SOLID")
            for j in range(len(parameter)):
                curInitStressSolid.append(parameter[j])
            initStressSolidList.append(curInitStressSolid)
        return initStressSolidList

    def AddInitialStressSolid(self, EID, NINT, NHISV, LARGE, IVEFLG, IALEG, NTHINT, NTHHSV, SIGXX, SIGYY, SIGZZ, SIGXY, SIGYZ, SIGZX, EPS, HISV1 = [], HISV2 = [], HISV3 = [], HISV4 = [] ,HISV5 = [], HISV6 = [], HISV7 = [], HISV8 = []):
        parameterList = []
        parameters1 = [EID, NINT, NHISV, LARGE, IVEFLG, IALEG, NTHINT, NTHHSV]
        parameterList.append(parameters1)
        if LARGE == 0:
            if type(SIGXX) == list:
                for i in range(len(SIGXX)):
                    parameters2 = [SIGXX[i], SIGYY[i], SIGZZ[i], SIGXY[i], SIGYZ[i], SIGZX[i], EPS[i]]
                    parameterList.append(parameters2)
            else:
                parameters2 = [SIGXX, SIGYY, SIGZZ, SIGXY, SIGYZ, SIGZX, EPS]
                parameterList.append(parameters2)
        elif LARGE == 1 and NHISV == 0:
            if type(SIGXX) == list:
                realSize = int(len(SIGXX)/2)                
                for i in range(realSize):
                    parameterA = [SIGXX[i], SIGYY[i], SIGZZ[i], SIGXY[i], SIGYZ[i]]                    
                    parameterList.append(parameterA)
                    parameterB = [SIGZX[i], EPS[i]]
                    parameterList.append(parameterB)

            else:
                parameterA = [SIGXX, SIGYY, SIGZZ, SIGXY, SIGYZ]
                parameterList.append(parameterA)
                parameterB = [SIGZX, EPS]
                parameterList.append(parameterB)
        elif LARGE == 1 and NHISV == 1:
            if type(SIGXX) == list:
                realSize = int(len(SIGXX)/2)
                for i in range(realSize):
                    parameterA = [SIGXX[i], SIGYY[i], SIGZZ[i], SIGXY[i], SIGYZ[i]]
                    parameterList.append(parameterA)
                    parameterB = [SIGZX[i], EPS[i], HISV1[i]]
                    parameterList.append(parameterB)
            else:
                parameterA = [SIGXX, SIGYY, SIGZZ, SIGXY, SIGYZ]
                parameterList.append(parameterA)
                parameterB = [SIGZX, EPS, HISV1]
                parameterList.append(parameterB)
        elif LARGE == 1 and NHISV == 2:
            if type(SIGXX) == list:
                realSize = int(len(SIGXX)/2)
                for i in range(realSize):
                    parameterA = [SIGXX[i], SIGYY[i], SIGZZ[i], SIGXY[i], SIGYZ[i]]
                    parameterList.append(parameterA)
                    parameterB = [SIGZX[i], EPS[i], HISV1[i], HISV2[i]]
                    parameterList.append(parameterB)
            else:
                parameterA = [SIGXX, SIGYY, SIGZZ, SIGXY, SIGYZ]
                parameterList.append(parameterA)
                parameterB = [SIGZX, EPS, HISV1, HISV2]
                parameterList.append(parameterB)
        elif LARGE == 1 and NHISV == 3:
            if type(SIGXX) == list:
                realSize = int(len(SIGXX)/2)
                for i in range(realSize):
                    parameterA = [SIGXX[i], SIGYY[i], SIGZZ[i], SIGXY[i], SIGYZ[i]]
                    parameterList.append(parameterA)
                    parameterB = [SIGZX[i], EPS[i], HISV1[i], HISV2[i], HISV3[i]]
                    parameterList.append(parameterB)
            else:
                parameterA = [SIGXX, SIGYY, SIGZZ, SIGXY, SIGYZ]
                parameterList.append(parameterA)
                parameterB = [SIGZX, EPS, HISV1, HISV2, HISV3]
                parameterList.append(parameterB)
        elif LARGE == 1 and NHISV > 3:
            if type(SIGXX) == list:
                realSize = int(len(SIGXX)/3)
                for i in range(realSize):
                    parameterA = [SIGXX[i], SIGYY[i], SIGZZ[i], SIGXY[i], SIGYZ[i]]
                    parameterList.append(parameterA)
                    parameterB = [SIGZX[i], EPS[i], HISV1[i], HISV2[i], HISV3[i]]
                    parameterList.append(parameterB)
                    for j in range(4, NHISV + 1):
                        parameterB.append(eval(f'HISV{j}[i]'))
                    parameterList.append(parameterB)
            else:
                parameterA = [SIGXX, SIGYY, SIGZZ, SIGXY, SIGYZ]
                parameterList.append(parameterA)
                parameterB = [SIGZX, EPS, HISV1, HISV2, HISV3]
                parameterList.append(parameterB)
                for j in range(4, NHISV + 1):
                    parameterB.append(eval(f'HISV{j}'))
                parameterList.append(parameterB)

        self.parameters.append(parameterList)
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*INITIAL_STRESS_SOLID\n")
            
            
            j = 0
            large = 0
            nhisv = 0
            numline = 1
            
            while j < len(parameter):
                if j == 0:
                    stream.write("$$     EID      NINT     NHISV    LARGE    IVEFLG     IALEG    NTHINT    NTHHSV\n")                
                    nint = int(parameter[j][1])
                    nhisv = int(parameter[j][2])
                    large = int(parameter[j][3])
                    if large == 1:
                        if nhisv <= 3:
                            numline = 2
                        else:
                            numline = 3
                    else:
                        numline = 1
                formatted_elements = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):>10}{str(parameter[j][6]):>10}{str(parameter[j][7]):>10}\n"
                stream.write(formatted_elements)
                
                formatted_elements = ""
                for k in range(j+1, j+1+numline*nint):
                    for m in range(len(parameter[k])):
                        formatted_elements += f"{str(parameter[k][m]):>10}"
                    formatted_elements += "\n"  
                    stream.write(formatted_elements)
                j += nint * numline + 1  # 여기서 건너뜀


class InitialStressSolidSet(DynaKeyword):
    def __init__(self):
        super(InitialStressSolidSet,self).__init__("INITIAL_STRESS_SOLID_SET")
    
    def parse(self, initialStressSolidSetKeywords):
        for i in range(len(initialStressSolidSetKeywords)):
            parameterList = []
            j = 0
            while j < len(initialStressSolidSetKeywords[i]):
                parameters1 = self.parse_whole(initialStressSolidSetKeywords[i][j], [10]*8)
                parameterList.append(parameters1)

                if len(parameters1[1]) > 0:
                    nint = int(parameters1[1])
                else:
                    nint = 1

                for k in range(j+1, j+1+nint):
                    parameter = self.parse_whole(initialStressSolidSetKeywords[i][k], [10]*8)
                    parameterList.append(parameter)

                j += nint + 1  # 수동으로 j 증가
            self.parameters.append(parameterList)
            
    def getInitialStressSolidSet(self):
        initStressSolidSetList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curInitStressSolidSet = []
            curInitStressSolidSet.append("*INITIAL_STRESS_SOLID_SET")
            for j in range(len(parameter)):
                curInitStressSolidSet.append(parameter[j])
            initStressSolidSetList.append(curInitStressSolidSet)
        return initStressSolidSetList
    
    def AddInitialStressSolidSet(self, ESID, NINT, NHISV, LARGE, IVEFLG, IALEG, NTHINT, NTHHSV, SIGXX, SIGYY, SIGZZ, SIGXY, SIGYZ, SIGZX, EPS):
        parameterList = []
        parameters1 = [ESID, NINT, NHISV, LARGE, IVEFLG, IALEG, NTHINT, NTHHSV]
        parameterList.append(parameters1)
        if type(SIGXX) == list:
            for i in range(len(SIGXX)):
                parameters2 = [SIGXX[i], SIGYY[i], SIGZZ[i], SIGXY[i], SIGYZ[i], SIGZX[i], EPS[i]]
                parameterList.append(parameters2)
        else:
            parameters2 = [SIGXX, SIGYY, SIGZZ, SIGXY, SIGYZ, SIGZX, EPS]
            parameterList.append(parameters2)
        self.parameters.append(parameterList)
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*INITIAL_STRESS_SOLID_SET\n")
            j = 0
            while j < len(parameter):
                if j == 0:
                    stream.write("$$     ESID      NINT     NHISV    LARGE    IVEFLG     IALEG    NTHINT    NTHHSV\n")
                elif j == 1:
                    stream.write("$$   SIGXX     SIGYY     SIGZZ     SIGXY     SIGYZ     SIGZX       EPS\n")

                formatted_elements = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):>10}{str(parameter[j][6]):>10}{str(parameter[j][7]):>10}\n"
                stream.write(formatted_elements)

                nint = int(parameter[j][1])
                for k in range(j+1, j+1+nint):
                    formatted_elements = f"{str(parameter[k][0]):>10}{str(parameter[k][1]):>10}{str(parameter[k][2]):>10}{str(parameter[k][3]):>10}{str(parameter[k][4]):>10}{str(parameter[k][5]):>10}{str(parameter[k][6]):>10}\n"
                    stream.write(formatted_elements)

                j += nint + 1

class InitialVelocity(DynaKeyword):
    def __init__(self):
        super(InitialVelocity,self).__init__("INITIAL_VELOCITY")
    
    def parse(self, initialVelocityKeywords):
        for i in range(len(initialVelocityKeywords)):
            parameterList = []
            parameters1 = self.parse_whole(initialVelocityKeywords[i][0], [10, 10, 10, 10, 10])
            parameterList.append(parameters1)
            parameters2 = self.parse_whole(initialVelocityKeywords[i][1], [10, 10, 10, 10, 10, 10])            
            parameterList.append(parameters2)
            if len(parameters1[1]) > 0 and int(parameters1[1]) >0:
                parameters3 = self.parse_whole(initialVelocityKeywords[i][2], [10, 10, 10, 10, 10, 10])
                parameterList.append(parameters3)
            self.parameters.append(parameterList)
        
    def getInitialVelocity(self):
        initVelList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curInitVel = []
            curInitVel.append("*INITIAL_VELOCITY")
            for j in range(len(parameter)):
                curInitVel.append(parameter[j])
            initVelList.append(curInitVel)
        return initVelList
        
    def AddInitialVelocity(self, NSIDID, NSIDEX, BOXID, IRIGID, ICID, VX, VY, VZ, VXR, VYR, VZR, VXE=None, VYE=None, VZE=None, VXRE=None, VYRE=None, VZRE=None):
        parameterList = []
        parameters1 = [NSIDID, NSIDEX, BOXID, IRIGID, ICID]
        parameterList.append(parameters1)
        parameters2 = [VX, VY, VZ, VXR, VYR, VZR]
        parameterList.append(parameters2)
        if VXE != None:
            parameters3 = [VXE, VYE, VZE, VXRE, VYRE, VZRE]
            parameterList.append(parameters3)
        self.parameters.append(parameterList)

    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*INITIAL_VELOCITY\n")
            stream.write("$$  NSIDID    NSIDEX     BOXID    IRIGID      ICID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      VX        VY        VZ       VXR       VYR       VZR\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}\n"
            stream.write(formatted_elements)
            if len(parameter) > 2:
                stream.write("$$     VXE       VYE       VZE      VXRE      VYRE      VZRE\n")
                formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}\n"
                stream.write(formatted_elements)    

class InitialVelocityNode(DynaKeyword):
    def __init__(self):
        super(InitialVelocityNode,self).__init__("INITIAL_VELOCITY_NODE")
    
    def parse(self, initialVelocityNodeKeywords):
        for i in range(len(initialVelocityNodeKeywords)):
            parameterList = []
            for j in range(len(initialVelocityNodeKeywords[i])):
                parameters = self.parse_whole(initialVelocityNodeKeywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getInitialVelocityNode(self):
        initVelNodeList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curInitVelNode = []
            curInitVelNode.append("*INITIAL_VELOCITY_NODE")
            for j in range(len(parameter)):
                curInitVelNode.append(parameter[j])
            initVelNodeList.append(curInitVelNode)
        return initVelNodeList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*INITIAL_VELOCITY_NODE\n")
            stream.write("$$     NID        VX        VY        VZ       VXR       VYR       VZR      ICID\n")
            for j in range(len(parameter)):
                formatted_elements = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):>10}{str(parameter[j][6]):>10}{str(parameter[j][7]):>10}\n"
                stream.write(formatted_elements)

class InitialVelocityGeneration(DynaKeyword):
    def __init__(self):
        super(InitialVelocityGeneration,self).__init__("INITIAL_VELOCITY_GENERATION")

    def parse(self, initialVelocityGenerationKeyword):
        for i in range(len(initialVelocityGenerationKeyword)):
            parameterList = []
            parameters = self.parse_whole(initialVelocityGenerationKeyword[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(initialVelocityGenerationKeyword[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getInitialVelocityGeneration(self):
        initVelGenList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curInitVelGen = []
            curInitVelGen.append("*INITIAL_VELOCITY_GENERATION")
            for j in range(len(parameter)):
                curInitVelGen.append(parameter[j])
            initVelGenList.append(curInitVelGen)
        return initVelGenList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*INITIAL_VELOCITY_GENERATION\n")
            stream.write("$$  NSIDID      STYP     OMEGA        VX        VY        VZ     IVATN      ICID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)            
            stream.write("$$      XC        YC        ZC        NX        NY        NZ     PHASE    IRIGID\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            self.writeParameter(stream,1)

class InterfaceSpringbackDYNA3D(DynaKeyword):
    def __init__(self):
        super(InterfaceSpringbackDYNA3D,self).__init__("INTERFACE_SPRINGBACK_DYNA3D")
    
    def parse(self, interfaceSpringbackDyna3DKeywords):
        for i in range(len(interfaceSpringbackDyna3DKeywords)):
            parameterList = []
            parameters = self.parse_whole(interfaceSpringbackDyna3DKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(interfaceSpringbackDyna3DKeywords[i])):
                parameters = self.parse_whole(interfaceSpringbackDyna3DKeywords[i][j], [10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*INTERFACE_SPRINGBACK_DYNA3D\n")
            stream.write("$$    PSID      NSHV    FTYPE    FTENSR    NTHHSV     RFLAG   INTSTRN\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"            
            stream.write(formatted_elements)            
            for j in range(1,len(parameter)):
                if j == 1:
                    stream.write("$$     NID        TC       RC\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class InterfaceSpringbackLSDYNA(DynaKeyword):
    def __init__(self):
        super(InterfaceSpringbackLSDYNA,self).__init__("INTERFACE_SPRINGBACK_LSDYNA")
    
    def parse(self, interfaceSpringbackLSDYNAKeywords):
        for i in range(len(interfaceSpringbackLSDYNAKeywords)):
            parameterList = []
            parameters = self.parse_whole(interfaceSpringbackLSDYNAKeywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)            
            if len(interfaceSpringbackLSDYNAKeywords[i]) > 1:
                parameters = self.parse_whole(interfaceSpringbackLSDYNAKeywords[i][1], [10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            if len(interfaceSpringbackLSDYNAKeywords[i]) > 2:
                parameters = self.parse_whole(interfaceSpringbackLSDYNAKeywords[i][2], [10, 10])
                parameterList.append(parameters)
            if len(interfaceSpringbackLSDYNAKeywords[i]) > 3:
                parameters = self.parse_whole(interfaceSpringbackLSDYNAKeywords[i][3], [10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getInterfaceSpringbackLSDYNA(self):
        interfaceSpringbackLSDyna = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curInterfaceSpringbackLSDyna = [] 
            curInterfaceSpringbackLSDyna.append("*INTERFACE_SPRINGBACK_LSDYNA")
            for j in range(len(parameter)):
                curInterfaceSpringbackLSDyna.append(parameter[j])
            interfaceSpringbackLSDyna.append(curInterfaceSpringbackLSDyna)
        return interfaceSpringbackLSDyna

    def AddInterfaceSpringbackLSDyna(self, PSID,NSHV=0,FTYPE=0,FTENSR=0,NTHHSV=0,RFLAG=0,INTSTRN=0, OPTC1="0", SLDO=0, NCYC="",FSPLIT=0,NGFLAG=0,CFLAG=0,HFLAG="",OPTC2="",DTWRT="",OPTC3="",NMWRT="",IVFLG=0,NID="",TC=0,RC=0):
        self.parameters.append([PSID, NSHV, FTYPE,"", FTENSR, NTHHSV, RFLAG, INTSTRN])
        if OPTC1 == "OPTCARD":
            self.parameters.append([OPTC1, SLDO, NCYC, FSPLIT, NGFLAG, CFLAG, HFLAG])
        if OPTC2 == "OPTCARD":
            self.parameters.append([OPTC2, DTWRT])
        if OPTC3 == "OPTCARD":
            self.parameters.append([OPTC3, NMWRT, IVFLG])
        self.parameters.append([NID, TC, RC])

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*INTERFACE_SPRINGBACK_LSDYNA\n")
            stream.write("$$    PSID      NSHV    FTYPE      NONE    FTENSR    NTHHSV     RFLAG   INTSTRN\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"            
            stream.write(formatted_elements)            
            numOption = len(parameter)
            if numOption == 2:
                stream.write("$$     NID        TC       RC\n")
                for k in range(len(parameter[1])):
                    formatted_elements = f"{str(parameter[1][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")
            if numOption == 3:
                for j in range(1,len(parameter)):                
                    if j == 1:                        
                        stream.write("$$    OPTC      SLDO      NCYC    FSPLIT    NDFLAG     CFLAG     HFLAG\n")
                    elif j == 2:
                        stream.write("$$     NID        TC       RC\n")            
                    for k in range(len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)
                    stream.write("\n")
            if numOption == 4:
                for j in range(1,len(parameter)):
                    if j == 1:
                        stream.write("$$    OPTC      SLDO      NCYC    FSPLIT    NDFLAG     CFLAG     HFLAG\n")
                    if j == 2:
                        stream.write("$$    OPTC     DTWRT\n")                        
                    elif j == 3:
                        stream.write("$$     NID        TC       RC\n")
                    for k in range(len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)
                stream.write("\n")
            if numOption == 5:
                for j in range(1,len(parameter)):
                    if j == 1:
                        stream.write("$$    OPTC      SLDO      NCYC    FSPLIT    NDFLAG     CFLAG     HFLAG\n")
                    elif j == 2:
                        stream.write("$$    OPTC     DTWRT\n")
                    elif j == 3:
                        stream.write("$$    OPTC     NMWRT     IVFLG\n")
                    elif j == 4:
                        stream.write("$$     NID        TC       RC\n")
                    for k in range(len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)
                stream.write("\n")

class InterfaceSpringbackNASTRAN(DynaKeyword):
    def __init__(self):
        super(InterfaceSpringbackNASTRAN,self).__init__("INTERFACE_SPRINGBACK_NASTRAN")
    
    def parse(self, interfaceSpringbackNASTRANKeywords):
        for i in range(len(interfaceSpringbackNASTRANKeywords)):
            parameterList = []
            parameters = self.parse_whole(interfaceSpringbackNASTRANKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(interfaceSpringbackNASTRANKeywords[i])):
                parameters = self.parse_whole(interfaceSpringbackNASTRANKeywords[i][j], [10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*INTERFACE_SPRINGBACK_NASTRAN\n")
            stream.write("$$    PSID      NSHV    FTYPE    FTENSR    NTHHSV     RFLAG   INTSTRN\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"            
            stream.write(formatted_elements)            
            for j in range(1,len(parameter)):                
                if j == 1:
                    stream.write("$$     NID        TC       RC\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")
            
class InterfaceSpringbackSeamless(DynaKeyword):
    def __init__(self):
        super(InterfaceSpringbackSeamless,self).__init__("INTERFACE_SPRINGBACK_SEAMLESS")

    def parse(self, interfaceSpringbackSeamlessKeywords):
        for i in range(len(interfaceSpringbackSeamlessKeywords)):
            parameterList = []
            parameters = self.parse_whole(interfaceSpringbackSeamlessKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(interfaceSpringbackSeamlessKeywords[i])):
                parameters = self.parse_whole(interfaceSpringbackSeamlessKeywords[i][j], [10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]            
            stream.write("*INTERFACE_SPRINGBACK_SEAMLESS\n")
            stream.write("$$    PSID      NSHV    FTYPE    FTENSR    NTHHSV     RFLAG   INTSTRN\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"            
            stream.write(formatted_elements)            
            for j in range(1,len(parameter)):                
                if j == 1:
                    stream.write("$$     NID        TC       RC\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class KeywordID(DynaKeyword):
    def __init__(self):
        super(KeywordID,self).__init__("KEYWORD_ID")
    
    def parse(self, keywordIDKeywords):
        parameterList = []
        parameters = self.parse_whole(keywordIDKeywords[0][0], [80])
        parameterList.append(parameters)
        self.parameters.append(parameterList)
    
    def write(self, stream):
        stream.write("*KEYWORD_ID\n")
        stream.write("$$                                                                          NAME\n")
        formatted_elements = f"{str(self.parameters[0][0][0]):<80}\n"
        stream.write(formatted_elements)

class LoadBodyX(DynaKeyword):
    def __init__(self):
        super(LoadBodyX,self).__init__("LOAD_BODY_X")
    
    def parse(self, loadBodyXKeywords):
        for i in range(len(loadBodyXKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadBodyXKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getLoadBodyXList(self):
        loadBodyXList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curLoadBodyX = []
            curLoadBodyX.append("*LOAD_BODY_X")
            for j in range(len(parameter)):
                curLoadBodyX.append(parameter[j])
            loadBodyXList.append(curLoadBodyX)
        return loadBodyXList

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_BODY_X\n")
            stream.write("$$    LCID        SF    LCIDDR        XC        YC        ZC       CID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
            stream.write(formatted_elements)

class LoadBodyY(DynaKeyword):
    def __init__(self):
        super(LoadBodyY,self).__init__("LOAD_BODY_Y")
    
    def parse(self, loadBodyYKeywords):
        for i in range(len(loadBodyYKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadBodyYKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def getLoadBodyYList(self):
        loadBodyYList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curLoadBodyY = []
            curLoadBodyY.append("*LOAD_BODY_Y")
            for j in range(len(parameter)):
                curLoadBodyY.append(parameter[j])
            loadBodyYList.append(curLoadBodyY)  
        return loadBodyYList

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_BODY_Y\n")
            stream.write("$$    LCID        SF    LCIDDR        XC        YC        ZC       CID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
            stream.write(formatted_elements)

class LoadBodyZ(DynaKeyword):
    def __init__(self):
        super(LoadBodyZ,self).__init__("LOAD_BODY_Z")
    
    def parse(self, loadBodyZKeywords):
        for i in range(len(loadBodyZKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadBodyZKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def getLoadBodyZList(self):
        loadBodyZList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curLoadBodyZ = []
            curLoadBodyZ.append("*LOAD_BODY_Z")
            for j in range(len(parameter)):
                curLoadBodyZ.append(parameter[j])
            loadBodyZList.append(curLoadBodyZ)
        return loadBodyZList
    

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_BODY_Z\n")
            stream.write("$$    LCID        SF    LCIDDR        XC        YC        ZC       CID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
            stream.write(formatted_elements)
            
            
class LoadBodyRX(DynaKeyword):
    def __init__(self):
        super(LoadBodyRX,self).__init__("LOAD_BODY_RX")
        
    def parse(self, loadBodyRXKeywords):
        for i in range(len(loadBodyRXKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadBodyRXKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def getLoadBodyRXList(self):
        loadBodyRXList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curLoadBodyRX = []
            curLoadBodyRX.append("*LOAD_BODY_RX")
            for j in range(len(parameter)):
                curLoadBodyRX.append(parameter[j])
            loadBodyRXList.append(curLoadBodyRX)
        return loadBodyRXList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_BODY_RX\n")
            stream.write("$$    LCID        SF    LCIDDR        XC        YC        ZC       CID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
            stream.write(formatted_elements)

class LoadBodyRY(DynaKeyword):
    def __init__(self):
        super(LoadBodyRY,self).__init__("LOAD_BODY_RY")
        
    def parse(self, loadBodyRYKeywords):
        for i in range(len(loadBodyRYKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadBodyRYKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getLoadBodyRYList(self):
        loadBodyRYList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curLoadBodyRY = []
            curLoadBodyRY.append("*LOAD_BODY_RY")
            for j in range(len(parameter)):
                curLoadBodyRY.append(parameter[j])
            loadBodyRYList.append(curLoadBodyRY)
        return loadBodyRYList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_BODY_RY\n")
            stream.write("$$    LCID        SF    LCIDDR        XC        YC        ZC       CID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
            stream.write(formatted_elements)
            
class LoadBodyRZ(DynaKeyword):
    def __init__(self):
        super(LoadBodyRZ,self).__init__("LOAD_BODY_RZ")

    def parse(self, loadBodyRZKeywords):
        for i in range(len(loadBodyRZKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadBodyRZKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getLoadBodyRZList(self):
        loadBodyRZList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curLoadBodyRZ = []
            curLoadBodyRZ.append("*LOAD_BODY_RZ")
            for j in range(len(parameter)):
                curLoadBodyRZ.append(parameter[j])
            loadBodyRZList.append(curLoadBodyRZ)
        return loadBodyRZList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_BODY_RZ\n")
            stream.write("$$    LCID        SF    LCIDDR        XC        YC        ZC       CID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
            stream.write(formatted_elements)
            
class LoadBodyVector(DynaKeyword):
    def __init__(self):
        super(LoadBodyVector,self).__init__("LOAD_BODY_VECTOR")
        
    def parse(self, loadBodyVectorKeywords):
        for i in range(len(loadBodyVectorKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadBodyVectorKeywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(loadBodyVectorKeywords[i][1], [10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getLoadBodyVectorList(self):
        loadBodyVectorList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curLoadBodyVector = []
            curLoadBodyVector.append("*LOAD_BODY_VECTOR")
            for j in range(len(parameter)):
                curLoadBodyVector.append(parameter[j])
            loadBodyVectorList.append(curLoadBodyVector)
        return loadBodyVectorList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_BODY_VECTOR\n")
            stream.write("$$    LCID        SF    LCIDDR        XC        YC        ZC       CID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$       VX        VY        VZ\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}\n"
            stream.write(formatted_elements)                      
        
class LoadRigidBody(DynaKeyword):
    def __init__(self):
        super(LoadRigidBody,self).__init__("LOAD_RIGID_BODY")
    
    def parse(self, loadRigidBodyKeywords):
        for i in range(len(loadRigidBodyKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadRigidBodyKeywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_RIGID_BODY\n")
            stream.write("$$     PID       DOF      LCID        SF       CID        M1        M2        M3\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)

class LoadNodePoint(DynaKeyword):
    def __init__(self):
        super(LoadNodePoint,self).__init__("LOAD_NODE_POINT")
    
    def parse(self, loadNodePointKeywords):
        for i in range(len(loadNodePointKeywords)):
            parameterList = []
            for j in range(len(loadNodePointKeywords[i])):
                parameters = self.parse_whole(loadNodePointKeywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddLoadNodePoint(self, NID, DOF, LCID, SF, CID="", M1="", M2="", M3=""):
        parameterList = [] 
        parameterList.append([NID, DOF, LCID, SF, CID, M1, M2, M3])
        self.parameters.append(parameterList)
        
    def getLoadNodePointList(self):
        loadNodePointList = [] 
        for i in range(len(self.parameters)):
            curLoadNodePoint = [] 
            curLoadNodePoint.append("*LOAD_NODE_POINT")
            curLoadNodePoint.append(self.parameters[i])
            loadNodePointList.append(curLoadNodePoint)
        return loadNodePointList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_NODE_POINT\n")
            stream.write("$$     NID       DOF      LCID        SF       CID        M1        M2        M3\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class LoadNodeSet(DynaKeyword):
    def __init__(self):
        super(LoadNodeSet,self).__init__("LOAD_NODE_SET")
    
    def parse(self, loadNodeSetKeywords):
        for i in range(len(loadNodeSetKeywords)):
            parameterList = []
            for j in range(len(loadNodeSetKeywords[i])):
                parameters = self.parse_whole(loadNodeSetKeywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddLoadNodeSet(self, NSID, DOF, LCID, SF, CID="", M1="", M2="", M3=""):
        parameterList = []
        parameterList.append([NSID, DOF, LCID, SF, CID, M1, M2, M3])
        self.parameters.append(parameterList)   

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_NODE_SET\n")
            stream.write("$$    NSID       DOF      LCID        SF       CID        M1        M2        M3\n")
            for j in range(len(parameter)):
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class LoadSegment(DynaKeyword):
    def __init__(self):
        super(LoadSegment,self).__init__("LOAD_SEGMENT")
    
    def parse(self, loadSegmentKeywords):
        for i in range(len(loadSegmentKeywords)):
            parameterList = []
            for j in range(len(loadSegmentKeywords[i])):
                parameters = self.parse_whole(loadSegmentKeywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getLoadSegmentList(self):
        loadSegmentList = []
        for i in range(len(self.parameters)):
            curLoadSegment = []
            curLoadSegment.append("*LOAD_SEGMENT")
            curLoadSegment.append(self.parameters[i])
            loadSegmentList.append(curLoadSegment)
        return loadSegmentList         
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_SEGMENT\n")            
            for j in range(len(parameter)):
                if j == 0:
                    stream.write("$$    LCID        SF        AT        N1        N2        N3        N4        N5\n")                
                                        
                    if len(parameter) > 1 and len(parameter[0]) == 8:
                        if parameter[0][7] != "" and int(parameter[0][7]) != 0:
                            stream.write("$$       N6        N7        N8\n")

                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class LoadSegmentID(DynaKeyword):
    def __init__(self):
        super(LoadSegmentID,self).__init__("LOAD_SEGMENT_ID")
    
    def parse(self, loadSegmentIDKeywords):
        for i in range(len(loadSegmentIDKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadSegmentIDKeywords[i][0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(loadSegmentIDKeywords[i])):
                parameters = self.parse_whole(loadSegmentIDKeywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getLoadSegmentIDList(self):
        loadSegmentList = []
        for i in range(len(self.parameters)):
            curLoadSegment = []
            curLoadSegment.append("*LOAD_SEGMENT_ID")
            curLoadSegment.append(self.parameters[i])
            loadSegmentList.append(curLoadSegment)
        return loadSegmentList                             

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_SEGMENT_ID\n")            
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(parameter)):
                if j == 1:
                    stream.write("$$    LCID        SF        AT        N1        N2        N3        N4        N5\n")                                                        
                    if len(parameter) > 1 and len(parameter[1]) == 8:
                        if parameter[1][7] != "" and int(parameter[1][7]) != 0:
                            stream.write("$$       N6        N7        N8\n")

                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class LoadSegmentSet(DynaKeyword):
    def __init__(self):
        super(LoadSegmentSet,self).__init__("LOAD_SEGMENT_SET")
    
    def parse(self, loadSegmentSetKeywords):
        for i in range(len(loadSegmentSetKeywords)):
            parameterList = []
            for j in range(len(loadSegmentSetKeywords[i])):
                parameters = self.parse_whole(loadSegmentSetKeywords[i][j], [10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddLoadSegmentSet(self, SSID, LCID, SF, AT):
        parameterList = []
        parameterList.append([SSID, LCID, SF, AT])
        self.parameters.append(parameterList)       
    
    def getLoadSegmentSetList(self):
        loadSegmentSetList = []
        for i in range(len(self.parameters)):
            curLoadSegmentSet = []
            curLoadSegmentSet.append("*LOAD_SEGMENT_SET")
            curLoadSegmentSet.append(self.parameters[i])
            loadSegmentSetList.append(curLoadSegmentSet)
        return loadSegmentSetList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_SEGMENT_SET\n")
            for j in range(len(parameter)):
                if j == 0:
                    stream.write("$$    SSID      LCID        SF        AT\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")            
            
class LoadSegmentSetID(DynaKeyword):
    def __init__(self):
        super(LoadSegmentSetID,self).__init__("LOAD_SEGMENT_SET_ID")
    
    def parse(self, loadSegmentSetIDKeywords):
        for i in range(len(loadSegmentSetIDKeywords)):
            parameterList = []
            parameters = self.parse_whole(loadSegmentSetIDKeywords[i][0], [10, 70])
            parameterList.append(parameters)
            for j in range(1,len(loadSegmentSetIDKeywords[i])):
                parameters = self.parse_whole(loadSegmentSetIDKeywords[i][j], [10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def AddLoadSegmentSetID(self, id, name, SSID, LCID, SF, AT):
        parameterList = []
        parameterList.append([id, name])
        parameterList.append([SSID, LCID, SF, AT])
        self.parameters.append(parameterList)        
        
    def getLoadSegmentSetIDList(self):
        loadSegmentSetIDList = []
        for i in range(len(self.parameters)):
            curLoadSegmentSetID = []
            curLoadSegmentSetID.append("*LOAD_SEGMENT_SET_ID")
            curLoadSegmentSetID.append(self.parameters[i])
            loadSegmentSetIDList.append(curLoadSegmentSetID)
        return loadSegmentSetIDList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*LOAD_SEGMENT_SET_ID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>70}\n"
            stream.write(formatted_elements)
            for j in range(1,len(parameter)):
                if j == 1:
                    stream.write("$$    SSID      LCID        SF        AT\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")        

# EOS_LINEAR_POLYNOMIAL
class EosLinearPolynomial(DynaKeyword):
    def __init__(self):
        super(EosLinearPolynomial,self).__init__("EOS_LINEAR_POLYNOMIAL")

    def parse(self, eosLinearPolynomialKeywords):
        for i in range(len(eosLinearPolynomialKeywords)):
            parameterList = []
            parameters = self.parse_whole(eosLinearPolynomialKeywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(eosLinearPolynomialKeywords[i][1], [10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddEOSLinearPolynomial(self, EOSID, C0, C1, C2, C3, C4, C5, C6, E0, V0):
        parameterList = []
        parameterList.append([EOSID, C0, C1, C2, C3, C4, C5, C6])
        parameterList.append([E0, V0])
        self.parameters.append(parameterList)      
    
    def getEOSLinearPolynomialList(self):
        eosLinearPolynomialList = []
        for i in range(len(self.parameters)):
            curEOSLinearPolynomial = []
            curEOSLinearPolynomial.append("*EOS_LINEAR_POLYNOMIAL")
            for j in range(len(self.parameters[i])):
                curEOSLinearPolynomial.append(self.parameters[i][j])
            eosLinearPolynomialList.append(curEOSLinearPolynomial)
        return eosLinearPolynomialList  
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*EOS_LINEAR_POLYNOMIAL\n")
            stream.write("$$   EOSID        C0        C1        C2        C3        C4        C5        C6\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      E0        V0\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}\n"
            stream.write(formatted_elements)




class MatAddErosion(DynaKeyword):    
    def __init__(self):
        super(MatAddErosion,self).__init__("MAT_ADD_EROSION")
    
    def parse(self, matAddErosionKeywords):
        for i in range(len(matAddErosionKeywords)):
            curMatErosion = matAddErosionKeywords[i]
            parameterList = [] 
            parameters = self.parse_whole(curMatErosion[0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curMatErosion[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(curMatErosion) > 2:
                parameters = self.parse_whole(curMatErosion[2], [10, 10])
                parameterList.append(parameters)
            if len(curMatErosion) > 3:
                parameters = self.parse_whole(curMatErosion[i][3], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            if len(curMatErosion) > 4:
                parameters = self.parse_whole(curMatErosion[i][4], [10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddMatAddErosion(self, MID, EXCL, MXPRES, MNEPS, EFFEPS, VOLEPS, NUMFIP, NCS, MNPRES, SIGP1, SIGVM, MXEPS, EPSSH, SIGTH, IMPULSE, FAILTM, IDAM, LCREGD, LCFLD, NSFF, EPSTHIN, ENGCRT, RADCRT, LCEPS12, LCEPS13, LCEPSMX, DTEFLT, VOLFRAC, MXTMP, DTMIN):
        parameterList = []
        parameterList.append([MID, EXCL, MXPRES, MNEPS, EFFEPS, VOLEPS, NUMFIP, NCS])    
        parameterList.append([MNPRES, SIGP1, SIGVM, MXEPS, EPSSH, SIGTH, IMPULSE, FAILTM])
        parameterList.append([IDAM, LCREGD])
        parameterList.append([LCFLD, NSFF, EPSTHIN, ENGCRT, RADCRT, LCEPS12, LCEPS13, LCEPSMX])
        parameterList.append([DTEFLT, VOLFRAC, MXTMP, DTMIN])
        self.parameters.append(parameterList)
    
    def getMatList(self):
        matList = []        
        for i in range(len(self.parameters)):
            curMat = [] 
            curMat.append("*MAT_ADD_EROSION")
            curMat.append(self.parameters[i])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            
            parameter = self.parameters[i]
            stream.write("*MAT_ADD_EROSION\n")
            stream.write("$$     MID      EXCL    MXPRES     MNEPS    EFFEPS    VOLEPS    NUMFIP       NCS\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$  MNPRES     SIGP1     SIGVM     MXEPS     EPSSH     SIGTH   IMPULSE    FAILTM\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            if len(parameter) > 2:
                stream.write("$$    IDAM    LCREGD\n")
                formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}\n"
                stream.write(formatted_elements)
            if len(parameter) > 3:
                stream.write("$$   LCFLD      NSFF   EPSTHIN   ENGCRT    RADCRT   LCEPS12   LCEPS13   LCEPSMX\n")
                formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}{str(parameter[3][6]):>10}{str(parameter[3][7]):>10}\n"
                stream.write(formatted_elements)
            if len(parameter) > 4:
                stream.write("$$  DTEFLT   VOLFRAC     MXTMP    DTMIN")
                formatted_elements = f"{str(parameter[4][0]):>10}{str(parameter[4][1]):>10}{str(parameter[4][2]):>10}{str(parameter[4][3]):>10}\n"
                stream.write(formatted_elements)
                
class MatAddPZElectric(DynaKeyword):
    def __init__(self):
        super(MatAddPZElectric,self).__init__("MAT_ADD_PZELECTRIC")
        
    def parse(self, matAddPZElectricKeywords):
        for i in range(len(matAddPZElectricKeywords)):
            curMatPZElectric = matAddPZElectricKeywords[i]
            parameterList = []
            parameters = self.parse_whole(curMatPZElectric[0], [10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curMatPZElectric[1], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curMatPZElectric[2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curMatPZElectric[3], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curMatPZElectric[4], [10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curMatPZElectric[5], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curMatPZElectric[6], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddMatAddPZElectric(self, mid, dtype, gpt, aopt, DMat, PXMat, PYMat, PZMat, Pnt, AVec, DVec):
        parameterList = [] 
        parameterList.append([mid, dtype, gpt, aopt])
        parameterList.append([DMat[0][0], DMat[1][1], DMat[2][2], DMat[0][1], DMat[0][2], DMat[1][2]])
        parameterList.append([PXMat[0][0], PXMat[1][1], PXMat[2][2], PXMat[0][1], PXMat[0][2], PXMat[1][2],PYMat[0][0], PYMat[1][1]])
        parameterList.append([PYMat[2][2], PYMat[0][1], PYMat[0][2], PYMat[1][2], PZMat[0][0], PZMat[1][1], PZMat[2][2], PZMat[0][1]])
        parameterList.append([PZMat[0][2], PZMat[1][2]])    
        parameterList.append([Pnt[0], Pnt[1], Pnt[2], AVec[0], AVec[1], AVec[2]])
        parameterList.append(["","","",DVec[0], DVec[1], DVec[2]])
        
    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = []
            curMat.append("*MAT_ADD_PZELECTRIC")
            curMat.append(self.parameters[i])
            matList.append(curMat)
        return matList
    
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_ADD_PZELECTRIC\n")
            stream.write("$$     MID     DTYPE       GPT      AOPT\n")    
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     DXX       DYY       DZZ       DXY       DXZ       DYZ\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    PX11      PX22      PX33      PX12      PX13      PX23      PY11      PY22\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    PY33      PY12      PY13      PY23      PZ11      PZ22      PZ33      PZ12\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}{str(parameter[3][6]):>10}{str(parameter[3][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    PZ13      PZ23\n")
            formatted_elements = f"{str(parameter[4][0]):>10}{str(parameter[4][1]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XP        YP        ZP        A1        A2        A3\n")
            formatted_elements = f"{str(parameter[5][0]):>10}{str(parameter[5][1]):>10}{str(parameter[5][2]):>10}{str(parameter[5][3]):>10}{str(parameter[5][4]):>10}{str(parameter[5][5]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$                                    D1        D2        D3\n")
            formatted_elements = f"{str(parameter[6][0]):>10}{str(parameter[6][1]):>10}{str(parameter[6][2]):>10}{str(parameter[6][3]):>10}{str(parameter[6][4]):>10}{str(parameter[6][5]):>10}\n"
            stream.write(formatted_elements)

class MatCSCMConcrete(DynaKeyword):
    def __init__(self):
        super(MatCSCMConcrete,self).__init__("MAT_CSCM_CONCRETE")
    
    def parse(self, matCSCMConcreteKeywords):
        for i in range(len(matCSCMConcreteKeywords)):
            parameterList = []
            parameters = self.parse_whole(matCSCMConcreteKeywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(matCSCMConcreteKeywords[i][1], [10])
            parameterList.append(parameters)
            parameters = self.parse_whole(matCSCMConcreteKeywords[i][2], [10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_CSCM_CONCRETE\n")
            for j in range(len(parameter)):
                if j == 0:
                    stream.write("$$     MID        R0     NPLOT     INCRE     IRATE     ERODE     RECOV   ITRETRC\n")
                if j == 1:
                    stream.write("$$    PRED\n")
                if j == 2:
                    stream.write("$$     FPC      DAGG     UNITS\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")

class MatCSCMConcreteTitle(DynaKeyword):
    def __init__(self):
        super(MatCSCMConcreteTitle,self).__init__("MAT_CSCM_CONCRETE_TITLE")
    
    def parse(self, matCSCMConcreteTitleKeywords):
        for i in range(len(matCSCMConcreteTitleKeywords)):
            parameterList = []
            parameters = self.parse_whole(matCSCMConcreteTitleKeywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(matCSCMConcreteTitleKeywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(matCSCMConcreteTitleKeywords[i][2], [10])
            parameterList.append(parameters)
            parameters = self.parse_whole(matCSCMConcreteTitleKeywords[i][3], [10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_CSCM_CONCRETE_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            for j in range(1,len(parameter)):
                if j == 1:
                    stream.write("$$     MID        R0     NPLOT     INCRE     IRATE     ERODE     RECOV   ITRETRC\n")
                if j == 2:
                    stream.write("$$    PRED\n")
                if j == 3:
                    stream.write("$$     FPC      DAGG     UNITS\n")
                for k in range(len(parameter[j])):
                    formatted_elements = f"{str(parameter[j][k]):>10}"
                    stream.write(formatted_elements)
                stream.write("\n")
# Mat 1 
class MatElastic(DynaKeyword):
    def __init__(self):
        super(MatElastic,self).__init__("MAT_ELASTIC")
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            #parameters = mat_keywords[i][0].parse_whole([10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
    
    def AddMatElastic(self, MID, RO, E, PR, DA="", DB="", K=""):
        parameterList = []
        parameterList.append([MID, RO, E, PR, DA, DB, K])
        self.parameters.append(parameterList)

    def MID(self,ith):
        return self.parameters[ith][0]
    
    def RO(self,ith):
        return self.parameters[ith][1]
    
    def E(self,ith):
        return self.parameters[ith][2]
    
    def PR(self,ith):
        return self.parameters[ith][3]
    
    def DA(self,ith):
        return self.parameters[ith][4]
    
    def DB(self,ith):
        return self.parameters[ith][5]
    
    def K(self,ith):
        return self.parameters[ith][6]
    
    def getMatList(self):
        matList = []
        for i in range(len(self.parameters)):
            curMat = [] 
            curMat.append("*MAT_ELASTIC")
            curMat.append(self.parameters[i])
            matList.append(curMat)
        return matList            
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_ELASTIC\n")
            stream.write("$$     MID        RO         E        PR        DA        DB         K\n")
            formatted_elements = f"{str(parameter[0]):>10}{str(parameter[1]):>10}{str(parameter[2]):>10}{str(parameter[3]):>10}{str(parameter[4]):>10}{str(parameter[5]):>10}{str(parameter[6]):>10}\n"
            stream.write(formatted_elements)
# Mat 1 
class MatElasticTitle(DynaKeyword):
    def __init__(self):
        super(MatElasticTitle,self).__init__("MAT_ELASTIC_TITLE")
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = [] 
            #parameters = mat_keywords[i][0].parse_whole([80])
            parameters = self.parse_whole(mat_keywords[i][0], [80])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][1].parse_whole([10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddMatElasticTitle(self, Name, MID, RO, E, PR, DA="", DB="", K=""):
        # float to exponential notation
        # 10.3e format
        RO = "{:10.3e}".format(RO)
        E = "{:10.3e}".format(E)
        PR = "{:10.3e}".format(PR)
        
        
        parameterList = []
        parameterList.append([Name])
        parameterList.append([MID, RO, E, PR, DA, DB, K])
        self.parameters.append(parameterList)
    
    def Name(self,ith):
        return self.parameters[ith][0][0]

    def MID(self,ith):
        return self.parameters[ith][1][0]
    
    def RO(self,ith):
        return self.parameters[ith][1][1]
    
    def E(self,ith):
        return self.parameters[ith][1][2]
    
    def PR(self,ith):
        return self.parameters[ith][1][3]
    
    def DA(self,ith):
        return self.parameters[ith][1][4]
    
    def DB(self,ith):
        return self.parameters[ith][1][5]
    
    def K(self,ith):
        return self.parameters[ith][1][6]
    
    def getMatList(self):
        matList = []
        for i in range(len(self.parameters)):
            curMat = []
            parameter = self.parameters[i]            
            curMat.append("*MAT_ELASTIC_TITLE")
            curMat.append(parameter[0])
            curMat.append(parameter[1])
            matList.append(curMat)
            
        return matList
    
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_ELASTIC_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$     MID        RO         E        PR        DA        DB         K\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}\n"
            stream.write(formatted_elements)
# Mat 3 
class MatPlasticKinematic(DynaKeyword):
    def __init__(self):
        super(MatPlasticKinematic,self).__init__("MAT_PLASTIC_KINEMATIC")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = [] 
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_PLASTIC_KINEMATIC")
            curMat.append(parameter[0])
            curMat.append(parameter[1])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_PLASTIC_KINEMATIC\n")
            stream.write("$$     MID        RO        E        PR      SIGY      ETAN      BETA\n")
            formatted_elements = f"{str(parameter[0][0])}{str(parameter[0][1])}{str(parameter[0][2])}{str(parameter[0][3])}{str(parameter[0][4])}{str(parameter[0][5])}{str(parameter[0][6])}\n"            
            stream.write(formatted_elements)            
            stream.write("$$     SRC       SRP       FS        VP\n")
            formatted_elements = f"{str(parameter[1][0])}{str(parameter[1][1])}{str(parameter[1][2])}{str(parameter[1][3])}\n"
            stream.write(formatted_elements)
# Mat 3 
class MatPlasticKinematicTitle(DynaKeyword):
    def __init__(self):
        super(MatPlasticKinematicTitle,self).__init__("MAT_PLASTIC_KINEMATIC_TITLE")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = [] 
            parameters = self.parse_whole(mat_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddMatPlasticKinematicTitle(self, Name, MID, RO, E, PR, SIGY, ETAN, BETA, SRC, SRP, FS, VP):
        parameterList = []
        parameterList.append([Name])
        parameterList.append([MID, RO, E, PR, SIGY, ETAN, BETA])
        parameterList.append([SRC, SRP, FS, VP])
        self.parameters.append(parameterList)
    
    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_PLASTIC_KINEMATIC")
            curMat.append(parameter[0])
            curMat.append(parameter[1])
            curMat.append(parameter[2])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_PLASTIC_KINEMATIC_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$     MID        RO        E        PR      SIGY      ETAN      BETA\n")
            formatted_elements = f"{str(parameter[1][0])}{str(parameter[1][1])}{str(parameter[1][2])}{str(parameter[1][3])}{str(parameter[1][4])}{str(parameter[1][5])}{str(parameter[1][6])}\n"
            stream.write(formatted_elements)
            stream.write("$$     SRC       SRP       FS        VP\n")
            formatted_elements = f"{str(parameter[2][0])}{str(parameter[2][1])}{str(parameter[2][2])}{str(parameter[2][3])}\n"
            stream.write(formatted_elements)
#Mat 5
class MatSoilAndFoam(DynaKeyword):
    def __init__(self):
        super(MatSoilAndFoam,self).__init__("MAT_SOIL_AND_FOAM")
    
    def parse(self,mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = [] 
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][3], [10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][4], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][5], [10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_SOIL_AND_FOAM")
            curMat.append(parameter[0])
            curMat.append(parameter[1])
            curMat.append(parameter[2])
            curMat.append(parameter[3])
            curMat.append(parameter[4])
            curMat.append(parameter[5])            
            matList.append(curMat)
        return matList

    def write(self, stream):
        for i in range(len(self.parameters)):            
            stream.write("*MAT_SOIL_AND_FOAM\n")
            parameter = self.parameters[i]
            stream.write("$$     MID        RO         G       KUN        A0        A1        A2        PC\n")
            formatted_elements = f"{str(parameter[0][0])}{str(parameter[0][1])}{str(parameter[0][2])}{str(parameter[0][3])}{str(parameter[0][4])}{str(parameter[0][5])}{str(parameter[0][6])}{str(parameter[0][7])}\n"
            stream.write(formatted_elements)
            stream.write("$$     VCR       REF      LCID\n")
            formatted_elements = f"{str(parameter[1][0])}{str(parameter[1][1])}{str(parameter[1][2])}\n"
            stream.write(formatted_elements)
            stream.write("$$    EPS1      EPS2      EPS3      EPS4      EPS5      EPS6      EPS7      EPS8\n")
            formatted_elements = f"{str(parameter[2][0])}{str(parameter[2][1])}{str(parameter[2][2])}{str(parameter[2][3])}{str(parameter[2][4])}{str(parameter[2][5])}{str(parameter[2][6])}{str(parameter[2][7])}\n"
            stream.write(formatted_elements)
            stream.write("$$    EPS9     EPS10\n")
            formatted_elements = f"{str(parameter[3][0])}{str(parameter[3][1])}\n"
            stream.write(formatted_elements)
            stream.write("$$      P1        P2        P3        P4        P5        P6        P7        P8\n")
            formatted_elements = f"{str(parameter[4][0])}{str(parameter[4][1])}{str(parameter[4][2])}{str(parameter[4][3])}{str(parameter[4][4])}{str(parameter[4][5])}{str(parameter[4][6])}{str(parameter[4][7])}\n"
            stream.write(formatted_elements)
            stream.write("$$      P9       P10\n")
            formatted_elements = f"{str(parameter[5][0])}{str(parameter[5][1])}\n"
            stream.write(formatted_elements)
#Mat 6
class MatViscoelastic(DynaKeyword):
    def __init__(self):
        super(MatViscoelastic,self).__init__("MAT_VISCOELASTIC")
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)
        
    def AddMatViscoelastic(self, MID, RO, K, G0, GI, BETA):
        parameterList = [] 
        parameterList.append([MID, RO, K, G0, GI, BETA])
        self.parameters.append(parameterList)
    
    def MID(self, ith):
        return self.parameters[ith][0]
    
    def RO(self, ith):
        return self.parameters[ith][1]

    def K(self, ith):
        return self.parameters[ith][2]
    
    def G0(self, ith):
        return self.parameters[ith][3]
    
    def GI(self, ith):
        return self.parameters[ith][4]
    
    def BETA(self, ith):
        return self.parameters[ith][5]
    
    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = []
            curMat.append("*MAT_VISCOELASTIC")
            curMat.append(self.parameters[i])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_VISCOELASTIC\n")
            stream.write("$$     MID        RO         K        G0        GI      BETA\n")
            formatted_elements = f"{str(parameter[0]):>10}{str(parameter[1]):>10}{str(parameter[2]):>10}{str(parameter[3]):>10}{str(parameter[4]):>10}{str(parameter[5]):>10}\n" 
            stream.write(formatted_elements) 
#Mat 6
class MatViscoelasticTitle(DynaKeyword):
    def __init__(self):
        super(MatViscoelasticTitle,self).__init__("MAT_VISCOELASTIC_TITLE") 
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            parameters = self.parse_whole(mat_keywords[i][0], [80])
            parameterList.append(parameters)    
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10, 10, 10]) 
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddMatViscoelasticTitle(self, Name, MID, RO, K, G0, GI, BETA):
        RO = "{:10.3e}".format(RO)
        K = "{:10.3e}".format(K)
        G0 = "{:10.3e}".format(G0)
        GI = "{:10.3e}".format(GI)
        BETA = "{:10.3e}".format(BETA)
        parameterList = []
        parameterList.append([Name])
        parameterList.append([MID, RO, K, G0, GI, BETA])
        self.parameters.append(parameterList)
    
    def Name(self,ith):
        return self.parameters[ith][0][0]

    def MID(self,ith):
        return self.parameters[ith][1][0]
    
    def RO(self,ith):
        return self.parameters[ith][1][1]
    
    def K(self,ith):
        return self.parameters[ith][1][2]
    
    def G0(self,ith):
        return self.parameters[ith][1][3]
    
    def GI(self,ith):
        return self.parameters[ith][1][4]
    
    def BETA(self,ith):
        return self.parameters[ith][1][5]
    
    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_VISCOELASTIC_TITLE")
            curMat.append(parameter[0])
            curMat.append(parameter[1])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_VISCOELASTIC_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$     MID        RO         K        G0        GI      BETA\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}\n"
            stream.write(formatted_elements)
            
#Mat 14 
class MatSoilAndFoamFailure(DynaKeyword):
    def __init__(self):
        super(MatSoilAndFoamFailure,self).__init__("MAT_SOIL_AND_FOAM_FAILURE")
    
    def parse(self,mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = [] 
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][3], [10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][4], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][5], [10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_SOIL_AND_FOAM_FAILURE")
            curMat.append(parameter[0])
            curMat.append(parameter[1])
            curMat.append(parameter[2])
            curMat.append(parameter[3])
            curMat.append(parameter[4])
            curMat.append(parameter[5])            
            matList.append(curMat)
        return matList

    def write(self, stream):
        for i in range(len(self.parameters)):            
            stream.write("*MAT_SOIL_AND_FOAM_FAILURE\n")
            parameter = self.parameters[i]
            stream.write("$$     MID        RO         G       KUN        A0        A1        A2        PC\n")
            formatted_elements = f"{str(parameter[0][0])}{str(parameter[0][1])}{str(parameter[0][2])}{str(parameter[0][3])}{str(parameter[0][4])}{str(parameter[0][5])}{str(parameter[0][6])}{str(parameter[0][7])}\n"
            stream.write(formatted_elements)
            stream.write("$$     VCR       REF      LCID\n")
            formatted_elements = f"{str(parameter[1][0])}{str(parameter[1][1])}{str(parameter[1][2])}\n"
            stream.write(formatted_elements)
            stream.write("$$    EPS1      EPS2      EPS3      EPS4      EPS5      EPS6      EPS7      EPS8\n")
            formatted_elements = f"{str(parameter[2][0])}{str(parameter[2][1])}{str(parameter[2][2])}{str(parameter[2][3])}{str(parameter[2][4])}{str(parameter[2][5])}{str(parameter[2][6])}{str(parameter[2][7])}\n"
            stream.write(formatted_elements)
            stream.write("$$    EPS9     EPS10\n")
            formatted_elements = f"{str(parameter[3][0])}{str(parameter[3][1])}\n"
            stream.write(formatted_elements)
            stream.write("$$      P1        P2        P3        P4        P5        P6        P7        P8\n")
            formatted_elements = f"{str(parameter[4][0])}{str(parameter[4][1])}{str(parameter[4][2])}{str(parameter[4][3])}{str(parameter[4][4])}{str(parameter[4][5])}{str(parameter[4][6])}{str(parameter[4][7])}\n"
            stream.write(formatted_elements)
            stream.write("$$      P9       P10\n")
            formatted_elements = f"{str(parameter[5][0])}{str(parameter[5][1])}\n"
            stream.write(formatted_elements)
# Mat 9
class MatNull(DynaKeyword):
    def __init__(self):
        super(MatNull,self).__init__("MAT_NULL")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            self.parameters.append(parameters)

    def MID(self,ith):
        return self.parameters[ith][0][0]
    
    def RO(self,ith):
        return self.parameters[ith][0][1]
    
    def PC(self,ith):
        return self.parameters[ith][0][2]
    
    def MU(self,ith):
        return self.parameters[ith][0][3]
    
    def TEROD(self,ith):
        return self.parameters[ith][0][4]
    
    def CEROD(self,ith):
        return self.parameters[ith][0][5]
    
    def YM(self,ith):
        return self.parameters[ith][0][6]
    
    def PR(self,ith):
        return self.parameters[ith][0][7]

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_NULL")            
            curMat.append(parameter)
            matList.append(curMat)
        return matList

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_NULL\n")
            stream.write("$$     MID        RO        PC        MU     TEROD     CEROD        YM        PR\n")
            for j in range(0,len(parameter)):
                formatted_elements = f"{str(parameter[j]):>10}"
                stream.write(formatted_elements)
            stream.write("\n")   

# Mat 17      
class MatOrientedCrack(DynaKeyword):
    def __init__(self):
        super(MatOrientedCrack,self).__init__("MAT_ORIENTED_CRACK")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(mat_keywords[i])>1:
                parameters = self.parse_whole(mat_keywords[i][1], [10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)


    def AddMatOrientedCrack(self, MID, R0, E, PR, SIGY, ETAN, FS, PRF, SOFT=1.0, CVELO=0.0):
        parameterList = []
        parameterList.append([MID, R0, E, PR, SIGY, ETAN, FS, PRF])
        parameterList.append([SOFT, CVELO])
        self.parameters.append(parameterList)
    
    def getMatList(self):
        matList = []
        for i in range(len(self.parameters)):
            curMat = []
            parameter = self.parameters[i]
            curMat.append("*MAT_ORIENTED_CRACK")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_ORIENTED_CRACK\n")
            stream.write("$$     MID        R0         E        PR      SIGY      ETAN        FS       PRF\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            if len(parameter) > 1:
                stream.write("$$    SOFT     CVELO\n")
                formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}\n"
                stream.write(formatted_elements)
            

# Mat 20
class MatRigid(DynaKeyword):
    def __init__(self):
        super(MatRigid,self).__init__("MAT_RIGID")
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            #parameters = mat_keywords[i][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            CMO = self.parse_whole(mat_keywords[i][1], [10])
            if CMO[0] == "":
                CMO = 0.0
            else:
                CMO = float(CMO[0])
            if CMO == 1.0 or CMO == -1.0:
                #parameters = mat_keywords[i][1].parse_whole([10, 10, 10])
                parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10])
            else:
                #parameters = mat_keywords[i][1].parse_whole([10])
                parameters = self.parse_whole(mat_keywords[i][1], [10])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][2].parse_whole([10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def MID(self,ith):
        return self.parameters[ith][0][0]
    
    def RO(self,ith):
        return self.parameters[ith][0][1]
    
    def E(self,ith):
        return self.parameters[ith][0][2]
    
    def PR(self,ith):
        return self.parameters[ith][0][3]
    
    def N(self,ith):
        return self.parameters[ith][0][4]
    
    def COUPLE(self,ith):
        return self.parameters[ith][0][5]
    
    def M(self, ith):
        return self.parameters[ith][0][6]
    
    def ALIASRE(self,ith):
        return self.parameters[ith][0][7]
    
    def CMO(self,ith):
        return self.parameters[ith][1][0]
    
    def CON1(self, ith):
        if self.CMO(ith) == 1.0 or self.CMO(ith) == -1.0:
            return self.parameters[ith][1][1]
        else:
            return None
    
    def CON2(self, ith):
        if self.CMO(ith) == 1.0 or self.CMO(ith) == -1.0:
            return self.parameters[ith][1][2]
        else:
            return None
    
    def LCOA1(self,ith):
        return self.parameters[ith][2][0]
    
    def A2(self,ith):
        return self.parameters[ith][2][1]
    
    def A3(self,ith):
        return self.parameters[ith][2][2]
    
    def V1(self,ith):
        return self.parameters[ith][2][3]
    
    def V2(self,ith):
        return self.parameters[ith][2][4]
    
    def V3(self,ith):
        return self.parameters[ith][2][5]

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_RIGID")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_RIGID\n")
            stream.write("$$     MID        RO         E        PR         N    COUPLE         M   ALIASRE\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     CMO      CON1      CON2\n")
            CMO = float(parameter[1][0])
            if CMO == 1.0 or CMO == -1.0:
                formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}\n"
            else:
                formatted_elements = f"{str(parameter[1][0]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$   LCOA1        A2        A3        V1        V2        V3\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}\n"
            stream.write(formatted_elements)                
# Mat 20
class MatRigidTitle(DynaKeyword):
    def __init__(self):
        super(MatRigidTitle,self).__init__("MAT_RIGID_TITLE")
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            #parameters = mat_keywords[i][0].parse_whole([80])
            parameters = self.parse_whole(mat_keywords[i][0], [80])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][1].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            #CMO = mat_keywords[i][2].parse_whole([10])
            CMO = self.parse_whole(mat_keywords[i][2], [10])
            if CMO[0] == "":
                CMO = 0.0
            else:
                CMO = float(CMO[0])
            
            if CMO == 1.0 or CMO == -1.0:
                #parameters = mat_keywords[i][2].parse_whole([10, 10, 10])
                parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10])
            else:
                #parameters = mat_keywords[i][2].parse_whole([10])
                parameters = self.parse_whole(mat_keywords[i][2], [10])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][3].parse_whole([10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][3], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddMatRigidTitle(self, MID, Name, RO, E, PR, N, COUPLE, M, ALIASRE, CMO, CON1, CON2, LCOA1, A2, A3, V1, V2, V3):
        RO = "{:10.3e}".format(RO)
        E = "{:10.3e}".format(E)
        PR = "{:10.3e}".format(PR)
        
        parameterList = []
        parameterList.append([Name])
        parameterList.append([MID, RO, E, PR, N, COUPLE, M, ALIASRE])
        if CMO == 1.0 or CMO == -1.0:
            parameterList.append([CMO, CON1, CON2])
        else:
            parameterList.append([CMO])
        parameterList.append([LCOA1, A2, A3, V1, V2, V3])
        self.parameters.append(parameterList)
        

    def Name(self,ith):
        return self.parameters[ith][0][0]
    
    def MID(self,ith):
        return self.parameters[ith][1][0]
    
    def RO(self,ith):
        return self.parameters[ith][1][1]
    
    def E(self,ith):
        return self.parameters[ith][1][2]
    
    def PR(self,ith):
        return self.parameters[ith][1][3]
    
    def N(self,ith):
        return self.parameters[ith][1][4]
    
    def COUPLE(self,ith):
        return self.parameters[ith][1][5]
    
    def M(self, ith):
        return self.parameters[ith][1][6]
    
    def ALIASRE(self,ith):
        return self.parameters[ith][1][7]
    
    def CMO(self,ith):
        return self.parameters[ith][2][0]
    
    def CON1(self, ith):
        if self.CMO(ith) == 1.0 or self.CMO(ith) == -1.0:
            return self.parameters[ith][2][1]
        else:
            return None
    
    def CON2(self, ith):
        if self.CMO(ith) == 1.0 or self.CMO(ith) == -1.0:
            return self.parameters[ith][2][2]
        else:
            return None
    
    def LCOA1(self,ith):
        return self.parameters[ith][3][0]
    
    def A2(self,ith):
        return self.parameters[ith][3][1]
    
    def A3(self,ith):
        return self.parameters[ith][3][2]
    
    def V1(self,ith):
        return self.parameters[ith][3][3]
    
    def V2(self,ith):
        return self.parameters[ith][3][4]
    
    def V3(self,ith):
        return self.parameters[ith][3][5]

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_RIGID_TITLE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_RIGID_TITLE\n")
            stream.write("{name}\n".format(name=self.Name(i)))
            stream.write("$$     MID        RO         E        PR         N    COUPLE         M   ALIASRE\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     CMO      CON1      CON2\n")
            if parameter[2][0] == 1.0 or parameter[2][0] == -1.0:
                formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}\n"
            else:
                formatted_elements = f"{str(parameter[2][0]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$   LCOA1        A2        A3        V1        V2        V3\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}\n"
            stream.write(formatted_elements)
# Mat 22
class MatCompositeDamage(DynaKeyword):
    def __init__(self):
        super(MatCompositeDamage,self).__init__("MAT_COMPOSITE_DAMAGE")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][3], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][4], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
    
    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_COMPOSITE_DAMAGE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_COMPOSITE_DAMAGE\n")
            stream.write("$$     MID        RO        EA        EB        EC      PRBA      PRCA      PRCB\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     GAB       GBC       GCA     KFAIL      AOPT      MACF    ATRACK\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XP        YP        ZP        A1        A2        A3\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      V1        V2        V3        D1        D2        D3      BETA\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}{str(parameter[3][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      SC        XT        YT        YC      ALPH        SN       SYZ       SZX\n")
            formatted_elements = f"{str(parameter[4][0]):>10}{str(parameter[4][1]):>10}{str(parameter[4][2]):>10}{str(parameter[4][3]):>10}{str(parameter[4][4]):>10}{str(parameter[4][5]):>10}{str(parameter[4][6]):>10}{str(parameter[4][7]):>10}\n"
            stream.write(formatted_elements)
# Mat 22
class MatCompositeDamageTitle(DynaKeyword):
    def __init__(self):
        super(MatCompositeDamageTitle,self).__init__("MAT_COMPOSITE_DAMAGE_TITLE")
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            parameters = self.parse_whole(mat_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][3], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][4], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][5], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_COMPOSITE_DAMAGE_TITLE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_COMPOSITE_DAMAGE_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$     MID        RO        EA        EB        EC      PRBA      PRCA      PRCB\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     GAB       GBC       GCA     KFAIL      AOPT      MACF    ATRACK\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XP        YP        ZP        A1        A2        A3\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      V1        V2        V3        D1        D2        D3      BETA\n")
            formatted_elements = f"{str(parameter[4][0]):>10}{str(parameter[4][1]):>10}{str(parameter[4][2]):>10}{str(parameter[4][3]):>10}{str(parameter[4][4]):>10}{str(parameter[4][5]):>10}{str(parameter[4][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      SC        XT        YT        YC      ALPH        SN       SYZ       SZX\n")
            formatted_elements = f"{str(parameter[5][0]):>10}{str(parameter[5][1]):>10}{str(parameter[5][2]):>10}{str(parameter[5][3]):>10}{str(parameter[5][4]):>10}{str(parameter[5][5]):>10}{str(parameter[5][6]):>10}{str(parameter[5][7]):>10}\n"
            stream.write(formatted_elements)          
# Mat 24 
class MatPiecewiseLinearPlasticity(DynaKeyword):
    def __init__(self):
        super(MatPiecewiseLinearPlasticity,self).__init__("MAT_PIECEWISE_LINEAR_PLASTICITY")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            #parameters = mat_keywords[i][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][1].parse_whole([10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10, 10])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][2].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][3].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][3], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def MID(self,ith):
        return self.parameters[ith][0][0]

    def RO(self,ith):
        return self.parameters[ith][0][1]
    
    def E(self,ith):
        return self.parameters[ith][0][2]
    
    def PR(self,ith):
        return self.parameters[ith][0][3]
    
    def SIGY(self,ith):
        return self.parameters[ith][0][4]
    
    def ETAN(self,ith):
        return self.parameters[ith][0][5]
    
    def FAIL(self,ith):
        return self.parameters[ith][0][6]
    
    def TDEL(self,ith):
        return self.parameters[ith][0][7]
    
    def C(self,ith):
        return self.parameters[ith][1][0]
    
    def P(self,ith):
        return self.parameters[ith][1][1]
    
    def LCSS(self,ith):
        return self.parameters[ith][1][2]
    
    def LCSR(self,ith):
        return self.parameters[ith][1][3]
    
    def VP(self,ith):
        return self.parameters[ith][1][4]
    
    def EPS1(self,ith):
        return self.parameters[ith][2][0]

    def EPS2(self,ith):
        return self.parameters[ith][2][1]
    
    def EPS3(self,ith):
        return self.parameters[ith][2][2]
    
    def EPS4(self,ith):
        return self.parameters[ith][2][3]
    
    def EPS5(self,ith):
        return self.parameters[ith][2][4]
    
    def EPS6(self,ith):
        return self.parameters[ith][2][5]
    
    def EPS7(self,ith):
        return self.parameters[ith][2][6]
    
    def EPS8(self,ith):
        return self.parameters[ith][2][7]
    
    def ES1(self,ith):
        return self.parameters[ith][3][0]
    
    def ES2(self,ith):
        return self.parameters[ith][3][1]
    
    def ES3(self,ith):
        return self.parameters[ith][3][2]
    
    def ES4(self,ith):
        return self.parameters[ith][3][3]
    
    def ES5(self,ith):
        return self.parameters[ith][3][4]
    
    def ES6(self,ith):
        return self.parameters[ith][3][5]
    
    def ES7(self,ith):
        return self.parameters[ith][3][6]
    
    def ES8(self,ith):
        return self.parameters[ith][3][7]

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_PIECEWISE_LINEAR_PLASTICITY")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        
        for parameter in self.parameters:
            stream.write("*MAT_PIECEWISE_LINEAR_PLASTICITY\n")
            stream.write("$$     MID        RO         E        PR      SIGY      ETAN      FAIL      TDEL\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$       C         P      LCSS      LCSR        Vp\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    EPS1      EPS2      EPS3      EPS4      EPS5      EPS6      EPS7      EPS8\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     ES1       ES2       ES3       ES4       ES5       ES6       ES7       ES8\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}{str(parameter[3][6]):>10}{str(parameter[3][7]):>10}\n"
            stream.write(formatted_elements)
#Mat 24
class MatPiecewiseLinearPlasticityTitle(DynaKeyword):
    def __init__(self):
        super(MatPiecewiseLinearPlasticityTitle,self).__init__("MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            #parameterList.append(mat_keywords[i][0].parse_whole([80]))
            parameterList.append(self.parse_whole(mat_keywords[i][0], [80]))
            #parameters = mat_keywords[i][1].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][2].parse_whole([10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10, 10, 10])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][3].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][3], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            #parameters = mat_keywords[i][4].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(mat_keywords[i][4], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def TITLE(self,ith):
        return self.parameters[ith][0][0]

    def SET_TITLE(self,ith,title):
        self.parameters[ith][0][0] = title

    def MID(self,ith):
        return self.parameters[ith][1][0]

    def SET_MID(self,ith,mid):
        self.parameters[ith][1][0] = mid

    def RO(self,ith):
        return self.parameters[ith][1][1]
    
    def SET_RO(self,ith,ro):
        self.parameters[ith][1][1] = ro
    
    def E(self,ith):
        return self.parameters[ith][1][2]
    
    def SET_E(self,ith,e):
        self.parameters[ith][1][2] = e
    
    def PR(self,ith):
        return self.parameters[ith][1][3]
    
    def SET_PR(self,ith,pr):
        self.parameters[ith][1][3] = pr
    
    def SIGY(self,ith):
        return self.parameters[ith][1][4]
    
    def SET_SIGY(self,ith,sigy):
        self.parameters[ith][1][4] = sigy
    
    def ETAN(self,ith):
        return self.parameters[ith][1][5]
    
    def SET_ETAN(self,ith,etan):
        self.parameters[ith][1][5] = etan
    
    def FAIL(self,ith):
        return self.parameters[ith][1][6]
    
    def SET_FAIL(self,ith,fail):
        self.parameters[ith][1][6] = fail
    
    def TDEL(self,ith):
        return self.parameters[ith][1][7]
    
    def SET_TDEL(self,ith,tdel):
        self.parameters[ith][1][7] = tdel
    
    def C(self,ith):
        return self.parameters[ith][2][0]
    
    def SET_C(self,ith,c):
        self.parameters[ith][2][0] = c
    
    def P(self,ith):
        return self.parameters[ith][2][1]
    
    def SET_P(self,ith,p):
        self.parameters[ith][2][1] = p
    
    def LCSS(self,ith):
        return self.parameters[ith][2][2]
    
    def SET_LCSS(self,ith,lcss):
        self.parameters[ith][2][2] = lcss
    
    def LCSR(self,ith):
        return self.parameters[ith][2][3]
    
    def SET_LCSR(self,ith,lcsr):
        self.parameters[ith][2][3] = lcsr
    
    def VP(self,ith):
        return self.parameters[ith][2][4]
    
    def SET_VP(self,ith,vp):
        self.parameters[ith][2][4] = vp
    
    def EPS1(self,ith):
        return self.parameters[ith][3][0]
    
    def SET_EPS1(self,ith,eps1):
        self.parameters[ith][3][0] = eps1

    def EPS2(self,ith):
        return self.parameters[ith][3][1]
    
    def SET_EPS2(self,ith,eps2):
        self.parameters[ith][3][1] = eps2
    
    def EPS3(self,ith):
        return self.parameters[ith][3][2]
    
    def SET_EPS3(self,ith,eps3):
        self.parameters[ith][3][2] = eps3
    
    def EPS4(self,ith):
        return self.parameters[ith][3][3]
    
    def SET_EPS4(self,ith,eps4):
        self.parameters[ith][3][3] = eps4
    
    def EPS5(self,ith):
        return self.parameters[ith][3][4]
    
    def SET_EPS5(self,ith,eps5):
        self.parameters[ith][3][4] = eps5
    
    def EPS6(self,ith):
        return self.parameters[ith][3][5]
    
    def SET_EPS6(self,ith,eps6):
        self.parameters[ith][3][5] = eps6
    
    def EPS7(self,ith):
        return self.parameters[ith][3][6]
    
    def SET_EPS7(self,ith,eps7):
        self.parameters[ith][3][6] = eps7
    
    def EPS8(self,ith):
        return self.parameters[ith][3][7]
    
    def SET_EPS8(self,ith,eps8):
        self.parameters[ith][3][7] = eps8
    
    def ES1(self,ith):
        return self.parameters[ith][4][0]

    def SET_ES1(self,ith,es1):
        self.parameters[ith][4][0] = es1
    
    def ES2(self,ith):
        return self.parameters[ith][4][1]
    
    def SET_ES2(self,ith,es2):
        self.parameters[ith][4][1] = es2
    
    def ES3(self,ith):
        return self.parameters[ith][4][2]
    
    def SET_ES3(self,ith,es3):
        self.parameters[ith][4][2] = es3
    
    def ES4(self,ith):
        return self.parameters[ith][4][3]
    
    def SET_ES4(self,ith,es4):
        self.parameters[ith][4][3] = es4
    
    def ES5(self,ith):
        return self.parameters[ith][4][4]
    
    def SET_ES5(self,ith,es5):
        self.parameters[ith][4][4] = es5
    
    def ES6(self,ith):
        return self.parameters[ith][4][5]
    
    def SET_ES6(self,ith,es6):
        self.parameters[ith][4][5] = es6
    
    def ES7(self,ith):
        return self.parameters[ith][4][6]
    
    def SET_ES7(self,ith,es7):
        self.parameters[ith][4][6] = es7
    
    def ES8(self,ith):
        return self.parameters[ith][4][7]
    
    def SET_ES8(self,ith,es8):
        self.parameters[ith][4][7] = es8

    def AddMatPiecewiseLinearPlasticityTitle(self, title, mid, ro, e, pr, sigy, etan, fail, tdel, c, p, lcss, lcsr, vp, eps, es):
        parameterList = []
        parameterList.append([title])
        parameterList.append([mid, ro, e, pr, sigy, etan, fail, tdel])
        parameterList.append([c, p, lcss, lcsr, vp])
        curEps = [] 
        for i in range(len(eps)):
            curEps.append(eps[i])
        parameterList.append(curEps)
        curEs = []
        for i in range(len(es)):
            curEs.append(es[i])
        parameterList.append(curEs)    
        self.parameters.append(parameterList)

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        
        for parameter in self.parameters:
            stream.write("*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE\n")
            stream.write("{title}\n".format(title=parameter[0][0]))
            stream.write("$$     MID        RO         E        PR      SIGY      ETAN      FAIL      TDEL\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$       C         P      LCSS      LCSR        Vp\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    EPS1      EPS2      EPS3      EPS4      EPS5      EPS6      EPS7      EPS8\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}{str(parameter[3][6]):>10}{str(parameter[3][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     ES1       ES2       ES3       ES4       ES5       ES6       ES7       ES8\n")
            formatted_elements = f"{str(parameter[4][0]):>10}{str(parameter[4][1]):>10}{str(parameter[4][2]):>10}{str(parameter[4][3]):>10}{str(parameter[4][4]):>10}{str(parameter[4][5]):>10}{str(parameter[4][6]):>10}{str(parameter[4][7]):>10}\n"
            stream.write(formatted_elements)

#Mat 25
class MatEnhancedCompositeDamage(DynaKeyword):
    def __init__(self):
        super(MatEnhancedCompositeDamage,self).__init__("MAT_ENHANCED_COMPOSITE_DAMAGE")
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            for j in range(len(mat_keywords[i])):
                parameters = self.parse_whole(mat_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_ENHANCED_COMPOSITE_DAMAGE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for parameter in self.parameters:
            stream.write("*MAT_ENHANCED_COMPOSITE_DAMAGE\n")
            stream.write("$$     MID        RO        EA        EB        EC      PRBA      PRCA      PRCB\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     GAB       GBC       GCA      (KF)      AOPT      2WAY        TI\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XP        YP        ZP        A1        A2        A3    MANGLE\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}\n"
            stream.write(formatted_elements)
            if len(parameter) > 3: 
                stream.write("$$      V1        V2        V3        D1        D2        D3    DFAILM    DFAILS\n")
                formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}{str(parameter[3][6]):>10}{str(parameter[3][7]):>10}\n"
                stream.write(formatted_elements)    
                
            if len(parameter) > 4:
                stream.write("$$   TFAIL      ALPH      SOFT      FBRT     YCFAC    DFAILT    DFAILC       EFS\n")            
                formatted_elements = f"{str(parameter[4][0]):>10}{str(parameter[4][1]):>10}{str(parameter[4][2]):>10}{str(parameter[4][3]):>10}{str(parameter[4][4]):>10}{str(parameter[4][5]):>10}{str(parameter[4][6]):>10}{str(parameter[4][7]):>10}\n"
                stream.write(formatted_elements)
            
            if len(parameter) > 5:                
                stream.write("$$      XC        XT        YC        YT        SC      CRIT      BETA\n")
                formatted_elements = f"{str(parameter[5][0]):>10}{str(parameter[5][1]):>10}{str(parameter[5][2]):>10}{str(parameter[5][3]):>10}{str(parameter[5][4]):>10}{str(parameter[5][5]):>10}{str(parameter[5][6]):>10}{str(parameter[5][7]):>10}\n"
                stream.write(formatted_elements)
            
            if len(parameter) > 6:                
                stream.write("$$     PFL      EPSF      EPSR      TSMD     SOFT2\n")
                formatted_elements = f"{str(parameter[6][0]):>10}{str(parameter[6][1]):>10}{str(parameter[6][2]):>10}{str(parameter[6][3]):>10}{str(parameter[6][4]):>10}\n"
                stream.write(formatted_elements)
            
            if len(parameter) > 7:
                stream.write("$$  SLIMT1    SLIMC1    SLIMT2    SLIMC2     SLIMS    NCYRED     SOFTG\n")
                formatted_elements = f"{str(parameter[7][0]):>10}{str(parameter[7][1]):>10}{str(parameter[7][2]):>10}{str(parameter[7][3]):>10}{str(parameter[7][4]):>10}{str(parameter[7][5]):>10}{str(parameter[7][6]):>10}\n"
                stream.write(formatted_elements)
            
            if len(parameter) > 8:                
                stream.write("$$    LCXC      LCXT      LCYC      LCYT      LCSC        DT\n")
                formatted_elements = f"{str(parameter[8][0]):>10}{str(parameter[8][1]):>10}{str(parameter[8][2]):>10}{str(parameter[8][3]):>10}{str(parameter[8][4]):>10}{str(parameter[8][5]):>10}\n"
                stream.write(formatted_elements)

class MatEnhancedCompositeDamageTitle(DynaKeyword):
    def __init__(self):
        super(MatEnhancedCompositeDamageTitle,self).__init__("MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE")
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            parameterList.append(self.parse_whole(mat_keywords[i][0], [80]))
            for j in range(1,len(mat_keywords[i])):
                parameters = self.parse_whole(mat_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for parameter in self.parameters:            
            stream.write("*MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$     MID        RO        EA        EB        EC      PRBA      PRCA      PRCB\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     GAB       GBC       GCA      (KF)      AOPT      2WAY        TI\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XP        YP        ZP        A1        A2        A3    MANGLE\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}{str(parameter[3][6]):>10}\n"
            stream.write(formatted_elements)
            if len(parameter) > 4: 
                stream.write("$$      V1        V2        V3        D1        D2        D3    DFAILM    DFAILS\n")
                formatted_elements = f"{str(parameter[4][0]):>10}{str(parameter[4][1]):>10}{str(parameter[4][2]):>10}{str(parameter[4][3]):>10}{str(parameter[4][4]):>10}{str(parameter[4][5]):>10}{str(parameter[4][6]):>10}{str(parameter[4][7]):>10}\n"
                stream.write(formatted_elements)    
                
            if len(parameter) > 5:
                stream.write("$$   TFAIL      ALPH      SOFT      FBRT     YCFAC    DFAILT    DFAILC       EFS\n")            
                formatted_elements = f"{str(parameter[5][0]):>10}{str(parameter[5][1]):>10}{str(parameter[5][2]):>10}{str(parameter[5][3]):>10}{str(parameter[5][4]):>10}{str(parameter[5][5]):>10}{str(parameter[5][6]):>10}{str(parameter[5][7]):>10}\n"
                stream.write(formatted_elements)
            
            if len(parameter) > 6:                
                stream.write("$$      XC        XT        YC        YT        SC      CRIT      BETA\n")
                formatted_elements = f"{str(parameter[6][0]):>10}{str(parameter[6][1]):>10}{str(parameter[6][2]):>10}{str(parameter[6][3]):>10}{str(parameter[6][4]):>10}{str(parameter[6][5]):>10}{str(parameter[6][6]):>10}\n"
                stream.write(formatted_elements)
            
            if len(parameter) > 7:                
                stream.write("$$     PFL      EPSF      EPSR      TSMD     SOFT2\n")
                formatted_elements = f"{str(parameter[7][0]):>10}{str(parameter[7][1]):>10}{str(parameter[7][2]):>10}{str(parameter[7][3]):>10}{str(parameter[7][4]):>10}\n"
                stream.write(formatted_elements)
            
            if len(parameter) > 8:
                stream.write("$$  SLIMT1    SLIMC1    SLIMT2    SLIMC2     SLIMS    NCYRED     SOFTG\n")
                formatted_elements = f"{str(parameter[8][0]):>10}{str(parameter[8][1]):>10}{str(parameter[8][2]):>10}{str(parameter[8][3]):>10}{str(parameter[8][4]):>10}{str(parameter[8][5]):>10}{str(parameter[8][6]):>10}\n"
                stream.write(formatted_elements)
            
            if len(parameter) > 9:                
                stream.write("$$    LCXC      LCXT      LCYC      LCYT      LCSC        DT\n")
                formatted_elements = f"{str(parameter[9][0]):>10}{str(parameter[9][1]):>10}{str(parameter[9][2]):>10}{str(parameter[9][3]):>10}{str(parameter[9][4]):>10}{str(parameter[9][5]):>10}\n"
                stream.write(formatted_elements)
                                     

#Mat 27               
class MatMooneyRivlinRubber(DynaKeyword):
    def __init__(self):
        super(MatMooneyRivlinRubber,self).__init__("MAT_MOONEY-RIVLIN_RUBBER")
    
    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            parameters = self.parse_whole(mat_keywords[i][0], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(mat_keywords[i]) == 2:
                parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_MOONEY-RIVLIN_RUBBER")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_MOONEY-RIVLIN_RUBBER\n")
            stream.write("$$     MID        RO        PR         A         B       REF\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}\n"
            stream.write(formatted_elements)
            if len(parameter) == 2:
                stream.write("$$    SGL        SW        ST      LCID\n")
                formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}\n"
                stream.write(formatted_elements)
#Mat 27   
class MatMooneyRivlinRubberTitle(DynaKeyword):
    def __init__(self):
        super(MatMooneyRivlinRubberTitle,self).__init__("MAT_MOONEY_RIVLIN-RUBBER_TITLE")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            parameterList = []
            parameters = self.parse_whole(mat_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(mat_keywords[i][1], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(mat_keywords[i]) == 3:
                parameters = self.parse_whole(mat_keywords[i][2], [10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_MOONEY-RIVLIN_RUBBER_TITLE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_MOONEY-RIVLIN_RUBBER_TITLE\n")
            stream.write("{title}\n".format(title=parameter[0][0]))
            stream.write("$$     MID        RO        PR         A         B       REF\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}\n"
            stream.write(formatted_elements)
            if len(parameter) == 3:
                stream.write("$$    SGL        SW        ST      LCID\n")
                formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}\n"
                stream.write(formatted_elements)   
#Mat 57
class MatLowDensityFoam(DynaKeyword):
    def __init__(self):
        super(MatLowDensityFoam,self).__init__("MAT_LOW_DENSITY_FOAM")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            curLowDensityFoam = mat_keywords[i]
            parameterList = []
            parameters = self.parse_whole(curLowDensityFoam[0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curLowDensityFoam[1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)   

    def getMatList(self):
        matList = []
        for i in range(len(self.parameters)):
            curMat = []
            parameter = self.parameters[i]
            curMat.append("*MAT_LOW_DENSITY_FOAM")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_LOW_DENSITY_FOAM\n")
            stream.write("$$     MID        RO         E      LCID        TC        HU      BETA      DAMP\n")
            stream.write(f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n")
            stream.write("$$   SHAPE      FAIL    BVFLAG        ED     BETA1      KCON       REF\n")
            stream.write(f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}\n")
class MatLowDensityFoamTitle(DynaKeyword):
    def __init__(self):
        super(MatLowDensityFoamTitle,self).__init__("MAT_LOW_DENSITY_FOAM_TITLE")

    def parse(self, mat_keywords):
        for i in range(len(mat_keywords)):
            curLowDensityFoam = mat_keywords[i]
            parameterList = []
            parameters = self.parse_whole(curLowDensityFoam[0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(curLowDensityFoam[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curLowDensityFoam[2], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getMatList(self):
        matList = []
        for i in range(len(self.parameters)):
            curMat = []
            parameter = self.parameters[i]
            curMat.append("*MAT_LOW_DENSITY_FOAM_TITLE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
        

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_LOW_DENSITY_FOAM_TITLE\n")
            stream.write("{title}\n".format(title=parameter[0][0]))
            stream.write("$$     MID        RO         E      LCID        TC        HU      BETA      DAMP\n")
            stream.write(f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n")
            stream.write("$$   SHAPE      FAIL    BVFLAG        ED     BETA1      KCON       REF\n")
            stream.write(f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}\n")

#Mat 100 
class MatSpotweld(DynaKeyword):
    def __init__(self):
        super(MatSpotweld,self).__init__("MAT_SPOTWELD")
    
    def parse(self, spotweldkeyword):
        for i in range(len(spotweldkeyword)):
            curSpotweld = spotweldkeyword[i]
            parameterList = []
            parameters = self.parse_whole(curSpotweld[0], [10, 10, 10, 10, 10, 10, 10, 10])            
            parameterList.append(parameters)
            parameters = self.parse_whole(curSpotweld[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_SPOTWELD")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_SPOTWELD\n")
            stream.write("$$     MID        RO         E        PR      SIGY        EH        DT     TFAIL\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$   EFAIL       NRR       NRS       NRT       MRR       MSS       MTT        NF\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
#Mat 100
class MatSpotweldTitle(DynaKeyword):
    def __init__(self):
        super(MatSpotweldTitle,self).__init__("MAT_SPOTWELD_TITLE")
    
    def parse(self, spotweldkeyword):
        for i in range(len(spotweldkeyword)):
            curSpotweld = spotweldkeyword[i]
            parameterList = []
            parameters = self.parse_whole(curSpotweld[0], [80])            
            parameterList.append(parameters)
            parameters = self.parse_whole(curSpotweld[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curSpotweld[2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i]
            curMat.append("*MAT_SPOTWELD_TITLE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_SPOTWELD_TITLE\n")
            stream.write("{title}\n".format(title=parameter[0][0]))
            stream.write("$$     MID        RO         E        PR      SIGY        EH        DT     TFAIL\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$   EFAIL       NRR       NRS       NRT       MRR       MSS       MTT        NF\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
            stream.write(formatted_elements)

#Mat 138
class MatCohesiveMixedMode(DynaKeyword):
    def __init__(self):
        super(MatCohesiveMixedMode,self).__init__("MAT_COHESIVE_MIXED_MODE")
    
    def parse(self, cohesiveMixedMode):
        for i in range(len(cohesiveMixedMode)):
            curCohesiveMixedMode = cohesiveMixedMode[i]
            parameterList = [] 
            parameters = self.parse_whole(curCohesiveMixedMode[0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curCohesiveMixedMode[1], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)    
            self.parameters.append(parameterList)
            
    def getMatList(self):
        matList = []
        for i in range(len(self.parameters)):
            curMat = []
            parameter = self.parameters[i] 
            curMat.append("*MAT_COHESIVE_MIXED_MODE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList

    def AddMatCohesiveMixedMode(self, MID,RO,ROFLG,INTFAIL,EN,ET,GIC,GIIC,XMU,T,S,UND,UTD,GAMMA):
        parameterList = []
        parameterList.append([MID,RO,ROFLG,INTFAIL,EN,ET,GIC,GIIC])
        parameterList.append([XMU,T,S,UND,UTD,GAMMA])
        self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_COHESIVE_MIXED_MODE\n")
            stream.write("$$     MID        RO     ROFLG   INTFAIL        EN        ET       GIC      GIIC\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     XMU        T         S       UND       UTD     GAMMA\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}\n"
            stream.write(formatted_elements)

#Mat 138 
class MatCohesiveMixedModeTitle(DynaKeyword):
    def __init__(self):
        super(MatCohesiveMixedModeTitle,self).__init__("MAT_COHESIVE_MIXED_MODE_TITLE")

    def parse(self, cohesiveMixedModeTitle):
        for i in range(len(cohesiveMixedModeTitle)):
            curCohesiveMixedModeTitle = cohesiveMixedModeTitle[i]
            parameterList = []
            parameters = self.parse_whole(curCohesiveMixedModeTitle[0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(curCohesiveMixedModeTitle[1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(curCohesiveMixedModeTitle[2], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getMatList(self):
        matList = [] 
        for i in range(len(self.parameters)):
            curMat = [] 
            parameter = self.parameters[i] 
            curMat.append("*MAT_COHESIVE_MIXED_MODE_TITLE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList 
    
    def AddMatCohesiveMixedModeTitle(self, MID, title, RO, ROFLG, INTFAIL, EN, ET, GIC, GIIC, XMU, T, S, UND, UTD, GAMMA):
        parameterList = [] 
        parameterList.append([title])
        parameterList.append([MID, RO, ROFLG, INTFAIL, EN, ET, GIC, GIIC])
        parameterList.append([XMU, T, S, UND, UTD, GAMMA])
        self.parameters.append(parameterList)
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_COHESIVE_MIXED_MODE_TITLE\n")
            stream.write("$$   TITLE\n")
            formatted_elements = f"{str(parameter[0][0]):>80}\n"
            stream.write(formatted_elements)
            stream.write("$$     MID        RO     ROFLG   INTFAIL        EN        ET       GIC      GIIC\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     XMU        T         S       UND       UTD     GAMMA\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}\n"
            stream.write(formatted_elements)
            
#Mat 292
class MatElasticPeri(DynaKeyword):
    def __init__(self):
        super(MatElasticPeri,self).__init__("MAT_ELASTIC_PERI")
    
    def parse(self, elasticPeri):
        for i in range(len(elasticPeri)):
            curElasticPeri = elasticPeri[i]
            parameterList = []
            parameters = self.parse_whole(curElasticPeri[0], [10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getMatList(self):
        matList = []
        for i in range(len(self.parameters)):
            curMat = []
            parameter = self.parameters[i]
            curMat.append("*MAT_ELASTIC_PERI")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def AddMatElasticPeri(self, mid, R0, E, GT, GS):
        parameterList = []        
        parameterList.append([mid, R0, E, GT, GS])
        self.parameters.append(parameterList)
                
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_ELASTIC_PERI\n")
            stream.write("$$     MID        RO         E        GT        GS\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}\n"
            stream.write(formatted_elements)
#Mat 292
class MatElasticPeriTitle(DynaKeyword):
    def __init__(self):
        super(MatElasticPeriTitle,self).__init__("MAT_ELASTIC_PERI_TITLE")
        
    def parse(self, elasticPeri):
        for i in range(len(elasticPeri)):
            curElasticPeri = elasticPeri[i]
            parameterList = []
            parameters = self.parse_whole(curElasticPeri[0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(curElasticPeri[1], [10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getMatList(self):
        matList = []
        for i in range(len(self.parameters)):
            curMat = []
            parameter = self.parameters[i]
            curMat.append("*MAT_ELASTIC_PERI_TITLE")
            for j in range(len(parameter)):
                curMat.append(parameter[j])
            matList.append(curMat)
        return matList
    
    def AddMatElasticPeriTitle(self, mid, title, R0, E, GT, GS):
        parameterList = []
        parameterList.append([title])
        parameterList.append([mid, R0, E, GT, GS])
        self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*MAT_ELASTIC_PERI_TITLE\n")
            stream.write("{title}\n".format(title=parameter[0][0]))
            stream.write("$$     MID        RO         E        GT        GS\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}\n"
            stream.write(formatted_elements)

class DynaNode(DynaKeyword):
    def __init__(self):
        super(DynaNode,self).__init__("NODE")
      
    def parse(self, node_keywords):
        for i in range(len(node_keywords)):
            parameterList = [] 
            for j in range(len(node_keywords[i])):
                #parameters = node_keywords[i][j].parse_whole([8, 16, 16, 16, 8, 8])
                parameters = self.parse_whole(node_keywords[i][j], [8, 16, 16, 16, 8, 8])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def NID(self,ith, jth):
        return self.parameters[ith][jth][0]
    
    def X(self,ith,jth):
        return self.parameters[ith][jth][1]
    
    def Y(self,ith,jth):
        return self.parameters[ith][jth][2]
    
    def Z(self,ith,jth):
        return self.parameters[ith][jth][3]
    
    def TC(self,ith,jth):
        return self.parameters[ith][jth][4]
    
    def RC(self,ith,jth):
        return self.parameters[ith][jth][5]
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            if i == 0:
                stream.write("$$ {i}st Node List\n".format(i=i+1))
            elif i == 1:
                stream.write("$$ {i}nd Node List\n".format(i=i+1))
            elif i == 2:
                stream.write("$$ {i}rd Node List\n".format(i=i+1))
            else:
                stream.write("$$ {i}th Node List\n".format(i=i+1))
            stream.write("*NODE\n")
            stream.write("$$   NID               X               Y               Z      TC      RC\n")
            for parameter in self.parameters[i]:
                formatted_elements = f"{str(parameter[0]):>8}{str(parameter[1]):>16}{str(parameter[2]):>16}{str(parameter[3]):>16}{str(parameter[4]):>8}{str(parameter[5]):>8}"
                result = formatted_elements
                stream.write(result)
                stream.write("\n")      
    def getNodeListAdvanced(self):
        # Flatten parameters to a list of entries
        all_entries = [entry for param in self.parameters for entry in param]

        # Preallocate the data array
        nTotal = len(all_entries)
        data = np.zeros((nTotal, 6))

        # Helper function to check if the string is convertible to a float
        def is_convertible_to_float(value):
            return value.replace('.', '', 1).isdigit()

        # Process entries without try-except
        for jj, entry in enumerate(all_entries):
            for k in range(min(len(entry), 6)):  # Only loop for the valid length
                if entry[k] != '' and is_convertible_to_float(entry[k]):
                    data[jj, k] = float(entry[k])
                else:
                    data[jj, k] = 0  # Default value for non-convertible entries

    # Flatten parameters and process in parallel
    def is_float(self,value):
        try:
            float(value)
            return True
        except ValueError:
            return False
       
    '''def getNodeListParallel(self):
        import numpy as np
        from multiprocessing import Pool

     

        nTotal = sum(len(param) for param in self.parameters)

        # Preallocate data
        data = np.zeros((nTotal, 6))

        # Using multiprocessing to process entries in parallel
        with Pool() as pool:
            all_entries = [entry for param in self.parameters for entry in param]
            processed_entries = pool.map(process_entry, all_entries)

        # Assign processed entries back to the data array
        for jj, processed_entry in enumerate(processed_entries):
            data[jj, :len(processed_entry)] = processed_entry
        return data'''
    
    def getNodeList(self):
        nTotal = sum(len(param) for param in self.parameters)

        # Initialize data with zeros
        data = np.zeros((nTotal, 6))

        jj = 0
        for param in self.parameters:
            for entry in param:
                try:
                    # Convert all elements in the entry to float at once
                    data[jj, :len(entry)] = [float(x) if x.strip() else 0 for x in entry]
                except ValueError:
                    # If there is a failure, handle it (here assumed 0)
                    data[jj, :len(entry)] = 0
                jj += 1
        return data
    def getNodeListOld(self):
        nTotal = 0
        for i in range(len(self.parameters)):
            nTotal += len(self.parameters[i])
        
        # size initialize as 10 by 6 matrix, 1 col is id and others are float. it should be faster than append. first col should be integer
        data = np.zeros((nTotal, 6))
        jj = 0
        for i in range(len(self.parameters)):
            for j in range(len(self.parameters[i])):
                for k in range(len(self.parameters[i][j])):
                    try:
                        # Attempt to convert the string to a float
                        data[jj][k] = self.parameters[i][j][k]                        
                    except ValueError:
                        # If conversion fails, set num to 0
                        data[j][k] = 0
                jj = jj + 1
                    
        return data
        

class Parameter(DynaKeyword):
    def __init__(self):
        super(Parameter,self).__init__("PARAMETER")

    def parse(self, parameter_keywords):
        for i in range(len(parameter_keywords)):
            parameterList = [] 
            for j in range(len(parameter_keywords[i])):
                #parameters = parameter_keywords[i][j].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
                parameters = self.parse_whole(parameter_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*PARAMETER\n")
            stream.write("$$   PRMR1      VAL1     PRMR2      VAL2     PRMR3      VAL3     PRMR4      VAL4\n")
            for parameter in self.parameters[i]:
                formatted_elements = f"{str(parameter[0]):>10}{str(parameter[1]):>10}{str(parameter[2]):>10}{str(parameter[3]):>10}{str(parameter[4]):>10}{str(parameter[5]):>10}{str(parameter[6]):>10}{str(parameter[7]):>10}\n"
                stream.write(formatted_elements)

class Part(DynaKeyword):
    def __init__(self):
        super(Part,self).__init__("PART")

    def parse(self, part_keywords):
        for i in range(len(part_keywords)):
            partith = part_keywords[i]
            parameterMatrix = [] 
            for j in range(0,len(partith),2):
                parameterList = []
                #parameters = partith[j].parse_whole([80])
                parameters = self.parse_whole(partith[j], [80])
                parameterList.append(parameters)
                #parameters = partith[j+1].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
                parameters = self.parse_whole(partith[j+1], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
                parameterMatrix.append(parameterList)
            self.parameters.append(parameterMatrix)
    
    def NAME(self,ith,jth):
        return self.parameters[ith][jth][0]
    
    def PID(self,ith,jth):
        return self.parameters[ith][jth][1][0]
    
    def SECID(self,ith,jth):
        return self.parameters[ith][jth][1][1]
    
    def MID(self,ith,jth):
        return self.parameters[ith][jth][1][2]
    
    def EOSID(self,ith,jth):
        return self.parameters[ith][jth][1][3]
    
    def HGID(self,ith,jth):
        return self.parameters[ith][jth][1][4]
    
    def GRAV(self,ith,jth):
        return self.parameters[ith][jth][1][5]
    
    def ADPOPT(self,ith,jth):
        return self.parameters[ith][jth][1][6]
    
    def TMID(self,ith,jth):
        return self.parameters[ith][jth][1][7]
    
    def HDIV(self,ith,jth):
        return self.parameters[ith][jth][1][4]
    
    def SHRINK(self,ith,jth):
        return self.parameters[ith][jth][1][5]
    
    def THICK(self,ith,jth):
        return self.parameters[ith][jth][1][6]
    
    def OFFSET(self,ith,jth):
        return self.parameters[ith][jth][1][7]
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*PART\n")
            for j in range(len(self.parameters[i])):
                parameter = self.parameters[i][j]
                stream.write("{name}\n".format(name=parameter[0][0]))
                #stream.write("$$     PID     SECID       MID     EOSID      HDIV    SHRINK     THICK    OFFSET\n")
                stream.write("$$     PID     SECID       MID     EOSID      HGID      GRAV    ADPOPT      TMID\n")
                formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
                stream.write(formatted_elements)

    def getPartList(self):
        nTotal = 0
        for i in range(len(self.parameters)):
            nTotal += len(self.parameters[i])
        dataList = [] 
        for i in range(len(self.parameters)):
            for j in range(len(self.parameters[i])):
                parameter = self.parameters[i][j]
                partData = [] 
                partData.append(parameter[0][0])
                for k in range(8):
                    partData.append(parameter[1][k])
                dataList.append(partData)
        return dataList



class PartComposite(DynaKeyword):
    def __init__(self):
        super(PartComposite,self).__init__("PART_COMPOSITE")

    def parse(self, part_keywords):
        for i in range(len(part_keywords)):
            parameterList = []
            parameters = self.parse_whole(part_keywords[i][0], [80])
            if "OPTCARD" in parameters[0]:
                parameters = self.parse_whole(part_keywords[i][0], [10, 10])
            parameterList.append(parameters)
            for j in range(1,len(part_keywords[i])):
                parameters = self.parse_whole(part_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*PART_COMPOSITE\n")
            parameters = self.parameters[i]
            if parameters[0][0] == "OPTCARD":
                formatted_elements = f"{str(parameters[0][0]):>10}{str(parameters[0][1]):>10}\n"
                stream.write(formatted_elements)
            else:
                stream.write("{name}\n".format(name=parameters[0][0]))
            
            for j in range(1,len(parameters)):
                if j == 1:
                    stream.write("$$     PID    ELFORM      SHRF      NLOC     MAREA      HGID    ADPOPT    THSHEL\n")
                elif j == 2:
                    stream.write("$$    MIDi    THICKi        Bi     TMIDi    MIDi+1  THICKi+1      Bi+1   TMIDi+1\n")
                formatted_elements = f"{str(parameters[j][0]):>10}{str(parameters[j][1]):>10}{str(parameters[j][2]):>10}{str(parameters[j][3]):>10}{str(parameters[j][4]):>10}{str(parameters[j][5]):>10}{str(parameters[j][6]):>10}{str(parameters[j][7]):>10}\n"
                stream.write(formatted_elements)
   
    def getPartList(self):
        nTotal = 0
        for i in range(len(self.parameters)):
            nTotal += 1
        dataList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            partData = [] 
            partData.append(parameter[0][0])
            for j in range(1,len(parameter)):
                partDataPoint = [] 
                for k in range(len(parameter[j])):
                    partDataPoint.append(parameter[j][k])
                partData.append(partDataPoint)
            dataList.append(partData)
        return dataList

class PartContact(DynaKeyword):
    def __init__(self):
        super(PartContact,self).__init__("PART_CONTACT")

    def parse(self, partContactKeywords):
        for i in range(len(partContactKeywords)):
            parameterList = [] 
            if len(partContactKeywords[i]) == 2:
                for j in range(len(partContactKeywords[i])):                
                    parameters = self.parse_whole(partContactKeywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                    parameterList.append(parameters)
            elif len(partContactKeywords[i]) == 3:
                parameters = self.parse_whole(partContactKeywords[i][0], [80])
                parameterList.append(parameters)
                for j in range(1,len(partContactKeywords[i])):                
                    parameters = self.parse_whole(partContactKeywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                    parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            if len(parameter) == 2:
                stream.write("*PART_CONTACT\n")
                stream.write("$$     PID     SECID       MID     EOSID      HGID      GRAV    ADPOPT      TMID\n")
                formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
                stream.write(formatted_elements)
                stream.write("$$      FS        FD        DC        VC      OPTT       SFT       SSF    CPARM8\n")
                formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            elif len(parameter) == 3:
                stream.write("*PART_CONTACT\n")
                stream.write("{name}\n".format(name=parameter[0][0]))
                stream.write("$$     PID     SECID       MID     EOSID      HGID      GRAV    ADPOPT      TMID\n")
                formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
                stream.write(formatted_elements)
                stream.write("$$      FS        FD        DC        VC      OPTT       SFT       SSF    CPARM8\n")
                formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
            stream.write(formatted_elements)

class RigidWallGeometricFlatDisplay(DynaKeyword):
    def __init__(self):
        super(RigidWallGeometricFlatDisplay,self).__init__("RIGIDWALL_GEOMETRIC_FLAT_DISPLAY")
    
    def parse(self, rigidwall_keywords):
        for i in range(len(rigidwall_keywords)):
            parameterList = []             
            parameters = self.parse_whole(rigidwall_keywords[i][0], [10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][2], [10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(rigidwall_keywords[i]) > 3:
                parameters = self.parse_whole(rigidwall_keywords[i][3], [10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getRigidWallGeometricFlatDisplay(self):
        parameterList = []
        for i in range(len(self.parameters)):
            parameters = self.parameters[i]
            curParameterList = []
            curParameterList.append("*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY")
            for j in range(len(parameters)):
                curParameterList.append(parameters[j])
            parameterList.append(curParameterList)
        return parameterList
    
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY\n")
            parameters = self.parameters[i]
            stream.write("$$    NSID    NSIDEX     BOXID     BIRTH     DEATH\n")
            formatted_elements = f"{str(parameters[0][0]):>10}{str(parameters[0][1]):>10}{str(parameters[0][2]):>10}{str(parameters[0][3]):>10}{str(parameters[0][4]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XT        YT        ZT        XH        YH        ZH      FRIC\n")
            formatted_elements = f"{str(parameters[1][0]):>10}{str(parameters[1][1]):>10}{str(parameters[1][2]):>10}{str(parameters[1][3]):>10}{str(parameters[1][4]):>10}{str(parameters[1][5]):>10}{str(parameters[1][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    XHEV      YHEV      ZHEV      LENL      LENM\n")
            formatted_elements = f"{str(parameters[2][0]):>10}{str(parameters[2][1]):>10}{str(parameters[2][2]):>10}{str(parameters[2][3]):>10}{str(parameters[2][4]):>10}\n"
            stream.write(formatted_elements)
            if len(parameters) > 4:
                stream.write("$$    XHEV      YHEV      ZHEV      LENL\n")
                formatted_elements = f"{str(parameters[3][0]):>10}{str(parameters[3][1]):>10}{str(parameters[3][2]):>10}{str(parameters[3][3]):>10}\n"
                stream.write(formatted_elements)

class RigidWallGeometricFlatDisplayID(DynaKeyword):
    def __init__(self):
        super(RigidWallGeometricFlatDisplayID,self).__init__("RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID")
    
    def parse(self, rigidwall_keywords):
        for i in range(len(rigidwall_keywords)):
            parameterList = []             
            parameters = self.parse_whole(rigidwall_keywords[i][0], [10,70])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][1], [10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][2], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][3], [10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(rigidwall_keywords[i]) > 4:
                parameters = self.parse_whole(rigidwall_keywords[i][4], [10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getRigidWallGeometricFlatDisplayID(self):
        parameterList = []
        for i in range(len(self.parameters)):
            parameters = self.parameters[i]
            curParameterList = []
            curParameterList.append("*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID")
            for j in range(len(parameters)):
                curParameterList.append(parameters[j])
            parameterList.append(curParameterList)
        return parameterList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID\n")
            parameters = self.parameters[i]
            stream.write("$$    RWID   HEADING\n")
            formatted_elements = f"{str(parameters[0][0]):>10}{str(parameters[0][1]):>70}\n"
            stream.write(formatted_elements)
            stream.write("$$    NSID    NSIDEX     BOXID     BIRTH     DEATH\n")
            formatted_elements = f"{str(parameters[1][0]):>10}{str(parameters[1][1]):>10}{str(parameters[1][2]):>10}{str(parameters[1][3]):>10}{str(parameters[1][4]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XT        YT        ZT        XH        YH        ZH      FRIC\n")
            formatted_elements = f"{str(parameters[2][0]):>10}{str(parameters[2][1]):>10}{str(parameters[2][2]):>10}{str(parameters[2][3]):>10}{str(parameters[2][4]):>10}{str(parameters[2][5]):>10}{str(parameters[2][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    XHEV      YHEV      ZHEV      LENL      LENM\n")
            formatted_elements = f"{str(parameters[3][0]):>10}{str(parameters[3][1]):>10}{str(parameters[3][2]):>10}{str(parameters[3][3]):>10}{str(parameters[3][4]):>10}\n"
            stream.write(formatted_elements)
            if len(parameters) > 4:
                stream.write("$$    XHEV      YHEV      ZHEV      LENL\n")
                formatted_elements = f"{str(parameters[4][0]):>10}{str(parameters[4][1]):>10}{str(parameters[4][2]):>10}{str(parameters[4][3]):>10}\n"
                stream.write(formatted_elements)

class RigidWallPlanar(DynaKeyword):
    def __init__(self):
        super(RigidWallPlanar,self).__init__("RIGIDWALL_PLANAR")

    def parse(self, rigidwall_keywords):
        for i in range(len(rigidwall_keywords)):            
            parameterList = [] 
            if len(rigidwall_keywords[i]) == 2:
                parameters = self.parse_whole(rigidwall_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
                parameters = self.parse_whole(rigidwall_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            elif len(rigidwall_keywords[i]) == 3:
                parameters = self.parse_whole(rigidwall_keywords[i][0], [10])
                parameterList.append(parameters)
                parameters = self.parse_whole(rigidwall_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
                parameters = self.parse_whole(rigidwall_keywords[i][2], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            if len(parameter) == 2:
                stream.write("*RIGIDWALL_PLANAR\n")
                stream.write("$$    NSID    NSIDEX     BOXID    OFFSET     BIRTH     DEATH     RWKSF\n")
                formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
                stream.write(formatted_elements)
                stream.write("$$      XT        YT        ZT        XH        YH        ZH      FRIC      WVEL\n")
                formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
                stream.write(formatted_elements)
            elif len(parameter) == 3:
                stream.write("*RIGIDWALL_PLANAR\n")
                stream.write("$$     SID\n")
                formatted_elements = f"{str(parameter[0][0]):>10}\n"
                stream.write(formatted_elements)
                stream.write("$$    NSID    NSIDEX     BOXID    OFFSET     BIRTH     DEATH     RWKSF\n")
                formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}\n"
                stream.write(formatted_elements)
                stream.write("$$      XT        YT        ZT        XH        YH        ZH      FRIC      WVEL\n")
                formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
                stream.write(formatted_elements)

class RigidWallPlanarID(DynaKeyword):
    def __init__(self):
        super(RigidWallPlanarID,self).__init__("RIGIDWALL_PLANAR_ID")

    def parse(self, rigidwall_keywords):
        for i in range(len(rigidwall_keywords)):            
            parameterList = [] 
            parameters = self.parse_whole(rigidwall_keywords[i][0], [10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]        
            stream.write("*RIGIDWALL_PLANAR_ID\n")
            stream.write("$$     SID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    NSID    NSIDEX     BOXID    OFFSET     BIRTH     DEATH     RWKSF\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XT        YT        ZT        XH        YH        ZH      FRIC      WVEL\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
            stream.write(formatted_elements)

class RigidWallPlanarMoving(DynaKeyword):
    def __init__(self):
        super(RigidWallPlanarMoving,self).__init__("RIGIDWALL_PLANAR_MOVING")
    
    def parse(self, rigidwall_keywords):
        for i in range(len(rigidwall_keywords)):
            parameterList = []
            parameters = self.parse_whole(rigidwall_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][2], [10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*RIGIDWALL_PLANAR_MOVING\n")
            stream.write("$$    NSID    NSIDEX     BOXID    OFFSET     BIRTH     DEATH     RWKSF\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XT        YT        ZT        XH        YH        ZH      FRIC      WVEL\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    MASS        V0\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}\n"
            stream.write(formatted_elements)  

class RigidWallPlanarMovingID(DynaKeyword):
    def __init__(self):
        super(RigidWallPlanarMovingID,self).__init__("RIGIDWALL_PLANAR_MOVING_ID")

    def parse(self, rigidwall_keywords):
        for i in range(len(rigidwall_keywords)):
            parameterList = []
            parameters = self.parse_whole(rigidwall_keywords[i][0], [10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(rigidwall_keywords[i][3], [10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)      

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*RIGIDWALL_PLANAR_MOVING_ID\n")
            stream.write("$$      ID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    NSID    NSIDEX     BOXID    OFFSET     BIRTH     DEATH     RWKSF\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XT        YT        ZT        XH        YH        ZH      FRIC      WVEL\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    MASS        V0\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}\n"
            stream.write(formatted_elements)           

class RigidWallPlanarMovingForces(DynaKeyword):
    def __init__(self):
        super(RigidWallPlanarMovingForces,self).__init__("RIGIDWALL_PLANAR_MOVING_FORCES")

    def parse(self, rigidwall_keywords):
        for i in range(len(rigidwall_keywords)):
            parameterList = [] 
            parameter = self.parse_whole(rigidwall_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameter)
            parameter = self.parse_whole(rigidwall_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameter)
            parameter = self.parse_whole(rigidwall_keywords[i][2], [10, 10])
            parameterList.append(parameter)
            parameter = self.parse_whole(rigidwall_keywords[i][3], [10, 10, 10, 10, 10, 10])            
            parameterList.append(parameter)
            self.parameters.append(parameterList)
    
    def getRigidWallPlanarMovingForces(self):
        rpmfList = [] 
        for i in range(len(self.parameters)):
            curRPMFList = [] 
            parameter = self.parameters[i]
            curRPMFList.append("*RIGIDWALL_PLANAR_MOVING_FORCES")
            curRPMFList.append(parameter[0])
            curRPMFList.append(parameter[1])
            curRPMFList.append(parameter[2])
            curRPMFList.append(parameter[3])
            rpmfList.append(curRPMFList)
        return rpmfList               
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*RIGIDWALL_PLANAR_MOVING_FORCES\n")
            stream.write("$$    NSID    NSIDEX     BOXID    OFFSET     BIRTH     DEATH     RWKSF\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XT        YT        ZT        XH        YH        ZH      FRIC      WVEL\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"            
            stream.write(formatted_elements)
            stream.write("$$    MASS        V0\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    SOFT      SSID        N1        N2        N3        N4\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}{str(parameter[3][2]):>10}{str(parameter[3][3]):>10}{str(parameter[3][4]):>10}{str(parameter[3][5]):>10}\n"
            stream.write(formatted_elements)

class RigidWallPlanarMovingForcesID(DynaKeyword):
    def __init__(self):
        super(RigidWallPlanarMovingForcesID,self).__init__("RIGIDWALL_PLANAR_MOVING_FORCES_ID")

    def parse(self, rigidwall_keywords):
        for i in range(len(rigidwall_keywords)):
            parameterList = [] 
            parameter = self.parse_whole(rigidwall_keywords[i][0], [10])
            parameterList.append(parameter)
            parameter = self.parse_whole(rigidwall_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameter)
            parameter = self.parse_whole(rigidwall_keywords[i][2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameter)
            parameter = self.parse_whole(rigidwall_keywords[i][3], [10, 10])
            parameterList.append(parameter)
            parameter = self.parse_whole(rigidwall_keywords[i][4], [10, 10, 10, 10, 10, 10])            
            parameterList.append(parameter)
            self.parameters.append(parameterList)
    
    def getRigidWallPlanarMovingForcesID(self):
        rpmfList = [] 
        for i in range(len(self.parameters)):
            curRPMFList = [] 
            parameter = self.parameters[i]
            curRPMFList.append("*RIGIDWALL_PLANAR_MOVING_FORCES")
            curRPMFList.append(parameter[0])
            curRPMFList.append(parameter[1])
            curRPMFList.append(parameter[2])
            curRPMFList.append(parameter[3])
            curRPMFList.append(parameter[4])
            rpmfList.append(curRPMFList)
        return rpmfList  
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*RIGIDWALL_PLANAR_MOVING_FORCES_ID\n")
            stream.write("$$      ID\n")
            formatted_elements = f"{str(parameter[0][0]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    NSID    NSIDEX     BOXID    OFFSET     BIRTH     DEATH     RWKSF\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      XT        YT        ZT        XH        YH        ZH      FRIC      WVEL\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    MASS        V0\n")
            formatted_elements = f"{str(parameter[3][0]):>10}{str(parameter[3][1]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$    SOFT      SSID        N1        N2        N3        N4\n")
            formatted_elements = f"{str(parameter[4][0]):>10}{str(parameter[4][1]):>10}{str(parameter[4][2]):>10}{str(parameter[4][3]):>10}{str(parameter[4][4]):>10}{str(parameter[4][5]):>10}\n"
            stream.write(formatted_elements)

class SectionBeam(DynaKeyword):
    def __init__(self):
        super(SectionBeam,self).__init__("SECTION_BEAM")

    def parse(self, section_beam_keywords):
        for i in range(len(section_beam_keywords)):
            parameterList = []  
            parameters = self.parse_whole(section_beam_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(section_beam_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddSectionBeam(self, secid, elform, shrf, qririd, cst, scoor, nsm, naupd, options):
        parameterList = []
        parameters = [secid, elform, shrf, qririd, cst, scoor, nsm, naupd]
        parameterList.append(parameters)
        parameters = []
        for option in options:
            parameters.append(option)
        parameterList.append(parameters)
        self.parameters.append(parameterList)        
        
    def getSectionBeams(self):
        sectionList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSectionList = []
            curSectionList.append("*SECTION_BEAM")
            curSectionList.append(parameter[0])
            curSectionList.append(parameter[1])
            sectionList.append(curSectionList)
        return sectionList            
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_BEAM\n")
            stream.write("$$   SECID    ELFORM      SHRF   QR/IRID       CST     SCOOR       NSM     NAUPD\n")                
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     TS1       TS2       TT1       TT2     NSLOC     NTLOC\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)

class SectionBeamTitle(DynaKeyword):
    def __init__(self):
        super(SectionBeamTitle,self).__init__("SECTION_BEAM_TITLE")

    def parse(self, section_beam_keywords):
        for i in range(len(section_beam_keywords)):
            parameterList = []
            parameters = self.parse_whole(section_beam_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(section_beam_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(section_beam_keywords[i][2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddSectionBeamTitle(self, name, secid, elform, shrf, qririd, cst, scoor, nsm, naupd, options):
        parameterList = []
        parameters = [name]
        parameterList.append(parameters)
        parameters = [secid, elform, shrf, qririd, cst, scoor, nsm, naupd]
        parameterList.append(parameters)
        parameters = []
        for option in options:
            parameters.append(option)
        parameterList.append(parameters)
        self.parameters.append(parameterList)
    
    def getSectionBeams(self):
        sectionList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSectionList = []
            curSectionList.append("*SECTION_BEAM_TITLE")
            curSectionList.append(parameter[0])
            curSectionList.append(parameter[1])
            sectionList.append(curSectionList)
        return sectionList
                
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_BEAM_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$   SECID    ELFORM      SHRF   QR/IRID       CST     SCOOR       NSM     NAUPD\n")                
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$     TS1       TS2       TT1       TT2     NSLOC     NTLOC\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
            stream.write(formatted_elements)

class SectionShell(DynaKeyword):
    def __init__(self):
        super(SectionShell,self).__init__("SECTION_SHELL")

    def parse(self, section_shell_keywords):
        for i in range(len(section_shell_keywords)):
            parameterList = []
            #parameters = section_shell_keywords[i][0].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(section_shell_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            #parameters = section_shell_keywords[i][1].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(section_shell_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddSectionShellTitle(self, name, secid, elform, shrf, nip, propt, qririd, icomp, setyp, t1, t2, t3, t4, nloc, marea, idof, edgset):
        parameterList = []
        parameters = [secid, elform, shrf, nip, propt, qririd, icomp, setyp]
        parameterList.append(parameters)
        parameters = [t1, t2, t3, t4, nloc, marea, idof, edgset]
        parameterList.append(parameters)
        self.parameters.append(parameterList)        
        
    def SECID(self,ith):
        return self.parameters[ith][0][0]
    
    def ELFORM(self,ith):
        return self.parameters[ith][0][1]
    
    def SHRF(self,ith):
        return self.parameters[ith][0][2]
    
    def NIP(self,ith):
        return self.parameters[ith][0][3]
    
    def PROPT(self,ith):
        return self.parameters[ith][0][4]
    
    def QRIRID(self,ith):
        return self.parameters[ith][0][5]
    
    def ICOMP(self,ith):
        return self.parameters[ith][0][6]
    
    def SETYP(self,ith):
        return self.parameters[ith][0][7]
    
    def T1(self,ith):
        return self.parameters[ith][1][0]
    
    def T2(self,ith):
        return self.parameters[ith][1][1]
    
    def T3(self,ith):
        return self.parameters[ith][1][2]
    
    def T4(self,ith):
        return self.parameters[ith][1][3]
    
    def NLOC(self,ith):
        return self.parameters[ith][1][4]
    
    def MAREA(self,ith):
        return self.parameters[ith][1][5]
    
    def IDOF(self,ith):
        return self.parameters[ith][1][6]
    
    def EDGSET(self,ith):
        return self.parameters[ith][1][7]

    def getSectionShells(self):
        sectionList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSection = []
            curSection.append("*SECTION_SHELL")
            curSection.append(parameter[0])
            curSection.append(parameter[1])
            sectionList.append(curSection)
        return sectionList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_SHELL\n")
            stream.write("$$   SECID    ELFORM      SHRF       NIP     PROPT    QRIRID     ICOMP     SETYP\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      T1        T2        T3        T4      NLOC     MAREA      IDOF    EDGSET\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)

class SectionShellTitle(DynaKeyword):
    def __init__(self):
        super(SectionShellTitle,self).__init__("SECTION_SHELL_TITLE")

    def parse(self, section_shell_keywords):
        for i in range(len(section_shell_keywords)):
            parameterList = []
            #parameters = section_shell_keywords[i][0].parse_whole([80])
            parameters = self.parse_whole(section_shell_keywords[i][0], [80])
            parameterList.append(parameters)
            #parameters = section_shell_keywords[i][1].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(section_shell_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            #parameters = section_shell_keywords[i][2].parse_whole([10, 10, 10, 10, 10, 10, 10, 10])
            parameters = self.parse_whole(section_shell_keywords[i][2], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddSectionShellTitle(self, name, secid, elform, shrf, nip, propt, qririd, icomp, setyp, t1, t2, t3, t4, nloc, marea, idof, edgset):
        parameterList = []
        parameters = [name]
        parameterList.append(parameters)
        parameters = [secid, elform, shrf, nip, propt, qririd, icomp, setyp]
        parameterList.append(parameters)
        parameters = [t1, t2, t3, t4, nloc, marea, idof, edgset]
        parameterList.append(parameters)
        self.parameters.append(parameterList)        
    
    def NAME(self, ith):
        return self.parameters[ith][0][0]

    def SECID(self,ith):
        return self.parameters[ith][1][0]
    
    def ELFORM(self,ith):
        return self.parameters[ith][1][1]
    
    def SHRF(self,ith):
        return self.parameters[ith][1][2]
    
    def NIP(self,ith):
        return self.parameters[ith][1][3]
    
    def PROPT(self,ith):
        return self.parameters[ith][1][4]
    
    def QRIRID(self,ith):
        return self.parameters[ith][1][5]
    
    def ICOMP(self,ith):
        return self.parameters[ith][1][6]
    
    def SETYP(self,ith):
        return self.parameters[ith][1][7]
    
    def T1(self,ith):
        return self.parameters[ith][2][0]
    
    def T2(self,ith):
        return self.parameters[ith][2][1]
    
    def T3(self,ith):
        return self.parameters[ith][2][2]
    
    def T4(self,ith):
        return self.parameters[ith][2][3]
    
    def NLOC(self,ith):
        return self.parameters[ith][2][4]
    
    def MAREA(self,ith):
        return self.parameters[ith][2][5]
    
    def IDOF(self,ith):
        return self.parameters[ith][2][6]
    
    def EDGSET(self,ith):
        return self.parameters[ith][2][7]
    
    def getSectionShells(self):
        sectionList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSection = []
            curSection.append("*SECTION_SHELL_TITLE")
            curSection.append(parameter[0]) 
            curSection.append(parameter[1]) 
            curSection.append(parameter[2])
            sectionList.append(curSection)
        return sectionList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_SHELL_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$   SECID    ELFORM      SHRF       NIP     PROPT    QRIRID     ICOMP     SETYP\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      T1        T2        T3        T4      NLOC     MAREA      IDOF    EDGSET\n")
            formatted_elements = f"{str(parameter[2][0]):>10}{str(parameter[2][1]):>10}{str(parameter[2][2]):>10}{str(parameter[2][3]):>10}{str(parameter[2][4]):>10}{str(parameter[2][5]):>10}{str(parameter[2][6]):>10}{str(parameter[2][7]):>10}\n"
            stream.write(formatted_elements)

class SectionSolid(DynaKeyword):
    def __init__(self):
        super(SectionSolid,self).__init__("SECTION_SOLID")

    def parse(self, section_solid_keywords):
        for i in range(len(section_solid_keywords)):
            parameterList = []
            parameters = self.parse_whole(section_solid_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddSectionSolid(self, secid, elform, aet, cohoff, gaskett):
        parameterList = []     
        parameters = [secid, elform, aet, "", "", "", cohoff, gaskett]
        parameterList.append(parameters)
        self.parameters.append(parameterList)
    
    def SECID(self,ith):
        return self.parameters[ith][0][0]
    
    def ELFORM(self,ith):
        return self.parameters[ith][0][1]
    
    def AET(self,ith):
        return self.parameters[ith][0][2]

    def COHOFF(self,ith):
        return self.parameters[ith][0][6]
    
    def GASKETT(self,ith):
        return self.parameters[ith][0][7]
    
    def getSectionSolids(self):
        sectionList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSection = []
            curSection.append("*SECTION_SOLID")
            curSection.append(parameter[0])
            sectionList.append(curSection)
        return sectionList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_SOLID\n")
            stream.write("$$   SECID    ELFORM       AET    COHOFF   GASKETT\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)

class SectionSolidTitle(DynaKeyword):
    def __init__(self):
        super(SectionSolidTitle,self).__init__("SECTION_SOLID_TITLE")
    
    def parse(self, section_solid_keywords):
        for i in range(len(section_solid_keywords)):
            parameterList = []
            parameters = self.parse_whole(section_solid_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(section_solid_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)

    def AddSectionSolidTitle(self, name, secid, elform, aet, cohoff, gaskett):
        parameterList = []
        parameters = [name]
        parameterList.append(parameters)
        parameters = [secid, elform, aet, "", "", "", cohoff, gaskett]
        parameterList.append(parameters)
        self.parameters.append(parameterList)        
    
    def NAME(self,ith):
        return self.parameters[ith][0][0]
    
    def SECID(self,ith):
        return self.parameters[ith][1][0]
    
    def ELFORM(self,ith):
        return self.parameters[ith][1][1]
    
    def AET(self,ith):
        return self.parameters[ith][1][2]
    
    def COHOFF(self,ith):
        return self.parameters[ith][1][6]
    
    def GASKETT(self,ith):
        return self.parameters[ith][1][7]

    def getSectionSolids(self):
        sectionList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSection = []
            curSection.append("*SECTION_SOLID_TITLE")
            curSection.append(parameter[0])
            curSection.append(parameter[1])            
            sectionList.append(curSection)
        return sectionList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_SOLID_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$   SECID    ELFORM       AET    COHOFF   GASKETT\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)

class SectionSolidPeri(DynaKeyword):
    def __init__(self):
        super(SectionSolidPeri,self).__init__("SECTION_SOLID_PERI")
    
    def parse(self, section_solid_keywords):
        for i in range(len(section_solid_keywords)):
            parameterList = []
            parameters = self.parse_whole(section_solid_keywords[i][0], [10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(section_solid_keywords[i][1], [10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddSectionSolid(self, secid, elform, dr, ptype):
        parameterList = []
        parameters = [secid, elform]
        parameterList.append(parameters)
        parameters = [dr, ptype]
        parameterList.append(parameters)
        self.parameters.append(parameterList)
    
    def SECID(self,ith):
        return self.parameters[ith][0][0]

    def ELFORM(self,ith):
        return self.parameters[ith][0][1]
    
    def DR(self,ith):
        return self.parameters[ith][1][0]
    
    def PTYPE(self,ith):
        return self.parameters[ith][1][1]
    
    def getSectionSolidPeris(self):
        sectionList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSection = []
            curSection.append("*SECTION_SOLID_PERI")
            curSection.append(parameter[0])
            curSection.append(parameter[1])
            sectionList.append(curSection)
        return sectionList

    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_SOLID_PERI\n")            
            stream.write("$$   SECID    ELFORM\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}\n"
            stream.write(formatted_elements)
            stream.write("$$      DR     PTYPE\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}\n"
            stream.write(formatted_elements)

class SectionSolidPeriTitle(DynaKeyword):
    def __init__(self):
        super(SectionSolidPeriTitle,self).__init__("SECTION_SOLID_PERI_TITLE")
    
    def parse(self, section_solid_keywords):
        for i in range(len(section_solid_keywords)):
            parameterList = []
            parameters = self.parse_whole(section_solid_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(section_solid_keywords[i][1], [10, 10])
            parameterList.append(parameters)
            parameters = self.parse_whole(section_solid_keywords[i][2], [10, 10])
            parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddSectionSolid(self, name, secid, elform, dr, ptype):
        parameterList = []
        parameters = [name]
        parameterList.append(parameters)
        parameters = [secid, elform]
        parameterList.append(parameters)
        parameters = [dr, ptype]
        parameterList.append(parameters)
        self.parameters.append(parameterList)
    
    def NAME(self,ith):
        return self.parameters[ith][0][0]
    
    def SECID(self,ith):
        return self.parameters[ith][1][0]
    
    def ELFORM(self,ith):
        return self.parameters[ith][1][1]
    
    def DR(self,ith):
        return self.parameters[ith][2][0]
    
    def PTYPE(self,ith):
        return self.parameters[ith][2][1]
    
    def getSectionSolidPeris(self):
        sectionList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSection = []
            curSection.append("*SECTION_SOLID_PERI_TITLE")
            curSection.append(parameter[0])
            curSection.append(parameter[1])
            curSection.append(parameter[2])
            sectionList.append(curSection)
        return sectionList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_SOLID_PERI_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$   SECID   ELFORM\n")
            stream.write("{secid:>10}{elform:>10}\n".format(secid=parameter[1][0], elform=parameter[1][1]))
            stream.write("$$      DR     PTYPE\n")
            stream.write("{dr:>10}{ptype:>10}\n".format(dr=parameter[2][0], ptype=parameter[2][1]))

class SectionTShell(DynaKeyword):
    def __init__(self):
        super(SectionTShell,self).__init__("SECTION_TSHELL")
    
    def parse(self, section_tshell_keywords):
        for i in range(len(section_tshell_keywords)):
            parameterList = [] 
            parameters = self.parse_whole(section_tshell_keywords[i][0], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(parameters) >= 7: 
                if parameters[6] == "1":
                    for j in range(1,len(section_tshell_keywords[i])):
                        parameters = self.parse_whole(section_tshell_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                        parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def AddSectionTShell(self, secid, elform, shrf, nip, propt, qr, icomp, tshear, bList):
        parameterList = []
        parameters = [secid, elform, shrf, nip, propt, qr, icomp, tshear]
        parameterList.append(parameters)
        # split blist by 8 elements
        bList = [bList[i:i + 8] for i in range(0, len(bList), 8)]
        
        for b in bList:
            parameters = b
            parameterList.append(parameters)
        self.parameters.append(parameterList)
        
    def getSectionTShells(self):
        sectionList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSection = []
            curSection.append("*SECTION_TSHELL")
            curSection.append(parameter[0])
            for j in range(1,len(parameter)):
                curSection.append(parameter[j])
            sectionList.append(curSection)
        return sectionList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_TSHELL\n")
            stream.write("$$   SECID    ELFORM      SHRF       NIP     PROPT        QR     ICOMP    TSHEAR\n")
            formatted_elements = f"{str(parameter[0][0]):>10}{str(parameter[0][1]):>10}{str(parameter[0][2]):>10}{str(parameter[0][3]):>10}{str(parameter[0][4]):>10}{str(parameter[0][5]):>10}{str(parameter[0][6]):>10}{str(parameter[0][7]):>10}\n"
            stream.write(formatted_elements)
            for j in range(1,len(parameter)):
                if j == 1:
                    stream.write("$$      Bi      Bi+1      Bi+2      Bi+3      Bi+4      Bi+5      Bi+6      Bi+7\n")
            
                formatted_elements = ""
                for k in range(0,len(parameter[j])):
                    formatted_elements += f"{str(parameter[j][k]):>10}"
                stream.write(formatted_elements)
                stream.write("\n")
                
class SectionTShellTitle(DynaKeyword):
    def __init__(self):
        super(SectionTShellTitle,self).__init__("SECTION_TSHELL_TITLE")
        
    def parse(self, section_tshell_keywords):
        for i in range(len(section_tshell_keywords)):
            parameterList = []
            parameters = self.parse_whole(section_tshell_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(section_tshell_keywords[i][1], [10, 10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            if len(parameters) >= 7:
                if parameters[6] == "1":
                    for j in range(2,len(section_tshell_keywords[i])):
                        parameters = self.parse_whole(section_tshell_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                        parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def AddSectionTShellTitle(self, name, secid, elform, shrf, nip, propt, qr, icomp, tshear, bList):
        parameterList = []
        parameters = [name]
        parameterList.append(parameters)
        parameters = [secid, elform, shrf, nip, propt, qr, icomp, tshear]
        parameterList.append(parameters)
        # split blist by 8 elements
        bList = [bList[i:i + 8] for i in range(0, len(bList), 8)]

        for b in bList:
            parameters = b
            parameterList.append(parameters)
        self.parameters.append(parameterList)
        
    def getSectionTShells(self):
        sectionList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSection = []
            curSection.append("*SECTION_TSHELL_TITLE")
            curSection.append(parameter[0])
            curSection.append(parameter[1])
            for j in range(2,len(parameter)):
                curSection.append(parameter[j])
            sectionList.append(curSection)
        return sectionList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            stream.write("*SECTION_TSHELL_TITLE\n")
            stream.write("{name}\n".format(name=parameter[0][0]))
            stream.write("$$   SECID    ELFORM      SHRF       NIP     PROPT        QR     ICOMP    TSHEAR\n")
            formatted_elements = f"{str(parameter[1][0]):>10}{str(parameter[1][1]):>10}{str(parameter[1][2]):>10}{str(parameter[1][3]):>10}{str(parameter[1][4]):>10}{str(parameter[1][5]):>10}{str(parameter[1][6]):>10}{str(parameter[1][7]):>10}\n"
            stream.write(formatted_elements)
            for j in range(2,len(parameter)):
                if j == 2:
                    stream.write("$$      Bi      Bi+1      Bi+2      Bi+3      Bi+4      Bi+5      Bi+6      Bi+7\n")
                
                formatted_elements = ""
                for k in range(0,len(parameter[j])):
                    formatted_elements += f"{str(parameter[j][k]):>10}"
                stream.write(formatted_elements)
                stream.write("\n")
        
class SetNodeAdd(DynaKeyword):
    def __init__(self):
        super(SetNodeAdd,self).__init__("SET_NODE_ADD")
    
    def parse(self, set_node_add_keywords):
        for i in range(len(set_node_add_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_node_add_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_node_add_keywords[i])):
                parameters = self.parse_whole(set_node_add_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_NODE_ADD\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                
                if j == 0:
                    stream.write("$#     SID       DA1       DA2       DA3       DA4    SOLVER       ITS\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}{str(parameter[j][6]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    stream.write("$    NSID1     NSID2     NSID3     NSID4     NSID5     NSID6     NSID7     NSID8\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")                            

class SetNodeGeneral(DynaKeyword):
    def __init__(self):
        super(SetNodeGeneral,self).__init__("SET_NODE_GENERAL")
        
    def parse(self, set_node_general_keywords):
        for i in range(len(set_node_general_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_node_general_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_node_general_keywords[i])):
                parameters = self.parse_whole(set_node_general_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_NODE_GENERAL\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                
                if j == 0:
                    stream.write("$#     SID       DA1       DA2       DA3       DA4    SOLVER       ITS\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}{str(parameter[j][6]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    stream.write("$   OPTION        E1        E2        E3        E4        E5        E6        E7        E8\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetNodeList(DynaKeyword):
    def __init__(self):
        super(SetNodeList,self).__init__("SET_NODE_LIST")
    
    def parse(self, set_node_list_keywords):
        for i in range(len(set_node_list_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_node_list_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_node_list_keywords[i])):
                parameters = self.parse_whole(set_node_list_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getSetNodeList(self):
        setnodeList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSetNode = [] 
            curSetNode.append("*SET_NODE_LIST")
            setNodeOption = [] 
            for j in range(len(parameter[0])):
                setNodeOption.append(parameter[0][j].strip())
            curSetNode.append(setNodeOption)
            nodeidList = []
            for j in range(1,len(parameter)):                
                for k in range(0,len(parameter[j])):
                    nodeidList.append(parameter[j][k])
            curSetNode.append(nodeidList)                    
            setnodeList.append(curSetNode)
        return setnodeList
            
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_NODE_LIST\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):                    
                if j == 0:
                    stream.write("$#     SID       DA1       DA2       DA3       DA4    SOLVER       ITS\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}{str(parameter[j][6]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    if j == 1:
                        stream.write("$    NSID1     NSID2     NSID3     NSID4     NSID5     NSID6     NSID7     NSID8\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetNodeListTitle(DynaKeyword):
    def __init__(self):
        super(SetNodeListTitle,self).__init__("SET_NODE_LIST_TITLE")
    
    def AddSetNodeList(self, title, sid, da1, da2, da3, da4, solver, its, nidList):
        parameterList = [] 
        parameters = [title]
        parameterList.append(parameters)
        parameters = [sid, da1, da2, da3, da4, solver, its]
        parameterList.append(parameters)        
        for i in range(0,len(nidList),8):
            parameters = []
            for j in range(i,i+8):
                if j < len(nidList):
                    parameters.append(nidList[j])
            
            parameterList.append(parameters)
        self.parameters.append(parameterList)
    
    def getSetNodeList(self):
        setnodeList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSetNode = [] 
            curSetNode.append("*SET_NODE_LIST_TITLE")
            titleList = [] 
            titleList.append(parameter[0][0].strip())
            curSetNode.append(titleList)
            
            setNodeOption = [] 
            for j in range(len(parameter[1])):
                setNodeOption.append(parameter[1][j].strip())
            curSetNode.append(setNodeOption)
            nodeidList = []
            for j in range(2,len(parameter)):                
                for k in range(0,len(parameter[j])):
                    nodeidList.append(parameter[j][k])
            curSetNode.append(nodeidList)                    
            setnodeList.append(curSetNode)
        return setnodeList

    def parse(self, set_node_list_keywords):
        for i in range(len(set_node_list_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_node_list_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(set_node_list_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(2,len(set_node_list_keywords[i])):
                parameters = self.parse_whole(set_node_list_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getSetNodeListTitle(self):
        setnodeList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSetNode = [] 
            curSetNode.append("*SET_NODE_LIST_TITLE")
            name = parameter[0][0].strip()
            curSetNode.append(name)
            setNodeOption = []             
            for j in range(len(parameter[1])):
                setNodeOption.append(parameter[1][j].strip())
            curSetNode.append(setNodeOption)
            nodeidList = []
            for j in range(2,len(parameter)):                
                for k in range(0,len(parameter[j])):
                    nodeidList.append(parameter[j][k])
            curSetNode.append(nodeidList)                    
            setnodeList.append(curSetNode)
        return setnodeList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_NODE_LIST_TITLE\n")
            parameter = self.parameters[i]
            stream.write("{name}\n".format(name=parameter[0][0]))
            for j in range(1,len(self.parameters[i])):                    
                if j == 1:
                    stream.write("$#     SID       DA1       DA2       DA3       DA4    SOLVER       ITS\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}{str(parameter[j][6]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    if j == 2:
                        stream.write("$    NSID1     NSID2     NSID3     NSID4     NSID5     NSID6     NSID7     NSID8\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetNodeListGenerate(DynaKeyword):
    def __init__(self):
        super(SetNodeListGenerate,self).__init__("SET_NODE_LIST_GENERATE")

    def parse(self, set_node_list_generate_keywords):
        for i in range(len(set_node_list_generate_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_node_list_generate_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_node_list_generate_keywords[i])):
                parameters = self.parse_whole(set_node_list_generate_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getSetNodeList(self):
        setnodeList = [] 
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSetNode = []
            curSetNode.append("*SET_NODE_LIST_GENERATE")
            for j in range(len(parameter)):
                curSetNode.append(parameter[j])
            setnodeList.append(curSetNode)
        return setnodeList

    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_NODE_LIST_GENERATE\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):                
                if j == 0:
                    stream.write("$#     SID       DA1       DA2       DA3       DA4    SOLVER       ITS\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}{str(parameter[j][6]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    stream.write("$    B1BEG     B1END     B2BEG     B2END     B3BEG     B3END     B4BEG     B4END\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetPart(DynaKeyword):
    def __init__(self):
        super(SetPart,self).__init__("SET_PART")

    def parse(self, set_part_keywords):
        for i in range(len(set_part_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_part_keywords[i][0], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_part_keywords[i])):
                parameters = self.parse_whole(set_part_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getSetPart(self):
        setPartList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSetPart = []
            curSetPart.append("*SET_PART")
            for j in range(len(parameter)):
                curSetPart.append(parameter[j])
            setPartList.append(curSetPart)
        return setPartList
            
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_PART\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                
                if j == 0:
                    stream.write("$$     SID       DA1       DA2       DA3       DA4    SOLVER\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    stream.write("$$    PID1      PID2      PID3      PID4      PID5      PID6      PID7      PID8\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetPartList(DynaKeyword):
    def __init__(self):
        super(SetPartList,self).__init__("SET_PART_LIST")
    
    def parse(self, set_part_list_keywords):
        for i in range(len(set_part_list_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_part_list_keywords[i][0], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_part_list_keywords[i])):
                parameters = self.parse_whole(set_part_list_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getSetPartList(self):
        setPartList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSetPart = []
            curSetPart.append("*SET_PART_LIST")
            for j in range(len(parameter)):
                curSetPart.append(parameter[j])
            setPartList.append(curSetPart)
        return setPartList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_PART_LIST\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):                    
                if j == 0:
                    stream.write("$$     SID       DA1       DA2       DA3       DA4    SOLVER\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    if j == 1:
                        stream.write("$$    PID1      PID2      PID3      PID4      PID5      PID6      PID7      PID8\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetPartListTitle(DynaKeyword):
    def __init__(self):
        super(SetPartListTitle,self).__init__("SET_PART_LIST_TITLE")
    
    def parse(self, set_part_list_title_keywords):
        for i in range(len(set_part_list_title_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_part_list_title_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(set_part_list_title_keywords[i][1], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(2,len(set_part_list_title_keywords[i])):
                parameters = self.parse_whole(set_part_list_title_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getsSetPartListTitle(self):
        setPartList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSetPart = []
            curSetPart.append("*SET_PART_LIST_TITLE")
            for j in range(len(parameter)):
                curSetPart.append(parameter[j])
            setPartList.append(curSetPart)
        return setPartList
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_PART_LIST_TITLE\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):                    
                if j == 0:
                    stream.write("$$                                                                              ")
                    result = f"{str(parameter[j][0]):>80}"
                    stream.write(result)
                    stream.write("\n")
                elif j == 1:
                    stream.write("$$     SID       DA1       DA2       DA3       DA4    SOLVER\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    if j == 2:
                        stream.write("$$    PID1      PID2      PID3      PID4      PID5      PID6      PID7      PID8\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetPartListGenerate(DynaKeyword):
    def __init__(self):
        super(SetPartListGenerate,self).__init__("SET_PART_LIST_GENERATE")

    def parse(self, set_part_list_generate_keywords):
        for i in range(len(set_part_list_generate_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_part_list_generate_keywords[i][0], [10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_part_list_generate_keywords[i])):
                parameters = self.parse_whole(set_part_list_generate_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
        
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_PART_LIST_GENERATE\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                
                if j == 0:
                    stream.write("$#     SID       DA1       DA2       DA3       DA4    SOLVER\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    stream.write("$    B1BEG     B1END     B2BEG     B2END     B3BEG     B3END     B4BEG     B4END\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetSegment(DynaKeyword):
    def __init__(self):
        super(SetSegment,self).__init__("SET_SEGMENT")
    
    def parse(self, set_segment_keywords):
        for i in range(len(set_segment_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_segment_keywords[i][0], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_segment_keywords[i])):
                parameters = self.parse_whole(set_segment_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getSetSegmentList(self):
        setSegmentList = []
        for i in range(len(self.parameters)):
            parameter = [] 
            parameter.append("*SET_SEGMENT")
            for j in range(len(self.parameters[i])):
                parameter.append(self.parameters[i][j])
            setSegmentList.append(parameter)
        return setSegmentList                    
    
    def AddSegment(self, sid, da1, da2, da3, da4, solver, its, nidList,fList):
        parameterList = []
        parameters = [sid, da1, da2, da3, da4, solver, its]
        parameterList.append(parameters)
        for i in range(0,len(nidList),4):
            parameters = []
            for j in range(i,i+4):
                if j < len(nidList):
                    parameters.append(nidList[j])
                else:
                    parameters.append("")
            for j in range(i, i+4):
                if j < len(fList):
                    parameters.append(fList[j])
                else:
                    parameters.append("")
            parameterList.append(parameters)
        self.parameters.append(parameterList)




    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_SEGMENT\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                
                if j == 0:
                    stream.write("$$     SID       DA1       DA2       DA3       DA4    SOLVER       ITS\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}{str(parameter[j][6]):<10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    if j == 1:
                        stream.write("$$      N1        N2        N3        N4        A1        A2        A3        A4\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetSegmentTitle(DynaKeyword):
    def __init__(self):
        super(SetSegmentTitle,self).__init__("SET_SEGMENT_TITLE")
    
    def parse(self, set_segment_keywords):
        for i in range(len(set_segment_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_segment_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(set_segment_keywords[i][1], [10, 10, 10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(2,len(set_segment_keywords[i])):
                parameters = self.parse_whole(set_segment_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getSetSegmentTitleList(self):
        setSegmentList = []
        for i in range(len(self.parameters)):
            parameter = [] 
            parameter.append("*SET_SEGMENT_TITLE")
            for j in range(len(self.parameters[i])):
                parameter.append(self.parameters[i][j])
            setSegmentList.append(parameter)
        return setSegmentList  
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_SEGMENT_TITLE\n")
            parameter = self.parameters[i]
            stream.write("{name}\n".format(name=parameter[0][0]))
            for j in range(1,len(self.parameters[i])):
                if j == 1:
                    stream.write("$$     SID       DA1       DA2       DA3       DA4    SOLVER       ITS\n")
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}{str(parameter[j][5]):<10}{str(parameter[j][6]):<10}"
                    stream.write(result)
                    stream.write("\n")
                else:
                    if j == 2:
                        stream.write("$$      N1        N2        N3        N4        A1        A2        A3        A4\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)
                    stream.write("\n")

class SetShell(DynaKeyword):
    def __init__(self):
        super(SetShell,self).__init__("SET_SHELL")
    
    def parse(self, set_shell_keywords):
        for i in range(len(set_shell_keywords)):
            parameterList = []
                        
            parameters = self.parse_whole(set_shell_keywords[i][0], [10, 10, 10, 10, 10])
            for j in range(1,len(set_shell_keywords[i])):
                parameters = self.parse_whole(set_shell_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getShellList(self):
        shellList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curShell = []
            curShell.append("*SET_SHELL")
            for j in range(len(parameter)):
                curShell.append(parameter[j])
            shellList.append(curShell)
        return shellList

    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_SHELL\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                if j == 0:
                    stream.write("$$     SID       DA1       DA2       DA3       DA4\n")
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}"
                    stream.write(result)
                    stream.write("\n")
                else:
                    stream.write("$$    EIDi    EIDi+1    EIDi+2    EIDi+3    EIDi+4    EIDi+5    EIDi+6    EIDi+7\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)
                    stream.write("\n")

class SetShellTitle(DynaKeyword):
    def __init__(self):
        super(SetShellTitle,self).__init__("SET_SHELL_TITLE")
    
    def parse(self, set_shell_keywords):
        for i in range(len(set_shell_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_shell_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(set_shell_keywords[i][1], [10, 10, 10, 10, 10])
            for j in range(2,len(set_shell_keywords[i])):
                parameters = self.parse_whole(set_shell_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getShellTitleList(self):
        shellList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curShell = []
            curShell.append("*SET_SHELL_TITLE")
            for j in range(len(parameter)):
                curShell.append(parameter[j])
            shellList.append(curShell)
        return shellList

    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_SHELL_TITLE\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                if j == 0:                    
                    stream.write("$$                                                                          Name")
                    result = f"{str(parameter[j][0]):>80}"
                    stream.write(result)
                    stream.write("\n")
                elif j == 1:
                    stream.write("$$     SID       DA1       DA2       DA3       DA4\n")
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}"
                    stream.write(result)
                    stream.write("\n")
                else:
                    stream.write("$$    EIDi    EIDi+1    EIDi+2    EIDi+3    EIDi+4    EIDi+5    EIDi+6    EIDi+7\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)
                    stream.write("\n")

class SetShellList(DynaKeyword):
    def __init__(self):
        super(SetShellList,self).__init__("SET_SHELL_LIST")
    
    def parse(self, set_shell_list_keywords):
        for i in range(len(set_shell_list_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_shell_list_keywords[i][0], [10, 10, 10, 10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_shell_list_keywords[i])):
                parameters = self.parse_whole(set_shell_list_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
            
    def getShellListList(self):
        shellList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curShell = []
            curShell.append("*SET_SHELL_LIST")
            for j in range(len(parameter)):
                curShell.append(parameter[j])
            shellList.append(curShell)
        return shellList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_SHELL_LIST\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):                
                if j == 0:
                    stream.write("$$     SID       DA1       DA2       DA3       DA4\n")      
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}{str(parameter[j][2]):>10}{str(parameter[j][3]):>10}{str(parameter[j][4]):>10}"
                    stream.write(result)
                    stream.write("\n")                    
                else:
                    stream.write("$$    EID1      EID2      EID3      EID4      EID5      EID6      EID7      EID8\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)                    
                    stream.write("\n")

class SetTShell(DynaKeyword):
    def __init__(self):
        super(SetTShell,self).__init__("SET_TSHELL")
    
    def parse(self, set_tshell_keywords):
        for i in range(len(set_tshell_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_tshell_keywords[i][0], [10])
            parameterList.append(parameters)
            for j in range(1,len(set_tshell_keywords[i])):
                parameters = self.parse_whole(set_tshell_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)
    
    def getTShellListList(self):
        tshellList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curTShell = []
            curTShell.append("*SET_TSHELL")
            for j in range(len(parameter)):
                curTShell.append(parameter[j])
            tshellList.append(curTShell)
        return tshellList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_TSHELL\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                if j == 0:
                    stream.write("$$     SID\n")
                    result = f"{str(parameter[j][0]):>10}"
                    stream.write(result)
                    stream.write("\n")
                    stream.write("$$    EID1      EID2      EID3      EID4      EID5      EID6      EID7      EID8\n")
                else:
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)
                    stream.write("\n")

class SetSolid(DynaKeyword):
    def __init__(self):
        super(SetSolid,self).__init__("SET_SOLID")
        
    def parse(self, set_solid_keywords):
        for i in range(len(set_solid_keywords)):
            parameterList = []            
            parameters = self.parse_whole(set_solid_keywords[i][0], [10, 10])
            parameterList.append(parameters)
            for j in range(1,len(set_solid_keywords[i])):
                parameters = self.parse_whole(set_solid_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getSolidList(self):
        solidList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSolid = []
            curSolid.append("*SET_SOLID")
            for j in range(len(parameter)):
                curSolid.append(parameter[j])
            solidList.append(curSolid)
        return solidList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_SOLID\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                if j == 0:
                    stream.write("$$     SID    SOLVER\n")
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}"
                    stream.write(result)
                    stream.write("\n")
                else:
                    stream.write("$$    EIDi    EIDi+1    EIDi+2    EIDi+3    EIDi+4    EIDi+5    EIDi+6    EIDi+7\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)
                    stream.write("\n")
                    
class SetSolidTitle(DynaKeyword):
    def __init__(self):
        super(SetSolidTitle,self).__init__("SET_SOLID_TITLE")
        
    def parse(self, set_solid_keywords):
        for i in range(len(set_solid_keywords)):
            parameterList = []
            parameters = self.parse_whole(set_solid_keywords[i][0], [80])
            parameterList.append(parameters)
            parameters = self.parse_whole(set_solid_keywords[i][1], [10, 10])
            parameterList.append(parameters)
            for j in range(2,len(set_solid_keywords[i])):
                parameters = self.parse_whole(set_solid_keywords[i][j], [10, 10, 10, 10, 10, 10, 10, 10])
                parameterList.append(parameters)
            self.parameters.append(parameterList)

    def getSolidTitleList(self):
        solidList = []
        for i in range(len(self.parameters)):
            parameter = self.parameters[i]
            curSolid = []
            curSolid.append("*SET_SOLID_TITLE")
            for j in range(len(parameter)):
                curSolid.append(parameter[j])
            solidList.append(curSolid)
        return solidList
    
    def write(self, stream):
        for i in range(len(self.parameters)):
            stream.write("*SET_SOLID_TITLE\n")
            parameter = self.parameters[i]
            for j in range(len(self.parameters[i])):
                if j == 0:                    
                    stream.write("$$                                                                          Name")
                    result = f"{str(parameter[j][0]):>80}"
                    stream.write(result)
                    stream.write("\n")
                elif j == 1:
                    stream.write("$$     SID    SOLVER\n")
                    result = f"{str(parameter[j][0]):>10}{str(parameter[j][1]):>10}"
                    stream.write(result)
                    stream.write("\n")
                else:
                    stream.write("$$    EIDi    EIDi+1    EIDi+2    EIDi+3    EIDi+4    EIDi+5    EIDi+6    EIDi+7\n")
                    for k in range(0,len(parameter[j])):
                        formatted_elements = f"{str(parameter[j][k]):>10}"
                        stream.write(formatted_elements)
                    stream.write("\n")

class Title(DynaKeyword):
    def __init__(self):
        super(Title,self).__init__("TITLE")

    def parse(self, line):
        parameters = self.parse_whole(line[0][0],[80])
        parameters[0] = parameters[0].replace("\n","")
        #parameters = line[0][0].parse_whole([80])
        self.parameters.append(parameters)

    def TITLE(self):
        return f"{str(self.parameters[0][0])}"
    
    def write(self, stream):
        stream.write("*TITLE\n")
        stream.write("$$  TITLE\n")
        self.writeParameters(stream)
    
class PreScript():

    def __init__(self):
        self.script = ""
        self.script +="$  ----------------------------------------------------------------------\n"
        self.script +="$ Copyright (C) 2023 Koo\n"
        self.script +="$ This is a pre-processing script for LS-DYNA\n"
        self.script +="$  ----------------------------------------------------------------------\n"

    def write(self, stream):
        stream.write(self.script)

class DynaKeywordManager():
    def __init__(self):
        self.keywords = {}
    
    def addKeyword(self, keyword):
        self.keywords[keyword.name] = keyword

    def CombinewithDynaManager(self, dynaManager):
        for key in dynaManager.keywords:
            self.keywords[key] = dynaManager.keywords[key]


class DynaManager():
    def __init__(self):
        self.currentDirectory = os.getcwd()
        self.inputFile = ""
        self.dynaKeywordMan = None
        pass
    
    def SetInputPath(self, path):

        #remove file name from path 
        self.currentDirectory = os.path.dirname(path)        
        #remain file name and ext only
        self.inputFile = os.path.basename(path)
    
    def ReadKeywordsfromFile(self, path, lines_with_asterisk, keyword_dict):        
        curLines = []
        latest_keyword = ""
        includedList = []
        empty_Keywords = []
        with open(path, 'r') as file:            
            
            for line in file:
                # Check if the line starts with an asterisk
                if line.startswith('*'):
                    if latest_keyword == 'INCLUDE':
                        includedList = curLines
                    line = line.split(' ')[0]
                    lines_with_asterisk.append(line[1:].strip())
                    if len(curLines) > 0:
                        if latest_keyword not in keyword_dict:
                            keyword_dict[latest_keyword] = []
                        keyword_dict[latest_keyword].append(curLines)
                    elif latest_keyword == "CONTROL_MPP_IO_NODUMP":
                        pass
                    elif latest_keyword == "":
                        pass
                    elif latest_keyword == "KEYWORD":
                        pass
                    else:
                        print("Warning: Empty keyword found: " + latest_keyword)
                        empty_Keywords.append(latest_keyword)


                        
                    curLines = [] 
                    
                    latest_keyword = line[1:].strip()
                elif line.startswith('$'):
                    continue
                else:
                    curLines.append(line)
        for curFile in includedList:
            self.ReadKeywordsfromFile(curFile.strip(), lines_with_asterisk, keyword_dict)

        for keyword in empty_Keywords:
            lines_with_asterisk.remove(keyword)
        return lines_with_asterisk, keyword_dict

    def WriteOutputFile(self, outputFileName,controlKeywords="", contactKeywords="", initialKeywords="", setKeywords="",rigidKeywords="",boundaryKeywords="",interfaceKeywords="",defineKeywords="",sectionKeywords="",materialKeywords="",loadKeywords="",meshKeywords="",databaseKeywords=""):
        dynaKeywords = self.dynaKeywordMan.keywords
        with open(outputFileName, 'w') as file:
            '''
            #KEYWORD
            '''
            if "KEYWORD_ID" in dynaKeywords:
                keyword_title = dynaKeywords["KEYWORD_ID"]
                keyword_title.write(file)
            else:
                file.write("*KEYWORD\n")
            '''
            #TITLE
            TITLE
            '''
            if "TITLE" in dynaKeywords:
                title = dynaKeywords["TITLE"]
                title.write(file)
            
            '''
            #PARAMETER
            PARAMETER
            '''

            if "PARAMETER" in dynaKeywords:
                parameter = dynaKeywords["PARAMETER"]
                parameter.write(file)

            '''
            #CONTROL CARDS    
            CONTROL_ACCURACY
            CONTROL_ADAPT
            CONTROL_ADAPTIVE
            CONTROL_ALE
            CONTROL_TERMINATION
            CONTROL_TIMESTEP
            CONTROL_ACCURACY
            CONTROL_SOLUTION
            CONTROL_DYNAMIC_RELAXATION
            CONTROL_CPU
            CONTROL_ENERGY
            CONTROL_HOURGLASS
            CONTROL_IMPLICIT_AUTO
            CONTROL_IMPLICIT_DYNAMICS
            CONTROL_IMPLICIT_EIGENVALUE
            CONTROL_IMPLICIT_GENERAL
            CONTROL_IMPLICIT_SOLUTION
            CONTROL_IMPLICIT_SOLVER
            CONTROL_BULK_VISCOSITY
            CONTROL_CONTACT
            CONTROL_RIGID
            CONTROL_SHELL
            CONTROL_SOLID
            CONTROL_OUTPUT
            CONTROL_MPP_IO_NODUMP
            '''
            if "CONTROL_ALE" in dynaKeywords:
                control_ale = dynaKeywords["CONTROL_ALE"]
                control_ale.write(file)
            if "CONTROL_ADAPT" in dynaKeywords:
                control_adapt = dynaKeywords["CONTROL_ADAPT"]
                control_adapt.write(file)
            if "CONTROL_ADAPTIVE" in dynaKeywords:
                control_adaptive = dynaKeywords["CONTROL_ADAPTIVE"]
                control_adaptive.write(file)
            if "CONTROL_TERMINATION" in dynaKeywords:
                control_termination = dynaKeywords["CONTROL_TERMINATION"]
                control_termination.write(file)
            if "CONTROL_TIMESTEP" in dynaKeywords:
                control_timestep = dynaKeywords["CONTROL_TIMESTEP"]
                control_timestep.write(file)
            if "CONTROL_ACCURACY" in dynaKeywords:
                control_accuracy = dynaKeywords["CONTROL_ACCURACY"]
                control_accuracy.write(file)
            if "CONTROL_SOLUTION" in dynaKeywords:
                control_solution = dynaKeywords["CONTROL_SOLUTION"]
                control_solution.write(file)   
            if "CONTROL_DYNAMIC_RELAXATION" in dynaKeywords:
                control_dynamic_relaxation = dynaKeywords["CONTROL_DYNAMIC_RELAXATION"]
                control_dynamic_relaxation.write(file)             
            if "CONTROL_CPU" in dynaKeywords:
                control_cpu = dynaKeywords["CONTROL_CPU"]
                control_cpu.write(file)
            if "CONTROL_ENERGY" in dynaKeywords:
                control_energy = dynaKeywords["CONTROL_ENERGY"]
                control_energy.write(file)
            if "CONTROL_HOURGLASS" in dynaKeywords:
                control_hourglass = dynaKeywords["CONTROL_HOURGLASS"]
                control_hourglass.write(file)
            if "CONTROL_IMPLICIT_AUTO" in dynaKeywords:
                control_implicit_auto = dynaKeywords["CONTROL_IMPLICIT_AUTO"]
                control_implicit_auto.write(file)
            if "CONTROL_IMPLICIT_DYNAMICS" in dynaKeywords:
                control_implicit_dynamics = dynaKeywords["CONTROL_IMPLICIT_DYNAMICS"]
                control_implicit_dynamics.write(file)
            if "CONTROL_IMPLICIT_EIGENVALUE" in dynaKeywords:
                control_implicit_eigenvalue = dynaKeywords["CONTROL_IMPLICIT_EIGENVALUE"]
                control_implicit_eigenvalue.write(file)
            if "CONTROL_IMPLICIT_GENERAL" in dynaKeywords:
                control_implicit_general = dynaKeywords["CONTROL_IMPLICIT_GENERAL"]
                control_implicit_general.write(file)
            if "CONTROL_IMPLICIT_SOLUTION" in dynaKeywords:
                control_implicit_solution = dynaKeywords["CONTROL_IMPLICIT_SOLUTION"]
                control_implicit_solution.write(file)
            if "CONTROL_IMPLICIT_SOLVER" in dynaKeywords:
                control_implicit_solver = dynaKeywords["CONTROL_IMPLICIT_SOLVER"]
                control_implicit_solver.write(file)                
            if "CONTROL_BULK_VISCOSITY" in dynaKeywords:
                control_bulk_viscosity = dynaKeywords["CONTROL_BULK_VISCOSITY"]
                control_bulk_viscosity.write(file)
            if "CONTROL_CONTACT" in dynaKeywords:
                control_contact = dynaKeywords["CONTROL_CONTACT"]
                control_contact.write(file)
            if "CONTROL_RIGID" in dynaKeywords:
                control_rigid = dynaKeywords["CONTROL_RIGID"]
                control_rigid.write(file)
            if "CONTROL_SHELL" in dynaKeywords:
                control_shell = dynaKeywords["CONTROL_SHELL"]
                control_shell.write(file)
            if "CONTROL_SOLID" in dynaKeywords:
                control_solid = dynaKeywords["CONTROL_SOLID"]
                control_solid.write(file)
            if "CONTROL_OUTPUT" in dynaKeywords:
                control_output = dynaKeywords["CONTROL_OUTPUT"]
                control_output.write(file)
            if "CONTROL_MPP_IO_NODUMP" in dynaKeywords:
                control_mpp_io_nodump = dynaKeywords["CONTROL_MPP_IO_NODUMP"]
                control_mpp_io_nodump.write(file)            
            
            if len(controlKeywords) > 0:
                file.write(controlKeywords)
            
            '''
            # CONTACT CARDS
            CONTACT_ADD_WEAR
            CONTACT_AUTOMATIC_SINGLE_SURFACE
            CONTACT_AUTOMATIC_SINGLE_SURFACE_ID
            CONTACT_AUTOMATIC_SURFACE_TO_SURFACE
            CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID
            CONTACT_AUTOMATIC_GENERAL
            CONTACT_AUTOMATIC_GENERAL_ID
            CONTACT_AUTOMATIC_NODES_TO_SURFACE
            CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID
            CONTACT_FEM_PERI_TIE_BREAK_ID
            CONTACT_NODES_TO_SURFACE
            CONTACT_NODES_TO_SURFACE_ID
            CONTACT_ONE_WAY_SURFACE_TO_SURFACE
            CONTACT_ONE_WAY_SURFACE_TO_SURFACE_ID
            CONTACT_SINGLE_SURFACE
            CONTACT_SINGLE_SURFACE_ID
            CONTACT_SURFACE_TO_SURFACE
            CONTACT_SURFACE_TO_SURFACE_ID
            CONTACT_SURFACE_TO_SURFACE_OFFSET
            CONTACT_SURFACE_TO_SURFACE_OFFSET_ID
            CONTACT_SURFACE_TO_SURFACE_INTERFERENCE
            CONTACT_SURFACE_TO_SURFACE_INTERFERENCE_ID
            CONTACT_TIED_NODES_TO_SURFACE
            CONTACT_TIED_NODES_TO_SURFACE_ID
            CONTACT_TIED_SHELL_EDGE_TO_SURFACE
            CONTACT_TIED_SHELL_EDGE_TO_SURFACE_ID
            CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET
            CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID
            CONTACT_TIED_SURFACE_TO_SURFACE
            CONTACT_TIED_SURFACE_TO_SURFACE_ID
            CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET
            CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID
            CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET
            CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID
            CONTACT_ERODING_NODES_TO_SURFACE
            CONTACT_ERODING_NODES_TO_SURFACE_ID
            CONTACT_ERODING_SINGLE_SURFACE
            CONTACT_ERODING_SINGLE_SURFACE_ID
            CONTACT_ERODING_SURFACE_TO_SURFACE
            CONTACT_ERODING_SURFACE_TO_SURFACE_ID
            CONTACT_ERODING_SURFACE_TO_SURFACE_TITLE
            CONTACT_FORCE_TRANSDUCER_PENALTY
            CONTACT_FORCE_TRANSDUCER_PENALTY_ID
            CONTACT_SLIDING_ONLY

            '''       
            if "CONTACT_ADD_WEAR" in dynaKeywords:
                contact_add_wear = dynaKeywords["CONTACT_ADD_WEAR"]
                contact_add_wear.write(file)      
            if "CONTACT_AUTOMATIC_SINGLE_SURFACE" in dynaKeywords:
                contact_automatic_single_surface = dynaKeywords["CONTACT_AUTOMATIC_SINGLE_SURFACE"]
                contact_automatic_single_surface.write(file)
            if "CONTACT_AUTOMATIC_SINGLE_SURFACE_ID" in dynaKeywords:
                contact_automatic_single_surface_id = dynaKeywords["CONTACT_AUTOMATIC_SINGLE_SURFACE_ID"]
                contact_automatic_single_surface_id.write(file)
            if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE" in dynaKeywords:
                contact_automatic_surface_to_surface = dynaKeywords["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE"]
                contact_automatic_surface_to_surface.write(file)
            if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID" in dynaKeywords:
                contact_automatic_surface_to_surface_id = dynaKeywords["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID"]
                contact_automatic_surface_to_surface_id.write(file)
            if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET" in dynaKeywords:
                contact_automatic_surface_to_surface_offset = dynaKeywords["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET"]
                contact_automatic_surface_to_surface_offset.write(file)
            if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET_ID" in dynaKeywords:
                contact_automatic_surface_to_surface_offset_id = dynaKeywords["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET_ID"]
                contact_automatic_surface_to_surface_offset_id.write(file)
            if "CONTACT_AUTOMATIC_GENERAL" in dynaKeywords:
                contact_automatic_general = dynaKeywords["CONTACT_AUTOMATIC_GENERAL"]
                contact_automatic_general.write(file)
            if "CONTACT_AUTOMATIC_GENERAL_ID" in dynaKeywords:
                contact_automatic_general_id = dynaKeywords["CONTACT_AUTOMATIC_GENERAL_ID"]
                contact_automatic_general_id.write(file)
            if "CONTACT_AUTOMATIC_NODES_TO_SURFACE" in dynaKeywords:
                contact_automatic_nodes_to_surface = dynaKeywords["CONTACT_AUTOMATIC_NODES_TO_SURFACE"]
                contact_automatic_nodes_to_surface.write(file)
            if "CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID" in dynaKeywords:
                contact_automatic_nodes_to_surface_id = dynaKeywords["CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID"]
                contact_automatic_nodes_to_surface_id.write(file)
            if "CONTACT_FEM_PERI_TIE_BREAK_ID" in dynaKeywords:
                contact_fem_peri_tie_break_id = dynaKeywords["CONTACT_FEM_PERI_TIE_BREAK_ID"]
                contact_fem_peri_tie_break_id.write(file)
            if "CONTACT_NODES_TO_SURFACE" in dynaKeywords:
                contact_nodes_to_surface = dynaKeywords["CONTACT_NODES_TO_SURFACE"]
                contact_nodes_to_surface.write(file)
            if "CONTACT_NODES_TO_SURFACE_ID" in dynaKeywords:
                contact_nodes_to_surface_id = dynaKeywords["CONTACT_NODES_TO_SURFACE_ID"]
                contact_nodes_to_surface_id.write(file)
            if "CONTACT_ONE_WAY_SURFACE_TO_SURFACE" in dynaKeywords:
                contact_one_way_surface_to_surface = dynaKeywords["CONTACT_ONE_WAY_SURFACE_TO_SURFACE"]
                contact_one_way_surface_to_surface.write(file)
            if "CONTACT_ONE_WAY_SURFACE_TO_SURFACE_ID" in dynaKeywords:
                contact_one_way_surface_to_surface_id = dynaKeywords["CONTACT_ONE_WAY_SURFACE_TO_SURFACE_ID"]
                contact_one_way_surface_to_surface_id.write(file)
            if "CONTACT_SINGLE_SURFACE" in dynaKeywords:
                contact_single_surface = dynaKeywords["CONTACT_SINGLE_SURFACE"]
                contact_single_surface.write(file)
            if "CONTACT_SINGLE_SURFACE_ID" in dynaKeywords:
                contact_single_surface_id = dynaKeywords["CONTACT_SINGLE_SURFACE_ID"]
                contact_single_surface_id.write(file)
            if "CONTACT_SURFACE_TO_SURFACE" in dynaKeywords:
                contact_surface_to_surface = dynaKeywords["CONTACT_SURFACE_TO_SURFACE"]
                contact_surface_to_surface.write(file)
            if "CONTACT_SURFACE_TO_SURFACE_ID" in dynaKeywords:
                contact_surface_to_surface_id = dynaKeywords["CONTACT_SURFACE_TO_SURFACE_ID"]
                contact_surface_to_surface_id.write(file)
            if "CONTACT_SURFACE_TO_SURFACE_INTERFERENCE" in dynaKeywords:
                contact_surface_to_surface_interference = dynaKeywords["CONTACT_SURFACE_TO_SURFACE_INTERFERENCE"]
                contact_surface_to_surface_interference.write(file)
            if "CONTACT_SURFACE_TO_SURFACE_INTERFERENCE_ID" in dynaKeywords:
                contact_surface_to_surface_interference_id = dynaKeywords["CONTACT_SURFACE_TO_SURFACE_INTERFERENCE_ID"]
                contact_surface_to_surface_interference_id.write(file)     
            if "CONTACT_TIED_NODES_TO_SURFACE" in dynaKeywords:
                contact_tied_nodes_to_surface = dynaKeywords["CONTACT_TIED_NODES_TO_SURFACE"]
                contact_tied_nodes_to_surface.write(file)
            if "CONTACT_TIED_NODES_TO_SURFACE_ID" in dynaKeywords:
                contact_tied_nodes_to_surface_id = dynaKeywords["CONTACT_TIED_NODES_TO_SURFACE_ID"]
                contact_tied_nodes_to_surface_id.write(file)       
            if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE" in dynaKeywords:
                contact_tied_shell_edge_to_surface = dynaKeywords["CONTACT_TIED_SHELL_EDGE_TO_SURFACE"]
                contact_tied_shell_edge_to_surface.write(file)
            if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_ID" in dynaKeywords:
                contact_tied_shell_edge_to_surface_id = dynaKeywords["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_ID"]
                contact_tied_shell_edge_to_surface_id.write(file)
            if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET" in dynaKeywords:
                contact_tied_shell_edge_to_surface_beam_offset = dynaKeywords["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET"]
                contact_tied_shell_edge_to_surface_beam_offset.write(file)
            if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID" in dynaKeywords:
                contact_tied_shell_edge_to_surface_beam_offset_id = dynaKeywords["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID"]
                contact_tied_shell_edge_to_surface_beam_offset_id.write(file)                
            if "CONTACT_TIED_SURFACE_TO_SURFACE" in dynaKeywords:
                contact_tied_surface_to_surface = dynaKeywords["CONTACT_TIED_SURFACE_TO_SURFACE"]
                contact_tied_surface_to_surface.write(file)
            if "CONTACT_TIED_SURFACE_TO_SURFACE_ID" in dynaKeywords:
                contact_tied_surface_to_surface_id = dynaKeywords["CONTACT_TIED_SURFACE_TO_SURFACE_ID"]
                contact_tied_surface_to_surface_id.write(file)                
            if "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET" in dynaKeywords:
                contact_tied_surface_to_surface_offset = dynaKeywords["CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET"]
                contact_tied_surface_to_surface_offset.write(file)
            if "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID" in dynaKeywords:
                contact_tied_surface_to_surface_offset_id = dynaKeywords["CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID"]
                contact_tied_surface_to_surface_offset_id.write(file)                
            if "CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET" in dynaKeywords:
                contact_tied_surface_to_surface_constrained_offset = dynaKeywords["CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET"]
                contact_tied_surface_to_surface_constrained_offset.write(file)
            if "CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID" in dynaKeywords:
                contact_tied_surface_to_surface_constrained_offset_id = dynaKeywords["CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID"]
                contact_tied_surface_to_surface_constrained_offset_id.write(file)
            if "CONTACT_ERODING_NODES_TO_SURFACE" in dynaKeywords:
                contact_eroding_nodes_to_surface = dynaKeywords["CONTACT_ERODING_NODES_TO_SURFACE"]
                contact_eroding_nodes_to_surface.write(file)
            if "CONTACT_ERODING_NODES_TO_SURFACE_ID" in dynaKeywords:
                contact_eroding_nodes_to_surface_id = dynaKeywords["CONTACT_ERODING_NODES_TO_SURFACE_ID"]
                contact_eroding_nodes_to_surface_id.write(file)
            if "CONTACT_ERODING_SINGLE_SURFACE" in dynaKeywords:
                contact_eroding_single_surface = dynaKeywords["CONTACT_ERODING_SINGLE_SURFACE"]
                contact_eroding_single_surface.write(file)
            if "CONTACT_ERODING_SINGLE_SURFACE_ID" in dynaKeywords:
                contact_eroding_single_surface_id = dynaKeywords["CONTACT_ERODING_SINGLE_SURFACE_ID"]
                contact_eroding_single_surface_id.write(file)                
            if "CONTACT_ERODING_SURFACE_TO_SURFACE" in dynaKeywords:
                contact_eroding_surface_to_surface = dynaKeywords["CONTACT_ERODING_SURFACE_TO_SURFACE"]
                contact_eroding_surface_to_surface.write(file)
            if "CONTACT_ERODING_SURFACE_TO_SURFACE_ID" in dynaKeywords:
                contact_eroding_surface_to_surface_id = dynaKeywords["CONTACT_ERODING_SURFACE_TO_SURFACE_ID"]
                contact_eroding_surface_to_surface_id.write(file)
            if "CONTACT_ERODING_SURFACE_TO_SURFACE_TITLE" in dynaKeywords:
                contact_eroding_surface_to_surface_title = dynaKeywords["CONTACT_ERODING_SURFACE_TO_SURFACE_TITLE"]
                contact_eroding_surface_to_surface_title.write(file)
            if "CONTACT_FORCE_TRANSDUCER_PENALTY" in dynaKeywords:
                contact_force_transducer_penalty = dynaKeywords["CONTACT_FORCE_TRANSDUCER_PENALTY"]
                contact_force_transducer_penalty.write(file)
            if "CONTACT_FORCE_TRANSDUCER_PENALTY_ID" in dynaKeywords:
                contact_force_transducer_penalty_id = dynaKeywords["CONTACT_FORCE_TRANSDUCER_PENALTY_ID"]
                contact_force_transducer_penalty_id.write(file)
            if "CONTACT_SLIDING_ONLY" in dynaKeywords:
                contact_sliding_only = dynaKeywords["CONTACT_SLIDING_ONLY"]
                contact_sliding_only.write(file)

            if len(contactKeywords) > 0:
                file.write(contactKeywords)

            '''
            # INITIAL CARDS
            INITIAL_STRESS_SOLID
            INITIAL_STRESS_SOLID_SET
            INITIAL_VELOCITY
            INITIAL_VELOCITY_NODE
            INITIAL_VELOCITY_GENERATION
            ''' 
            if "INITIAL_STRESS_SOLID" in dynaKeywords:
                initial_stress_solid = dynaKeywords["INITIAL_STRESS_SOLID"]
                initial_stress_solid.write(file)
            if "INITIAL_STRESS_SOLID_SET" in dynaKeywords:
                initial_stress_solid_set = dynaKeywords["INITIAL_STRESS_SOLID_SET"]
                initial_stress_solid_set.write(file)
            if "INITIAL_VELOCITY" in dynaKeywords:
                initial_velocity = dynaKeywords["INITIAL_VELOCITY"]
                initial_velocity.write(file)
            if "INITIAL_VELOCITY_NODE" in dynaKeywords:
                initial_velocity_node = dynaKeywords["INITIAL_VELOCITY_NODE"]
                initial_velocity_node.write(file)
            if "INITIAL_VELOCITY_GENERATION" in dynaKeywords:
                initial_velocity_generation = dynaKeywords["INITIAL_VELOCITY_GENERATION"]
                initial_velocity_generation.write(file)
            
            if len(initialKeywords) > 0:
                file.write(initialKeywords)

            '''
            # SET CARDS
            SET_PART
            SET_PART_LIST
            SET_PART_LIST_TITLE
            SET_PART_LIST_GENERATE            
            SET_NODE_ADD
            SET_NODE_LIST
            SET_NODE_LIST_TITLE
            SET_NODE_LIST_GENERATE
            SET_NODE_GENERAL
            SET_SEGMENT
            SET_SEGMENT_TITLE
            SET_SHELL
            SET_SHELL_TITLE
            SET_SHELL_LIST
            SET_SOLID
            SET_SOLID_TITLE
            '''
            if "SET_PART" in dynaKeywords:
                set_part = dynaKeywords["SET_PART"]
                set_part.write(file)
            if "SET_PART_LIST" in dynaKeywords:
                set_part_list = dynaKeywords["SET_PART_LIST"]
                set_part_list.write(file)
            if "SET_PART_LIST_TITLE" in dynaKeywords:
                set_part_list_title = dynaKeywords["SET_PART_LIST_TITLE"]
                set_part_list_title.write(file)
            if "SET_PART_LIST_GENERATE" in dynaKeywords:
                set_part_list_generate = dynaKeywords["SET_PART_LIST_GENERATE"]
                set_part_list_generate.write(file)            
            if "SET_NODE_ADD" in dynaKeywords:
                set_node_add = dynaKeywords["SET_NODE_ADD"]
                set_node_add.write(file)
            if "SET_NODE_LIST" in dynaKeywords:
                set_node_list = dynaKeywords["SET_NODE_LIST"]
                set_node_list.write(file)
            if "SET_NODE_LIST_TITLE" in dynaKeywords:
                set_node_list_title = dynaKeywords["SET_NODE_LIST_TITLE"]
                set_node_list_title.write(file)
            if "SET_NODE_LIST_GENERATE" in dynaKeywords:
                set_node_list_generate = dynaKeywords["SET_NODE_LIST_GENERATE"]
                set_node_list_generate.write(file)
            if "SET_NODE_GENERAL" in dynaKeywords:
                set_node_general = dynaKeywords["SET_NODE_GENERAL"]
                set_node_general.write(file)
            if "SET_SEGMENT"  in dynaKeywords:
                set_segment = dynaKeywords["SET_SEGMENT"]
                set_segment.write(file)
            if "SET_SEGMENT_TITLE" in dynaKeywords:
                set_segment_title = dynaKeywords["SET_SEGMENT_TITLE"]
                set_segment_title.write(file)
            if "SET_SHELL" in dynaKeywords:
                set_shell = dynaKeywords["SET_SHELL"]
                set_shell.write(file)
            if "SET_SHELL_TITLE" in dynaKeywords:
                set_shell_title = dynaKeywords["SET_SHELL_TITLE"]
                set_shell_title.write(file)
            if "SET_SHELL_LIST" in dynaKeywords:
                set_shell_list = dynaKeywords["SET_SHELL_LIST"]
                set_shell_list.write(file)
            if "SET_SOLID" in dynaKeywords:
                set_solid = dynaKeywords["SET_SOLID"]
                set_solid.write(file)
            if "SET_SOLID_TITLE" in dynaKeywords:
                set_solid_title = dynaKeywords["SET_SOLID_TITLE"]
                set_solid_title.write(file)

            if len(setKeywords) > 0:
                file.write(setKeywords)
            '''
            # RIGID CARDS
            RIGIDWALL_GEOMETRIC_FLAT_DISPLAY
            RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID
            RIGIDWALL_PLANAR     
            RIGIDWALL_PLANAR_ID       
            RIGIDWALL_PLANAR_MOVING
            RIGIDWALL_PLANAR_MOVING_ID
            RIGIDWALL_PLANAR_MOVING_FORCES
            RIGIDWALL_PLANAR_MOVING_FORCES_ID

            '''            
            if "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY" in dynaKeywords:
                rigidwall_geometric_flat_display = dynaKeywords["RIGIDWALL_GEOMETRIC_FLAT_DISPLAY"]
                rigidwall_geometric_flat_display.write(file)
            if "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID" in dynaKeywords:
                rigidwall_geometric_flat_display_id = dynaKeywords["RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID"]
                rigidwall_geometric_flat_display_id.write(file)            
            if "RIGIDWALL_PLANAR" in dynaKeywords:
                rigidwall_planar = dynaKeywords["RIGIDWALL_PLANAR"]
                rigidwall_planar.write(file)
            if "RIGIDWALL_PLANAR_ID" in dynaKeywords:
                rigidwall_planar_id = dynaKeywords["RIGIDWALL_PLANAR_ID"]
                rigidwall_planar_id.write(file)
            if "RIGIDWALL_PLANAR_MOVING" in dynaKeywords:
                rigidwall_planar_moving = dynaKeywords["RIGIDWALL_PLANAR_MOVING"]
                rigidwall_planar_moving.write(file)
            if "RIGIDWALL_PLANAR_MOVING_ID" in dynaKeywords:
                rigidwall_planar_moving_id = dynaKeywords["RIGIDWALL_PLANAR_MOVING_ID"]
                rigidwall_planar_moving_id.write(file)
            if "RIGIDWALL_PLANAR_MOVING_FORCES" in dynaKeywords:
                rigidwall_planar_moving_forces = dynaKeywords["RIGIDWALL_PLANAR_MOVING_FORCES"]
                rigidwall_planar_moving_forces.write(file)
            if "RIGIDWALL_PLANAR_MOVING_FORCES_ID" in dynaKeywords:
                rigidwall_planar_moving_forces_id = dynaKeywords["RIGIDWALL_PLANAR_MOVING_FORCES_ID"]
                rigidwall_planar_moving_forces_id.write(file)

            if len(rigidKeywords) > 0:
                file.write(rigidKeywords)            
            '''            
            #BOUNDARY / INITIAL CONDITIONS
            BOUNDARY_PRESCRIBED_MOTION_NODE
            BOUNDARY_PRESCRIBED_MOTION_NODE_ID
            BOUNDARY_PRESCRIBED_MOTION_RIGID
            BOUNDARY_PRESCRIBED_MOTION_RIGID_ID
            BOUNDARY_PRESCRIBED_MOTION_SET
            BOUNDARY_PRESCRIBED_MOTION_SET_ID
            BOUNDARY_PZEPOT
            BOUNDARY_SPC_NODE
            BOUNDARY_SPC_NODE_ID
            BOUNDARY_SPC_SET
            BOUNDARY_SPC_SET_ID
            CONSTRAINED_JOINT_SPHERICAL
            CONSTRAINED_JOINT_SPHERICAL_ID
            CONSTRAINED_NODAL_RIGID_BODY
            CONSTRAINED_NODAL_RIGID_BODY_TITLE
            CONSTRAINED_EXTRA_NODES_NODE
            CONSTRAINED_EXTRA_NODES_SET
            CONSTRAINED_NODE_SET
            CONSTRAINED_NODE_SET_ID
            CONSTRAINED_INTERPOLATION
            CONSTRAINED_RIGID_BODIES
            CONSTRAINED_RIGID_BODIES_SET
            
            '''
            if "BOUNDARY_PRESCRIBED_MOTION_NODE" in dynaKeywords:
                boundary_prescribed_motion_node = dynaKeywords["BOUNDARY_PRESCRIBED_MOTION_NODE"]
                boundary_prescribed_motion_node.write(file)
            if "BOUNDARY_PRESCRIBED_MOTION_NODE_ID" in dynaKeywords:
                boundary_prescribed_motion_node_id = dynaKeywords["BOUNDARY_PRESCRIBED_MOTION_NODE_ID"]
                boundary_prescribed_motion_node_id.write(file)
            if "BOUNDARY_PRESCRIBED_MOTION_RIGID" in dynaKeywords:
                boundary_prescribed_motion_rigid = dynaKeywords["BOUNDARY_PRESCRIBED_MOTION_RIGID"]
                boundary_prescribed_motion_rigid.write(file)
            if "BOUNDARY_PRESCRIBED_MOTION_RIGID_ID" in dynaKeywords:
                boundary_prescribed_motion_rigid_id = dynaKeywords["BOUNDARY_PRESCRIBED_MOTION_RIGID_ID"]
                boundary_prescribed_motion_rigid_id.write(file)
            if "BOUNDARY_PRESCRIBED_MOTION_SET" in dynaKeywords:
                boundary_prescribed_motion_set = dynaKeywords["BOUNDARY_PRESCRIBED_MOTION_SET"]
                boundary_prescribed_motion_set.write(file)                
            if "BOUNDARY_PRESCRIBED_MOTION_SET_ID" in dynaKeywords:
                boundary_prescribed_motion_set_id = dynaKeywords["BOUNDARY_PRESCRIBED_MOTION_SET_ID"]
                boundary_prescribed_motion_set_id.write(file)
            if "BOUNDARY_PZEPOT" in dynaKeywords:
                boundary_pzepot = dynaKeywords["BOUNDARY_PZEPOT"]
                boundary_pzepot.write(file)
            if "BOUNDARY_SPC_NODE" in dynaKeywords:
                boundary_spc_node = dynaKeywords["BOUNDARY_SPC_NODE"]
                boundary_spc_node.write(file)
            if "BOUNDARY_SPC_SET_ID" in dynaKeywords:
                boundary_spc_set_id = dynaKeywords["BOUNDARY_SPC_SET_ID"]
                boundary_spc_set_id.write(file)
            if "BOUNDARY_SPC_SET" in dynaKeywords:
                boundary_spc_set = dynaKeywords["BOUNDARY_SPC_SET"]
                boundary_spc_set.write(file)
            if "BOUNDARY_SPC_SET_ID" in dynaKeywords:
                boundary_spc_set_id = dynaKeywords["BOUNDARY_SPC_SET_ID"]
                boundary_spc_set_id.write(file)
            if "CONSTRAINED_JOINT_SPHERICAL" in dynaKeywords:
                constrained_joint_spherical = dynaKeywords["CONSTRAINED_JOINT_SPHERICAL"]
                constrained_joint_spherical.write(file)
            if "CONSTRAINED_JOINT_SPHERICAL_ID" in dynaKeywords:
                constrained_joint_spherical_id = dynaKeywords["CONSTRAINED_JOINT_SPHERICAL_ID"]
                constrained_joint_spherical_id.write(file)
            if "CONSTRAINED_NODAL_RIGID_BODY" in dynaKeywords:
                constrained_nodal_rigid_body = dynaKeywords["CONSTRAINED_NODAL_RIGID_BODY"]
                constrained_nodal_rigid_body.write(file)
            if "CONSTRAINED_NODAL_RIGID_BODY_TITLE" in dynaKeywords:
                constrained_nodal_rigid_body_title = dynaKeywords["CONSTRAINED_NODAL_RIGID_BODY_TITLE"]
                constrained_nodal_rigid_body_title.write(file)
            if "CONSTRAINED_EXTRA_NODES_NODE" in dynaKeywords:
                constrained_extra_nodes_node = dynaKeywords["CONSTRAINED_EXTRA_NODES_NODE"]
                constrained_extra_nodes_node.write(file)
            if "CONSTRAINED_EXTRA_NODES_SET" in dynaKeywords:
                constrained_extra_nodes_set = dynaKeywords["CONSTRAINED_EXTRA_NODES_SET"]
                constrained_extra_nodes_set.write(file)
            if "CONSTRAINED_NODE_SET" in dynaKeywords:
                constrained_node_set = dynaKeywords["CONSTRAINED_NODE_SET"]
                constrained_node_set.write(file)
            if "CONSTRAINED_NODE_SET_ID" in dynaKeywords:
                constrained_node_set_id = dynaKeywords["CONSTRAINED_NODE_SET_ID"]
                constrained_node_set_id.write(file)
            if "CONSTRAINED_INTERPOLATION" in dynaKeywords:
                constrained_interpolation = dynaKeywords["CONSTRAINED_INTERPOLATION"]
                constrained_interpolation.write(file)
            if "CONSTRAINED_RIGID_BODIES" in dynaKeywords:
                constrained_rigid_bodies = dynaKeywords["CONSTRAINED_RIGID_BODIES"]
                constrained_rigid_bodies.write(file)
            if "CONSTRAINED_RIGID_BODIES_SET" in dynaKeywords:
                constrained_rigid_bodies_set = dynaKeywords["CONSTRAINED_RIGID_BODIES_SET"]
                constrained_rigid_bodies_set.write(file)

            if len(boundaryKeywords) > 0:
                file.write(boundaryKeywords)           

            '''
            #DATABASE

            DATABASE_BNDOUT
            DATABASE_CROSS_SECTION_SET
            DATABASE_CROSS_SECTION_SET_ID
            DATABASE_CROSS_SECTION_PLANE
            DATABASE_CROSS_SECTION_PLANE_ID            
            DATABASE_DEFORC
            DATABASE_ELOUT
            DATABASE_FREQUENCY_BINARY_D3SSD
            DATABASE_GLSTAT
            DATABASE_MATSUM   
            DATABASE_NCFORC         
            DATABASE_NODFOR
            DATABASE_NODOUT
            DATABASE_RBDOUT
            DATABASE_RCFORC
            DATABASE_RWFORC
            DATABASE_SECFORC
            DATABASE_SPCFORC
            DATABASE_SLEOUT
            DATABASE_SWFORC
            DATABASE_BINARY_D3PLOT
            DATABASE_BINARY_D3THDT
            DATABASE_BINARY_D3DUMP
            DATABASE_BINARY_RUNRSF
            DATABASE_BINARY_INTFOR
            DATABASE_BINARY_INTFOR_FILE
            DATABASE_EXTENT_BINARY
            DATABASE_EXTENT_INTFOR
            DATABASE_FORMAT
            DATABASE_HISTORY_NODE
            DATABASE_HISTORY_BEAM
            DATABASE_HISTORY_BEAM_SET
            DATABASE_HISTORY_SHELL
            DATABASE_HISTORY_SHELL_SET
            DATABASE_HISTORY_SOLID
            DATABASE_HISTORY_SOLID_SET
            DATABASE_HISTORY_NODE_SET            
            DATABASE_NODAL_FORCE_GROUP
            '''
            if "DATABASE_BNDOUT" in dynaKeywords:
                database_bndout = dynaKeywords["DATABASE_BNDOUT"]
                database_bndout.write(file)
            if "DATABASE_CROSS_SECTION_SET" in dynaKeywords:
                database_cross_section_set = dynaKeywords["DATABASE_CROSS_SECTION_SET"]
                database_cross_section_set.write(file)
            if "DATABASE_CROSS_SECTION_SET_ID" in dynaKeywords:
                database_cross_section_set_id = dynaKeywords["DATABASE_CROSS_SECTION_SET_ID"]
                database_cross_section_set_id.write(file)
            if "DATABASE_CROSS_SECTION_PLANE" in dynaKeywords:
                database_cross_section_plane = dynaKeywords["DATABASE_CROSS_SECTION_PLANE"]
                database_cross_section_plane.write(file)
            if "DATABASE_CROSS_SECTION_PLANE_ID" in dynaKeywords:
                database_cross_section_plane_id = dynaKeywords["DATABASE_CROSS_SECTION_PLANE_ID"]
                database_cross_section_plane_id.write(file)
            if "DATABASE_DEFORC" in dynaKeywords:
                database_deforc = dynaKeywords["DATABASE_DEFORC"]
                database_deforc.write(file)                
            if "DATABASE_ELOUT" in dynaKeywords:
                database_elout = dynaKeywords["DATABASE_ELOUT"]
                database_elout.write(file)
            if 'DATABASE_FREQUENCY_BINARY_D3SSD' in dynaKeywords:
                database_frequency_binary_d3ssd = dynaKeywords["DATABASE_FREQUENCY_BINARY_D3SSD"]
                database_frequency_binary_d3ssd.write(file)
            if "DATABASE_GLSTAT" in dynaKeywords:
                database_glstat = dynaKeywords["DATABASE_GLSTAT"]
                database_glstat.write(file)
            if "DATABASE_MATSUM" in dynaKeywords:
                database_matsum = dynaKeywords["DATABASE_MATSUM"]
                database_matsum.write(file) 
            if "DATABASE_NCFORC" in dynaKeywords:
                database_ncforc = dynaKeywords["DATABASE_NCFORC"]
                database_ncforc.write(file)
            if "DATABASE_NODFOR" in dynaKeywords:
                database_nodfor = dynaKeywords["DATABASE_NODFOR"]
                database_nodfor.write(file)
            if "DATABASE_NODOUT" in dynaKeywords:
                database_nodout = dynaKeywords["DATABASE_NODOUT"]
                database_nodout.write(file)               
            if "DATABASE_RBDOUT" in dynaKeywords:
                database_rbdout = dynaKeywords["DATABASE_RBDOUT"]
                database_rbdout.write(file)
            if "DATABASE_RCFORC" in dynaKeywords:
                database_rcforc = dynaKeywords["DATABASE_RCFORC"]
                database_rcforc.write(file)
            if "DATABASE_RWFORC" in dynaKeywords:
                database_rwforc = dynaKeywords["DATABASE_RWFORC"]
                database_rwforc.write(file)
            if "DATABASE_SECFORC" in dynaKeywords:
                database_secforc = dynaKeywords["DATABASE_SECFORC"]
                database_secforc.write(file)
            if "DATABASE_SPCFORC" in dynaKeywords:
                database_spcforc = dynaKeywords["DATABASE_SPCFORC"]
                database_spcforc.write(file)
            if "DATABASE_SLEOUT" in dynaKeywords:
                database_sleout = dynaKeywords["DATABASE_SLEOUT"]
                database_sleout.write(file)
            if "DATABASE_SWFORC" in dynaKeywords:
                database_swforc = dynaKeywords["DATABASE_SWFORC"]
                database_swforc.write(file)
            if "DATABASE_BINARY_D3PLOT" in dynaKeywords:
                database_binary_d3plot = dynaKeywords["DATABASE_BINARY_D3PLOT"]
                database_binary_d3plot.write(file)
            if "DATABASE_BINARY_D3THDT" in dynaKeywords:
                database_binary_d3thdt = dynaKeywords["DATABASE_BINARY_D3THDT"]
                database_binary_d3thdt.write(file)
            if "DATABASE_BINARY_D3DUMP" in dynaKeywords:
                database_binary_d3dump = dynaKeywords["DATABASE_BINARY_D3DUMP"]
                database_binary_d3dump.write(file)
            if "DATABASE_BINARY_RUNRSF" in dynaKeywords:
                database_binary_runrsf = dynaKeywords["DATABASE_BINARY_RUNRSF"]
                database_binary_runrsf.write(file)
            if "DATABASE_BINARY_INTFOR" in dynaKeywords:
                database_binary_intfor = dynaKeywords["DATABASE_BINARY_INTFOR"]
                database_binary_intfor.write(file)
            if "DATABASE_BINARY_INTFOR_FILE" in dynaKeywords:
                database_binary_intfor_file = dynaKeywords["DATABASE_BINARY_INTFOR_FILE"]
                database_binary_intfor_file.write(file)
            if "DATABASE_EXTENT_BINARY" in dynaKeywords:
                database_extent_binary = dynaKeywords["DATABASE_EXTENT_BINARY"]
                database_extent_binary.write(file)
            if "DATABASE_EXTENT_INTFOR" in dynaKeywords:
                database_extent_intfor = dynaKeywords["DATABASE_EXTENT_INTFOR"]
                database_extent_intfor.write(file)
            if "DATABASE_FORMAT" in dynaKeywords:
                database_format = dynaKeywords["DATABASE_FORMAT"]
                database_format.write(file)
            if "DATABASE_HISTORY_NODE" in dynaKeywords:
                database_history_node = dynaKeywords["DATABASE_HISTORY_NODE"]
                database_history_node.write(file)
            if "DATABASE_HISTORY_BEAM" in dynaKeywords:
                database_history_beam = dynaKeywords["DATABASE_HISTORY_BEAM"]
                database_history_beam.write(file)
            if "DATABASE_HISTORY_BEAM_SET" in dynaKeywords:
                database_history_beam_set = dynaKeywords["DATABASE_HISTORY_BEAM_SET"]
                database_history_beam_set.write(file)
            if "DATABASE_HISTORY_SHELL" in dynaKeywords:
                database_history_shell = dynaKeywords["DATABASE_HISTORY_SHELL"]
                database_history_shell.write(file)
            if "DATABASE_HISTORY_SHELL_SET" in dynaKeywords:
                database_history_shell_set = dynaKeywords["DATABASE_HISTORY_SHELL_SET"]
                database_history_shell_set.write(file)
            if "DATABASE_HISTORY_SOLID" in dynaKeywords:
                database_history_solid = dynaKeywords["DATABASE_HISTORY_SOLID"]
                database_history_solid.write(file)
            if "DATABASE_HISTORY_SOLID_SET" in dynaKeywords:
                database_history_solid_set = dynaKeywords["DATABASE_HISTORY_SOLID_SET"]
                database_history_solid_set.write(file)
            if "DATABASE_HISTORY_NODE_SET" in dynaKeywords:
                database_history_node_set = dynaKeywords["DATABASE_HISTORY_NODE_SET"]
                database_history_node_set.write(file)            
            if "DATABASE_NODAL_FORCE_GROUP" in dynaKeywords:    
                database_nodal_force_group = dynaKeywords["DATABASE_NODAL_FORCE_GROUP"]
                database_nodal_force_group.write(file)

            if len(databaseKeywords) > 0:
                file.write(databaseKeywords)
            
            '''
            # INTERFACE
            INTERFACE_SPRINGBACK_DYNA3D
            INTERFACE_SPRINGBACK_LSDYNA
            INTERFACE_SPRINGBACK_NASTRAN
            INTERFACE_SPRINGBACK_SEAMLESS
            '''
            if "INTERFACE_SPRINGBACK_DYNA3D" in dynaKeywords:
                interface_springback_dyna3d = dynaKeywords["INTERFACE_SPRINGBACK_DYNA3D"]
                interface_springback_dyna3d.write(file)
            if "INTERFACE_SPRINGBACK_LSDYNA" in dynaKeywords:
                interface_springback_lsdyna = dynaKeywords["INTERFACE_SPRINGBACK_LSDYNA"]
                interface_springback_lsdyna.write(file)
            if "INTERFACE_SPRINGBACK_NASTRAN" in dynaKeywords:
                interface_springback_nastran = dynaKeywords["INTERFACE_SPRINGBACK_NASTRAN"]
                interface_springback_nastran.write(file)
            if "INTERFACE_SPRINGBACK_SEAMLESS" in dynaKeywords:
                interface_springback_seamless = dynaKeywords["INTERFACE_SPRINGBACK_SEAMLESS"]
                interface_springback_seamless.write(file)

            if len(interfaceKeywords) > 0:
                file.write(interfaceKeywords)
            
            ''' DEFINE
            DEFINE_BOX
            DEFINE_COORDINATE_SYSTEM
            DEFINE_COORDINATE_SYSTEM_TITLE
            DEFINE_CURVE
            DEFINE_CURVE_TITLE
            '''
            if "DEFINE_BOX" in dynaKeywords:
                define_box = dynaKeywords["DEFINE_BOX"]
                define_box.write(file)
            if "DEFINE_COORDINATE_SYSTEM" in dynaKeywords:
                define_coordinate_system = dynaKeywords["DEFINE_COORDINATE_SYSTEM"]
                define_coordinate_system.write(file)
            if "DEFINE_COORDINATE_SYSTEM_TITLE" in dynaKeywords:
                define_coordinate_system_title = dynaKeywords["DEFINE_COORDINATE_SYSTEM_TITLE"]
                define_coordinate_system_title.write(file)
            if "DEFINE_CURVE" in dynaKeywords:
                define_curve = dynaKeywords["DEFINE_CURVE"]
                define_curve.write(file)
            if "DEFINE_CURVE_TITLE" in dynaKeywords:
                define_curve_title = dynaKeywords["DEFINE_CURVE_TITLE"]
                define_curve_title.write(file)
            
            if len(defineKeywords) > 0:
                file.write(defineKeywords)
            
            '''
            #SECTION
            SECTION_BEAM
            SECTION_BEAM_TITLE
            SECTION_SHELL
            SECTION_SHELL_TITLE
            SECTION_SOLID
            SECTION_SOLID_TITLE
            SECTION_SOLID_PERI
            SECTION_SOLID_PERI_TITLE
            SECTION_TSHELL
            SECTION_TSHELL_TITLE
            
            '''
            if "SECTION_BEAM" in dynaKeywords:
                section_beam = dynaKeywords["SECTION_BEAM"]
                section_beam.write(file)
            if "SECTION_BEAM_TITLE" in dynaKeywords:
                section_beam_title = dynaKeywords["SECTION_BEAM_TITLE"]
                section_beam_title.write(file)
            if "SECTION_SHELL" in dynaKeywords:
                section_shell = dynaKeywords["SECTION_SHELL"]
                section_shell.write(file)
            if "SECTION_SHELL_TITLE" in dynaKeywords:
                section_shell_title = dynaKeywords["SECTION_SHELL_TITLE"]
                section_shell_title.write(file)
            if "SECTION_SOLID" in dynaKeywords:
                section_solid = dynaKeywords["SECTION_SOLID"]
                section_solid.write(file)
            if "SECTION_SOLID_TITLE" in dynaKeywords:
                section_solid_title = dynaKeywords["SECTION_SOLID_TITLE"]
                section_solid_title.write(file)
            if "SECTION_SOLID_PERI" in dynaKeywords:
                section_solid_peri = dynaKeywords["SECTION_SOLID_PERI"]
                section_solid_peri.write(file)
            if "SECTION_SOLID_PERI_TITLE" in dynaKeywords:
                section_solid_peri_title = dynaKeywords["SECTION_SOLID_PERI_TITLE"]
                section_solid_peri_title.write(file)
            if "SECTION_TSHELL" in dynaKeywords:
                section_tshell = dynaKeywords["SECTION_TSHELL"]
                section_tshell.write(file)
            if "SECTION_TSHELL_TITLE" in dynaKeywords:
                section_tshell_title = dynaKeywords["SECTION_TSHELL_TITLE"]
                section_tshell_title.write(file)

            if len(sectionKeywords) > 0:
                file.write(sectionKeywords)
            '''
            #HOURGLASS
            HOURGLASS
            '''
            if "HOURGLASS" in dynaKeywords:
                hourglass = dynaKeywords["HOURGLASS"]
                hourglass.write(file)

            """
            #EOS
            EOS_LINEAR_POLYNOMIAL
            EOS_TABULATED
            """
            if "EOS_LINEAR_POLYNOMIAL" in dynaKeywords:
                eos_linear_polynomial = dynaKeywords["EOS_LINEAR_POLYNOMIAL"]
                eos_linear_polynomial.write(file)                
            if "EOS_TABULATED" in dynaKeywords:
                eos_tabulated = dynaKeywords["EOS_TABULATED"]
                eos_tabulated.write(file)
            '''
            #MATERIAL
            
            MAT_ADD_EROSION
            MAT_ADD_PZELECTRIC
            MAT_CSCM_CONCRETE
            MAT_CSCM_CONCRETE_TITLE
            MAT_ELASTIC
            MAT_ELASTIC_TITLE
            MAT_VISCOELASTIC
            MAT_VISCOELASTIC_TITLE
            MAT_SOIL_AND_FOAM
            MAT_SOIL_AND_FOAM_FAILURE
            MAT_RIGID
            MAT_RIGID_TITLE
            MAT_COMPOSITE_DAMAGE
            MAT_COMPOSITE_DAMAGE_TITLE
            MAT_PLASTIC_KINEMATIC
            MAT_PLASTIC_KINEMATIC_TITLE                        
            MAT_PIECEWISE_LINEAR_PLASTICITY
            MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE
            MAT_ORIENTED_CRACK
            MAT_ENHANCED_COMPOSITE_DAMAGE
            MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE
            MAT_MOONEY-RIVLIN_RUBBER
            MAT_MOONEY-RIVLIN_RUBBER_TITLE
            MAT_LOW_DENSITY_FOAM
            MAT_LOW_DENSITY_FOAM_TITLE
            MAT_SPOTWELD
            MAT_SPOTWELD_TITLE
            MAT_COHESIVE_MIXED_MODE
            MAT_COHESIVE_MIXED_MODE_TITLE
            MAT_ELASTIC_PERI
            MAT_ELASTIC_PERI_TITLE
            MAT_NULL
            DAMPING_GLOBAL
            DAMPING_PART_MASS
            DAMPING_PART_MASS_SET
            DAMPING_PART_STIFFNESS
            DAMPING_PART_STIFFNESS_SET
            '''
            if "MAT_ADD_EROSION" in dynaKeywords:
                mat_add_erosion = dynaKeywords["MAT_ADD_EROSION"]
                mat_add_erosion.write(file)
            if "MAT_ADD_PZELECTRIC" in dynaKeywords:
                mat_add_pzelectric = dynaKeywords["MAT_ADD_PZELECTRIC"]
                mat_add_pzelectric.write(file)
            if "MAT_CSCM_CONCRETE" in dynaKeywords:
                mat_cscm_concrete = dynaKeywords["MAT_CSCM_CONCRETE"]
                mat_cscm_concrete.write(file)
            if "MAT_CSCM_CONCRETE_TITLE" in dynaKeywords:
                mat_cscm_concrete_title = dynaKeywords["MAT_CSCM_CONCRETE_TITLE"]
                mat_cscm_concrete_title.write(file)
            if "MAT_ELASTIC" in dynaKeywords:
                mat_elastic = dynaKeywords["MAT_ELASTIC"]
                mat_elastic.write(file)
            if "MAT_ELASTIC_TITLE" in dynaKeywords:
                mat_elastic_title = dynaKeywords["MAT_ELASTIC_TITLE"]
                mat_elastic_title.write(file)
            if "MAT_VISCOELASTIC" in dynaKeywords:
                mat_viscoelastic = dynaKeywords["MAT_VISCOELASTIC"]
                mat_viscoelastic.write(file)
            if "MAT_VISCOELASTIC_TITLE" in dynaKeywords:
                mat_viscoelastic_title = dynaKeywords["MAT_VISCOELASTIC_TITLE"]
                mat_viscoelastic_title.write(file)
            if "MAT_SOIL_AND_FOAM" in dynaKeywords:
                mat_soil_and_foam = dynaKeywords["MAT_SOIL_AND_FOAM"]
                mat_soil_and_foam.write(file)
            if "MAT_SOIL_AND_FOAM_FAILURE" in dynaKeywords:
                mat_soil_and_foam_failure = dynaKeywords["MAT_SOIL_AND_FOAM_FAILURE"]
                mat_soil_and_foam_failure.write(file)
            if "MAT_RIGID" in dynaKeywords:
                mat_rigid = dynaKeywords["MAT_RIGID"]
                mat_rigid.write(file)
            if "MAT_RIGID_TITLE" in dynaKeywords:
                mat_rigid_title = dynaKeywords["MAT_RIGID_TITLE"]
                mat_rigid_title.write(file)
            if "MAT_COMPOSITE_DAMAGE" in dynaKeywords:
                mat_composite_damage = dynaKeywords["MAT_COMPOSITE_DAMAGE"]
                mat_composite_damage.write(file)
            if "MAT_COMPOSITE_DAMAGE_TITLE" in dynaKeywords:
                mat_composite_damage_title = dynaKeywords["MAT_COMPOSITE_DAMAGE_TITLE"]
                mat_composite_damage_title.write(file)
            if "MAT_PLASTIC_KINEMATIC" in dynaKeywords:
                mat_plastic_kinematic = dynaKeywords["MAT_PLASTIC_KINEMATIC"]
                mat_plastic_kinematic.write(file)
            if "MAT_PLASTIC_KINEMATIC_TITLE" in dynaKeywords:
                mat_plastic_kinematic_title = dynaKeywords["MAT_PLASTIC_KINEMATIC_TITLE"]
                mat_plastic_kinematic_title.write(file)
            if "MAT_PIECEWISE_LINEAR_PLASTICITY" in dynaKeywords:
                mat_piecewise_linear_plasticity = dynaKeywords["MAT_PIECEWISE_LINEAR_PLASTICITY"]
                mat_piecewise_linear_plasticity.write(file)
            if "MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE" in dynaKeywords:
                mat_piecewise_linear_plasticity_title = dynaKeywords["MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE"]
                mat_piecewise_linear_plasticity_title.write(file)
            if "MAT_ORIENTED_CRACK" in dynaKeywords:
                mat_oriented_crack = dynaKeywords["MAT_ORIENTED_CRACK"]
                mat_oriented_crack.write(file)
            if "MAT_ENHANCED_COMPOSITE_DAMAGE" in dynaKeywords:
                mat_enhanced_composite_damage = dynaKeywords["MAT_ENHANCED_COMPOSITE_DAMAGE"]
                mat_enhanced_composite_damage.write(file)
            if "MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE" in dynaKeywords:
                mat_enhanced_composite_damage_title = dynaKeywords["MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE"]
                mat_enhanced_composite_damage_title.write(file)
            if "MAT_MOONEY-RIVLIN_RUBBER" in dynaKeywords:
                mat_mooney_rivlin_rubber = dynaKeywords["MAT_MOONEY-RIVLIN_RUBBER"]
                mat_mooney_rivlin_rubber.write(file)
            if "MAT_MOONEY-RIVLIN_RUBBER_TITLE" in dynaKeywords:
                mat_mooney_rivlin_rubber_title = dynaKeywords["MAT_MOONEY-RIVLIN_RUBBER_TITLE"]
                mat_mooney_rivlin_rubber_title.write(file)
            if "MAT_LOW_DENSITY_FOAM" in dynaKeywords:
                mat_low_density_foam = dynaKeywords["MAT_LOW_DENSITY_FOAM"]
                mat_low_density_foam.write(file)
            if "MAT_LOW_DENSITY_FOAM_TITLE" in dynaKeywords:
                mat_low_density_foam_title = dynaKeywords["MAT_LOW_DENSITY_FOAM_TITLE"]
                mat_low_density_foam_title.write(file)
            if "MAT_SPOTWELD" in dynaKeywords:
                mat_spotweld = dynaKeywords["MAT_SPOTWELD"]
                mat_spotweld.write(file)
            if "MAT_SPOTWELD_TITLE" in dynaKeywords:
                mat_spotweld_title = dynaKeywords["MAT_SPOTWELD_TITLE"]
                mat_spotweld_title.write(file)
            if "MAT_COHESIVE_MIXED_MODE" in dynaKeywords:
                mat_cohesive_mixed_mode = dynaKeywords["MAT_COHESIVE_MIXED_MODE"]
                mat_cohesive_mixed_mode.write(file)
            if "MAT_COHESIVE_MIXED_MODE_TITLE" in dynaKeywords:
                mat_cohesive_mixed_mode_title = dynaKeywords["MAT_COHESIVE_MIXED_MODE_TITLE"]
                mat_cohesive_mixed_mode_title.write(file)
            if "MAT_ELASTIC_PERI" in dynaKeywords:
                mat_elastic_peri = dynaKeywords["MAT_ELASTIC_PERI"]
                mat_elastic_peri.write(file)
            if "MAT_ELASTIC_PERI_TITLE" in dynaKeywords:
                mat_elastic_peri_title = dynaKeywords["MAT_ELASTIC_PERI_TITLE"]
                mat_elastic_peri_title.write(file)
            if "MAT_NULL" in dynaKeywords:
                mat_null = dynaKeywords["MAT_NULL"]
                mat_null.write(file)
            if "DAMPING_GLOBAL" in dynaKeywords:
                damping_global = dynaKeywords["DAMPING_GLOBAL"]
                damping_global.write(file)
            if "DAMPING_PART_MASS" in dynaKeywords:
                damping_part_mass = dynaKeywords["DAMPING_PART_MASS"]
                damping_part_mass.write(file)
            if "DAMPING_PART_MASS_SET" in dynaKeywords:
                damping_part_mass_set = dynaKeywords["DAMPING_PART_MASS_SET"]
                damping_part_mass_set.write(file)
            if "DAMPING_PART_STIFFNESS" in dynaKeywords:
                damping_part_stiffness = dynaKeywords["DAMPING_PART_STIFFNESS"]
                damping_part_stiffness.write(file)
            if "DAMPING_PART_STIFFNESS_SET" in dynaKeywords:
                damping_part_stiffness_set = dynaKeywords["DAMPING_PART_STIFFNESS_SET"]
                damping_part_stiffness_set.write(file)                

            if len(materialKeywords) > 0:
                file.write(materialKeywords)

            '''
            # LOAD CARDS
            LOAD_BODY_X
            LOAD_BODY_Y
            LOAD_BODY_Z
            LOAD_BODY_RX
            LOAD_BODY_RY
            LOAD_BODY_RZ
            LOAD_BODY_VECTOR
            LOAD_RIGID_BODY
            LOAD_NODE_POINT
            LOAD_NODE_SET
            LOAD_SEGMENT
            LOAD_SEGMENT_ID
            LOAD_SEGMENT_SET
            LOAD_SEGMENT_SET_ID
            '''
            if "LOAD_BODY_X" in dynaKeywords:
                load_body_x = dynaKeywords["LOAD_BODY_X"]
                load_body_x.write(file)
            if "LOAD_BODY_Y" in dynaKeywords:
                load_body_y = dynaKeywords["LOAD_BODY_Y"]
                load_body_y.write(file)
            if "LOAD_BODY_Z" in dynaKeywords:
                load_body_z = dynaKeywords["LOAD_BODY_Z"]
                load_body_z.write(file)
            if "LOAD_BODY_RX" in dynaKeywords:
                load_body_rx = dynaKeywords["LOAD_BODY_RX"]
                load_body_rx.write(file)
            if "LOAD_BODY_RY" in dynaKeywords:
                load_body_ry = dynaKeywords["LOAD_BODY_RY"]
                load_body_ry.write(file)
            if "LOAD_BODY_RZ" in dynaKeywords:
                load_body_rz = dynaKeywords["LOAD_BODY_RZ"]
                load_body_rz.write(file)
            if "LOAD_BODY_VECTOR" in dynaKeywords:
                load_body_vector = dynaKeywords["LOAD_BODY_VECTOR"]
                load_body_vector.write(file)
            if "LOAD_RIGID_BODY" in dynaKeywords:
                load_rigid_body = dynaKeywords["LOAD_RIGID_BODY"]
                load_rigid_body.write(file)
            if "LOAD_NODE_POINT" in dynaKeywords:
                load_node_point = dynaKeywords["LOAD_NODE_POINT"]
                load_node_point.write(file)
            if "LOAD_NODE_SET" in dynaKeywords:
                load_node_set = dynaKeywords["LOAD_NODE_SET"]
                load_node_set.write(file)
            if "LOAD_SEGMENT" in dynaKeywords:
                load_segment = dynaKeywords["LOAD_SEGMENT"]
                load_segment.write(file)
            if "LOAD_SEGMENT_ID" in dynaKeywords:
                load_segment_id = dynaKeywords["LOAD_SEGMENT_ID"]
                load_segment_id.write(file)
            if "LOAD_SEGMENT_SET" in dynaKeywords:
                load_segment_set = dynaKeywords["LOAD_SEGMENT_SET"]
                load_segment_set.write(file)
            if "LOAD_SEGMENT_SET_ID" in dynaKeywords:
                load_segment_set_id = dynaKeywords["LOAD_SEGMENT_SET_ID"]
                load_segment_set_id.write(file)                        

            if len(loadKeywords) > 0:
                file.write(loadKeywords)
            '''
            #MESH
            PART
            PART_COMPOSITE
            PART_CONTACT
            ELEMENT_SOLID
            ELEMENT_SHELL
            ELEMENT_SHELL_THICKNESS
            ELEMENT_BEAM
            ELEMENT_MASS
            ELEMENT_MASS_NODE_SET
            NODE
            '''
            if "PART" in dynaKeywords:
                part = dynaKeywords["PART"]
                part.write(file)
            if "PART_COMPOSITE" in dynaKeywords:
                part_composite = dynaKeywords["PART_COMPOSITE"]
                part_composite.write(file)
            if "PART_CONTACT" in dynaKeywords:
                part_contact = dynaKeywords["PART_CONTACT"]
                part_contact.write(file)
            if "ELEMENT_SOLID" in dynaKeywords:
                element_solid = dynaKeywords["ELEMENT_SOLID"]
                element_solid.write(file)
            if "ELEMENT_SHELL" in dynaKeywords:
                element_shell = dynaKeywords["ELEMENT_SHELL"]
                element_shell.write(file)
            if "ELEMENT_SHELL_THICKNESS" in dynaKeywords:
                element_shell_thickness = dynaKeywords["ELEMENT_SHELL_THICKNESS"]
                element_shell_thickness.write(file)
            if "ELEMENT_BEAM" in dynaKeywords:
                element_beam = dynaKeywords["ELEMENT_BEAM"]
                element_beam.write(file)
            if "ELEMENT_MASS" in dynaKeywords:
                element_mass = dynaKeywords["ELEMENT_MASS"]
                element_mass.write(file)
            if "ELEMENT_MASS_NODE_SET" in dynaKeywords:
                element_mass_node_set = dynaKeywords["ELEMENT_MASS_NODE_SET"]
                element_mass_node_set.write(file)
            if "NODE" in dynaKeywords:
                node = dynaKeywords["NODE"]
                node.write(file)
            
            if len(meshKeywords) > 0:
                file.write(meshKeywords)
            '''
            #FREQUENCY
            FREQUENCY_DOMAIN_SSD
            '''
            if "FREQUENCY_DOMAIN_SSD" in dynaKeywords:
                frequency_domain_ssd = dynaKeywords["FREQUENCY_DOMAIN_SSD"]
                frequency_domain_ssd.write(file)

        
            file.write("*END\n")


    def ReadInputFile(self, outputFileName,writelog = True):
        os.chdir(self.currentDirectory)
        path = os.path.join(self.currentDirectory, self.inputFile)        
        # Initialize an empty list to store the lines
        lines_with_asterisk = []
        keyword_dict = {}
        
        
      
        lines_with_asterisk, keyword_dict = self.ReadKeywordsfromFile(path,lines_with_asterisk, keyword_dict)
        
        # remove duplicate keywords
        lines_with_asterisk_reduced = list(dict.fromkeys(lines_with_asterisk))
        if writelog:
            print("\n\nImported Keywords :")
            for keyword in lines_with_asterisk_reduced:
                print(keyword)
        self.keywordInterpreted = {}
        for keyword in lines_with_asterisk_reduced:
            self.keywordInterpreted[keyword] = False

        dynaKeywordMan = DynaKeywordManager()

        with open(outputFileName, 'w') as file:
            scipt = PreScript()
            scipt.write(file)
            if "TITLE" in lines_with_asterisk:
                #title = keywords["TITLE"]
                title = keyword_dict["TITLE"]
                t = Title()            
                t.parse(title)
                t.write(file)
                dynaKeywordMan.addKeyword(t)            
                while "TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("TITLE")            
            if "PARAMETER" in lines_with_asterisk:
                parameter = keyword_dict["PARAMETER"]
                p = Parameter()
                p.parse(parameter)
                p.write(file)
                dynaKeywordMan.addKeyword(p)
                while "PARAMETER" in lines_with_asterisk:
                    lines_with_asterisk.remove("PARAMETER")
            if "BOUNDARY_PRESCRIBED_MOTION_NODE" in lines_with_asterisk:
                boundary_prescribed_motion_node = keyword_dict["BOUNDARY_PRESCRIBED_MOTION_NODE"]
                bprescribed_motion_node = BoundaryPrescribedMotionNode()
                bprescribed_motion_node.parse(boundary_prescribed_motion_node)
                bprescribed_motion_node.write(file)
                dynaKeywordMan.addKeyword(bprescribed_motion_node)
                while "BOUNDARY_PRESCRIBED_MOTION_NODE" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_PRESCRIBED_MOTION_NODE")
            if "BOUNDARY_PRESCRIBED_MOTION_NODE_ID" in lines_with_asterisk:
                boundary_prescribed_motion_node_id = keyword_dict["BOUNDARY_PRESCRIBED_MOTION_NODE_ID"]
                bprescribed_motion_node_id = BoundaryPrescribedMotionNodeID()
                bprescribed_motion_node_id.parse(boundary_prescribed_motion_node_id)
                bprescribed_motion_node_id.write(file)
                dynaKeywordMan.addKeyword(bprescribed_motion_node_id)
                while "BOUNDARY_PRESCRIBED_MOTION_NODE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_PRESCRIBED_MOTION_NODE_ID")
            if "BOUNDARY_PRESCRIBED_MOTION_RIGID" in lines_with_asterisk:
                boundary_prescribed_motion_rigid = keyword_dict["BOUNDARY_PRESCRIBED_MOTION_RIGID"]
                bprescribed_motion_rigid = BoundaryPrescribedMotionRigid()
                bprescribed_motion_rigid.parse(boundary_prescribed_motion_rigid)
                bprescribed_motion_rigid.write(file)
                dynaKeywordMan.addKeyword(bprescribed_motion_rigid)
                while "BOUNDARY_PRESCRIBED_MOTION_RIGID" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_PRESCRIBED_MOTION_RIGID")
            if "BOUNDARY_PRESCRIBED_MOTION_RIGID_ID" in lines_with_asterisk:
                boundary_prescribed_motion_rigid_id = keyword_dict["BOUNDARY_PRESCRIBED_MOTION_RIGID_ID"]
                bprescribed_motion_rigid_id = BoundaryPrescribedMotionRigidID()
                bprescribed_motion_rigid_id.parse(boundary_prescribed_motion_rigid_id)
                bprescribed_motion_rigid_id.write(file)
                dynaKeywordMan.addKeyword(bprescribed_motion_rigid_id)
                while "BOUNDARY_PRESCRIBED_MOTION_RIGID_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_PRESCRIBED_MOTION_RIGID_ID")            
            if "BOUNDARY_PRESCRIBED_MOTION_SET" in lines_with_asterisk:
                boundary_prescribed_motion_set = keyword_dict["BOUNDARY_PRESCRIBED_MOTION_SET"]
                bprescribed_motion_set = BoundaryPrescribedMotionSet()
                bprescribed_motion_set.parse(boundary_prescribed_motion_set)
                bprescribed_motion_set.write(file)
                dynaKeywordMan.addKeyword(bprescribed_motion_set)
                while "BOUNDARY_PRESCRIBED_MOTION_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_PRESCRIBED_MOTION_SET")
            if "BOUNDARY_PRESCRIBED_MOTION_SET_ID" in lines_with_asterisk:
                boundary_prescribed_motion_set_id = keyword_dict["BOUNDARY_PRESCRIBED_MOTION_SET_ID"]
                bprescribed_motion_set_id = BoundaryPrescribedMotionSetID()
                bprescribed_motion_set_id.parse(boundary_prescribed_motion_set_id)
                bprescribed_motion_set_id.write(file)
                dynaKeywordMan.addKeyword(bprescribed_motion_set_id)
                while "BOUNDARY_PRESCRIBED_MOTION_SET_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_PRESCRIBED_MOTION_SET_ID")
            if "BOUNDARY_PZEPOT" in lines_with_asterisk:
                boundary_pzepot = keyword_dict["BOUNDARY_PZEPOT"]
                bpzepot = BoundaryPZEPOT()
                bpzepot.parse(boundary_pzepot)
                bpzepot.write(file)
                dynaKeywordMan.addKeyword(bpzepot)
                while "BOUNDARY_PZEPOT" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_PZEPOT")
            if "BOUNDARY_SPC_NODE" in lines_with_asterisk:
                boundary_spc_node = keyword_dict["BOUNDARY_SPC_NODE"]
                bspc_node = BoundarySPCNode()
                bspc_node.parse(boundary_spc_node)
                bspc_node.write(file)
                dynaKeywordMan.addKeyword(bspc_node)
                while "BOUNDARY_SPC_NODE" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_SPC_NODE")
            if "BOUNDARY_SPC_NODE_ID" in lines_with_asterisk:
                boundary_spc_node_id = keyword_dict["BOUNDARY_SPC_NODE_ID"]
                bspc_node_id = BoundarySPCNodeID()
                bspc_node_id.parse(boundary_spc_node_id)
                bspc_node_id.write(file)
                dynaKeywordMan.addKeyword(bspc_node_id)
                while "BOUNDARY_SPC_NODE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_SPC_NODE_ID")
            if "BOUNDARY_SPC_SET" in lines_with_asterisk:
                boundary_spc_set = keyword_dict["BOUNDARY_SPC_SET"]
                bspc_set = BoundarySPCSet()
                bspc_set.parse(boundary_spc_set)
                bspc_set.write(file)
                dynaKeywordMan.addKeyword(bspc_set)
                while "BOUNDARY_SPC_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_SPC_SET")
            if "BOUNDARY_SPC_SET_ID" in lines_with_asterisk:
                boundary_spc_sec_id = keyword_dict["BOUNDARY_SPC_SET_ID"]
                bspc_sec_id = BoundarySPCSetID()
                bspc_sec_id.parse(boundary_spc_sec_id)
                bspc_sec_id.write(file)
                dynaKeywordMan.addKeyword(bspc_sec_id)
                while "BOUNDARY_SPC_SET_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("BOUNDARY_SPC_SET_ID")
            print("Boundary Keywords Read Complete")
            if "CONSTRAINED_JOINT_SPHERICAL" in lines_with_asterisk:
                constrained_joint_spherical = keyword_dict["CONSTRAINED_JOINT_SPHERICAL"]
                cjoint_spherical = ConstrainedJointSpherical()
                cjoint_spherical.parse(constrained_joint_spherical)
                cjoint_spherical.write(file)
                dynaKeywordMan.addKeyword(cjoint_spherical)
                while "CONSTRAINED_JOINT_SPHERICAL" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_JOINT_SPHERICAL")            
            if "CONSTRAINED_JOINT_SPHERICAL_ID" in lines_with_asterisk:
                constrained_joint_spherical_id = keyword_dict["CONSTRAINED_JOINT_SPHERICAL_ID"]
                cjoint_spherical_id = ConstrainedJointSphericalID()     
                cjoint_spherical_id.parse(constrained_joint_spherical_id)
                cjoint_spherical_id.write(file)
                dynaKeywordMan.addKeyword(cjoint_spherical_id)
                while "CONSTRAINED_JOINT_SPHERICAL_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_JOINT_SPHERICAL_ID")    
            if "CONSTRAINED_NODAL_RIGID_BODY" in lines_with_asterisk:
                constrained_nodal_rigid_body = keyword_dict["CONSTRAINED_NODAL_RIGID_BODY"]
                cnode_rigid_body = ConstrainedNodalRigidBody()
                cnode_rigid_body.parse(constrained_nodal_rigid_body)
                cnode_rigid_body.write(file)
                dynaKeywordMan.addKeyword(cnode_rigid_body)
                while "CONSTRAINED_NODAL_RIGID_BODY" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_NODAL_RIGID_BODY")
            if "CONSTRAINED_NODAL_RIGID_BODY_TITLE" in lines_with_asterisk:
                constrained_nodal_rigid_body_title = keyword_dict["CONSTRAINED_NODAL_RIGID_BODY_TITLE"]
                cnode_rigid_body_title = ConstrainedNodalRigidBodyTitle()
                cnode_rigid_body_title.parse(constrained_nodal_rigid_body_title)
                cnode_rigid_body_title.write(file)
                dynaKeywordMan.addKeyword(cnode_rigid_body_title)
                while "CONSTRAINED_NODAL_RIGID_BODY_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_NODAL_RIGID_BODY_TITLE")                                
            if "CONSTRAINED_EXTRA_NODES_NODE" in lines_with_asterisk:
                constrained_extra_nodes_node = keyword_dict["CONSTRAINED_EXTRA_NODES_NODE"]
                cextra_nodes_node = ConstrainedExtraNodesNode()
                cextra_nodes_node.parse(constrained_extra_nodes_node)
                cextra_nodes_node.write(file)
                dynaKeywordMan.addKeyword(cextra_nodes_node)
                while "CONSTRAINED_EXTRA_NODES_NODE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_EXTRA_NODES_NODE")
            if "CONSTRAINED_EXTRA_NODES_SET" in lines_with_asterisk:
                constrained_extra_nodes_set = keyword_dict["CONSTRAINED_EXTRA_NODES_SET"]
                cextra_nodes_set = ConstrainedExtraNodesSet()
                cextra_nodes_set.parse(constrained_extra_nodes_set)
                cextra_nodes_set.write(file)
                dynaKeywordMan.addKeyword(cextra_nodes_set)
                while "CONSTRAINED_EXTRA_NODES_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_EXTRA_NODES_SET")
            if "CONSTRAINED_NODE_SET" in lines_with_asterisk:
                constrained_node_set = keyword_dict["CONSTRAINED_NODE_SET"]
                cnode_set = ConstrainedNodeSet()
                cnode_set.parse(constrained_node_set)
                cnode_set.write(file)
                dynaKeywordMan.addKeyword(cnode_set)
                while "CONSTRAINED_NODE_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_NODE_SET")            
            if "CONSTRAINED_NODE_SET_ID" in lines_with_asterisk:
                constrained_node_set_id = keyword_dict["CONSTRAINED_NODE_SET_ID"]
                cnode_set_id = ConstrainedNodeSetID()
                cnode_set_id.parse(constrained_node_set_id)
                cnode_set_id.write(file)
                dynaKeywordMan.addKeyword(cnode_set_id)
                while "CONSTRAINED_NODE_SET_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_NODE_SET_ID")
            if "CONSTRAINED_INTERPOLATION" in lines_with_asterisk:
                constrained_interpolation = keyword_dict["CONSTRAINED_INTERPOLATION"]
                cinterpolation = ConstrainedInterpolation()
                cinterpolation.parse(constrained_interpolation)
                cinterpolation.write(file)
                dynaKeywordMan.addKeyword(cinterpolation)
                while "CONSTRAINED_INTERPOLATION" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_INTERPOLATION")
            if "CONSTRAINED_RIGID_BODIES" in lines_with_asterisk:
                constrained_rigid_bodies = keyword_dict["CONSTRAINED_RIGID_BODIES"]
                crigid_bodies = ConstrainedRigidBodies()
                crigid_bodies.parse(constrained_rigid_bodies)
                crigid_bodies.write(file)
                dynaKeywordMan.addKeyword(crigid_bodies)
                while "CONSTRAINED_RIGID_BODIES" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_RIGID_BODIES")
            if "CONSTRAINED_RIGID_BODIES_SET" in lines_with_asterisk:
                constrained_rigid_bodies_set = keyword_dict["CONSTRAINED_RIGID_BODIES_SET"]
                crigid_bodies_set = ConstrainedRigidBodiesSet()
                crigid_bodies_set.parse(constrained_rigid_bodies_set)
                crigid_bodies_set.write(file)
                dynaKeywordMan.addKeyword(crigid_bodies_set)
                while "CONSTRAINED_RIGID_BODIES_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONSTRAINED_RIGID_BODIES_SET")
            print("Constrained Keywords Read Complete")
            if "CONTACT_ADD_WEAR" in lines_with_asterisk:
                contact_add_wear = keyword_dict["CONTACT_ADD_WEAR"]
                c_add_wear = ContactAddWear()
                c_add_wear.parse(contact_add_wear)
                c_add_wear.write(file)
                dynaKeywordMan.addKeyword(c_add_wear)
                while "CONTACT_ADD_WEAR" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ADD_WEAR")
            if "CONTACT_AUTOMATIC_SINGLE_SURFACE" in lines_with_asterisk:
                contact_automatic_single_surface = keyword_dict["CONTACT_AUTOMATIC_SINGLE_SURFACE"]
                cautomatic_single_surface = ContactAutomaticSingleSurface()
                cautomatic_single_surface.parse(contact_automatic_single_surface)
                cautomatic_single_surface.write(file)
                dynaKeywordMan.addKeyword(cautomatic_single_surface)
                while "CONTACT_AUTOMATIC_SINGLE_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_SINGLE_SURFACE")
            if "CONTACT_AUTOMATIC_SINGLE_SURFACE_ID" in lines_with_asterisk:
                contact_automatic_single_surface_id = keyword_dict["CONTACT_AUTOMATIC_SINGLE_SURFACE_ID"]
                cautomatic_single_surface_id = ContactAutomaticSingleSurfaceID()
                cautomatic_single_surface_id.parse(contact_automatic_single_surface_id)
                cautomatic_single_surface_id.write(file)
                dynaKeywordMan.addKeyword(cautomatic_single_surface_id)
                while "CONTACT_AUTOMATIC_SINGLE_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_SINGLE_SURFACE_ID")
            if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE" in lines_with_asterisk:
                contact_automatic_surface_to_surface = keyword_dict["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE"]
                cautomatic_surface_to_surface = ContactAutomaticSurfaceToSurface()
                cautomatic_surface_to_surface.parse(contact_automatic_surface_to_surface)
                cautomatic_surface_to_surface.write(file)
                dynaKeywordMan.addKeyword(cautomatic_surface_to_surface)
                while "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_SURFACE_TO_SURFACE")
            if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                contact_automatic_surface_to_surface_id = keyword_dict["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID"]
                cautomatic_surface_to_surface_id = ContactAutomaticSurfaceToSurfaceID()
                cautomatic_surface_to_surface_id.parse(contact_automatic_surface_to_surface_id)
                cautomatic_surface_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(cautomatic_surface_to_surface_id)
                while "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID")
            if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET" in lines_with_asterisk:
                contact_automatic_surface_to_surface_offset = keyword_dict["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET"]
                cautomatic_surface_to_surface_offset = ContactAutomaticSurfaceToSurfaceOffset()
                cautomatic_surface_to_surface_offset.parse(contact_automatic_surface_to_surface_offset)
                cautomatic_surface_to_surface_offset.write(file)
                dynaKeywordMan.addKeyword(cautomatic_surface_to_surface_offset)
                while "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET")
            if "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET_ID" in lines_with_asterisk:
                contact_automatic_surface_to_surface_offset_id = keyword_dict["CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET_ID"]
                cautomatic_surface_to_surface_offset_id = ContactAutomaticSurfaceToSurfaceOffsetID()
                cautomatic_surface_to_surface_offset_id.parse(contact_automatic_surface_to_surface_offset_id)
                cautomatic_surface_to_surface_offset_id.write(file)
                dynaKeywordMan.addKeyword(cautomatic_surface_to_surface_offset_id)
                while "CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_OFFSET_ID")                    
            if "CONTACT_AUTOMATIC_GENERAL" in lines_with_asterisk:
                contact_automatic_general = keyword_dict["CONTACT_AUTOMATIC_GENERAL"]
                cautomatic_general = ContactAutomaticGeneral()
                cautomatic_general.parse(contact_automatic_general)
                cautomatic_general.write(file)
                dynaKeywordMan.addKeyword(cautomatic_general)
                while "CONTACT_AUTOMATIC_GENERAL" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_GENERAL")
            if "CONTACT_AUTOMATIC_GENERAL_ID" in lines_with_asterisk:
                contact_automatic_general_id = keyword_dict["CONTACT_AUTOMATIC_GENERAL_ID"]
                cautomatic_general_id = ContactAutomaticGeneralID()
                cautomatic_general_id.parse(contact_automatic_general_id)
                cautomatic_general_id.write(file)
                dynaKeywordMan.addKeyword(cautomatic_general_id)
                while "CONTACT_AUTOMATIC_GENERAL_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_GENERAL_ID")
            if "CONTACT_AUTOMATIC_NODES_TO_SURFACE" in lines_with_asterisk:
                contact_automatic_nodes_to_surface = keyword_dict["CONTACT_AUTOMATIC_NODES_TO_SURFACE"]
                cautomatic_nodes_to_surface = ContactAutomaticNodesToSurface()
                cautomatic_nodes_to_surface.parse(contact_automatic_nodes_to_surface)
                cautomatic_nodes_to_surface.write(file)
                dynaKeywordMan.addKeyword(cautomatic_nodes_to_surface)
                while "CONTACT_AUTOMATIC_NODES_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_NODES_TO_SURFACE")
            if "CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID" in lines_with_asterisk:
                contact_automatic_nodes_to_surface_id = keyword_dict["CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID"]
                cautomatic_nodes_to_surface_id = ContactAutomaticNodesToSurfaceID()
                cautomatic_nodes_to_surface_id.parse(contact_automatic_nodes_to_surface_id)
                cautomatic_nodes_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(cautomatic_nodes_to_surface_id)
                while "CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_AUTOMATIC_NODES_TO_SURFACE_ID")                
            if "CONTACT_FEM_PERI_TIE_BREAK_ID" in lines_with_asterisk:
                contact_fem_peri_tie_break_id = keyword_dict["CONTACT_FEM_PERI_TIE_BREAK_ID"]
                cfem_peri_tie_break_id = ContactFEMPERITieBreakID()
                cfem_peri_tie_break_id.parse(contact_fem_peri_tie_break_id)
                cfem_peri_tie_break_id.write(file)
                dynaKeywordMan.addKeyword(cfem_peri_tie_break_id)
                while "CONTACT_FEM_PERI_TIE_BREAK_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_FEM_PERI_TIE_BREAK_ID")
            if "CONTACT_NODES_TO_SURFACE" in lines_with_asterisk:
                contact_nodes_to_surface = keyword_dict["CONTACT_NODES_TO_SURFACE"]
                cnodes_to_surface = ContactNodesToSurface()
                cnodes_to_surface.parse(contact_nodes_to_surface)
                cnodes_to_surface.write(file)
                dynaKeywordMan.addKeyword(cnodes_to_surface)
                while "CONTACT_NODES_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_NODES_TO_SURFACE")
            if "CONTACT_NODES_TO_SURFACE_ID" in lines_with_asterisk:
                contact_nodes_to_surface_id = keyword_dict["CONTACT_NODES_TO_SURFACE_ID"]
                cnodes_to_surface_id = ContactNodesToSurfaceID()
                cnodes_to_surface_id.parse(contact_nodes_to_surface_id)
                cnodes_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(cnodes_to_surface_id)
                while "CONTACT_NODES_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_NODES_TO_SURFACE_ID")
            if "CONTACT_ONE_WAY_SURFACE_TO_SURFACE" in lines_with_asterisk:
                contact_one_way_surface_to_surface = keyword_dict["CONTACT_ONE_WAY_SURFACE_TO_SURFACE"]
                cone_way_surface_to_surface = ContactOneWaySurfaceToSurface()
                cone_way_surface_to_surface.parse(contact_one_way_surface_to_surface)
                cone_way_surface_to_surface.write(file)
                dynaKeywordMan.addKeyword(cone_way_surface_to_surface)
                while "CONTACT_ONE_WAY_SURFACE_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ONE_WAY_SURFACE_TO_SURFACE")
            if "CONTACT_ONE_WAY_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                contact_one_way_surface_to_surface_id = keyword_dict["CONTACT_ONE_WAY_SURFACE_TO_SURFACE_ID"]
                cone_way_surface_to_surface_id = ContactOneWaySurfaceToSurfaceID()
                cone_way_surface_to_surface_id.parse(contact_one_way_surface_to_surface_id)
                cone_way_surface_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(cone_way_surface_to_surface_id)
                while "CONTACT_ONE_WAY_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ONE_WAY_SURFACE_TO_SURFACE_ID")
            if "CONTACT_SINGLE_SURFACE" in lines_with_asterisk:
                contact_single_surface = keyword_dict["CONTACT_SINGLE_SURFACE"]
                csingle_surface = ContactSingleSurface()
                csingle_surface.parse(contact_single_surface)
                csingle_surface.write(file)
                dynaKeywordMan.addKeyword(csingle_surface)
                while "CONTACT_SINGLE_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_SINGLE_SURFACE")
            if "CONTACT_SINGLE_SURFACE_ID" in lines_with_asterisk:
                contact_single_surface_id = keyword_dict["CONTACT_SINGLE_SURFACE_ID"]
                csingle_surface_id = ContactSingleSurfaceID()
                csingle_surface_id.parse(contact_single_surface_id)
                csingle_surface_id.write(file)
                dynaKeywordMan.addKeyword(csingle_surface_id)
                while "CONTACT_SINGLE_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_SINGLE_SURFACE_ID")
            if "CONTACT_SURFACE_TO_SURFACE" in lines_with_asterisk:
                contact_surface_to_surface = keyword_dict["CONTACT_SURFACE_TO_SURFACE"]
                csurface_to_surface = ContactSurfaceToSurface()
                csurface_to_surface.parse(contact_surface_to_surface)
                csurface_to_surface.write(file)
                dynaKeywordMan.addKeyword(csurface_to_surface)
                while "CONTACT_SURFACE_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_SURFACE_TO_SURFACE")
            if "CONTACT_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                contact_surface_to_surface_id = keyword_dict["CONTACT_SURFACE_TO_SURFACE_ID"]
                csurface_to_surface_id = ContactSurfaceToSurfaceID()
                csurface_to_surface_id.parse(contact_surface_to_surface_id)
                csurface_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(csurface_to_surface_id)
                while "CONTACT_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_SURFACE_TO_SURFACE_ID")
            if "CONTACT_SURFACE_TO_SURFACE_INTERFERENCE" in lines_with_asterisk:
                contact_surface_to_surface_interference = keyword_dict["CONTACT_SURFACE_TO_SURFACE_INTERFERENCE"]
                cinterference = ContactSurfaceToSurfaceInterference()
                cinterference.parse(contact_surface_to_surface_interference)
                cinterference.write(file)
                dynaKeywordMan.addKeyword(cinterference)
                while "CONTACT_SURFACE_TO_SURFACE_INTERFERENCE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_SURFACE_TO_SURFACE_INTERFERENCE")                    
            if "CONTACT_SURFACE_TO_SURFACE_INTERFERENCE_ID" in lines_with_asterisk:
                contact_surface_to_surface_interference_id = keyword_dict["CONTACT_SURFACE_TO_SURFACE_INTERFERENCE_ID"]
                cinterference_id = ContactSurfaceToSurfaceInterferenceID()
                cinterference_id.parse(contact_surface_to_surface_interference_id)
                cinterference_id.write(file)
                dynaKeywordMan.addKeyword(cinterference_id)
                while "CONTACT_SURFACE_TO_SURFACE_INTERFERENCE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_SURFACE_TO_SURFACE_INTERFERENCE_ID")
            if "CONTACT_TIED_NODES_TO_SURFACE" in lines_with_asterisk:
                contact_tied_nodes_to_surface = keyword_dict["CONTACT_TIED_NODES_TO_SURFACE"]
                ctied_nodes_to_surface = ContactTiedNodesToSurface()
                ctied_nodes_to_surface.parse(contact_tied_nodes_to_surface)
                ctied_nodes_to_surface.write(file)
                dynaKeywordMan.addKeyword(ctied_nodes_to_surface)
                while "CONTACT_TIED_NODES_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_NODES_TO_SURFACE")
            if "CONTACT_TIED_NODES_TO_SURFACE_ID" in lines_with_asterisk:
                contact_tied_nodes_to_surface_id = keyword_dict["CONTACT_TIED_NODES_TO_SURFACE_ID"]
                ctied_nodes_to_surface_id = ContactTiedNodesToSurfaceID()
                ctied_nodes_to_surface_id.parse(contact_tied_nodes_to_surface_id)
                ctied_nodes_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(ctied_nodes_to_surface_id)
                while "CONTACT_TIED_NODES_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_NODES_TO_SURFACE_ID")
            if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE" in lines_with_asterisk:
                contact_tied_shell_edge_to_surface = keyword_dict["CONTACT_TIED_SHELL_EDGE_TO_SURFACE"]
                ctied_shell_edge_to_surface = ContactTiedShellEdgeToSurface()
                ctied_shell_edge_to_surface.parse(contact_tied_shell_edge_to_surface)
                ctied_shell_edge_to_surface.write(file)
                dynaKeywordMan.addKeyword(ctied_shell_edge_to_surface)
                while "CONTACT_TIED_SHELL_EDGE_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SHELL_EDGE_TO_SURFACE")
            if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_ID" in lines_with_asterisk:
                contact_tied_shell_edge_to_surface_id = keyword_dict["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_ID"]
                ctied_shell_edge_to_surface_id = ContactTiedShellEdgeToSurfaceID()
                ctied_shell_edge_to_surface_id.parse(contact_tied_shell_edge_to_surface_id)
                ctied_shell_edge_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(ctied_shell_edge_to_surface_id)
                while "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SHELL_EDGE_TO_SURFACE_ID")
            if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET" in lines_with_asterisk:
                contact_tied_shell_edge_to_surface_beam_offset = keyword_dict["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET"]
                ctied_shell_edge_to_surface_beam_offset = ContactTiedShellEdgeToSurfaceBeamOffset()
                ctied_shell_edge_to_surface_beam_offset.parse(contact_tied_shell_edge_to_surface_beam_offset)
                ctied_shell_edge_to_surface_beam_offset.write(file)
                dynaKeywordMan.addKeyword(ctied_shell_edge_to_surface_beam_offset)
                while "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET")
            if "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID" in lines_with_asterisk:  
                contact_tied_shell_edge_to_surface_beam_offset_id = keyword_dict["CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID"]
                ctied_shell_edge_to_surface_beam_offset_id = ContactTiedShellEdgeToSurfaceBeamOffsetID()
                ctied_shell_edge_to_surface_beam_offset_id.parse(contact_tied_shell_edge_to_surface_beam_offset_id)
                ctied_shell_edge_to_surface_beam_offset_id.write(file)
                dynaKeywordMan.addKeyword(ctied_shell_edge_to_surface_beam_offset_id)
                while "CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SHELL_EDGE_TO_SURFACE_BEAM_OFFSET_ID")                                        
            if "CONTACT_TIED_SURFACE_TO_SURFACE" in lines_with_asterisk:
                contact_tied_surface_to_surface = keyword_dict["CONTACT_TIED_SURFACE_TO_SURFACE"]
                ctied_surface_to_surface = ContactTiedSurfaceToSurface()
                ctied_surface_to_surface.parse(contact_tied_surface_to_surface)
                ctied_surface_to_surface.write(file)
                dynaKeywordMan.addKeyword(ctied_surface_to_surface)
                while "CONTACT_TIED_SURFACE_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SURFACE_TO_SURFACE")
            if "CONTACT_TIED_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                contact_tied_surface_to_surface_id = keyword_dict["CONTACT_TIED_SURFACE_TO_SURFACE_ID"]
                ctied_surface_to_surface_id = ContactTiedSurfaceToSurfaceID()
                ctied_surface_to_surface_id.parse(contact_tied_surface_to_surface_id)
                ctied_surface_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(ctied_surface_to_surface_id)
                while "CONTACT_TIED_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SURFACE_TO_SURFACE_ID")                        
            if "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET" in lines_with_asterisk:
                contact_tied_surface_to_surface_offset = keyword_dict["CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET"]
                ctied_surface_to_surface_offset = ContactTiedSurfaceToSurfaceOffset()
                ctied_surface_to_surface_offset.parse(contact_tied_surface_to_surface_offset)
                ctied_surface_to_surface_offset.write(file)
                dynaKeywordMan.addKeyword(ctied_surface_to_surface_offset)
                while "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET")
            if "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID" in lines_with_asterisk:
                contact_tied_surface_to_surface_offset_id = keyword_dict["CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID"]
                ctied_surface_to_surface_offset_id = ContactTiedSurfaceToSurfaceOffsetID()
                ctied_surface_to_surface_offset_id.parse(contact_tied_surface_to_surface_offset_id)
                ctied_surface_to_surface_offset_id.write(file)
                dynaKeywordMan.addKeyword(ctied_surface_to_surface_offset_id)
                while "CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SURFACE_TO_SURFACE_OFFSET_ID")                    
            if "CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET" in lines_with_asterisk:
                contact_tied_surface_to_surface_constrained_offset = keyword_dict["CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET"]
                ctied_surface_to_surface_constrained_offset = ContactTiedSurfaceToSurfaceConstrainedOffset()
                ctied_surface_to_surface_constrained_offset.parse(contact_tied_surface_to_surface_constrained_offset)
                ctied_surface_to_surface_constrained_offset.write(file)
                dynaKeywordMan.addKeyword(ctied_surface_to_surface_constrained_offset)
                while "CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET")
            if "CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID" in lines_with_asterisk:
                contact_tied_surface_to_surface_constrained_offset_id = keyword_dict["CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID"]
                ctied_surface_to_surface_constrained_offset_id = ContactTiedSurfaceToSurfaceConstrainedOffsetID()
                ctied_surface_to_surface_constrained_offset_id.parse(contact_tied_surface_to_surface_constrained_offset_id)
                ctied_surface_to_surface_constrained_offset_id.write(file)
                dynaKeywordMan.addKeyword(ctied_surface_to_surface_constrained_offset_id)
                while "CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID")                                        
            if "CONTACT_ERODING_NODES_TO_SURFACE" in lines_with_asterisk:
                contact_eroding_nodes_to_surface = keyword_dict["CONTACT_ERODING_NODES_TO_SURFACE"]
                ceroding_nodes_to_surface = ContactErodingNodesToSurface()
                ceroding_nodes_to_surface.parse(contact_eroding_nodes_to_surface)
                ceroding_nodes_to_surface.write(file)
                dynaKeywordMan.addKeyword(ceroding_nodes_to_surface)                
                while "CONTACT_ERODING_NODES_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ERODING_NODES_TO_SURFACE")
            if "CONTACT_ERODING_NODES_TO_SURFACE_ID" in lines_with_asterisk:
                contact_eroding_nodes_to_surface_id = keyword_dict["CONTACT_ERODING_NODES_TO_SURFACE_ID"]
                ceroding_nodes_to_surface_id = ContactErodingNodesToSurfaceID()
                ceroding_nodes_to_surface_id.parse(contact_eroding_nodes_to_surface_id)
                ceroding_nodes_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(ceroding_nodes_to_surface_id)
                while "CONTACT_ERODING_NODES_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ERODING_NODES_TO_SURFACE_ID")
            if "CONTACT_ERODING_SINGLE_SURFACE" in lines_with_asterisk:
                contact_eroding_single_surface = keyword_dict["CONTACT_ERODING_SINGLE_SURFACE"]
                ceroding_single_surface = ContactErodingSingleSurface()
                ceroding_single_surface.parse(contact_eroding_single_surface)
                ceroding_single_surface.write(file)
                dynaKeywordMan.addKeyword(ceroding_single_surface)
                while "CONTACT_ERODING_SINGLE_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ERODING_SINGLE_SURFACE")
            if "CONTACT_ERODING_SINGLE_SURFACE_ID" in lines_with_asterisk:
                contact_eroding_single_surface_id = keyword_dict["CONTACT_ERODING_SINGLE_SURFACE_ID"]
                ceroding_single_surface_id = ContactErodingSingleSurfaceID()
                ceroding_single_surface_id.parse(contact_eroding_single_surface_id)
                ceroding_single_surface_id.write(file)
                dynaKeywordMan.addKeyword(ceroding_single_surface_id)
                while "CONTACT_ERODING_SINGLE_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ERODING_SINGLE_SURFACE_ID")
            if "CONTACT_ERODING_SURFACE_TO_SURFACE" in lines_with_asterisk:
                contact_eroding_surface_to_surface = keyword_dict["CONTACT_ERODING_SURFACE_TO_SURFACE"]
                ceroding_surface_to_surface = ContactErodingSurfaceToSurface()
                ceroding_surface_to_surface.parse(contact_eroding_surface_to_surface)
                ceroding_surface_to_surface.write(file)
                dynaKeywordMan.addKeyword(ceroding_surface_to_surface)
                while "CONTACT_ERODING_SURFACE_TO_SURFACE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ERODING_SURFACE_TO_SURFACE")
            if "CONTACT_ERODING_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                contact_eroding_surface_to_surface_id = keyword_dict["CONTACT_ERODING_SURFACE_TO_SURFACE_ID"]
                ceroding_surface_to_surface_id = ContactErodingSurfaceToSurfaceID()
                ceroding_surface_to_surface_id.parse(contact_eroding_surface_to_surface_id)
                ceroding_surface_to_surface_id.write(file)
                dynaKeywordMan.addKeyword(ceroding_surface_to_surface_id)
                while "CONTACT_ERODING_SURFACE_TO_SURFACE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ERODING_SURFACE_TO_SURFACE_ID")
            if "CONTACT_ERODING_SURFACE_TO_SURFACE_TITLE" in lines_with_asterisk:
                contact_eroding_surface_to_surface_title = keyword_dict["CONTACT_ERODING_SURFACE_TO_SURFACE_TITLE"]
                ceroding_surface_to_surface_title = ContactErodingSurfaceToSurfaceTitle()
                ceroding_surface_to_surface_title.parse(contact_eroding_surface_to_surface_title)
                ceroding_surface_to_surface_title.write(file)
                dynaKeywordMan.addKeyword(ceroding_surface_to_surface_title)
                while "CONTACT_ERODING_SURFACE_TO_SURFACE_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_ERODING_SURFACE_TO_SURFACE_TITLE")
            if "CONTACT_FORCE_TRANSDUCER_PENALTY" in lines_with_asterisk:
                contact_force_transducer_penalty = keyword_dict["CONTACT_FORCE_TRANSDUCER_PENALTY"]
                cforce_transducer_penalty = ContactForceTransducerPenalty()
                cforce_transducer_penalty.parse(contact_force_transducer_penalty)
                cforce_transducer_penalty.write(file)
                dynaKeywordMan.addKeyword(cforce_transducer_penalty)
                while "CONTACT_FORCE_TRANSDUCER_PENALTY" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_FORCE_TRANSDUCER_PENALTY")
            if "CONTACT_FORCE_TRANSDUCER_PENALTY_ID" in lines_with_asterisk:
                contact_force_transducer_penalty_id = keyword_dict["CONTACT_FORCE_TRANSDUCER_PENALTY_ID"]
                cforce_transducer_penalty_id = ContactForceTransducerPenaltyID()
                cforce_transducer_penalty_id.parse(contact_force_transducer_penalty_id)
                cforce_transducer_penalty_id.write(file)
                dynaKeywordMan.addKeyword(cforce_transducer_penalty_id)
                while "CONTACT_FORCE_TRANSDUCER_PENALTY_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_FORCE_TRANSDUCER_PENALTY_ID")
            if "CONTACT_SLIDING_ONLY" in lines_with_asterisk:
                contact_sliding_only = keyword_dict["CONTACT_SLIDING_ONLY"]
                csliding_only = ContactSlidingOnly()
                csliding_only.parse(contact_sliding_only)
                csliding_only.write(file)
                dynaKeywordMan.addKeyword(csliding_only)
                while "CONTACT_SLIDING_ONLY" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTACT_SLIDING_ONLY")
            print("Contact Keywords Read Complete")
            if "CONTROL_ACCURACY" in lines_with_asterisk:   
            # control_accuracy = keywords["CONTROL_ACCURACY"]
                control_accuracy = keyword_dict["CONTROL_ACCURACY"]
                cacc = ControlAccuracy()
                cacc.parse(control_accuracy)
                cacc.write(file)
                dynaKeywordMan.addKeyword(cacc)
                while "CONTROL_ACCURACY" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_ACCURACY")        
            if "CONTROL_ADAPT" in lines_with_asterisk:
                control_adapt = keyword_dict["CONTROL_ADAPT"]
                cadapt = ControlAdapt()
                cadapt.parse(control_adapt)
                cadapt.write(file)
                dynaKeywordMan.addKeyword(cadapt)
                while "CONTROL_ADAPT" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_ADAPT")
            if "CONTROL_ADAPTIVE" in lines_with_asterisk:
                control_adaptive = keyword_dict["CONTROL_ADAPTIVE"]
                cadaptive = ControlAdaptive()
                cadaptive.parse(control_adaptive)
                cadaptive.write(file)
                dynaKeywordMan.addKeyword(cadaptive)
                while "CONTROL_ADAPTIVE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_ADAPTIVE")
            if "CONTROL_ALE" in lines_with_asterisk:
                control_ale = keyword_dict["CONTROL_ALE"]
                cale = ControlALE()
                cale.parse(control_ale)
                cale.write(file)
                dynaKeywordMan.addKeyword(cale)
                while "CONTROL_ALE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_ALE")
            if "CONTROL_BULK_VISCOSITY" in lines_with_asterisk:
                #control_bulk_viscosity = keywords["CONTROL_BULK_VISCOSITY"]
                control_bulk_viscosity = keyword_dict["CONTROL_BULK_VISCOSITY"]
                cbviscosity = ControlBulkViscosity()
                cbviscosity.parse(control_bulk_viscosity)
                cbviscosity.write(file)
                dynaKeywordMan.addKeyword(cbviscosity)
                while "CONTROL_BULK_VISCOSITY" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_BULK_VISCOSITY")            
            if "CONTROL_CONTACT" in lines_with_asterisk:
                control_contact = keyword_dict["CONTROL_CONTACT"]
                ccontact = ControlContact()
                ccontact.parse(control_contact)
                ccontact.write(file)
                dynaKeywordMan.addKeyword(ccontact)
                while "CONTROL_CONTACT" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_CONTACT")
            if "CONTROL_CPU" in lines_with_asterisk:
                control_cpu = keyword_dict["CONTROL_CPU"]
                ccpu = ControlCPU()
                ccpu.parse(control_cpu)
                ccpu.write(file)
                dynaKeywordMan.addKeyword(ccpu)
                while "CONTROL_CPU" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_CPU")
            if "CONTROL_DYNAMIC_RELAXATION" in lines_with_asterisk:
                control_dynamic_relaxation = keyword_dict["CONTROL_DYNAMIC_RELAXATION"]
                cdynamic_relaxation = ControlDynamicRelaxation()
                cdynamic_relaxation.parse(control_dynamic_relaxation)
                cdynamic_relaxation.write(file)
                dynaKeywordMan.addKeyword(cdynamic_relaxation)
                while "CONTROL_DYNAMIC_RELAXATION" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_DYNAMIC_RELAXATION")
            if "CONTROL_ENERGY" in lines_with_asterisk:
                control_energy = keyword_dict["CONTROL_ENERGY"]
                cenergy = ControlEnergy()
                cenergy.parse(control_energy)
                cenergy.write(file)
                dynaKeywordMan.addKeyword(cenergy)
                while "CONTROL_ENERGY" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_ENERGY")
            if "CONTROL_HOURGLASS" in lines_with_asterisk:
                control_hourglass = keyword_dict["CONTROL_HOURGLASS"]
                chourglass = ControlHourglass()
                chourglass.parse(control_hourglass)
                chourglass.write(file)
                dynaKeywordMan.addKeyword(chourglass)
                while "CONTROL_HOURGLASS" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_HOURGLASS")
            if "CONTROL_IMPLICIT_AUTO" in lines_with_asterisk:
                control_implicit_auto = keyword_dict["CONTROL_IMPLICIT_AUTO"]
                cimplicit_auto = ControlImplicitAuto()
                cimplicit_auto.parse(control_implicit_auto)
                cimplicit_auto.write(file)
                dynaKeywordMan.addKeyword(cimplicit_auto)
                while "CONTROL_IMPLICIT_AUTO" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_IMPLICIT_AUTO")
            if "CONTROL_IMPLICIT_DYNAMICS" in lines_with_asterisk:
                control_implicit_dynamics = keyword_dict["CONTROL_IMPLICIT_DYNAMICS"]
                cimplicit_dynamics = ControlImplicitDynamics()
                cimplicit_dynamics.parse(control_implicit_dynamics)
                cimplicit_dynamics.write(file)
                dynaKeywordMan.addKeyword(cimplicit_dynamics)
                while "CONTROL_IMPLICIT_DYNAMICS" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_IMPLICIT_DYNAMICS")
            if "CONTROL_IMPLICIT_EIGENVALUE" in lines_with_asterisk:
                control_implicit_eigenvalue = keyword_dict["CONTROL_IMPLICIT_EIGENVALUE"]
                cimplicit_eigenvalue = ControlImplicitEigenvalue()
                cimplicit_eigenvalue.parse(control_implicit_eigenvalue)
                cimplicit_eigenvalue.write(file)
                dynaKeywordMan.addKeyword(cimplicit_eigenvalue)
                while "CONTROL_IMPLICIT_EIGENVALUE" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_IMPLICIT_EIGENVALUE")
            if "CONTROL_IMPLICIT_GENERAL" in lines_with_asterisk:
                control_implicit_general = keyword_dict["CONTROL_IMPLICIT_GENERAL"]
                cimplicit_general = ControlImplicitGeneral()
                cimplicit_general.parse(control_implicit_general)
                cimplicit_general.write(file)
                dynaKeywordMan.addKeyword(cimplicit_general)
                while "CONTROL_IMPLICIT_GENERAL" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_IMPLICIT_GENERAL")
            if "CONTROL_IMPLICIT_SOLUTION" in lines_with_asterisk:
                control_implicit_solution = keyword_dict["CONTROL_IMPLICIT_SOLUTION"]
                cimplicit_solution = ControlImplicitSolution()
                cimplicit_solution.parse(control_implicit_solution)
                cimplicit_solution.write(file)
                dynaKeywordMan.addKeyword(cimplicit_solution)
                while "CONTROL_IMPLICIT_SOLUTION" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_IMPLICIT_SOLUTION")
            if "CONTROL_IMPLICIT_SOLVER" in lines_with_asterisk:
                control_implicit_solver = keyword_dict["CONTROL_IMPLICIT_SOLVER"]
                cimplicit_solver = ControlImplicitSolver()
                cimplicit_solver.parse(control_implicit_solver)
                cimplicit_solver.write(file)
                dynaKeywordMan.addKeyword(cimplicit_solver)
                while "CONTROL_IMPLICIT_SOLVER" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_IMPLICIT_SOLVER")            
            if "CONTROL_MPP_IO_NODUMP" in lines_with_asterisk:
                cmpp_nodump = ControlMppIoNodump()
                cmpp_nodump.write(file)
                dynaKeywordMan.addKeyword(cmpp_nodump)
                while "CONTROL_MPP_IO_NODUMP" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_MPP_IO_NODUMP")
            if "CONTROL_OUTPUT" in lines_with_asterisk:
                control_output = keyword_dict["CONTROL_OUTPUT"]
                cout = ControlOutput()
                cout.parse(control_output)
                cout.write(file)
                dynaKeywordMan.addKeyword(cout)
                while "CONTROL_OUTPUT" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_OUTPUT")
            if "CONTROL_RIGID" in lines_with_asterisk:
                control_rigid = keyword_dict["CONTROL_RIGID"]
                crigid = ControlRigid()
                crigid.parse(control_rigid)
                crigid.write(file)
                dynaKeywordMan.addKeyword(crigid)
                while "CONTROL_RIGID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_RIGID")
            if "CONTROL_PARALLEL" in lines_with_asterisk:
                control_parallel = keyword_dict["CONTROL_PARALLEL"]
                cparallel = ControlParallel()
                cparallel.parse(control_parallel)
                cparallel.write(file)
                dynaKeywordMan.addKeyword(cparallel)
                while "CONTROL_PARALLEL" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_PARALLEL")
            if "CONTROL_SHELL" in lines_with_asterisk:
                control_shell = keyword_dict["CONTROL_SHELL"]
                cshell = ControlShell()
                cshell.parse(control_shell)
                cshell.write(file)
                dynaKeywordMan.addKeyword(cshell)
                while "CONTROL_SHELL" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_SHELL")
            if "CONTROL_SOLID" in lines_with_asterisk:
                control_solid = keyword_dict["CONTROL_SOLID"]
                csolid = ControlSolid()
                csolid.parse(control_solid)
                csolid.write(file)
                dynaKeywordMan.addKeyword(csolid)
                while "CONTROL_SOLID" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_SOLID")
            if "CONTROL_SOLUTION" in lines_with_asterisk:
                control_solution = keyword_dict["CONTROL_SOLUTION"]
                csolution = ControlSolution()
                csolution.parse(control_solution)
                csolution.write(file)
                dynaKeywordMan.addKeyword(csolution)
                while "CONTROL_SOLUTION" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_SOLUTION")            
            if "CONTROL_TERMINATION" in lines_with_asterisk:
                control_termination = keyword_dict["CONTROL_TERMINATION"]         
                cterm = ControlTermination()
                cterm.parse(control_termination)
                cterm.write(file)
                dynaKeywordMan.addKeyword(cterm)
                while "CONTROL_TERMINATION" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_TERMINATION")
            if "CONTROL_TIMESTEP" in lines_with_asterisk:
                control_timestep = keyword_dict["CONTROL_TIMESTEP"]
                ctime = ControlTimeStep()
                ctime.parse(control_timestep)
                ctime.write(file)
                dynaKeywordMan.addKeyword(ctime)
                while "CONTROL_TIMESTEP" in lines_with_asterisk:
                    lines_with_asterisk.remove("CONTROL_TIMESTEP")                            
            print("Control Keywords Read Complete")
            if "DAMPING_GLOBAL" in lines_with_asterisk:
                damping_global = keyword_dict["DAMPING_GLOBAL"]
                dglobal = DampingGlobal()
                dglobal.parse(damping_global)
                dglobal.write(file)
                dynaKeywordMan.addKeyword(dglobal)
                while "DAMPING_GLOBAL" in lines_with_asterisk:
                    lines_with_asterisk.remove("DAMPING_GLOBAL")
            if "DAMPING_PART_MASS" in lines_with_asterisk:
                damping_part_mass = keyword_dict["DAMPING_PART_MASS"]
                dpart_mass = DampingPartMass()
                dpart_mass.parse(damping_part_mass)
                dpart_mass.write(file)
                dynaKeywordMan.addKeyword(dpart_mass)
                while "DAMPING_PART_MASS" in lines_with_asterisk:
                    lines_with_asterisk.remove("DAMPING_PART_MASS")
            if "DAMPING_PART_MASS_SET" in lines_with_asterisk:
                damping_part_mass_set = keyword_dict["DAMPING_PART_MASS_SET"]
                dpart_mass_set = DampingPartMassSet()
                dpart_mass_set.parse(damping_part_mass_set)
                dpart_mass_set.write(file)
                dynaKeywordMan.addKeyword(dpart_mass_set)
                while "DAMPING_PART_MASS_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("DAMPING_PART_MASS_SET")
            if "DAMPING_PART_STIFFNESS" in lines_with_asterisk:
                damping_part_stiffness = keyword_dict["DAMPING_PART_STIFFNESS"]
                dpart_stiffness = DampingPartStiffness()
                dpart_stiffness.parse(damping_part_stiffness)
                dpart_stiffness.write(file)
                dynaKeywordMan.addKeyword(dpart_stiffness)
                while "DAMPING_PART_STIFFNESS" in lines_with_asterisk:
                    lines_with_asterisk.remove("DAMPING_PART_STIFFNESS")                    
            if "DAMPING_PART_STIFFNESS_SET" in lines_with_asterisk:
                damping_part_stiffness_set = keyword_dict["DAMPING_PART_STIFFNESS_SET"]
                dpart_stiffness_set = DampingPartStiffnessSet()
                dpart_stiffness_set.parse(damping_part_stiffness_set)
                dpart_stiffness_set.write(file)
                dynaKeywordMan.addKeyword(dpart_stiffness_set)
                while "DAMPING_PART_STIFFNESS_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("DAMPING_PART_STIFFNESS_SET")
            print("Damping Keywords Read Complete")
            if "DATABASE_BNDOUT" in lines_with_asterisk:
                database_bndout = keyword_dict["DATABASE_BNDOUT"]
                dbndout = DatabaseBndout()
                dbndout.parse(database_bndout)
                dbndout.write(file)
                dynaKeywordMan.addKeyword(dbndout)
                while "DATABASE_BNDOUT" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_BNDOUT")
            if "DATABASE_CROSS_SECTION_SET" in lines_with_asterisk:
                database_cross_section_set = keyword_dict["DATABASE_CROSS_SECTION_SET"]
                dbcsset = DatabaseCrossSectionSet()
                dbcsset.parse(database_cross_section_set)
                dbcsset.write(file)
                dynaKeywordMan.addKeyword(dbcsset)
                while "DATABASE_CROSS_SECTION_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_CROSS_SECTION_SET")
            if "DATABASE_CROSS_SECTION_SET_ID" in lines_with_asterisk:
                database_cross_section_set_id = keyword_dict["DATABASE_CROSS_SECTION_SET_ID"]
                dbcsset_id = DatabaseCrossSectionSetID()
                dbcsset_id.parse(database_cross_section_set_id)
                dbcsset_id.write(file)
                dynaKeywordMan.addKeyword(dbcsset_id)
                while "DATABASE_CROSS_SECTION_SET_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_CROSS_SECTION_SET_ID")
            if "DATABASE_CROSS_SECTION_PLANE" in lines_with_asterisk:
                database_cross_section_plane = keyword_dict["DATABASE_CROSS_SECTION_PLANE"]
                dbcsplane = DatabaseCrossSectionPlane()
                dbcsplane.parse(database_cross_section_plane)
                dbcsplane.write(file)
                dynaKeywordMan.addKeyword(dbcsplane)
                while "DATABASE_CROSS_SECTION_PLANE" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_CROSS_SECTION_PLANE")
            if "DATABASE_CROSS_SECTION_PLANE_ID" in lines_with_asterisk:
                database_cross_section_plane_id = keyword_dict["DATABASE_CROSS_SECTION_PLANE_ID"]
                dbcsplane_id = DatabaseCrossSectionPlaneID()
                dbcsplane_id.parse(database_cross_section_plane_id)
                dbcsplane_id.write(file)
                dynaKeywordMan.addKeyword(dbcsplane_id)      
                while "DATABASE_CROSS_SECTION_PLANE_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_CROSS_SECTION_PLANE_ID")                  
            if "DATABASE_DEFORC" in lines_with_asterisk:
                database_deforc = keyword_dict["DATABASE_DEFORC"]
                dbdeforc = DatabaseDeforc()
                dbdeforc.parse(database_deforc)
                dbdeforc.write(file)
                dynaKeywordMan.addKeyword(dbdeforc)
                while "DATABASE_DEFORC" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_DEFORC")
            if "DATABASE_ELOUT" in lines_with_asterisk:
                database_elout = keyword_dict["DATABASE_ELOUT"]
                delout = DatabaseElout()
                delout.parse(database_elout)
                delout.write(file)
                dynaKeywordMan.addKeyword(delout)
                while "DATABASE_ELOUT" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_ELOUT")
            if "DATABASE_FREQUENCY_BINARY_D3SSD" in lines_with_asterisk:
                database_frequency_binary_d3ssd = keyword_dict["DATABASE_FREQUENCY_BINARY_D3SSD"]
                dfreq_binary_d3ssd = DatabaseFrequencyBinaryD3SSD()
                dfreq_binary_d3ssd.parse(database_frequency_binary_d3ssd)
                dfreq_binary_d3ssd.write(file)
                dynaKeywordMan.addKeyword(dfreq_binary_d3ssd)
                while "DATABASE_FREQUENCY_BINARY_D3SSD" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_FREQUENCY_BINARY_D3SSD")
            if "DATABASE_GLSTAT" in lines_with_asterisk:
                database_glstat = keyword_dict["DATABASE_GLSTAT"]
                dglstat = DatabaseGlstat()
                dglstat.parse(database_glstat)
                dglstat.write(file)
                dynaKeywordMan.addKeyword(dglstat)
                while "DATABASE_GLSTAT" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_GLSTAT")
            if "DATABASE_MATSUM" in lines_with_asterisk:
                database_matsum = keyword_dict["DATABASE_MATSUM"]
                dmatsum = DatabaseMatsum()
                dmatsum.parse(database_matsum)
                dmatsum.write(file)
                dynaKeywordMan.addKeyword(dmatsum)
                while "DATABASE_MATSUM" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_MATSUM")
            if 'DATABASE_NCFORC' in lines_with_asterisk:
                database_ncforc = keyword_dict["DATABASE_NCFORC"]
                dncforc = DatabaseNcforc()
                dncforc.parse(database_ncforc)
                dncforc.write(file)
                dynaKeywordMan.addKeyword(dncforc)
                while "DATABASE_NCFORC" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_NCFORC")
            if "DATABASE_NODAL_FORCE_GROUP" in lines_with_asterisk:
                database_nodal_force_group = keyword_dict["DATABASE_NODAL_FORCE_GROUP"]
                dnodal_force_group = DatabaseNodalForceGroup()
                dnodal_force_group.parse(database_nodal_force_group)
                dnodal_force_group.write(file)
                dynaKeywordMan.addKeyword(dnodal_force_group)
                while "DATABASE_NODAL_FORCE_GROUP" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_NODAL_FORCE_GROUP")
            if "DATABASE_NODFOR" in lines_with_asterisk:
                database_nodfor = keyword_dict["DATABASE_NODFOR"]
                dbnodfor = DatabaseNodfor()
                dbnodfor.parse(database_nodfor)
                dbnodfor.write(file)
                dynaKeywordMan.addKeyword(dbnodfor)
                while "DATABASE_NODFOR" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_NODFOR")
            if "DATABASE_NODOUT" in lines_with_asterisk:
                database_nodout = keyword_dict["DATABASE_NODOUT"]
                dnodout = DatabaseNodout()
                dnodout.parse(database_nodout)
                dnodout.write(file)
                dynaKeywordMan.addKeyword(dnodout)
                while "DATABASE_NODOUT" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_NODOUT")
            if "DATABASE_RBDOUT" in lines_with_asterisk:
                database_rbdout = keyword_dict["DATABASE_RBDOUT"]
                drbdout = DatabaseRbdout()
                drbdout.parse(database_rbdout)
                drbdout.write(file)
                dynaKeywordMan.addKeyword(drbdout)
                while "DATABASE_RBDOUT" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_RBDOUT")
            if "DATABASE_RCFORC" in lines_with_asterisk:
                database_rcforc = keyword_dict["DATABASE_RCFORC"]
                drcforc = DatabaseRcforc()
                drcforc.parse(database_rcforc)
                drcforc.write(file)
                dynaKeywordMan.addKeyword(drcforc)
                while "DATABASE_RCFORC" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_RCFORC")
            if "DATABASE_RWFORC" in lines_with_asterisk:
                database_rwforc = keyword_dict["DATABASE_RWFORC"]
                drwforc = DatabaseRwforc()
                drwforc.parse(database_rwforc)
                drwforc.write(file)
                dynaKeywordMan.addKeyword(drwforc)
                while "DATABASE_RWFORC" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_RWFORC")
            if "DATABASE_SECFORC" in lines_with_asterisk:
                database_secforc = keyword_dict["DATABASE_SECFORC"]
                dsecforc = DatabaseSecforc()
                dsecforc.parse(database_secforc)
                dsecforc.write(file)
                dynaKeywordMan.addKeyword(dsecforc)
                while "DATABASE_SECFORC" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_SECFORC")
            if "DATABASE_SPCFORC" in lines_with_asterisk:
                database_spcforc = keyword_dict["DATABASE_SPCFORC"]
                dspcforc = DatabaseSpcforc()
                dspcforc.parse(database_spcforc)
                dspcforc.write(file)
                dynaKeywordMan.addKeyword(dspcforc)
                while "DATABASE_SPCFORC" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_SPCFORC")
            if "DATABASE_SLEOUT" in lines_with_asterisk:
                database_sleout = keyword_dict["DATABASE_SLEOUT"]
                dsleout = DatabaseSleout()
                dsleout.parse(database_sleout)
                dsleout.write(file)
                dynaKeywordMan.addKeyword(dsleout)
                while "DATABASE_SLEOUT" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_SLEOUT")
            if "DATABASE_SWFORC" in lines_with_asterisk:
                database_swforc = keyword_dict["DATABASE_SWFORC"]
                dswforc = DatabaseSwforc()
                dswforc.parse(database_swforc)
                dswforc.write(file)
                dynaKeywordMan.addKeyword(dswforc)
                while "DATABASE_SWFORC" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_SWFORC")
            if "DATABASE_BINARY_D3PLOT" in lines_with_asterisk:
                database_binary_d3plot = keyword_dict["DATABASE_BINARY_D3PLOT"]
                dbinary_d3plot = DatabaseBinaryD3plot()
                dbinary_d3plot.parse(database_binary_d3plot)
                dbinary_d3plot.write(file)
                dynaKeywordMan.addKeyword(dbinary_d3plot)
                while "DATABASE_BINARY_D3PLOT" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_BINARY_D3PLOT")
            if "DATABASE_BINARY_D3THDT" in lines_with_asterisk:
                database_binary_d3thdt = keyword_dict["DATABASE_BINARY_D3THDT"]
                dbinary_d3thdt = DatabaseBinaryD3thdt()
                dbinary_d3thdt.parse(database_binary_d3thdt)
                dbinary_d3thdt.write(file)
                dynaKeywordMan.addKeyword(dbinary_d3thdt)
                while "DATABASE_BINARY_D3THDT" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_BINARY_D3THDT")
            if "DATABASE_BINARY_D3DUMP" in lines_with_asterisk:
                database_binary_d3dump = keyword_dict["DATABASE_BINARY_D3DUMP"]
                dbinary_d3dump = DatabaseBinaryD3Dump()
                dbinary_d3dump.parse(database_binary_d3dump)
                dbinary_d3dump.write(file)
                dynaKeywordMan.addKeyword(dbinary_d3dump)
                while "DATABASE_BINARY_D3DUMP" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_BINARY_D3DUMP")
            if "DATABASE_BINARY_RUNRSF" in lines_with_asterisk:
                database_binary_runrsf = keyword_dict["DATABASE_BINARY_RUNRSF"]
                dbinary_runrsf = DatabaseBinaryRunrsf()
                dbinary_runrsf.parse(database_binary_runrsf)
                dbinary_runrsf.write(file)
                dynaKeywordMan.addKeyword(dbinary_runrsf)
                while "DATABASE_BINARY_RUNRSF" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_BINARY_RUNRSF")
            if "DATABASE_BINARY_INTFOR" in lines_with_asterisk:
                database_binary_intfor = keyword_dict["DATABASE_BINARY_INTFOR"]
                dbinary_intfor = DatabaseBinaryIntfor()
                dbinary_intfor.parse(database_binary_intfor)
                dbinary_intfor.write(file)
                dynaKeywordMan.addKeyword(dbinary_intfor)
                while "DATABASE_BINARY_INTFOR" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_BINARY_INTFOR")
            if "DATABASE_BINARY_INTFOR_FILE" in lines_with_asterisk:
                database_binary_intfor_file = keyword_dict["DATABASE_BINARY_INTFOR_FILE"]
                dbinary_intfor_file = DatabaseBinaryIntforFile()
                dbinary_intfor_file.parse(database_binary_intfor_file)
                dbinary_intfor_file.write(file)
                dynaKeywordMan.addKeyword(dbinary_intfor_file)
                while "DATABASE_BINARY_INTFOR_FILE" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_BINARY_INTFOR_FILE")
            if "DATABASE_EXTENT_BINARY" in lines_with_asterisk:
                database_extent_binary = keyword_dict["DATABASE_EXTENT_BINARY"]
                dbinary_extent = DatabaseExtentBinary()
                dbinary_extent.parse(database_extent_binary)
                dbinary_extent.write(file)
                dynaKeywordMan.addKeyword(dbinary_extent)
                while "DATABASE_EXTENT_BINARY" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_EXTENT_BINARY")
            if "DATABASE_EXTENT_INTFOR" in lines_with_asterisk:
                database_extent_intfor = keyword_dict["DATABASE_EXTENT_INTFOR"]
                dbinary_extent_intfor = DatabaseExtentIntfor()
                dbinary_extent_intfor.parse(database_extent_intfor)
                dbinary_extent_intfor.write(file)
                dynaKeywordMan.addKeyword(dbinary_extent_intfor)
                while "DATABASE_EXTENT_INTFOR" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_EXTENT_INTFOR")            
            if "DATABASE_FORMAT" in lines_with_asterisk:
                database_format = keyword_dict["DATABASE_FORMAT"]
                dformat = DatabaseFormat()
                dformat.parse(database_format)
                dformat.write(file)
                dynaKeywordMan.addKeyword(dformat)
                while "DATABASE_FORMAT" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_FORMAT")
            if "DATABASE_HISTORY_NODE" in lines_with_asterisk:
                database_history_node = keyword_dict["DATABASE_HISTORY_NODE"]
                dhistory_node = DatabaseHistoryNode()
                dhistory_node.parse(database_history_node)
                dhistory_node.write(file)
                dynaKeywordMan.addKeyword(dhistory_node)
                while "DATABASE_HISTORY_NODE" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_HISTORY_NODE")
            if "DATABASE_HISTORY_BEAM" in lines_with_asterisk:
                database_history_beam = keyword_dict["DATABASE_HISTORY_BEAM"]
                dhistory_beam = DatabaseHistoryBeam()
                dhistory_beam.parse(database_history_beam)
                dhistory_beam.write(file)
                dynaKeywordMan.addKeyword(dhistory_beam)
                while "DATABASE_HISTORY_BEAM" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_HISTORY_BEAM")
            if "DATABASE_HISTORY_BEAM_SET" in lines_with_asterisk:
                database_history_beam_set = keyword_dict["DATABASE_HISTORY_BEAM_SET"]
                dhistory_beam_set = DatabaseHistoryBeamSet()
                dhistory_beam_set.parse(database_history_beam_set)
                dhistory_beam_set.write(file)
                dynaKeywordMan.addKeyword(dhistory_beam_set)
                while "DATABASE_HISTORY_BEAM_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_HISTORY_BEAM_SET")
            if "DATABASE_HISTORY_SHELL" in lines_with_asterisk:
                database_history_shell = keyword_dict["DATABASE_HISTORY_SHELL"]
                dhistory_shell = DatabaseHistoryShell()
                dhistory_shell.parse(database_history_shell)
                dhistory_shell.write(file)
                dynaKeywordMan.addKeyword(dhistory_shell)
                while "DATABASE_HISTORY_SHELL" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_HISTORY_SHELL")
            if "DATABASE_HISTORY_SHELL_SET" in lines_with_asterisk:
                database_history_shell_set = keyword_dict["DATABASE_HISTORY_SHELL_SET"]
                dhistory_shell_set = DatabaseHistoryShellSet()
                dhistory_shell_set.parse(database_history_shell_set)
                dhistory_shell_set.write(file)
                dynaKeywordMan.addKeyword(dhistory_shell_set)
                while "DATABASE_HISTORY_SHELL_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_HISTORY_SHELL_SET")
            if "DATABASE_HISTORY_SOLID" in lines_with_asterisk:
                database_history_solid = keyword_dict["DATABASE_HISTORY_SOLID"]
                dhistory_solid = DatabaseHistorySolid()
                dhistory_solid.parse(database_history_solid)
                dhistory_solid.write(file)
                dynaKeywordMan.addKeyword(dhistory_solid)
                while "DATABASE_HISTORY_SOLID" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_HISTORY_SOLID")                    
            if "DATABASE_HISTORY_SOLID_SET" in lines_with_asterisk:
                database_history_solid_set = keyword_dict["DATABASE_HISTORY_SOLID_SET"]
                dhistory_solid_set = DatabaseHistorySolidSet()
                dhistory_solid_set.parse(database_history_solid_set)
                dhistory_solid_set.write(file)
                dynaKeywordMan.addKeyword(dhistory_solid_set)
                while "DATABASE_HISTORY_SOLID_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_HISTORY_SOLID_SET")
            if "DATABASE_HISTORY_NODE_SET" in lines_with_asterisk:
                database_history_node_set = keyword_dict["DATABASE_HISTORY_NODE_SET"]
                dhistory_node_set = DatabaseHistoryNodeSet()
                dhistory_node_set.parse(database_history_node_set)
                dhistory_node_set.write(file)
                dynaKeywordMan.addKeyword(dhistory_node_set)
                while "DATABASE_HISTORY_NODE_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("DATABASE_HISTORY_NODE_SET")                                
            print("Database Keywords Read Complete")
            if "DEFINE_BOX" in lines_with_asterisk:
                define_box = keyword_dict["DEFINE_BOX"]
                dbox = DefineBox()
                dbox.parse(define_box)
                dbox.write(file)
                dynaKeywordMan.addKeyword(dbox)
                while "DEFINE_BOX" in lines_with_asterisk:
                    lines_with_asterisk.remove("DEFINE_BOX")
            if "DEFINE_COORDINATE_SYSTEM" in lines_with_asterisk:
                define_coordinate_system = keyword_dict["DEFINE_COORDINATE_SYSTEM"]
                dcoordinate_system = DefineCoordinateSystem()
                dcoordinate_system.parse(define_coordinate_system)
                dcoordinate_system.write(file)
                dynaKeywordMan.addKeyword(dcoordinate_system)
                while "DEFINE_COORDINATE_SYSTEM" in lines_with_asterisk:
                    lines_with_asterisk.remove("DEFINE_COORDINATE_SYSTEM")
            if "DEFINE_COORDINATE_SYSTEM_TITLE" in lines_with_asterisk:
                define_coordinate_system_title = keyword_dict["DEFINE_COORDINATE_SYSTEM_TITLE"]
                dcoordinate_system_title = DefineCoordinateSystemTitle()
                dcoordinate_system_title.parse(define_coordinate_system_title)
                dcoordinate_system_title.write(file)
                dynaKeywordMan.addKeyword(dcoordinate_system_title)
                while "DEFINE_COORDINATE_SYSTEM_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("DEFINE_COORDINATE_SYSTEM_TITLE")
            if "DEFINE_CURVE" in lines_with_asterisk:
                define_curve = keyword_dict["DEFINE_CURVE"]
                dcurve = DefineCurve()
                dcurve.parse(define_curve)
                dcurve.write(file)
                dynaKeywordMan.addKeyword(dcurve)
                while "DEFINE_CURVE" in lines_with_asterisk:
                    lines_with_asterisk.remove("DEFINE_CURVE")
            if "DEFINE_CURVE_TITLE" in lines_with_asterisk:
                define_curve_title = keyword_dict["DEFINE_CURVE_TITLE"]
                dcurve_title = DefineCurveTitle()
                dcurve_title.parse(define_curve_title)
                dcurve_title.write(file)
                dynaKeywordMan.addKeyword(dcurve_title)
                while "DEFINE_CURVE_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("DEFINE_CURVE_TITLE")            
            print("Define Keywords Read Complete")
            if "ELEMENT_MASS" in lines_with_asterisk:
                element_mass = keyword_dict["ELEMENT_MASS"]
                emass = ElementMass()
                emass.parse(element_mass)
                emass.write(file)
                dynaKeywordMan.addKeyword(emass)
                while "ELEMENT_MASS" in lines_with_asterisk:
                    lines_with_asterisk.remove("ELEMENT_MASS")
            if "ELEMENT_MASS_NODE_SET" in lines_with_asterisk:
                element_mass_node_set = keyword_dict["ELEMENT_MASS_NODE_SET"]
                emass_node_set = ElementMassNodeSet()
                emass_node_set.parse(element_mass_node_set)
                emass_node_set.write(file)
                dynaKeywordMan.addKeyword(emass_node_set)
                while "ELEMENT_MASS_NODE_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("ELEMENT_MASS_NODE_SET")
            if "ELEMENT_BEAM" in lines_with_asterisk:
                element_beam = keyword_dict["ELEMENT_BEAM"]
                ebeam = ElementBeam()
                ebeam.parse(element_beam)
                ebeam.write(file)
                dynaKeywordMan.addKeyword(ebeam)
                while "ELEMENT_BEAM" in lines_with_asterisk:
                    lines_with_asterisk.remove("ELEMENT_BEAM")
            if "ELEMENT_SHELL" in lines_with_asterisk:
                element_shell = keyword_dict["ELEMENT_SHELL"]
                eshell = ElementShell()
                eshell.parse(element_shell)
                eshell.write(file)
                dynaKeywordMan.addKeyword(eshell)
                while "ELEMENT_SHELL" in lines_with_asterisk:
                    lines_with_asterisk.remove("ELEMENT_SHELL")
            if "ELEMENT_SHELL_THICKNESS" in lines_with_asterisk:
                element_shell_thick = keyword_dict["ELEMENT_SHELL_THICKNESS"]
                eshell_thick = ElementShellThickness()
                eshell_thick.parse(element_shell_thick)
                eshell_thick.write(file)
                dynaKeywordMan.addKeyword(eshell_thick)
                while "ELEMENT_SHELL_THICKNESS" in lines_with_asterisk:
                    lines_with_asterisk.remove("ELEMENT_SHELL_THICKNESS")
            if "ELEMENT_SOLID" in lines_with_asterisk:
                element_solid = keyword_dict["ELEMENT_SOLID"]
                esolid = ElementSolid()
                esolid.parse(element_solid)
                esolid.write(file)
                dynaKeywordMan.addKeyword(esolid)
                while "ELEMENT_SOLID" in lines_with_asterisk:
                    lines_with_asterisk.remove("ELEMENT_SOLID")
            print("Element Keywords Read Complete")
            if "FREQUENCY_DOMAIN_SSD" in lines_with_asterisk:        
                frequency_domain_ssd = keyword_dict["FREQUENCY_DOMAIN_SSD"]
                fdssd = FrequencyDomainSSD()
                fdssd.parse(frequency_domain_ssd)
                fdssd.write(file)            
                dynaKeywordMan.addKeyword(fdssd)
                while "FREQUENCY_DOMAIN_SSD" in lines_with_asterisk:
                    lines_with_asterisk.remove("FREQUENCY_DOMAIN_SSD")
            if "HOURGLASS" in lines_with_asterisk:
                hourglass = keyword_dict["HOURGLASS"]
                hglass = Hourglass()
                hglass.parse(hourglass)
                hglass.write(file)
                dynaKeywordMan.addKeyword(hglass)
                while "HOURGLASS" in lines_with_asterisk:
                    lines_with_asterisk.remove("HOURGLASS")
            if "EOS_TABULATED" in lines_with_asterisk:
                eos_tabulated = keyword_dict["EOS_TABULATED"]
                etabulated = EOSTabulated()
                etabulated.parse(eos_tabulated)
                etabulated.write(file)
                dynaKeywordMan.addKeyword(etabulated)
                while "EOS_TABULATED" in lines_with_asterisk:
                    lines_with_asterisk.remove("EOS_TABULATED")
            if "INITIAL_STRESS_SOLID" in lines_with_asterisk:
                initial_stress_solid = keyword_dict["INITIAL_STRESS_SOLID"]
                istress_solid = InitialStressSolid()
                istress_solid.parse(initial_stress_solid)
                istress_solid.write(file)
                dynaKeywordMan.addKeyword(istress_solid)
                while "INITIAL_STRESS_SOLID" in lines_with_asterisk:
                    lines_with_asterisk.remove("INITIAL_STRESS_SOLID")
            if "INITIAL_STRESS_SOLID_SET" in lines_with_asterisk:
                initial_stress_solid_set = keyword_dict["INITIAL_STRESS_SOLID_SET"]
                istress_solid_set = InitialStressSolidSet()
                istress_solid_set.parse(initial_stress_solid_set)
                istress_solid_set.write(file)
                dynaKeywordMan.addKeyword(istress_solid_set)
                while "INITIAL_STRESS_SOLID_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("INITIAL_STRESS_SOLID_SET")
            if "INITIAL_VELOCITY" in lines_with_asterisk:
                initial_velocity = keyword_dict["INITIAL_VELOCITY"]
                ivelocity = InitialVelocity()
                ivelocity.parse(initial_velocity)
                ivelocity.write(file)
                dynaKeywordMan.addKeyword(ivelocity)
                while "INITIAL_VELOCITY" in lines_with_asterisk:
                    lines_with_asterisk.remove("INITIAL_VELOCITY")
            if "INITIAL_VELOCITY_NODE" in lines_with_asterisk:
                initial_velocity_node = keyword_dict["INITIAL_VELOCITY_NODE"]
                ivelocity_node = InitialVelocityNode()
                ivelocity_node.parse(initial_velocity_node)
                ivelocity_node.write(file)
                dynaKeywordMan.addKeyword(ivelocity_node)
                while "INITIAL_VELOCITY_NODE" in lines_with_asterisk:
                    lines_with_asterisk.remove("INITIAL_VELOCITY_NODE")
            if "INITIAL_VELOCITY_GENERATION" in lines_with_asterisk:
                initial_velocity_generation = keyword_dict["INITIAL_VELOCITY_GENERATION"]
                ivelocity_generation = InitialVelocityGeneration()
                ivelocity_generation.parse(initial_velocity_generation)
                ivelocity_generation.write(file)
                dynaKeywordMan.addKeyword(ivelocity_generation)
                while "INITIAL_VELOCITY_GENERATION" in lines_with_asterisk:
                    lines_with_asterisk.remove("INITIAL_VELOCITY_GENERATION")
            print("Initial Keywords Read Complete")
            if "INTERFACE_SPRINGBACK_DYNA3D" in lines_with_asterisk:
                interface_springback_DYNA3D = keyword_dict["INTERFACE_SPRINGBACK_DYNA3D"]
                ispringback_DYNA3D = InterfaceSpringbackDYNA3D()
                ispringback_DYNA3D.parse(interface_springback_DYNA3D)
                ispringback_DYNA3D.write(file)
                dynaKeywordMan.addKeyword(ispringback_DYNA3D)
                while "INTERFACE_SPRINGBACK_DYNA3D" in lines_with_asterisk:
                    lines_with_asterisk.remove("INTERFACE_SPRINGBACK_DYNA3D")
            if "INTERFACE_SPRINGBACK_LSDYNA" in lines_with_asterisk:
                interface_springback_LSDYNA = keyword_dict["INTERFACE_SPRINGBACK_LSDYNA"]
                ispringback_LSDYNA = InterfaceSpringbackLSDYNA()
                ispringback_LSDYNA.parse(interface_springback_LSDYNA)
                ispringback_LSDYNA.write(file)
                dynaKeywordMan.addKeyword(ispringback_LSDYNA)
                while "INTERFACE_SPRINGBACK_LSDYNA" in lines_with_asterisk:
                    lines_with_asterisk.remove("INTERFACE_SPRINGBACK_LSDYNA")
            if "INTERFACE_SPRINGBACK_NASTRAN" in lines_with_asterisk:
                interface_springback_NASTRAN = keyword_dict["INTERFACE_SPRINGBACK_NASTRAN"]
                ispringback_NASTRAN = InterfaceSpringbackNASTRAN()
                ispringback_NASTRAN.parse(interface_springback_NASTRAN)
                ispringback_NASTRAN.write(file)
                dynaKeywordMan.addKeyword(ispringback_NASTRAN)
                while "INTERFACE_SPRINGBACK_NASTRAN" in lines_with_asterisk:    
                    lines_with_asterisk.remove("INTERFACE_SPRINGBACK_NASTRAN")
            if "INTERFACE_SPRINGBACK_SEAMLESS" in lines_with_asterisk:
                interface_springback_seamless = keyword_dict["INTERFACE_SPRINGBACK_SEAMLESS"]
                ispringback_seamless = InterfaceSpringbackSeamless()
                ispringback_seamless.parse(interface_springback_seamless)
                ispringback_seamless.write(file)
                dynaKeywordMan.addKeyword(ispringback_seamless)
                while "INTERFACE_SPRINGBACK_SEAMLESS" in lines_with_asterisk:
                    lines_with_asterisk.remove("INTERFACE_SPRINGBACK_SEAMLESS")                
            print("Interface Keywords Read Complete")
            if "KEYWORD_ID" in lines_with_asterisk:
                keyword_id = keyword_dict["KEYWORD_ID"]
                kword_id = KeywordID()
                kword_id.parse(keyword_id)
                kword_id.write(file)
                dynaKeywordMan.addKeyword(kword_id)
                while "KEYWORD_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("KEYWORD_ID")
            if "LOAD_BODY_X" in lines_with_asterisk:
                load_body_x = keyword_dict["LOAD_BODY_X"]
                lbody_x = LoadBodyX()
                lbody_x.parse(load_body_x)
                lbody_x.write(file)
                dynaKeywordMan.addKeyword(lbody_x)
                while "LOAD_BODY_X" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_BODY_X")
            if "LOAD_BODY_Y" in lines_with_asterisk:
                load_body_y = keyword_dict["LOAD_BODY_Y"]
                lbody_y = LoadBodyY()
                lbody_y.parse(load_body_y)
                lbody_y.write(file)
                dynaKeywordMan.addKeyword(lbody_y)
                while "LOAD_BODY_Y" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_BODY_Y")
            if "LOAD_BODY_Z" in lines_with_asterisk:
                load_body_z = keyword_dict["LOAD_BODY_Z"]
                lbody_z = LoadBodyZ()
                lbody_z.parse(load_body_z)
                lbody_z.write(file)
                dynaKeywordMan.addKeyword(lbody_z)
                while "LOAD_BODY_Z" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_BODY_Z")
            if "LOAD_BODY_RX" in lines_with_asterisk:
                load_body_rx = keyword_dict["LOAD_BODY_RX"]
                lbody_rx = LoadBodyRX()
                lbody_rx.parse(load_body_rx)
                lbody_rx.write(file)
                dynaKeywordMan.addKeyword(lbody_rx)
                while "LOAD_BODY_RX" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_BODY_RX")
            if "LOAD_BODY_RY" in lines_with_asterisk:
                load_body_ry = keyword_dict["LOAD_BODY_RY"]
                lbody_ry = LoadBodyRY()
                lbody_ry.parse(load_body_ry)
                lbody_ry.write(file)
                dynaKeywordMan.addKeyword(lbody_ry)
                while "LOAD_BODY_RY" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_BODY_RY")
            if "LOAD_BODY_RZ" in lines_with_asterisk:
                load_body_rz = keyword_dict["LOAD_BODY_RZ"]
                lbody_rz = LoadBodyRZ()
                lbody_rz.parse(load_body_rz)
                lbody_rz.write(file)
                dynaKeywordMan.addKeyword(lbody_rz)
                while "LOAD_BODY_RZ" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_BODY_RZ")
            if "LOAD_BODY_VECTOR" in lines_with_asterisk:
                load_body_vector = keyword_dict["LOAD_BODY_VECTOR"]
                lbody_vector = LoadBodyVector()
                lbody_vector.parse(load_body_vector)
                lbody_vector.write(file)
                dynaKeywordMan.addKeyword(lbody_vector)
                while "LOAD_BODY_VECTOR" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_BODY_VECTOR")
            if "LOAD_RIGID_BODY" in lines_with_asterisk:
                load_rigid_body = keyword_dict["LOAD_RIGID_BODY"]
                lrigid_body = LoadRigidBody()
                lrigid_body.parse(load_rigid_body)
                lrigid_body.write(file)
                dynaKeywordMan.addKeyword(lrigid_body)
                while "LOAD_RIGID_BODY" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_RIGID_BODY")
            if "LOAD_NODE_POINT" in lines_with_asterisk:
                load_node_point = keyword_dict["LOAD_NODE_POINT"]
                lnode_point = LoadNodePoint()
                lnode_point.parse(load_node_point)
                lnode_point.write(file)
                dynaKeywordMan.addKeyword(lnode_point)
                while "LOAD_NODE_POINT" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_NODE_POINT")
            if "LOAD_NODE_SET" in lines_with_asterisk:
                load_node_set = keyword_dict["LOAD_NODE_SET"]
                lnode_set = LoadNodeSet()
                lnode_set.parse(load_node_set)
                lnode_set.write(file)
                dynaKeywordMan.addKeyword(lnode_set)
                while "LOAD_NODE_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_NODE_SET")
            if "LOAD_SEGMENT" in lines_with_asterisk:
                load_segment = keyword_dict["LOAD_SEGMENT"]
                lsegment = LoadSegment()
                lsegment.parse(load_segment)
                lsegment.write(file)
                dynaKeywordMan.addKeyword(lsegment)
                while "LOAD_SEGMENT" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_SEGMENT")
            if "LOAD_SEGMENT_ID" in lines_with_asterisk:
                load_segment_id = keyword_dict["LOAD_SEGMENT_ID"]
                lsegment_id = LoadSegmentID()
                lsegment_id.parse(load_segment_id)
                lsegment_id.write(file)
                dynaKeywordMan.addKeyword(lsegment_id)
                while "LOAD_SEGMENT_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_SEGMENT_ID")
            if "LOAD_SEGMENT_SET" in lines_with_asterisk:
                load_segment_set = keyword_dict["LOAD_SEGMENT_SET"]
                lsegment_set = LoadSegmentSet()
                lsegment_set.parse(load_segment_set)
                lsegment_set.write(file)
                dynaKeywordMan.addKeyword(lsegment_set)
                while "LOAD_SEGMENT_SET" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_SEGMENT_SET")
            if "LOAD_SEGMENT_SET_ID" in lines_with_asterisk:
                load_segment_set_id = keyword_dict["LOAD_SEGMENT_SET_ID"]
                lsegment_set_id = LoadSegmentSetID()
                lsegment_set_id.parse(load_segment_set_id)
                lsegment_set_id.write(file)
                dynaKeywordMan.addKeyword(lsegment_set_id)
                while "LOAD_SEGMENT_SET_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("LOAD_SEGMENT_SET_ID")
            print("Load Keywords Read Complete")
            if "EOS_LINEAR_POLYNOMIAL" in lines_with_asterisk:
                eos_linear_polynomial = keyword_dict["EOS_LINEAR_POLYNOMIAL"]
                lpolynomial = EosLinearPolynomial()
                lpolynomial.parse(eos_linear_polynomial)
                lpolynomial.write(file)
                dynaKeywordMan.addKeyword(lpolynomial)
                while "EOS_LINEAR_POLYNOMIAL" in lines_with_asterisk:
                    lines_with_asterisk.remove("EOS_LINEAR_POLYNOMIAL")                    
            if "MAT_ADD_EROSION" in lines_with_asterisk:
                mat_add_erosion = keyword_dict["MAT_ADD_EROSION"]
                madd_erosion = MatAddErosion()
                madd_erosion.parse(mat_add_erosion)
                madd_erosion.write(file)
                dynaKeywordMan.addKeyword(madd_erosion)
                while "MAT_ADD_EROSION" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_ADD_EROSION")
            if "MAT_ADD_PZELECTRIC" in lines_with_asterisk:
                mat_add_pzelectric = keyword_dict["MAT_ADD_PZELECTRIC"]
                madd_pzelectric = MatAddPZElectric()
                madd_pzelectric.parse(mat_add_pzelectric)
                madd_pzelectric.write(file)
                dynaKeywordMan.addKeyword(madd_pzelectric)
                while "MAT_ADD_PZELECTRIC" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_ADD_PZELECTRIC")                    
            if "MAT_CSCM_CONCRETE" in lines_with_asterisk:
                mat_cscm_concrete = keyword_dict["MAT_CSCM_CONCRETE"]
                mcscm_concrete = MatCSCMConcrete()
                mcscm_concrete.parse(mat_cscm_concrete)
                mcscm_concrete.write(file)
                dynaKeywordMan.addKeyword(mcscm_concrete)
                while "MAT_CSCM_CONCRETE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_CSCM_CONCRETE")
            if "MAT_CSCM_CONCRETE_TITLE" in lines_with_asterisk:
                mat_cscm_concrete_title = keyword_dict["MAT_CSCM_CONCRETE_TITLE"]
                mcscm_concrete_title = MatCSCMConcreteTitle()
                mcscm_concrete_title.parse(mat_cscm_concrete_title)
                mcscm_concrete_title.write(file)
                dynaKeywordMan.addKeyword(mcscm_concrete_title)
                while "MAT_CSCM_CONCRETE_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_CSCM_CONCRETE_TITLE")
            if "MAT_ELASTIC" in lines_with_asterisk:
                mat_elastic = keyword_dict["MAT_ELASTIC"]
                elastic = MatElastic()
                elastic.parse(mat_elastic)
                elastic.write(file)
                dynaKeywordMan.addKeyword(elastic)
                while "MAT_ELASTIC" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_ELASTIC")
            if "MAT_ELASTIC_TITLE" in lines_with_asterisk:
                mat_elastic_title = keyword_dict["MAT_ELASTIC_TITLE"]
                elastic_title = MatElasticTitle()
                elastic_title.parse(mat_elastic_title)
                elastic_title.write(file)
                dynaKeywordMan.addKeyword(elastic_title)
                while "MAT_ELASTIC_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_ELASTIC_TITLE")
            if "MAT_VISCOELASTIC" in lines_with_asterisk:
                mat_viscoelastic = keyword_dict["MAT_VISCOELASTIC"]
                viscoelastic = MatViscoelastic()
                viscoelastic.parse(mat_viscoelastic)
                viscoelastic.write(file)
                dynaKeywordMan.addKeyword(viscoelastic)
                while "MAT_VISCOELASTIC" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_VISCOELASTIC")
            if "MAT_VISCOELASTIC_TITLE" in lines_with_asterisk:
                mat_viscoelastic_title = keyword_dict["MAT_VISCOELASTIC_TITLE"]
                viscoelastic_title = MatViscoelasticTitle()
                viscoelastic_title.parse(mat_viscoelastic_title)
                viscoelastic_title.write(file)
                dynaKeywordMan.addKeyword(viscoelastic_title)
                while "MAT_VISCOELASTIC_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_VISCOELASTIC_TITLE")
            if "MAT_SOIL_AND_FOAM" in lines_with_asterisk:
                mat_soil_and_foam = keyword_dict["MAT_SOIL_AND_FOAM"]
                soil_foam = MatSoilAndFoam()
                soil_foam.parse(mat_soil_and_foam)
                soil_foam.write(file)
                dynaKeywordMan.addKeyword(soil_foam)
                while "MAT_SOIL_AND_FOAM" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_SOIL_AND_FOAM")
            if "MAT_SOIL_AND_FOAM_FAILURE" in lines_with_asterisk:                    
                mat_soil_and_foam_failure = keyword_dict["MAT_SOIL_AND_FOAM_FAILURE"]
                soil_foam_failure = MatSoilAndFoamFailure()
                soil_foam_failure.parse(mat_soil_and_foam_failure)
                soil_foam_failure.write(file)
                dynaKeywordMan.addKeyword(soil_foam_failure)
                while "MAT_SOIL_AND_FOAM_FAILURE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_SOIL_AND_FOAM_FAILURE")
            if "MAT_PLASTIC_KINEMATIC" in lines_with_asterisk:
                mat_plastic_kinematic = keyword_dict["MAT_PLASTIC_KINEMATIC"]
                plastic_kinematic = MatPlasticKinematic()
                plastic_kinematic.parse(mat_plastic_kinematic)
                plastic_kinematic.write(file)
                dynaKeywordMan.addKeyword(plastic_kinematic)
                while "MAT_PLASTIC_KINEMATIC" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_PLASTIC_KINEMATIC")                    
            if "MAT_PLASTIC_KINEMATIC_TITLE" in lines_with_asterisk:
                mat_plastic_kinematic_title = keyword_dict["MAT_PLASTIC_KINEMATIC_TITLE"]
                plastic_kinematic_title = MatPlasticKinematicTitle()
                plastic_kinematic_title.parse(mat_plastic_kinematic_title)
                plastic_kinematic_title.write(file)
                dynaKeywordMan.addKeyword(plastic_kinematic_title)
                while "MAT_PLASTIC_KINEMATIC_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_PLASTIC_KINEMATIC_TITLE")
            if "MAT_ORIENTED_CRACK" in lines_with_asterisk:                    
                mat_oriented_crack = keyword_dict["MAT_ORIENTED_CRACK"]
                oriented_crack = MatOrientedCrack()
                oriented_crack.parse(mat_oriented_crack)
                oriented_crack.write(file)
                dynaKeywordMan.addKeyword(oriented_crack)
                while "MAT_ORIENTED_CRACK" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_ORIENTED_CRACK")
            if "MAT_NULL" in lines_with_asterisk:
                mat_null = keyword_dict["MAT_NULL"]
                curMatNull = MatNull()
                curMatNull.parse(mat_null)
                curMatNull.write(file)
                dynaKeywordMan.addKeyword(curMatNull)
                while "MAT_NULL" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_NULL")
            if "MAT_RIGID" in lines_with_asterisk:
                mat_rigid = keyword_dict["MAT_RIGID"]
                rigid = MatRigid()
                rigid.parse(mat_rigid)
                rigid.write(file)
                dynaKeywordMan.addKeyword(rigid)
                while "MAT_RIGID" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_RIGID")
            if "MAT_RIGID_TITLE" in lines_with_asterisk:
                mat_rigid_title = keyword_dict["MAT_RIGID_TITLE"]
                rigid_title = MatRigidTitle()
                rigid_title.parse(mat_rigid_title)
                rigid_title.write(file)
                dynaKeywordMan.addKeyword(rigid_title) 
                while "MAT_RIGID_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_RIGID_TITLE")   
            if "MAT_COMPOSITE_DAMAGE" in lines_with_asterisk:
                mat_composite_damage = keyword_dict["MAT_COMPOSITE_DAMAGE"]
                composite_damage = MatCompositeDamage()
                composite_damage.parse(mat_composite_damage)
                composite_damage.write(file)
                dynaKeywordMan.addKeyword(composite_damage)
                while "MAT_COMPOSITE_DAMAGE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_COMPOSITE_DAMAGE") 
            if "MAT_COMPOSITE_DAMAGE_TITLE" in lines_with_asterisk:
                mat_composite_damage_title = keyword_dict["MAT_COMPOSITE_DAMAGE_TITLE"]
                composite_damage_title = MatCompositeDamageTitle()
                composite_damage_title.parse(mat_composite_damage_title)
                composite_damage_title.write(file)
                dynaKeywordMan.addKeyword(composite_damage_title)
                while "MAT_COMPOSITE_DAMAGE_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_COMPOSITE_DAMAGE_TITLE")
            if "MAT_PIECEWISE_LINEAR_PLASTICITY" in lines_with_asterisk:
                mat_piecewise_linear_plasticity = keyword_dict["MAT_PIECEWISE_LINEAR_PLASTICITY"]
                mplasticity = MatPiecewiseLinearPlasticity()
                mplasticity.parse(mat_piecewise_linear_plasticity)
                mplasticity.write(file)
                dynaKeywordMan.addKeyword(mplasticity)
                while "MAT_PIECEWISE_LINEAR_PLASTICITY" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_PIECEWISE_LINEAR_PLASTICITY")
            if "MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE" in lines_with_asterisk:
                mat_piecewise_linear_plasticity_title = keyword_dict["MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE"]
                mplasticity_title = MatPiecewiseLinearPlasticityTitle()
                mplasticity_title.parse(mat_piecewise_linear_plasticity_title)
                mplasticity_title.write(file)
                dynaKeywordMan.addKeyword(mplasticity_title)
                while "MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE")
            if "MAT_ENHANCED_COMPOSITE_DAMAGE" in lines_with_asterisk:
                mat_enhanced_composite_damage = keyword_dict["MAT_ENHANCED_COMPOSITE_DAMAGE"]
                mcomposite_damage = MatEnhancedCompositeDamage()
                mcomposite_damage.parse(mat_enhanced_composite_damage)
                mcomposite_damage.write(file)
                dynaKeywordMan.addKeyword(mcomposite_damage)
                while "MAT_ENHANCED_COMPOSITE_DAMAGE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_ENHANCED_COMPOSITE_DAMAGE")
            if "MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE" in lines_with_asterisk:
                mat_enhanced_composite_damage_title = keyword_dict["MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE"]
                mcomposite_damage_title = MatEnhancedCompositeDamageTitle()
                mcomposite_damage_title.parse(mat_enhanced_composite_damage_title)
                mcomposite_damage_title.write(file)
                dynaKeywordMan.addKeyword(mcomposite_damage_title)
                while "MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_ENHANCED_COMPOSITE_DAMAGE_TITLE")
            if "MAT_MOONEY-RIVLIN_RUBBER" in lines_with_asterisk:
                mat_mooney_rivlin_rubber = keyword_dict["MAT_MOONEY-RIVLIN_RUBBER"]
                mmrubber = MatMooneyRivlinRubber()
                mmrubber.parse(mat_mooney_rivlin_rubber)
                mmrubber.write(file)
                dynaKeywordMan.addKeyword(mmrubber)
                while "MAT_MOONEY-RIVLIN_RUBBER" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_MOONEY-RIVLIN_RUBBER")
            if "MAT_MOONEY-RIVLIN_RUBBER_TITLE" in lines_with_asterisk:
                mat_mooney_rivlin_rubber_title = keyword_dict["MAT_MOONEY-RIVLIN_RUBBER_TITLE"]
                mmrubber_title = MatMooneyRivlinRubberTitle()
                mmrubber_title.parse(mat_mooney_rivlin_rubber_title)
                mmrubber_title.write(file)
                dynaKeywordMan.addKeyword(mmrubber_title)
                while "MAT_MOONEY-RIVLIN_RUBBER_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_MOONEY-RIVLIN_RUBBER_TITLE")
            if "MAT_LOW_DENSITY_FOAM" in lines_with_asterisk:
                mat_low_density_foam = keyword_dict["MAT_LOW_DENSITY_FOAM"]
                mlow_density_foam = MatLowDensityFoam()
                mlow_density_foam.parse(mat_low_density_foam)
                mlow_density_foam.write(file)
                dynaKeywordMan.addKeyword(mlow_density_foam)
                while "MAT_LOW_DENSITY_FOAM" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_LOW_DENSITY_FOAM")
            if "MAT_LOW_DENSITY_FOAM_TITLE" in lines_with_asterisk:
                mat_low_density_foam_title = keyword_dict["MAT_LOW_DENSITY_FOAM_TITLE"]
                mlow_density_foam_title = MatLowDensityFoamTitle()
                mlow_density_foam_title.parse(mat_low_density_foam_title)
                mlow_density_foam_title.write(file)
                dynaKeywordMan.addKeyword(mlow_density_foam_title)
                while "MAT_LOW_DENSITY_FOAM_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_LOW_DENSITY_FOAM_TITLE")
            if "MAT_SPOTWELD" in lines_with_asterisk:
                mat_spotweld = keyword_dict["MAT_SPOTWELD"]
                mspotweld = MatSpotweld()
                mspotweld.parse(mat_spotweld)
                mspotweld.write(file)
                dynaKeywordMan.addKeyword(mspotweld)
                while "MAT_SPOTWELD" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_SPOTWELD")
            if "MAT_SPOTWELD_TITLE" in lines_with_asterisk:
                mat_spotweld_title = keyword_dict["MAT_SPOTWELD_TITLE"]
                mspotweld_title = MatSpotweldTitle()
                mspotweld_title.parse(mat_spotweld_title)
                mspotweld_title.write(file)
                dynaKeywordMan.addKeyword(mspotweld_title)
                while "MAT_SPOTWELD_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_SPOTWELD_TITLE")                
            if "MAT_COHESIVE_MIXED_MODE" in lines_with_asterisk:
                mat_cohesive_mixed_mode = keyword_dict["MAT_COHESIVE_MIXED_MODE"]
                mcohesive_mixed_mode = MatCohesiveMixedMode()
                mcohesive_mixed_mode.parse(mat_cohesive_mixed_mode)
                mcohesive_mixed_mode.write(file)
                dynaKeywordMan.addKeyword(mcohesive_mixed_mode)
                while "MAT_COHESIVE_MIXED_MODE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_COHESIVE_MIXED_MODE")
            if "MAT_COHESIVE_MIXED_MODE_TITLE" in lines_with_asterisk:
                mat_cohesive_mixed_mode_title = keyword_dict["MAT_COHESIVE_MIXED_MODE_TITLE"]
                mcohesive_mixed_mode_title = MatCohesiveMixedModeTitle()
                mcohesive_mixed_mode_title.parse(mat_cohesive_mixed_mode_title)
                mcohesive_mixed_mode_title.write(file)
                dynaKeywordMan.addKeyword(mcohesive_mixed_mode_title)
                while "MAT_COHESIVE_MIXED_MODE_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_COHESIVE_MIXED_MODE_TITLE")
            if "MAT_ELASTIC_PERI" in lines_with_asterisk:
                mat_elastic_peri = keyword_dict["MAT_ELASTIC_PERI"]
                melastic_peri = MatElasticPeri()
                melastic_peri.parse(mat_elastic_peri)
                melastic_peri.write(file)
                dynaKeywordMan.addKeyword(melastic_peri)
                while "MAT_ELASTIC_PERI" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_ELASTIC_PERI")
            if "MAT_ELASTIC_PERI_TITLE" in lines_with_asterisk:
                mat_elastic_peri_title = keyword_dict["MAT_ELASTIC_PERI_TITLE"]
                melastic_peri_title = MatElasticPeriTitle()
                melastic_peri_title.parse(mat_elastic_peri_title)
                melastic_peri_title.write(file)
                dynaKeywordMan.addKeyword(melastic_peri_title)
                while "MAT_ELASTIC_PERI_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("MAT_ELASTIC_PERI_TITLE")                    
            print("Material Keywords Read Complete")
            if "NODE" in lines_with_asterisk:
                node = keyword_dict["NODE"]
                n = DynaNode()
                n.parse(node)
                n.write(file)
                dynaKeywordMan.addKeyword(n)
                while "NODE" in lines_with_asterisk:
                    lines_with_asterisk.remove("NODE")
            print("Node Keywords Read Complete")
            if "PART" in lines_with_asterisk:
                part = keyword_dict["PART"]
                p = Part()
                p.parse(part)
                p.write(file)
                dynaKeywordMan.addKeyword(p)
                while "PART" in lines_with_asterisk:
                    lines_with_asterisk.remove("PART")   
            if "PART_COMPOSITE" in lines_with_asterisk:
                part_composite = keyword_dict["PART_COMPOSITE"]
                pcomposite = PartComposite()
                pcomposite.parse(part_composite)
                pcomposite.write(file)
                dynaKeywordMan.addKeyword(pcomposite)
                while "PART_COMPOSITE" in lines_with_asterisk:
                    lines_with_asterisk.remove("PART_COMPOSITE")         
            if "PART_CONTACT" in lines_with_asterisk:
                part_contact = keyword_dict["PART_CONTACT"]
                pcontact = PartContact()
                pcontact.parse(part_contact)
                pcontact.write(file)
                dynaKeywordMan.addKeyword(pcontact)
                while "PART_CONTACT" in lines_with_asterisk:
                    lines_with_asterisk.remove("PART_CONTACT")
            print("Part Keywords Read Complete")
            if "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY" in lines_with_asterisk:
                rigidwall_geometric_flat_display = keyword_dict["RIGIDWALL_GEOMETRIC_FLAT_DISPLAY"]
                rgeometric_flat_display = RigidWallGeometricFlatDisplay()
                rgeometric_flat_display.parse(rigidwall_geometric_flat_display)
                rgeometric_flat_display.write(file)
                dynaKeywordMan.addKeyword(rgeometric_flat_display)
                while "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY" in lines_with_asterisk:
                    lines_with_asterisk.remove("RIGIDWALL_GEOMETRIC_FLAT_DISPLAY")
            if "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID" in lines_with_asterisk:
                rigidwall_geometric_flat_display_id = keyword_dict["RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID"]
                rgeometric_flat_display_id = RigidWallGeometricFlatDisplayID()
                rgeometric_flat_display_id.parse(rigidwall_geometric_flat_display_id)
                rgeometric_flat_display_id.write(file)
                dynaKeywordMan.addKeyword(rgeometric_flat_display_id)
                while "RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("RIGIDWALL_GEOMETRIC_FLAT_DISPLAY_ID")            
            if "RIGIDWALL_PLANAR" in lines_with_asterisk:
                rigidwall_planar = keyword_dict["RIGIDWALL_PLANAR"]
                rplanar = RigidWallPlanar()
                rplanar.parse(rigidwall_planar)
                rplanar.write(file)
                dynaKeywordMan.addKeyword(rplanar)
                while "RIGIDWALL_PLANAR" in lines_with_asterisk:
                    lines_with_asterisk.remove("RIGIDWALL_PLANAR")
            if "RIGIDWALL_PLANAR_ID" in lines_with_asterisk:
                rigidwall_planar_id = keyword_dict["RIGIDWALL_PLANAR_ID"]
                rplanar_id = RigidWallPlanarID()
                rplanar_id.parse(rigidwall_planar_id)
                rplanar_id.write(file)
                dynaKeywordMan.addKeyword(rplanar_id)
                while "RIGIDWALL_PLANAR_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("RIGIDWALL_PLANAR_ID")
            if "RIGIDWALL_PLANAR_MOVING" in lines_with_asterisk:
                rigidwall_planar_moving = keyword_dict["RIGIDWALL_PLANAR_MOVING"]
                rplanar_moving = RigidWallPlanarMoving()
                rplanar_moving.parse(rigidwall_planar_moving)
                rplanar_moving.write(file)
                dynaKeywordMan.addKeyword(rplanar_moving)
                while "RIGIDWALL_PLANAR_MOVING" in lines_with_asterisk:
                    lines_with_asterisk.remove("RIGIDWALL_PLANAR_MOVING")
            if "RIGIDWALL_PLANAR_MOVING_ID" in lines_with_asterisk:
                rigidwall_planar_moving_id = keyword_dict["RIGIDWALL_PLANAR_MOVING_ID"]
                rplanar_moving_id = RigidWallPlanarMovingID()
                rplanar_moving_id.parse(rigidwall_planar_moving_id)
                rplanar_moving_id.write(file)
                dynaKeywordMan.addKeyword(rplanar_moving_id)
                while "RIGIDWALL_PLANAR_MOVING_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("RIGIDWALL_PLANAR_MOVING_ID")                    
            if "RIGIDWALL_PLANAR_MOVING_FORCES" in lines_with_asterisk:
                rigidwall_planar_moving_forces = keyword_dict["RIGIDWALL_PLANAR_MOVING_FORCES"]
                rplanar_moving_forces = RigidWallPlanarMovingForces()
                rplanar_moving_forces.parse(rigidwall_planar_moving_forces)
                rplanar_moving_forces.write(file)
                dynaKeywordMan.addKeyword(rplanar_moving_forces)
                while "RIGIDWALL_PLANAR_MOVING_FORCES" in lines_with_asterisk:
                    lines_with_asterisk.remove("RIGIDWALL_PLANAR_MOVING_FORCES")
            if "RIGIDWALL_PLANAR_MOVING_FORCES_ID" in lines_with_asterisk:
                rigidwall_planar_moving_forces_id = keyword_dict["RIGIDWALL_PLANAR_MOVING_FORCES_ID"]
                rplanar_moving_forces_id = RigidWallPlanarMovingForcesID()
                rplanar_moving_forces_id.parse(rigidwall_planar_moving_forces_id)
                rplanar_moving_forces_id.write(file)
                dynaKeywordMan.addKeyword(rplanar_moving_forces_id)
                while "RIGIDWALL_PLANAR_MOVING_FORCES_ID" in lines_with_asterisk:
                    lines_with_asterisk.remove("RIGIDWALL_PLANAR_MOVING_FORCES_ID")                    
            print("RigidWall Keywords Read Complete")
            if "SECTION_BEAM" in lines_with_asterisk:
                section_beam = keyword_dict["SECTION_BEAM"]
                sbeam = SectionBeam()
                sbeam.parse(section_beam)
                sbeam.write(file)
                dynaKeywordMan.addKeyword(sbeam)
                while "SECTION_BEAM" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_BEAM")
            if "SECTION_BEAM_TITLE" in lines_with_asterisk:
                section_beam_title = keyword_dict["SECTION_BEAM_TITLE"]
                sbeam_title = SectionBeamTitle()
                sbeam_title.parse(section_beam_title)
                sbeam_title.write(file)
                dynaKeywordMan.addKeyword(sbeam_title)
                while "SECTION_BEAM_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_BEAM_TITLE")
            if "SECTION_SHELL" in lines_with_asterisk:
                section_shell = keyword_dict["SECTION_SHELL"]
                sshell = SectionShell()
                sshell.parse(section_shell)
                sshell.write(file)
                dynaKeywordMan.addKeyword(sshell)
                while "SECTION_SHELL" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_SHELL")
            if "SECTION_SHELL_TITLE" in lines_with_asterisk:
                section_shell_title = keyword_dict["SECTION_SHELL_TITLE"]
                sshell_title = SectionShellTitle()
                sshell_title.parse(section_shell_title)
                sshell_title.write(file)
                dynaKeywordMan.addKeyword(sshell_title)
                while "SECTION_SHELL_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_SHELL_TITLE")
            if "SECTION_SOLID" in lines_with_asterisk:
                section_solid = keyword_dict["SECTION_SOLID"]
                ssolid = SectionSolid()
                ssolid.parse(section_solid)
                ssolid.write(file)
                dynaKeywordMan.addKeyword(ssolid)
                while "SECTION_SOLID" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_SOLID")
            if "SECTION_SOLID_TITLE" in lines_with_asterisk:
                section_solid_title = keyword_dict["SECTION_SOLID_TITLE"]
                ssolid_title = SectionSolidTitle()
                ssolid_title.parse(section_solid_title)
                ssolid_title.write(file)
                dynaKeywordMan.addKeyword(ssolid_title)
                while "SECTION_SOLID_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_SOLID_TITLE")        
            if "SECTION_SOLID_PERI" in lines_with_asterisk:
                section_solid_peri = keyword_dict["SECTION_SOLID_PERI"]
                ssolid_peri = SectionSolidPeri()
                ssolid_peri.parse(section_solid_peri)
                ssolid_peri.write(file)
                dynaKeywordMan.addKeyword(ssolid_peri)
                while "SECTION_SOLID_PERI" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_SOLID_PERI")                    
            if "SECTION_SOLID_PERI_TITLE" in lines_with_asterisk:
                section_solid_peri_title = keyword_dict["SECTION_SOLID_PERI_TITLE"]
                ssolid_peri_title = SectionSolidPeriTitle()
                ssolid_peri_title.parse(section_solid_peri_title)
                ssolid_peri_title.write(file)
                dynaKeywordMan.addKeyword(ssolid_peri_title)
                while "SECTION_SOLID_PERI_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_SOLID_PERI_TITLE")                
            if "SECTION_TSHELL" in lines_with_asterisk:
                section_tshell = keyword_dict["SECTION_TSHELL"]
                stshell = SectionTShell()
                stshell.parse(section_tshell)
                stshell.write(file)
                dynaKeywordMan.addKeyword(stshell)
                while "SECTION_TSHELL" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_TSHELL")
            if "SECTION_TSHELL_TITLE" in lines_with_asterisk:
                section_tshell_title = keyword_dict["SECTION_TSHELL_TITLE"]
                stshell_title = SectionTShellTitle()
                stshell_title.parse(section_tshell_title)
                stshell_title.write(file)
                dynaKeywordMan.addKeyword(stshell_title)
                while "SECTION_TSHELL_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SECTION_TSHELL_TITLE")
            print("Section Keywords Read Complete")
            if "SET_NODE_ADD" in lines_with_asterisk:
                set_node_add = keyword_dict["SET_NODE_ADD"]
                sna = SetNodeAdd()
                sna.parse(set_node_add)
                sna.write(file)
                dynaKeywordMan.addKeyword(sna)
                while "SET_NODE_ADD" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_NODE_ADD")
            if "SET_NODE_GENERAL" in lines_with_asterisk:
                set_node_general = keyword_dict["SET_NODE_GENERAL"]
                sng = SetNodeGeneral()
                sng.parse(set_node_general)
                sng.write(file)
                dynaKeywordMan.addKeyword(sng)
                while "SET_NODE_GENERAL" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_NODE_GENERAL")
            if "SET_NODE_LIST" in lines_with_asterisk:
                set_node_list = keyword_dict["SET_NODE_LIST"]
                snl = SetNodeList()
                snl.parse(set_node_list)
                snl.write(file)
                dynaKeywordMan.addKeyword(snl)
                while "SET_NODE_LIST" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_NODE_LIST")
            if "SET_NODE_LIST_TITLE" in lines_with_asterisk:
                set_node_list_title = keyword_dict["SET_NODE_LIST_TITLE"]
                snl_title = SetNodeListTitle()
                snl_title.parse(set_node_list_title)
                snl_title.write(file)
                dynaKeywordMan.addKeyword(snl_title)
                while "SET_NODE_LIST_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_NODE_LIST_TITLE")
            if "SET_NODE_LIST_GENERATE" in lines_with_asterisk:
                set_node_list_generate = keyword_dict["SET_NODE_LIST_GENERATE"]
                snlg = SetNodeListGenerate()
                snlg.parse(set_node_list_generate)
                snlg.write(file)
                dynaKeywordMan.addKeyword(snlg)
                while "SET_NODE_LIST_GENERATE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_NODE_LIST_GENERATE")            
            if "SET_PART" in lines_with_asterisk:
                set_part = keyword_dict["SET_PART"]
                sp = SetPart()
                sp.parse(set_part)
                sp.write(file)
                dynaKeywordMan.addKeyword(sp)
                while "SET_PART" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_PART")
            if "SET_PART_LIST" in lines_with_asterisk:
                set_part_list = keyword_dict["SET_PART_LIST"]
                spl = SetPartList()
                spl.parse(set_part_list)
                spl.write(file)
                dynaKeywordMan.addKeyword(spl)
                while "SET_PART_LIST" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_PART_LIST")
            if "SET_PART_LIST_TITLE" in lines_with_asterisk:
                set_part_list_title = keyword_dict["SET_PART_LIST_TITLE"]
                spl_title = SetPartListTitle()
                spl_title.parse(set_part_list_title)
                spl_title.write(file)
                dynaKeywordMan.addKeyword(spl_title)
                while "SET_PART_LIST_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_PART_LIST_TITLE")                    
            if "SET_PART_LIST_GENERATE" in lines_with_asterisk:
                set_part_list_generate = keyword_dict["SET_PART_LIST_GENERATE"]
                splg = SetPartListGenerate()
                splg.parse(set_part_list_generate)
                splg.write(file)
                dynaKeywordMan.addKeyword(splg)
                while "SET_PART_LIST_GENERATE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_PART_LIST_GENERATE")
            if "SET_SEGMENT" in lines_with_asterisk:
                set_segment = keyword_dict["SET_SEGMENT"]
                ssl = SetSegment()
                ssl.parse(set_segment)
                ssl.write(file)
                dynaKeywordMan.addKeyword(ssl)
                while "SET_SEGMENT" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_SEGMENT")
            if "SET_SEGMENT_TITLE" in lines_with_asterisk:
                set_segment_title = keyword_dict["SET_SEGMENT_TITLE"]
                ssl_title = SetSegmentTitle()
                ssl_title.parse(set_segment_title)
                ssl_title.write(file)
                dynaKeywordMan.addKeyword(ssl_title)
                while "SET_SEGMENT_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_SEGMENT_TITLE")
            if "SET_SHELL" in lines_with_asterisk:
                set_shell = keyword_dict["SET_SHELL"]
                ssl = SetShell()
                ssl.parse(set_shell)
                ssl.write(file)
                dynaKeywordMan.addKeyword(ssl)
                while "SET_SHELL" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_SHELL")                    
            if "SET_SHELL_TITLE" in lines_with_asterisk:
                set_shell_title = keyword_dict["SET_SHELL_TITLE"]
                ssl_title = SetShellTitle()
                ssl_title.parse(set_shell_title)
                ssl_title.write(file)
                dynaKeywordMan.addKeyword(ssl_title)
                while "SET_SHELL_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_SHELL_TITLE")                    
            if "SET_SHELL_LIST" in lines_with_asterisk:
                set_shell_ist = keyword_dict["SET_SHELL_LIST"]
                ssl = SetShellList()
                ssl.parse(set_shell_ist)
                ssl.write(file)
                dynaKeywordMan.addKeyword(ssl)
                while "SET_SHELL_LIST" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_SHELL_LIST")
            if "SET_SOLID" in lines_with_asterisk:
                set_solid = keyword_dict["SET_SOLID"]
                ssl = SetSolid()
                ssl.parse(set_solid)
                ssl.write(file)
                dynaKeywordMan.addKeyword(ssl)
                while "SET_SOLID" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_SOLID")
            if "SET_SOLID_TITLE" in lines_with_asterisk:
                set_solid_title = keyword_dict["SET_SOLID_TITLE"]
                ssl_title = SetSolidTitle()
                ssl_title.parse(set_solid_title)
                ssl_title.write(file)
                dynaKeywordMan.addKeyword(ssl_title)
                while "SET_SOLID_TITLE" in lines_with_asterisk:
                    lines_with_asterisk.remove("SET_SOLID_TITLE")
            print("Set Keywords Read Complete")
            while "INCLUDE" in lines_with_asterisk:
                lines_with_asterisk.remove("INCLUDE")
            while "KEYWORD" in lines_with_asterisk:
                lines_with_asterisk.remove("KEYWORD")
            while "END" in lines_with_asterisk:
                lines_with_asterisk.remove("END")

            file.write("*END\n")
            file.close()

            self.dynaKeywordMan = dynaKeywordMan
            if writelog == True:
                # Output the result
                print("\n\nFollowing keywords are not parsed")
                numofnotParsed = 0
                for line in lines_with_asterisk:
                    print(line)
                    numofnotParsed = numofnotParsed + 1
                
                if numofnotParsed == 0:
                    print("All keywords are parsed successfully")
                else:
                    print("Number of not parsed keywords: ", numofnotParsed)
                


        
    

if __name__ == '__main__':
    mode = "ZUG_TEST3_RS"
    mode = "CONTACT_OVERVIEW"
    mode = "TAYLOR_BAR"
    mode = "TAYLOR_BAR_ALE"
    mode = "TAYLOR_BAR_ALE_DETAIL"
    mode = "TAYLOR_BAR_ALE_REDUCED"
    mode = "EXP_SC_DROP"
    mode = "EXP_SC_CONTACT_INTERFERENCE"
    mode = "CONTACT_AUTOMATIC"
    mode = "CONTACT_ERODING_BIRDBALL"
    mode = "CONTACT_ERODING_PROJ_ERROD"
    mode = "CONTACT_FOAM"
    mode = "CONTACT_FRICTION_BRAKE"
    mode = "CONTACT_FRICTION_BRAKE_DEBUG"
    mode = "CONTACT_PIPES_PIPS"
    mode = "CONTACT_PIPES_ADPIPS"
    mode = "CONTACT_RUBBER"
    mode = "CONTACT_SPOTWELD"
    mode = "CONTACTS_CONTACT1"
    mode = "CONTACTS_CONTACT2"
    mode = "CONTACTS_CONTACT3"
    mode = "CONTACTS_CONTACT4"
    mode = "CONTACTS_CONTACT5"
    mode = "CONTACTS_CONTACT6"
    mode = "CONTACTS_FORCETRANSDUCER"
    mode = "CONTACTS_PROJECTILE_BLOCK"  
    mode = "CONTACTS_SPHERE"
    mode = "ADAPTIVE_ADAPTIVE1"
    mode = "ADAPTIVE_ADAPTIVE2"
    mode = "ADAPTIVE_ADAPTIVE3"
    mode = "UDEMY_LSDYNA_3PT_BENDING_TEST"
    mode = "UDEMY_LSDYNA_ADAPTIVE_3PT_BENDING_TEST"
    mode = "UDEMY_LSDYNA_BRACKET_LINEAR_ANALYSIS"
    mode = "UDEMY_LSDYNA_COMPOSITE"
    mode = "UDEMY_LSDYNA_CON_ROD"
    mode = "UDEMY_LSDYNA_CRASH_BOX"    
    mode = "UDEMY_LSDYNA_HIGH_SPEED_IMPACT"    
    mode = "UDEMY_LSDYNA_HONEYCOMB_COMPOSITE"
    mode = "UDEMY_LSDYNA_IMPLICIT"
    mode = "UDEMY_LSDYNA_SSD"    
    mode = "TAYLOR_BAR"
    mode = "COMPOSITE_LAMINATE"
   
    testfile = "test.k"
    
    
    if mode == "ZUG_TEST3_RS":
        path = os.getcwd()
        path = os.path.join(path, "OpenRadioss/examples/zug_test3_RS/zug_test3_RS.k")
    elif mode == "CONTACT_OVERVIEW":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Overview"        
        path = os.path.join(path, "OpenRadioss/examples/Contact_Overview/main.k")
        os.chdir(newdir)
    elif mode == "TAYLOR_BAR":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/taylor_A.k"
        path = os.path.join(path, "OpenRadioss/examples/taylor_A.k/taylor_A.k")
        os.chdir(newdir)
    elif mode == "TAYLOR_BAR_ALE":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/taylor_B_ALE"        
        path = os.path.join(path, "OpenRadioss/examples/taylor_B_ALE/taylor_B_ALE.k")
        os.chdir(newdir)
    elif mode == "TAYLOR_BAR_ALE_DETAIL":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/taylor_C_ALE_detail"                
        path = os.path.join(path, "OpenRadioss/examples/taylor_C_ALE_detail/taylor_C_ALE_detail.k")
        os.chdir(newdir)
    elif mode == "TAYLOR_BAR_ALE_REDUCED":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/taylor_D_ALE_reduced"                
        path = os.path.join(path, "OpenRadioss/examples/taylor_D_ALE_reduced/taylor_D_ALE_reduced.k")
        os.chdir(newdir)
    elif mode == "EXP_SC_DROP":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/exp_sc_drop"
        path = os.path.join(path, "OpenRadioss/examples/exp_sc_drop/exp_sc_drop.key")
        os.chdir(newdir)
    elif mode == "EXP_SC_CONTACT_INTERFERENCE":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/EXP_SC_CONTACT_INTERFERENCE"        
        path = os.path.join(path, "OpenRadioss/examples/EXP_SC_CONTACT_INTERFERENCE/EXP_SC_CONTACT_INTERFERENCE.key")
        os.chdir(newdir)
    elif mode == "CONTACT_AUTOMATIC":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/CONTACT_AUTOMATIC"
        path = os.path.join(path, "OpenRadioss/examples/CONTACT_AUTOMATIC/tube.k")
        os.chdir(newdir)
    elif mode == "CONTACT_ERODING_BIRDBALL":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Eroding/birdball"
        path = os.path.join(path, "OpenRadioss/examples/Contact_Eroding/birdball/birdball.k")
        os.chdir(newdir)
    elif mode == "CONTACT_ERODING_PROJ_ERROD":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Eroding/proj-errod"
        path = os.path.join(path, "OpenRadioss/examples/Contact_Eroding/proj-errod/proj-errod.k")
        os.chdir(newdir)
    elif mode == "CONTACT_FOAM":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Foam"
        path = os.path.join(path, "OpenRadioss/examples/Contact_Foam/matfoamsoil.k")
        os.chdir(newdir)
    elif mode =="CONTACT_FRICTION_BRAKE":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Friction/brake"
        path = os.path.join(path, "OpenRadioss/examples/Contact_Friction/brake/brake.k")
        os.chdir(newdir)
    elif mode =="CONTACT_FRICTION_BRAKE_DEBUG":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Friction/brake_debug"
        path = os.path.join(path, "OpenRadioss/examples/Contact_Friction/brake_debug/brake_debug.k")
        os.chdir(newdir)
    elif mode =="CONTACT_PIPES_PIPS":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Pipes/pips"        
        path = os.path.join(path, "OpenRadioss/examples/Contact_Pipes/pips/pips.k")
        os.chdir(newdir)
    elif mode == "CONTACT_PIPES_ADPIPS":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Pipes/adpips"        
        path = os.path.join(path, "OpenRadioss/examples/Contact_Pipes/adpips/adpips.k")
        os.chdir(newdir)
    elif mode == "CONTACT_RUBBER":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Rubber"
        path = os.path.join(path, "OpenRadioss/examples/Contact_Rubber/matrubber.k")
        os.chdir(newdir)
    elif mode == "CONTACT_SPOTWELD":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contact_Spotweld"
        path = os.path.join(path, "OpenRadioss/examples/Contact_Spotweld/spotweld.k")
        os.chdir(newdir)
    elif mode == "CONTACTS_CONTACT1":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contacts/Contact1"
        path = os.path.join(path, "OpenRadioss/examples/Contacts/Contact1/plate.typ3.k")
        os.chdir(newdir)
    elif mode == "CONTACTS_CONTACT2":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contacts/Contact2"
        path = os.path.join(path, "OpenRadioss/examples/Contacts/Contact2/plate.typ13.k")
        os.chdir(newdir)
    elif mode == "CONTACTS_CONTACT3":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contacts/Contact3"
        path = os.path.join(path, "OpenRadioss/examples/Contacts/Contact3/box.typ6.k")
    elif mode == "CONTACTS_CONTACT4":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contacts/Contact4"
        path = os.path.join(path, "OpenRadioss/examples/Contacts/Contact4/ring_01.k")
        os.chdir(newdir)
    elif mode == "CONTACTS_CONTACT5":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contacts/Contact5"
        path = os.path.join(path, "OpenRadioss/examples/Contacts/Contact5/ring_1.k")
        os.chdir(newdir)
    elif mode == "CONTACTS_CONTACT6":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contacts/Contact6"
        path = os.path.join(path, "OpenRadioss/examples/Contacts/Contact6/ring_100.k")
        os.chdir(newdir)
    elif mode == "CONTACTS_FORCETRANSDUCER":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contacts/ForceTransducer"
        path = os.path.join(path, "OpenRadioss/examples/Contacts/ForceTransducer/transducer.k")
        os.chdir(newdir)
    elif mode == "CONTACTS_PROJECTILE_BLOCK":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contacts/ProjectileBlock"                  
        path = os.path.join(path, "OpenRadioss/examples/Contacts/ProjectileBlock/typ14-m24.k")
        os.chdir(newdir)        
    elif mode == "CONTACTS_SPHERE":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Contacts/Sphere"
        path = os.path.join(path, "OpenRadioss/examples/Contacts/Sphere/sphere1.k")
        os.chdir(newdir)
    elif mode == "ADAPTIVE_ADAPTIVE1":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Adaptive/Adaptive1"
        path = os.path.join(path, "OpenRadioss/examples/Adaptive/Adaptive1/bend.k")
        os.chdir(newdir)
    elif mode == "ADAPTIVE_ADAPTIVE2":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Adaptive/Adaptive2"
        path = os.path.join(path, "OpenRadioss/examples/Adaptive/Adaptive2/thinning1.k")
        os.chdir(newdir)
    elif mode == "ADAPTIVE_ADAPTIVE3":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Adaptive/Adaptive3"
        path = os.path.join(path, "OpenRadioss/examples/Adaptive/Adaptive3/thinning2.k")
        os.chdir(newdir)
    elif mode == "UDEMY_LSDYNA_3PT_BENDING_TEST":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/3 pt bending test"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/3 pt bending test/3p_bending_3.k")
        testfile = "test_3pt_bending_3.k"
        os.chdir(newdir)
    elif mode == "UDEMY_LSDYNA_ADAPTIVE_3PT_BENDING_TEST":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/Adaptive 3pt bending"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/Adaptive 3pt bending/3p_bending_ADAPTIVE_1.k")
        testfile = "test_adaptive_3pt_bending.k"
        os.chdir(newdir)
    elif mode == "UDEMY_LSDYNA_BRACKET_LINEAR_ANALYSIS":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/Bracket linear analysis"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/Bracket linear analysis/Bracket_2.k")
        testfile = "test_bracket_linear_analysis.k"
        os.chdir(newdir)
    elif mode == "UDEMY_LSDYNA_COMPOSITE":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/Composite"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/Composite/comp2.k")
        testfile = "test_composite.k"
        os.chdir(newdir)
    elif mode == "UDEMY_LSDYNA_CON_ROD":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/con_rod_modal"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/con_rod_modal/rod.k")
        testfile = "test_rod.k"
        os.chdir(newdir)
    elif mode == "UDEMY_LSDYNA_CRASH_BOX":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/Crash Box"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/Crash Box/Crash_box_final.k")
        testfile = "test_crash_box.k"
        os.chdir(newdir)
    elif mode == "UDEMY_LSDYNA_HIGH_SPEED_IMPACT":
        ######## Long keyword input  해야함 
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/high_speed_impact"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/high_speed_impact/High_speed_Impact_final3.k")
        testfile = "test_high_speed_impact.k"
        os.chdir(newdir)        
    elif mode == "UDEMY_LSDYNA_HONEYCOMB_COMPOSITE":        
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/honeycomb_composite"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/honeycomb_composite/composite_final.k")
        testfile = "test_honeycomb_composite.k"
        os.chdir(newdir)
    elif mode == "UDEMY_LSDYNA_IMPLICIT":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/Implicit"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/Implicit/plate_imp.k")
        testfile = "test_plate_imp.k"
    elif mode == "UDEMY_LSDYNA_SSD":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Udemy_LSDYNA/SSD"
        path = os.path.join(path, "OpenRadioss/examples/Udemy_LSDYNA/SSD/SSD1.k")
        testfile = "test_SSD1.k"
    elif mode =="COMPOSITE_LAMINATE":
        path = os.getcwd()
        newdir = "OpenRadioss/examples/Composite"
        path = os.path.join(path, "OpenRadioss/examples/Composite/laminate.k")
        testfile = "test_laminate.k"
    else:
        print("No such mode")
        exit()

    # Initialize an empty list to store the lines
        
    dynaMan = DynaManager()
    dynaMan.SetInputPath(path)
    dynaMan.ReadInputFile(testfile)
    dynaMan.WriteOutputFile(testfile)
