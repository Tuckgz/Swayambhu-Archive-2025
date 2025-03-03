// server.js or index.js is similar to main.py in python 
import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import connectDB from "./config/db-connection.js"; 

dotenv.config(); 
const app = express();
const PORT = process.env.PORT || 5000;
app.use(express.json());
app.use(cors()); 

connectDB();


app.get("/", (req, res) => {
  res.send("Node.js backend is running");
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));



