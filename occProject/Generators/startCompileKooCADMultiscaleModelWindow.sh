rm -rf KooCADMultiscaleModelWindow.dist KooCADMultiscaleModelWindow.build .nuitka
python -m nuitka ./KooCADMultiscaleModelWindow.py \
        --standalone \
        --enable-plugin=pyqt5 \
        --include-package=OCC \
        --include-package=vtk --include-package=vtkmodules \
        --include-package=trimesh \
        --include-package-data=trimesh \
        --follow-imports \
        --show-progress   
