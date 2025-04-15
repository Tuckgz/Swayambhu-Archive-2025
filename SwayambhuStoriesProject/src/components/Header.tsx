// src/components/Header.tsx
import React from 'react';
import { FaUserCircle, FaArrowLeft } from 'react-icons/fa';
import logoImage from '../assets/templeIcon.png';
import { useLocation, useNavigate } from 'react-router-dom';

type HeaderProps = {
  onUserIconClick: () => void;
};

const Header: React.FC<HeaderProps> = ({ onUserIconClick }) => {
  const location = useLocation();
  const navigate = useNavigate();

  // Check if the current path starts with '/admin'
  const isAdmin = location.pathname.startsWith('/admin');

  // Handler for back button that navigates back to the main page
  const handleBackClick = () => {
    navigate('/');
  };

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
          {isAdmin ? (
            // Show back arrow icon button for admin page
            <button onClick={handleBackClick}>
              <FaArrowLeft />
            </button>
          ) : (
            // Show user icon button for main page
            <div onClick={onUserIconClick}>
              <FaUserCircle />
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
