// src/components/admin/SecurityAndPermissionsCard.tsx
import React, { useState } from "react";

const SecurityAndPermissionsCard: React.FC = () => {
  const [addData, setAddData] = useState({
    filename: "",
    date_added: "",
    date_recorded: "",
    language: "",
    transcript_en: "",
    transcript_ne: "",
    url: "",
    location: "",
    speaker: "",
    type: "",
    keywords: ""
  });
  
  const [removeId, setRemoveId] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // Handle changes for the add form inputs.
  const handleAddChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAddData({
      ...addData,
      [e.target.name]: e.target.value
    });
  };

  // POST to the /api/add endpoint.
  const handleAddSubmit = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(addData)
      });
      const data = await response.json();
      console.log("Added document:", data);
    } catch (error) {
      console.error("Error adding document:", error);
    }
  };

  // DELETE to the /api/remove/:id endpoint.
  const handleRemoveSubmit = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/remove/${removeId}`, {
        method: "DELETE"
      });
      const data = await response.json();
      console.log("Removed document:", data);
    } catch (error) {
      console.error("Error removing document:", error);
    }
  };

  // GET request to the /api/search endpoint.
  const handleSearchSubmit = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/search?keyword=${searchKeyword}`);
      const data = await response.json();
      console.log("Search results:", data);
      setSearchResults(data);
    } catch (error) {
      console.error("Error searching documents:", error);
    }
  };

  return (
    <div className="p-4 border rounded shadow">
      <h2 className="text-xl font-bold mb-2">Security & Permissions</h2>
      <p>This is a placeholder for security and permissions settings.</p>

      {/* Section to add a document */}
      <div className="mt-4">
        <h3 className="font-semibold">Add Document</h3>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="text"
            name="filename"
            placeholder="Filename"
            value={addData.filename}
            onChange={handleAddChange}
            className="border p-1"
          />
          <input
            type="text"
            name="date_added"
            placeholder="Date Added"
            value={addData.date_added}
            onChange={handleAddChange}
            className="border p-1"
          />
          <input
            type="text"
            name="date_recorded"
            placeholder="Date Recorded"
            value={addData.date_recorded}
            onChange={handleAddChange}
            className="border p-1"
          />
          <input
            type="text"
            name="language"
            placeholder="Language"
            value={addData.language}
            onChange={handleAddChange}
            className="border p-1"
          />
          <input
            type="text"
            name="transcript_en"
            placeholder="Transcript (EN)"
            value={addData.transcript_en}
            onChange={handleAddChange}
            className="border p-1 col-span-2"
          />
          <input
            type="text"
            name="transcript_ne"
            placeholder="Transcript (NE)"
            value={addData.transcript_ne}
            onChange={handleAddChange}
            className="border p-1 col-span-2"
          />
          <input
            type="text"
            name="url"
            placeholder="URL"
            value={addData.url}
            onChange={handleAddChange}
            className="border p-1 col-span-2"
          />
          <input
            type="text"
            name="location"
            placeholder="Location"
            value={addData.location}
            onChange={handleAddChange}
            className="border p-1"
          />
          <input
            type="text"
            name="speaker"
            placeholder="Speaker"
            value={addData.speaker}
            onChange={handleAddChange}
            className="border p-1"
          />
          <input
            type="text"
            name="type"
            placeholder="Type"
            value={addData.type}
            onChange={handleAddChange}
            className="border p-1"
          />
          <input
            type="text"
            name="keywords"
            placeholder="Keywords (comma separated)"
            value={addData.keywords}
            onChange={handleAddChange}
            className="border p-1 col-span-2"
          />
        </div>
        <button
          onClick={handleAddSubmit}
          className="mt-2 bg-blue-500 text-white px-2 py-1 rounded"
        >
          Add Document
        </button>
      </div>

      {/* Section to remove a document */}
      <div className="mt-6">
        <h3 className="font-semibold">Remove Document</h3>
        <input
          type="text"
          placeholder="Document ID"
          value={removeId}
          onChange={(e) => setRemoveId(e.target.value)}
          className="border p-1"
        />
        <button
          onClick={handleRemoveSubmit}
          className="ml-2 bg-red-500 text-white px-2 py-1 rounded"
        >
          Remove Document
        </button>
      </div>

      {/* Section to search for documents */}
      <div className="mt-6">
        <h3 className="font-semibold">Search Documents</h3>
        <input
          type="text"
          placeholder="Keyword"
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          className="border p-1"
        />
        <button
          onClick={handleSearchSubmit}
          className="ml-2 bg-green-500 text-white px-2 py-1 rounded"
        >
          Search
        </button>
      </div>

      {/* Display search results (for testing purposes) */}
      <div className="mt-6">
        <h3 className="font-semibold">Search Results</h3>
        <pre className="bg-gray-100 p-2 rounded max-h-60 overflow-auto">
          {JSON.stringify(searchResults, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default SecurityAndPermissionsCard;
