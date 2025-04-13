import express from "express";
import subtitleFile from "../models/subtitleschema.js";

const router = express.Router();

const searchAll = async (req, res) => {
    try {
        const { keyword } = req.query;

        const phrase = `"${keyword}"`;

        const results = await subtitleFile.find(
            { $text: { $search: phrase } },
            { name: 1, content: 1 }
        );

        if (results.length === 0) {
            return res.status(404).json({ message: `No matchings for "${keyword}"` });
        }

        const response = results.map(file => {
            const lines = file.content.split("\n");
            const matches = [];

            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes("-->")) {
                    const timestamp = lines[i];
                    const text = lines[i + 1] || "";

                    if (text.toLowerCase().includes(keyword.toLowerCase())) {
                        matches.push({
                            timestamp,
                            text: text.trim()
                        });
                    }
                }
            }
            return {
                name: file.name,
                matches,
                occurrences: matches.length
            };
        }).filter(entry => entry.occurrences > 0);

        res.json({ keyword, results: response });

    }  catch (error) {
        console.error(error);
        res.status(500).json({ error: "Server error while keywording files" });
    }
}

router.get("/search", searchAll);

export default router;