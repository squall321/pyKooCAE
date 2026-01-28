import sys
import os

getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")
if sys.platform.startswith("win"):
    # Windows 전용
    os.add_dll_directory(path)
else:
    # Linux/Unix 계열은 LD_LIBRARY_PATH에 넣으면 됨
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if path not in ld_path.split(":"):
        os.environ["LD_LIBRARY_PATH"] = path + ":" + ld_path


from os.path import join
from PyQt5 import QtGui 
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QDockWidget, QWidget, QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog
from PyQt5.QtGui import QKeySequence, QBrush, QColor
from PyQt5.QtWidgets import QButtonGroup, QRadioButton, QGroupBox
from PyQt5.QtGui import QDoubleValidator

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ
from OCC.Core.AIS import AIS_Manipulator

from KooCAEManager.KooCAEModel import (
    KooCAEModel,
    QKooGeometryItem, 
    QKooManipulatorItem
)
from KooCAEManager.KooAISGeometry import (
    KooAISManipulator
)

class KooPropertyWidget(QWidget):
    def __init__(self, mainWindowFunc, parent = None, name = "Property"):
        super(KooPropertyWidget,self).__init__(parent)
        self.isOpened = True 
        self.setMinimumWidth(100)
        self.setMinimumHeight(200)
        self.mainWindowFunc = mainWindowFunc
        #self.setStyleSheet('border: 2px solid black;')

        layout = QVBoxLayout()
        self.labelTitle = QLabel(name,self)
        self.labelTitle.setAlignment(Qt.AlignCenter)
        self.labelTitle.setFont(QtGui.QFont("Arial", 8, QtGui.QFont.Bold))
        layout.addWidget(self.labelTitle)
        self.setLayout(layout)


    def on_button_click(self):
        self.mainWindowFunc()

    def show(self) -> None:
        self.isOpened = True
        return super().show()

    def close(self) -> bool:
        self.isOpened = False
        return super().close()
    
class KooFaceGeometryWidget(KooPropertyWidget):
    def __init__(self, mainWindowFunc, parent = None, name = "Property"):
        super(KooFaceGeometryWidget,self).__init__(mainWindowFunc, parent, name)
        self.faceItem = None 
        layout = self.layout()
        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Property","Value"])
        size = 3
        self.table.setRowCount(size)
        self.table.verticalHeader().hide()

        self.table.setItem(0,0,QTableWidgetItem("Mesh Size"))
        self.table.setItem(1,0,QTableWidgetItem("Generate Mesh"))
        for i in range(0,2):
            item = self.table.item(i,0)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        
        self.meshSize = 1.0
        self.meshSizeEdit = QLineEdit("1.0")
        self.buttonGenerateMesh = QPushButton("Generate")
        self.buttonGenerateMesh.clicked.connect(self.on_button_click_generate_mesh)

        self.meshSizeEdit.textChanged.connect(self.on_item_changed)

        self.table.setCellWidget(0,1,self.meshSizeEdit)
        self.table.setCellWidget(1,1,self.buttonGenerateMesh)

        layout.addWidget(self.table)


    def on_button_click_generate_mesh(self):
        if self.faceItem is not None:
            if self.faceItem.meshItem is not None:
                self.faceItem.SetMeshSize(float(self.meshSizeEdit.text()))
                self.faceItem.GenerateMesh()
        pass

    def on_item_changed(self):
        try:
            changed = False 
            if self.meshSize != float(self.meshSizeEdit.text()):
                changed = True 
        except:
            return
        if changed:
            self.meshSize = float(self.meshSizeEdit.text())
            self.faceItem.SetMeshSize(self.meshSize)
            self.on_button_changed()

    def on_button_changed(self):
        self.mainWindowFunc()

    def SetFaceItem(self, faceItem : QKooGeometryItem):
        self.faceItem = faceItem


