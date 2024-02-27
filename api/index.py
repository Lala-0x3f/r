import requests
from flask import Flask, send_file, request, redirect
from io import BytesIO
from random import randint
import re

app = Flask(__name__)


def fetch_single_img(response_json):
    file_url = response_json.get("preview_file_url")

    if file_url:
        # 使用requests库获取图片数据
        image_response = requests.get(file_url)

        # 检查图片请求是否成功
        if image_response.status_code == 200:
            # 将图片数据转换为BytesIO对象
            image_data = BytesIO(image_response.content)

            # 使用send_file函数发送图片
            return send_file(image_data, mimetype="image/jpeg")
        else:
            return "Failed to fetch image", 404
    else:
        return "file url not found in JSON", 404


@app.route("/")
def hone():
    return redirect("https://www.douyin.com/", code=302)


@app.route("/i/<path:proxy_file_path>.jpg")
def get_image_by_path(proxy_file_path):
    full_image_url = f"https://cdn.donmai.us/{proxy_file_path}.jpg"
    # 使用requests库获取远程图片数据
    response = requests.get(full_image_url)
    # 检查请求是否成功
    if response.status_code == 200:
        # 将图片数据转换为BytesIO对象
        image_data = BytesIO(response.content)

        # 使用send_file函数发送图片
        return send_file(image_data, mimetype="image/jpeg")
    else:
        return "Failed to fetch image", 404


@app.route("/r/<int:image_id>.jpg")
def get_image_by_id(image_id):
    # 构建JSON文件的URL
    json_url = f"https://danbooru.donmai.us/posts/{image_id}.json"

    print("json url is" + json_url)

    # 使用requests库获取JSON数据
    response = requests.get(json_url)

    if response.status_code != 200:
        response = requests.get(json_url, verify=False)

    # 检查请求是否成功
    if response.status_code == 200:
        return fetch_single_img(response.json())

    else:
        return "Failed to fetch JSON data", 404


@app.route("/<string:ratio>/<string:search_tag>.jpg")
def get_img_by_search(ratio: str, search_tag: str):
    if re.match(r"^\d+-\d+$", ratio):
        min_img_id = randint(0, 7000000)
        max_img_id = min_img_id + 1000000
        img_tag = search_tag  # TODO:模糊匹配
        img_ratio = ratio.replace("-", "/")
        json_url = f"https://danbooru.donmai.us/posts/random.json?tags=score:%3E50+ratio:{img_ratio}+rating:s,g+limit:1+id:%3E{min_img_id}+id:%3C{max_img_id}+{img_tag}"
        if json_url:
            print(json_url)
            print("Fetching...")
            response = requests.get(json_url)
            if response.status_code != 200:
                response = requests.get(json_url, verify=False)

            # 检查请求是否成功
            if response.status_code == 200:
                return fetch_single_img(response.json())

            else:
                return "Failed to fetch JSON data", 404
        else:
            return "Error requery Format", 404
    else:
        return "Error ratio", 404


app.run(debug=True)