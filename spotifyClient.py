from refresh import Refresh
from flask_login import current_user
import requests
from flask import redirect
from secrets_spoti import url
from db import db
import json

class SpotifyClient():
    def __init__(self):
        refresh = Refresh()
        access_token = refresh.refresh()
        current_user.auth_token = access_token
        self.token = current_user.auth_token

    def recently_played(self):
        
        tracks = []
        url = f"https://api.spotify.com/v1/me/player/recently-played?limit=20"

        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }
        )
        response_json = response.json()
        for track in response_json['items']:
            seconds, track['track']['duration_ms'] = divmod(track['track']['duration_ms'], 1000)
            minutes, seconds = divmod(seconds, 60)
            duration = f'{int(minutes):01d}:{int(seconds):02d}'
            tracks.append(
                {"name": track['track']['name'],
                "artists": track['track']['artists'][0]['name'],
                "duration": duration,
                "image": track['track']['album']['images'][1]['url']
                }
                )

        return tracks
        
    def currently_playing(self):
        
        url = f"https://api.spotify.com/v1/me/player/currently-playing"
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }
        )
        try:
            track={}
            response_json = response.json()
            seconds, response_json['item']['duration_ms'] = divmod(response_json['item']['duration_ms'], 1000)
            minutes, seconds = divmod(seconds, 60)
            duration = f'{int(minutes):01d}:{int(seconds):02d}'
            track['name'] = response_json['item']['name']
            track['artist'] = response_json['item']['artists'][0]['name']
            track['duration'] = duration
            track['image'] = response_json['item']['album']['images'][1]['url']
            return track
        except:
            return None

    def favourite_tracks(self, time_range):
       
        tracks = []
        url = f"https://api.spotify.com/v1/me/top/tracks?limit=30&time_range={time_range}"
        response = requests.get(
            url, 
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }
        )
        response_json = response.json()
        position=0
        for track in response_json['items']:
            position+=1
            tracks.append(
                {"position": position,
                    "name": track['name'],
                "artists": track['artists'][0]['name'],
                "image": track['album']['images'][1]['url']
                }
                )
        return tracks

    def favourite_artists(self, time_range):
        
        artists = []
        url = f"https://api.spotify.com/v1/me/top/artists?limit=30&time_range={time_range}"
        response = requests.get(
            url, 
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }
        )
        response_json = response.json()
        position=0
        for artist in response_json['items']:
            position+=1
            artists.append(
                {"position": position,
                    "name": artist['name'],
                "image": artist['images'][1]['url'],
                "followers": artist['followers']['total'],
                "genres": artist['genres']
                }
                )
        return artists
    
    def create_and_populate_playlist(self, playlist_name, uris):
        
        user_id = self.get_user_id()
        url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

        request_body = json.dumps({"name": playlist_name,
                "description": "playlist created by spotiHelper",
                "public": False})

        response = requests.post(
            url,
            headers={
                "Content-Type": "application\json",
                "Authorization": f"Bearer {self.token}"
            },
            data=request_body
        )

        url = f"https://api.spotify.com/v1/playlists/{response.json()['id']}/tracks"
        request_body2 = json.dumps({"uris": uris,"position": 0})
        response_populate = requests.post(
            url,
            headers={
            "Content-Type": "application\json",
            "Authorization": f"Bearer {self.token}"
            },
            data=request_body2
        )

    def get_user_id(self):
       
        url = "https://api.spotify.com/v1/me"
        response = requests.get(
            url,
            headers={
                "Content-Type": "application\json",
                "Authorization": f"Bearer {self.token}"
            }
        )
        return response.json()['id']


    def get_name(self):
        
        url = "https://api.spotify.com/v1/me"
        response = requests.get(
            url,
            headers={
                "Content-Type": "application\json",
                "Authorization": f"Bearer {self.token}"
            }
        )
        return response.json()['display_name']
    def get_playlists(self):
        
        url = "https://api.spotify.com/v1/me/playlists?limit=50"
        response = requests.get(
            url,
            headers={
                "Content-Type": "application\json",
                "Authorization": f"Bearer {self.token}"
            }
        )
        playlists = []
        for playlist in response.json()['items']:
            if len(playlist['images']) == 0:
                image = "https://community.spotify.com/t5/image/serverpage/image-id/25294i2836BD1C1A31BDF2?v=v2"
            else:
                image = playlist['images'][0]['url']

            playlists.append(
                {
                    "name": playlist['name'],
                    "owner": playlist['owner']["display_name"],
                    "tracks": playlist['tracks']['total'],
                    "image": image
                    
                }
            )

        return playlists

    def get_genres(self):
        artists = self.favourite_artists("short_term")
        genres = []
        for artist in artists:
            for genre in artist['genres']:
                genres.append(genre)
                break

        return set(genres)

    def generate_tracks(self, limit):
        genres = self.get_genres()
        genres = list(genres)
        tracks = []
        new_genres = []
        for genre in genres:
            new_genres.append(genre.replace(" ", "%20"))
        if len(new_genres) > 5:
            divider = 5
        else: 
            divider = len(new_genres)    

        new_limit = int(limit) // divider
        new_limit = str(new_limit)
        i = 0
        while i < len(new_genres):
            url =f'https://api.spotify.com/v1/search?type=track&q=genre:%22{new_genres[i]}%22&limit={new_limit}'
            response = requests.get(
                url,
                headers={
                    "Content-Type": "application\json",
                    "Authorization": f"Bearer {self.token}"
                }
            )
        
            for track in response.json()['tracks']['items']:
                tracks.append(
                    {"name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "image": track['album']['images'][1]['url'],
                    "url": track['href'],
                    "uri": track['uri'],
                    "genre": genres[i]
                    }
                )
            i+=1
            
        return tracks

    def call_refresh(self):

        refresh_caller = Refresh()
        current_user.auth_token = refresh_caller.refresh()
        db.session.commit()
        self.token = current_user.auth_token
     
        


