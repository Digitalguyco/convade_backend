"""
Views for serving API documentation.
"""
from django.http import HttpResponse, Http404
from django.conf import settings
import os


def documentation_index(request):
    """Serve the main documentation index page."""
    try:
        # Path to the index.html file in the project root
        doc_path = os.path.join(settings.BASE_DIR.parent, 'index.html')
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("""
        <html>
        <head><title>Documentation Not Found</title></head>
        <body>
            <h1>Documentation Not Found</h1>
            <p>The documentation files are not available. Please ensure the HTML files exist in the project root.</p>
            <p><a href="/api/docs/">Try Swagger UI instead</a></p>
        </body>
        </html>
        """, content_type='text/html', status=404)


def api_documentation(request):
    """Serve the comprehensive API documentation page."""
    try:
        # Path to the API_DOCUMENTATION.html file in the project root
        doc_path = os.path.join(settings.BASE_DIR.parent, 'API_DOCUMENTATION.html')
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("""
        <html>
        <head><title>API Documentation Not Found</title></head>
        <body>
            <h1>API Documentation Not Found</h1>
            <p>The API documentation file is not available. Please ensure API_DOCUMENTATION.html exists in the project root.</p>
            <p><a href="/api/docs/">Try Swagger UI instead</a></p>
            <p><a href="/">Back to documentation index</a></p>
        </body>
        </html>
        """, content_type='text/html', status=404)


def documentation_readme(request):
    """Serve the README documentation as HTML."""
    try:
        # Path to the README_API_DOCS.md file in the project root
        readme_path = os.path.join(settings.BASE_DIR.parent, 'README_API_DOCS.md')
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple conversion of markdown to HTML for basic display
        html_content = f"""
        <html>
        <head>
            <title>Convade LMS API - Setup Guide</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px;
                    line-height: 1.6;
                }}
                code {{ 
                    background: #f6f8fa; 
                    padding: 2px 6px; 
                    border-radius: 3px;
                    font-family: monospace;
                }}
                pre {{ 
                    background: #f6f8fa; 
                    padding: 15px; 
                    border-radius: 6px;
                    overflow-x: auto;
                }}
                h1, h2, h3 {{ color: #24292f; }}
                a {{ color: #0969da; }}
            </style>
        </head>
        <body>
            <div style="margin-bottom: 20px;">
                <a href="/">&larr; Back to Documentation Home</a> | 
                <a href="/docs/api/">View Full API Docs</a> | 
                <a href="/api/docs/">Swagger UI</a>
            </div>
            <pre>{content}</pre>
        </body>
        </html>
        """
        
        return HttpResponse(html_content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("""
        <html>
        <head><title>README Not Found</title></head>
        <body>
            <h1>README Not Found</h1>
            <p>The README file is not available.</p>
            <p><a href="/">Back to documentation index</a></p>
        </body>
        </html>
        """, content_type='text/html', status=404) 