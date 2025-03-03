import mongoose from "mongoose";


// using mongoose to create a schema for the srt files in mongodb
const SRTSchema = new mongoose.Schema({
  name: { type: String, required: true },
  content: { type: String, required: true }, 
  date: { type: Date, default: Date.now }
});

//connection point, will create one if one does not exist
const SRTFile = mongoose.model("SRTFile", SRTSchema);
export default SRTFile;
