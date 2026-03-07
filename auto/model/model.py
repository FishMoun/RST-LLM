import re
from .param import Param
from .action import Action
from .scenario import Scenario

class Model:
    def __init__(self, name, rq_path, llm_info):
        # 模型名称
        self.name = name
        # 模型需求文档路径
        self.rq_path = rq_path
        # LLM返回的信息
        self.llm_info_p1 = llm_info[0]
        self.llm_info_p2 = llm_info[1]
        self.llm_info_p3 = llm_info[2]
        # 初始化实例变量
        self.requirements = []
        self.params = []
        self.test_configs = []
        self.scenarios = []
        self.actions = []
        
    
    # 抽取提示1中LLM信息中的关键字段
    def extract_llm_info_p1(self):
        # 使用正则表达式提取所有“描述:”后的文字
        self.requirements = re.findall(r'Requirement Description[:：]\s*(.*)', self.llm_info_p1)
        # 去除可能的空行或首尾空白
        self.requirements = [d.strip() for d in self.requirements if d.strip()]
         # 使用正则表达式提取“测试配置”后的文本
        self.test_configs = re.findall(r'Test Configuration \d+[：:]\s*(.*)', self.llm_info_p1)
        self.test_configs = [c.strip() for c in self.test_configs if c.strip()]
        #抽取变量相关信息
        blocks = re.findall(r'Variable Name[:：](.*?)Type[:：](.*?)Description[:：](.*?)Port Type[:：](.*?)Is Constant[:：](.*?)(?:\n|$)', self.llm_info_p1, re.S)
        for name, data_type, description, port_type,is_constant in blocks:
            self.params.append(
                Param(
                    name=name.strip(),
                    data_type=data_type.strip(),
                    description=description.strip(),
                    port_type=port_type.strip(),
                    is_constant= is_constant.strip(),
                    test_config=self.test_configs
                )
            )
        # 从测试配置中寻找时序变量及其范围，并添加到变量集中
        for test_config in self.test_configs:
            if "t" in test_config:
                self.params.append(
                    Param(
                    name="t",
                    data_type= None,
                    description="time var",
                    port_type=None,
                    is_constant=None,
                    test_config = self.test_configs)
                )
        
        


   


    # 抽取提示2中LLM信息中的关键字段：动作
    def extract_llm_info_p2(self):
        pattern = re.compile(
            r"Action Name:(?P<name>.+?)\s+"
            r"Semantic Description:(?P<desc>.+?)\s+"
            r"Input Constraint:(?P<stl>.+?)\s+"
            r"Temporal Constraint:(?P<temp>.+?)(?:\n\n|\Z)",
            re.S
        )

        self.actions = [
            Action(
                name=m.group("name").strip(),
                description=m.group("desc").strip(),
                STL_str=m.group("stl").strip(),
                temporal_str=m.group("temp").strip(),
            )
            for m in pattern.finditer(self.llm_info_p2)
        ]

    # 抽取提示3中LLM信息中的关键字段：场景
    def extract_llm_info_p3_1(self):
           # 先粗略按场景块切分：每个块从 #Sx: 到下一个 **场景N：** 或文本结束
        block_pattern = re.compile(
        r"\*\*场景\d+：\*\*.*?#(?P<name>S\d+):(.*?)(?=\n\*\*场景\d+：\*\*|\Z)",
        re.S
    )


        for m in block_pattern.finditer(self.llm_info_p3):
            name = m.group("name").strip()   # S1, S2, ...
            body = m.group(2)                # 场景内部的多行文本

            desc = ""
            actions = []
            constraints = ""
            linked_rq = "" 

            # 按行解析，避免跨行误吃
            for line in body.splitlines():
                # 去掉前面的 "* "、空格之类
                line_stripped = line.strip()
                line_clean = line_stripped.lstrip("*").strip()

                if not line_clean:
                    continue

                # 统一处理全角/半角冒号
                if "：" in line_clean:
                    key, value = line_clean.split("：", 1)
                elif ":" in line_clean:
                    key, value = line_clean.split(":", 1)
                else:
                    continue

                key = key.strip()
                value = value.strip()

                if "场景语义描述" in key:
                    desc = value
                elif "可执行动作集合" in key:
                    acts_raw = value.replace("，", ",")
                    actions = [a.strip() for a in acts_raw.split(",") if a.strip()]
                elif "场景约束" in key:
                    constraints = value
                elif "关联需求条目编号" in key:
                    linked_rq = value

            scenario = Scenario(
                name=name,
                description=desc,
                executable_actions=actions,
                constraints=constraints,
                linked_rq=linked_rq
            )
            self.scenarios.append(scenario)

    def extract_llm_info_p3(self):
        # 正则模式：逐个场景块提取信息
        pattern = re.compile(
            r'#(S\d+):\s*'                                 # 场景名 S1, S2 ...
            r'\* Scenario Semantic Description:(?P<desc>.*?)\n'            # 场景语义描述
            r'\* Executable Action Set:(?P<actions>.*?)\n'       # 可执行动作集合
            r'\* Scenario Action Sequence:(?P<constraints>.*?)\n'         # 场景约束
            r'\* Associated Requirement:(?P<rq>.*?)(?=\n\n#S\d+:|\Z)',  # 需求编号，到下一个#S..或文本结束
            re.DOTALL
        )


        for m in pattern.finditer(self.llm_info_p3):
            name = m.group(1).strip()
            desc = m.group('desc').strip()
            actions_raw = m.group('actions').strip()
            constraints_raw = m.group('constraints').strip()
            rq_raw = m.group('rq').strip()

            # 将“可执行动作集合”按逗号切分成列表
            executable_actions = [a.strip() for a in actions_raw.split(',') if a.strip()]

            scenario = Scenario(
                name=name,
                description=desc,
                executable_actions=executable_actions,
                constraints=constraints_raw,
                linked_rq=rq_raw
            )
            self.scenarios.append(scenario)


    # 获取场景
    def get_scenarios(self):
        return self.scenarios
    # 获取动作
    def get_actions(self):
        return self.actions


def main():
    # 测试Model类的功能
    model_test = Model(
        name="TestModel",
        rq_path="path/to/requirement.docx",
        llm_info=['','',"""
#S1:\n* 前置条件: t ϵ N, 0 ≤ t ≤ 30; 0 ≤ ia, ib, ic ≤ 20; 0 ≤ Tlevel ≤ 1; 1 ≤ PClimit ≤ 5\n* 场景语义描述：在整个时间范围内，所有三个信号始终彼此一致，差异不超过阈值Tlevel。\n* 可执行动作集合：A1\n* 场景动作序列：[A1]\n* 关联需求条目编号：RM-002\n\n
"""]
    )
    model_test.extract_llm_info_p3()
    print("模型名称:", model_test.name)





# 测试类的function
if __name__ == "__main__":
    main()