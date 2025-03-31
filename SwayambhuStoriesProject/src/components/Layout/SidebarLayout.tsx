import React, { ReactNode } from 'react';

interface SidebarLayoutProps {
  sidebar: ReactNode;
  main: ReactNode;
}

const SidebarLayout: React.FC<SidebarLayoutProps> = ({ sidebar, main }) => {
  return (
    <div className="flex-container">
      <aside className="sidebar">
        {sidebar}
      </aside>
      <div className="main-content">
        {main}
      </div>
    </div>
  );
};

export default SidebarLayout;