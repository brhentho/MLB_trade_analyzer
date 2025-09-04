#!/usr/bin/env python3
"""
Production Deployment Script for Baseball Trade AI
Automated setup and validation for optimized FastAPI deployment
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def validate_environment():
    """Validate production environment configuration"""
    logger.info("🔍 Validating environment configuration...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY', 
        'OPENAI_API_KEY',
        'JWT_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    # Validate secret key strength
    secret_key = os.getenv('JWT_SECRET_KEY')
    if len(secret_key) < 32:
        logger.warning("⚠️ JWT_SECRET_KEY should be at least 32 characters")
    
    logger.info("✅ Environment validation passed")
    return True


async def test_database_connection():
    """Test database connectivity"""
    logger.info("🗄️ Testing database connection...")
    
    try:
        from services.supabase_service import supabase_service
        health = await supabase_service.health_check()
        
        if health.get('status') == 'healthy':
            logger.info(f"✅ Database connected - {health.get('teams_count', 0)} teams available")
            return True
        else:
            logger.error(f"❌ Database health check failed: {health}")
            return False
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def test_cache_system():
    """Test cache system"""
    logger.info("🔄 Testing cache system...")
    
    try:
        from services.cache_service import cache_service
        
        # Test cache operations
        test_key = "deployment_test"
        test_value = {"deployment_time": time.time()}
        
        await cache_service.set(test_key, test_value, 60)
        retrieved = await cache_service.get(test_key)
        
        if retrieved == test_value:
            await cache_service.delete(test_key)
            logger.info("✅ Cache system working correctly")
            return True
        else:
            logger.error("❌ Cache read/write test failed")
            return False
    except Exception as e:
        logger.error(f"❌ Cache system test failed: {e}")
        return False


async def initialize_queue_service():
    """Initialize and test queue service"""
    logger.info("📋 Initializing queue service...")
    
    try:
        from services.advanced_queue_service import advanced_queue_service
        
        # Start queue service
        await advanced_queue_service.start()
        
        # Test with a simple task
        task_id = await advanced_queue_service.enqueue(
            'cleanup',
            {'type': 'test'},
            priority=advanced_queue_service.TaskPriority.LOW
        )
        
        if task_id:
            logger.info("✅ Queue service initialized successfully")
            return True
        else:
            logger.error("❌ Queue service test failed")
            return False
    except Exception as e:
        logger.error(f"❌ Queue service initialization failed: {e}")
        return False


async def validate_security_config():
    """Validate security configuration"""
    logger.info("🔒 Validating security configuration...")
    
    try:
        from security.auth import SecurityConfig
        
        issues = SecurityConfig.validate_environment()
        
        if issues:
            for issue in issues:
                logger.warning(f"⚠️ Security: {issue}")
        else:
            logger.info("✅ Security configuration validated")
        
        return len(issues) == 0
    except Exception as e:
        logger.error(f"❌ Security validation failed: {e}")
        return False


async def run_health_checks():
    """Run comprehensive health checks"""
    logger.info("🏥 Running comprehensive health checks...")
    
    try:
        from monitoring.health_checks import health_monitor
        
        health_report = await health_monitor.perform_health_checks()
        overall_status = health_report.get('overall_status')
        
        if overall_status in ['healthy', 'degraded']:
            logger.info(f"✅ Health checks passed - Status: {overall_status}")
            
            # Log any issues
            for check in health_report.get('checks', []):
                if check.get('status') != 'healthy':
                    logger.warning(f"⚠️ {check['name']}: {check['message']}")
            
            return True
        else:
            logger.error(f"❌ Health checks failed - Status: {overall_status}")
            return False
    except Exception as e:
        logger.error(f"❌ Health checks failed: {e}")
        return False


async def setup_monitoring():
    """Setup monitoring and alerting"""
    logger.info("📊 Setting up monitoring...")
    
    try:
        from middleware.monitoring import get_monitoring_stats
        
        stats = get_monitoring_stats()
        if stats:
            logger.info("✅ Monitoring system initialized")
            return True
        else:
            logger.warning("⚠️ Monitoring system not fully available")
            return True  # Non-blocking
    except Exception as e:
        logger.error(f"❌ Monitoring setup failed: {e}")
        return False


def create_systemd_service():
    """Create systemd service file for production"""
    service_content = """[Unit]
