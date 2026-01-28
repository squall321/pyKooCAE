import os 
from KooODBCADManager.WarpageSurface import WarpageSurface
from scipy.interpolate import LinearNDInterpolator
from scipy.ndimage import gaussian_filter

import numpy as np
class KooWarpage(WarpageSurface):
    def __init__(self, xLoc, yLoc, xLength, yLength, warpageFile = "Warpage.dat"):
        
        super(KooWarpage, self).__init__()
        
        self.xLoc = xLoc
        self.yLoc = yLoc
        self.xLength = xLength
        self.yLength = yLength
        self.WarpageFile = warpageFile
        self.WarpageUnit = "mm"
        self.WarpageUnitAmp = 1.0
        self.WarpageMatrix = []
        self.Interpolator = None
        self.CurvatureX = None
        self.CurvatureY = None
        self.CurvatureXY = None
    
    def SetWarpageUnit(self, unit):
        self.WarpageUnitAmp = 1.0
        self.WarpageUnit = unit
        if unit.lower() == "microm":
            self.WarpageUnitAmp = 1e-3
        elif unit.lower() == "mm":
            self.WarpageUnitAmp = 1.0
        elif unit.lower() == "cm":
            self.WarpageUnitAmp = 1e1
        elif unit.lower() == "m":
            self.WarpageUnitAmp = 1e3
        elif unit.lower() == "inch":
            self.WarpageUnitAmp = 25.4

    def GenerateZInterpolator(self):
        path = os.getcwd()
        if len(self.WarpageMatrix) == 0:
            self.ImportWarpage(path, self.WarpageUnitAmp)
            self.RemoveEmptySpace()
        xSize = len(self.WarpageMatrix)
        ySize = len(self.WarpageMatrix[0])

        xList = [0.0] * (xSize*ySize)
        yList = [0.0] * (xSize*ySize)
        zList = [0.0] * (xSize*ySize)
        
        for j in range(ySize):
            for i in range(xSize):
                x = self.xLoc + (i)/(xSize-1) * self.xLength
                y = self.yLoc + (ySize - j - 1) / (ySize-1) * self.yLength
                z = self.WarpageMatrix[i][j]
                xList[i + j*xSize] = x
                yList[i + j*xSize] = y
                zList[i + j*xSize] = z
        # 보간기 생성 (한 번만)
        points = np.column_stack((xList, yList))
        self.Interpolator = LinearNDInterpolator(points, zList)

    def GenerateCurvatureInterpolator(self, amplitude = 1.0):
       # 기존 데이터
        if len(self.WarpageMatrix) == 0:
            path = os.getcwd()
            self.ImportWarpage(path, self.WarpageUnitAmp)
            self.RemoveEmptySpace()
        xSize = len(self.WarpageMatrix)
        ySize = len(self.WarpageMatrix[0])

        dx = self.xLength / (xSize - 1)
        dy = self.yLength / (ySize - 1)

        W = np.array(self.WarpageMatrix).T  # shape (y, x)로 바꿈
        W = W * amplitude
        # 2차 미분 계산
        d2w_dx2 = np.gradient(np.gradient(W, dx, axis=1), dx, axis=1)
        d2w_dy2 = np.gradient(np.gradient(W, dy, axis=0), dy, axis=0)
        #d2w_dxdy = np.gradient(np.gradient(W, dy, axis=0), dx, axis=1)
        d2w_dxdy1 = np.gradient(np.gradient(W, dy, axis=0), dx, axis=1)
        d2w_dxdy2 = np.gradient(np.gradient(W, dx, axis=1), dy, axis=0)
        d2w_dxdy = 0.5 * (d2w_dxdy1 + d2w_dxdy2)
        d2w_dxdy = gaussian_filter(d2w_dxdy, sigma=2)

        # 보간기용 리스트로 변환
        points = []
        d2x_list = []
        d2y_list = []
        d2xy_list = []

        for j in range(ySize):
            for i in range(xSize):
                x = self.xLoc + (i) / (xSize - 1) * self.xLength
                y = self.yLoc + (ySize - j - 1) / (ySize - 1) * self.yLength
                points.append((x, y))
                d2x_list.append(d2w_dx2[j, i])
                d2y_list.append(d2w_dy2[j, i])
                d2xy_list.append(d2w_dxdy[j, i])

        # 보간기 생성
        self.CurvatureX = LinearNDInterpolator(points, d2x_list)
        self.CurvatureY = LinearNDInterpolator(points, d2y_list)
        self.CurvatureXY = LinearNDInterpolator(points, d2xy_list)
    
    def GetZ(self, x, y):
        if self.Interpolator is None:
            raise ValueError("Interpolator not initialized. Call GenerateZInterpolator first.")
        x_query = np.array([x])
        y_query = np.array([y])
        query_points = np.column_stack((x_query, y_query))
        z = self.Interpolator(query_points)
        return z        
    
    def GetZList(self, xList, yList):
        if self.Interpolator is None:
            raise ValueError("Interpolator not initialized. Call GenerateZInterpolator first.")
        x_query = np.array(xList)
        y_query = np.array(yList)
        query_points = np.column_stack((x_query, y_query))
        z = self.Interpolator(query_points)
        return z
    
    def GetCurvature(self, x, y):
        if self.CurvatureX is None or self.CurvatureY is None or self.CurvatureXY is None:
            raise ValueError("Curvature interpolators not initialized. Call GenerateCurvatureInterpolator first.")
        
        x_query = np.array([x])
        y_query = np.array([y])
        query_points = np.column_stack((x_query, y_query))
        
        curvature_x = self.CurvatureX(query_points)
        curvature_y = self.CurvatureY(query_points)
        curvature_xy = self.CurvatureXY(query_points)
        
        return curvature_x, curvature_y, curvature_xy
    
    def GetCurvatureList(self, xList, yList):
        if self.CurvatureX is None or self.CurvatureY is None or self.CurvatureXY is None:
            raise ValueError("Curvature interpolators not initialized. Call GenerateCurvatureInterpolator first.")
        
        x_query = np.array(xList)
        y_query = np.array(yList)
        query_points = np.column_stack((x_query, y_query))
        
        curvature_x = self.CurvatureX(query_points)
        curvature_y = self.CurvatureY(query_points)
        curvature_xy = self.CurvatureXY(query_points)
        
        return curvature_x, curvature_y, curvature_xy
    
                