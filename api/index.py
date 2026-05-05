from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_file
import os
import json
import csv
import io
from datetime import datetime, timedelta
import secrets
import uuid

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ==================== DATA STORAGE (In-memory for Vercel compatibility) ====================

# Products with categories
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

# Categories
CATEGORIES = [
    {'id': 1, 'name': 'Knives', 'slug': 'knives', 'icon': 'knife', 'count': 2},
    {'id': 2, 'name': 'Pans', 'slug': 'pans', 'icon': 'pan', 'count': 1},
    {'id': 3, 'name': 'Pots', 'slug': 'pots', 'icon': 'pot', 'count': 2},
    {'id': 4, 'name': 'Utensils', 'slug': 'utensils', 'icon': 'utensils', 'count': 3},
]

# Orders storage
ORDERS = []

# Users storage
USERS = []

# Coupons storage
COUPONS = [
    {'id': 1, 'code': 'WELCOME10', 'description': '10% off your first order', 'discount_type': 'percentage', 'discount_value': 10, 'min_order': 5000, 'max_discount': 5000, 'used_count': 0, 'usage_limit': 100, 'expiry_date': (datetime.now() + timedelta(days=365)).isoformat(), 'active': True},
    {'id': 2, 'code': 'SAVE20', 'description': '₦20,000 off on orders over ₦100,000', 'discount_type': 'fixed', 'discount_value': 20000, 'min_order': 100000, 'used_count': 0, 'usage_limit': 50, 'expiry_date': (datetime.now() + timedelta(days=180)).isoformat(), 'active': True},
]

# Newsletter subscribers
NEWSLETTER_SUBSCRIBERS = []

# Reviews
REVIEWS = [
    {'id': 1, 'product_id': 1, 'user': 'John D.', 'rating': 5, 'title': 'Excellent knife!', 'comment': 'Very sharp and well-balanced. Highly recommend!', 'date': '2024-01-15', 'approved': True},
    {'id': 2, 'product_id': 2, 'user': 'Mary A.', 'rating': 4, 'title': 'Great non-stick pan', 'comment': 'Food slides right off. Very easy to clean.', 'date': '2024-01-20', 'approved': True},
]

# Wishlist
WISHLISTS = {}

# ==================== HELPER FUNCTIONS ====================

def get_products(category=None, search=None, sort=None, min_price=None, max_price=None):
    """Get products with filters"""
    products = PRODUCTS.copy()
    
    if category:
        products = [p for p in products if p['category'].lower() == category.lower()]
    
    if search:
        products = [p for p in products if search.lower() in p['name'].lower() or search.lower() in p['description'].lower()]
    
    if min_price:
        products = [p for p in products if p['price'] >= float(min_price)]
    
    if max_price:
        products = [p for p in products if p['price'] <= float(max_price)]
    
    if sort == 'price_asc':
        products.sort(key=lambda x: x['price'])
    elif sort == 'price_desc':
        products.sort(key=lambda x: x['price'], reverse=True)
    elif sort == 'rating':
        products.sort(key=lambda x: x.get('rating', 0), reverse=True)
    elif sort == 'bestseller':
        products.sort(key=lambda x: x.get('bestseller', False), reverse=True)
    
    return products

def get_product(product_id):
    return next((p for p in PRODUCTS if p['id'] == product_id), None)

def update_product(product_id, data):
    product = get_product(product_id)
    if product:
        product.update(data)
        return True
    return False

def delete_product(product_id):
    global PRODUCTS
    PRODUCTS = [p for p in PRODUCTS if p['id'] != product_id]
    return True

def add_product(product_data):
    global PRODUCTS
    new_id = max([p['id'] for p in PRODUCTS]) + 1 if PRODUCTS else 1
    product_data['id'] = new_id
    PRODUCTS.append(product_data)
    return new_id

def calculate_cart_total(cart):
    total = 0
    for product_id, quantity in cart.items():
        product = get_product(int(product_id))
        if product:
            total += product['price'] * quantity
    return total

