import os 
from KooODBCADManager.PCB import PCB
from KooODBCADManager.ArrayPCB import ArrayPCB
from KooODBCADManager.ODBPPImporter import ODBPPImporter

class PCBManager():
    
    def __init__(self, polyMan):
        self.pcb = {}
        self.arraypcb = {}
        self.maxPCBID = 0
        self.maxArrayPCBID = 0 
        self.odbpImporter = ODBPPImporter()
        self.polyMan = polyMan
    
    def CreatePCBfromFlatVector(self,id,flatVertexVector):
        newPCB= PCB(id)
        self.maxPCBID = max(self.maxPCBID,id)
        cx = 1
        cy = 1
        cz = 1
        newPCB.SetColor(cx,cy,cz,1.0)
        pcbPolygon = self.odbpImporter.ImportPolygonfromFlatVector(self.polygonManager,flatVertexVector)
        newPCB.AddPolygon(pcbPolygon)
        self.pcb[id] = newPCB
        return newPCB
    
    def CreatePCB(self):
        self.maxPCBID = self.maxPCBID + 1
        newPCB = PCB(self.maxPCBID)
        newPCB.SetColor(0.5,0.5,0.5,1.0)
        self.pcb[self.maxPCBID] = newPCB
        return newPCB    
    
    def CreateArrayPCB(self):
        self.maxArrayPCBID = self.maxArrayPCBID + 1
        newArrayPCB = ArrayPCB(self.maxArrayPCBID)        
        newArrayPCB.SetColor(0.5,0.5,0.5,1.0)
        self.arraypcb[self.maxArrayPCBID] = newArrayPCB
        return newArrayPCB
    
    def InsertPCB(self,id):
        newPCB = PCB(id)
        self.maxPCBID = max(self.maxPCBID,id)
        newPCB.SetColor(0.5,0.5,0.5,1.0)
        self.pcb[id] = newPCB
    
    def InsertArrayPCB(self,id):
        newArrayPCB = ArrayPCB(id)
        self.maxArrayPCBID = max(self.maxArrayPCBID,id)
        newArrayPCB.SetColor(0.5,0.5,0.5,1.0)
        self.arraypcb[id] = newArrayPCB
    
    def SetPCBDesign(self,id,layup,thickness,material,symbol):
        curPCB = self.FindPCB(id)
        if curPCB != None:
            curPCB.SetLayup(layup)
            curPCB.SetThickness(thickness)
            curPCB.SetMaterialFile(material)
            curPCB.SetSymbolFolder(symbol)
    
    def SetArrayPCBDesign(self, id, layup, thickness, material, symbol):
        curArrayPCB = self.FindArrayPCB(id)
        if curArrayPCB != None:
            curArrayPCB.SetLayup(layup)
            curArrayPCB.SetThickness(thickness)
            curArrayPCB.SetMaterialFile(material)
            curArrayPCB.SetSymbolFolder(symbol)

    def RemovePCB(self,id):
        self.pcb.pop(id)
    
    def RemoveArrayPCB(self,id):
        self.arraypcb.pop(id)

    def FindPCB(self,id):
        if id in self.pcb:
            return self.pcb[id]
        else:
            return None

    def FindArrayPCB(self,id): 
        if id in self.arraypcb:
            return self.arraypcb[id]
        else:
            return None    
        
    def ImportPCBfromODB(self,stream):    
        sline = stream.readline()
        sline = sline.lstrip()
        curPCB = None
        while not self.is_eof(stream):
            
            if len(sline) == 0:
                pass
            elif len(sline) > 0:
                if sline.find("S P") ==0:
                    print("PCB found")
                    curPCB = self.CreatePCB()
                    curPoly = self.odbpImporter.ImportFeature(self.polyMan,sline,stream)
                    curPCB.AddPolygon(curPoly)
                    print("PCB created PCB ID : ",curPCB.id)                                        
            sline = stream.readline()
            sline = sline.lstrip()  
        return curPCB      
    def ImportPCBfromOCBTwo(self,stream):
        curPCB = self.CreatePCB()
        upList = self.odbpImporter.ImportPCBFeature(self.polyMan,stream)
        for i in upList:
            curPCB.AddPolygon(upList[i])
        
        print("PCB created PCB ID : ",curPCB.id)
        return curPCB

    def ImportArrayPCBfromODB(self,stream):          
        curArrayPCB = self.CreateArrayPCB()
        [uplist, aplist, hplist, bplist]= self.odbpImporter.ImportArrayFeature(self.polyMan,stream)
        print(uplist)
        print(aplist)
        print(hplist)
        print(bplist)
        
        curArrayPCB.AddUnitPolygons(uplist)
        curArrayPCB.AddArrayPolygons(aplist)
        curArrayPCB.AddHolePolygons(hplist)
        curArrayPCB.AddBridgePolygons(bplist)
        return curArrayPCB
        
        
    
    def is_eof(self,f):
        cur = f.tell()
        f.seek(0, os.SEEK_END)
        end = f.tell()
        f.seek(cur, os.SEEK_SET)
        return cur == end