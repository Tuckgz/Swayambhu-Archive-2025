import React, { useState } from 'react';
import { FaCog, FaBookmark, FaUserShield } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';  // googleLogout,  - may want to use this
import axios from 'axios';

const UserMenu: React.FC = () => {
  const navigate = useNavigate();
  const [showRequestAccess, setShowRequestAccess] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);
  const username = userName || "Guest";


  const login = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const res = await axios.post('/api/google-auth', {
          token: tokenResponse.access_token,
        });
        const user = res.data.user;

        if (res.data.status === 'approved') {
          setUserName(user?.name || null);
          navigate('/admin');
        } else if (res.data.status === 'pending') {
          setUserName(user?.name || null);
          setShowRequestAccess(true); // show button to confirm
        }
      } catch (err) {
        console.error('Google login failed:', err);
        alert('Unable to log in or you do not have access.');
      }
    },
    onError: (err) => {
      console.error('Login Failed:', err);
    },
  });

  const handleAdminClick = () => {
    login(); 
  };

  const requestAccess = () => {
    alert("Access request already submitted. Awaiting approval.");
    setShowRequestAccess(false);
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
          onClick={handleAdminClick}
        >
          <FaUserShield />
          <span>Admin</span>
        </li>
      </ul>

        {showRequestAccess && (
          <div className="p-2 border-t mt-2 text-center">
            <p className="text-sm text-gray-600">Access request submitted.</p>
            <button
              onClick={requestAccess}
              className="mt-2 bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded text-sm"
            >
              Got it
            </button>
          </div>
        )}
    </div>
  );
};

export default UserMenu;
