import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import VideoPreviewPage from "./pages/VideoPreviewPage";

const App = () => (
  <Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/video/:videoId" element={<VideoPreviewPage />} />
  </Routes>
);

export default App;
