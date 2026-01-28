import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QKeySequence, QBrush, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator


class LayerPropertyDialog(QDialog):
    def __init__(self, parent = None):
        super().__init__()

        self.setWindowTitle("Layer Property Dialog")        

        layout = QVBoxLayout()

        hlayoutNumLayers = QHBoxLayout()
        self.label = QLabel("Number of Layers:")
        hlayoutNumLayers.addWidget(self.label)
        self.editNumLayers = QLineEdit()
        self.editNumLayers.setText("1")
        self.editNumLayers.setValidator(QIntValidator())
        self.editNumLayers.selectionChanged.connect(self.changeNumLayers)
        hlayoutNumLayers.addWidget(self.editNumLayers)
        layout.addLayout(hlayoutNumLayers)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Layer Name", "Thickness"])

        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 100)

        self.table.setRowCount(1)
        self.table.verticalHeader().hide()

        self.table.setItem(0, 0, QTableWidgetItem("Layer " + str(1)))
        self.table.setItem(0, 1, QTableWidgetItem("1"))

        self.table.cellClicked.connect(self.changeCell)

        layout.addWidget(self.table)

        hlayoutButtons = QHBoxLayout()
        self.buttonApply = QPushButton("Apply")
        self.buttonApply.clicked.connect(self.accept)
        hlayoutButtons.addWidget(self.buttonApply)
        self.buttonCancel = QPushButton("Cancel")
        self.buttonCancel.clicked.connect(self.reject)
        hlayoutButtons.addWidget(self.buttonCancel)
        layout.addLayout(hlayoutButtons)

        self.setFixedWidth(600)
        self.setLayout(layout)
        self.prevNumLayers = 1
        self.parent = parent
    
    def changeNumLayers(self):
        numLayers = int(self.editNumLayers.text())
        prevNumLayers = self.prevNumLayers
        if prevNumLayers == numLayers:
            return
        self.prevNumLayers = numLayers
        self.table.setRowCount(numLayers)
        for i in range(numLayers):
            if i < prevNumLayers:
                continue
            self.table.setItem(i, 0, QTableWidgetItem("Layer " + str(i + 1)))   
            self.table.setItem(i, 1, QTableWidgetItem("1"))
    
    def SetNumLayers(self, layerNameList):
        numLayers = len(layerNameList)
        self.prevNumLayers = numLayers
        self.editNumLayers.setText(str(numLayers))
        self.table.setRowCount(numLayers)
        for i in range(numLayers):
            self.table.setItem(i, 0, QTableWidgetItem(layerNameList[i]))   
            self.table.setItem(i, 1, QTableWidgetItem("1"))
    
    def changeCell(self, row, column):
        pass

    def accept(self) -> None:
        layerNameList = []
        layerThicknessList = []
        for i in range(self.prevNumLayers):
            layerNameList.append(self.table.item(i, 0).text())
            layerThicknessList.append(float(self.table.item(i, 1).text()))
        
        if self.parent is not None:
            pass
        return super().accept()
    
    def reject(self) -> None:
        return super().reject()

            



if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = LayerPropertyDialog()
    dialog.show()
    sys.exit(app.exec_())