from flask import Flask, jsonify, request, send_file, session
from flask_cors import CORS
import pandas as pd
import pickle
import numpy as np
import os
from datetime import datetime, timedelta
import io
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Import database functions
from database import get_db_connection, init_database, seed_demo_users, import_csv_to_sqlite

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
app.secret_key = 'zakat-tech-secret-key-2024'  # Change in production!
CORS(app, supports_credentials=True)

# Constants
NISAB_THRESHOLD = 22000  # RM - approximately 85 grams of gold

# Load Model
MODEL_PATH = 'zakat_model.pkl'

model = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
else:
    print("Warning: Model file not found.")

# Initialize database on startup
init_database()
seed_demo_users()
import_csv_to_sqlite()

# ============== AUTH DECORATORS ==============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Login required"}), 401
        if session.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============== STATIC ROUTES ==============

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/user')
def user_dashboard():
    return app.send_static_file('user-dashboard.html')

@app.route('/admin')
def admin_dashboard():
    return app.send_static_file('admin-dashboard.html')

# ============== AUTH API ROUTES ==============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('fullName', '').strip()
        
        if not email or not password or not full_name:
            return jsonify({"error": "All fields are required"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Email already registered"}), 400
        
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, 'user')
        ''', (email, password_hash, full_name))
        
        user_id = cursor.lastrowid
        
        # Create empty profile
        cursor.execute('''
            INSERT INTO user_profiles (user_id, age, income, savings)
            VALUES (?, 30, 0, 0)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "message": "Registration successful! Please login.",
            "status": "success"
        })
    except Exception as e: # <--- CATCH THE ERROR HERE
        print(f"❌ REGISTER ERROR: {e}") # This prints to your VS Code Terminal
        return jsonify({"error": str(e)}), 500 # Returns the specific error to the frontend

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user."""
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if not user or not check_password_hash(user['password_hash'], password):
        conn.close()
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Update last login
    cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                   (datetime.now(), user['id']))
    conn.commit()
    conn.close()
    
    # Set session
    session['user_id'] = user['id']
    session['email'] = user['email']
    session['full_name'] = user['full_name']
    session['role'] = user['role']
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "fullName": user['full_name'],
            "role": user['role']
        },
        "status": "success"
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user."""
    session.clear()
    return jsonify({"message": "Logged out", "status": "success"})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current logged in user."""
    if 'user_id' not in session:
        return jsonify({"logged_in": False})
    
    return jsonify({
        "logged_in": True,
        "user": {
            "id": session['user_id'],
            "email": session['email'],
            "fullName": session['full_name'],
            "role": session['role']
        }
    })

# ============== USER PROFILE API ==============

@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user's financial profile."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM user_profiles WHERE user_id = ?
    ''', (session['user_id'],))
    profile = cursor.fetchone()
    conn.close()
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    return jsonify({
        "profile": dict(profile),
        "status": "success"
    })

@app.route('/api/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user's financial profile."""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE user_profiles SET
            age = ?,
            income = ?,
            savings = ?,
            gold_value = ?,
            investment_value = ?,
            family_size = ?,
            employment_status = ?,
            contribution_score = ?,
            haul_start_date = ?,
            updated_at = ?
        WHERE user_id = ?
    ''', (
        data.get('age', 30),
        data.get('income', 0),
        data.get('savings', 0),
        data.get('goldValue', 0),
        data.get('investmentValue', 0),
        data.get('familySize', 1),
        data.get('employmentStatus', 1),
        data.get('contributionScore', 50),
        data.get('haulStartDate'),
        datetime.now(),
        session['user_id']
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Profile updated", "status": "success"})

# ============== CONTRIBUTION HISTORY ==============

@app.route('/api/user/contributions', methods=['GET'])
@login_required
def get_contributions():
    """Get user's contribution history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM contributions 
        WHERE user_id = ? 
        ORDER BY year DESC
    ''', (session['user_id'],))
    contributions = cursor.fetchall()
    conn.close()
    
    history = [dict(c) for c in contributions]
    total = sum(c['amount'] for c in history)
    
    return jsonify({
        "history": history,
        "total_contributed": total,
        "years_active": len(set(c['year'] for c in history)),
        "status": "success"
    })

