from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_file
import os
import json
import csv
import io
from datetime import datetime, timedelta
import secrets

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ==================== DATA STORAGE ====================
PRODUCTS = [
    {'id': 1, 'name': 'Professional Chef Knife', 'description': 'High-carbon stainless steel chef knife with ergonomic handle', 'price': 89999, 'compare_price': 129999, 'image': 'knife', 'category': 'Knives', 'stock': 50, 'featured': True, 'bestseller': True, 'rating': 4.8, 'reviews': 124},
    {'id': 2, 'name': 'Non-Stick Frying Pan', 'description': 'Durable non-stick coating, even heat distribution', 'price': 49999, 'compare_price': 79999, 'image': 'pan', 'category': 'Pans', 'stock': 100, 'featured': True, 'bestseller': True, 'rating': 4.6, 'reviews': 89},
    {'id': 3, 'name': 'Stainless Steel Saucepan', 'description': 'Professional grade saucepan with lid', 'price': 39999, 'compare_price': None, 'image': 'pot', 'category': 'Pots', 'stock': 75, 'featured': False, 'bestseller': False, 'rating': 4.5, 'reviews': 56},
    {'id': 4, 'name': 'Silicone Spatula Set', 'description': 'Heat-resistant silicone spatulas, set of 3', 'price': 19999, 'compare_price': 29999, 'image': 'utensil', 'category': 'Utensils', 'stock': 200, 'featured': True, 'bestseller': False, 'rating': 4.7, 'reviews': 203},
]

CATEGORIES = [
    {'id': 1, 'name': 'Knives', 'slug': 'knives', 'icon': 'knife', 'count': 1},
    {'id': 2, 'name': 'Pans', 'slug': 'pans', 'icon': 'pan', 'count': 1},
    {'id': 3, 'name': 'Pots', 'slug': 'pots', 'icon': 'pot', 'count': 1},
    {'id': 4, 'name': 'Utensils', 'slug': 'utensils', 'icon': 'utensils', 'count': 1},
]

ORDERS = []
USERS = []
NEWSLETTER_SUBSCRIBERS = []
REVIEWS = []
WISHLISTS = {}
chat_sessions = []

# ==================== HELPER FUNCTIONS ====================
def get_product(product_id):
    return next((p for p in PRODUCTS if p['id'] == product_id), None)

def get_products(category=None, search=None, sort=None, min_price=None, max_price=None):
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

# ==================== PUBLIC ROUTES ====================
@app.route('/')
def home():
    featured = [p for p in PRODUCTS if p.get('featured', False)]
    bestsellers = [p for p in PRODUCTS if p.get('bestseller', False)]
    return render_template('home.html', products=featured[:4], bestsellers=bestsellers[:4], categories=CATEGORIES)

@app.route('/products')
def products_page():
    category = request.args.get('category')
    search = request.args.get('q')
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
    return render_template('product_detail.html', product=product, reviews=product_reviews, categories=CATEGORIES)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = get_products(search=query)
    return render_template('search.html', products=results, query=query, categories=CATEGORIES)

