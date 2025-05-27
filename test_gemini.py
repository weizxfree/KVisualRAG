from litellm import completion
import os
import json
import requests
from urllib.parse import urlparse

# 设置 API key
os.environ["GEMINI_API_KEY"] = "AIzaSyC-bGA1H3RRL8nyXTsXlx4tPYz8V4slZOc"

def check_network_connectivity():
    """检查网络连接性"""
    print("\n=== 网络连接测试 ===")
    test_urls = [
        "https://generativelanguage.googleapis.com",
        "https://www.google.com",
        "https://www.baidu.com"  # 作为对比
    ]
    
    # 设置代理
    proxies = {
        "http": "socks5h://127.0.0.1:1080",  # 使用 SOCKS5 代理
        "https": "socks5h://127.0.0.1:1080"
    }
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5, proxies=proxies)
            print(f"✅ {url} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - 连接失败: {str(e)}")
            if "generativelanguage.googleapis.com" in url:
                print("提示: 无法连接到 Gemini API，请检查：")
                print("1. 是否已建立 SSH 隧道: ssh -L 7890:localhost:7890 administrator@36.155.18.243")
                print("2. Mac 上的代理是否正常运行")
                print("3. 是否安装了 requests[socks] 包: pip install -U 'requests[socks]'")

def test_basic_completion():
    """测试基本的文本补全"""
    try:
        # 设置代理
        proxies = {
            "http": "socks5h://127.0.0.1:1080",
            "https": "socks5h://127.0.0.1:1080"
        }
        
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": "你好，请做个自我介绍"}],
            api_base="https://generativelanguage.googleapis.com/v1beta/models",
            proxies=proxies
        )
        print("\n=== 基本文本补全测试 ===")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"基本补全测试失败: {str(e)}")
        if "Connection" in str(e) or "timeout" in str(e).lower():
            print("提示: 这可能是网络连接问题，请检查：")
            print("1. 是否已建立 SSH 隧道: ssh -L 7890:localhost:7890 administrator@36.155.18.243")
            print("2. Mac 上的代理是否正常运行")
            print("3. 是否安装了 requests[socks] 包: pip install -U 'requests[socks]'")
        return False

def test_streaming_completion():
    """测试流式输出"""
    try:
        proxies = {
            "http": "socks5h://127.0.0.1:1080",
            "https": "socks5h://127.0.0.1:1080"
        }
        
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": "请用中文写一首短诗"}],
            stream=True,
            api_base="https://generativelanguage.googleapis.com/v1beta/models",
            proxies=proxies
        )
        print("\n=== 流式输出测试 ===")
        for chunk in response:
            if hasattr(chunk, 'choices') and chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
        print("\n")
        return True
    except Exception as e:
        print(f"流式输出测试失败: {str(e)}")
        return False

def test_with_system_prompt():
    """测试带系统提示的对话"""
    try:
        proxies = {
            "http": "socks5h://127.0.0.1:1080",
            "https": "socks5h://127.0.0.1:1080"
        }
        
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的AI助手，擅长用简洁的语言回答问题。"
            },
            {
                "role": "user",
                "content": "请解释什么是人工智能"
            }
        ]
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=messages,
            api_base="https://generativelanguage.googleapis.com/v1beta/models",
            proxies=proxies
        )
        print("\n=== 系统提示测试 ===")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"系统提示测试失败: {str(e)}")
        return False

def test_with_tools():
    """测试带工具的调用"""
    try:
        proxies = {
            "http": "socks5h://127.0.0.1:1080",
            "https": "socks5h://127.0.0.1:1080"
        }
        
        tools = [{"googleSearch": {}}]
        response = completion(
            model="gemini/gemini-2.0-flash",
            messages=[{"role": "user", "content": "今天北京的天气怎么样？"}],
            tools=tools,
            api_base="https://generativelanguage.googleapis.com/v1beta/models",
            proxies=proxies
        )
        print("\n=== 工具调用测试 ===")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"工具调用测试失败: {str(e)}")
        return False

def main():
    """运行所有测试"""
    # 首先检查网络连接
    check_network_connectivity()
    
    tests = [
        ("基本补全", test_basic_completion),
        ("流式输出", test_streaming_completion),
        ("系统提示", test_with_system_prompt),
        ("工具调用", test_with_tools)
    ]
    
    print("\n开始 Gemini API 测试...")
    results = []
    
    for test_name, test_func in tests:
        print(f"\n执行测试: {test_name}")
        success = test_func()
        results.append((test_name, success))
    
    print("\n=== 测试结果汇总 ===")
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")

if __name__ == "__main__":
    main() 