@app.route('/api/user/contributions', methods=['POST'])
@login_required
def add_contribution():
    """Add a new contribution record."""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO contributions (user_id, amount, payment_date, year, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        data.get('amount', 0),
        data.get('paymentDate', datetime.now().strftime('%Y-%m-%d')),
        data.get('year', datetime.now().year),
        data.get('notes', '')
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Contribution recorded", "status": "success"})

# ============== COMMON API ROUTES ==============

@app.route('/api/nisab', methods=['GET'])
def get_nisab():
    """Returns current Nisab threshold."""
    return jsonify({
        "nisab_threshold": NISAB_THRESHOLD,
        "currency": "MYR",
        "description": "Approximately 85 grams of gold at current market rate"
    })

@app.route('/api/user/nisab-check', methods=['POST'])
def check_nisab():
    """Check if user's wealth meets Nisab threshold."""
    data = request.json
    try:
        total_wealth = (
            data.get('savings', 0) + 
            data.get('goldValue', 0) + 
            data.get('investmentValue', 0)
        )
        
        is_eligible = total_wealth >= NISAB_THRESHOLD
        
        return jsonify({
            "total_wealth": total_wealth,
            "nisab_threshold": NISAB_THRESHOLD,
            "is_eligible": is_eligible,
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/user/predict', methods=['POST'])
def predict_zakat_user():
    """Predicts Zakat amount based on user financial profile."""
    if not model:
        return jsonify({"error": "Model not loaded"}), 500
        
    data = request.json
    try:
        savings = data.get('savings', 0)
        gold_value = data.get('goldValue', 0)
        investment = data.get('investmentValue', 0)
        total_wealth = savings + gold_value + investment
        
        if total_wealth < NISAB_THRESHOLD:
            return jsonify({
                "predicted_zakat": 0,
                "is_eligible": False,
                "message": "Total wealth is below Nisab threshold.",
                "status": "success"
            })
        
        features = [
            data.get('age', 30),
            data.get('income', 0),
            savings,
            gold_value,
            investment,
            data.get('familySize', 1),
            data.get('employmentStatus', 1),
            data.get('previousContributionScore', 50)
        ]
        
        features_array = np.array(features).reshape(1, -1)
        prediction = model.predict(features_array)[0]
        standard_zakat = total_wealth * 0.025
        
        return jsonify({
            "predicted_zakat": max(0, round(prediction, 2)),
            "standard_zakat": round(standard_zakat, 2),
            "total_wealth": total_wealth,
            "is_eligible": True,
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/user/haul-status', methods=['POST'])
def get_haul_status():
    """Calculate Haul status for Zakat due date."""
    data = request.json
    try:
        haul_start_str = data.get('haulStartDate')
        
        if not haul_start_str:
            return jsonify({
                "has_haul": False,
                "message": "Haul start date not set."
            })
        
        haul_start = datetime.strptime(haul_start_str, "%Y-%m-%d")
        today = datetime.now()
        lunar_year_days = 354
        days_since_haul = (today - haul_start).days
        
        if days_since_haul >= lunar_year_days:
            return jsonify({
                "has_haul": True,
                "is_due": True,
                "days_completed": days_since_haul,
                "message": "Zakat is due!",
                "status": "success"
            })
        else:
            days_remaining = lunar_year_days - days_since_haul
            due_date = haul_start + timedelta(days=lunar_year_days)
            return jsonify({
                "has_haul": True,
                "is_due": False,
                "days_completed": days_since_haul,
                "days_remaining": days_remaining,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "progress_percent": round((days_since_haul / lunar_year_days) * 100, 1),
                "status": "success"
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/user/history/<donor_id>', methods=['GET'])
def get_user_history(donor_id):
    """Get contribution history for demo."""
    return jsonify({
        "donor_id": donor_id,
        "history": [
            {"year": 2021, "amount": 1200, "date": "2021-06-15"},
            {"year": 2022, "amount": 1450, "date": "2022-06-20"},
            {"year": 2023, "amount": 1680, "date": "2023-06-18"},
            {"year": 2024, "amount": 1820, "date": "2024-06-22"}
        ],
        "total_contributed": 6150,
        "status": "success"
    })

# ============== ADMIN API ROUTES ==============

@app.route('/api/admin/forecast', methods=['GET'])
@admin_required
def get_forecast():
    """Get collection forecast."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM donors')
    donors = cursor.fetchall()
    conn.close()
    
    total_predicted = sum(d['zakat_amount'] for d in donors)
    eligible_donors = len([d for d in donors if d['zakat_amount'] > 0])
    
    return jsonify({
        "total_annual_forecast": round(total_predicted, 2),
        "monthly_forecast": round(total_predicted / 12, 2),
        "quarterly_forecast": round(total_predicted / 4, 2),
        "average_per_donor": round(total_predicted / len(donors) if donors else 0, 2),
        "eligible_donors": eligible_donors,
        "total_donors": len(donors),
        "status": "success"
    })

@app.route('/api/admin/segments', methods=['GET'])
@admin_required
def get_segments():
    """Get donor segmentation data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM donors')
    donors = cursor.fetchall()
    conn.close()
    
    tier_counts = {}
    segments = {}
    
    for d in donors:
        tier = d['donor_tier']
        if tier not in tier_counts:
            tier_counts[tier] = 0
            segments[tier] = {'count': 0, 'total_zakat': 0, 'total_wealth': 0}
        tier_counts[tier] += 1
        segments[tier]['count'] += 1
        segments[tier]['total_zakat'] += d['zakat_amount']
        segments[tier]['total_wealth'] += d['total_wealth']
    
    segment_list = []
    for tier, data in segments.items():
        segment_list.append({
            "tier": tier,
            "count": data['count'],
            "total_zakat": round(data['total_zakat'], 2),
            "avg_zakat": round(data['total_zakat'] / data['count'], 2) if data['count'] > 0 else 0,
            "avg_wealth": round(data['total_wealth'] / data['count'], 2) if data['count'] > 0 else 0
        })
    
    return jsonify({
        "tier_counts": tier_counts,
        "segments": segment_list,
        "status": "success"
    })

@app.route('/api/admin/trends', methods=['GET'])
@admin_required
def get_trends():
    """Get wealth trend analysis data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT income, total_wealth, zakat_amount, donor_tier, employment_status FROM donors')
    donors = cursor.fetchall()
    conn.close()
    
    income_vs_zakat = [{'Income': d['income'], 'ZakatAmount': d['zakat_amount'], 'DonorTier': d['donor_tier']} for d in donors]
    wealth_vs_zakat = [{'TotalWealth': d['total_wealth'], 'ZakatAmount': d['zakat_amount'], 'DonorTier': d['donor_tier']} for d in donors]
    
    return jsonify({
        "income_vs_zakat": income_vs_zakat,
        "wealth_vs_zakat": wealth_vs_zakat,
        "status": "success"
    })

@app.route('/api/admin/at-risk', methods=['GET'])
@admin_required
def get_at_risk():
    """Get list of at-risk donors."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT * FROM donors 
        WHERE total_wealth >= ? AND last_payment_date < ?
        ORDER BY total_wealth DESC
    ''', (NISAB_THRESHOLD, cutoff_date))
    
    at_risk = cursor.fetchall()
    conn.close()
    
    at_risk_list = []
    potential = 0
    for d in at_risk:
        days_since = (datetime.now() - datetime.strptime(d['last_payment_date'], '%Y-%m-%d')).days
        at_risk_list.append({
            'DonorID': d['donor_id'],
            'TotalWealth': d['total_wealth'],
            'Income': d['income'],
            'DonorTier': d['donor_tier'],
            'LastPaymentDate': d['last_payment_date'],
            'days_since_payment': days_since
        })
        potential += d['zakat_amount']
    
    return jsonify({
        "at_risk_count": len(at_risk_list),
        "at_risk_donors": at_risk_list,
        "potential_collection": round(potential, 2),
        "status": "success"
    })

@app.route('/api/admin/export', methods=['GET'])
@admin_required
def export_data():
    """Export donor data as CSV."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM donors')
    donors = cursor.fetchall()
    conn.close()
    
    df = pd.DataFrame([dict(d) for d in donors])
    
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'zakat_data_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/api/data', methods=['GET'])
def get_data():
    """Returns aggregated data for visualization."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM donors')
    donors = cursor.fetchall()
    conn.close()
    
    if not donors:
        return jsonify({"error": "No data found"}), 404
    
    # Aggregate data
    emp_totals = {}
    emp_counts = {}
    for d in donors:
        emp = d['employment_status']
        if emp not in emp_totals:
            emp_totals[emp] = 0
            emp_counts[emp] = 0
        emp_totals[emp] += d['zakat_amount']
        emp_counts[emp] += 1
    
    avg_by_employment = {k: emp_totals[k] / emp_counts[k] for k in emp_totals}
    
    import random
    sample = random.sample(list(donors), min(50, len(donors)))
    scatter_data = [{'Income': d['income'], 'ZakatAmount': d['zakat_amount']} for d in sample]
    
    return jsonify({
        "avg_zakat_by_employment": avg_by_employment,
        "income_vs_zakat": scatter_data,
        "total_donors": len(donors),
        "total_zakat_pool": sum(d['zakat_amount'] for d in donors),
        "nisab_threshold": NISAB_THRESHOLD
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
