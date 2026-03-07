# 导入大模型工具
from llm_tool import LLMTool
# 导入工具类
from utils import Utils


# 导入测试用例自动化控制类
from auto.controller import Controller

import shutil
import os
import time
# 设置实验文件路径
requirement_file_path = "dataset\\lm_challenges\\original_models\\5_nn\\5_nn_reqs.docx"
# 设置当前实验编号
experiment_id = "1506-nn-1"
# 初始化大模型上下文
llm_tool = None

# 时间收集
time_list = {

}

# step1：与大模型对话，生成动作和场景集
def chat_with_llm():

    print(f"Starting experiment {experiment_id}...")
    # 如果实验文件夹已经存在，则先删除
    if os.path.exists(f"./experiments/{experiment_id}"):
        shutil.rmtree(f"./experiments/{experiment_id}")
          # 设置实验的模型路径,并将模型文件复制到实验文件夹

    # 将当前prompts文件夹复制放到实验文件夹下
    Utils.copy_files("./prompts", f"./experiments/{experiment_id}/prompts")
    # 初始化大模型上下文
    global llm_tool 
    llm_tool = LLMTool()
    # 记录开始交流时间
    llm_start_time1 = time.time()
    # 1、与大模型交互，识别需求领域并抽取需求条目
    interact_with_llm(prompt_path="./prompts/s1_base_info.txt", 
                      ai_response_path=f"./experiments/{experiment_id}/ai_response_s1.txt",
                        step="step 1")
    llm_end_time1 = time.time()
    time_list["llm_interaction_time_step1"] = llm_end_time1 - llm_start_time1
    # 2.1、与大模型交互, 分析系统的动作类型
    # interact_with_llm(prompt_path="./prompts/s2_1.txt", 
    #                   ai_response_path= f"./experiments/{experiment_id}/ai_response_s2-1.txt",
    #                     step="step 2-1")
    # interact_with_llm(prompt_path="./prompts/s2_2.txt", 
    #                   ai_response_path= f"./experiments/{experiment_id}/ai_response_s2-2.txt",
    #                     step="step 2-2")
    interact_with_llm(prompt_path="./prompts/s2_action_set.txt", 
                      ai_response_path= f"./experiments/{experiment_id}/ai_response_s2-1.txt",
                        step="step 2-1")
    interact_with_llm(prompt_path="./prompts/s2_refine_action.txt", 
                      ai_response_path= f"./experiments/{experiment_id}/ai_response_s2.txt",
                        step="step 2-2")

    # 2.2、与大模型交互, 检查动作集是否符合标准
    # interact_with_llm(prompt_path="./prompts/s2_action_check.txt", 
    #                   ai_response_path= f"./experiments/{experiment_id}/ai_response_s2_check.txt",
    #                     step="step 2-2",
    #                     )
    llm_end_time2 = time.time()
    time_list["llm_interaction_time_step2"] = llm_end_time2 - llm_end_time1
    # ========================================================
    # 3、与大模型交互，结合需求条目生成场景
    interact_with_llm(prompt_path="./prompts/s3_scenario_set.txt", 
                      ai_response_path= f"./experiments/{experiment_id}/ai_response_s3.txt",
                        step="step 3-1")
    # 3.2、与大模型交互，检查场景集是否符合标准
    # interact_with_llm(prompt_path="./prompts/s3_scenario_check.txt", 
    #                   ai_response_path= f"./experiments/{experiment_id}/ai_response_s3_check.txt",
    #                     step="step 3-2",
    #                     )  
    # ======================================================== 
    # 针对需求1，生成场景
    # ai_response_path=f"./experiments/{experiment_id}/ai_response_s3_1.txt"
    # interact_with_llm(prompt_path="./prompts/reinforce_single_rq1.txt", 
    #                    ai_response_path= ai_response_path,
    #                      step="step 3-1")
    # llm_end_time3_1 = time.time()
    # time_list["llm_interaction_time_step3_1"] = llm_end_time3_1 - llm_end_time2
    # 针对需求2，生成场景
    # ai_response_path=f"./experiments/{experiment_id}/ai_response_s3_2.txt"
    # interact_with_llm(prompt_path="./prompts/reinforce_single_rq2.txt", 
    #                    ai_response_path= ai_response_path,
    #                      step="step 3-2")
    # llm_end_time3_2 = time.time()
    # time_list["llm_interaction_time_step3_2"] = llm_end_time3_2 - llm_end_time3_1
    # 针对需求3，生成场景
    # ai_response_path=f"./experiments/{experiment_id}/ai_response_s3_3.txt"
    # interact_with_llm(prompt_path="./prompts/reinforce_single_rq3.txt", 
    #                    ai_response_path= ai_response_path,
    #                      step="step 3-3")
    # llm_end_time3_3 = time.time()
    # time_list["llm_interaction_time_step3_3"] = llm_end_time3_3 - llm_end_time3_2
    # # 针对需求4，生成场景
    # ai_response_path=f"./experiments/{experiment_id}/ai_response_s3_4.txt"
    # interact_with_llm(prompt_path="./prompts/reinforce_single_rq4.txt", 
    #                    ai_response_path= ai_response_path,
    #                      step="step 3-4")
    # llm_end_time3_4 = time.time()
    # time_list["llm_interaction_time_step3_4"] = llm_end_time3_4 - llm_end_time3_3
    print(f"Experiment {experiment_id} LLM interaction completed.")
    chat_history_json_path = f"./experiments/{experiment_id}/chat_history.json"
    llm_tool.save_chat_history(chat_history_json_path)







