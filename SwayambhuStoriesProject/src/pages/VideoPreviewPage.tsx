import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReactPlayer from "react-player";
import Header from "../components/Header";

// Dummy video data (in real app, fetch this by ID from backend or context)
const allVideos = Array.from({ length: 12 }).map((_, i) => {
  const duration = Math.floor(Math.random() * 60) + 30;
  return {
    id: (i + 1).toString(),
    title: `Interview Title ${i + 1}`,
    description: `This is a detailed description for video ${i + 1}.`,
    participants: `Participant ${i + 1}`,
    language: i % 2 === 0 ? "NEPALI" : "ENGLISH",
    speaker:
      i % 2 === 0
        ? "Academic"
        : i % 3 === 0
        ? "Community Member"
        : "Religious Leader",
    location:
      i % 4 === 0
        ? "Kathmandu"
        : i % 4 === 1
        ? "Patan"
        : i % 4 === 2
        ? "Bhaktapur"
        : "Other",
    length: `${duration} min`,
    durationInMinutes: duration,
    date: new Date(2023, 0, i + 1),
    categories: [`Category ${(i % 3) + 1}`, `Category ${((i + 1) % 3) + 1}`],
    videoUrl: "https://youtu.be/KgrCYvVYSRE?si=nONhjhLj1YySvVmD",
    captions: [
      { timestamp: "00:00", text: "Introduction to the speaker." },
      { timestamp: "00:45", text: "Discussion of early life." },
      { timestamp: "02:30", text: "Cultural practices in Kathmandu." },
    ],
  };
});

const VideoPreviewPage: React.FC = () => {
  const { videoId } = useParams();
  const navigate = useNavigate();

  const video = allVideos.find((v) => v.id === videoId);

  if (!video) {
    return (
      <div className="p-8">
        <p className="text-red-600">Video not found.</p>
        <button
          onClick={() => navigate(-1)}
          className="mt-4 underline text-blue-600"
        >
          Go Back
        </button>
      </div>
    );
  }

  const formattedDate = video.date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div>
      <Header />
      <div className="mx-auto px-5 py-8 bg-amber-50">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Video and Details Section */}
          <div className="w-full lg:w-2/3">
            <div className="rounded overflow-hidden shadow bg-orange-100 aspect-video">
              <ReactPlayer
                url={video.videoUrl}
                controls
                width="100%"
                height="100%"
              />
            </div>

            <div className="mt-6 space-y-4">
              <h2 className="text-2xl font-semibold text-gray-800">
                {video.title}
              </h2>
              <p className="text-gray-700">{video.description}</p>

              <div className="space-y-4 text-gray-800">
                {/* First row */}
                <div className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
                  <div>
                    <strong>Participants:</strong> {video.participants}
                  </div>
                  <div>
                    <strong>Speaker Type:</strong> {video.speaker}
                  </div>
                  <div>
                    <strong>Language:</strong> {video.language}
                  </div>
                </div>

                {/* Second row */}
                <div className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
                  <div>
                    <strong>Location:</strong> {video.location}
                  </div>
                  <div>
                    <strong>Length:</strong> {video.length}
                  </div>
                  <div>
                    <strong>Date:</strong> {formattedDate}
                  </div>
                </div>

                {/* Categories */}
                <div className="flex flex-wrap gap-2 mt-1">
                  {video.categories.map((cat, idx) => (
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

          {/* Transcript Section */}
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
