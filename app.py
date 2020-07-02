#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import zipfile
from flask import Flask, request, redirect, url_for, flash, render_template,session
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = "/Users/ens/Desktop/Upload_job"
ALLOWED_EXTENSIONS = set(['zip'])


app = Flask(__name__)
app.secret_key = "super secret key"
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/',methods=['POST','GET'])
def index():
    if "username" in session :
        return redirect(url_for('upload_file'))
    else:
        if request.method == 'POST':
            username =  request.form['username']
            passwd  = request.form['passwd']
            if username == 'admin' and passwd == 'admin':
                session['username'] = username
                return redirect(url_for('upload_file'))

            else:
                return redirect(url_for('index'))
        return render_template('login.html')



@app.route('/home', methods=['GET', 'POST'])
def upload_file():
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
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r')
                zip_ref.extractall(UPLOAD_FOLDER)
                os.remove(os.path.join(UPLOAD_FOLDER, filename))
                zip_ref.close()
                flash('Upload Successfuly')
                return redirect(url_for('upload_file',filename=namefile))
            
        return render_template('upload.html')
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


@app.route('/joblist')
def dirtree():
    if "username" in session:
        path = "/Users/ens/Desktop/Upload_job"
        return render_template('joblist.html', tree=make_tree(path))
    else:
        return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
