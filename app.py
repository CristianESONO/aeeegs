from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify
from flask_migrate import Migrate
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Import de l'instance db créée dans extensions.py
from extensions import db

# Import des modèles (assure-toi que models.py utilise la même instance db)
from models import Admin, Category, Article, Comment, Like, BoardTerm, BoardMember, Department, ContactInfo

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_for_dev_only')

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'tonemail@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'motdepasse_d_application')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'tonemail@gmail.com')


mail = Mail(app)


# Création du dossier instance si nécessaire
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, 'site.db')
db_url = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Initialise db et migrate avec l'app
db.init_app(app)
migrate = Migrate(app, db)

def run_migrations_safely():
    from models import Admin
    from werkzeug.security import generate_password_hash

    try:
        # db.create_all() crée toutes les tables manquantes définies dans models.py
        # C'est plus fiable que les migrations Alembic sur un filesystem éphémère (Render)
        db.create_all()
        print("Database tables created/verified successfully.")

        if Admin.query.count() == 0:
            default_admin = Admin(
                username=os.environ.get('ADMIN_USERNAME', 'admin'),
                password=generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))
            )
            db.session.add(default_admin)
            db.session.commit()
            print("Default admin created.")
    except Exception as e:
        print(f"Database init error: {e}")
        raise e

import sys
is_cli = len(sys.argv) > 1 and sys.argv[1] in ['db', 'shell', 'run']
if not is_cli:
    with app.app_context():
        run_migrations_safely()
        # Seed contact info if not exists
        if ContactInfo.query.count() == 0:
            default_contact = ContactInfo(
                address="Dakar, Senegal",
                email="Aeeegs@gmail.com",
                phone="+221 78 596 14 79",
                whatsapp_url="https://whatsapp.com/channel/0029VaycmEG9mrGYpZBjll2i",
                facebook_url="https://www.facebook.com/AEEEGS",
                instagram_url="https://www.instagram.com/aeeegs_tv/?hl=fr-fr"
            )
            db.session.add(default_contact)
            db.session.commit()
            print("Default contact info seeded.")

@app.context_processor
def inject_contact_info():
    """Inject contact info into all templates automatically."""
    contact_info = ContactInfo.query.first()
    if not contact_info:
        contact_info = ContactInfo(
            address="Dakar, Senegal",
            email="Aeeegs@gmail.com",
            phone="+221 78 596 14 79",
            whatsapp_url="https://whatsapp.com/channel/0029VaycmEG9mrGYpZBjll2i",
            facebook_url="https://www.facebook.com/AEEEGS",
            instagram_url="https://www.instagram.com/aeeegs_tv/?hl=fr-fr"
        )
    return dict(contact_info=contact_info)

# Décorateur pour routes protégées admin
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Merci de vous connecter d'abord.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ===== ROUTES =====

@app.route('/admin')
def admin_redirect():
    return redirect(url_for('admin_dashboard'))

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(Article.date_posted.desc()).paginate(page=page, per_page=6)
    categories = Category.query.order_by(Category.name).all()
    return render_template('home.html', articles=articles, categories=categories)

@app.route('/about')
def about():
    current_term = BoardTerm.query.filter_by(is_current=True).first()
    history = BoardTerm.query.order_by(BoardTerm.start_year.desc()).all()
    depts = Department.query.all()
    return render_template('about.html', current_term=current_term, history=history, departments=depts)

@app.route('/directiva')
def directiva_public():
    term_id = request.args.get('term', type=int)
    all_terms = BoardTerm.query.order_by(BoardTerm.start_year.desc()).all()
    
    if term_id:
        selected_term = BoardTerm.query.get(term_id)
    else:
        selected_term = BoardTerm.query.filter_by(is_current=True).first()
        if not selected_term and all_terms:
            selected_term = all_terms[0]
            
    departments = Department.query.all()
    return render_template('directiva.html', selected_term=selected_term, terms=all_terms, departments=departments)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    contact_info = ContactInfo.query.first()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message_content = request.form['message']
        recipient = contact_info.email if contact_info else "Aeeegs@gmail.com"

        msg = Message(
            subject=f"Nuevo mensaje de {name}",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[recipient],
            body=f"""
Vous avez reçu un nouveau message depuis le site AEEEGS :

Nom : {name}
Email : {email}

Message :
{message_content}
"""
        )

        try:
            mail.send(msg)
            flash("Mensaje enviado correctamente. ¡Gracias!", "success")
        except Exception as e:
            print("Erreur lors de l'envoi :", e)
            flash("Error al enviar el mensaje. Inténtalo de nuevo más tarde.", "danger")

        return redirect(url_for('contact'))

    return render_template('contact.html', contact_info=contact_info)


