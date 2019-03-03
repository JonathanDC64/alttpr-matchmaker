"""Main Flask App"""
from os import environ, path
from uuid import uuid4
from flask import Flask, redirect, abort, session, render_template, make_response, request
from flask_recaptcha import ReCaptcha
from flask_sslify import SSLify
from flask_sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
import validation
import alttpr_api
import chat

# TODO Add way to clean up expired database entries

app = Flask(__name__)


POSTGRES = {
	'user':     environ.get('DATABASE_USER'),
	'pw':      environ.get('DATABASE_PASSWORD'),
	'db':       environ.get('DATABASE_NAME'),
	'host':    environ.get('DATABASE_HOST'),
	'port':     environ.get('DATABASE_PORT')
}

DATABASE_URI = ''

if environ.get('DATABASE_URL'):
	DATABASE_URI = environ.get('DATABASE_URL')
else:
	DATABASE_URI = f'postgresql://{POSTGRES["user"]}:{POSTGRES["pw"]}@{POSTGRES["host"]}/{POSTGRES["db"]}'

# only trigger SSLify if the app is running on Heroku
if 'DYNO' in environ:
	sslify = SSLify(app)

work_dir = path.dirname(__file__)

# ReCaptcha Config
# Disabled in debug mode
app.config.update({
	'RECAPTCHA_ENABLED': True if not app.config['DEBUG'] else False,
	'RECAPTCHA_SITE_KEY': environ.get('RECAPTCHA_SITE_KEY'),
	'RECAPTCHA_SECRET_KEY': environ.get('RECAPTCHA_SECRET_KEY'),
	'SQLALCHEMY_DATABASE_URI': DATABASE_URI,
	'SQLALCHEMY_TRACK_MODIFICATIONS': False,
	#"SQLALCHEMY_ECHO": True
})


# App secret key for sessions
# Stored in file called secret_key
app.secret_key = environ.get('APP_SECRET_KEY')

toolbar = DebugToolbarExtension(app)

# Connect SQLAlchemy to app
db = SQLAlchemy(app)

from database import Player, Room, RoomPlayer, Settings, Difficulty, Logic, Goal, Mode, Variation, Weapons, init_db_values

init_db_values()


# Protect against CSRF attacks
@app.before_request
def csrf_protect():
	if request.method == "POST":
		token = session.pop('_csrf_token', None)
		if not token or token != request.form.get('_csrf_token'):
			abort(403)


def generate_csrf_token():
	if '_csrf_token' not in session:
		session['_csrf_token'] = str(uuid4())
	return session['_csrf_token']


# Enable the use of csrf tokens in jinja templates
app.jinja_env.globals['csrf_token'] = generate_csrf_token  # pylint: disable=no-member

# Global var to handle recaptcha
recaptcha = ReCaptcha(app=app)

settings_values = {
	"difficulty": Difficulty.query.all(),
	"goal": Goal.query.all(),
	"logic": Logic.query.all(),
	"mode": Mode.query.all(),
	"variation": Variation.query.all(),
	"weapons": Weapons.query.all()
}



# Main page
@app.route('/')
def index():
	return render_template('index.html')


# Rooms listing
@app.route('/rooms')
def rooms():
	rooms = Room.query.order_by(Room.create_time.desc()).all()
	return render_template('rooms.html', rooms=rooms)


