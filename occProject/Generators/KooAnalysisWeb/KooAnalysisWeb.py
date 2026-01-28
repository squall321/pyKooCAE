#서버 데이터 접근을 위한 import 
import os
import os.path


from flask import Flask, render_template, request, session, redirect, url_for, flash 

from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, DateTime, Boolean, Float
from sqlalchemy.orm import mapper
from database import BaseDB, db_session, add_user 


import pyvista 
from pyvista import examples 

# glob은 확장자 없는 파일 이름만으로 파일 존재하는지 찾는 패키지 
import glob
# bootstrap.js 기능을 사용할 수 있게 해주는 패키지 (프레임워크) 
from flask_bootstrap import Bootstrap
# Moment.js 기능을 사용할 수 있게 해주는 패키지 (시간)
from flask_moment import Moment
from datetime import datetime

# 홈페이지 자체 모듈 
import KooLogin as klogin
from generator_capacitor import * 
from generator_pcb import *

static_image_path = os.path.join('static','images')
if not os.path.isdir(static_image_path):
    os.makedirs(static_image_path)

static_capacitor_path = os.path.join('static','capacitor')
if not os.path.isdir(static_capacitor_path):
    os.makedirs(static_capacitor_path)

static_pcb_path = os.path.join('static','pcb')
if not os.path.isdir(static_pcb_path):
    os.makedirs(static_pcb_path)

currentCapacitorView = os.path.join(static_image_path,'Name_','index.html')
currentPCBView = os.path.join(static_pcb_path,'Name_','index.html')
app = Flask(__name__)

app.config['SECRET_KEY'] = 'GNFNEPFLZKGNFNEPFLZKSOSEKS#!$'
                            
bootstrap = Bootstrap(app)
moment = Moment(app)

class User(BaseDB):
    __tablename__ = 'users'
    employee_number = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    id = Column(String(120), unique=True)
    def __init__(self,name=None,id=None,employee_number=None):
        print("유저를 생성합니다.")
        print("유저이름 : {name}".format(name=name))
        self.name = name
        print("유저아이디 : {id}".format(id=id))
        self.id = id
        print("유저사번 : {employee_number}".format(employee_number=employee_number))
        self.employee_number = employee_number
    def __repr__(self):
        return '<User %r>' % (self.name)
    
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html',
                           name=session.get('name'),
                           current_time=datetime.utcnow())

@app.route('/logout',methods=['GET','POST'])
def logout():
    session.clear()
    return index()

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = klogin.NameForm()
    print("로그인 페이지에 접속하였습니다.")
    if form.validate_on_submit():
        name = form.name.data
        id = form.id.data
        eid = form.employee_number.data
        if add_user(name,id,eid):
            old_name = session.get('name')
            if old_name is not None and old_name != name:
                print(old_name)
                print(form.name.data)
                flash('Looks like you have changed your name!')
            session['name'] = form.name.data
            return index()
        else:
            flash('이미 존재하는 아이디입니다.')
            #return redirect(url_for('login'))
    return render_template('user.html',
                           form=form,
                           name=session.get('name'),
                           current_time=datetime.utcnow())

