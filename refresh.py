from secrets_spoti import base64
import requests
from flask_login import current_user
from flask import redirect
from secrets_spoti import url
import json

class Refresh():
    def __init__(self):
        self.refresh_token = current_user.refresh_token
        self.base64 = base64
        
    def refresh(self):

        query = "https://accounts.spotify.com/api/token"
        response = requests.post(query,
        data={"grant_type":"refresh_token",
            "refresh_token":current_user.refresh_token},
        headers={"Authorization": "Basic " + base64}
        )
        return response.json()["access_token"]

    def has_been_revoked(self):
        query = "https://accounts.spotify.com/api/token"
        response = requests.post(query,
        data={"grant_type":"refresh_token",
            "refresh_token":current_user.refresh_token},
        headers={"Authorization": "Basic " + base64}
        )
        try:
            test = response.json()["access_token"]
            return False
        except:
            return True

