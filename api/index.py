from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import os

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'your-secret-key-here-change-in-production'

# Sample products
PRODUCTS = [
    {'id': 1, 'name': 'Professional Chef Knife', 'description': 'High-carbon stainless steel chef knife', 'price': 89999, 'image': 'knife'},
    {'id': 2, 'name': 'Non-Stick Frying Pan', 'description': 'Durable non-stick coating', 'price': 49999, 'image': 'pan'},
    {'id': 3, 'name': 'Stainless Steel Saucepan', 'description': 'Professional grade saucepan', 'price': 39999, 'image': 'pot'},
    {'id': 4, 'name': 'Silicone Spatula Set', 'description': 'Heat-resistant silicone spatulas', 'price': 19999, 'image': 'utensil'},
    {'id': 5, 'name': 'Cast Iron Dutch Oven', 'description': '5.5qt enameled cast iron', 'price': 129999, 'image': 'pot'},
    {'id': 6, 'name': 'Wooden Cutting Board', 'description': 'Large bamboo cutting board', 'price': 24999, 'image': 'cutting-board'},
    {'id': 7, 'name': 'Kitchen Knife Set', 'description': '6-piece premium knife set', 'price': 199999, 'image': 'knife'},
    {'id': 8, 'name': 'Measuring Cups Set', 'description': 'Stainless steel measuring cups', 'price': 14999, 'image': 'cup'},
]

@app.route('/')
def home():
    return render_template('index.html', products=PRODUCTS[:4])

@app.route('/products')
def products():
    return render_template('products.html', products=PRODUCTS)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        return redirect(url_for('products'))
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, quantity in cart.items():
        product = next((p for p in PRODUCTS if p['id'] == int(product_id)), None)
        if product:
            item_total = product['price'] * quantity
            total += item_total
            cart_items.append({'product': product, 'quantity': quantity, 'total': item_total})
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    cart = session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session['cart'] = cart
    return jsonify({'success': True, 'cart_count': sum(cart.values())})

@app.route('/update-cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    product_id = str(data.get('product_id'))
    quantity = data.get('quantity')
    cart = session.get('cart', {})
    if quantity <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = quantity
    session['cart'] = cart
    return jsonify({'success': True})

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return jsonify({'success': True})

@app.route('/checkout')
def checkout():
    if 'user' not in session:
        flash('Please login to checkout', 'warning')
        return redirect(url_for('login'))
    
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('products'))
    
    return render_template('checkout.html')

@app.route('/place-order', methods=['POST'])
def place_order():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    state = request.form.get('state')
    payment = request.form.get('payment')
    
    # Clear cart
    session.pop('cart', None)
    
    flash(f'Thank you {name}! Your order has been placed successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/cart/count')
def cart_count():
    cart = session.get('cart', {})
    total_count = sum(cart.values())
    return jsonify({'count': total_count})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        session['user'] = email
        flash(f'Welcome back {email}!', 'success')
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        session['user'] = email
        flash(f'Account created! Welcome {name}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully', 'info')
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

if __name__ == '__main__':
    app.run(debug=True)