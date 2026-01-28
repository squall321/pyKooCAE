import sys 
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QDialogButtonBox, QLineEdit, QLabel, QHBoxLayout
from PyQt5.QtGui import QDoubleValidator, QCursor
from PyQt5.QtCore import Qt

class PositiveNegativeSelectDialog(QDialog):
    def __init__(self, parent=None, angle = 0.0):
        super(PositiveNegativeSelectDialog, self).__init__(parent)
        self.initUI(angle)
    
    def initUI(self,angle):
        layout = QHBoxLayout()
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        positiveAngleString = "Positive Angle : " + str(angle)
        negativeAngleString = "Negative Angle : " + str(angle-360.0)
        self.PositiveButton = QPushButton(positiveAngleString)
        self.NagativeButton = QPushButton(negativeAngleString)
        self.PositiveButton.clicked.connect(self.accept)
        self.NagativeButton.clicked.connect(self.reject)
        layout.addWidget(self.PositiveButton)
        layout.addWidget(self.NagativeButton)        

        self.setLayout(layout)

class RadiusPopupDialog(QDialog):
    def __init__(self, parent=None, radius = 1.0):
        super(RadiusPopupDialog, self).__init__(parent)
        self.radius = radius
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        
        label = QLabel("Radius : ")
        self.input_field = QLineEdit()
        radiusStr = str(self.radius)
        self.input_field.setText(radiusStr)
        double_validator = QDoubleValidator()
        self.input_field.setValidator(double_validator)
        hLayout = QHBoxLayout()
        hLayout.addWidget(label)
        hLayout.addWidget(self.input_field)
        layout.addLayout(hLayout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setWindowTitle("Edit Radius")

        # Cursor should select all text in the input field
        self.input_field.selectAll()

        self.setLayout(layout)

class AnglePopupDialog(QDialog):
    def __init__(self, parent=None,angle = 90.0):
        super(AnglePopupDialog, self).__init__(parent)
        self.angle = angle
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        # Create an input field
        label = QLabel("Angle : ")
        self.input_field = QLineEdit()
        angleStr = str(self.angle)
        self.input_field.setText(angleStr)
        double_validator = QDoubleValidator()
        self.input_field.setValidator(double_validator)
        hLayout = QHBoxLayout()
        hLayout.addWidget(label)
        hLayout.addWidget(self.input_field)
        layout.addLayout(hLayout)

        # Create OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.input_field.selectAll()
        self.setWindowTitle("Edit Angle")

        self.setLayout(layout)

if __name__ == "__main__":
    class MyWidgets(QWidget):
        def __init__(self):
            super().__init__()
            self.initUI()

        def initUI(self):
            layout = QVBoxLayout()

            # Create a button to trigger the edit popup
            edit_button = QPushButton("Angle Popup")
            edit_button.clicked.connect(self.showAnglePopup)
            layout.addWidget(edit_button)

            self.setLayout(layout)

        def showAnglePopup(self):
            # Create an instance of the edit popup
            edit_popup = AnglePopupDialog(self)

            edit_popup.move(QCursor.pos())

            # Show the popup and get the result
            result = edit_popup.exec_()

            if result == QDialog.Accepted:
                # User clicked OK, retrieve the input value
                input_value = edit_popup.input_field.text()
                print("Input value:", input_value)

            edit_popup.deleteLater()
        
    app = QApplication(sys.argv)
    widget = MyWidgets()
    widget.show()
    sys.exit(app.exec_())