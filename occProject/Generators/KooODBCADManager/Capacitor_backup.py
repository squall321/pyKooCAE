import sys
from math import cos, pi 
import os 
import os.path 

getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")
os.add_dll_directory(path)
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Display.SimpleGui import init_display
from OCC.Core.TColgp import TColgp_Array1OfPnt2d
from OCC.Core.gp import gp_Pnt, gp_Pnt2d, gp_Ax2, gp_Dir, gp_Circ, gp_Ax3, gp_Pln, gp_Trsf, gp_Vec, gp_Ax1
from OCC.Extend.TopologyUtils import TopologyExplorer
import OCC.Core.BRepBuilderAPI as BRepBuilderAPI
from OCC.Core.BRep import BRep_Builder
from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCC.Core.TopoDS import TopoDS_Compound
import subprocess
from KooAnalysisWeb.Apps import ConvertCAD as convertCAD
import math

from OCC.Core.BRepAlgoAPI import (
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Section,
)

from OCC.Core.Quantity import (
    Quantity_Color,
    Quantity_TOC_RGB,
    Quantity_NOC_BLACK,
    Quantity_NOC_GRAY,
    Quantity_NOC_WHITE,
    Quantity_NOC_RED,
    Quantity_NOC_GREEN,
    Quantity_NOC_BLUE1,
    Quantity_NOC_YELLOW,
    Quantity_NOC_BROWN,
    Quantity_NOC_PINK,
    Quantity_NOC_ORANGE,
    Quantity_NOC_PURPLE,
)

if __name__ =="__main__":
    display, start_display, add_menu, add_function_to_menu = init_display()
