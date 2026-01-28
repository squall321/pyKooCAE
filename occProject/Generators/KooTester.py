

from KooCAEManager.KooNode import * 
from KooCAEManager.KooElement import *
from KooCAEManager.KooMeshImporter import *

from KooODBCADManager.PackageWarpageLayer import *

from OCC.Display.SimpleGui import init_display
if __name__ == "__main__":
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        # 오프스크린 모드: GUI 함수들을 더미로 정의
        def display_dummy(*args, **kwargs):
            print("[offscreen] display called with", args, kwargs)

        def start_display_dummy():
            print("[offscreen] start_display skipped")

        def add_menu_dummy(name):
            print(f"[offscreen] add_menu('{name}') skipped")

        def add_function_to_menu_dummy(*args, **kwargs):
            print("[offscreen] add_function_to_menu skipped")

        display = display_dummy
        start_display = start_display_dummy
        add_menu = add_menu_dummy
        add_function_to_menu = add_function_to_menu_dummy

    else:
        # 정상 GUI 모드
        from OCC.Display.SimpleGui import init_display
        display, start_display, add_menu, add_function_to_menu = init_display()






if __name__ == "__main__":
    mode = "WarpedPackages"    
    # WarpedPackage Test
    solidList = [] 
    warpageList = [] 
    warpageList.append("ArrayWarpage9999.txt") # Warpage File
    warpageList.append(0.0) # Warpage X Location
    warpageList.append(0.0) # Warpage Y Location
    warpageList.append(0.0) # Warpage Z Location        
    warpageList.append(-100.0) # xLeftBottom
    warpageList.append(100.0) # xLengthTop
    warpageList.append(-100.0) # yLeftBottom        
    warpageList.append(75.0) # yLengthTop
    warpageList.append("MM")
    warpageList.append(1.0) # amplification
    modeType = "SMD"
    angle = 3.0
    xoffset = 0.1
    yoffset = 0.2
    #angle = 0.0
    #xoffset = 0.0
    #yoffset = 0.0
    dh = 0.0 
    if mode == "WarpageSolderJoint" or "WarpedPackages" in mode:
        solderJointWarped = SolderJointsLayer("TestSolderJoint",0.0,0.0,0.1,16.0,16.0,1.9)
        solderJointWarped.SetDetailSolder(True)
        
        solderJointWarped.SetSurfaceTension(480.0)
        solderJointWarped.SetWarpageVariables(warpageList)
        solderJointWarped.SetRotationPad(0.0,angle)
        solderJointWarped.SetPositionPad(0.0,0.0,0.1,xoffset,yoffset)
        for i in range(0,5):
            for j in range(0,5):
                bottomPadLocX = -8.0 + i*4.0
                bottomPadLocY = -8.0 + j*4.0
                bottomPadRadius = 1.5
                topPadLocX = -8.0+0.0 + i*4.0
                topPadLocY = -8.0+0.0 + j*4.0
                topPadRadius = 1.5
                solderRadius = 1.7
                topMaskThickness = 0.2
                bottomPadThickness = 0.1
                bottomMaskThickness = 0.1
                #3 digit number of i and j
                ith = str(i).zfill(3)
                jth = str(j).zfill(3)
                name = "Pad" + ith + jth
                if modeType == "NSMD":
                    solderJointWarped.CreateNSMDVariables(bottomPadLocX, bottomPadLocY, bottomPadRadius, topPadLocX, topPadLocY, topPadRadius, solderRadius, name, topMaskThickness, bottomPadThickness)
                elif modeType == "SMD":
                    solderJointWarped.CreateSMDVariables(bottomPadLocX, bottomPadLocY, bottomPadRadius, topPadLocX, topPadLocY, topPadRadius, solderRadius, name, topMaskThickness, bottomMaskThickness)

        solderJointWarped.GenerateImportWarpageSurface()
        solderJointWarped.SetSolderJointObjects()
        shapeList = solderJointWarped.GenerateSolderJoints()    
        dh = solderJointWarped.dh
        solidList.extend(shapeList)
    
    
    if mode == "WarpedPackageCylinder" or "WarpedPackages" in mode:
        
     
        pkgLayer = PackageWarpedLayer("TestCylinder", 0,0,0,-1,-1,0.1)
        pkgLayer.SetWarpageVariables(warpageList)
        for i in range(0, 5):
            for j in range(0,5):
                cylinderList = []
                cylinderList.append("CYLINDER") 
                cylinderList.append(-8.0 + i*4.0)
                cylinderList.append(-8.0 + j*4.0)
                cylinderList.append(1.5)
                cylinderList.append(1)
                cylinderList.append([])
                cylinderList.append([])
                cylinderList.append([])
                pkgLayer.AddVariables(cylinderList)
        shape = pkgLayer.GenerateShapes()
        solidList.extend(shape)
        
        pkgLayer = PackageWarpedLayer("TestCylinder", xoffset,yoffset,2.0+dh,-1,-1,0.1)        
        pkgLayer.SetWarpageVariables(warpageList)
        pkgLayer.SetRotation(angle)

        for i in range(0, 5):
            for j in range(0,5):
                cylinderList = []
                cylinderList.append("CYLINDER") 
                cylinderList.append(-8.0 + i*4.0)
                cylinderList.append(-8.0 + j*4.0)
                cylinderList.append(1.5)
                cylinderList.append(1)
                cylinderList.append([])
                cylinderList.append([])
                cylinderList.append([])               
                pkgLayer.AddVariables(cylinderList)
        shape = pkgLayer.GenerateShapes()
        solidList.append(shape)           
        
    if mode == "WarpedPackageBox" or "WarpedPackages" in mode:
        pkgWarped = PackageWarpedLayer("TestBox", xoffset,yoffset,2.1+dh,-1,-1,2.0)
        pkgWarped.SetWarpageVariables(warpageList)
        pkgWarped.SetRotation(angle)
        boxList = []               
        boxList.append("BOX") 
        boxList.append(0.0) # x
        boxList.append(0.0) # y
        boxList.append(20.0) # xLength
        boxList.append(20.0) # yLength
        boxList.append(1) # matID
        boxList.append([]) #compMatIDList
        boxList.append([]) #compThicknessList
        boxList.append([]) #compBList
        boxList.append(-1) #numElemforEachLayer
        boxList.append([]) #compositeEOSList
        boxList.append([]) #compositeMeshrefinementSizeLlist
        boxList.append([]) #compositeMeshrefinementLocationXList
        boxList.append([]) #compositeMehrefinementLocationYList
        boxList.append([]) #compositeModeList:
        
        pkgWarped.AddVariables(boxList)        
        solid = pkgWarped.GenerateShapes()
        solidList.append(solid)
        
        pkgWarped = PackageWarpedLayer("TestBox", xoffset,yoffset,4.1+dh,-1,-1,1.0)
        pkgWarped.SetWarpageVariables(warpageList)
        pkgWarped.SetRotation(angle)
        boxList = []      
        boxList.append("BOX")          
        boxList.append(0.0) # x
        boxList.append(0.0) # y
        boxList.append(20.0) # xLength
        boxList.append(20.0) # yLength
        boxList.append(1) # matID
        boxList.append([]) #compMatIDList
        boxList.append([]) #compThicknessList
        boxList.append([]) #compBList
        boxList.append(-1) #numElemforEachLayer
        boxList.append([]) #compositeEOSList
        boxList.append([]) #compositeMeshrefinementSizeLlist
        boxList.append([]) #compositeMeshrefinementLocationXList
        boxList.append([]) #compositeMehrefinementLocationYList
        boxList.append([]) #compositeModeList:
        
        pkgWarped.AddVariables(boxList)        
        solid = pkgWarped.GenerateShapes()
        solidList.append(solid)
        
    
    for solid in solidList:
        if type(solid) == list:
            for solid2 in solid:
                display.DisplayShape(solid2, update = True)
        else:
            display.DisplayShape(solid, update = True)
    start_display()
    
    
    # MSHImporter Test
    if mode == "MSHImporter":
        path = os.getcwd()
        nodeManager : NodeManager = NodeManager() 
        elementManager : ElementManager = ElementManager(nodeManager)
        path = os.path.join(path,'Example\\Model\\New_Model_1\\Solid4\\Solid4.msh') 
        importer = KooMSHImporter(nodeManager, elementManager)
        importer.import_msh_file(path)