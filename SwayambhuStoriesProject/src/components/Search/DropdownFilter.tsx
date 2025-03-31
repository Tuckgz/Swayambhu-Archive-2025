import React, { useState } from 'react';
import { FaChevronDown } from 'react-icons/fa';

interface DropdownFilterProps {
  title: string;
  options: string[];
}

const DropdownFilter: React.FC<DropdownFilterProps> = ({ title, options }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="filter-dropdown">
      <div className="dropdown-header" onClick={() => setIsOpen(!isOpen)}>
        <span className="dropdown-title">{title}</span>
        <FaChevronDown className={`chevron ${isOpen ? 'up' : 'down'}`} />
      </div>
      <div className={`dropdown-content ${isOpen ? 'show' : ''}`}>
        {options.map((option, index) => (
          <div key={index} className="dropdown-option">
            <input type="checkbox" id={`${title}-${index}`} />
            <label htmlFor={`${title}-${index}`}>{option}</label>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DropdownFilter;