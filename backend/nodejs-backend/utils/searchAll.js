import express from "express";
import subtitleFile from "../models/subtitleschema.js";

const router = express.Router();

const searchAll = async (req, res) => {
  try {
    const { keyword } = req.query;
    if (!keyword) {
      return res.status(400).json({ error: "Missing keyword" });
    }

    const phrase = `"${keyword}"`;

    // First try MongoDB text search
    let results = await subtitleFile.find(
      { $text: { $search: phrase } },
      { title: 1, transcript_en: 1 }
    );

    // Fallback to regex search if text search yields no results
    if (results.length === 0) {
      results = await subtitleFile.find(
        { transcript_en: { $regex: keyword, $options: "i" } },
        { title: 1, transcript_en: 1 }
      );
    }

    if (results.length === 0) {
      return res.status(404).json({ message: `No matchings for "${keyword}"` });
    }

    const response = results.map(file => {
      const lines = file.transcript_en.split("\n");
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
        title: file.title,
        matches,
        occurrences: matches.length
      };
    }).filter(entry => entry.occurrences > 0);

    res.json({ keyword, results: response });

  } catch (error) {
    console.error("Keyword search error:", error);
    res.status(500).json({ error: "Server error while keywording files" });
  }
};

router.get("/search", searchAll);

export default router;
