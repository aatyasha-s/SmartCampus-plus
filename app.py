from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "smartcampus_secret"

# ---------- DATABASE ----------

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'student'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS vendors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        status TEXT DEFAULT 'Open'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS menu(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_name TEXT,
        item_name TEXT,
        price INTEGER,
        icon TEXT DEFAULT 'fa-bowl-food'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS cart(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        vendor_name TEXT,
        item TEXT,
        price INTEGER,
        quantity INTEGER
    )""")

    # NEW: Orders table for the kitchen
    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        vendor_name TEXT,
        item TEXT,
        quantity INTEGER,
        status TEXT DEFAULT 'Preparing'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS rooms(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT,
        status TEXT DEFAULT 'Available'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS seats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seat_no TEXT,
        status TEXT DEFAULT 'Available'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        date TEXT
    )""")

    # Seed Users (Admin, Student, Vendors)
    c.execute("INSERT OR IGNORE INTO users(username, password, role) VALUES('student', '1234', 'student')")
    c.execute("INSERT OR IGNORE INTO users(username, password, role) VALUES('admin', 'admin123', 'admin')")
    c.execute("INSERT OR IGNORE INTO users(username, password, role) VALUES('snapeats', 'vendor123', 'vendor')")
    c.execute("INSERT OR IGNORE INTO users(username, password, role) VALUES('infinity', 'vendor123', 'vendor')")
    c.execute("INSERT OR IGNORE INTO users(username, password, role) VALUES('chow', 'vendor123', 'vendor')")
    
    # Seed Vendors
    vendors_list = ["Snap Eats", "Infinity Kitchen", "House of Chow"]
    for v_name in vendors_list:
        c.execute("INSERT OR IGNORE INTO vendors (name) VALUES (?)", (v_name,))

    # Seed Menu
    c.execute("SELECT COUNT(*) FROM menu")
    if c.fetchone()[0] == 0:
        default_menu = [
            ("Snap Eats", "Burger", 70, "fa-burger"),
            ("Snap Eats", "Cold Coffee", 60, "fa-mug-hot"),
            ("Infinity Kitchen", "Veg Sandwich", 50, "fa-bread-slice"),
            ("House of Chow", "Maggi", 40, "fa-bowl-food")
        ]
        for m in default_menu:
            c.execute("INSERT INTO menu (vendor_name, item_name, price, icon) VALUES (?, ?, ?, ?)", m)

    # Seed Rooms & Seats
    c.execute("SELECT COUNT(*) FROM rooms")
    if c.fetchone()[0] == 0:
        for i in range(1, 4):
            c.execute("INSERT INTO rooms (room_name) VALUES (?)", (f"GD Room {i}",))
            c.execute("INSERT INTO seats (seat_no) VALUES (?)", (f"Seat {i}",))

    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT username, role FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        session["user"] = user[0]
        session["role"] = user[1]
        
        if user[1] == "admin":
            return redirect("/admin")
        elif user[1] == "vendor":
            return redirect("/vendor") # This points to the Vendor Route below!
        return redirect("/dashboard")
        
    return render_template("login.html", error="Invalid Credentials")

@app.route("/dashboard")
def dashboard():
    if "user" not in session or session.get("role") != "student":
        return redirect("/")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM vendors WHERE status='Open'")
    vendors = c.fetchall()
    conn.close()
    
    return render_template("dashboard.html", user=session["user"], vendors=vendors)

# ---------- ADMIN ROUTES ----------

@app.route("/admin")
def admin_panel():
    if "user" not in session or session.get("role") != "admin":
        return redirect("/")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM vendors")
    vendors = c.fetchall()
    c.execute("SELECT * FROM users WHERE role='student'")
    students = c.fetchall()
    conn.close()
    
    return render_template("admin.html", vendors=vendors, students=students)

