import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReactPlayer from "react-player";
import Header from "../components/Header";

const VideoPreviewPage: React.FC = () => {
  const { videoId } = useParams();
  const navigate = useNavigate();
  const [video, setVideo] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLang, setSelectedLang] = useState<string>("");

  useEffect(() => {
    const fetchVideo = async () => {
      try {
        const response = await fetch(`http://localhost:5003/api/videos/${videoId}`);
        if (!response.ok) throw new Error("Video not found");
        const data = await response.json();
        setVideo(data);

        const langs = data.transcript_content ? Object.keys(data.transcript_content) : [];
        if (langs.length > 0) setSelectedLang(langs[0]);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchVideo();
  }, [videoId]);

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  if (error || !video) {
    return (
      <div className="p-8">
        <p className="text-red-600">{error || "Video not found."}</p>
        <button
          onClick={() => navigate(-1)}
          className="mt-4 underline text-blue-600"
        >
          Go Back
        </button>
      </div>
    );
  }

  const formattedDate = new Date(video.date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  const availableLanguages = video.transcript_content ? Object.keys(video.transcript_content) : [];
  const transcriptText =
    (video.transcript_content && video.transcript_content[selectedLang]) || "";

  return (
    <div>
      <Header />
      <div className="mx-auto px-5 py-8 bg-amber-50">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Video and Details Section */}
          <div className="w-full lg:w-2/3">
            <div className="rounded overflow-hidden shadow bg-orange-100 aspect-video">
              <ReactPlayer
                url={video.source_location}
                controls
                width="100%"
                height="100%"
              />
            </div>

            <div className="mt-6 space-y-4">
              <h2 className="text-2xl font-semibold text-gray-800">
                {video.title}
              </h2>
              <p className="text-gray-700">{video.description || "No description available."}</p>

              <div className="space-y-4 text-gray-800">
                <div className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
                  <div><strong>Participants:</strong> {video.participants}</div>
                  <div><strong>Speaker Type:</strong> {video.speaker}</div>
                  <div><strong>Language:</strong> {video.language}</div>
                </div>

                <div className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
                  <div><strong>Location:</strong> {video.location}</div>
                  <div><strong>Length:</strong> {video.duration}</div>
                  <div><strong>Date:</strong> {formattedDate}</div>
                </div>

                <div className="flex flex-wrap gap-2 mt-1">
                  {(video.categories || []).map((cat: string, idx: number) => (
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
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800">Transcript</h3>
              <select
                value={selectedLang}
                onChange={(e) => setSelectedLang(e.target.value)}
                className="rounded border border-gray-300 bg-white px-2 py-1 text-sm text-gray-800"
              >
                {availableLanguages.map((lang) => (
                  <option key={lang} value={lang}>
                    {lang.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            <div className="h-[400px] overflow-y-auto pr-2 space-y-2">
              {transcriptText ? (
                transcriptText
                  .split("\n")
                  .filter(
                    (line: string) =>
                      line &&
                      !line.startsWith("WEBVTT") &&
                      !line.includes("-->") &&
                      isNaN(Number(line))
                  )
                  .map((line: string, idx: number) => (
                    <div key={idx} className="text-sm text-gray-700">
                      {line}
                    </div>
                  ))
              ) : (
                <p>No transcript available.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPreviewPage;