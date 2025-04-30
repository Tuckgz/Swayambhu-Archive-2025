// src/components/UserMenu.tsx
import React from 'react';
import {  FaUserShield } from 'react-icons/fa'; // FaCog, FaBookmark,
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';


const UserMenu: React.FC = () => {
  const { loginWithRedirect, isAuthenticated, logout, user, isLoading } = useAuth0();
  const navigate = useNavigate();
  //const username = "PlaceholderUser";

  const handleAdminClick = () => {
    loginWithRedirect({
      appState: { targetUrl: '/admin' }, // After login, send them to /admin page
      connection: "google-oauth2",        // Optional: force only Google Sign-in
    });
  };

  const handleLogout = () => {
    logout({ logoutParams: { returnTo: window.location.origin } });
  };

  // const goToAdmin = () => {
  //   navigate('/admin');
  // };

  return (
    <div className="absolute right-8 mt-2 w-48 rounded bg-white shadow-lg z-50">
      <ul>
        {!isLoading && !isAuthenticated && (
          <li
            className="flex items-center gap-2 p-2 hover:bg-gray-100 cursor-pointer"
            onClick={handleAdminClick}
          >
            <FaUserShield />
            <span>Sign in as Admin</span>
          </li>
        )}

        {!isLoading && isAuthenticated && (
          <>
            <li className="flex items-center gap-2 p-2">
              Welcome, {user?.name}
            </li>
            <li
              className="flex items-center gap-2 p-2 hover:bg-gray-100 cursor-pointer"
              onClick={() => navigate('/admin')}
            >
              <FaUserShield />
              <span>Go to Admin Dashboard</span>
            </li>
            <li
              className="flex items-center gap-2 p-2 hover:bg-gray-100 cursor-pointer"
              onClick={handleLogout}
            >
              Logout
            </li>
          </>
        )}
      </ul>
    </div>
  );
};

export default UserMenu;
