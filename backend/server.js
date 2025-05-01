const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();
const PORT = 6080;

app.use(cors());
app.use(express.json());

const transcriptsDir = path.join(__dirname, "transcripts");

// Function to search for keywords in all .srt files
const searchInSRTFiles = (keywords) => {
  const results = [];

  // Get all .srt files from the folder
  const files = fs
    .readdirSync(transcriptsDir)
    .filter((file) => file.endsWith(".srt"));

  files.forEach((file) => {
    const filePath = path.join(transcriptsDir, file);
    const content = fs.readFileSync(filePath, "utf-8");

    // Split content into subtitle blocks
    const blocks = content.split("\n\n");

    blocks.forEach((block) => {
      const lines = block.split("\n");
      if (lines.length > 2) {
        const timestamp = lines[1]; // Extract timestamp
        const text = lines.slice(2).join(" "); // Merge text lines

        // Check if any keyword appears in the text (case insensitive)
        const foundKeyword = keywords.some((keyword) =>
          text.toLowerCase().includes(keyword.toLowerCase())
        );

        if (foundKeyword) {
          results.push({ file, timestamp, text });
        }
      }
    });
  });

  return results;
};

// API endpoint to handle search requests
app.post("/search", (req, res) => {
  const { terms } = req.body;
  if (!terms || !Array.isArray(terms) || terms.length === 0) {
    return res.status(400).json({ error: "No search terms provided" });
  }

  const searchResults = searchInSRTFiles(terms);
  res.json(searchResults);
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
