# 测试用例自动化控制器
# 导入模型类
from auto.model.model import Model
# 导入动作序列生成器
from auto.action_sequence_generator import LTLActionGenerator_pyMC
from auto.as_generator import ASG 
# 导入测试用例生成器
from auto.testcase_generator import STL_TCGenerator
# import 正则表达式模块
import re
# 导入时间模块
import time
import os


# 导入场景增强类
from auto.scenario_enhance import Enhancer
class Controller:
    def __init__(self,name,rq_path,llm_info_path,rq):
        # 获取模型名称
        self.name = name
        # 获取需求文档路径
        self.rq_path = rq_path
        # 获取llm信息
        llm_info = []
        self.rq = rq
        # 解析路径下的txt文本
        with open(f"{llm_info_path}/ai_response_s1.txt", "r", encoding="utf-8") as f:
            llm_info.append(f.read())
        with open(f"{llm_info_path}/ai_response_s2.txt", "r", encoding="utf-8") as f:
            llm_info.append(f.read())
        with open(f"{llm_info_path}/{rq}", "r", encoding="utf-8") as f:
            llm_info.append(f.read())
        self.llm_info = llm_info
        self.llm_info_path = llm_info_path
        self.time = 0


    def run(self):
        # 主控制器代码编写
        # s1:解析llm回复
        model = Model(
            name= self.name,
            rq_path= self.rq_path,
            llm_info = self.llm_info
        )
        # 调用模型解析方法
        model.extract_llm_info_p1()
        model.extract_llm_info_p2()
        model.extract_llm_info_p3()
        # s2:随机生成场景动作序列
        scenarios = model.get_scenarios()
        # s3:场景变异增强
        enhancer = Enhancer()
        enhanced_scenarios = enhancer.enhance_scenarios(scenarios)
        for scenario in enhanced_scenarios:
            executable_actions = scenario.executable_actions
            constraints = scenario.constraints
           
            #action_generator = LTLActionGenerator_pyMC(executable_actions, constraints, seq_len=10, tries=500, verbose=True)
            #seq = action_generator.search()

            action_generator = ASG(executable_actions, seq_len=10)
            seq = action_generator.get_sequence(constraints)
            # s3：解析动作序列并生成测试用例(csv格式) 
            print(seq)
            # 传入动作序列、动作集、场景可执行动作、变量集
            
            tc_generator = STL_TCGenerator(seq,model.actions,executable_actions,model.params)
            # 记录遗传算法的测试用例生成时间
            
            start_time = time.time()
            result = tc_generator.batch_run()
            end_time = time.time()
            self.time = end_time - start_time
            print(f"{scenario.name} Test case generation time: {self.time} seconds")

            # 变量包含控制点的生成方式：
            self.generate_cp_test_files(result, scenario.name)
            # 生成测试文件
            #self.generate_test_files(result, scenario.name)
            # # 生成测试日志
            self.generate_test_log(result, scenario,seq)

    # 测试文件生成
    def generate_test_files(self,result, scenario_name):
        testcase_dir_name = self.rq.replace(".txt","") + "_testcase"
        filename = f"{self.llm_info_path}/{testcase_dir_name}/{scenario_name}_tc.csv"
        # 获取目录路径
        dirpath = os.path.dirname(filename)
        # 如果目录不存在就创建
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(filename, "w", encoding="utf-8") as f:
            # 写入表头
            # 获取变量名列表
            variable_names = list(result[0][3].keys()) + list(result[0][4].keys())
            headers = ",".join(variable_names)
            headers += ",action"
            f.write(headers + "\n")
            # 写入数据行
            t = 0
            for tc in result:
                data_size = len(tc[3]['time'])
                for j in range(data_size):
                    row = ""
                    for var in list(result[0][3].keys()):
                            if var == 'time':
                                row += str(t) + ","
                                t += 1
                            else:
                                row += str(tc[3][var][j]) + ","
                    for var in list(result[0][4].keys()):
                            row += str(tc[4][var]) + ","
                    row += tc[0]
                    f.write(row + "\n")

    # 测试日志生成
    def generate_test_log(self,result, scenario,seq):
        testcase_dir_name = self.rq.replace(".txt","") + "_testcase"
        filename = f"{self.llm_info_path}/{testcase_dir_name}/{scenario.name}_log.txt"
        # 获取目录路径
        dirpath = os.path.dirname(filename)
        # 如果目录不存在就创建
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Scenario: {scenario.name}\n")
            f.write(f"Scenario constraint {scenario.constraints}:\n")
            f.write(f"  Action Sequence: {seq}\n")
            f.write(f"Test case generation time: {self.time} seconds\n") 
            # f.write(f"Robustness:")
            # for idx, tc in enumerate(result):
            #     f.write(f" {tc[2]}\n")
            #     f.write("\n")

    # 含控制点的测试文件生成
    def generate_cp_test_files(self,result, scenario_name):
        testcase_dir_name = self.rq.replace(".txt","") + "_testcase"
        filename = f"{self.llm_info_path}/{testcase_dir_name}/{scenario_name}_tc.csv"
        # 获取目录路径
        dirpath = os.path.dirname(filename)
        # 如果目录不存在就创建
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(filename, "w", encoding="utf-8") as f:
            headers = ",".join(result[2])
            headers += ",action"
            f.write(headers + "\n")
            for tc in result[0]:
                action_name = result[1][result[0].index(tc)] 
                for tc_a in tc:
                    # 写入数据行
                    row = ""
                    # 写入时间点
                    row += str(tc_a) + ","
                    # 写入变量值
                    for var in tc[tc_a]:
                        row += str(tc[tc_a][var][0]) + ","
                    # 写入常量值
                    for var in result[3]:
                        row += str(result[3][var]) + ","
                    # 写入动作
                    row += action_name
                    f.write(row + "\n")


        return