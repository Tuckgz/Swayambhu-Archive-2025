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
    <div className="container">
      <div className="add-term-container">
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
      <div className="search-terms-container">
        {terms.map((term, index) => (
          <SearchTerm
            key={index}
            term={term}
            onRemove={() => onRemoveTerm(index)}
          />
        ))}
      </div>
    </div>
  );
};

export default SearchFilters;
