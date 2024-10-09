from flask import Flask, request, render_template, redirect, url_for
import requests
import os

app = Flask(__name__)
apiurl = 'https://api.openai-proxy.com/v1'

# 设置OpenAI的API密钥
openai_api_key = os.getenv('OPENAI_API_KEY')

# 设置文件上传目录
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def upload_form():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # 保存上传的文件
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)

            # 上传文件到OpenAI
            headers = {
                'Authorization': f'Bearer {openai_api_key}'
            }
            files = {'file': open(filename, 'rb')}
            data = {'purpose': 'fine-tune'}

            response = requests.post(
                f'{apiurl}/files',
                headers=headers,
                files=files,
                data=data
            )

            if response.status_code == 200:
                return redirect(url_for('list_files'))
            else:
                return f'Error uploading file: {response.text}', 500

@app.route('/list')
def list_files():
    # 获取已上传文件的列表
    headers = {
        'Authorization': f'Bearer {openai_api_key}'
    }

    response = requests.get(f'{apiurl}/files', headers=headers)

    if response.status_code == 200:
        files = response.json().get('data', [])
        return render_template('list.html', files=files)
    else:
        return f'Error retrieving files: {response.text}', 500

if __name__ == '__main__':
    app.run(debug=True)