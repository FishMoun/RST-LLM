import sys
import os
import shutil
import re
from pathlib import Path
# -------------------------
# 路径设置：保证能 import 项目模块
# -------------------------
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from llm_tool import LLMTool
from utils import Utils

# -------------------------
# 配置区（按需修改）
# -------------------------
requirement_file_path = "dataset\\lm_challenges\\original_models\\5_nn\\5_nn_reqs.docx"
root_dir = f'batch_test\\4NN\\coverage_llm'
iter = 10
# 设置测试用例输出目录
testcase_output_dir = f"batch_test\\4NN\\testcase\\nn_testcase_coverage_llm"

# 如果你希望每次迭代目录名为 testcase_{i}
ITER_DIR_PATTERN = "testcase_{i}"  # 也可以改成 "iter_{i}" / "{exp_id}"


def run_one_iteration(llm_tool: LLMTool,  out_dir: str):
    """
    单次实验：调用 LLM -> 保存 ai_response -> 提取 csv -> 存到 out_dir
    """
    os.makedirs(out_dir, exist_ok=True)

    # 读取 prompt
    with open(f'{root_dir}/NN_coverage.txt', "r", encoding="utf-8") as f:
        prompt = f.read()

    # 输出路径（全部放到 out_dir）
    ai_response_path = os.path.join(out_dir, "ai_responses.txt")

    # 1) 调 LLM，写入 ai_responses.txt
    llm_tool.chat_with_file(
        ai_response_path,
        file_path=requirement_file_path,
        user_message=prompt
    )

   
    with open(ai_response_path, "r", encoding="utf-8") as f:
        content = f.read()
        # 使用正则表达式提取csv代码块
        csv_content = re.findall(r"```csv\n(.*?)```", content, re.DOTALL)
        # 把所有的csv代码块分别写入一个.csv文件中
        i = 1
        if csv_content:
            for content in csv_content:
                filename = out_dir + f"/S{i}_tc.csv"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                i += 1


def main():
    TARGET_BASE = testcase_output_dir

    os.makedirs(TARGET_BASE, exist_ok=True)

    

    for i in range(1,11):
    

        iter_dir_name = f'testcase_{i}' 
        out_dir = os.path.join(TARGET_BASE, iter_dir_name)

        # 如果你希望每轮覆盖旧目录，先删掉
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir, exist_ok=True)

        print(f"\n=== Running experiment ===")
        print(f"Output dir: {out_dir}")
        # 每次重新实例化 LLMTool，保证对话历史不干扰
        llm_tool = LLMTool()
        run_one_iteration(llm_tool,  out_dir)

        print(f"=== Experiment completed ===")

    print("\nAll experiments completed.")
    print(f"All testcases saved under: {os.path.abspath(TARGET_BASE)}")


if __name__ == "__main__":
    main()
