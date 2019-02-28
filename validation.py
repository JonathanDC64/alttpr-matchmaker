from matchmaker import Settings

def validate_settings(settings: Settings) -> (bool, str):

    if not (settings.difficulty in Settings.difficulty.keys()):
        return False, 'Selected difficulty does not exist'

    if not (settings.goal in Settings.goal.keys()):
        return False, 'Selected goal does not exist'
    
    if not (settings.logic in Settings.logic.keys()):
        return False, 'Selected logic does not exist'

    if not (settings.mode in Settings.mode.keys()):
        return False, 'Selected mode does not exist'

    if not (settings.variation in Settings.variation.keys()):
        return False, 'Selected variation does not exist'

    if not (settings.weapons in Settings.weapons.keys()):
        return False, 'Selected weapons does not exist'
    
    return True, ''

        


MAX_NAME_LENGTH = 12
def validate_name(name: str) -> (bool, str):
    if len(name) == 0:
        return False, 'Name cannot be empty.'
    if len(name) <= MAX_NAME_LENGTH:
        return True, ''
    else:
        return False, f'Name must contain {MAX_NAME_LENGTH} characters or less.'