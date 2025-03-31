import React, { ReactNode } from 'react';

interface SidebarLayoutProps {
  sidebar: ReactNode;
  main: ReactNode;
}

const SidebarLayout: React.FC<SidebarLayoutProps> = ({ sidebar, main }) => {
  return (
    <div className="flex gap-6 px-5 py-8">
      <aside className="w-[280px] shrink-0 rounded bg-[rgba(215,185,133,0.13)] p-6">
        {sidebar}
      </aside>
      <div className="flex-1">{main}</div>
    </div>
  );
};

export default SidebarLayout;