class KooSolidGeometryWidget(KooPropertyWidget):
    def __init__(self, mainWindowFunc, parent = None, name = "Property"):
        super(KooSolidGeometryWidget,self).__init__(mainWindowFunc, parent, name)
        self.solidItem = None

        layout = self.layout()
        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Property","Value"])
        size = 3
        self.table.setRowCount(size)
        self.table.verticalHeader().hide()

        self.table.setItem(0,0,QTableWidgetItem("Mesh Size"))
        self.table.setItem(1,0,QTableWidgetItem("Generate Mesh"))        
        for i in range(0,2):
            item = self.table.item(i,0)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)

        self.meshSize = 1.0 

        self.meshSizeEdit = QLineEdit("1.0")
        self.buttonGenerateMesh = QPushButton("Generate")

        self.buttonGenerateMesh.clicked.connect(self.on_button_click_generate_mesh)

        self.meshSizeEdit.textChanged.connect(self.on_item_changed)

        self.table.setCellWidget(0,1,self.meshSizeEdit)
        self.table.setCellWidget(1,1,self.buttonGenerateMesh)

        layout.addWidget(self.table)

    def on_button_click_generate_mesh(self):
        if self.solidItem is not None:
            if self.solidItem.meshItem is not None:
                self.solidItem.SetMeshSize(float(self.meshSizeEdit.text()))
                self.solidItem.GenerateMesh()
        pass

    def on_item_changed(self):
        try:
            changed = False 
            if self.meshSize != float(self.meshSizeEdit.text()):
                changed = True 
        except:
            return
        if changed:
            self.meshSize = float(self.meshSizeEdit.text())
            self.solidItem.SetMeshSize(self.meshSize)
            self.on_button_changed()

    def on_button_changed(self):
        self.mainWindowFunc()

    def SetSolidItem(self, solidItem : QKooGeometryItem):
        self.solidItem = solidItem        
        

