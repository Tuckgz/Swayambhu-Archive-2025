import express from "express"
import SRTFile from "../models/srtschema.js"

const router = express.Router();

router.get("/srt/:name", async (req, res) => {
    try {
        const { name } = req.params;
        console.log("Requested filename:", name);
        const srtFile = await SRTFile.findOne({ name });

        if (!srtFile) {
            return res.status(404).json({ error: "File not found" });
        }

        res.json(srtFile);

    } catch (error) {
        res.status(500).json({ error: "Error" });
      }
})

export default router;