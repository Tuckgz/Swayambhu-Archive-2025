import express from "express";
import subtitleFile from "../models/subtitleschema.js";

const router = express.Router();

const deleteFile = async (req, res) => {
    try {
        const { name } = req.params;
        console.log("Requested file to be deleted:", name);

        let result = await subtitleFile.deleteOne({ filename: name });

        if (result.deletedCount === 0) {
            result = await subtitleFile.deleteOne({ title: name });
        }

        if (result.deletedCount === 0) {
            return res.status(404).json({ error: "File not found" });
        }

        res.json({ message: "File deleted successfully", result });

    } catch (error) {
        console.error("Deletion error:", error);
        res.status(500).json({ error: "Internal server error" });
    }
};

router.delete("/:name", deleteFile);

export default router;
