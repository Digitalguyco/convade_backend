# 🚀 Convade LMS Deployment Guide

Complete guide for deploying your Django LMS project to popular hosting platforms.

## 📋 Pre-Deployment Checklist

- [ ] Code committed to Git repository (GitHub, GitLab, etc.)
- [ ] Environment variables documented
- [ ] Database migrations tested
- [ ] Static files configuration verified
- [ ] Dependencies updated in requirements.txt

---

## 🏆 Option 1: Render (Recommended)

**💰 Cost**: Free tier + $7/month for PostgreSQL starter (if you need more than 1GB)
**⏱️ Deployment time**: 5-10 minutes

### Step 1: Prepare Repository
```bash
# Make sure all files are committed
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Deploy to Render
1. Go to [render.com](https://render.com) and sign up
2. Connect your GitHub repository
3. Create a new **Web Service**:
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn convade_backend.wsgi:application`
   - **Environment**: `Python 3`

### Step 3: Create PostgreSQL Database
1. In Render dashboard, create a new **PostgreSQL** database
2. Copy the **Database URL**

### Step 4: Set Environment Variables
In your web service settings, add:
```
DATABASE_URL=postgresql://...  (from step 3)
DJANGO_SETTINGS_MODULE=convade_backend.settings.production
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=your-app-name.onrender.com
```

### Step 5: Deploy
Click **Deploy** and wait 5-10 minutes!

**✅ Your app will be live at**: `https://your-app-name.onrender.com`

---

## 🚆 Option 2: Railway

**💰 Cost**: $5 monthly credit (free)
**⏱️ Deployment time**: 3-5 minutes

### Deploy with One Command
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

### Environment Variables
```
DJANGO_SETTINGS_MODULE=convade_backend.settings.production
SECRET_KEY=your-super-secret-key
```

Railway automatically provides `DATABASE_URL` and `REDIS_URL`!

---

## ✈️ Option 3: Fly.io

**💰 Cost**: Good free tier
**⏱️ Deployment time**: 5-10 minutes

### Step 1: Install Fly CLI
```bash
# macOS
brew install flyctl

# Other systems
curl -L https://fly.io/install.sh | sh
```

### Step 2: Deploy
```bash
# Initialize Fly app
fly launch

# Deploy
fly deploy
```

### Step 3: Set Environment Variables
```bash
fly secrets set DJANGO_SETTINGS_MODULE=convade_backend.settings.production
fly secrets set SECRET_KEY=your-super-secret-key
```

---

## 🔧 Environment Variables Reference

### Required Variables
```bash
DJANGO_SETTINGS_MODULE=convade_backend.settings.production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://...  (provided by hosting platform)
```

### Optional Variables
```bash
# Redis (for better performance)
REDIS_URL=redis://...

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Social Authentication
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret

# Sentry (Error Monitoring)
SENTRY_DSN=https://...
```

---

## 📊 Platform Comparison

| Platform | Free Tier | Database | Redis | Custom Domain | Ease of Use |
|----------|-----------|----------|-------|---------------|-------------|
| **Render** | ✅ Limited | ✅ 1GB PostgreSQL | ❌ ($7/month) | ✅ | ⭐⭐⭐⭐⭐ |
| **Railway** | ✅ $5 credit | ✅ PostgreSQL | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Fly.io** | ✅ Good limits | ✅ PostgreSQL | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Heroku** | ❌ No free tier | ❌ Paid only | ❌ Paid only | ✅ | ⭐⭐⭐⭐⭐ |

---

## 🎯 Recommended Deployment Strategy

### Phase 1: Start Free
1. **Use Render** for web app (free tier)
2. **Use Render PostgreSQL** (free 1GB)
3. **Skip Redis initially** (use database caching)

### Phase 2: Scale Up ($7-15/month)
1. **Upgrade to Railway** or **Render Pro**
2. **Add Redis** for better performance
3. **Add custom domain**

### Phase 3: Production Ready ($20-50/month)
1. **Use dedicated hosting** (DigitalOcean, AWS, etc.)
2. **Add CDN** for static files
3. **Add monitoring** (Sentry, LogRocket)
4. **Add backup strategy**

---

## 🔍 Testing Your Deployment

### 1. Basic Health Check
```bash
curl https://your-app.onrender.com/
# Should return your documentation page
```

### 2. API Endpoints Test
```bash
# Test API documentation
curl https://your-app.onrender.com/api/docs/

# Test schema
curl https://your-app.onrender.com/api/schema/
```

### 3. Database Test
```bash
# Create superuser (one-time)
# SSH into your hosting platform and run:
python manage.py createsuperuser
```

---

## 🐛 Common Issues & Solutions

### Issue: Static Files Not Loading
**Solution**: Ensure `STATIC_ROOT` is set correctly
```python
# In production.py
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

### Issue: Database Connection Error
**Solution**: Check `DATABASE_URL` format
```
postgresql://username:password@host:port/database_name
```

### Issue: Allowed Hosts Error
**Solution**: Add your domain to `ALLOWED_HOSTS`
```python
ALLOWED_HOSTS = ['your-app.onrender.com', 'your-domain.com']
```

### Issue: Secret Key Error
**Solution**: Generate a strong secret key
```python
import secrets
print(secrets.token_urlsafe(50))
```

---

## 📈 Performance Tips

1. **Enable Gzip**: Automatically handled by hosting platforms
2. **Use WhiteNoise**: Already configured for static files
3. **Database Connection Pooling**: Enable with `CONN_MAX_AGE=600`
4. **Add Redis**: For caching and sessions when budget allows
5. **Monitor with Sentry**: Catch errors before users do

---

## 🔐 Security Checklist

- [ ] `DEBUG = False` in production
- [ ] Strong `SECRET_KEY` set
- [ ] `ALLOWED_HOSTS` configured
- [ ] SSL/HTTPS enabled (automatic on hosting platforms)
- [ ] Environment variables used (no secrets in code)
- [ ] Database credentials secured
- [ ] CORS properly configured

---

## 🎉 Next Steps

1. **Deploy to Render** (easiest start)
2. **Set up custom domain** (optional)
3. **Add monitoring** with Sentry
4. **Create admin user** for testing
5. **Test all API endpoints**
6. **Build your frontend** and connect to API

**🚀 Your API will be live and ready for frontend integration!**

---

## 💬 Need Help?

- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app  
- **Fly.io Docs**: https://fly.io/docs
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/