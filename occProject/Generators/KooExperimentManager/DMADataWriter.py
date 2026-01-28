import os
import sys
import json

## cur file directory
curDir = os.path.dirname(os.path.realpath(__file__))

fileName = "DMAData.txt"
filePath = os.path.join(curDir, fileName)

density = 7800
nu = 0.3 
fmin = 1
fmax = 1000
ftarget = 100

frequency = [1.0e-3, 1.0e-2, 1.0e-1, 1.0e0, 1.0e1, 1.0e2, 1.0e3]
storage_modulus =[1.0e6, 1.0e5, 1.0e4, 1.0e3, 1.0e2, 1.0e1, 1.0e0]
temperature = [25, 25, 25, 25, 25, 25, 25]   
loss_modulus =[1.0e4 , 1.0e3 , 1.0e2 , 1.0e1 , 1.0e0 , 1.0e-1 , 1.0e-2]

variables  = {}

variables['Density'] = density
variables['Nu'] = nu    
variables['Fmin'] = fmin
variables['Fmax'] = fmax
variables['Ftarget'] = ftarget
variables['Mode'] = 'SimpleViscoelastic'

data = {}
for i in range(len(frequency)):
    ithData = {}
    ithData["Freq"] = frequency[i]
    ithData["Temp"] = temperature[i]
    ithData["Storage"] = storage_modulus[i]
    ithData["Loss"] = loss_modulus[i]
    data[i] = ithData
   
inputs = {} 
inputs["Data"] = data
inputs["Variables"] = variables

json_data = json.dumps(inputs, indent=4)


with open(filePath, "w") as f:
    json.dump(inputs, f, indent=4)