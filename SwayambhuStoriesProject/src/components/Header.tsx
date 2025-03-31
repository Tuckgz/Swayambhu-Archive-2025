import React from 'react';
import { FaUserCircle } from 'react-icons/fa';
import logoImage from '../assets/templeIcon.png';

const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 h-[60px] bg-yellow-400 shadow-md">
      <div className="flex h-full items-center justify-between px-8">
        <div className="flex items-center gap-4">
          <img
            src={logoImage}
            alt="Story Archive Logo"
            className="h-10 w-auto object-contain"
          />
          <h1 className="m-0 font-serif text-xl font-normal text-gray-800">
            Swayambhu Story Archive
          </h1>
        </div>
        <div className="text-2xl text-gray-800 cursor-pointer">
          <FaUserCircle />
        </div>
      </div>
    </header>
  );
};

export default Header;
