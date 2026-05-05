from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_file
import os
import csv
import io
from datetime import datetime, timedelta
import secrets

# Create Flask app
app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ==================== DATA STORAGE ====================
PRODUCTS = [
    {'id': 1, 'name': 'Professional Chef Knife', 'description': 'High-carbon stainless steel chef knife with ergonomic handle', 'price': 89999, 'compare_price': 129999, 'image': 'knife', 'category': 'Knives', 'stock': 50, 'featured': True, 'bestseller': True, 'rating': 4.8, 'reviews': 124},
    {'id': 2, 'name': 'Non-Stick Frying Pan', 'description': 'Durable non-stick coating, even heat distribution', 'price': 49999, 'compare_price': 79999, 'image': 'pan', 'category': 'Pans', 'stock': 100, 'featured': True, 'bestseller': True, 'rating': 4.6, 'reviews': 89},
    {'id': 3, 'name': 'Stainless Steel Saucepan', 'description': 'Professional grade saucepan with lid', 'price': 39999, 'compare_price': None, 'image': 'pot', 'category': 'Pots', 'stock': 75, 'featured': False, 'bestseller': False, 'rating': 4.5, 'reviews': 56},
    {'id': 4, 'name': 'Silicone Spatula Set', 'description': 'Heat-resistant silicone spatulas, set of 3', 'price': 19999, 'compare_price': 29999, 'image': 'utensil', 'category': 'Utensils', 'stock': 200, 'featured': True, 'bestseller': False, 'rating': 4.7, 'reviews': 203},
    {'id': 5, 'name': 'Cast Iron Dutch Oven', 'description': '5.5qt enameled cast iron dutch oven', 'price': 129999, 'compare_price': 179999, 'image': 'pot', 'category': 'Pots', 'stock': 30, 'featured': True, 'bestseller': True, 'rating': 4.9, 'reviews': 67},
    {'id': 6, 'name': 'Wooden Cutting Board', 'description': 'Large bamboo cutting board', 'price': 24999, 'compare_price': None, 'image': 'cutting-board', 'category': 'Utensils', 'stock': 60, 'featured': False, 'bestseller': False, 'rating': 4.4, 'reviews': 45},
    {'id': 7, 'name': 'Kitchen Knife Set', 'description': '6-piece premium knife set with block', 'price': 199999, 'compare_price': 299999, 'image': 'knife', 'category': 'Knives', 'stock': 25, 'featured': True, 'bestseller': True, 'rating': 4.8, 'reviews': 98},
    {'id': 8, 'name': 'Measuring Cups Set', 'description': 'Stainless steel measuring cups and spoons', 'price': 14999, 'compare_price': 24999, 'image': 'cup', 'category': 'Utensils', 'stock': 150, 'featured': False, 'bestseller': False, 'rating': 4.6, 'reviews': 112},
]

CATEGORIES = [
    {'id': 1, 'name': 'Knives', 'slug': 'knives', 'icon': 'knife', 'count': 2},
    {'id': 2, 'name': 'Pans', 'slug': 'pans', 'icon': 'pan', 'count': 1},
    {'id': 3, 'name': 'Pots', 'slug': 'pots', 'icon': 'pot', 'count': 2},
    {'id': 4, 'name': 'Utensils', 'slug': 'utensils', 'icon': 'utensils', 'count': 3},
]

ORDERS = []
USERS = []
NEWSLETTER_SUBSCRIBERS = []
REVIEWS = [
    {'id': 1, 'product_id': 1, 'user': 'John D.', 'rating': 5, 'title': 'Excellent knife!', 'comment': 'Very sharp and well-balanced. Highly recommend!', 'date': '2024-01-15', 'approved': True},
    {'id': 2, 'product_id': 2, 'user': 'Mary A.', 'rating': 4, 'title': 'Great non-stick pan', 'comment': 'Food slides right off. Very easy to clean.', 'date': '2024-01-20', 'approved': True},
]
WISHLISTS = {}

# ==================== HELPER FUNCTIONS ====================
def get_product(product_id):
    return next((p for p in PRODUCTS if p['id'] == product_id), None)

def get_products(category=None, search=None, sort=None):
    products = PRODUCTS.copy()
    if category:
        products = [p for p in products if p['category'].lower() == category.lower()]
    if search:
        products = [p for p in products if search.lower() in p['name'].lower() or search.lower() in p['description'].lower()]
    if sort == 'price_asc':
        products.sort(key=lambda x: x['price'])
    elif sort == 'price_desc':
        products.sort(key=lambda x: x['price'], reverse=True)
    return products

def calculate_cart_total(cart):
    total = 0
    for product_id, quantity in cart.items():
        product = get_product(int(product_id))
        if product:
            total += product['price'] * quantity
    return total

# ==================== ROUTES ====================
@app.route('/')
def home():
    featured = [p for p in PRODUCTS if p.get('featured', False)]
    bestsellers = [p for p in PRODUCTS if p.get('bestseller', False)]
    return render_template('home.html', products=featured[:4], bestsellers=bestsellers[:4], categories=CATEGORIES)

