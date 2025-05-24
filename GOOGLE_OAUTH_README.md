# Google OAuth2 Setup for Convade LMS

## 🚀 Overview

Convade LMS supports **Google OAuth2** authentication, allowing users to sign up and log in using their Google accounts. This provides a seamless, secure authentication experience.

## ✅ Why Google OAuth2?

- **🔒 Secure**: Industry-standard OAuth2 protocol
- **👥 Popular**: Most users have Google accounts
- **🆓 Free**: No cost for standard usage
- **🚀 Fast**: Quick setup and integration
- **📱 Mobile-friendly**: Works across all devices

## 🔧 Quick Setup

### 1. Run the Setup Script
```bash
python google_oauth_setup.py
```

### 2. Test Your Configuration
```bash
python test_social_auth.py
```

## 📖 Manual Setup Instructions

### Step 1: Google Cloud Console Setup

1. **🌐 Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **📁 Create or Select a Project**
   - Click "Select a project" dropdown
   - Click "New Project" or select existing one
   - Name: "Convade LMS" (or your preferred name)

3. **🔌 Enable Google+ API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. **🔑 Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "+ CREATE CREDENTIALS"
   - Select "OAuth 2.0 Client IDs"

5. **⚙️ Configure OAuth Consent Screen** (if prompted)
   - User Type: **External**
   - App name: **Convade LMS**
   - User support email: your email
   - Developer contact: your email
   - Save and continue through all steps

6. **🔧 Configure OAuth 2.0 Client**
   - Application type: **Web application**
   - Name: **Convade LMS Backend**

7. **🔗 Add Authorized Redirect URIs**
   
   **For Development:**
   ```
   http://localhost:8000/auth/complete/google-oauth2/
   http://127.0.0.1:8000/auth/complete/google-oauth2/
   ```
   
   **For Production** (replace with your domain):
   ```
   https://your-domain.com/auth/complete/google-oauth2/
   https://api.your-domain.com/auth/complete/google-oauth2/
   ```

8. **💾 Save and Copy Credentials**
   - Click "CREATE"
   - Copy the **Client ID** and **Client Secret**
   - Keep these secure!

### Step 2: Update Environment Configuration

Add these to your `production.env` file:

```env
# Google OAuth2 Configuration
GOOGLE_OAUTH2_CLIENT_ID=your_actual_client_id_here
GOOGLE_OAUTH2_CLIENT_SECRET=your_actual_client_secret_here
```

## 🔗 API Endpoints

### Get Google Provider Info
```http
GET /api/auth/social-providers/
```

**Response:**
```json
{
  "providers": [
    {
      "name": "google-oauth2",
      "display_name": "Google",
      "icon": "fab fa-google",
      "color": "#db4437",
      "auth_url": "/auth/login/google-oauth2/"
    }
  ],
  "total": 1,
  "message": "Convade LMS supports secure login with Google"
}
```

### Social Login
```http
POST /api/auth/social-login/
Content-Type: application/json

{
  "provider": "google-oauth2",
  "code": "oauth_authorization_code",
  "redirect_uri": "http://localhost:3000/auth/callback"
}
```

### Connect Google Account
```http
POST /api/auth/social-connect/google-oauth2/
Authorization: Bearer <jwt_token>
```

### Disconnect Google Account
```http
DELETE /api/auth/social-disconnect/google-oauth2/
Authorization: Bearer <jwt_token>
```

## 🎯 Authentication Flow

### Frontend Integration

**1. Redirect to Google Auth:**
```javascript
const googleLogin = () => {
  window.location.href = 'http://localhost:8000/auth/login/google-oauth2/';
};
```

**2. Handle the Callback:**
After successful authentication, Google redirects users back to your frontend with auth tokens.

**3. React/JavaScript Example:**
```jsx
// Login Button Component
const GoogleLoginButton = () => {
  const handleGoogleLogin = () => {
    window.location.href = `${API_BASE_URL}/auth/login/google-oauth2/`;
  };

  return (
    <button 
      onClick={handleGoogleLogin}
      className="google-login-btn"
    >
      <i className="fab fa-google"></i>
      Continue with Google
    </button>
  );
};
```

## 🔒 Security Features

- **✅ JWT Token Authentication**: Secure token-based auth
- **✅ Profile Picture Sync**: Automatically downloads Google profile pictures
- **✅ CSRF Protection**: Built-in protection against attacks
- **✅ Scope Limiting**: Only requests necessary permissions
- **✅ State Validation**: Prevents authorization code interception

## 🧪 Testing

### Test Configuration
```bash
python test_social_auth.py
```

### Test URLs
- **Auth URL**: http://localhost:8000/auth/login/google-oauth2/
- **API Endpoint**: http://localhost:8000/api/auth/social-providers/

### Manual Testing
1. Start Django server: `python manage.py runserver`
2. Visit: http://localhost:8000/auth/login/google-oauth2/
3. Should redirect to Google login page

## 🚨 Troubleshooting

### Common Issues

**1. "Invalid redirect URI"**
- ✅ Check redirect URIs in Google Cloud Console match exactly
- ✅ Include both `http://localhost:8000` and `http://127.0.0.1:8000`

**2. "Client ID not found"**
- ✅ Verify `GOOGLE_OAUTH2_CLIENT_ID` in environment file
- ✅ Check credentials are not placeholder values

**3. "OAuth consent screen not configured"**
- ✅ Complete OAuth consent screen setup in Google Cloud Console
- ✅ Add your email as a test user during development

**4. "Access blocked"**
- ✅ Make sure app is not in "Testing" mode for production
- ✅ Add authorized domains in OAuth consent screen

### Debug Mode

Enable debug mode for detailed error messages:
```python
SOCIAL_AUTH_RAISE_EXCEPTIONS = True
```

## 📊 Production Checklist

- [ ] Google Cloud project created
- [ ] OAuth consent screen configured
- [ ] Production redirect URIs added
- [ ] Client ID and Secret updated in production.env
- [ ] SSL certificate configured (HTTPS required for production)
- [ ] Domain verified in Google Cloud Console

## 🎉 Success!

Once configured, your users can:
- ✅ Sign up instantly with Google accounts
- ✅ Log in with one click
- ✅ Sync profile information automatically
- ✅ Enjoy secure, token-based authentication

Your Convade LMS now has **enterprise-grade Google authentication**! 🚀

## 📚 Additional Resources

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Django Social Auth Documentation](https://python-social-auth.readthedocs.io/) 