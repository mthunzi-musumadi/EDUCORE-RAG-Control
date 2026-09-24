import urllib.request
import json
import time

payload = {
    'model': 'educore-enterprise-all',
    'messages': [
        {
            'role': 'user',
            'content': 'Analyze this conversation and provide:\n1. The detected language of the conversation\n2. A concise title in the detected language (5 words or less, no punctuation or quotation)\n\nUser: What are the admission rules for Solwezi campus?'
        }
    ],
    'stream': False
}

t0 = time.time()
req = urllib.request.Request(
    'http://127.0.0.1:8000/v1/chat/completions',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode('utf-8'))
latency = (time.time() - t0) * 1000

print(f"Status: {res.status}")
print(f"Latency: {latency:.2f} ms")
print(f"Content: {data['choices'][0]['message']['content']}")
