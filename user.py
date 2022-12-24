from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db import db

class UserModel(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    password_hash = db.Column(db.String(1000))
    auth_token = db.Column(db.String(1000))
    refresh_token = db.Column(db.String(1000))
        
    def __init__(self, email, password):
      self.email = email
      self.password = password     

    def get_id(self):
           return (self.user_id)
      
    @property
    def password(self):  
        raise AttributeError('password is not a readable attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password) 
       
    @classmethod   
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        
    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()