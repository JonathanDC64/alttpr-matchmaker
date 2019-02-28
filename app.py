from flask import Flask, redirect, abort, session, url_for, render_template, make_response, request
from flask_recaptcha import ReCaptcha
from matchmaker import Room, RoomManager, Settings, Player
import validation
import uuid

app = Flask(__name__)

# ReCaptcha Config
# Put your site key in a file called recaptcha_site_key
# Put your secret key in a file called recaptcha_secret_key
# Disabled in debug mode
app.config.update({
    'RECAPTCHA_ENABLED': True if not app.config['DEBUG'] else False,
    'RECAPTCHA_SITE_KEY': open('./recaptcha_site_key', 'r').read(),
    'RECAPTCHA_SECRET_KEY': open('./recaptcha_secret_key', 'r').read()
})


# App secret key for sessions
# Stored in file called secret_key
app.secret_key = open('secret_key', 'r').read()

# Protect against CSRF attacks
@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = str(uuid.uuid4())
    return session['_csrf_token']


# Enable the use of csrf tokens in jinja templates
app.jinja_env.globals['csrf_token'] = generate_csrf_token  # pylint: disable=no-member

# Global var to handle recaptcha
recaptcha = ReCaptcha(app=app)

room_manager = RoomManager()

# Main page
@app.route('/')
def index():
    return render_template('index.html')

# Rooms listing
@app.route('/rooms')
def rooms():
    return render_template('rooms.html', rooms=room_manager.get_rooms(), Settings=Settings)

# Room creation form
@app.route('/create', methods=['GET', 'POST'])
def create():
    # Get player id stored in a cookie
    player_id = request.cookies.get('id')
    # List of all players on the website
    players = Room.player_pool

    # If user doesnt have a name and id assigned, redirect them to create one
    if not player_id or not player_id in players.keys():
        return redirect('/name/create')

    if request.method == 'POST':

        # Get the players info
        player = players[player_id]

        # User has not accepted the use of cookies
        if not request.cookies.get('cookies'):
            return render_template('create.html', settings=Settings, error='You must accept the use of cookies before proceeding.')

        # Validate recaptcha
        if not recaptcha.verify():
            return render_template('create.html', settings=Settings, error='ReCaptcha failed.')

        # Gather settings input from game form
        settings = Settings(
            request.form.get('difficulty'),
            request.form.get('enemizer'),
            request.form.get('goal'),
            'en',
            request.form.get('logic'),
            request.form.get('mode'),
            request.form.get('spoilers'),
            request.form.get('tournament'),
            request.form.get('variation'),
            request.form.get('weapons'),
        )

        settings_validate, settings_error = validation.validate_settings(
            settings)

        # Make certain that all selected settings exist
        if not settings_validate:
            return render_template('create.html', settings=Settings, error=settings_error)

        # Create a game room
        room = room_manager.create_room(settings, player)

        # generate response that redirects to the game room just created
        response = make_response(redirect(f'/room/{room.get_id()}'))

        return response
    else:
        return render_template('create.html', settings=Settings, error=None)


@app.route('/room/<room_id>')
def room(room_id):
    # List of all game rooms
    rooms = room_manager.get_rooms()
    # Get current game room based on url paramater room_id
    room = rooms.get(room_id)
    # Get the players id stored in the cookie
    player_id = request.cookies.get('id')

    # Validate that the room exists
    if not room:
        return render_template('room.html', error='Room does not exist.')

    # Validate that the player exists
    elif not player_id or not player_id in Room.player_pool.keys():
        return redirect(f'/name/room/{room_id}')

    # Join the room
    else:
        # Get player data from the player pool and add them to this room
        player: Player = Room.player_pool[player_id]
        room.add_player(player)
        return render_template('room.html', player_id=player_id, name=player.name(), room=room, id=room_id, Settings=Settings, error=None)


@app.route('/leave/<room_id>')
def leave(room_id: str):
    # Get room the user desires to leave
    room = room_manager.get_rooms().get(room_id)
    # Get the players id from the cookie
    player_id = request.cookies.get('id')
    # Get player data
    player = room.get_players().get(player_id)
    # validate that room and player exists and that the player is in the room
    if room and player and player_id in room.get_players().keys():
        room.remove_player(player)
    return redirect('/rooms')

# Accept and enable cookies
@app.route('/cookies')
def cookie_accept():
    origin = request.referrer
    response = make_response(redirect(origin))
    response.set_cookie('cookies', b'true')
    return response


def set_name(name: str, response) -> Player:
    player_id = request.cookies.get('id')
    players = Room.player_pool
    # If player already exists, just change the name
    if player_id and player_id in players.keys():
        players[player_id].set_name(name)
        return players[player_id]
    else:
        player: Player = Player(name)
        Room.add_global_player(player)
        response.set_cookie('id', player.get_id())
        return player


# Page to set your name
@app.route('/name', methods=['GET', 'POST'])
@app.route('/name/<path:redir>', methods=['GET', 'POST'])
def name(redir=None):
    if request.method == 'POST':
        
        # Redirect to previous page after setting name
        # TODO: Check for security flaws with this technique
        response = None
        if redir:
            response = make_response(redirect(f'/{redir}'))
        else:
            response = make_response(render_template(
                'name.html', error=None, redir=redir))

        # Validate that the user accepted the use of cookies
        if not request.cookies.get('cookies'):
            return render_template('name.html', error='You must accept the use of cookies before proceeding.', redir=redir)

        # Validate recaptcha
        if not recaptcha.verify():
            return render_template('name.html', error='ReCaptcha failed.', redir=redir)

        # Get and valiate chosen name
        name = request.form.get('name')
        name_validation, name_error = validation.validate_name(name)
        if not name_validation:
            return render_template('name.html', error=name_error, redir=redir)

        set_name(name, response)

        return response

    else:
        return render_template('name.html', error=None, redir=redir)
