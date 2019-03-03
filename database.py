from app import db
from datetime import datetime, timedelta
from uuid import uuid4

difficulty = {
	'normal': "Normal",
	'easy': "Easy",
	'hard': "Hard",
	'expert': "Expert",
	'insane': "Insane",
	'crowdControl': "Crowd Control"
}

goal = {
	"ganon": "Defeat Ganon",
	"dungeons": "All Dungeons",
	"pedestal": "Master Sword Pedestal",
	"triforce-hunt": "Triforce Pieces"
}

logic = {
	'NoGlitches': "No Glitches",
	'OverworldGlitches': "Overworld Glitches",
	'MajorGlitches': "Major Glitches",
	'None': "None (I know what I’m doing)"
}

mode = {
	'standard': "Standard",
	'open': "Open",
	'inverted': "Inverted"
}

variation = {
	'none': "None",
	'timed-race': "Timed Race",
	'timed-ohko': "Timed OHKO",
	'ohko': "OHKO",
	'key-sanity': "Keysanity",
	'retro': "Retro"
}

weapons = {
	'uncle': "Uncle Assured",
	'randomized': "Randomized",
	'swordless': "Swordless"
}


class Difficulty(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), nullable=False)
	description = db.Column(db.String(40), nullable=False)

	def __init__(self, name, description):
		self.name = name
		self.description = description

	def __repr__(self):
		return f'<id {self.id}>'


class Goal(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), nullable=False)
	description = db.Column(db.String(40), nullable=False)

	def __init__(self, name, description):
		self.name = name
		self.description = description

	def __repr__(self):
		return f'<id {self.id}>'


class Logic(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), nullable=False)
	description = db.Column(db.String(40), nullable=False)

	def __init__(self, name, description):
		self.name = name
		self.description = description

	def __repr__(self):
		return f'<id {self.id}>'


class Mode(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), nullable=False)
	description = db.Column(db.String(40), nullable=False)

	def __init__(self, name, description):
		self.name = name
		self.description = description

	def __repr__(self):
		return f'<id {self.id}>'


class Variation(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), nullable=False)
	description = db.Column(db.String(40), nullable=False)

	def __init__(self, name, description):
		self.name = name
		self.description = description

	def __repr__(self):
		return f'<id {self.id}>'


class Weapons(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(30), nullable=False)
	description = db.Column(db.String(40), nullable=False)

	def __init__(self, name, description):
		self.name = name
		self.description = description

	def __repr__(self):
		return f'<id {self.id}>'


class Settings(db.Model):

	id = db.Column(db.Integer, primary_key=True)

	difficulty_id = db.Column(db.Integer, db.ForeignKey('difficulty.id'))
	difficulty = db.relationship(
		'Difficulty', foreign_keys='Settings.difficulty_id')

	enemizer = db.Column(db.Boolean)

	goal_id = db.Column(db.Integer, db.ForeignKey('goal.id'))
	goal = db.relationship('Goal', foreign_keys='Settings.goal_id')

	logic_id = db.Column(db.Integer, db.ForeignKey('logic.id'))
	logic = db.relationship('Logic', foreign_keys='Settings.logic_id')

	mode_id = db.Column(db.Integer, db.ForeignKey('mode.id'))
	mode = db.relationship('Mode', foreign_keys='Settings.mode_id')

	spoilers = db.Column(db.Boolean)

	tournament = db.Column(db.Boolean)

	variation_id = db.Column(db.Integer, db.ForeignKey('variation.id'))
	variation = db.relationship(
		'Variation', foreign_keys='Settings.variation_id')

	weapons_id = db.Column(db.Integer, db.ForeignKey('weapons.id'))
	weapons = db.relationship('Weapons', foreign_keys='Settings.weapons_id')

	def __init__(self, difficulty, enemizer, goal, logic, mode, spoilers, tournament, variation, weapons):
		self.difficulty = difficulty
		self.enemizer = enemizer
		self.goal = goal
		self.logic = logic
		self.mode = mode
		self.spoilers = spoilers
		self.tournament = tournament
		self.variation = variation
		self.weapons = weapons

	def to_dict(self) -> dict:
		return {
			"difficulty": self.difficulty.name,
			"enemizer": self.enemizer,
			"lang": 'en',
			"logic": self.logic.name,
			"mode": self.mode.name,
			"spoilers": self.spoilers,
			"tournament": self.tournament,
			"variation": self.variation.name,
			"weapons": self.weapons.name
		}







class Player(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	uuid = db.Column(db.String(40), nullable=False)
	name = db.Column(db.String(30), nullable=False)
	create_date = db.Column(db.DateTime(), nullable=False)

	def __init__(self, name):
		self.uuid = str(uuid4())
		self.name = name
		self.create_date = datetime.now()

	def __repr__(self):
		return f'<id {self.id}>'

class Room(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	settings_id = db.Column(db.Integer, db.ForeignKey(Settings.id))
	settings = db.relationship('Settings', foreign_keys="Room.settings_id")
	chat_url = db.Column(db.String(40))
	players = db.relationship('Player', secondary="room_player")
	creator_id = db.Column(db.Integer, db.ForeignKey(Player.id))
	creator = db.relationship('Player', foreign_keys="Room.creator_id")

	hash_code = db.Column(db.String(50))
	expire_time = db.Column(db.DateTime())

	def __init__(self, settings, chat_url, creator, hash_code):
		self.settings = settings
		self.chat_url = chat_url
		self.players.append(creator)
		self.creator = creator
		self.hash_code = hash_code
		self.expire_time = datetime.now() + timedelta(hours=6)

	def get_seed_url(self):
		return f'https://alttpr.com/en/h/{self.hash_code}'
	
	def get_expire_time(self) -> str:
		expire_time = self.expire_time - datetime.now()
		total_seconds = max(expire_time.seconds, 0)
		hours = total_seconds // 3600
		minutes = (total_seconds % 3600) // 60
		seconds = (total_seconds % 3600) % 60
		return f'{hours} hours, {minutes} minutes, {seconds} seconds'

room_player = db.Table(
		'room_player',
		db.Column('room_id', db.Integer, db.ForeignKey(Room.id), primary_key=True),
		db.Column('player_id', db.Integer, db.ForeignKey(Player.id), primary_key=True)
	)

def init_db_values():
	#db.session.commit()
	#db.drop_all()

	settings = [
		(difficulty, Difficulty),
		(goal, Goal),
		(logic, Logic),
		(mode, Mode),
		(variation, Variation),
		(weapons, Weapons)
	]
	room_player.drop(db.engine, checkfirst=True)
	Room.__table__.drop(db.engine, checkfirst=True)
	Settings.__table__.drop(db.engine, checkfirst=True)
	for setting_values, setting_type in settings:
		setting_type.__table__.drop(db.engine, checkfirst=True)
		setting_type.__table__.create(db.engine, checkfirst=True)
		for name, description in setting_values.items():
			entry = setting_type(name, description)
			db.session.add(entry)

	db.create_all()
	db.session.commit()
