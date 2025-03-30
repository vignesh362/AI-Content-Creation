import { Home, Video, PlayCircle } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;
  
  return (
    <nav className="bg-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex space-x-8">
            <Link
              to="/"
              className={`inline-flex items-center px-3 py-2 text-sm font-medium ${
                isActive('/') 
                  ? 'text-blue-600 border-b-2 border-blue-600' 
                  : 'text-gray-500 hover:text-blue-600'
              }`}
            >
              <Home className="w-5 h-5 mr-2" />
              Home
            </Link>
            
            <Link
              to="/content"
              className={`inline-flex items-center px-3 py-2 text-sm font-medium ${
                isActive('/content')
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-blue-600'
              }`}
            >
              <Video className="w-5 h-5 mr-2" />
              Content Generation
            </Link>
            
            <Link
              to="/playback"
              className={`inline-flex items-center px-3 py-2 text-sm font-medium ${
                isActive('/playback')
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-blue-600'
              }`}
            >
              <PlayCircle className="w-5 h-5 mr-2" />
              Video Playback
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}