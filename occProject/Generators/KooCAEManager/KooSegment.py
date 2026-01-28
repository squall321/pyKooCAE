from __future__ import annotations

class KooSegmentSet:
    def __init__(self, sid, da1=0.0, da2= 0.0, da3 = 0.0, da4 = 0.0, solver = "MECH", its = 0,name=""):
        self.sid = sid         
        self.stype = None
        self.da1 = da1
        self.da2 = da2
        self.da3 = da3
        self.da4 = da4
        self.solver = solver
        self.its = its
        self.segments = []
        self.attributes = []  
        if name == "":
            self.name = "SegmentSet" + str(sid)
        else:
            self.name = name
        
        self.pid = 0
    
    def OffsetNID(self, offset):
        for i in range(len(self.segments)):
            segment = self.segments[i]
            segment[0] += offset
            segment[1] += offset
            segment[2] += offset
            segment[3] += offset               

    def SetSegments(self, segments, attributes):
        self.segments = segments
        self.attributes = attributes
        
    def AddLineSegment(self, n1, n2):
        self.segments.append([n1,n2,n2,n2])
        self.attributes.append([self.da1,self.da2,self.da3,self.da4])
    
    def AddLineSegmentwithAttributes(self, n1, n2, da1, da2, da3, da4):
        self.segments.append([n1,n2,n2,n2])
        self.attributes.append([da1,da2,da3,da4])
    
    def AddTrianagleSegment(self, n1, n2, n3):
        self.segments.append([n1,n2,n3,n3])
        self.attributes.append([self.da1,self.da2,self.da3,self.da4])
    
    def AddTriangleSegmentwithAttributes(self, n1, n2, n3, da1, da2, da3, da4):
        self.segments.append([n1,n2,n3,n3])
        self.attributes.append([da1,da2,da3,da4])
    
    def AddQuadrangleSegment(self, n1, n2, n3, n4):
        self.segments.append([n1,n2,n3,n4])
        self.attributes.append([self.da1,self.da2,self.da3,self.da4])
    
    def AddQuadrangleSegmentwithAttributes(self, n1, n2, n3, n4, da1, da2, da3, da4):
        self.segments.append([n1,n2,n3,n4])
        self.attributes.append([da1,da2,da3,da4])
        
    def AddSegments(self, segments):
        for segment in segments:
            if len(segment) == 2:
                self.AddLineSegment(segment[0], segment[1])
            elif len(segment) == 3:
                self.AddTrianagleSegment(segment[0], segment[1], segment[2])
            elif len(segment) == 4:
                self.AddQuadrangleSegment(segment[0], segment[1], segment[2], segment[3])
            
    
    def WritetoDynaKeyword(self, startID):
        if len(self.segments) == 0:
            return ""
        keyword = ""
        keyword += "*SET_SEGMENT_TITLE\n"
        keyword += format(self.name, ">80") + "\n"
        keyword += format(self.sid + startID, ">10")
        keyword += format(self.da1, ">10.3f")
        keyword += format(self.da2, ">10.3f")
        keyword += format(self.da3, ">10.3f")
        keyword += format(self.da4, ">10.3f")
        keyword += format(self.solver, ">10")
        keyword += format(self.its, ">10")
        keyword += "\n"
        for i in range(len(self.segments)):
            segment = self.segments[i]
            attribute = self.attributes[i]
            n1 = format(segment[0], ">10")
            n2 = format(segment[1], ">10")
            n3 = format(segment[2], ">10")
            n4 = format(segment[3], ">10")
            da1 = format(attribute[0], ">10.3f")
            da2 = format(attribute[1], ">10.3f")
            da3 = format(attribute[2], ">10.3f")
            da4 = format(attribute[3], ">10.3f")
            keyword += n1 + n2 + n3 + n4 + da1 + da2 + da3 + da4 + "\n"
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        if len(self.segments) == 0:
            return
        stream.write("*SET_SEGMENT_TITLE\n")
        stream.write(format(self.name, ">80") + "\n")
        stream.write(format(self.sid + startID, ">10"))
        stream.write(format(self.da1, ">10.3f"))
        stream.write(format(self.da2, ">10.3f"))
        stream.write(format(self.da3, ">10.3f"))
        stream.write(format(self.da4, ">10.3f"))
        stream.write(format(self.solver, ">10"))
        stream.write(format(self.its, ">10"))
        stream.write("\n")
        for i in range(len(self.segments)):
            segment = self.segments[i]
            attribute = self.attributes[i]
            n1 = format(segment[0], ">10")
            n2 = format(segment[1], ">10")
            n3 = format(segment[2], ">10")
            n4 = format(segment[3], ">10")
            da1 = format(attribute[0], ">10.3f")
            da2 = format(attribute[1], ">10.3f")
            da3 = format(attribute[2], ">10.3f")
            da4 = format(attribute[3], ">10.3f")
            stream.write(n1 + n2 + n3 + n4 + da1 + da2 + da3 + da4 + "\n")
              
