//model to represent expected document form for a video and associated data
const mongoose = require("mongoose");

const videoSchema = new mongoose.Schema({
  job_id: String,
  title: String,
  participants: String,
  speaker: String,
  language: String,
  location: String,
  type: String, // e.g., Interview, Lecture
  source_location: String,
  thumbnail_url: String,
  duration: String,
  date: Date,
  categories: [String],
  transcript_content: mongoose.Schema.Types.Mixed,
});

module.exports = mongoose.model("Video", videoSchema, "media_transcripts");
