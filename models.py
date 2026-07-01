from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# NEW: User Model for Multi-User Accounts
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False) # NEW: Admin privilege flag
    yearly_goal = db.Column(db.Integer, default=50) # NEW: Customizable yearly reading goal
    books = db.relationship('Book', backref='owner', lazy=True, cascade="all, delete-orphan") # NEW: Cascade deletion

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    series = db.Column(db.String(150))
    series_number = db.Column(db.String(20)) 
    genre = db.Column(db.String(100))
    tags = db.Column(db.String(200))
    isbn = db.Column(db.String(20))
    cover_image = db.Column(db.String(500))
    publication_year = db.Column(db.Integer)
    total_pages = db.Column(db.Integer, nullable=False, default=0)
    current_page = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='Want to Read')
    rating = db.Column(db.Integer, default=0) # NEW: Star Rating (1-5)
    notes = db.Column(db.Text)
    favorite = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)
    
    # NEW: Links book to specific user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @property
    def progress_percentage(self):
        if self.status == 'Completed': return 100
        if self.total_pages and self.total_pages > 0: return min(int((self.current_page / self.total_pages) * 100), 100)
        return 0
        
    @property
    def pages_remaining(self):
        return max(0, self.total_pages - self.current_page)