@app.route('/capacitor', methods=['GET', 'PUT', 'POST'])
def capacitor():
    global currentCapacitorView
    print("Test Capacitor On")    
    form = CapacitorForm()
    vURL = currentCapacitorView
    print(vURL)
    form.visualURL = vURL 
    if request.method == 'POST':
      #  print("Test Post On")
        form.validate()
        lpw = float(request.form['leftPadWidth'])
        lph = float(request.form['leftPadHeight'])
        rpw = float(request.form['rightPadWidth'])
        rph = float(request.form['rightPadHeight'])
        piw = float(request.form['padIntervalWidth'])
        pt = float(request.form['padThickness'])
        cbw = float(request.form['ceramicBodyWidth'])
        cbh = float(request.form['ceramicBodyHeight'])
        cbt = float(request.form['ceramicBodyThickness'])
        ltw = float(request.form['leftTerminationWidth'])
        ltt = float(request.form['leftTerminationThickness'])
        rtw = float(request.form['rightTerminationWidth'])
        rtt = float(request.form['rightTerminationThickness'])
        lbw = float(request.form['leftBarrierWidth'])
        lbt = float(request.form['leftBarrierThickness'])
        rbw = float(request.form['rightBarrierWidth'])
        rbt = float(request.form['rightBarrierThickness'])
        lfw = float(request.form['leftFinishWidth'])
        lft = float(request.form['leftFinishThickness'])
        rfw = float(request.form['rightFinishWidth'])
        rft = float(request.form['rightFinishThickness'])
        lst = float(request.form['leftSolderThickness'])
        lsv = float(request.form['leftSolderVolume'])
        rst = float(request.form['rightSolderThickness'])
        rsv = float(request.form['rightSolderVolume'])
        selectedValue =  form.select_typicalSizeCap.data
        if selectedValue == "0402":
            print("0402 is selected")
            form.Set0402()
        elif selectedValue == "0603":
            print("0603 is selected")
            form.Set0603()
        elif selectedValue == "0805":
            print("0805 is selected")
            form.Set0805()
        elif selectedValue == "1206":
            print("1206 is selected")
            form.Set1206()
        elif selectedValue == "1210":
            print("1210 is selected")
            form.Set1210()
        elif selectedValue == "1806":
            print("1806 is selected")
            form.Set1806()
        elif selectedValue == "1812":
            print("1812 is selected")
            form.Set1812()
        elif selectedValue == "1825":
            print("1825 is selected")
            form.Set1825()
        elif selectedValue == "2220":
            print("2220 is selected")
            form.Set2220()
        elif selectedValue == "2225":
            print("2225 is selected")
            form.Set2225()
        elif selectedValue == "3640":
            print("3640 is selected")
            form.Set3640()
        if selectedValue != "None":
            lpw = form.leftPadWidth.data
            lph = form.leftPadHeight.data
            rpw = form.rightPadWidth.data
            rph = form.rightPadHeight.data
            piw = form.padIntervalWidth.data
            pt = form.padThickness.data
            cbw = form.ceramicBodyWidth.data
            cbh = form.ceramicBodyHeight.data
            cbt = form.ceramicBodyThickness.data
            ltw = form.leftTerminationWidth.data
            ltt = form.leftTerminationThickness.data
            rtw = form.rightTerminationWidth.data
            rtt = form.rightTerminationThickness.data
            lbw = form.leftBarrierWidth.data
            lbt = form.leftBarrierThickness.data
            rbw = form.rightBarrierWidth.data
            rbt = form.rightBarrierThickness.data
            lfw = form.leftFinishWidth.data
            lft = form.leftFinishThickness.data
            rfw = form.rightFinishWidth.data
            rft = form.rightFinishThickness.data
            lst = form.leftSolderThickness.data
            lsv = form.leftSolderVolume.data
            rst = form.rightSolderThickness.data
            rsv = form.rightSolderVolume.data

        elif selectedValue == "None":
        # print(vURL)
            form.leftPadWidth.data = lpw
            form.leftPadHeight.data = lph
            form.rightPadWidth.data = rpw
            form.rightPadHeight.data = rph
            form.padIntervalWidth.data = piw
            form.padThickness.data = pt
            form.ceramicBodyWidth.data = cbw
            form.ceramicBodyHeight.data = cbh
            form.ceramicBodyThickness.data = cbt
            form.leftTerminationWidth.data = ltw
            form.leftTerminationThickness.data = ltt
            form.rightTerminationWidth.data = rtw
            form.rightTerminationThickness.data = rtt
            form.leftBarrierWidth.data = lbw
            form.leftBarrierThickness.data = lbt
            form.rightBarrierWidth.data = rbw
            form.rightBarrierThickness.data = rbt
            form.leftFinishWidth.data = lfw
            form.leftFinishThickness.data = lft
            form.rightFinishWidth.data = rfw
            form.rightFinishThickness.data = rft
            form.leftSolderThickness.data = lst
            form.leftSolderVolume.data = lsv
            form.rightSolderThickness.data = rst
            form.rightSolderVolume.data = rsv
            form.visualURL = vURL
    if form.validate_on_submit():
        #print("Test Validate On")
      
            
        if form.submit_initialize.data:
            #print("Test Validate On Initialize Submit")
            lpw = 877.0
            lph = 800.0
            rpw = 870.0
            rph = 800.0
            piw = 495.0
            pt = 30.0
            cbw = 1800.0
            cbh = 500.0
            cbt = 600.0
            ltw = 300.0
            ltt = 10.0
            rtw = 300.0
            rtt = 10.0
            lbw = 20.0
            lbt = 10.0
            rbw = 20.0
            rbt = 10.0
            lfw = 20.0
            lft = 10.0
            rfw = 20.0
            rft = 10.0
            lst = 30.0
            lsv = 500
            rst = 34.0
            rsv = 500
            form = CapacitorForm("",lpw,lph,rpw,rph,piw,pt,cbw,cbh,cbt,ltw,ltt,rtw,rtt,lbw,lbt,rbw,rbt,lfw,lft,rfw,rft,lst,lsv,rst,rsv)
        elif form.submit_generate.data:
            print("Test Validate On Generate Submit")
            curName = form.name.data
            name = curName.replace(" ","_")
            #currentCapacitorView = form.MakeMLCC(name)            
            currentCapacitorView = form.MakeMLCC(name)
            form.visualURL = currentCapacitorView
            print(currentCapacitorView," is generated")
        return render_template('generatorcapacitor.html',
                               form = form,
                               lpwValue = lpw,
                               lphValue = lph,
                               rpwValue = rpw,
                               rphValue = rph,
                               piwValue = piw,
                               ptValue = pt,
                               cbwValue = cbw,
                               cbhValue = cbh,
                               cbtValue = cbt,
                               ltwValue = ltw,
                               lttValue = ltt,
                               rtwValue = rtw,
                               rttValue = rtt,
                               lbwValue = lbw,
                               lbtValue = lbt,
                               rbwValue = rbw,
                               rbtValue = rbt,
                               lfwValue = lfw,
                               lftValue = lft,
                               rfwValue = rfw,
                               rftValue = rft,
                               lstValue = lst,
                               lsvValue = lsv,
                               rstValue = rst,
                               rsvValue = rsv,
                               current_time=datetime.utcnow())                            
    print("Test Capacitor On 2")
    return render_template('generatorcapacitor.html',
                           form = form, 
                           lpwValue = 877.0,
                           lphValue = 800.0,
                           rpwValue = 870.0,
                           rphValue = 800.0,
                           piwValue = 495.0,
                           ptValue = 30.0,
                           cbwValue = 1800.0,
                           cbhValue = 500.0,
                           cbtValue = 600.0,
                           ltwValue = 300.0,
                           lttValue = 10.0,
                           rtwValue = 300.0,
                           rttValue = 10.0,
                           lbwValue = 20.0,
                           lbtValue = 10.0,
                           rbwValue = 20.0,
                           rbtValue = 10.0,
                           lfwValue = 20.0,
                           lftValue = 10.0,
                           rfwValue = 20.0,
                           rftValue = 10.0,
                           lstValue = 30.0,
                           lsvValue = 500,
                           rstValue = 34.0,
                           rsvValue = 500,
                           current_time=datetime.utcnow())
