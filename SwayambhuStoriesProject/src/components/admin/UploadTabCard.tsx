// src/components/admin/UploadTabCard.tsx
import React, { useState, ChangeEvent, FormEvent } from "react";

// Helper to truncate text to a given length.
const truncateText = (text: string, length: number = 50): string =>
  text.length <= length ? text : text.substring(0, length) + "...";

type UploadMode = "url" | "file";

// Set the base URL for the API.
// const API_URL = "https://swayambhu-archive-2025.onrender.com";
const API_URL = "http://localhost:5000";

const UploadTabCard: React.FC = () => {
  const [uploadMode, setUploadMode] = useState<UploadMode>("url");
  const [urlInput, setUrlInput] = useState<string>("");
  const [fileInput, setFileInput] = useState<File | null>(null);
  // --- Added State for Metadata Checkbox ---
  const [generateMetadata, setGenerateMetadata] = useState<boolean>(false); // Default to false
  // --- End Added State ---
  const [loading, setLoading] = useState<boolean>(false);
  const [bannerMessage, setBannerMessage] = useState<string>("");

  // Reset inputs to empty values.
  const resetForm = () => {
    setUrlInput("");
    setFileInput(null);
    // Optionally reset the checkbox too, or keep its state
    // setGenerateMetadata(false);
  };

  // When switching mode, clear the non-active field.
  const handleModeChange = (mode: UploadMode) => {
    setUploadMode(mode);
    if (mode === "url") {
      setFileInput(null); // Clear file input when switching to URL
    } else {
      setUrlInput(""); // Clear URL input when switching to file
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFileInput(e.target.files[0]);
    } else {
      setFileInput(null); // Ensure state is null if no file is selected
    }
  };

  const handleUrlChange = (e: ChangeEvent<HTMLInputElement>) => {
    setUrlInput(e.target.value);
  };

  // --- Added Handler for Metadata Checkbox ---
  const handleMetadataChange = (e: ChangeEvent<HTMLInputElement>) => {
    setGenerateMetadata(e.target.checked);
  };
  // --- End Added Handler ---

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
        // --- Modified API Call for URL ---
        response = await fetch(`${API_URL}/api/generate-transcription`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_type: "youtube", // Assuming 'youtube' for URL mode
            source: urlInput, // The URL itself
            generate_metadata: generateMetadata, // Include checkbox value
          }),
        });
        // --- End Modified API Call ---
      } else { // uploadMode === "file"
        if (!fileInput) {
          setBannerMessage("Please select an MP4 file.");
          setLoading(false);
          return;
        }
        // --- Modified API Call for File ---
        const formData = new FormData();
        formData.append("source_type", "mp4"); // Assuming 'mp4' for file mode
        formData.append("source", fileInput); // The file itself
        // Send boolean as string 'true' or 'false' for FormData
        formData.append("generate_metadata", String(generateMetadata));
        response = await fetch(`${API_URL}/api/generate-transcription`, {
          method: "POST",
          body: formData, // No 'Content-Type' header needed, browser sets it for FormData
        });
        // --- End Modified API Call ---
      }

      const text = await response.text();
      const data = text ? JSON.parse(text) : {};

      if (!response.ok) {
        // Use error message from backend if available, otherwise a default
        setBannerMessage(`Error: ${data.error || response.statusText || "Upload failed"}`);
        setLoading(false);
        return;
      }

      // Display success message with truncated transcripts
      const filename = data.filename || (uploadMode === 'file' ? fileInput?.name : urlInput) || "your file/URL";
      const transcriptEn = data.transcript_en || "";
      const transcriptNe = data.transcript_ne || "";

      const banner = `"${truncateText(filename, 30)}" processed. EN: ${truncateText(
        transcriptEn,
        30
      )} | NE: ${truncateText(transcriptNe, 30)}`;
      setBannerMessage(banner);

      resetForm(); // Reset form fields on success

    } catch (error) {
      // Handle network errors or issues parsing JSON
      setBannerMessage("An error occurred during the request.");
      console.error("Upload error:", error);
    } finally {
      setLoading(false); // Ensure loading state is always reset
    }
  };

  return (
    <div className="p-4 border rounded shadow-md space-y-4 bg-white"> {/* Added shadow and bg */}
      <h2 className="text-xl font-semibold text-gray-700">Upload & Transcribe</h2> {/* Adjusted heading */}
      <div className="flex items-center space-x-4 border-b pb-3 mb-3"> {/* Added border bottom */}
        <label className="flex items-center cursor-pointer">
          <input
            type="radio"
            name="uploadMode" // Added name for grouping
            value="url"
            checked={uploadMode === "url"}
            onChange={() => handleModeChange("url")}
            className="form-radio h-4 w-4 text-blue-600" // Tailwind styling
          />
          <span className="ml-2 text-gray-700">Upload via URL</span>
        </label>
        <label className="flex items-center cursor-pointer">
          <input
            type="radio"
            name="uploadMode" // Added name for grouping
            value="file"
            checked={uploadMode === "file"}
            onChange={() => handleModeChange("file")}
            className="form-radio h-4 w-4 text-blue-600" // Tailwind styling
          />
          <span className="ml-2 text-gray-700">Upload MP4 File</span>
        </label>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* URL Input Section */}
        <div className={uploadMode === "url" ? "" : "hidden"}> {/* Show/hide based on mode */}
          <label htmlFor="urlInput" className="block font-medium text-sm text-gray-600 mb-1"> {/* Adjusted label style */}
            YouTube URL
          </label>
          <input
            id="urlInput"
            type="url" // Changed type to 'url' for better semantics/validation
            value={urlInput}
            onChange={handleUrlChange}
            disabled={uploadMode !== "url" || loading} // Disable when loading too
            className={`w-full border border-gray-300 px-3 py-2 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm ${
              uploadMode !== "url" ? "bg-gray-100 cursor-not-allowed" : ""
            }`}
            placeholder="https://www.youtube.com/watch?v=..."
          />
        </div>

        {/* File Input Section */}
        <div className={uploadMode === "file" ? "" : "hidden"}> {/* Show/hide based on mode */}
          <label htmlFor="fileInput" className="block font-medium text-sm text-gray-600 mb-1"> {/* Adjusted label style */}
            MP4 File
          </label>
          <input
            id="fileInput"
            type="file"
            onChange={handleFileChange}
            disabled={uploadMode !== "file" || loading} // Disable when loading too
            className={`w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 ${
               uploadMode !== "file" ? "opacity-50 cursor-not-allowed" : "cursor-pointer"
            }`}
            accept=".mp4,video/mp4" // More specific accept attribute
            // Use a key to force re-render and allow selecting the same file after reset
            key={fileInput ? fileInput.name : 'file-input'}
          />
           {fileInput && <span className="text-xs text-gray-500 mt-1 block">Selected: {truncateText(fileInput.name, 40)}</span>}
        </div>

        {/* --- Added Metadata Checkbox Input --- */}
        <div className="flex items-center pt-2">
          <input
            id="generateMetadataCheckbox"
            type="checkbox"
            checked={generateMetadata}
            onChange={handleMetadataChange}
            disabled={loading} // Disable when loading
            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
          />
          <label htmlFor="generateMetadataCheckbox" className="ml-2 block text-sm text-gray-700 cursor-pointer">
            Generate metadata during transcription
          </label>
        </div>
        {/* --- End Added Checkbox Input --- */}

        <button
          type="submit"
          disabled={loading || (uploadMode === 'url' && !urlInput) || (uploadMode === 'file' && !fileInput)} // Disable if no input or loading
          className={`w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </>
          ) : "Upload & Transcribe"}
        </button>
      </form>

      {/* Banner Message Area */}
      {bannerMessage && (
        <div className={`mt-4 p-3 rounded-md text-sm ${bannerMessage.startsWith("Error:") ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
          {bannerMessage}
        </div>
      )}
    </div>
  );
};

export default UploadTabCard;