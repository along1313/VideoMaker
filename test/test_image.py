
import sys
import os
import json
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from service.ai_service import ImageModelService
from service.picture_generate_service import PictureGenerateService
from static.style_config import STYLE_CONFIG

json_text = """
{'title': '小红帽奇遇记', 'main_character_description': ['小红帽：10岁女孩，乌黑长发扎成马尾，穿着红色及膝斗篷，腰间系蓝白格纹围裙，竹篮里装着新鲜草莓蛋糕', '大灰狼：棕灰色皮毛，尖耳朵竖立，红眼睛闪着狡黠光芒，穿着缀满铜纽扣的旧外套', '外婆：银发盘成发髻，戴着圆框眼镜，穿着墨绿色羊毛披肩，手中编织着毛线坐垫'], 'content': [{'index': '0', 'voice_text': '晨雾笼罩的森林里，小红帽提着装满蛋糕的竹篮出发了。她踮着脚尖跨过小溪，斗篷上的雏菊随着步伐轻轻摇晃。篮子里的草莓还沾着露水，像红宝石般晶莹剔透。'}, {'index': '1', 'voice_text': "忽然，灌木丛中传来沙沙声。大灰狼抖了抖皮毛，露出锋利的獠牙：'亲爱的，要不要吃块蛋糕？'他故意把句子拉得又长又慢，尾巴在身后画着圈圈。"}, {'index': '2', 'voice_text': "小红帽握紧篮子边缘，围裙口袋里的银剪刀微微发烫。她想起外婆的叮嘱：'遇到陌生人要仔细分辨...'但大灰狼的声音像棉花糖般软绵绵的，篮子里的草莓突然变得沉甸甸的。"}, {'index': '3', 'voice_text': "狼吞下蛋糕后打了个嗝，喉咙里咕噜噜响着：'现在该去外婆家了。'他故意放慢脚步，让斗篷下摆扫过潮湿的青苔。小红帽的蝴蝶结在风中越系越紧。"}, {'index': '4', 'voice_text': "当外婆家的木门打开时，狼的外套下竟露出猎人银色的子弹袋！他举起左轮手枪：'终于等到你们了！'远处传来猎犬的吠叫，狼的铜纽扣在阳光下闪着慌乱的光。"}, {'index': '5', 'voice_text': '猎人用子弹击碎狼的假牙，外婆用毛线织成的网兜住了小红帽。晨光中，银剪刀在篮子里发出清脆的响声，斗篷上的雏菊重新绽放出七种颜色。'}], 'total_count': 6, 'total_voice_text_count': 398, 'note': '建议配乐采用钢琴与竖琴交织的轻快旋律，关键转折点加入硬币落地般的清脆音效。角色设计参考19世纪欧洲童书插画风，背景采用手绘水彩质感。'}
"""

style = "绘本"

image_model_service = ImageModelService()

picture_generate_service = PictureGenerateService(image_model_service)



image_url = asyncio.run(picture_generate_service.generate_picture_from_json(json_text, style, 4))
print(image_url)


    