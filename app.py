from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, redirect, url_for, flash
from flask import session, g
from flask_login import login_user , UserMixin, LoginManager, login_required
from flask import current_app
from flask import send_from_directory
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite pour la simplicité
app.config['SECRET_KEY'] = '5f89fa56ea3bf3e8385e14b600c4e4a7f557c4418c707eecbd423a3d8921dcf0'

UPLOAD_FOLDER = 'uploads'  # Dossier où vous stockerez vos fichiers PDF
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
login_manager = LoginManager(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'




class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Nom d\'utilisateur déjà pris. Veuillez en choisir un autre.', 'danger')
            return redirect(url_for('register'))

        # Créer un nouvel utilisateur
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Inscription réussie! Connectez-vous avec votre nouveau compte.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Connexion réussie!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Identifiants incorrects. Veuillez réessayer.', 'danger')

    return render_template('login.html')


@app.route('/download/<classe>/<filename>')
@login_required
def download_file(classe, filename):
    class_folder = os.path.join(app.config['UPLOAD_FOLDER'], classe)
    return send_from_directory(class_folder, filename)


@app.route('/')
@login_required
def home():
    pdf_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.pdf')]
    return render_template('home.html', pdf_files=pdf_files)

@app.route('/class/<classe>')
@login_required
def class_files(classe):
    class_folder = os.path.join(app.config['UPLOAD_FOLDER'], classe)
    pdf_files = [f for f in os.listdir(class_folder) if f.endswith('.pdf')]
    return render_template('class_files.html', classe=classe, pdf_files=pdf_files)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)