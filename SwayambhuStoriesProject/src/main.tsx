import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { GoogleOAuthProvider  } from '@react-oauth/google'
import App from './App.tsx'

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

console.log("Google Client ID:", clientId);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <GoogleOAuthProvider clientId={clientId}>
      <App />
    </GoogleOAuthProvider>
  </StrictMode>,
)