class KooManipulatorWidget(KooPropertyWidget):
    def __init__(self, mainWindowFunc, parent = None, name = "Property"):
        super(KooManipulatorWidget,self).__init__(mainWindowFunc, parent, name)
        self.data = None
        self.manipulator = None
        self.manipulatorItem = None
        layout = self.layout()


        self.manipulatorLocationX = 0.0 
        self.manipulatorLocationY = 0.0
        self.manipulatorLocationZ = 0.0
        self.manipulatorRotationX = 0.0 
        self.manipulatorRotationY = 0.0 
        self.manipulatorRotationZ = 0.0 
        # Table 

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Property","Value"])
        size = 10
        self.table.setRowCount(size)
        self.table.verticalHeader().hide()
        self.table.setItem(0,0,QTableWidgetItem("Location X"))
        self.table.setItem(1,0,QTableWidgetItem("Location Y"))
        self.table.setItem(2,0,QTableWidgetItem("Location Z"))
        self.table.setItem(3,0,QTableWidgetItem("Axis X"))
        self.table.setItem(4,0,QTableWidgetItem("X Coordinate"))        
        self.table.setItem(5,0,QTableWidgetItem("Axis Y"))
        self.table.setItem(6,0,QTableWidgetItem("Y Coordinate"))
        self.table.setItem(7,0,QTableWidgetItem("Rotate X"))
        self.table.setItem(8,0,QTableWidgetItem("Rotate Y"))
        self.table.setItem(9,0,QTableWidgetItem("Rotate Z"))


        for i in range(0,7):
            item = self.table.item(i,0)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # Disable the cell
        
        self.locationXEdit = QLineEdit("0")
        self.locationYEdit = QLineEdit("0")
        self.locationZEdit = QLineEdit("0")
        self.buttonAxisX = QPushButton("Select")
        self.buttonAxisY = QPushButton("Select")
        self.locationXEdit.setValidator(QDoubleValidator())
        self.locationYEdit.setValidator(QDoubleValidator())
        self.locationZEdit.setValidator(QDoubleValidator())

        self.buttonAxisX.clicked.connect(self.on_button_click_axis_x)
        self.buttonAxisY.clicked.connect(self.on_button_click_axis_y)
        
        self.table.setCellWidget(0, 1,self.locationXEdit)  # Replace row and column indices with your desired cell position
        self.table.setCellWidget(1, 1,self.locationYEdit)  # Replace row and column indices with your desired cell position
        self.table.setCellWidget(2, 1,self.locationZEdit)  # Replace row and column indices with your desired cell position
        self.table.setCellWidget(3, 1,self.buttonAxisX)  # Replace row and column indices with your desired cell position

        hlayoutAxisX = QHBoxLayout()
        self.editAxisX_X = QLineEdit("0")
        self.editAxisX_Y = QLineEdit("0")
        self.editAxisX_Z = QLineEdit("0")
        self.editAxisX_X.setValidator(QDoubleValidator())
        self.editAxisX_Y.setValidator(QDoubleValidator())
        self.editAxisX_Z.setValidator(QDoubleValidator())
        self.editAxisX_X.setMinimumHeight(20)
        self.editAxisX_Y.setMinimumHeight(20)
        self.editAxisX_Z.setMinimumHeight(20)
        hlayoutAxisX.addWidget(self.editAxisX_X)
        hlayoutAxisX.addWidget(self.editAxisX_Y)
        hlayoutAxisX.addWidget(self.editAxisX_Z)
        widgetx = QWidget()
        widgetx.setLayout(hlayoutAxisX)
        
        self.table.setCellWidget(4, 1,widgetx)  # Replace row and column indices with your desired cell position

        self.table.setCellWidget(5, 1,self.buttonAxisY)  # Replace row and column indices with your desired cell position

        hlayoutAxisY = QHBoxLayout()
        self.editAxisY_X = QLineEdit("0")
        self.editAxisY_Y = QLineEdit("0")
        self.editAxisY_Z = QLineEdit("0")
        self.editAxisY_X.setValidator(QDoubleValidator())
        self.editAxisY_Y.setValidator(QDoubleValidator())
        self.editAxisY_Z.setValidator(QDoubleValidator())
        self.editAxisY_X.setMinimumHeight(20)
        self.editAxisY_Y.setMinimumHeight(20)
        self.editAxisY_Z.setMinimumHeight(20)
        hlayoutAxisY.addWidget(self.editAxisY_X)
        hlayoutAxisY.addWidget(self.editAxisY_Y)
        hlayoutAxisY.addWidget(self.editAxisY_Z)
        widgety = QWidget()
        widgety.setLayout(hlayoutAxisY)
        self.table.setCellWidget(6, 1,widgety)  # Replace row and column indices with your desired cell position
   
   
        self.editRotateX = QLineEdit("0")
        self.editRotateY = QLineEdit("0")
        self.editRotateZ = QLineEdit("0")
        self.editRotateX.setValidator(QDoubleValidator())
        self.editRotateY.setValidator(QDoubleValidator())
        self.editRotateZ.setValidator(QDoubleValidator())
        
        self.table.setCellWidget(7, 1,self.editRotateX)  # Replace row and column indices with your desired cell position
        self.table.setCellWidget(8, 1,self.editRotateY)  # Replace row and column indices with your desired cell position
        self.table.setCellWidget(9, 1,self.editRotateZ)  # Replace row and column indices with your desired cell position

        #self.table.setItem(0,1,QTableWidgetItem("0"))
        #self.table.setItem(1,1,QTableWidgetItem("0"))
        #self.table.setItem(2,1,QTableWidgetItem("0"))
       
        #double_validator = QDoubleValidator()
        #double_validator.setNotation(QDoubleValidator.StandardNotation)
        #double_validator.setDecimals(2)
        #item = self.table.item(0,1)
        #self.table.setitemdel
        #self.table.setItemDelegateForColumn(0, QStyledItemDelegate(table))
        #self.table.itemDelegateForColumn().setValidator(double_validator)
        layout.addWidget(self.table)
  
        self.table.itemChanged.connect(self.on_item_changed)
        self.locationXEdit.textChanged.connect(self.on_item_changed)
        self.locationYEdit.textChanged.connect(self.on_item_changed)
        self.locationZEdit.textChanged.connect(self.on_item_changed)

        self.editRotateX.textChanged.connect(self.on_item_changed)
        self.editRotateY.textChanged.connect(self.on_item_changed)
        self.editRotateZ.textChanged.connect(self.on_item_changed)
    
        
    def SetManipulator(self, manipulatorItem : QKooManipulatorItem):
        
        self.manipulator = None
        self.manipulatorItem = None
        self.data = None
        self.manipulator = manipulatorItem.manipulator  
        self.manipulatorItem = manipulatorItem
        #print(self.manipulator.locationX)      
        #print(self.manipulator.locationY)
        #print(self.manipulator.locationZ)
        #print(self.manipulator.rotationX)
        #print(self.manipulator.rotationY)
        #print(self.manipulator.rotationZ)
       
        
        self.locationXEdit.setText(str(self.manipulator.locationX))
        self.locationYEdit.setText(str(self.manipulator.locationY))
        self.locationZEdit.setText(str(self.manipulator.locationZ))
        self.editRotateX.setText(str(self.manipulator.rotationX))
        self.editRotateY.setText(str(self.manipulator.rotationY))
        self.editRotateZ.setText(str(self.manipulator.rotationZ)) 
        #self.on_item_changed()
        self.data = manipulatorItem.data

      
    def on_button_click_axis_x(self):
        pass

    def on_button_click_axis_y(self):
        pass

    def on_item_changed(self):
        #print("Table item changed")
        #print("Location X", self.locationXEdit.text())
        #print("Location Y", self.locationYEdit.text())
        #print("Location Z", self.locationZEdit.text())
        #print("Rotate X", self.editRotateX.text())
        #print("Rotate Y", self.editRotateY.text())
        #print("Rotate Z", self.editRotateZ.text())        
        try:
            changed = False
            if self.manipulatorLocationX != float(self.locationXEdit.text()):
                changed = True
            if self.manipulatorLocationY != float(self.locationYEdit.text()):
                changed = True
            if self.manipulatorLocationZ != float(self.locationZEdit.text()):
                changed = True
            if self.manipulatorRotationX != float(self.editRotateX.text()):
                changed = True
            if self.manipulatorRotationY != float(self.editRotateY.text()):
                changed = True
            if self.manipulatorRotationZ != float(self.editRotateZ.text()):
                changed = True
        except:
            return
        if changed:
            self.manipulatorLocationX = float(self.locationXEdit.text())
            self.manipulatorLocationY = float(self.locationYEdit.text())
            self.manipulatorLocationZ = float(self.locationZEdit.text())
            self.manipulatorRotationX = float(self.editRotateX.text())
            self.manipulatorRotationY = float(self.editRotateY.text())
            self.manipulatorRotationZ = float(self.editRotateZ.text())
            
            self.on_button_click()
            '''
            if self.manipulatorRotationX >180.0:
                self.manipulatorRotationX = self.manipulatorRotationX - int(self.manipulatorRotationX/360.0)*360.0
            elif self.manipulatorRotationX <180.0:
                a = int(self.manipulatorRotationX/360.0)
                b = a*360.0
                self.manipulatorRotationX = self.manipulatorRotationX - b
            if self.manipulatorRotationY >180.0:
                self.manipulatorRotationY = self.manipulatorRotationY - int(self.manipulatorRotationY/360.0)*360.0
            elif self.manipulatorRotationY <180.0:
                a = int(self.manipulatorRotationY/360.0)
                b = a*360.0
                self.manipulatorRotationY = self.manipulatorRotationY - b
            if self.manipulatorRotationZ >180.0:
                self.manipulatorRotationZ = self.manipulatorRotationZ - int(self.manipulatorRotationZ/360.0)*360.0
            elif self.manipulatorRotationZ <180.0:
                a = int(self.manipulatorRotationZ/360.0)
                b = a*360.0
                self.manipulatorRotationZ = self.manipulatorRotationZ - b
            self.editRotateX.setText(str(self.manipulatorRotationX))
            self.editRotateY.setText(str(self.manipulatorRotationY))
            self.editRotateZ.setText(str(self.manipulatorRotationZ))
            '''
    

if __name__ == "__main__":
    class MainWindow(QMainWindow):
        def __init__(self, *args, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)
            self.setWindowTitle("Koo Property Widget Test")
            self.resize(800,600)

            self.button = QPushButton("Test Manipulator Button",self)
            self.button.clicked.connect(self.open_test_manipulator_widget)

            self.label = QLabel("Button not clicked yet",self)
            self.label.move(10,50)
            layout = QVBoxLayout()
            layout.addWidget(self.label)
            layout.addWidget(self.button)
            
            widget = QWidget()
            widget.setLayout(layout)
            self.setCentralWidget(widget)
            #self.setCentralWidget(self.button)
           


        def open_test_manipulator_widget(self):
            self.customWidget = KooManipulatorWidget(self.on_button_click_test_manipulator,None,"Manipulator")
            self.dockWidget = QDockWidget("Test Manipulator Widget",self)
            self.dockWidget.setWidget(self.customWidget)

            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.dockWidget)

        def on_button_click_test_manipulator(self):
            self.label.setText("Manipulator Button Clicked")
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
