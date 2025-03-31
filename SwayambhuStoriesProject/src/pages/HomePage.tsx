import React, { useState } from "react";
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

  const allVideos = Array.from({ length: 12 }).map((_, i) => ({
    id: i + 1,
    title: `Interview Title ${i + 1}`,
    participants: `Participant ${i + 1}`,
    language: i % 2 === 0 ? "NEPALI" : "ENGLISH",
    length: `${Math.floor(Math.random() * 60) + 30} min`,
    categories: [`Category ${(i % 3) + 1}`, `Category ${((i + 1) % 3) + 1}`],
  }));

  const indexOfLastVideo = currentPage * videosPerPage;
  const indexOfFirstVideo = indexOfLastVideo - videosPerPage;
  const currentVideos = allVideos.slice(indexOfFirstVideo, indexOfLastVideo);
  const totalPages = Math.ceil(allVideos.length / videosPerPage);

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

            <button className="mt-4 flex items-center justify-center gap-2 rounded bg-blue-100 px-4 py-2 text-gray-800 hover:bg-blue-200 md:mt-0">
              <FaFilter /> Filter Results
            </button>
          </div>
        </div>

        <div className="flex gap-6">
          <aside className="w-[280px] shrink-0 rounded bg-transparent p-0">
            <div className="space-y-4 rounded bg-[rgba(215,185,133,0.13)] p-6">
              <DropdownFilter title="LANGUAGE" options={languageOptions} />
              <DropdownFilter title="SOURCE TYPE" options={sourceOptions} />
              <DropdownFilter title="SPEAKER TYPE" options={speakerOptions} />
              <DropdownFilter title="LOCATION" options={locationOptions} />
            </div>
          </aside>

          <div className="flex-1">
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
              <div className="mt-8 flex justify-center gap-2">
                {Array.from({ length: totalPages }).map((_, index) => (
                  <button
                    key={index}
                    className={`rounded border border-yellow-800 px-3 py-1 text-gray-800 hover:bg-yellow-300 ${
                      currentPage === index + 1 ? "bg-yellow-800 text-white" : "bg-orange-100"
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