@app.route('/products')
def products_page():
    category = request.args.get('category')
    search = request.args.get('search')
    sort = request.args.get('sort')
    products_list = get_products(category, search, sort)
    return render_template('products.html', products=products_list, categories=CATEGORIES, current_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('products_page'))
    product_reviews = [r for r in REVIEWS if r['product_id'] == product_id and r.get('approved', False)]
    return render_template('product_detail.html', product=product, reviews=product_reviews)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = get_products(search=query)
    return render_template('search_results.html', products=results, query=query)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, quantity in cart.items():
        product = get_product(int(product_id))
        if product:
            item_total = product['price'] * quantity
            total += item_total
            cart_items.append({'product': product, 'quantity': quantity, 'total': item_total})
    return render_template('cart.html', cart_items=cart_items, total=total, discount=0, final_total=total, coupon=None)

@app.route('/cart/count')
def cart_count():
    cart = session.get('cart', {})
    return jsonify({'count': sum(cart.values())})

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
        return redirect(url_for('products_page'))
    subtotal = calculate_cart_total(cart)
    shipping = 0 if subtotal >= 50000 else 2500
    final_total = subtotal + shipping
    return render_template('checkout.html', subtotal=subtotal, discount=0, total=subtotal, shipping=shipping, final_total=final_total)

@app.route('/place-order', methods=['POST'])
def place_order():
    if 'user' not in session:
        flash('Please login to place order', 'warning')
        return redirect(url_for('login'))
    
    cart = session.get('cart', {})
    subtotal = calculate_cart_total(cart)
    shipping = 0 if subtotal >= 50000 else 2500
    
    order = {
        'id': len(ORDERS) + 1,
        'order_number': f"GK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'customer_name': request.form.get('name'),
        'customer_email': request.form.get('email'),
        'customer_phone': request.form.get('phone'),
        'delivery_address': request.form.get('address'),
        'city': request.form.get('city'),
        'state': request.form.get('state'),
        'payment_method': request.form.get('payment'),
        'subtotal': subtotal,
        'shipping': shipping,
        'total_amount': subtotal + shipping,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    ORDERS.append(order)
    session.pop('cart', None)
    flash(f'Order placed successfully! Order #{order["order_number"]}', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
def orders():
    if 'user' not in session:
        flash('Please login to view orders', 'warning')
        return redirect(url_for('login'))
    user_email = session['user']
    user_orders = [o for o in ORDERS if o['customer_email'] == user_email]
    user_orders.sort(key=lambda x: x['created_at'], reverse=True)
    return render_template('orders.html', orders=user_orders)

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    order = next((o for o in ORDERS if o['id'] == order_id), None)
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('orders'))
    return render_template('order_detail.html', order=order)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Admin login
        if email == 'admin@example.com' and password == 'admin123':
            session['user'] = email
            session['user_name'] = 'Admin'
            session['is_admin'] = True
            flash('Welcome Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        # User login
        user = next((u for u in USERS if u['email'] == email), None)
        if user and user.get('password') == password:
            session['user'] = email
            session['user_name'] = user.get('name', email.split('@')[0])
            session['is_admin'] = False
            flash(f'Welcome back {session["user_name"]}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if any(u['email'] == email for u in USERS):
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        USERS.append({
            'id': len(USERS) + 1,
            'name': name,
            'email': email,
            'password': password,
            'is_admin': False,
            'created_at': datetime.now().isoformat()
        })
        session['user'] = email
        session['user_name'] = name
        flash(f'Account created! Welcome {name}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/wishlist')
def wishlist():
    if 'user' not in session:
        flash('Please login to view wishlist', 'warning')
        return redirect(url_for('login'))
    user_email = session['user']
    wishlist_items = WISHLISTS.get(user_email, [])
    products_in_wishlist = [get_product(pid) for pid in wishlist_items if get_product(pid)]
    return render_template('wishlist.html', products=products_in_wishlist)

@app.route('/add-to-wishlist/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    user_email = session['user']
    if user_email not in WISHLISTS:
        WISHLISTS[user_email] = []
    if product_id not in WISHLISTS[user_email]:
        WISHLISTS[user_email].append(product_id)
        return jsonify({'success': True, 'message': 'Added to wishlist'})
    return jsonify({'success': False, 'message': 'Already in wishlist'})

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        flash('Please login to view profile', 'warning')
        return redirect(url_for('login'))
    user = next((u for u in USERS if u['email'] == session['user']), None)
    return render_template('profile.html', user=user)

# ==================== ADMIN ROUTES ====================
@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/dashboard.html', products=PRODUCTS, orders=ORDERS, users=USERS)

@app.route('/admin/products')
def admin_products():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/products.html', products=PRODUCTS)

@app.route('/admin/orders')
def admin_orders():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/orders.html', orders=ORDERS)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'products': len(PRODUCTS), 'users': len(USERS)})

# This is CRITICAL for Vercel
app = app

if __name__ == '__main__':
    app.run()