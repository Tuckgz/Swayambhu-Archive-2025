import mongoose from "mongoose";
import connectDB from "../config/db-connection.js"

await connectDB();

// Define a schema for use in the script (can later import this from a shared model)
const videoSchema = new mongoose.Schema({}, { strict: false });
const Video = mongoose.model("Video", videoSchema, "media_transcripts");

const dummyData = Array.from({ length: 10 }).map((_, i) => ({
  job_id: `video_${i + 1}`,
  title: `Sample Video Title ${i + 1}`,
  participants: `Participant ${i + 1}`,
  speaker: ["Academic", "Community Member", "Religious Leader"][i % 3],
  language: i % 2 === 0 ? "ENGLISH" : "NEPALI",
  location: ["Kathmandu", "Patan", "Bhaktapur"][i % 3],
  type: ["Interview", "Lecture", "Documentary"][i % 3],
  source_location: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  thumbnail_url: "https://img.youtube.com/vi/dQw4w9WgXcQ/0.jpg",
  duration: `${Math.floor(Math.random() * 3) + 2}:00`,
  date: new Date(2023, 0, i + 1),
  categories: ["Culture", "Tradition"],
  transcript_content: {
    english: `This is a dummy transcript for video ${i + 1} that mentions rituals, festivals, and traditions.`,
  },
}));

await Video.deleteMany({});
await Video.insertMany(dummyData);

console.log("✅ Dummy video data seeded!");
process.exit();
