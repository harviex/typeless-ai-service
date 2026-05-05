from openai import OpenAI
from http.server import BaseHTTPRequestHandler
import json
import os

# OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY_HERE")
)

# System prompt for text polishing
SYSTEM_PROMPT = """你是一个专业的文本润色助手。请对用户输入的文字进行以下处理：

1. **去除口语化用词**：删除"嗯、啊、那个、然后"等口头禅，转为书面语。
2. **删除冗余逻辑**：去除重复语句、自相矛盾或逻辑混乱的内容，保证文字通顺。
3. **结构化排版**：
   - 将长文分段，每段不超过3-4行。
   - 使用**序号标签**（一、二、三...）或**分级序号**（1.1, 1.2, 2.1...）。
   - 如果是清单/建议，使用Markdown列表（- 或 1.）。
4. **保持原意**：润色后必须保留原文本的核心信息和意图。

直接返回润色后的文字，不要添加任何解释或开场白。
"""

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            user_text = data.get('text', '')
            
            if not user_text:
                self._send_json({'error': 'Missing text field'}, 400)
                return
            
            # Call OpenRouter API
            response = client.chat.completions.create(
                model="meta-llama/llama-3.3-8b-instruct:free",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            polished_text = response.choices[0].message.content
            
            self._send_json({'polished_text': polished_text})
            
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
