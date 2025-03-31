import React from 'react';
import { FaUserCircle } from 'react-icons/fa';
import logoImage from '../assets/templeIcon.png';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-container">
        <div className="logo-container">
        <img src={logoImage} alt="Story Archive Logo" className="logo" />
        <h1 className="site-title font-serif">Swayambhu Story Archive</h1>
        </div>
        <div className="account-icon">
          <FaUserCircle />
        </div>
      </div>
    </header>
  );
};

export default Header;