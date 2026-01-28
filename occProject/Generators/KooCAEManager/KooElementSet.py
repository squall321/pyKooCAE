from KooCAEManager.KooNode import *
from KooCAEManager.KooElement import *

class ElementSet:
    # Type : Line, Face, Solid
    def __init__(self,id=0,type="Solid"):
        self.id = id
        self.setType = type
        self.elements = {}
        self.boundaries = {}

    def AddElement(self,element):
        self.elements[element.id] = element
    
    def AddElements(self,elements):
        for element in elements:
            self.AddElement(element)

class LineElementSet(ElementSet):

    def __init__(self,id=0):
        self.setType = "Line"
        super(LineElementSet,self).__init__(id,self.setType)  
        
  
class FaceElementSet(ElementSet):

    def __init__(self, id=0):
        self.setType = "Face"
        super(FaceElementSet,self).__init__(id,self.setType)

class SolidElementSet(ElementSet):

    def __init__(self, id=0):
        self.setType = "Solid"
        super(SolidElementSet,self).__init__(id, self.setType)

        