@app.route('/admin/contact', methods=['GET', 'POST'])
@login_required
def admin_contact():
    contact_info = ContactInfo.query.first()
    if not contact_info:
        contact_info = ContactInfo()
        db.session.add(contact_info)
        db.session.commit()

    if request.method == 'POST':
        contact_info.address = request.form.get('address', contact_info.address)
        contact_info.email = request.form.get('email', contact_info.email)
        contact_info.phone = request.form.get('phone', contact_info.phone)
        contact_info.facebook_url = request.form.get('facebook_url', contact_info.facebook_url)
        contact_info.instagram_url = request.form.get('instagram_url', contact_info.instagram_url)
        contact_info.whatsapp_url = request.form.get('whatsapp_url', contact_info.whatsapp_url)
        db.session.commit()
        flash("Información de contacto actualizada correctamente.", "success")
        return redirect(url_for('admin_contact'))

    return render_template('admin/contact.html', contact_info=contact_info)


@app.route('/admin/articles')
@login_required
def admin_articles():
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    return render_template('admin/articles.html', articles=articles)

@app.route('/admin/categories')
@login_required
def admin_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)


@app.route('/post/<int:post_id>')
def post(post_id):
    article = Article.query.get_or_404(post_id)
    return render_template('post.html', article=article)

@app.route('/category/<int:category_id>')
def posts_by_category(category_id):
    page = request.args.get('page', 1, type=int)
    category = Category.query.get_or_404(category_id)
    articles = Article.query.filter_by(category_id=category_id).order_by(Article.date_posted.desc()).paginate(page=page, per_page=6)
    recent_articles = Article.query.order_by(Article.date_posted.desc()).limit(3).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('category_posts.html', articles=articles, categories=categories, category=category, recent_articles=recent_articles)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()

    if not query:
        return redirect(url_for('index'))  # ou afficher un message

    # Recherche dans le titre et le contenu
    articles = Article.query.filter(
        Article.title.ilike(f'%{query}%') |
        Article.content.ilike(f'%{query}%')
    ).order_by(Article.date_posted.desc()).all()

    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'search_results.html',
        query=query,
        articles=articles,
        categories=categories
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash("Connecté avec succès.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Identifiants invalides.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Déconnecté.", "info")
    return redirect(url_for('home'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    total_articles = Article.query.count()
    total_comments = Comment.query.count()
    total_likes = Like.query.count()

    # On prépare des listes séparées pour le graphe
    stats = db.session.query(Category.name, db.func.count(Article.id)).join(Article).group_by(Category.name).all()
    articles_labels = [name for name, _ in stats]
    articles_counts = [count for _, count in stats]

    return render_template(
        'admin/admin.html',
        total_articles=total_articles,
        total_comments=total_comments,
        total_likes=total_likes,
        articles_labels=articles_labels,
        articles_counts=articles_counts
    )


# --- CRUD Articles ---
@app.route('/admin/article/add', methods=['GET', 'POST'])
@login_required
def add_article():
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form['title']
        subtitle = request.form.get('subtitle')
        content = request.form['content']
        category_id = request.form.get('category_id')  # <-- correction ici
        image = request.files.get('image')

        image_filename = None
        if image and image.filename != '':
            image_filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        article = Article(
            title=title,
            content=content,
            category_id=category_id,
            image_filename=image_filename,
            author_id=session['admin_id'],
            date_posted=datetime.now(timezone.utc)
        )
        db.session.add(article)
        db.session.commit()
        flash("Article ajouté avec succès.", "success")
        return redirect(url_for('admin_articles'))

    return render_template('admin/add_article.html', categories=categories)


@app.route('/admin/article/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    categories = Category.query.all()

    if request.method == 'POST':
        article.title = request.form['title']
        article.subtitle = request.form.get('subtitle')
        article.content = request.form['content']
        article.category_id = request.form.get('category_id')  # <-- correction ici

        image = request.files.get('image')
        if image and image.filename != '':
            image_filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            article.image_filename = image_filename

        db.session.commit()
        flash("Article modifié avec succès.", "success")
        return redirect(url_for('admin_articles'))

    return render_template('admin/edit_article.html', article=article, categories=categories)


@app.route('/admin/article/delete/<int:article_id>', methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash("Article supprimé.", "info")
    return redirect(url_for('admin_articles'))

# --- CRUD Comments ---
@app.route('/like_article/<int:article_id>', methods=['POST'])
def like_article(article_id):
    article = Article.query.get_or_404(article_id)
    # On crée un nouveau Like lié à l'article
    like = Like(article_id=article.id)
    db.session.add(like)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'status': 'success',
            'likes_count': len(article.likes)
        })
    
    flash("Merci pour votre like !", "success")
    return redirect(request.referrer or url_for('post', post_id=article_id))


@app.route('/like_comment/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.likes is None:
        comment.likes = 0
    comment.likes += 1
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'status': 'success',
            'likes_count': comment.likes
        })

    flash("Merci pour votre like sur le commentaire !", "success")
    return redirect(request.referrer or url_for('post', post_id=comment.post_id))


@app.route('/add_comment', methods=['POST'])
def add_comment():
    post_id = request.form.get('post_id')
    parent_id = request.form.get('parent_id')  # Peut être None
    username = request.form.get('username')
    content = request.form.get('content')

    if not post_id or not username or not content:
        flash("Tous les champs sont obligatoires.", "danger")
        return redirect(request.referrer or url_for('home'))

    article = Article.query.get(post_id)
    if not article:
        abort(404)

    comment = Comment(
        post_id=article.id,
        parent_id=parent_id if parent_id else None,
        username=username.strip(),
        content=content.strip(),
        date_posted=datetime.now(timezone.utc),
        likes=0
    )
    db.session.add(comment)
    db.session.commit()
    flash("Commentaire ajouté avec succès !", "success")
    return redirect(url_for('post', post_id=article.id))


# --- CRUD Categories ---
@app.route('/admin/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        flash("Catégorie ajoutée.", "success")
        return redirect(url_for('admin_categories'))
    return render_template('admin/add_category.html')

@app.route('/admin/category/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        category.name = request.form['name']
        db.session.commit()
        flash("Catégorie modifiée.", "success")
        return redirect(url_for('admin_categories'))
    return render_template('admin/edit_category.html', category=category)

@app.route('/admin/category/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Catégorie supprimée.", "info")
    return redirect(url_for('admin_categories'))

# --- CRUD Admins ---
@app.route('/admin/users')
@login_required
def list_admins():
    users = Admin.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/add', methods=['GET', 'POST'])
@login_required
def add_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        admin = Admin(username=username, password=hashed_password)
        db.session.add(admin)
        db.session.commit()
        flash("Administrateur ajouté.", "success")
        return redirect(url_for('list_admins'))
    return render_template('admin/add_users.html')

@app.route('/admin/user/edit/<int:admin_id>', methods=['GET', 'POST'])
@login_required
def edit_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    if request.method == 'POST':
        admin.username = request.form['username']
        if request.form['password']:
            admin.password = generate_password_hash(request.form['password'])
        db.session.commit()
        flash("Administrateur modifié.", "success")
        return redirect(url_for('list_admins'))
    return render_template('admin/edit_users.html', admin=admin)

@app.route('/admin/user/delete/<int:admin_id>', methods=['POST'])
@login_required
def delete_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    if admin.id == session.get('admin_id'):
        flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect(url_for('list_admins'))
    db.session.delete(admin)
    db.session.commit()
    flash("Administrateur supprimé.", "info")
    return redirect(url_for('list_admins'))

# --- CRUD Board Terms ---
@app.route('/admin/board')
@login_required
def admin_board():
    terms = BoardTerm.query.order_by(BoardTerm.start_year.desc()).all()
    return render_template('admin/board.html', terms=terms)

@app.route('/admin/board/add', methods=['GET', 'POST'])
@login_required
def add_board_term():
    if request.method == 'POST':
        start_year = request.form['start_year']
        end_year = request.form['end_year']
        president_name = request.form['president_name']
        president_bio = request.form['president_bio']
        is_current = 'is_current' in request.form
        
        image = request.files.get('president_image')
        image_filename = None
        if image and image.filename != '':
            image_filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        if is_current:
            BoardTerm.query.update({BoardTerm.is_current: False})

        term = BoardTerm(
            start_year=start_year,
            end_year=end_year,
            president_name=president_name,
            president_bio=president_bio,
            president_image=image_filename,
            is_current=is_current
        )
        db.session.add(term)
        db.session.commit()
        flash("Periodo directivo añadido.", "success")
        return redirect(url_for('admin_board'))
    return render_template('admin/add_term.html')

@app.route('/admin/board/edit/<int:term_id>', methods=['GET', 'POST'])
@login_required
def edit_board_term(term_id):
    term = BoardTerm.query.get_or_404(term_id)
    if request.method == 'POST':
        term.start_year = request.form['start_year']
        term.end_year = request.form['end_year']
        term.president_name = request.form['president_name']
        term.president_bio = request.form['president_bio']
        is_current = 'is_current' in request.form
        
        image = request.files.get('president_image')
        if image and image.filename != '':
            image_filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            term.president_image = image_filename

        if is_current and not term.is_current:
            BoardTerm.query.update({BoardTerm.is_current: False})
            term.is_current = True
        elif not is_current:
            term.is_current = False

        db.session.commit()
        flash("Periodo directivo actualizado.", "success")
        return redirect(url_for('admin_board'))
    return render_template('admin/edit_term.html', term=term)

@app.route('/admin/board/delete/<int:term_id>', methods=['POST'])
@login_required
def delete_board_term(term_id):
    term = BoardTerm.query.get_or_404(term_id)
    db.session.delete(term)
    db.session.commit()
    flash("Periodo directivo eliminado.", "info")
    return redirect(url_for('admin_board'))

@app.route('/admin/board/member/add/<int:term_id>', methods=['POST'])
@login_required
def add_board_member(term_id):
    name = request.form['name']
    role = request.form['role']
    dept_id = request.form.get('department_id')
    
    image = request.files.get('image')
    image_filename = None
    if image and image.filename != '':
        image_filename = image.filename
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    member = BoardMember(
        term_id=term_id, 
        department_id=dept_id if dept_id else None,
        name=name, 
        role=role,
        image_filename=image_filename
    )
    db.session.add(member)
    db.session.commit()
    flash("Miembro añadido.", "success")
    return redirect(url_for('edit_board_term', term_id=term_id))

@app.route('/admin/board/member/delete/<int:member_id>', methods=['POST'])
@login_required
def delete_board_member(member_id):
    member = BoardMember.query.get_or_404(member_id)
    term_id = member.term_id
    db.session.delete(member)
    db.session.commit()
    flash("Miembro eliminado.", "info")
    return redirect(url_for('edit_board_term', term_id=term_id))

# --- CRUD Departments (Carpetas) ---
@app.route('/admin/departments')
@login_required
def admin_departments():
    depts = Department.query.all()
    terms = BoardTerm.query.order_by(BoardTerm.start_year.desc()).all()
    return render_template('admin/departments.html', depts=depts, terms=terms)

@app.route('/admin/department/add', methods=['POST'])
@login_required
def add_department():
    name = request.form['name']
    description = request.form.get('description')
    if Department.query.filter_by(name=name).first():
        flash("Esta carpeta ya existe.", "danger")
    else:
        dept = Department(name=name, description=description)
        db.session.add(dept)
        db.session.commit()
        flash("Carpeta creada globalmente.", "success")
    return redirect(url_for('admin_departments'))

@app.route('/admin/department/delete/<int:dept_id>', methods=['POST'])
@login_required
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash("Carpeta eliminada del catálogo global.", "info")
    return redirect(url_for('admin_departments'))

@app.route('/admin/board/member/add', methods=['POST'])
@login_required
def add_board_member_standalone():
    term_id = request.form.get('term_id')
    dept_id = request.form.get('department_id')
    name = request.form['name']
    role = request.form['role']
    
    if not term_id:
        flash("Debes seleccionar un Periodo.", "danger")
        return redirect(url_for('admin_departments'))

    image = request.files.get('image')
    image_filename = None
    if image and image.filename != '':
        image_filename = image.filename
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    member = BoardMember(
        term_id=term_id, 
        department_id=dept_id if dept_id else None,
        name=name, 
        role=role,
        image_filename=image_filename
    )
    db.session.add(member)
    db.session.commit()
    flash("Miembro asignado exitosamente.", "success")
    return redirect(url_for('admin_departments'))

# === MAIN ===
if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'True') == 'True')
