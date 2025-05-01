# Swayambhu Archive

A full-stack academic video archive for searching and viewing multilingual oral history interviews. Built with React, Node.js, and MongoDB.

---

## 🚀 Tech Stack

### Frontend:
- React + TypeScript
- Vite + React Router
- Tailwind CSS

### Backend:
- Node.js + Express
- MongoDB (Mongoose)
- dotenv

---

## 🧑‍💻 Setup Instructions

### 1. Clone the Repository

```bash
git clone <HTTP LINK Grabbed from repo>
```

### 2. Install Dependencies

```bash
cd SwayambhuStoriesProject
npm install

cd ../backend/nodejs-backend
npm install
```

---

## 🔐 Environment Variables

Create a `.env` file inside `backend/nodejs-backend` with:

```
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/transcript_db
```

---

## 🔄 Running the App

### Backend (Node.js API)

```bash
cd backend/nodejs-backend
node server.js
```

Those commands should result in the following:
    
    "Server running on port {XXXX}"
    "Connection Made to Mongodb"

### Frontend (Vite + React)

```bash
cd SwayambhuStoriesProject
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧠 Backend API Overview

| Route                  | Method | Description                                      |
|------------------------|--------|--------------------------------------------------|
| `/api/videos`          | GET    | Get all video metadata                           |
| `/api/videos/:id`      | GET    | Fetch a single video by Mongo `_id`              |
| `/api/videos/search`   | POST   | Search videos by keywords in transcript          |
| `/api/search?keyword=hello`| GET| returns all occurrences of a word/phrase in order within db with filename, and timestamp|
| `/api/example.srt`      | GET    | returns the entire file|
| `/api/example.srt?search=hello`| GET |returns all of the occurances of a word within file|
| `/api/example.vtt`| DELETE |deletes file from Mongodb|

**Search Payload Example:**
```json
{ "terms": ["sack", "enjoy"] }
```

---

## 🌐 Frontend Features

- **Search Terms**: Add/remove terms to find videos matching keywords in transcript.
- **Dropdown Filters**: Filter by language, source type, speaker type, and location.
- **Sorting**: Sort results by duration or date.
- **Pagination**: View results across multiple pages.
- **Video Preview**: Watch videos, view metadata, and scroll transcripts.
- **Language Picker**: Select from available transcript languages.
- **Admin Page**: Internal admin interface at `/admin` where authenticated users can upload new videos, manage metadata, and trigger transcription and translation tools.

---



## 📁 Transcript Data Format

Stored in MongoDB under `transcript_content` field:

```json
{
  "en": "WEBVTT\n00:00:01.000 --> 00:00:04.000\nHello world",
  "ne": "WEBVTT\n00:00:01.000 --> 00:00:04.000\nनमस्ते संसार"
}
```

Transcript language keys may be `en`, `ne`, `english`, `nepali`, etc.

---

## 🔍 Search & Filtering Logic

- **Search**: Performed server-side with exact word matching.
- **Filtering**: Done client-side using metadata and transcript languages.
- **Sorting**: Uses `useMemo` to optimize performance on the frontend.

---

## 🥚 Dummy Data

The backend includes scripts to:
- Populate the `media_transcripts` collection with sample documents.
- Update existing documents with required metadata.

---

## 🛠️ Future Improvements

- Add fuzzy search and full-text Mongo indexing
- Enable ranked search results
- Implement state management for ease of use
---


    



