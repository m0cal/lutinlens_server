import requests
import base64
import os
import time
import uuid
import json
import mimetypes

# --- 配置 ---
# 请将这里的图片路径替换为您自己的连续拍摄的照片路径
# 确保照片是按拍摄顺序排列的
IMAGE_PATHS = [
    # 例如: "/path/to/your/photos/photo_01.jpg",
    # 例如: "/path/to/your/photos/photo_02.jpg",
    # 例如: "/path/to/your/photos/photo_03.jpg",
    # 请在这里填入您的图片路径:
    "test_photo/photo1.jpeg",
    "test_photo/photo2.jpeg",
    "test_photo/photo3.jpeg",
]

# 服务地址
SERVER_URL = "http://127.0.0.1:8000/generate"

# --- 脚本 ---

def encode_image_to_base64(filepath):
    """读取图片文件并将其编码为Base64字符串"""
    if not os.path.exists(filepath):
        print(f"错误: 文件未找到 -> {filepath}")
        return None
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def run_test():
    """运行测试，向服务器发送一系列图片"""
    session_id = str(uuid.uuid4())
    print(f"启动新一轮测试，会话ID: {session_id}\n")

    for i, image_path in enumerate(IMAGE_PATHS):
        print(f"--- 发送第 {i+1} 张图片: {os.path.basename(image_path)} ---")

        # 1. 编码图片
        img_base64 = encode_image_to_base64(image_path)
        if not img_base64:
            continue

        # 2. 准备数据URI (data:[MIME_type];base64,{base64_image})
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "application/octet-stream"  # 如果无法猜测，则使用默认值

        data_uri = f"data:{mime_type};base64,{img_base64}"

        # 3. 准备请求数据
        payload = {
            "session_id": session_id,
            "img": data_uri
        }

        try:
            # 4. 发送POST请求
            response = requests.post(SERVER_URL, json=payload, timeout=60)
            response.raise_for_status()  # 如果请求失败则抛出异常

            # 5. 解析并打印建议
            response_data = response.json()
            suggestion = response_data.get("suggestion", "没有收到建议。")
            ready_to_shoot = response_data.get("ready_to_shoot", 0)

            print(f"收到的建议: {suggestion}")
            if ready_to_shoot == 1:
                print("状态: ✅ 准备拍摄！")
                break  # 如果准备好了，可以提前结束测试
            else:
                print("状态: 🔄 需要调整。")

        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            break
        except json.JSONDecodeError:
            print(f"无法解析服务器响应。")
            break

        print("-" * (20 + len(os.path.basename(image_path))))

        # 模拟用户调整的间隔
        if i < len(IMAGE_PATHS) - 1:
            print("...等待2秒，模拟用户调整相机...\n")
            time.sleep(2)

    print("\n测试完成。")

if __name__ == "__main__":
    # 检查图片列表是否为空
    if not IMAGE_PATHS or any(path.startswith("image") for path in IMAGE_PATHS):
        print("错误: 请在脚本中设置您的图片路径。")
        print("请打开 test_client.py 文件并编辑 IMAGE_PATHS 列表。")
    else:
        run_test()
