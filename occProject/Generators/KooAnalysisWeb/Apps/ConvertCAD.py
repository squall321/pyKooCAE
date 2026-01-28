import os

getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")

from OCC.Core.StlAPI import StlAPI_Reader
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Compound, TopoDS_Shell
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_MakeShell
from OCC.Core.TopAbs import TopAbs_COMPOUND

from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SHELL, TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
from OCC.Core.TopoDS import topods, TopoDS_Face, TopoDS_Edge, TopoDS_Vertex
from OCC.Core import STEPControl
from OCC.Display.SimpleGui import init_display

def ConvertStltoStep(stlName,stepName):
    reader = StlAPI_Reader()
    shape = TopoDS_Shape()
    reader.Read(shape, stlName)
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    shapes = []
    i = 0 

    shell = TopoDS_Shell()
    shellBuilder = BRep_Builder()
    shellBuilder.MakeShell(shell)

    while explorer.More():
        i += 1
        face = topods.Face(explorer.Current())
        shellBuilder.Add(shell, face)
        #print(i)
        explorer.Next()
    #print(shell)
    solid = BRepBuilderAPI_MakeSolid(shell).Solid()
    step_writer = STEPControl.STEPControl_Writer()
    step_writer.Transfer(solid, STEPControl.STEPControl_AsIs)
    step_writer.Write(stepName)
    return solid



if __name__ == "__main__":
    stlName = ".\\KooAnalysisWeb\\Apps\\Samples\\sample1_solder.stl"
    stepName = ".\\KooAnalysisWeb\\Apps\\Samples\\sample1_solder.stp"
    solid = ConvertStltoStep(stlName,stepName)
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        # 오프스크린 모드: GUI 함수들을 더미로 정의
        def display_dummy(*args, **kwargs):
            print("[offscreen] display called with", args, kwargs)

        def start_display_dummy():
            print("[offscreen] start_display skipped")

        def add_menu_dummy(name):
            print(f"[offscreen] add_menu('{name}') skipped")

        def add_function_to_menu_dummy(*args, **kwargs):
            print("[offscreen] add_function_to_menu skipped")

        display = display_dummy
        start_display = start_display_dummy
        add_menu = add_menu_dummy
        add_function_to_menu = add_function_to_menu_dummy

    else:
        # 정상 GUI 모드
        from OCC.Display.SimpleGui import init_display
        display, start_display, add_menu, add_function_to_menu = init_display()
        display.DisplayShape(solid)
        start_display()