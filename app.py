from flask import Flask, redirect, abort, session, url_for, render_template, make_response, request
#from flask_socketio import SocketIO, join_room, leave_room, emit, send
from flask_recaptcha import ReCaptcha
from matchmaker import Room, RoomManager, Settings, Player
import validation
import uuid

app = Flask(__name__)

# ReCaptcha Config
# Put your site key in a file called recaptcha_site_key
# Put your secret key in a file called recaptcha_secret_key
app.config.update({
    'RECAPTCHA_ENABLED': True if not app.config['DEBUG'] else False,
    'RECAPTCHA_SITE_KEY': open('recaptcha_site_key', 'r').read(),
    'RECAPTCHA_SECRET_KEY': open('recaptcha_secret_key', 'r').read()
})


# App secret key for sessions
# Stored in file called secret_key
app.secret_key = open('secret_key', 'r').read()

# Too complicated and perhaps not needed
"""
socketio = SocketIO(app)

users: Dict[str, User] = {}

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    sid = request.sid
    user = users.get(sid)
    if user:
        player = Room.player_pool[user.player_id]
        room_manager.get_rooms()[user.room].remove_player(player)
        leave_room(user.room)
        users.pop(sid)
        print(player_id + ' has left the room.')
        send(player.name() + ' has left the room.', room=room)
    print('Client disconnected')

@socketio.on('join')
def on_join(data):
    player_id = data['player_id']
    room = data['room']
    sid = request.sid
    users[sid] = User(player_id, room)
    player = Room.player_pool[player_id]
    join_room(room)
    print(player_id + ' has entered the room.')
    #send(player_id + ' has entered the room.', room=room)


@socketio.on('leave')
def on_leave(data):
    player_id = data['player_id']
    room = data['room']
    leave_room(room)
    print(player_id + ' has left the room.')
    #send(player_id + ' has left the room.', room=room)
"""

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


app.jinja_env.globals['csrf_token'] = generate_csrf_token

recaptcha = ReCaptcha(app=app)

room_manager = RoomManager()

# Main page
@app.route('/')
def index():
    return render_template('index.html')

# Rooms listing
@app.route('/rooms')
def rooms():
    return render_template('rooms.html', rooms=room_manager.get_rooms(), Settings = Settings)

# Room creation form
@app.route('/create', methods=['GET', 'POST'])
def create():
    player_id = request.cookies.get('id')
    players = Room.player_pool

    # If user doesnt have a name and id assigned, redirect them
    if not player_id or not player_id in players.keys():
        return redirect('/name/create')

    if request.method == 'POST':

        player = players[player_id]

        if not request.cookies.get('cookies'):
            return render_template('create.html', settings=Settings, error='You must accept the use of cookies before proceeding.')

        if not recaptcha.verify():
            return render_template('create.html', settings=Settings, error='ReCaptcha failed.')

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

        if not settings_validate:
            return render_template('create.html', settings=Settings, error=settings_error)

        room = room_manager.create_room(settings, player)

        response = make_response(redirect(f'/room/{room.get_id()}'))

        return response
    else:
        return render_template('create.html', settings=Settings, error=None)


@app.route('/room/<room_id>')
def room(room_id):
    rooms = room_manager.get_rooms()
    room = rooms.get(room_id)
    player_id = request.cookies.get('id')

    if not room:
        return render_template('room.html', error='Room does not exist.')

    elif not player_id or not player_id in Room.player_pool.keys():
        return redirect(f'/name/room/{room_id}')

    #elif room.is_full():
    #    return render_template('room.html', error='The room is full.')

    else:
        player: Player = Room.player_pool[player_id]
        room.add_player(player)
        return render_template('room.html', player_id = player_id, name=player.name(), room=room, id=room_id, Settings = Settings, error=None)
        

# Accept and enable cookies
@app.route('/cookies')
def cookie_accept():
    origin = request.referrer
    response = make_response(redirect(origin))
    response.set_cookie('cookies', b'true')
    return response

def set_name(name: str, response) -> Player:
    # If player already exists, just change the name
    player_id = request.cookies.get('id')
    players = Room.player_pool
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

        response = None
        if redir:
            response = make_response(redirect(f'/{redir}'))
        else:
            response = make_response(render_template('name.html', error = None, redir = redir))

        if not request.cookies.get('cookies'):
            return render_template('name.html', error='You must accept the use of cookies before proceeding.', redir = redir)


        if not recaptcha.verify():
            return render_template('name.html', error='ReCaptcha failed.', redir = redir)


        name = request.form.get('name')
        name_validation, name_error = validation.validate_name(name)
        if not name_validation:
            return render_template('name.html', error = name_error, redir = redir)

        set_name(name, response)

        return response

    else:
        return render_template('name.html', error = None, redir = redir)
