
import re

for i in range(1, 4):
    print(f"Processing iteration {i}...")
    ai_response_path = f"./tri_testcase_llm/testcase_{i+7}/ai_responses.txt"
    with open(ai_response_path, "r", encoding="utf-8") as f:
        content = f.read()
        # 使用正则表达式提取csv代码块
        csv_content = re.findall(r"```csv\n(.*?)```", content, re.DOTALL)
        # 把所有的csv代码块分别写入一个.csv文件中
        j = 1
        if csv_content:
            for content in csv_content:
                filename = f"./tri_testcase_llm/testcase_{i+7}/S{j}_tc.csv"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                j += 1
