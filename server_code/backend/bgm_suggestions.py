import os
import freesound
from dotenv import load_dotenv

load_dotenv()
client = freesound.FreesoundClient()
client.set_token(os.getenv("FREE_SOUND_API_KEY"), "token")
print(client)
print('----------------------')

def get_bgm_suggestions(theme):
    results = client.text_search(
        query=theme,
        filter="duration:[30 TO 300]",
        sort="score",
        fields="id,name,previews,url"
    )

    sound_list = [{"name" : sound.name, "link" : sound.previews.preview_hq_mp3} for sound in results]
    return sound_list
