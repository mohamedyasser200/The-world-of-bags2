import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# الدالة للحصول على اسم الشبكة اللاسلكية (SSID) على نظام Windows
def get_wifi_name_windows():
    try:
        result = subprocess.check_output(["netsh", "wlan", "show", "interfaces"])
        result = result.decode("utf-8", errors="ignore").split("\n")
        for line in result:
            if "SSID" in line:
                ssid = line.split(":")[1].strip()
                return ssid
    except subprocess.CalledProcessError:
        return None

# الدالة للتحقق من أن الجهاز متصل بالشبكة المحددة
def is_connected_to_allowed_network():
    current_ssid = get_wifi_name_windows()
    
    conn = get_db_connection()
    allowed_networks = conn.execute('SELECT ssid FROM allowed_networks').fetchall()
    conn.close()

    allowed_ssids = [network['ssid'] for network in allowed_networks]
    return current_ssid in allowed_ssids

def add_admin_account():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # التحقق من وجود الحساب مسبقًا
    admin_exists = cursor.execute('SELECT * FROM users WHERE username = ?', ('mohamed',)).fetchone()
    if not admin_exists:
        cursor.execute('''
        INSERT INTO users (username, password, phone, is_admin)
        VALUES (?, ?, ?, ?)
        ''', ('mohamed', 'mohamed2006', '01020887340', True))
        conn.commit()
    
    conn.close()

# إضافة حساب المدير عند بدء تشغيل التطبيق
add_admin_account()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['is_admin'] = user['is_admin']
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('employee_dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        
        if not is_connected_to_allowed_network():
            flash('يجب أن تكون متصلاً بالشبكة المسموح بها للتسجيل.')
            return redirect(url_for('register'))

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('اسم المستخدم موجود بالفعل.')
            return redirect(url_for('register'))

        conn.execute('INSERT INTO users (username, password, phone, is_admin) VALUES (?, ?, ?, ?)',
                     (username, password, phone, False))
        conn.commit()
        conn.close()
        flash('تم التسجيل بنجاح.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM users WHERE is_admin = 0').fetchall()
    attendance = conn.execute('SELECT * FROM attendance WHERE date >= ?', (datetime.now() - timedelta(days=30),)).fetchall()
    allowed_networks = conn.execute('SELECT * FROM allowed_networks').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', employees=employees, attendance=attendance, allowed_networks=allowed_networks)

@app.route('/employee/dashboard')
def employee_dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user_id = session['user_id']
    attendance = conn.execute('SELECT * FROM attendance WHERE user_id = ? AND date >= ?', (user_id, datetime.now() - timedelta(days=30))).fetchall()
    conn.close()
    return render_template('employee_dashboard.html', attendance=attendance)

@app.route('/employee/check_in', methods=['POST'])
def check_in():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    if not is_connected_to_allowed_network():
        flash('يجب أن تكون متصلاً بالشبكة المسموح بها لتسجيل الحضور.')
        return redirect(url_for('employee_dashboard'))

    now = datetime.now()
    if now.hour < 11 or now.hour > 15:
        flash('يسمح بتسجيل الحضور فقط بين الساعة 11 صباحًا و 3 مساءً.')
        return redirect(url_for('employee_dashboard'))

    conn = get_db_connection()
    user_id = session['user_id']
    today = now.date()
    existing_record = conn.execute('SELECT * FROM attendance WHERE user_id = ? AND date = ?', (user_id, today)).fetchone()
    if existing_record:
        flash('لقد قمت بتسجيل الحضور اليوم بالفعل.')
        return redirect(url_for('employee_dashboard'))

    conn.execute('INSERT INTO attendance (user_id, date, time) VALUES (?, ?, ?)', (user_id, today, now.time()))
    conn.commit()
    conn.close()
    flash('تم تسجيل الحضور بنجاح.')
    return redirect(url_for('employee_dashboard'))

@app.route('/admin/discount', methods=['POST'])
def admin_discount():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    employee_id = request.form['employee_id']
    amount = request.form['amount']
    reason = request.form['reason']

    conn = get_db_connection()
    conn.execute('INSERT INTO discounts (employee_id, amount, reason, date) VALUES (?, ?, ?, ?)', (employee_id, amount, reason, datetime.now()))
    conn.commit()
    conn.close()

    flash('تم إصدار الخصم بنجاح.')
    return redirect(url_for('admin_dashboard'))

@app.route('/add_admin', methods=['POST'])
def add_admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    username = request.form['username']
    password = request.form['password']
    phone = request.form['phone']

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password, phone, is_admin) VALUES (?, ?, ?, ?)', (username, password, phone, True))
        conn.commit()
        flash('تم إضافة المدير بنجاح.')
    except sqlite3.IntegrityError:
        flash('اسم المستخدم موجود بالفعل.')
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_network', methods=['POST'])
def add_network():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    ssid = request.form['ssid']

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO allowed_networks (ssid) VALUES (?)', (ssid,))
        conn.commit()
        flash('تم إضافة الشبكة بنجاح.')
    except sqlite3.IntegrityError:
        flash('اسم الشبكة موجود بالفعل.')
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)