import socket

class Irc:
    irc_server = "irc.chat.twitch.tv"
    oauth = None
    irc_port = 6667
    username = None
    channel = None
    prefix = None

    def __init__(self, token, username, channel, prefix):
        self.oauth_token = token
        self.username = username
        self.channel = channel
        self.prefix = prefix

    def connect(self):
        self.irc = socket.socket()
        self.irc.connect((self.irc_server, self.irc_port))
        self.send_command(f"PASS {self.oauth_token}")
        self.send_command(f"NICK {self.username}")
        self.send_command(f"JOIN #{self.channel}")
        self.send_command("CAP REQ :twitch.tv/commands twitch.tv/tags")

    def recv_message(self):
        self.resp = self.irc.recv(2048).decode("utf-8")
        try:
            self.message = self.parse_raw_message(self.resp)
            if self.message["command"]["command"] == "PING":
                self.send_command("PONG :tmi.twitch.tv")
                pass
        except:
            self.message = None
        return self.message

    def parse_raw_message(self, raw_message):
        message = {"tags": None, "source": None, "command": None, "parameters": None}

        idx = 0
        raw_tags = None
        raw_source = None
        raw_command = None
        raw_parameters = None

        if raw_message[idx].startswith("@"):
            end_idx = raw_message.index(" ")
            raw_tags = raw_message[1:end_idx]
            idx = end_idx + 1

        if raw_message[idx].startswith(":"):
            idx += 1
            end_idx = raw_message.index(" ", idx)
            raw_source = raw_message[idx:end_idx]
            idx = end_idx + 1

        end_idx = raw_message.index(":", idx)

        if -1 == end_idx:
            end_idx = len(raw_message)
        raw_command = raw_message[idx:end_idx]

        message["command"] = self.parse_command(raw_command)

        if end_idx != len(raw_message):
            idx = end_idx + 1
            raw_parameters = raw_message[idx:].strip()

        if message["command"] is None:
            return
        else:
            if raw_tags is not None:
                message["tags"] = self.parse_tags(raw_tags)
            message["source"] = self.parse_source(raw_source)
            message["parameters"] = raw_parameters
            if raw_parameters and raw_parameters[0] == self.prefix:
                message["command"] = self.parse_parameters(
                    raw_parameters, message["command"]
                )

        return message

    def parse_tags(self, raw_tags):
        parsed_tags = {}
        tags_parts = raw_tags.split(";")
        for tag in tags_parts:
            tag_part = tag.split("=")
            if tag_part[1] == "" or len(tag_part) == 0:
                tag_value = None
            else:
                tag_value = tag_part[1]

            match tag_part[0]:
                case "badge-info":
                    pass
                case "badges":
                    if tag_value:
                        dict_badges = {}
                        badges = tag_value.split(",")
                        for badge in badges:
                            badge_parts = badge.split("/")
                            dict_badges[badge_parts[0]] = badge_parts[1]
                        parsed_tags[tag_part[0]] = dict_badges
                    else:
                        parsed_tags[tag_part[0]] = None
                case "emotes":
                    if tag_value:
                        dict_emotes = {}
                        emotes = tag_value.split("/")
                        for emote in emotes:
                            emote_parts = emote.split(":")
                            text_position = []
                            positions = emote_parts[1].split(",")
                            for position in positions:
                                position_parts = position.split("-")
                                text_position.append(
                                    {
                                        "start_position": position_parts[0],
                                        "end_position": position_parts[1],
                                    }
                                )
                            dict_emotes[emote_parts[0]] = text_position
                        parsed_tags[tag_part[0]] = dict_emotes
                    else:
                        parsed_tags[tag_part[0]] = None
                case "emote-sets":
                    emote_sets_id = tag_value.split(",")
                    parsed_tags[tag_part[0]] = emote_sets_id
                case _:
                    if tag_part[0] in ["client-nonce", "flags"]:
                        pass
                    else:
                        parsed_tags[tag_part[0]] = tag_value

        return parsed_tags

    def parse_command(self, raw_command):
        parsed_command = None
        command_parts = raw_command.split(" ")
        match command_parts[0]:
            case "PRIVMSG":
                parsed_command = {
                    "command": command_parts[0],
                    "channel": command_parts[1],
                }
            case "PING":
                parsed_command = {"command": command_parts[0]}
            case "CAP":
                parsed_command = {
                    "command": command_parts[0],
                    "is_cap_request_enabled": True
                    if command_parts[2] == "ACK"
                    else False,
                }
            case "GLOBALUSERSTATE":
                parsed_command = {"command": command_parts[0]}
            case "ROOMSTATE":
                parsed_command = {
                    "command": command_parts[0],
                    "channel": command_parts[1],
                }
            case "RECONNECT":
                parsed_command = {"command": command_parts[0]}
            case "001":
                parsed_command = {
                    "command": command_parts[0],
                    "channel": command_parts[1],
                }
            case _:
                return

        return parsed_command

    def parse_source(self, raw_source):
        if raw_source is None:
            return None
        else:
            source_parts = raw_source.split("!")
            if len(source_parts) == 2:
                return {
                    "nick": source_parts[0],
                    "host": source_parts[1],
                }
            else:
                return {
                    "nick": None,
                    "host": source_parts[0],
                }

    def parse_parameters(self, raw_parameters, command):
        idx = 0
        command_parts = raw_parameters[idx + 1 :].split()
        if len(command_parts) == 0:
            command["bot_command"] = command_parts[0]
        else:
            command["bot_command"] = command_parts[0]
            command["bot_command_params"] = command_parts[1:]

        return command

    def send_privmsg(self, text):
        self.send_command(f"PRIVMSG #{self.channel} :{text}")

    def send_command(self, command):
        self.irc.send(((command) + "\n").encode("utf-8"))
