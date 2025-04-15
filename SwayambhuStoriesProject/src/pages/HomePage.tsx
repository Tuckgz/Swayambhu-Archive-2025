import React, { useMemo, useState } from "react";
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

  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [selectedSpeakers, setSelectedSpeakers] = useState<string[]>([]);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);

  const languageOptions = ["NEPALI", "ENGLISH"];
  const sourceOptions = ["Interview", "Documentary", "Lecture"];
  const speakerOptions = ["Academic", "Community Member", "Religious Leader"];
  const locationOptions = ["Kathmandu", "Patan", "Bhaktapur", "Other"];

  const [sortOption, setSortOption] = useState<string>(""); // "", "duration-asc", "duration-desc", etc.
  const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);

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

  const allVideos = useMemo(() => {
    return Array.from({ length: 12 }).map((_, i) => {
      const duration = Math.floor(Math.random() * 60) + 30;
      return {
        id: i + 1,
        title: `Interview Title ${i + 1}`,
        participants: `Participant ${i + 1}`,
        language: i % 2 === 0 ? "NEPALI" : "ENGLISH",
        source:
          i % 3 === 0 ? "Interview" : i % 3 === 1 ? "Documentary" : "Lecture",
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
        categories: [
          `Category ${(i % 3) + 1}`,
          `Category ${((i + 1) % 3) + 1}`,
        ],
      };
    });
  }, []);

  const filteredVideos = allVideos.filter((video) => {
    const matchesLanguage =
      selectedLanguages.length === 0 ||
      selectedLanguages.includes(video.language);
    const matchesSource =
      selectedSources.length === 0 || selectedSources.includes(video.source);
    const matchesSpeaker =
      selectedSpeakers.length === 0 || selectedSpeakers.includes(video.speaker);
    const matchesLocation =
      selectedLocations.length === 0 ||
      selectedLocations.includes(video.location);

    return (
      matchesLanguage && matchesSource && matchesSpeaker && matchesLocation
    );
  });

  let sortedVideos = [...filteredVideos];

  if (sortOption === "duration-asc") {
    sortedVideos.sort((a, b) => a.durationInMinutes - b.durationInMinutes);
  } else if (sortOption === "duration-desc") {
    sortedVideos.sort((a, b) => b.durationInMinutes - a.durationInMinutes);
  } else if (sortOption === "date-newest") {
    sortedVideos.sort((a, b) => b.date.getTime() - a.date.getTime());
  } else if (sortOption === "date-oldest") {
    sortedVideos.sort((a, b) => a.date.getTime() - b.date.getTime());
  }

  const indexOfLastVideo = currentPage * videosPerPage;
  const indexOfFirstVideo = indexOfLastVideo - videosPerPage;
  const currentVideos = sortedVideos.slice(indexOfFirstVideo, indexOfLastVideo);
  const totalPages = Math.ceil(sortedVideos.length / videosPerPage);

  return (
    <div>
      <Header />
      <div className="mx-auto px-5 py-8 bg-amber-50">
        <div className="mb-8 w-full">
          <div className="flex w-full gap-4 mb-4">
            <input
              type="text"
              value={newTerm}
              onChange={(e) => setNewTerm(e.target.value)}
              placeholder="Add search term"
              className="w-full rounded border border-yellow-800 bg-orange-100 px-4 py-2 placeholder:text-gray-700 focus:outline-none"
              onKeyPress={(e) => e.key === "Enter" && handleAddTerm()}
            />
            <button
              className="w-50 rounded border border-yellow-900 bg-yellow-800 px-4 py-2 text-gray-800 hover:bg-yellow-700"
              onClick={handleAddTerm}
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
                    onClick={() => handleRemoveTerm(index)}
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
            {currentVideos.map((video) => (
              <VideoCard
                key={video.id}
                id={video.id}
                title={video.title}
                participants={video.participants}
                language={video.language}
                length={video.length}
                categories={video.categories}
                speaker={video.speaker}
                date={video.date}
              />
            ))}

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
