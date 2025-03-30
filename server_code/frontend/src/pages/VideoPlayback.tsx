import { Video } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import React from 'react';
interface PlaybackState {
  content: string;
  sourceVideo: {
    id: string;
    title: string;
  };
  contentSource: 'youtube' | 'edited' | 'ai';
}

export default function VideoPlayback() {
  const location = useLocation();
  const playbackState = location.state as PlaybackState;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center mb-6">
          {playbackState ? (
            <div className="w-full h-full bg-black rounded-lg flex items-center justify-center">
              {/* TODO: Replace with actual video player */}
              <div className="text-center text-white">
                <Video className="w-16 h-16 mx-auto mb-4" />
                <p>Generated video is being processed...</p>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500">
              <Video className="w-16 h-16 mx-auto mb-4" />
              <p>No video selected for playback</p>
            </div>
          )}
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Video Details</h2>
          {playbackState ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-medium text-gray-700">Source</h3>
                <p className="text-gray-600">
                  {playbackState.sourceVideo?.title || 'Custom Generated Content'}
                </p>
              </div>
              <div>
                <h3 className="font-medium text-gray-700">Content Type</h3>
                <p className="text-gray-600 capitalize">{playbackState.contentSource}</p>
              </div>
              <div>
                <h3 className="font-medium text-gray-700">Content Preview</h3>
                <p className="text-gray-600 line-clamp-3">{playbackState.content}</p>
              </div>
            </div>
          ) : (
            <p className="text-gray-600">
              No video content available. Please generate a video from the content generation page.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}