class KooSegmentSetManager:
    def __init__(self):
        self.maxid = 0 
        self.segmentSetList = {}
        
    def FindPidfromSegments(self, partManager):
        for part in partManager.parts.values():
            part.elementManager.SetBoundaryNodes()
        
        for key, segmentSet in self.segmentSetList.items():
            nid = 0
            for part in partManager.parts.values():
                elemMan = part.elementManager
                for segments in segmentSet.segments:                
                    for snid in segments:
                        if snid in elemMan.boundaryNodes:
                            nid = snid
                    if nid != 0:
                        segmentSet.pid = part.id
                        break
                if nid != 0:
                    break
            
                            

    def OffsetID(self, offset, offsetNID):
        for key in self.segmentSetList:
            segmentSet = self.segmentSetList[key]
            segmentSet.sid += offset
            segmentSet.OffsetNID(offsetNID)

    def OverwritefromSegmentSetManager(self, segmentSetManager : KooSegmentSetManager):
        self.maxid = max(self.maxid, segmentSetManager.maxid)
        for key, value in segmentSetManager.segmentSetList.items():
            self.segmentSetList[key] = value

    def CreateSegmentSet(self, da1=0.0, da2=0.0, da3=0.0, da4=0.0, solver = "MECH", its = 0, name = ""):
        self.maxid += 1
        segmentSet = KooSegmentSet(self.maxid, da1, da2, da3, da4, solver, its, name)
        return self.AddSegmentSet(segmentSet)
    
    def CreateSegmentSetwithID(self, sid, da1=0.0, da2=0.0, da3=0.0, da4=0.0, solver = "MECH", its = 0, name = ""):
        segmentSet = KooSegmentSet(sid, da1, da2, da3, da4, solver, its, name)
        return self.AddSegmentSet(segmentSet)
        
    def AddSegmentSet(self, segmentSet):
        if segmentSet.sid > self.maxid:
            self.maxid = segmentSet.sid
        self.segmentSetList[segmentSet.sid] = segmentSet
        return segmentSet
    
    def AddSegmentSetfromDyna(self, segmentSetKeyword):
        if segmentSetKeyword[0] == "*SET_SEGMENT":
            keyword = segmentSetKeyword[1]
            if len(keyword[0].strip()) == 0:
                keyword[0] = "0"
            if len(keyword[1].strip()) == 0:
                keyword[1] = "0.0"
            if len(keyword[2].strip()) == 0:
                keyword[2] = "0.0"
            if len(keyword[3].strip()) == 0:
                keyword[3] = "0.0"
            if len(keyword[4].strip()) == 0:
                keyword[4] = "0.0"
            if len(keyword[5].strip()) == 0:
                keyword[5] = "MECH"
            if len(keyword[6].strip()) == 0:
                keyword[6] = "0"
            
            sid = int(keyword[0])
            da1 = float(keyword[1])
            da2 = float(keyword[2])
            da3 = float(keyword[3])
            da4 = float(keyword[4])
            solver = keyword[5]
            its = int(keyword[6])
            if sid == 0:
                segmentSet = self.CreateSegmentSet(da1, da2, da3, da4, solver, its)
            else:
                segmentSet = self.CreateSegmentSetwithID(sid, da1, da2, da3, da4, solver, its)
            for i in range(2,len(segmentSetKeyword)):
                keyword = segmentSetKeyword[i]
                if len(keyword[0].strip()) == 0:
                    keyword[0] = "0"
                if len(keyword[1].strip()) == 0:
                    keyword[1] = "0"
                if len(keyword[2].strip()) == 0:
                    keyword[2] = "0"
                if len(keyword[3].strip()) == 0:
                    keyword[3] = "0"
                if len(keyword[4].strip()) == 0:
                    keyword[4] = "0.0"
                if len(keyword[5].strip()) == 0:
                    keyword[5] = "0.0"
                if len(keyword[6].strip()) == 0:
                    keyword[6] = "0.0"
                if len(keyword[7].strip()) == 0:
                    keyword[7] = "0.0"
                n1 = int(keyword[0])
                n2 = int(keyword[1])
                n3 = int(keyword[2])
                n4 = int(keyword[3])
                da1 = float(keyword[4])
                da2 = float(keyword[5])
                da3 = float(keyword[6])
                da4 = float(keyword[7])
                if n3 == 0:
                    segmentSet.AddLineSegmentwithAttributes(n1, n2, da1, da2, da3, da4)
                elif n4 == 0:
                    segmentSet.AddTriangleSegmentwithAttributes(n1, n2, n3, da1, da2, da3, da4)
                else:
                    segmentSet.AddQuadrangleSegmentwithAttributes(n1, n2, n3, n4, da1, da2, da3, da4)

        if segmentSetKeyword[0] == "*SET_SEGMENT_TITLE":
            name = segmentSetKeyword[1]
            if type(name) == list:
                name = name[0]

            keyword = segmentSetKeyword[2]
            if len(keyword[0].strip()) == 0:
                keyword[0] = "0"
            if len(keyword[1].strip()) == 0:
                keyword[1] = "0.0"
            if len(keyword[2].strip()) == 0:
                keyword[2] = "0.0"
            if len(keyword[3].strip()) == 0:
                keyword[3] = "0.0"
            if len(keyword[4].strip()) == 0:
                keyword[4] = "0.0"
            if len(keyword[5].strip()) == 0:
                keyword[5] = "MECH"
            if len(keyword[6].strip()) == 0:
                keyword[6] = "0"
            
            sid = int(keyword[0])
            da1 = float(keyword[1])
            da2 = float(keyword[2])
            da3 = float(keyword[3])
            da4 = float(keyword[4])
            solver = keyword[5]
            its = int(keyword[6])
            if sid == 0:
                segmentSet = self.CreateSegmentSet(da1, da2, da3, da4, solver, its, name)
            else:
                segmentSet = self.CreateSegmentSetwithID(sid, da1, da2, da3, da4, solver, its, name)
            for i in range(3,len(segmentSetKeyword)):
                keyword = segmentSetKeyword[i]
                if len(keyword[0].strip()) == 0:
                    keyword[0] = "0"
                if len(keyword[1].strip()) == 0:
                    keyword[1] = "0"
                if len(keyword[2].strip()) == 0:
                    keyword[2] = "0"
                if len(keyword[3].strip()) == 0:
                    keyword[3] = "0"
                if len(keyword[4].strip()) == 0:
                    keyword[4] = "0.0"
                if len(keyword[5].strip()) == 0:
                    keyword[5] = "0.0"
                if len(keyword[6].strip()) == 0:
                    keyword[6] = "0.0"
                if len(keyword[7].strip()) == 0:
                    keyword[7] = "0.0"
                n1 = int(keyword[0])
                n2 = int(keyword[1])
                n3 = int(keyword[2])
                n4 = int(keyword[3])
                da1 = float(keyword[4])
                da2 = float(keyword[5])
                da3 = float(keyword[6])
                da4 = float(keyword[7])
                if n3 == 0:
                    segmentSet.AddLineSegmentwithAttributes(n1, n2, da1, da2, da3, da4)
                elif n4 == 0:
                    segmentSet.AddTriangleSegmentwithAttributes(n1, n2, n3, da1, da2, da3, da4)
                else:
                    segmentSet.AddQuadrangleSegmentwithAttributes(n1, n2, n3, n4, da1, da2, da3, da4)
            
        
    def WritetoDynaKeyword(self, startID):
        keyword = ""
        for sid in self.segmentSetList:
            keyword += self.segmentSetList[sid].WritetoDynaKeyword(startID)
        return keyword
    
    def WriteStreamDynaKeyword(self, stream, startID):
        for sid in self.segmentSetList:
           self.segmentSetList[sid].WriteStreamDynaKeyword(stream,startID)