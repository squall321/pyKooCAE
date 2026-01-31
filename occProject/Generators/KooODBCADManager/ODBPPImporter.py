import os
from KooODBCADManager.Polygon import Polygon2D as Poly
from KooODBCADManager.PolygonManager import PolygonManager2D as PolygonManager

class ODBPPImporter():
    
    def __init__(self,unitamp = 25.4):
        self.unitAmp = unitamp
        pass

    def SetUnitAmp(self,unitamp):
        self.unitAmp = unitamp

    def ImportPolygonfromFlatVector(self,polyMan : PolygonManager,svector,stream=0):
        aPoly = polyMan.CreatePolygonfromFlattenVector(svector)
        return aPoly

    def ImportPolygon(self,polyMan : PolygonManager,sline,stream=0):
        sline = sline.lstrip()
        svector = sline.split(' ')
        if sline.find('RC') == 0:
            lowleftX = float(svector[1])*self.unitAmp
            lowleftY = float(svector[2])*self.unitAmp
            width = float(svector[3])*self.unitAmp
            height = float(svector[4])*self.unitAmp
            vertices = [] 
            vertices.append(polyMan.CreateVertex(lowleftX,lowleftY))
            vertices.append(polyMan.CreateVertex(lowleftX+width,lowleftY))
            vertices.append(polyMan.CreateVertex(lowleftX+width,lowleftY+height))
            vertices.append(polyMan.CreateVertex(lowleftX,lowleftY+height))
            vertices.append(polyMan.CreateVertex(lowleftX,lowleftY))
            aPoly = polyMan.CreatePolygon(vertices,'RC')
            return aPoly
        elif sline.find('SQ') == 0:
            xc = float(svector[1])*self.unitAmp
            yc = float(svector[2])*self.unitAmp
            length = float(svector[3])*self.unitAmp
            vertices = []
            vertices.append(polyMan.CreateVertex(xc-length/2,yc-length/2))
            vertices.append(polyMan.CreateVertex(xc+length/2,yc-length/2))
            vertices.append(polyMan.CreateVertex(xc+length/2,yc+length/2))
            vertices.append(polyMan.CreateVertex(xc-length/2,yc+length/2))
            vertices.append(polyMan.CreateVertex(xc-length/2,yc-length/2))
            aPoly = polyMan.CreatePolygon(vertices,'RC')
        elif sline.find('CR') == 0:
            xc = float(svector[1])*self.unitAmp
            yc = float(svector[2])*self.unitAmp
            radius = float(svector[3])*self.unitAmp
            vertices = []
            v = polyMan.CreateVertex(xc,yc,radius)
            vertices.append(v)
            aPoly = polyMan.CreatePolygon(vertices,'CR')
            return aPoly
        elif sline.find('CT') == 0:
            if stream ==0:
                return None
            vertices = []
            edges = []
            prevVertex = None
            while True:
                sline = stream.readline()
                if isinstance(sline, bytes):
                    sline = sline.decode('utf-8')
                svector = sline.split(' ')
                if sline.find('#') == 0:
                    break
                elif sline.find('OB') == 0 or sline.find('OS') == 0:
                    x = float(svector[1])*self.unitAmp
                    y = float(svector[2])*self.unitAmp
                    v = polyMan.CreateVertex(x,y)
                    if prevVertex is not None:
                        edges.append(polyMan.CreateLine(prevVertex, v))
                    vertices.append(v)
                    prevVertex = v
                elif sline.find('OC') == 0:
                    xEnd = float(svector[1])*self.unitAmp
                    yEnd = float(svector[2])*self.unitAmp
                    xCenter = float(svector[3])*self.unitAmp
                    yCenter = float(svector[4])*self.unitAmp
                    cw = svector[5].strip().lower() == 'y'
                    vEnd = polyMan.CreateVertex(xEnd, yEnd)
                    vCenter = polyMan.CreateVertex(xCenter, yCenter)
                    if prevVertex is not None:
                        edges.append(polyMan.CreateArc(prevVertex, vEnd, vCenter, not cw))
                    vertices.append(vEnd)
                    vertices.append(vCenter)
                    prevVertex = vEnd
                elif sline.find('OE') == 0 or sline.find('CE') == 0:
                    break
            if len(edges) > 0:
                aPoly = polyMan.CreatePolygon(vertices,'CT', edges)
            else:
                aPoly = polyMan.CreatePolygon(vertices,'CT')
            if aPoly is not None:
                aPoly.ReduceEdgesToArcs()
            return aPoly
        else:
            return None

    def ImportFeature(self, polyMan, sline, stream):
        if stream == 0:
            return None
        vertices = []
        edges = []
        prevVertex = None
        while True:
            sline = stream.readline()
            svector = sline.split(' ')
            if sline.find('#') == 0:
                break
            elif sline.find('OB') == 0 or sline.find('OS') == 0:
                x = float(svector[1])
                y = float(svector[2])
                v = polyMan.CreateVertex(x,y)
                if prevVertex is not None:
                    edges.append(polyMan.CreateLine(prevVertex, v))
                vertices.append(v)
                prevVertex = v
            elif sline.find('OC') == 0:
                xEnd = float(svector[1])
                yEnd = float(svector[2])
                xCenter = float(svector[3])
                yCenter = float(svector[4])
                cw = svector[5].strip().lower() == 'y'
                vEnd = polyMan.CreateVertex(xEnd, yEnd)
                vCenter = polyMan.CreateVertex(xCenter, yCenter)
                if prevVertex is not None:
                    edges.append(polyMan.CreateArc(prevVertex, vEnd, vCenter, not cw))
                vertices.append(vEnd)
                vertices.append(vCenter)
                prevVertex = vEnd
            elif sline.find('OE') == 0 or sline.find('SE') == 0:
                break
        if len(edges) > 0:
            aPoly = polyMan.CreatePolygon(vertices,'CT', edges)
        else:
            aPoly = polyMan.CreatePolygon(vertices,'CT')
        if aPoly is not None:
            aPoly.ReduceEdgesToArcs()
        return aPoly
    
    def ImportPCBFeature(self, polyMan, stream):
        edgesUnitList = self.ImportEdgeFeature(stream)
        unitPolygonList = self.RawEdgeListtoPolygons(polyMan,edgesUnitList)
        return unitPolygonList

    def ImportEdgeFeature(self, stream):
        if stream == 0:
            return None
        edgesUnitList = {}
        unit = "MM"
        unitamp = 1.0 
        xprev = 0.0 
        yprev = 0.0
        curKey = 0      
        #edgesUnitList[curKey] = []
        while not self.is_eof(stream):
            sline = stream.readline()
            sline = sline.replace("\n","")
            svector = sline.split(' ')
            if svector[0].find('#') == 0:
                continue
            elif svector[0].find("U") == 0:
                if sline.find("MM") == 0:
                    unit = "MM"
                elif sline.find("INCH") >= 0:
                    unit = "INCH"
                    unitamp = 25.4
            elif svector[0].find("A") == 0:                
                x1 = round(float(svector[1])*unitamp,6)
                y1 = round(float(svector[2])*unitamp,6)
                x2 = round(float(svector[3])*unitamp,6)
                y2 = round(float(svector[4])*unitamp,6)
                x3 = round(float(svector[5])*unitamp,6)
                y3 = round(float(svector[6])*unitamp,6)
                clk = 1
                if sline.find("Y") == 0:
                    clk = 0          
                if curKey in edgesUnitList:
                    pass
                else:
                    edgesUnitList[curKey] = []                
                edgesUnitList[curKey].append([x1,y1,x2,y2,x3,y3,clk])
                curKey = curKey + 1
            elif svector[0].find("L") == 0:
                x1 = round(float(svector[1])*unitamp,6)
                y1 = round(float(svector[2])*unitamp,6)
                x2 = round(float(svector[3])*unitamp,6)
                y2 = round(float(svector[4])*unitamp,6)
                if curKey in edgesUnitList:
                    pass
                else:
                    edgesUnitList[curKey] = []
                edgesUnitList[curKey].append([x1,y1,x2,y2])
                curKey = curKey + 1
            elif sline.find('OB') == 0:
                x = float(svector[1])
                y = float(svector[2])
                xprev = x
                yprev = y
                curKey = curKey + 1

            elif sline.find('OS') == 0:
                x = float(svector[1])
                y = float(svector[2])
                print(xprev,yprev,x,y)
                if curKey in edgesUnitList:
                    pass
                else:
                    edgesUnitList[curKey] = []

                edgesUnitList[curKey].append([xprev,yprev,x,y])
                xprev = x
                yprev = y

            elif sline.find('OC') == 0:
                xEnd = float(svector[1])
                yEnd = float(svector[2])
                xCenter = float(svector[3])
                yCenter = float(svector[4])
                clk = 0
                if svector[5].strip().lower() == 'y':
                    clk = 1
                if curKey in edgesUnitList:
                    pass
                else:
                    edgesUnitList[curKey] = []
                edgesUnitList[curKey].append([xprev,yprev,xEnd,yEnd,xCenter,yCenter,clk])
                xprev = xEnd
                yprev = yEnd

            elif sline.find('OE') == 0 or sline.find('SE') == 0:
                break
       
        return edgesUnitList

    def ImportArrayFeature(self, polyMan, stream):
        if stream == 0:
            return None
        
        edgesUnitList = {} 
        edgesArrayList = {}
        edgesBridgeList = {}
        edgesHoleList = {}

        unit = "MM"
        unitamp = 1.0
        while not self.is_eof(stream):
            sline = stream.readline() 
            sline = sline.replace("\n","")
            svector = sline.split(' ')
            
            if svector[0].find('#') == 0:
                continue
            elif svector[0].find("U") == 0:
                if sline.find("MM") == 0:
                    unit = "MM"
                elif sline.find("INCH") >= 0:
                    unit = "INCH"
                    unitamp = 25.4
            elif svector[0].find("A") == 0:                
                curi =svector[len(svector)-1]
                if len(curi) == 0:
                    curi = svector[len(svector)-2]
                    if len(curi) == 0:
                        curi = svector[len(svector)-3]
                    
                #print("unit test : ", unitamp)
                curKey = int(curi)
                #curKey = int(svector[len(svector)-1])
                x1 = round(float(svector[1])*unitamp,6)
                y1 = round(float(svector[2])*unitamp,6)
                x2 = round(float(svector[3])*unitamp,6)
                y2 = round(float(svector[4])*unitamp,6)
                x3 = round(float(svector[5])*unitamp,6)
                y3 = round(float(svector[6])*unitamp,6)
                clk = 0
                if sline.find("Y") == 0:
                    clk = 1             
                if curKey >= 10000:
                    ## hole 
                    if curKey in edgesHoleList:
                        edgesHoleList[curKey].append([x1,y1,x2,y2,x3,y3,clk]) 
                    else:
                        edgesHoleList[curKey] = []
                        edgesHoleList[curKey].append([x1,y1,x2,y2,x3,y3,clk]) 
                    pass
                elif curKey >= 100 and curKey < 1000:
                    if curKey in edgesUnitList:
                        edgesUnitList[curKey].append([x1,y1,x2,y2,x3,y3,clk]) 
                    else:
                        edgesUnitList[curKey] = []
                        edgesUnitList[curKey].append([x1,y1,x2,y2,x3,y3,clk]) 
                else:
                    if curKey in edgesArrayList:
                        edgesArrayList[curKey].append([x1,y1,x2,y2,x3,y3,clk]) 
                    else:
                        edgesArrayList[curKey] = []
                        edgesArrayList[curKey].append([x1,y1,x2,y2,x3,y3,clk]) 

                    
            elif svector[0].find("L") == 0:
                
                #print("unit test : ", unitamp)
                curi =svector[len(svector)-1]
                if len(curi) == 0:
                    curi = svector[len(svector)-2]
                    if len(curi) == 0:
                        curi = svector[len(svector)-3]
                    
                curKey = int(curi)
                #print(curKey)
                x1 = round(float(svector[1])*unitamp,6)
                y1 = round(float(svector[2])*unitamp,6)
                x2 = round(float(svector[3])*unitamp,6)
                y2 = round(float(svector[4])*unitamp,6)

                if curKey >= 1000 and curKey < 10000:
                    ## bridge
                    if curKey in edgesBridgeList:
                        edgesBridgeList[curKey].append([x1,y1,x2,y2])
                    else:
                        edgesBridgeList[curKey] = []
                        edgesBridgeList[curKey].append([x1,y1,x2,y2])
                    pass
                elif curKey >= 10000:
                    ## hole
                    if curKey in edgesHoleList:
                        edgesHoleList[curKey].append([x1,y1,x2,y2])
                    else:
                        edgesHoleList[curKey] = []
                        edgesHoleList[curKey].append([x1,y1,x2,y2])
                    pass
                elif curKey >= 100 and curKey < 1000:                    
                    ## unit 
                    if curKey in edgesUnitList:
                        edgesUnitList[curKey].append([x1,y1,x2,y2])
                    else:
                        edgesUnitList[curKey] = []
                        edgesUnitList[curKey].append([x1,y1,x2,y2])
                    pass
                else:
                    ## array
                    if curKey in edgesArrayList:
                        edgesArrayList[curKey].append([x1,y1,x2,y2])
                    else:
                        edgesArrayList[curKey] = []
                        edgesArrayList[curKey].append([x1,y1,x2,y2])
                    pass
            elif len(sline) == 0:
                pass
            else:
                pass

        #if polyMan != None:
        unitPolygonList = self.RawEdgeListtoPolygons(polyMan,edgesUnitList)
        arrayPolygonList = self.RawEdgeListtoPolygons(polyMan,edgesArrayList)
        holePolygonList = self.RawEdgeListtoPolygons(polyMan,edgesHoleList)
        bridgePolygonList = self.RawEdgeofBridgetoPolygons(polyMan,edgesBridgeList)
        return [unitPolygonList,arrayPolygonList,holePolygonList,bridgePolygonList]
        #else:
        #    return [edgesUnitList,edgesArrayList,edgesHoleList,edgesBridgeList]


    def RawEdgeofBridgetoPolygons(self,polyMan,edgesList):
        polygonList = {} 
        for key in edgesList.keys():
            tmpPoly = edgesList[key]
            e1 = tmpPoly[0]
            e2 = tmpPoly[1]
            x1 = e1[0]
            y1 = e1[1]
            x2 = e1[2]
            y2 = e1[3]
            x3 = e2[0]
            y3 = e2[1]
            x4 = e2[2]
            y4 = e2[3]
            v1 = polyMan.CreateVertex(x1,y1)
            v2 = polyMan.CreateVertex(x2,y2)
            v3 = polyMan.CreateVertex(x3,y3)
            v4 = polyMan.CreateVertex(x4,y4)
            vertices = [v1,v2,v4,v3,v1]
            edges = polyMan.CreateLines(vertices)            
            aPoly = polyMan.CreatePolygon(vertices,"L",edges)
            polygonList[key] = aPoly
        return polygonList
    
    def RawEdgeListtoPolygons(self,polyMan,edgesList):
        polygonList = {}
        tmpPolyMan = PolygonManager()        

        for key in edgesList.keys():
            tmpPoly = edgesList[key]
            for curEdge in tmpPoly:
                # 2 points 4 data
                if len(curEdge) == 4:
                    x1 = curEdge[0]
                    y1 = curEdge[1]
                    x2 = curEdge[2]
                    y2 = curEdge[3]
                    tmpPolyMan.FindVertex(x1,y1)
                    tmpPolyMan.FindVertex(x2,y2)
                # 3 points 6 data +clk = 7 
                elif len(curEdge) == 7:
                    x1 = curEdge[0] 
                    y1 = curEdge[1]
                    x2 = curEdge[2]
                    y2 = curEdge[3]
                    x3 = curEdge[4]
                    y3 = curEdge[5]
                    clk = curEdge[6] 
                    tmpPolyMan.FindVertex(x1,y1)
                    tmpPolyMan.FindVertex(x2,y2)
                    tmpPolyMan.FindVertex(x3,y3)
        polyMan.CreateNewVertices(tmpPolyMan.vertices)
        for key in edgesList.keys():
            curPoly = edgesList[key]
            vertices = [] 
            edges = []             
            for curEdge in curPoly:                
                if len(curEdge) == 4:
                    x1 = curEdge[0]
                    y1 = curEdge[1]
                    x2 = curEdge[2]
                    y2 = curEdge[3]
                    v1 = polyMan.FindVertex(x1,y1)                    
                    v2 = polyMan.FindVertex(x2,y2)
                    vertices.append(v1)
                    vertices.append(v2)
                    e = polyMan.CreateLine(v1,v2)
                    edges.append(e)                    
                elif len(curEdge) == 7:
                    x1 = curEdge[0] 
                    y1 = curEdge[1]
                    x2 = curEdge[2]
                    y2 = curEdge[3]
                    x3 = curEdge[4]
                    y3 = curEdge[5]
                    clk = curEdge[6] 
                    tmpPolyMan.FindVertex(x1,y1)
                    tmpPolyMan.FindVertex(x2,y2)
                    tmpPolyMan.FindVertex(x3,y3)
                    v1 = polyMan.FindVertex(x1,y1)
                    v2 = polyMan.FindVertex(x2,y2)
                    v3 = polyMan.FindVertex(x3,y3)
                    vertices.append(v1)
                    vertices.append(v2)
                    vertices.append(v3)
                    if clk == 1:
                        e = polyMan.CreateArc(v1,v2,v3,True)
                    else:
                        e = polyMan.CreateArc(v1,v2,v3,False)                    
                    edges.append(e)
            aPoly = polyMan.CreatePolygon(vertices,'L',edges)
            polygonList[key] = aPoly
        return polygonList

    def AddPointatPolygonList(self,polyMan, polyList, x, y):
        for i in range(0, len(polyList)):
            if self.FindPointfromPolygon(polyList[i]) == True:
                polyList[i].AddVertex(polyMan.CreateVertex(x,y))
                return i
        vertices = [] 
        vertices.append(polyMan.CreateVertex(x,y))
        aPoly = polyMan.CreatePolygon(vertices,'L')
        polyList.append(aPoly)
        return len(polyList)-1    
        
    def FindPointfromPolygon(self, poly, x, y):
        for i in range(0, len(poly.vertices)):
            if poly.vertices[i].x == x and poly.vertices[i].y == y:
                return True
        return False                     

    def is_eof(self,f):
        cur = f.tell()
        f.seek(0, os.SEEK_END)
        end = f.tell()
        f.seek(cur, os.SEEK_SET)
        return cur == end

        


    
