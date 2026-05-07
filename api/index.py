import os
import requests
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_file
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
import secrets
import json
import csv
import io

# Create Flask app
app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ==================== SUPABASE CONFIGURATION (using REST API) ====================
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://fendtnsspplwehzagdgj.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'sb_publishable_7kx1UWYtb-UDbRtAKhVxUA_Mx-6l9fi')

def supabase_request(method, endpoint, data=None):
    """Make a request to Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return None
        
        if response.status_code in [200, 201, 204]:
            return response.json() if response.text else True
        else:
            print(f"Supabase error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

# ==================== EMAIL CONFIGURATION ====================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

# Initialize serializer for email tokens
serializer = URLSafeTimedSerializer(app.secret_key)

# ==================== DATABASE FUNCTIONS ====================

def get_products_from_db(category=None, search=None, sort=None, min_price=None, max_price=None):
    """Get products from Supabase"""
    query = "products?select=*"
    conditions = []
    
    if category:
        conditions.append(f"category=eq.{category}")
    if min_price:
        conditions.append(f"price=gte.{min_price}")
    if max_price:
        conditions.append(f"price=lte.{max_price}")
    
    if conditions:
        query += "&" + "&".join(conditions)
    
    if sort == 'price_asc':
        query += "&order=price.asc"
    elif sort == 'price_desc':
        query += "&order=price.desc"
    else:
        query += "&order=created_at.desc"
    
    if search:
        result = supabase_request('GET', f"products?select=*&name=ilike.%{search}%")
    else:
        result = supabase_request('GET', query)
    
    return result if result else []

def get_product_from_db(product_id):
    """Get single product from Supabase"""
    result = supabase_request('GET', f"products?select=*&id=eq.{product_id}")
    return result[0] if result else None

def save_user_to_db(user_data):
    """Save user to Supabase"""
    return supabase_request('POST', 'users', user_data)

def get_user_from_db(email):
    """Get user from Supabase by email"""
    result = supabase_request('GET', f"users?select=*&email=eq.{email}")
    return result[0] if result else None

def update_user_in_db(email, user_data):
    """Update user in Supabase"""
    return supabase_request('PATCH', f"users?email=eq.{email}", user_data)

def save_order_to_db(order_data):
    """Save order to Supabase"""
    return supabase_request('POST', 'orders', order_data)

def get_user_orders_from_db(email):
    """Get user orders from Supabase"""
    result = supabase_request('GET', f"orders?select=*&customer_email=eq.{email}&order=created_at.desc")
    return result if result else []

def get_all_orders_from_db():
    """Get all orders for admin"""
    result = supabase_request('GET', "orders?select=*&order=created_at.desc")
    return result if result else []

def update_order_status_in_db(order_id, status):
    """Update order status"""
    return supabase_request('PATCH', f"orders?id=eq.{order_id}", {'status': status})

def get_coupon_from_db(code):
    """Get coupon from Supabase"""
    result = supabase_request('GET', f"coupons?select=*&code=eq.{code.upper()}&active=eq.true")
    return result[0] if result else None

def update_coupon_usage_in_db(coupon_id):
    """Update coupon usage count"""
    result = supabase_request('GET', f"coupons?select=used_count&id=eq.{coupon_id}")
    if result:
        current_count = result[0].get('used_count', 0)
        new_count = current_count + 1
        return supabase_request('PATCH', f"coupons?id=eq.{coupon_id}", {'used_count': new_count})
    return None

def get_reviews_from_db(product_id):
    """Get approved reviews for product"""
    result = supabase_request('GET', f"reviews?select=*&product_id=eq.{product_id}&approved=eq.true&order=created_at.desc")
    return result if result else []

def save_review_to_db(review_data):
    """Save review to Supabase"""
    return supabase_request('POST', 'reviews', review_data)

def save_newsletter_subscriber_to_db(email):
    """Save newsletter subscriber to Supabase"""
    existing = supabase_request('GET', f"newsletter_subscribers?select=*&email=eq.{email}")
    if existing:
        return True
    return supabase_request('POST', 'newsletter_subscribers', {'email': email})

# ==================== FALLBACK DATA ====================
CATEGORIES = [
    {'id': 1, 'name': 'Knives', 'slug': 'knives', 'icon': 'knife', 'count': 2},
    {'id': 2, 'name': 'Pans', 'slug': 'pans', 'icon': 'pan', 'count': 1},
    {'id': 3, 'name': 'Pots', 'slug': 'pots', 'icon': 'pot', 'count': 2},
    {'id': 4, 'name': 'Utensils', 'slug': 'utensils', 'icon': 'utensils', 'count': 3},
]

chat_sessions = {}

# ==================== EMAIL FUNCTIONS ====================

def send_verification_email(user_email, name, token):
    base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
    verification_link = f"{base_url}/verify-email/{token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #E67E22; color: white; padding: 20px; text-align: center; }}
            .button {{ background: #E67E22; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h2>Golden Kitchen Nigeria 🇳🇬</h2></div>
            <div class="content">
                <h3>Hello {name}!</h3>
                <p>Please verify your email:</p>
                <p><a href="{verification_link}" class="button">Verify Email</a></p>
                <p>This link expires in 24 hours.</p>
            </div>
        </div>
    </body>
    </html>
    """
    try:
        msg = Message("Verify Your Email - Golden Kitchen Nigeria", recipients=[user_email])
        msg.html = html
        mail.send(msg)
        print(f"✅ Verification email sent to {user_email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def send_welcome_email(user_email, name):
    base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
    shop_link = f"{base_url}/products"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #E67E22; color: white; padding: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h2>Welcome to Golden Kitchen Nigeria!</h2></div>
            <div class="content">
                <h3>Hello {name}!</h3>
                <p>Your account is now active!</p>
                <p><a href="{shop_link}" class="button">Start Shopping</a></p>
                <p>Use code <strong>WELCOME10</strong> for 10% off!</p>
            </div>
        </div>
    </body>
    </html>
    """
    try:
        msg = Message("Welcome to Golden Kitchen Nigeria! 🎉", recipients=[user_email])
        msg.html = html
        mail.send(msg)
        return True
    except Exception as e:
        print(f"❌ Welcome email error: {e}")
        return False

def send_password_reset_email(user_email, token):
    base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
    reset_link = f"{base_url}/reset-password/{token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #E67E22; color: white; padding: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h2>Reset Your Password</h2></div>
            <div class="content">
                <p><a href="{reset_link}" class="button">Reset Password</a></p>
                <p>This link expires in 1 hour.</p>
            </div>
        </div>
    </body>
    </html>
    """
    try:
        msg = Message("Reset Your Password - Golden Kitchen Nigeria", recipients=[user_email])
        msg.html = html
        mail.send(msg)
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def send_order_confirmation(order):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #E67E22; color: white; padding: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h2>Order Confirmation #{order['order_number']}</h2></div>
            <div class="content">
                <p>Thank you for your order!</p>
                <p><strong>Total:</strong> ₦{order['total_amount']:,.0f}</p>
                <p><strong>Payment Method:</strong> {order['payment_method']}</p>
            </div>
        </div>
    </body>
    </html>
    """
    try:
        msg = Message(f"Order Confirmation #{order['order_number']}", recipients=[order['customer_email']])
        msg.html = html
        mail.send(msg)
        return True
    except Exception as e:
        print(f"❌ Order email error: {e}")
        return False

# ==================== HELPER FUNCTIONS ====================

def calculate_cart_total(cart):
    total = 0
    for product_id, quantity in cart.items():
        product = get_product_from_db(int(product_id))
        if product:
            total += product['price'] * quantity
    return total

def generate_order_number():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = secrets.token_hex(4).upper()
    return f"GK-{timestamp}-{random_part}"

def apply_coupon(coupon_code, subtotal):
    coupon = get_coupon_from_db(coupon_code)
    if not coupon:
        return None, 0
    if coupon.get('expiry_date'):
        expiry = datetime.fromisoformat(coupon['expiry_date'])
        if expiry < datetime.now():
            return {'error': 'Coupon expired'}, 0
    if coupon.get('usage_limit') and coupon['used_count'] >= coupon['usage_limit']:
        return {'error': 'Coupon usage limit reached'}, 0
    if subtotal < coupon['min_order']:
        return {'error': f'Minimum order ₦{coupon["min_order"]:,.0f} required'}, 0
    if coupon['discount_type'] == 'percentage':
        discount = subtotal * (coupon['discount_value'] / 100)
        if coupon.get('max_discount'):
            discount = min(discount, coupon['max_discount'])
    else:
        discount = min(coupon['discount_value'], subtotal)
    return coupon, discount

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def home():
    products = get_products_from_db()[:4]
    return render_template('index.html', products=products, categories=CATEGORIES)

@app.route('/products')
def products():
    category = request.args.get('category')
    search = request.args.get('search')
    sort = request.args.get('sort')
    products_list = get_products_from_db(category, search, sort)
    return render_template('products.html', products=products_list, categories=CATEGORIES, current_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = get_product_from_db(product_id)
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('products'))
    reviews = get_reviews_from_db(product_id)
    return render_template('product_detail.html', product=product, reviews=reviews)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = get_products_from_db(search=query)
    return render_template('search_results.html', products=results, query=query)

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
    for pid, qty in cart.items():
        product = get_product_from_db(int(pid))
        if product:
            item_total = product['price'] * qty
            total += item_total
            cart_items.append({'product': product, 'quantity': qty, 'total': item_total})
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
    wishlist_items = session.get('wishlist', [])
    products_in_wishlist = [get_product_from_db(pid) for pid in wishlist_items if get_product_from_db(pid)]
    return render_template('wishlist.html', products=products_in_wishlist)

@app.route('/add-to-wishlist/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    wishlist = session.get('wishlist', [])
    if product_id not in wishlist:
        wishlist.append(product_id)
        session['wishlist'] = wishlist
        return jsonify({'success': True, 'message': 'Added to wishlist'})
    return jsonify({'success': False, 'message': 'Already in wishlist'})

@app.route('/remove-from-wishlist/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    if 'user' not in session:
        return jsonify({'success': False}), 401
    wishlist = session.get('wishlist', [])
    if product_id in wishlist:
        wishlist.remove(product_id)
        session['wishlist'] = wishlist
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
    review_data = {
        'product_id': product_id,
        'user_email': session['user'],
        'rating': rating,
        'title': title,
        'comment': comment,
        'approved': False
    }
    save_review_to_db(review_data)
    flash('Thank you for your review! It will appear after moderation.', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

# ==================== NEWSLETTER ROUTES ====================

@app.route('/subscribe-newsletter', methods=['POST'])
def subscribe_newsletter():
    email = request.form.get('email')
    if email:
        save_newsletter_subscriber_to_db(email)
        flash('Thank you for subscribing!', 'success')
    else:
        flash('Please provide a valid email', 'warning')
    return redirect(request.referrer or url_for('home'))

# ==================== CHECKOUT & ORDERS ====================

@app.route('/checkout')
def checkout():
    if 'user' not in session:
        flash('Please login to checkout', 'warning')
        return redirect(url_for('login'))
    return render_template('checkout.html')

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
    
    order_data = {
        'order_number': generate_order_number(),
        'customer_name': name,
        'customer_email': email,
        'customer_phone': phone,
        'delivery_address': address,
        'city': city,
        'state': state,
        'payment_method': payment,
        'cart_items': json.dumps(cart),
        'subtotal': subtotal,
        'discount': discount,
        'shipping': shipping,
        'total_amount': final_total,
        'coupon_code': coupon['code'] if coupon else None,
        'status': 'pending'
    }
    
    saved_order = save_order_to_db(order_data)
    if saved_order:
        send_order_confirmation(order_data)
    
    session.pop('cart', None)
    session.pop('coupon', None)
    
    if coupon and coupon.get('id'):
        update_coupon_usage_in_db(coupon['id'])
    
    flash(f'Thank you {name}! Your order #{order_data["order_number"]} has been placed.', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
def orders():
    if 'user' not in session:
        flash('Please login to view orders', 'warning')
        return redirect(url_for('login'))
    user_orders = get_user_orders_from_db(session['user'])
    return render_template('orders.html', orders=user_orders)

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    if 'user' not in session:
        flash('Please login to view order', 'warning')
        return redirect(url_for('login'))
    
    result = supabase_request('GET', f"orders?select=*&id=eq.{order_id}")
    if result:
        order = result[0]
        if order['customer_email'] != session['user'] and not session.get('is_admin'):
            flash('Access denied', 'danger')
            return redirect(url_for('orders'))
        return render_template('order_detail.html', order=order)
    
    flash('Order not found', 'danger')
    return redirect(url_for('orders'))

# ==================== AUTH ROUTES ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing = get_user_from_db(email)
        if existing:
            flash('Email already registered', 'danger')
            return redirect(url_for('login'))
        
        token = serializer.dumps(email, salt='email-verify')
        user_data = {'name': name, 'email': email, 'password': password, 'is_admin': False, 'is_verified': False}
        user = save_user_to_db(user_data)
        
        if user:
            send_verification_email(email, name, token)
            flash(f'✅ Verification sent to {email}!', 'success')
        else:
            flash('Registration failed', 'danger')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/verify-email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verify', max_age=86400)
        user = get_user_from_db(email)
        if user and not user.get('is_verified'):
            update_user_in_db(email, {'is_verified': True})
            send_welcome_email(email, user.get('name', 'Customer'))
            flash('🎉 Email verified! You can now login.', 'success')
        else:
            flash('Already verified or expired', 'warning')
    except:
        flash('Invalid or expired link', 'danger')
    return redirect(url_for('login'))

@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form.get('email')
        user = get_user_from_db(email)
        if user and not user.get('is_verified'):
            token = serializer.dumps(email, salt='email-verify')
            send_verification_email(email, user.get('name', 'Customer'), token)
            flash('New verification link sent!', 'success')
        else:
            flash('Email not found or already verified', 'warning')
        return redirect(url_for('login'))
    return render_template('resend_verification.html')

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
        
        user = get_user_from_db(email)
        if not user:
            flash('Email not found', 'danger')
            return redirect(url_for('register'))
        if user.get('password') != password:
            flash('Invalid password', 'danger')
            return render_template('login.html')
        if not user.get('is_verified'):
            flash('Please verify your email first', 'warning')
            return redirect(url_for('resend_verification'))
        
        session['user'] = email
        session['user_name'] = user.get('name', email.split('@')[0])
        session['is_admin'] = user.get('is_admin', False)
        flash(f'Welcome back!', 'success')
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        flash('Please login', 'warning')
        return redirect(url_for('login'))
    user = get_user_from_db(session['user'])
    if request.method == 'POST' and user:
        update_data = {}
        if request.form.get('name'): update_data['name'] = request.form.get('name')
        if request.form.get('phone'): update_data['phone'] = request.form.get('phone')
        if request.form.get('address'): update_data['address'] = request.form.get('address')
        if request.form.get('city'): update_data['city'] = request.form.get('city')
        if request.form.get('state'): update_data['state'] = request.form.get('state')
        if update_data:
            update_user_in_db(session['user'], update_data)
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/order/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    if 'user' not in session:
        flash('Please login', 'warning')
        return redirect(url_for('login'))
    
    result = supabase_request('GET', f"orders?select=*&id=eq.{order_id}")
    if result:
        order = result[0]
        if order['customer_email'] != session['user']:
            flash('Access denied', 'danger')
            return redirect(url_for('orders'))
        if order['status'] not in ['pending', 'processing']:
            flash('This order cannot be cancelled', 'warning')
            return redirect(url_for('order_detail', order_id=order_id))
        supabase_request('PATCH', f"orders?id=eq.{order_id}", {'status': 'cancelled'})
        flash('Order cancelled!', 'success')
    else:
        flash('Order not found', 'danger')
    return redirect(url_for('orders'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    orders = get_all_orders_from_db()
    products = get_products_from_db()
    total_sales = sum(o.get('total_amount', 0) for o in orders)
    total_orders = len(orders)
    total_products = len(products)
    
    return render_template('admin/dashboard.html', 
                         total_sales=total_sales,
                         total_orders=total_orders,
                         total_products=total_products)

@app.route('/admin/products')
def admin_products():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    products = get_products_from_db()
    return render_template('admin/products.html', products=products)

@app.route('/admin/orders')
def admin_orders():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    orders = get_all_orders_from_db()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/customers')
def admin_customers():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    users = supabase_request('GET', "users?select=*") or []
    return render_template('admin/customers.html', customers=users)

@app.route('/health')
def health():
    products = get_products_from_db()
    return jsonify({
        'status': 'ok',
        'supabase': True,
        'products': len(products)
    })

@app.route('/debug')
def debug():
    return jsonify({
        'status': 'ok',
        'supabase_connected': True,
        'env_vars': {
            'MAIL_USERNAME': bool(os.environ.get('MAIL_USERNAME')),
            'MAIL_PASSWORD': bool(os.environ.get('MAIL_PASSWORD')),
            'SECRET_KEY': bool(os.environ.get('SECRET_KEY')),
            'SUPABASE_URL': bool(SUPABASE_URL),
            'SUPABASE_KEY': bool(SUPABASE_KEY)
        }
    })

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)