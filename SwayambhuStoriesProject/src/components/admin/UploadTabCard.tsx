// src/components/admin/UploadTabCard.tsx
import React, { useState, ChangeEvent, FormEvent } from "react";

// Helper to truncate text to a given length.
const truncateText = (text: string, length: number = 50): string =>
  text.length <= length ? text : text.substring(0, length) + "...";

type UploadMode = "url" | "file";

// Set the base URL for the API.
const API_URL = "https://swayambhu-archive-2025.onrender.com";
// const API_URL = "http://localhost:5000";

const UploadTabCard: React.FC = () => {
  const [uploadMode, setUploadMode] = useState<UploadMode>("url");
  const [urlInput, setUrlInput] = useState<string>("");
  const [fileInput, setFileInput] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [bannerMessage, setBannerMessage] = useState<string>("");

  // Reset inputs to empty values.
  const resetForm = () => {
    setUrlInput("");
    setFileInput(null);
  };

  // When switching mode, clear the non-active field.
  const handleModeChange = (mode: UploadMode) => {
    setUploadMode(mode);
    if (mode === "url") {
      setFileInput(null);
    } else {
      setUrlInput("");
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFileInput(e.target.files[0]);
    }
  };

  const handleUrlChange = (e: ChangeEvent<HTMLInputElement>) => {
    setUrlInput(e.target.value);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setBannerMessage("");

    try {
      let response;
      if (uploadMode === "url") {
        if (!urlInput) {
          setBannerMessage("Please provide a URL.");
          setLoading(false);
          return;
        }
        response = await fetch(`${API_URL}/api/generate-transcription`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_type: "youtube",
            source: urlInput,
          }),
        });
      } else {
        if (!fileInput) {
          setBannerMessage("Please select an MP4 file.");
          setLoading(false);
          return;
        }
        const formData = new FormData();
        formData.append("source_type", "mp4");
        formData.append("source", fileInput);
        response = await fetch(`${API_URL}/api/generate-transcription`, {
          method: "POST",
          body: formData,
        });
      }

      // Read the response text and parse JSON only if it is not empty.
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};

      if (!response.ok) {
        setBannerMessage(`Error: ${data.error || "Upload failed"}`);
        setLoading(false);
        return;
      }

      // Assume the backend returns an object with:
      // { filename, transcript_en, transcript_ne, ... }
      const filename = data.filename || "unknown filename";
      const transcriptEn = data.transcript_en || "";
      const transcriptNe = data.transcript_ne || "";

      const banner = `File "${filename}" successfully uploaded. EN: ${truncateText(
        transcriptEn,
        50
      )} | NE: ${truncateText(transcriptNe, 50)}`;
      setBannerMessage(banner);

      // Reset input fields.
      resetForm();
    } catch (error) {
      setBannerMessage("An error occurred during upload.");
      console.error("Upload error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 border rounded shadow space-y-4">
      <h2 className="text-xl font-bold">Upload</h2>
      <div className="flex items-center space-x-4">
        <label className="flex items-center">
          <input
            type="radio"
            value="url"
            checked={uploadMode === "url"}
            onChange={() => handleModeChange("url")}
          />
          <span className="ml-2">Upload via URL</span>
        </label>
        <label className="flex items-center">
          <input
            type="radio"
            value="file"
            checked={uploadMode === "file"}
            onChange={() => handleModeChange("file")}
          />
          <span className="ml-2">Upload File</span>
        </label>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block font-semibold mb-1">YouTube URL</label>
          <input
            type="text"
            value={urlInput}
            onChange={handleUrlChange}
            disabled={uploadMode !== "url"}
            className={`w-full border px-2 py-1 rounded ${
              uploadMode !== "url" ? "bg-gray-100" : ""
            }`}
            placeholder="Enter video URL"
          />
        </div>
        <div>
          <label className="block font-semibold mb-1">MP4 File</label>
          <input
            type="file"
            onChange={handleFileChange}
            disabled={uploadMode !== "file"}
            className={`w-full ${uploadMode !== "file" ? "bg-gray-100" : ""}`}
            accept="video/mp4"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className={`px-4 py-2 rounded bg-blue-500 text-white ${
            loading ? "opacity-50 cursor-not-allowed" : "hover:bg-blue-600"
          }`}
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>

      {bannerMessage && (
        <div className="mt-4 p-2 bg-green-200 text-green-800 rounded">
          {bannerMessage}
        </div>
      )}
    </div>
  );
};

export default UploadTabCard;
