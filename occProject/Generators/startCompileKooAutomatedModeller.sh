rm -rf KooAutomatedModeller.dist KooAutomatedModeller.build .nuitka
python -m nuitka ./KooAutomatedModeller.py \
        --standalone \
        --enable-plugin=pyqt5 \
        --jobs=8 \
        --include-package=OCC \
        --include-package=vtk --include-package=vtkmodules \
        --include-package=trimesh \
        --include-package-data=trimesh \
        --follow-imports \
        --show-progress   
