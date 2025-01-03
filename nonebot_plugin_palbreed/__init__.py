import json

from nonebot import get_plugin_config, get_bot, logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.plugin import PluginMetadata
from nonebot.plugin.on import on_regex
from httpx import AsyncClient

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="pal_breed",
    description="获取帕鲁的配种信息",
    homepage="nonebot_plugin_palbreed",
    usage="通过发送对应格式的消息，来获取帕鲁的配种信息",
    type="application",
    config=Config,
)
config = get_plugin_config(Config)

# 匹配格式：以#开头，两个字符串中间需要有一个+号

get_breed = on_regex(r"^#([\w\u4e00-\u9fa5]+)\+([\w\u4e00-\u9fa5]+)$", priority=1, block=True)
get_process = on_regex(r"^#([\w\u4e00-\u9fa5]+)$", priority=1, block=True)
upload_data = on_regex(r"^/更新数据", priority=1, block=True)


async def get_breed_list(p1: str, p2: str, p3: str = "all") -> dict:
    url = config.api_url
    url = url.replace("?", p1, 1).replace("?", p2, 1)
    if p1 == "all" and p2 == "all":
        url = url.replace("all.json", p3 + ".json", 1)
    print(url)
    response = await AsyncClient().get(url)
    if response.status_code == 200:
        logger.info(response.url)
        return response.json()
    else:
        return {}


@get_breed.handle()
async def handle_get_breed(event: GroupMessageEvent):
    try:
        re = MessageSegment.reply(event.message_id)
        f_msg_before = event.get_plaintext().split("+")[0].split("#")[1]
        f_msg_after = event.get_plaintext().split("+")[1]
        bot = get_bot()
        pal_list = config.pal_list
        await bot.call_api("set_group_reaction", group_id=event.group_id, user_id=event.user_id,
                           message_id=event.message_id,
                           code="424", is_add=True)
        # 检查f_msg_before和f_msg_after是否在pal_list列表下字典的name中
        parent1_pal = None
        parent2_pal = None
        for pal in pal_list:
            if not isinstance(pal, dict):
                continue
            if pal.get("name") == f_msg_before:
                parent1_pal = pal.get("key")
            if pal.get("name") == f_msg_after:
                parent2_pal = pal.get("key")

        if parent1_pal is None or parent2_pal is None:
            await get_breed.finish(re + f"{f_msg_before}或{f_msg_after}不在种子列表中")
        data = await get_breed_list(parent1_pal, parent2_pal)
        if not data:
            await get_breed.finish(re + f"获取失败！")
        result_list = data.get("pageProps").get("data")
        msg = f"{f_msg_before}+{f_msg_after}的种族繁育结果如下：\n"
        for result in result_list:
            msg += f"{result['child_pal']['name']}\n"
        if not result_list or len(result_list) == 0:
            msg += "没有找到结果！"
        await get_breed.finish(re + f"获取成功！{msg}")
    except Exception:
        raise


@get_process.handle()
async def handle_get_process(event: GroupMessageEvent):
    try:
        re = MessageSegment.reply(event.message_id)
        f_msg = event.get_plaintext().split("#")[1]
        bot = get_bot()
        pal_list = config.pal_list
        await bot.call_api("set_group_reaction", group_id=event.group_id, user_id=event.user_id,
                           message_id=event.message_id, code="424", is_add=True)
        # 检查f_msg是否在pal_list列表下字典的name中
        child_pal = None
        for pal in pal_list:
            if not isinstance(pal, dict):
                continue
            if pal.get("name") == f_msg:
                child_pal = pal.get("key")

        if child_pal is None:
            await get_process.finish(re + f"{f_msg}不在种子列表中")
        data = await get_breed_list("all", "all", child_pal)
        if not data:
            await get_process.finish(re + f"获取失败！")
        result_list = data.get("pageProps").get('data')
        msg = f"{f_msg}的繁育过程如下：\n"
        for result in result_list:
            msg += f"{result['parent1_pal']['name']}+{result['parent2_pal']['name']}\n"
        if not result_list or len(result_list) == 0:
            msg += "没有找到结果！"
        await get_process.finish(re + f"获取成功！{msg}")
    except Exception:
        raise


@upload_data.handle()
async def handle_upload_data(event: GroupMessageEvent):
    try:
        re = MessageSegment.reply(event.message_id)
        await upload_data.send(re + "正在尝试更新数据，请稍后...")
        async with AsyncClient as client:
            response = await client.get(
                "https://cn.palworldbreed.com/_next/data/QlGgTQeBY0eTQxyIDL1jc/zh-CN/all/all/all.json")

            options = json.loads(response.text)["pageProps"]["pals"]
            #       导出json文件
            with open("./src/plugins/pal_breed/pal_list.json", "w", encoding="utf-8") as f:
                json.dump(options, f, ensure_ascii=False, indent=4)
                config.pal_list = options
                await upload_data.finish(re + "更新成功！")
    except Exception:
        raise
