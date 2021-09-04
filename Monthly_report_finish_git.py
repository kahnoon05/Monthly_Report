#-*-coding: utf-8 -*-
# Auto Monthly Report
# PDF backend module
#
# v.1.3.0 25/01/64
#   - merge all vm of cus in one pdf
#
# v.1.2.0 30/10/63
#   - add full release version api module
#
# v.1.1.0 11/08/63
#   - initial api module
#
# v.1.0.0 13/07/63
#   - initial release
#   - initial mockup pdf module
#
# author inet-vdi


# ================== Import library ==================
from flask import Flask, request, Response #FlasK API
# from flaskext.mysql import MySQL #FlasK MySQL
# import threading, time, os, re, subprocess, platform
import urllib.parse #url encode
import json #json form
import time #time
# from vdi_send_notify_line_onechat import LineNotify, OneChatNotify #custom alert
import re #regular expression
# import pprint #pretty print
# from functools import wraps
import requests #request http
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle, Frame, PageTemplate #platypus
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle #style
from reportlab.lib import colors #color
from reportlab.lib.pagesizes import A4, landscape #a4 paper
from reportlab.lib.units import mm #millimeter
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER #align format
from reportlab.pdfbase import pdfmetrics #style
from reportlab.pdfbase.ttfonts import TTFont #font
from reportlab.platypus import Image #image from local
import json


# ============== defined variable ====================
static_endpoint_url  = '0.0.0.0'
static_endpoint_port = '5552'
# static_endpoint_port = '5553'
static_endpoint_getrawdata = '/api/selectVm'
static_backend_rawdata_url = 'http://xxxxxxxxxxxx:3000/api/selectVmStat'
# static_backend_rawdata_url = 'http://localhost:3000/api/selectVmStat'
static_return_url = 'http://xxxxxxxxxxxx/mypdf.pdf'


# ================== Function ========================
# Tooling get cus name and cno
def FindCusnameCNO(data_group):
    try:
        # split name and cno from group
        _tempcusname = data_group.split('#')
        try: 
            _data_groupcusname = _tempcusname[0].strip()
        except:
            _data_groupcusname = ''
        try: 
            _data_groupcno = _tempcusname[1].strip()
        except:
            _data_groupcno  = ''
        # get cusname english from api db
        try:
            # url endpoint
            url = 'http://xxxxxxxxxxxx:3306/api/v1/findcompanyname'
            # header
            headers = {
                'Content-Type': 'application/json'
            }
            # send request
            json_data = {
                "cno" : _data_groupcno
            }
            response = requests.request("POST", url, headers=headers, json=json_data, timeout=60, verify=False)
            if (response.status_code == 200):
                _data_cusname = json.loads(response.text)["companynameen"]
            else:
                _data_cusname = _data_groupcusname
        except:
            # error via timeout or error
            _data_cusname = _data_groupcusname
        return (_data_cusname,_data_groupcusname,_data_groupcno)
    except:
        return ('','','')


# Tooling get vm name
def FindVMname(_data_device):
    _count_vm = len(_data_device)
    try:
        _data_vmname    = [re.search("_\[(.*?)\]", _data_device[i]).group(1) for i in range (_count_vm)]
        _data_ipprivate = [re.search("IP\((.*?)\)", _data_device[i]).group(1) for i in range (_count_vm)]
    except:
        _data_vmname    = ''
        _data_ipprivate = ''
    for i in range (_count_vm):
        if (_data_vmname == ''):
            _data_vmname = _data_device
    return (_data_vmname, _data_ipprivate)


# Tooling generate pdf name
def FindPDFname(_data_cus):
    try:
        _time_now_obj  = time.localtime() #time.time()
        _data_pdf_name = "PDF_" + _data_cus + "_" + time.strftime('%d%B%Y-%H%M%S', _time_now_obj) + ".pdf"
        _path = "C:\\Users\\Khanoon\\Desktop\\Code_study\\monthly_report\\"
        # _path = "/home/user01/pythoncode/pdfstore/"
        _data_pdf_fullpath = _path + _data_pdf_name
        return _data_pdf_name,_data_pdf_fullpath
    except:
        return "","exported_mypdf.pdf"


