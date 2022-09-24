import re
from dotenv import load_dotenv
import os
from nootbot.irc.irc import Irc
from nootbot.spotify.spotify import Spotify


URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

load_dotenv()


class Bot:
    def __init__(self):
        self.commands = {
            "ping": self.ping,
            "song": self.song,
            "pause": self.pause,
            "skip": self.skip,
            "play": self.play,
            "volume": self.volume,
            "sr": self.add_song,
            "last": self.last_song,
        }
        self.irc = Irc(
            token=os.getenv("OAUTH_TOKEN"),
            username=os.getenv("BOT_NAME"),
            channel=os.getenv("CHANNEL"),
            prefix=os.getenv("PREFIX"),
        )

        self.sp = Spotify(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_SECRET"),
        )
        self.start()

    def start(self):
        self.irc.connect()
        self.message_handler()

    def message_handler(self):
        while True:
            message = self.irc.recv_message()
            if message is not None:
                self.command_handler(message)

    def command_handler(self, message):
        command = message["command"]
        if command is None:
            pass
        if "bot_command" in command:
            if command["bot_command"] in self.commands:
                self.commands[command["bot_command"]](message)

    def is_broadcaster(self, message):
        if "broadcaster" in message["tags"]["badges"]:
            if message["tags"]["badges"]["broadcaster"] == "1":
                return True

    def is_mod(self, message):
        if self.is_broadcaster(message) or message["tags"]["mod"] == "1":
            return True

    def message_author(self, message):
        user = message["source"]["nick"]
        return user

    def ping(self, message):
        self.irc.send_privmsg(f"{self.message_author(message)} PONG")

    def song(self, message):
        response = self.sp.playback_state()
        artist = response["item"]["artists"][0]["name"]
        song_name = response["item"]["name"]
        url = response["item"]["external_urls"]["spotify"]
        response_message = f"@{self.message_author(message)} Now playing {artist} - {song_name} [{url}]"
        self.irc.send_privmsg(response_message)

    def last_song(self, message):
        response = self.sp.recently_played()
        if response["items"]:
            artist = response["items"][0]["track"]["artists"][0]["name"]
            song_name = response["items"][0]["track"]["name"]
            url = response["items"][0]["track"]["external_urls"]["spotify"]
            response_message = f"@{self.message_author(message)} Previous song {artist} - {song_name} [{url}]"
            self.irc.send_privmsg(response_message)

    def pause(self, message):
        if self.is_mod(message):
            self.sp.pause_playback()
            self.irc.send_privmsg(f"@{self.message_author(message)} paused SongRequest")

    def play(self, message):
        if self.is_mod(message):
            self.sp.start_playback()
            self.irc.send_privmsg(
                f"@{self.message_author(message)} resumed SongRequest"
            )

    def skip(self, message):
        if self.is_mod(message):
            self.sp.skip_playback()
            self.irc.send_privmsg(
                f"@{self.message_author(message)} skipped the current song"
            )

    def volume(self, message):
        if message["command"]["bot_command_params"]:
            volume = int(message["command"]["bot_command_params"][0])
            if volume.endswith("%"):
                volume = volume.replace("%", "")

            if self.is_mod(message):
                if volume < 0 or volume > 100:
                    pass
                self.sp.playback_volume(volume)
                self.irc.send_privmsg(
                    f"@{self.message_author(message)} changed the volume to {volume}%"
                )

    def add_song(self, message):
        song_uri = None

        song = "".join(message["command"]["bot_command_params"][0:])
        if (
            song.startswith("spotify:track:")
            or not song.startswith("spotify:track")
            and re.match(URL_REGEX, song)
        ):
            song_uri = song
            self.chat_sr(message, song_uri, song_uri)
        else:
            self.chat_sr(message, song, song_uri)

    def chat_sr(self, message, song, song_uri):
        if song_uri == None:
            response = self.sp.search(song)
            if response["tracks"]["items"] != []:
                song_uri = response["tracks"]["items"][0]["uri"]
            else:
                song_uri = None
        elif re.match(URL_REGEX, song_uri):
            song_uri = song_uri.split("/")[4]
            data = self.sp.track(song_uri)
            if data != None:
                song_uri = data["uri"]

        if song_uri != None:
            song_id = song_uri.replace("spotify:track:", "")
            response = self.sp.track(song_id)
            song_name = response["name"]
            song_artists = [artist["name"] for artist in response["artists"]]
            duration = response["duration_ms"] / 60000
            url = response["external_urls"]["spotify"]
            if duration > 7:
                self.irc.send_privmsg(
                    f"@{self.message_author(message)} This song is too long"
                )
            else:
                self.sp.add_to_queue(song_uri)
                self.irc.send_privmsg(
                    f"@{self.message_author(message)} {song_name} - {', '.join(song_artists)} [{url}] has been added to SongRequest"
                )
        else:
            self.irc.send_privmsg(
                f"@{self.message_author(message)} This song doesn't exist."
            )
