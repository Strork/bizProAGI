import requests
import os

url_base = "https://api.openai-proxy.com/v1"

# 设置OpenAI的API密钥
openai_api_key = os.getenv('OPENAI_API_KEY')

# 定义API URL和头部信息
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai_api_key}",
    "OpenAI-Beta": "assistants=v2"
}



def create_assistants():
    # 定义要发送的数据
    data = {
        "instructions": "你是一个博学多识的助手，能分析文件内容、解答问题。",
        "name": "assistants-4o",
        "tools": [{"type": "file_search"}],
        "model": "gpt-4o"
    }

    # 发送POST请求
    response = requests.post(f"{url_base}/assistants", json=data, headers=headers)

    # 打印响应内容
    print(response.json())