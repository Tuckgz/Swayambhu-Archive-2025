import React from 'react';

interface CheckboxFilterProps {
  label: string;
  name: string;
  checked?: boolean;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const CheckboxFilter: React.FC<CheckboxFilterProps> = ({ 
  label, 
  name, 
  checked = false,
  onChange 
}) => {
  return (
    <div className="checkbox-filter">
      <input
        type="checkbox"
        id={name}
        name={name}
        checked={checked}
        onChange={onChange}
        className="filter-checkbox"
      />
      <label htmlFor={name} className="filter-label">
        {label}
      </label>
    </div>
  );
};

export default CheckboxFilter;