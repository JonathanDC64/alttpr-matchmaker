
base_url = 'https://tlk.io/'

def get_chat_room(seed: str) -> str:
    return f'{base_url}alttr_{seed}'

def get_chat_html(channel_name: str, nickname: str) -> str:
    return 
    f"""<div id="tlkio" data-channel="{channel_name}" data-nickname="{nickname}" style="width:100%;height:400px;"></div>
    <script async src="http://tlk.io/embed.js" type="text/javascript"></script>"""