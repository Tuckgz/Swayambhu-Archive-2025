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
  categories = ["Category 1", "Category 2"],
}) => {
  return (
    <div className="mb-6 flex rounded bg-[rgba(215,185,133,0.13)] shadow-sm transition hover:shadow-md">
      <div className="h-40 w-60 flex-shrink-0 bg-[rgba(215,185,133,0.3)]" />
      <div className="flex flex-col justify-between p-6">
        <div>
          <h3 className="mb-1 text-lg font-semibold text-gray-800">{title}</h3>
          <p className="mb-3 text-sm text-gray-700 opacity-80">{participants}</p>
          <div className="mb-3 flex gap-6 text-xs text-gray-700 opacity-80">
            <span>{language}</span>
            <span>{length}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {categories.map((category, index) => (
            <span
              key={index}
              className="rounded bg-[rgba(215,185,133,0.3)] px-2 py-1 text-xs text-gray-800"
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