def apply_coupon(coupon_code, subtotal):
    coupon = next((c for c in COUPONS if c['code'] == coupon_code.upper() and c['active']), None)
    if not coupon:
        return None, 0
    
    expiry = datetime.fromisoformat(coupon['expiry_date']) if coupon['expiry_date'] else None
    if expiry and expiry < datetime.now():
        return {'error': 'Coupon has expired'}, 0
    
    if coupon['usage_limit'] and coupon['used_count'] >= coupon['usage_limit']:
        return {'error': 'Coupon usage limit reached'}, 0
    
    if subtotal < coupon['min_order']:
        return {'error': f'Minimum order of ₦{coupon["min_order"]:,.0f} required'}, 0
    
    if coupon['discount_type'] == 'percentage':
        discount = subtotal * (coupon['discount_value'] / 100)
        if coupon.get('max_discount'):
            discount = min(discount, coupon['max_discount'])
    else:
        discount = min(coupon['discount_value'], subtotal)
    
    return coupon, discount

def generate_order_number():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = secrets.token_hex(4).upper()
    return f"GK-{timestamp}-{random_part}"

def get_sales_stats(days=30):
    start_date = datetime.now() - timedelta(days=days)
    recent_orders = [o for o in ORDERS if datetime.fromisoformat(o['created_at']) >= start_date]
    
    total_sales = sum(o['total_amount'] for o in recent_orders)
    total_orders = len(recent_orders)
    avg_order = total_sales / total_orders if total_orders > 0 else 0
    
    return {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order': avg_order,
        'orders_count': total_orders
    }

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def home():
    featured = [p for p in PRODUCTS if p.get('featured', False)]
    bestsellers = [p for p in PRODUCTS if p.get('bestseller', False)]
    return render_template('index.html', products=featured[:4], bestsellers=bestsellers[:4], categories=CATEGORIES)

@app.route('/products')
def products():
    category = request.args.get('category')
    search = request.args.get('search')
    sort = request.args.get('sort')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    
    products_list = get_products(category, search, sort, min_price, max_price)
    return render_template('products.html', products=products_list, categories=CATEGORIES, current_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('products'))
    
    product_reviews = [r for r in REVIEWS if r['product_id'] == product_id and r['approved']]
    return render_template('product_detail.html', product=product, reviews=product_reviews)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = get_products(search=query)
    return render_template('search_results.html', products=results, query=query)

@app.route('/categories')
def categories():
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

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

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
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
    
    coupon = session.get('coupon')
    discount = 0
    if coupon:
        coupon_data, discount = apply_coupon(coupon['code'], total)
        if coupon_data and isinstance(coupon_data, dict) and 'error' in coupon_data:
            session.pop('coupon', None)
    
    final_total = total - discount
    
    return render_template('cart.html', cart_items=cart_items, total=total, discount=discount, final_total=final_total, coupon=session.get('coupon'))

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

@app.route('/admin/remove-subscriber/<email>', methods=['POST'])
def remove_subscriber(email):
    if not session.get('is_admin'):
        return jsonify({'success': False})
    if email in NEWSLETTER_SUBSCRIBERS:
        NEWSLETTER_SUBSCRIBERS.remove(email)
    return jsonify({'success': True})

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return jsonify({'success': True})

@app.route('/apply-coupon', methods=['POST'])
def apply_coupon_route():
    coupon_code = request.form.get('coupon_code', '').strip().upper()
    cart = session.get('cart', {})
    subtotal = calculate_cart_total(cart)
    
    coupon, discount = apply_coupon(coupon_code, subtotal)
    
    if isinstance(coupon, dict) and 'error' in coupon:
        flash(coupon['error'], 'danger')
    elif coupon:
        session['coupon'] = {'code': coupon['code'], 'discount': discount}
        flash(f'Coupon {coupon_code} applied! You saved ₦{discount:,.0f}', 'success')
    else:
        flash('Invalid coupon code', 'danger')
    
    return redirect(url_for('cart'))

@app.route('/remove-coupon', methods=['POST'])
def remove_coupon():
    session.pop('coupon', None)
    flash('Coupon removed', 'info')
    return redirect(url_for('cart'))

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

# ==================== REVIEW ROUTES ====================

