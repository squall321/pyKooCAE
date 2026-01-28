import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QKeySequence, QBrush, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator


class ImportImageDialog(QDialog):
    def __init__(self, parent = None):
        super().__init__()
        self.setWindowTitle("Import Image Dialog")

        layout = QVBoxLayout()

        # add label and edit box for number of layers
        hLayoutNumLayers = QHBoxLayout()        
        self.label = QLabel("Number of Layers:")
        hLayoutNumLayers.addWidget(self.label)
        self.editNumLayers = QLineEdit()
        self.editNumLayers.setText("1")
        # only integers allowed
        self.editNumLayers.setValidator(QIntValidator())
        self.editNumLayers.selectionChanged.connect(self.changeNumLayers)
        hLayoutNumLayers.addWidget(self.editNumLayers)
        layout.addLayout(hLayoutNumLayers)
        
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Layer Name", "Layer Path", "X Size", "Y Size"])

        # set each column width
        self.table.setColumnWidth(0, 100)        
        self.table.setColumnWidth(1, 370)
        self.table.setColumnWidth(2, 50)
        
        self.table.setColumnWidth(3, 50)
        self.table.setRowCount(1)
        self.table.verticalHeader().hide()
        
        self.table.setItem(0, 0, QTableWidgetItem("Layer " + str(1)))
        self.table.setItem(0, 1, QTableWidgetItem("Path to Layer " + str(1)))        
        self.table.setItem(0, 2, QTableWidgetItem("600"))
        self.table.setItem(0, 3, QTableWidgetItem("400"))   
        
        self.table.cellClicked.connect(self.changeCell)            
        
        layout.addWidget(self.table)

        hLayoutButtons = QHBoxLayout()        
        self.buttonApply = QPushButton("Apply")
        self.buttonApply.clicked.connect(self.accept)
        hLayoutButtons.addWidget(self.buttonApply)
        self.buttonCancel = QPushButton("Cancel")
        self.buttonCancel.clicked.connect(self.reject)
        hLayoutButtons.addWidget(self.buttonCancel)
        layout.addLayout(hLayoutButtons)
        

        # fix dialog size
        self.setFixedWidth(600)
        
        self.setLayout(layout)

        self.prevNumLayers = 1
        self.parent = parent
    
    # change number of layers if edit number of layers is changed
    def changeNumLayers(self):
        numLayers = int(self.editNumLayers.text())
        prevNumLayers = self.prevNumLayers
        if numLayers == self.prevNumLayers:
            return
        self.prevNumLayers = numLayers
        self.table.setRowCount(numLayers)
        for i in range(numLayers):
            if i < prevNumLayers:
                continue
            self.table.setItem(i, 0, QTableWidgetItem("Layer " + str(i+1)))
            self.table.setItem(i, 1, QTableWidgetItem("Path to Layer " + str(i+1)))
            # connect import Image function if second column is clicked
            self.table.setItem(i, 2, QTableWidgetItem("600"))
            self.table.setItem(i, 3, QTableWidgetItem("400"))    

    def SetNumLayers(self, layerNameList):
        numLayers = len(layerNameList)        
        self.prevNumLayers = numLayers
        self.editNumLayers.setText(str(numLayers))
        self.table.setRowCount(numLayers)
        for i in range(numLayers):
            self.table.setItem(i, 0, QTableWidgetItem(layerNameList[i]))
            self.table.setItem(i, 1, QTableWidgetItem("Path to " + layerNameList[i]))
            # connect import Image function if second column is clicked
            self.table.setItem(i, 2, QTableWidgetItem("600"))
            self.table.setItem(i, 3, QTableWidgetItem("400"))

    # import dialog if second column in table is clicked
    def changeCell(self, row, column):
        if column == 1:
            print("Import Image Dialog")
            file_Dialog = QFileDialog(self)
            file_path, _ = file_Dialog.getOpenFileName(
                self, "Import Image", "", "Image Files (*.png *.jpg *.bmp)"
                )
            if file_path:
                self.table.setItem(row, column, QTableWidgetItem(file_path))
                print("Image Path: ", file_path)
        
    def accept(self) -> None:
        layerNameList = []
        layerPathList = []
        layerXSizeList = []
        layerYSizeList = []
        for i in range(self.table.rowCount()):
            layerNameList.append(self.table.item(i, 0).text())
            layerPathList.append(self.table.item(i, 1).text())
            layerXSizeList.append(int(self.table.item(i, 2).text()))
            layerYSizeList.append(int(self.table.item(i, 3).text()))

        if self.parent is not None:
            self.parent.ImportTextureBox(layerNameList, layerPathList, layerXSizeList, layerYSizeList)
        return super().accept()
    
    def reject(self) -> None:
        return super().reject()





if __name__ == '__main__':
    app = QApplication(sys.argv)

    dialog = ImportImageDialog()
    dialog.exec_()

    sys.exit(app.exec_())