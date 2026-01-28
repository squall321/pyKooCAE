import sys
import numpy as np 
import os 


#getcwd = os.getcwd()
#path = os.path.join(getcwd, "Library")
#os.add_dll_directory(path)
#path = os.path.join(getcwd, "Library\\vtkmodules")
#os.add_dll_directory(path)

import vtkmodules
import vtkmodules.all

import pyvista as pv
from pyvista import CellType
from pyvista import Actor

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtWidgets import QAction, QDialog, QFileDialog, QPushButton, QTableWidgetItem, QTableWidget, QCheckBox, QLabel, QComboBox, QLineEdit
from PyQt5.QtGui import QIcon, QDoubleValidator

from PyQt5.QtCore import Qt

from pyvistaqt import QtInteractor, BackgroundPlotter


from KooCAEManager.KooNode import *
from KooCAEManager.KooElement import *
from KooCAEManager.KooPart import *
from KooCAEManager.KooResult import *
from KooCAEManager.KooMeshImporter import KooMSHImporter, KooDynaImporter

class PostWindow(QMainWindow):
    def __init__(self, nodeManager : NodeManager = None, partManager : KooPartManager = None, elementManager : ElementManager = None, parent=None):
        super(PostWindow, self).__init__(parent)
        self.cx = [0.929411765,0.235294118,0.721568627,0,0.941176471,0.274509804,0.678431373,0.482352941,0.780392157,1,0.333333333,0.098039216,0.415686275,0.878431373,0,0.82745098,0.823529412,0.545098039,0.941176471,0.466666667,0.498039216,0.501960784,0.901960784,0.858823529,0.941176471,0.2,0,0.678431373,0.870588235,0.529411765,0.529411765,0.803921569,0.411764706,0,0.580392157,0,0,0,1,0.576470588,0.741176471,1,0.647058824,1,0.282352941,0,0.196078431,0.737254902,0.419607843,0.254901961,0.498039216,1,0.91372549,0.933333333,0,0.858823529,0.501960784,0.596078431,0.117647059,0.392156863,0,0.501960784,0.282352941,0,0.847058824,0.698039216,0.941176471,0.980392157,1,0.501960784,0.333333333,0.662745098,0.690196078,0.588235294,0,0.780392157,0.541176471,0,0.294117647,0.180392157,0.545098039,0,1,0.564705882,1,0.6,1,0.250980392,0.603921569,0.729411765,0.37254902,0,1,0,0.62745098,1,0.823529412,0.752941176,1,1,0.854901961,0.133333333,1,1,1,0.862745098,0.933333333,0.980392157,1,0.803921569,0.854901961,0.68627451,0.545098039,0.690196078,0.4,0.866666667,1]
        self.cy = [0.643137255,0.701960784,0.525490196,0.501960784,0.501960784,0.509803922,0.847058824,0.407843137,0.082352941,0.270588235,0.419607843,0.098039216,0.352941176,1,0,0.82745098,0.411764706,0.270588235,0.97254902,0.533333333,1,0.501960784,0.901960784,0.439215686,0.901960784,0.6,0.807843137,1,0.721568627,0.807843137,0.807843137,0.360784314,0.411764706,0.8,0,0,1,0,0.62745098,0.439215686,0.717647059,0.941176471,0.164705882,0.411764706,0.239215686,0.392156863,0.803921569,0.560784314,0.556862745,0.411764706,1,0.647058824,0.588235294,0.909803922,0,0.439215686,0.501960784,0.984313725,0.564705882,0.584313725,1,0,0.819607843,0.980392157,0.749019608,0.133333333,1,0.501960784,0.71372549,0,0.419607843,0.662745098,0.768627451,0.588235294,0.501960784,0.082352941,0.168627451,0.545098039,0,0.545098039,0,1,0.843137255,0.933333333,0,0.196078431,0.549019608,0.878431373,0.803921569,0.333333333,0.619607843,0.749019608,0.6,0,0.321568627,0.388235294,0.705882353,0.752941176,1,0.752941176,0.647058824,0.545098039,1,0,0.498039216,0.862745098,0.509803922,0.980392157,0.078431373,0.521568627,0.439215686,0.933333333,0,0.878431373,0.803921569,0.62745098,0.4]
        self.cz = [0.239215686,0.443137255,0.043137255,0,0.501960784,0.705882353,0.901960784,0.933333333,0.521568627,0,0.184313725,0.439215686,0.803921569,1,0,0.82745098,0.117647059,0.074509804,1,0.6,0,0.501960784,0.980392157,0.576470588,0.549019608,0.4,0.819607843,0.184313725,0.529411765,0.921568627,0.980392157,0.360784314,0.411764706,1,0.82745098,0.803921569,0.498039216,0.545098039,0.478431373,0.858823529,0.419607843,0.960784314,0.164705882,0.705882353,0.545098039,0,0.196078431,0.560784314,0.137254902,0.882352941,0.831372549,0,0.478431373,0.666666667,0.501960784,0.576470588,0,0.596078431,1,0.929411765,1,0,0.8,0.603921569,0.847058824,0.133333333,1,0.447058824,0.756862745,0.501960784,0.184313725,0.662745098,0.870588235,0.588235294,0.501960784,0.521568627,0.88627451,0.545098039,0.509803922,0.341176471,0,0,0,0.564705882,1,0.8,0,0.815686275,0.196078431,0.82745098,0.62745098,1,0,1,0.176470588,0.278431373,0.549019608,0.752941176,0.878431373,0.796078431,0.125490196,0.133333333,0,0,0.31372549,0.862745098,0.933333333,0.823529412,0.576470588,0.247058824,0.839215686,0.933333333,0.545098039,0.901960784,0.666666667,0.866666667,0]

        self.setFolderPath = None
        self.setWindowTitle('Post-Processor')
        self.setGeometry(100, 100, 800, 600)
        self.frame = QWidget()
        self.vl = QVBoxLayout()
        self.vtkWidget = QtInteractor(self.frame)
        # add BackgroundPlotter to the layout
        #self.bgPlotter = BackgroundPlotter()
        #self.bgPlotter.set_background("white")
        layoutMainBody = QHBoxLayout()
        layoutMainBody.addWidget(self.vtkWidget)
        vLayoutMainBody = QVBoxLayout()
        
        self.checkBoxManualRange = QCheckBox("Manual",self)
        self.checkBoxManualRange.setChecked(False)
        self.checkBoxManualRange.setFixedWidth(120)
        #self.checkBoxAllColorRange.stateChanged.connect(self.on_selection_changed_checkbox_view)
        self.editBoxMinColorLabel = QLabel("Min",self)
        self.editBoxMinColorLabel.setFixedWidth(30)
        self.editBoxMinColor = QLineEdit(self)
        # only x.xxE+xx format for editboxmincolor
        self.editBoxMinColor.setValidator(QDoubleValidator())
        self.editBoxMinColor.setFixedWidth(60)
        self.editBoxMaxColorLabel = QLabel("Max",self)
        self.editBoxMaxColorLabel.setFixedWidth(30)
        self.editBoxMaxColor = QLineEdit(self)
        self.editBoxMaxColor.setValidator(QDoubleValidator())
        self.editBoxMaxColor.setFixedWidth(60)
        hLayoutforColorRange = QHBoxLayout()
        hLayoutforColorRange.addWidget(self.checkBoxManualRange)
        hLayoutforColorRange.addWidget(self.editBoxMinColorLabel)
        hLayoutforColorRange.addWidget(self.editBoxMinColor)
        hLayoutforColorRange.addWidget(self.editBoxMaxColorLabel)
        hLayoutforColorRange.addWidget(self.editBoxMaxColor)
        vLayoutMainBody.addLayout(hLayoutforColorRange)
        self.importedDataTable = QTableWidget(self)
        self.importedDataTable.setColumnCount(5)
        self.importedDataTable.setColumnWidth(0, 100)
        self.importedDataTable.setColumnWidth(1, 25)
        self.importedDataTable.setColumnWidth(2, 60)
        self.importedDataTable.setColumnWidth(3, 30)
        self.importedDataTable.setColumnWidth(4, 100)
        
        self.importedDataTable.setHorizontalHeaderLabels(["Name", "View", "Option", "IntPt", "Time"])
        self.importedDataTable.setFixedWidth(340)
        self.selection_table_model = self.importedDataTable.selectionModel()
        self.selection_table_model.selectionChanged.connect(self.on_selection_changed_table)
        vLayoutMainBody.addWidget(self.importedDataTable)
        
        layoutMainBody.addLayout(vLayoutMainBody)
        
        self.vl.addLayout(layoutMainBody)
        #self.vl.addWidget(self.vtkWidget)
        # self.vl.addWidget(self.bgPlotter.interactor)
        
        layoutBottomOption = QHBoxLayout()
        layoutBottomOption.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.SetBottomViewButton = QPushButton('',self)
        self.SetTopViewButton = QPushButton('',self)
        self.SetLeftViewButton = QPushButton('',self)   
        self.SetRightViewButton = QPushButton('',self)
        self.SetFrontViewButton = QPushButton('',self)
        self.SetBackViewButton = QPushButton('',self)
        self.SetIsoViewButton = QPushButton('',self)
        
        
        self.SetBottomViewButton.setFixedSize(32, 32)
        self.SetTopViewButton.setFixedSize(32, 32)  
        self.SetLeftViewButton.setFixedSize(32, 32)
        self.SetRightViewButton.setFixedSize(32, 32)
        self.SetFrontViewButton.setFixedSize(32, 32)
        self.SetBackViewButton.setFixedSize(32, 32)
        self.SetIsoViewButton.setFixedSize(32, 32)
                
        # hilighted effect of push button when mouse hover               
        hoverstyle = """
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            padding: 10px;
        }
        QPushButton:hover {
            background-color: #dcdcdc;
            border: 1px solid #888;
        }
        QPushButton:pressed {
            background-color: #bcbcbc;
            border: 1px solid #555;
        }
        """        
        self.SetBottomViewButton.setIcon(QIcon('Library\\resource\\ViewBottom.png'))
        self.SetTopViewButton.setIcon(QIcon('Library\\resource\\ViewTop.png'))  
        self.SetLeftViewButton.setIcon(QIcon('Library\\resource\\ViewLeft.png'))
        self.SetRightViewButton.setIcon(QIcon('Library\\resource\\ViewRight.png'))
        self.SetFrontViewButton.setIcon(QIcon('Library\\resource\\ViewFront.png'))
        self.SetBackViewButton.setIcon(QIcon('Library\\resource\\ViewBack.png'))
        self.SetIsoViewButton.setIcon(QIcon('Library\\resource\\ViewIso.png'))
        
        self.SetBottomViewButton.setStyleSheet(hoverstyle)
        self.SetTopViewButton.setStyleSheet(hoverstyle)
        self.SetLeftViewButton.setStyleSheet(hoverstyle)
        self.SetRightViewButton.setStyleSheet(hoverstyle)
        self.SetFrontViewButton.setStyleSheet(hoverstyle)
        self.SetBackViewButton.setStyleSheet(hoverstyle)
        self.SetIsoViewButton.setStyleSheet(hoverstyle)        
        
        self.SetBottomViewButton.setIconSize(self.SetBottomViewButton.size())
        self.SetTopViewButton.setIconSize(self.SetTopViewButton.size())
        self.SetLeftViewButton.setIconSize(self.SetLeftViewButton.size())
        self.SetRightViewButton.setIconSize(self.SetRightViewButton.size())
        self.SetFrontViewButton.setIconSize(self.SetFrontViewButton.size())
        self.SetBackViewButton.setIconSize(self.SetBackViewButton.size())
        self.SetIsoViewButton.setIconSize(self.SetIsoViewButton.size())
        # icon image of push button from image file
        
        self.SetBottomViewButton.clicked.connect(self.SetBottomView)
        self.SetTopViewButton.clicked.connect(self.SetTopView)
        self.SetLeftViewButton.clicked.connect(self.SetLeftView)
        self.SetRightViewButton.clicked.connect(self.SetRightView)
        self.SetFrontViewButton.clicked.connect(self.SetFrontView)
        self.SetBackViewButton.clicked.connect(self.SetBackView)
        self.SetIsoViewButton.clicked.connect(self.SetIsoView)
        
        layoutBottomOption.addWidget(self.SetBottomViewButton)
        layoutBottomOption.addWidget(self.SetTopViewButton)
        layoutBottomOption.addWidget(self.SetLeftViewButton)
        layoutBottomOption.addWidget(self.SetRightViewButton)
        layoutBottomOption.addWidget(self.SetFrontViewButton)
        layoutBottomOption.addWidget(self.SetBackViewButton)
        layoutBottomOption.addWidget(self.SetIsoViewButton)
                
        self.vl.addLayout(layoutBottomOption)
        
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)
        self.setGeometry(100, 100, 1280, 720)
        self.show()

        # Initialize PyVista plotter
        self.plotter = self.vtkWidget

        if nodeManager is not None:
            self.nodeManager = nodeManager
        if elementManager is not None:
            self.elementManager = elementManager  
        if partManager is not None:
            self.partManager = partManager     

        self.meshLine2 = {}
        self.meshLine3 = {}
        self.meshTri3 = {}
        self.meshTri6 = {} 
        self.meshQuad4 = {}
        self.meshQuad8 = {}
        self.meshTetra4 = {}
        self.meshTetra10 = {}
        self.meshPenta6 = {}        
        self.meshHexa8 = {}
        self.meshHexa20 = {} 

        self.meshLine2Actor = {}
        self.meshLine3Actor = {}
        self.meshTri3Actor = {}
        self.meshTri6Actor = {}
        self.meshQuad4Actor = {} 
        self.meshQuad8Actor = {}        
        self.meshTetra4Actor = {}
        self.meshTetra10Actor = {}        
        self.meshPenta6Actor = {}
        self.meshHexa8Actor = {} 
        self.meshHexa20Actor = {}
        
        self.importer = None
        
        self.resultMode = "Stress"
        self.resultMode = "Displacement"
        self.resultMode = None
        self.initUI()
        
        
        # perspective view
        self.vtkWidget.enable_parallel_projection()
        pass
    
    def initUI(self):
        menu_bar = self.menuBar()
        self.file_menu = menu_bar.addMenu("File")        
        
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.newFile)
        self.file_menu.addAction(new_action)
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Import Menu    
            
        import_msh_action = QAction("msh",self)
        import_msh_action.triggered.connect(self.importMsh)
        
        import_dyna_action = QAction("LSDyna",self)
        import_dyna_action.triggered.connect(self.importDyna)
                        
        import_sub_menu = self.file_menu.addMenu("Import")
        import_sub_menu.addAction(import_msh_action)
        import_sub_menu.addAction(import_dyna_action)
        
        
        ### Import Result Menu                        
        import_result_d3plot_disp_action = QAction("D3plot-Disp",self)
        import_result_d3plot_disp_action.triggered.connect(self.importD3plotDisp)
        
        import_result_d3plot_stress_action = QAction("D3plot-Stress",self)
        import_result_d3plot_stress_action.triggered.connect(self.importD3plotStress)
        
        import_result_nodout_action = QAction("Nodout",self)
        import_result_nodout_action.triggered.connect(self.importNodout)
        
        import_result_elout_action = QAction("Elout",self)
        import_result_elout_action.triggered.connect(self.importElout)        
        
        import_result_sub_menu = self.file_menu.addMenu("Import Result")
        import_result_sub_menu.addAction(import_result_d3plot_disp_action)
        import_result_sub_menu.addAction(import_result_d3plot_stress_action)
        import_result_sub_menu.addAction(import_result_nodout_action)
        import_result_sub_menu.addAction(import_result_elout_action)
                
        self.file_menu.addAction(exit_action)
        
        self.setWindowTitle("Post Window")
        pass
    
    def SetBottomView(self):
        self.vtkWidget.view_vector((0, 0, -1), (0, 1, 0))
    
    def SetTopView(self):
        self.vtkWidget.view_vector((0, 0, 1), (0, 1, 0))
        
    def SetLeftView(self):
        self.vtkWidget.view_vector((1, 0, 0), (0, 0, 1))
    
    def SetRightView(self):
        self.vtkWidget.view_vector((-1, 0, 0), (0, 0, 1))
    
    def SetFrontView(self):
        self.vtkWidget.view_vector((0, 1, 0), (0, 0, 1))
    
    def SetBackView(self):
        self.vtkWidget.view_vector((0, -1, 0), (0, 0, 1))
    
    def SetIsoView(self):
        self.vtkWidget.view_isometric()
        
    def on_selection_changed_table(self):
        #indexes = self.selection_table_model.selectedIndexes()
        #for index in indexes:
        #    print(index.row(), index.column())
        partIDList = [] 
        for part in self.partManager.parts.values():
            partIDList.append(part.id)
        curTimeStep = 0
        if self.resultMode == "Stress":
            curOption = "S11"
            curIntpt = 0
            for i in range(len(self.comboBoxTimeStateList)):
                prevTimeState = self.comboBoxTimeStateList[i]
                prevOptionState = self.comboBoxOptionStateList[i]
                prevIntptState = self.comboBoxIntegrationPointStateList[i]
                curTimeState = self.comboBoxTimeList[i].currentIndex()
                curIntptState = self.comboBoxIntegrationPointList[i].currentIndex()
                curOptionState = self.comboBoxOptionList[i].currentText()
                if prevTimeState != curTimeState or prevOptionState != curOptionState or prevIntptState != curIntptState:
                    self.comboBoxTimeStateList[i] = curTimeState
                    self.comboBoxOptionStateList[i] = curOptionState
                    self.comboBoxIntegrationPointStateList[i] = curIntptState
                    if self.checkBoxManualRange.isChecked() == False:
                        #self.ResetElementColor(curOptionState, curTimeState)
                        self.UpdateElementColorPart(partIDList[i],curOptionState,curIntptState, curTimeState)
                        break
                    curTimeStep = curTimeState
                    curOption = curOptionState
                    curIntpt = curIntptState
            if self.checkBoxManualRange.isChecked() == True:
                self.UpdateElementColorManual(curOption, curIntpt, curTimeStep)
        elif self.resultMode == "Displacement":
            curOption = "ut"
            for i in range(len(self.comboBoxTimeStateList)):
                prevTimeState = self.comboBoxTimeStateList[i]
                prevOptionState = self.comboBoxOptionStateList[i]
                curTimeState = self.comboBoxTimeList[i].currentIndex()
                curOptionState = self.comboBoxOptionList[i].currentText()
                if prevTimeState != curTimeState or prevOptionState != curOptionState:
                    self.comboBoxTimeStateList[i] = curTimeState
                    self.comboBoxOptionStateList[i] = curOptionState                
                    if self.checkBoxManualRange.isChecked() == False:
                        self.ResetElementColor(curOptionState, curTimeState)
                        self.UpdateNodalColorPart(partIDList[i],curOptionState, curTimeState)
                        break 
                    curTimeStep = curTimeState
                    curOption = curOptionState
            if self.checkBoxManualRange.isChecked() == True:
                
                self.UpdateNodalColorManual(curOption, curTimeStep)
            
            # update color 
            
            
    def on_selection_changed_checkbox_view(self):
        
        newCheckedList = [] 
        for i in range(self.importedDataTable.rowCount()):
            curLayout = self.importedDataTable.cellWidget(i,1).layout()
            #Get widget from layout
            curWidget : QCheckBox = curLayout.itemAt(0).widget()
            if curWidget.checkState() == Qt.CheckState.Checked:
                newCheckedList.append(True)
            else:
                newCheckedList.append(False)
        i = 0 
        
        for part in self.partManager.parts.values():
            if newCheckedList[i] != self.checkedViewList[i]:
                partID = part.id
                nodeManager = part.nodeManager
                elementManager = part.elementManager
                if newCheckedList[i] == False:
                    self.Update(nodeManager, elementManager, partID, True, True)
                else:
                    self.Update(nodeManager, elementManager, partID, True)                
                
            i = i + 1
        
        self.checkedViewList = newCheckedList
    
    def newFile(self):
        self.RemoveAll()
                
    def importMsh(self):
        file_dialog = QFileDialog(self)
        filePath = file_dialog.getOpenFileName(self, "Open File", "", "MSH Files (*.msh)")
        if filePath[0] == "":
            return
        
        self.setFolderPath = os.path.dirname(filePath[0])
        nodeManager : NodeManager = NodeManager()
        elementManager : ElementManager = ElementManager(nodeManager)
        importer = KooMSHImporter()
        importer.import_msh_file(filePath[0])
        importer.SetUpdateManager(nodeManager, elementManager)
        importer.UpdateManager()
        self.nodeManager = nodeManager
        self.elementManager = elementManager
        self.importer = importer
        self.Update(None,None,1,True)

    def importDyna(self):
        file_dialog = QFileDialog(self)
        filePath = file_dialog.getOpenFileName(self, "Open File", "", "Dyna Files (*.k)") 
        if filePath[0] == "":
            return
        # if dialog canceled
        
        self.RemoveAll()
        
        self.setFolderPath = os.path.dirname(filePath[0])
        self.nodeManager : NodeManager = NodeManager()
        self.partManager : KooPartManager = KooPartManager()
        self.importer = None
        self.importer = KooDynaImporter(self.nodeManager,self.partManager)
        self.importer.importDynaFile(filePath[0])
        self.importer.importNode()
        self.importer.importPart()
        
        self.UpdateParts(self.nodeManager, self.partManager)
    
    def importD3plotDisp(self):
        if self.setFolderPath == None:
            self.importDyna()
        if self.setFolderPath == None:
            return
        filePath = os.path.join(self.setFolderPath, "d3plot")
        self.importer.importD3plotDisp(filePath)
        numPart = len(self.partManager.parts)
        partIDList = [] 
        for part in self.partManager.parts.values():
            partIDList.append(part.id) 
        
        self.comboBoxTimeList = [] 
        self.comboBoxOptionList = []
        self.comboBoxTimeStateList = []
        self.comboBoxOptionStateList = []       
        self.resultMode = "Displacement"
        for i in range(numPart):
            part = self.partManager.parts[partIDList[i]]            
            nodeManager : NodeManager = part.nodeManager
            comboBox = QComboBox()
            for curTime in nodeManager.time:
                # curTime as x.xxE+xx
                curTime = "{:.2e}".format(curTime)
                 
                comboBox.addItem(str(curTime))
            comboBoxOption = QComboBox()

            # label inside comboBoxOption
            comboBoxOption.addItem("ut")
            comboBoxOption.addItem("ux")
            comboBoxOption.addItem("uy")
            comboBoxOption.addItem("uz")
            
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(comboBox)
            # connect comboBox to Function
            comboBox.currentIndexChanged.connect(self.on_selection_changed_table)
            cell_layout.setAlignment(comboBox,Qt.AlignmentFlag.AlignCenter)
            cell_layout.setContentsMargins(0,0,0,0)
            cell_widget.setLayout(cell_layout)                    
            self.importedDataTable.setCellWidget(i,4,cell_widget)
            
            cell_widget_option = QWidget()
            cell_layout_option = QHBoxLayout(cell_widget_option)
            cell_layout_option.addWidget(comboBoxOption)
            cell_layout_option.setAlignment(comboBoxOption,Qt.AlignmentFlag.AlignCenter)
            cell_layout_option.setContentsMargins(0,0,0,0)
            cell_widget_option.setLayout(cell_layout_option)
            comboBoxOption.currentIndexChanged.connect(self.on_selection_changed_table)
            self.importedDataTable.setCellWidget(i,2,cell_widget_option)
        
            lastStep = len(nodeManager.time) - 1
            self.comboBoxTimeList.append(comboBox)
            self.comboBoxOptionList.append(comboBoxOption)
            self.comboBoxTimeStateList.append(lastStep)
            self.comboBoxOptionStateList.append("ut")
        
        if lastStep >= 0:
            self.UpdateNodalColor("ut",lastStep)
        
    def importD3plotStress(self):
        if self.setFolderPath == None:
            self.importDyna()
        if self.setFolderPath == None:
            return
        
        filePath = os.path.join(self.setFolderPath, "d3plot")
        self.importer.importD3plotStress(filePath)
        numPart = len(self.partManager.parts)
        partIDList = []
        for part in self.partManager.parts.values():
            partIDList.append(part.id)
            
        self.comboBoxTimeList = []
        self.comboBoxOptionList = []
        self.comboBoxIntegrationPointList = [] 
        self.comboBoxTimeStateList = []
        self.comboBoxOptionStateList = []
        self.comboBoxIntegrationPointStateList = []
        self.resultMode = "Stress"  
        for i in range(numPart):
            part = self.partManager.parts[partIDList[i]]
            comboBox = QComboBox()
            for curTime in part.elementManager.time:
                comboBox.addItem(str(curTime))
            comboBoxOption = QComboBox()
            comboBoxOption.addItem("SXX")
            comboBoxOption.addItem("SYY")
            comboBoxOption.addItem("SZZ")
            comboBoxOption.addItem("SXY")
            comboBoxOption.addItem("SYZ")
            comboBoxOption.addItem("SZX")
            
            comboBoxIntegrationPoint = QComboBox()
            if part.elementManager.GetNumIntegrationPoints() > 0:
                for j in range(part.elementManager.GetNumIntegrationPoints()):
                    comboBoxIntegrationPoint.addItem(str(j))
            else:
                comboBoxIntegrationPoint.addItem("0")       
            
            
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(comboBox)
            comboBox.currentIndexChanged.connect(self.on_selection_changed_table)
            cell_layout.setAlignment(comboBox,Qt.AlignmentFlag.AlignCenter)
            cell_layout.setContentsMargins(0,0,0,0)
            cell_widget.setLayout(cell_layout)
            self.importedDataTable.setCellWidget(i,4,cell_widget)

            cell_widget_option = QWidget()
            cell_layout_option = QHBoxLayout(cell_widget_option)
            cell_layout_option.addWidget(comboBoxOption)
            cell_layout_option.setAlignment(comboBoxOption,Qt.AlignmentFlag.AlignCenter)
            cell_layout_option.setContentsMargins(0,0,0,0)
            cell_widget_option.setLayout(cell_layout_option)
            comboBoxOption.currentIndexChanged.connect(self.on_selection_changed_table)
            self.importedDataTable.setCellWidget(i,2,cell_widget_option)
            
            cell_widget_intpt = QWidget()
            cell_layout_intpt = QHBoxLayout(cell_widget_intpt)
            cell_layout_intpt.addWidget(comboBoxIntegrationPoint)
            cell_layout_intpt.setAlignment(comboBoxIntegrationPoint,Qt.AlignmentFlag.AlignCenter)
            cell_layout_intpt.setContentsMargins(0,0,0,0)
            cell_widget_intpt.setLayout(cell_layout_intpt)
            comboBoxIntegrationPoint.currentIndexChanged.connect(self.on_selection_changed_table)
            self.importedDataTable.setCellWidget(i,3,cell_widget_intpt)

            lastStep = len(part.elementManager.time) - 1
            self.comboBoxTimeList.append(comboBox)
            self.comboBoxOptionList.append(comboBoxOption)
            self.comboBoxIntegrationPointList.append(comboBoxIntegrationPoint)
            self.comboBoxTimeStateList.append(lastStep)
            self.comboBoxOptionStateList.append("S11")
            self.comboBoxIntegrationPointStateList.append(0)   
            
    
            
    
    def importNodout(self):
        if self.setFolderPath == None:
            self.importDyna()
        if self.setFolderPath == None:
            return
        filePath = os.path.join(self.setFolderPath, "nodout")
        self.importer.importNODOUT(filePath)
        self.UpdateNodalColor("TotalDisp",0)
        
    def importElout(self):
        if self.setFolderPath == None:
            self.importDyna()
        if self.setFolderPath == None:
            return
        filePath = os.path.join(self.setFolderPath, "elout")
        self.importer.importELOUT(filePath)

    def UpdateAllParts(self):
        self.plotter.clear()
        for part in self.partManager.parts.values():
            self.UpdatePartSkin(part)
    
    def UpdatePartSkin(self, part : KooPart):
        nodeManager = part.nodeManager
        elementManager = part.elementManager
        partID = part.id
        self.Update(nodeManager, elementManager, partID, False)
        
    def RemoveAll(self):
        self.plotter.clear()
        self.meshLine2 = {}
        self.meshLine3 = {}
        self.meshTri3 = {}
        self.meshTri6 = {} 
        self.meshQuad4 = {}
        self.meshQuad8 = {}
        self.meshTetra4 = {}
        self.meshTetra10 = {}
        self.meshPenta6 = {}        
        self.meshHexa8 = {}
        self.meshHexa20 = {} 

        self.meshLine2Actor = {}
        self.meshLine3Actor = {}
        self.meshTri3Actor = {}
        self.meshTri6Actor = {}
        self.meshQuad4Actor = {} 
        self.meshQuad8Actor = {}        
        self.meshTetra4Actor = {}
        self.meshTetra10Actor = {}        
        self.meshPenta6Actor = {}
        self.meshHexa8Actor = {} 
        self.meshHexa20Actor = {}
        
        self.importer = None
        self.nodeManager = None
        self.elementManager = None
        self.partManager = None        
        self.setFolderPath = None
        
        self.importedDataTable.clear()
        self.importedDataTable.setColumnCount(5)
        self.importedDataTable.setColumnWidth(0, 100)
        self.importedDataTable.setColumnWidth(1, 25)
        self.importedDataTable.setColumnWidth(2, 60)
        self.importedDataTable.setColumnWidth(3, 30)
        self.importedDataTable.setColumnWidth(4, 100)
        
        self.importedDataTable.setHorizontalHeaderLabels(["Name", "View", "Option", "IntPt", "Time"])
        self.importedDataTable.setFixedWidth(340)
        
        
    

    def UpdateSkin(self, nodeManager : NodeManager = None, elementManager : ElementManager = None, partID = 0, update = False):
        if nodeManager == None:
            nodeManager = self.nodeManager
        if elementManager == None:
            elementManager = self.elementManager
        colorid = partID%117
        if update == True: 
            self.plotter.clear()
            self.meshLine2[partID] = None
            self.meshLine3[partID] = None
            self.meshTri3[partID] = None
            self.meshTri6[partID] = None
            self.meshQuad4[partID] = None
            self.meshQuad8[partID] = None
            self.meshTetra4[partID] = None
            self.meshTetra10[partID] = None
            self.meshPenta6[partID] = None
            self.meshHexa8[partID] = None
            self.meshHexa20[partID] = None

        idtokey, nodalCoordinates = nodeManager.GetNodalCoordinates()
        elementQuad8Connectivities = elementManager.GetQuad8Connectivities(idtokey)
        elementQuad4Connectivities = elementManager.GetQuad4Connectivities(idtokey)
        elementTri6Connectivities = elementManager.GetTri6Connectivities(idtokey)
        elementTri3Connectivities = elementManager.GetTri3Connectivities(idtokey)
        elementLine3Connectivities = elementManager.GetLine3Connectivities(idtokey)
        elementLine2Connectivities = elementManager.GetLine2Connectivities(idtokey)
        elementPointConnectivities = elementManager.GetPointConnectivities(idtokey)
        
        if elementQuad8Connectivities.size != 0:
            cell_types = np.full(elementQuad8Connectivities.size // 9, CellType.QUAD)
            cells = np.hstack(elementQuad8Connectivities)
            meshQuad8 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshQuad8Actor = self.plotter.add_mesh(meshQuad8, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshQuad8Actor[partID] = meshQuad8Actor
        else:
            meshQuad8 = None

        if elementQuad4Connectivities.size != 0:
            cell_types = np.full(elementQuad4Connectivities.size // 5, CellType.QUAD)  # 4 points + 1 for the count
            cells = np.hstack(elementQuad4Connectivities)
            meshQuad4 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshQuad4Actor =self.plotter.add_mesh(meshQuad4, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshQuad4Actor[partID] = meshQuad4Actor

        else:
            meshQuad4 = None
        if elementTri6Connectivities.size != 0: 
            cell_types = np.full(elementTri6Connectivities.size // 7, CellType.TRIANGLE)
            cells = np.hstack(elementTri6Connectivities)
            meshTri6 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshTri6Actor = self.plotter.add_mesh(meshTri6, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshTri6Actor[partID] = meshTri6Actor
        else:   
            meshTri6 = None

        if elementTri3Connectivities.size != 0:
            cell_types = np.full(elementTri3Connectivities.size // 4, CellType.TRIANGLE)  # 3 points + 1 for the count
            cells = np.hstack(elementTri3Connectivities)
            meshTri3 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)            
            meshTri3Actor = self.plotter.add_mesh(meshTri3, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshTri3Actor[partID] = meshTri3Actor
        else:
            meshTri3 = None
        if meshQuad8 is not None or meshQuad4 is not None or meshTri6 is not None or meshTri3 is not None:
            self.meshQuad8[partID] = meshQuad8
            self.meshTri6[partID] = meshTri6
            self.meshQuad4[partID] = meshQuad4
            self.meshTri3[partID] = meshTri3            
            return
        
        if elementLine3Connectivities.size != 0:             
            cell_types = np.full(elementLine3Connectivities.size // 4, CellType.LINE)  # 3 points + 1 for the count
            cells = np.hstack(elementLine3Connectivities)
            meshLine3 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshLine3Actor = self.plotter.add_mesh(meshLine3, show_edges=True,line_width=2,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshLine3Actor[partID] = meshLine3Actor

        else:
            meshLine3 = None
        if elementLine2Connectivities.size != 0:
            cell_types = np.full(elementLine2Connectivities.size // 3, CellType.LINE)
            cells = np.hstack(elementLine2Connectivities)
            meshLine2 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshLine2Actor = self.plotter.add_mesh(meshLine2, show_edges=True,line_width=2,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))          
            self.meshLine2Actor[partID] = meshLine2Actor
        else:
            meshLine2 = None
        if meshLine3 is not None or meshLine2 is not None:
            self.meshLine2[partID] = meshLine2
            self.meshLine3[partID] = meshLine3            
            return
        
        if elementPointConnectivities.size != 0:
            cell_types = np.full(elementPointConnectivities.size // 2, CellType.VERTEX)
            cells = np.hstack(elementPointConnectivities)
            meshPoint = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshPointActor = self.plotter.add_mesh(meshPoint, show_edges=True,line_width=2,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshLine2Actor[partID] = meshPointActor

        
        #self.plotter.show()


    def Update(self,nodeManager : NodeManager = None, elementManager : ElementManager = None, partID = 0, update = False, hide = False, deformed = False, Option = "ut", TimeStep = 0):
        
        if nodeManager == None:
            nodeManager = self.nodeManager
        if elementManager == None:
            elementManager = self.elementManager
        colorid = partID%117
        if update == True:
            if partID in self.meshLine2:
                if self.meshLine2[partID] is not None:
                    self.plotter.remove_actor(self.meshLine2Actor[partID])
            if partID in self.meshLine3:
                if self.meshLine3[partID] is not None:
                    self.plotter.remove_actor(self.meshLine3Actor[partID])
            if partID in self.meshTri3:
                if self.meshTri3[partID] is not None:
                    self.plotter.remove_actor(self.meshTri3Actor[partID])                    
            if partID in self.meshTri6:
                if self.meshTri6[partID] is not None:
                    self.plotter.remove_actor(self.meshTri6Actor[partID])
            if partID in self.meshQuad4:
                if self.meshQuad4[partID] is not None:
                    self.plotter.remove_actor(self.meshQuad4Actor[partID])
            if partID in self.meshQuad8:
                if self.meshQuad8[partID] is not None:
                    self.plotter.remove_actor(self.meshQuad8Actor[partID])
            if partID in self.meshTetra4:
                if self.meshTetra4[partID] is not None:
                    self.plotter.remove_actor(self.meshTetra4Actor[partID])
            if partID in self.meshTetra10:
                if self.meshTetra10[partID] is not None:
                    self.plotter.remove_actor(self.meshTetra10Actor[partID])
            if partID in self.meshPenta6:
                if self.meshPenta6[partID] is not None:
                    self.plotter.remove_actor(self.meshPenta6Actor[partID])
            if partID in self.meshHexa8:
                if self.meshHexa8[partID] is not None:
                    self.plotter.remove_actor(self.meshHexa8Actor[partID])
            if partID in self.meshHexa20:
                if self.meshHexa20[partID] is not None:
                    self.plotter.remove_actor(self.meshHexa20Actor[partID])
                               
            self.meshLine2[partID] = None
            self.meshLine3[partID] = None
            self.meshTri3[partID] = None
            self.meshTri6[partID] = None
            self.meshQuad4[partID] = None
            self.meshQuad8[partID] = None
            self.meshTetra4[partID] = None
            self.meshTetra10[partID] = None
            self.meshPenta6[partID] = None  
            self.meshHexa8[partID] = None
            self.meshHexa20[partID] = None
            if hide == True:
                return

        if deformed == True:
            idtokey, nodalCoordinates = nodeManager.GetDeformedCoordinates(Option, TimeStep)        
        else:
            idtokey, nodalCoordinates = nodeManager.GetNodalCoordinates()        
        elementHexa20Connectivities = elementManager.GetHexa20Connectivities(idtokey) 
        elementHexa8Connectivities = elementManager.GetHexa8Connectivities(idtokey)
        elementPenta6Connectivities = elementManager.GetPenta6Connectivities(idtokey)
        elementTetra10Connectivities = elementManager.GetTetra10Connectivities(idtokey)        
        elementTetra4Connectivities = elementManager.GetTetra4Connectivities(idtokey)
        elementQuad8Connectivities = elementManager.GetQuad8Connectivities(idtokey)
        elementQuad4Connectivities = elementManager.GetQuad4Connectivities(idtokey)
        elementTri6Connectivities = elementManager.GetTri6Connectivities(idtokey)
        elementTri3Connectivities = elementManager.GetTri3Connectivities(idtokey)
        elementLine3Connectivities = elementManager.GetLine3Connectivities(idtokey)
        elementLine2Connectivities = elementManager.GetLine2Connectivities(idtokey)
        elementPointConnectivities = elementManager.GetPointConnectivities(idtokey)
            
            
        if elementHexa20Connectivities.size != 0:
            cell_types = np.full(elementHexa20Connectivities.size // 21, CellType.HEXAHEDRON)
            cells = np.hstack(elementHexa20Connectivities)
            meshHexa20 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshHexa20Actor = self.plotter.add_mesh(meshHexa20, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshHexa20Actor[partID] = meshHexa20Actor
        else:
            meshHexa20 = None

        if elementHexa8Connectivities.size != 0:            
            cell_types = np.full(elementHexa8Connectivities.size // 9, CellType.HEXAHEDRON)  # 8 points + 1 for the count            
            cells = np.hstack(elementHexa8Connectivities)
            meshHexa8 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshHexa8Actor : Actor = self.plotter.add_mesh(meshHexa8, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshHexa8Actor[partID] = meshHexa8Actor
        else:
            meshHexa8 = None     

        if elementPenta6Connectivities.size != 0:
            cell_types = np.full(elementPenta6Connectivities.size // 7, CellType.WEDGE)
            cells = np.hstack(elementPenta6Connectivities)
            meshPenta6 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshPenta6Actor = self.plotter.add_mesh(meshPenta6, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshPenta6Actor[partID] = meshPenta6Actor
        else:
            meshPenta6 = None

        if elementTetra10Connectivities.size != 0:
            cell_types = np.full(elementTetra10Connectivities.size // 11, CellType.TETRA)
            cells = np.hstack(elementTetra10Connectivities)
            meshTetra10 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshTetra10Actor = self.plotter.add_mesh(meshTetra10, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshTetra10Actor[partID] = meshTetra10Actor
        else:
            meshTetra10 = None

        if elementTetra4Connectivities.size != 0:
            cell_types = np.full(elementTetra4Connectivities.size // 5, CellType.TETRA)  # 4 points + 1 for the count
            cells = np.hstack(elementTetra4Connectivities)            
            meshTetra4 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)            
            meshTetra4Actor = self.plotter.add_mesh(meshTetra4, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshTetra4Actor[partID] = meshTetra4Actor  
        else:
            meshTetra4 = None
        if meshHexa8 is not None or meshTetra4 is not None or meshPenta6 is not None or meshTetra10 is not None or meshHexa20 is not None:
            self.meshTetra4[partID] = meshTetra4    
            self.meshPenta6[partID] = meshPenta6
            self.meshHexa8[partID] = meshHexa8
            self.meshTetra10[partID] = meshTetra10
            self.meshHexa20[partID] = meshHexa20
            #self.plotter.show()
            return
        

        if elementQuad8Connectivities.size != 0:
            cell_types = np.full(elementQuad8Connectivities.size // 9, CellType.QUAD)
            cells = np.hstack(elementQuad8Connectivities)
            meshQuad8 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshQuad8Actor = self.plotter.add_mesh(meshQuad8, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshQuad8Actor[partID] = meshQuad8Actor
        else:
            meshQuad8 = None

        if elementQuad4Connectivities.size != 0:
            cell_types = np.full(elementQuad4Connectivities.size // 5, CellType.QUAD)  # 4 points + 1 for the count
            cells = np.hstack(elementQuad4Connectivities)
            meshQuad4 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            #self.plotter.add_mesh(meshQuad4, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            #connectivityMap, colorMap = elementManager.GetQuad4ConnectivitieswithVonMisesStress(idtokey,2,8)
            #meshQuad4.cell_data["VonMisesStress"] = colorMap
            #cmap = "rainbow"
            meshQuad4Actor : Actor = self.plotter.add_mesh(meshQuad4, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            #meshQuad4Actor : Actor = self.plotter.add_mesh(meshQuad4, show_edges=True,scalars="VonMisesStress", cmap=cmap)
            self.meshQuad4Actor[partID] = meshQuad4Actor
            # remove meshQuad4
            #self.plotter.remove_actor(meshActor)
        else:
            meshQuad4 = None

        if elementTri6Connectivities.size != 0:
            cell_types = np.full(elementTri6Connectivities.size // 7, CellType.TRIANGLE)
            cells = np.hstack(elementTri6Connectivities)
            meshTri6 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshTri6Actor : Actor = self.plotter.add_mesh(meshTri6, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshTri6Actor[partID] = meshTri6Actor
        else:
            meshTri6 = None

        if elementTri3Connectivities.size != 0:
            cell_types = np.full(elementTri3Connectivities.size // 4, CellType.TRIANGLE)  # 3 points + 1 for the count
            cells = np.hstack(elementTri3Connectivities)
            meshTri3 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)            
            meshTri3Actor : Actor = self.plotter.add_mesh(meshTri3, show_edges=True,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshTri3Actor[partID] = meshTri3Actor

        else:
            meshTri3 = None
        if meshQuad4 is not None or meshTri3 is not None or meshTri6 is not None or meshQuad8 is not None:
            self.meshTri3[partID] = meshTri3
            self.meshQuad4[partID] = meshQuad4            
            self.meshTri6[partID] = meshTri6
            self.meshQuad8[partID] = meshQuad8
            #self.plotter.show()
            return
        
        if elementLine3Connectivities.size != 0:             
            cell_types = np.full(elementLine3Connectivities.size // 4, CellType.LINE)  # 3 points + 1 for the count
            cells = np.hstack(elementLine3Connectivities)
            meshLine3 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshLine3Actor : Actor = self.plotter.add_mesh(meshLine3, show_edges=True,line_width=2,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshLine3Actor[partID] = meshLine3Actor
        else:
            meshLine3 = None
        if elementLine2Connectivities.size != 0:
            cell_types = np.full(elementLine2Connectivities.size // 3, CellType.LINE)
            cells = np.hstack(elementLine2Connectivities)
            meshLine2 = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            meshLine2Actor : Actor = self.plotter.add_mesh(meshLine2, show_edges=True,line_width=2,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))          
            self.meshLine2Actor[partID] = meshLine2Actor
        else:
            meshLine2 = None
        if meshLine3 is not None or meshLine2 is not None:
            self.meshLine2[partID] = meshLine2
            self.meshLine3[partID] = meshLine3            
            #self.plotter.show()
            return
        
        if elementPointConnectivities.size != 0:
            cell_types = np.full(elementPointConnectivities.size // 2, CellType.VERTEX)
            cells = np.hstack(elementPointConnectivities)
            meshPoint = pv.UnstructuredGrid(cells, cell_types, nodalCoordinates)
            self.plotter.add_mesh(meshPoint, show_edges=True,line_width=2,color=(self.cx[colorid],self.cy[colorid],self.cz[colorid]))
            self.meshPoint = meshPoint
        
        #self.plotter.show()
        
    def UpdateParts(self, nodeManager : NodeManager, partManager : KooPartManager, deformed = False, option = "ut", ithStep = 0):
        self.plotter.clear()
        self.meshLine2 = {}
        self.meshLine3 = {}
        self.meshTri3 = {}
        self.meshTri6 = {}
        self.meshQuad4 = {}
        self.meshQuad8 = {}
        self.meshTetra4 = {}
        self.meshTetra10 = {}
        self.meshPenta6 = {}
        self.meshHexa8 = {}
        self.meshHexa20 = {}
        
        
        numPart = 0
        partIDList = []
        partNameList = []
        for part in partManager.parts.values():
            elementManager : ElementManager = part.elementManager
            partID = part.id
            if deformed == True:
                self.Update(nodeManager, elementManager, partID, True, False, deformed, option, ithStep)
            else:
                self.Update(nodeManager, elementManager, partID, True, False, deformed)
            numPart += 1
            partIDList.append(partID)
            partNameList.append(part.name)
        
        self.importedDataTable.setRowCount(numPart)
        self.checkedViewList = [True for i in range(numPart)]
        for i in range(numPart):
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            # connect checkbox to function
            checkbox.stateChanged.connect(self.on_selection_changed_checkbox_view)
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(checkbox)
            cell_layout.setAlignment(checkbox,Qt.AlignmentFlag.AlignCenter)
            cell_layout.setContentsMargins(0,0,0,0)
            cell_widget.setLayout(cell_layout)
            #part_name_widget = QLabel(f"Part {partIDList[i]}")
            part_name_widget = QLabel(f"{partNameList[i]}")
            self.importedDataTable.setCellWidget(i,0,part_name_widget)
            self.importedDataTable.setCellWidget(i,1,cell_widget)
    
    def UpdateNodalColor(self, Option="ut", ithStep=0):
        for partID in self.partManager.parts.keys():
            self.UpdateNodalColorPart(partID, Option, ithStep)
    
    def UpdateElementColor(self, Option="SXX", intpt = 0, ithStep = 0):
        for partID in self.partManager.parts.keys():
            self.UpdateElementColorPart(partID, Option, intpt, ithStep)    
    
    def ResetElementColor(self,Option="ut", ithStep=0,deformed=False):
        self.plotter.clear()
        self.meshLine2 = {}
        self.meshLine3 = {}
        self.meshTri3 = {}
        self.meshTri6 = {} 
        self.meshQuad4 = {}
        self.meshQuad8 = {}
        self.meshTetra4 = {}
        self.meshTetra10 = {}
        self.meshPenta6 = {}        
        self.meshHexa8 = {}
        self.meshHexa20 = {} 

        self.meshLine2Actor = {}
        self.meshLine3Actor = {}
        self.meshTri3Actor = {}
        self.meshTri6Actor = {}
        self.meshQuad4Actor = {} 
        self.meshQuad8Actor = {}        
        self.meshTetra4Actor = {}
        self.meshTetra10Actor = {}        
        self.meshPenta6Actor = {}
        self.meshHexa8Actor = {} 
        self.meshHexa20Actor = {}
        self.UpdateParts(self.nodeManager, self.partManager, deformed, Option, ithStep)        
        
    
    def UpdateNodalColorManual(self, Option="ut", ithStep=0):
        self.ResetElementColor(Option,ithStep,True)
        self.UpdateNodalColor(Option, ithStep)
        self.plotter.show()
        pass
        
    def UpdateElementColorManual(self, Option="SXX", intpt = 0, ithStep = 0):
        self.ResetElementColor(Option,ithStep,False)
        self.UpdateElementColor(Option, intpt, ithStep)
    
    def UpdateNodalColorPart(self, partID, Option="ut", ithStep=0):
        nodeManager : NodeManager = self.partManager.parts[partID].nodeManager
        if Option == "ut":
            colorMap = nodeManager.GetTotalDisplacement(ithStep)
        elif Option == "ux":
            colorMap = nodeManager.GetDisplacementX(ithStep)
        elif Option == "uy":
            colorMap = nodeManager.GetDisplacementY(ithStep)
        elif Option == "uz":
            colorMap = nodeManager.GetDisplacementZ(ithStep)
        else:
            colorMap = None
        if colorMap is None:
            return 
        maxColor = 0.0
        minColor = 0.0 
        if self.checkBoxManualRange.isChecked():
            # get value from self.editBoxMaxColor
            if self.editBoxMaxColor.text() == "":
                maxColor = np.max(colorMap)
            else:
                maxColor = float(self.editBoxMaxColor.text())
            if self.editBoxMinColor.text() == "":
                minColor = np.min(colorMap)
            else:
                minColor = float(self.editBoxMinColor.text())
        else:
            maxColor = np.max(colorMap)
            minColor = np.min(colorMap)
            # x.xxE+xx form
            maxColorStr = "{:.2e}".format(maxColor)
            minColorStr = "{:.2e}".format(minColor)
            self.editBoxMaxColor.setText(maxColorStr)
            self.editBoxMinColor.setText(minColorStr)
            
        if partID in self.meshTri3Actor.keys():
            self.plotter.remove_actor(self.meshTri3Actor[partID])            
            self.meshTri3[partID].point_data["TotalDisp"] = colorMap
            cmap = "rainbow"
            self.meshTri3Actor[partID] = None
            self.meshTri3Actor[partID] = self.plotter.add_mesh(self.meshTri3[partID], scalars="TotalDisp", cmap=cmap, show_scalar_bar=True, show_edges=True,clim=[minColor, maxColor])
            
        
        if partID in self.meshQuad4Actor.keys():
            self.plotter.remove_actor(self.meshQuad4Actor[partID])            
            self.meshQuad4[partID].point_data["TotalDisp"] = colorMap
            cmap = "rainbow"
            self.meshQuad4Actor[partID] = None
            self.meshQuad4Actor[partID] = self.plotter.add_mesh(self.meshQuad4[partID], scalars="TotalDisp", cmap=cmap, show_scalar_bar=True, show_edges=True,clim=[minColor, maxColor])
                    
        if partID in self.meshTetra4Actor.keys():
            self.plotter.remove_actor(self.meshTetra4Actor[partID])            
            self.meshTetra4[partID].point_data["TotalDisp"] = colorMap
            cmap = "rainbow"
            self.meshTetra4Actor[partID] = None
            self.meshTetra4Actor[partID] = self.plotter.add_mesh(self.meshTetra4[partID], scalars="TotalDisp", cmap=cmap, show_scalar_bar=True, show_edges=True,clim=[minColor, maxColor])
            
        if partID in self.meshTetra10Actor.keys():
            self.plotter.remove_actor(self.meshTetra10Actor[partID])            
            self.meshTetra10[partID].point_data["TotalDisp"] = colorMap
            cmap = "rainbow"
            self.meshTetra10Actor[partID] = None
            self.meshTetra10Actor[partID] = self.plotter.add_mesh(self.meshTetra10[partID], scalars="TotalDisp", cmap=cmap, show_scalar_bar=True, show_edges=True,clim=[minColor, maxColor])
        
        if partID in self.meshPenta6Actor.keys():
            self.plotter.remove_actor(self.meshPenta6Actor[partID])            
            self.meshPenta6[partID].point_data["TotalDisp"] = colorMap
            cmap = "rainbow"
            self.meshPenta6Actor[partID] = None
            self.meshPenta6Actor[partID] = self.plotter.add_mesh(self.meshPenta6[partID], scalars="TotalDisp", cmap=cmap, show_scalar_bar=True, show_edges=True,clim=[minColor, maxColor])
            
        if partID in self.meshHexa8Actor.keys():
            self.plotter.remove_actor(self.meshHexa8Actor[partID])            
            self.meshHexa8[partID].point_data["TotalDisp"] = colorMap
            cmap = "rainbow"
            self.meshHexa8Actor[partID] = None
            self.meshHexa8Actor[partID] = self.plotter.add_mesh(self.meshHexa8[partID], scalars="TotalDisp", cmap=cmap, show_scalar_bar=True, show_edges=True,clim=[minColor, maxColor])
        
        if partID in self.meshHexa20Actor.keys():
            self.plotter.remove_actor(self.meshHexa20Actor[partID])            
            self.meshHexa20[partID].point_data["TotalDisp"] = colorMap
            cmap = "rainbow"
            self.meshHexa20Actor[partID] = None
            self.meshHexa20Actor[partID] = self.plotter.add_mesh(self.meshHexa20[partID], scalars="TotalDisp", cmap=cmap, show_scalar_bar=True, show_edges=True,clim=[minColor, maxColor])
             
    def UpdateElementColorPart(self, partID,Option="VonMisesStress", ipt=1, ithStep=1):        
        if partID in self.meshTri3.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            if Option == "VonMisesStress":
                colorMapTri3 = elementManager.GetTri3VonMisesStresses(ipt, ithStep)
            elif Option == "SXX":
                colorMapTri3 = elementManager.GetTri3StressXX(ipt, ithStep)
            elif Option == "SYY":
                colorMapTri3 = elementManager.GetTri3StressYY(ipt, ithStep)
            elif Option == "SXY":
                colorMapTri3 = elementManager.GetTri3StressXY(ipt, ithStep)            
            else:
                colorMapTri3 = None
    
            
            if colorMapTri3 is not None and colorMapTri3.size != 0:
                if self.meshTri3[partID] is not None:
                    maxColor = 0.0
                    minColor = 0.0
                    if self.checkBoxManualRange.isChecked():
                        if self.editBoxMaxColor.text() == "":
                            maxColor = np.max(colorMapTri3)
                        else:
                            maxColor = float(self.editBoxMaxColor.text())
                        if self.editBoxMinColor.text() == "":
                            minColor = np.min(colorMapTri3)
                        else:
                            minColor = float(self.editBoxMinColor.text())
                    else:
                        maxColor = np.max(colorMapTri3)
                        minColor = np.min(colorMapTri3)
                        maxColorStr = "{:.2e}".format(maxColor)
                        minColorStr = "{:.2e}".format(minColor)
                        self.editBoxMaxColor.setText(maxColorStr)
                        self.editBoxMinColor.setText(minColorStr)   
                    self.plotter.remove_actor(self.meshTri3Actor[partID])
                    self.meshTri3[partID].cell_data["VonMisesStress"] = colorMapTri3
                    cmap = "rainbow"
                    self.meshTri3Actor[partID] = None
                    self.meshTri3Actor[partID] = self.plotter.add_mesh(self.meshTri3[partID], scalars="VonMisesStress", cmap=cmap, show_edges=True, clim=[minColor, maxColor])
        if partID in self.meshQuad4.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            if Option == "VonMisesStress":
                colorMapQuad4 = elementManager.GetQuad4VonMisesStresses(ipt, ithStep)
            elif Option == "SXX":
                colorMapQuad4 = elementManager.GetQuad4StressXX(ipt, ithStep)
            elif Option == "SYY":
                colorMapQuad4 = elementManager.GetQuad4StressYY(ipt, ithStep)
            elif Option == "SXY":
                colorMapQuad4 = elementManager.GetQuad4StressXY(ipt, ithStep)            
            else:
                colorMapQuad4 = None
                            
            if colorMapQuad4 is not None and colorMapQuad4.size != 0:
                if self.meshQuad4[partID] is not None:
                    maxColor = 0.0
                    minColor = 0.0
                    if self.checkBoxManualRange.isChecked():
                        if self.editBoxMaxColor.text() == "":
                            maxColor = np.max(colorMapQuad4)
                        else:
                            maxColor = float(self.editBoxMaxColor.text())
                        if self.editBoxMinColor.text() == "":
                            minColor = np.min(colorMapQuad4)
                        else:
                            minColor = float(self.editBoxMinColor.text())
                    else:
                        maxColor = np.max(colorMapQuad4)
                        minColor = np.min(colorMapQuad4)
                        maxColorStr = "{:.2e}".format(maxColor)
                        minColorStr = "{:.2e}".format(minColor)
                        self.editBoxMaxColor.setText(maxColorStr)
                        self.editBoxMinColor.setText(minColorStr)
                    self.plotter.remove_actor(self.meshQuad4Actor[partID])
                    self.meshQuad4[partID].cell_data["VonMisesStress"] = colorMapQuad4
                    cmap = "rainbow"
                    self.meshQuad4Actor[partID] = None
                    self.meshQuad4Actor[partID] = self.plotter.add_mesh(self.meshQuad4[partID], scalars="VonMisesStress", cmap=cmap, show_edges=True, clim=[minColor, maxColor])
        if partID in self.meshTetra4.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            if Option == "VonMisesStress":
                colorMapTetra4 = elementManager.GetTetra4VonMisesStresses(ipt, ithStep)
            elif Option == "SXX":
                colorMapTetra4 = elementManager.GetTetra4StressXX(ipt, ithStep)
            elif Option == "SYY":
                colorMapTetra4 = elementManager.GetTetra4StressYY(ipt, ithStep)
            elif Option == "SZZ":
                colorMapTetra4 = elementManager.GetTetra4StressZZ(ipt, ithStep)
            elif Option == "SXY":
                colorMapTetra4 = elementManager.GetTetra4StressXY(ipt, ithStep)            
            elif Option == "SYZ":
                colorMapTetra4 = elementManager.GetTetra4StressYZ(ipt, ithStep)
            elif Option == "SXZ":
                colorMapTetra4 = elementManager.GetTetra4StressXZ(ipt, ithStep)                
            else:
                colorMapTetra4 = None
                
            if colorMapTetra4 is not None and colorMapTetra4.size != 0:
                if self.meshTetra4[partID] is not None:
                    maxColor = 0.0
                    minColor = 0.0
                    if self.checkBoxManualRange.isChecked():
                        if self.editBoxMaxColor.text() == "":
                            maxColor = np.max(colorMapTetra4)
                        else:
                            maxColor = float(self.editBoxMaxColor.text())
                        if self.editBoxMinColor.text() == "":
                            minColor = np.min(colorMapTetra4)
                        else:
                            minColor = float(self.editBoxMinColor.text())
                    else:
                        maxColor = np.max(colorMapTetra4)
                        minColor = np.min(colorMapTetra4)
                        maxColorStr = "{:.2e}".format(maxColor)
                        minColorStr = "{:.2e}".format(minColor)
                        self.editBoxMaxColor.setText(maxColorStr)
                        self.editBoxMinColor.setText(minColorStr)
                        
                    self.plotter.remove_actor(self.meshTetra4Actor[partID])
                    self.meshTetra4[partID].cell_data["VonMisesStress"] = colorMapTetra4
                    cmap = "rainbow"
                    self.meshTetra4Actor[partID] = None
                    self.meshTetra4Actor[partID] = self.plotter.add_mesh(self.meshTetra4[partID], scalars="VonMisesStress", cmap=cmap, show_edges=True, clim=[minColor, maxColor])
        if partID in self.meshTetra10.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            if Option == "VonMisesStress":
                colorMapTetra10 = elementManager.GetTetra10VonMisesStresses(ipt, ithStep)
            elif Option == "SXX":
                colorMapTetra10 = elementManager.GetTetra10StressXX(ipt, ithStep)
            elif Option == "SYY":
                colorMapTetra10 = elementManager.GetTetra10StressYY(ipt, ithStep)
            elif Option == "SZZ":
                colorMapTetra10 = elementManager.GetTetra10StressZZ(ipt, ithStep)
            elif Option == "SXY":
                colorMapTetra10 = elementManager.GetTetra10StressXY(ipt, ithStep)            
            elif Option == "SYZ":
                colorMapTetra10 = elementManager.GetTetra10StressYZ(ipt, ithStep)
            elif Option == "SXZ":
                colorMapTetra10 = elementManager.GetTetra10StressXZ(ipt, ithStep)                
            else:
                colorMapTetra10 = None
                
            if colorMapTetra10 is not None and colorMapTetra10.size != 0:
                if self.meshTetra10[partID] is not None:
                    maxColor = 0.0
                    minColor = 0.0
                    if self.checkBoxManualRange.isChecked():
                        if self.editBoxMaxColor.text() == "":
                            maxColor = np.max(colorMapTetra10)
                        else:
                            maxColor = float(self.editBoxMaxColor.text())
                        if self.editBoxMinColor.text() == "":
                            minColor = np.min(colorMapTetra10)
                        else:
                            minColor = float(self.editBoxMinColor.text())
                    else:
                        maxColor = np.max(colorMapTetra10)
                        minColor = np.min(colorMapTetra10)
                        maxColorStr = "{:.2e}".format(maxColor)
                        minColorStr = "{:.2e}".format(minColor)
                        self.editBoxMaxColor.setText(maxColorStr)
                        self.editBoxMinColor.setText(minColorStr)
                    self.plotter.remove_actor(self.meshTetra10Actor[partID])
                    self.meshTetra10[partID].cell_data["VonMisesStress"] = colorMapTetra10
                    cmap = "rainbow"
                    self.meshTetra10Actor[partID] = None
                    self.meshTetra10Actor[partID] = self.plotter.add_mesh(self.meshTetra10[partID], scalars="VonMisesStress", cmap=cmap, show_edges=True, clim=[minColor, maxColor])
        if partID in self.meshPenta6.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            if Option == "VonMisesStress":
                colorMapPenta6 = elementManager.GetPenta6VonMisesStresses(ipt, ithStep)
            elif Option == "SXX":
                colorMapPenta6 = elementManager.GetPenta6StressXX(ipt, ithStep)
            elif Option == "SYY":
                colorMapPenta6 = elementManager.GetPenta6StressYY(ipt, ithStep)
            elif Option == "SZZ":
                colorMapPenta6 = elementManager.GetPenta6StressZZ(ipt, ithStep)
            elif Option == "SXY":
                colorMapPenta6 = elementManager.GetPenta6StressXY(ipt, ithStep)            
            elif Option == "SYZ":
                colorMapPenta6 = elementManager.GetPenta6StressYZ(ipt, ithStep)
            elif Option == "SXZ":
                colorMapPenta6 = elementManager.GetPenta6StressXZ(ipt, ithStep)                
            else:
                colorMapPenta6 = None
                
            if colorMapPenta6 is not None and colorMapPenta6.size != 0:
                if self.meshPenta6[partID] is not None:
                    maxColor = 0.0
                    minColor = 0.0
                    if self.checkBoxManualRange.isChecked():
                        if self.editBoxMaxColor.text() == "":
                            maxColor = np.max(colorMapPenta6)
                        else:
                            maxColor = float(self.editBoxMaxColor.text())
                        if self.editBoxMinColor.text() == "":
                            minColor = np.min(colorMapPenta6)
                        else:
                            minColor = float(self.editBoxMinColor.text())
                    else:
                        maxColor = np.max(colorMapPenta6)
                        minColor = np.min(colorMapPenta6)
                        maxColorStr = "{:.2e}".format(maxColor)
                        minColorStr = "{:.2e}".format(minColor)
                        self.editBoxMaxColor.setText(maxColorStr)
                        self.editBoxMinColor.setText(minColorStr)
                    self.plotter.remove_actor(self.meshPenta6Actor[partID])
                    self.meshPenta6[partID].cell_data["VonMisesStress"] = colorMapPenta6
                    cmap = "rainbow"
                    self.meshPenta6Actor[partID] = None
                    self.meshPenta6Actor[partID] = self.plotter.add_mesh(self.meshPenta6[partID], scalars="VonMisesStress", cmap=cmap, show_edges=True, clim=[minColor, maxColor])
        if partID in self.meshHexa8.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            if Option == "VonMisesStress":
                colorMapHexa8 = elementManager.GetHexa8VonMisesStresses(ipt, ithStep)
            elif Option == "SXX":
                colorMapHexa8 = elementManager.GetHexa8StressXX(ipt, ithStep)
            elif Option == "SYY":
                colorMapHexa8 = elementManager.GetHexa8StressYY(ipt, ithStep)
            elif Option == "SZZ":
                colorMapHexa8 = elementManager.GetHexa8StressZZ(ipt, ithStep)
            elif Option == "SXY":
                colorMapHexa8 = elementManager.GetHexa8StressXY(ipt, ithStep)            
            elif Option == "SYZ":
                colorMapHexa8 = elementManager.GetHexa8StressYZ(ipt, ithStep)
            elif Option == "SXZ":
                colorMapHexa8 = elementManager.GetHexa8StressXZ(ipt, ithStep)                
            else:
                colorMapHexa8 = None
            
            if colorMapHexa8 is not None and colorMapHexa8.size != 0:
                if self.meshHexa8[partID] is not None:
                    maxColor = 0.0
                    minColor = 0.0
                    if self.checkBoxManualRange.isChecked():
                        if self.editBoxMaxColor.text() == "":
                            maxColor = np.max(colorMapHexa8)
                        else:
                            maxColor = float(self.editBoxMaxColor.text())
                        if self.editBoxMinColor.text() == "":
                            minColor = np.min(colorMapHexa8)
                        else:
                            minColor = float(self.editBoxMinColor.text())
                    else:
                        maxColor = np.max(colorMapHexa8)
                        minColor = np.min(colorMapHexa8)
                        maxColorStr = "{:.2e}".format(maxColor)
                        minColorStr = "{:.2e}".format(minColor)
                        self.editBoxMaxColor.setText(maxColorStr)
                        self.editBoxMinColor.setText(minColorStr)
                    
                    self.plotter.remove_actor(self.meshHexa8Actor[partID])
                    self.meshHexa8[partID].cell_data["VonMisesStress"] = colorMapHexa8
                    cmap = "rainbow"
                    self.meshHexa8Actor[partID] = None
                    self.meshHexa8Actor[partID] = self.plotter.add_mesh(self.meshHexa8[partID], scalars="VonMisesStress", cmap=cmap, show_edges=True, clim=[minColor, maxColor])
        if partID in self.meshHexa20.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            if Option == "VonMisesStress":
                colorMapHexa20 = elementManager.GetHexa20VonMisesStresses(ipt, ithStep)
            elif Option == "SXX":
                colorMapHexa20 = elementManager.GetHexa20StressXX(ipt, ithStep)
            elif Option == "SYY":
                colorMapHexa20 = elementManager.GetHexa20StressYY(ipt, ithStep)
            elif Option == "SZZ":
                colorMapHexa20 = elementManager.GetHexa20StressZZ(ipt, ithStep)
            elif Option == "SXY":
                colorMapHexa20 = elementManager.GetHexa20StressXY(ipt, ithStep)            
            elif Option == "SYZ":
                colorMapHexa20 = elementManager.GetHexa20StressYZ(ipt, ithStep)
            elif Option == "SXZ":
                colorMapHexa20 = elementManager.GetHexa20StressXZ(ipt, ithStep)                
            else:
                colorMapHexa20 = None
                            
            if colorMapHexa20 is not None and colorMapHexa20.size != 0:
                if self.meshHexa20[partID] is not None:
                    maxColor = 0.0
                    minColor = 0.0
                    if self.checkBoxManualRange.isChecked():
                        if self.editBoxMaxColor.text() == "":
                            maxColor = np.max(colorMapHexa20)
                        else:
                            maxColor = float(self.editBoxMaxColor.text())
                        if self.editBoxMinColor.text() == "":
                            minColor = np.min(colorMapHexa20)
                        else:
                            minColor = float(self.editBoxMinColor.text())
                    else:
                        maxColor = np.max(colorMapHexa20)
                        minColor = np.min(colorMapHexa20)
                        maxColorStr = "{:.2e}".format(maxColor)
                        minColorStr = "{:.2e}".format(minColor)
                        self.editBoxMaxColor.setText(maxColorStr)
                        self.editBoxMinColor.setText(minColorStr)
                    self.plotter.remove_actor(self.meshHexa20Actor[partID])
                    self.meshHexa20[partID].cell_data["VonMisesStress"] = colorMapHexa20
                    cmap = "rainbow"
                    self.meshHexa20Actor[partID] = None
                    self.meshHexa20Actor[partID] = self.plotter.add_mesh(self.meshHexa20[partID], scalars="VonMisesStress", cmap=cmap, show_edges=True, clim=[minColor, maxColor])                
    
    def UpdateColorVonMisesStress(self):
        nodeManager = self.nodeManager
        #idtokey, nodalCoordinates = nodeManager.GetNodalCoordinates()
        for partID in self.meshTri3.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            colorMapTri3 = elementManager.GetTri3VonMisesStresses(1,1)
            if colorMapTri3.size != 0:
                self.plotter.remove_actor(self.meshTri3Actor[partID])
                mesh = self.meshTri3[partID]
                mesh.cell_data["VonMisesStress"] = colorMapTri3
                cmap = "rainbow"            
                self.meshTri3Actor[partID] = self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)
        for partID in self.meshQuad4.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            colorMapQuad4 = elementManager.GetQuad4VonMisesStresses(1,1)
            if colorMapQuad4.size != 0:
                self.plotter.remove_actor(self.meshQuad4Actor[partID])
                mesh = self.meshQuad4[partID]
                mesh.cell_data["VonMisesStress"] = colorMapQuad4
                cmap = "rainbow"
                self.meshQuad4Actor[partID] = self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)
        
        for partID in self.meshTetra4.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            colorMapTetra4 = elementManager.GetTetra4VonMisesStresses(1,1)
            if colorMapTetra4.size != 0:
                self.plotter.remove_actor(self.meshTetra4Actor[partID])
                mesh = self.meshTetra4[partID]
                mesh.cell_data["VonMisesStress"] = colorMapTetra4
                cmap = "rainbow"
                self.meshTetra4Actor[partID] = self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)
                        
        for partID in self.meshTetra10.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            colorMapTetra10 = elementManager.GetTetra10VonMisesStresses(1,1)
            if colorMapTetra10.size != 0:
                self.plotter.remove_actor(self.meshTetra10Actor[partID])
                mesh = self.meshTetra10[partID]
                mesh.cell_data["VonMisesStress"] = colorMapTetra10
                cmap = "rainbow"
                self.meshTetra10Actor[partID] = self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)
       
        for partID in self.meshPenta6.keys():
            elementManager : ElementManager = self.partManager.parts[partID].elementManager
            colorMapPenta6 = elementManager.GetPenta6VonMisesStresses(1,1)
            if colorMapPenta6.size != 0:
                self.plotter.remove_actor(self.meshPenta6Actor[partID])
                mesh = self.meshPenta6[partID]
                mesh.cell_data["VonMisesStress"] = colorMapPenta6
                cmap = "rainbow"
                self.meshPenta6Actor[partID] = self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)

        for partID in self.meshHexa8.keys():
            elementManager = self.partManager.parts[partID].elementManager
            colorMapHexa8 = elementManager.GetHexa8VonMisesStresses(1,1)
            if colorMapHexa8.size != 0:
                self.plotter.remove_actor(self.meshHexa8Actor[partID])
                mesh = self.meshHexa8[partID]
                mesh.cell_data["VonMisesStress"] = colorMapHexa8
                cmap = "rainbow"
                self.meshHexa8Actor[partID] = self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)

        for partID in self.meshHexa20.keys():
            elementManager = self.partManager.parts[partID].elementManager
            colorMapHexa20 = elementManager.GetHexa20VonMisesStresses(1,1)
            if colorMapHexa20.size != 0:
                self.plotter.remove_actor(self.meshHexa20Actor[partID])
                mesh = self.meshHexa20[partID]
                mesh.cell_data["VonMisesStress"] = colorMapHexa20
                cmap = "rainbow"
                self.meshHexa20Actor[partID] = self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)
        
    
    
    

        '''
        for part in self.partManager.parts.values():
            elementManager : ElementManager = part.elementManager
            partID = part.id            
            colorMapTri3 = elementManager.GetTri3VonMisesStresses(1,1)
            colorMapQuad4 = elementManager.GetQuad4VonMisesStresses(1,1)
            colorMapTetra4 = elementManager.GetTetra4VonMisesStresses(1,1)
            colorMapHexa8 = elementManager.GetHexa8VonMisesStresses(1,1)

            if colorMapTri3.size != 0:
                if partID in self.meshTri3.keys():
                    mesh = self.meshTri3[partID]
                    mesh.cell_data["VonMisesStress"] = colorMapTri3
                    cmap = "rainbow"
                    self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)    
            if colorMapQuad4.size != 0:
                if partID in self.meshQuad4.keys():
                    mesh = self.meshQuad4[partID]
                    mesh.cell_data["VonMisesStress"] = colorMapQuad4
                    cmap = "rainbow"
                    self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)
            if colorMapTetra4.size != 0:
                if partID in self.meshTetra4.keys():
                    mesh = self.meshTetra4[partID]
                    mesh.cell_data["VonMisesStress"] = colorMapTetra4
                    cmap = "rainbow"
                    self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)
            if colorMapHexa8.size != 0:
                if partID in self.meshHexa8.keys():
                    mesh = self.meshHexa8[partID]
                    mesh.cell_data["VonMisesStress"] = colorMapHexa8
                    cmap = "rainbow"
                    self.plotter.add_mesh(mesh, scalars="VonMisesStress", cmap=cmap)

        '''
            

                   





if __name__ == "__main__":
    
    
    mode = "ImportGMSH"
    mode = "ImportLSDyna"    
    import os
    app = QApplication(sys.argv)
    path = os.getcwd()


    nodoutPath = None
    eloutPath = None

    if mode == "ImportGMSH": 
        nodeManager : NodeManager = NodeManager() 
        elementManager : ElementManager = ElementManager(nodeManager)
        elementManager.elementManagerID = 10
        #path = os.path.join(path,'Example\\Model\\New_Model_1\\Solid3\\Solid3.msh') 
        #path = os.path.join(path,'Example\\FacemshExample.msh') 
        #path = os.path.join(path,'Example\\FacemshExample3_result.msh')
        #path = os.path.join(path, "PackageMesh\\PolynomialPartMesh1.msh")
        path = os.path.join(path, "PackageMesh\\PolynomialCutPartMesh1.msh")
        importer = KooMSHImporter()
        importer.import_msh_file(path)
        importer.SetUpdateManager(nodeManager, elementManager)
        importer.UpdateManager()
        window = PostWindow(nodeManager, None, elementManager)
        window.Update()
    elif mode == "ImportLSDyna":
        modelMode = "Taylor"    
        modelMode = "Composite"
        modelMode = "3PTBendingTest"
        modelMode = "Test_GeneratedMesh"
        modelMode = "DisplayImpactSolid"
        modelMode = "3ptBendingDOE"
        modelMode = "PeriDynamics"
        
        path = os.getcwd()
        if modelMode == "Taylor":
            newdir = "OpenRadioss\\examples\\taylor_A.k"
            path = os.path.join(path, "OpenRadioss\\examples\\taylor_A.k\\taylor_A.k")
        elif modelMode == "Composite":            
            newdir = "OpenRadioss\\examples\\Composite"
            path = os.path.join(path, "OpenRadioss\\examples\\Composite\\test_laminate.k")
            eloutPath = os.path.join(path,"elout")
        elif modelMode == "3PTBendingTest":
            newdir = "OpenRadioss\\examples\\Udemy_LSDYNA\\3 pt bending test\\test_ascii"            
            folder = os.path.join(path, "OpenRadioss\\examples\\Udemy_LSDYNA\\3 pt bending test\\test_ascii")
            path = os.path.join(path, "OpenRadioss\\examples\\Udemy_LSDYNA\\3 pt bending test\\test_ascii\\3ptBending_asciioutput.k")
            nodoutPath = os.path.join(folder,"nodout")
            eloutPath = os.path.join(folder,"elout")
        elif modelMode == "Test_GeneratedMesh":
            newdir = "occProject\\Generators\\dist\\DisplayImpact2"
            folder = os.path.join(path, newdir)
            path = os.path.join(folder,"PackageInfoBoxMeshCompositeMaterial.k")
        elif modelMode == "DisplayImpactSolid":
            newdir = "occProject\\Generators\\dist\\DisplayImpactSolid\\3ptBending_1_00000001"
            folder = os.path.join(path, newdir)
            path = os.path.join(folder,"3ptBending_1_00000001.k")
        elif modelMode == "PeriDynamics":
            newdir = "occProject\\Generators\\dist\\DisplayImpactBall\\crackresult_peri_goodconvergence"
            folder = os.path.join(path, newdir)
            path = os.path.join(folder,"Impact_1_00000001.k")
        elif modelMode == "3ptBendingDOE":
            newdir = "OpenRadioss\\examples\\Udemy_LSDYNA\\3 pt bending test\\test_DOE\\3ptBending_1_00000001"    
            folder = os.path.join(path, newdir)
            path = os.path.join(folder,"3ptBending_1_00000001.k")        
            
        
        os.chdir(newdir)
        nodeManager : NodeManager = NodeManager()
        partManager : KooPartManager = KooPartManager()
        importer = KooDynaImporter(nodeManager,partManager)
        resultMan : KooResultManager = KooResultManager(nodeManager)
        importer.importDynaFile(path)                

        importer.importNode()
        importer.importPart()
        if nodoutPath is not None:
            importer.importNODOUT(nodoutPath)
        if eloutPath is not None:
            importer.importELOUT(eloutPath)
        
        window = PostWindow(nodeManager, partManager)
        window.setFolderPath = os.path.dirname(path)
        window.importer = importer
        if nodoutPath is None and eloutPath is None:
            window.UpdateParts(nodeManager,partManager)
        else:

            maxDisp = nodeManager.MaxDisplacement()[1]
            minDisp = nodeManager.MinDisplacement()[1]
            maxDispX = nodeManager.MaxDisplacementX()[1]
            minDispX = nodeManager.MinDisplacementX()[1]
            maxDispY = nodeManager.MaxDisplacementY()[1]
            minDispY = nodeManager.MinDisplacementY()[1]
            maxDispZ = nodeManager.MaxDisplacementZ()[1]
            minDispZ = nodeManager.MinDisplacementZ()[1]
            print("Max Displacement: ", maxDisp)
            print("Min Displacement: ", minDisp)
            print("Max Displacement X: ", maxDispX)
            print("Min Displacement X: ", minDispX)
            print("Max Displacement Y: ", maxDispY)
            print("Min Displacement Y: ", minDispY)
            print("Max Displacement Z: ", maxDispZ)
            print("Min Displacement Z: ", minDispZ)

            for part in partManager.parts.values():
                elementManager : ElementManager = part.elementManager
                vonMises = elementManager.GetMaximumVonMisesStress()
                principal = elementManager.GetMaximumPrincipalStress()
                hydroStatic = elementManager.GetMaximumHydrostaticStress()
                print("Part ID: ", part.id)
                print("Max Von Mises Stress: ", vonMises)
                print("Max Principal Stress: ", principal)
                print("Max Hydrostatic Stress: ", hydroStatic)

            window.UpdateColorVonMisesStress()
            window.UpdateAllParts()
   

    sys.exit(app.exec_())
