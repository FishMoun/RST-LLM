# 导入场景类
from auto.model.scenario import Scenario
# 导入随机类
import random
class Enhancer:

    def __init__(self,max_combinations=5):
        # 场景最大组合数
        self.max_combinations = max_combinations


    def enhance_scenarios(self,scenarios):
        enhanced_scenarios = []
        num = len(scenarios)
        for i in range(num):
            # 随机给出当前增强场景组合数2~5
            cur_num = random.randint(2, self.max_combinations)
            # 将i号原场景作为组合的第1位
            combination = [scenarios[i]]
            # 从剩余场景中随机选择cur_num-1个场景进行组合
            for j in range(cur_num - 1):
                idx = random.randint(0, num - 1)
                while idx == i or scenarios[idx] in combination:
                    idx = random.randint(0, num - 1)
                combination.append(scenarios[idx])
            # 生成增强场景
            enhanced_scenario = self.combine_scenario(combination,i)
            enhanced_scenarios.append(enhanced_scenario)
        return enhanced_scenarios

    
    def combine_scenario(self, combination, index):
        # 将场景的数组组合并为一个场景
        combined_name = "Enh_Scenario_" + str(index)
        combined_description = " | ".join([scenario.description for scenario in combination])
        combined_actions = []
        # 合并所有场景的动作，去除重复的动作
        for scenario in combination:
            combined_actions.extend(scenario.executable_actions)
        combined_actions = list(set(combined_actions))

        # 拼接场景约束，单个场景约束形如"[A1,A2]"的字符串,多个场景约束拼接形如"[A1,A2,B1,B2]"
        combined_constraints = ""
        for scenario in combination:
            # 去除场景约束的中括号
            constraints = scenario.constraints[1:-1]
            combined_constraints += constraints + ","

        combined_constraints = "[" + combined_constraints[:-1] + "]"
        # 拼接链接需求
        linked_rq = ""
        for scenario in combination:
            linked_rq += scenario.linked_requirements + "; "
        # 创建新的增强场景对象
        enhanced_scenario = Scenario(
            name=combined_name,
            description=combined_description,
            executable_actions=combined_actions,
            constraints=combined_constraints,
            linked_rq=linked_rq
        )
        return enhanced_scenario