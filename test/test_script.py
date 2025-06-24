import sys
import os
import json
from zhipuai import ZhipuAI
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService
from service.script_service import ScriptService
from service.picture_prompt_service import PicturePromptService
from utility import parse_json

llm = LLMService()
script_service = ScriptService(llm)
#script = script_service.generate_text("创作纳什均衡的讲解视频")
text = """
小蝌蚪找妈妈
在一个阳光明媚的春天，池塘里的一片荷叶下，有一群刚刚孵化出来的小蝌蚪。它们黑黑的、圆圆的身体，拖着细细长长的尾巴，在水中快活地游来游去。

“我们都没有见过妈妈，她长什么样子呢？”一只小蝌蚪好奇地问。

“听说妈妈长得很特别，等我们长大了就能认出来了。”另一只小蝌蚪回答。

于是，小蝌蚪们决定出发去找妈妈。

他们先遇到了一只大眼睛、绿皮肤的青蛙。“您是我们的妈妈吗？”小蝌蚪们兴奋地问。

青蛙笑着说：“我不是你们的妈妈哦，我是青蛙，而你们现在还是小蝌蚪呢。”

小蝌蚪们点点头，继续向前游去。

接着，他们遇到了一只乌龟，四只脚，背着硬壳慢慢地爬行。

“请问……您是我们的妈妈吗？”小蝌蚪们小心翼翼地问。

乌龟慢悠悠地说：“我不是你们的妈妈，我可是乌龟呀。”

小蝌蚪们有些失望，但没有放弃，继续往前寻找。

后来，他们遇到了一条大鱼，大鱼摇着尾巴说：“孩子们，我不是你们的妈妈，我是鱼，我没有腿哦。”

小蝌蚪们开始有点灰心了，但还是坚持寻找。

日子一天天过去，小蝌蚪们的身体也慢慢发生了变化——他们长出了后腿，然后又长出了前腿，尾巴也越来越短了。

终于有一天，他们在岸边看到了一只熟悉又亲切的身影：大大的眼睛，绿色的身体，蹲在荷叶上正唱着歌。

“妈妈！”小蝌蚪们激动地叫了起来。

那只青蛙转过头，温柔地看着他们：“孩子们，你们终于找到我了，我也一直在等你们长大呢！”

小蝌蚪们高兴地游到妈妈身边，围成一团，心里暖洋洋的。

从那以后，他们和妈妈一起生活在池塘边，白天捉虫，晚上听风唱歌，过上了幸福快乐的生活。


"""
script = script_service.generate_json_script_from_prompt("生成一个小红帽的视频")
print(script)
script_json = parse_json(script)
print(script_json)