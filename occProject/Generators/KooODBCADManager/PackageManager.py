import os
from KooODBCADManager.Package import Package
from KooODBCADManager.PCB import PCB
from KooODBCADManager.Polygon import Polygon2D as Polygon
from KooODBCADManager.PolygonManager import PolygonManager2D as PolygonManager
from KooODBCADManager.ODBPPImporter import ODBPPImporter
import random

class PackageManager():
    def __init__(self,polyMan, unitamp = 1.0):
        self.packages = {}
        self.polygonManager = polyMan
        self.odbpImporter = ODBPPImporter(unitamp)

    def SetUnitAmp(self,unitamp):
        self.odbpImporter.SetUnitAmp(unitamp)

    def CreatePackage(self,id,name,polygonList):
        newPackage = Package(id,name)
        cx = [0.929411765,0.235294118,0.721568627,0,0.941176471,0.274509804,0.678431373,0.482352941,0.780392157,1,0.333333333,0.098039216,0.415686275,0.878431373,0,0.82745098,0.823529412,0.545098039,0.941176471,0.466666667,0.498039216,0.501960784,0.901960784,0.858823529,0.941176471,0.2,0,0.678431373,0.870588235,0.529411765,0.529411765,0.803921569,0.411764706,0,0.580392157,0,0,0,1,0.576470588,0.741176471,1,0.647058824,1,0.282352941,0,0.196078431,0.737254902,0.419607843,0.254901961,0.498039216,1,0.91372549,0.933333333,0,0.858823529,0.501960784,0.596078431,0.117647059,0.392156863,0,0.501960784,0.282352941,0,0.847058824,0.698039216,0.941176471,0.980392157,1,0.501960784,0.333333333,0.662745098,0.690196078,0.588235294,0,0.780392157,0.541176471,0,0.294117647,0.180392157,0.545098039,0,1,0.564705882,1,0.6,1,0.250980392,0.603921569,0.729411765,0.37254902,0,1,0,0.62745098,1,0.823529412,0.752941176,1,1,0.854901961,0.133333333,1,1,1,0.862745098,0.933333333,0.980392157,1,0.803921569,0.854901961,0.68627451,0.545098039,0.690196078,0.4,0.866666667,1]
        cy = [0.643137255,0.701960784,0.525490196,0.501960784,0.501960784,0.509803922,0.847058824,0.407843137,0.082352941,0.270588235,0.419607843,0.098039216,0.352941176,1,0,0.82745098,0.411764706,0.270588235,0.97254902,0.533333333,1,0.501960784,0.901960784,0.439215686,0.901960784,0.6,0.807843137,1,0.721568627,0.807843137,0.807843137,0.360784314,0.411764706,0.8,0,0,1,0,0.62745098,0.439215686,0.717647059,0.941176471,0.164705882,0.411764706,0.239215686,0.392156863,0.803921569,0.560784314,0.556862745,0.411764706,1,0.647058824,0.588235294,0.909803922,0,0.439215686,0.501960784,0.984313725,0.564705882,0.584313725,1,0,0.819607843,0.980392157,0.749019608,0.133333333,1,0.501960784,0.71372549,0,0.419607843,0.662745098,0.768627451,0.588235294,0.501960784,0.082352941,0.168627451,0.545098039,0,0.545098039,0,1,0.843137255,0.933333333,0,0.196078431,0.549019608,0.878431373,0.803921569,0.333333333,0.619607843,0.749019608,0.6,0,0.321568627,0.388235294,0.705882353,0.752941176,1,0.752941176,0.647058824,0.545098039,1,0,0.498039216,0.862745098,0.509803922,0.980392157,0.078431373,0.521568627,0.439215686,0.933333333,0,0.878431373,0.803921569,0.62745098,0.4] 
        cz = [0.239215686,0.443137255,0.043137255,0,0.501960784,0.705882353,0.901960784,0.933333333,0.521568627,0,0.184313725,0.439215686,0.803921569,1,0,0.82745098,0.117647059,0.074509804,1,0.6,0,0.501960784,0.980392157,0.576470588,0.549019608,0.4,0.819607843,0.184313725,0.529411765,0.921568627,0.980392157,0.360784314,0.411764706,1,0.82745098,0.803921569,0.498039216,0.545098039,0.478431373,0.858823529,0.419607843,0.960784314,0.164705882,0.705882353,0.545098039,0,0.196078431,0.560784314,0.137254902,0.882352941,0.831372549,0,0.478431373,0.666666667,0.501960784,0.576470588,0,0.596078431,1,0.929411765,1,0,0.8,0.603921569,0.847058824,0.133333333,1,0.447058824,0.756862745,0.501960784,0.184313725,0.662745098,0.870588235,0.588235294,0.501960784,0.521568627,0.88627451,0.545098039,0.509803922,0.341176471,0,0,0,0.564705882,1,0.8,0,0.815686275,0.196078431,0.82745098,0.62745098,1,0,1,0.176470588,0.278431373,0.549019608,0.752941176,0.878431373,0.796078431,0.125490196,0.133333333,0,0,0.31372549,0.862745098,0.933333333,0.823529412,0.576470588,0.247058824,0.839215686,0.933333333,0.545098039,0.901960784,0.666666667,0.866666667,0]
        cx = cx[id%117]
        cy = cy[id%117]
        cz = cz[id%117]
        newPackage.SetColor(cx,cy,cz,1.0)
        for aPoly in polygonList:
            newPackage.AddPolygon(aPoly)
        return self.AddPackage(newPackage)    
    
    def AddPackage(self,newPackage):
        self.packages[newPackage.id] = newPackage        
        return newPackage
    
    def RemovePackage(self,id):
        self.packages.pop(id)
    
    def FindPackage(self,id):
        if id in self.packages:
            return self.packages[id]
        else:
            return None
    
    def ImportPackagesfromODB(self,stream):
        
        print("Import Packages from ODB++")
        sline = stream.readline()
        isByte = False
        if isinstance(sline, bytes):
            isByte = True
        if isByte:
            sline = sline.decode('utf-8')

        sline = sline.lstrip()
        ii = 0 
        while not self.is_eof(stream):
            if len(sline) ==0:
                pass
            elif len(sline)>0:
                if "PRP BOARD_PLACEMENT_OUTLINE" in sline:
                    pass
                    #self.maxPCBID = self.maxPCBID + 1
                    #svector = sline.split(' ')
                    #svector = svector[3:]
                    #self.CreatePCB(self.maxPCBID,svector)
                if len(sline) == 0:
                    pass
                elif sline.find("# PKG") ==0:
                    svector = sline.split(' ')
                    id = int(svector[2])
                    sline = stream.readline()
                    if isByte:
                        sline = sline.decode('utf-8')
                    sline = sline.lstrip()
                    svector = sline.split(' ')
                    pkgname = svector[1] 
                    polygonList = []
                    if len(svector)>=7:
                        sline = stream.readline()
                        if isByte:
                            sline = sline.decode('utf-8')
                        svector = sline.split(' ')
                        aPoly = self.odbpImporter.ImportPolygon(self.polygonManager,sline,stream)
                        polygonList.append(aPoly)
                    
                    while True:
                        if not sline or sline[0].find("#") ==0:
                            break
                        elif sline.find('PIN')==0:
                            sline = stream.readline()       
                            if isByte:
                                sline = sline.decode('utf-8')                     
                            aPoly = self.odbpImporter.ImportPolygon(self.polygonManager,sline,stream)
                            polygonList.append(aPoly)
                        sline = stream.readline()
                        if isByte:
                            sline = sline.decode('utf-8')
                    self.CreatePackage(id,pkgname,polygonList)
                    print("Package ID : ",id," Package Name : ",pkgname)
                    continue
                elif sline[0] == '#':
                    sline = stream.readline()
                    if isByte:
                        sline = sline.decode('utf-8')
                    sline = sline.lstrip()
                    continue
            sline = stream.readline()
            if isByte:
                sline = sline.decode('utf-8')
            sline = sline.lstrip()
            ii = ii + 1 
            if ii%1000 == 0:
                print(ii,"th line is read")
    
    def WritePackagestoJSON(self,path):
        for aPackage in self.packages.values():
            aPackage.WritePackageJSON(path)

    def WritePackagestoFile(self,stream):
        for aPackage in self.packages.values():
            aPackage.WritePackage(stream)

    def is_eof(self,f):
        cur = f.tell()
        f.seek(0, os.SEEK_END)
        end = f.tell()
        f.seek(cur, os.SEEK_SET)
        return cur == end
    
    def ExportPackage(self, folderPath, minimumSize = 0.0):
        for aPackage in self.packages.values():
            aPackage : Package = aPackage            
            boundBox = aPackage.BoundaryBox()
            minSize = min(boundBox[1]-boundBox[0],boundBox[3]-boundBox[2])
            if minSize < minimumSize:
                continue
            pkgName = aPackage.name
            fileName = "{pkgname}.txt".format(pkgname=pkgName)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,'w') as f:
                aPackage.ExportPackage(f)            
            print("Exported Package : ",pkgName," to ",filePath)
            fileName = "{pkgname}_detail.txt".format(pkgname=pkgName)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,'w') as f:
                aPackage.ExportDetailPackage(f)
                f.close()
        return True







    

        