import React from 'react';

interface SearchTermProps {
  term: string;
  onRemove: () => void;
}

const SearchTerm: React.FC<SearchTermProps> = ({ term, onRemove }) => {
  return (
    <span className="flex items-center rounded-full bg-orange-100 px-3 py-1 text-sm text-gray-800">
      {term}
      <button
        className="ml-2 text-lg font-bold text-gray-800 hover:text-red-500"
        onClick={onRemove}
        aria-label={`Remove ${term}`}
      >
        &times;
      </button>
    </span>
  );
};

export default SearchTerm;
