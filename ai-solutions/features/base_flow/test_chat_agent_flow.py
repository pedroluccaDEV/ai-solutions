# test_skill_flow.py
import asyncio
import aiohttp
import json

async def test_skill_flow():
    url = "http://localhost:8000/api/v2/chat/stream"
    
    # Dados do formulário
    data = aiohttp.FormData()
    data.add_field('message', 'busque o clima e mande para pedroluccatrabalho2004@gmail.com')
    data.add_field('flow_type', 'skill')
    data.add_field('skill_ids', json.dumps(['69d506f27b50065f60108c9b']))
    data.add_field('agent_overrides', json.dumps({
        'mcps': ['6894bc021791731bebbe9146', '6894cabfbcf1dbe10ca8b0e7'],
        'tools': [],
        'knowledgeBase': [],
        'model': '1'
    }))
    
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjcwZmM5YzU0YjhiMjQyMWZmMTgyOTgxNTQyZmQ0NjRlOWJlYzM1NDUiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiUGVkcm8gTHVjY2EgR29uw6dhbHZlcyBkZSBBcmF1am8iLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSXRWWDgyVUY5VWhRVVExaTlFXy1LSjRCc2xmbkwyWGxkSlpaYl9XUHRSWjA4NGpRPXM5Ni1jIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL3NhcGhpZW5zYWkiLCJhdWQiOiJzYXBoaWVuc2FpIiwiYXV0aF90aW1lIjoxNzc0OTYwNDI2LCJ1c2VyX2lkIjoicFFUd1hiUmZWRVB2cDFLOFFySDM4QkdBZHVBMiIsInN1YiI6InBRVHdYYlJmVkVQdnAxSzhRckgzOEJHQWR1QTIiLCJpYXQiOjE3NzU3NDMwODUsImV4cCI6MTc3NTc0NjY4NSwiZW1haWwiOiJwZWRyb2x1Y2NhYXJhdWpvMjAwNEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjEwMzUwNjA4MzU1OTQ3NTQ0OTYwMiJdLCJlbWFpbCI6WyJwZWRyb2x1Y2NhYXJhdWpvMjAwNEBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJnb29nbGUuY29tIn19.Z_9hbEdjoXIL2ygG6hZ7bLk3hh6XJiBgojC3di-imrIE48JnC9CBQXFIUrNawOylupXJ91p7DJoyKVOB--vK-pqgdqmvnIImt0DZv7mAHZkJogLySJQijQwq3aqmpIY-Ih3vuDiY_eFDI7p3ZM-SPoS3fjtMk2BUd6nkKxXI-VtoLyzt06xOjXG1fULDBGJdECyk8HFG0_VMnZd3KvGuSf8XN_C6y6SEOAGKlWvC3s2kAe100DDUp9wfwhRoBUrSV7LeMuXq6KboetYUu3yUYQfEmM64I_14dc8aQbfbF0haT0BUW-9kBNSul6NpQQ9b9w4suyGgJb_EUH2GZBJfCg'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as resp:
            async for line in resp.content:
                if line.startswith(b'data: '):
                    event = json.loads(line[6:])
                    print(f"Evento: {event.get('type')}")
                    if event.get('type') == 'executor_chunk':
                        print(event.get('data', {}).get('content', ''), end='')
                    elif event.get('type') == 'flow_complete':
                        print("\n✅ Concluído!")
                        break

if __name__ == "__main__":
    asyncio.run(test_skill_flow())