import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactPlayer from "react-player";
import Header from "../components/Header";

const VideoPreviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { videoId } = useParams();

  // Placeholder data (update with a real YouTube link)
  const video = {
    title: "Sample Interview Title",
    description: "This is a detailed description of the interview video.",
    category: ["Category 1", "Category 2"],
    language: "Nepali",
    length: "45 min",
    participants: "Participant Name",
    videoUrl: "https://youtu.be/irlGOL63iX8?si=WTXJ_g0M88kO4dbU", // Example YouTube link
    captions: [
      { timestamp: "00:00", text: "Introduction to the speaker." },
      { timestamp: "00:45", text: "Discussion of early life." },
      { timestamp: "02:30", text: "Cultural practices in Kathmandu." },
    ],
  };

  return (
    <div>
      <Header />
      <div className="mx-auto px-5 py-8 bg-amber-50">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Video and Details Section */}
          <div className="w-full lg:w-2/3">
            <div className="rounded overflow-hidden shadow bg-orange-100 aspect-video">
              <ReactPlayer
                url={video.videoUrl.replace(
                  "youtube.com",
                  "youtube-nocookie.com"
                )}
                controls
                width="100%"
                height="100%"
                config={{
                  youtube: {
                    playerVars: {
                      modestbranding: 1,
                      rel: 0,
                      showinfo: 0,
                      disablekb: 1,
                    },
                    embedOptions: {
                      sandbox:
                        "allow-same-origin allow-scripts allow-presentation", // restricts navigation
                    },
                  },
                }}
                onContextMenu={(e) => e.preventDefault()} // disable right-click context menu
              />
            </div>

            {/* Video Details (Below the Video) */}
            <div className="mt-6 space-y-4">
              <h2 className="text-2xl font-semibold text-gray-800">
                {video.title}
              </h2>
              <p className="text-gray-700">{video.description}</p>

              <div className="flex flex-col gap-2">
                <div>
                  <strong className="font-medium text-gray-800">
                    Language:
                  </strong>{" "}
                  {video.language}
                </div>
                <div>
                  <strong className="font-medium text-gray-800">Length:</strong>{" "}
                  {video.length}
                </div>
                <div>
                  <strong className="font-medium text-gray-800">
                    Participants:
                  </strong>{" "}
                  {video.participants}
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {video.category.map((cat, idx) => (
                    <span
                      key={idx}
                      className="rounded bg-[rgba(215,185,133,0.3)] px-2 py-1 text-xs text-gray-800"
                    >
                      {cat}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Transcript Section (Captions) */}
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">
              Transcript
            </h3>
            <div className="space-y-2">
              {video.captions.map((cap, idx) => (
                <div key={idx} className="text-sm text-gray-700">
                  <span className="font-medium text-gray-900">
                    [{cap.timestamp}]
                  </span>{" "}
                  {cap.text}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPreviewPage;
