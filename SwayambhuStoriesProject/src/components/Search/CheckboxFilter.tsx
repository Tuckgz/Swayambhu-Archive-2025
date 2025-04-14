import React from 'react';

interface CheckboxFilterProps {
  label: string;
  name: string;
  isChecked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const CheckboxFilter: React.FC<CheckboxFilterProps> = ({
  label,
  name,
  isChecked,
  onChange,
}) => {
  return (
    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id={name}
        name={name}
        checked={isChecked}
        onChange={onChange}
        className="h-4 w-4 rounded border-gray-300 text-yellow-800 focus:ring-yellow-800"
      />
      <label htmlFor={name} className="text-sm text-gray-800">
        {label}
      </label>
    </div>
  );
};

export default CheckboxFilter;
