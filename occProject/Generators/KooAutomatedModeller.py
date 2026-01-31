import os
import sys

# --- Qt 라이브러리 충돌 방지: PyQt5 번들 Qt를 우선 로드 ---
# LD_LIBRARY_PATH는 프로세스 시작 시 동적 링커가 읽으므로,
# Python 내에서 설정 후 자기 자신을 재실행(re-exec)해야 적용됨.
if sys.platform.startswith("linux"):
    _reexec_marker = "_PYKOOCAE_QT_PATH_SET"
    if os.environ.get(_reexec_marker) != "1":
        # PyQt5 번들 Qt 경로 찾기
        try:
            import PyQt5
            qt_lib_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "lib")
        except ImportError:
            qt_lib_path = None

        if qt_lib_path and os.path.isdir(qt_lib_path):
            ld_path = os.environ.get("LD_LIBRARY_PATH", "")
            if qt_lib_path not in ld_path.split(":"):
                os.environ["LD_LIBRARY_PATH"] = qt_lib_path + ":" + ld_path

        # OCC 라이브러리 경로도 함께 설정
        occ_path = os.path.join(os.getcwd(), "Library", "OCC")
        if os.path.isdir(occ_path):
            ld_path = os.environ.get("LD_LIBRARY_PATH", "")
            if occ_path not in ld_path.split(":"):
                os.environ["LD_LIBRARY_PATH"] = occ_path + ":" + ld_path

        # 재실행 마커 설정 후 re-exec
        os.environ[_reexec_marker] = "1"
        os.execv(sys.executable, [sys.executable] + sys.argv)

os.environ["QT_QPA_PLATFORM"] = "offscreen"

getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")  # 더 안전한 방법

if sys.platform.startswith("win"):
    # Windows 전용
    os.add_dll_directory(path)
else:
    # Linux/Unix 계열은 LD_LIBRARY_PATH에 넣으면 됨 (re-exec 후이므로 이미 적용됨)
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if path not in ld_path.split(":"):
        os.environ["LD_LIBRARY_PATH"] = path + ":" + ld_path

#import KooODBCADManager.Capacitor as cp 
from KooODBCADManager.ODBCADManager import ODBCADManager
from KooODBCADManager.PackageGenerator import PackageUserdefined
from KooODBCADManager.Capacitor import CapacitorManager

import threading
import time

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtOpenGL as QtOpenGL

QtCore, QtGui, QtWidgets, QtOpenGL = QtCore, QtGui, QtWidgets, QtOpenGL


from OCC.Display.backend import load_backend
load_backend("pyqt5")


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


def GenerateDOEforLSDYNA(fileName):
    print("Generate DOE for LSDYNA")
    
def ImportCADManager(path,pkgFileName,compFileNameList):
    cadMan = ODBCADManager()
    cadMan.load_package(path,pkgFileName)
    for aCompFileName in compFileNameList:
        cadMan.load_component(path,aCompFileName)
    return cadMan


