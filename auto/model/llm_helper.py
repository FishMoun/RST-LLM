from openai import OpenAI
import re
# 用大模型解析得到的信息，辅助其他模块工作
class LLM_Helper:
    # deepseek的密钥
    api_key = ""
    # deepseek的api
    api_url = "https://api.deepseek.com"
    # 记录缓存
    cache = {}
    def __init__(self):
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_url)
        self.messages = [ {"role": "system", "content": "You are a helpful assistant."}]

    def getDuration(self,temporal_str):
        # 设置时序区间的提示词
        prompt = """
        请解析以下表达式，提取其中的时间持续信息:
        获取t2 - t1(均为整数)的最大值或最小值，你给我提供的输出格式必须严格遵守，不用说明理由：
        最大值/最小值: x(x是具体数值)
        下面是例子：
        用户输入：t2 - t1 - 1 > 5
        回复： 最小值: 7
        用户输入：t2 - t1 - 1 <= 5
        回复： 最大值: 6
        """
        if temporal_str in self.cache.keys():
            return self.cache[temporal_str]

        # 添加用户消息
        self.messages.append({"role": "user", "content": prompt +"\n"+ temporal_str})


        completion = self.client.chat.completions.create(
            model="deepseek-reasoner",
            messages=self.messages
        )
        ai_response = completion.choices[0].message.content
        # 解析回复，提取最大值或最小值
        match = re.search(r'(最大值|最小值):\s*(\d+)', ai_response)
        if match:
            value_type = match.group(1)
            value = int(match.group(2))
            self.cache[temporal_str] = (value_type, value)
            return value_type, value
        # 如果没有匹配到则重新调用
        print("LLM回复解析失败，重新调用...", temporal_str, ai_response)
        return self.getDuration(temporal_str)

    def generateIndividual(self,requirement_str):
        # 设置生成初始个体的提示词
        prompt = """
        请根据以下需求，生成一个符合要求的初始个体表示：
        需求: {}
        输出格式必须是一个Python字典(dict)，其中包含关键属性和值。
        """
        # 添加用户消息
        self.messages.append({"role": "user", "content": prompt.format(requirement_str)})

        completion = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=self.messages
        )
        ai_response = completion.choices[0].message.content
        # 解析回复，提取字典表示
        try:
            individual_dict = eval(ai_response)
            if isinstance(individual_dict, dict):
                return individual_dict
        except:
            return None

def main():
    llm_helper = LLM_Helper()
    

if __name__ == "__main__":
    main()
