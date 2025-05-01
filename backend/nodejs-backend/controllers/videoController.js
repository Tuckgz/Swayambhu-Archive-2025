import mongoose from "mongoose";
import connectDB from "../config/db-connection.js";

await connectDB();

const videoSchema = new mongoose.Schema({}, { strict: false });
const Video = mongoose.model("Video", videoSchema, "media_transcripts");

// EXAMPLE:
// GET http://localhost:5000/api/videos
export const getAllVideos = async (req, res) => {
  try {
    const videos = await Video.find().sort({ date: -1 });
    res.json(videos);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

//EXAMPLE: 
// GET http://localhost:5000/api/videos/<video_id> *** REMOVE <> ***
// 

export const getVideoById = async (req, res) => {
  try {
    const { id } = req.params;

    let video;
    if (mongoose.Types.ObjectId.isValid(id)) {
      video = await Video.findById(id);
    }

    // Fallback: also check if it's a job_id (string-based ID)
    if (!video) {
      video = await Video.findOne({ job_id: id });
    }

    if (!video) {
      return res.status(404).json({ message: "Video not found" });
    }

    res.json(video);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

export const searchVideos = async (req, res) => {
  try {
    const { terms } = req.body;

    if (!Array.isArray(terms) || terms.length === 0) {
      return res.status(400).json({ message: "Search terms must be a non-empty array" });
    }

    const languageFields = [
      "transcript_content.en",
      "transcript_content.english",
      "transcript_content.ne",
    ];

    // Create a list of { field: { $regex: word boundary } } queries
    const orQueries = [];

    for (const term of terms) {
      const boundarySafe = `\\b${term}\\b`;
      const regex = new RegExp(boundarySafe, "i");

      for (const field of languageFields) {
        orQueries.push({ [field]: regex });
      }
    }

    const videos = await Video.find({ $or: orQueries });

    res.json(videos);
  } catch (err) {
    console.error("Search failed:", err);
    res.status(500).json({ error: err.message });
  }
};


