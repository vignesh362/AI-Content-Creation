import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import React from 'react';

export default function ContentGeneration() {
  const location = useLocation();
  const navigate = useNavigate();
  const video = location.state?.video;
  const allVideos = location.state?.allVideos;

  useEffect(() => {
    if (!video || !allVideos || allVideos.length === 0) {
      navigate('/');
    }
  }, [video, allVideos, navigate]);

  const [summary, setSummary] = useState(video?.summary || '');

  // Generate combined transcript (shared for all videos)
  const combinedTranscript = allVideos
    ?.map((v) => v.summary)
    .join(' ') || 'Transcript not available.';

  const handleGenerateVideo = () => {
    navigate('/playback', {
      state: {
        content: summary,
        video_id: video.video_id,
        title: video.title,
        source: video.source,
      },
    });
  };

  return (
    <div className="flex flex-row h-[calc(100vh-4rem)]">
      {/* Left Column: YouTube Video */}
      <div className="w-1/2 p-6">
        <iframe
          className="rounded-lg shadow-lg w-full h-[70vh]"
          src={`https://www.youtube.com/embed/${video.video_id}`}
          title={video.title}
          allowFullScreen
        />
      </div>

      {/* Right Column: Editable Summary & Shared Transcript */}
      <div className="w-1/2 p-6 flex flex-col gap-6">
        {/* Editable summary for THIS video */}
        <div className="flex-1">
          <h2 className="text-xl font-semibold mb-2">Editable Summary for This Video</h2>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            className="w-full h-40 p-4 border rounded resize-none"
          />
          <button
            onClick={handleGenerateVideo}
            className="mt-4 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          >
            Generate Video
          </button>
        </div>

        {/* Shared Transcript (from all summaries) */}
        <div className="flex-1 overflow-y-auto bg-gray-50 border rounded p-4">
          <h2 className="text-xl font-semibold mb-2">Shared Transcript (from all summaries)</h2>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">
            {combinedTranscript}
          </p>
        </div>
      </div>
    </div>
  );
}
