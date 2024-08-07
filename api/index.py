import requests
from flask import Flask, send_file, request, redirect
from io import BytesIO
from random import randint
from geoip2.database import Reader
import re
from PIL import Image
from os import environ

End_point = str(environ.get("ENDPOINT","danbooru.donmai.us"))

Quality = int(environ.get("QUALITY",1))
# 质量控制
# 0：180*180
# 1: 360*360
# ......

Rating = environ.get("RATING","g,s,q")
# 默认过滤级别

Similarity = float(environ.get("SIMILARITY",0.15))
# 图片比例最大差异

app = Flask(__name__)

r = Reader("api/geoip/Country.mmdb")


def cut_by_ratio(input_img: BytesIO, post: dict, ratio: float):

    source_w = post["media_asset"]["variants"][Quality]["width"]
    source_h = post["media_asset"]["variants"][Quality]["height"]
    img_ratio = source_w / source_h

    if img_ratio == ratio:
        return input_img

    output = input_img

    print(f"🌾Cutting image to fit the ratio [{img_ratio}]-->({ratio})")
    i = Image.open(input_img)
    

    if img_ratio > ratio:
        l = int(source_h * ratio)
        h = source_h - 1
        box = ((source_w - l) / 2, 0, (source_w + l) / 2, h)
    else:
        h = int(source_w / ratio)
        l = source_w - 1
        box = (0, (source_h - h) / 2, l, (source_h + h) / 2)

    print(f"✂️ Cutting img {source_w} * {source_h} --> {l} * {h}")
    print(f"Box is {box}")
    cropped_img = i.crop(box)
    cropped_img.save(output, format="JPEG")

    output.seek(0)

    return output


def get_user_ip():
    user_ip = request.remote_addr
    try:
        c = r.country(user_ip).country.name
    except Exception:
        c = f"No Geoip data match user ip {str(Exception)}"
    return f"🧭Request from ip:[{user_ip}] --> {c} "


def ratio_parse(ratio_str: str) -> float:
    mw, mh = map(int, ratio_str.split("/"))
    return mw / mh


def fuzzy_ratio_get(post: dict, match_ratio_str: str, similarity: float) -> bool:

    match_ratio = ratio_parse(match_ratio_str)
    h = post["image_height"]
    w = post["image_width"]
    ratio: float = w / h
    if abs(ratio - match_ratio) <= similarity:
        print("------------------")
        print("🔢id -->", post["id"])
        print("💖favourite -->", post["fav_count"])
        print("🪢Fuzzy Ratio -->", abs(ratio - match_ratio))
        print("------------------")
        return True
    else:
        return False


def fuzzy_matching(tag: str) -> str:
    if tag:
        json_url = f"https://{End_point}/autocomplete.json?search[type]=tag_query&search[query]={tag}"
        response = requests.get(json_url)
        try:
            value = response.json()[0]["value"]
            print("{", tag, "} is matched to tag: {", value, "}")
            return value
        except:
            print("Error in fuzzy matching tag value of ", tag)
            print(response.json())
            return ""
    else:
        return ""


def get_single_img_data(post: dict[str, any]):
    file_url = post["media_asset"]["variants"][Quality]["url"]
    print("🎯URL -->", file_url)
    print("🔢id -->", post["id"])
    print("💖favourite -->", post["fav_count"])

    image_response = requests.get(file_url)

    # 将图片数据转换为BytesIO对象
    image_data = BytesIO(image_response.content)

    print("😃SUCCESS!")
    return image_data


def fetch_single_img(post: dict[str, any]):
    print("fetch_single_img start")
    try:
        return send_file(get_single_img_data(post), mimetype="image/jpeg")
    except:
        print("Error fetch image data")
        return "Error fetch image data", 404


def fetch_single_img_and_crop(post: dict, ratio: float):
    try:
        i = cut_by_ratio(get_single_img_data(post), post, ratio)
        return send_file(i, mimetype="image/jpeg")
    except Exception as e:
        print(str(e))
        return "Error cant not fetching img or crop img", 404
    
