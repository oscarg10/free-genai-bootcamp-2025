import asyncio
from ollama import AsyncClient

async def main():
    print("Testing Ollama connection...")
    try:
        async with AsyncClient(host='http://localhost:11434') as client:
            print("Client created, getting models...")
            response = await client.list()
            print(f"Models: {response}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