unit = 1.0
class CapacitorForm():
    def __init__(self):
        self.lpw = 877.0*unit
        self.lph = 800.0*unit
        self.rpw = 870.0*unit
        self.rph = 800.0*unit
        self.piw = 495.0*unit
        self.pt = 30.0*unit
        self.cbw = 1800.0*unit
        self.cbh = 500.0*unit
        self.cbt = 600.0*unit
        self.ltw = 300.0*unit
        self.ltt = 10.0*unit
        self.rtw = 300.0*unit
        self.rtt = 10.0*unit
        self.lbw = 20.0*unit
        self.lbt = 10.0*unit
        self.rbw = 20.0*unit
        self.rbt = 10.0*unit
        self.lfw = 20.0*unit
        self.lft = 10.0*unit
        self.rfw = 20.0*unit
        self.rft = 10.0*unit
        self.lst = 30.0*unit
        self.lsv = 700.0
        self.rst = 30.0*unit
        self.rsv = 700.0
        self.tens = 0.1*unit
        self.solderWidthRatio = 0.8
        self.solderThicknessRatio = 0.5
        self.solderBottomWidthRatio = 0.4
        self.sgValue = 8
        self.tilt = 0
        self.compound = []
    
    def SetProperties(self,lpw, lph, rpw, rph, piw, pt, cbw, cbh, cbt, ltw, ltt, rtw, rtt, lbw, lbt, rbw, rbt, lfw, lft, rfw, rft, lst, lsv, rst, rsv, tens, solderWidthRatio, solderThicknessRatio, solderBottomWidthRatio, sgValue, tilt):
        self.lpw = lpw
        self.lph = lph
        self.rpw = rpw
        self.rph = rph
        self.piw = piw
        self.pt = pt
        self.cbw = cbw
        self.cbh = cbh
        self.cbt = cbt
        self.ltw = ltw
        self.ltt = ltt
        self.rtw = rtw
        self.rtt = rtt
        self.lbw = lbw
        self.lbt = lbt 
        self.rbw = rbw
        self.rbt = rbt
        self.lfw = lfw
        self.lft = lft
        self.rfw = rfw
        self.rft = rft
        self.lst = lst
        self.lsv = lsv
        self.rst = rst
        self.rsv = rsv
        self.tens = tens
        self.solderWidthRatio = solderWidthRatio
        self.solderThicknessRatio = solderThicknessRatio
        self.solderBottomWidthRatio = solderBottomWidthRatio        
        self.sgValue = sgValue
        self.tilt = tilt 

    def GetLeftTotalThickness(self):
        ltt = self.ltt
        lbt = self.lbt
        lft = self.lft 
        lst = self.lst
        pt = self.pt 
        totalthick = ltt+lbt+lft+lst+pt
        return totalthick
    def GetRightTotalThickness(self):
        rtt = self.rtt
        rbt = self.rbt
        rft = self.rft 
        rst = self.rst
        pt = self.pt 
        totalthick = rtt+rbt+rft+rst+pt
        return totalthick
    def GetTotalThickness(self):
        ltt = self.ltt
        lbt = self.lbt
        lft = self.lft 
        lst = self.lst
        rtt = self.rtt
        rbt = self.rbt
        rft = self.rft 
        rst = self.rst
        pt = self.pt 
        totalthick = max(ltt,rtt)
        totalthick += max(lbt,rbt)
        totalthick += max(lft,rft)
        totalthick += max(lst,rst)
        totalthick += pt
        return totalthick
    def MakeFillet(self,box,indexList,fillet):
        fbox = BRepFilletAPI_MakeFillet(box)
        expl = list(TopologyExplorer(box).edges())
        for i in indexList:
            fbox.Add(fillet,fillet,expl[i])
        fbox.Build()
        if fbox.IsDone():
            return fbox
        else:
            print('Fillet Failed')
            return box 

    def MakeLeftPad(self):
        lpw = self.lpw
        lph = self.lph
        piw = self.piw
        pt = self.pt
        pl1 = gp_Pnt(-piw/2.0,0.0,lph/2.0)
        pl2 = gp_Pnt(-lpw-piw/2.0,pt,-lph/2.0)
        return BRepPrimAPI_MakeBox(pl1,pl2)
    
    def MakeRightPad(self):
        rpw = self.rpw
        rph = self.rph
        piw = self.piw
        pt = self.pt
        pr1 = gp_Pnt(piw/2.0,0.0,rph/2.0)
        pr2 = gp_Pnt(rpw+piw/2.0,pt,-rph/2.0)
        return BRepPrimAPI_MakeBox(pr1,pr2)
    
    def MakeCeramicBodyDetail(self):
        H = self.cbh
        W = self.cbw

    def MakeCeramicBody(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        # total thickness
        totalThickness = self.GetTotalThickness()
        plb3 = gp_Pnt(-cbw/2.0,totalThickness,-cbh/2.0)
        prt3 = gp_Pnt(cbw/2.0,totalThickness+cbt,cbh/2.0)
        box = BRepPrimAPI_MakeBox(plb3,prt3)
        return box
        
    def MakeLeftTerminal(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        ltt = self.ltt
        ltw = self.ltw
        totalThickness = self.GetLeftTotalThickness()
        plb1 = gp_Pnt(-cbw/2.0-ltt,totalThickness+cbt+ltt,cbh/2.0+ltt)
        plb2 = gp_Pnt(-cbw/2.0+ltw+ltt,totalThickness-ltt,-cbh/2.0-ltt)
        return BRepPrimAPI_MakeBox(plb1,plb2)
    
    def MakeRightTerminal(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        rtt = self.rtt
        rtw = self.rtw
        totalThickness = self.GetRightTotalThickness()
        prb1 = gp_Pnt(cbw/2.0+rtt,totalThickness+cbt+rtt,cbh/2.0+rtt)
        prb2 = gp_Pnt(cbw/2.0-rtw-rtt,totalThickness-rtt,-cbh/2.0-rtt)
        return BRepPrimAPI_MakeBox(prb1,prb2)

    def MakeLeftBarrier(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        ltt = self.ltt
        ltw = self.ltw
        lbt = self.lbt
        lbw = self.lbw
        totalthickness = self.GetLeftTotalThickness()
        pl51 = gp_Pnt(-cbw/2.0-ltt-lbt,totalthickness+cbt+ltt+lbt,cbh/2.0+ltt+lbt)
        pl52 = gp_Pnt(-cbw/2.0+ltw+lbw+ltt+lbt,totalthickness-ltt-lbt,-cbh/2.0-ltt-lbt)
        return BRepPrimAPI_MakeBox(pl51,pl52)
    
    def MakeRightBarrier(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        rtt = self.rtt
        rtw = self.rtw
        rbt = self.rbt
        rbw = self.rbw
        totalthickness = self.GetRightTotalThickness()
        pr51 = gp_Pnt(cbw/2.0+rtt+rbt,totalthickness+cbt+rtt+rbt,cbh/2.0+rtt+rbt)
        pr52 = gp_Pnt(cbw/2.0-rtw-rbw-rtt-rbt,totalthickness-rtt-rbt,-cbh/2.0-rtt-rbt)
        return BRepPrimAPI_MakeBox(pr51,pr52)
    
    def MakeLeftFinish(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        ltt = self.ltt
        ltw = self.ltw
        lbt = self.lbt
        lbw = self.lbw
        lft = self.lft
        lfw = self.lfw
        totalthickness = self.GetLeftTotalThickness()
        pl61 = gp_Pnt(-cbw/2.0-ltt-lbt-lft,totalthickness+cbt+ltt+lbt+lft,cbh/2.0+ltt+lbt+lft)
        pl62 = gp_Pnt(-cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft,totalthickness-ltt-lbt-lft,-cbh/2.0-ltt-lbt-lft)
        box = BRepPrimAPI_MakeBox(pl61,pl62).Shape()
        fillet = 10*unit
        return self.MakeFillet(box,[0,1,2,3,4,5,6,7,8,9,10,11],fillet)
    
    def MakeRightFinish(self):
        cbw = self.cbw
        cbh = self.cbh
        cbt = self.cbt
        rtt = self.rtt
        rtw = self.rtw
        rbt = self.rbt
        rbw = self.rbw
        rft = self.rft
        rfw = self.rfw
        totalthickness = self.GetRightTotalThickness()
        pr61 = gp_Pnt(cbw/2.0+rtt+rbt+rft,totalthickness+cbt+rtt+rbt+rft,cbh/2.0+rtt+rbt+rft)
        pr62 = gp_Pnt(cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft,totalthickness-rtt-rbt-rft,-cbh/2.0-rtt-rbt-rft)
        box = BRepPrimAPI_MakeBox(pr61,pr62).Shape()
        fillet = 10*unit
        return self.MakeFillet(box,[0,1,2,3,4,5,6,7,8,9,10,11],fillet)       

    def MakeMLCC(self,name):
        display.EraseAll()
        
        # Generate Geometry Components
        lp = self.MakeLeftPad()
        rp = self.MakeRightPad()
        cb = self.MakeCeramicBody()
        lt = self.MakeLeftTerminal()
        rt = self.MakeRightTerminal()
        lb = self.MakeLeftBarrier()
        rb = self.MakeRightBarrier()
        lf = self.MakeLeftFinish()
        rf = self.MakeRightFinish()
        display.DisplayShape(lp.Shape())
        display.DisplayShape(rp.Shape())
        ## Display Ceramic Body
        rreal = 145.0 / 255.0
        greal = 102.0 / 255.0
        breal = 83.0 / 255.0
        color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)
        display.DisplayShape(cb.Shape(),None,None,color)
        ## Cut Operatior of Terminal 'by' Ceramic Body
        clt = BRepAlgoAPI_Cut(lt.Shape(),cb.Shape())
        crt = BRepAlgoAPI_Cut(rt.Shape(),cb.Shape())
        ## Display Left/Right Terminal
        rreal = 26.0 / 255.0
        greal = 52.0 / 255.0
        breal = 109.0  / 255.0
        color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)

        display.DisplayShape(clt.Shape(),None,None,color,update=True)
        display.DisplayShape(crt.Shape(),None,None,color,update=True)
        ## Display Left/Right Barrier
        clb = BRepAlgoAPI_Cut(lb.Shape(),cb.Shape())
        crb = BRepAlgoAPI_Cut(rb.Shape(),cb.Shape())
        clb =   BRepAlgoAPI_Cut(clb.Shape(),lt.Shape())
        crb =   BRepAlgoAPI_Cut(crb.Shape(),rt.Shape())
        rreal = 245.0 / 255.0
        greal = 104.0 / 255.0
        breal = 12.0 / 255.0
        color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)
        display.DisplayShape(clb.Shape(),None,None,color,update=True)
        display.DisplayShape(crb.Shape(),None,None,color,update=True)

        ## Display Left/Right Finish 
        ## Cut Operation of finish 'by' Ceramic Body, Terminal and Barrier 
        clf = BRepAlgoAPI_Cut(lf.Shape(),cb.Shape())
        crf = BRepAlgoAPI_Cut(rf.Shape(),cb.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lt.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rt.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lb.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rb.Shape())

        rreal = 181.0/255.0
        greal = 178.0/255.0
        breal = 189.0/255.0
        color = Quantity_Color(rreal,greal,breal,Quantity_TOC_RGB)
        display.DisplayShape(clf.Shape(),None,None,color,update=True)
        display.DisplayShape(crf.Shape(),None,None,color,update=True)
    def MakeSolderScript(self,fileName,direction,solderWidthRatio,solderThicknessRatio,solderBottomWidthRatio,tens,SG,tilt):
        evolverScript = "//Capacitor \n"
        evolverScript += "Evolver_Version ""2.11""\n"
        evolverScript += "// Physical dimensions of the chip\n"
        evolverScript += "parameter lpw = {lpw} // leftPadWidth\n"
        evolverScript += "parameter lph = {lph} // leftPadHeight\n"
        evolverScript += "parameter pt = {pt} // padThickness\n"
        evolverScript += "parameter piw = {piw} // padIntervalWidth\n"        
        evolverScript += "parameter rpw = {rpw} // rightPadWidth\n"
        evolverScript += "parameter rph = {rph} // rightPadHeight\n"
        evolverScript += "parameter cbw = {cbw} // ceramicBodyWidth\n"
        evolverScript += "parameter cbh = {cbh} // ceramicBodyHeight\n"
        evolverScript += "parameter cbt = {cbt} // ceramicBodyThickness\n"
        evolverScript += "parameter ltw = {ltw} // leftTerminalWidth\n"
        evolverScript += "parameter ltt = {ltt} // leftTerminalThickness\n"
        evolverScript += "parameter rtw = {rtw} // rightTerminalWidth\n"
        evolverScript += "parameter rtt = {rtt} // rightTerminalThickness\n"
        evolverScript += "parameter lbw = {lbw} // leftBarrierWidth\n"
        evolverScript += "parameter lbt = {lbt} // leftBarrierThickness\n"
        evolverScript += "parameter rbw = {rbw} // rightBarrierWidth\n"
        evolverScript += "parameter rbt = {rbt} // rightBarrierThickness\n"
        evolverScript += "parameter lfw = {lfw} // leftFinishWidth\n"
        evolverScript += "parameter lft = {lft} // leftFinishThickness\n"
        evolverScript += "parameter rfw = {rfw} // rightFinishWidth\n"
        evolverScript += "parameter rft = {rft} // rightFinishThickness\n"
        evolverScript += "parameter lst = {lst} // leftSolderThickness\n"
        evolverScript += "parameter lsv = {lsv} // leftSolderVolume\n"
        evolverScript += "parameter rst = lst // rightSolderThickness\n"
        evolverScript += "parameter rsv = {rsv} // rightSolderVolume\n"
        evolverScript += "parameter v1 = lsv*1000*1000*1000\n"
        evolverScript += "parameter v2 = rsv*1000*1000*1000\n"
        #evolverScript += "parameter v1 = lsv\n"
        #evolverScript += "parameter v2 = rsv\n"
        evolverScript += "parameter leftTotalThickness = ltt + lbt + lft + lst + pt// left total thickness\n"
        evolverScript += "parameter rightTotalThickness = rtt + rbt + rft + rst + pt// right total thickness\n"
        evolverScript += "// solder\n"
        evolverScript += "parameter solderWidthRatio = {solderWidthRatio} // solderWidthRatio\n"
        evolverScript += "parameter solderThicknessRatio = {solderThicknessRatio} // solderThicknessRatio\n"
        evolverScript += "parameter solderBottomWidthRatio = {solderBottomWidthRatio} // solderBottonWidth\n"
        evolverScript += "parameter PW_x = lpw\n"
        evolverScript += "parameter PW_y = lph\n"
        evolverScript += "parameter TENS = {tens}*1000\n"
        #evolverScript += "parameter TENS = {tens}\n"
        evolverScript += "parameter SG = {SG}\n"
        evolverScript += "parameter tilt = {tilt}\n"
        evolverScript += "#define st sin(tilt*pi/180)\n"
        evolverScript += "#define ct cos(tilt*pi/180)\n"
        evolverScript += "parameter x0 = 0\n"
        evolverScript += "parameter zl0 = leftTotalThickness+cbt/2.0\n"
        evolverScript += "parameter zr0 = rightTotalThickness+cbt/2.0\n"
        evolverScript += "parameter z0 = 0\n"
        evolverScript += "#define CHIPLX    (ct*(x-x0)-st*(z-zl0))\n"
        evolverScript += "#define CHIPLY    (y)\n"
        evolverScript += "#define CHIPLZ    (st*(x-x0)+ct*(z-zl0))+zl0\n" 
        evolverScript += "#define CHIPRX    (ct*(x-x0)-st*(z-zr0))\n"
        evolverScript += "#define CHIPRY    (y)\n"
        evolverScript += "#define CHIPRZ    (st*(x-x0)+ct*(z-zr0))+zr0\n"
        evolverScript += "gravity_constant  9.81\n"
        evolverScript += "scale_limit  1/TENS\n"
        evolverScript += "// Left Pad\n"
        evolverScript += "constraint 1 // +x face of left pad\n"
        evolverScript += "formula : x = -piw/2.0\n"
        evolverScript += "constraint 2 // -x face of left pad\n"
        evolverScript += "formula : x = -lpw-piw/2.0\n"
        evolverScript += "constraint 3 // +y face of left pad\n"
        evolverScript += "formula : y = lph/2.0\n"
        evolverScript += "constraint 4 // -y face of left pad\n"
        evolverScript += "formula : y = -lph/2.0\n"
        evolverScript += "constraint 5 // +z face of left pad\n"
        evolverScript += "formula : z = pt\n"
        evolverScript += "constraint 6 // -z face of left pad\n"
        evolverScript += "formula : z = 0\n"
        evolverScript += "// Left Finish\n"
        evolverScript += "constraint 7 // +x face of left finish\n"
        evolverScript += "formula : CHIPLX = -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft\n"
        evolverScript += "constraint 8 // -x face of left finish\n"
        evolverScript += "formula : CHIPLX = -cbw/2.0-ltt-lbt-lft\n"
        evolverScript += "constraint 9 // +y face of left finish\n"
        evolverScript += "formula : CHIPLY = cbh/2.0+ltt+lbt+lft\n"
        evolverScript += "constraint 10 // -y face of left finish\n"
        evolverScript += "formula : CHIPLY = -cbh/2.0-ltt-lbt-lft\n"
        evolverScript += "constraint 11 // +z face of left finish\n"
        evolverScript += "formula : CHIPLZ = leftTotalThickness + cbt + ltt + lbt + lft\n"
        evolverScript += "constraint 12 // -z face of left finish\n"
        evolverScript += "formula : CHIPLZ = leftTotalThickness - ltt - lbt - lft\n"
        evolverScript += "// Right Pad\n"
        evolverScript += "constraint 1001 // +x face of right pad\n"
        evolverScript += "formula : x = rpw+piw/2.0\n"
        evolverScript += "constraint 1002 // -x face of right pad\n"
        evolverScript += "formula : x = piw/2.0\n"
        evolverScript += "constraint 1003 // +y face of right pad\n"
        evolverScript += "formula : y = rph/2.0\n"
        evolverScript += "constraint 1004 // -y face of right pad\n"
        evolverScript += "formula : y = -rph/2.0\n"
        evolverScript += "constraint 1005 // +z face of right pad\n"
        evolverScript += "formula : z = pt\n"
        evolverScript += "constraint 1006 // -z face of right pad\n"
        evolverScript += "formula : z = 0\n"
        evolverScript += "// Right Finish\n"
        evolverScript += "constraint 1007 // +x face of right finish\n"
        evolverScript += "formula : CHIPRX = cbw/2.0 - rtw - rbw - rfw - rtt - rbt - rft\n"
        evolverScript += "constraint 1008 // -x face of right finish\n"
        evolverScript += "formula : CHIPRX = cbw/2.0 + rtt + rbt + rft\n"
        evolverScript += "constraint 1009 // +y face of right finish\n"
        evolverScript += "formula : CHIPRY = cbh/2.0 + rtt + rbt + rft\n"
        evolverScript += "constraint 1010 // -y face of right finish\n"
        evolverScript += "formula : CHIPRY = -cbh/2.0 - rtt - rbt - rft\n"
        evolverScript += "constraint 1011 // +z face of right finish\n"
        evolverScript += "formula : CHIPRZ = rightTotalThickness + cbt + rtt + rbt + rft\n"
        evolverScript += "constraint 1012 // -z face of right finish\n"
        evolverScript += "formula : CHIPRZ = rightTotalThickness - rtt - rbt - rft\n"
        evolverScript += "// Constraint for solder on chip\n"
        evolverScript += "// Left pad\n"        
        evolverScript += "constraint 101 nonpositive // to keep solder within pos y bound\n"
        evolverScript += "formula : x+piw/2.0\n"
        evolverScript += "constraint 102 nonnegative\n"
        evolverScript += "formula : x+piw/2.0+lpw\n"
        evolverScript += "constraint 103 nonpositive\n"
        evolverScript += "formula : y-lph/2.0\n"
        evolverScript += "constraint 104 nonnegative\n"
        evolverScript += "formula : y+lph/2.0\n"
        evolverScript += "constraint 105 nonpositive\n"
        evolverScript += "formula : z-pt\n"
        evolverScript += "constraint 106 nonnegative\n"
        evolverScript += "formula : z\n"
        evolverScript += "// Left Finish\n"
        evolverScript += "constraint 107 nonpositive // +x face of left finish\n"
        evolverScript += "formula : CHIPLX + cbw/2.0 - ltw - lbw - lfw - ltt - lbw - lft\n"
        evolverScript += "constraint 108 nonnegative // -x face of left finish\n"
        evolverScript += "formula : CHIPLX + cbw/2.0 + ltt + lbt + lft\n"
        evolverScript += "constraint 109 nonpositive // +y face of left finish\n"
        evolverScript += "formula : CHIPLY - cbh/2.0 - ltt - lbt - lft\n"
        evolverScript += "constraint 110 nonnegative // -y face of left finish\n"
        evolverScript += "formula : CHIPLY + cbh/2.0 + ltt + lbt + lft\n"
        evolverScript += "constraint 111 nonpositive // +z face of left finish\n"
        evolverScript += "formula : CHIPLZ - leftTotalThickness - cbt - ltt - lbt - lft\n"
        evolverScript += "constraint 112 nonnegative // -z face of left finish\n"
        evolverScript += "formula : CHIPLZ - leftTotalThickness + ltt + lbt + lft\n"
        evolverScript += "// Right Pad\n"
        evolverScript += "constraint 1101 nonpositive // +x face of right pad\n"
        evolverScript += "formula : x - rpw - piw/2.0\n"
        evolverScript += "constraint 1102 nonnegative // -x face of right pad\n"
        evolverScript += "formula : x - piw/2.0\n"
        evolverScript += "constraint 1103 nonpositive // +y face of right pad\n"
        evolverScript += "formula : y - rph/2.0\n"
        evolverScript += "constraint 1104 nonnegative // -y face of right pad\n"
        evolverScript += "formula : y + rph/2.0\n"
        evolverScript += "constraint 1105 nonpositive // +z face of right pad\n"
        evolverScript += "formula : z - pt\n"
        evolverScript += "constraint 1106 nonnegative // -z face of right pad\n"
        evolverScript += "formula : z\n"
        evolverScript += "// Right Finish\n"
        evolverScript += "constraint 1107 nonnegative // +x face of right finish\n"
        evolverScript += "formula : CHIPRX - cbw/2.0 + rtw + rbw + rfw + rtt + rbt + rft\n"
        evolverScript += "constraint 1108 nonpositive // -x face of right finish\n"
        evolverScript += "formula : CHIPRX - cbw/2.0 - rtt - rbt - rft\n"
        evolverScript += "constraint 1109 nonpositive // +y face of right finish\n"
        evolverScript += "formula : CHIPRY - cbh/2.0 - rtt - rbt - rft\n"
        evolverScript += "constraint 1110 nonnegative // -y face of right finish\n"
        evolverScript += "formula : CHIPRY + cbh/2.0 + rtt + rbt + rft\n"
        evolverScript += "constraint 1111 nonpositive // +z face of right finish\n"
        evolverScript += "formula : CHIPRZ - rightTotalThickness - cbt - rtt - rbt - rft\n"
        evolverScript += "constraint 1112 nonnegative // -z face of right finish\n"
        evolverScript += "formula : CHIPRZ - rightTotalThickness + rtt + rbt + rft\n"
        evolverScript += "// Initial Shape Specification\n"
        evolverScript += "// Note that numbering of elements is not continous to keep the same \n"
        evolverScript += "// elements after loading, start Evolver with the -i option\n"
        evolverScript += "// given as coordinates\n"
        evolverScript += "vertices\n"

        evolverScript += "//left pad\n"
        evolverScript += "1 -lpw-piw/2.0    -lph/2.0    0.0 fixed\n"
        evolverScript += "2 -piw/2.0    -lph/2.0     0.0 fixed\n"
        evolverScript += "3 -piw/2.0    lph/2.0     0.0 fixed\n"
        evolverScript += "4 -lpw-piw/2.0    lph/2.0     0.0 fixed\n"
        evolverScript += "5 -lpw-piw/2.0    -lph/2.0    pt fixed\n"
        evolverScript += "6 -piw/2.0    -lph/2.0     pt fixed\n"
        evolverScript += "7 -piw/2.0    lph/2.0     pt fixed\n"
        evolverScript += "8 -lpw-piw/2.0    lph/2.0     pt fixed\n"

        evolverScript += "//left finish \n"
        evolverScript += "9 -cbw/2.0-ltt-lbt-lft    -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft fixed\n"
        evolverScript += "10 -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft    -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft fixed\n"
        evolverScript += "11 -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft    cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft fixed\n"
        evolverScript += "12 -cbw/2.0-ltt-lbt-lft    cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft fixed\n"
        evolverScript += "13 -cbw/2.0-ltt-lbt-lft    -cbh/2.0-ltt-lbt-lft    leftTotalThickness+cbt+ltt+lbt+lft fixed\n"
        evolverScript += "14 -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft    -cbh/2.0-ltt-lbt-lft    leftTotalThickness+cbt+ltt+lbt+lft fixed\n"
        evolverScript += "15 -cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft    cbh/2.0+ltt+lbt+lft    leftTotalThickness+cbt+ltt+lbt+lft fixed\n"
        evolverScript += "16 -cbw/2.0-ltt-lbt-lft    cbh/2.0+ltt+lbt+lft    leftTotalThickness+cbt+ltt+lbt+lft fixed\n"

        evolverScript += "//right pad\n"
        evolverScript += "1001 rpw+piw/2.0    -rph/2.0    0.0 fixed\n"
        evolverScript += "1002 piw/2.0    -rph/2.0     0.0 fixed\n"
        evolverScript += "1003 piw/2.0    rph/2.0     0.0 fixed\n"
        evolverScript += "1004 rpw+piw/2.0    rph/2.0     0.0 fixed\n"
        evolverScript += "1005 rpw+piw/2.0    -rph/2.0    pt fixed\n"
        evolverScript += "1006 piw/2.0    -rph/2.0     pt fixed\n"
        evolverScript += "1007 piw/2.0    rph/2.0     pt fixed\n"
        evolverScript += "1008 rpw+piw/2.0    rph/2.0     pt fixed\n"
        evolverScript += "//right finish\n"
        evolverScript += "1009 cbw/2.0+rtt+rbt+rft    -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft fixed\n"
        evolverScript += "1010 cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft    -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft fixed\n"
        evolverScript += "1011 cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft    cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft fixed\n"
        evolverScript += "1012 cbw/2.0+rtt+rbt+rft    cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft fixed\n"
        evolverScript += "1013 cbw/2.0+rtt+rbt+rft    -cbh/2.0-rtt-rbt-rft    rightTotalThickness+cbt+rtt+rbt+rft fixed\n"
        evolverScript += "1014 cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft   -cbh/2.0-rtt-rbt-rft    rightTotalThickness+cbt+rtt+rbt+rft fixed\n"
        evolverScript += "1015 cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft    cbh/2.0+rtt+rbt+rft    rightTotalThickness+cbt+rtt+rbt+rft fixed\n"
        evolverScript += "1016 cbw/2.0+rtt+rbt+rft    cbh/2.0+rtt+rbt+rft    rightTotalThickness+cbt+rtt+rbt+rft fixed\n"


        evolverScript += "//left solder\n"
        evolverScript += "101 -lpw-piw/2.0    -lph/2.0    pt    constraints 5   105\n"
        evolverScript += "102 -lpw*(1.0-solderBottomWidthRatio)-piw/2.0    -lph/2.0     pt    constraints 5   105\n"
        evolverScript += "103 -lpw*(1.0-solderBottomWidthRatio)-piw/2.0    lph/2.0    pt    constraints 5   105\n"
        evolverScript += "104 -lpw-piw/2.0    lph/2.0    pt    constraints 5   105\n"
        evolverScript += "105 -cbw/2.0-ltt-lbt-lft   -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft  constraints 12  8   10\n"
        evolverScript += "106 -cbw/2.0-ltt-lbt-lft+solderWidthRatio*(ltw+lbw+lfw+2.0*ltt+2.0*lbt+2.0*lft)   -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft  constraints 12\n"
        evolverScript += "107 -cbw/2.0-ltt-lbt-lft+solderWidthRatio*(ltw+lbw+lfw+2.0*ltt+2.0*lbt+2.0*lft)   cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft  constraints 12\n"
        evolverScript += "108 -cbw/2.0-ltt-lbt-lft   cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft  constraints 12  8   9\n"
        evolverScript += "109 -cbw/2.0-ltt-lbt-lft   -cbh/2.0-ltt-lbt-lft    leftTotalThickness-ltt-lbt-lft+solderThicknessRatio*(cbt+2.0*ltt+2.0*lbt+2.0*lft)  constraints 8   10\n"
        evolverScript += "110 -cbw/2.0-ltt-lbt-lft   cbh/2.0+ltt+lbt+lft    leftTotalThickness-ltt-lbt-lft+solderThicknessRatio*(cbt+2.0*ltt+2.0*lbt+2.0*lft)  constraints 8    9\n"

        evolverScript += "//right solder\n"
        evolverScript += "1101  rpw+piw/2.0   -rph/2.0  pt  constraints 1005   1105\n"
        evolverScript += "1102  rpw*(1.0-solderBottomWidthRatio)+piw/2.0   -rph/2.0  pt  constraints 1005   1105\n"
        evolverScript += "1103  rpw*(1.0-solderBottomWidthRatio)+piw/2.0   rph/2.0  pt  constraints 1005   1105\n"
        evolverScript += "1104  rpw+piw/2.0   rph/2.0  pt  constraints 1005   1105\n"
        evolverScript += "1105  cbw/2.0+rtt+rbt+rft   -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft  constraints 1012  1008   1010\n"
        evolverScript += "1106  cbw/2.0+rtt+rbt+rft-solderWidthRatio*(rtw+rbw+rfw+2.0*rtt+2.0*rbt+2.0*rft)   -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft  constraints 1012\n"
        evolverScript += "1107  cbw/2.0+rtt+rbt+rft-solderWidthRatio*(rtw+rbw+rfw+2.0*rtt+2.0*rbt+2.0*rft)  cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft  constraints 1012\n"
        evolverScript += "1108  cbw/2.0+rtt+rbt+rft   cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft  constraints 1012  1008   1009\n"
        evolverScript += "1109  cbw/2.0+rtt+rbt+rft   -cbh/2.0-rtt-rbt-rft    rightTotalThickness-rtt-rbt-rft+solderThicknessRatio*(cbt+2.0*rtt+2.0*rbt+2.0*rft)  constraints 1008   1010\n"
        evolverScript += "1110  cbw/2.0+rtt+rbt+rft   cbh/2.0+rtt+rbt+rft    rightTotalThickness-rtt-rbt-rft+solderThicknessRatio*(cbt+2.0*rtt+2.0*rbt+2.0*rft)  constraints 1008    1009\n"

        evolverScript += "100001    x0  -1000 zl0\n"
        evolverScript += "100002    x0  1000  zl0\n"
        evolverScript += "100003    x0  -1000 zr0\n"
        evolverScript += "100004    x0  1000  zr0\n"
        evolverScript += "edges\n"
        evolverScript += "100001    100001  100002\n"
        evolverScript += "100002    100003  100004\n"
        evolverScript += "//left pad \n"
        evolverScript += "1  1  2   fixed   no_refine\n"
        evolverScript += "2  2  3   fixed   no_refine\n"
        evolverScript += "3  3  4   fixed   no_refine\n"
        evolverScript += "4  4  1   fixed   no_refine\n"
        evolverScript += "5  5  6   fixed   no_refine\n"
        evolverScript += "6  6  7   fixed   no_refine\n"
        evolverScript += "7  7  8   fixed   no_refine\n"
        evolverScript += "8  8  5   fixed   no_refine\n"
        evolverScript += "9  1  5   fixed   no_refine\n"
        evolverScript += "10  2  6   fixed   no_refine\n"
        evolverScript += "11  3  7   fixed   no_refine\n"
        evolverScript += "12  4  8   fixed   no_refine\n"
        evolverScript += "//left finish\n" 
        evolverScript += "13  9  10   fixed   no_refine\n"
        evolverScript += "14  10  11   fixed   no_refine\n"
        evolverScript += "15  11  12   fixed   no_refine\n"
        evolverScript += "16  12  9   fixed   no_refine\n"
        evolverScript += "17  13  14   fixed   no_refine\n"
        evolverScript += "18  14  15   fixed   no_refine\n"
        evolverScript += "19  15  16   fixed   no_refine\n"
        evolverScript += "20  16  13   fixed   no_refine\n"
        evolverScript += "21  9  13   fixed   no_refine\n"
        evolverScript += "22  10  14   fixed   no_refine\n"
        evolverScript += "23  11  15   fixed   no_refine\n"
        evolverScript += "24  12  16   fixed   no_refine\n"
        evolverScript += "// right pad\n"
        evolverScript += "1001  1001  1002   fixed   no_refine\n"
        evolverScript += "1002  1002  1003   fixed   no_refine\n"
        evolverScript += "1003  1003  1004   fixed   no_refine\n"
        evolverScript += "1004  1004  1001   fixed   no_refine\n"
        evolverScript += "1005  1005  1006   fixed   no_refine\n"
        evolverScript += "1006  1006  1007   fixed   no_refine\n"
        evolverScript += "1007  1007  1008   fixed   no_refine\n"
        evolverScript += "1008  1008  1005   fixed   no_refine\n"
        evolverScript += "1009  1001  1005   fixed   no_refine\n"
        evolverScript += "1010  1002  1006   fixed   no_refine\n"
        evolverScript += "1011  1003  1007   fixed   no_refine\n"
        evolverScript += "1012  1004  1008   fixed   no_refine\n"
        evolverScript += "// right finish\n"
        evolverScript += "1013  1009  1010   fixed   no_refine\n"
        evolverScript += "1014  1010  1011   fixed   no_refine\n"
        evolverScript += "1015  1011  1012   fixed   no_refine\n"
        evolverScript += "1016  1012  1009   fixed   no_refine\n"
        evolverScript += "1017  1013  1014   fixed   no_refine\n"
        evolverScript += "1018  1014  1015   fixed   no_refine\n"
        evolverScript += "1019  1015  1016   fixed   no_refine\n"
        evolverScript += "1020  1016  1013   fixed   no_refine\n"
        evolverScript += "1021  1009  1013   fixed   no_refine\n"
        evolverScript += "1022  1010  1014   fixed   no_refine\n"
        evolverScript += "1023  1011  1015   fixed   no_refine\n"
        evolverScript += "1024  1012  1016   fixed   no_refine\n"
        evolverScript += "// left solder below\n"
        evolverScript += "101   101 102 constraints 5   105 106\n"
        evolverScript += "102   102 103 constraints 5   105 106\n"
        evolverScript += "103   103 104 constraints 5   105 106\n"
        evolverScript += "104   104 101 constraints 5   105 106\n"
        evolverScript += "105 101 109\n"
        evolverScript += "106 104 110\n"
        evolverScript += "107 109 110 constraints 8 108\n"
        evolverScript += "109 106 102\n"
        evolverScript += "111 107 103\n"
        evolverScript += "112 106 107 constraints 12 112\n"
        evolverScript += "114 108 105 constraints 12 8\n"
        evolverScript += "108 109 106 constraints 10 110\n"
        evolverScript += "115 105 106 constraints 12 10\n"
        evolverScript += "116 105 109 constraints 8 10\n"
        evolverScript += "110 110 107 constraints 9 109\n"
        evolverScript += "113 107 108 constraints 12 9 \n"
        evolverScript += "117 108 110 constraints 8 9 \n"
        evolverScript += "// right solder below\n"
        evolverScript += "1101 1101 1102 constraints 1005 1105 1106 \n"
        evolverScript += "1102 1102 1103 constraints 1005 1105 1106 \n"
        evolverScript += "1103 1103 1104 constraints 1005 1105 1106 \n"
        evolverScript += "1104 1104 1101 constraints 1005 1105 1106 \n"
        evolverScript += "1105 1101 1109 \n"
        evolverScript += "1106 1104 1110 \n"
        evolverScript += "1107 1109 1110 constraints 1008 1108 \n"
        evolverScript += "1109 1106 1102 \n"
        evolverScript += "1111 1107 1103 \n"
        evolverScript += "1112 1106 1107 constraints 1012 1112 \n"
        evolverScript += "1114 1108 1105 constraints 1012 1008 \n"
        evolverScript += "1108 1109 1106 constraints 1010 1110 \n"
        evolverScript += "1115 1105 1106 constraints 1012 1010 \n"
        evolverScript += "1116 1105 1109 constraints 1008 1010 \n"
        evolverScript += "1110 1110 1107 constraints 1009 1109 \n"
        evolverScript += "1113 1107 1108 constraints 1012 1009  \n"
        evolverScript += "1117 1108 1110 constraints 1008 1009  \n"
        evolverScript += "faces\n"
        evolverScript += "// left pad\n"
        evolverScript += "/*\n"
        evolverScript += "1 -4 -3 -2 -1 color red fixed no_refine\n"
        evolverScript += "2 5 6 7 8 color red fixed no_refine\n"
        evolverScript += "3 1 10 -5 -9 color red fixed no_refine\n"
        evolverScript += "4 2 11 -6 -10 color red fixed no_refine\n"
        evolverScript += "5 3 12 -7 -11 color red fixed no_refine\n"
        evolverScript += "6 4 9 -8 -12 color red fixed no_refine\n"
        evolverScript += "// left finish\n" 
        evolverScript += "7 -16 -15 -14 -13 color lightred fixed no_refine\n"
        evolverScript += "8 17 18 19 20 color lightred fixed no_refine\n"
        evolverScript += "9 13 22 -17 -21 color lightred fixed no_refine\n"
        evolverScript += "10 14 23 -18 -22 color lightred fixed no_refine\n"
        evolverScript += "11 15 24 -19 -23 color lightred fixed no_refine\n"
        evolverScript += "12 16 21 -20 -24 color lightred fixed no_refine\n"
        evolverScript += "// right pad\n"
        evolverScript += "1001 1001 1002 1003 1004 color red fixed no_refine\n"
        evolverScript += "1002 -1008 -1007 -1006 -1005 color red fixed no_refine\n"
        evolverScript += "1003 1009 1005 -1010 -1001 color red fixed no_refine\n"
        evolverScript += "1004 1010 1006 -1011 -1002 color red fixed no_refine\n"
        evolverScript += "1005 1011 1007 -1012 -1003 color red fixed no_refine\n"
        evolverScript += "1006 1012 1008 -1009 -1004 color red fixed no_refine\n"
        evolverScript += "// right finish\n"
        evolverScript += "1007 1013 1014 1015 1016 color lightred fixed no_refine\n"
        evolverScript += "1008 -1020 -1019 -1018 -1017 color lightred fixed no_refine\n"
        evolverScript += "1009 1021 1017 -1022 -1013 color lightred fixed no_refine\n"
        evolverScript += "1010 1022 1018 -1023 -1014 color lightred fixed no_refine\n"
        evolverScript += "1011 1023 1019 -1024 -1015 color lightred fixed no_refine\n"
        evolverScript += "1012 1024 1020 -1021 -1016 color lightred fixed no_refine\n"
        evolverScript += "*/\n"
        if direction == "left":
            evolverScript += "//left solder \n"
            evolverScript += "// 밑면 \n"
            evolverScript += "101 -104 -103 -102 -101 color blue constraints 5 105 \n"
            evolverScript += "// 좌측면\n"
            evolverScript += "102 104 105 107 -106 color blue constraints 107\n"
            evolverScript += "103 -105 101 -109 -108 color blue\n"
            evolverScript += "104 106 110 111 103 color blue \n"
            evolverScript += "105 -112 109 102 -111 color blue\n"
            evolverScript += "//측면 하단\n"
            evolverScript += "106 108 -115 116 color blue constraints 10 110 \n"
            evolverScript += "//측면 상단\n"
            evolverScript += "107 -117 -113 -110 color blue constraints 9 109\n"
            evolverScript += "//내부 수직면\n"
            evolverScript += "108 -116 -114 117 -107 color blue constraints 8 108\n"
            evolverScript += "109 115 112 113 114 color blue constraints 12 112\n"
        elif direction == "right":
            evolverScript += "//right solder \n"
            evolverScript += "// 밑면 \n"
            evolverScript += "1101 1101 1102 1103 1104 color blue constraints 1005 1105 \n"
            evolverScript += "// 좌측면\n"
            evolverScript += "1102 1106 -1107 -1105 -1104 color blue constraints 1107\n"
            evolverScript += "1103 1108 1109 -1101 1105 color blue\n"
            evolverScript += "1104 -1103 -1111 -1110 -1106 color blue \n"
            evolverScript += "1105 1111 -1102 -1109 1112 color blue\n"
            evolverScript += "//측면 하단\n"
            evolverScript += "1106 -1116 1115 -1108 color blue constraints 1010 1110 \n"
            evolverScript += "//측면 상단\n"
            evolverScript += "1107 1110 1113 1117 color blue constraints 1009 1109\n"
            evolverScript += "//내부 수직면\n"
            evolverScript += "1108 1107 -1117 1114 1116 color blue constraints 1008 1108\n"
            evolverScript += "1109 -1114 -1113 -1112 -1115 color blue constraints 1012 1112\n"
        
        evolverScript += "bodies\n"
        if direction == "left":
            evolverScript += "3 101 102 103 104 105 106 107 108 109 volume v1\n"
        elif direction == "right":
            evolverScript += "4 1101 1102 1103 1104 1105 1106 1107 1108 1109 volume v2\n"
        evolverScript += "read\n"
        evolverScript += "//typical evolution\n"
        evolverScript += """gogo :={{ r; g 15; r; g10;\n"""
        evolverScript += "conj_grad;\n"
        evolverScript += "t 10;\n"
        evolverScript += "u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;\n"
        evolverScript += "t 10;\n"
        evolverScript += "u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;u;\n"
        evolverScript += "}}\n"
        evolverScript += "gogo\n"
        evolverScript += "optimize 1\n"
        evolverScript += "read \"stl.cmd\"\n"
        evolverScript += "stl >>> \"{stlFileName}\"\n"
        evolverScript += "q\n"
        evolverScript += "q\n"
        return evolverScript.format(stlFileName = fileName,
                                    lpw = self.lpw, 
                                    lph = self.lph,
                                    pt = self.pt,
                                    piw = self.piw,
                                    rpw = self.rpw,
                                    rph = self.rph,
                                    cbw = self.cbw,
                                    cbh = self.cbh,
                                    cbt = self.cbt,
                                    ltw = self.ltw,
                                    ltt = self.ltt,
                                    rtw = self.rtw,
                                    rtt = self.rtt,
                                    lbw = self.lbw,
                                    lbt = self.lbt,
                                    rbw = self.rbw,
                                    rbt = self.rbt,
                                    lfw = self.lfw,
                                    lft = self.lft,
                                    rfw = self.rfw,
                                    rft = self.rft,
                                    lst = self.lst,
                                    lsv = self.lsv,
                                    rsv = self.rsv,
                                    solderWidthRatio = solderWidthRatio,
                                    solderThicknessRatio = solderThicknessRatio,
                                    solderBottomWidthRatio = solderBottomWidthRatio,
                                    tens=tens,
                                    SG=SG,
                                    tilt=tilt)
    def MakeLeftSolder(self):
        fileName = "leftSolder.stl"
        script = self.MakeSolderScript(fileName, "left", self.tens, self.solderWidthRatio, self.solderThicknessRatio, self.solderBottomWidthRatio, self.sgValue, self.tilt)
        evolverExe = "./KooAnalysisWeb/Apps/Evolver/evolver64.exe"
        scriptName = "./KooAnalysisWeb/Apps/Evolver/tmpScript.txt"
        cwd = "./KooAnalysisWeb/Apps/Evolver/"
        with open(scriptName, "w") as f:
            f.write(script)
        
        result = subprocess.run([evolverExe,"tmpScript.txt"],cwd=cwd, stdout=subprocess.PIPE)
        fileName = "./KooAnalysisWeb/Apps/Evolver/" + fileName
        fileNameOutput = fileName.replace(".stl",".step")
        leftSolder = convertCAD.ConvertStltoStep(fileName,fileNameOutput)

        trsf = gp_Trsf()
        pnt = gp_Pnt(0,0,0)
        dir = gp_Dir(0,1,1)
        axis = gp_Ax1(pnt,dir)
        trsf.SetMirror(axis)
        transformed_shape = BRepBuilderAPI.BRepBuilderAPI_Transform(leftSolder,trsf).Shape()

        display.DisplayShape(transformed_shape,None,None)
        return transformed_shape
    
    def MakeRightSolder(self):
        fileName = "rightSolder.stl"
        script = self.MakeSolderScript(fileName, "right", self.tens, self.solderWidthRatio, self.solderThicknessRatio, self.solderBottomWidthRatio, self.sgValue, self.tilt)
        
        evolverExe = "./KooAnalysisWeb/Apps/Evolver/evolver64.exe"
        scriptName = "./KooAnalysisWeb/Apps/Evolver/tmpScript.txt"
        cwd = "./KooAnalysisWeb/Apps/Evolver/"
        with open(scriptName, "w") as f:
            f.write(script)
        
        result = subprocess.run([evolverExe,"tmpScript.txt"],cwd=cwd, stdout=subprocess.PIPE)
        fileName = "./KooAnalysisWeb/Apps/Evolver/" + fileName
        fileNameOutput = fileName.replace(".stl",".step")
        rightSolder = convertCAD.ConvertStltoStep(fileName,fileNameOutput)
        trsf = gp_Trsf()
        pn = gp_Pnt(0,0,0)
        dir = gp_Dir(0,1,1)
        axis = gp_Ax1(pn,dir)
        trsf.SetMirror(axis)
        transformed_shape = BRepBuilderAPI.BRepBuilderAPI_Transform(rightSolder,trsf).Shape()
        display.DisplayShape(transformed_shape,None,None)
        return transformed_shape
    
    def MakeMLCCShape(self,compound):
        builder = BRep_Builder()
        lp = self.MakeLeftPad()
        rp = self.MakeRightPad()
        cb = self.MakeCeramicBody()
        lt = self.MakeLeftTerminal()
        rt = self.MakeRightTerminal()
        lb = self.MakeLeftBarrier()
        rb = self.MakeRightBarrier()
        lf = self.MakeLeftFinish()
        rf = self.MakeRightFinish()

        builder.Add(compound,lp.Shape())
        builder.Add(compound,rp.Shape())
        builder.Add(compound,cb.Shape())

        clt = BRepAlgoAPI_Cut(lt.Shape(),cb.Shape())
        crt = BRepAlgoAPI_Cut(rt.Shape(),cb.Shape())
        builder.Add(compound,clt.Shape())
        builder.Add(compound,crt.Shape())

        clb = BRepAlgoAPI_Cut(lb.Shape(),cb.Shape())
        crb = BRepAlgoAPI_Cut(rb.Shape(),cb.Shape())
        clb =   BRepAlgoAPI_Cut(clb.Shape(),lt.Shape())
        crb =   BRepAlgoAPI_Cut(crb.Shape(),rt.Shape())
        builder.Add(compound,clb.Shape())
        builder.Add(compound,crb.Shape())

        clf = BRepAlgoAPI_Cut(lf.Shape(),cb.Shape())
        crf = BRepAlgoAPI_Cut(rf.Shape(),cb.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lt.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rt.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lb.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rb.Shape())
        builder.Add(compound,clf.Shape())
        builder.Add(compound,crf.Shape())
        return compound


    
    def MakeSolder(self,MLCCFileName):
        compound = TopoDS_Compound()
        builder = BRep_Builder()
        builder.MakeCompound(compound)
        shapeLeft = self.MakeLeftSolder()
        builder.Add(compound,shapeLeft)
        shapeRight = self.MakeRightSolder()
        builder.Add(compound,shapeRight)
        compound = self.MakeMLCCShape(compound)
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
        from OCC.Core.gp import gp_Trsf

        # Assuming you have a compound named 'my_compound' and a scaling factor of 1000
        scaling_factor = 0.001

        # Create a scaling transformation
        scaling_transform = gp_Trsf()
        scaling_transform.SetScale(gp_Pnt(0, 0, 0), scaling_factor)

        # Apply the transformation to the compound
        transform_builder = BRepBuilderAPI_Transform(compound, scaling_transform)
        scaled_compound = transform_builder.Shape()

        self.compund = scaled_compound
        step_writer = STEPControl_Writer()
        step_writer.Transfer(scaled_compound,STEPControl_AsIs)
        step_writer.Write(MLCCFileName)
        
                                    

    def Set0402(self):
        xValue = 400 
        yValue = 200
        zValue = 200 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set0603(self):
        xValue = 600 
        yValue = 300
        zValue = 300 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set0805(self):
        xValue = 800 
        yValue = 500
        zValue = 500 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1206(self):
        xValue = 1200 
        yValue = 600
        zValue = 600 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1210(self):
        xValue = 1200 
        yValue = 1000
        zValue = 600 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1806(self):
        xValue = 1800 
        yValue = 600
        zValue = 600 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1812(self):
        xValue = 1800 
        yValue = 1200
        zValue = 1200 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set1825(self):
        xValue = 1800 
        yValue = 2500
        zValue = 2500 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set2220(self):
        xValue = 2200 
        yValue = 2000
        zValue = 2000 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set2225(self):
        xValue = 2200 
        yValue = 2500
        zValue = 2500 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def Set3640(self):
        xValue = 3600 
        yValue = 4000
        zValue = 4000 
        self.SetCapSizebyXYZ(xValue, yValue, zValue)
    def SetCapSizebyXYZ(self, xValue, yValue, zValue):
        self.lpw = xValue*3.0/5.0
        self.lph = xValue*4.0/5.0
        self.rpw = xValue*3.0/5.0
        self.rph = xValue*4.0/5.0
        self.piw = xValue/4.0
        self.pt = 30.0
        self.cbw = xValue
        self.cbh = yValue
        self.cbt = zValue
        self.ltw = xValue/8.0
        self.ltt = 10.0
        self.rtw = xValue/8.0
        self.rtt = 10.0
        self.lbw = 20.0
        self.lbt = 10.0
        self.rbw = 20.0
        self.rbt = 10.0
        self.lfw = 20.0
        self.lft = 10.0
        self.rfw = 20.0
        self.rft = 10.0
        self.lst = 30.0
        self.lsv = math.pow(xValue*yValue*zValue,1./3.0)/3
        self.rst = 30.0
        self.rsv = self.lsv
        pass    




if __name__ =="__main__":
    capForm = CapacitorForm()
    capForm.Set0402()
    capForm.MakeMLCC("MLCC")
    capForm.MakeSolder("MLCCTest.step")
    start_display()

