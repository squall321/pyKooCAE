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
import numpy as np 

class ImageLayer:
    def __init__(self):
        self.ImageMatrix = [] 
        pass

    def SetZerosImageMatrix(self, xSize, ySize):
        self.ImageMatrix = np.zeros((xSize, ySize))

    def Import(self, fileName):
        pass

if __name__ == '__main__':

    
    # import jpg file as image 
    from PIL import Image
    import numpy as np
    import matplotlib.image as mpimg
    img = mpimg.imread('C:\\Users\\koo\\Desktop\\test.jpg')

    

