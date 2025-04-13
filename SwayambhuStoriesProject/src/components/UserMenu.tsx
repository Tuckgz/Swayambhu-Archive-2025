// src/components/UserMenu.tsx
import React from 'react';
import { FaCog, FaBookmark, FaUserShield } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

const UserMenu: React.FC = () => {
  const navigate = useNavigate();
  const username = "PlaceholderUser";

  const goToAdmin = () => {
    navigate('/admin');
  };

  return (
    <div className="absolute right-8 mt-2 w-48 rounded bg-white shadow-lg z-50">
      <div className="p-4 border-b">
        <span className="font-bold">{username}</span>
      </div>
      <ul>
        <li className="flex items-center gap-2 p-2 hover:bg-gray-100 cursor-pointer">
          <FaCog />
          <span>Settings</span>
        </li>
        <li className="flex items-center gap-2 p-2 hover:bg-gray-100 cursor-pointer">
          <FaBookmark />
          <span>Bookmarks</span>
        </li>
        <li
          className="flex items-center gap-2 p-2 hover:bg-gray-100 cursor-pointer"
          onClick={goToAdmin}
        >
          <FaUserShield />
          <span>Admin</span>
        </li>
      </ul>
    </div>
  );
};

export default UserMenu;
