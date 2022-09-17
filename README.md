# NootBot 👾

NootBot is a song request bot that uses Spotify to play songs. My goal when creating this bot was to not use already existing libraries to communicate with spotify and twitch. 


## Installation
1. Clone the repository and install the required libraries:
```bash
git clone https://github.com/jakubiee/NootBot
cd NootBot
./install.sh
source env/bin/activate
```
2. Change the values in the `.env` file.
3. Run the bot:
```bash
python3 main.py
```

## Commands
- User commands
    - `!ping` - Checks if the bot is online
    - `!song` - Shows the current song
    - `!sr {song_name}` - Adds song to the queue
- Moderator commands
    - `!pause` - Stops the music
    - `!play` - Turns on the music
    - `!skip` - Skips the current song
    - `!volume {value}` - Changes the volume 

## License
This project is distributed under the [MIT](LICENSE) license.