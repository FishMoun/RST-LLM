import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
# 导入大模型工具
from llm_tool import LLMTool
# 导入工具类
from utils import Utils


# 导入测试用例自动化控制类
from auto.controller import Controller
import time
# 设置实验文件路径
requirement_file_path = "dataset\\lm_challenges\\original_models\\5_nn\\5_nn_reqs.docx"
demo = "batch_test\\4NN\\demo"
# 设置当前根目录
root_dir = "./batch_test/4NN/coverage_scenario"
# 设置测试用例输出目录
testcase_output_dir = f"batch_test\\4NN\\testcase\\nn_testcase_coverage_scenario"
# 设置实验运行轮次
iter = 10
# 初始化大模型上下文
llm_tool = None

# 时间收集
time_list = {

}





# step2：根据场景集，生成测试用例
def generate_testcase(rq):
    controller = Controller(
        name= "integrator_12B",
        rq_path= requirement_file_path,
        llm_info_path= f"{demo}",
        rq = rq
    )
    controller.run()




# 收集时间函数
def collect_exp_time():
    # 打印实验各项的时间，并形成日志文件time_log.txt保存到对应的实验目录下
    filename = f"{root_dir}/time_log.txt"
    with open(filename, "a", encoding="utf-8") as f:
        print(f"Time Summary:")
        f.write(f"Time Summary:\n")
        for key, value in time_list.items():
            print(f"{key}: {round(value, 2)} seconds")
            f.write(f"{key}: {round(value, 2)} seconds\n")
        
   
        
# 历史对话全流程主程序
def chat_with_llm_history():
    
    # 构建历史对话
    history_messages = [
        {"role": "assistant", "content": "你现在是需求领域专家，"}]
    # 添加整理模型对话
    with open("./prompts/s1_base_info.txt", "r", encoding="utf-8") as f:
        prompt1 = f.read()
    history_messages.append({"role": "user", "content": prompt1})
    with open(f"{demo}/ai_response_s1.txt", "r", encoding="utf-8") as f:
        ai_response1 = f.read()
    history_messages.append({"role": "assistant", "content": ai_response1})
    # 添加动作集对话
    with open("./prompts/s2_action_set.txt", "r", encoding="utf-8") as f:
        prompt2 = f.read()
    history_messages.append({"role": "user", "content": prompt2})
    with open(f"{demo}/ai_response_s2.txt", "r", encoding="utf-8") as f:
        ai_response2 = f.read()
    history_messages.append({"role": "assistant", "content": ai_response2})
    
    llm_tool = LLMTool()
    ai_response_path=f"{root_dir}/ai_response_s3.txt"
    with open(f"{root_dir}/s3_scenario_set.txt", "r", encoding="utf-8") as f:
        prompt_rq1 = f.read()
    history_messages.append({"role": "user", "content": prompt_rq1})
    llm_tool.chat_with_history(history_messages , ai_response_path)
    history_messages.pop()

  
# 与大模型交互的函数
def interact_with_llm(prompt_path="", ai_response_path="", step="",add_prompt=""):
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()
    if (add_prompt != ""):
        prompt = prompt + add_prompt
    print(f"Starting {step}...")
    llm_tool.chat_with_file(ai_response_path, file_path=requirement_file_path, user_message=prompt )
    print(f"{step} done")

# 单个实验测试函数
def single_main():
     # 总计时
    start_time = time.time()
    # step1：与大模型对话，生成动作和场景集
    #chat_with_llm_history()
    end_time_step1 = time.time()
    time_list["total_llm_interaction_time"] = end_time_step1 - start_time
    # step2：根据场景集，生成测试用例
    generate_testcase("ai_response_s3.txt")

    end_time_step2 = time.time()
    time_list["testcase_generation_time"] = end_time_step2 - end_time_step1
    # 组织测试用例
    Utils.organize_testcase_files(f"{root_dir}")
    end_time_step3 = time.time()
    time_list["matlab_simulation_time"] = end_time_step3 - end_time_step2
    time_list["total_experiment_time"] = end_time_step3 - start_time
    collect_exp_time()
    

# 多次实验测试函数
def multi_main():
    for i in range(1, iter+1):
        print(f"Starting experiment iteration {i}...")

        # 复制demo文件夹下的内容到新的实验文件夹
        Utils.copy_dir_contents(demo, f"{root_dir}")
        single_main()
        # 提取每次实验的testcase文件夹下的所有内容到一个新的文件夹中，命名为testcase_i
        Utils.copy_dir_contents(f"{root_dir}/model/testcase", f"{testcase_output_dir}/testcase_{i}")



if __name__ == "__main__":
   multi_main()





