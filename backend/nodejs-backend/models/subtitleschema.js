import mongoose from "mongoose";

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


// transcripts: {
//   en: { type: String, required: true },               
//   ne: { type: String, default: "" },                 
  
// },

subtitleFileSchema.index({ content: "text" })


const subtitleFile = mongoose.model("SRTFile", subtitleFileSchema);
export default subtitleFile;
