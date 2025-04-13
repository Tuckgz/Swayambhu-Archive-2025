import { useState } from "react";
import axios from "axios";
import "./Search.css";

const Search = () => {
  const [searchTerms, setSearchTerms] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [results, setResults] = useState<
    { file: string; timestamp: string; text: string }[]
  >([]);
  const [error, setError] = useState<string | null>(null);

  const addSearchTerm = () => {
    if (input.trim() && !searchTerms.includes(input.trim())) {
      setSearchTerms([...searchTerms, input.trim()]);
      setInput("");
    }
  };

  const removeSearchTerm = (term: string) => {
    setSearchTerms(searchTerms.filter((t) => t !== term));
  };

  const search = async () => {
    if (searchTerms.length === 0) {
      setError("Please enter at least one search term.");
      return;
    }

    try {
      setError(null);
      const response = await axios.post("http://localhost:6080/search", {
        terms: searchTerms,
      });
      setResults(response.data);
    } catch (error) {
      setError("Error searching. Please try again.");
      console.error("Search error:", error);
    }
  };

  const resetSearch = () => {
    setSearchTerms([]);
    setResults([]);
    setInput("");
    setError(null);
  };

  return (
    <div className="page-container">
      <div className="search-container">
        <h2 className="search-title">Search SRT Transcripts</h2>

        <div className="search-input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter search term"
            className="search-input"
          />
          <button onClick={addSearchTerm} className="add-button">
            Add
          </button>
        </div>

        <div className="search-terms">
          {searchTerms.map((term) => (
            <span
              key={term}
              className="search-term"
              onClick={() => removeSearchTerm(term)}
            >
              {term} ✕
            </span>
          ))}
        </div>

        <button onClick={search} className="search-button">
          Search
        </button>

        <button onClick={resetSearch} className="reset-button">
          Reset
        </button>

        {error && <p className="error-message">{error}</p>}

        <div className="results-container">
          <h3>Results:</h3>
          {results.length > 0 ? (
            results.map((result, index) => (
              <div key={index} className="result-item">
                <strong>{result.file}</strong> ({result.timestamp})
                <p>{result.text}</p>
              </div>
            ))
          ) : (
            <p>No results found.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Search;
