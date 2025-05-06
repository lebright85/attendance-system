from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # frontdesk, teacher, admin

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # math, yoga, wellness
    date = db.Column(db.String(10), nullable=False)  # e.g., "2025-03-12"
    time = db.Column(db.String(10), nullable=False)  # e.g., "10:00 AM"
    teacher = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(20), nullable=False)  # office, online
    group = db.Column(db.String(20), nullable=False)  # counseling, life-skills, recreation

class Attendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    time_in = db.Column(db.String(10), nullable=False)
    time_out = db.Column(db.String(10), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    location = db.Column(db.String(20), nullable=False)
    group = db.Column(db.String(20), nullable=False)
    stipend = db.Column(db.Boolean, nullable=False)
    comments = db.Column(db.Text)

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Seed initial users
        if not User.query.first():
            users = [
                User(username="frontdesk", password="fd123", role="frontdesk"),
                User(username="teacher", password="t123", role="teacher"),
                User(username="admin", password="ad123", role="admin")
            ]
            db.session.bulk_save_objects(users)
            db.session.commit()