import os
import logging
from logging.handlers import RotatingFileHandler
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.shared_data import SharedDataMiddleware
from app import app
import gzip
import time

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# 1. Advanced Logging Configuration with Auto-Rotating File
log_formatter = logging.Formatter('%(asctime)s [%(process)d] [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Rotating file handler (Max 5MB per file, keep last 5 backups)
file_handler = RotatingFileHandler('logs/server.log', maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)

server_logger = logging.getLogger('waitress')
server_logger.setLevel(logging.INFO)
server_logger.addHandler(console_handler)
server_logger.addHandler(file_handler)

access_logger = logging.getLogger('access')
access_logger.setLevel(logging.INFO)
access_logger.addHandler(console_handler)
access_logger.addHandler(file_handler)

# Remove default handlers to avoid duplicate logs if they exist
app.logger.handlers = []

# 2. Access Logger Middleware
class AccessLoggerMiddleware:
    """WSGI middleware to provide basic access logging for requests."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        req_uri = environ.get('PATH_INFO', '')
        if environ.get('QUERY_STRING'):
            req_uri += '?' + environ['QUERY_STRING']
        method = environ.get('REQUEST_METHOD', 'GET')
        remote_addr = environ.get('REMOTE_ADDR', '-')
        start_time = time.time()
        
        def custom_start_response(status, headers, exc_info=None):
            duration = (time.time() - start_time) * 1000
            access_logger.info(f"{remote_addr} - {method} {req_uri} - {status} [{duration:.2f}ms]")
            return start_response(status, headers, exc_info)
            
        return self.wsgi_app(environ, custom_start_response)

# 3. Gzip Compression Middleware
class GzipMiddleware:
    """Compresses HTTP responses using Gzip to speed up page loads."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        if 'gzip' not in environ.get('HTTP_ACCEPT_ENCODING', ''):
            return self.wsgi_app(environ, start_response)
            
        captured = []
        
        def custom_start_response(status, headers, exc_info=None):
            captured.append((status, headers, exc_info))
            return lambda body: None
            
        response_iterable = self.wsgi_app(environ, custom_start_response)
        
        if not captured:
            return response_iterable
            
        status, headers, exc_info = captured[0]
        
        should_compress = False
        for name, value in headers:
            if name.lower() == 'content-type' and any(t in value.lower() for t in ['text/', 'application/json']):
                should_compress = True
                break
                
        if not should_compress:
            start_response(status, headers, exc_info)
            return response_iterable
            
        # Perform gzip compression
        try:
            body = b"".join(response_iterable)
            if hasattr(response_iterable, 'close'):
                response_iterable.close()
                
            compressed = gzip.compress(body)
            
            new_headers = [(n, v) for n, v in headers if n.lower() != 'content-length']
            new_headers.append(('Content-Encoding', 'gzip'))
            new_headers.append(('Vary', 'Accept-Encoding'))
            new_headers.append(('Content-Length', str(len(compressed))))
            
            start_response(status, new_headers, exc_info)
            return [compressed]
        except Exception:
            start_response(status, headers, exc_info)
            return response_iterable

# 4. Health Check Middleware
class HealthCheckMiddleware:
    """Provides a fast /health endpoint for load balancers."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        if environ.get('PATH_INFO') == '/health':
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [b'{"status": "alive", "server": "waitress"}']
        return self.wsgi_app(environ, start_response)

# 5. Simple Rate Limiting Middleware (In-Memory)
class RateLimitingMiddleware:
    """Prevents IP spamming (Max 100 requests per 10 seconds per IP)."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
        self.ips = {}

    def __call__(self, environ, start_response):
        ip = environ.get('REMOTE_ADDR', '127.0.0.1')
        current_time = time.time()
        
        # Clean up old ips periodically
        if len(self.ips) > 10000:
            self.ips.clear()
            
        if ip not in self.ips:
            self.ips[ip] = []
            
        # Filter requests older than 10 seconds
        self.ips[ip] = [t for t in self.ips[ip] if current_time - t < 10]
        
        if len(self.ips[ip]) > 100:
            start_response('429 Too Many Requests', [('Content-Type', 'text/plain')])
            return [b'Rate Limit Exceeded. Please slow down.']
            
        self.ips[ip].append(current_time)
        return self.wsgi_app(environ, start_response)

# Apply middlewares from innermost to outermost
app_prod = ProxyFix(app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app_prod = RateLimitingMiddleware(app_prod)
app_prod = HealthCheckMiddleware(app_prod)
app_prod = AccessLoggerMiddleware(app_prod)
app_prod = GzipMiddleware(app_prod)
# Basic Static Caching bypass (Werkzeug SharedDataMiddleware)
app_prod = SharedDataMiddleware(app_prod, {'/static': os.path.join(os.path.dirname(__file__), 'static')})


if __name__ == '__main__':
    # Environment Variable Based Configuration
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    threads = int(os.environ.get('WAITRESS_THREADS', 6))
    url_scheme = os.environ.get('WAITRESS_SCHEME', 'http')
    connection_limit = int(os.environ.get('WAITRESS_CONNECTION_LIMIT', 1000))
    channel_timeout = int(os.environ.get('WAITRESS_CHANNEL_TIMEOUT', 120))

    server_logger.info("=" * 60)
    server_logger.info("🚀 Starting ADVANCED PRODUCTION Web Server (Waitress)")
    server_logger.info(f"🌍 Address/Host : {url_scheme}://{host}:{port}")
    server_logger.info(f"🧵 Threads      : {threads}")
    server_logger.info(f"🔌 Connections  : {connection_limit} (Max)")
    server_logger.info(f"⏱️  Timeout      : {channel_timeout}s")
    server_logger.info(f"💾 Logging      : Enabled (logs/server.log)")
    server_logger.info(f"🛡️  Middlewares : ProxyFix, RateLimit, HealthCheck, Gzip, AccessLog")
    server_logger.info("=" * 60)

    try:
        serve(
            app_prod,
            host=host,
            port=port,
            threads=threads,
            url_scheme=url_scheme,
            connection_limit=connection_limit,
            channel_timeout=channel_timeout,
            ident="GlacierGoals-Prod-Server",
            clear_untrusted_proxy_headers=True
        )
    except KeyboardInterrupt:
        server_logger.info("🛑 Received KeyboardInterrupt, shutting down gracefully...")
    except Exception as e:
        server_logger.exception(f"❌ Server encountered a fatal error: {e}")
