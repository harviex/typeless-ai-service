from openai import OpenAI, APIStatusError
import os
import json
from http.server import BaseHTTPRequestHandler
import sys

# OpenRouter client
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
if not API_KEY:
    print("❌ 严重错误: OPENROUTER_API_KEY 环境变量未配置！", file=sys.stderr)
    sys.exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY
)

SYSTEM_PROMPT = """你是一个语音识别文字润色工具。

输入：语音识别转出的文字（无标点、口语化、可能有错字）。
输出：一段经过润色的规范书面中文。

你必须遵守以下规则：
1. 直接输出润色后的文字，不要输出任何思考过程、分析步骤、中间结果或解释。
2. 不要用"第一步""第二步"等标记你的处理过程。
3. 不要输出任何markdown标记、代码块、标签。

润色规则（默默执行，不要说出来）：
- 添加正确的标点符号（。！？，、）
- 按语义合理分段
- 删除语气词（嗯、啊、那个、然后等）
- 修正错别字和语病
- 保持原意不变

示例：
输入：嗯那个我今天去了一个很好吃的餐厅然后我们点了很多菜
输出：我今天去了一个很好吃的餐厅，然后我们点了很多菜。

输入：我觉得这个方案有问题首先成本太高然后时间来不及
输出：我觉得这个方案有问题。首先，成本太高。其次，时间来不及。
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
    <h1>Typeless AI Service</h1>
    <p>Model: minimax/minimax-m2.5:free</p>
    <p>POST /api/polish</p>
</body></html>
"""
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
                model="minimax/minimax-m2.5:free",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            polished_text = response.choices[0].message.content
            result = polished_text.strip()

            # 去掉markdown代码块
            if result.startswith("```"):
                lines = result.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                result = "\n".join(lines).strip()

            # 去掉思考过程：截取最后一个"输出："之后的内容
            if "输出：" in result:
                idx = result.rfind("输出：")
                result = result[idx + 3:].strip()

            # 去重：连续相同的行只保留一行
            lines = result.split("\n")
            deduped = []
            for line in lines:
                stripped = line.strip()
                if stripped and deduped and deduped[-1].strip() == stripped:
                    continue
                deduped.append(line)
            result = "\n".join(deduped).strip()

            self._send_json({'polished_text': result})

        except APIStatusError as e:
            if e.status_code == 402:
                self._send_json({'error': 'API额度已用尽(402)，请在OpenRouter充值'}, 402)
            else:
                self._send_json({'error': f'API错误: {str(e)}'}, e.status_code)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))