import sqlite3

DATABASE = 'database.db'

def create_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # إنشاء جدول المستخدمين إذا لم يكن موجودًا
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        phone TEXT NOT NULL,
        is_admin BOOLEAN NOT NULL DEFAULT 0
    )
    ''')
    
    # إنشاء جدول الحضور إذا لم يكن موجودًا
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date DATE NOT NULL,
        time TIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # إنشاء جدول الخصومات إذا لم يكن موجودًا
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS discounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        reason TEXT,
        date DATE NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES users (id)
    )
    ''')

    # إنشاء جدول الشبكات المسموح بها إذا لم يكن موجودًا
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS allowed_networks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ssid TEXT NOT NULL UNIQUE
    )
    ''')
    
    # إدراج حساب المدير إذا لم يكن موجودًا
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password, phone, is_admin)
    VALUES (?, ?, ?, ?)
    ''', ('mohamed', 'mohamed2006', '01020887340', True))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
    print("Database created successfully.")