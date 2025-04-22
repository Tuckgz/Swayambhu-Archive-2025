import express from "express";
import subtitleFile from "../models/subtitleschema.js";

const router = express.Router();

const getSubtitleFile = async (req, res) => {
    try {
        const { name } = req.params;
        const { search } = req.query;
        console.log("Requested file:", name);

        let subFile = await subtitleFile.findOne({ filename: name });
        if (!subFile) {
            subFile = await subtitleFile.findOne({ title: name });
        }

        if (!subFile) {
            return res.status(404).json({ error: "File not found" });
        }

        if (search) {
            const lines = subFile.transcript_en.split("\n");
            const results = [];

            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes("-->")) {
                    const timestamp = lines[i];
                    const text = lines[i + 1] || "";
                    if (text.toLowerCase().includes(search.toLowerCase())) {
                        results.push({ timestamp, text });
                    }
                }
            }

            if (results.length === 0) {
                return res.status(404).json({ message: `Word "${search}" not found` });
            }

            return res.json({ search, results });
        }

        res.json(subFile);

    } catch (error) {
        console.error("Error retrieving subtitle file:", error);
        res.status(500).json({ error: "Internal server error" });
    }
};

router.get("/:name", getSubtitleFile);

export default router;

