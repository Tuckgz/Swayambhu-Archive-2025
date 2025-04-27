const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  googleId: { type: String, required: true, unique: true },
  email: { type: String, required: true, unique: true },
  name: { type: String },
  role: { type: String, enum: ['admin', 'user'], default: 'user' },  
  createdAt: { type: Date, default: Date.now },
  lastLogin: { type: Date },
});

const userFile = mongoose.model('User', userSchema);
export default userFile;