
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




from io import StringIO

from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec, gp_Ax2, gp_Circ
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere

from KooCAEManager.KooNode import *
from KooCAEManager.KooElement import *
from KooCAEManager.KooPart import *
from KooCAEManager.KooResult import *
from KooCAEManager.KooSection import *  
from KooCAEManager.KooMaterial import *

from KooCAEManager.KooDynaKeyword import *
from KooCAEManager.KooMeshImporter import KooMSHImporter, KooDynaImporter
from KooCAEManager.KooMeshManagerGMSH import KooMeshManagerGMSH
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

class KooImpactSimulationGenerator():
    def __init__(self, dynaImporter : KooDynaImporter):
        self.dynaImporter = dynaImporter

        self.ballImpactorMeshList = [] 
        self.backsideWallMeshList = []
        self.ballImpactorPartIDList = []
        self.backsideWallPartIDList = []
        self.ZBottomList = [] 
        self.zTopList = []

        self.meshGenerationMode = False 
        self.meshPath = os.getcwd()
        self.meshSizeList = [] 
        self.dynaFileList = [] 

        self.addScriptList = []

        self.outputOptionList = []

        self.LoadBoundaryOptionPath = ""

        self.maxNID = 0
        self.maxEID = 0
        self.maxPID = 0
        self.maxSID = 0
        self.maxMID = 0

    def SetLoadBoundaryOptionPath(self, path):
        self.LoadBoundaryOptionPath = path

    def ImportLoadBoundaryOption(self, path):
        self.SetLoadBoundaryOptionPath(path)
        return self.SetLoadBoundaryOption()
    
    def SetLoadBoundaryOption(self):
        outputOption = {}
        script = ""
        with open(self.LoadBoundaryOptionPath, "r") as file:
            sline = file.readline()
            while sline:
                sline = sline.strip()
                if "*end" in sline.lower():
                    break

                elif "#" in sline:
                    sline = file.readline()
                    continue
                elif "*SimulationMode" in sline:
                    if "impactball" in sline.lower():
                        outputOption["SimulationMode"] = "ImpactBall"
                        while True:
                            sline = file.readline()
                            if "*" in sline:
                                break
                            elif "#" in sline:
                                continue
                            svector = sline.split(",")
                            if "filename" in svector[0].lower():
                                curFileName = svector[1].strip()
                            elif "impactballlocation" in svector[0].lower():
                                outputOption["ImpactBallLocation"] = [(svector[1]), (svector[2])]
                            elif "impactballdirection" in svector[0].lower():
                                outputOption["ImpactBallDirection"] = [float(svector[1]), float(svector[2]), float(svector[3])]
                            elif "impactballradius" in svector[0].lower():
                                outputOption["ImpactBallRadius"] = float(svector[1])
                            elif "impactballheight" in svector[0].lower():
                                outputOption["ImpactBallHeight"] = float(svector[1])
                            elif "impactballelasticmodulus" in svector[0].lower():
                                outputOption["ImpactBallElasticModulus"] = float(svector[1])
                            elif "impactballpoissonratio" in svector[0].lower():
                                outputOption["ImpactBallPoissonRatio"] = float(svector[1])
                            elif "impactballdensity" in svector[0].lower():
                                outputOption["ImpactBallDensity"] = float(svector[1])
                            elif "impactballvelocity" in svector[0].lower():
                                outputOption["ImpactBallVelocity"] = float(svector[1])
                            elif "impactballpointmass" in svector[0].lower():
                                outputOption["ImpactBallPointMass"] = float(svector[1])
                            elif "impactballforcehalfsinefrequency" in svector[0].lower():
                                outputOption["ImpactBallForceHalfSineFrequency"] = float(svector[1])
                            elif "impactballforcehalfsineamplitude" in svector[0].lower():
                                outputOption["ImpactBallForceHalfSineAmplitude"] = float(svector[1])
                            elif "impactballmeshsizerefine" in svector[0].lower():
                                outputOption["ImpactBallMeshSizeRefine"] = float(svector[1])
                            elif "impactballmeshsize" in svector[0].lower():
                                outputOption["ImpactBallMeshSize"] = float(svector[1])
                            elif "meshsize" in svector[0].lower():
                                outputOption["MeshSize"] = float(svector[1])
                                if "ImpactBallMeshSize" not in outputOption:
                                    outputOption["ImpactBallMeshSize"] = outputOption["MeshSize"]
                                if "BacksideWallMeshSize" not in outputOption:
                                    outputOption["BacksideWallMeshSize"] = outputOption["MeshSize"]
                                if "ImpactBallMeshSizeRefine" not in outputOption:
                                    outputOption["ImpactBallMeshSizeRefine"] = outputOption["MeshSize"]
                            elif "thicknessoffset" in svector[0].lower():
                                outputOption["ThicknessOffset"] = float(svector[1])
                            elif "backsidewallthickness" in svector[0].lower():
                                outputOption["BacksideWallThickness"] = float(svector[1])
                            elif "backsidewallnumberofelementsinthickness" in svector[0].lower():
                                outputOption["BacksideWallNumberofElementsinThickness"] = int(svector[1])
                            elif "backsidewallelasticmodulus" in svector[0].lower():
                                outputOption["BacksideWallElasticModulus"] = float(svector[1])
                            elif "backsidewallpoissonratio" in svector[0].lower():
                                outputOption["BacksideWallPoissonRatio"] = float(svector[1])
                            elif "backsidewalldensity" in svector[0].lower():
                                outputOption["BacksideWallDensity"] = float(svector[1])
                            elif "backsidewallmeshsize" in svector[0].lower():
                                outputOption["BacksideWallMeshSize"] = float(svector[1])
                            elif "tfinal" in svector[0].lower():
                                outputOption["TFinal"] = float(svector[1])
                            elif "dt" in svector[0].lower():
                                outputOption["DT"] = float(svector[1])

                        curFileName = curFileName.replace("_IBL","_{0}_{1}".format(outputOption["ImpactBallLocation"][0], outputOption["ImpactBallLocation"][1]))
                        curFileName = curFileName.replace("_IBD","_{0}_{1}_{2}".format(outputOption["ImpactBallDirection"][0], outputOption["ImpactBallDirection"][1], outputOption["ImpactBallDirection"][2]))
                        curFileName = curFileName.replace("_IBR","_{0}".format(outputOption["ImpactBallRadius"]))
                        curFileName = curFileName.replace("_IBH","_{0}".format(outputOption["ImpactBallHeight"]))
                        if "ImpactBallElasticModulus" in outputOption:
                            curFileName = curFileName.replace("_IBEM","_{0}".format(outputOption["ImpactBallElasticModulus"]))
                        if "ImpactBallPoissonRatio" in outputOption:
                            curFileName = curFileName.replace("_IBPR","_{0}".format(outputOption["ImpactBallPoissonRatio"]))
                        if "ImpactBallDensity" in outputOption:
                            curFileName = curFileName.replace("_IBD","_{0}".format(outputOption["ImpactBallDensity"]))                                                
                        if "ImpactBallVelocity" in outputOption:
                            curFileName = curFileName.replace("_IBV","_{0}".format(outputOption["ImpactBallVelocity"]))
                        if "ImpactBallPointMass" in outputOption:
                            curFileName = curFileName.replace("_IBPM","_{0}".format(outputOption["ImpactBallPointMass"]))
                        if "ImpactBallForceHalfSineFrequency" in outputOption:
                            curFileName = curFileName.replace("_IBFHSF","_{0}".format(outputOption["ImpactBallForceHalfSineFrequency"]))
                        if "ImpactBallForceHalfSineAmplitude" in outputOption:
                            curFileName = curFileName.replace("_IBFHSA","_{0}".format(outputOption["ImpactBallForceHalfSineAmplitude"]))
                        if "MeshSize" in outputOption:
                            curFileName = curFileName.replace("_MS","_{0}".format(outputOption["MeshSize"]))
                        if "ImpactBallMeshSize" in outputOption:
                            curFileName = curFileName.replace("_IBMS","_{0}".format(outputOption["ImpactBallMeshSize"]))
                        if "ImpactBallMeshSizeRefine" in outputOption:
                            curFileName = curFileName.replace("_IBMSR","_{0}".format(outputOption["ImpactBallMeshSizeRefine"]))
                        if "BacksideWallMeshSize" in outputOption:
                            curFileName = curFileName.replace("_BWMS","_{0}".format(outputOption["BacksideWallMeshSize"]))
                        if "ThicknessOffset" in outputOption:
                            curFileName = curFileName.replace("_TO","_{0}".format(outputOption["ThicknessOffset"]))
                        if "BacksideWallThickness" in outputOption:
                            curFileName = curFileName.replace("_BWT","_{0}".format(outputOption["BacksideWallThickness"]))
                        if "BacksideWallNumberofElementsinThickness" in outputOption:
                            curFileName = curFileName.replace("_BWNEIT","_{0}".format(outputOption["BacksideWallNumberofElementsinThickness"]))                        
                        if "BacksideWallElasticModulus" in outputOption:
                            curFileName = curFileName.replace("_BWEM","_{0}".format(outputOption["BacksideWallElasticModulus"]))
                        if "BacksideWallPoissonRatio" in outputOption:
                            curFileName = curFileName.replace("_BWPR","_{0}".format(outputOption["BacksideWallPoissonRatio"]))
                        if "BacksideWallDensity" in outputOption:
                            curFileName = curFileName.replace("_BWD","_{0}".format(outputOption["BacksideWallDensity"]))
                        
                        self.dynaFileList.append(curFileName)
                        continue
                
                elif "**AddScript" in sline:
                    sline = file.readline()
                    script = ""
                    while True:
                        if "**" in sline:
                            break
                        script += sline
                        sline = file.readline()                        
                    
                sline = file.readline()
        self.addScriptList.append(script)
        self.outputOptionList.append(outputOption)
        return outputOption

    def SetMeshPath(self, meshPath):
        self.meshGenerationMode = True
        self.meshPath = os.getcwd() + "\\" + meshPath
        if not os.path.exists(self.meshPath):
            os.makedirs(self.meshPath)

    def SetPreMaxMeshID(self, maxNID, maxEID, maxPID, maxSID, maxMID):
        self.maxNID = maxNID
        self.maxEID = maxEID
        self.maxPID = maxPID
        self.maxSID = maxSID
        self.maxMID = maxMID

    def SetImpactBallScenario(self, outputOption):
        impactBallLocation = outputOption["ImpactBallLocation"]
        impactBallDirection = outputOption["ImpactBallDirection"]
        impactBallRadius = outputOption["ImpactBallRadius"]
        impactBallHeight = outputOption["ImpactBallHeight"]
        if "ImpactBallElasticModulus" in outputOption:
            impactBallElasticModulus = outputOption["ImpactBallElasticModulus"]
        else:
            impactBallElasticModulus = 2.0E11
        if "ImpactBallPoissonRatio" in outputOption:
            impactBallPoissonRatio = outputOption["ImpactBallPoissonRatio"]
        else:
            impactBallPoissonRatio = 0.294
        if "ImpactBallDensity" in outputOption:
            impactBallDensity = outputOption["ImpactBallDensity"]
        else:
            impactBallDensity = 7840.0
            
        impactBallVelocity = outputOption["ImpactBallVelocity"]
        impactBallForceHalfSineFrequency = outputOption["ImpactBallForceHalfSineFrequency"]
        impactBallForceHalfSineAmplitude = outputOption["ImpactBallForceHalfSineAmplitude"]
        
        meshSizeBall = outputOption["ImpactBallMeshSize"]
        meshSizeBallRefine = outputOption["ImpactBallMeshSizeRefine"]
        meshSizeBacksideWall = outputOption["BacksideWallMeshSize"]
        thicknessOffset = outputOption["ThicknessOffset"]
        backsideWallThickness = outputOption["BacksideWallThickness"]
        backsideWallNumberofElementsinThickness = outputOption["BacksideWallNumberofElementsinThickness"]        
        
        if "BacksideWallElasticModulus" in outputOption:
            backsideWallElasticModulus = outputOption["BacksideWallElasticModulus"]
        else:
            backsideWallElasticModulus = 2.0E11
        if "BacksideWallPoissonRatio" in outputOption:
            backsideWallPoissonRatio = outputOption["BacksideWallPoissonRatio"]
        else:
            backsideWallPoissonRatio = 0.294
        if "BacksideWallDensity" in outputOption:
            backsideWallDensity = outputOption["BacksideWallDensity"]
        else:
            backsideWallDensity = 7840.0


        minX, minY, minZ, maxX, maxY, maxZ = self.dynaImporter.FindBoundBox()
        center = [(minX + maxX)/2, (minY + maxY)/2, (minZ + maxZ)/2]
        xLoc = impactBallLocation[0]
        yLoc = impactBallLocation[1]
        xLoc = xLoc.replace("CX", str(center[0]))
        yLoc = yLoc.replace("CY", str(center[1]))
        xLoc = xLoc.replace("XMIN", str(minX))
        xLoc = xLoc.replace("XMAX", str(maxX))
        yLoc = yLoc.replace("YMIN", str(minY))
        yLoc = yLoc.replace("YMAX", str(maxY))

        xLoc = eval(xLoc)
        yLoc = eval(yLoc)
        zLoc = maxZ + impactBallRadius + thicknessOffset
        # generate sphere from BRepBuilderAPI
        
        angle1 = -90.0/180.0*math.pi  # Start angle from the vertical axis
        angle2 = 0.0/180.0*math.pi  # End angle from the vertical axis (90 degrees for the bottom half)
        angle3 = 360.0/180.0*math.pi  # Full rotation in the horizontal plane

        sphere = BRepPrimAPI_MakeSphere(gp_Pnt(xLoc, yLoc, zLoc), impactBallRadius,angle1,angle2,angle3).Shape()

        # backside wall

        xbwMin = minX - center[0]/2.0
        xbwMax = maxX + center[0]/2.0
        ybwMin = minY - center[1]/2.0
        ybwMax = maxY + center[1]/2.0
        zbwMin = minZ - backsideWallThickness - thicknessOffset
        zbwMax = minZ - thicknessOffset
        wire = BRepBuilderAPI_MakePolygon(gp_Pnt(xbwMin, ybwMin, zbwMin), gp_Pnt(xbwMax, ybwMin, zbwMin), gp_Pnt(xbwMax, ybwMax, zbwMin), gp_Pnt(xbwMin, ybwMax, zbwMin),True).Wire()
        face = BRepBuilderAPI_MakeFace(wire).Face()
        backsideWall = BRepPrimAPI_MakePrism(face, gp_Vec(0,0,zbwMax-zbwMin)).Shape()

        zTop = zLoc
        zBottom = zbwMin
        self.zTopList.append(zLoc)
        self.ZBottomList.append(zbwMin)

        if self.meshGenerationMode:
            nodeManager = self.dynaImporter.nodeManager 
            meshManager = KooMeshManagerGMSH(nodeManager)
            meshManager.SetPath(self.meshPath)
            meshManager.SetName("ImpactBall")
            if meshSizeBallRefine == meshSizeBall:
                meshManager.mesh_shape(sphere,meshSizeBall,meshSizeBall,3,None,self.maxNID,self.maxEID)
            else:
                center = [xLoc, yLoc, zLoc-impactBallRadius]
                charLength = impactBallRadius
                meshManager.mesh_shape_refine(sphere,meshSizeBall,meshSizeBallRefine,center,charLength,3,None,self.maxNID,self.maxEID)


            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
            self.maxPID += 1
            
            materialBall = self.dynaImporter.matManager.CreateElasticMaterial("ImpactBallMaterial",impactBallDensity,impactBallElasticModulus,impactBallPoissonRatio)            
            sectionBall = self.dynaImporter.sectionManager.CreateSolidSection("ImpactBallSection",1)
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetMaterialID(materialBall.id)
            meshManager.part.SetSectionID(sectionBall.id)
            self.maxSID += 1
            self.maxMID += 1
            meshManager.part.name = "ImpactBall"
            
            self.ballImpactorMeshList.append(meshManager)
            self.ballImpactorPartIDList.append(self.maxPID)

            meshManager = KooMeshManagerGMSH(nodeManager)
            meshManager.SetPath(self.meshPath)
            meshManager.SetName("BacksideWall")
            meshManager.mesh_shape(backsideWall,meshSizeBacksideWall,meshSizeBacksideWall,3,None,self.maxNID,self.maxEID)
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
            self.maxPID += 1            
            materialWall = self.dynaImporter.matManager.CreateElasticMaterial("BacksideWallMaterial",backsideWallDensity,backsideWallElasticModulus,backsideWallPoissonRatio)
            sectionWall = self.dynaImporter.sectionManager.CreateSolidSection("BacksideWallSection",1)
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetMaterialID(materialWall.id)
            meshManager.part.SetSectionID(sectionWall.id)
            self.maxSID += 1
            self.maxMID += 1
            meshManager.part.name = "BacksideWall"
            self.backsideWallMeshList.append(meshManager)
            self.backsideWallPartIDList.append(self.maxPID)


        if __name__ == "__main__":
            display.DisplayShape(sphere, update=True)
            display.FitAll()

    def AddPartstoDynaImporter(self):
        partMan : KooPartManager = self.dynaImporter.partManager
        for meshManager in self.ballImpactorMeshList:
            partMan.AddPartfromKooPart(meshManager.part.id, meshManager.part)
        for meshManager in self.backsideWallMeshList:
            partMan.AddPartfromKooPart(meshManager.part.id, meshManager.part)

    def ExportDyna(self, filePath, controlKeywords="",constrainedKeywords="",defineKeywords="",databaseKeywords="", setKeywords="",boundaryKeywords="", sectionKeywords="",materialKeywords="", contactKeywords="",loadKeywords="",addScripts=""):
        with open(filePath, "w") as file:
            file.write("*KEYWORD\n")
            file.write("*TITLE\n")
            title = os.path.basename(filePath)
            file.write(title + "\n")
            addString = self.dynaImporter.matManager.WritetoDynaKeyword(0)
            file.write(addString)
            if len(materialKeywords) > 0:
                file.write(materialKeywords)
            addString = self.dynaImporter.sectionManager.WritetoDynaKeyword(0)
            file.write(addString)
            if len(sectionKeywords) > 0:
                file.write(sectionKeywords)

            if len(controlKeywords) > 0:
                file.write(controlKeywords)
            if len(databaseKeywords) > 0:
                file.write(databaseKeywords)
            if len(defineKeywords) > 0:
                file.write(defineKeywords)
            for i in self.dynaImporter.partManager.parts:
                part : KooPart = self.dynaImporter.partManager.parts[i]
                addString = part.WritetoDynaPart()
                file.write(addString)
                #addString = part.WritetoDynaNodes(0)
                #file.write(addString)
                addString = part.WritetoDynaElements(0,0)
                file.write(addString)        
            addString = self.dynaImporter.nodeManager.WritetoDynaKeyword(0)
            file.write(addString)
            addString = self.dynaImporter.partManager.nodeManager.WritetoDynaKeyword(0)
            file.write(addString)
            addString = self.dynaImporter.partManager.elementManager.WritetoDynaKeyword(0,0,0)
            file.write(addString)
            if len(setKeywords) > 0:
                file.write(setKeywords)        
            if len(boundaryKeywords) > 0:
                file.write(boundaryKeywords)            
            if len(contactKeywords) > 0:
                file.write(contactKeywords)
            if len(constrainedKeywords) > 0:
                file.write(constrainedKeywords)
            if len(loadKeywords) > 0:
                file.write(loadKeywords)

            '''
            *DATABASE_GLSTAT
            *DATABASE_MATSUM
            *BOUNDARY_PRESCRIBED_MOTION_RIGID
            *MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE            
            *MAT_RIGID_TITLE
            '''
            file.write(addScripts)
            file.write("*END")
            file.close()

    def GenerateHalfSineCurve(self, dt, tFinal, frequency, amplitude):
        tList = [] 
        fList = [] 
        t = 0.0
        while t < tFinal:
            # t to exponential float such as 1.0e-16
            t = round(t,16)            
            #t = round(t,16)
            # exponential float
            
            tList.append(t)
            if t < 1.0/frequency/2.0:
                curVal = amplitude*math.sin(2*math.pi*frequency*t)
                # 20 digit
                curVal = round(curVal,16)
                fList.append(curVal)
            else:
                fList.append(0.0)
            t += dt
        return tList, fList

    def SetImpactBallLoadBoundary(self, outputOption, ballPart : KooPart, backWallPart : KooPart, nodeMan : NodeManager, topZ, bottomZ, addScripts = ""):

        impactBallLocation = outputOption["ImpactBallLocation"]
        impactBallDirection = outputOption["ImpactBallDirection"]
        impactBallRadius = outputOption["ImpactBallRadius"]
        impactBallHeight = outputOption["ImpactBallHeight"]
        impactBallVelocity = outputOption["ImpactBallVelocity"]
        if "ImpactBallPointMass" in outputOption:
            impactBallPointMass = outputOption["ImpactBallPointMass"]
        else:
            impactBallPointMass = 0.00000001
        impactBallForceHalfSineFrequency = outputOption["ImpactBallForceHalfSineFrequency"]
        impactBallForceHalfSineAmplitude = outputOption["ImpactBallForceHalfSineAmplitude"]
        meshSize = outputOption["MeshSize"]
        thicknessOffset = outputOption["ThicknessOffset"]
        backsideWallThickness = outputOption["BacksideWallThickness"]
        backsideWallNumberofElementsinThickness = outputOption["BacksideWallNumberofElementsinThickness"]        

        controlIO = StringIO()
        defineIO = StringIO()
        constrainedIO = StringIO()
        databaseIO = StringIO()
        setKeywordIO = StringIO()
        boundaryKeywordsIO = StringIO()
        sectionKeywordsIO = StringIO()
        materialKeywordsIO = StringIO()
        contactKeywordsIO = StringIO()
        loadKeywordsIO = StringIO()
        

        control_termination = ControlTermination()
        ENDTIM = outputOption["TFinal"]
        ENDCYC = 0
        DTMIN = 1.0E-10
        ENDENG = 0.0
        ENDMAS = 10000000.0
        NOSOL = 0
        #### Control Termination
        control_termination.SetControlTermination(ENDTIM, ENDCYC, DTMIN, ENDENG, ENDMAS, NOSOL)
        control_termination.write(controlIO)
        #### Control_Timestep
        control_timestep = ControlTimeStep()
        DTINIT = 0.0
        TSSFAC = 0.7
        ISDO = 0
        TSLIMT = 0.0
        DT2MS = 0.0
        LCTM = 0 
        ERODE = 1
        MSIST = 0 
        control_timestep.SetControlTimeStep(DTINIT, TSSFAC, ISDO, TSLIMT, DT2MS, LCTM, ERODE, MSIST)        
        control_timestep.write(controlIO)
        #### Control_Contact
        control_Contact = ControlContact()
        slsfac = 0.1
        rwpnal = 0.1
        islchk = 1
        shlthk = 0
        penopt = 1 
        thkchg = 0
        orien = 1
        enmass = 0
        usrstr = 0
        usrfrc = 0
        nsbcs = 0
        interm = 0
        xpene = 4.0
        ssthk = 1
        ecdt = 0
        tiedprj = 0
        sfric = 0.0
        dfric = 0.0
        edc = 0.0
        vfc = 0.0
        th = 0.0
        th_sf = 0.0
        pen_sf = 0.0
        ignore = 1
        frceng = 0
        skiprwg = 0
        outseg = 0
        spotstp = 0
        spotdel = 0
        spothin = 0.0
        isym = 0
        nserod = 0
        rwgaps = 1
        rwgdth = 0.0
        rwksf = 1.0
        icov = 0
        swradf = 0.0
        ithoff = 0
        shledg = 0
        pstiff = 0
        ithcnt = 0
        tdcnof = 0
        ftall = 0
        unused = ""
        shltrw = 0.0
        igactc = 0
        control_Contact.AddControlContact(slsfac, rwpnal, islchk, shlthk, penopt, thkchg, orien, enmass, usrstr, usrfrc, nsbcs, interm, xpene, ssthk, ecdt, tiedprj, sfric, dfric, edc, vfc, th, th_sf, pen_sf, ignore, frceng, skiprwg, outseg, spotstp, spotdel, spothin, isym, nserod, rwgaps, rwgdth, rwksf, icov, swradf, ithoff, shledg, pstiff, ithcnt, tdcnof, ftall, unused, shltrw, igactc)
        control_Contact.write(controlIO)
        #### Control_Hourglass
        control_Hourglass = ControlHourglass()
        ihq = 5
        qh = 0.1
        control_Hourglass.AddControlHourglass(ihq, qh)
        #### nodout elout 
        dt = outputOption["DT"]
        binary = 1
        lcur = 0
        ioopt = 1
        nodoutKeyword = DatabaseNodout()
        nodoutKeyword.AddDatabaseNodout(dt, binary, lcur, ioopt)
        nodoutKeyword.write(databaseIO)
        eloutKeyword = DatabaseElout()
        eloutKeyword.AddDatabaseElout(dt, binary, lcur, ioopt)
        eloutKeyword.write(databaseIO)
        #### binary d3plot
        binaryD3plot = DatabaseBinaryD3plot()
        DTCYCL = dt
        LCDT = ""
        BEAM = 0
        NPLTC = int(ENDTIM/dt)
        PSETID = 0 
        binaryD3plot.AddDatabaseBinaryD3plot(DTCYCL, LCDT, BEAM, NPLTC, PSETID)
        binaryD3plot.write(databaseIO)

        #### Define curve 
        defineCurve = DefineCurve()
        LCID = 1
        SIDR = 0
        SFA = 1.0
        SFO = 1.0
        OFFA = 0.0
        OFFO = 0.0
        DATTYP = 0
        LCINT = 0
        A1List, O1List = self.GenerateHalfSineCurve(dt/10.0,ENDTIM,impactBallForceHalfSineFrequency,impactBallForceHalfSineAmplitude)
        defineCurve.AddDefineCurve(LCID, SIDR, SFA, SFO, OFFA, OFFO, DATTYP, LCINT, A1List, O1List)
        defineCurve.write(defineIO)


        ##### Set Node List 

        zTopNodes = ballPart.GetNodesZRange(topZ-1.e-7,topZ+1.e-7)
        zBottomNodes = backWallPart.GetNodesZRange(bottomZ-1.e-7,bottomZ+1.e-7)
        ballNodes = ballPart.GetNodesonPart()

        zbnList = SetNodeListTitle()
        ztnList = SetNodeListTitle()
        ztn2List = SetNodeListTitle()
        ballnList = SetNodeListTitle()
        zBottomNodeIDList = []
        zTopNodeIDList = []
        zTopNode2IDList = []
        ballNodeIDList = []
        for node in zBottomNodes:
            zBottomNodeIDList.append(ballPart.nodeManager.nodes[node].id)
        for node in zTopNodes:
            zTopNodeIDList.append(ballPart.nodeManager.nodes[node].id)
        
        for node in ballNodes:
            ballNodeIDList.append(ballPart.nodeManager.nodes[node].id)

        centerXTop = 0.0
        centerYTop = 0.0
        centerZTop = 0.0
        for node in zTopNodes:
            centerXTop += ballPart.nodeManager.nodes[node].x
            centerYTop += ballPart.nodeManager.nodes[node].y
            centerZTop += ballPart.nodeManager.nodes[node].z
        centerXTop /= len(zTopNodes)
        centerYTop /= len(zTopNodes)
        centerZTop /= len(zTopNodes)
        dNode = self.dynaImporter.partManager.AddIndependentNode(centerXTop, centerYTop, centerZTop)
        zTopNode2IDList.append(dNode.id)

        da1 = 0.0
        da2 = 0.0
        da3 = 0.0
        da4 = 0.0
        solver = "MECH"
        sidzbn = 1
        sidztn = 2
        sidztn2 = 3
        sidbn = 4
        namezbn = "BottomNodes"
        nameztn = "TopNodes"
        nameztn2 = "IndependentNode"
        namebn = "BallNodes"
        its = 0
        zbnList.AddSetNodeList(namezbn,sidzbn,da1, da2, da3, da4,solver,its,zBottomNodeIDList)
        ztnList.AddSetNodeList(nameztn,sidztn,da1, da2, da3, da4,solver,its,zTopNodeIDList)
        ztn2List.AddSetNodeList(nameztn2,sidztn2,da1, da2, da3, da4,solver,its,zTopNode2IDList)
        ballnList.AddSetNodeList(namebn,sidbn,da1, da2, da3, da4,solver,its,ballNodeIDList)

        zbnList.write(setKeywordIO)
        ztnList.write(setKeywordIO)
        ztn2List.write(setKeywordIO)
        ballnList.write(setKeywordIO)

        #### Constrained 

        lcid = 1
        dnid = dNode.id
        ddof = "3"
        CIDD = ""
        ITYP = 0
        IDNSW = 1
        FGM = 0
        idofList = []
        for i in zTopNodeIDList:
            idofList.append("123")
        rbe3 = ConstrainedInterpolation()
        rbe3.AddConstrainedInterpolation(lcid, dnid, ddof, CIDD, ITYP, IDNSW, FGM,zTopNodeIDList, idofList)
        rbe3.write(constrainedIO)

        rbe2 = ConstrainedNodeSet()
        nsid = sidztn2
        dof = 4
        tf = 1.0e20
        rbe2.AddConstrainedNodeSet(nsid, dof, tf)
        rbe2.write(constrainedIO)


        #### Load
        lnpoint = LoadNodePoint()
        dof = 3 
        sf = -1.0 
        lcid = 1 
        lnpoint.AddLoadNodePoint(dNode.id,dof,lcid,sf)
        lnpoint.write(loadKeywordsIO)
        
        self.dynaImporter.partManager.CreatePointElement(dNode,impactBallPointMass)

        #### Initial Velocity 
        ivel = impactBallVelocity
        iheight = impactBallHeight
        fvel = ivel + math.sqrt(2.0*9.81*iheight)
        # exponential form with 10 digit
        fvel = "{:.4e}".format(fvel) 
        fvel = float(fvel)
        ivel = InitialVelocity()
        ivel.AddInitialVelocity(sidbn,NSIDEX=0,BOXID=0,IRIGID=0,ICID=0,VX=0,VY=0,VZ=-fvel,VXR=0.0,VYR=0.0,VZR=0.0)
        ivel.write(defineIO)

        ###### Set Boundary SPD 
        bspcid = 1
        spcls = BoundarySPCSet()
        spcls.AddBoundarySPCSet(sidzbn,0,0,0,1,0,0,0)
        spcls.write(boundaryKeywordsIO)
        
        
        ###### contact 
        MSIDImpactBall = ballPart.id
        MSIDBacksideWall = backWallPart.id
           
        SSTYP = 3
        MSTYP = 3
        SBOXID = 0
        MBOXID = 0
        SPR = 0
        MPR = 0
        FS = 0.0
        FD = 0.0
        DC = 0.0
        VC = 0.0
        VDC = 0.0
        PENCHK = 0
        BT = 0.00
        DT = 1.00000E20
        SFS = ""
        SFM = ""
        SST = ""
        MST = ""
        SFST = ""
        SFMT = ""
        FSF = ""
        VSF = ""   
        prevMaxContactID = 0 

        allPartIDList = [] 
        allPartDimensionist = [] 
        allPartCenterZList = []
        allPartModelType = [] 
        partMan = self.dynaImporter.partManager
        secMan = self.dynaImporter.sectionManager
        for pid in partMan.parts:
            if pid == MSIDImpactBall or pid == MSIDBacksideWall:
                continue
            allPartIDList.append(pid)             
            allPartDimensionist.append(partMan.parts[pid].GetPartDimension())            
            allPartCenterZList.append(partMan.parts[pid].GetCenterZ())
            partMan.parts[pid].SetModelTypebySection(secMan)
            
            allPartModelType.append(partMan.parts[pid].modelType)
               # change the order of the part by center Z
        
        for i in range(len(allPartCenterZList)):
            for j in range(i+1, len(allPartCenterZList)):
                if allPartCenterZList[i] > allPartCenterZList[j]:
                    temp = allPartCenterZList[i]
                    allPartCenterZList[i] = allPartCenterZList[j]
                    allPartCenterZList[j] = temp
                    temp = allPartIDList[i]
                    allPartIDList[i] = allPartIDList[j]
                    allPartIDList[j] = temp
                    temp = allPartDimensionist[i]
                    allPartDimensionist[i] = allPartDimensionist[j]
                    allPartDimensionist[j] = temp

        autoSurfacetoSurface = ContactAutomaticSurfaceToSurfaceID()
        partID = allPartIDList[len(allPartIDList)-1]
        prevMaxContactID = prevMaxContactID + 1
        FS = 0.2
        FD = 0.2
        autoSurfacetoSurface.AddAutomaticSurfacetoSurfaceID(prevMaxContactID,"{0}toImpactBallContact".format(partID), partID, MSIDImpactBall, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        partID = allPartIDList[0]        
        FS = 0.2
        FD = 0.2
        prevMaxContactID = prevMaxContactID + 1        
        autoSurfacetoSurface.AddAutomaticSurfacetoSurfaceID(prevMaxContactID,"{0}toBacksideWallContact".format(partID), partID, MSIDBacksideWall, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        autoSurfacetoSurface.write(contactKeywordsIO)
        
        if "$$ AUTOMATIC SINGLE CONTACT" in addScripts:
            prevMaxContactID = prevMaxContactID + 1
            autoSingle = ContactSingleSurfaceID()
            SOFT = 2
            autoSingle.AddContactSingleSurfaceID(prevMaxContactID,"ALL", 0, 0, 5, 5, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF, SOFT)
            autoSingle.write(contactKeywordsIO)
        if "$$ AUTOMATIC GENERAL CONTACT" in addScripts:
            prevMaxContactID = prevMaxContactID + 1        
            autoGeneral = ContactAutomaticGeneralID()
            autoGeneral.AddContactAutomaticGeneralID(prevMaxContactID,"ALL", 0, 0, 5, 5, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
            autoGeneral.write(contactKeywordsIO)
        if "$$ NO ADDITIONAL CONTACT" in addScripts or "$$ NO INTERNAL CONTACT" in addScripts:
            pass
        else:

            tiedShelltoShellSurface = ContactTiedShellEdgeToSurfaceBeamOffsetID()
            #tiedSolidtoSolidSurface = ContactTiedSurfaceToSurfaceID()#ContactAutomaticSurfaceToSurfaceID()
            tiedSolidtoSolidSurface = ContactAutomaticSurfaceToSurfaceID()
            tiedShelltoSolidSurface = ContactTiedSurfaceToSurfaceOffsetID() 
            tiedFEMtoPeriSurface = ContactFEMPERITieBreakID()
            for i in range(len(allPartIDList)-1):            
                prevMaxContactID = prevMaxContactID + 1            
                partID = allPartIDList[i]
                nextPartID = allPartIDList[i+1]
                name = "{0}to{1}".format(partID,nextPartID)

                #FS = 0.2
                #FD = 0.2            
                SFS = 1.0
                SFM = 1.0
                SFST = 1.0
                SFMT = 1.0
                FSF = 1.0
                VSF = 1.0
                SSTYP = 3
                MSTYP = 3
                #autoSurfacetoSurface.AddAutomaticSurfacetoSurfaceID(prevMaxContactID,"{0}to{1}".format(partID,nextPartID), partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                #tiedSurface.AddContactTiedShellEdgeToSurface(partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                if allPartModelType[i] == "PERI" and allPartModelType[i+1] == "FEM":                    
                    #FEMID
                    msid = allPartIDList[i+1]
                    #PERIID
                    ssid = allPartIDList[i]
                    tensile = 100.0E6
                    compressive = 2.0E20
                    
                    tiedFEMtoPeriSurface.AddContactFEMPERITieBreakID(prevMaxContactID,msid,ssid,tensile,compressive)                                        
                     
                elif allPartModelType[i] == "FEM" and allPartModelType[i+1] == "PERI":
                    msid = allPartIDList[i]
                    ssid = allPartIDList[i+1]
                    tensile = 100.0E6
                    compressive = 2.0E20                    
                    tiedFEMtoPeriSurface.AddContactFEMPERITieBreakID(prevMaxContactID,msid,ssid,tensile,compressive)                                        
                
                elif allPartDimensionist[i] == 3 and allPartDimensionist[i+1] == 3:
                    FS = 0.8
                    FD = 0.2
                    #tiedSolidtoSolidSurface.AddContactTiedSurfaceToSurfaceID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                    tiedShelltoSolidSurface.AddContactTiedSurfaceToSurfaceOffsetID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                    #tiedSolidtoSolidSurface.AddAutomaticSurfacetoSurfaceID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                
                elif allPartDimensionist[i] == 2 and allPartDimensionist[i+1] == 2:
                    FS = 0.2
                    FD = 0.2
                    tiedShelltoShellSurface.AddContactTiedShellEdgeToSurfaceBeamOffsetID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                
                else:
                    FS = 0.2
                    FD = 0.2
                    tiedShelltoSolidSurface.AddContactTiedSurfaceToSurfaceOffsetID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)

                        
            tiedShelltoShellSurface.write(contactKeywordsIO)
            tiedSolidtoSolidSurface.write(contactKeywordsIO)
            tiedShelltoSolidSurface.write(contactKeywordsIO)
            tiedFEMtoPeriSurface.write(contactKeywordsIO)
        

        controlIO.seek(0)
        defineIO.seek(0)
        constrainedIO.seek(0)
        databaseIO.seek(0)
        setKeywordIO.seek(0)
        boundaryKeywordsIO.seek(0)
        sectionKeywordsIO.seek(0)
        materialKeywordsIO.seek(0)
        contactKeywordsIO.seek(0)
        loadKeywordsIO.seek(0)
        
        controlKeywords = controlIO.read()
        constrainedKeywords = constrainedIO.read()
        defineKeywords = defineIO.read()
        databaseKeywords = databaseIO.read()
        setKeywords = setKeywordIO.read()
        boundaryKeywords = boundaryKeywordsIO.read()
        sectionKeywords = sectionKeywordsIO.read()
        materialKeywords = materialKeywordsIO.read()
        contactKeywords = contactKeywordsIO.read()
        loadKeywords = loadKeywordsIO.read()

        return controlKeywords, constrainedKeywords, defineKeywords, databaseKeywords, setKeywords, boundaryKeywords, sectionKeywords,materialKeywords, contactKeywords,loadKeywords

    def GenerateDynabyLoadBoundaryOption(self):
        for i in range(len(self.outputOptionList)):
            outputOption = self.outputOptionList[i]
            self.SetImpactBallScenario(outputOption)
            self.AddPartstoDynaImporter()
            partMan = self.dynaImporter.partManager
            ballPartID = self.ballImpactorPartIDList[i]
            backWallPartID = self.backsideWallPartIDList[i]
            ballPart : KooPart = partMan.parts[ballPartID]
            backWallPart : KooPart = partMan.parts[backWallPartID]
            nodeMan : NodeManager = self.dynaImporter.nodeManager

            topZ = self.zTopList[i]
            bottomZ = self.ZBottomList[i]

            controlKeywords, constrainedKeywords, defineKeywords, databaseKeywords, setKeywords, boundaryKeywords, sectionKeywords, materialKeywords, contactKeywords, loadKeywords = self.SetImpactBallLoadBoundary(outputOption, ballPart, backWallPart, nodeMan, topZ, bottomZ, self.addScriptList[i])
            if len(self.addScriptList) >i:
                self.ExportDyna(self.dynaFileList[i], controlKeywords, constrainedKeywords, defineKeywords, databaseKeywords, setKeywords, boundaryKeywords, sectionKeywords, materialKeywords, contactKeywords, loadKeywords, self.addScriptList[i])
            else:
                self.ExportDyna(self.dynaFileList[i], controlKeywords, constrainedKeywords, defineKeywords, databaseKeywords, setKeywords, boundaryKeywords, sectionKeywords, materialKeywords, contactKeywords, loadKeywords)
        return self.dynaFileList



if __name__ == "__main__":

    nodeMan = NodeManager()
    partMan = KooPartManager()
    secMan = KooSectionManager() 
    matMan = KooMaterialManager()
    resultMan = KooResultManager(nodeMan)

    dynaImporter = KooDynaImporter(nodeMan, partMan, resultMan, matMan, secMan)

    dir = os.getcwd()

    filePath = os.path.join(dir, "PackageInfoBoxMeshCompositeSolidMaterial.k")
    stepPath = os.path.join(dir, "PackageInfoBoxMeshCompositeSolidMaterial.step")

    outputOptionPath = os.path.join(dir, "OutputOptionBallImpact.txt")

    dynaImporter.importDynaFile(filePath)
    maxNID = dynaImporter.importNode()
    maxPID = dynaImporter.importPart()
    maxSID = dynaImporter.importSection()
    maxMID = dynaImporter.importMaterial()
    maxEID = dynaImporter.partManager.FindMaxEID()

    dynaScenarioMan = KooImpactSimulationGenerator(dynaImporter)
    dynaScenarioMan.SetPreMaxMeshID(maxNID, maxEID, maxPID, maxSID, maxMID)
    dynaScenarioMan.SetMeshPath("Meshes")
    dynaScenarioMan.ImportLoadBoundaryOption(outputOptionPath)    
    dynaScenarioMan.GenerateDynabyLoadBoundaryOption()
    

