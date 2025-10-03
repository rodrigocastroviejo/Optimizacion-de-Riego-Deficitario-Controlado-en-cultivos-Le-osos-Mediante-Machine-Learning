from datetime import datetime
from app import db

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    filepath = db.Column(db.String(200), nullable=False)  # ruta en disco
    # En el futuro:
    # user_id = db.Column(db.Integer, db.ForeignKey("user.id"))