# Swayambhu-Archive-2025
COMP 523 - Team A

This is an extension of an existing project centered on transcription and storage and preservation of the spoken history and interviews surrounding Swayambhu Mahachaitya.


## Backend Startup:
    Run the following commands from project root
    
    - "cd backend/nodejs-backend"
    - "node server.js"
    
    Those commands should result in the following:
    
    "Server running on port 5000"
    "Connection Made to Mongodb"
## Backend API Routes (For MongoDB)
- api route **http://localhost:5000**
- GET 
  - **/api/search?keyword=hello** (returns all occurrences of a word/phrase in order within db with filename, and timestamp)
  - **/api/example.srt** (returns the entire file)
  - **/api/example.srt?search=hello** (returns all of the occurances of a word within file)
- DELETE
  - **/api/example.vtt** (deletes file from Mongodb)


    



