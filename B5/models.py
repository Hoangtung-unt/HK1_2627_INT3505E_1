from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Book(db.Model):
    __tablename__ = "books"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    price_vnd = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0)
    genre = db.Column(db.String(100), index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": f"book_{self.id}",
            "title": self.title,
            "isbn": self.isbn,
            "price": {"amount": self.price_vnd, "currency": "VND"},
            "stock": self.stock,
            "genre": self.genre,
            "createdAt": self.created_at.isoformat() + "Z" if self.created_at else None
        }