Description=Baseball Trade AI - Production FastAPI Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app
Environment=PATH=/app/venv/bin
Environment=ENVIRONMENT=production
ExecStart=/app/venv/bin/python main_production.py
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/app/logs /tmp

[Install]
WantedBy=multi-user.target
"""
    
    service_path = Path('/etc/systemd/system/baseball-trade-ai.service')
    
    try:
        if os.geteuid() == 0:  # Running as root
            with open(service_path, 'w') as f:
                f.write(service_content)
            logger.info(f"✅ Systemd service created: {service_path}")
            return True
        else:
            logger.info("ℹ️ Run as root to create systemd service automatically")
            logger.info(f"Service content saved to: ./baseball-trade-ai.service")
            
            with open('baseball-trade-ai.service', 'w') as f:
                f.write(service_content)
            return True
    except Exception as e:
        logger.error(f"❌ Failed to create systemd service: {e}")
        return False


def create_nginx_config():
    """Create nginx configuration for production"""
    nginx_config = """server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 75;
        proxy_send_timeout 300;
    }
    
    # Health check endpoint (no rate limiting)
    location /api/v1/health {
        limit_req off;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    
    try:
        with open('nginx-baseball-trade-ai.conf', 'w') as f:
            f.write(nginx_config)
        logger.info("✅ Nginx configuration created: nginx-baseball-trade-ai.conf")
        logger.info("ℹ️ Copy to /etc/nginx/sites-available/ and enable with nginx")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create nginx config: {e}")
        return False


async def run_deployment_validation():
    """Run complete deployment validation"""
    logger.info("🚀 Starting production deployment validation...")
    
    checks = [
        ("Environment", validate_environment()),
        ("Database", test_database_connection()),
        ("Cache System", test_cache_system()),
        ("Queue Service", initialize_queue_service()),
        ("Security Config", validate_security_config()),
        ("Health Checks", run_health_checks()),
        ("Monitoring", setup_monitoring())
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_coro in checks:
        try:
            result = await check_coro
            if result:
                passed += 1
                logger.info(f"✅ {check_name}: PASSED")
            else:
                logger.error(f"❌ {check_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {check_name}: ERROR - {e}")
    
    # Create system files
    create_systemd_service()
    create_nginx_config()
    
    # Final report
    logger.info(f"\n🎯 Deployment Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("🎉 All checks passed! Ready for production deployment.")
        logger.info("\nNext steps:")
        logger.info("1. Copy systemd service to /etc/systemd/system/")
        logger.info("2. Configure nginx with the provided config")
        logger.info("3. Set up SSL certificates")
        logger.info("4. Enable and start the service")
        logger.info("5. Monitor logs and metrics")
        return True
    else:
        logger.warning("⚠️ Some checks failed. Address issues before production deployment.")
        return False


def print_startup_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════╗
║               Baseball Trade AI                      ║
║            Production Deployment Script              ║
║                                                      ║
║  FastAPI Optimized • Security Enhanced • Monitored  ║
╚══════════════════════════════════════════════════════╝
"""
    print(banner)


async def main():
    """Main deployment script"""
    print_startup_banner()
    
    try:
        success = await run_deployment_validation()
        
        if success:
            logger.info("\n🚀 Production deployment validation completed successfully!")
            logger.info("The optimized FastAPI application is ready for production.")
            sys.exit(0)
        else:
            logger.error("\n❌ Deployment validation failed!")
            logger.error("Please address the issues above before deploying to production.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️ Deployment validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Unexpected error during deployment validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())