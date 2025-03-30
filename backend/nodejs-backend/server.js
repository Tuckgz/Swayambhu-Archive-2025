// server.js or index.js is similar to main.py in python 
import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import connectDB from "./config/db-connection.js"; 
import uploadFiles from "./utils/upload.js";
import getFile from "./utils/getFile.js";
import deleteFile from "./utils/deleteFile.js"

dotenv.config(); 
const app = express();
const PORT = process.env.PORT || 5000;
app.use(express.json());
app.use(cors()); 

connectDB();

const FOLDER_PATH = "../transcripts";
uploadFiles(FOLDER_PATH);

app.use("/file", getFile);
app.use("/file", deleteFile);

app.get("/", (req, res) => {
  res.send("Node.js backend is running");
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));





