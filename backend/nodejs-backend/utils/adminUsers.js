import express from 'express';
import axios from 'axios';
import AdminUser from '../models/userschema.js'; // Your Mongoose model

const router = express.Router();

router.post('/google-auth', async (req, res) => {
  const { token } = req.body;

  try {
    const response = await axios.get('https://www.googleapis.com/oauth2/v3/userinfo', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const { sub: googleId, email, name } = response.data;
    let user = await AdminUser.findOne({ email });

    if (!user) {
      user = await AdminUser.create({
        googleId,
        email,
        name,
        role: 'pending',
      });
      return res.status(200).json({ status: 'pending', user });
    }

    if (user.role === 'pending') {
      return res.status(200).json({ status: 'pending', user });
    }

    res.json({ status: 'approved', user });

  } catch (err) {
    console.error('Google auth failed:', err.message);
    res.status(401).json({ error: 'Unauthorized or invalid token' });
  }
});

export default router;
