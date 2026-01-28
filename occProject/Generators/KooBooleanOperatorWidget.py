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

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QDockWidget, QWidget, QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog
from PyQt5.QtGui import QKeySequence, QBrush, QColor
from PyQt5.QtWidgets import QButtonGroup, QRadioButton, QGroupBox

from KooCAEManager.KooAISGeometry import (
    KooAISGeomFace
)

from OCC.Core.BRepAlgoAPI import (
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Section,
    BRepAlgoAPI_Cut
)

class KooCutOperatorWidget(QWidget):
    def __init__(self, mainWindowFunc, parent = None):
        super(KooCutOperatorWidget,self).__init__(parent)
        self.isOpened = True 
        self.setMinimumWidth(150)
        self.mainWindowFunc = mainWindowFunc

        self.layout = QVBoxLayout()

        self.MainFaceButton = QPushButton("Select Main")
        self.ToolFaceButton = QPushButton("Select Tool")

        self.MainFaceButton.clicked.connect(self.on_button_click_main_face)
        self.ToolFaceButton.clicked.connect(self.on_button_click_tool_face)
        
        self.layout.addWidget(self.MainFaceButton)        
        self.layout.addWidget(self.ToolFaceButton)
        
        self.setLayout(self.layout)

        self.selectedMainFace : KooAISGeomFace = None
        self.selectedToolFace : KooAISGeomFace = None
        self.CutOperationMode = False

    def on_button_click_main_face(self):
        self.MainFaceButton.setText("Select Main")
        self.selectedMainFace = None

    def on_button_click_tool_face(self):
        self.ToolFaceButton.setText("Select Tool")
        self.selectedToolFace = None

    def show(self) -> None:
        self.isOpened = True
        self.initializeSelection()
        return super().show()

    def initializeSelection(self):
        self.selectedMainFace = None
        self.selectedToolFace = None
        self.MainFaceButton.setText("Select Main")
        self.ToolFaceButton.setText("Select Tool")

    def AddFace(self, face : KooAISGeomFace):
        if self.selectedMainFace is None:
            self.selectedMainFace = face
            self.MainFaceButton.setText("Main Face Selected")
        else:
            if face.id == self.selectedMainFace.id:
                return
            self.selectedToolFace = face
            nameMain = self.selectedMainFace.name
            nameTool = self.selectedToolFace.name
            self.ToolFaceButton.setText(nameMain + " cut by " + nameTool)
            self.CutOperationMode = True
            self.mainWindowFunc("Generate")

    
    # when QWidget is closed, this function is called
    def closeEvent(self, event):
        self.hide()
        self.isOpened = False
        self.mainWindowFunc("Close")
        
    def forceClose(self):
        self.hide()
        self.isOpened = False
        self.mainWindowFunc("Close")
    

class KooBooleanOperatorWidget(QWidget):
    def __init__(self, mainWindowFunc, parent = None):
        super(KooBooleanOperatorWidget,self).__init__(parent)
        self.isOpened = True 
        self.setMinimumWidth(50)
        self.mainWindowFunc = mainWindowFunc

        self.layout = QVBoxLayout()

        self.GroupBoxOperationMode = QGroupBox("Boolean Operation Mode")
        self.GroupBoxOperationMode.setMaximumHeight(300)
        # Boolean Operation Fuse, Common, Section, Cut
        vLayout1 = QVBoxLayout()
        self.SelectFuseButton = QRadioButton("Fuse")
        self.SelectFuseButton.setChecked(True)
        self.SelectCommonButton = QRadioButton("Common")
        self.SelectSectionButton = QRadioButton("Section")
        self.SelectCutButton = QRadioButton("Cut")

        vLayout1.addWidget(self.SelectFuseButton)
        vLayout1.addWidget(self.SelectCommonButton)
        vLayout1.addWidget(self.SelectSectionButton)
        vLayout1.addWidget(self.SelectCutButton)
        
        self.GroupBoxOperationMode.setLayout(vLayout1)
        
        self.layout.addWidget(self.GroupBoxOperationMode)

        self.setLayout(self.layout)



    def on_button_click(self):
        self.mainWindowFunc()

    def show(self) -> None:
        self.isOpened = True
        return super().show()
    
    def close(self) -> bool:
        self.isOpened = False
        return super().close()
    
if __name__ == "__main__":
    class MainWindow(QMainWindow):
        def __init__(self, *args, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)
            self.resize(800, 600)
            self.button = QPushButton("Open Widget", self)
            self.button.clicked.connect(self.open_widget)

            self.label = QLabel("Button not clicked yet", self)
            self.label.move(10,50)
            self.setCentralWidget(self.button)
        
        def open_widget(self):
            self.customWidget = KooBooleanOperatorWidget(self.on_dialog_button_click, self)
            self.dockWidget = QDockWidget("Dockable", self)
            self.dockWidget.setWidget(self.customWidget)

            from PyQt5.QtCore import Qt

            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget)
        
        def on_dialog_button_click(self):
            self.label.setText("Button clicked in widget!")
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
