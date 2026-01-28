import sys
from PyQt5.QtWidgets import (
    QWidget, QApplication, QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel, QScrollArea
)
from PyQt5.QtCore import Qt

class LayerInputDialog(QDialog):
    def __init__(self, parent=None, nameList = []):
        super().__init__(parent)
        self.setWindowTitle("Layer Input Dialog")
        
        # 메인 레이아웃을 수평 레이아웃으로 설정
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.filePath = ""

        # 총 층수, CU 층수, 전체 두께를 한 줄로 표시하는 레이아웃
        label_layout = QHBoxLayout()
        self.total_layers_label = QLabel("Total Layers: 0")
        self.cu_layers_label = QLabel("CU Layers: 0")
        self.total_thickness_label = QLabel("Total Thickness: 0.0")
        
        self.thicknessList = [] 
        self.smThickness = 0.0
        self.spThickness = 0.0

        # 라벨들을 한 줄로 추가
        label_layout.addWidget(self.total_layers_label)
        label_layout.addWidget(self.cu_layers_label)
        label_layout.addWidget(self.total_thickness_label)
        self.main_layout.addLayout(label_layout)

        # 레이어 정보를 저장할 리스트
        self.layers = []
        
        # 수평 레이아웃을 만들어서 레이어 추가
        self.column_layout = QHBoxLayout()
        self.main_layout.addLayout(self.column_layout)

        # 첫 번째 열 생성 및 추가
        self.create_new_column()

        # Add 및 Export 버튼을 포함하는 레이아웃
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_layer)
        button_layout.addWidget(self.add_button)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_data)
        button_layout.addWidget(self.export_button)

        self.main_layout.addLayout(button_layout)
        self.setAddLayerOption = 0
        editControl = self.add_layer()
        editControl.setText("0.0")
        self.setAddLayerOption = 0
        editControl = self.add_layer()
        editControl.setText("0.0")
        numcu = 0 
        for i in range(len(nameList)):
            if "cu" in nameList[i] or "lay" in nameList[i] or "comp" in nameList[i] or "sold" in nameList[i]:
                numcu += 1
        curcu = 0
        for i in range(len(nameList)):
            if "cu" in nameList[i] or "lay" in nameList[i] or "comp" in nameList[i] or "sold" in nameList[i]:
                self.setAddLayerOption = 1
                curcu = curcu + 1
            elif "ppg" in nameList[i]:
                self.setAddLayerOption = 2
                if curcu == numcu/2: 
                    self.setAddLayerOption = 5
            else:
                self.setAddLayerOption = 3
            editControl = self.add_layer()
            if self.setAddLayerOption == 1:
                editControl.setText("1.5e-5")
            elif self.setAddLayerOption == 2:
                editControl.setText("3.1e-5")
            elif self.setAddLayerOption == 3:
                editControl.setText("2.5e-5")
            elif self.setAddLayerOption == 4:
                editControl.setText("2.5e-5")
            elif self.setAddLayerOption == 5:
                editControl.setText("6.5e-5")        
        # 총 정보 업데이트
        self.update_labels()

    def create_new_column(self):
        """새로운 열을 생성하고 수평 레이아웃에 추가"""
        new_column = QVBoxLayout()
        self.column_layout.addLayout(new_column)
        return new_column

    def add_layer(self):
        # 현재 열을 가져오고, 새로운 열을 추가할 필요가 있는지 확인
        if len(self.layers) % 10 == 0:
            self.current_column = self.create_new_column()

        # 레이어를 위한 레이아웃
        layer_layout = QHBoxLayout()

        # ComboBox 생성 및 옵션 추가
        combo_box = QComboBox()
        combo_box.addItem("None")
        combo_box.addItem("CU")
        combo_box.addItem("PPG")
        combo_box.addItem("SM")
        combo_box.addItem("SP")        
        combo_box.addItem("Core")
        if self.setAddLayerOption == 1:
            combo_box.setCurrentIndex(1)
        elif self.setAddLayerOption == 2:
            combo_box.setCurrentIndex(2)
        elif self.setAddLayerOption == 3:
            combo_box.setCurrentIndex(3)
        elif self.setAddLayerOption == 5:
            combo_box.setCurrentIndex(5)
        # 두께 입력을 위한 QLineEdit
        thickness_edit = QLineEdit()
        thickness_edit.setPlaceholderText("Enter thickness")

        # 옵션 변경 시 두께의 기본값 설정 및 라벨 업데이트
        combo_box.currentIndexChanged.connect(
            lambda index, edit=thickness_edit: self.set_default_thickness(index, edit)
        )
        combo_box.currentIndexChanged.connect(self.update_labels)
        thickness_edit.textChanged.connect(self.update_labels)
        
        # 레이아웃에 ComboBox와 QLineEdit 추가
        layer_layout.addWidget(combo_box)
        layer_layout.addWidget(thickness_edit)

        # 현재 열에 레이어 추가
        self.current_column.addLayout(layer_layout)

        # 레이어 정보 저장
        self.layers.append((combo_box, thickness_edit))
        return thickness_edit

    def set_default_thickness(self, index, thickness_edit):
        # 각 옵션에 따른 기본 두께 값 설정
        default_thickness = {
            1: "1.5e-5",  # CU
            2: "3.1e-5",  # PPG
            3: "2.5e-5",  # SM
            4: "2.5e-5",  # SP
            5: "6.5e-5",  # Core
        }
        if index in default_thickness:
            thickness_edit.setText(default_thickness[index])
        else:
            thickness_edit.clear()  # None 선택 시 두께 입력 초기화

    def update_labels(self):
        total_layers = 0
        cu_layers = 0
        total_thickness = 0.0
        
        self.thicknessList = []

        for combo_box, thickness_edit in self.layers:
            option = combo_box.currentText()
            thickness = thickness_edit.text()

            if option != "None":
                try:
                    thickness_value = float(thickness)
                    
                    if thickness_value > 0:  # 두께가 0보다 클 때만 계산에 포함
                        total_layers += 1
                        if option == 'PPG':
                            self.thicknessList.append(thickness_value)
                        if option == 'SM':
                            self.smThickness = thickness_value
                        if option == 'SP':
                            self.spThickness = thickness_value                            
                        if option == "CU":
                            self.thicknessList.append(thickness_value)
                            cu_layers += 1
                        if option == "Core":
                            self.thicknessList.append(thickness_value)
                        total_thickness += thickness_value
                except ValueError:
                    pass  # 잘못된 입력 무시

        # 라벨 업데이트
        self.total_layers_label.setText(f"Total Layers: {total_layers}")
        self.cu_layers_label.setText(f"CU Layers: {cu_layers}")
        self.total_thickness_label.setText(f"Total Thickness: {total_thickness:.5e}")

    def SetFilePath(self, filePath):
        self.filePath = filePath
    
    def export_data(self):
        # 데이터를 부모 클래스에 반환하고 대화 상자 닫기
        data = {
            "total_layers": self.total_layers_label.text(),
            "cu_layers": self.cu_layers_label.text(),
            "total_thickness": self.total_thickness_label.text(),
            "thicknesslist" : self.thicknessList,
            "smThickness" : self.smThickness,
            "spThickness" : self.spThickness,
            "filepath" : self.filePath
        }
        self.accept()  # QDialog를 닫으면서 accept 상태를 반환
        self.parent().ExportMultiscaleModelFile(data)  # 부모 클래스에 데이터 전달

class ParentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parent Window")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.open_dialog_button = QPushButton("Open Layer Input Dialog")
        self.open_dialog_button.clicked.connect(self.open_dialog)
        self.layout.addWidget(self.open_dialog_button)

        self.data_label = QLabel("Exported Data: None")
        self.layout.addWidget(self.data_label)

    def open_dialog(self):
        dialog = LayerInputDialog(self)
        if dialog.exec_():  # 모달 대화 상자를 열고 accept 상태 반환 시
            pass  # 여기서 추가 처리가 가능합니다

    def ExportMultiscaleModelFile(self, data):
        # 부모 클래스에서 데이터 처리
        self.data_label.setText(f"Exported Data: {data}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ParentWindow()
    window.show()
    sys.exit(app.exec_())
