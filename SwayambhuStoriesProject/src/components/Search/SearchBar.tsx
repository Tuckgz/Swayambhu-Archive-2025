import React from 'react';

interface SearchBarProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSearch: () => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ value, onChange, onSearch }) => {
  return (
    <div className="search-area">
      <div className="container">
        <div className="search-container">
          <input
            type="text"
            value={value}
            onChange={onChange}
            placeholder="Enter keywords to filter your search"
            className="search-input"
            onKeyPress={(e) => e.key === 'Enter' && onSearch()}
          />
          <button className="search-button" onClick={onSearch}>
            Search
          </button>
        </div>
        
      </div>
    </div>
  );
};

export default SearchBar;