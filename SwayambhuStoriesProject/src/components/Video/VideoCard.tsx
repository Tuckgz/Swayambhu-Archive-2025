import React from 'react';

interface VideoCardProps {
  title?: string;
  participants?: string;
  language?: string;
  length?: string;
  categories?: string[];
}

const VideoCard: React.FC<VideoCardProps> = ({ 
  title = "TITLE OF THE INTERVIEW", 
  participants = "PARTICIPANT(S) NAME",
  language = "LANGUAGE",
  length = "LENGTH",
  categories = ["Category 1", "Category 2"]
}) => {
  return (
    <div className="video-card">
      <div className="video-thumbnail"></div>
      <div className="video-content">
        <h3 className="video-title">{title}</h3>
        <p className="video-participants">{participants}</p>
        <div className="video-meta">
          <span>{language}</span>
          <span>{length}</span>
        </div>
        <div className="video-categories">
          {categories.map((category, index) => (
            <span 
              key={index}
              className="category-tag"
            >
              {category}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default VideoCard;