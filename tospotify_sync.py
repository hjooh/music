import discord
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BTOKEN")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CSECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT")

# helper function to grab target Discord UID from file
def get_uid(filename="uid.txt"):
    with open(filename, "r") as f:
        return int(f.read().strip())

# Spotify auth
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state",
    open_browser=False,
    cache_path=".cache"
))


# Discord bot
intents = discord.Intents.default()
intents.presences = True # for activity status
intents.members = True # to find correct user
client = discord.Client(intents=intents)

# user-tracking logic (Discord bot)
@client.event
async def on_ready():
    target_id = get_uid()
    print(f'bot status: online as {client.user}')
    print(f'tracking user: {target_id}')


# track updates on YouTube music (e.g. changing the song)
@client.event
async def on_presence_update(_, after):
    current_target_id = get_uid()

    # find specific user
    if after.id != current_target_id:
        return

    if not after.activities:
        print('no activities for this user found')
        return

    for activity in after.activities:
        # may have to update if YouTube Music -> Pear 
        if activity.name == "YouTube Music" or "Music" in activity.name:
            title = activity.details  
            artist = activity.state   
            
            if title:
                print(f"song detected: {title} - {artist}")
                sync_to_yt(title, artist)
                return


# update Spotify to track YT Music
def sync_to_yt(title, artist):
    try:
        search_query = f"{title}"
        if artist:
            search_query += f" {artist}"

        # check if the song playing is already being played on Spotify
        current = sp.current_playback()
        if current and current.get('item'):
            current_track = current['item']['name']
            if title.lower() in current_track.lower():
                return 

        # search Spotify for song
        results = sp.search(q=search_query, limit=1, type='track')
        
        if results['tracks']['items']:
            uri = results['tracks']['items'][0]['uri']
            song_name = results['tracks']['items'][0]['name']
            
            # play the song on Spotify
            sp.start_playback(uris=[uri])
            print(f"synced to Spotify: {song_name}")
        else:
            print(f"could not find song on Spotify: {search_query}")

    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 403:
            print("Spotify not open on your device")
        elif e.http_status == 404:
             print("Spotify not active - press play to start (any song works)")
        else:
            print(f"Spotify API error: {e}")

client.run(DISCORD_TOKEN)