def GeneratePackage(fileName,displayMode):
    print("Generate Package as Step File")  
    curPath = os.getcwd()
    inputFilePath = os.path.join(curPath,fileName)
    print("Current Path : {curPath}".format(curPath=inputFilePath))
    if os.path.exists(inputFilePath) == False:
        print("File not exist")
        return
    
    package = PackageUserdefined()
    outFileName = fileName.replace(".txt",".step")
    outFilePath = os.path.join(curPath,outFileName)
    package.outFileName = outFilePath
    package.ImportPackage(inputFilePath)
    shapes = package.GenerateShapeList()
    nonNoneShape = False
    for aShape in shapes:
        if aShape is not None:
            nonNoneShape = True
            break
    if nonNoneShape == True:
        
        update_thread = threading.Thread(target=update_shape,args=(shapes,))
        update_thread.start()
            
    if displayMode == True:
        start_display()    
        update_thread.join()
    print("Update Complete")
    
    
    if package.layerList[0].meshGenerationMode == True:
        nastranFileName = fileName.replace(".txt",".bdf")
        dynaFileName = fileName.replace(".txt",".k")
        ansysFileName = fileName.replace(".txt",".cdb")
        abaqusFileName = fileName.replace(".txt",".inp")
        objFileName = fileName.replace(".txt",".obj")
               
        
        partMan = package.CreatePartsforPackage()
        package.CombineNodeManager()
        #package.nodeManager.MergeNodes(1.0e-9)
        package.CreateNodeSetsforPackage(partMan)
        package.CreateDefine(partMan)
        package.CreateContact()
        package.CreateBoundary()
        package.CreateSegmentSetsforPackage(partMan)
        package.CreateLoad()
        
        #print("Exporting NastranMesh : {nastranFileName}".format(nastranFileName=nastranFileName))
        #package.ExportNastranMesh(nastranFileName)
        
        
        print("Exporting DynaMesh : {dynaFileName}".format(dynaFileName=dynaFileName))
        package.ExportDynaMesh(dynaFileName)
        print("Complete Exporting DynaMesh : {dynaFileName}".format(dynaFileName=dynaFileName))
        
        #print("Exporting AnsysAPDLMesh : {ansysFileName}".format(ansysFileName=ansysFileName))
        #package.ExportAnsysAPDLMesh(ansysFileName)
        #print("Complete Exporting AnsysAPDLMesh : {ansysFileName}".format(ansysFileName=ansysFileName))
        #print("Exporting ABAQUSMesh : {abaqusFileName}".format(abaqusFileName=abaqusFileName))
        #package.ExportABAQUSMesh(abaqusFileName)
        #print("Complete Exporting ABAQUSMesh : {abaqusFileName}".format(abaqusFileName=abaqusFileName))
        #print("Exporting OBJMesh : {objFileName}".format(objFileName=objFileName))
        #package.ExportOBJMesh(objFileName)
        #print("Complete Exporting OBJMesh : {objFileName}".format(objFileName=objFileName))

    if package.layerList[0].meshGenerationMode == False:
        print("Exporting Step File : {outFileName}".format(outFileName=outFileName))
        package.ExportPackage()
        print("Complete Exporting Step File : {outFileName}".format(outFileName=outFileName))

    pass

def GenerateCapacitor(fileName):
    print("Generate Capacitor as Step File")
    curPath = os.getcwd()
    inputFilePath = os.path.join(curPath, fileName)
    print("Current Path : {curPath}".format(curPath = inputFilePath))
    if os.path.exists(inputFilePath) == False:
        print("File not exist")
        return
    capMan = CapacitorManager()
    print("Set Folder Path : {curPath}".format(curPath=curPath))    
    capMan.SetFolderPath(curPath)
    print("Import Capacitor File : {inputFilePath}".format(inputFilePath=inputFilePath))
    capMan.ImportCapacitor(inputFilePath)
    print("Generate Capacitors")
    capMan.GenerateCapacitors()
    print("Export Capacitors")
    capMan.ExportShapes()
    print("Complete Export Capacitors")
    capMan.ExportMeshes()
    print("Complete Export Meshes")
    
    pass

def GeneratePCB(fileName):
    print("Generate PCB as Step File")
    odbManager = ODBCADManager() 
    curPath = os.getcwd()
    curFilePath = os.path.join(curPath,fileName)
    print("Current Path : {curPath}".format(curPath=curPath))
    print("Current File Path : {curFilePath}".format(curFilePath=curFilePath))

    odbManager.ImportModellingOptions(curPath,fileName)
    odbManager.ImportPCBs()
    pass



def GeneratePBA(fileName, displayMode):
    print("Generate PBA as Step File")
    odbManager = ODBCADManager()
    curPath = os.getcwd()
    curFilePath = os.path.join(curPath,fileName)
    print("Current Path : {curPath}".format(curPath=curPath))
    print("Current File Path : {curFilePath}".format(curFilePath=curFilePath))

    odbManager.ImportModellingOptions(curPath,fileName)
    shapeList = odbManager.ImportPBA()
    print(len(shapeList), "Shapes are imported")

    update_thread = threading.Thread(target=update_shape,args=(shapeList,))
    update_thread.start()
        
    #if displayMode == True:
    start_display()    
    #update_thread.join()    
    print("Update Complete")
    exportFileName = curFilePath
    exportFileName = exportFileName.replace(".txt","_total.step")
    odbManager.ExportShapes(exportFileName)

    pass

def update_shape(shapeList):
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        return
    for aShape in shapeList:
        if aShape is not None:
            if type(aShape) == list:
                for aSubShape in aShape:
                    display.DisplayShape(aSubShape,update=True)
            else:
                display.DisplayShape(aShape,update=True)    

