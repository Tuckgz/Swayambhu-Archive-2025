import React, { useState } from 'react';
import { FaChevronDown } from 'react-icons/fa';

interface DropdownFilterProps {
  title: string;
  options: string[];
  selected: string[];
  setSelected: React.Dispatch<React.SetStateAction<string[]>>;
}

const DropdownFilter: React.FC<DropdownFilterProps> = ({ title, options }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selected, setSelected] = useState([])

  return (
    <div className="border-b border-[rgba(215,185,133,0.3)] pb-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between py-2 text-left text-gray-800 font-semibold"
      >
        <span>{title}</span>
        <FaChevronDown
          className={`transition-transform duration-200 ${
            isOpen ? 'rotate-180' : 'rotate-0'
          }`}
        />
      </button>

      {isOpen && (
        <div className="mt-2 space-y-2 pl-1">
          {options.map((option, index) => (
            <div key={index} className="flex items-center space-x-2 text-sm text-gray-800">
              <input
                type="checkbox"
                id={`${title}-${index}`}
                className="h-4 w-4 rounded border-gray-300 text-yellow-800 focus:ring-yellow-800"
              />
              <label htmlFor={`${title}-${index}`}>{option}</label>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DropdownFilter;
