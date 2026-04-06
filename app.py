from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from models import db, User, AccountRequest
from forms import LoginForm, JoinForm

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ====================== EMAIL ======================
def send_password_email(to_email, password, role):
    msg = MIMEMultipart()
    msg['From'] = app.config.get('SMTP_EMAIL', 'noreply@guardia.cs')
    msg['To'] = to_email
    msg['Subject'] = "Votre compte Guardia EDU"

    body = f"""Bonjour,\n\nVotre compte {role} a été créé.\nEmail : {to_email}\nMot de passe : {password}\n\nConnectez-vous : http://127.0.0.1:5000/login"""
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(app.config.get('SMTP_SERVER'), app.config.get('SMTP_PORT', 587))
        server.starttls()
        server.login(app.config.get('SMTP_EMAIL'), app.config.get('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Email error:", e)
        return False

# ====================== ROUTES ======================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Connexion réussie', 'success')
            return redirect(url_for('dashboard'))
        flash('Identifiants incorrects', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnexion réussie', 'info')
    return redirect(url_for('login'))

@app.route('/join', methods=['GET', 'POST'])
def join():
    form = JoinForm()
    if form.validate_on_submit():
        role = form.role.data
        email = form.email.data.strip().lower()

        if (role == 'student' and not email.endswith('@etu.guardia.cs')) or \
           (role == 'professor' and not email.endswith('@guardia.cs')):
            flash("L'email doit correspondre au type de compte", "danger")
            return redirect(url_for('join'))

        if User.query.filter_by(email=email).first() or AccountRequest.query.filter_by(email=email, status='pending').first():
            flash("Un compte ou une demande existe déjà", "danger")
            return redirect(url_for('join'))

        req = AccountRequest(email=email, role=role)
        db.session.add(req)
        db.session.commit()

        flash("Demande envoyée à l'administrateur. Vous recevrez un email avec votre mot de passe.", "success")
        return redirect(url_for('login'))
    return render_template('join.html', form=form)

@app.route('/admin/approve_request/<int:req_id>', methods=['POST'])
@login_required
def approve_request(req_id):
    if current_user.role != 'admin':
        abort(403)
    req = AccountRequest.query.get_or_404(req_id)
    if req.status != 'pending':
        flash("Déjà traité", "warning")
        return redirect(url_for('admin_dashboard'))

    password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(14))
    user = User(username=req.email.split('@')[0], email=req.email, role=req.role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    req.status = 'approved'
    db.session.commit()

    sent = send_password_email(req.email, password, req.role)
    flash(f"Compte créé pour {req.email}" + (" (email envoyé)" if sent else " (email non envoyé)"), "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    stats = {
        "total_users": User.query.count(),
        "students": User.query.filter_by(role='student').count(),
        "professors": User.query.filter_by(role='professor').count(),
    }
    pending_requests = AccountRequest.query.filter_by(status='pending').order_by(AccountRequest.requested_at.desc()).all()
    return render_template('dashboard_admin.html', stats=stats, pending_requests=pending_requests)

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    if current_user.role == 'professor':
        return redirect(url_for('professor_dashboard'))
    return redirect(url_for('student_dashboard'))

# Placeholder dashboards (tu peux les remplir plus tard)
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    return render_template('dashboard_student.html')

@app.route('/professor/dashboard')
@login_required
def professor_dashboard():
    return render_template('dashboard_professor.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)