import mongoose from "mongoose";


// using mongoose to create a schema for the srt or vtt files in mongodb
const subtitleFileSchema = new mongoose.Schema({
  name: { type: String, required: true },
  content: { type: String, required: true }, 
  date: { type: Date, default: Date.now }
});


// allows for mongoDB indexing making our database wide word search queries faster
subtitleFileSchema.index({ content: "text" })


//connection point, will create one if one does not exist
const subtitleFile = mongoose.model("SRTFile", subtitleFileSchema);
export default subtitleFile;
