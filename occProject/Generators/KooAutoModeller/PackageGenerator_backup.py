import sys 
import os

getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")
os.add_dll_directory(path)

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir,gp_Ax2, gp_Circ
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound, topods_Compound
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections


class PackageLayer:
    def __init__(self,name="",x=0.0,y=0.0,z=0.0,xLength=1.0,yLength=1.0,thickness=1.0):
        self.name = name
        self.posX = x
        self.posY = y
        self.posZ = z         
        self.xLength = xLength
        self.yLength = yLength
        self.thickness = thickness
        self.cylinderList = []         
        self.boxList = []
        self.cylinderShapeList = []        
        self.boxShapeList = []
        self.detailSolderList = [] 
        self.detailSolderShapeList = []         
        self.shape = None 

    
    def SetPosition(self,x,y,z):
        self.posX = x
        self.posY = y
        self.posZ = z
        pass

    def SetLength(self,x,y):
        self.xLength = x
        self.yLength = y
        pass

    def SetThickness(self,thickness):
        self.thickness = thickness
        pass

    def AddDetailSolderShape(self, x,y,points):
        self.detailSolderList.append([x,y,points])
        pass

    def AddCylinder(self, x,y,r):
        self.cylinderList.append([x,y,r])
        pass
    
    def AddBox(self, x,y,xLength,yLength):
        self.boxList.append([x,y,xLength,yLength])
        pass

    def GenerateDetailSolderShapes(self):
        self.detailSolderShapeList = []
        for detailSolder in self.detailSolderList:
            x = detailSolder[0] + self.posX
            y = detailSolder[1] + self.posY
            z = self.posZ
            points = detailSolder[2]
            wires = [] 
            for radius, height in points:
                circle = gp_Circ(gp_Ax2(gp_Pnt(x,y,z+height*self.thickness), gp_Dir(0, 0, 1)), radius)
                circle_edge = BRepBuilderAPI_MakeEdge(circle).Edge()
                circle_wire = BRepBuilderAPI_MakeWire(circle_edge).Wire()
                wires.append(circle_wire)
            loft = BRepOffsetAPI_ThruSections(True)
            for wire in wires:
                loft.AddWire(wire)
            loft.Build()
            shape = loft.Shape()
            self.detailSolderShapeList.append(shape)




    def GenerateCylinderShapes(self):
        self.cylinderShapeList = [] 
        for cylinder in self.cylinderList:
            x = cylinder[0] + self.posX
            y = cylinder[1] + self.posY
            z = self.posZ
            r = cylinder[2]
            thickness = self.thickness

            center = gp_Pnt(x,y,z)
            normal = gp_Dir(0,0,1)
            circle_geom = gp_Circ(gp_Ax2(center,normal),r)
            circle_edge = BRepBuilderAPI_MakeEdge(circle_geom).Edge()
            circle_wire = BRepBuilderAPI_MakeWire(circle_edge).Wire()
            circle_face = BRepBuilderAPI_MakeFace(circle_wire).Face()
            cylinder_shape = BRepPrimAPI_MakePrism(circle_face,gp_Vec(0,0,thickness)).Shape()
            self.cylinderShapeList.append(cylinder_shape)

    def GenerateBoxShape(self):
        self.boxShapeList = [] 
        for box in self.boxList:
            x = box[0] + self.posX
            y = box[1] + self.posY
            z = self.posZ
            xLength = box[2]
            yLength = box[3]
            thickness = self.thickness

            box_shape = BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),xLength,yLength,thickness).Shape()
            self.boxShapeList.append(box_shape)

    def GenerateShape(self):
        print("Generate Shape of DetailSolder")
        self.GenerateDetailSolderShapes()
        print("Generate Shape of PackageLayer")        
        self.GenerateCylinderShapes()
        print("Cyliner shape generated")
        self.GenerateBoxShape()
        print("Box shape generated")


        # Package MainBody 
        leftBottomX = self.posX - self.xLength/2
        leftBottomY = self.posY - self.yLength/2
        leftBottomZ = self.posZ        
        self.shape = BRepPrimAPI_MakeBox(gp_Pnt(leftBottomX,leftBottomY,leftBottomZ),self.xLength,self.yLength,self.thickness).Shape()
        print("Main Body Generated") 
        initShape = self.shape
        cut = BRepAlgoAPI_Cut()
        L1 = TopTools_ListOfShape()
        L1.Append(self.shape)
        L2 = TopTools_ListOfShape()
        i = 0 
        for detail_shape in self.detailSolderShapeList:
            L2.Append(detail_shape)
            i += 1
            print("Detail Solder Shape " + str(i) + " Appended")
            
        for cylinder_shape in self.cylinderShapeList:
            L2.Append(cylinder_shape)
            i += 1
            print("Cylinder Shape " + str(i) + " Appended")
        for box_shape in self.boxShapeList:
            L2.Append(box_shape)
            i += 1
            print("Box Shape " + str(i) + " Appended")
        if i>0:
            cut.SetArguments(L1)
            cut.SetTools(L2)
            cut.SetRunParallel(True)
            cut.SetFuzzyValue(0.0000001)
            cut.Build()
            if cut.Shape() == None:
                print("Cut Failed")
                self.shape = initShape
            else:
                print("Cut Success")
                self.shape = cut.Shape()
            
        return self.shape




