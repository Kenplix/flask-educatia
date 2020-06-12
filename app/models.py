from datetime import datetime
from typing import Optional

from flask import current_app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from app import db, bcrypt, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


UserRole = db.Table(
    'user_role',
    db.Column('user_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    image_file = db.Column(db.String(64), nullable=False, default='default.jpg')
    password_hash = db.Column(db.String(128), nullable=False)

    @property
    def password(self):
        raise AttributeError('Password not readable')

    @password.setter
    def password(self, plaintext: str):
        self.password_hash = bcrypt.generate_password_hash(plaintext).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def reset_token(self, expires_sec: int = 1800) -> str:
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @ staticmethod
    def verify_token(reset_token: str) -> Optional['User']:
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(reset_token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    posts = db.relationship(
        'Post',
        backref='author',
        lazy='dynamic'
    )

    roles = db.relationship(
        'Role',
        secondary=UserRole,
        backref=db.backref('users', lazy='dynamic'),
        lazy=True
    )

    def has_role(self, name: str) -> bool:
        role = Role.query.filter_by(name=name).first()
        return True if role in self.roles else False

    def __repr__(self):
        return f'User #{self.id} <{self.username}: {self.email}>'


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'Role #{self.id} <{self.name}: {self.description}>'


PostTag = db.Table(
    'post_tag',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    tags = db.relationship(
        'Tag',
        secondary=PostTag,
        backref=db.backref('posts', lazy='dynamic'),
        lazy=True
    )

    def __repr__(self):
        return f'Post #{self.id} <{self.author.username}: {self.title}>'


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    def __repr__(self):
        return f'Tag #{self.id} <{self.name}>'
