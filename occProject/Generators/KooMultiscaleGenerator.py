import os
from KooSimulationGenerator import KooSimulationGenerator   
from KooCAEManager.KooNode import *
from KooCAEManager.KooElement import *
from KooCAEManager.KooPart import *
from KooCAEManager.KooResult import *
from KooCAEManager.KooSection import *  
from KooCAEManager.KooMaterial import *
from KooCAEManager.KooBoundaryNode import *
from KooCAEManager.KooLoad import *
from KooCAEManager.KooSegment import *
from KooCAEManager.KooDefine import *
from KooCAEManager.KooContact import *
from KooCAEManager.KooDynaControl import *
from KooCAEManager.KooDamping import *

from KooCAEManager.KooDynaKeyword import *
from KooCAEManager.KooDynaResult import *
from KooCAEManager.KooMeshImporter import KooMSHImporter, KooDynaImporter
from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH


class KooMultiscaleSimulationGenerator(KooSimulationGenerator):
    def __init__(self, dynaImporter : KooDynaImporter = None):
        if dynaImporter == None:
            nodeMan = NodeManager()
            nodeSetMan = NodeSetManager(nodeMan)
            secMan = KooSectionManager()
            matMan = KooMaterialManager()
            elemMan = ElementManager()
            partMan = KooPartManager()
            loadMan = KooLoadManager()
            boundaryNodeMan = KooBoundaryNodeManager()
            defineManager = KooDefineManager()
            contactMan = KooContactManager()
            segSetMan = KooSegmentSetManager()
            controlMan = KooControlManager()
            dampingMan = KooDampingManager()
            dynaResultManager = KooDynaResultManager(defineManager=defineManager,boundaryNodeManager=boundaryNodeMan)
            resultMan = KooResultManager(nodeMan)
            dynaImporter = KooDynaImporter(nodeMan,partMan,resultMan,matMan,secMan,nodeSetMan,loadMan,boundaryNodeMan,defineManager,contactMan,segSetMan,dynaResultManager,controlMan, dampingMan)    
        super().__init__(dynaImporter)
        self.dynaPath = ""
        self.appFileName = "appfile.txt"
    
    def ImportMultiscaleSimulationOption(self, fileName):
        filePath = os.path.join(self.curDir, fileName)    
    
    def GenerateSimulation(self):
        pass
        

if __name__ == "__main__":
    curDir = "D:\\OpenCASCADE-7.7.0-vc14-64\\pythonoccenv310\\occProject\\Generators\\dist\\Examples\\4.MultiscaleSimulation\\CoupleMultiscale\\"
    optionName = "MultiscaleOption.txt"
    simGenerator : KooMultiscaleSimulationGenerator = KooMultiscaleSimulationGenerator()
    simGenerator.SetCurrentDirectory(curDir)
    simGenerator.ImportMultiscaleSimulationOption(optionName)
    simGenerator.ImportBaseFile()
    simGenerator.GenerateSimulation()
    
    