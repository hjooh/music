import discord
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import asyncio 
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BTOKEN")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CSECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT")

TARGET_UID = None

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

# synchronous sync to Spotify function (runs in a thread)
def blocking_spotify_sync(title, artist):
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
             print("Spotify not active - press play to start")
        else:
            print(f"Spotify API error: {e}")
    except Exception as e:
        print(f"{e}")


# event loop (asynchronous)
@client.event
async def on_ready():
    global TARGET_UID
    TARGET_UID = get_uid()
    print(f'bot status: online as {client.user}')
    print(f'tracking user: {TARGET_UID}')

@client.event
async def on_presence_update(_, after):
    if TARGET_UID is None: 
        return

    if after.id != TARGET_UID:
        return

    if not after.activities:
        return

    for activity in after.activities:
        if activity.name == "YouTube Music" or "Music" in activity.name:
            
            if isinstance(activity, discord.Spotify):
                continue
            
            title = activity.details  
            artist = activity.state   
            
            if title:
                print(f"song detected on Discord: {title} - {artist}")

                await asyncio.to_thread(blocking_spotify_sync, title, artist)
                
                return

client.run(DISCORD_TOKEN)