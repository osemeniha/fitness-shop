import wtforms as LoginForm
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, current_user, login_required, UserMixin, logout_user
from flask_wtf import FlaskForm
from flask_paginate import Pagination, get_page_parameter
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, PasswordField
from wtforms.validators import InputRequired
from datetime import datetime
import pandas as pd

app = Flask(__name__, static_folder='shop')

app.config['UPLOAD_FOLDER'] = 'shop'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shopDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret key'

db = SQLAlchemy(app)

migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = '/login'

number = 8  # количество товаров на странице


class Collection(db.Model):  # раздел магазина
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    trans = db.Column(db.String(50), nullable=False)


class Item(db.Model):  # товар
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    descr = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    #   image=db.Column(db.String(200), nullable=False)
    collect = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)


class User(UserMixin, db.Model):  # пользователь
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return str(self.id_) + ' ' + self.name + ' ' + self.password


class Comment(db.Model):  # отзыв о товаре
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(700), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

    def __repr__(self):
        return f"Comment('{self.body}', '{self.timestamp}')"


class ItemInBusket(db.Model):  # товар, помещённый в корзину
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)


@login_manager.user_loader  # для доступа нужно авторизоваться
@app.route('/busket')  # корзина
def busket():
    items = db.session.query(
        Item, ItemInBusket).filter(Item.id == ItemInBusket.item_id, ItemInBusket.user_id == current_user.id).all()
    return render_template('Busket.html', items=items, collections=Collection.query.all(), user_=current_user, col=None)


@app.route('/')  # главная страница
def main():
    return render_template(
        'ShopMain.html', collections=Collection.query.all(), title='Главная страница', col=None, user_=current_user)


@app.route('/tovary/<int:id_>/busket', methods=['post'])  # добавление товара в корзину
@login_required
def add_to_busket(id_):
    # im=Item.query.filter_by(id=id_).first()#.image
    data = ItemInBusket(user_id=current_user.id, item_id=id_)
    db.session.add(data)
    db.session.commit()
    return redirect(url_for('busket'))


@app.route('/busket/del/', methods=['post'])  # удаление товара в корзину
def delete_to_busket():
    try:
        db.session.query(ItemInBusket).delete()
        db.session.commit()
        return redirect(url_for('busket'))
    except:
        return "При удалении товара произошла ошибка"


@app.route('/tovary/<int:id_>/')  # страница товара
def item_page(id_):
    data = Item.query.filter_by(id=id_).first()
    c = Collection.query.filter_by(id=data.collect).first()
    return render_template('product.html', item=data, collections=Collection.query.all(),
                           title=data.title, user_=current_user,
                           comments=Comment.query.filter_by(item_id=data.id).all(), col=c)


@app.route('/tovary/<int:id_>/comment', methods=['post'])  # сохранение отзыва
def comment(id_):
    user = User.query.filter_by(id=current_user.id).first()
    text = request.form['comment']
    # form = AddCommentForm()
    if text != '':
        data = Comment(body=text, username=user.name, item_id=id_)
        db.session.add(data)
        db.session.commit()
    return redirect(url_for('item_page', id_=id_))


@login_manager.user_loader  # загрузка пользователя
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])  # авторизация
def login():
     login_=request.form.get('login')
     password=request.form.get('password')
     if login_ and password:
         user=User.query.filter_by(name=login_).first()
         try:
             user.password
         except:
             return flash('Error')
         else:
             if check_password_hash(user.password,password):
                 login_user(user,remember=True)
                 return redirect(url_for('main'))
             else:
                 return flash('Error')
     flash('Fill both fields')
     return render_template('ShopLogin.html',title='Вход',user_=current_user)

@app.route('/<string:collect>/')  # страницы отдельных разделов
@app.route('/<string:collect>/<int:page>')
def page(collect, page=None):
    try:
        bus = [g.item_id for g in ItemInBusket.query.filter_by(user_id=current_user.id).all()]  # товары в корзине
    except:
        bus = []
    if collect in [col.title for col in Collection.query.all()]:
        col = Collection.query.filter_by(title=collect).first().id
        goods = db.session.query(Item, Collection).filter(Item.collect == Collection.id).filter_by(collect=col)
        if page in (None, 1):
            return render_template('ShopGoods.html', goods=goods.paginate(1, number, False),
                                   collections=Collection.query.all()
                                   , col=Collection.query.filter_by(title=collect).first(), user_=current_user, bus=bus)
            # return redirect(url_for('first_page',collect=collect))
        return render_template('ShopGoods.html', goods=goods.paginate(page, number, False),
                               collections=Collection.query.all(),
                               col=Collection.query.filter_by(title=collect).first().title, user_=current_user, bus=bus)


@app.route('/tovary/')  # все товары
@app.route('/tovary/page=<int:page>')
def all_(page=None):
    try:
        bus = [g.item_id for g in ItemInBusket.query.filter_by(user_id=current_user.id).all()]  # товары в корзине
    except:
        bus = []
    goods = db.session.query(Item, Collection).filter(Item.collect == Collection.id)
    if page in (None, 1):
        return render_template('ShopGoods.html', goods=goods.paginate(1, number, False), user_=current_user, bus=bus,
                               collections=Collection.query.all(), col=Collection(title='tovary', trans='Все товары'))
    return render_template('ShopGoods.html', goods=goods.paginate(page, number, False), user_=current_user, bus=bus,
                           collections=Collection.query.all(), col=Collection(title='tovary', trans='Все товары'))


@app.route('/sign', methods=['GET', 'POST'])  # регистрация
def sign():
    sign_ = request.form.get('login')
    password = request.form.get('password')
    if request.method == 'POST':
        if not (sign_ or password):
            flash('Please, fill all fields')
        else:
            if User.query.filter_by(name=sign_).first() == None:
                passw = generate_password_hash(password)
                user = User(name=sign_, password=passw)
                db.session.add(user)
                db.session.commit()
                return redirect('/')
            else:
                flash('User already exists')
    return render_template('ShopSign.html', title='Регистрация', user_=current_user)


@app.route('/logout')  # выход из аккаунта
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)

db.create_all()  # создание базы данных
