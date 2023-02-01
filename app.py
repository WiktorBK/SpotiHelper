from flask import Flask, request, redirect, render_template, url_for, flash
import requests
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from user import UserModel
from db import db
from secrets_spoti import url, base64
from flask_migrate import Migrate
from forms import LoginForm, RegisterForm, PlaylistGenerator
from werkzeug.security import generate_password_hash, check_password_hash
from spotipy.oauth2 import SpotifyOAuth
from spotifyClient import SpotifyClient
from refresh import Refresh

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/spotihelper'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SECRET_KEY'] = "top_secret"


db.init_app(app)
@app.before_first_request
def create_tables():
     db.create_all()

migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return UserModel.query.get(int(id))

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = UserModel.find_by_email(form.email.data)
        if user is None:
            user = UserModel(form.email.data, form.password.data)
            user.save_to_db()
            form.email.data = ''
            form.password.data = ''
            form.repeat_password.data = ''
            login_user(user)
            return redirect(url)
        else:
            flash("User with that email address already exists.")
    
    return render_template('register.html', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
          user = UserModel.find_by_email(form.email.data)
          if user:
            if user.auth_token == "":
                return redirect(url)
            elif check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successfull!")
                try:
                    return redirect(url_for('index'))
                except:
                    return redirect(url)
            else:
                flash("Wrong Password - Try Again!")
          else:
               flash("That User Doesn't Exist - Try Again!")

    return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out")
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    refresh = Refresh()
    if refresh.has_been_revoked() is False:
        client = SpotifyClient()
        user = current_user
        currently_playing = client.currently_playing()
        return render_template("home.html", user=user, currently_playing=currently_playing)
    else:
        return redirect(url)

@app.route("/recently-played-songs")
@login_required
def recently_played():
    refresh = Refresh()
    if refresh.has_been_revoked() is False:
        client = SpotifyClient()
        user = current_user
        tracks = client.recently_played()

        return render_template("recentlyplayed.html", user=user, tracks=tracks)
    else:
        return redirect(url)

@app.route("/favourite-tracks/<string:time_range>")
@login_required
def favourite_tracks(time_range):
    refresh = Refresh()
    if refresh.has_been_revoked() is False:
        client = SpotifyClient()
        tracks = client.favourite_tracks(time_range)
        return render_template("favourite_tracks.html", tracks = tracks, time_range=time_range)
    else:
        return redirect(url)

@app.route("/favourite-artists/<string:time_range>")
@login_required
def favourite_artists(time_range):
    refresh = Refresh()
    if refresh.has_been_revoked() is False:
        client = SpotifyClient()
        artists = client.favourite_artists(time_range)
        return render_template("favourite_artists.html", artists = artists, time_range=time_range)
    else:
        return redirect(url)

@app.route("/playlists")
@login_required
def playlists():
    refresh = Refresh()
    if refresh.has_been_revoked() is False:
        client = SpotifyClient()
        playlists = client.get_playlists()
        return render_template("playlists.html", playlists=playlists)
    else:
        return redirect(url)

@app.route("/playlist-generator", methods=["GET", "POST"])
@login_required
def playlist_generator():
    refresh = Refresh()
    if refresh.has_been_revoked() is False:
        client = SpotifyClient()
        form = PlaylistGenerator()
        if form.validate_on_submit() == True:
            playlist_name = form.name.data
            songs = form.songs.data
            tracks = client.generate_tracks(songs)
            client.create_and_populate_playlist(playlist_name, [track['uri'] for track in tracks])
            form.name.data = ''
            flash("Congratulations, you've created new playlist successfully!")
            return render_template("new_playlist.html", tracks = tracks, playlist_name = playlist_name)
            
        return render_template("playlist_generator.html", form=form)
    else:
        return redirect(url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    if code is None:
        flash("Couldn't create account. Spotify access not granted")
        user = UserModel.find_by_email(current_user.email)
        logout_user()
        user.delete_from_db()
        return redirect(url_for('register'))
    else:
       data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://localhost:8000/callback',
    }
       response = requests.post('https://accounts.spotify.com/api/token',headers={"Authorization": f'Basic {base64}'}, data=data)
       user = current_user
       user.auth_token = response.json()['access_token']
       user.refresh_token = response.json()['refresh_token']
       db.session.commit() 
       
       return redirect("/")

@app.route("/account")
@login_required
def manage_account():
    refresh = Refresh()
    client = SpotifyClient()
    if refresh.has_been_revoked() is False:
        user_id = client.get_user_id()
        name = client.get_name()
        return render_template('account.html', user_id = user_id, name = name)
    else:
        return redirect(url)

@app.route("/access-decline")
@login_required
def access_decline():
    user = current_user
    user.auth_token = ""
    user.refresh_token = ""
    db.session.commit()
    flash("Spotify access not granted. Sign in again")
    return redirect(url_for('login'))

@app.route("/delete/account")
@login_required
def delete_account():
    user = current_user
    logout_user()
    user.delete_from_db()
    return redirect(url_for('register'))

if __name__ == '__main__':
    app.run(port=8000, host="localhost", debug=True)
