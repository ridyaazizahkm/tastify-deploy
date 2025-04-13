"""
Middleware untuk mengimplementasikan Content Security Policy
"""
from django.utils.deprecation import MiddlewareMixin

class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """
    Middleware untuk menambahkan header Content-Security-Policy
    untuk mencegah XSS attacks
    """
    
    def process_response(self, request, response):
        # Konfigurasi CSP yang aman tetapi masih mengizinkan fitur yang diperlukan
        csp_policies = [
            "default-src 'self'", 
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.tailwindcss.com https://unpkg.com", 
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com", 
            "font-src 'self' https://fonts.gstatic.com", 
            "img-src 'self' data: https:", 
            "connect-src 'self'",
            "frame-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'self'",
            "upgrade-insecure-requests",
        ]
        
        # Gabungkan semua kebijakan menjadi satu header
        response['Content-Security-Policy'] = "; ".join(csp_policies)
        
        # Tambahkan header X-XSS-Protection untuk browser lama
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Mencegah browser berperilaku seperti tipe konten berbeda dari yang ditentukan
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Mengontrol bagaimana informasi referer ditransmisikan
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response