import os
from KooODBCADManager.Component import PCBComponent, PackageComponent
from KooODBCADManager.PackageManager import PackageManager

class ComponentManager():
    #unitamp = 25.4
    def __init__(self,id,name,pkgMan : PackageManager, isTop = False, zLoc = 0.0, thickness = 1.6, unitamp = 1):
        self.id = id
        self.name = name
        self.components = {}
        self.componentsPCB = {}        
        self.packageManager : PackageManager = pkgMan

        self.isTop = isTop
        self.pcbThickness = thickness
        self.pcbZLoc = zLoc
        self.unitamp = unitamp

    def SetUnitAmp(self,unitamp):
        self.unitamp = unitamp
        self.packageManager.SetUnitAmp(unitamp)
    
    def AddPackageComponent(self,id,newComp):
        self.components[id] = newComp
        return newComp
    
    def AddPCBComponent(self,id,newComp):
        self.componentsPCB[id] = newComp
        return newComp

    def CreatePCBComponent(self,id,originX,originY,rotation,mirror,PCBRef):
        curPCB = self.packageManager.FindPCB(PCBRef)
        if curPCB == None:
            return None
        newCompPCB = PCBComponent(id,curPCB)
        newCompPCB.SetOrigin(originX,originY)
        newCompPCB.SetRotation(rotation)
        newCompPCB.SetMirror(mirror)
        self.AddPCBComponent(id,newCompPCB)
        return newCompPCB
    
    def CreatePackageComponent(self,id,originX,originY,originZ,rotation,mirror,packageRef,packageThickness):
        curPackage = self.packageManager.FindPackage(packageRef)
        if curPackage == None:
            return None
        newCompPackage = PackageComponent(id,curPackage)
        newCompPackage.SetOrigin(originX,originY,originZ)        
        newCompPackage.SetRotation(rotation)
        newCompPackage.SetMirror(mirror)
        newCompPackage.SetPackageThickness(packageThickness)
        self.AddPackageComponent(id,newCompPackage)
        return newCompPackage

    def ImportComponentfromODB(self,stream):
        sline = stream.readline()
        if isinstance(sline, bytes):
            sline = sline.decode('utf-8')
        sline = sline.lstrip()

        
        #for pcbid  in self.packageManager.pcb:
        #    self.CreatePCBComponent(pcbid,0,0,0,False,pcbid)

        while not self.is_eof(stream):
            if len(sline) ==0:
                pass
            elif sline.find("# CMP") == 0:                
                svector = sline.split(' ')
                id = int(svector[2])
                sline = stream.readline()
                if isinstance(sline, bytes):
                    sline = sline.decode('utf-8')
                sline = sline.lstrip()
                svector = sline.split(' ')
                pkg_ref = int(svector[1])
                xcoord = float(svector[2])*self.unitamp
                ycoord = float(svector[3])*self.unitamp
                zcoord = 0.0
                rotangle = int(float(svector[4]))
                mirror = True
                comp_height = 0.0
                comp_height_max = 0.0
                comp_height_min = 0.0
                xSize = 0.0
                ySize = 0.0
                voltage = 0.0
                value = 0.0
                pkgType = "IC"
                if svector[5] == 'N':
                    mirror = False
                while True:
                    if not sline or sline[0].find("#") == 0:
                        break
                    elif sline.find("comp_height") == 0:
                        svector = sline.split(' ')                        
                        comp_height = float(svector[2].replace('\'','').replace("\n","").replace("mm",""))                                                                    
                    elif "PRP COMP_HEIGHT " in sline:
                        svector = sline.split(' ')                        
                        comp_height = float(svector[2].replace('\'','').replace("\n","").replace("mm",""))                                                
                    elif "PRP COMP_HEIGHT_UNITS " in sline:
                        svector = sline.split(' ')                        
                        if svector[2].replace('\'','') == 'inch':
                            comp_height = comp_height * 25.4                        
                    elif "PRP COMP_HEIGHT_MAX " in sline:
                        svector = sline.split(' ')                        
                        comp_height_max = float(svector[2].replace('\'','').replace("\n","").replace("mm",""))                                                
                    elif "PRP COMP_HEIGHT_MIN " in sline:
                        svector = sline.split(' ')                        
                        comp_height_min = float(svector[2].replace('\'','').replace("\n","").replace("mm",""))                                                
                    elif "PRP VOL" in sline:
                        svector = sline.split(' ')                        
                        voltage = svector[2].replace('\'','').replace("\n","").replace("V","")
                        if voltage == "*":
                            voltage = 0.0
                    elif "PRP VALUE" in sline:
                        svector = sline.split(' ')
                        value = svector[2].replace('\'','').replace("\n","")
                    elif "PRP TYPE" in sline:
                        svector = sline.split(' ')
                        pkgType = svector[2].replace('\'','').replace("\n","")
                    elif "PRP SIZE" in sline:
                        svector = sline.split(' ')
                        pkgSize = svector[2].replace('\'','').replace("\n","")
                        pkgSize = pkgSize.replace("_OPEN","").replace("_CLOSED","").replace("_HALF","").replace("_FULL","")
                        pkgSize = pkgSize.replace("_NC","").replace("_NOC","").replace("_N","").replace("_C","")
                        # if 4 digit, split each 2 digit
                        if len(pkgSize) == 4:
                            xSize = float(pkgSize[0:2])                            
                            ySize = float(pkgSize[2:4])                            
                            comp_height = ySize
                        else:
                            xSize = float(pkgSize[0:2])
                            ySize = float(pkgSize[2:4])
                            if ySize == 0.0:
                                xSize = float(pkgSize[0:3])
                                ySize = float(pkgSize[3:6])
                                zSize = ySize
                            else:                            
                                zSize = float(pkgSize[4:6])
                            comp_height = zSize
                            
                            if comp_height >= 20:
                                xSize = float(pkgSize[0:3])/10.0
                                ySize = float(pkgSize[3:6])/10.0
                                zSize = ySize 
                                comp_height = zSize
                                
                        
                                                                                                      
                    sline = stream.readline()  
                    if isinstance(sline, bytes):
                        sline = sline.decode('utf-8')              
                
                if comp_height_max != 0.0 and comp_height_min != 0.0:
                    comp_height = (comp_height_max + comp_height_min) / 2
                elif comp_height_max != 0.0:
                    comp_height = comp_height_max
                elif comp_height_min != 0.0:
                    comp_height = comp_height_min
                else: 
                    if comp_height_max == 0.0:
                        comp_height_max = comp_height
                    if comp_height_min == 0.0:
                        comp_height_min = comp_height

                if comp_height == 0.0:
                    comp_height = 0.5
                package = self.CreatePackageComponent(id,xcoord,ycoord,zcoord,rotangle,mirror,pkg_ref,comp_height)
                if package == None:
                    print("Error: Package {id} not found".format(id=pkg_ref))
                    continue
                solder_height = 0.1
                # if xSize and ySize is defined, set first polygon as package size
                if xSize != 0.0 and ySize != 0.0:
                    pass     
                # only capacitor has three polygons
                if len(package.pkg.polygons) == 3:
                    solder_height = 0.03
                else:
                    solder_height = 0.08
                package.SetPackageThicknesswithMinMax(comp_height,comp_height_max,comp_height_min)
                package.SetSolderJointThickness(solder_height)                                 
                package.value = value
                print("Import Component {id} {name} {pkg} {x} {y} {z} {rot} {mir}".format(id=id,name=package.pkg.name, pkg=pkg_ref,x=xcoord,y=ycoord,z=zcoord,rot=rotangle,mir=mirror))
                continue

            elif sline[0] =="#":
                sline = stream.readline()
                if isinstance(sline, bytes):
                    sline = sline.decode('utf-8')
                sline = sline.lstrip()
                continue
            sline = stream.readline()
            if isinstance(sline, bytes):
                sline = sline.decode('utf-8')
            sline = sline.lstrip()
    

    def ExportComponenttoODB(self,stream):
        for aComponent in self.components.values():
            id = aComponent.id
            pkg_ref = aComponent.package.id
            xcoord = aComponent.originX
            ycoord = aComponent.originY
            zcoord = aComponent.originZ
            rotangle = aComponent.rotation
            strmirror = 'N'
            if aComponent.mirror == True:
                strmirror = 'Y'
            stream.write("# CMP {id}\n".format(id=id))
            stream.write("CMP {pid},{xc},{rc},{rot},{mir}\n".format(pid=pkg_ref,xc=xcoord,rc=ycoord,rot=rotangle,mir=strmirror))

    def is_eof(self,f):
        cur = f.tell()
        f.seek(0, os.SEEK_END)
        end = f.tell()
        f.seek(cur, os.SEEK_SET)
        return cur == end
    
    def Generate(self, minimumSize = 0.0, detailPADS = {}, udPKGName = {}):
        if self.isTop == True:
            return self.GenerateTop(minimumSize, detailPADS, udPKGName)
        else:
            return self.GenerateBottom(minimumSize, detailPADS, udPKGName)            

    def GenerateTop(self, minimumSize, detailPADS, udPKGName):
        shapeList = []
        pkgZLoc = self.pcbZLoc + self.pcbThickness
        for aComponent in self.components.values():
            aComponent : PackageComponent = aComponent
            boundaryBox = aComponent.BoundaryBox()
            minSize = max(boundaryBox[1]-boundaryBox[0],boundaryBox[3]-boundaryBox[2])
            if minSize < minimumSize:
                continue    
            '''if "fsc" in aComponent.pkg.name:
                aComponent.pkg.polygons[0].ReshapeHolePolygonstoShell()
                aComponent.type = "ShieldCan"'''
            if aComponent.pkg.name in udPKGName:
                if udPKGName[aComponent.pkg.name] == "None":
                    continue
                shape = aComponent.GenerateTopUserdefined(pkgZLoc,udPKGName[aComponent.pkg.name])
                if shape == None:
                    continue
            else:
                shape = aComponent.GenerateTop(pkgZLoc,detailPADS)

            print("Draw Component Top {id} {name}".format(id=aComponent.id,name=aComponent.pkg.name))

            if shape != None:
                shapeList.append(shape)
        return shapeList
    
    
    def GenerateBottom(self, minimumSize, detailPADS, udPKGName):
        shapeList = [] 
        pkgZLoc = self.pcbZLoc
        for aComponent in self.components.values():
            aComponent : PackageComponent = aComponent
            boundaryBox = aComponent.BoundaryBox()
            minSize = max(boundaryBox[1]-boundaryBox[0],boundaryBox[3]-boundaryBox[2])
            if minSize < minimumSize:
                continue      
            if "intp_P3_L_R03_SLAVE" in aComponent.pkg.name:
                pass      
            '''if "fsc" in aComponent.pkg.name:
                aComponent.pkg.polygons[0].ReshapeHolePolygonstoShell()
                aComponent.type = "ShieldCan"'''
            if aComponent.pkg.name in udPKGName:
                if udPKGName[aComponent.pkg.name] == "None":
                    continue
                shape = aComponent.GenerateBottomUserdefined(pkgZLoc,udPKGName[aComponent.pkg.name])
                if shape == None:
                    continue
            else:
                shape = aComponent.GenerateBottom(pkgZLoc,detailPADS)
            print("Draw Component Bottom {id} {name}".format(id=aComponent.id,name=aComponent.pkg.name))
            if shape != None:
                shapeList.append(shape)
        return shapeList
    
    def ExportComponent(self,folderPath, mininumSize = 0.0):
        if self.isTop == True:
            return self.ExportComponentTop(folderPath,mininumSize)
        else:
            return self.ExportComponentBottom(folderPath,mininumSize)
        
    def ExportComponentTop(self,folderPath, mininumSize):
        pkgZLoc = self.pcbZLoc + self.pcbThickness
        for aComponent in self.components.values():
            aComponent : PackageComponent = aComponent
            boundaryBox = aComponent.BoundaryBox()
            minSize = max(boundaryBox[1]-boundaryBox[0],boundaryBox[3]-boundaryBox[2])
            if minSize < mininumSize:
                continue            
            pkgName = aComponent.pkg.name
            
            if "qfn8mp_W110L110_C035_2_v2" in pkgName:
                pass             
            fileName = "{pkgName}_{compID}.txt".format(pkgName=pkgName,compID=aComponent.id)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,"w") as f:
                aComponent.ExportTop(f,pkgZLoc, False)
            fileName = "{pkgName}_{compID}_mesh.txt".format(pkgName=pkgName,compID=aComponent.id)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,"w") as f:
                aComponent.ExportTop(f,pkgZLoc, True)
                            
            fileName = "{pkgName}_detail_{compID}.txt".format(pkgName=pkgName,compID=aComponent.id)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,"w") as f:
                aComponent.ExportTopDetail(f,pkgZLoc, False)
            fileName = "{pkgName}_detail_{compID}_mesh.txt".format(pkgName=pkgName,compID=aComponent.id)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,"w") as f:
                aComponent.ExportTopDetail(f,pkgZLoc, True)
            print("Export Component Top {id} {name}".format(id=aComponent.id,name=aComponent.pkg.name))
        return True
    def ExportComponentBottom(self,folderPath, mininumSize):
        pkgZLoc = self.pcbZLoc
        for aComponent in self.components.values():
            aComponent : PackageComponent = aComponent
            boundaryBox = aComponent.BoundaryBox()
            minSize = max(boundaryBox[1]-boundaryBox[0],boundaryBox[3]-boundaryBox[2])
            if minSize < mininumSize:
                continue            
            pkgName = aComponent.pkg.name            
            fileName = "{pkgName}_{compID}.txt".format(pkgName=pkgName,compID=aComponent.id)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,"w") as f:
                aComponent.ExportBottom(f,pkgZLoc, False)
            fileName = "{pkgName}_{compID}_mesh.txt".format(pkgName=pkgName,compID=aComponent.id)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,"w") as f:
                aComponent.ExportBottom(f,pkgZLoc, True)
                            
            fileName = "{pkgName}_detail_{compID}.txt".format(pkgName=pkgName,compID=aComponent.id)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,"w") as f:
                aComponent.ExportBottomDetail(f,pkgZLoc, False)            
            fileName = "{pkgName}_detail_{compID}_mesh.txt".format(pkgName=pkgName,compID=aComponent.id)
            filePath = os.path.join(folderPath,fileName)
            with open(filePath,"w") as f:
                aComponent.ExportBottomDetail(f,pkgZLoc, True)
                                              
            print("Export Component Bottom {id} {name}".format(id=aComponent.id,name=aComponent.pkg.name))
        pass