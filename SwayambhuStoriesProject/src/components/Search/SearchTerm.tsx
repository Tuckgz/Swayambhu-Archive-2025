import React from 'react';

interface SearchTermProps {
  term: string;
  onRemove: () => void;
}

const SearchTerm: React.FC<SearchTermProps> = ({ term, onRemove }) => {
  return (
    <div className="search-term">
      {term}
      <button 
        className="remove-term"
        onClick={onRemove}
        aria-label={`Remove ${term}`}
      >
        &times;
      </button>
    </div>
  );
};

export default SearchTerm;