# Tooling get rawdata without dot data
def FindRawData(_data_url,_data_token,_data_startdate,_data_enddate,_data_customer,_data_vm):
    try:
        #getrawdata
        result = []
        for i in _data_vm:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': _data_token
            }
            _payload_data = 'sdate=' + _data_startdate + '&edate=' + _data_enddate + '&customer=' + _data_customer + '&device=' + i
            _payload_encode = urllib.parse.quote(_payload_data, safe='=&')
            # print(_payload_encode)
            response = requests.request("POST", _data_url, headers=headers, data = _payload_encode, timeout=120, verify=False)
            # pprint.pprint(response.text) 
            result.append(json.loads(response.text))
        return  result
    except:
        return {}
        
# Form table vm detail
def UpdateVarTableVMDetail(vmname,ipprivate):
    _count_vm = len(vmname)
    try:
        table_vm_detail = [['VM Name','IP Address']]
        for i in range (_count_vm):
            table_vm_detail.append([vmname[i],ipprivate[i]])
        return table_vm_detail
    except:
        return [['VM Name','IP Address']]


# Form table system util
def UpdateVarTableSystemUtil(rawdata):
    try:
        data = []
        status = {
            True  : 'สูง',
            False : 'ปกติ'
        }
        # print(rawdata)
        for i in range (len(rawdata)):
            count = 0
            data_prepare = []
            if 'cpu_data' in rawdata[i].keys():
                data_sub = []
                _temp_value = '{:.2f}'.format(rawdata[i]['cpu_data'][0]['avg'])
                data_sub = ['CPU','< 80%',_temp_value,status[float(_temp_value)>=80]]
                data_prepare.append(data_sub)
                count = count + 1
            if 'memory_data' in rawdata[i].keys():
                data_sub = []
                _temp_value = '{:.2f}'.format(100-(rawdata[i]['memory_data'][0]['avg']))
                data_sub = ['Memory','< 80%',_temp_value,status[float(_temp_value)>=80]]
                data_prepare.append(data_sub)
                count = count + 1
            if 'disk_data' in rawdata[i].keys():
                for run_sensor in range(len(rawdata[i]['disk_data'])):
                    data_sub = []
                    _temp_value = '{:.2f}'.format(rawdata[i]['disk_data'][run_sensor]['avg'])
                    disk_name = rawdata[i]['disk_data'][run_sensor]['name']
                    if disk_name.find(':\\'):
                        disk_name = disk_name[:disk_name.find(':\\') + 2]
                    elif disk_name.find('/'):
                        disk_name = disk_name[:disk_name.find(':/') + 1]
                    else:
                        disk_name = disk_name
                    data_sub = [disk_name,'> 20%',_temp_value,status[float(_temp_value)<=20]]
                    data_prepare.append(data_sub)
                    count = count + 1
            if count > 0:
                data.append(data_prepare)
            if count < 0:
                data.append(['','','',''])  
        return data 
    except:
        return {}

# Define flask application
Backend_API = Flask(__name__)
# Add session secret key
# Backend_API.secret_key = Config['crypto']['secret']

# allow origin
@Backend_API.after_request
def after_request(response):
    response.headers.add(
        'Access-Control-Allow-Origin',
        '*'
    )
    response.headers.add(
        'Access-Control-Allow-Headers',
        'Authorization,X-Requested-With,Content-type,withCredentials'
    )
    response.headers.add(
        'Access-Control-Allow-Methods',
        'GET,PUT,POST,DELETE,OPTIONS'
    )
    return response

# Return to client with json format and setup status code ether
def response_json(data, code):
    response_data = Backend_API.response_class(
        response = json.dumps(data),
        status = code,
        mimetype = 'application/json'
    )
    return response_data

