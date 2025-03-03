import mongoose from "mongoose";

const SRTSchema = new mongoose.Schema({
  name: { type: String, required: true },
  content: { type: String, required: true }, 
  date: { type: Date, default: Date.now }
});

const SRTFile = mongoose.model("SRTFile", SRTSchema);
export default SRTFile;
