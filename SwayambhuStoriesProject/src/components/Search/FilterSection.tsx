import React, { ReactNode } from 'react';

interface FilterSectionProps {
  title: string;
  children: ReactNode;
}

const FilterSection: React.FC<FilterSectionProps> = ({ title, children }) => {
  return (
    <div className="mb-4">
      <h3 className="mb-2 text-sm font-semibold text-gray-800">{title}</h3>
      {children}
    </div>
  );
};

export default FilterSection;
