import React, { useState } from "react";
import SearchFilters from "../components/Search/SearchFilters";
import DropdownFilter from "../components/Search/DropdownFilter";
import VideoCard from "../components/Video/VideoCard";
import { FaFilter } from "react-icons/fa";
import Header from "../components/Header";

const HomePage: React.FC = () => {
  const [searchTerms, setSearchTerms] = useState<string[]>([
    "Rituals",
    "Familial Duties",
  ]);
  const [newTerm, setNewTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const videosPerPage = 5;

  // Filter options
  const languageOptions = ["NEPALI", "ENGLISH"];
  const sourceOptions = ["Interview", "Documentary", "Lecture"];
  const speakerOptions = ["Academic", "Community Member", "Religious Leader"];
  const locationOptions = ["Kathmandu", "Patan", "Bhaktapur", "Other"];

  const handleAddTerm = () => {
    if (newTerm.trim() && !searchTerms.includes(newTerm.trim())) {
      setSearchTerms([...searchTerms, newTerm.trim()]);
      setNewTerm("");
    }
  };

  const handleRemoveTerm = (index: number) => {
    const newTerms = [...searchTerms];
    newTerms.splice(index, 1);
    setSearchTerms(newTerms);
  };

  // Mock video data
  const allVideos = Array.from({ length: 12 }).map((_, i) => ({
    id: i + 1,
    title: `Interview Title ${i + 1}`,
    participants: `Participant ${i + 1}`,
    language: i % 2 === 0 ? "NEPALI" : "ENGLISH",
    length: `${Math.floor(Math.random() * 60) + 30} min`,
    categories: [`Category ${(i % 3) + 1}`, `Category ${((i + 1) % 3) + 1}`],
  }));

  // Pagination logic
  const indexOfLastVideo = currentPage * videosPerPage;
  const indexOfFirstVideo = indexOfLastVideo - videosPerPage;
  const currentVideos = allVideos.slice(indexOfFirstVideo, indexOfLastVideo);
  const totalPages = Math.ceil(allVideos.length / videosPerPage);

  return (
    <div>
      <Header />

      <div className="content-wrapper">
        {/* Search + Filter Area */}
        <div className="search-terms-section">
          {/* Add Term Input */}
          <div className="add-term-row">
            <div className="add-term-input-container">
              <input
                type="text"
                value={newTerm}
                onChange={(e) => setNewTerm(e.target.value)}
                placeholder="Add search term"
                className="add-term-input"
                onKeyPress={(e) => e.key === "Enter" && handleAddTerm()}
              />
              <button className="add-term-button" onClick={handleAddTerm}>
                Add Term
              </button>
            </div>
          </div>

          {/* Added Terms + Filter Button */}
          <div className="search-terms-row">
            <div className="search-terms-container">
              {searchTerms.map((term, index) => (
                <div key={index} className="search-term">
                  {term}
                  <button
                    className="remove-term"
                    onClick={() => handleRemoveTerm(index)}
                  >
                    &times;
                  </button>
                </div>
              ))}
            </div>

            <button className="filter-results-button">
              <FaFilter style={{ marginRight: "8px" }} />
              Filter Results
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="main-content">
          <aside className="sidebar">
            <DropdownFilter title="LANGUAGE" options={languageOptions} />
            <DropdownFilter title="SOURCE TYPE" options={sourceOptions} />
            <DropdownFilter title="SPEAKER TYPE" options={speakerOptions} />
            <DropdownFilter title="LOCATION" options={locationOptions} />
          </aside>

          <div className="video-list">
            {currentVideos.map((video) => (
              <VideoCard
                key={video.id}
                title={video.title}
                participants={video.participants}
                language={video.language}
                length={video.length}
                categories={video.categories}
              />
            ))}

            {totalPages > 1 && (
              <div className="pagination">
                {Array.from({ length: totalPages }).map((_, index) => (
                  <button
                    key={index}
                    className={`page-button ${
                      currentPage === index + 1 ? "active" : ""
                    }`}
                    onClick={() => setCurrentPage(index + 1)}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