# ENDPOINT TEST
@Backend_API.route('/api/v1/test', methods=['GET'])
def APItest():
    print('WORKING')
    return response_json('ITS WORKED', 200)

# ENDPOINT RECEIVER
@Backend_API.route('/api/selectVm', methods=['POST'])
# @Backend_API.route('/api/selectMultiVm', methods=['POST'])
def APIreceiver():
    print("start")

    # STEP GET BODY
    try:
        # JSON (FRONTEND REACT)
        _data_received = request.json
        _data_input_sdate    = _data_received['sdate']
        _data_input_edate    = _data_received['edate']
        _data_input_customer = _data_received['customer'].replace("%","#")
        _data_input_device = json.loads(_data_received['device'].replace("%","#"))
        _data_input_token = request.headers.get('authorization') #.split(" ")[1] #Bearer xxxx
    except:
        # FORM (POSTMAN)
        _data_input_sdate = request.form['sdate']
        _data_input_edate = request.form['edate']
        _data_input_customer = request.form['customer'].replace("%","#")
        _data_input_device = json.loads(request.form['device'].replace("%","#"))
        _data_input_token = request.headers.get('authorization') #.split(" ")[1] #Bearer xxxx

    # STEP DEFINED VARIABLE
    var_pdf_name_header = 'INET Service Report'
    var_cusnameen = ''
    var_startdate = ''
    var_enddate   = ''
    var_vmname    = ''
    var_ipprivate = ''
    var_cusgroup_full    = ''
    var_cusgroup_cusname = ''
    var_cusgroup_cno     = 0
    var_device           = ''
    var_server_nx        = 'https://xxxxxxxxxxxx.co.th'
    var_count_sensor     = 0
    var_rawdata          = {}
    var_pdf_name         = ''
    var_return_url       = ''
    var_table_vmdetail   = [['VM Name','IP Address']]
    var_table_systemutil = []

    # STEP ADJUST VARIABLE AND CALL API
    var_startdate = _data_input_sdate
    var_enddate   = _data_input_edate
    var_startdate_obj = time.strptime(var_startdate, '%Y-%m-%d-%H-%M-%S')
    var_enddate_obj   = time.strptime(var_enddate,   '%Y-%m-%d-%H-%M-%S')
    var_startdate_str = time.strftime('%d %B %Y', var_startdate_obj)
    var_enddate_str   = time.strftime('%d %B %Y', var_enddate_obj  )
    var_cusgroup_full = _data_input_customer
    var_vmname = _data_input_device
    var_cusnameen,var_cusgroup_cusname,var_cusgroup_cno = FindCusnameCNO(var_cusgroup_full)
    var_device = _data_input_device
    var_vmname,var_ipprivate = FindVMname(var_device)
    var_pdf_name, temp_var_pdf_fullpath = FindPDFname(var_cusnameen.replace(" ","_"))
    print(var_pdf_name)
    var_return_url = 'https://xxxxxxxxxxxx/pdfstore/' + var_pdf_name
    
    var_rawdata  = FindRawData(static_backend_rawdata_url,_data_input_token,
        var_startdate,var_enddate,var_cusgroup_full,_data_input_device)

    # STEP GENERATE PDF
    ############### DRAW PDF ##############################
    pdfmetrics.registerFont(
        TTFont('font_tahoma', 'tahoma.ttf')
    )
    my_pdf = SimpleDocTemplate(
        temp_var_pdf_fullpath,
        title = var_pdf_name_header,
        author = 'INET',
        pagesize = A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=3*mm,
        bottomMargin=3*mm,
        showBoundary=0
    )
    my_styles = getSampleStyleSheet( )
    my_style = ParagraphStyle(
            name='Normal',
            fontName='font_tahoma',
            fontSize=10,
            )
    my_style_center = ParagraphStyle(
            name='Normal',
            fontName='font_tahoma',
            alignment=TA_CENTER,
            fontSize=20,
            )
    my_flow = [] #CANVAS


    # PAGE 1
    # spacer header to subject 
    my_flow.append(Spacer(1,41*mm))

    # subject at 5.5cm
    para_text = Paragraph("Service Report",my_style_center)
    my_flow.append(para_text)

    # spacer subject to customer name english
    my_flow.append(Spacer(1,70*mm))

    # customer name english at 13.0cm
    para_text = Paragraph(var_cusnameen,my_style_center)
    my_flow.append(para_text)

    # spacer customer name thai to date
    my_flow.append(Spacer(1,5*mm))

    # time range at 13.9cm
    para_text = Paragraph('( '+ var_startdate_str + ' - ' + var_enddate_str + ' )',my_style_center)
    my_flow.append(para_text)

    # spacer date to inet name
    my_flow.append(Spacer(1,57*mm))

    # inet name at 20.1cm
    para_text = Paragraph('By Internet Thailand Public Co., Ltd.',my_style_center)
    my_flow.append(para_text)

    # inet name to inet logo
    my_flow.append(Spacer(1,10*mm))

    #inet logo
    # picture = Image('inetlogo.jpeg')
    # # para_text = Paragraph(picture,my_style_center)
    # picture.drawWidth = 60*mm
    # picture.drawHeight = 30*mm
    # my_flow.append(picture)
    
    # instead pic
    my_flow.append(Spacer(1,60*mm))


    # PAGE2
    my_flow.append(PageBreak())

    # spacer header to vm detail header
    my_flow.append(Spacer(1,20*mm))

    # vm detail header
    para_text = Paragraph('VM Detail',my_style)
    my_flow.append(para_text)

    # spacer vm detail header to vm detail table
    my_flow.append(Spacer(1,3*mm))

    # vm detail table
    var_table_vmdetail = UpdateVarTableVMDetail(var_vmname,var_ipprivate)
    
    table_vmdetail = Table(var_table_vmdetail,[80*mm,30*mm],hAlign='LEFT')
    table_vmdetail_style = TableStyle([
        ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        ('BACKGROUND', (0,0), (-1,0), colors.Color(red=0.0000,green=0.68,blue=0.000)),
        ('ALIGN',      (0,0), (-1,-1), 'LEFT'),
        ('GRID',       (0,0), (-1,-1), 1, colors.black)
        ])
    table_vmdetail.setStyle(table_vmdetail_style)
    my_flow.append(table_vmdetail)

    # spacer vm detail table to system util header
    my_flow.append(Spacer(1,10*mm))

    # system util header
    para_text = Paragraph('System Utilization',my_style)
    my_flow.append(para_text)

    # spacer system util header to system util table
    my_flow.append(Spacer(1,3*mm))

    # system util table - subject
    table_systemutil_subject = Table([['ค่าของการใช้งานปกติ (threshold)','ปริมาณการใช้งานจริง']],[90*mm,60*mm])
    table_systemutil_subject_style = TableStyle([
        ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        ('BACKGROUND', (0,0), (-1,0), colors.Color(red=0.0000,green=0.68,blue=0.000)),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('GRID',       (0,0), (-1,-1), 1, colors.black),
        ('TOPPADDING', (0,0),(-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1), 3)
        ])
    table_systemutil_subject.setStyle(table_systemutil_subject_style)
    
    # test
    # system util table - data
    keep_table_systemutil_data = []

    # Generate vm_name list
    filtered_vmname = []
    var_table_vmdetail_test = UpdateVarTableVMDetail(var_vmname,var_ipprivate)

    for i in range (1,len(var_table_vmdetail_test)):
        filtered_vmname.append(var_table_vmdetail[i][0])

    for i in range (len(var_rawdata)):   
        
        table_vmdetail = Table([[filtered_vmname[i]]],[150*mm],hAlign='LEFT')
        # table_vmdetail = Table(["test"],[80*mm],hAlign='LEFT')
        table_vmdetail_style = TableStyle([
            ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
            ('FONTSIZE',   (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,0), (-1,0), colors.Color(red=0.451,green=0.800,blue=0.4353)),
            ('ALIGN',      (0,0), (-1,-1), 'LEFT'),
            ('GRID',       (0,0), (-1,-1), 1, colors.black)
            ])
        table_vmdetail.setStyle(table_vmdetail_style)

        keep_table_systemutil_data.append(table_vmdetail)
        
        var_table_systemutil = UpdateVarTableSystemUtil(var_rawdata)[i]

        table_systemutil_data = Table(var_table_systemutil,[45*mm,45*mm,30*mm,30*mm])
        table_systemutil_data_style = TableStyle([
            ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
            ('FONTSIZE',   (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,0), (0,-1), colors.Color(red=0.7695,green=0.8750,blue=0.6992)),
            ('ALIGN',      (0,0), (0,-1), 'LEFT'),
            ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
            ('GRID',       (0,0), (-1,-1), 1, colors.black),
            ('TOPPADDING', (0,0),(-1,-1), 3),
            ('BOTTOMPADDING',(0,0),(-1,-1), 3),
            ])
        table_systemutil_data.setStyle(table_systemutil_data_style)
        keep_table_systemutil_data.append(table_systemutil_data)

    # system util table - main
    table_systemutil_main = Table(
        [
            [table_systemutil_subject],
            [keep_table_systemutil_data]
        ],
        150*mm,
        hAlign='LEFT'
        )
    table_systemutil_main_style = TableStyle([
        ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        # ('GRID',       (0,0), (-1,-1), 1, colors.black),
        ('TOPPADDING', (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
        ('LEFTPADDING', (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0)
        ])
    table_systemutil_main.setStyle(table_systemutil_main_style)
    my_flow.append(table_systemutil_main)

    for i in range (len(filtered_vmname)):

        # spacer to vmname english
        my_flow.append(Spacer(1,140*mm))

        # customer name english at 13.0cm
        para_text = Paragraph(filtered_vmname[i],my_style_center)
        my_flow.append(para_text)

        # PAGE Custom CPU
        if 'cpu_data' in var_rawdata[i].keys():
            my_flow.append(PageBreak())

            # spacer header to vm detail header
            my_flow.append(Spacer(1,20*mm))

            # INFO header
            para_text = Paragraph('System Utilization',my_style)
            my_flow.append(para_text)

            # spacer INFO header header to VM name
            my_flow.append(Spacer(1,3*mm))
            
            # VM name
            para_text = Paragraph('VM name : {}'.format(filtered_vmname[i]),my_style)
            my_flow.append(para_text)

            # spacer INFO header header to CPU label
            my_flow.append(Spacer(1,3*mm))

            # CPU label
            para_text = Paragraph('CPU Usage:',my_style)
            my_flow.append(para_text)

            # spacer CPU label to CPU image
            my_flow.append(Spacer(1,3*mm))

            # # CPU image
            # cpu_url = var_server_nx + '/chart.png?id=' + str(var_rawdata['cpu_data'][0]['sensor_id']) + '&avg=900&width=1080&height=600&graphstyling=baseFontSize=%2712%27&showLegend=%271%27&graphid=-1&username=inet-sdi&passhash=359285728&sdate=' + var_startdate + '&edate=' + var_enddate + '&hide=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16'
            # cpu_image = Image(cpu_url)
            # cpu_image.drawWidth = 180*mm
            # cpu_image.drawHeight = 100*mm
            # my_flow.append(cpu_image)

            # instead pic
            my_flow.append(Spacer(180,100*mm))

            # spacer CPU image to cpu table
            my_flow.append(Spacer(1,10*mm))

            # cpu util table - data
            var_table_cpuutil = []
            status = {
                    True  : 'สูง',
                    False : 'ปกติ'
                }
            _temp_value = '{:.2f}'.format(var_rawdata[i]['cpu_data'][0]['avg'])
            _data_sub = ['CPU','<80%',_temp_value,status[float(_temp_value)>=80]]
            var_table_cpuutil.append(_data_sub)
            table_cpuutil_data = Table(var_table_cpuutil,[45*mm,45*mm,30*mm,30*mm])
            table_cpuutil_data_style = TableStyle([
                ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
                ('FONTSIZE',   (0,0), (-1,-1), 10),
                ('BACKGROUND', (0,0), (0,-1), colors.Color(red=0.7695,green=0.8750,blue=0.6992)),
                ('ALIGN',      (0,0), (0,-1), 'LEFT'),
                ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
                ('GRID',       (0,0), (-1,-1), 1, colors.black),
                ('TOPPADDING', (0,0),(-1,-1), 3),
                ('BOTTOMPADDING',(0,0),(-1,-1), 3),
                ])
            table_cpuutil_data.setStyle(table_cpuutil_data_style)

            # cpu util table - main
            table_cpuutil_main = Table(
                [
                    [table_systemutil_subject],
                    [table_cpuutil_data]
                ],
                150*mm,
                hAlign='LEFT'
                )
            table_cpuutil_main_style = TableStyle([
                ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
                ('FONTSIZE',   (0,0), (-1,-1), 10),
                # ('GRID',       (0,0), (-1,-1), 1, colors.black),
                ('TOPPADDING', (0,0),(-1,-1), 0),
                ('BOTTOMPADDING',(0,0),(-1,-1), 0),
                ('LEFTPADDING', (0,0),(-1,-1), 0),
                ('RIGHTPADDING', (0,0),(-1,-1), 0)
                ])
            table_cpuutil_main.setStyle(table_cpuutil_main_style)
            my_flow.append(table_cpuutil_main)


        # PAGE Custom Memory
        if 'memory_data' in var_rawdata[i].keys():

            my_flow.append(PageBreak())

            # spacer header to memory label
            my_flow.append(Spacer(1,20*mm))

           # VM name
            para_text = Paragraph('VM name : {}'.format(filtered_vmname[i]),my_style)
            my_flow.append(para_text)

            # spacer VM name to memory label
            my_flow.append(Spacer(1,3*mm))

            # memory label
            para_text = Paragraph('Memory Available:',my_style)
            my_flow.append(para_text)

            # spacer memory label to memory image
            my_flow.append(Spacer(1,3*mm))

            # # memory image
            # memory_url = var_server_nx + '/chart.png?id=' + str(var_rawdata['memory_data'][0]['sensor_id']) + '&avg=900&width=1080&height=600&graphstyling=baseFontSize=%2712%27&showLegend=%271%27&graphid=-1&username=inet-sdi&passhash=359285728&sdate=' + var_startdate + '&edate=' + var_enddate + '&hide=1,2'
            # memory_image = Image(memory_url)
            # memory_image.drawWidth = 180*mm
            # memory_image.drawHeight = 100*mm
            # my_flow.append(memory_image)

            # instead pic
            my_flow.append(Spacer(180,100*mm))


            # spacer memory image to memory table
            my_flow.append(Spacer(1,10*mm))

            # memory util table - data
            var_table_memoryutil = []
            _status = {
                    True  : 'สูง',
                    False : 'ปกติ'
                }
            _temp_value = '{:.2f}'.format(100-var_rawdata[i]['memory_data'][0]['avg'])
            # print("_temp_value : ", _temp_value)
            _data_sub = ['Memory','<80%',_temp_value,_status[float(_temp_value)>=80]]
            var_table_memoryutil.append(_data_sub)
            table_memoryutil_data = Table(var_table_memoryutil,[45*mm,45*mm,30*mm,30*mm])
            table_memoryutil_data_style = TableStyle([
                ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
                ('FONTSIZE',   (0,0), (-1,-1), 10),
                ('BACKGROUND', (0,0), (0,-1), colors.Color(red=0.7695,green=0.8750,blue=0.6992)),
                ('ALIGN',      (0,0), (0,-1), 'LEFT'),
                ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
                ('GRID',       (0,0), (-1,-1), 1, colors.black),
                ('TOPPADDING', (0,0),(-1,-1), 3),
                ('BOTTOMPADDING',(0,0),(-1,-1), 3),
                ])
            table_memoryutil_data.setStyle(table_memoryutil_data_style)

            # memory util table - main
            table_memoryutil_main = Table(
                [
                    [table_systemutil_subject],
                    [table_memoryutil_data]
                ],
                150*mm,
                hAlign='LEFT'
                )
            table_memoryutil_main_style = TableStyle([
                ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
                ('FONTSIZE',   (0,0), (-1,-1), 10),
                # ('GRID',       (0,0), (-1,-1), 1, colors.black),
                ('TOPPADDING', (0,0),(-1,-1), 0),
                ('BOTTOMPADDING',(0,0),(-1,-1), 0),
                ('LEFTPADDING', (0,0),(-1,-1), 0),
                ('RIGHTPADDING', (0,0),(-1,-1), 0)
                ])
            table_memoryutil_main.setStyle(table_memoryutil_main_style)
            my_flow.append(table_memoryutil_main)


        # PAGE Custom Disk
        if 'disk_data' in var_rawdata[i].keys():
            for run_sensor in range(len(var_rawdata[i]['disk_data'])):
                my_flow.append(PageBreak())

                # spacer header to disk label
                my_flow.append(Spacer(1,20*mm))

                # VM name
                para_text = Paragraph('VM name : {}'.format(filtered_vmname[i]),my_style)
                my_flow.append(para_text)

                # spacer VM name to memory label
                my_flow.append(Spacer(1,3*mm))

                # disk label
                para_text = Paragraph('Disk Available:',my_style)
                my_flow.append(para_text)

                # spacer disk label to disk image
                my_flow.append(Spacer(1,3*mm))

                # # disk image
                # disk_url = var_server_nx + '/chart.png?id=' + str(var_rawdata[0]['disk_data'][run_sensor]['sensor_id']) + '&avg=900&width=1080&height=600&graphstyling=baseFontSize=%2712%27&showLegend=%271%27&graphid=-1&username=inet-sdi&passhash=359285728&sdate=' + var_startdate + '&edate=' + var_enddate + '&hide=1,2'
                # disk_image = Image(disk_url)
                # disk_image.drawWidth = 180*mm
                # disk_image.drawHeight = 100*mm
                # my_flow.append(disk_image)
                
                # instead pic
                my_flow.append(Spacer(180,100*mm))


                # spacer disk image to disk table
                my_flow.append(Spacer(1,10*mm))

                # disk util table - data
                var_table_diskutil = []
                _status = {
                        True  : 'สูง',
                        False : 'ปกติ'
                    }
                _temp_value = '{:.2f}'.format(var_rawdata[i]['disk_data'][run_sensor]['avg'])
                _data_sub = [var_rawdata[i]['disk_data'][run_sensor]['name'][:14],'<80%',_temp_value,status[float(_temp_value)>=80]]
                var_table_diskutil.append(_data_sub)
                table_diskutil_data = Table(var_table_diskutil,[45*mm,45*mm,30*mm,30*mm])
                table_diskutil_data_style = TableStyle([
                    ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
                    ('FONTSIZE',   (0,0), (-1,-1), 10),
                    ('BACKGROUND', (0,0), (0,-1), colors.Color(red=0.7695,green=0.8750,blue=0.6992)),
                    ('ALIGN',      (0,0), (0,-1), 'LEFT'),
                    ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
                    ('GRID',       (0,0), (-1,-1), 1, colors.black),
                    ('TOPPADDING', (0,0),(-1,-1), 3),
                    ('BOTTOMPADDING',(0,0),(-1,-1), 3),
                    ])
                table_diskutil_data.setStyle(table_diskutil_data_style)

                # disk util table - main
                table_diskutil_main = Table(
                    [
                        [table_systemutil_subject],
                        [table_diskutil_data]
                    ],
                    150*mm,
                    hAlign='LEFT'
                    )
                table_diskutil_main_style = TableStyle([
                    ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
                    ('FONTSIZE',   (0,0), (-1,-1), 10),
                    # ('GRID',       (0,0), (-1,-1), 1, colors.black),
                    ('TOPPADDING', (0,0),(-1,-1), 0),
                    ('BOTTOMPADDING',(0,0),(-1,-1), 0),
                    ('LEFTPADDING', (0,0),(-1,-1), 0),
                    ('RIGHTPADDING', (0,0),(-1,-1), 0)
                    ])
                table_diskutil_main.setStyle(table_diskutil_main_style)
                my_flow.append(table_diskutil_main)


    # PAGE Appendix
    my_flow.append(PageBreak())

    # spacer header to appendix header
    my_flow.append(Spacer(1,20*mm))

    # appendix header
    para_text = Paragraph('Appendix on monitoring metric:',my_style)
    my_flow.append(para_text)

    # spacer appendix header to appendix table
    my_flow.append(Spacer(1,3*mm))

    # appendix table
    var_appendix_data = [
        ['Parameter','Description'],
        ['CPU','CPU usage > 80% of the total capacity for a long period of time, such as 5 minutes continuously'],
        ['Memory','Memory usage > 80% of the total capacity for a long period of time, such as 5 minutes continuously'],
        ['Disk','Total available capacity is less than 20%'],
        ['SLA','99.90%']
    ]
    table_appendix = Table(var_appendix_data,hAlign='LEFT')
    table_appendix_style = TableStyle([
        ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
        ('FONTSIZE',   (0,0), (-1,0), 10),
        ('FONTSIZE',   (0,1), (0,-1), 10),
        ('FONTSIZE',   (1,1), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,0), colors.Color(red=0.0000,green=0.6800,blue=0.0000)),
        ('ALIGN',      (0,0), (-1,0), 'CENTER'),
        ('ALIGN',      (0,1), (-1,-1), 'LEFT'),
        ('GRID',       (0,0), (-1,-1), 1, colors.black)
        ])
    table_appendix.setStyle(table_appendix_style)
    my_flow.append(table_appendix)

    # spacer appendix header to company info table
    my_flow.append(Spacer(1,10*mm))

    # company info table
    var_companyinfo_data = [
        ['Internet Thailand Public Company Limited'],
        ['1768 Thai Summit Tower, 10th-12th Floor and IT Floor'],
        ['New Petchburi Road, Khwaeng Bang Kapi,'],
        ['Khet HuayKhwang, Bangkok 10310'],
        ['• Tel. : 0-2257-7000'],
        ['• Fax  : 0-2257-7222'],
        ['• Call Center : 0-2257-7111']
    ]
    table_companyinfo = Table(var_companyinfo_data,hAlign='LEFT')
    table_companyinfo_style = TableStyle([
        ('FONTNAME',   (0,0), (-1,-1), 'font_tahoma'),
        ('FONTSIZE',   (0,0), (-1,0), 12),
        ('FONTSIZE',   (0,1), (-1,-1), 8),
        ('ALIGN',      (0,1), (-1,-1), 'LEFT'),
        # ('GRID',       (0,0), (-1,-1), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('BOTTOMPADDING',(0,0),(-1,0), 10),
        ('TOPPADDING', (0,1), (-1,-1), 1),
        ('BOTTOMPADDING',(0,1),(-1,-1), 1)
        ])
    table_companyinfo.setStyle(table_companyinfo_style)
    my_flow.append(table_companyinfo)

    #build pdf
    my_pdf.build(my_flow)


    _res_success = { 
        'status' : 'success',
        'result' : var_return_url
    }
    print("loop success")
    return response_json(_res_success, 200)
    # except Exception as e:
    #     print("loop error",e)
    #     _res_fail = {
    #         'status' : 'fail',
    #         'result' : ''
    #     }
    #     return response_json(_res_fail, 500)


# ================== Main Sector =====================
def main():
    print("Hello World")
    # start Flask API Service
    Backend_API.run(debug=True, threaded=True, host=static_endpoint_url, port=static_endpoint_port)

if __name__ == "__main__":
    main()



# required library
# flask >> pip install Flask
# reportlab >> pip install reportlab

#very end