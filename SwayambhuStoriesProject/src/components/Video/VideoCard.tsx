import React from "react";
import { useNavigate } from "react-router-dom";

interface VideoCardProps {
  id: number;
  title: string;
  participants: string;
  language: string;
  length: string;
  categories: string[];
}

const VideoCard: React.FC<VideoCardProps> = ({
  id,
  title,
  participants,
  language,
  length,
  categories,
}) => {
  const navigate = useNavigate();

  return (
    <div
      className="mb-4 cursor-pointer rounded border border-yellow-800 bg-orange-100 p-4 hover:bg-yellow-200"
      onClick={() => navigate(`/video/${id}`)}
    >
      <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
      <p className="text-sm text-gray-700">Participants: {participants}</p>
      <p className="text-sm text-gray-700">Language: {language}</p>
      <p className="text-sm text-gray-700">Length: {length}</p>
      <div className="mt-2 flex flex-wrap gap-2">
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
  );
};

export default VideoCard;
