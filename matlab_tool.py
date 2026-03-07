import matlab.engine
import time
import os
class MatlabTool:

 
    def __init__(self):
        self.eng = matlab.engine.start_matlab()

    # 运行matlab脚本
    def run_mscript(self, script_path, script_log_path, model_dir):

        # 使用 MATLAB API 设置工作目录
        # 将相对路径转换为绝对路径
        model_dir = os.path.abspath(model_dir)
        self.eng.cd(model_dir, nargout=0)
        script = script_path
        try:
            # 运行 MATLAB 脚本
            # 记录运行matlab脚本的时间
            start_time = time.time()
            result = self.eng.eval(f"run('{script}')", nargout=0)
            # 运行结束时间
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"脚本运行时间: {elapsed_time:.2f}秒")
            # 将运行时间保存到指定文件中，如果文件已经存在，则追加内容
            with open(script_log_path, "a", encoding="utf-8") as f:
                f.write(f"脚本运行时间: {elapsed_time:.2f}秒\n")
                f.write(f"运行结果:\n{result}\n")
                f.write("-" * 50 + "\n")
            
            return [False, "运行成功！"]
        except Exception as e:
            # 运行时出现错误
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"脚本运行时间: {elapsed_time:.2f}秒")
            with open(script_log_path, "a", encoding="utf-8") as f:
                f.write(f"脚本运行时间: {elapsed_time:.2f}秒\n")
                f.write(f"错误信息:\n{str(e)}\n")
                f.write("-" * 50 + "\n")
            print(f"运行脚本时发生错误：{str(e)}")
            return [True, str(e)]

    # 获取Simulink模型的层级结构信息
    def get_Simulink_hierarchy(self, source_model_path,source_model_dir):
        # 根据路径获取模型名称
        model_name = os.path.splitext(os.path.basename(source_model_path))[0]

        code = f"""
        load_system('{source_model_path}');
        blocks = find_system('{model_name}', 'BlockType', 'SubSystem'); 
        blockPaths = blocks; 
        blockSIDs = cell(1, length(blocks));
        for i = 1:length(blocks)
            blockSIDs{{i}} = get_param(blocks{{i}}, 'SID');
        end
        """

        self.eng.eval(code, nargout=0)

        # 从 workspace 获取一维 cell 数组
        paths = self.eng.workspace['blockPaths']
        sids = self.eng.workspace['blockSIDs']

        # 合并为 Python 中的元组列表
        block_info = list(zip([str(p) for p in paths], [str(s) for s in sids]))

        # 输出结果
        for path, sid in block_info:
            print(f"路径: {path}, SID: {sid}")

        # 写入到txt文件中去
        output_file = source_model_dir + "/Simulink_Subsystems_SID.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            for path, sid in block_info:
                line = f"路径: {path}, SID: {sid}"
                f.write(line + "\n")  # 写入文件
        return [paths,sids, output_file]
    
    
    # 读取仿真结果csv,并将文件内容转换成字符串
    def get_simulation_results(self,model_dir):
        result_file = model_dir + "/result.csv"
        with open(result_file, "r", encoding="utf-8") as f:
            content = f.read()
        return content

# # 测试matlab
# path = "./experiments/experiment_250617_1/AFC.slx"
# matlab_tool = MatlabTool()
# matlab_tool.get_Simulink_hierarchy(path)
# matlab_tool.eng.quit()  # 关闭 MATLAB 引擎
# 测试运行函数并获取仿真结果
# script_path = "run"
# script_log_path = "./dataset/lm_challenges/original_models/0_triplex/run.log"
# model_dir = "./dataset/lm_challenges/original_models/0_triplex"
# matlab_tool = MatlabTool()
# modelName = "'triplex_12B'"
# simulation_time = 57
# ans = matlab_tool.run_mscript(script_path, script_log_path, model_dir, modelName, simulation_time)
# print(simulation_results := matlab_tool.get_simulation_results())
# matlab_tool.eng.quit()  # 关闭 MATLAB 引擎
