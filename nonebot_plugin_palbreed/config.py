from pydantic import BaseModel
import json
import os

file_path = os.path.join(os.path.dirname(__file__), 'pal_list.json')


def pal_list() -> dict[str, str]:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    else:
        return {}


class Config(BaseModel):
    """Plugin Config Here"""
    pal_list: dict[str, str] = pal_list()
    api_url: str = 'https://cn.palworldbreed.com/_next/data/QlGgTQeBY0eTQxyIDL1jc/zh-CN/?/?/all.json'

