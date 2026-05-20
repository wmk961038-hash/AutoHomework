import base64
import json
import os
import requests
from pathlib import Path
from typing import Any, Dict

# 可选：PyYAML 用于加载 YAML 配置，如果不可用会回退到 JSON / 默认
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

# 默认配置（代码内备份）
DEFAULT_CONFIG: Dict[str, Any] = {
    "image_folder": ".",
    "output_txt": "answers.txt",
    "model_name": "qwen3.5:2b",
    "ollama_api_url": "http://localhost:11434/api/generate",
    "image_extensions": ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff"],
    "stream": False,
    "options": {"temperature": 0.1},
    "requests": {"timeout_seconds": 120},
}


def load_config() -> Dict[str, Any]:
    """加载配置：优先级 环境变量 > config.yaml > config.json > 默认值"""
    config = DEFAULT_CONFIG.copy()

    base = Path(__file__).parent
    yaml_path = base / "config.yaml"
    json_path = base / "config.json"

    # 尝试加载 YAML（如果存在并且 PyYAML 可用），否则回退到 JSON
    loaded = False
    if yaml_path.exists():
        if yaml is None:
            print("警告：找到了 config.yaml，但未安装 PyYAML。请运行: pip install pyyaml")
        else:
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    loader = getattr(yaml, "safe_load", None)
                    if callable(loader):
                        cfg = loader(f) or {}
                    else:
                        cfg = {}
                if isinstance(cfg, dict):
                    config.update(cfg)
                    loaded = True
            except Exception as e:
                print(f"警告：读取 config.yaml 失败，使用默认或其它配置。错误：{e}")

    if not loaded and json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                cfg = json.load(f) or {}
            if isinstance(cfg, dict):
                config.update(cfg)
                loaded = True
        except Exception as e:
            print(f"警告：读取 config.json 失败，使用默认或其它配置。错误：{e}")

    # 环境变量覆盖（按字段）
    env_map = {
        "IMAGE_FOLDER": "image_folder",
        "OUTPUT_TXT": "output_txt",
        "MODEL_NAME": "model_name",
        "OLLAMA_API_URL": "ollama_api_url",
    }
    for env_key, cfg_key in env_map.items():
        val = os.getenv(env_key)
        if val:
            config[cfg_key] = val

    # image_extensions 允许用逗号分隔的字符串
    if isinstance(config.get("image_extensions"), str):
        config["image_extensions"] = [s.strip() for s in config["image_extensions"].split(",") if s.strip()]

    return config


CONFIG = load_config()


def encode_image_to_base64(image_path: Path) -> str:
    """将图片文件编码为 base64 字符串（不带 data:前缀）"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def solve_image(image_path: Path) -> str:
    """通过 Ollama HTTP API 解答图片中的题目"""
    print(f"  正在处理: {image_path.name}")
    img_base64 = encode_image_to_base64(image_path)

    payload = {
        "model": CONFIG.get("model_name"),
        "prompt": "请解答图片中的题目，直接输出最终答案，不要输出任何额外解释或注释。",
        "images": [img_base64],
        "stream": bool(CONFIG.get("stream", False)),
        "options": CONFIG.get("options", {}),
    }

    try:
        wrong_url = "http://sldfjaslkfdjlaskjf"
        timeout = CONFIG.get("requests", {}).get("timeout_seconds", 120)
        response = requests.post(CONFIG.get("ollama_api_url"), json=payload, timeout=timeout)
        if response.status_code != 200:
            return f"API 错误：{response.status_code} - {response.text}"
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        return f"请求异常：{str(e)}"


def main():
    image_folder = Path(CONFIG.get("image_folder", "."))
    if not image_folder.exists():
        print(f"图片目录不存在: {image_folder}")
        return

    image_files = []
    for ext in CONFIG.get("image_extensions", []):
        image_files.extend(image_folder.glob(ext))

    if not image_files:
        print("当前文件夹中没有找到图片文件。")
        return

    print(f"找到 {len(image_files)} 张图片，开始解答...")
    output_txt = CONFIG.get("output_txt", "answers/answers.txt")
    output_path = Path(output_txt)
    if not output_path.is_absolute():
        output_path = Path(__file__).parent / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, img_path in enumerate(image_files, 1):
            print(f"[{idx}/{len(image_files)}] 处理中...")
            answer = solve_image(img_path)
            if not answer:
                print("答案为空")
            f.write(f"--- 图片 {idx}: {img_path.name} ---\n")
            f.write(answer + "\n\n")
    print(f"✅ 所有答案已保存到 {CONFIG.get('output_txt', 'answers.txt')}")


if __name__ == "__main__":
    main()