def compress_png_to_webp(png_bytesio):
    # 从BytesIO中读取PNG图像
    image = Image.open(png_bytesio)
    
    # 创建一个新的BytesIO对象来保存WebP图像数据
    webp_bytesio = BytesIO()
    
    # 将PNG图像转换为WebP图像并保存到webp_bytesio中
    image.save(webp_bytesio, 'WEBP', quality=80)
    
    # 重置文件指针以便后续读取
    webp_bytesio.seek(0)
    
    return webp_bytesio

@app.route("/")
def hone():
    print(get_user_ip())
    return redirect("https://www.douyin.com/", code=302)

@app.route("/attachments/<path:file_path>")
def proxy_discord_cdn(file_path):
    print(get_user_ip())
    query_params = request.args
    query_url = file_path + '?' + '&'.join([f'{key}={value}' for key, value in query_params.items()])
    full_image_url = f"https://cdn.discordapp.com/attachments/{query_url}"
    # print("aaaaaaaaaa -> ",full_image_url)
    # 使用requests库获取远程图片数据
    response = requests.get(full_image_url)
    # 检查请求是否成功
    if response.status_code == 200:
        # 将图片数据转换为BytesIO对象
        image_data = BytesIO(response.content)

        # 使用send_file函数发送图片
        return send_file(compress_png_to_webp(image_data), mimetype="image/jpeg")
    else:
        return "Failed to fetch image", 404
 


@app.route("/i/<path:proxy_file_path>.jpg")
def get_image_by_path(proxy_file_path):
    print(get_user_ip())
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
    print(get_user_ip())
    # 构建JSON文件的URL
    json_url = f"https://{End_point}/posts/{image_id}.json"

    print("Post json url -->" + json_url)

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
    print(get_user_ip())
    print("===================================")
    if re.match(r"^\d+-\d+$", ratio):

        if search_tag == "_":
            search_tag == ""
        else:
            img_tag = fuzzy_matching(search_tag)
        img_ratio = ratio.replace("-", "/")

        json_url_rank = f"https://{End_point}/posts.json?tags=rating:{Rating}+limit:10+{img_tag}+order:rank"
        json_url_score = f"https://{End_point}/posts.json?tags=rating:{Rating}+limit:1+{img_tag}+order:score+ratio:{img_ratio}"

        print(json_url_rank)
        print("Fetching images order by RANK...")

        response = requests.get(json_url_rank)

        # 检查请求是否成功
        if response.ok:

            if response.json():
                posts = list(
                    filter(
                        lambda x: fuzzy_ratio_get(x, img_ratio, Similarity),
                        response.json(),
                    )
                )
                if len(posts) == 0:
                    print("❗Cat not get any data searching in RANK")
                else:
                    posts_len = len(posts)
                    print("Get ", posts_len, " post(s)")
                    randpost = posts[randint(0, posts_len - 1)]
                    return fetch_single_img_and_crop(randpost, ratio_parse(img_ratio))
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
            print("Error", e)
            return str(e), 404

    else:
        return "Error ratio", 404


@app.route("/e/<string:ratio>/<string:search_tag>.jpg")
def get_image_by_tag_E(ratio: str, search_tag: str):
    global Rating
    r = Rating
    Rating = "e,q"
    print("✨ a other mode ...")
    x = get_img_by_search(ratio, search_tag)
    Rating = r
    return x

@app.route("/<string:ratio>.jpg")
def random_image(ratio: str):
    print("===================================")
    print(get_user_ip())
    print("===================================")
    if re.match(r"^\d+-\d+$", ratio):
        img_ratio = ratio.replace("-", "/")

        json_url_random = f"https://{End_point}/posts.json?tags=rating:{Rating}+order:random"

        print(json_url_random)
        print("Fetching images order by RANDOM🎲...")

        response = requests.get(json_url_random)

        # 检查请求是否成功
        if response.ok:

            if response.json():
                posts = list(
                    filter(
                        lambda x: fuzzy_ratio_get(x, img_ratio, Similarity),
                        response.json(),
                    )
                )
                if len(posts) == 0:
                    print("❗Cat not get any data searching in RANDOM🎲")
                else:
                    posts_len = len(posts)
                    print("Get ", posts_len, " post(s)")
                    randpost = posts[randint(0, posts_len - 1)]
                    return fetch_single_img_and_crop(randpost, ratio_parse(img_ratio))
        else:
            return "Failed to fetch posts data", 404
    else:
        return "Error ratio", 404
    



