from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Product, Order
import boto3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

s3 = boto3.client(
    's3',
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY']
)

@app.route('/')
def home():
    products = Product.query.all()
    return render_template('home.html', products=products)

@app.route('/product/<int:product_id>')
def product(product_id):
    product = Product.query.get(product_id)
    return render_template('product.html', product=product)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.files['image']
        filename = secure_filename(image.filename)
        image.save(filename)
        s3.upload_file(
            Bucket=app.config['AWS_S3_BUCKET'],
            Filename=filename,
            Key=filename
        )
        image_url = f"https://{app.config['AWS_S3_BUCKET']}.s3.amazonaws.com/{filename}"
        new_product = Product(name=name, description=description, price=price, image_url=image_url)
        db.session.add(new_product)
        db.session.commit()
        os.remove(filename)
        return redirect(url_for('home'))
    return render_template('add_product.html')

@app.route('/order/<int:product_id>', methods=['POST'])
def order(product_id):
    quantity = request.form['quantity']
    product = Product.query.get(product_id)
    total_price = product.price * int(quantity)
    new_order = Order(product_id=product_id, quantity=quantity, total_price=total_price)
    db.session.add(new_order)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