# step2：根据场景集，生成测试用例
def generate_testcase(rq):
    controller = Controller(
        name= "triplex_12B",
        rq_path= requirement_file_path,
        llm_info_path= f"./experiments/{experiment_id}",
        rq = rq
    )
    controller.run()


# step3: 调用matlab工具，运行模型仿真，获取仿真结果
def run_matlab_simulation():
    matlab_tool = MatlabTool()
    model_dir = f"./experiments/{experiment_id}/model"
    matlab_tool.run_mscript(script_path="./collect_coverage.m"
                                                 ,
                                                 script_log_path=model_dir + "/run.log", 
                                                 model_dir=model_dir, 
                                                )




# 收集时间函数
def collect_exp_time():
    # 打印实验各项的时间，并形成日志文件time_log.txt保存到对应的实验目录下
    filename = f"./experiments/{experiment_id}/time_log.txt"
    with open(filename, "a", encoding="utf-8") as f:
        print(f"Experiment {experiment_id} Time Summary:")
        f.write(f"Experiment {experiment_id} Time Summary:\n")
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
    with open(f"./experiments/{experiment_id}/ai_response_s1.txt", "r", encoding="utf-8") as f:
        ai_response1 = f.read()
    history_messages.append({"role": "assistant", "content": ai_response1})
    # 添加动作集对话
    with open("./prompts/s2_action_set.txt", "r", encoding="utf-8") as f:
        prompt2 = f.read()
    history_messages.append({"role": "user", "content": prompt2})
    with open(f"./experiments/{experiment_id}/ai_response_s2.txt", "r", encoding="utf-8") as f:
        ai_response2 = f.read()
    history_messages.append({"role": "assistant", "content": ai_response2})
    
    # with open("./prompts/s2_action_check.txt", "r", encoding="utf-8") as f:
    #     prompt2_1 = f.read()
    # history_messages.append({"role": "user", "content": prompt2_1})
    # with open(f"./experiments/{experiment_id}/ai_response_s2_check.txt", "r", encoding="utf-8") as f:
    #     ai_response2_1 = f.read()
    # history_messages.append({"role": "assistant", "content": ai_response2_1})

    # 添加场景集对话,该对话生成的场景针对所有需求
    # with open("./prompts/s3_scenario_set.txt", "r", encoding="utf-8") as f:
    #     prompt3 = f.read()
    # history_messages.append({"role": "user", "content": prompt3})
    # with open(f"./experiments/{experiment_id}/ai_response_s3.txt", "r", encoding="utf-8") as f:
    #     ai_response3 = f.read()
    # history_messages.append({"role": "assistant", "content": ai_response3})
    # with open("./prompts/s3_scenario_check.txt", "r", encoding="utf-8") as f:
    #     prompt3_1 = f.read()
    # history_messages.append({"role": "user", "content": prompt3_1})
    # with open(f"./experiments/{experiment_id}/ai_response_s3_check.txt", "r", encoding="utf-8") as f:
    #     ai_response3_1 = f.read()
    # history_messages.append({"role": "assistant", "content": ai_response3_1})
    # 针对需求1，生成场景
    # llm_tool = LLMTool()
    # ai_response_path=f"./experiments/{experiment_id}/ai_response_s3_1.txt"
    # with open("./prompts/reinforce_single_rq1.txt", "r", encoding="utf-8") as f:
    #     prompt_rq1 = f.read()
    # history_messages.append({"role": "user", "content": prompt_rq1})
    # llm_tool.chat_with_history(history_messages , ai_response_path)
    # # 删除rq1对话，减少token
    # history_messages.pop()

    # 针对需求2，生成场景
    # llm_tool = LLMTool()
    # ai_response_path=f"./experiments/{experiment_id}/ai_response_s3_2.txt"
    # with open("./prompts/reinforce_single_rq2.txt", "r", encoding="utf-8") as f:
    #     prompt_rq2 = f.read()
    # history_messages.append({"role": "user", "content": prompt_rq2})
    # llm_tool.chat_with_history(history_messages , ai_response_path)
    # history_messages.pop()

    llm_tool = LLMTool()
    ai_response_path=f"./experiments/{experiment_id}/ai_response_s3.txt"
    with open("./prompts/s3_scenario_set.txt", "r", encoding="utf-8") as f:
        prompt_rq1 = f.read()
    history_messages.append({"role": "user", "content": prompt_rq1})
    llm_tool.chat_with_history(history_messages , ai_response_path)
    history_messages.pop()

    # 针对需求4，生成场景
    # llm_tool = LLMTool()
    # ai_response_path=f"./experiments/{experiment_id}/ai_response_s3_4.txt"
    # with open("./prompts/reinforce_single_rq4.txt", "r", encoding="utf-8") as f:
    #     prompt_rq4 = f.read()
    # history_messages.append({"role": "user", "content": prompt_rq4})
    # llm_tool.chat_with_history(history_messages , ai_response_path)

  
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
    chat_with_llm()
    #chat_with_llm_history()
    end_time_step1 = time.time()
    time_list["total_llm_interaction_time"] = end_time_step1 - start_time
    # step2：根据场景集，生成测试用例
    #generate_testcase("ai_response_s3.txt")
    # generate_testcase("ai_response_s3_2.txt")
    #generate_testcase("ai_response_s3_3.txt")
    # generate_testcase("ai_response_s3_4.txt")
    end_time_step2 = time.time()
    time_list["testcase_generation_time"] = end_time_step2 - end_time_step1
    # 组织测试用例
    Utils.organize_testcase_files(f"./experiments/{experiment_id}")
    # step3: 调用matlab工具，运行模型仿真，获取仿真结果
    # 导入matlab工具类
    #from matlab_tool import MatlabTool
    # run_matlab_simulation()
    end_time_step3 = time.time()
    time_list["matlab_simulation_time"] = end_time_step3 - end_time_step2
    time_list["total_experiment_time"] = end_time_step3 - start_time
    collect_exp_time()
    
    #main2()