def GenerateArrayPCB(fileName):
    print("Generate Array PCB as Step File")
    odbManager = ODBCADManager()
    curPath = os.getcwd()
    curFilePath = os.path.join(curPath,fileName)
    print("Current Path : {curPath}".format(curPath=curPath))
    print("Current File Path : {curFilePath}".format(curFilePath=curFilePath))
 
    odbManager.ImportModellingOptions(curPath,fileName)
    odbManager.ImportArrayPCBs()
    pass

## receive arguments from command line from sys.argv
import socket

def get_ip_address():
    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Connect to a remote server (doesn't matter which)
        sock.connect(("8.8.8.8", 80))
        # Retrieve the local IP address
        ip_address = sock.getsockname()[0]
    except socket.error:
        ip_address = None
    finally:
        # Close the socket
        sock.close()

    return ip_address

import requests
import json
from datetime import datetime

def get_current_time(url):
    try:
        # Send an HTTP GET request to the specified URL
        response = requests.get(url)
        # Extract the current time from the response
        data = json.loads(response.text)
        #{"year":2023,"month":7,"day":11,"hour":12,"minute":46,"seconds":53,"milliSeconds":490,"dateTime":"2023-07-11T12:46:53.4904705","date":"07/11/2023","time":"12:46","timeZone":"Asia/Seoul","dayOfWeek":"Tuesday","dstActive":false}

        current_time = datetime(data["year"],data["month"],data["day"],data["hour"],data["minute"],data["seconds"],data["milliSeconds"])
        #current_time = datetime.strptime(response.text, "%Y-%m-%d %H:%M:%S")
        return current_time
    except requests.exceptions.RequestException as e:
        print("Error occurred:", e)
        return None
    
if __name__ == '__main__':    
    print("""KooAutomatedModeller Software License Agreement

IMPORTANT - READ CAREFULLY: This License Agreement is a legal agreement between you (either an individual or a single entity) and Koo, the author and copyright owner of "KooAutomatedModeller" (the "Software"). By installing, copying, or otherwise using the Software, you agree to be bound by the terms of this License Agreement. If you do not agree to the terms of this License Agreement, do not install or use the Software.

Grant of License: Koo hereby grants you a non-exclusive, non-transferable license to use the Software solely for your personal or internal business purposes on a single computer.

Ownership: The Software is protected by intellectual property laws and treaties. Koo or its suppliers own the title, copyright, and other intellectual property rights in the Software. The Software is licensed, not sold.

Restrictions:

You may not distribute, sell, lease, rent, lend, or sublicense the Software to any third party.
You may not modify, decompile, disassemble, reverse engineer, or create derivative works based on the Software.
You may not remove any proprietary notices or labels on the Software.
No Warranty: The Software is provided "as is" without warranty of any kind, either expressed or implied, including, but not limited to, the implied warranties of merchantability and fitness for a particular purpose. The entire risk as to the quality and performance of the Software is with you.

Limitation of Liability: In no event shall Koo be liable for any special, incidental, indirect, or consequential damages whatsoever (including, without limitation, damages for loss of business profits, business interruption, loss of business information, or any other pecuniary loss) arising out of the use of or inability to use the Software, even if Koo has been advised of the possibility of such damages.

Termination: This License Agreement is effective until terminated. You may terminate it at any time by destroying the Software, together with all copies thereof. This License Agreement will also terminate if you fail to comply with any term or condition of this Agreement. Upon such termination, you agree to destroy the Software, together with all copies thereof.

COPYRIGHT NOTICE: Copyright © 2025 Koo. All rights reserved.
""")
# List of registered IP addresses
    
    registered_ips = ["110.15.177.120","10.252.37.33","10.252.38.170","10.252.39.184","10.252.38.171","172.16.140.28","172.16.2.205","10.254.236.128","10.252.39.170","10.252.37.36","10.252.39.181","219.250.247.155","222.234.112.125", "219.250.247.168", "10.252.34.71", "10.252.32.210", "10.252.33.107", "58.124.52.240", "10.252.32.33"]

    for i in range(1,250):
        registered_ips.append("10.254.236."+str(i))
    for i in range(1,250):
        registered_ips.append("192.168.0."+str(i))

    # Get the current IP address
    ip = get_ip_address()

    # Check if the current IP is in the registered list
    if ip in registered_ips:
        print("Access granted. IP address:", ip)
        
        # Continue running the application
    else:
        print("Access denied. IP address:", ip)
        exit(0)
        # Terminate the application or perform any desired action
    
    
    
    # Specify the URL of the website that provides the current time
    time_website_url = "https://www.timeapi.io/api/Time/current/zone?timeZone=Asia/Seoul"

    # Specify the threshold date for termination
    threshold_date = datetime(2027, 12, 31)  

    # Call the function to get the current time from the website
    #current_time = get_current_time(time_website_url)
    current_time = datetime.now()

    # Check if the current time was successfully retrieved
    if current_time is not None:
        print("Current time:", current_time)
        print("License Limit Date:",threshold_date)

        # Compare the current time with the threshold date
        if current_time > threshold_date:
            print("Terminating the application. Threshold date exceeded.")
            # Terminate the application or perform any other desired action
            exit()
        else:
            print("Threshold date not exceeded. Continuing with the application.")
            # Continue running the application
    else:
        exit()
    
    
    #display, start_display, add_menu, add_function_to_menu = init_display()

    if len(sys.argv)<3:
        
        curDir = os.getcwd()
        curDir = os.path.join(curDir,"Examples","ODB")
        # set cwd as curDir
        os.chdir(curDir)
        #sys.argv.clear()
        #sys.argv.append("KooAutomatedModeller")
        #sys.argv.append("MicroModelling")
        
        ########################################################
        ####### PBA Generation #################################
        ########################################################
        
        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller")
        sys.argv.append("PBA")
        #sys.argv.append("ECADfilesforPBA.txt")
        #sys.argv.append("ECADfilesforPBA_P3.txt")        
        # detail level
        #sys.argv.append("ECADfilesforPBA_P3_Multiscale.txt")
        #sys.argv.append("ECADfilesforPBA_P3_PADDetail.txt")
        #sys.argv.append("ECADfilesforPBA_P3_PADDetailfor.txt")
        #sys.argv.append("ECADfilesforPBA_P3_PADSimple.txt")
        #sys.argv.append("ECADfilesforPBA_P3_PADSimpleBigPKGOnly.txt")
        #sys.argv.append("ECADfilesforPBA_P3_PrescribedPKG.txt")
        #sys.argv.append("ECADfilesforPBA_P3_Export.txt")
        sys.argv.append("ECADfilesforPBA_P3_Export_detail.txt")
        #sys.argv.append("P3_3.txt")
        #sys.argv.append("P3_4_1.txt")
        #sys.argv.append("P3Multiscale_2_1.txt")        
        #sys.argv.append("P3_5.txt")        
        #sys.argv.append("P3_6.txt")        
        #sys.argv.append("MultiscaleTest_3.txt")
        #sys.argv.append("TestODBzip.txt")
        
        ########################################################
        ########################################################
        ########################################################

        ########################################################
        ###### Package Generation ##############################
        ########################################################
        
        '''sys.argv.clear()
        sys.argv.append("KooAutomatedModeller")
        sys.argv.append("PKG")'''
        
        ##### No Warpage
        #sys.argv.append("PackageInfoSimple.txt")
        #sys.argv.append("PackageInfoDetail.txt")
        
        #sys.argv.append("PackageInfoCylinderMesh.txt")
        
        
        # Box 기본- 단일/복합 소재 등
        #sys.argv.append("PackageInfoBoxMesh.txt")
        #sys.argv.append("PackageInfoBoxMeshShell.txt")
        #sys.argv.append("PackageInfoBoxMeshMaterial.txt")
        #sys.argv.append("PackageInfoBoxMeshCompositeMaterial.txt")
        #sys.argv.append("PackageInfoBoxMeshSolidMaterial.txt")
        #sys.argv.append("PackageInfoBoxMeshCompositeSolidMaterial.txt")
        
        # Polynomial Solid/Shell
        #sys.argv.append("PackageInfo_PolynomialPartMesh.txt")
        #sys.argv.append("PackageInfo_PolynomialCutPartMesh.txt")
        
        # Box with Crack Shape
        #sys.argv.append("PackageInfoBoxCrack.txt")
        #sys.argv.append("PackageInfoBoxCrackMesh.txt")
        #sys.argv.append("PackageInfoBoxMultipleCrack.txt")
        #sys.argv.append("PackageInfoRectangleTube.txt")
        #sys.argv.append("PackageInfoRectangleTubeMesh.txt")
        #sys.argv.append("PackageInfoRectangleTubeShellMesh.txt")
        #sys.argv.append("PackageInfoRectangleTubeMeshStack.txt")
        #sys.argv.append("PackageInfoRectangleCircleCut.txt")
        #sys.argv.append("PackageInfoPolynomialSweep.txt")
        #sys.argv.append("PackageInfoPolynomialSweepMesh.txt")
        #sys.argv.append("PackageInfoRectangleTubeShell.txt")
        #sys.argv.append("PackageInfoRectangleFilletCut.txt")
        #sys.argv.append("PackageInfoRectangleFilletCutMesh.txt")
        #sys.argv.append("PackageInfoRectangleTubeMeshStackMaterialTest.txt")
        
        #sys.argv.append("PackageInfoShieldCan.txt")
        #sys.argv.append("PackageInfoShieldcanSolid.txt")
        #sys.argv.append("PackageInfoShieldcanComplex.txt")
        #sys.argv.append("PackageInfoShieldcanComplexShell.txt")
        #sys.argv.append("PackageInfoShieldcanDetail.txt")
        #sys.argv.append("PackageInfoShieldcanDetailMesh.txt")
        #sys.argv.append("PackageInfoImpactZig.txt")
        
        #sys.argv.append("MultiscaleTest_1_pcb_multiscale_mesh.txt")
        #sys.argv.append("PackageInfoStepFile.txt")
        #sys.argv.append("PackageInfoStepMeshFile.txt")
        #sys.argv.append("PackageInfoStepMeshFileDetail.txt")
        #sys.argv.append("testodb2.txt")
        #sys.argv.append("P3_5_unitfeature.txt")
        #sys.argv.append("P3_6_unitfeature.txt")
        #sys.argv.append("MultiscaleTest_1_unitfeature.txt")
        #sys.argv.append("MultiscaleTest_1_pcb_multiscale_mesh.txt")
        #sys.argv.append("MultiscaleTest_1_pcb_multiscale_mesh_detail.txt")
        # 아직 미개발 sys.argv.append('PackageInfoDetailMesh.txt')
        #sys.argv.append('PackageInfo_ImagePartMesh.txt')
        #sys.argv.append('PackageInfoBoxMultipleCrackwithLayer.txt')
        #sys.argv.append("PackageInfoRoundedBox.txt")
        #sys.argv.append("bga68f_W306L378_B02_RB_119_mesh.txt")
        #sys.argv.append("bga68f_W306L378_B02_RB_detail_119_mesh.txt")
        #sys.argv.append("intp_P3_L_R03_SLAVE_detail_70_mesh.txt")
        #sys.argv.append("qfn8mp_W110L110_C035_2_v2_404_mesh.txt")
        #sys.argv.append("qfn8mp_W110L110_C035_2_v2_detail_404_mesh.txt")
        ####### Warpage
        #sys.argv.append("bga1f_W10L10.txt")
        #sys.argv.append("PackageInfoBoxWarpage.txt")
        #sys.argv.append("PackageInfoBoxWarpageSimple.txt")
        #sys.argv.append("PackageInfoBoxWarpageSmileCry.txt")
        #sys.argv.append("PackageInfoBoxWarpageSmileCryExtreme.txt")
        #sys.argv.append("PackageInfoBoxWarpageSmileCryExtremeNoDetailMode.txt")
        #sys.argv.append("PackageInfoBoxWarpageNoWarpage.txt")
        #sys.argv.append("PackageInfoBoxWarpageDesign.txt")
        #sys.argv.append("PackageInfoBoxWarpageSmileCryExtremeResin.txt")
        #sys.argv.append("PackageInfoBoxWarpageMesh.txt")
        #sys.argv.append("PackageInfoBoxWarpageMeshTetra.txt")
        #sys.argv.append("PackageInfoBoxCylinderSolderMesh.txt")
        #sys.argv.append("bga103f_W64z0L500_DSM_MU_KOZ_LT_1_detail_288.txt")
        #sys.argv.append("bga103f_W640L500_DSM_MU_KOZ_LT_1_detail_288_Warped.txt")
        #sys.argv.append("bga103f_W640L500_DSM_MU_KOZ_LT_1_detail_288_Warped_mesh.txt")
        #sys.argv.append("bga103f_W640L500_DSM_MU_KOZ_LT_1_detail_288_Warped_mesh_test.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_sold1.5.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_sold1.5_warped.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_sold1.5_warped_30um_nodetail.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_sold1.5_warped_30um_nodetail_low_surface_tension.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_sold1.5_warped_30um_nodetail_low_surface_tension_locmisalign.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_30um_nodetail_low_surface_tension_locmisalign_randSold.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_30um_nodetail_low_surface_tension_locmisalign_randSold_SMD.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_30um_nodetail_low_surface_tension_locmisalign_randSold_NSMD.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_30um_nodetail_low_surface_tension_locmisalign_randSold_SMD_detail.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_30um_nodetail_low_surface_tension_randSold_SMD_detail.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_none_30um_nodetail.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_30um_nodetail.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_50um_nodetail.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_100um_nodetail.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_200um_nodetail.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_none_nodetail_misalign.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_none_nodetail_misalign_rot.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_none_nodetail_misalign_0.2.txt")
        #sys.argv.append("PackageInfoStepMeshFilePackage.txt")
        #sys.argv.append("PackageInfoSimpleStepMeshFileBoundary.txt")
        #sys.argv.append("PackageInfoSimpleStepMeshFileBoundaryRBETiedContact.txt")
        #sys.argv.append("PackageInfoStackBoundaryRBETiedContact.txt")        
        #sys.argv.append("PackageInfoStackBoundaryRBETiedContactDetail1Layer.txt")
        #sys.argv.append("bga401f_W700L788_SB02_L_detail_405_mesh_warped_100um_nodetail_largewarpage.txt")
        # 개발 필요, 외곽 라인에 대해 
        #sys.argv.append("bga54f_W280L400_C024_RT_v3_RS_detail.txt")
        #sys.argv.append("PackageInfoBoxCylinderSolderMeshRotatedMirrored.txt")
        #sys.argv.append("con40mp_W1016L220_SOC_035P_v4_detail_345_mesh.txt")
        #sys.argv.append("con56mp_W1290L214_SOC_035P_v2_detail_340_mesh.txt")
        
        #sys.argv.append("PackageInfoDMATest.txt")
        #sys.argv.append("PackageInfoDMAShellTest.txt")
        #sys.argv.append("PackageInfoGMSH.txt")
        #sys.argv.append("PackageInfoGMSHMesh.txt")
        #sys.argv.append("PackageInfoStlMeshFile.txt")
        #sys.argv.append("PackageInfoStepMeshFilePCB.txt")
        #sys.argv.append("P3_3_pcb_multiscale_mesh.txt")
        #sys.argv.append("P3_4_1_pcb_multiscale_mesh.txt")
        #sys.argv.append("P3Multiscale_2_1_pcb_multiscale_mesh.txt")
        ########################################################
        
        #sys.argv.append("None")
        #sys.argv.append("False")
        
        
        ########################################################
        ########################################################
        

        ########################################################
        #Move to the directory where the executable file is located
        ########################################################
        '''
        os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\KooOptimizer")
        sys.argv.clear()        
        sys.argv.append("KooAutomatedModeller")
        sys.argv.append("PKG")
        sys.argv.append("PackageInfoBoxMeshCompositeMaterial.txt")

        os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\DisplayImpact2")
        sys.argv.clear()        
        sys.argv.append("KooAutomatedModeller")
        sys.argv.append("PKG")
        sys.argv.append("PackageInfoBoxMeshCompositeMaterial.txt")

        os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\KooAutomatedModeller")
        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller")
        sys.argv.append("PKG")
        sys.argv.append("PackageInfoBoxCrackMesh.txt")
        
                
        os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\KooAutomatedModeller"))
        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller")
        sys.argv.append("PBA")        
        sys.argv.append("ECADfilesforPBA_P3_Export.txt")
        
        os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\KooAutomatedModeller\\PackageExported")
        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller")
        sys.argv.append("PKG")        
        sys.argv.append("bga401f_W700L788_SB02_L_405.txt")
        '''
        ########################################################
        ########################################################
        ########################################################
        
        


        ########################################################
        ###### Array PCB Generation ############################
        ########################################################

        #sys.argv.clear()
        #sys.argv.append("KooAutomatedModeller")
        #sys.argv.append("ArrayPCB")
        #sys.argv.append("DieSample.txt")
        ########################################################
        ########################################################
        ########################################################

        ########################################################
        ###### PCB Generation ##################################
        ########################################################
        #os.chdir("D:\\OpenCASCADE-7.7.0-vc14-64\\pythonoccenv310")
        #sys.argv.clear()               
        #sys.argv.append("KooAutomatedModeller")
        #vsys.argv.append("PCB")
        #sys.argv.append("ECADfiles.txt")
        ########################################################
        ########################################################
        ########################################################

        ########################################################
        # Warpage 반영된 Array PCB 생성 #########################
        ########################################################
        '''
        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller")
        sys.argv.append("ArrayPCB")
        sys.argv.append("ECADNoWarpage.txt")
        #sys.argv.append("ECADfiles.txt")
        '''
        ########################################################
        ########################################################
        ########################################################
        
        ########################################################
        # LSdyna DOE 생성 ######################################
        ########################################################
        '''
        sys.argv.clear(); 
        sys.argv.append("KooAutomatedModeller")
        sys.argv.append("LSDynaDOE")
        sys.argv.append("LSDynaDOE.txt")
        '''        
        ########################################################
        ########################################################
        ########################################################
        
        ########################################################
        ##Prescribed PKG #######################################
        ########################################################
        '''
        os.chdir(os.path.join(curDir, "occProject\\Generators\\dist\\PBA"))

        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller.exe")
        sys.argv.append("PBA")
        sys.argv.append("ECADfilesforPBA_P3_PrescribedPKG.txt")
        '''
        ########################################################
        ########################################################
        ########################################################
    
        
        ########################################################
        #### Capacitor Generation Example ######################
        ########################################################   
        
        '''os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\Capacitor"))
        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller.exe")
        sys.argv.append("CAP")
        #sys.argv.append("Cap1005.txt")
        sys.argv.append("Cap0603Mesh.txt")'''
        
        
        ########################################################
        ########################################################
        ########################################################
        
        ########################################################
        ####Display Impact Example##############################
        ########################################################
        '''
        os.chdir(os.path.join(curDir,"occProject\\Generators\\dist\\DisplayImpactBall"))

        #os.chdir("D:\\OpenCASCADE-7.7.0-vc14-64\\pythonoccenv310\\occProject\\Generators\\dist\\PBA")
        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller.exe")
        sys.argv.append("PKG")
        #sys.argv.append("PackageInfoBoxMeshCompositeSolidMaterial.txt")
        sys.argv.append("PackageInfoBoxMeshCompositeSolidMaterialRefinement.txt")
        #sys.argv.append("PackageInfoGMSH.txt")
        '''
        '''
        curDir = os.path.join(curDir,"occProject\\Generators\\dist\\Examples\\1.DisplayImpactBall_Peridynamics")
        os.chdir(curDir)
        
        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller.exe")
        sys.argv.append("PKG")        
        sys.argv.append("DisplayImpact.txt")
        '''
        '''
        curDir = os.path.join(curDir,"occProject\\Generators\\dist\\Examples\\1.DisplayImpactBallPeridynamicsFine")
        os.chdir(curDir)
        sys.argv.clear()
        sys.argv.append("KooAutomatedModeller.exe")
        sys.argv.append("PKG")
        sys.argv.append("DisplayImpact.txt")
        '''

        ########################################################
        ########################################################
        ########################################################
        """
        print('입력 keyword가 존재하지 않습니다.')
        print('CAPACITOR 생성 : python KooAutomatedModeller.py CAPACITOR [fileName]')
        print('PCB 생성 : python KooAutomatedModeller.py PCB [fileName]')
        print('ArrayPCB 생성 : python KooAutomatedModeller.py ArrayPCB [fileName]')
        sys.exit(0)
        """
        sys.argv.append("None")
        sys.argv.append("False")
    mode = sys.argv[1] 
    fileName = sys.argv[2]
    if len(sys.argv) > 3:
        if sys.argv[3].lower() == "none":
            pass
        else:
            curdir = os.getcwd()
            workdir = sys.argv[3]
            os.chdir(os.path.join(curdir,workdir))
    displayMode = False
    if len(sys.argv) >4:
        if sys.argv[4].lower() == "false":
            displayMode = False
        else:
            displayMode = True
    if mode == "CAPACITOR" or mode == "CAP":
        GenerateCapacitor(fileName)
    elif mode == "PCB":
        GeneratePCB(fileName)
    elif mode == "ArrayPCB":
        GenerateArrayPCB(fileName)
    elif mode == "PBA":
        GeneratePBA(fileName, displayMode)
    elif mode == "PKG":
        GeneratePackage(fileName, displayMode)
    elif mode == "LSDYNADOE":
        pass

