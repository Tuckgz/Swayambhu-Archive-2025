import mongoose from "mongoose";
import connectDB from "../config/db-connection.js";
import dotenv from "dotenv";
dotenv.config();

await connectDB(); // this must connect to transcript_db

// Define schema and explicitly bind to correct collection
const videoSchema = new mongoose.Schema({}, { strict: false });
const Video = mongoose.model("Video", videoSchema, "media_transcripts");

const getYouTubeId = (url) => {
  const match = url?.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/);
  return match ? match[1] : null;
};

const updateExistingDocuments = async () => {
  const videos = await Video.find();

  for (const video of videos) {
    const updated = {};

    if (!video.title) updated.title = "Untitled Video";
    if (!video.participants) updated.participants = "Unknown Participant";
    if (!video.speaker) updated.speaker = "Unknown";
    if (!video.language) updated.language = video.detected_language || "Unknown";
    if (!video.location) updated.location = "Kathmandu";
    if (!video.type) updated.type = "Interview";

    if (!video.thumbnail_url && video.source_location) {
      const ytId = getYouTubeId(video.source_location);
      if (ytId) updated.thumbnail_url = `https://img.youtube.com/vi/${ytId}/0.jpg`;
    }

    if (!video.duration) updated.duration = "3:00";
    if (!video.date) updated.date = new Date("2023-01-01");
    if (!video.categories || video.categories.length === 0)
      updated.categories = ["General"];

    if (Object.keys(updated).length > 0) {
      await Video.updateOne({ _id: video._id }, { $set: updated });
      console.log(`✅ Updated: ${video.job_id || video._id}`);
    }
  }

  console.log("✅ All updates complete.");
  process.exit();
};

updateExistingDocuments();
