from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy instance
db = SQLAlchemy()

# User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# ClimateData model
class ClimateData(db.Model):
    __tablename__ = 'climate_data'
    id = db.Column(db.Integer, primary_key=True)
    ulke = db.Column(db.String(100), nullable=False)  # Country
    sehir = db.Column(db.String(100), nullable=False)  # City
    saat = db.Column(db.String(50), nullable=False)  # Time
    nem = db.Column(db.Float, nullable=False)  # Humidity
    sicaklik_degeri = db.Column(db.Float, nullable=False)  # Temperature
    oran = db.Column(db.Float, nullable=False)  # CO2 Ratio
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

