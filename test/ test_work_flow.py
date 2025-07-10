from service.work_flow_service import run_work_flow_v3_with_progress
import asyncio

text = """
"金刚经第一品 法会因由分
如是我闻，一时，佛在舍卫国祗树给孤独园，与大比丘众千二百五十人俱。尔时，世尊食时，著衣持钵，
入舍卫大城乞食。于其城中，次第乞已，还至本处。饭食讫，收衣钵，洗足已，敷座而坐。"
请根据以上内容，结合实际生活，做一个讲解视频.视频题目为：金刚经第一品 法会因由分。使用大师解经的口吻来写。
"""
result_dir = "test/test_output"
user_id = "test_user"
style = "绘本"
template = "通用"

work_flow_record = asyncio.run(run_work_flow_v3_with_progress(
    text=text, 
    result_dir=result_dir, 
    user_id=user_id, 
    style=style, 
    template=template,
    tts_model_str="gemini-2.5-flash-preview-tts",
    voice_name = "Puck"
))

print(work_flow_record)