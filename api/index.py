from flask import Flask, jsonify
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'test-key')

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "Golden Kitchen API is running",
        "environment": {
            "has_mail_username": bool(os.environ.get('MAIL_USERNAME')),
            "has_mail_password": bool(os.environ.get('MAIL_PASSWORD')),
            "has_secret_key": bool(os.environ.get('SECRET_KEY'))
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# Vercel handler
handler = app

if __name__ == '__main__':
    app.run()