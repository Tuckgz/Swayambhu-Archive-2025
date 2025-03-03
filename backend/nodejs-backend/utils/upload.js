import { promises as fs } from "fs";
import path from "path";
import SRTFile from "../models/srtschema.js"; 

const uploadFiles = async (Path) => {
  try {
    const files = await fs.readdir(Path); 

    for (const file of files) {
      if (path.extname(file) === ".srt") {
        const filePath = path.join(Path, file);
        const content = await fs.readFile(filePath, "utf8"); 
        const existingFile = await SRTFile.findOne({ name: file });

        if (existingFile) {
          console.log(`File '${file}' is already in database.`);
          continue;
        }

        const newSRT = new SRTFile({ name: file, content });
        await newSRT.save();
        console.log(`Saved'${file}' in MongoDB.`);
      }
    }
  } catch (error) {
    console.error("Error uploading SRT files:", error.message);
  }
};

export default uploadFiles;
