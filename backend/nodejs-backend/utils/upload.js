import { promises as fs } from "fs";
import path from "path";
import subtitleFile from "../models/subtitleschema.js"; 

const uploadFiles = async (Path) => {
  try {
    const files = await fs.readdir(Path);

    for (const file of files) {
      const ext = path.extname(file);
      if (ext !== ".srt" && ext !== ".vtt") continue;

      const filePath = path.join(Path, file);
      const content = await fs.readFile(filePath, "utf8");

      const existingFile = await subtitleFile.findOne({ filename: file });
      if (existingFile) {
        // console.log(`File '${file}' is already in database.`);
        continue;
      }

      const newFile = new subtitleFile({
        title: path.parse(file).name,      // filename without extension
        filename: file,                    // full file name with extension
        transcript_en: content,            // actual transcript
        transcript_ne: "",                 // will be added later
        language: "English",               // default or placeholder
        url: "",                           // can be added manually later
        speaker_name: [],
        keywords: [],
        date_recorded: null                // optional to fill later
        // date_added auto-filled by schema default
      });

      await newFile.save();
      console.log(`Saved '${file}' in MongoDB.`);
    }

  } catch (error) {
    console.error("Error uploading SRT or VTT files:", error.message);
  }
};

export default uploadFiles;
