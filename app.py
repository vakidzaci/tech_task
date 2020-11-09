from flask import Flask, render_template, flash, redirect, request, url_for, session, logging
from werkzeug.datastructures import ImmutableMultiDict
from pdf2image import convert_from_bytes
from signature_extractor import get_signatures
from tika import parser
from pytesseract import image_to_string
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from text_extractor import text_extractor
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/test.db'
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    rowid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=True, nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Document(db.Model):
    __tablename__ = 'documents'
    rowid = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    def __init__(self, filename, content, user_id):
        self.filename = filename
        self.content = content
        self.user_id = user_id

class Signature(db.Model):
    __tablename__ = 'signatures'
    rowid = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(120), nullable=False)
    document_id = db.Column(db.Integer, nullable=False)

@app.route('/login', methods=[ "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password_candidate = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user is None:
            error = "Пользователь с почтой {} не существует".format(username)
            print(error)
            return {"message":error, "status":400}
        elif sha256_crypt.verify(password_candidate, user.password):
            app.logger.info("PASSWORD MATCHED")
            session['username'] = username
            session['user_id'] = user.rowid
            print(user.rowid)
            return {"message":"Вошлни в систему", "status":200}
        else:
            error = "Пароль неверен"
            print(error)
            return {"message": error, "status": 400}


@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST" :
        username = request.form['username']
        password = sha256_crypt.encrypt(str(request.form['password']))
        if db.session.query(User).filter(User.username == username).count()==0:
            data = User(username, password)
            db.session.add(data)
            db.session.commit()
            return {"message":"Зарегистрировано","code":200}
        else:
            # flash('The address %s is already in use, choose another one' % email)
            error = "Почта уже используется другим пользователем"
            return {"message":error,"code":400}

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/get_users')
def get_users():
    rows = User.query.all()
    for row in rows:
        print(row.username)
    return 'Hi this is list'

@app.route('/upload', methods=["POST"])
def upload():
    # print(request.args)
    # print(request.get_data())
    data = request.form
    user_id = request.form['user_id']
    file = request.files['file']
    text,links = get_signatures(convert_from_bytes(file.read()))
    doc = Document(file.filename, text, user_id)
    db.session.add(doc)
    # db.session.flush()
    db.session.commit()
    return {"status":200,"doc_id":doc.rowid,"links":links}

@app.route('/upload_doc', methods=['POST'])
def upload_doc():
    data = request.form
    user_id = request.form['user_id']
    file = request.files['file']
    text = text_extractor(file.read())
    doc = Document(file.filename,text,user_id)
    db.session.add(doc)
    # db.session.flush()
    db.session.commit()
    return {"message":"OK","status":200,"document_id":doc.rowid}

# @app.route('/upload_file'):


if __name__ == '__main__':
    app.secret_key = os.urandom(24)
    app.run(debug=True)
