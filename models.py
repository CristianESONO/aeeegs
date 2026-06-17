from extensions import db
from datetime import datetime, timezone

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # hashé

    articles = db.relationship('Article', backref='author', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    articles = db.relationship('Article', backref='category', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # réponse possible
    username = db.Column(db.String(100), nullable=False)  # pseudo laissé par le visiteur
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    likes = db.Column(db.Integer, default=0)

    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(100))
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    comments = db.relationship('Comment', backref='article', lazy=True)
    likes = db.relationship('Like', backref='article', lazy=True)

class BoardTerm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_year = db.Column(db.Integer, nullable=False)
    end_year = db.Column(db.Integer, nullable=False)
    president_name = db.Column(db.String(200), nullable=False)
    president_image = db.Column(db.String(100))
    president_bio = db.Column(db.Text)
    is_current = db.Column(db.Boolean, default=False)
    
    members = db.relationship('BoardMember', backref='term', lazy=True, cascade="all, delete-orphan")

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    members = db.relationship('BoardMember', backref='department', lazy=True, cascade="all, delete-orphan")

class BoardMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('board_term.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True) # Si es null, es core (Presi, etc)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    image_filename = db.Column(db.String(100))

