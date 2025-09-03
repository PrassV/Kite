# Trading Analysis Platform - FastAPI Backend

Production-ready FastAPI backend for comprehensive stock market analysis with Kite Connect integration.

## Features

- 🚀 **FastAPI Framework**: High-performance async API with automatic OpenAPI documentation
- 🔐 **JWT Authentication**: Secure authentication with Kite Connect OAuth integration
- 📊 **Comprehensive Analysis**: Advanced market analysis with patterns, Fibonacci, and volume analysis
- 🔄 **Redis Caching**: High-performance caching with configurable TTL
- 🗄️ **PostgreSQL Integration**: Scalable database with async SQLAlchemy
- ⚡ **Rate Limiting**: Configurable rate limiting per endpoint and user
- 📈 **Real-time Data**: Integration with Kite Connect for live market data
- 🐳 **Docker Support**: Production-ready containerization
- 🚂 **Railway Deployment**: Optimized for Railway cloud platform
- 📝 **Structured Logging**: JSON logging with request tracing
- 🔍 **Health Monitoring**: Comprehensive health checks and metrics

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Kite Connect API credentials

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd trading_platform/backend
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application**
```bash
# Development
python -m uvicorn app.main:app --reload

# Production
python start.py
```

### Docker Setup

```bash
# Build image
docker build -t trading-platform-api .

# Run container
docker run -p 8000:8000 --env-file .env trading-platform-api
```

## API Documentation

When running in development mode, API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Environment Variables

### Required Variables

```bash
# Kite Connect API
KITE_API_KEY=your-kite-api-key
KITE_API_SECRET=your-kite-api-secret

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/trading_platform
# OR individual components:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_platform
DB_USER=postgres
DB_PASSWORD=password

# Redis (optional but recommended)
REDIS_URL=redis://localhost:6379/0
# OR individual components:
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Optional Variables

See `.env.example` for all available configuration options.

## API Endpoints

### Authentication
- `POST /auth/login` - Initiate Kite Connect OAuth
- `POST /auth/callback` - Handle OAuth callback
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout user

### Analysis
- `POST /analysis/{symbol}` - Comprehensive stock analysis
- `GET /analysis/{symbol}/quick` - Quick analysis
- `GET /analysis/history` - Analysis history
- `DELETE /analysis/{symbol}/cache` - Clear analysis cache

### Stocks
- `GET /stocks/search` - Search stocks
- `GET /stocks/quote/{symbol}` - Get stock quote
- `GET /stocks/quotes` - Get multiple quotes
- `GET /stocks/market-status` - Market status
- `GET /stocks/watchlist` - User watchlist
- `POST /stocks/watchlist` - Add to watchlist

### Health
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system metrics
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

## Analysis Features

### Comprehensive Analysis
- **Trendline Detection**: Automated support/resistance identification
- **Chart Patterns**: Triangles, flags, head & shoulders, double tops/bottoms
- **Volume Analysis**: Volume confirmation and anomaly detection  
- **Fibonacci Analysis**: Retracements and extensions with trend-aware calculations
- **Trading Opportunities**: Entry/exit points with risk management

### Analysis Types
- `COMPREHENSIVE` - Full analysis with all components
- `QUICK` - Fast analysis for real-time decisions
- `PATTERNS` - Chart pattern detection only
- `FIBONACCI` - Fibonacci analysis only
- `VOLUME` - Volume analysis only
- `TRENDLINES` - Trendline analysis only

## Performance & Scalability

### Caching Strategy
- **Analysis Results**: 5-minute TTL (configurable)
- **Stock Quotes**: 1-minute TTL
- **Search Results**: 1-hour TTL
- **Redis Fallback**: Graceful degradation when Redis unavailable

### Rate Limiting
- **Analysis Endpoints**: 20 requests/minute per user
- **Auth Endpoints**: 10 requests/minute per IP
- **General Endpoints**: 100 requests/minute per user
- **Configurable**: Per-endpoint and per-user limits

### Database Optimization
- **Connection Pooling**: Configurable pool sizes
- **Async Operations**: Non-blocking database operations
- **Index Strategy**: Optimized queries for analysis history
- **Migration Support**: Alembic for schema management

## Production Deployment

### Railway Deployment

1. **Connect Repository**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

2. **Environment Variables**
Set in Railway dashboard:
- `KITE_API_KEY`
- `KITE_API_SECRET`
- `SECRET_KEY`
- `JWT_SECRET_KEY`

Railway automatically provides:
- `DATABASE_URL` (PostgreSQL)
- `REDIS_URL` (Redis)
- `PORT`

3. **Services Required**
- PostgreSQL database
- Redis instance
- Web service

### Docker Production

```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim
# ... (see Dockerfile for complete configuration)
```

### Health Monitoring

The application provides comprehensive health endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed system metrics
curl http://localhost:8000/health/detailed

# Kubernetes probes
curl http://localhost:8000/health/ready   # Readiness
curl http://localhost:8000/health/live    # Liveness
```

## Security

### Authentication Flow
1. Client initiates OAuth with Kite Connect
2. User authenticates with Kite
3. Callback generates JWT tokens (access + refresh)
4. JWT tokens authorize API requests
5. Refresh tokens enable seamless token renewal

### Security Features
- **JWT Tokens**: Secure stateless authentication
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Pydantic model validation
- **CORS Configuration**: Controlled cross-origin access
- **SQL Injection Protection**: SQLAlchemy ORM
- **Request Logging**: Complete audit trail

## Monitoring & Logging

### Structured Logging
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "Analysis completed",
  "request_id": "req-123",
  "user_id": "user-456",
  "symbol": "RELIANCE",
  "processing_time": "1.234s"
}
```

### Metrics Available
- Request processing times
- Analysis success/failure rates
- Cache hit/miss ratios
- Database connection health
- System resource usage

## Development

### Project Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── models/              # Pydantic models
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   ├── auth/                # Authentication
│   ├── core/                # Configuration
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── migrations/              # Database migrations
├── requirements.txt         # Dependencies
├── Dockerfile              # Container config
└── railway.json            # Deployment config
```

### Testing
```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_analysis.py -v
```

### Code Quality
```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint code
flake8 app/ tests/
mypy app/
```

## API Usage Examples

### Authentication
```python
import httpx

# Initiate login
response = httpx.post("http://localhost:8000/auth/login")
login_url = response.json()["login_url"]

# After OAuth callback, you'll receive tokens
tokens = {
    "access_token": "eyJ...",
    "refresh_token": "eyJ..."
}

# Use tokens for authenticated requests
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
```

### Analysis
```python
# Comprehensive analysis
analysis_request = {
    "symbol": "RELIANCE",
    "analysis_type": "comprehensive",
    "timeframe": "day",
    "analysis_window": 60,
    "include_volume": True,
    "include_patterns": True,
    "include_fibonacci": True
}

response = httpx.post(
    "http://localhost:8000/analysis/RELIANCE",
    json=analysis_request,
    headers=headers
)

analysis_result = response.json()
```

### Stock Data
```python
# Get quote
response = httpx.get(
    "http://localhost:8000/stocks/quote/RELIANCE",
    headers=headers
)

quote = response.json()

# Search stocks
response = httpx.get(
    "http://localhost:8000/stocks/search?query=RELIANCE",
    headers=headers
)

search_results = response.json()
```

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review logs for error details
3. Check health endpoints for system status
4. Ensure all environment variables are set correctly

## License

This project is licensed under the MIT License.