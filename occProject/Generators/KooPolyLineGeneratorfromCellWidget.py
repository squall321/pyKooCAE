import sys
from os.path import join
from PyQt5 import QtGui 

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QDockWidget, QWidget, QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog
from PyQt5.QtGui import QKeySequence, QBrush, QColor
from KooODBCADManager.ODBCADManager import ODBCADManager
from KooODBCADManager.ODBPPImporter import ODBPPImporter
class KooPolyLineGeneratorfromCellWidget(QWidget):

    def __init__(self, mainWindowFunc, parent=None):
        super(KooPolyLineGeneratorfromCellWidget, self).__init__(parent)
        self.isOpened = True
        self.setMinimumWidth(300)
        self.edgeGroups = {}
        #self.setMaximumWidth(300)
        self.ODBCADManager = ODBCADManager()
        self.ODBImporter = ODBPPImporter()
        self.mainWindowFunc = mainWindowFunc

        self.layout = QVBoxLayout()

        # Label and edit control
        hlayoutSetPosition = QHBoxLayout()
        label = QLabel("Position x1,y1 : ")
        self.editPosition = QLineEdit()
        self.editPosition.setText("0,0")
        hlayoutSetPosition.addWidget(label)
        hlayoutSetPosition.addWidget(self.editPosition)
        #hlayoutSetPosition2 = QHBoxLayout()
        label2 = QLabel("x2,y2 : ")
        self.editPosition2 = QLineEdit()
        self.editPosition2.setText("1,0")
        hlayoutSetPosition.addWidget(label2)
        hlayoutSetPosition.addWidget(self.editPosition2)   
        
        self.layout.addLayout(hlayoutSetPosition)
        #self.layout.addLayout(hlayoutSetPosition2)
        # Add to Table 
        hlayoutAddtoTable = QHBoxLayout()
        self.buttonAddtoTable = QPushButton("Add")
        self.buttonimporttoTable = QPushButton("Import")
        self.buttonAddtoTable.clicked.connect(self.addtoTable)
        self.buttonimporttoTable.clicked.connect(self.importtoTable)
        hlayoutAddtoTable.addWidget(self.buttonAddtoTable)
        hlayoutAddtoTable.addWidget(self.buttonimporttoTable)
        self.layout.addLayout(hlayoutAddtoTable)
        # Table
        self.table = QTableWidget()
        colcount = 8 
        self.table.setColumnCount(colcount)
        self.table.setHorizontalHeaderLabels(["Type","x1", "y1", "x2", "y2", "x3", "y3", "Option"])
        self.table.setColumnWidth(0,50)
        for i in range(1,colcount):
            self.table.setColumnWidth(i,60)
        
        self.layout.addWidget(self.table)
        hlayoutSetTableOption = QHBoxLayout()
        self.buttonRemove = QPushButton("Remove")
        self.buttonUp = QPushButton("Up")
        self.buttonDown = QPushButton("Down")
        self.buttonSort = QPushButton("Sort")
        self.buttonRemove.clicked.connect(self.removeLine)
        self.buttonDown.clicked.connect(self.downLine)
        self.buttonUp.clicked.connect(self.upLine)
        self.buttonSort.clicked.connect(self.sortLines)
        
        hlayoutSetTableOption.addWidget(self.buttonRemove)
        hlayoutSetTableOption.addWidget(self.buttonUp)
        hlayoutSetTableOption.addWidget(self.buttonDown)
        hlayoutSetTableOption.addWidget(self.buttonSort)
        self.layout.addLayout(hlayoutSetTableOption)


        self.button = QPushButton("Update Geometry", self)
        self.button.clicked.connect(self.on_button_click)

        
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            clipboard = QApplication.clipboard()
            data = clipboard.text()
            if not data:
                return 
            rows = data.split("\n")
            row_count = len(rows)
            self.table.clearContents()
            self.table.setRowCount(row_count)
            for row in range(row_count):
                line = rows[row].split("\t")
                col_count = len(line)
                for col in range(col_count):
                    item = QTableWidgetItem(line[col])
                    self.table.setItem(row, col, item)
        else:
            super().keyPressEvent(event)
    
    def addtoTable(self):
        pos1Text = self.editPosition.text()
        pos2Text = self.editPosition2.text()

        pos1 = pos1Text.split(",")
        pos2 = pos2Text.split(",")
        # Add to Table
        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)
        self.table.setItem(rowPosition, 0, QTableWidgetItem("Line"))
        self.table.setItem(rowPosition, 1, QTableWidgetItem(pos1[0]))
        self.table.setItem(rowPosition, 2, QTableWidgetItem(pos1[1]))
        self.table.setItem(rowPosition, 3, QTableWidgetItem(pos2[0]))
        self.table.setItem(rowPosition, 4, QTableWidgetItem(pos2[1]))
        self.table.setItem(rowPosition, 5, QTableWidgetItem(""))
        pass
    
    def importtoTable(self):
        file_Dialog = QFileDialog(self)
        file_path, _ = file_Dialog.getOpenFileName(
            self, "Open Feature File", "", "Text Files (*.txt)"
            )
        if file_path:
            print("Selected file : " , file_path)
            self.importFeatureFile(file_path)
        pass
    
    def importFeatureFile(self,file_path):
        #self.arrayPCB = self.ODBCADManager.load_arrayPCB("",file_path)
        edges = {}
        with open(join("",file_path)) as stream:
            edges = self.ODBImporter.ImportEdgeFeature(stream)
        #print(edges)
        self.table.clearContents()
        
        for i in edges:
            edge = edges[i]
            rowPosition = self.table.rowCount()
            
            #print(edge)
            if len(edge) == 1:
                self.table.insertRow(rowPosition)
                self.table.setItem(rowPosition, 0, QTableWidgetItem("Line"))
            elif len(edge) == 4:
                self.table.insertRow(rowPosition)
                self.table.setItem(rowPosition, 0, QTableWidgetItem("Line"))
            elif len(edge) == 7:
                self.table.insertRow(rowPosition)
                self.table.setItem(rowPosition, 0, QTableWidgetItem("Arc"))
            if len(edge) == 4 or len(edge) == 7:
                for j in range(0,len(edge)):
                    self.table.setItem(rowPosition, j+1, QTableWidgetItem(str(edge[j])))
            elif len(edge) == 1:
                for j in range(0,len(edge[0])):
                    self.table.setItem(rowPosition, j+1, QTableWidgetItem(str(edge[0][j])))
            else:
                for j in range(0,len(edge)):
                    rowPosition = self.table.rowCount()
                    self.table.insertRow(rowPosition)
                    self.table.setItem(rowPosition, 0, QTableWidgetItem("Line"))
                    for k in range(0,len(edge[j])):
                        self.table.setItem(rowPosition, k+1, QTableWidgetItem(str(edge[j][k])))
        pass

    def removeLine(self):
        pass
    def downLine(self):
        pass
    def upLine(self):
        pass
    def sortLines(self):
        edges = self.GetEdgesfromTable()

        newEdgeGroup = []
        print(edges)
        edgeGroup = [] 
        edgeGroup.append(edges[0])
        newEdgeGroup.append(edgeGroup) 
        for i in range(1,len(edges)):
            curEdge = edges[i]
            x1 = curEdge[1]
            y1 = curEdge[2]
            x2 = curEdge[3]
            y2 = curEdge[4]
            isConnected = False
           # print(i,"th Edge")
            for j in range(0,len(newEdgeGroup)):
                prevEdge = newEdgeGroup[j][len(newEdgeGroup[j])-1]
              #  print("PrevEdgeLength :",len(prevEdge))
                x1prev = prevEdge[1]
                y1prev = prevEdge[2]
                x2prev = prevEdge[3]
                y2prev = prevEdge[4]
                if x1 == x2prev and y1 == y2prev:
                    newEdgeGroup[j].append(curEdge)
                    isConnected = True
                    break
                elif x2 == x1prev and y2 == y1prev:
                    newEdgeGroup[j].append(curEdge)
                    isConnected = True
                    break
                elif x1 == x1prev and y1 == y1prev:
                    newEdgeGroup[j].append(curEdge)
                    isConnected = True
                    break
                elif x2 == x2prev and y2 == y2prev:
                    newEdgeGroup[j].append(curEdge)
                    isConnected = True
                    break
            if not isConnected:
                edgeGroup = [] 
                edgeGroup.append(curEdge)
                newEdgeGroup.append(edgeGroup) 
                
        print(len(newEdgeGroup))
        for i in range(0,len(newEdgeGroup)):
            print(len(newEdgeGroup[i]))
        self.edgeGroups = newEdgeGroup



    def GetEdgesfromTable(self):
        edges = {}
        for i in range(0,self.table.rowCount()):
            edge = []
            colSize = self.table.columnCount()
            if self.table.item(i,0) == None:
                colSize = 0 
            elif self.table.item(i,0).text() == "Line":
                colSize = 5
            elif self.table.item(i,0).text() == "Arc":
                colSize = 8
            for j in range(0,colSize):
                #print(j,self.table.item(i,j).text())
                if j == 0:
                    edge.append(self.table.item(i,j).text())
                elif j<7:
                    edge.append(float(self.table.item(i,j).text()))
                elif j == 7:
                    edge.append(int(self.table.item(i,j).text()))
            edges[i] = edge
        return edges
    
    def on_button_click(self):
        # Call the function from MainWindow
        self.mainWindowFunc()
    
    def show(self) -> None:
        self.isOpened = True 
        return super().show()
    
    def close(self) -> bool:
        self.isOpened = False
        return super().close()

if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, *args, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)
            self.resize(800, 600)
            self.button = QPushButton("Open Widget", self)
            self.button.clicked.connect(self.open_widget)

            self.label = QLabel("Button not clicked yet", self)
            self.label.move(10, 50)

            self.setCentralWidget(self.button)

        def open_widget(self):
            self.customWidget = KooPolyLineGeneratorfromCellWidget(self.on_dialog_button_click, self)
            self.dockWidget = QDockWidget("Cell-based PolyLine Generator", self)
            self.dockWidget.setWidget(self.customWidget)
            from PyQt5.QtCore import Qt
        
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockWidget)

        def on_dialog_button_click(self):
            self.label.setText("Button clicked in widget!")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()

