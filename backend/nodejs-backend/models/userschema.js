import mongoose from "mongoose";

const userSchema = new mongoose.Schema({
  googleId: { type: String, required: true, unique: true },
  email: { type: String, required: true, unique: true },
  name: { type: String },
  role: { type: String, enum: ['admin', 'pending'], default: 'pending' },  
  createdAt: { type: Date, default: Date.now },
  lastLogin: { type: Date },
});

const AdminUser = mongoose.model('Admin', userSchema, 'Admins');
export default AdminUser;