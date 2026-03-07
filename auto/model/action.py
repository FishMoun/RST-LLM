import re
class Action:
    def __init__(self, name: str, description: str, STL_str: str, temporal_str: str):
        # 动作名称
        self.name = name
        # 动作语义描述
        self.description = description
        # 输入约束STL
        self.STL_str = STL_str
        # 动作时序约束，t1表示动作开始时间，t2表示动作结束时间
        self.temporal_str = temporal_str
        # 更新STL格式
        self._update_STL()

    def _update_STL(self):
        self.STL_str = re.sub(r"\|\s*(.*?)\s*\|", r"abs(\1)", self.STL_str)
        self.STL_str = re.sub(r"∨", r"or", self.STL_str)
        self.STL_str = re.sub(r"∧", r" and ", self.STL_str)
        self.STL_str = re.sub(r"&&", r"and", self.STL_str)
        # 小于等于和大于等于替换
        self.STL_str = re.sub(r"≤", r"<=", self.STL_str)
        self.STL_str = re.sub(r"≥", r">=", self.STL_str)
        # False替换为0, True替换为1
        self.STL_str = re.sub(r"\bFalse\b", r"0", self.STL_str)
        self.STL_str = re.sub(r"\bTrue\b", r"1", self.STL_str)


    # 提取时序约束中的最小或最大持续时间
    def extract_duration(self,temporal_str):
        # 初始化最小和最大持续时间
        min_duration = 1
        # 最大持续时间设为30
        max_duration = 30
        pattern = r"(duration)\s*([<>]=?)\s*(\d+)"
        match = re.search(pattern, temporal_str)
        if match:
            operator = match.group(2)
            duration = int(match.group(3))
            if operator == "<":
                max_duration = duration - 1
            elif operator == "<=":
                max_duration = duration
            elif operator == ">":
                min_duration = duration + 1
            elif operator == ">=":
                min_duration = duration
        return min_duration, max_duration