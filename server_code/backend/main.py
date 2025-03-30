from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_utils import get_top_channels_for_topic
from video_utils import generate_dialogue_script
from bgm_suggestions import get_bgm_suggestions
from typing import List

app = FastAPI()
# Enable CORS so frontend can access this API
def format_json():
    pass 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev. Use exact origin in production (e.g., http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class VideoInput(BaseModel):
    video_id: str
    transcript: str

class VideoBatchRequest(BaseModel):
    videos: List[VideoInput]

class SearchRequest(BaseModel):
    keyword: str

@app.post('/api/search')
async def search_videos(request: SearchRequest):
    # topic=request.keyword
    # print("searching for {topic}")
    top_results=get_top_channels_for_topic(request.keyword,top_n=3)
    return top_results

@app.post("/api/generate-content")
async def generate_content(request: VideoBatchRequest):
    individual_summaries=[]
    for v in request.videos:
        summary=generate_dialogue_script(v.transcript)
        individual_summaries.append({
            "video_id":v.video_id,
            "summary":summary
        })
    combined_text=" ".join([s['summary'] for s in individual_summaries])
    combined_transcript=generate_dialogue_script(combined_text)
    return {
        "summaries":individual_summaries,
        "combined_transcript":combined_transcript
    }

@app.post("/api/bgm_suggestions")
def bgm_suggestions(request: SearchRequest):
    response = get_bgm_suggestions(request.keyword)
    return response

