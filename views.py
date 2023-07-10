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

        
def checks_auth(username, auth_token):
    url = 'http://localhost:5000/check_auth'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + auth_token
    }
    data = {
        'username': username
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response and  response.json()['message'] == 'Authorized':
        return True
    else:
        return False