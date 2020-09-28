#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import zipfile
from flask import Flask, request, redirect, url_for, flash, render_template,session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from plistlib import Data
from pydrive.drive import GoogleDrive 
from pydrive.auth import GoogleAuth 
import pandas as pd
from openpyxl.workbook import Workbook
from openpyxl.writer.excel import save_virtual_workbook
import shutil




# UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = "/Users/ens/Desktop/Upload_job"
UPLOAD_DATA_FOLDER = "/Users/ens/Desktop/Data"
ALLOWED_EXTENSIONS = set(['zip'])
ALLOWED_DATA_EXTENSIONS = set(['csv','xlsx','xls'])


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.secret_key = "sup3rs3cr3tk3y"

app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///'+os.path.join(basedir,'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
db = SQLAlchemy(app)



class Joblist(db.Model):
    
    job_id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(100), unique=True)
    job_runfile = db.Column(db.String(255))
    job_context = db.Column(db.String(255))
    job_schedule = db.Column(db.String(255))
    job_logfile = db.Column(db.String(255))
    job_status = db.Column(db.String(255))
    
    def __init__(self,job_name,job_runfile,job_context,job_schedule,job_logfile,job_status):
        self.job_name = job_name
        self.job_runfile = job_runfile
        self.job_context = job_context
        self.job_schedule = job_schedule
        self.job_logfile =job_logfile
        self.job_status = job_status
        
    def __repr__(self):
        return '<Joblist %r>' % self.job_name   

class Filelist(db.Model):
    
    file_id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(100))
    file_path = db.Column(db.String(100))
    
    def __init__(self,file_name,file_path):
        self.file_name = file_name
        
    def __repr__(self):
        return '<Filelist %r>' % self.file_name 



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_data_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_DATA_EXTENSIONS


@app.route('/',methods=['POST','GET'])
def index():
    if "username" in session :
        return redirect(url_for('dirtree'))
    else:
        if request.method == 'POST':
            username =  request.form['username']
            passwd  = request.form['passwd']
            if username == 'admin' and passwd == 'admin':
                session['username'] = username
                return redirect(url_for('dirtree'))

            else:
                return redirect(url_for('index'))
        return render_template('login.html')


@app.route('/home', methods=['GET', 'POST'])
def upload_file():
    if "username" in session:
        
        if request.method == 'POST':
            # gauth = GoogleAuth() 
            # # Creates local webserver and auto 
            # # handles authentication. 
            # gauth.LocalWebserverAuth()        
            # drive = GoogleDrive(gauth) 
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_data_file(file.filename):
                filename = secure_filename(file.filename)
                namefile = filename
                file.save(filename)
                shutil.move(filename,UPLOAD_DATA_FOLDER)
               
                tree = make_tree(UPLOAD_DATA_FOLDER)

                # for i in tree.items():
                #     cek = i[1]

                list=[]
               
                list.append(filename)
                print(filename)
                for filename in list:
                    file_name = filename
                    file_path = os.path.join(UPLOAD_DATA_FOLDER,filename)
                    addFileData = Filelist(file_name,file_path)
                    db.session.add(addFileData)
                    db.session.commit()
                flash('Upload Successfuly')
                return redirect(url_for('upload_file'))

        all_file_data = Filelist.query.all()
        return render_template('upload.html',filedata=all_file_data)
    else:
         return redirect(url_for('index'))


@app.route('/logout')
def admin_page():
    session.pop("username")
    return redirect(url_for('index'))


def make_tree(path):
    tree = dict(name=os.path.basename(path), children=[])
    try: lst = os.listdir(path)
    except OSError:
        pass #ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            if os.path.isdir(fn):
                tree['children'].append(make_tree(fn))
            else:
                tree['children'].append(dict(name=name))
    return tree


@app.route('/joblist',methods=['GET', 'POST'])
def dirtree():
    if "username" in session:
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                namefile = filename
                # os.makedirs(os.path.join(UPLOAD_FOLDER,namefilee[0]))
                path_upload = "/Users/ens/Desktop/Upload_job/demo"
                file.save(os.path.join(path_upload, filename))
                zip_ref = zipfile.ZipFile(os.path.join(path_upload, filename), 'r')
                zip_ref.extractall(os.path.join(path_upload))
                os.remove(os.path.join(path_upload, filename))
                zip_ref.close()

                
                tree=make_tree(UPLOAD_FOLDER)
                for i in tree.items():
                    cek = i[1]
                # print(cek)
                list=[]
                if(len(cek)!=0):
                    for item in tree.items():
                        a = item[1]
                    # print(a)
                    b = a[0]['children']
                    
                    for i in b:
                        # print (i)
                        if i['name'] != 'lib' and i['name'] != 'jobInfo.properties':
                            list.append(i)
                    
                    db.drop_all()
                    db.create_all()
                    for j in list:
                        job_name = j['name']
                        print(job_name)
                        jobrunfile =  job_name+'_run.sh'
                        runfile_path = (os.path.join("/Users/ens/Desktop/Upload_job/demo/",job_name,jobrunfile))
                        addData = Joblist(job_name,runfile_path,'','','','')
                        db.session.add(addData)
                        db.session.commit()
                flash('Upload Successfuly')
                return redirect(url_for('dirtree'))

        all_data = Joblist.query.all()
        return render_template('joblist.html', joblist=all_data)
    else:
        return redirect(url_for('index'))


@app.route('/update',methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        my_data = Joblist.query.get(request.form.get('jobid')) 

      
        
        my_data.job_name = request.form['jobname']
        my_data.job_runfile = my_data.job_runfile
        my_data.job_context =  my_data.job_context
        my_data.job_schedule = request.form['schedule']
        my_data.job_logfile = my_data.job_logfile
        my_data.job_status = my_data.job_status

        db.session.commit()
        flash("update job settings succesfull")
        return redirect(url_for('dirtree'))

@app.route('/runjob',methods=['GET','POST'])
def runjob():
    if request.method == 'POST':
        runfile_path = request.form['job_runfile']

        command_run = 'sh '+os.path.join(runfile_path)
        print(command_run)
        run = os.system(command_run)
        print('returned value: ',run)
        if(run==0):
            flash('Run Job Successfuly')
        # my_data = Joblist.query.filter(Joblist.job_id==job_id).all()
        # print(my_data)
        return redirect(url_for('dirtree'))
    return redirect(url_for('dirtree'))

@app.route('/delete',methods=['GET','POST'])
def delete():
    if request.method ==  'POST':
        job_name = request.form['job_id_delete']
        print(job_name)
        delete_command = 'rm -rf '+os.path.join("/Users/ens/Desktop/Upload_job/demo/",job_name)
        print(delete_command)
        Joblist.query.filter_by(job_name=job_name).delete()

        db.session.commit()
        command_delete = os.system(delete_command)
        print('returned value: ',command_delete)

        return redirect(url_for('dirtree'))
    return redirect(url_for('dirtree'))

@app.route('/delete-file',methods=['GET','POST'])
def delete_file():
    if request.method == 'POST':
        file_id = request.form['file_id_delete']
        file_name = request.form['file_name_delete']
        print(file_name)
        delete_command = 'rm -rf '+os.path.join(UPLOAD_DATA_FOLDER,file_name)
        print(delete_command)
        Filelist.query.filter_by(file_id=file_id).delete()

        db.session.commit()
        command_delete = os.system(delete_command)
        print('returned value: ',command_delete)

        return redirect(url_for('upload_file'))
    return redirect(url_for('upload_file'))

if __name__ == "__main__":
    app.run(debug=True,port=8080)
