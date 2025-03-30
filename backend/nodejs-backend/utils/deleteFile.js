import express from "express"
import subtitleFile from "../models/subtitleschema.js"

const router = express.Router();


 const deleteFile = async (req, res) => {
    try {
        const { name } = req.params;
        console.log("Requested file to be deleted:", name);
        const srtFile = await subtitleFile.deleteOne({ name });

        if (srtFile.deletedCount === 0) {
            return res.status(404).json({ error: "File not found" });
        }

        res.json(srtFile);

    } catch (error) {
        res.status(500).json({ error: "Error" });
      }
}

router.delete("/:name", deleteFile);

export default router;