import numpy as np
from KooCAEManager.KooNode import Node, NodeManager
from KooCAEManager.KooElement import Element, ElementManager

class KooNodeResult():
    def __init__(self, node = None):
        self.refNode : Node = node 
        self.time = []
        self.forceX = []
        self.forceY = []
        self.forceZ = []
        self.momentX = []
        self.momentY = []
        self.momentZ = []
        self.energy = []

    def SetReferenceNode(self, node : Node):
        self.refNode = node
    
    def AddTime(self, time):
        self.time.append(time)
    
    def AddForce(self, forceX, forceY, forceZ):
        self.forceX.append(forceX)
        self.forceY.append(forceY)
        self.forceZ.append(forceZ)
    
    def AddMoment(self, momentX, momentY, momentZ):
        self.momentX.append(momentX)
        self.momentY.append(momentY)
        self.momentZ.append(momentZ)

    def AddEnergy(self, energy):
        self.energy.append(energy)
    
class KooElementResult():
    def __init__(self, element = None):
        self.refElement : Element = element
    
    def SetReferenceElement(self, element : Element):
        self.refElement = element

class KooSetResult():
    def __init__(self, setid = None):
        self.setid = setid
        self.time = [] 
        self.forceX = []
        self.forceY = []
        self.forceZ = []
        self.momentX = []
        self.momentY = []
        self.momentZ = []
        self.energy = []  
    
    def SetSetID(self, setid):
        self.setid = setid
    
    def AddTime(self, time):
        self.time.append(time)
    
    def AddForce(self, forceX, forceY, forceZ):
        self.forceX.append(forceX)
        self.forceY.append(forceY)
        self.forceZ.append(forceZ)
    
    def AddMoment(self, momentX, momentY, momentZ):
        self.momentX.append(momentX)
        self.momentY.append(momentY)
        self.momentZ.append(momentZ)
    
    def AddEnergy(self, energy):
        self.energy.append(energy)

class KooGroupResult():
    def __init__(self, groupid = None):
        self.groupid = groupid
        self.nodeResults = {}
    
    def AddNodeResult(self, nodeid, nodeResult : KooNodeResult):
        self.nodeResults[nodeid] = nodeResult

class KooResultManager():
    def __init__(self, nodeManager : NodeManager):
        self.nodeManager = nodeManager
        self.nodeResult = {}
        self.elementResult = {}
        self.setResult = {}
        self.groupResult = {}

    def AddBndoutResult(self, setid, time, forceX, forceY, forceZ, momentX, momentY, momentZ, energy):
        if setid not in self.setResult:
            self.setResult[setid] = KooSetResult(setid)
        self.setResult[setid].AddTime(time)
        self.setResult[setid].AddForce(forceX, forceY, forceZ)
        self.setResult[setid].AddMoment(momentX, momentY, momentZ)
        self.setResult[setid].AddEnergy(energy)
        return self.setResult[setid]
    
    def AddNodforResult(self, nodeid, time, forceX, forceY, forceZ, energy):
        if nodeid not in self.nodeResult:
            self.nodeResult[nodeid] = KooNodeResult(self.nodeManager.FindNodefromID(nodeid))
        self.nodeResult[nodeid].AddTime(time)
        self.nodeResult[nodeid].AddForce(forceX, forceY, forceZ)
        self.nodeResult[nodeid].AddEnergy(energy)
        return self.nodeResult[nodeid]

    def AddGroupResult(self, groupid):
        if groupid not in self.groupResult:
            self.groupResult[groupid] = KooGroupResult(groupid)
        return self.groupResult[groupid]
    
    def AddNodeResultinGroup(self, groupid, nodeid, nodeResult : KooNodeResult):
        if groupid not in self.groupResult:
            self.groupResult[groupid] = KooGroupResult(groupid)
        self.groupResult[groupid].AddNodeResult(nodeid, nodeResult)
