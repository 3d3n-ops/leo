import asyncio
import httpx

async def test_endpoints():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test basic endpoints
        print("Testing /docs...")
        try:
            response = await client.get(f"{base_url}/docs")
            print(f"✅ /docs: {response.status_code}")
        except Exception as e:
            print(f"❌ /docs: {e}")
        
        print("\nTesting /tasks...")
        try:
            response = await client.get(f"{base_url}/tasks")
            print(f"✅ /tasks: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"❌ /tasks: {e}")
        
        # Test ingest (this might fail without proper setup)
        print("\nTesting /ingest...")
        try:
            response = await client.post(
                f"{base_url}/ingest", 
                params={"url": "https://docs.python.org/3/"}
            )
            print(f"✅ /ingest: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"❌ /ingest: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())