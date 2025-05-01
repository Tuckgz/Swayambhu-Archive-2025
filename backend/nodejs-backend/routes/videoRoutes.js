import express from "express";
import {
  getAllVideos,
  getVideoById,
  searchVideos,
} from "../controllers/videoController.js";

const router = express.Router();

router.get("/", getAllVideos);
router.get("/:id", getVideoById);
router.post("/search", searchVideos);

export default router;
