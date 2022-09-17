from urllib import response
import webbrowser
import requests
import base64
import urllib.parse
import datetime


class SpotifyOauth:
    client_id = None
    client_secret = None
    redirect_uri = "http://localhost:8888/callback"
    token = None
    scopes = None
    access_token = None
    access_token_expires = datetime.datetime.now()
    refresh_token = None
    code = None

    def __init__(self, client_id=None, client_secret=None, scopes=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes
        self.code = self._get_auth_response()

    def _get_user_input(self, prompt):
        return input(prompt)

    def _open_auth_url(self):
        auth_url = self._get_authorize_url()
        webbrowser.open(auth_url)

    def _get_auth_response(self):
        self._open_auth_url()
        prompt = "Enter the url: \n"
        response = self._get_user_input(prompt)
        code = self._parse_auth_response_url(response)
        return code

    def _get_authorize_url(self):
        headers = {
            "scope": self.scopes,
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
        }
        params = urllib.parse.urlencode(headers)
        url = f"https://accounts.spotify.com/authorize?{params}"
        return url

    def _parse_auth_response_url(self, redirected_url):
        code = urllib.parse.parse_qs(urllib.parse.urlsplit(redirected_url).query)[
            "code"
        ][0]
        return code

    def _get_base64_message(self):
        message = f"{self.client_id}:{self.client_secret}"
        message_bytes = message.encode("ascii")
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode("ascii")
        return base64_message

    def _perform_access_token(self):
        token_url = "https://accounts.spotify.com/api/token"
        auth_header = {
            "Authorization": "Basic " + self._get_base64_message(),
        }
        auth_data = {
            "grant_type": "authorization_code",
            "code": self.code,
            "redirect_uri": self.redirect_uri,
        }
        response = requests.post(token_url, headers=auth_header, data=auth_data).json()
        self.access_token = response["access_token"]
        expires_in = response["expires_in"]
        self.refresh_token = response["refresh_token"]
        now = datetime.datetime.now()
        self.access_token_expires = now + datetime.timedelta(seconds=expires_in)

    def _refresh_token(self):
        token_url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + self._get_base64_message()
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        response = requests.post(token_url, headers=headers, data=data).json()
        self.access_token = response["access_token"]
        expires_in = response["expires_in"]
        now = datetime.datetime.now()
        self.access_token_expires = now + datetime.timedelta(seconds=expires_in)

    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if token == None:
            self._perform_access_token()
            return self.get_access_token()
        elif expires < now:
            self._refresh_token()
            return self.get_access_token()
        return token
