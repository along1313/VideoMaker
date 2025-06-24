import dashscope
from dashscope.audio.tts_v2 import *
import os
import dotenv
import sys
import json


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service.ai_service import ImageModelService
from workflow import add_time
dotenv.load_dotenv()

#从workstore/user1/博弈论基石/work_flow_record.json读取work_flow_record
work_flow_record = json.load(open("workstore/user1/博弈论基石/work_flow_record.json"))

#调用add_time函数
work_flow_record = add_time(work_flow_record, "workstore/user1/博弈论基石/audios")

#将work_flow_record保存到workstore/user1/博弈论基石/work_flow_record.json
json.dump(work_flow_record, open("workstore/user1/博弈论基石/test_work_flow_record.json", "w"), ensure_ascii=False)
