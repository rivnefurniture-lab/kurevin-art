"""
Impressionism by Alexey Kurevin - Artist Portfolio & Gallery
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kurevin-art-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kurevin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/paintings'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max

# Contact settings
app.config['CONTACT_EMAIL'] = 'kurevin.art@gmail.com'
app.config['CONTACT_PHONE'] = '+380501234567'
app.config['CONTACT_TELEGRAM'] = 'kurevin_art'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============== MODELS ==============

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Painting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Titles in 3 languages
    title_uk = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    title_ru = db.Column(db.String(200), nullable=False)
    # Descriptions
    description_uk = db.Column(db.Text)
    description_en = db.Column(db.Text)
    description_ru = db.Column(db.Text)
    # Technical details
    width = db.Column(db.Integer)  # in cm
    height = db.Column(db.Integer)  # in cm
    year = db.Column(db.Integer)
    technique_uk = db.Column(db.String(100))  # e.g., "Олія на полотні"
    technique_en = db.Column(db.String(100))  # e.g., "Oil on canvas"
    technique_ru = db.Column(db.String(100))  # e.g., "Масло на холсте"
    # Pricing & availability
    price = db.Column(db.Float)  # in USD
    is_sold = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    # Image
    image = db.Column(db.String(255))
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.Column(db.Integer, default=0)
    
    def get_title(self, lang):
        return getattr(self, f'title_{lang}', self.title_en)
    
    def get_description(self, lang):
        return getattr(self, f'description_{lang}', self.description_en)
    
    def get_technique(self, lang):
        return getattr(self, f'technique_{lang}', self.technique_en)
    
    def get_size_display(self):
        if self.width and self.height:
            return f"{self.width} × {self.height} cm"
        return None

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    painting_id = db.Column(db.Integer, db.ForeignKey('painting.id'))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    painting = db.relationship('Painting', backref='inquiries')

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value_uk = db.Column(db.Text)
    value_en = db.Column(db.Text)
    value_ru = db.Column(db.Text)

# ============== HELPERS ==============

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

def get_lang():
    lang = session.get('lang', 'uk')
    if lang not in ['uk', 'en', 'ru']:
        lang = 'uk'
    return lang

def get_translations():
    """Return translations dictionary for current language"""
    lang = get_lang()
    translations = {
        'uk': {
            'site_title': 'Імпресіонізм Олексія Куревіна',
            'nav_home': 'Головна',
            'nav_gallery': 'Галерея',
            'nav_about': 'Про художника',
            'nav_contact': 'Контакти',
            'hero_subtitle': 'Світло, колір та емоції на полотні',
            'view_gallery': 'Переглянути роботи',
            'contact_artist': 'Зв\'язатися з художником',
            'featured_works': 'Вибрані роботи',
            'all_works': 'Усі роботи',
            'about_title': 'Про художника',
            'contact_title': 'Зв\'язатися',
            'contact_subtitle': 'Якщо вас зацікавила робота або ви бажаєте замовити картину',
            'your_name': 'Ваше ім\'я',
            'your_email': 'Ваш email',
            'your_phone': 'Телефон',
            'your_message': 'Повідомлення',
            'send': 'Надіслати',
            'price': 'Ціна',
            'size': 'Розмір',
            'year': 'Рік',
            'technique': 'Техніка',
            'oil_on_canvas': 'Олія на полотні',
            'available': 'Доступна',
            'sold': 'Продано',
            'inquire': 'Запитати про цю роботу',
            'back_to_gallery': 'Повернутися до галереї',
            'interested_in': 'Мене цікавить робота',
            'message_sent': 'Дякуємо! Ваше повідомлення надіслано.',
            'all_paintings': 'Усі картини',
            'filter_available': 'Доступні',
            'filter_sold': 'Продані',
        },
        'en': {
            'site_title': 'Impressionism by Alexey Kurevin',
            'nav_home': 'Home',
            'nav_gallery': 'Gallery',
            'nav_about': 'About',
            'nav_contact': 'Contact',
            'hero_subtitle': 'Light, color and emotion on canvas',
            'view_gallery': 'View Gallery',
            'contact_artist': 'Contact the Artist',
            'featured_works': 'Featured Works',
            'all_works': 'All Works',
            'about_title': 'About the Artist',
            'contact_title': 'Get in Touch',
            'contact_subtitle': 'If you are interested in a work or would like to commission a painting',
            'your_name': 'Your Name',
            'your_email': 'Your Email',
            'your_phone': 'Phone',
            'your_message': 'Message',
            'send': 'Send',
            'price': 'Price',
            'size': 'Size',
            'year': 'Year',
            'technique': 'Technique',
            'oil_on_canvas': 'Oil on canvas',
            'available': 'Available',
            'sold': 'Sold',
            'inquire': 'Inquire about this work',
            'back_to_gallery': 'Back to Gallery',
            'interested_in': 'I am interested in the work',
            'message_sent': 'Thank you! Your message has been sent.',
            'all_paintings': 'All Paintings',
            'filter_available': 'Available',
            'filter_sold': 'Sold',
        },
        'ru': {
            'site_title': 'Импрессионизм Алексея Куревина',
            'nav_home': 'Главная',
            'nav_gallery': 'Галерея',
            'nav_about': 'О художнике',
            'nav_contact': 'Контакты',
            'hero_subtitle': 'Свет, цвет и эмоции на холсте',
            'view_gallery': 'Смотреть работы',
            'contact_artist': 'Связаться с художником',
            'featured_works': 'Избранные работы',
            'all_works': 'Все работы',
            'about_title': 'О художнике',
            'contact_title': 'Связаться',
            'contact_subtitle': 'Если вас заинтересовала работа или вы хотите заказать картину',
            'your_name': 'Ваше имя',
            'your_email': 'Ваш email',
            'your_phone': 'Телефон',
            'your_message': 'Сообщение',
            'send': 'Отправить',
            'price': 'Цена',
            'size': 'Размер',
            'year': 'Год',
            'technique': 'Техника',
            'oil_on_canvas': 'Масло на холсте',
            'available': 'Доступна',
            'sold': 'Продано',
            'inquire': 'Узнать об этой работе',
            'back_to_gallery': 'Вернуться в галерею',
            'interested_in': 'Меня интересует работа',
            'message_sent': 'Спасибо! Ваше сообщение отправлено.',
            'all_paintings': 'Все картины',
            'filter_available': 'Доступные',
            'filter_sold': 'Проданные',
        }
    }
    return translations.get(lang, translations['uk'])

@app.context_processor
def inject_globals():
    return {
        'lang': get_lang(),
        't': get_translations(),
        'config': app.config,
        'current_year': datetime.now().year
    }

# ============== PUBLIC ROUTES ==============

@app.route('/')
def home():
    featured = Painting.query.filter_by(is_featured=True, is_available=True).order_by(Painting.order).limit(6).all()
    if not featured:
        featured = Painting.query.filter_by(is_available=True).order_by(Painting.order).limit(6).all()
    return render_template('pages/home.html', paintings=featured)

@app.route('/gallery')
def gallery():
    filter_type = request.args.get('filter', 'all')
    
    query = Painting.query.filter_by(is_available=True)
    
    if filter_type == 'available':
        query = query.filter_by(is_sold=False)
    elif filter_type == 'sold':
        query = query.filter_by(is_sold=True)
    
    paintings = query.order_by(Painting.order, Painting.created_at.desc()).all()
    return render_template('pages/gallery.html', paintings=paintings, current_filter=filter_type)

@app.route('/painting/<int:painting_id>')
def painting_detail(painting_id):
    painting = Painting.query.get_or_404(painting_id)
    other_paintings = Painting.query.filter(
        Painting.id != painting_id,
        Painting.is_available == True
    ).order_by(Painting.order).limit(4).all()
    return render_template('pages/painting.html', painting=painting, other_paintings=other_paintings)

@app.route('/about')
def about():
    return render_template('pages/about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    painting_id = request.args.get('painting')
    painting = None
    if painting_id:
        painting = Painting.query.get(painting_id)
    
    if request.method == 'POST':
        msg = ContactMessage(
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            painting_id=request.form.get('painting_id') or None,
            message=request.form.get('message')
        )
        db.session.add(msg)
        db.session.commit()
        flash(get_translations()['message_sent'], 'success')
        return redirect(url_for('contact'))
    
    return render_template('pages/contact.html', painting=painting)

@app.route('/set-lang/<lang>')
def set_lang(lang):
    if lang in ['uk', 'en', 'ru']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

# ============== ADMIN ROUTES ==============

@app.route('/studio/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        flash('Невірний логін або пароль', 'error')
    
    return render_template('admin/login.html')

@app.route('/studio/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/studio')
@login_required
def admin_dashboard():
    paintings_count = Painting.query.count()
    available_count = Painting.query.filter_by(is_sold=False, is_available=True).count()
    sold_count = Painting.query.filter_by(is_sold=True).count()
    messages_count = ContactMessage.query.filter_by(is_read=False).count()
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', 
                         paintings_count=paintings_count,
                         available_count=available_count,
                         sold_count=sold_count,
                         messages_count=messages_count,
                         recent_messages=recent_messages)

@app.route('/studio/paintings')
@login_required
def admin_paintings():
    paintings = Painting.query.order_by(Painting.order, Painting.created_at.desc()).all()
    return render_template('admin/paintings.html', paintings=paintings)

@app.route('/studio/paintings/add', methods=['GET', 'POST'])
@login_required
def admin_add_painting():
    if request.method == 'POST':
        painting = Painting(
            title_uk=request.form.get('title_uk'),
            title_en=request.form.get('title_en'),
            title_ru=request.form.get('title_ru'),
            description_uk=request.form.get('description_uk'),
            description_en=request.form.get('description_en'),
            description_ru=request.form.get('description_ru'),
            width=int(request.form.get('width')) if request.form.get('width') else None,
            height=int(request.form.get('height')) if request.form.get('height') else None,
            year=int(request.form.get('year')) if request.form.get('year') else None,
            technique_uk=request.form.get('technique_uk') or 'Олія на полотні',
            technique_en=request.form.get('technique_en') or 'Oil on canvas',
            technique_ru=request.form.get('technique_ru') or 'Масло на холсте',
            price=float(request.form.get('price')) if request.form.get('price') else None,
            is_sold=request.form.get('is_sold') == 'on',
            is_featured=request.form.get('is_featured') == 'on',
            order=int(request.form.get('order')) if request.form.get('order') else 0
        )
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid duplicates
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                painting.image = filename
        
        db.session.add(painting)
        db.session.commit()
        flash('Картину додано!', 'success')
        return redirect(url_for('admin_paintings'))
    
    return render_template('admin/painting_form.html', painting=None)

@app.route('/studio/paintings/edit/<int:painting_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_painting(painting_id):
    painting = Painting.query.get_or_404(painting_id)
    
    if request.method == 'POST':
        painting.title_uk = request.form.get('title_uk')
        painting.title_en = request.form.get('title_en')
        painting.title_ru = request.form.get('title_ru')
        painting.description_uk = request.form.get('description_uk')
        painting.description_en = request.form.get('description_en')
        painting.description_ru = request.form.get('description_ru')
        painting.width = int(request.form.get('width')) if request.form.get('width') else None
        painting.height = int(request.form.get('height')) if request.form.get('height') else None
        painting.year = int(request.form.get('year')) if request.form.get('year') else None
        painting.technique_uk = request.form.get('technique_uk')
        painting.technique_en = request.form.get('technique_en')
        painting.technique_ru = request.form.get('technique_ru')
        painting.price = float(request.form.get('price')) if request.form.get('price') else None
        painting.is_sold = request.form.get('is_sold') == 'on'
        painting.is_featured = request.form.get('is_featured') == 'on'
        painting.order = int(request.form.get('order')) if request.form.get('order') else 0
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                painting.image = filename
        
        db.session.commit()
        flash('Картину оновлено!', 'success')
        return redirect(url_for('admin_paintings'))
    
    return render_template('admin/painting_form.html', painting=painting)

@app.route('/studio/paintings/delete/<int:painting_id>', methods=['POST'])
@login_required
def admin_delete_painting(painting_id):
    painting = Painting.query.get_or_404(painting_id)
    db.session.delete(painting)
    db.session.commit()
    flash('Картину видалено!', 'success')
    return redirect(url_for('admin_paintings'))

@app.route('/studio/messages')
@login_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)

@app.route('/studio/messages/mark-read/<int:message_id>', methods=['POST'])
@login_required
def admin_mark_read(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    msg.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/studio/messages/delete/<int:message_id>', methods=['POST'])
@login_required
def admin_delete_message(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Повідомлення видалено!', 'success')
    return redirect(url_for('admin_messages'))

# ============== INIT ==============

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin if not exists
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin')
            admin.set_password('kurevin2026')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    init_db()
    app.run(debug=False, port=5001, host='0.0.0.0')
