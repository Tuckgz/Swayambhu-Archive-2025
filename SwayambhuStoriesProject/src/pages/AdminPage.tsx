// src/pages/AdminPage.tsx
import React, { useState } from "react";
import "../styles/styles.css"; // Ensure you import the CSS file
import Header from "../components/Header";
import UploadTabCard from "../components/admin/UploadTabCard";
import ManageContentCard from "../components/admin/ManageContentCard";
import SecurityAndPermissionsCard from "../components/admin/SecurityAndPermissionsCard";
import ManageAdmins from "../components/admin/ManageAdmins";

const AdminPage: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState<
    "upload" | "manageContent" | "manual entry" | "permissions"
  >("upload");

  const renderContent = () => {
    switch (selectedTab) {
      case "upload":
        return <UploadTabCard />;
      case "manageContent":
        return <ManageContentCard />;
      case "manual entry":
        return <SecurityAndPermissionsCard />;
      case "permissions":
        return <ManageAdmins/>;
      default:
        return null;
    }
  };

  return (
    // Use the admin-bg class for background tint from your theme
    <div className="relative min-h-screen admin-bg">
      <Header onUserIconClick={() => {}} />

      <div className="flex">
        {/* Sidebar uses the theme's secondary color with slight opacity */}
        <aside className="w-64 admin-sidebar-bg p-4">
          <ul className="space-y-2">
            <li>
              <button
                onClick={() => setSelectedTab("upload")}
                className={`w-full text-left p-2 rounded hover:bg-[var(--primary-color)] hover:text-[#2c3e50] ${
                  selectedTab === "upload"
                    ? "bg-[var(--primary-color)] text-[#2c3e50]"
                    : "bg-white text-gray-800"
                }`}
              >
                Upload
              </button>
            </li>
            <li>
              <button
                onClick={() => setSelectedTab("manageContent")}
                className={`w-full text-left p-2 rounded hover:bg-[var(--primary-color)] hover:text-[#2c3e50] ${
                  selectedTab === "manageContent"
                    ? "bg-[var(--primary-color)] text-[#2c3e50]"
                    : "bg-white text-gray-800"
                }`}
              >
                Manage Content
              </button>
            </li>
            <li>
              <button
                onClick={() => setSelectedTab("manual entry")}
                className={`w-full text-left p-2 rounded hover:bg-[var(--primary-color)] hover:text-[#2c3e50] ${
                  selectedTab === "manual entry"
                    ? "bg-[var(--primary-color)] text-[#2c3e50]"
                    : "bg-white text-gray-800"
                }`}
              >
                Manual Entry
              </button>
            </li>
            <li>
              <button
                onClick={() => setSelectedTab("permissions")}
                className={`w-full text-left p-2 rounded hover:bg-[var(--primary-color)] hover:text-[#2c3e50] ${
                  selectedTab === "permissions"
                    ? "bg-[var(--primary-color)] text-[#2c3e50]"
                    : "bg-white text-gray-800"
                }`}
              >
                Permissions
              </button>
            </li>
          </ul>
        </aside>

        {/* Main content area background updated to white for differentiation */}
        <main className="flex-1 p-6 bg-white rounded shadow-sm">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default AdminPage;
