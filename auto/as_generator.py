# 这里是as_generator，第二版，舍弃了模型检查判断的方案
import re
class ASG:
    def __init__(self, actions, seq_len=10):
        self.actions = actions
        self.seq_len = seq_len


    def _sequence_extractor(self, formula):
        # 提取方案："A"开头,但不包括"A"本身
        
        vars = re.findall(r'\bA[A-Za-z0-9_]+\b', formula)
        return vars

    def get_sequence(self, formula):
        vars = self._sequence_extractor(formula)
        return vars






