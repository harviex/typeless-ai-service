from openai import OpenAI
import os
import json
from http.server import BaseHTTPRequestHandler

# OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "")
)

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
    def do_GET(self):
        """Handle root path - show usage instructions"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Typeless AI Service</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>✨ Typeless AI Service</h1>
    <p>文本润色API服务，基于OpenRouter免费模型。</p>
    <h2>使用方法</h2>
    <pre>curl -X POST https://typeless-ai-service.vercel.app/api/polish \\
  -H "Content-Type: application/json" \\
  -d '{"text": "嗯，那个，我想去吃饭"}'</pre>
    <h2>功能</h2>
    <ul>
        <li>去除口语化用词</li>
        <li>删除冗余逻辑</li>
        <li>结构化排版</li>
        <li>保持原意</li>
    </ul>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        # Only handle /api/polish
        if self.path != '/api/polish':
            self._send_json({'error': 'Not found'}, 404)
            return
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            user_text = data.get('text', '')
            
            if not user_text:
                self._send_json({'error': 'Missing text field'}, 400)
                return
            
            # Validate API key
            if not client.api_key:
                self._send_json({'error': 'OPENROUTER_API_KEY not configured'}, 500)
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
