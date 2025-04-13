import React, { useState } from "react";
import SearchTerm from "./SearchTerm";

interface SearchFiltersProps {
  terms: string[];
  onAddTerm: (term: string) => void;
  onRemoveTerm: (index: number) => void;
}

const SearchFilters: React.FC<SearchFiltersProps> = ({
  terms,
  onAddTerm,
  onRemoveTerm,
}) => {
  const [newTerm, setNewTerm] = useState("");

  const handleAddTerm = () => {
    if (newTerm.trim()) {
      onAddTerm(newTerm.trim());
      setNewTerm("");
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Add Term Input Row */}
      <div className="flex w-full max-w-3xl gap-4">
        <input
          type="text"
          value={newTerm}
          onChange={(e) => setNewTerm(e.target.value)}
          placeholder="Add search term"
          className="flex-grow rounded border border-yellow-800 bg-orange-100 px-4 py-2 placeholder:text-gray-700 focus:outline-none"
          onKeyPress={(e) => e.key === "Enter" && handleAddTerm()}
        />
        <button
          className="w-40 rounded bg-yellow-800 px-4 py-2 text-gray-100 hover:bg-yellow-700"
          onClick={handleAddTerm}
        >
          Add Term
        </button>
      </div>

      {/* Display Search Terms */}
      <div className="flex flex-wrap gap-2">
        {terms.map((term, index) => (
          <SearchTerm key={index} term={term} onRemove={() => onRemoveTerm(index)} />
        ))}
      </div>
    </div>
  );
};

export default SearchFilters;