class Package:

    def __init__(self,xOrigin=0.0,yOrigin=0.0,zOrigin=0.0):
        self.layerList = []
        self.outFileName = "output.txt"
        self.xOrigin = xOrigin
        self.yOrigin = yOrigin
        self.zOrigin = zOrigin
        
        pass

    def AddPackageLayer(self,layer : PackageLayer):
        self.layerList.append(layer)

    def ImportPackage(self, filePath):
        f = open(filePath, 'r')
        line = f.readline()        
        totalThickness = 0.0
        # read line by line
        while True:
            
            if not line: break
            #print(line)
            if line[0] == '#':
                line = f.readline()
                continue
            elif line[0] == '*':
                svector = line.split(',')

                if svector[0] == "*Layer":
                    if len(svector) >= 2:
                        layer = PackageLayer(svector[1])
                    else:
                        layer = PackageLayer()
                    print("Layer Created")
                    while True:
                        line = f.readline()
                        if not line:break
                        svector = line.split(',')
                        if svector[0][0] == "*":
                            print("Layer End")
                            break
                        elif svector[0] == "Location":
                            x = float(svector[1])
                            y = float(svector[2])
                            if len(svector) >= 4:
                                z = float(svector[3])                            
                                layer.SetPosition(x,y,z)
                            else:
                                z = totalThickness
                                layer.SetPosition(x,y,totalThickness)
                            print("Location: ",x,y,z)
                        elif svector[0] == "Length":
                            xLength = float(svector[1])
                            yLength = float(svector[2])
                            layer.SetLength(xLength,yLength)
                            print("Length: ",xLength,yLength)
                        elif svector[0] == "Thickness":
                            thickness = float(svector[1])
                            layer.SetThickness(thickness)
                            totalThickness += thickness
                            print("Thickness: ",thickness)
                        elif svector[0] == "DetailSolder":
                            x = float(svector[1])
                            y = float(svector[2])
                            points = []
                            for i in range(3,len(svector),2):
                                radius = float(svector[i])
                                height = float(svector[i+1])
                                points.append([radius,height])
                            layer.AddDetailSolderShape(x,y,points)
                            print("DetailSolder: ",x,y,points)
                        elif svector[0] == "Cylinder":
                            x = float(svector[1])
                            y = float(svector[2])
                            r = float(svector[3])
                            layer.AddCylinder(x,y,r)
                            print("Cylinder: ",x,y,r)
                        elif svector[0] == "Box":
                            x = float(svector[1])
                            y = float(svector[2])
                            xLength = float(svector[3])
                            yLength = float(svector[4])
                            layer.AddBox(x,y,xLength,yLength)                            
                            print("Box: ",x,y,xLength,yLength)
                    self.layerList.append(layer)

            else:
                line = f.readline()



        f.close()
        pass

    def GenerateShapeList(self):
        self.shapeList = []
        for layer in self.layerList:
            layer.GenerateShape()            
            self.shapeList.append(layer.shape)
            for detailShapes in layer.detailSolderShapeList:
                self.shapeList.append(detailShapes)
            for cylinderShapes in layer.cylinderShapeList:
                self.shapeList.append(cylinderShapes)
            for boxShapes in layer.boxShapeList:
                self.shapeList.append(boxShapes)
        return self.shapeList

    def ExportPackage(self):

        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        for shape in self.shapeList:
            if shape != None:
                builder.Add(compound,shape)
        from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
        print("Save Solder Joints to STEP File")
        step_writer = STEPControl_Writer()
        #for shape in self.shapeList:
        #    step_writer.Transfer(shape, STEPControl_AsIs)
        step_writer.Transfer(compound, STEPControl_AsIs)
        status = step_writer.Write(self.outFileName)
        #if status == 0:            
        print("Done.\n")
        #else:
        #print("Error: can't write file.\n")
        #pass

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

    
    # List of registered IP addresses
    registered_ips = ["219.250.247.155","222.234.112.125", "219.250.247.168", "10.252.34.71", "10.252.32.210", "10.252.33.107", "58.124.52.240", "10.252.32.33"]

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
    threshold_date = datetime(2025, 12, 1)

    # Call the function to get the current time from the website
    current_time = get_current_time(time_website_url)

    # Check if the current time was successfully retrieved
    if current_time is not None:
        print("Current time:", current_time)
        print("License Limit Date:",threshold_date)

        # Compare the current time with the threshold date
        if current_time > threshold_date:
            print("Terminating the application. Threshold date exceeded.")
            # Terminate the application or perform any other desired action
            exit(0)
        else:
            print("Threshold date not exceeded. Continuing with the application.")
            # Continue running the application
    else:
        exit(0)
    
    if len(sys.argv)<2:
        #print("Usage: PackageGenerator.exe [input file path] [output file path]")
        #sys.exit(0)
        sys.argv.clear() 
        sys.argv.append("PackageGenerator")
        sys.argv.append("PackageInfo.txt")
        sys.argv.append("PackageOut.stp")
    
    inputFilePath = sys.argv[1]    
    
    
    #get current directory 
    currentDirectory = os.getcwd()
    #input file to path 
    inputFilePath = os.path.join(currentDirectory,inputFilePath)

    
    print("inputFilePath: ",inputFilePath)     
    if os.path.exists(inputFilePath):
        print("File exists.")
    else:
        print("File does not exist.")
    xOrigin = 0.0
    yOrigin = 0.0 
    package = Package(xOrigin,yOrigin)
    if len(sys.argv)>=3:        
        outputFilePath = sys.argv[2]
        print("outputFilePath: ",outputFilePath)
        package.outFileName = outputFilePath
    package.outFileName = os.path.join(currentDirectory,package.outFileName)

    print("Import Package")
    package.ImportPackage(inputFilePath)
    
    shapes = package.GenerateShapeList()
    
        
    print("Shape Generated")
    print("Export Package")
    package.ExportPackage()
    print("Package Exported")
    print("Display Package")
    i = 0
    from OCC.Display.SimpleGui import init_display
    display, start_display, add_menu, add_function_to_menu = init_display()
    for shape in shapes:
        if shape != None:
            display.DisplayShape(shape,update=False)    
        i = i + 1
        #print("Shape " + str(i) + " Displayed")

    display.FitAll()
    start_display()

    


    