@app.route('/categories')
def categories_page():
    return render_template('categories.html', categories=CATEGORIES)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        flash(f'Thank you {name}! Your message has been sent.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

# ==================== CART ROUTES ====================
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

@app.route('/clear-cart', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    return jsonify({'success': True})

# ==================== WISHLIST ROUTES ====================
@app.route('/wishlist')
def wishlist():
    if 'user' not in session:
        flash('Please login to view your wishlist', 'warning')
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

@app.route('/remove-from-wishlist/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    if 'user' not in session:
        return jsonify({'success': False}), 401
    user_email = session['user']
    if user_email in WISHLISTS and product_id in WISHLISTS[user_email]:
        WISHLISTS[user_email].remove(product_id)
        return jsonify({'success': True})
    return jsonify({'success': False})

# ==================== CHECKOUT & ORDERS ====================
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
    return render_template('checkout.html', subtotal=subtotal, shipping=shipping, final_total=final_total, discount=0)

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
    flash('Order placed successfully!', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
def orders():
    if 'user' not in session:
        flash('Please login to view orders', 'warning')
        return redirect(url_for('login'))
    user_email = session['user']
    user_orders = [o for o in ORDERS if o['customer_email'] == user_email]
    return render_template('orders.html', orders=user_orders)

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    if 'user' not in session:
        flash('Please login to view order', 'warning')
        return redirect(url_for('login'))
    order = next((o for o in ORDERS if o['id'] == order_id), None)
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('orders'))
    return render_template('order_detail.html', order=order)

# ==================== AUTH ROUTES ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == 'admin@example.com' and password == 'admin123':
            session['user'] = email
            session['user_name'] = 'Admin'
            session['is_admin'] = True
            flash('Welcome Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        user = next((u for u in USERS if u['email'] == email), None)
        if user and user.get('password') == password:
            session['user'] = email
            session['user_name'] = user.get('name', email.split('@')[0])
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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        flash('Please login to view profile', 'warning')
        return redirect(url_for('login'))
    user = next((u for u in USERS if u['email'] == session['user']), None)
    if request.method == 'POST' and user:
        user['name'] = request.form.get('name')
        user['phone'] = request.form.get('phone')
        user['address'] = request.form.get('address')
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = next((u for u in USERS if u['email'] == email), None)
        if user:
            flash('Password reset link sent to your email!', 'success')
        else:
            flash('Email not found', 'danger')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password == confirm:
            flash('Password reset successfully! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match', 'danger')
    return render_template('reset_password.html')

@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form.get('email')
        flash('Verification email sent!', 'success')
        return redirect(url_for('login'))
    return render_template('resend_verification.html')

# ==================== NEWSLETTER ====================
@app.route('/subscribe-newsletter', methods=['POST'])
def subscribe_newsletter():
    email = request.form.get('email')
    if email and email not in NEWSLETTER_SUBSCRIBERS:
        NEWSLETTER_SUBSCRIBERS.append(email)
        flash('Thank you for subscribing!', 'success')
    else:
        flash('Already subscribed or invalid email', 'warning')
    return redirect(request.referrer or url_for('home'))

# ==================== ADMIN ROUTES ====================
@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/dashboard.html', 
                         total_products=len(PRODUCTS),
                         total_orders=len(ORDERS),
                         total_customers=len(USERS),
                         products=PRODUCTS)

@app.route('/admin/products')
def admin_products():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/products.html', products=PRODUCTS)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    if request.method == 'POST':
        new_id = max([p['id'] for p in PRODUCTS]) + 1 if PRODUCTS else 1
        PRODUCTS.append({
            'id': new_id,
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price')),
            'compare_price': float(request.form.get('compare_price')) if request.form.get('compare_price') else None,
            'image': request.form.get('image', 'utensil'),
            'category': request.form.get('category'),
            'stock': int(request.form.get('stock', 0)),
            'featured': 'featured' in request.form,
            'bestseller': 'bestseller' in request.form,
            'rating': 0,
            'reviews': 0
        })
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/add_product.html', categories=CATEGORIES)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    product = get_product(product_id)
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('admin_products'))
    if request.method == 'POST':
        product.update({
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price')),
            'compare_price': float(request.form.get('compare_price')) if request.form.get('compare_price') else None,
            'image': request.form.get('image', 'utensil'),
            'category': request.form.get('category'),
            'stock': int(request.form.get('stock', 0)),
            'featured': 'featured' in request.form,
            'bestseller': 'bestseller' in request.form,
        })
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/edit_product.html', product=product, categories=CATEGORIES)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    global PRODUCTS
    PRODUCTS = [p for p in PRODUCTS if p['id'] != product_id]
    flash('Product deleted', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
def admin_orders():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/orders.html', orders=ORDERS)

@app.route('/admin/customers')
def admin_customers():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/customers.html', customers=USERS)

@app.route('/admin/coupons')
def admin_coupons():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/coupons.html')

@app.route('/admin/reviews')
def admin_reviews():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/reviews.html', reviews=REVIEWS)

@app.route('/admin/newsletter')
def admin_newsletter():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/newsletter.html', subscribers=NEWSLETTER_SUBSCRIBERS)

@app.route('/admin/reports')
def admin_reports():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/reports.html')

@app.route('/admin/bulk-import')
def bulk_import():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/bulk_import.html')

@app.route('/admin/export-products')
def export_products():
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Category', 'Price', 'Stock'])
    for p in PRODUCTS:
        writer.writerow([p['id'], p['name'], p['category'], p['price'], p['stock']])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='products.csv')

# ==================== HEALTH CHECK ====================
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'products': len(PRODUCTS),
        'orders': len(ORDERS),
        'users': len(USERS)
    })

# ==================== VERCEL HANDLER ====================
app = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)