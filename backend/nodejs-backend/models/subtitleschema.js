import mongoose from "mongoose";


// using mongoose to create a schema for the srt or vtt files in mongodb
const subtitleFileSchema = new mongoose.Schema({
  title: { type: String, required: true },           // filename without extension
  filename: { type: String, required: true },        // full filename with extension
  transcript_en: { type: String, required: true },  
  transcript_ne: { type: String, default: "" },      
  language: { type: String, default: "English" },    
  url: { type: String, default: "" },              
  speaker_name: { type: [String], default: [] },    
  keywords: { type: [String], default: [] },         
  date_recorded: { type: Date, default: null },      
  date_added: { type: Date, default: Date.now }     
});

// allows for mongoDB indexing making our database wide word search queries faster
subtitleFileSchema.index({ content: "text" })


//connection point, will create one if one does not exist
const subtitleFile = mongoose.model("SRTFile", subtitleFileSchema);
export default subtitleFile;
