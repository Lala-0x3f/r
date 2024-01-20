import requests
from flask import Flask, send_file, request
from io import BytesIO

app = Flask(__name__)


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

@app.route('/i/<path:proxy_file_path>.jpg')
def get_image_by_path(proxy_file_path):
    full_image_url = f'https://cdn.donmai.us/{proxy_file_path}.jpg'
    # 使用requests库获取远程图片数据
    response = requests.get(full_image_url) 
    # 检查请求是否成功
    if response.status_code == 200:
        # 将图片数据转换为BytesIO对象
        image_data = BytesIO(response.content)
        
        # 使用send_file函数发送图片
        return send_file(image_data, mimetype='image/jpeg')
    else:
        return 'Failed to fetch image', 404




@app.route('/r/<int:image_id>.jpg')
def get_image_by_id(image_id):
    # 构建JSON文件的URL
    json_url = f'https://danbooru.donmai.us/posts/{image_id}.json'
    
    print('json url is'+json_url)

    # 使用requests库获取JSON数据
    response = requests.get(json_url,headers = headers)

    # 检查请求是否成功
    if response.status_code == 200:
        # 解析JSON数据
        json_data = response.json()

        # 获取file_url字段
        file_url = json_data.get('file_url')

        if file_url:

            # 使用requests库获取图片数据
            image_response = requests.get(file_url)

            # 检查图片请求是否成功
            if image_response.status_code == 200:
                # 将图片数据转换为BytesIO对象
                image_data = BytesIO(image_response.content)
                
                # 使用send_file函数发送图片
                return send_file(image_data, mimetype='image/jpeg')
            else:
                return 'Failed to fetch image', 404
        else:
            return 'file_url not found in JSON', 404
    else:
        return 'Failed to fetch JSON data', 404

