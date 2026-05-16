from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-123'
basedir = os.path.abspath(os.path.dirname(__file__))
# Using a brand-new database name to ensure a clean slate
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'todo_final_v3.sqlite')

db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Todo', backref='owner', lazy=True)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_content = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- LOGIN MANAGER ---
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---
@app.route('/tasks')
@login_required
def index():
    user_tasks = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', tasks=user_tasks)

@app.route('/', methods=['GET', 'POST'])
def login():
    
        
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')
import re # Ensure this is at the top of your file

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # --- Professional Password Rules ---
        if len(password) < 8:
            flash('Password must be at least 8 characters.')
            return redirect(url_for('register'))
        
        if not re.search("[A-Z]", password):
            flash('Add at least one uppercase letter (A-Z).')
            return redirect(url_for('register'))

        if not re.search("[0-9]", password):
            flash('Add at least one number (0-9).')
            return redirect(url_for('register'))

        # This new line checks for special characters
        if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
            flash('Add at least one special character (e.g., @, #, $, !).')
            return redirect(url_for('register'))

        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('That username is already taken.')
            return redirect(url_for('register'))

        # Hash and Save
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')
@app.route('/add', methods=['POST'])
@login_required
def add():
    content = request.form.get('content')
    if content:
        new_task = Todo(task_content=content, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Todo.query.get_or_404(task_id)
    if task.user_id == current_user.id:
        task.is_completed = not task.is_completed
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print(f"Database created at: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.run(debug=True)