import os
import numpy as np 
import trimesh

class KooSTLGeometry:
    def __init__(self, id, name, stl_path = ""):
        self.id = id
        self.name = name 
        self.vertices = None
        self.faces = None
        
        if stl_path == "":
            self.stl_path = name + ".stl"            
        else:
            self.stl_path = stl_path
            
    
    def ImportSTL(self, stl_path = ""):
        if stl_path == "":
            stl_path = self.stl_path
        else:
            self.stl_path = stl_path
            
        if not os.path.exists(stl_path):
            return False
        
        mesh = trimesh.load_mesh(stl_path)
        self.vertices = mesh.vertices
        self.faces = mesh.faces
        
        return True
    
    def ExportSTL(self, stl_path = "", sub_str = ""):
        if ".stl" in stl_path:
            stl_path = stl_path.replace(".stl", sub_str + ".stl")
            
        if stl_path == "":
            stl_path = self.stl_path
        else:
            self.stl_path = stl_path
        
        if self.vertices is None or self.faces is None:
            return False
        
        mesh = trimesh.Trimesh(vertices=self.vertices, faces=self.faces)
        
        mesh.export(stl_path)
                
        return True
    
    

class KooSTLGeometryManager:
    def __init__(self):
        self.max_id = 0
        self.stl_geometries = {}
        
    def AddSTLGeometry(self, name, stl_path = ""):
        self.max_id += 1
        stl_geometry = KooSTLGeometry(self.max_id, name, stl_path)
        self.stl_geometries[self.max_id] = stl_geometry
        
        # check stl_path exist
        curDir = os.path.dirname(stl_path)
        if not os.path.exists(curDir):
            pass
        else:
            if not os.path.exists(stl_path):
                return False
            else:
                pass
            
                
        return stl_geometry
    
    
    
    
if __name__ == "__main__":
    stl_manager = KooSTLGeometryManager()
    stl_geometry = stl_manager.AddSTLGeometry("ellipsoid_raw", "ellipsoid_raw.stl")
    
    # Import STL
    stl_geometry.ImportSTL()
    
    # Export STL
    stl_geometry.ExportSTL("ellipsoid_raw.stl", "_out")
    
        