import express from 'express';
import AdminUser from '../models/userschema.js'; 

const router = express.Router();

router.get('/admin-users', async (req, res) => {
  try {
    const pending = await AdminUser.find({ role: 'pending' });
    const admins = await AdminUser.find({ role: 'admin' });
    res.json({ pending, admins });
  } catch (err) {
    res.status(500).json({ error: 'Failed to load users' });
  }
});

router.delete('/admin-users/:id', async (req, res) => {
    try {
      await AdminUser.findByIdAndDelete(req.params.id);
      res.json({ success: true });
    } catch (err) {
      res.status(500).json({ error: 'Deletion failed' });
    }
  });

router.patch('/admin-users/:id/approve', async (req, res) => {
    try {
      await AdminUser.findByIdAndUpdate(req.params.id, { role: 'admin' });
      res.json({ success: true });
    } catch (err) {
      res.status(500).json({ error: 'Approval failed' });
    }
  });
  
export default router;
