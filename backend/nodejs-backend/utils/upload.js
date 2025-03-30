import { promises as fs } from "fs";
import path from "path";
import subtitleFile from "../models/subtitleschema.js"; 

const uploadFiles = async (Path) => {
  try {
    const files = await fs.readdir(Path); 

    for (const file of files) {
      if (path.extname(file) === ".srt" || ".vtt" ) {
        const filePath = path.join(Path, file);
        const content = await fs.readFile(filePath, "utf8"); 
        const existingFile = await subtitleFile.findOne({ name: file });

        if (existingFile) {
          // console.log(`File '${file}' is already in database.`);
          continue;
        }

        const newSRT = new subtitleFile({ name: file, content });
        await newSRT.save();
        console.log(`Saved'${file}' in MongoDB.`);
      }
    }
  } catch (error) {
    console.error("Error uploading SRT or VTT files:", error.message);
  }
};

export default uploadFiles;
