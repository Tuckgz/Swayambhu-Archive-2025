import express from "express"
import subtitleFile from "../models/subtitleschema.js"

const router = express.Router();

const getSubtitleFile = async (req, res) => {
    try {
        const { name } = req.params;
        console.log("Requested file:", name);
        const srtFile = await subtitleFile.findOne({ name });

        if (!srtFile) {
            return res.status(404).json({ error: "File not found" });
        }

        res.json(srtFile);

    } catch (error) {
        res.status(500).json({ error: "Error" });
      }
};

router.get("/:name", getSubtitleFile);

export default router;