@app.route('/add-review/<int:product_id>', methods=['POST'])
def add_review(product_id):
    if 'user' not in session:
        flash('Please login to leave a review', 'warning')
        return redirect(url_for('login'))
    
    rating = int(request.form.get('rating', 0))
    title = request.form.get('title')
    comment = request.form.get('comment')
    
    if rating < 1 or rating > 5:
        flash('Please provide a valid rating', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Check if user already reviewed this product
    existing = next((r for r in REVIEWS if r['product_id'] == product_id and r['user'] == session['user']), None)
    if existing:
        flash('You have already reviewed this product', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    review = {
        'id': len(REVIEWS) + 1,
        'product_id': product_id,
        'user': session['user'],
        'rating': rating,
        'title': title,
        'comment': comment,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'approved': False,  # Needs admin approval
        'verified_purchase': False  # Check if user actually bought the product
    }
    
    REVIEWS.append(review)
    
    flash('Thank you for your review! It will appear after moderation.', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

# ==================== NEWSLETTER ROUTES ====================

@app.route('/subscribe-newsletter', methods=['POST'])
def subscribe_newsletter():
    email = request.form.get('email')
    if email and email not in NEWSLETTER_SUBSCRIBERS:
        NEWSLETTER_SUBSCRIBERS.append(email)
        flash('Thank you for subscribing to our newsletter!', 'success')
    else:
        flash('Email already subscribed or invalid', 'warning')
    return redirect(request.referrer or url_for('home'))

# ==================== CHECKOUT & ORDERS ====================

@app.route('/checkout')
def checkout():
    if 'user' not in session:
        flash('Please login to checkout', 'warning')
        return redirect(url_for('login'))
    
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('products'))
    
    subtotal = calculate_cart_total(cart)
    coupon = session.get('coupon')
    discount = coupon.get('discount', 0) if coupon else 0
    total = subtotal - discount
    
    shipping = 0 if total >= 50000 else 2500
    final_total = total + shipping
    
    return render_template('checkout.html', subtotal=subtotal, discount=discount, total=total, shipping=shipping, final_total=final_total)

@app.route('/place-order', methods=['POST'])
def place_order():
    if 'user' not in session:
        flash('Please login to place order', 'warning')
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    city = request.form.get('city')
    state = request.form.get('state')
    payment = request.form.get('payment')
    
    cart = session.get('cart', {})
    subtotal = calculate_cart_total(cart)
    coupon = session.get('coupon')
    discount = coupon.get('discount', 0) if coupon else 0
    total = subtotal - discount
    shipping = 0 if total >= 50000 else 2500
    final_total = total + shipping
    
    order = {
        'id': len(ORDERS) + 1,
        'order_number': generate_order_number(),
        'customer_name': name,
        'customer_email': email,
        'customer_phone': phone,
        'delivery_address': address,
        'city': city,
        'state': state,
        'payment_method': payment,
        'cart_items': cart,
        'subtotal': subtotal,
        'discount': discount,
        'shipping': shipping,
        'total_amount': final_total,
        'coupon_code': coupon['code'] if coupon else None,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    ORDERS.append(order)
    
    # Clear cart and coupon
    session.pop('cart', None)
    session.pop('coupon', None)
    
    # Update coupon usage count
    if coupon:
        coupon_data = next((c for c in COUPONS if c['code'] == coupon['code']), None)
        if coupon_data:
            coupon_data['used_count'] += 1
    
    flash(f'Thank you {name}! Your order #{order["order_number"]} has been placed successfully.', 'success')
    return redirect(url_for('order_detail', order_id=order['id']))

@app.route('/orders')
def orders():
    if 'user' not in session:
        flash('Please login to view your orders', 'warning')
        return redirect(url_for('login'))
    
    user_email = session['user']
    user_orders = [o for o in ORDERS if o['customer_email'] == user_email]
    user_orders.sort(key=lambda x: x['created_at'], reverse=True)
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
    
    if order['customer_email'] != session['user'] and not session.get('is_admin'):
        flash('Access denied', 'danger')
        return redirect(url_for('orders'))
    
    return render_template('order_detail.html', order=order)

# ==================== AUTH ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = next((u for u in USERS if u['email'] == email), None)
        if user and user.get('password') == password:
            session['user'] = email
            session['user_name'] = user.get('name', email.split('@')[0])
            session['is_admin'] = user.get('is_admin', False)
            flash(f'Welcome back {session["user_name"]}!', 'success')
            return redirect(url_for('home'))
        elif email == 'admin@example.com' and password == 'admin123':
            session['user'] = email
            session['user_name'] = 'Admin'
            session['is_admin'] = True
            flash('Welcome Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        flash('Please login to view profile', 'warning')
        return redirect(url_for('login'))
    
    user = next((u for u in USERS if u['email'] == session['user']), None)
    
    if request.method == 'POST':
        if user:
            user['name'] = request.form.get('name')
            user['phone'] = request.form.get('phone')
            user['address'] = request.form.get('address')
            flash('Profile updated successfully!', 'success')
    
    return render_template('profile.html', user=user)

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    # Calculate stats
    total_sales = sum(o['total_amount'] for o in ORDERS)
    total_orders = len(ORDERS)
    total_customers = len(USERS)
    total_products = len(PRODUCTS)
    pending_reviews = len([r for r in REVIEWS if not r.get('approved', False)])
    
    # Low stock products
    low_stock = [p for p in PRODUCTS if p['stock'] < 10]
    
    # Recent orders
    recent_orders = sorted(ORDERS, key=lambda x: x['created_at'], reverse=True)[:5]
    
    # Chart data for last 7 days
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        chart_labels.append(date.strftime('%a'))
        daily_sales = sum(o['total_amount'] for o in ORDERS if o.get('created_at', '')[:10] == date_str)
        chart_data.append(daily_sales)
    
    return render_template('admin/dashboard.html', 
                         total_sales=total_sales,
                         total_orders=total_orders,
                         total_customers=total_customers,
                         total_products=total_products,
                         pending_reviews=pending_reviews,
                         low_stock=low_stock,
                         recent_orders=recent_orders,
                         chart_labels=chart_labels,
                         chart_data=chart_data)
    
@app.route('/admin/bulk-import')
def bulk_import():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/bulk_import.html')

@app.route('/admin/products/import', methods=['POST'])
def import_products_csv():
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    
    file = request.files.get('csv_file')
    if not file:
        flash('No file uploaded', 'danger')
        return redirect(url_for('bulk_import'))
    
    import csv
    import io
    content = file.stream.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(content))
    
    imported = 0
    for row in csv_reader:
        product = {
            'id': len(PRODUCTS) + 1 + imported,
            'name': row.get('name'),
            'sku': row.get('sku'),
            'price': float(row.get('price', 0)),
            'stock': int(row.get('stock', 0)),
            'description': row.get('description', ''),
            'category': row.get('category', 'Utensils'),
            'image': 'utensil',
            'featured': False,
            'bestseller': False,
            'rating': 0,
            'reviews': 0
        }
        PRODUCTS.append(product)
        imported += 1
    
    flash(f'Imported {imported} products successfully!', 'success')
    return redirect(url_for('admin_products'))

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
        product = {
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
        }
        add_product(product)
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
        update_product(product_id, {
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
    
    delete_product(product_id)
    flash('Product deleted', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
def admin_orders():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    status_filter = request.args.get('status')
    orders = ORDERS
    if status_filter:
        orders = [o for o in orders if o['status'] == status_filter]
    
    orders.sort(key=lambda x: x['created_at'], reverse=True)
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
def admin_update_order_status(order_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    
    data = request.get_json()
    status = data.get('status')
    
    order = next((o for o in ORDERS if o['id'] == order_id), None)
    if order:
        order['status'] = status
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 404

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
    return render_template('admin/coupons.html', coupons=COUPONS)

@app.route('/admin/coupons/add', methods=['POST'])
def admin_add_coupon():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    coupon = {
        'id': len(COUPONS) + 1,
        'code': request.form.get('code').upper(),
        'description': request.form.get('description'),
        'discount_type': request.form.get('discount_type'),
        'discount_value': float(request.form.get('discount_value')),
        'min_order': float(request.form.get('min_order', 0)),
        'max_discount': float(request.form.get('max_discount')) if request.form.get('max_discount') else None,
        'used_count': 0,
        'usage_limit': int(request.form.get('usage_limit')) if request.form.get('usage_limit') else None,
        'expiry_date': request.form.get('expiry_date') or (datetime.now() + timedelta(days=365)).isoformat(),
        'active': True
    }
    COUPONS.append(coupon)
    flash(f'Coupon {coupon["code"]} added!', 'success')
    return redirect(url_for('admin_coupons'))

@app.route('/admin/coupons/toggle/<int:coupon_id>', methods=['POST'])
def admin_toggle_coupon(coupon_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    
    coupon = next((c for c in COUPONS if c['id'] == coupon_id), None)
    if coupon:
        coupon['active'] = not coupon['active']
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/admin/reviews')
def admin_reviews():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    pending = [r for r in REVIEWS if not r.get('approved', False)]
    approved = [r for r in REVIEWS if r.get('approved', False)]
    return render_template('admin/reviews.html', pending_reviews=pending, approved_reviews=approved)

@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    message = data.get('message')
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    chat_sessions[session_id].append({
        'sender': 'user',
        'message': message,
        'time': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})
@app.route('/admin/reports')
def admin_reports():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    # Sales report data
    sales_by_day = {}
    for order in ORDERS:
        date = order['created_at'][:10]
        sales_by_day[date] = sales_by_day.get(date, 0) + order['total_amount']
    
    return render_template('admin/reports.html', sales_by_day=sales_by_day)

@app.route('/api/chat/messages/<session_id>')
def chat_messages(session_id):
    messages = chat_sessions.get(session_id, [])
    return jsonify({'messages': messages})

@app.route('/admin/reviews/approve/<int:review_id>', methods=['POST'])
def admin_approve_review(review_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    
    review = next((r for r in REVIEWS if r['id'] == review_id), None)
    if review:
        review['approved'] = True
        # Update product rating
        product = get_product(review['product_id'])
        if product:
            product_reviews = [r for r in REVIEWS if r['product_id'] == review['product_id'] and r.get('approved', False)]
            if product_reviews:
                product['rating'] = sum(r['rating'] for r in product_reviews) / len(product_reviews)
                product['reviews'] = len(product_reviews)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/admin/reviews/delete/<int:review_id>', methods=['POST'])
def admin_delete_review(review_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    
    global REVIEWS
    REVIEWS = [r for r in REVIEWS if r['id'] != review_id]
    return jsonify({'success': True})

@app.route('/admin/newsletter')
def admin_newsletter():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/newsletter.html', subscribers=NEWSLETTER_SUBSCRIBERS)


@app.route('/admin/send-newsletter', methods=['POST'])
def send_newsletter():
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    subject = request.form.get('subject')
    message = request.form.get('message')
    flash(f'Newsletter "{subject}" sent to {len(NEWSLETTER_SUBSCRIBERS)} subscribers!', 'success')
    return redirect(url_for('admin_newsletter'))

# Export routes
@app.route('/admin/export-orders')
def export_orders():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order #', 'Customer', 'Email', 'Total', 'Status', 'Date'])
    for order in ORDERS:
        writer.writerow([order['order_number'], order['customer_name'], order['customer_email'], order['total_amount'], order['status'], order['created_at'][:10]])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='orders_export.csv')

@app.route('/admin/export-customers')
def export_customers():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Email', 'Name', 'Joined'])
    for user in USERS:
        writer.writerow([user['email'], user.get('name', ''), user.get('created_at', '')[:10]])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='customers_export.csv')

@app.route('/admin/export-products')
def admin_export_products():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Category', 'Price', 'Stock', 'Description'])
    for p in PRODUCTS:
        writer.writerow([p['id'], p['name'], p['category'], p['price'], p['stock'], p['description']])
    
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='products_export.csv')

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'products': len(PRODUCTS),
        'orders': len(ORDERS),
        'users': len(USERS)
    })

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)