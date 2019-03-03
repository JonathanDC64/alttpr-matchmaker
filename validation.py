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
