import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, render_template, session, redirect, url_for, flash

# Initialize Flask
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'

# Sample data
PRODUCTS = [
    {'id': 1, 'name': 'Professional Chef Knife', 'price': 89999, 'image': 'knife', 'category': 'Knives', 'stock': 50},
    {'id': 2, 'name': 'Non-Stick Frying Pan', 'price': 49999, 'image': 'pan', 'category': 'Pans', 'stock': 100},
]

CATEGORIES = [
    {'id': 1, 'name': 'Knives', 'icon': 'knife', 'count': 1},
    {'id': 2, 'name': 'Pans', 'icon': 'pan', 'count': 1},
]

@app.route('/')
def home():
    try:
        return render_template('home.html', products=PRODUCTS[:4], categories=CATEGORIES)
    except Exception as e:
        return f"Template error: {str(e)}", 500

@app.route('/products')
def products():
    return render_template('products.html', products=PRODUCTS, categories=CATEGORIES)

@app.route('/product/<int:id>')
def product(id):
    product = next((p for p in PRODUCTS if p['id'] == id), None)
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    return render_template('cart.html', cart_items=[], total=0)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    cart = session.get('cart', {})
    cart[str(data.get('product_id'))] = cart.get(str(data.get('product_id')), 0) + 1
    session['cart'] = cart
    return jsonify({'success': True})

@app.route('/cart/count')
def cart_count():
    cart = session.get('cart', {})
    return jsonify({'count': sum(cart.values())})

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form.get('email')
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/admin')
def admin():
    return render_template('admin/dashboard.html', products=PRODUCTS)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'products': len(PRODUCTS)})

# This is CRITICAL for Vercel
app = app

if __name__ == '__main__':
    app.run()