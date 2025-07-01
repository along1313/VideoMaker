from service.work_flow_service import run_work_flow_v3_with_progress
import asyncio

text = "生成一个结合实际科普贝叶斯公式的问题"
result_dir = "test/test_output"
user_id = "test"
style = "绘本"
template = "通用"

work_flow_record = asyncio.run(run_work_flow_v3_with_progress(
    text=text, 
    result_dir=result_dir, 
    user_id=user_id, 
    style=style, 
    template=template,
    tts_model_str="gemini-2.5-flash-preview-tts",
))

print(work_flow_record)