from openai import OpenAI, APIStatusError
import os
import json
from http.server import BaseHTTPRequestHandler

# OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "")
)

SYSTEM_PROMPT = """你是语音识别文字转规范书面语的工具。输入是语音识别结果（无标点、口语化、可能有错字）。输出是经过处理后的规范书面中文。

你的处理规则，严格按以下顺序执行：

第一步：加标点
- 每句结尾必须有句号"。"、问号"？"或感叹号"！"
- 陈述句用句号。疑问语气（含"吗/呢/什么/怎么/哪里/为什么/是不是/有没有"等）用问号。感叹语气用感叹号。
- 句子中间适当位置加逗号"，"分隔
- 并列词组之间用顿号"、"

第二步：分段
- 如果内容涉及多个话题/要点/步骤，必须分段
- 每段1~4行，不同话题之间空一行
- 并列要点用"一、二、三、"编号
- 步骤流程用"第一步、第二步、"编号
- 建议清单用短横线列表"- xxx"

第三步：去口语
- 删除所有语气词：嗯、呃、啊、哦、哎、嘛、哇、唉、哼、呵、嘿嘿、嘻嘻
- 删除填充词：那个、嗯...、就是、然后（除非表示时间顺序）、的话、哦对了、对了
- 删除重复的词句

第四步：修正
- 修正明显的错别字
- 修正语病和不通顺的地方
- 转为规范书面语表达

约束条件：
- 不改变原文的核心意思、观点、态度
- 不添加原文中没有的新信息
- 如果原文已经规范，原样返回即可
- 直接返回处理结果，不要任何解释或开场白

示例输入1：今天天气不错我们去公园散步吧你觉得呢
示例输出1：今天天气不错，我们去公园散步吧？你觉得呢？

示例输入2：今天我们要讨论三个问题第一个是关于预算的问题我觉得应该增加十万第二个是关于人员安排的问题需要调整一下第三个是关于时间安排的问题我想把会议推迟到下周你们觉得怎么样嗯啊那个
示例输出2：
今天我们要讨论三个问题。

一、关于预算问题，我觉得应该增加十万。

二、关于人员安排问题，需要调整一下。

三、关于时间安排问题，我想把会议推迟到下周。你们觉得怎么样？

示例输入3：我觉得这个方案还是有一些问题的首先就是成本太高了然后就是时间上来不及嗯你觉得呢我们是不是应该再讨论一下
示例输出3：
我觉得这个方案还是有一些问题的。

首先，成本太高。其次，时间上来不及。你觉得呢？我们是不是应该再讨论一下？
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
    <p>Model: deepseek/deepseek-v4-flash:free</p>
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
                model="deepseek/deepseek-v4-flash:free",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            polished_text = response.choices[0].message.content
            self._send_json({'polished_text': polished_text})

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