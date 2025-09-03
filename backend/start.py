"""
Production startup script for the Trading Analysis Platform
Handles graceful startup, shutdown, and process management
"""

import asyncio
import signal
import sys
import uvicorn
from multiprocessing import cpu_count

from app.core.config import settings
from app.core.logging_config import setup_logging, get_context_logger

# Setup logging before importing other modules
setup_logging()
logger = get_context_logger(__name__)


class GracefulShutdown:
    """Handle graceful shutdown of the application"""
    
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(
            f"🔄 Received shutdown signal: {signum}",
            extra={"signal": signum}
        )
        self.shutdown_event.set()
    
    async def wait_for_shutdown(self):
        """Wait for shutdown event"""
        await self.shutdown_event.wait()


def get_worker_count() -> int:
    """Calculate optimal number of workers based on CPU cores"""
    cpu_cores = cpu_count()
    
    # For Railway and containerized environments
    if settings.WORKERS > 0:
        workers = settings.WORKERS
    else:
        # Default: 2 * CPU cores + 1 (but cap at 8 for cost efficiency)
        workers = min(2 * cpu_cores + 1, 8)
    
    logger.info(
        "👷 Worker configuration",
        extra={
            "cpu_cores": cpu_cores,
            "workers": workers,
            "environment": settings.ENVIRONMENT
        }
    )
    
    return workers


def get_uvicorn_config() -> dict:
    """Get Uvicorn configuration based on environment"""
    
    config = {
        "app": "app.main:app",
        "host": settings.HOST,
        "port": settings.PORT,
        "log_config": None,  # We handle logging ourselves
        "access_log": False,  # We log requests in middleware
    }
    
    if settings.is_production:
        # Production configuration
        config.update({
            "workers": get_worker_count(),
            "worker_class": "uvicorn.workers.UvicornWorker",
            "preload_app": True,
            "max_requests": 1000,  # Restart workers after 1000 requests
            "max_requests_jitter": 100,
            "timeout_keep_alive": 5,
            "timeout_graceful_shutdown": 30,
        })
    else:
        # Development configuration
        config.update({
            "reload": True,
            "reload_dirs": ["app"],
            "log_level": "debug" if settings.DEBUG else "info",
        })
    
    return config


async def startup_checks():
    """Perform startup health checks"""
    logger.info("🔧 Performing startup checks...")
    
    try:
        # Import here to ensure logging is setup
        from app.core.database import init_db, get_db_health
        from app.core.redis_client import init_redis, get_redis_health
        
        # Initialize database
        await init_db()
        db_healthy, db_status = await get_db_health()
        
        if not db_healthy:
            logger.error(
                "❌ Database health check failed during startup",
                extra={"status": db_status}
            )
            sys.exit(1)
        
        # Initialize Redis (optional)
        await init_redis()
        redis_healthy, redis_status = await get_redis_health()
        
        if not redis_healthy:
            logger.warning(
                "⚠️  Redis health check failed - caching will be disabled",
                extra={"status": redis_status}
            )
        
        logger.info("✅ All startup checks completed successfully")
        
    except Exception as e:
        logger.error(
            "❌ Startup checks failed",
            extra={"error": str(e)},
            exc_info=True
        )
        sys.exit(1)


def main():
    """Main entry point"""
    logger.info(
        f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}",
        extra={
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "host": settings.HOST,
            "port": settings.PORT
        }
    )
    
    # Get Uvicorn configuration
    config = get_uvicorn_config()
    
    try:
        if settings.is_production:
            # Production: Use Gunicorn with Uvicorn workers
            import gunicorn.app.base
            
            class StandaloneApplication(gunicorn.app.base.BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()
                
                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)
                
                def load(self):
                    return self.application
            
            # Gunicorn options
            options = {
                'bind': f"{config['host']}:{config['port']}",
                'workers': config['workers'],
                'worker_class': 'uvicorn.workers.UvicornWorker',
                'worker_connections': 1000,
                'max_requests': config.get('max_requests', 1000),
                'max_requests_jitter': config.get('max_requests_jitter', 100),
                'timeout': 120,
                'keepalive': 5,
                'preload_app': True,
                'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
            }
            
            # Run startup checks
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(startup_checks())
            loop.close()
            
            # Start Gunicorn
            StandaloneApplication("app.main:app", options).run()
            
        else:
            # Development: Use Uvicorn directly
            async def run_with_startup():
                await startup_checks()
                
                # Setup graceful shutdown
                shutdown_handler = GracefulShutdown()
                
                # Create server
                server_config = uvicorn.Config(**config)
                server = uvicorn.Server(server_config)
                
                # Run server with graceful shutdown
                try:
                    await asyncio.gather(
                        server.serve(),
                        shutdown_handler.wait_for_shutdown()
                    )
                except Exception as e:
                    logger.error(
                        "❌ Server error",
                        extra={"error": str(e)},
                        exc_info=True
                    )
                finally:
                    logger.info("🔄 Server shutting down...")
            
            asyncio.run(run_with_startup())
            
    except KeyboardInterrupt:
        logger.info("👋 Received keyboard interrupt - shutting down gracefully")
    except Exception as e:
        logger.error(
            "❌ Unexpected error during startup",
            extra={"error": str(e)},
            exc_info=True
        )
        sys.exit(1)
    
    logger.info("✅ Application shutdown complete")


if __name__ == "__main__":
    main()