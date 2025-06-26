from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_migrate import Migrate
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime

# Import de l'instance db créée dans extensions.py
from extensions import db

# Import des modèles (assure-toi que models.py utilise la même instance db)
from models import Admin, Category, Article, Comment, Like

app = Flask(__name__)
app.secret_key = 'ton_secret_key_ici'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tonemail@gmail.com'
app.config['MAIL_PASSWORD'] = 'motdepasse_d_application'
app.config['MAIL_DEFAULT_SENDER'] = 'tonemail@gmail.com'


mail = Mail(app)


# Création du dossier instance si nécessaire
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, 'site.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Initialise db et migrate avec l'app
db.init_app(app)
migrate = Migrate(app, db)

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

@app.route('/')
def home():
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('home.html', articles=articles, categories=categories)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message_content = request.form['message']

        msg = Message(
            subject=f"Nouveau message de {name}",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=["Aeeegs@gmail.com"],  # L'adresse qui reçoit les messages
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

    return render_template('contact.html')


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
    articles = Article.query.filter_by(category_id=category_id).order_by(Article.date_posted.desc()).all()
    recent_articles = Article.query.order_by(Article.date_posted.desc()).limit(3).all()
    categories = Category.query.order_by(Category.name).all()
    category = Category.query.get_or_404(category_id)
    return render_template('category_posts.html', articles=articles, categories=categories, category=category,recent_articles=recent_articles)


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
            date_posted=datetime.utcnow()
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
    flash("Merci pour votre like !", "success")
    return redirect(request.referrer or url_for('post', post_id=article_id))


@app.route('/like_comment/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.likes is None:
        comment.likes = 0
    comment.likes += 1
    db.session.commit()
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
        date_posted=datetime.utcnow(),
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
    return render_template('edit_admin.html', admin=admin)

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

# === MAIN ===
if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists(db_path):
            db.create_all()
            print("Base de données créée dans 'instance/site.db'.")

        # Création d'un admin par défaut s'il n'existe pas encore
        if Admin.query.count() == 0:
            default_admin = Admin(
                username='admin',
                password=generate_password_hash('admin123')
            )
            db.session.add(default_admin)
            db.session.commit()
            print("Admin par défaut créé : username='admin', password='admin123'")

    app.run(debug=True)
