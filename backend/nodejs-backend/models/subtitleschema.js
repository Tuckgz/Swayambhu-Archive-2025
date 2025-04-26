import mongoose from "mongoose";

const subtitleFileSchema = new mongoose.Schema({
  title: { type: String, required: true },           
  filename: { type: String, required: true },        
  transcripts : {
    en: {type: String, required: true},
    en: { type: String, default: ""}
  },
  language: { type: String, default: "English" },    
  url: { type: String, default: "" },              
  speaker_name: { type: [String], default: [] },    
  keywords: { type: [String], default: [] },         
  date_recorded: { type: Date, default: null },      
  date_added: { type: Date, default: Date.now }     
});

subtitleFileSchema.index({ content: "text" })


const subtitleFile = mongoose.model("SRTFile", subtitleFileSchema);
export default subtitleFile;
