import json
import os

CONFIG_PATH = "config.json"

DEFAULT_CONFIG = {
    "wait_time": 20,    # 单位：秒
    "offline_mode": False,   # 离线资源提取功能
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
        if 'offline_mode' not in config:
            config['offline_mode'] = True
            return config

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
