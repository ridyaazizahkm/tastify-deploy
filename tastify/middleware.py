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
            # Default policy untuk semua konten
            "default-src 'self'", 
            
            # Untuk inline scripts dan styles yang diperlukan dalam template
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com", 
            
            # Style dari sumber yang aman
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com", 
            
            # Font dari sumber yang aman
            "font-src 'self' https://fonts.gstatic.com", 
            
            # Gambar dari sumber yang aman
            "img-src 'self' data: https:", 
            
            # Untuk fonts dan styles
            "connect-src 'self'",
            
            # Frame hanya dari sumber yang sama
            "frame-src 'self'",
            
            # Untuk melarang semua plugin seperti Flash, Java, dll.
            "object-src 'none'",
            
            # Untuk melarang inline JavaScript event handlers
            "base-uri 'self'",
            
            # Untuk melarang <form> mendaftarkan handler di luar domain yang sama
            "form-action 'self'",
            
            # Melarang embedding <frame>, <iframe>, <object>, <embed>, <applet>
            "frame-ancestors 'self'",
            
            # Memaksa HTTPS untuk semua aset
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