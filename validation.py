"""Input Validation"""

def validate_settings(settings) -> (bool, str):
	"""Validate selected game settings"""
	if not settings.difficulty:
		return False, 'Selected difficulty does not exist'

	if not settings.goal:
		return False, 'Selected goal does not exist'

	if not settings.logic:
		return False, 'Selected logic does not exist'

	if not settings.mode:
		return False, 'Selected mode does not exist'

	if not settings.variation:
		return False, 'Selected variation does not exist'

	if not settings.weapons:
		return False, 'Selected weapons does not exist'

	return True, ''


MAX_NAME_LENGTH = 12


def validate_name(name: str) -> (bool, str):
	"""Validate form name"""
	if not name:
		return False, 'Name cannot be empty.'
	if len(name) <= MAX_NAME_LENGTH:
		return True, ''
	else:
		return False, f'Name must contain {MAX_NAME_LENGTH} characters or less.'

def validate_time(hours: str, minutes: str, seconds: str) -> (bool, str):
	"""Validate game time"""
	if not hours:
		return False, 'Missing hours.'
	if not minutes:
		return False, 'Missing minutes.'
	if not seconds:
		return False, 'Missing seconds.'
	if hours.isdigit() and minutes.isdigit() and seconds.isdigit():
		return False, 'Values must be numeric.'
	hours, minutes, seconds = int(hours), int(minutes), int(seconds)
	if hours < 0:
		return False, 'Hours must be larger than or equal to 0.'
	if minutes < 0 or minutes > 59:
		return False, 'Minutes must be between 0 and 59.'
	if seconds < 0 or seconds > 59:
		return False, 'Seconds must be between 0 and 59.'
	return True, ''