'''
@app.route("/update-iframe",methods=['POST'])
def update_iframe():
    global currentCapacitorView
    url = currentCapacitorView
    print("update Image for Capacitor")
    print(url)
    return url
'''
@app.route("/getimagecapacitor")
def get_img_capacitor():
    global currentCapacitorView
    print("Test Get Image Capacitor")
    print(currentCapacitorView)
    return redirect(currentCapacitorView)

@app.route('/pcb',methods=['GET','PUT','POST'])
def pcb():
    global currentPCBView
    print("Test PCB On")
    form = PCBForm()
    vURL = currentPCBView
    print(vURL)
    form.visualURL = vURL
    if request.method =='POST':
        pass
    elif request.method =='GET':
        pass
    elif request.method =='PUT':
        pass
    if form.validate_on_submit():
        if form.submit_initialize.data:
            pass
        elif form.submit_generate.data:
            print("Test PCB's Validate On Generate Submit")
            curName = form.name.data
            name = curName.replace(" ","_")
            currentPCBView = form.MakePCB(name)
            form.visualURL = currentPCBView
            print(currentPCBView," is generated")
        pass

    
    return render_template('generatorpcb.html',
                           form = form,          
                           current_time=datetime.utcnow())

@app.route("/getimagepcb")
def get_img_pcb():
    global currentPCBView
    print("Test Get Image PCB")
    print(currentPCBView)
    return redirect(currentPCBView)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',current_time=datetime.utcnow()), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html',current_time=datetime.utcnow()), 500

                            











            