# Room creation form
@app.route('/create', methods=['GET', 'POST'])
def create():
	# Get player id stored in a cookie
	player_id = request.cookies.get('uuid')
	# List of all players on the website
	player = Player.query.filter_by(uuid=player_id).first()

	# If user doesnt have a name and id assigned, redirect them to create one
	if not player_id or not player:
		return redirect('/name/create')

	if request.method == 'POST':

		# User has not accepted the use of cookies
		if not request.cookies.get('cookies'):
			return render_template('create.html', settings=settings_values, error='You must accept the use of cookies before proceeding.')

		# Validate recaptcha
		if not recaptcha.verify():
			return render_template('create.html', settings=settings_values, error='ReCaptcha failed.')

		difficulty = Difficulty.query.filter_by(name=request.form.get('difficulty')).first()
		goal = Goal.query.filter_by(name=request.form.get('goal')).first()
		logic = Logic.query.filter_by(name=request.form.get('logic')).first()
		mode = Mode.query.filter_by(name=request.form.get('mode')).first()
		variation = Variation.query.filter_by(name=request.form.get('variation')).first()
		weapons = Weapons.query.filter_by(name=request.form.get('weapons')).first()
	
		settings = Settings(difficulty, bool(request.form.get('enemizer')), goal, logic, mode, bool(
			request.form.get('spoilers')), bool(request.form.get('tournament')), variation, weapons)

		settings_validate, settings_error = validation.validate_settings(settings)

		# Make certain that all selected settings exist
		if not settings_validate:
			return render_template('create.html', settings=settings, error=settings_error)

		seed = alttpr_api.generate_seed(settings.to_dict())

		hash_code = seed['hash']

		chat_url = chat.get_chat_room(hash_code)

		# Create a game room
		room =  Room(settings=settings, chat_url=chat_url, creator=player, hash_code=hash_code)

		#db.session.add(settings)
		db.session.add(room)

		db.session.commit()

		# generate response that redirects to the game room just created
		response = make_response(redirect(f'/room/{room.hash_code}'))

		return response
	else:
		return render_template('create.html', settings=settings_values, error=None)


@app.route('/room/<room_id>')
def room(room_id):
	# List of all game rooms
	rooms = Room.query.all()
	# Get current game room based on url paramater room_id
	room = Room.query.filter_by(hash_code=room_id).first()
	# Get the players id stored in the cookie
	player_id = request.cookies.get('uuid')
	player = Player.query.filter_by(uuid=player_id).first()

	# Validate that the room exists
	if not room:
		return render_template('room.html', error='Room does not exist.')

	# Validate that the player exists
	elif not player_id or not player:
		return redirect(f'/name/room/{room_id}')

	# Join the room
	else:
		if not player in room.players:
			room.players.append(player)
			db.session.commit()
		room_times = RoomPlayer.query.join(Room).filter(Room.hash_code==room_id).all()
		return render_template('room.html', player=player, room=room, room_times=room_times, error=None)


@app.route('/leave/<room_id>')
def leave(room_id: str):
	# Get room the user desires to leave
	room = Room.query.filter_by(hash_code=room_id).first()
	# Get the players id from the cookie
	player_id = request.cookies.get('uuid')
	# Get player data
	player = Player.query.filter_by(uuid=player_id).first()
	# validate that room and player exists and that the player is in the room
	if room and player and player in room.players:
		room.players.remove(player)
		db.session.commit()
	return redirect('/rooms')


@app.route('/remove/<room_id>')
def remove(room_id):
	room = Room.query.filter_by(hash_code=room_id).first()
	player_id = request.cookies.get('uuid')
	player = Player.query.filter_by(uuid=player_id).first()

	if player_id and player and room and room.creator == player:
		db.session.delete(room)
		db.session.commit()
	
	return redirect('/rooms')


@app.route('/time/<room_id>', methods=['POST'])
def time(room_id):
	room = Room.query.filter_by(hash_code=room_id).first()
	player_id = request.cookies.get('uuid')
	player = Player.query.filter_by(uuid=player_id).first()

	if player_id and player and room and player in room.players:
		hours = request.form.get('hours')
		minutes = request.form.get('minutes')
		seconds = request.form.get('seconds')

		time_validation, time_error = validation.validate_time(hours, minutes, seconds)

		if not validation:
			return redirect(f'/room/{room_id}')

		time = int(seconds) + (int(minutes) * 60) + (int(hours) * 60  * 60)

		room_player = RoomPlayer.query.filter(RoomPlayer.room==room, RoomPlayer.player==player).first()

		room_player.time = time

		#db.session.add(room_player)
		db.session.commit()
	return redirect(f'/room/{room_id}')


# Accept and enable cookies
@app.route('/cookies')
def cookie_accept():
	origin = request.referrer
	response = make_response(redirect(origin))
	response.set_cookie('cookies', b'true')
	return response


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

		player_id = request.cookies.get('uuid')
		player = Player.query.filter_by(uuid=player_id).first()

		# If player already exists, just change the name
		if player_id and player:
			player.name = name
		else:
			player: Player = Player(name)
			db.session.add(player)
			response.set_cookie('uuid', player.uuid)

		db.session.commit()

		return response

	else:
		return render_template('name.html', error=None, redir=redir)
