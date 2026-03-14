import React from 'react';
import { Play } from 'lucide-react';

function VideoRecommendations({ videos }) {
  if (!videos || videos.length === 0) {
    return (
      <div className="text-[var(--text-muted)] italic text-sm">
        No specific video recommendations available at this time.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {videos.map((vid, idx) => (
        <a
          key={idx}
          href={vid.url}
          target="_blank"
          rel="noopener noreferrer"
          className="card overflow-hidden group hover:-translate-y-1 transition-transform duration-200 block"
        >
          <div className="relative aspect-video bg-gray-900 border-b border-[var(--border)]">
            <img 
              src={vid.thumbnail} 
              alt={vid.title} 
              className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
            />
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 group-hover:bg-black/20 transition-colors">
              <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center shadow-lg shadow-red-900/50 group-hover:scale-110 transition-transform">
                <Play className="text-white ml-1 w-6 h-6" />
              </div>
            </div>
            <div className="absolute top-2 right-2 bg-indigo-600/90 backdrop-blur text-white text-[0.65rem] uppercase font-bold px-2 py-1 rounded">
              {vid.concept}
            </div>
          </div>
          <div className="p-4">
            <h4 className="text-sm font-semibold text-[var(--text-primary)] line-clamp-2 leading-tight mb-1 group-hover:text-indigo-400 transition-colors">
              {vid.title}
            </h4>
            <span className="text-xs text-[var(--text-secondary)]">
              {vid.channel}
            </span>
          </div>
        </a>
      ))}
    </div>
  );
}

export default VideoRecommendations;
