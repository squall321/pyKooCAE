
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


class KooThreePointBendingSimulationGenerator():
    def __init__(self, dynaImporter : KooDynaImporter):
        self.dynaImporter : KooDynaImporter = dynaImporter
        self.bendingPushCylinderMeshList = []
        self.bendingSupportLeftCylinderMeshList = []
        self.bendingSupportRightCylinderMeshList = []
        self.bendingPushCylinderPartIDList = [] 
        self.bendingSupportLeftCylinderPartIDList = []
        self.bendingSupportRightCylinderPartIDList = []
        self.bendingZBottomList = [] 
        self.bendingZTopList = [] 

        self.meshGenerationMode = False
        self.meshPath = os.getcwd()
        self.meshSizeList = [ ]
        self.dynaFileList = []

        self.addScriptList = []

        self.outputOptionList = []

        self.LoadBoundaryOptionPath = ""

        self.maxNID = 0
        self.maxEID = 0
        self.maxPID = 0
        self.maxSID = 0 
        self.maxMID = 0
        self.maxNSID = 0 

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
                if "*END" in sline:
                    break
                elif "#" in sline:
                    sline = file.readline()
                    continue
                elif "*SimulationMode" in sline:                    
                    if "3ptbending" in sline.lower():
                        outputOption["SimulationMode"] = "3ptBending"
                        
                        while True: 
                            sline = file.readline()
                            if "*" in sline:
                                break
                            elif "#" in sline:
                                continue
                            svector = sline.split(",")
                            if "filename" in svector[0].lower():
                                curFileName = svector[1].strip()
                            elif "pushdirection" in svector[0].lower():
                                outputOption["PushDirection"] = [float(svector[1]), float(svector[2])]
                            elif "distancebetweensupportcylinder" in svector[0].lower():
                                outputOption["DistanceBetweenSupportCylinder"] = float(svector[1])
                            elif "pushcylinderradius" in svector[0].lower():
                                outputOption["PushCylinderRadius"] = float(svector[1])
                            elif "pushcylinderwidth" in svector[0].lower():
                                outputOption["PushCylinderWidth"] = float(svector[1])
                            elif "supportcylinderradius" in svector[0].lower():
                                outputOption["SupportCylinderRadius"] = float(svector[1])
                            elif "supportcylinderwidth" in svector[0].lower():
                                outputOption["SupportCylinderWidth"] = float(svector[1])
                            elif "thicknessoffset" in svector[0].lower():
                                outputOption["ThicknessOffset"] = float(svector[1])
                            elif "meshsize" in svector[0].lower():
                                outputOption["MeshSize"] = float(svector[1])
                            elif "pushcylinderelasticmodulus" in svector[0].lower():
                                outputOption["PushCylinderElasticModulus"] = float(svector[1])
                            elif "pushcylinderpoissonratio" in svector[0].lower():
                                outputOption["PushCylinderPoissonRatio"] = float(svector[1])
                            elif "pushcylinderdensity" in svector[0].lower():
                                outputOption["PushCylinderDensity"] = float(svector[1])
                            elif "supportcylinderelasticmodulus" in svector[0].lower():
                                outputOption["SupportCylinderElasticModulus"] = float(svector[1])
                            elif "supportcylinderpoissonratio" in svector[0].lower():
                                outputOption["SupportCylinderPoissonRatio"] = float(svector[1])
                            elif "supportcylinderdensity" in svector[0].lower():
                                outputOption["SupportCylinderDensity"] = float(svector[1])
                                
                        curFileName = curFileName.replace("_PD", "_{0}_{1}".format(str(outputOption["PushDirection"][0]), str(outputOption["PushDirection"][1])))
                        curFileName = curFileName.replace("_DBSC", "_{0}".format(str(outputOption["DistanceBetweenSupportCylinder"])))
                        curFileName = curFileName.replace("_PCR", "_{0}".format(str(outputOption["PushCylinderRadius"])))
                        curFileName = curFileName.replace("_PCW", "_{0}".format(str(outputOption["PushCylinderWidth"])))
                        curFileName = curFileName.replace("_SCR", "_{0}".format(str(outputOption["SupportCylinderRadius"])))
                        curFileName = curFileName.replace("_SCW", "_{0}".format(str(outputOption["SupportCylinderWidth"])))
                        curFileName = curFileName.replace("_TO", "_{0}".format(str(outputOption["ThicknessOffset"])))
                        curFileName = curFileName.replace("_MS", "_{0}".format(str(outputOption["MeshSize"])))
                        if "PushCylinderElasticModulus" in outputOption:
                            curFileName = curFileName.replace("_PCEM", "_{0}".format(str(outputOption["PushCylinderElasticModulus"])))
                        if "PushCylinderPoissonRatio" in outputOption:
                            curFileName = curFileName.replace("_PCPR", "_{0}".format(str(outputOption["PushCylinderPoissonRatio"])))
                        if "PushCylinderDensity" in outputOption:
                            curFileName = curFileName.replace("_PCD", "_{0}".format(str(outputOption["PushCylinderDensity"])))
                        if "SupportCylinderElasticModulus" in outputOption:
                            curFileName = curFileName.replace("_SCEM", "_{0}".format(str(outputOption["SupportCylinderElasticModulus"])))
                        if "SupportCylinderPoissonRatio" in outputOption:
                            curFileName = curFileName.replace("_SCPR", "_{0}".format(str(outputOption["SupportCylinderPoissonRatio"])))
                        if "SupportCylinderDensity" in outputOption:
                            curFileName = curFileName.replace("_SCD", "_{0}".format(str(outputOption["SupportCylinderDensity"])))
                        
                        self.dynaFileList.append(curFileName)                        
                        continue
                        
                elif "*ExperimentData" in sline:
                    sline = file.readline()
                    sline.replace("\n","")
                    svector = sline.split(",")
                    titleList = svector
                    values = []
                    while True:
                        sline = file.readline()
                        sline.replace("\n","")
                        if "*" in sline:
                            break
                        elif "#" in sline:
                            continue
                        svector = sline.split(",")
                        # svector to float vector 
                        fvector = []
                        for s in svector:
                            fvector.append(float(s))                            
                        values.append(fvector)
                    for i in range(len(values)):
                        if i == 0:
                            for j in range(len(values[0])):
                                titleList[j] = titleList[j].strip()
                                outputOption[titleList[j]] = []
                        for j in range(len(values[0])):
                            outputOption[titleList[j]].append(values[i][j])                           
                    continue
                elif "*ControlMode" in sline:
                    sline = file.readline()
                    if "force" in sline.lower():
                        outputOption["ControlMode"] = "Force"
                    elif "displacement" in sline.lower():
                        outputOption["ControlMode"] = "Displacement"
                elif "**AddScript" in sline:
                    sline = file.readline()                    
                    script = ""
                    while True:
                        if "**" in sline:
                            break
                        script = script + sline
                        sline = file.readline()                                            
                    continue
                        
                elif "*End" in sline:
                    break
                sline = file.readline()
        self.addScriptList.append(script)
        self.outputOptionList.append(outputOption)
        return outputOption

    def SetMeshPath(self, meshPath):
        self.meshGenerationMode = True
        self.meshPath = os.getcwd() + "\\" + meshPath
        # if it is not exist, create the folder
        if not os.path.exists(self.meshPath):
            os.makedirs(self.meshPath)

    def SetPreMaxMeshID(self, maxNID, maxEID, maxPID, maxSID, maxMID, maxNSID):
        self.maxNID = maxNID
        self.maxEID = maxEID
        self.maxPID = maxPID   
        self.maxSID = maxSID
        self.maxMID = maxMID
        self.maxNSID = maxNSID
    
    def SetThreePointBendingScenario(self,outputOption):
        directionX = outputOption["PushDirection"][0] 
        directionY = outputOption["PushDirection"][1]
        distanceSupportCylinder = outputOption["DistanceBetweenSupportCylinder"]
        pushCylinderRadius = outputOption["PushCylinderRadius"]
        pushCylinderWidth = outputOption["PushCylinderWidth"] 
        supportCylinderRadius = outputOption["SupportCylinderRadius"] 
        supportCyllinderWidth = outputOption["SupportCylinderWidth"] 
        thickness = outputOption["ThicknessOffset"]
        meshSize = outputOption["MeshSize"] 
        

        minX, minY, minZ, maxX, maxY, maxZ = self.dynaImporter.FindBoundBox()
        # Find the center of the part
        center = gp_Pnt((maxX + minX) / 2, (maxY + minY) / 2, (maxZ + minZ) / 2)
        # Find the axis direction
        axis = gp_Dir(directionX, directionY, 0)
        
        # inplane bu t normal to (directonX, directionY, 0) direction
        axis2 = gp_Dir(-directionY, directionX, 0)

        if pushCylinderWidth <= 0:
            pushCylinderWidth = maxY-minY
        if supportCyllinderWidth <= 0:
            supportCyllinderWidth = maxY-minY
        # Find vector for support cylinder
        supportCylinderVector = gp_Vec(axis.X(), axis.Y(), axis.Z())
        supportCylinderVector.Multiply(distanceSupportCylinder/2.0)

        pcpntCenter = gp_Pnt(center.X() +axis2.X()*pushCylinderWidth/2.0, center.Y() + axis2.Y()*pushCylinderWidth/2.0, maxZ+0.0000001 + pushCylinderRadius + thickness/2.0)
        pcpntStart = gp_Pnt(center.X() +axis2.X()*pushCylinderWidth/2.0+axis.X()*pushCylinderRadius, center.Y() + axis2.Y()*pushCylinderWidth/2.0+axis.Y()*pushCylinderRadius, maxZ + 0.0000001 + pushCylinderRadius + thickness/2.0)
        pcpntEnd = gp_Pnt(center.X() +axis2.X()*pushCylinderWidth/2.0-axis.X()*pushCylinderRadius, center.Y() + axis2.Y()*pushCylinderWidth/2.0-axis.Y()*pushCylinderRadius, maxZ + 0.0000001 + pushCylinderRadius + thickness/2.0)

        self.bendingZTopList.append(maxZ + 0.0000001 + pushCylinderRadius + thickness/2.0)

        # arc for push cylinder pcpnt2, pcpnt1, pcpnt3        
        coordinate_system = gp_Ax2(pcpntCenter, axis2)
        radius = pushCylinderRadius
        arc = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system, radius), pcpntStart, pcpntEnd)
        arc = arc.Edge()
        line1 = BRepBuilderAPI_MakeEdge(pcpntStart, pcpntCenter).Edge()
        line2 = BRepBuilderAPI_MakeEdge(pcpntCenter, pcpntEnd).Edge()
        wire_builder = BRepBuilderAPI_MakeWire()
        wire_builder.Add(arc)
        wire_builder.Add(line1)
        wire_builder.Add(line2)
        wire = wire_builder.Wire()
        face_builder = BRepBuilderAPI_MakeFace(wire, True)
        face_builder.Build()
        face = face_builder.Face()
        prism_builder = BRepPrimAPI_MakePrism(face, gp_Vec(directionY*pushCylinderWidth, -directionX*pushCylinderWidth, 0))

        prism_builder.Build()
        solidPush = prism_builder.Shape()
        axis2 = gp_Dir(directionY, -directionX, 0)
        scpntLeftCenter = gp_Pnt(center.X() + axis2.X()*supportCyllinderWidth/2.0-axis.X()*(distanceSupportCylinder/2.0-supportCylinderRadius), center.Y() + axis2.Y()*supportCyllinderWidth/2.0-axis.Y()*(distanceSupportCylinder/2.0-supportCylinderRadius), minZ-0.0000001-supportCylinderRadius - thickness/2.0)
        scpntLeftStart = gp_Pnt(center.X() + axis2.X()*supportCyllinderWidth/2.0-axis.X()*(distanceSupportCylinder/2.0-supportCylinderRadius)+axis.X()*supportCylinderRadius, center.Y() + axis2.Y()*supportCyllinderWidth/2.0-axis.Y()*(distanceSupportCylinder/2.0-supportCylinderRadius)+axis.Y()*supportCylinderRadius, minZ-0.0000001-supportCylinderRadius - thickness/2.0)
        scpntLeftEnd = gp_Pnt(center.X() + axis2.X()*supportCyllinderWidth/2.0-axis.X()*(distanceSupportCylinder/2.0-supportCylinderRadius)-axis.X()*supportCylinderRadius, center.Y() + axis2.Y()*supportCyllinderWidth/2.0-axis.Y()*(distanceSupportCylinder/2.0-supportCylinderRadius)-axis.Y()*supportCylinderRadius, minZ-0.0000001-supportCylinderRadius - thickness/2.0)

        self.bendingZBottomList.append(minZ-0.0000001-supportCylinderRadius - thickness/2.0)
        

        coordinate_system_support_left = gp_Ax2(scpntLeftCenter, axis2)
        radius = supportCylinderRadius
        arc = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system_support_left, radius), scpntLeftStart, scpntLeftEnd)
        arc = arc.Edge()
        line1 = BRepBuilderAPI_MakeEdge(scpntLeftStart, scpntLeftCenter).Edge()
        line2 = BRepBuilderAPI_MakeEdge(scpntLeftCenter, scpntLeftEnd).Edge()
        wire_builder = BRepBuilderAPI_MakeWire()
        wire_builder.Add(arc)
        wire_builder.Add(line1)
        wire_builder.Add(line2)
        wire = wire_builder.Wire()
        face_builder = BRepBuilderAPI_MakeFace(wire, True)
        face_builder.Build()
        face = face_builder.Face()
        prism_builder = BRepPrimAPI_MakePrism(face, gp_Vec(-directionY*supportCyllinderWidth, directionX*supportCyllinderWidth, 0))
        prism_builder.Build()
        solidSupportLeft = prism_builder.Shape()

        scpntRightCenter = gp_Pnt(center.X() - axis2.X()*supportCyllinderWidth/2.0+axis.X()*(distanceSupportCylinder/2.0-supportCylinderRadius), center.Y() - axis2.Y()*supportCyllinderWidth/2.0+axis.Y()*(distanceSupportCylinder/2.0-supportCylinderRadius), minZ-0.0000001-supportCylinderRadius - thickness/2.0)
        scpntRightStart = gp_Pnt(center.X() - axis2.X()*supportCyllinderWidth/2.0+axis.X()*(distanceSupportCylinder/2.0-supportCylinderRadius)+axis.X()*supportCylinderRadius, center.Y() - axis2.Y()*supportCyllinderWidth/2.0+axis.Y()*(distanceSupportCylinder/2.0-supportCylinderRadius)+axis.Y()*supportCylinderRadius, minZ-0.0000001-supportCylinderRadius - thickness/2.0)
        scpntRightEnd = gp_Pnt(center.X() - axis2.X()*supportCyllinderWidth/2.0+axis.X()*(distanceSupportCylinder/2.0-supportCylinderRadius)-axis.X()*supportCylinderRadius, center.Y() - axis2.Y()*supportCyllinderWidth/2.0+axis.Y()*(distanceSupportCylinder/2.0-supportCylinderRadius)-axis.Y()*supportCylinderRadius, minZ-0.0000001-supportCylinderRadius - thickness/2.0)

        coordinate_system_support_right = gp_Ax2(scpntRightCenter, axis2)
        radius = supportCylinderRadius
        arc = BRepBuilderAPI_MakeEdge(gp_Circ(coordinate_system_support_right, radius), scpntRightStart, scpntRightEnd)
        arc = arc.Edge()
        line1 = BRepBuilderAPI_MakeEdge(scpntRightStart, scpntRightCenter).Edge()
        line2 = BRepBuilderAPI_MakeEdge(scpntRightCenter, scpntRightEnd).Edge()
        wire_builder = BRepBuilderAPI_MakeWire()
        wire_builder.Add(arc)
        wire_builder.Add(line1)
        wire_builder.Add(line2)
        wire = wire_builder.Wire()
        face_builder = BRepBuilderAPI_MakeFace(wire, True)
        face_builder.Build()
        face = face_builder.Face()
        prism_builder = BRepPrimAPI_MakePrism(face, gp_Vec(directionY*supportCyllinderWidth, -directionX*supportCyllinderWidth, 0))
        prism_builder.Build()
        solidSupportRight = prism_builder.Shape()

        if self.meshGenerationMode:
            nodeManager = self.dynaImporter.nodeManager
            meshManager = KooMeshManagerGMSH(nodeManager)
            meshManager.SetPath(self.meshPath)
            meshManager.SetName("ThreePointBendingPushCylinder")            
            meshManager.mesh_shape(solidPush, meshSize,meshSize,3,None,self.maxNID,self.maxEID)
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
            self.maxPID = self.maxPID + 1
            self.maxSID = self.maxSID + 1
            self.maxMID = self.maxMID + 1
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetSectionID(self.maxSID)
            meshManager.part.SetMaterialID(self.maxMID)
            meshManager.part.name = "ThreePointBendingPushCylinder"
            self.bendingPushCylinderMeshList.append(meshManager)
            self.bendingPushCylinderPartIDList.append(self.maxPID)

            meshManager = KooMeshManagerGMSH(nodeManager)
            meshManager.SetPath(self.meshPath)
            meshManager.SetName("ThreePointBendingSupportLeftCylinder")
            meshManager.mesh_shape(solidSupportLeft, meshSize,meshSize,3, None,self.maxNID,self.maxEID)
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
            self.maxPID = self.maxPID + 1
            self.maxSID = self.maxSID + 1   
            self.maxMID = self.maxMID + 1            
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetSectionID(self.maxSID)
            meshManager.part.SetMaterialID(self.maxMID)
            meshManager.part.name = "ThreePointBendingSupportLeftCylinder"
            self.bendingSupportLeftCylinderMeshList.append(meshManager)
            self.bendingSupportLeftCylinderPartIDList.append(self.maxPID)
            meshManager = KooMeshManagerGMSH(nodeManager)
            meshManager.SetPath(self.meshPath)
            meshManager.SetName("ThreePointBendingSupportRightCylinder")
            meshManager.mesh_shape(solidSupportRight, meshSize,meshSize,3, None,self.maxNID,self.maxEID)
            self.maxNID, self.maxEID = meshManager.GetMaxIDs()
            self.maxPID = self.maxPID + 1
            self.maxSID = self.maxSID + 1
            self.maxMID = self.maxMID + 1            
            meshManager.part.SetID(self.maxPID)
            meshManager.part.SetSectionID(self.maxSID)
            meshManager.part.SetMaterialID(self.maxMID)
            meshManager.part.name = "ThreePointBendingSupportRightCylinder"
            self.bendingSupportRightCylinderMeshList.append(meshManager)
            self.bendingSupportRightCylinderPartIDList.append(self.maxPID)

            ## material and section


               
        if __name__ == "__main__":
            if self.meshGenerationMode == True:
                display.DisplayShape(self.bendingPushCylinderMeshList[len(self.bendingPushCylinderMeshList)-1].shape, update=True)
                display.DisplayShape(self.bendingSupportLeftCylinderMeshList[len(self.bendingSupportLeftCylinderMeshList)-1].shape, update=True)                
                display.DisplayShape(self.bendingSupportRightCylinderMeshList[len(self.bendingSupportRightCylinderMeshList)-1].shape, update=True)
                display.FitAll()
            else:
                display.DisplayShape(solidPush, update=True)
                display.DisplayShape(solidSupportLeft, update=True)
                display.DisplayShape(solidSupportRight, update=True)                
                display.FitAll()
    
    def AddPartstoDynaImporter(self):
        partMan : KooPartManager = self.dynaImporter.partManager
        for meshManager in self.bendingPushCylinderMeshList:
            partMan.AddPartfromKooPart(meshManager.part.id, meshManager.part)
        for meshManager in self.bendingSupportLeftCylinderMeshList:
            partMan.AddPartfromKooPart(meshManager.part.id, meshManager.part)
        for meshManager in self.bendingSupportRightCylinderMeshList:
            partMan.AddPartfromKooPart(meshManager.part.id, meshManager.part)

    def ExportDyna(self, filePath,controlKeywords="",constrainedKeywords="",defineKeywords="",databaseKeywords="", setKeywords="",boundaryKeywords="", sectionKeywords="",materialKeywords="", contactKeywords="",loadKeywords="",addScripts=""):
        with open(filePath, "w") as file:
            file.write("*KEYWORD\n")
            file.write("*TITLE\n")
            title = os.path.basename(filePath)
            file.write("{0}\n".format(title))
            
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

        pass

    def SetThreePointBendingLoadBoundary(self, outputOption, pcPart : KooPart, slcPart : KooPart, srcPart : KooPart, nodeMan : NodeManager, topZ, bottomZ, addScripts = ""):

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
        
        ######### Control 
        timeList = outputOption["TIME"]
        dispList = outputOption["DISP"]
        forceList = outputOption["FORCE"]
        if "PushCylinderElasticModulus" in outputOption:
            matEPush = outputOption["PushCylinderElasticModulus"]
        else:
            matEPush = 2.0E11
        if "PushCylinderPoissonRatio" in outputOption:
            matPRPush = outputOption["PushCylinderPoissonRatio"]
        else:
            matPRPush = 0.294
        if "PushCylinderDensity" in outputOption:
            matDPush = outputOption["PushCylinderDensity"]
        else:
            matDPush = 7840.0
        if "SupportCylinderElasticModulus" in outputOption:
            matESupport = outputOption["SupportCylinderElasticModulus"]
        else:
            matESupport = 2.0E11
        if "SupportCylinderPoissonRatio" in outputOption:
            matPRSupport = outputOption["SupportCylinderPoissonRatio"]
        else:
            matPRSupport = 0.294
        if "SupportCylinderDensity" in outputOption:
            matDSupport = outputOption["SupportCylinderDensity"]
        else:
            matDSupport = 7840.0
        
        

        
        control_termination = ControlTermination()
        ENDTIM = timeList[len(timeList)-1]
        ENDCYC = 0
        DTMIN = 0.0
        ENDENG = 0.0
        ENDMAS = 10000000.0
        NOSOL = 0
        control_termination.SetControlTermination(ENDTIM, ENDCYC, DTMIN, ENDENG, ENDMAS, NOSOL)
        control_termination.write(controlIO)

        control_timestep = ControlTimeStep()
        DTINIT = 0.0
        TSSFAC = 0.7
        ISDO = 0
        TSLIMT = 0.0
        DT2MS = 0.0
        LCTM = 0
        ERODE = 0
        MSIST = 0 
        control_timestep.SetControlTimeStep(DTINIT, TSSFAC, ISDO, TSLIMT, DT2MS, LCTM, ERODE, MSIST)
        control_timestep.write(controlIO)

        ##### Control_Contact
        controlContact = ControlContact()
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
        controlContact.AddControlContact(slsfac, rwpnal, islchk, shlthk, penopt, thkchg, orien, enmass, usrstr, usrfrc, nsbcs, interm, xpene, ssthk, ecdt, tiedprj, sfric, dfric, edc, vfc, th, th_sf, pen_sf, ignore, frceng, skiprwg, outseg, spotstp, spotdel, spothin, isym, nserod, rwgaps, rwgdth, rwksf, icov, swradf, ithoff, shledg, pstiff, ithcnt, tdcnof, ftall, unused, shltrw, igactc)

        controlContact.write(controlIO)
        
        controlHourglass = ControlHourglass()
        ihq = 5
        qh = 0.1
        controlHourglass.AddControlHourglass(ihq, qh)

        dt = ENDTIM/len(timeList)
        #유효숫자 4
        dt = round(dt, 4)
        binary = 1
        lcur = 0 
        ioopt = 1

        nodeoutKeywords = DatabaseNodout()
        nodeoutKeywords.AddDatabaseNodout(dt, binary, lcur, ioopt)
        #nodeoutKeywords.write(databaseIO)
        eleoutKeywords = DatabaseElout()
        eleoutKeywords.AddDatabaseElout(dt, binary, lcur, ioopt)
        #eleoutKeywords.write(databaseIO)
        binaryD3plot = DatabaseBinaryD3plot()
        DTCYCL = dt
        LCDT = ""
        BEAM = 0
        NPLTC = len(timeList)
        PSETID = 0
        binaryD3plot.AddDatabaseBinaryD3plot(DTCYCL, LCDT, BEAM, NPLTC, PSETID)
        binaryD3plot.write(databaseIO)

        
        ######### Define
        defineCurve = DefineCurve()
        A1List = []
        O1List = []
        for i in range(len(timeList)):
            A1List.append(timeList[i])
            if outputOption["ControlMode"] == "Force":
                O1List.append(forceList[i])
            else:
                O1List.append(dispList[i])
        defineCurve.AddDefineCurve(1, 0, 1.0, 1.0, 0.0, 0.0, 0, 0, A1List, O1List)
        defineCurve.write(defineIO)

        ######### Set Node List
        zBottomLeftNodes = slcPart.GetNodesZRange(bottomZ-0.0000001, bottomZ+0.0000001)
        zBottomRightNodes = srcPart.GetNodesZRange(bottomZ-0.0000001, bottomZ+0.0000001)
        zTopNodes = pcPart.GetNodesZRange(topZ-0.0000001, topZ+0.0000001)        

        zblnList = SetNodeListTitle()
        zbrnList = SetNodeListTitle()
        ztnList = SetNodeListTitle()
        ztn2List = SetNodeListTitle()
        zBottomLeftNodeIDList = []
        zBottomRightNodeIDList = []
        zTopNodeIDList = []
        zTopNode2IDList = []
        for node in zBottomLeftNodes:
            zBottomLeftNodeIDList.append(slcPart.nodeManager.nodes[node].id)
        for node in zBottomRightNodes:
            zBottomRightNodeIDList.append(srcPart.nodeManager.nodes[node].id)

        centerXTop = 0.0
        centerYTop = 0.0
        centerZTop = 0.0
        for node in zTopNodes:
            zTopNodeIDList.append(pcPart.nodeManager.nodes[node].id)
            centerXTop = centerXTop + zTopNodes[node].x
            centerYTop = centerYTop + zTopNodes[node].y
            centerZTop = centerZTop + zTopNodes[node].z
        centerXTop = centerXTop / len(zTopNodes)
        centerYTop = centerYTop / len(zTopNodes)
        centerZTop = centerZTop / len(zTopNodes)
        dnode = self.dynaImporter.partManager.AddIndependentNode(centerXTop, centerYTop, centerZTop)
        zTopNode2IDList.append(dnode.id)
        


        da1 = 0.0
        da2 = 0.0
        da3 = 0.0
        da4 = 0.0
        solver = "MECH"
        sidzbln = 1
        sidzbrn = 2
        sidztn = 3
        sidztn2 = 4 
        namezbln = "BottomLeftNodes"
        namezbrn = "BottomRightNodes"
        nameztn = "TopNodes"
        nameztn2 = "TopNode"
        its = 0
        zblnList.AddSetNodeList(namezbln, sidzbln, da1, da2, da3, da4, solver, its, zBottomLeftNodeIDList)
        zbrnList.AddSetNodeList(namezbrn, sidzbrn, da1, da2, da3, da4, solver, its, zBottomRightNodeIDList)
        ztnList.AddSetNodeList(nameztn, sidztn, da1, da2, da3, da4, solver, its, zTopNodeIDList)
        ztn2List.AddSetNodeList(nameztn2, sidztn2, da1, da2, da3, da4, solver, its, zTopNode2IDList)
    
       

        ######### Constrained
        lcid = 1
        dnid = dnode.id
        ddof = "3"
        CIDD = ""
        ITYP = 0
        IDNSW = 1
        FGM = 0
        idofList = []
        for i in zTopNodeIDList:
            idofList.append("123")
        
        rbe3 = ConstrainedInterpolation()
        rbe3.AddConstrainedInterpolation(lcid, dnid, ddof, CIDD, ITYP, IDNSW, FGM, zTopNodeIDList, idofList)
        rbe3.write(constrainedIO)

        
        
        
        
        lcid = 2 
        rbe2 = ConstrainedNodeSet()
        nsid = sidztn2
        dof = 12456
        tf = 1.0e20

        rbe2.AddConstrainedNodeSet(nsid, dof,tf)
        rbe2.write(constrainedIO)
        
        


        if outputOption["ControlMode"] == "Force":
            ######### Load

            lnpoint = LoadNodePoint()
            nid = dnode.id
            

            #EQ.1: x-direction of load action, 
            #EQ.2: y-direction of load action, 
            #EQ.3: z-direction of load action, 
            #EQ.4: Follower force (see Remark 2), 
            #EQ.5: Moment about the x-axis (see Remark 4), 
            #EQ.6: Moment about the y-axis axis (see Remark 4), 
            #EQ.7: Moment about the z-axis axis (see Remark 4), 
            #EQ.8: Follower moment (see Remarks 2 and 4). 
            dof = 3
            lcid = 1
            sf = -1.0 
            lnpoint.AddLoadNodePoint(nid,dof,lcid,sf)
            lnpoint.write(loadKeywordsIO)

            self.dynaImporter.partManager.CreatePointElement(dnode,0.001)
        else:
            bpmr = BoundaryPrescribedMotionNode()
            #bpmrid = 4
            #bpmrname = "TopNode{0}".format(bpmrid)
            nid = dnode.id
            dof = 3
            lcid = 1
            sf = -1.0
            typeid = nid 
            dof = 3
            vad = 2
            vid = 0
            death = 1.0E28
            birth = 0.0
            bpmr.AddBoundaryPrescribedMotionNode(nid, dof, vad, lcid, sf, vid, death, birth)
            bpmr.write(boundaryKeywordsIO)
            
            


        

        ######### Set Boundary SPC
        bspcid1 = 1 
        bspcid2 = 2        
        spcls = BoundarySPCSet()
        spcls.AddBoundarySPCSet(sidzbln, 0,1,1,1,1,1,1)
        spcrs = BoundarySPCSet()
        spcrs.AddBoundarySPCSet(sidzbrn, 0,1,1,1,1,1,1)      

        
        spctp = BoundarySPCSet()
        spctp.AddBoundarySPCSet(sidztn, 0,1,1,0,1,1,1)
        
        zblnList.write(setKeywordIO)
        zbrnList.write(setKeywordIO)
        ztnList.write(setKeywordIO)
        ztn2List.write(setKeywordIO)
        spcls.write(boundaryKeywordsIO)
        spcrs.write(boundaryKeywordsIO)
        spctp.write(boundaryKeywordsIO)

        ######### Set Section Solid
        
        sectionSolid = SectionSolid()
        sectionSolid.AddSectionSolid(slcPart.secid,1,"","","")
        sectionSolid.AddSectionSolid(srcPart.secid,1,"","","")
        sectionSolid.AddSectionSolid(pcPart.secid,1,"","","")
        
        sectionSolid.write(sectionKeywordsIO)

        
        ######### Material Solid
        materialElastic = MatElasticTitle()
        materialElastic.AddMatElasticTitle("LeftCylinderMat",slcPart.mid, matDSupport, matESupport, matPRSupport)
        materialElastic.AddMatElasticTitle("RightCylinderMat",srcPart.mid, matDSupport, matESupport, matPRSupport)
        materialElastic.AddMatElasticTitle("PushCylinderMat",pcPart.mid, matDPush, matEPush, matPRPush)

        materialElastic.write(materialKeywordsIO)

        ######### Contact
        MSIDPushCylinder = pcPart.id
        MSIDLeftSupportCylinder = slcPart.id
        MSIDRightSupportCylinder = srcPart.id
        #autoSingleSurfaceContactID = ContactAutomaticSingleSurfaceID()
        autoSurfacetoSurface = ContactAutomaticSurfaceToSurfaceID()        
        #autoSurfacetoSurfaceImplicit = ContactAutomaticSurfaceToSurfaceOffsetID()
        # Part ID
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
            if pid == MSIDPushCylinder or pid == MSIDLeftSupportCylinder or pid == MSIDRightSupportCylinder:
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
            
        '''
        for partID in allPartIDList:
            prevMaxContactID = prevMaxContactID + 1
            autoSingleSurfaceContactID.AddAutomaticSingleSurfaceID(prevMaxContactID,"{0}toPushCylinderContact".format(partID), partID, MSIDPushCylinder, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
            prevMaxContactID = prevMaxContactID + 1
            autoSingleSurfaceContactID.AddAutomaticSingleSurfaceID(prevMaxContactID,"{0}toLeftSupportCylinderContact".format(partID), partID,MSIDLeftSupportCylinder, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
            prevMaxContactID = prevMaxContactID + 1
            autoSingleSurfaceContactID.AddAutomaticSingleSurfaceID(prevMaxContactID,"{0}toRightSupportCylinderContact".format(partID), partID, MSIDRightSupportCylinder, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        '''
        
        partID = allPartIDList[len(allPartIDList)-1]
        prevMaxContactID = prevMaxContactID + 1
        FS = 0.2
        FD = 0.2
        #if "implicit" in addScripts.lower():
        #    autoSurfacetoSurfaceImplicit.AddAutomaticSurfacetoSurfaceOffsetID(prevMaxContactID,"{0}toPushCylinderContact".format(partID), partID, MSIDPushCylinder, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        #else:
        autoSurfacetoSurface.AddAutomaticSurfacetoSurfaceID(prevMaxContactID,"{0}toPushCylinderContact".format(partID), partID, MSIDPushCylinder, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        partID = allPartIDList[0]        
        FS = 0.2
        FD = 0.2
        prevMaxContactID = prevMaxContactID + 1        
        #if "implicit" in addScripts.lower():
        #    autoSurfacetoSurfaceImplicit.AddAutomaticSurfacetoSurfaceOffsetID(prevMaxContactID,"{0}toLeftSupportCylinderContact".format(partID), partID,MSIDLeftSupportCylinder, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        #else:
        autoSurfacetoSurface.AddAutomaticSurfacetoSurfaceID(prevMaxContactID,"{0}toLeftSupportCylinderContact".format(partID), partID,MSIDLeftSupportCylinder, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        prevMaxContactID = prevMaxContactID + 1
        #if "implicit" in addScripts.lower():
        #    autoSurfacetoSurfaceImplicit.AddAutomaticSurfacetoSurfaceOffsetID(prevMaxContactID,"{0}toRightSupportCylinderContact".format(partID), partID, MSIDRightSupportCylinder, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        #else:
        autoSurfacetoSurface.AddAutomaticSurfacetoSurfaceID(prevMaxContactID,"{0}toRightSupportCylinderContact".format(partID), partID, MSIDRightSupportCylinder, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
        #autoSingleSurfaceContactID.write(contactKeywordsIO)
        autoSurfacetoSurface.write(contactKeywordsIO)
        #autoSurfacetoSurfaceImplicit.write(contactKeywordsIO)
    
        
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
            
        
        
            
        
        segIDList = [] 
        setSegment = SetSegment()        
        segid = 1
        for i in range(len(allPartIDList)):
            curPartID = allPartIDList[i]
            nidList = [] 
            fList = [] 
            nodes = partMan.parts[curPartID].GetShellSegmentList()            
            for node in nodes:
                nidList.append(node.id)
                fList.append(0.0)
            da1 = 0.0
            da2 = 0.0
            da3 = 0.0
            da4 = 0.0
            solver = "MECH"
            its = 0
            if len(nidList) == 0:
                continue
            setSegment.AddSegment(segid,da1,da2,da3,da4,solver,its,nidList,fList)
            segIDList.append(segid)
            segid = segid + 1
        setSegment.write(setKeywordIO)


        
        
        
        '''
        contactSlidingOnly = ContactSlidingOnly()
        for i in range(len(allPartIDList)-1):
            segid = i + 1           
            prevMaxContactID = prevMaxContactID + 1
            contactSlidingOnly.AddContactSlidingOnly(segid,segid+1, 0, 0, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)            
            #contactSlidingOnly.AddContactSlidingOnly(allPartIDList[i],allPartIDList[i+1], 3, 3, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)            
        contactSlidingOnly.write(contactKeywordsIO)
        '''
        
        
        if "$$ NO ADDITIONAL CONTACT" in addScripts or "$$ NO INTERNAL CONTACT" in addScripts:
            pass
        else:
        
            tiedShelltoShellSurface = ContactTiedShellEdgeToSurfaceBeamOffsetID()
            tiedSolidtoSolidSurface = ContactTiedSurfaceToSurfaceID()
            tiedShelltoSolidSurface = ContactTiedSurfaceToSurfaceOffsetID() 
            tiedSolidtoSolidSurfaceImplicit = ContactTiedSurfaceToSurfaceConstrainedOffsetID()
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
                    
                if allPartDimensionist[i] == 3 and allPartDimensionist[i+1] == 3:
                    if "implicit" in addScripts.lower():
                        #tiedShelltoSolidSurface.AddContactTiedSurfaceToSurfaceOffsetID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                        tiedSolidtoSolidSurfaceImplicit.AddContactTiedSurfaceToSurfaceConstrainedOffsetID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                    else:
                        tiedSolidtoSolidSurface.AddContactTiedSurfaceToSurfaceID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                        
                elif allPartDimensionist[i] == 2 and allPartDimensionist[i+1] == 2:
                    tiedShelltoShellSurface.AddContactTiedShellEdgeToSurfaceBeamOffsetID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)
                else:
                    tiedShelltoSolidSurface.AddContactTiedSurfaceToSurfaceOffsetID(prevMaxContactID,name,partID, nextPartID, SSTYP, MSTYP, SBOXID, MBOXID, SPR, MPR, FS, FD, DC, VC, VDC, PENCHK, BT, DT, SFS, SFM, SST, MST, SFST, SFMT, FSF, VSF)

                        
            tiedShelltoShellSurface.write(contactKeywordsIO)
            tiedSolidtoSolidSurface.write(contactKeywordsIO)
            tiedShelltoSolidSurface.write(contactKeywordsIO)
            tiedSolidtoSolidSurfaceImplicit.write(contactKeywordsIO)
            tiedFEMtoPeriSurface.write(contactKeywordsIO) 
      
        
        
        
        '''
        *CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID
         41to3                                                                  
$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR
         1         2         0         0         0         0         0         0
$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT
       0.0       0.0       0.0       0.0       0.0         0       0.0     1e+20
$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF
       1.0       1.0                           1.0       1.0       1.0       1.0
*CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID
         53to6                                                                  
$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR
         2         3         0         0         0         0         0         0
$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT
       0.0       0.0       0.0       0.0       0.0         0       0.0     1e+20
$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF
       1.0       1.0                           1.0       1.0       1.0       1.0                                                                                
*CONTACT_TIED_SURFACE_TO_SURFACE_CONSTRAINED_OFFSET_ID
         66to10                                                                 
$$    SSID      MSID     SSTYP     MSTYP    SBOXID    MBOXID       SPR       MPR
         3         4         0         0         0         0         0         0
$$      FS        FD        DC        VC       VDC    PENCHK        BT        DT
       0.0       0.0       0.0       0.0       0.0         0       0.0     1e+20
$$     SFS       SFM       SST       MST      SFST      SFMT       FSF       VSF
       1.0       1.0                           1.0       1.0       1.0       1.0              
       '''


        
        
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
            self.SetThreePointBendingScenario(outputOption)                                    
            self.AddPartstoDynaImporter()
            partMan = self.dynaImporter.partManager
            pushCylinderPartID = self.bendingPushCylinderPartIDList[i]
            supportLeftCylinderPartID = self.bendingSupportLeftCylinderPartIDList[i]
            supportRightCylinderPartID = self.bendingSupportRightCylinderPartIDList[i]
            pcPart : KooPart = partMan.parts[pushCylinderPartID]
            slcPart : KooPart = partMan.parts[supportLeftCylinderPartID]
            srcPart : KooPart = partMan.parts[supportRightCylinderPartID]
            nodeMan : NodeManager = self.dynaImporter.nodeManager                        

            
            topZ = self.bendingZTopList[i]
            bottomZ = self.bendingZBottomList[i]
            
            controlKeywords, constrainedKeywords, defineKeywords, databaseKeywords, setKeywords, boundaryKeywords, sectionKeywords, materialKeywords, contactKeywords, loadKeywords = self.SetThreePointBendingLoadBoundary(outputOption, pcPart, slcPart, srcPart, nodeMan, topZ, bottomZ, self.addScriptList[i])            
            if len(self.addScriptList)> i:
                self.ExportDyna(self.dynaFileList[i],controlKeywords,constrainedKeywords, defineKeywords, databaseKeywords, setKeywords,boundaryKeywords, sectionKeywords, materialKeywords, contactKeywords,loadKeywords,self.addScriptList[i])
            else:
                self.ExportDyna(self.dynaFileList[i],controlKeywords,constrainedKeywords, defineKeywords, databaseKeywords, setKeywords,boundaryKeywords, sectionKeywords, materialKeywords, contactKeywords,loadKeywords)
            
        return self.dynaFileList
        


            
            


if __name__ == "__main__":
    
    nodeMan = NodeManager()
    partMan = KooPartManager()
    secMan = KooSectionManager()
    matMan = KooMaterialManager()
    resultMan = KooResultManager(nodeMan)

    dynaImporter = KooDynaImporter(nodeMan,partMan,resultMan,matMan,secMan)
    dir = os.getcwd()
    #filePath = os.path.join(dir, "PackageInfoBoxMeshMaterial.k")
    #filePath = os.path.join(dir, "PackageInfoBoxMeshCompositeMaterial.k")
    #filePath = os.path.join(dir, "PackageInfoBoxMeshSolidMaterial.k")
    filePath = os.path.join(dir, "PackageInfoBoxMeshCompositeSolidMaterial.k")
    #stepPath = os.path.join(dir, "PackageInfoBoxMeshMaterial.step")
    #stepPath = os.path.join(dir, "PackageInfoBoxMeshCompositeMaterial.step")
    #stepPath = os.path.join(dir, "PackageInfoBoxMeshSolidMaterial.step")
    stepPath = os.path.join(dir, "PackageInfoBoxMeshCompositeSolidMaterial.step")
    outputOptionPath = os.path.join(dir, "OutputOptionShell.txt")
    
    dynaImporter.importDynaFile(filePath)
    maxNID = dynaImporter.importNode()    
    maxPID = dynaImporter.importPart()
    maxSID = dynaImporter.importSection()
    maxMID = dynaImporter.importMaterial()
    maxEID = dynaImporter.partManager.FindMaxEID()
    maxNSID = dynaImporter.nodeSetManager.FindMaxNSID()

    dynaScenarioMan = KooThreePointBendingSimulationGenerator(dynaImporter)
    dynaScenarioMan.SetPreMaxMeshID(maxNID, maxEID, maxPID, maxSID, maxMID, maxNSID)
    dynaScenarioMan.SetMeshPath("PackageMesh")
    dynaScenarioMan.SetLoadBoundaryOptionPath(outputOptionPath)
    dynaScenarioMan.SetLoadBoundaryOption()
    dynaScenarioMan.GenerateDynabyLoadBoundaryOption()

    
    


    from OCC.Core.STEPControl import STEPControl_Reader
    stepReader = STEPControl_Reader()
    stepReader.ReadFile(stepPath)
    stepReader.TransferRoots()
    if stepReader.NbShapes() == 0:
        print("No shapes found")
    
    else:
        shape = stepReader.Shape(1)    
        display.DisplayShape(shape, update=True)
    
    start_display()
    
