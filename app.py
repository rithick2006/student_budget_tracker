import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- App setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///budget.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Extensions ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Login loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        if not username or not email or not password:
            flash('Please fill all fields', 'warning')
            return redirect(url_for('register'))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    recent = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(8).all()
    total = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0.0
    category_data = db.session.query(Expense.category, db.func.sum(Expense.amount))\
        .filter_by(user_id=current_user.id).group_by(Expense.category).all()
    categories = [c for c, _ in category_data]
    sums = [float(s) for _, s in category_data]
    return render_template('dashboard.html', recent=recent, total=total, categories=categories, sums=sums)

# Add expense
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        date_str = request.form['date']
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            flash('Invalid date format', 'danger')
            return redirect(url_for('add_expense'))
        category = request.form['category']
        try:
            amount = float(request.form['amount'])
        except ValueError:
            flash('Invalid amount', 'danger')
            return redirect(url_for('add_expense'))
        note = request.form.get('note', '')
        e = Expense(user_id=current_user.id, date=date_obj, category=category, amount=amount, note=note)
        db.session.add(e)
        db.session.commit()
        flash('Expense added', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_expense.html')

# Edit expense
@app.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    e = Expense.query.get_or_404(expense_id)
    if e.user_id != current_user.id:
        flash('Not authorised', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        try:
            e.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        except Exception:
            flash('Invalid date', 'danger')
            return redirect(url_for('edit_expense', expense_id=expense_id))
        e.category = request.form['category']
        try:
            e.amount = float(request.form['amount'])
        except ValueError:
            flash('Invalid amount', 'danger')
            return redirect(url_for('edit_expense', expense_id=expense_id))
        e.note = request.form.get('note', '')
        db.session.commit()
        flash('Expense updated', 'success')
        return redirect(url_for('expenses'))
    return render_template('edit_expense.html', e=e)

# Delete expense
@app.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    e = Expense.query.get_or_404(expense_id)
    if e.user_id != current_user.id:
        flash('Not authorised', 'danger')
        return redirect(url_for('expenses'))
    db.session.delete(e)
    db.session.commit()
    flash('Expense deleted', 'info')
    return redirect(url_for('expenses'))

# List all expenses
@app.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    q = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('expenses.html', pagination=pagination)

# Export CSV
@app.route('/export')
@login_required
def export_expenses():
    import csv
    import io
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'date', 'category', 'amount', 'note'])
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    for ex in expenses:
        cw.writerow([ex.id, ex.date.isoformat(), ex.category, f"{ex.amount:.2f}", ex.note])
    output = make_response(si.getvalue())
    output.headers['Content-Disposition'] = 'attachment; filename=expenses.csv'
    output.headers['Content-Type'] = 'text/csv'
    return output

# API for charts
@app.route('/api/category-summary')
@login_required
def category_summary():
    results = db.session.query(Expense.category, db.func.sum(Expense.amount))\
        .filter_by(user_id=current_user.id).group_by(Expense.category).all()
    data = {r[0]: float(r[1]) for r in results}
    return jsonify(data)

# --- Run ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


