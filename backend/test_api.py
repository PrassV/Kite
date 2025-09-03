#!/usr/bin/env python3
"""
Quick API test script to verify the FastAPI backend is working
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_api_endpoints():
    """Test basic API endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Trading Analysis Platform API")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Root endpoint
        print("1. Testing root endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            print("   ✅ Root endpoint working")
        except Exception as e:
            print(f"   ❌ Root endpoint failed: {e}")
        
        print()
        
        # Test 2: Health check
        print("2. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            health_data = response.json()
            print(f"   Health Status: {health_data.get('status', 'unknown')}")
            print("   ✅ Health endpoint working")
        except Exception as e:
            print(f"   ❌ Health endpoint failed: {e}")
        
        print()
        
        # Test 3: Detailed health check
        print("3. Testing detailed health endpoint...")
        try:
            response = await client.get(f"{base_url}/health/detailed")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                detailed_health = response.json()
                print(f"   System CPU: {detailed_health.get('system', {}).get('cpu_usage_percent', 'N/A')}%")
                print(f"   System Memory: {detailed_health.get('system', {}).get('memory_usage_percent', 'N/A')}%")
                print(f"   Database: {detailed_health.get('services', {}).get('database', {}).get('status', 'N/A')}")
                print(f"   Redis: {detailed_health.get('services', {}).get('redis', {}).get('status', 'N/A')}")
                print("   ✅ Detailed health endpoint working")
        except Exception as e:
            print(f"   ❌ Detailed health endpoint failed: {e}")
        
        print()
        
        # Test 4: Public stats (no auth required)
        print("4. Testing public stats endpoint...")
        try:
            response = await client.get(f"{base_url}/monitoring/public/stats")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                stats = response.json()
                print(f"   Service: {stats.get('service', 'N/A')}")
                print(f"   Version: {stats.get('version', 'N/A')}")
                print(f"   Environment: {stats.get('environment', 'N/A')}")
                print(f"   Uptime: {stats.get('uptime_hours', 0):.2f} hours")
                print("   ✅ Public stats endpoint working")
        except Exception as e:
            print(f"   ❌ Public stats endpoint failed: {e}")
        
        print()
        
        # Test 5: Auth login (should work without credentials)
        print("5. Testing auth login endpoint...")
        try:
            response = await client.post(f"{base_url}/auth/login", json={})
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                auth_data = response.json()
                print(f"   Login URL generated: {bool(auth_data.get('login_url'))}")
                print("   ✅ Auth login endpoint working")
            else:
                print("   ⚠️  Auth login returned non-200 status (expected if Kite credentials not set)")
        except Exception as e:
            print(f"   ❌ Auth login endpoint failed: {e}")
        
        print()
        
        # Test 6: Protected endpoint (should fail without auth)
        print("6. Testing protected endpoint (should fail)...")
        try:
            response = await client.post(f"{base_url}/analysis/RELIANCE", json={
                "symbol": "RELIANCE",
                "analysis_type": "quick"
            })
            print(f"   Status: {response.status_code}")
            if response.status_code == 401:
                print("   ✅ Protected endpoint correctly requires authentication")
            else:
                print(f"   ⚠️  Unexpected status code: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Protected endpoint test failed: {e}")
        
        print()
        
        # Test 7: OpenAPI docs (in development)
        print("7. Testing API documentation...")
        try:
            response = await client.get(f"{base_url}/docs")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ API documentation available at /docs")
            elif response.status_code == 404:
                print("   ℹ️  API documentation disabled (production mode)")
            else:
                print(f"   ⚠️  Unexpected status code: {response.status_code}")
        except Exception as e:
            print(f"   ❌ API documentation test failed: {e}")
    
    print()
    print("=" * 50)
    print("🏁 API test completed!")
    print()
    print("Next steps:")
    print("1. Check the logs for any errors")
    print("2. Set up Kite Connect API credentials in .env")
    print("3. Configure PostgreSQL and Redis connections")
    print("4. Test the full authentication flow")
    print("5. Try the analysis endpoints with proper authentication")


if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the FastAPI server is running: python -m uvicorn app.main:app --reload")
    print()
    
    try:
        asyncio.run(test_api_endpoints())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")