@app.route("/admin/add_vendor", methods=["POST"])
def add_vendor():
    if session.get("role") == "admin":
        name = request.form["vendor_name"]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO vendors (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
    return redirect("/admin")

@app.route("/admin/delete_vendor/<int:id>", methods=["POST"])
def delete_vendor(id):
    if session.get("role") == "admin":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT name FROM vendors WHERE id=?", (id,))
        vendor = c.fetchone()
        if vendor:
            c.execute("DELETE FROM menu WHERE vendor_name=?", (vendor[0],))
            c.execute("DELETE FROM vendors WHERE id=?", (id,))
        conn.commit()
        conn.close()
    return redirect("/admin")

@app.route("/admin/toggle_vendor/<int:id>", methods=["POST"])
def toggle_vendor(id):
    if session.get("role") == "admin":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE vendors SET status = CASE WHEN status='Open' THEN 'Closed' ELSE 'Open' END WHERE id=?", (id,))
        conn.commit()
        conn.close()
    return redirect("/admin")

@app.route("/admin/add_food", methods=["POST"])
def add_food():
    if session.get("role") == "admin":
        vendor_name = request.form["vendor_name"]
        item_name = request.form["item_name"]
        price = request.form["price"]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO menu (vendor_name, item_name, price) VALUES (?, ?, ?)", (vendor_name, item_name, price))
        conn.commit()
        conn.close()
    return redirect("/admin")

# ---------- VENDOR ROUTES (Fixes the 404 Error!) ----------

@app.route("/vendor")
def vendor_panel():
    if "user" not in session or session.get("role") != "vendor":
        return redirect("/")
    
    username_to_vendor = {
        "snapeats": "Snap Eats",
        "infinity": "Infinity Kitchen",
        "chow": "House of Chow"
    }
    vendor_name = username_to_vendor.get(session["user"], "Unknown")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, student_name, item, quantity, status FROM orders WHERE vendor_name=? AND status != 'Completed' ORDER BY id ASC", (vendor_name,))
    orders = c.fetchall()
    conn.close()
    
    return render_template("vendor.html", vendor_name=vendor_name, orders=orders)

@app.route("/vendor/update_order/<int:order_id>", methods=["POST"])
def update_order(order_id):
    if session.get("role") == "vendor":
        action = request.form.get("action")
        new_status = "Ready to Pickup" if action == "ready" else "Completed"
        
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
        conn.commit()
        conn.close()
    return redirect("/vendor")

# ---------- CART & ORDER APIs ----------

@app.route("/get_menu/<vendor_name>")
def get_menu(vendor_name):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT item_name, price, icon FROM menu WHERE vendor_name=?", (vendor_name,))
    menu = c.fetchall()
    conn.close()
    return jsonify([{"name": m[0], "price": m[1], "icon": m[2]} for m in menu])

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    data = request.json
    user = session["user"]
    item = data["item"]
    price = data["price"]
    vendor = data.get("vendor_name", "Unknown")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT quantity FROM cart WHERE username=? AND item=? AND vendor_name=?", (user, item, vendor))
    existing = c.fetchone()

    if existing:
        c.execute("UPDATE cart SET quantity=quantity+1 WHERE username=? AND item=? AND vendor_name=?", (user, item, vendor))
    else:
        c.execute("INSERT INTO cart(username, vendor_name, item, price, quantity) VALUES(?, ?, ?, ?, ?)", (user, vendor, item, price, 1))
    
    conn.commit()
    conn.close()
    return jsonify({"status": "added"})

@app.route("/get_cart")
def get_cart():
    user = session["user"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT item, price, quantity, vendor_name FROM cart WHERE username=?", (user,))
    items = c.fetchall()
    conn.close()
    return jsonify(items)

@app.route("/checkout", methods=["POST"])
def checkout():
    user = session["user"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    # 1. Get cart items
    c.execute("SELECT vendor_name, item, quantity FROM cart WHERE username=?", (user,))
    cart_items = c.fetchall()
    
    # 2. Move to vendor orders
    for item in cart_items:
        c.execute("INSERT INTO orders (student_name, vendor_name, item, quantity) VALUES (?, ?, ?, ?)", 
                  (user, item[0], item[1], item[2]))
        
    # 3. Clear cart
    c.execute("DELETE FROM cart WHERE username=?", (user,))
    
    conn.commit()
    conn.close()
    return jsonify({"status": "order_placed"})

@app.route("/update_quantity", methods=["POST"])
def update_quantity():
    data = request.json
    item = data["item"]
    action = data["action"]
    user = session["user"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if action == "increase":
        c.execute("UPDATE cart SET quantity=quantity+1 WHERE username=? AND item=?", (user, item))
    elif action == "decrease":
        c.execute("UPDATE cart SET quantity=quantity-1 WHERE username=? AND item=?", (user, item))
        c.execute("DELETE FROM cart WHERE username=? AND item=? AND quantity<=0", (user, item))

    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})

@app.route("/remove_item", methods=["POST"])
def remove_item():
    data = request.json
    item = data["item"]
    user = session["user"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM cart WHERE username=? AND item=?", (user, item))
    conn.commit()
    conn.close()
    return jsonify({"status": "removed"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)