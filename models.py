from email.policy import default
from enum import unique
from xmlrpc.client import DateTime
from flask_sqlalchemy import SQLAlchemy
from psycopg2 import Date
from pyparsing import nullDebugAction
from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import date

db = SQLAlchemy()


class EmployeeModel(db.Model):
    __tablename__ = "employee"

    emp_id = db.Column(db.Integer, primary_key=True)
    emp_name = db.Column(db.String())
    emp_salary = db.Column(db.Integer())

    def __init__(self, name, salary):
        self.emp_name = name
        self.emp_salary = salary

    def __repr__(self):
        return f"{self.emp_name}:{self.emp_id}"


class Accounts(db.Model):
    __tablename__ = "accounts"

    account_id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(12), unique=True)
    users_count = db.Column(db.Integer, default=1)
    users = db.relationship('Users', backref='accounts', lazy=True)
    lang = db.Column(db.String(3))
    last_message = db.Column(db.String(500))
    curr_user = db.Column(db.Integer)

    def __init__(self, account_number):
        self.account_number = account_number
        self.users_count = 0

    def __repr__(self):
        return f"{self.account_number}"


class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    user_name = db.Column(db.String(50), nullable=False)
    user_pincode = db.Column(db.String(100), nullable=False)
    user_state = db.Column(db.String(50), nullable=False)
    user_age = db.Column(db.Integer, nullable=False)
    user_gender = db.Column(db.String(1), nullable=False)
    user_income = db.Column(db.Integer)
    user_category = db.Column(ARRAY(db.Integer))

    account_id = db.Column(db.Integer, db.ForeignKey(
        'accounts.account_id'), nullable=False)

    def __repr__(self):
        return f"{self.user_name}"


class Schemes(db.Model):
    __tablename__ = "schemes"

    scheme_id = db.Column(db.Integer, primary_key=True)
    scheme_code = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(5000), nullable=False)
    link = db.Column(db.String(280))
    eligible_gender = db.Column(db.String(1), nullable=False)
    min_age = db.Column(db.Integer)
    max_age = db.Column(db.Integer)
    eligible_income = db.Column(db.Integer)
    eligible_category = db.Column(ARRAY(db.String))
    required_documents = db.Column(ARRAY(db.String))
    link = db.Column(ARRAY(db.String))

    def __repr__(self):
        return f"{self.scheme_code}:{self.description[:50]}..."


"""
    CREATE TABLE Schemes(
    scheme_id serial PRIMARY KEY,
    scheme_code varchar(255) not NULL,
    description varchar(5000) not NULL,
    link varchar(280),
    eligible_gender char not NULL,
    min_age int,
    max_age int,
    eligible_income int,
    eligible_category text[],
    required_documents text[]
    );
"""


class AppliedSchemes(db.Model):
    __tablename___ = 'applied_schemes'

    def __init__(self, scheme_id, user_id, status='P'):
        self.scheme_id = scheme_id
        self.user_id = user_id
        self.status = 'P'

    id = db.Column(db.Integer, primary_key=True)

    scheme_id = db.Column(db.Integer, db.ForeignKey(
        'schemes.scheme_id'), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'), nullable=False)

    status = db.Column(db.String(1), default='P')
    applied_date = db.Column(db.Date, default=date.today())

    def __repr__(self):
        return f"{self.scheme_id} {self.user_id} {self.applied_date}"