# 多次实验测试函数
def multi_main():
    demo = "./experiments/1506-fsm-s"
    suffix = "1506-fsm-s-fault"
    global experiment_id  # 关键
    for i in range(1, 4):
        print(f"Starting experiment iteration {i}...")
        exp_id = f"{suffix}-{i}"
        if os.path.exists(f"./experiments/{exp_id}"):
            shutil.rmtree(f"./experiments/{exp_id}")
        os.makedirs(f"./experiments/{exp_id}")
        # 复制demo文件夹下的内容到新的实验文件夹
        Utils.copy_dir_contents(demo, f"./experiments/{exp_id}")
        experiment_id = exp_id
        single_main()
        # 提取每次实验的testcase文件夹下的所有内容到一个新的文件夹中，命名为testcase_i
        Utils.copy_dir_contents(f"./experiments/{exp_id}/model/testcase", f"./fsm_testcase_fault/testcase_{i}")

def multi(demo,name):

    suffix = "1506-tri-fault-s"
    for i in range(1, 11):
        print(f"Starting {name}...")
        if os.path.exists(f"./experiments/{exp_id}"):
            shutil.rmtree(f"./experiments/{exp_id}")
        os.makedirs(f"./experiments/{exp_id}")
        # 复制demo文件夹下的内容到新的实验文件夹
        Utils.copy_dir_contents(demo, f"./experiments/{exp_id}")
        experiment_id = exp_id
        single_main()
        # 提取每次实验的testcase文件夹下的所有内容到一个新的文件夹中，命名为testcase_i
        Utils.copy_dir_contents(f"./experiments/{exp_id}/model/testcase", f"./tri_testcase_fault/testcase_{i}")

if __name__ == "__main__":
   #multi_main()
   single_main()




