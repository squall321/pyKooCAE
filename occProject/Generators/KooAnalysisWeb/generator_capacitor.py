from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, NumberRange

import os
import os.path
getcwd = os.getcwd()
path = os.path.join(getcwd, "Library", "OCC")
os.add_dll_directory(path)
defaultPath = os.path.join('static','images','Name_','index.html')

import pyvista as pv

from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.gp import gp_Pnt
from OCC.Display.WebGl import threejs_renderer
from OCC.Display.WebGl import x3dom_renderer
from OCC.Core.AIS import AIS_ColoredShape
from OCC.Display.OCCViewer import rgb_color
from OCC.Extend.TopologyUtils import TopologyExplorer

from OCC.Core.BRepAlgoAPI import (
    BRepAlgoAPI_Fuse,
    BRepAlgoAPI_Cut,
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Section,
)

import math

class CapacitorForm(FlaskForm):
    visualURL = StringField('VisualizeView',default=defaultPath)
    name = StringField('Capacitor Name',default="Name")
    leftPadWidth = FloatField('Left CU Pad Width',validators=[DataRequired()])
    leftPadHeight = FloatField('Left CU Pad Height',validators=[DataRequired()])

    rightPadWidth = FloatField('Right CU Pad Width',validators=[DataRequired()])
    rightPadHeight = FloatField('Right CU Pad Height',validators=[DataRequired()])

    padIntervalWidth = FloatField('Pad Interval Width',validators=[DataRequired()])
    padThickness = FloatField('Pad Thickness',validators=[DataRequired()])

    ceramicBodyWidth = FloatField('Ceramic Body Width',validators=[DataRequired()])
    ceramicBodyHeight = FloatField('Ceramic Body Height',validators=[DataRequired()])
    ceramicBodyThickness = FloatField('Ceramic Body Thickness',validators=[DataRequired()])

    leftTerminationWidth = FloatField('Left Termination Width',validators=[DataRequired()])
    leftTerminationThickness = FloatField('Left Termination Thickness',validators=[DataRequired()])
    
    rightTerminationWidth = FloatField('Right Termination Width',validators=[DataRequired()])
    rightTerminationThickness = FloatField('Right Termination Thickness',validators=[DataRequired()])

    leftBarrierWidth = FloatField('Left Barrier Width',validators=[DataRequired()])
    leftBarrierThickness = FloatField('Left Barrier Thickness',validators=[DataRequired()])

    rightBarrierWidth = FloatField('Right Barrier Width',validators=[DataRequired()])
    rightBarrierThickness = FloatField('Right Barrier Thickness',validators=[DataRequired()])

    leftFinishWidth = FloatField('Left Finish Width',validators=[DataRequired()])
    leftFinishThickness = FloatField('Left Finish Thickness',validators=[DataRequired()])

    rightFinishWidth = FloatField('Right Finish Width',validators=[DataRequired()])
    rightFinishThickness = FloatField('Right Finish Thickness',validators=[DataRequired()])

    leftSolderThickness = FloatField('Left Solder Thickness',validators=[DataRequired()])
    leftSolderVolume = FloatField('Left Solder Volume',validators=[DataRequired()])

    rightSolderThickness = FloatField('Right Solder Thickness',validators=[DataRequired()])    
    rightSolderVolume = FloatField('Right Solder Volume',validators=[DataRequired()])
    
    submit_generate = SubmitField('Generate',render_kw={'id':'generate'})
    submit_initialize = SubmitField('Initialize')
    select_typicalSizeCap = SelectField('Select Type')

    def __init__(self,name="",lpw=0,lph=0,rpw=0,rph=0,piw=0,pt=0,cbw=0,cbh=0,cbt=0,ltw=0,ltt=0,rtw=0,rtt=0,lbw=0,lbt=0,rbw=0,rbt=0,lfw=0,lft=0,rfw=0,rft=0,lst=0,lsv=0,rst=0,rsv=0):
        super(CapacitorForm,self).__init__()
        self.select_typicalSizeCap.choices = [('None','None'),('0402','0402'),('0603','0603'),('0805','0805'),('1206','1206'),('1210','1210'),('1806','1806'),('1812','1812'),('1825','1825'),('2220','2220'),('2225','2225'),('3640','3640')]
        if name != "":
            self.name.data = name
        
        if lpw > 0:
            self.leftPadWidth.data = lpw
        if lph > 0:
            self.leftPadHeight.data = lph
        if rpw > 0:
            self.rightPadWidth.data = rpw
        if rph > 0:
            self.rightPadHeight.data = rph
        if piw > 0:
            self.padIntervalWidth.data = piw
        if pt > 0:
            self.padThickness.data = pt
        if cbw > 0:
            self.ceramicBodyWidth.data = cbw
        if cbh > 0:
            self.ceramicBodyHeight.data = cbh
        if cbt > 0:
            self.ceramicBodyThickness.data = cbt
        if ltw > 0:
            self.leftTerminationWidth.data = ltw
        if ltt > 0:
            self.leftTerminationThickness.data = ltt
        if rtw > 0:
            self.rightTerminationWidth.data = rtw
        if rtt > 0:
            self.rightTerminationThickness.data = rtt
        if lbw > 0:
            self.leftBarrierWidth.data = lbw
        if lbt > 0:
            self.leftBarrierThickness.data = lbt
        if rbw > 0:
            self.rightBarrierWidth.data = rbw
        if rbt > 0:
            self.rightBarrierThickness.data = rbt
        if lfw > 0:
            self.leftFinishWidth.data = lfw
        if lft > 0:
            self.leftFinishThickness.data = lft
        if rfw > 0:
            self.rightFinishWidth.data = rfw
        if rft > 0:
            self.rightFinishThickness.data = rft
        if lst > 0:
            self.leftSolderThickness.data = lst
        if lsv > 0:
            self.leftSolderVolume.data = lsv
        if rst > 0:
            self.rightSolderThickness.data = rst
        if rsv > 0:
            self.rightSolderVolume.data = rsv

    def MakeFillet(self,box,indexList,fillet):
        fbox = BRepFilletAPI_MakeFillet(box.Shape())
        expl = list(TopologyExplorer(box.Shape()).edges())        
        for i in indexList:
            fbox.Add(fillet,fillet,expl[i])
        fbox.Build()
        if fbox.IsDone():
            return fbox
        else:
            print("Fillet Failed")
            return box
        
    def GetTotalThickness(self):
        ltt = self.leftTerminationThickness.data
        rtt = self.rightTerminationThickness.data
        lbt = self.leftBarrierThickness.data
        rbt = self.rightBarrierThickness.data
        lft = self.leftFinishThickness.data
        rft = self.rightFinishThickness.data
        lst = self.leftSolderThickness.data
        rst = self.rightSolderThickness.data
        pt = self.padThickness.data

        totalthick = max(ltt,rtt)
        totalthick += max(lbt,rbt)
        totalthick += max(lft,rft)
        totalthick += max(lst,rst)
        totalthick += pt
        return totalthick
    
    def MakeLeftPad(self):
        lpw = self.leftPadWidth.data
        lph = self.leftPadHeight.data
        piw = self.padIntervalWidth.data
        pt = self.padThickness.data
        pl1 = gp_Pnt(-piw/2.0,0.0,lph/2.0)
        pl2 = gp_Pnt(-lpw-piw/2.0,pt,-lph/2.0)
        return BRepPrimAPI_MakeBox(pl1,pl2)
    
    def MakeRightPad(self):
        rpw = self.rightPadWidth.data
        rph = self.rightPadHeight.data
        piw = self.padIntervalWidth.data
        pt = self.padThickness.data
        pr1 = gp_Pnt(piw/2.0,0.0,rph/2.0)
        pr2 = gp_Pnt(rpw+piw/2.0,pt,-rph/2.0)
        return BRepPrimAPI_MakeBox(pr1,pr2)
    
    def MakeCeramicBody(self):
        cbw = self.ceramicBodyWidth.data
        cbh = self.ceramicBodyHeight.data
        cbt = self.ceramicBodyThickness.data

        totalThick = self.GetTotalThickness()
        pl3 = gp_Pnt(-cbw/2.0,totalThick,-cbh/2.0)
        pr3 = gp_Pnt(cbw/2.0,totalThick+cbt,cbh/2.0)
        return BRepPrimAPI_MakeBox(pl3,pr3)
    
    def MakeLeftTermination(self):
        cbw = self.ceramicBodyWidth.data
        cbh = self.ceramicBodyHeight.data
        cbt = self.ceramicBodyThickness.data

        ltt = self.leftTerminationThickness.data
        ltw = self.leftTerminationWidth.data
        totalThick = self.GetTotalThickness()
        p141 = gp_Pnt(-cbw/2.0-ltt,totalThick+cbt+ltt,cbh/2.0+ltt)
        p142 = gp_Pnt(-cbw/2.0+ltw+ltt,totalThick-ltt,-cbh/2.0-ltt)
        return BRepPrimAPI_MakeBox(p141,p142)
    
    def MakeRightTermination(self):
        cbw = self.ceramicBodyWidth.data
        cbh = self.ceramicBodyHeight.data
        cbt = self.ceramicBodyThickness.data

        rtt = self.rightTerminationThickness.data
        rtw = self.rightTerminationWidth.data
        totalThick = self.GetTotalThickness()
        pr41 = gp_Pnt(cbw/2.0+rtt,totalThick+cbt+rtt,cbh/2.0+rtt)
        pr42 = gp_Pnt(cbw/2.0-rtw-rtt,totalThick-rtt,-cbh/2.0-rtt)
        return BRepPrimAPI_MakeBox(pr41,pr42)
    
    def MakeLeftBarrier(self):
        cbw = self.ceramicBodyWidth.data
        cbh = self.ceramicBodyHeight.data
        cbt = self.ceramicBodyThickness.data
        ltt = self.leftTerminationThickness.data
        ltw = self.leftTerminationWidth.data
        lbt = self.leftBarrierThickness.data
        lbw = self.leftBarrierWidth.data
        totalThick = self.GetTotalThickness()
        pl51 = gp_Pnt(-cbw/2.0-ltt-lbt,totalThick+cbt+ltt+lbt,cbh/2.0+ltt+lbt)
        pl52 = gp_Pnt(-cbw/2.0+ltw+lbw+ltt+lbt,totalThick-ltt-lbt,-cbh/2.0-ltt-lbt)
        return BRepPrimAPI_MakeBox(pl51,pl52)
    
    def MakeRightBarrier(self):
        cbw = self.ceramicBodyWidth.data
        cbh = self.ceramicBodyHeight.data
        cbt = self.ceramicBodyThickness.data
        rtt = self.rightTerminationThickness.data
        rtw = self.rightTerminationWidth.data
        rbt = self.rightBarrierThickness.data
        rbw = self.rightBarrierWidth.data
        totalThick = self.GetTotalThickness()
        pr51 = gp_Pnt(cbw/2.0+rtt+rbt,totalThick+cbt+rtt+rbt,cbh/2.0+rtt+rbt)
        pr52 = gp_Pnt(cbw/2.0-rtw-rbw-rtt-rbt,totalThick-rtt-rbt,-cbh/2.0-rtt-rbt)
        return BRepPrimAPI_MakeBox(pr51,pr52)
    
    def MakeLeftFinish(self):
        cbw = self.ceramicBodyWidth.data
        cbh = self.ceramicBodyHeight.data
        cbt = self.ceramicBodyThickness.data
        ltt = self.leftTerminationThickness.data
        ltw = self.leftTerminationWidth.data
        lbt = self.leftBarrierThickness.data
        lbw = self.leftBarrierWidth.data
        lft = self.leftFinishThickness.data
        lfw = self.leftFinishWidth.data
        totalThick = self.GetTotalThickness()
        p161 = gp_Pnt(-cbw/2.0-ltt-lbt-lft,totalThick+cbt+ltt+lbt+lft,cbh/2.0+ltt+lbt+lft)
        p162 = gp_Pnt(-cbw/2.0+ltw+lbw+lfw+ltt+lbt+lft,totalThick-ltt-lbt-lft,-cbh/2.0-ltt-lbt-lft)
        box = BRepPrimAPI_MakeBox(p161,p162)
        fillet = 10 
        return self.MakeFillet(box,[0,1,2,3,4,5,6,7,8,9,10,11],fillet)
    
    def MakeRightFinish(self):
        cbw = self.ceramicBodyWidth.data
        cbh = self.ceramicBodyHeight.data
        cbt = self.ceramicBodyThickness.data
        rtt = self.rightTerminationThickness.data
        rtw = self.rightTerminationWidth.data
        rbt = self.rightBarrierThickness.data
        rbw = self.rightBarrierWidth.data
        rft = self.rightFinishThickness.data
        rfw = self.rightFinishWidth.data
        totalThick = self.GetTotalThickness()
        pr61 = gp_Pnt(cbw/2.0+rtt+rbt+rft,totalThick+cbt+rtt+rbt+rft,cbh/2.0+rtt+rbt+rft)
        pr62 = gp_Pnt(cbw/2.0-rtw-rbw-rfw-rtt-rbt-rft,totalThick-rtt-rbt-rft,-cbh/2.0-rtt-rbt-rft)
        box = BRepPrimAPI_MakeBox(pr61,pr62)
        fillet = 10
        return self.MakeFillet(box,[0,1,2,3,4,5,6,7,8,9,10,11],fillet)

    def MakeBox(self,name):
        box = BRepPrimAPI_MakeBox(self.leftPadWidth.data,self.leftPadHeight.data,self.padThickness.data).Shape()
        curPath = os.path.join('static','images',name)
        if not os.path.isdir(curPath):
            os.makedirs(curPath)
        renderer = threejs_renderer.ThreejsRenderer(curPath)

        curHtmlPath = os.path.join(curPath,'index.html')
        print(curHtmlPath)
        renderer.DisplayShape(box)
        renderer.generate_html_file()
        return curHtmlPath
    
    def MakeMLCC(self,name):
        curPath = os.path.join('static','images',name)
        if not os.path.isdir(curPath):
            os.makedirs(curPath)
        print(curPath)
        #renderer = threejs_renderer.ThreejsRenderer(curPath)
        renderer = x3dom_renderer.X3DomRenderer(curPath)

        lp = self.MakeLeftPad()
        rp = self.MakeRightPad()
        cb = self.MakeCeramicBody()
        lt = self.MakeLeftTermination()
        rt = self.MakeRightTermination()
        lb = self.MakeLeftBarrier()
        rb = self.MakeRightBarrier()
        lf = self.MakeLeftFinish()
        rf = self.MakeRightFinish()

        curHtmlPath = os.path.join(curPath,'index.html')
        print(curHtmlPath)
        renderer.DisplayShape(lp.Shape(),export_edges=True,color=(1,0,0))
        renderer.DisplayShape(rp.Shape(),export_edges=True,color=(1,0,0))
        rreal = 145.0 / 255.0
        greal = 102.0 / 255.0
        breal = 83.0 / 255.0
        renderer.DisplayShape(cb.Shape(),export_edges=True,color=(rreal,greal,breal))

        clt = BRepAlgoAPI_Cut(lt.Shape(),cb.Shape())
        crt = BRepAlgoAPI_Cut(rt.Shape(),cb.Shape())

        rreal = 26.0 / 255.0
        greal = 52.0 / 255.0
        breal = 109.0 / 255.0

        renderer.DisplayShape(clt.Shape(),export_edges=True,color=(rreal,greal,breal))
        renderer.DisplayShape(crt.Shape(),export_edges=True,color=(rreal,greal,breal))

        clb = BRepAlgoAPI_Cut(lb.Shape(),cb.Shape())
        crb = BRepAlgoAPI_Cut(rb.Shape(),cb.Shape())
        clb = BRepAlgoAPI_Cut(clb.Shape(),lt.Shape())
        crb = BRepAlgoAPI_Cut(crb.Shape(),rt.Shape())

        rreal = 245.0 / 255.0
        greal = 104.0 / 255.0
        breal = 12.0 / 255.0

        renderer.DisplayShape(clb.Shape(),export_edges=True,color=(rreal,greal,breal))
        renderer.DisplayShape(crb.Shape(),export_edges=True,color=(rreal,greal,breal))

        clf = BRepAlgoAPI_Cut(lf.Shape(),cb.Shape())
        crf = BRepAlgoAPI_Cut(rf.Shape(),cb.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lt.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rt.Shape())
        clf = BRepAlgoAPI_Cut(clf.Shape(),lb.Shape())
        crf = BRepAlgoAPI_Cut(crf.Shape(),rb.Shape())
        print(clf)
        print(crf)

        rreal = 181.0 / 255.0
        greal = 178.0 / 255.0
        breal = 189.0 / 255.0
        renderer.DisplayShape(clf.Shape(),export_edges=True,color=(rreal,greal,breal))
        renderer.DisplayShape(crf.Shape(),export_edges=True,color=(rreal,greal,breal))

        renderer.generate_html_file(axes_plane='XY',axes_plane_zoom_factor=1.5)
        print("curHtmlPath:",curHtmlPath)

              
        return curHtmlPath
    
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
        self.leftPadWidth.data = xValue*3.0/5.0
        self.leftPadHeight.data = xValue*4.0/5.0
        self.rightPadWidth.data = xValue*3.0/5.0
        self.rightPadHeight.data = xValue*4.0/5.0
        self.padIntervalWidth.data = xValue/4.0
        self.padThickness.data = 30.0
        self.ceramicBodyWidth.data = xValue
        self.ceramicBodyHeight.data = yValue
        self.ceramicBodyThickness.data = zValue
        self.leftTerminationWidth.data = xValue/8.0
        self.leftTerminationThickness.data = 10.0
        self.rightTerminationWidth.data = xValue/8.0
        self.rightTerminationThickness.data = 10.0
        self.leftBarrierWidth.data = 20.0
        self.leftBarrierThickness.data = 10.0
        self.rightBarrierWidth.data = 20.0
        self.rightBarrierThickness.data = 10.0
        self.leftFinishWidth.data = 20.0
        self.leftFinishThickness.data = 10.0
        self.rightFinishWidth.data = 20.0
        self.rightFinishThickness.data = 10.0
        self.leftSolderThickness.data = 30.0
        self.leftSolderVolume.data = math.pow(xValue*yValue*zValue,1./3.0)/3
        self.rightSolderThickness.data = 30.0
        self.rightSolderVolume.data = self.leftSolderVolume.data
        pass







