import React, { ReactNode } from 'react';

interface FilterSectionProps {
  title: string;
  children: ReactNode;
}

const FilterSection: React.FC<FilterSectionProps> = ({ title, children }) => {
  return (
    <div className="filter-section">
      <h3 className="filter-title">{title}</h3>
      {children}
    </div>
  );
};

export default FilterSection;