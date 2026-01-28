import os
import vtk
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from vtkmodules.vtkFiltersGeometry import vtkCompositeDataGeometryFilter
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)
import numpy as np
from scipy.spatial import KDTree


class KooD3Plot:
    def __init__(self, filePath):
        self.reader = vtk.vtkLSDynaReader()
        self.filePath = filePath
        self.timeData = []
        self.points = {}
        self.dispData = {}
        self.tree = None
        

    def SetReader(self):
        fileName = self.filePath
        if "d3plot" in fileName:
            pass
        else:
            fileName = os.path.join(fileName, "d3plot")
        
        self.reader.SetFileName(fileName)
        
    def GetTimeData(self):
        return self.timeData
    
    def GetPointsinBoundaryBox(self , minX, maxX, minY, maxY, minZ, maxZ):
        pointsInBox = {}
        for i in range(len(self.points)):
            if self.points[i][0] >= minX and self.points[i][0] <= maxX and self.points[i][1] >= minY and self.points[i][1] <= maxY and self.points[i][2] >= minZ and self.points[i][2] <= maxZ:
                pointsInBox[i] = self.points[i]
        return pointsInBox
    
    def SetDatainBoundaryBox(self, minX, maxX, minY, maxY, minZ, maxZ):
        num_time_step = self.reader.GetNumberOfTimeSteps()
        
        for time_step in range(num_time_step):
            
            self.reader.SetTimeStep(time_step)
            self.reader.Update()
            output = self.reader.GetOutput()
            geometry_filter = vtkCompositeDataGeometryFilter()
            geometry_filter.SetInputData(output)
            geometry_filter.Update()
            
            point_data = geometry_filter.GetOutput().GetPointData()
            points = geometry_filter.GetOutput().GetPoints()
            if time_step == 0:
                for i in range(points.GetNumberOfPoints()):
                    if points.GetPoint(i)[0] >= minX and points.GetPoint(i)[0] <= maxX and points.GetPoint(i)[1] >= minY and points.GetPoint(i)[1] <= maxY and points.GetPoint(i)[2] >= minZ and points.GetPoint(i)[2] <= maxZ:
                        self.points[i] = points.GetPoint(i)
                    
            displacement = point_data.GetArray("Deflection")
            if displacement is None:
                print(f"No displacement data found for timestep {time_step}")
                continue
            curTime = self.reader.GetTimeValue(time_step)
            self.timeData.append(curTime)
            self.dispData[time_step] = {}
            for i in range(points.GetNumberOfPoints()):
                if i in self.points:
                    self.dispData[time_step][i] = displacement.GetTuple(i)
        
        point_coords = np.array(list(self.points.values()))
        self.tree = KDTree(point_coords)
        
            
    
    def SetData(self):
        num_time_step = self.reader.GetNumberOfTimeSteps()
        
        for time_step in range(num_time_step):
            
            self.reader.SetTimeStep(time_step)
            self.reader.Update()
            output = self.reader.GetOutput()
            geometry_filter = vtkCompositeDataGeometryFilter()
            geometry_filter.SetInputData(output)
            geometry_filter.Update()
            
            point_data = geometry_filter.GetOutput().GetPointData()
            points = geometry_filter.GetOutput().GetPoints()
            if time_step == 0:
                for i in range(points.GetNumberOfPoints()):
                    self.points[i] = points.GetPoint(i)
                    
            displacement = point_data.GetArray("Deflection")
            if displacement is None:
                print(f"No displacement data found for timestep {time_step}")
                continue
            curTime = self.reader.GetTimeValue(time_step)
            self.timeData.append(curTime)
            self.dispData[time_step] = {}
            for i in range(points.GetNumberOfPoints()):
                self.dispData[time_step][i] = displacement.GetTuple(i)
            
        point_coords = np.array(list(self.points.values()))
        self.tree = KDTree(point_coords)
    
    def interpolate_displacement(self, new_points, k=3):
        interpolated_disp = {} 
        for timestep, displacements in self.dispData.items():
            timestep_disp = {} 
            disp_coords = np.array(list(displacements.keys()))
            disp_values = np.array(list(displacements.values()))
            
            for new_point_id in new_points:
                cur_point = new_points[new_point_id]
                distances, indices = self.tree.query(cur_point, k=k)
                nearest_disp = disp_values[indices]
                weights = 1 / distances
                interpolated_value = np.dot(weights, nearest_disp)
                interpolated_value /= weights.sum()
                timestep_disp[new_point_id] = tuple(interpolated_value)
            
            interpolated_disp[timestep] = timestep_disp
    
        return interpolated_disp    
        
    def GetBoundBox(self):
        self.reader.SetTimeStep(0)
        self.reader.Update()
        output = self.reader.GetOutput()
        geometry_filter = vtkCompositeDataGeometryFilter()
        geometry_filter.SetInputData(output)
        geometry_filter.Update()
        
        point_data = geometry_filter.GetOutput().GetPointData()
        points = geometry_filter.GetOutput().GetPoints()
        
        minX = 1.e99
        maxX = -1.e99
        minY = 1.e99
        maxY = -1.e99
        minZ = 1.e99    
        maxZ = -1.e99
            
        for i in range(points.GetNumberOfPoints()):
            original_position = points.GetPoint(i)
            minX = min(minX, original_position[0])
            maxX = max(maxX, original_position[0])
            minY = min(minY, original_position[1])
            maxY = max(maxY, original_position[1])
            minZ = min(minZ, original_position[2])
            maxZ = max(maxZ, original_position[2])
        
        return minX, maxX, minY, maxY, minZ, maxZ

class KooExternalDynaResultManager:
    def __init__(self):
        self.d3plot = None
    
    def Clear(self):
        self.d3plot = None
        
    def GetTimeData(self):
        return self.d3plot.GetTimeData()
     
    def SetD3Plot(self, d3plotPath):
        self.d3plot = KooD3Plot(d3plotPath)
        self.d3plot.SetReader()
        self.d3plot.SetData()
        
    def InterpolateDisplacement(self, newPoints, k=3):
        return self.d3plot.interpolate_displacement(newPoints, k)
        
    def SetD3PlotinBoundaryBox(self, d3plotPath, minX, maxX, minY, maxY, minZ, maxZ):
        self.d3plot = KooD3Plot(d3plotPath)
        self.d3plot.SetReader()
        self.d3plot.SetDatainBoundaryBox(minX,maxX,minY,maxY,minZ,maxZ)

if __name__ == '__main__':
    filePath = ".\\occProject\\Generators\\dist\\DisplayImpactImplicit\\3ptBending_1_00000001\\d3plot"
    d3plot = KooD3Plot(filePath)
    d3plot.SetReader()
    boundBox = d3plot.GetBoundBox()
    #d3plot.SetData()
    minX = -0.01
    maxX = 0.01
    minY = -0.004
    maxY = 0.004
    minZ = -0.001
    maxZ = 0.001
    #d3plot.SetData()
    d3plot.SetDatainBoundaryBox(minX,maxX,minY,maxY,minZ,maxZ)
    print("Boundary Box: ", boundBox)
    
    

