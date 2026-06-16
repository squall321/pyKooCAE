import numpy as np

from KooODBCADManager.Module import *
from KooODBCADManager.Modules import *
from KooODBCADManager.ModulesConnector import *

class ModuleManager():
    def __init__(self):
        self.modules = {}
        self.maxid = 0 
    
    def CreateSphereImpactModule(self, name, radius=1.0, center=(0.0, 0.0, 0.0)):
        self.maxid += 1
        module = SphereImpactModule(self.maxid, name, radius, center)
        self.modules[self.maxid] = module
        return module
    
    def CreateCylinderwithMassImpactModule(self, name, radius = 0.008, outerRadius = 0.01, heightFront = 0.02, heightBack = 0.01, center=(0.0, 0.0, 0.0), zDir = (0.0, 0.0, 1.0), backRadius = 0.01, midRadius = 0, heightMid = 0):
        self.maxid += 1
        module = CylinderwithMassImpactModule(self.maxid, name, radius, outerRadius, heightFront, heightBack, center, zDir, backRadius, midRadius, heightMid)
        self.modules[self.maxid] = module
        return module
    
    def CreateConnectorFlexibleModule(self, name, Pstart2D, Pend2D, numPoints = 100, desired_length = 7):
        self.maxid += 1
        module = ConnectorFlexible(self.maxid, name, Pstart2D, Pend2D, numPoints, desired_length)
        self.modules[self.maxid] = module
        return module
    
    def CreateConnectorFlexible3DModule(self, name, Pstart3D, Pend3D, xdir, ydir, zdir, numPoints = 100, desired_length = 7.0):
        self.maxid += 1        
        module : ConnectorFlexible = ConnectorFlexible(self.maxid, name, None, None, numPoints, desired_length)
        # orthogonal projection to plane defined by zdir
        module.Set3DInformation(Pstart3D, Pend3D, xdir, ydir, zdir)
        self.modules[self.maxid] = module
        return module
    
    def RemoveModule(self, id):
        if id in self.modules:
            del self.modules[id]