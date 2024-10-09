import requests
import json
import os

open_api_key = os.getenv('OPENAI_API_KEY')

base_url = "https://api.openai-proxy.com/v1"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {open_api_key}",
    "OpenAI-Beta": "assistants=v2"
}
thread_id = ""

# 创建助手
def create_assistant():
    # 设置API URL和头部信息
    url = f"{base_url}/assistants"

    # 定义助手的参数
    data = {
        "name": "Financial Analyst Assistant",
        "instructions": "You are an expert financial analyst. Use your knowledge base to answer questions about audited financial statements.",
        "tools": [{"type": "file_search"}],
        "model": "gpt-4o"
    }

    # 发送POST请求
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # 处理响应
    if response.status_code == 200:
        print("助手创建成功:", response.json())
    else:
        print("创建助手失败:", response.status_code, response.text)

def delete_thread(thread_id):
    url = f"{base_url}/threads/{thread_id}"
    print(url)
    response = requests.delete(url, headers=headers)
    if response.status_code == 200:
        print(f"thread：{thread_id}成功删除")
    else:
        print("删除线程失败:", response.status_code, response.text)

def get_thread():
    url = f"{base_url}/threads"
    print(url)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        threads = response.json()
        print("线程列表:")
        for thread in threads['data']:
            print(f"ID: {thread['id']}, Created At: {thread['created_at']}, Updated At: {thread['updated_at']}")
    else:
        print("获取线程列表失败:", response.status_code, response.text)


def create_thread():
    url = f"{base_url}/threads"
    data = {}
    # 发送POST请求
    response = requests.post(url, headers=headers, json=data)

    # 检查响应状态码
    if response.status_code == 200:
        print("线程创建成功:", response.json())
        thread_id = response.json().get("id")
        print(thread_id)
        delete_thread(thread_id)
    else:
        print("创建线程失败:", response.status_code, response.text)

get_thread()



# # 创建向量存储，上传文件
# def create_vector_store(name):
#     url = f"{base_url}/vector_stores"
#     data = {
#         "name": name
#     }
#     response = requests.post(url, headers=headers, json=data)
#     return response.json()

# def upload_files(vector_store_id, file_paths):
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {open_api_key}",
#         "OpenAI-Beta": "assistants=v2"
#     }
#     url = f"{base_url}/vector_stores/{vector_store_id}/files"
#     file_batches = []
#     for file_path in file_paths:
#         with open(file_path, 'rb') as file:
#             files = {'file': (os.path.basename(file_path), file)}
#             response = requests.post(url, headers=headers, files=files)
#             file_batches.append(response.json())
#     return file_batches


