import base64
import requests
from pathlib import Path

from config import Config


def encode_image_to_base64(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def solve_image(image_path: Path, config: Config) -> str:
    print(f"  正在处理: {image_path.name}")
    img_base64 = encode_image_to_base64(image_path)

    payload = {
        "model": config.model_name,
        "messages": [
            {
                "role": "user",
                "content": config.prompt,
                "images": [img_base64],
            }
        ],
        "stream": config.stream,
        "think": config.options.think,
        "options": {
            "temperature": config.options.temperature,
            "num_predict": config.options.num_predict,
        },
    }

    try:
        if not config.options.think:
            print("模型没有启用思考")
        response = requests.post(config.chat_url, json=payload, timeout=config.requests.timeout_seconds)
        if response.status_code != 200:
            return f"API 错误：{response.status_code} - {response.text}"
        result = response.json()
        msg = result.get("message", {})
        content = msg.get("content", "").strip()
        thinking = msg.get("thinking", {})
        print("content:"+content)
        print("thinking:"+thinking)
        if not content:
            return thinking
        return content
    except Exception as e:
        return f"请求异常：{str(e)}"


def main():
    config = Config.load()

    image_folder = Path(config.image_folder)
    if not image_folder.exists():
        print(f"图片目录不存在: {image_folder}")
        return

    image_files = []
    for ext in config.image_extensions:
        image_files.extend(image_folder.glob(ext))

    if not image_files:
        print("当前文件夹中没有找到图片文件。")
        return

    print(f"找到 {len(image_files)} 张图片，开始解答...")
    output_path = Path(config.output_txt)
    if not output_path.is_absolute():
        output_path = Path(__file__).parent / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, img_path in enumerate(image_files, 1):
            print(f"[{idx}/{len(image_files)}] 处理中...")
            answer = solve_image(img_path, config)
            if not answer:
                print("答案为空")
            f.write(f"--- 图片 {idx}: {img_path.name} ---\n")
            f.write(answer + "\n\n")
            f.flush()
    print(f"✅ 所有答案已保存到 {config.output_txt}")


if __name__ == "__main__":
    main()
