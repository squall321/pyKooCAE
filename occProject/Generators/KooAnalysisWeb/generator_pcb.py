from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, FloatField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange

from OCC.Core.gp import gp_Pnt, gp_Ax2, gp_Dir, gp_Circ, gp_Ax3, gp_Pln, gp_Trsf, gp_Vec
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox

import os
import os.path
defaultPath = os.path.join('static','pcb','Name_','empty3DView.html')

from OCC.Display.WebGl import x3dom_renderer

class PCBForm(FlaskForm):
    visualURL = StringField('VisualizeView',default=defaultPath)
    name = StringField('PCB Name', default='Name_')

    submit_generate = SubmitField('Generate',render_kw={'id':'generate'})
    submit_initialize = SubmitField('Initialize')
    select_typicalTypeofPCB = SelectField("Select Type")
  

    def __init__(self,name=""):
        super(PCBForm,self).__init__()
        self.select_typicalTypeofPCB.choices = [('None','None'),('Cap Noise Test Board','Cap Noise Test Board'),('Cap Bending Test Board','Cap Bending Test Board')]
        if name != "":
            self.name.data = name
    def MakeBox(self,xCenterLoc, yCenterLoc, zCenterLoc, xLength, yLength, zLength):
        
        pl1 = gp_Pnt(xCenterLoc - xLength/2, yCenterLoc - yLength/2, zCenterLoc - zLength/2)
        pl2 = gp_Pnt(xCenterLoc + xLength/2, yCenterLoc + yLength/2, zCenterLoc + zLength/2)
        return BRepPrimAPI_MakeBox(pl1, pl2)

    def MakePCB(self,name):
        curPath = os.path.join('static','pcb',name)
        if not os.path.exists(curPath):
            os.makedirs(curPath)
        curHtmlPath = os.path.join(curPath,'index.html')
        box = self.MakeBox(0,0,0,100,100,100)
        renderer = x3dom_renderer.X3DomRenderer(curPath)
        renderer.DisplayShape(box.Shape(), export_edges=True, color=(1,0,0))
        renderer.generate_html_file(axes_plane='XY', axes_plane_zoom_factor=1.5)
        return curHtmlPath
    