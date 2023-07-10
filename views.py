import datetime
from models import *
from flask import jsonify, render_template
import requests, json
import bcrypt




def verify_credentials(username, password):
    user = User.query.filter_by(username=username).first()
    if user:
        hashed_password = user.password.encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), hashed_password):
            return True
        else:
            return False

        