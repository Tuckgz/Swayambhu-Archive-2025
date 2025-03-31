import React, { ReactNode } from 'react';

interface MainLayoutProps {
  children: ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-[rgba(238,196,82,0.07)] text-gray-800">
      <header className="sticky top-0 z-50 h-[60px] bg-yellow-400 shadow-md">
        <div className="mx-auto flex h-full items-center px-8">
          <h1 className="font-serif text-xl font-normal">Swayambhu Story Archive</h1>
        </div>
      </header>
      <main className="mx-auto px-5 py-8">{children}</main>
    </div>
  );
};

export default MainLayout;
