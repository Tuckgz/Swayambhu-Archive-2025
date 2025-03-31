import React, { ReactNode } from 'react';

interface MainLayoutProps {
  children: ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen">
      <header className="header">
        <div className="container">
          <h1 className="font-serif">Swayambhu Story Archive</h1>
        </div>
      </header>
      <main className="container">
        {children}
      </main>
    </div>
  );
};

export default MainLayout;