// server.js or index.js is similar to main.py in python 
import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import connectDB from "./config/db-connection.js"; 
import uploadFiles from "./utils/upload.js";
import getFile from "./utils/getFile.js";
import deleteFile from "./utils/deleteFile.js";
import searchAll from "./utils/searchAll.js";
import userFile from "./models/userschema.js";

dotenv.config(); 
const app = express();
const PORT = process.env.PORT || 5000;
app.use(express.json());
app.use(cors()); 


const FOLDER_PATH = "../transcripts";
uploadFiles(FOLDER_PATH);


app.use("/api", searchAll);
// http://localhost:5000/api/search?keyword=hello

app.use("/api", getFile); 
// http://localhost:5000/file/example.srt?search=hello - how to request a word within the file with a timestamp
// http://localhost:5000/file/example.srt - how to request the entire file

app.use("/api", deleteFile);



async function createTestUser() {
  const testUser = await userFile.findOne({ email: "test@example.com" });
  if (!testUser) {
    await new userFile({
      googleId: "test-google-id",
      email: "test@example.com",
      name: "Test User",
      role: "admin",
    }).save();
  }
}



connectDB()
  .then(async () => {
    await createTestUser();  // <-- Add call here!
    app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
  })
  .catch((err) => console.error(err));


app.get("/", (req, res) => {
  res.send("Node.js backend is running");
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));





