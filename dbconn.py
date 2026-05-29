from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# =========================================================
# DATABASE CONNECTION CONFIGURATION (Dynamic setup)
# =========================================================
raw_uri = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/finalrankup')

if raw_uri.startswith('mysql://'):
    raw_uri = raw_uri.replace('mysql://', 'mysql+pymysql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = raw_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        "ssl": {"ssl_mode": "REQUIRED"}
    }
}

app.secret_key = 'rankup_secret_key_ni_boss' 
db = SQLAlchemy(app)

try:
    with app.app_context():
        db.session.execute(db.text("SELECT 1"))
    print("🚀 Database Connection Successful! Swabe ang koneksyon, boss.")
except Exception as e:
    print(f"❌ Connection Failed: {e}")