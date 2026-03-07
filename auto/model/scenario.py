import re
class Scenario:
    def __init__(self, name: str, description: str, executable_actions: list, constraints: str,linked_rq:str):
        # 场景名称
        self.name = name
        # 场景语义描述
        self.description = description
        # 场景包含的可执行动作列表
        self.executable_actions = executable_actions
        # 场景约束
        self.constraints = constraints
        # 场景中的链接需求
        self.linked_requirements = linked_rq
        
        # 更新约束格式
        #self.update_constraints(constraints)


    def update_constraints(self, constraints: str  ):
         # constrains中的箭头符号更改：''
        constraints = constraints.replace("→", "-->")
        # constraints中的逻辑与符号更改：&
        constraints = constraints.replace("∧", "&")
        # constraints中的逻辑或符号更改：|
        constraints = constraints.replace("∨", "|")
        # constraints中的全局符号更改：G, 用正则去除G
        constraints = re.sub(r'\bG\b', '', constraints)
        # 加入A()的外层括号
        constraints = "A (" + constraints + ")"
        self.constraints = constraints