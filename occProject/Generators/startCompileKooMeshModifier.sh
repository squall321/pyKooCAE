rm -rf KooMeshModifier.dist KooMeshModifier.build .nuitka
python3 -m nuitka ./KooMeshModifier.py \
        --standalone \
        --enable-plugin=pyqt5 \
        --jobs=8 \
        --include-package=OCC \
        --include-package=vtk --include-package=vtkmodules \
        --include-package=trimesh \
        --include-package-data=trimesh \
        --follow-imports \
        --show-progress   
