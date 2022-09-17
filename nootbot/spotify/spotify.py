from re import M
from .oauth2 import SpotifyOauth
from requests import request


class Spotify:
    auth_token = None
    client_id = None
    client_secret = None
    scopes = "user-read-currently-playing user-read-playback-state user-modify-playback-state"
    prefix = "https://api.spotify.com/v1/"

    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.sp_oauth = SpotifyOauth(self.client_id, self.client_secret, self.scopes)

    def _headers(self):
        return {"Authorization": f"Bearer {self.sp_oauth.get_access_token()}"}



    def int_request(self, method, url):
        url = self.prefix + url
        req = request(method, url, headers=self._headers())
        if req.status_code == 200:
            return req.json()
            
    def _get(self, url):
        return self.int_request("GET", url)

    def _put(self, url):
        return self.int_request("PUT", url)

    def _post(self, url):
        return self.int_request("POST", url)

    def _delete(self, url):
        return self.int_request("DELETE", url)

    def playback_state(self):
        return self._get("me/player")

    def user_queue(self):
        return self._get("me/player/queue")
    
    def pause_playback(self):
        return self._put("me/player/pause")

    def skip_playback(self):
        return self._post("me/player/next")

    def start_playback(self):
        return self._put("me/player/play")

    def playback_volume(self, volume):
        return self._put(f"me/player/volume?volume_percent={volume}")

    def add_to_queue(self, uri):
        uri = self._get_uri(uri)
        return self._post(f"me/player/queue?uri={uri}")

    def search(self, query):
        return self._get(f"search?q={query}&type=track&limit=1")

    def track(self, track_id):
        return self._get(f"tracks/{track_id}")

    def _get_uri(self, id):
        if id.startswith("spotify:") and len(id.split(":")) == 3:
            return id 
        else:
            return f"spotify:track:{id}"