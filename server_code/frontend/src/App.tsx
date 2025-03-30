import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import ContentGeneration from './pages/ContentGeneration';
import VideoPlayback from './pages/VideoPlayback';
import React from 'react';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/content" element={<ContentGeneration />} />
            <Route path="/playback" element={<VideoPlayback />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;