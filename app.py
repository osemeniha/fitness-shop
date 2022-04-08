from flask import Flask,render_template,redirect,url_for,request,flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager,login_user,current_user,login_required,UserMixin,logout_user
from flask_wtf import FlaskForm
from flask_paginate import Pagination, get_page_parameter
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, TextAreaField,  BooleanField, PasswordField
from wtforms.validators import InputRequired
from datetime import datetime
import pandas as pd

app=Flask(__name__, static_folder='shop')

app.config['UPLOAD_FOLDER']='shop'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///shopDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY'] = 'secret key'

db=SQLAlchemy(app)

migrate = Migrate(app, db)

login_manager=LoginManager(app)
login_manager.login_view = '/login'

number=8 #количество товаров на странице

class Collection(db.Model): #раздел магазина
    id = db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(50), nullable=False)
    trans=db.Column(db.String(50), nullable=False)

class Item(db.Model): #товар
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(100), nullable=False)
    descr=db.Column(db.String(500), nullable=False)
    price=db.Column(db.Integer, nullable=False)
 #   image=db.Column(db.String(200), nullable=False)
    collect=db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)

class User(UserMixin,db.Model): #пользователь
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(200), nullable=False)
    password=db.Column(db.String(150), nullable=False)
    def __repr__(self):
        return str(self.id_)+' '+self.name+' '+self.password

class Comment(db.Model): #отзыв о товаре
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(700), nullable=False)
    username= db.Column(db.String(100),nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    def __repr__(self):
        return f"Comment('{self.body}', '{self.timestamp}')"

class ItemInBusket(db.Model): #товар, помещённый в корзину
    id = db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id=db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)


db.create_all() #создание базы данных
