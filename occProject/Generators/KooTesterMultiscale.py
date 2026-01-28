import os
from KooCAEManager.KooNode import *
from KooCAEManager.KooDefine import *
from KooCAEManager.KooLoad import *
from KooCAEManager.KooBoundaryNode import *
from KooCAEManager.KooDynaResult import *
path = os.getcwd()
path = os.path.join(path, "Dyna/DMA/Test/d3plot")

print(path)
try:
    defineMan : KooDefineManager = KooDefineManager()
    boundaryMan : KooBoundaryNodeManager = KooBoundaryNodeManager()
    nodalResult = KooDynaNodalResultNodalDisp(path, [],1.e-3, defineMan,boundaryMan)
    nodalResult.ImportResults()
    
    nodeMan : NodeManager = NodeManager()
    
    nodeMan.CreateNodefromGivenID(408,1.554774e-02,-1.42870762e-04,3.00000000e-04)
    nodeMan.CreateNodefromGivenID(409,1.89118936e-02,4.17119835e-04,3.00000000e-04)
    
    nodes = list(nodeMan.nodes.values())    
    nodalResult.SetNodes(nodes)
    #check current time
    import time
    start = time.time()                
    nodalResult.InterpolateDisplacement()
    end1 = time.time()
    #nodalResult.InterpolateDisplacementOld()
    #end2 = time.time()
    print("New Method Time : ", end1 - start)
    #print("Old Method Time : ", end2 - end1)
    nodalResult.Print()
    nodalResult.GenenerateNodalDisp()
    
    print(boundaryMan.WritetoDynaKeyword(0))
    print(defineMan.WritetoDynaKeyword(0))
    
    
        
    
except Exception as e:
    print(e)
    pass