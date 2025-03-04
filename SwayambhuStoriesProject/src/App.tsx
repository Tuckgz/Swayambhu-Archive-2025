import { useState } from "react";
import "./App.css";
import templeIcon from "./assets/templeIcon.png";
import Search from "./Search";

function HomePage() {
  return (
    <>
      <div className="titleBar">
        <img src={templeIcon} alt="Temple Icon" className="icon" />
        <h2>Swayambhu Story Archive</h2>
      </div>

      <div>
        <Search />
      </div>
    </>
  );
}

export default HomePage;
