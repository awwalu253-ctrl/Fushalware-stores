import os
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from supabase import create_client, Client
import requests
import json
import secrets
import json
import csv
import io
import traceback

# Create Flask app
app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ==================== SUPABASE CONFIGURATION (using requests) ====================
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
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Supabase error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

# ==================== SUPABASE CONFIGURATION ====================
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://fendtnsspplwehzagdgj.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'sb_publishable_7kx1UWYtb-UDbRtAKhVxUA_Mx-6l9fi')

# Remove this line:
# supabase = True

# Add these lines:
try:
    from supabase import create_client, Client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase connected successfully!")
except Exception as e:
    print(f"❌ Supabase connection error: {e}")
    supabase = None

# ==================== EMAIL CONFIGURATION ====================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

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
            .button {{ background: #E67E22; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h2>Golden Kitchen Nigeria 🇳🇬</h2></div>
            <div class="content">
                <h3>Hello {name}!</h3>
                <p>Please verify your email address to start shopping:</p>
                <p style="text-align: center;">
                    <a href="{verification_link}" class="button">Verify Email</a>
                </p>
                <p>Or copy this link: <br><small>{verification_link}</small></p>
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
            .button {{ background: #E67E22; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h2>Welcome to Golden Kitchen Nigeria!</h2></div>
            <div class="content">
                <h3>Hello {name}!</h3>
                <p>Thank you for verifying your email address.</p>
                <p>Your account is now fully active and you can start shopping!</p>
                <p style="text-align: center;">
                    <a href="{shop_link}" class="button">Start Shopping</a>
                </p>
                <p>Use code <strong>WELCOME10</strong> for 10% off your first order! 🎉</p>
                <p>Happy Cooking!<br>Golden Kitchen Nigeria Team 🇳🇬</p>
            </div>
        </div>
    </body>
    </html>
    """
    try:
        msg = Message("Welcome to Golden Kitchen Nigeria! 🎉", recipients=[user_email])
        msg.html = html
        mail.send(msg)
        print(f"✅ Welcome email sent to {user_email}")
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
            .button {{ background: #E67E22; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h2>Reset Your Password</h2></div>
            <div class="content">
                <p>Click below to reset your password:</p>
                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </p>
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
        print(f"✅ Password reset email sent to {user_email}")
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
                <p>We will notify you when your order ships.</p>
            </div>
        </div>
    </body>
    </html>
    """
    try:
        msg = Message(f"Order Confirmation #{order['order_number']}", recipients=[order['customer_email']])
        msg.html = html
        mail.send(msg)
        print(f"✅ Order confirmation sent to {order['customer_email']}")
        return True
    except Exception as e:
        print(f"❌ Order email error: {e}")
        return False

# ==================== FLASK-LOGIN SETUP ====================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    if not supabase:
        return None
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            user_data = response.data[0]
            class User:
                def __init__(self, data):
                    self.id = data.get('id')
                    self.email = data.get('email')
                    self.name = data.get('name')
                    self.is_admin = data.get('is_admin', False)
                    self.is_authenticated = True
                    self.is_active = True
                    self.is_anonymous = False
                def get_id(self): return str(self.id)
                def get_full_name(self): return self.name or self.email
            return User(user_data)
    except Exception as e:
        print(f"Error loading user: {e}")
    return None

@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)

# ==================== SUPABASE DATABASE FUNCTIONS ====================

def get_products_from_db(category=None, search=None, sort=None, min_price=None, max_price=None):
    if not supabase:
        return []
    try:
        query = supabase.table('products').select('*')
        if category:
            query = query.eq('category', category)
        if search:
            query = query.ilike('name', f'%{search}%')
        if min_price:
            query = query.gte('price', float(min_price))
        if max_price:
            query = query.lte('price', float(max_price))
        if sort == 'price_asc':
            query = query.order('price', desc=False)
        elif sort == 'price_desc':
            query = query.order('price', desc=True)
        elif sort == 'rating':
            query = query.order('rating', desc=True)
        else:
            query = query.order('created_at', desc=True)
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

def get_product_from_db(product_id):
    if not supabase:
        return None
    try:
        response = supabase.table('products').select('*').eq('id', product_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching product: {e}")
        return None

def save_user_to_db(user_data):
    if not supabase:
        return None
    try:
        response = supabase.table('users').insert(user_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error saving user: {e}")
        return None

def get_user_from_db(email):
    if not supabase:
        return None
    try:
        response = supabase.table('users').select('*').eq('email', email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def update_user_in_db(email, user_data):
    if not supabase:
        return None
    try:
        response = supabase.table('users').update(user_data).eq('email', email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating user: {e}")
        return None

def save_order_to_db(order_data):
    if not supabase:
        return None
    try:
        response = supabase.table('orders').insert(order_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error saving order: {e}")
        return None

def get_user_orders_from_db(email):
    if not supabase:
        return []
    try:
        response = supabase.table('orders').select('*').eq('customer_email', email).order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return []

def get_all_orders_from_db():
    if not supabase:
        return []
    try:
        response = supabase.table('orders').select('*').order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return []

def update_order_status_in_db(order_id, status):
    if not supabase:
        return None
    try:
        response = supabase.table('orders').update({'status': status}).eq('id', order_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating order: {e}")
        return None

def save_review_to_db(review_data):
    if not supabase:
        return None
    try:
        response = supabase.table('reviews').insert(review_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error saving review: {e}")
        return None

def get_reviews_from_db(product_id):
    if not supabase:
        return []
    try:
        response = supabase.table('reviews').select('*').eq('product_id', product_id).eq('approved', True).order('created_at', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return []

def save_newsletter_subscriber_to_db(email):
    if not supabase:
        return False
    try:
        existing = supabase.table('newsletter_subscribers').select('*').eq('email', email).execute()
        if existing.data and len(existing.data) > 0:
            return True
        response = supabase.table('newsletter_subscribers').insert({'email': email}).execute()
        return True
    except Exception as e:
        print(f"Error saving subscriber: {e}")
        return False

def get_coupon_from_db(code):
    if not supabase:
        return None
    try:
        response = supabase.table('coupons').select('*').eq('code', code.upper()).eq('active', True).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching coupon: {e}")
        return None

def update_coupon_usage_in_db(coupon_id):
    if not supabase:
        return False
    try:
        # First get current count
        response = supabase.table('coupons').select('used_count').eq('id', coupon_id).execute()
        if response.data:
            current_count = response.data[0].get('used_count', 0)
            new_count = current_count + 1
            supabase.table('coupons').update({'used_count': new_count}).eq('id', coupon_id).execute()
        return True
    except Exception as e:
        print(f"Error updating coupon: {e}")
        return False

# ==================== FALLBACK DATA ====================
CATEGORIES = [
    {'id': 1, 'name': 'Knives', 'slug': 'knives', 'icon': 'knife', 'count': 2},
    {'id': 2, 'name': 'Pans', 'slug': 'pans', 'icon': 'pan', 'count': 1},
    {'id': 3, 'name': 'Pots', 'slug': 'pots', 'icon': 'pot', 'count': 2},
    {'id': 4, 'name': 'Utensils', 'slug': 'utensils', 'icon': 'utensils', 'count': 3},
]

chat_sessions = {}

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
            return {'error': 'Coupon has expired'}, 0
    if coupon.get('usage_limit') and coupon['used_count'] >= coupon['usage_limit']:
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

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def home():
    products = get_products_from_db()[:4]
    bestsellers = [p for p in get_products_from_db() if p.get('bestseller', False)][:4]
    return render_template('index.html', products=products, bestsellers=bestsellers, categories=CATEGORIES)

@app.route('/products')
def products():
    category = request.args.get('category')
    search = request.args.get('search')
    sort = request.args.get('sort')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    products_list = get_products_from_db(category, search, sort, min_price, max_price)
    return render_template('products.html', products=products_list, categories=CATEGORIES, current_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = get_product_from_db(product_id)
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('products'))
    product_reviews = get_reviews_from_db(product_id)
    return render_template('product_detail.html', product=product, reviews=product_reviews)

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
    for product_id, quantity in cart.items():
        product = get_product_from_db(int(product_id))
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
    product = get_product_from_db(int(product_id))
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'})
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
        flash('Thank you for subscribing to our newsletter!', 'success')
    else:
        flash('Please provide a valid email', 'warning')
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
    flash(f'Thank you {name}! Your order #{order_data["order_number"]} has been placed successfully.', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
def orders():
    if 'user' not in session:
        flash('Please login to view your orders', 'warning')
        return redirect(url_for('login'))
    user_email = session['user']
    user_orders = get_user_orders_from_db(user_email)
    return render_template('orders.html', orders=user_orders)

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    if 'user' not in session:
        flash('Please login to view order', 'warning')
        return redirect(url_for('login'))
    if not supabase:
        flash('Order details coming soon', 'info')
        return redirect(url_for('orders'))
    try:
        response = supabase.table('orders').select('*').eq('id', order_id).execute()
        if response.data:
            order = response.data[0]
            if order['customer_email'] != session['user'] and not session.get('is_admin'):
                flash('Access denied', 'danger')
                return redirect(url_for('orders'))
            return render_template('order_detail.html', order=order)
    except Exception as e:
        print(f"Error fetching order: {e}")
    flash('Order not found', 'danger')
    return redirect(url_for('orders'))

# ==================== AUTH ROUTES ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = get_user_from_db(email)
        if existing_user:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('login'))
        
        token = serializer.dumps(email, salt='email-verify')
        
        user_data = {
            'name': name,
            'email': email,
            'password': password,
            'is_admin': False,
            'is_verified': False
        }
        user = save_user_to_db(user_data)
        
        if user:
            send_verification_email(email, name, token)
            flash(f'✅ Registration successful! A verification link has been sent to {email}.', 'success')
            flash('Please check your email and click the verification link to activate your account.', 'info')
        else:
            flash('⚠️ Registration failed. Please try again.', 'danger')
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/verify-email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verify', max_age=86400)
        user = get_user_from_db(email)
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('register'))
        if user.get('is_verified'):
            flash('Email already verified. You can now login.', 'info')
            return redirect(url_for('login'))
        update_user_in_db(email, {'is_verified': True})
        send_welcome_email(email, user.get('name', 'Customer'))
        flash('🎉 Email verified successfully! Your account is now active.', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        print(f"Verification error: {e}")
        flash('The verification link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('resend_verification'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
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
            flash('Email not found. Please register.', 'danger')
            return redirect(url_for('register'))
        if user.get('password') != password:
            flash('Invalid password.', 'danger')
            return render_template('login.html')
        if not user.get('is_verified', False):
            flash('⚠️ Please verify your email before logging in.', 'warning')
            return redirect(url_for('resend_verification'))
        session['user'] = email
        session['user_name'] = user.get('name', email.split('@')[0])
        session['is_admin'] = user.get('is_admin', False)
        flash(f'Welcome back {session["user_name"]}!', 'success')
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form.get('email')
        user = get_user_from_db(email)
        if not user:
            flash('Email not found. Please register first.', 'danger')
            return redirect(url_for('register'))
        if user.get('is_verified', False):
            flash('Email is already verified. You can login.', 'success')
            return redirect(url_for('login'))
        token = serializer.dumps(email, salt='email-verify')
        send_verification_email(email, user.get('name', 'Customer'), token)
        flash(f'✅ New verification link sent to {email}.', 'success')
        return redirect(url_for('login'))
    return render_template('resend_verification.html')

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
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/order/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    if 'user' not in session:
        flash('Please login to cancel order', 'warning')
        return redirect(url_for('login'))
    if not supabase:
        flash('Cannot cancel order at this time', 'danger')
        return redirect(url_for('orders'))
    try:
        response = supabase.table('orders').select('*').eq('id', order_id).execute()
        if response.data:
            order = response.data[0]
            if order['customer_email'] != session['user']:
                flash('Access denied', 'danger')
                return redirect(url_for('orders'))
            if order['status'] not in ['pending', 'processing']:
                flash('This order cannot be cancelled', 'warning')
                return redirect(url_for('order_detail', order_id=order_id))
            supabase.table('orders').update({'status': 'cancelled'}).eq('id', order_id).execute()
            flash('Order cancelled successfully!', 'success')
    except Exception as e:
        print(f"Error cancelling order: {e}")
        flash('Failed to cancel order', 'danger')
    return redirect(url_for('orders'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    orders = get_all_orders_from_db()
    products = get_products_from_db()
    users = []
    if supabase:
        try:
            users_response = supabase.table('users').select('*').execute()
            users = users_response.data if users_response.data else []
        except:
            pass
    total_sales = sum(o.get('total_amount', 0) for o in orders)
    total_orders = len(orders)
    total_customers = len(users)
    total_products = len(products)
    low_stock = [p for p in products if p.get('stock', 0) < 10]
    recent_orders = orders[:5]
    chart_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    chart_data = [0, 0, 0, 0, 0, 0, 0]
    return render_template('admin/dashboard.html', 
                         total_sales=total_sales,
                         total_orders=total_orders,
                         total_customers=total_customers,
                         total_products=total_products,
                         low_stock=low_stock,
                         recent_orders=recent_orders,
                         chart_labels=chart_labels,
                         chart_data=chart_data)

@app.route('/admin/products')
def admin_products():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    products = get_products_from_db()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    if request.method == 'POST':
        if not supabase:
            flash('Database not connected', 'danger')
            return redirect(url_for('admin_products'))
        product_data = {
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
        supabase.table('products').insert(product_data).execute()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/add_product.html', categories=CATEGORIES)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    if not supabase:
        flash('Database not connected', 'danger')
        return redirect(url_for('admin_products'))
    if request.method == 'POST':
        update_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price')),
            'compare_price': float(request.form.get('compare_price')) if request.form.get('compare_price') else None,
            'image': request.form.get('image', 'utensil'),
            'category': request.form.get('category'),
            'stock': int(request.form.get('stock', 0)),
            'featured': 'featured' in request.form,
            'bestseller': 'bestseller' in request.form,
        }
        supabase.table('products').update(update_data).eq('id', product_id).execute()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    product = get_product_from_db(product_id)
    return render_template('admin/edit_product.html', product=product, categories=CATEGORIES)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    if supabase:
        supabase.table('products').delete().eq('id', product_id).execute()
    flash('Product deleted', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
def admin_orders():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    orders = get_all_orders_from_db()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
def admin_update_order_status(order_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    data = request.get_json()
    status = data.get('status')
    update_order_status_in_db(order_id, status)
    return jsonify({'success': True})

@app.route('/admin/customers')
def admin_customers():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    users = []
    if supabase:
        try:
            response = supabase.table('users').select('*').execute()
            users = response.data if response.data else []
        except:
            pass
    return render_template('admin/customers.html', customers=users)

@app.route('/admin/coupons')
def admin_coupons():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    coupons = []
    if supabase:
        try:
            response = supabase.table('coupons').select('*').execute()
            coupons = response.data if response.data else []
        except:
            pass
    return render_template('admin/coupons.html', coupons=coupons)

@app.route('/admin/coupons/add', methods=['POST'])
def admin_add_coupon():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    if supabase:
        coupon = {
            'code': request.form.get('code').upper(),
            'description': request.form.get('description'),
            'discount_type': request.form.get('discount_type'),
            'discount_value': float(request.form.get('discount_value')),
            'min_order': float(request.form.get('min_order', 0)),
            'max_discount': float(request.form.get('max_discount')) if request.form.get('max_discount') else None,
            'usage_limit': int(request.form.get('usage_limit')) if request.form.get('usage_limit') else None,
            'expiry_date': request.form.get('expiry_date') or None,
            'active': True
        }
        supabase.table('coupons').insert(coupon).execute()
    flash('Coupon added!', 'success')
    return redirect(url_for('admin_coupons'))

@app.route('/admin/coupons/toggle/<int:coupon_id>', methods=['POST'])
def admin_toggle_coupon(coupon_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    if supabase:
        response = supabase.table('coupons').select('active').eq('id', coupon_id).execute()
        if response.data:
            current = response.data[0].get('active', True)
            supabase.table('coupons').update({'active': not current}).eq('id', coupon_id).execute()
    return jsonify({'success': True})

@app.route('/admin/reviews')
def admin_reviews():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    pending = []
    approved = []
    if supabase:
        try:
            pending_response = supabase.table('reviews').select('*').eq('approved', False).execute()
            approved_response = supabase.table('reviews').select('*').eq('approved', True).execute()
            pending = pending_response.data if pending_response.data else []
            approved = approved_response.data if approved_response.data else []
        except:
            pass
    return render_template('admin/reviews.html', pending_reviews=pending, approved_reviews=approved)

@app.route('/admin/reviews/approve/<int:review_id>', methods=['POST'])
def admin_approve_review(review_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    if supabase:
        supabase.table('reviews').update({'approved': True}).eq('id', review_id).execute()
        # Update product rating
        response = supabase.table('reviews').select('*').eq('id', review_id).execute()
        if response.data:
            review = response.data[0]
            product_id = review.get('product_id')
            reviews_response = supabase.table('reviews').select('rating').eq('product_id', product_id).eq('approved', True).execute()
            if reviews_response.data:
                ratings = [r.get('rating', 0) for r in reviews_response.data]
                avg_rating = sum(ratings) / len(ratings)
                supabase.table('products').update({'rating': avg_rating, 'reviews': len(ratings)}).eq('id', product_id).execute()
    return jsonify({'success': True})

@app.route('/admin/reviews/delete/<int:review_id>', methods=['POST'])
def admin_delete_review(review_id):
    if not session.get('is_admin'):
        return jsonify({'success': False}), 403
    if supabase:
        supabase.table('reviews').delete().eq('id', review_id).execute()
    return jsonify({'success': True})

@app.route('/admin/newsletter')
def admin_newsletter():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    subscribers = []
    if supabase:
        try:
            response = supabase.table('newsletter_subscribers').select('*').execute()
            subscribers = response.data if response.data else []
        except:
            pass
    return render_template('admin/newsletter.html', subscribers=subscribers)

@app.route('/admin/send-newsletter', methods=['POST'])
def send_newsletter_route():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    subject = request.form.get('subject')
    content = request.form.get('message')
    if supabase:
        try:
            response = supabase.table('newsletter_subscribers').select('email').execute()
            if response.data:
                for subscriber in response.data:
                    try:
                        msg = Message(subject, recipients=[subscriber['email']])
                        msg.html = content
                        mail.send(msg)
                    except Exception as e:
                        print(f"Failed to send to {subscriber['email']}: {e}")
        except Exception as e:
            print(f"Newsletter error: {e}")
    flash(f'Newsletter "{subject}" sent to subscribers!', 'success')
    return redirect(url_for('admin_newsletter'))

@app.route('/admin/bulk-import')
def bulk_import():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/bulk_import.html')

@app.route('/admin/export-products')
def admin_export_products():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    products = get_products_from_db()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Category', 'Price', 'Stock', 'Description'])
    for p in products:
        writer.writerow([p.get('id'), p.get('name'), p.get('category'), p.get('price'), p.get('stock'), p.get('description', '')])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='products_export.csv')

@app.route('/admin/export-orders')
def export_orders():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    orders = get_all_orders_from_db()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order #', 'Customer', 'Email', 'Total', 'Status', 'Date'])
    for o in orders:
        writer.writerow([o.get('order_number'), o.get('customer_name'), o.get('customer_email'), o.get('total_amount'), o.get('status'), o.get('created_at', '')[:10]])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='orders_export.csv')

@app.route('/admin/export-customers')
def export_customers():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    users = []
    if supabase:
        try:
            response = supabase.table('users').select('*').execute()
            users = response.data if response.data else []
        except:
            pass
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Email', 'Name', 'Joined'])
    for u in users:
        writer.writerow([u.get('email'), u.get('name', ''), u.get('created_at', '')[:10] if u.get('created_at') else ''])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='customers_export.csv')

@app.route('/admin/remove-subscriber/<email>', methods=['POST'])
def remove_subscriber(email):
    if not session.get('is_admin'):
        return jsonify({'success': False})
    if supabase:
        supabase.table('newsletter_subscribers').delete().eq('email', email).execute()
    return jsonify({'success': True})

@app.route('/admin/products/import', methods=['POST'])
def import_products_csv():
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    file = request.files.get('csv_file')
    if not file:
        flash('No file uploaded', 'danger')
        return redirect(url_for('bulk_import'))
    content = file.stream.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(content))
    imported = 0
    for row in csv_reader:
        product = {
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
        if supabase:
            supabase.table('products').insert(product).execute()
        imported += 1
    flash(f'Imported {imported} products successfully!', 'success')
    return redirect(url_for('admin_products'))

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

@app.route('/api/chat/messages/<session_id>')
def chat_messages(session_id):
    messages = chat_sessions.get(session_id, [])
    return jsonify({'messages': messages})

@app.route('/admin/reports')
def admin_reports():
    if not session.get('is_admin'):
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    sales_by_day = {}
    orders = get_all_orders_from_db()
    for order in orders:
        date = order.get('created_at', '')[:10]
        if date:
            sales_by_day[date] = sales_by_day.get(date, 0) + order.get('total_amount', 0)
    return render_template('admin/reports.html', sales_by_day=sales_by_day)

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'supabase': supabase is not None,
        'products': len(get_products_from_db()),
        'orders': len(get_all_orders_from_db())
    })

@app.route('/debug')
def debug():
    return jsonify({
        "status": "ok",
        "supabase_connected": supabase is not None,
        "env_vars": {
            "MAIL_USERNAME": bool(os.environ.get('MAIL_USERNAME')),
            "MAIL_PASSWORD": bool(os.environ.get('MAIL_PASSWORD')),
            "SECRET_KEY": bool(os.environ.get('SECRET_KEY')),
            "SUPABASE_URL": bool(SUPABASE_URL),
            "SUPABASE_KEY": bool(SUPABASE_KEY)
        }
    })

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
