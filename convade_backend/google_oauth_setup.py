#!/usr/bin/env python3
"""
Google OAuth2 Setup Script for Convade LMS
This script helps you set up Google OAuth2 authentication with step-by-step instructions.
"""
import sys
import re
import webbrowser


def show_google_setup_instructions():
    """Show detailed Google OAuth2 setup instructions"""
    
    print("🔧 Google OAuth2 Setup for Convade LMS")
    print("=" * 60)
    print()
    
    print("📋 Step-by-Step Instructions:")
    print()
    
    print("1. 🌐 Go to Google Cloud Console")
    print("   https://console.cloud.google.com/")
    print()
    
    print("2. 📁 Create or Select a Project")
    print("   • Click 'Select a project' dropdown")
    print("   • Click 'New Project' or select existing one")
    print("   • Name: 'Convade LMS' (or your preferred name)")
    print()
    
    print("3. 🔌 Enable Google+ API")
    print("   • Go to 'APIs & Services' → 'Library'")
    print("   • Search for 'Google+ API'")
    print("   • Click 'Enable'")
    print()
    
    print("4. 🔑 Create OAuth 2.0 Credentials")
    print("   • Go to 'APIs & Services' → 'Credentials'")
    print("   • Click '+ CREATE CREDENTIALS'")
    print("   • Select 'OAuth 2.0 Client IDs'")
    print()
    
    print("5. ⚙️ Configure OAuth Consent Screen (if prompted)")
    print("   • User Type: External")
    print("   • App name: Convade LMS")
    print("   • User support email: your email")
    print("   • Developer contact: your email")
    print("   • Save and continue through all steps")
    print()
    
    print("6. 🔧 Configure OAuth 2.0 Client")
    print("   • Application type: Web application")
    print("   • Name: Convade LMS Backend")
    print()
    
    print("7. 🔗 Add Authorized Redirect URIs:")
    print("   For Development:")
    print("   • http://localhost:8000/auth/complete/google-oauth2/")
    print("   • http://127.0.0.1:8000/auth/complete/google-oauth2/")
    print()
    print("   For Production (replace with your domain):")
    print("   • https://your-domain.com/auth/complete/google-oauth2/")
    print("   • https://api.your-domain.com/auth/complete/google-oauth2/")
    print()
    
    print("8. 💾 Save and Copy Credentials")
    print("   • Click 'CREATE'")
    print("   • Copy the 'Client ID' and 'Client Secret'")
    print("   • Keep these secure!")
    print()


def update_env_file(client_id, client_secret):
    """Update the production.env file with Google OAuth2 credentials"""
    
    try:
        with open('production.env', 'r') as file:
            content = file.read()
        
        # Replace the Google OAuth2 credentials
        content = re.sub(
            r'GOOGLE_OAUTH2_CLIENT_ID=.*',
            f'GOOGLE_OAUTH2_CLIENT_ID={client_id}',
            content
        )
        content = re.sub(
            r'GOOGLE_OAUTH2_CLIENT_SECRET=.*',
            f'GOOGLE_OAUTH2_CLIENT_SECRET={client_secret}',
            content
        )
        
        with open('production.env', 'w') as file:
            file.write(content)
        
        print("✅ Environment file updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update environment file: {e}")
        return False


def test_configuration():
    """Test the Google OAuth2 configuration"""
    
    print("\n🧪 Testing Google OAuth2 Configuration...")
    print("-" * 40)
    
    try:
        import os
        import django
        
        # Set up Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'convade_backend.settings.development')
        django.setup()
        
        from django.conf import settings
        
        # Check if credentials are configured
        client_id = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
        client_secret = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')
        
        if client_id and client_secret and not client_id.startswith('your-'):
            print("✅ Google OAuth2 credentials configured")
            print(f"🔑 Client ID: {client_id[:20]}...")
            print("🔑 Client Secret: [HIDDEN]")
            
            # Test URL
            print(f"\n🔗 Test URL: http://localhost:8000/auth/login/google-oauth2/")
            print("🔗 API Endpoint: http://localhost:8000/api/auth/social-providers/")
            
            return True
        else:
            print("⚠️ Google OAuth2 credentials not configured")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def main():
    """Main setup process"""
    
    print("🚀 Convade LMS - Google OAuth2 Setup")
    print("=" * 50)
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_configuration()
        return
    
    # Show instructions
    show_google_setup_instructions()
    
    # Ask if they want to open Google Cloud Console
    response = input("Open Google Cloud Console in your browser? (y/n): ").strip().lower()
    if response == 'y':
        webbrowser.open('https://console.cloud.google.com/apis/credentials')
        print("🌐 Google Cloud Console opened in your browser")
        print()
    
    # Get credentials from user
    print("📝 Enter your Google OAuth2 credentials:")
    print("(You can find these in Google Cloud Console → APIs & Services → Credentials)")
    print()
    
    while True:
        client_id = input("Google OAuth2 Client ID: ").strip()
        if client_id:
            break
        print("❌ Client ID is required")
    
    while True:
        client_secret = input("Google OAuth2 Client Secret: ").strip()
        if client_secret:
            break
        print("❌ Client Secret is required")
    
    # Update environment file
    print("\n💾 Updating environment file...")
    if update_env_file(client_id, client_secret):
        print("\n🎉 Google OAuth2 setup complete!")
        
        # Test the configuration
        if input("\nTest the configuration now? (y/n): ").strip().lower() == 'y':
            test_configuration()
        
        print("\n🚀 Next Steps:")
        print("1. Start your Django server: python manage.py runserver")
        print("2. Test the auth URL: http://localhost:8000/auth/login/google-oauth2/")
        print("3. Check API endpoint: http://localhost:8000/api/auth/social-providers/")
        print("4. Integrate with your frontend using the provided URLs")
    else:
        print("❌ Setup failed. Please try again.")


if __name__ == "__main__":
    main() 