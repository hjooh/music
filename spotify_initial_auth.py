from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()


def run_setup():   
    # auth manager 
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CID"),
        client_secret=os.getenv("SPOTIPY_CSECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT"),
        scope="user-modify-playback-state user-read-playback-state",
        open_browser=True,  
        cache_path=".cache" 
    )

    token = auth_manager.get_access_token(as_dict=False)
    
    if token:
        print("Spotify is authorized. You may continue.")

    else:
        print("authorization failed.")

if __name__ == "__main__":
    run_setup()