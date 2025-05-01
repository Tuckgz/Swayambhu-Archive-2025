import React, { useEffect, useState, useCallback, useMemo } from "react";
import DropdownFilter from "../components/Search/DropdownFilter";
import VideoCard from "../components/Video/VideoCard";
import { FaFilter } from "react-icons/fa";
import Header from "../components/Header";
import UserMenu from "../components/UserMenu";

const HomePage: React.FC = () => {

  const [searchTerms, setSearchTerms] = useState<string[]>([]);
  const [newTerm, setNewTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [videos, setVideos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const videosPerPage = 5;


  const toggleUserMenu = () => {
    setUserMenuOpen((prev) => !prev);
  };
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [selectedSpeakers, setSelectedSpeakers] = useState<string[]>([]);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);

  const languageOptions = ["nepali", "english"];
  const sourceOptions = ["Interview", "Documentary", "Lecture"];
  const speakerOptions = ["Academic", "Community Member", "Religious Leader"];
  const locationOptions = ["Kathmandu", "Patan", "Bhaktapur", "Other"];

  const [sortOption, setSortOption] = useState<string>("");
  const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);

  const fetchVideos = useCallback(async (terms: string[]) => {
    if (terms.length === 0) {
      setVideos([]);
      return;
    }
    setLoading(true);
    try {
      const response = await fetch("http://localhost:5003/api/videos/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ terms }),
      });
      const data = await response.json();
      setVideos(data);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleAddTerm = () => {
    const term = newTerm.trim();
    if (term && !searchTerms.includes(term)) {
      const updatedTerms = [...searchTerms, term];
      setSearchTerms(updatedTerms);
      setNewTerm("");
      fetchVideos(updatedTerms);
    }
  };


  const handleRemoveTerm = (index: number) => {
    const newTerms = [...searchTerms];
    newTerms.splice(index, 1);
    setSearchTerms(newTerms);
    fetchVideos(newTerms);
  };


  useEffect(() => {
    fetchVideos(searchTerms);
  }, [searchTerms, fetchVideos]);

  const filteredAndSortedVideos = useMemo(() => {
    const filtered = videos.filter((video) => {
      const transcriptLanguages = video.transcript_content
        ? Object.keys(video.transcript_content).flatMap((lang) => {
            if (["en", "english"].includes(lang.toLowerCase()))
              return "english";
            if (["ne", "nepali"].includes(lang.toLowerCase())) return "nepali";
            return lang.toLowerCase();
          })
        : [];

      const matchesLanguage =
        selectedLanguages.length === 0 ||
        selectedLanguages.some((lang) => transcriptLanguages.includes(lang));

      const matchesSource =
        selectedSources.length === 0 || selectedSources.includes(video.type);
      const matchesSpeaker =
        selectedSpeakers.length === 0 ||
        selectedSpeakers.includes(video.speaker);
      const matchesLocation =
        selectedLocations.length === 0 ||
        selectedLocations.includes(video.location);

      return (
        matchesLanguage && matchesSource && matchesSpeaker && matchesLocation
      );
    });

    if (sortOption === "duration-asc") {
      return filtered.sort(
        (a, b) => parseDuration(a.duration) - parseDuration(b.duration)
      );
    } else if (sortOption === "duration-desc") {
      return filtered.sort(
        (a, b) => parseDuration(b.duration) - parseDuration(a.duration)
      );
    } else if (sortOption === "date-newest") {
      return filtered.sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
      );
    } else if (sortOption === "date-oldest") {
      return filtered.sort(
        (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
      );
    }

    return filtered;
  }, [
    videos,
    selectedLanguages,
    selectedSources,
    selectedSpeakers,
    selectedLocations,
    sortOption,
  ]);

  const indexOfLastVideo = currentPage * videosPerPage;
  const indexOfFirstVideo = indexOfLastVideo - videosPerPage;
  const currentVideos = filteredAndSortedVideos.slice(
    indexOfFirstVideo,
    indexOfLastVideo
  );
  const totalPages = Math.ceil(filteredAndSortedVideos.length / videosPerPage);

  function parseDuration(duration: string): number {
    if (!duration) return 0;
    const parts = duration.split(":");
    const minutes = parseInt(parts[0]) || 0;
    const seconds = parseInt(parts[1]) || 0;
    return minutes * 60 + seconds;
  }

  return (

    <div className="relative">
      {/* Pass the toggle callback to Header */}
      <Header onUserIconClick={toggleUserMenu} />
      
      {/* Conditionally render the UserMenu */}
      {userMenuOpen && <UserMenu />}

      <div className="mx-auto px-5 py-8 bg-amber-50">
        {/* Search input and buttons */}
        <div className="mb-8 w-full">
          <div className="flex w-full gap-4 mb-4">
            <input
              type="text"
              value={newTerm}
              onChange={(e) => setNewTerm(e.target.value)}
              placeholder="Add search term"
              className="w-full rounded border border-yellow-800 bg-orange-100 px-4 py-2 placeholder:text-gray-700 focus:outline-none"
              onKeyPress={(e) => e.key === "Enter" && newTerm.trim() && setSearchTerms([...searchTerms, newTerm.trim()])}
            />
            <button
              className="w-50 rounded border border-yellow-900 bg-yellow-800 px-4 py-2 text-gray-800 hover:bg-yellow-700"
              onClick={() => newTerm.trim() && setSearchTerms([...searchTerms, newTerm.trim()])}
            >
              Add Term
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-between">
            <div className="flex flex-wrap gap-2">
              {searchTerms.map((term, index) => (
                <span
                  key={index}
                  className="flex items-center rounded-full bg-orange-100 px-3 py-1 text-sm text-gray-800"
                >
                  {term}
                  <button
                    className="ml-2 text-lg font-bold text-gray-800 hover:text-red-500"
                    onClick={() => {
                      const newTerms = [...searchTerms];
                      newTerms.splice(index, 1);
                      setSearchTerms(newTerms);
                    }}
                  >
                    &times;
                  </button>
                </span>
              ))}
            </div>

            <div className="relative mt-4 md:mt-0">
              <button
                onClick={() => setIsSortMenuOpen(!isSortMenuOpen)}
                className="flex items-center justify-center gap-2 rounded bg-blue-100 px-4 py-2 text-gray-800 hover:bg-blue-200"
              >
                <FaFilter /> Filter Results
              </button>

              {isSortMenuOpen && (
                <div className="absolute right-0 z-10 mt-2 w-64 rounded border bg-white shadow-lg">
                  <ul className="text-sm text-gray-800">
                    <li>
                      <button
                        onClick={() => setSortOption("duration-asc")}
                        className="w-full px-4 py-2 text-left hover:bg-blue-100"
                      >
                        Duration: Shortest to Longest
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => setSortOption("duration-desc")}
                        className="w-full px-4 py-2 text-left hover:bg-blue-100"
                      >
                        Duration: Longest to Shortest
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => setSortOption("date-newest")}
                        className="w-full px-4 py-2 text-left hover:bg-blue-100"
                      >
                        Date: Newest First
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => setSortOption("date-oldest")}
                        className="w-full px-4 py-2 text-left hover:bg-blue-100"
                      >
                        Date: Oldest First
                      </button>
                    </li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Rest of your page content */}
        <div className="flex gap-6">
          <aside className="w-[280px] shrink-0 rounded bg-transparent p-0">
            <div className="space-y-4 rounded bg-[rgba(215,185,133,0.13)] p-6">

              <DropdownFilter
                title="LANGUAGE"
                options={languageOptions}
                selected={selectedLanguages}
                setSelected={setSelectedLanguages}
              />
              <DropdownFilter
                title="SOURCE TYPE"
                options={sourceOptions}
                selected={selectedSources}
                setSelected={setSelectedSources}
              />
              <DropdownFilter
                title="SPEAKER TYPE"
                options={speakerOptions}
                selected={selectedSpeakers}
                setSelected={setSelectedSpeakers}
              />
              <DropdownFilter
                title="LOCATION"
                options={locationOptions}
                selected={selectedLocations}
                setSelected={setSelectedLocations}
              />
            </div>
          </aside>

          <div className="flex-1">
            {loading ? (
              <p className="text-gray-700">Searching...</p>
            ) : searchTerms.length === 0 ? (
              <div className="text-center text-gray-600 mt-8">
                <p className="text-lg font-medium">
                  🔍 Let's find something fascinating.
                </p>
                <p className="text-sm">
                  Add a search term above to begin your journey through the
                  archive!
                </p>
              </div>
            ) : currentVideos.length > 0 ? (
              currentVideos.map((video) => (
                <VideoCard
                  key={video._id}
                  id={video._id}
                  title={video.title}
                  participants={video.participants || "Unknown"}
                  language={video.language || "N/A"}
                  length={video.duration || "0:00"}
                  categories={video.categories || []}
                  speaker={video.speaker || "Unknown"}
                  date={video.date || ""}
                  thumbnailUrl={video.thumbnail_url || ""}
                />
              ))
            ) : (
              <p className="text-gray-700">
                No videos match the search criteria.
              </p>
            )}

            {totalPages > 1 && (
              <div className="mt-8 flex justify-center gap-2">
                {Array.from({ length: totalPages }).map((_, index) => (
                  <button
                    key={index}
                    className={`rounded border border-yellow-800 px-3 py-1 text-gray-800 hover:bg-yellow-300 ${
                      currentPage === index + 1
                        ? "bg-yellow-800 text-white"
                        : "bg-orange-100"
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
