#!/usr/bin/env python3
"""
Typeless AI Service - 本地测试脚本
展示润色效果，无需真实OpenRouter Key
"""

import json
import re

# 模拟OpenRouter润色（用规则引擎代替）
def mock_polish(text):
    """模拟AI润色：去口语化、分段、分点"""
    
    # 1. 去除口语化用词
    oral_words = ["嗯", "啊", "那个", "然后", "就是", "那个啥", "呃"]
    result = text
    for word in oral_words:
        result = result.replace(word, "")
    
    # 2. 删除重复语句（简单去重）
    sentences = re.split(r'[。！？]', result)
    seen = set()
    unique = []
    for s in sentences:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            unique.append(s)
    result = '。'.join(unique) + '。' if unique else result
    
    # 3. 分段、分点
    # 如果文本较长，分成段落
    if len(result) > 100:
        # 按主题分段（简单按句号分割）
        parts = result.split('。')
        if len(parts) > 3:
            # 结构化输出
            output = "一、主要观点\n"
            for i, part in enumerate(parts[:3], 1):
                if part.strip():
                    output += f"{i}. {part.strip()}。\n"
            if len(parts) > 3:
                output += "\n二、补充说明\n"
                for i, part in enumerate(parts[3:], 1):
                    if part.strip():
                        output += f"{i}. {part.strip()}。\n"
            return output
    
    return result

# 测试用例
test_cases = [
    {
        "input": "嗯，那个我想说一下，今天天气真不错，然后我就想出去走走，然后我又觉得可能要下雨，所以我还是在家呆着吧，在家呆着吧，看看书什么的，对了还有那个喝水很重要，要多喝水。",
        "expected": "结构化、去口语化"
    },
    {
        "input": "那个，这个项目我觉得吧，首先我们需要做A，然后做B，然后做C，然后那个D也很重要，还有就是E也不能忘，然后还有F，对了G也要做。",
        "expected": "分点列出，清晰结构化"
    },
    {
        "input": "呃，今天开会讨论了几个问题，第一个是预算，第二个是人员，第三个是时间表，还有就是那个预算可能不够，预算需要再申请。",
        "expected": "去重，结构化"
    }
]

print("=" * 70)
print("Typeless AI Service - 润色效果测试")
print("=" * 70)

for i, case in enumerate(test_cases, 1):
    print(f"\n测试用例 {i}:")
    print(f"输入: {case['input'][:50]}...")
    print(f"期望: {case['expected']}")
    print("\n润色后:")
    polished = mock_polish(case['input'])
    print(polished)
    print("-" * 70)

# 模拟API调用
print("\n" + "=" * 70)
print("模拟 API 调用: POST /api/polish")
print("=" * 70)

test_text = test_cases[0]['input']
print(f"\n请求体:")
print(json.dumps({"text": test_text}, ensure_ascii=False, indent=2))

print(f"\n响应体:")
print(json.dumps({"polished_text": mock_polish(test_text)}, ensure_ascii=False, indent=2))

print("\n" + "=" * 70)
print("✅ 测试完成！实际部署时将调用OpenRouter API进行真实润色。")
print("=" * 70)
