import { Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import React from 'react';

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [videos, setVideos] = useState([]);
  const navigate = useNavigate();
  useEffect(() => {
    const cached = localStorage.getItem('searchVideos');
    if (cached) {
      setVideos(JSON.parse(cached));
    }
  }, []);
  
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    const res = await fetch('http://localhost:8000/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword: searchQuery }),
    });

    const data = await res.json();
    const flatVideos = data.flatMap((channel: any) => channel.videos);
    setVideos(flatVideos);
    localStorage.setItem('searchVideos', JSON.stringify(flatVideos));
  };

  const handleVideoSelect = (video: any) => {
    navigate('/content', { state: { video,allVideos:videos }});
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <form onSubmit={handleSearch}>
        <div className="relative mb-8">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tech videos..."
            className="w-full px-4 py-3 pr-12 rounded-lg border"
          />
          <button type="submit" className="absolute right-3 top-1/2 -translate-y-1/2">
            <Search className="w-6 h-6" />
          </button>
        </div>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {videos.map((video: any) => (
          <div
            key={video.video_id}
            onClick={() => handleVideoSelect(video)}
            className="cursor-pointer bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition"
          >
            <img
              src={`https://img.youtube.com/vi/${video.video_id}/0.jpg`}
              className="w-full h-40 object-cover rounded"
            />
            <h3 className="font-bold mt-2">{video.title}</h3>
            <p className="text-xs text-gray-500 mt-1">
              {video.summary.slice(0, 100)}...
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
