# 🎓 Convade LMS API Documentation

Welcome to the comprehensive API documentation for the Convade Learning Management System!

## 📖 Documentation Overview

Our API documentation is designed to help frontend developers quickly integrate with the Convade LMS backend. It includes:

- **Complete endpoint reference** with all available API endpoints
- **Code examples** for both Axios and Fetch API
- **Authentication guide** with JWT token management
- **Error handling** patterns and best practices
- **Real-world examples** with React and Vue.js components

## 🚀 Quick Start

1. **View the Documentation**: Open `API_DOCUMENTATION.html` in your browser
2. **Start the Development Server**: 
   ```bash
   cd convade_backend
   python manage.py runserver 8001
   ```
3. **Access Interactive Docs**: Visit http://127.0.0.1:8001/api/docs/ for Swagger UI

## 🌐 Live Deployment

### Free Hosting Options
We've prepared everything for easy deployment to popular hosting platforms:

- **🏆 Render** (Recommended) - Free tier with PostgreSQL
- **🚆 Railway** - $5 monthly credit (effectively free)
- **✈️ Fly.io** - Good free tier with global edge deployment

**📖 See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete deployment instructions!**

### Quick Deploy to Render
1. Push your code to GitHub
2. Connect GitHub to [Render](https://render.com)
3. Use these settings:
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn convade_backend.wsgi:application`
4. Add environment variables and deploy!

## 📋 Available Documentation Formats

- **📄 HTML Documentation**: `API_DOCUMENTATION.html` - Beautiful, GitHub-style docs
- **🔧 Swagger UI**: `/api/docs/` - Interactive API explorer  
- **📚 ReDoc**: `/api/redoc/` - Alternative interactive documentation
- **🔍 OpenAPI Schema**: `/api/schema/` - Raw API schema

## 🌟 Key Features Covered

### 🔐 Authentication
- JWT token-based authentication
- Login/logout endpoints
- Token refresh patterns
- Social authentication (Google OAuth)

### 👤 Account Management
- User registration with invitations
- Profile management
- Password changes
- User administration

### 📖 Course Management
- Course listing and filtering
- Enrollment management
- Categories and modules
- Lessons and announcements

### 📝 Testing System
- Test creation and management
- Question banks
- Test attempts and results
- Progress tracking

## 💡 Frontend Integration Examples

The documentation includes complete examples for:

- **React Components**: Login forms, course lists
- **Vue.js Components**: Course enrollment, user profiles
- **Error Handling**: Token refresh, API errors
- **Best Practices**: Request patterns, state management

## 🔧 Development Setup

### Prerequisites
- Python 3.8+
- Django 5.2+
- PostgreSQL (for production)
- Redis (for caching and sessions)

### Environment Variables
```bash
# Database
DB_NAME=convade_production
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
DJANGO_SETTINGS_MODULE=convade_backend.settings.production
SECRET_KEY=your_secret_key
DEBUG=False

# Social Authentication
GOOGLE_OAUTH2_CLIENT_ID=your_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_client_secret
```

### API Base URLs
- **Development**: `http://127.0.0.1:8001/api`
- **Production**: `https://your-domain.com/api`

## 🚀 Production Deployment

### Cost Breakdown
| Platform | Free Tier | Starter Plan | Pro Plan |
|----------|-----------|--------------|----------|
| **Render** | ✅ Free web + 1GB DB | $7/month | $25/month |
| **Railway** | ✅ $5 credit/month | $10/month | $20/month |
| **Fly.io** | ✅ Good free tier | $5/month | $15/month |

### Deployment Files Included
- `render.yaml` - Render configuration
- `build.sh` - Build script for all platforms  
- `convade_backend/settings/production.py` - Production settings
- `requirements.txt` - Updated with hosting dependencies
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide

## 📱 Frontend Framework Examples

### React/Next.js
```javascript
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';
const token = localStorage.getItem('access_token');

axios.defaults.baseURL = API_BASE;
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
```

### Vue.js/Nuxt.js
```javascript
// plugins/axios.js
export default function ({ $axios, store }) {
  $axios.setBaseURL(process.env.API_URL || '/api');
  
  if (store.state.auth.token) {
    $axios.setToken(store.state.auth.token, 'Bearer');
  }
}
```

### Angular
```typescript
// services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable()
export class ApiService {
  private baseUrl = environment.apiUrl || '/api';
  
  constructor(private http: HttpClient) {}
  
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }
}
```

## 🤝 Contributing

When adding new API endpoints, please:

1. Update the OpenAPI schema
2. Add examples to the HTML documentation
3. Test with both Axios and Fetch API
4. Include error handling examples
5. Update this README if needed

## 🆘 Support

- **📧 API Issues**: Check the error handling section in the docs
- **🔧 Development**: See the interactive Swagger UI
- **📚 Examples**: Review the complete examples section
- **🔍 Schema**: Download the OpenAPI schema for code generation
- **🚀 Deployment**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## 📊 API Statistics

- **Endpoints**: 25+ RESTful endpoints
- **Authentication**: JWT + Social OAuth
- **Response Format**: JSON
- **Versioning**: URL-based (/api/v1/)
- **Rate Limiting**: Configurable per endpoint
- **Documentation**: Auto-generated + Manual examples
- **Hosting Ready**: Optimized for free hosting platforms

## 🎯 Getting Started Checklist

### For Developers
- [ ] Clone repository
- [ ] Set up local environment
- [ ] Read API documentation
- [ ] Test endpoints with Swagger UI
- [ ] Build frontend integration

### For Deployment
- [ ] Choose hosting platform (Render recommended)
- [ ] Generate secret key: `python generate_secret_key.py`
- [ ] Set environment variables
- [ ] Follow deployment guide
- [ ] Test live API endpoints

---

**🎉 Happy Coding!** The API is designed to be developer-friendly with comprehensive documentation and examples. Ready for both development and production deployment! 