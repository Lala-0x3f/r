import requests
from flask import Flask, send_file, request, redirect
from io import BytesIO
from random import randint
import re

Rating = "s,g,q"
Similarity = 0.15

app = Flask(__name__)


def fuzzy_ratio_get(post: dict, match_ratio_str: str, similarity:float) -> bool:
    mw ,mh = map(int, match_ratio_str.split("/"))
    match_ratio = mw / mh
    h = post["image_height"]
    w = post["image_width"]
    ratio:float = w / h
    if abs(ratio - match_ratio) <= similarity :
        print("------------------")
        print("🔢id -->",post["id"])
        print("💖favourite -->",post["fav_count"])
        print("🪢Fuzzy Ratio -->",abs(ratio - match_ratio))
        print("------------------")
        return True
    else:
        return False


def fuzzy_matching(tag: str) -> str:
    if tag:
        json_url = f"https://danbooru.donmai.us/autocomplete.json?search[type]=tag_query&search[query]={tag}"
        response = requests.get(json_url)
        try:
            value = response.json()[0]["value"]
            print("{", tag, "} is matched to tag: {", value, "}")
            return value
        except:
            print("Error in fuzzy matching tag value of ", tag)
            print(response.json())
            return
    else:
        return


def fetch_single_img(response_json: dict[str, any]):
    print("fetch_single_img start")
    # file_url = response_json.get("file_url")
    file_url = response_json["media_asset"]["variants"][1]["url"]
    print("🎯URL -->",file_url)
    print("🔢id -->",response_json["id"])
    print("💖favourite -->",response_json["fav_count"])
    if file_url:
        # 使用requests库获取图片数据
        image_response = requests.get(file_url)

        # 检查图片请求是否成功
        if image_response.status_code == 200:
            # 将图片数据转换为BytesIO对象
            image_data = BytesIO(image_response.content)

            # 使用send_file函数发送图片
            print("😃SUCCESS!")
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
    print("===================================")
    if re.match(r"^\d+-\d+$", ratio):

        img_tag = fuzzy_matching(search_tag)
        img_ratio = ratio.replace("-", "/")

        json_url_rank = f"https://danbooru.donmai.us/posts.json?tags=rating:{Rating}+limit:10+{img_tag}+order:rank"
        json_url_score = f"https://danbooru.donmai.us/posts.json?tags=rating:{Rating}+limit:1+{img_tag}+order:score+ratio:{img_ratio}"

        print(json_url_rank)
        print("Fetching images order by RANK...")

        response = requests.get(json_url_rank)

        # 检查请求是否成功
        if response.ok:

            if response.json():
                posts = list(filter(lambda x: fuzzy_ratio_get(x,img_ratio,Similarity),response.json()))
                if len(posts) == 0:
                    print("❗Cat not get any data searching in RANK")
                else:
                    posts_len = len(posts)
                    print("Get ",posts_len," post(s)")
                    return fetch_single_img(posts[randint(0,posts_len-1)])
        else:
            return "Failed to fetch posts data", 404
        
        try:
            response = requests.get(json_url_score)
            print("Get posts by SCORES...")
            print(json_url_score)
        except:
            print("❗Cat not get any response")

        try:
            if response.json():
                return fetch_single_img(response.json()[0])
            else:
                print("❗Cat not get any data searching in SCORES")
                return "No Posts", 404
        except Exception as e:
            print("Error",e)
            return str(e), 404
      
    else:
        return "Error ratio", 404

