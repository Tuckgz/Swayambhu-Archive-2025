import React from "react";
import { useNavigate } from "react-router-dom";

interface VideoCardProps {
  id: string;
  title: string;
  participants: string;
  language: string;
  length: string;
  categories: string[];
  speaker: string;
  date: string | Date;
  thumbnailUrl?: string;
}

const VideoCard: React.FC<VideoCardProps> = ({
  id,
  title,
  participants,
  language,
  length,
  categories,
  speaker,
  date,
  thumbnailUrl,
}) => {
  const navigate = useNavigate();

  const formattedDate = new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  const handleClick = () => {
    navigate(`/video/${id}`);
  };

  return (
    <button
      onClick={handleClick}
      className="w-full text-left mb-6 flex gap-4 rounded p-4 shadow-sm hover:shadow-md transition-shadow duration-200 bg-orange-100 focus:outline-none"
    >
      {/* Thumbnail Placeholder */}
      <div className="w-32 h-32 bg-gray-300 rounded overflow-hidden">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt="Thumbnail"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-sm text-gray-600">
            No Thumbnail
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col justify-between">
        <h3 className="text-lg font-semibold text-gray-800">{title}</h3>

        <div className="mt-2 flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-700">
          <p>
            <strong>Participants:</strong> {participants}
          </p>
          <p>
            <strong>Language:</strong> {language}
          </p>
          <p>
            <strong>Speaker:</strong> {speaker}
          </p>
        </div>

        <div className="mt-1 flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-700">
          <p>
            <strong>Length:</strong> {length}
          </p>
          <p>
            <strong>Date:</strong> {formattedDate}
          </p>
        </div>

        <div className="mt-2 flex flex-wrap gap-2">
          {categories.map((cat, index) => (
            <span
              key={index}
              className="rounded bg-[rgba(215,185,133,0.3)] px-2 py-1 text-xs text-gray-800"
            >
              {cat}
            </span>
          ))}
        </div>
      </div>
    </button>
  );
};

export default VideoCard;
