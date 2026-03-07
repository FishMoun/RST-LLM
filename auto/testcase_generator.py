import random
import numpy as np
import rtamt
from deap import base, creator, tools, algorithms
from auto.model.param import ParamParser

import copy
class STL_TCGenerator:
    """
    用遗传算法搜索/生成满足给定 STL 公式的离散时间信号序列。
    - 支持配置个体长度、种群规模、进化代数、交叉/变异概率等
    - 将 RTAMT 的解析与评估、DEAP 的算法流程封装在类中
    """

    def __init__(
        self,
        seq, # 动作序列
        actions, # 动作集
        executable_actions, # 场景可执行动作
        params, # 变量集

        stl_formula: str = 'G[0,5](a >= 0.5) & G[2,5](b < 0.3)',
        gene_length: int = 10,
        pop_size: int = 30,
        ngen: int = 10,
        cxpb: float = 0.7,
        mutpb: float = 0.2,
        rng_seed: int | None = None,
    ):
        
        self.seq = seq
        self.actions = actions
        self.executable_actions = executable_actions
        self.params = params
        self.stl_formula = stl_formula
        self.gene_length = gene_length
        self.pop_size = pop_size
        self.ngen = ngen
        self.cxpb = cxpb
        self.mutpb = mutpb
        # 初始化常量字典
        self.constant_dict = {}
        # 获取输入变量列表
        self.input_params = [p for p in self.params if p.port_type == "Input" and p.name != "t" and p.is_constant != "Yes"]
        # 初始化t1和t2
        self.t1 = 0
        self.t2 = 0


        if rng_seed is not None:
            random.seed(rng_seed)
            np.random.seed(rng_seed)
        # 构建DEAP 组件
        self._build_deap()

    # ---------- RTAMT初始化规格 ----------
    def _build_spec(self,formula):
        """创建并解析 STL 规格。"""
        self.spec = rtamt.StlDiscreteTimeSpecification()
        # 声明变量集中所有的输入变量
        for param in self.params:
            # 排除时序变量和输出变量
            if param.name == "t" or param.port_type != "Input" or param.is_constant == "Yes":
                continue
            if param.data_type == "integer":
                self.spec.declare_var(param.name, 'int')
            elif param.data_type == "boolean":
                self.spec.declare_var(param.name, 'float')
            else:
                self.spec.declare_var(param.name, 'float')
            # 检查该变量是否为控制点变量
            if param.is_control_point:
                for cp in param.control_points:
                    self.spec.declare_var(cp, 'float')

        self.spec.spec = formula
        self.spec.parse()

    # ---------- DEAP遗传算法初始化组件 ----------
    def _build_deap(self):
        """创建遗传算法所需的 DEAP 组件（带幂等防护）。"""
        try:
            _ = creator.FitnessMax  # 若已创建则跳过
        except AttributeError:
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))

        try:
            _ = creator.Individual
        except AttributeError:
            creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()
        self.toolbox.register("individual", tools.initIterate, creator.Individual, self._create_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self.evaluate)
        lowers, uppers, types = self._flatten_gene_meta()

        self.toolbox.register("mate", self.mate_bounded, lowers=lowers, uppers=uppers, types=types)
        self.toolbox.register("mutate", self.mutate_bounded, lowers=lowers, uppers=uppers, types=types,
                            mu=0.0, sigma=1.0, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
   
    



    # ---------- 个体构造 ----------
    def _create_individual(self):
        # 根据输入变量个数、基因长度、各变量的输入范围，创建一个随机个体
        individual = []
        # 在input_params中寻找控制点变量,将控制点变量值加入个体最前部分
        for param in self.input_params:
            if param.is_control_point:
                for cp in param.control_points:
                    if param.data_type == "integer":
                        individual.append(random.randint(param.lower_bound, param.upper_bound))
                    elif param.data_type == "boolean":
                        individual.append(random.choice([0, 1]))  # 用0/1表示布尔值
                    else:
                        individual.append(random.uniform(param.lower_bound, param.upper_bound))
        # 从非控制点变量中加入个体剩余部分
        for param in self.input_params:
            if param.is_control_point:
                continue
            if param.data_type == "integer":
                individual.append(random.randint(param.lower_bound, param.upper_bound))
            elif param.data_type == "boolean":
                individual.append(random.choice([0, 1]))  # 用0/1表示布尔值
            else:
                individual.append(random.uniform(param.lower_bound, param.upper_bound))
        return individual

    # ---------- 数据构造与评估 ----------
    def _signals_from_individual(self, individual):
        """由个体构造信号及时间轴。"""
        
        # t 为仿真开始时间
        t = np.arange(0, 1)
        dataset = {'time':t}
        # 先构造控制点变量
        idx = 0
        for param in self.input_params:
            if param.is_control_point:
                signal = []
                for cp in param.control_points:
                    cp_value = individual[idx]
                    idx += 1;
                    signal = [cp_value]
                    dataset[cp] = np.array(signal)
        # 再构造为每个非控制点输入变量构造信号
        for param in self.input_params:
            if param.is_control_point:
                continue
            signal = [individual[idx]]
            idx += 1
            dataset[param.name] = np.array(signal)
        
        return dataset

    # ---------- 适应度函数 ----------
    def evaluate(self, individual):
        """
        适应度函数：返回 (fitness,)
        - 若所有时间点的鲁棒度 >= 0，则返回正适应度 1.0
        - 否则返回负适应度 -1.0
        """
        dataset = self._signals_from_individual(individual)
        robustness_trace = self._rtamt_evaluate(dataset)  # list[(time, rob)]
        # 若 evaluate 返回标量，也兼容处理
        if isinstance(robustness_trace, (int, float)):
            return (1.0,) if robustness_trace >= 0 else (-1.0,)

        avg_robustness = np.mean([rob for t, rob in robustness_trace])
        return (avg_robustness,)

    # ---------- 交叉 ----------------
    # def _cx2DUniform(self,ind1, ind2, indpb=0.5):
    #     point = np.random.randint(1, len(ind1))
    #     c1 = np.concatenate([ind1[:point], ind2[point:]])
    #     c2 = np.concatenate([ind2[:point], ind1[point:]])
    #     return c1, c2

    # # ---------- 变异 ----------
    # def _mut2DGaussian(self,individual, mu=0, sigma=1, indpb=0.1):
    #     y = individual.copy()
    #     for i in range(len(y)):
    #         if np.random.rand() < indpb:
    #             y[i] += np.random.normal(mu, sigma)
    #     return y
    # 基因级别的边界与类型
    def _flatten_gene_meta(self):
        lowers, uppers, types = [], [], []

        # 控制点部分（与你 _create_individual 的顺序一致）
        for param in self.input_params:
            if param.is_control_point:
                for _ in param.control_points:
                    lowers.append(param.lower_bound)
                    uppers.append(param.upper_bound)
                    types.append(param.data_type)  # "integer" / "boolean" / others

        # 非控制点部分
        for param in self.input_params:
            if param.is_control_point:
                continue
            lowers.append(param.lower_bound)
            uppers.append(param.upper_bound)
            types.append(param.data_type)

        return lowers, uppers, types
    # 修复函数
    def _clip_and_cast(self, ind, lowers, uppers, types):
        for i, x in enumerate(ind):
            lb, ub, t = lowers[i], uppers[i], types[i]

            if t == "boolean":
                # 强制回到 0/1
                ind[i] = 1 if x >= 0.5 else 0
                continue

            # clip
            if x < lb:
                x = lb
            elif x > ub:
                x = ub

            if t == "integer":
                x = int(round(x))
                if x < lb:
                    x = int(lb)
                elif x > ub:
                    x = int(ub)

            ind[i] = x
    # 交叉
    def mate_bounded(self, ind1, ind2, lowers, uppers, types):
        size = min(len(ind1), len(ind2))
        if size < 2:
            return ind1, ind2

        cx1 = random.randint(1, size - 1)
        cx2 = random.randint(1, size - 1)
        if cx2 < cx1:
            cx1, cx2 = cx2, cx1

        ind1[cx1:cx2], ind2[cx1:cx2] = ind2[cx1:cx2], ind1[cx1:cx2]

        # 修复类型/边界
        self._clip_and_cast(ind1, lowers, uppers, types)
        self._clip_and_cast(ind2, lowers, uppers, types)
        return ind1, ind2
    # 变异
    def mutate_bounded(self, ind, lowers, uppers, types, mu=0.0, sigma=1.0, indpb=0.1):
        for i, x in enumerate(ind):
            if random.random() > indpb:
                continue

            lb, ub, t = lowers[i], uppers[i], types[i]

            if t == "boolean":
                ind[i] = 1 - int(x)  # flip
                continue

            if t == "integer":
                # 整数：做一次高斯扰动，但全程保证落在范围内
                x = float(x) + random.gauss(mu, sigma)
                x = int(round(x))
                if x < lb:
                    x = int(lb)
                elif x > ub:
                    x = int(ub)
                ind[i] = x
                continue

            # 默认当作 float
            x = float(x) + random.gauss(mu, sigma)
            if x < lb:
                x = lb
            elif x > ub:
                x = ub
            ind[i] = x
        return (ind,)

    # ---------- 动作序列随机时序生成 --------
    # 输入:动作序列、时序范围、动作集
    # 输出：可映射的时序二维数组，比如[[0,1],[2,2],[3,4]]
    def _generate_time_sequence(self):
        #1 获取仿真开始和结束时间
        param_t = next((p for p in self.params if p.name == "t"), None)
        time_lower = 0
        time_upper = param_t.constant_value
        total_duration = time_upper - time_lower + 1
        # 动作序列长度
        num_actions = len(self.seq)
        # 这里可能需要考虑动作最小持续时间超过总时间的情况，暂时不处理
        # 默认最小持续时间为1
        min_durations = [1 for _ in range(num_actions)]
        remaining_duration = total_duration - sum(min_durations)
         # 默认最大持续时间为总时间
        max_durations = [remaining_duration for _ in range(num_actions)]
        
       
        # 更新动作的最小持续时间和最大持续时间
        for idx, action_name in enumerate(self.seq):
            # 考虑动作的时序约束
            action_name = self.seq[idx]
            # 在动作集中寻找该动作
            action = next((a for a in self.actions if a.name == action_name), None)
            # 提取动作的时序约束
            temporal_str = action.temporal_str
            # 代入时序约束中出现的常量
            if (temporal_str is not None) and (temporal_str != "true"):
                for var in self.constant_dict:
                        temporal_str = temporal_str.replace(var, str(self.constant_dict[var]))
                # # 用大模型辅助解析时序约束，得到最大值或最小值
                # value_type, value = self.llm_helper.getDuration(temporal_str)
                # if value_type == "最小值":
                #     min_durations[idx] = max(min_durations[idx], value)
                # elif value_type == "最大值":
                #     max_durations[idx] = min(max_durations[idx], value+1)
                # 用动作自身的方法解析时序约束，得到最大值或最小值
                min_dur, max_dur = action.extract_duration(temporal_str)
                min_durations[idx] = max(min_durations[idx], min_dur)
                max_durations[idx] = min(max_durations[idx], max_dur)
        remaining_duration = total_duration - sum(min_durations)
        # 为每个动作分配最小持续时间，并将剩余时间随机分配给每个动作
        action_times = []
        current_time = time_lower


        for i in range(num_actions):
            # 每个动作的开始时间
            action_start = current_time
            # 每个动作的持续时间，初步分配最小值
           
            action_duration = min_durations[i]
            
            # 如果还有剩余时间，随机在动作的最大持续时间范围内分配额外的时间
            if remaining_duration > 0:

                extra_time = random.randint(0, min(remaining_duration, max_durations[i] - min_durations[i]))
                action_duration += extra_time
                remaining_duration -= extra_time

            
            # 计算动作的结束时间
            action_end = action_start + action_duration - 1
            action_times.append([action_start, action_end])
            current_time = action_end + 1   # 更新下一个动作的开始时间
    
        # 如果最后还有剩余时间，分配给最后一个动作
        if remaining_duration > 0:
            action_times[-1][1] += remaining_duration
        return action_times

    # ---------- 动作序列随机时序生成，针对连续时钟周期 --------
    def _generate_time_sequence_continuous(self):
        #1 获取仿真开始和结束时间
        param_t = next((p for p in self.params if p.name == "t"), None)
        time_lower = 0
        time_upper = param_t.constant_value
        total_duration = time_upper - time_lower
        # 动作序列长度
        num_actions = len(self.seq)
        # 这里可能需要考虑动作最小持续时间超过总时间的情况，暂时不处理
        # 默认最小持续时间为1
        min_durations = [1 for _ in range(num_actions)]
        remaining_duration = total_duration - sum(min_durations)
         # 默认最大持续时间为总时间
        max_durations = [remaining_duration for _ in range(num_actions)]
        
       
        # 更新动作的最小持续时间和最大持续时间
        for idx, action_name in enumerate(self.seq):
            # 考虑动作的时序约束
            action_name = self.seq[idx]
            # 在动作集中寻找该动作
            action = next((a for a in self.actions if a.name == action_name), None)
            # 提取动作的时序约束
            temporal_str = action.temporal_str
            # 代入时序约束中出现的常量
            if (temporal_str is not None) and (temporal_str != "true"):
                for var in self.constant_dict:
                        temporal_str = temporal_str.replace(var, str(self.constant_dict[var]))
                # # 用大模型辅助解析时序约束，得到最大值或最小值
                # value_type, value = self.llm_helper.getDuration(temporal_str)
                # if value_type == "最小值":
                #     min_durations[idx] = max(min_durations[idx], value)
                # elif value_type == "最大值":
                #     max_durations[idx] = min(max_durations[idx], value+1)
                # 用动作自身的方法解析时序约束，得到最大值或最小值
                min_dur, max_dur = action.extract_duration(temporal_str)
                min_durations[idx] = max(min_durations[idx], min_dur)
                max_durations[idx] = min(max_durations[idx], max_dur)
        remaining_duration = total_duration - sum(min_durations)
        # 为每个动作分配最小持续时间，并将剩余时间随机分配给每个动作
        action_times = []
        current_time = time_lower
        for i in range(num_actions):
            # 每个动作的开始时间
            action_start = current_time
            # 每个动作的持续时间，初步分配最小值
            action_duration = min_durations[i]
            # 如果还有剩余时间，随机在动作的最大持续时间范围内分配额外的时间
            if remaining_duration > 0:
                extra_time = random.randint(0, min(remaining_duration, max_durations[i] - min_durations[i]))
                action_duration += extra_time
                remaining_duration -= extra_time

            
            # 计算动作的结束时间
            action_end = action_start + action_duration
            action_times.append([action_start, action_end])
            current_time = action_end   # 更新下一个动作的开始时间
        # 如果最后还有剩余时间，分配给最后一个动作
        if remaining_duration > 0:
            action_times[-1][1] += remaining_duration
        return action_times

    # -----------
    def _rtamt_evaluate(self, signals):
        """
        直接使用RTAMT评估信号的鲁棒度，返回鲁棒度轨迹。
        """
        signals_copy = copy.deepcopy(signals)
        # 如果时间点只有1个周期，则补充一个周期，避免RTAMT报错
        if len(signals_copy['time']) == 1:
            signals_copy['time'] = np.array([signals_copy['time'][0], signals_copy['time'][0] + 1])
            # signals中其他变量也补充一个周期的值，保持一致
            for param in signals_copy:
                if param != 'time':
                    signals_copy[param] = np.array([signals_copy[param][0], signals_copy[param][0]])
           
        robustness_trace = self.spec.evaluate(signals_copy)  # list[(time, rob)]
        return robustness_trace

    # ---------- 单个动作主流程 版本2：取种群中前n好的个体，生成的时序测试用例会重复 ----------
    #def _run(self, verbose: bool = True):
        """
        运行遗传算法，返回：
        - best_individual: 最优个体（list[float]）
        - best_robustness: 该个体的鲁棒度轨迹或标量
        - signals: 构造出的信号数据集 dict{time,a,b}
        """
        population = self.toolbox.population(n=self.pop_size)
        # 在population中加入自定义初始个体


        gen_cnt = 0
        # 选择当前种群中最优个体
        best_individual_n = tools.selBest(population,self.gene_length)
        # 构建信号
        signals = []
        for ind in best_individual_n:
            signal = self._signals_from_individual(ind)
            signals.append(signal)
        # 构建鲁棒度
        best_robustness_n = []
        for signal in signals:
            best_robustness = self._rtamt_evaluate(signal)
            best_robustness_n.append(best_robustness)
        # 如果最好的个体存在robustness小于0，则重新运行一次

        while True:
            robust_flag = True
            for best_robustness in best_robustness_n:
                # 检查鲁棒度轨迹中是否有小于0的值
                for t, rob in best_robustness:
                    if rob < 0:
                        robust_flag = False
                        break
                if not robust_flag:
                    break
            if robust_flag:
                print(f"Robustness condition met at generation {gen_cnt}.")
                break
            algorithms.eaSimple(
                            population,
                            self.toolbox,
                            cxpb=self.cxpb,
                            mutpb=self.mutpb,
                            ngen=self.ngen,
                            stats=None,
                            halloffame=None,
                            verbose= False
                            )
            gen_cnt += self.ngen
            print(f"Generation {gen_cnt} completed.")
             # 选择当前种群中最优个体
            best_individual_n = tools.selBest(population,self.gene_length)
            # 构建信号
            signals = []
            for ind in best_individual_n:
                signal = self._signals_from_individual(ind)
                signals.append(signal)
            # 构建鲁棒度
                best_robustness_n = []
            for signal in signals:
                best_robustness = self._rtamt_evaluate(signal)
                best_robustness_n.append(best_robustness)
           
        # 重构signals为单个信号
        signals_new = {}
        for key in signals[0]:
            combined_signal = np.concatenate([signals[i][key] for i in range(len(signals))])
            signals_new[key] = combined_signal
        # 其中time改成递增
        signals_new['time'] = np.arange(0, len(signals_new['time']))
        

        return (best_individual_n,best_robustness_n,signals_new)
    # ---------- 单个动作主流程 版本3：每次取种群中最优个体，重复时序次数的遗传算法流程----------
    def _run(self, verbose: bool = True):
        """
        运行遗传算法，返回：
        - best_individual: 最优个体（list[float]）
        - best_robustness: 该个体的鲁棒度轨迹或标量
        - signals: 构造出的信号数据集 dict{time,a,b}
        """
        # 运行时序次的遗传算法流程
        signals = []
        best_individuals = []
        best_robustnesses = []
        for i in range(self.gene_length):
            population = self.toolbox.population(n=self.pop_size)
            # 在population中加入自定义初始个体
            gen_cnt = 0
            # 选择当前种群中最优个体
            best_individual = tools.selBest(population,1)[0]
            # 构建信号
            signal = self._signals_from_individual(best_individual)
            # 构建鲁棒度
            best_robustness = self._rtamt_evaluate(signal)
            while True:
                robust_flag = True
                for t, rob in best_robustness:
                    if rob < 0:
                        robust_flag = False
                        break
                    if not robust_flag:
                        break
                if robust_flag:
                    print(f"Robustness condition met at generation {gen_cnt}.")
                    break
                algorithms.eaSimple(
                                population,
                                self.toolbox,
                                cxpb=self.cxpb,
                                mutpb=self.mutpb,
                                ngen=self.ngen,
                                stats=None,
                                halloffame=None,
                                verbose= False
                                )
                gen_cnt += self.ngen
               
                # 选择当前种群中最优个体
                best_individual = tools.selBest(population,1)[0]
                # 构建信号
                signal = self._signals_from_individual(best_individual)
                # 构建鲁棒度
                best_robustness = self._rtamt_evaluate(signal)
                if gen_cnt % 100 == 0:
                    print(f"Generation {gen_cnt} completed.")
                if gen_cnt >= 2000:
                    print("Reached maximum generation limit of 2000. Stopping evolution.")
                    break
            signals.append(signal)
            best_individuals.append(best_individual)
            best_robustnesses.append(best_robustness)
        # 重构signals为单个信号
        signals_new = {}
        for key in signals[0]:
            combined_signal = np.concatenate([signals[i][key] for i in range(len(signals))])
            signals_new[key] = combined_signal
        # 其中time改成递增
        signals_new['time'] = np.arange(0, len(signals_new['time']))
        

        return (best_individuals,best_robustnesses,signals_new)
   
    # ----------- 单个动作主流程，控制点版本 ----------
    def _run_control_point(self, verbose: bool = True):
        """
            运行遗传算法，返回：
            - best_individual: 最优个体（list[float]）
            - best_robustness: 该个体的鲁棒度轨迹或标量
            - signals: 构造出的信号数据集 dict{time,a,b}
            """
        population = self.toolbox.population(n=self.pop_size)
        # 在population中加入自定义初始个体
        gen_cnt = 0
        # 选择当前种群中最优个体
        best_individual = tools.selBest(population,1)[0]
        # 构建信号
        signal = self._signals_from_individual(best_individual)
        # 构建鲁棒度
        best_robustness = self._rtamt_evaluate(signal)
        while True:
            robust_flag = True
            for t, rob in best_robustness:
                if rob < 0:
                    robust_flag = False
                    break
                if not robust_flag:
                    break
            if robust_flag:
                print(f"Robustness condition met at generation {gen_cnt}.")
                break
            algorithms.eaSimple(
                            population,
                            self.toolbox,
                            cxpb=self.cxpb,
                            mutpb=self.mutpb,
                            ngen=self.ngen,
                            stats=None,
                            halloffame=None,
                            verbose= False
                            )
            gen_cnt += self.ngen
            
            # 选择当前种群中最优个体
            best_individual = tools.selBest(population,1)[0]
            # 构建信号
            signal = self._signals_from_individual(best_individual)
            # 构建鲁棒度
            best_robustness = self._rtamt_evaluate(signal)
            if gen_cnt % 100 == 0:
                print(f"Generation {gen_cnt} completed.")
            if gen_cnt >= 2000:
                print("Reached maximum generation limit of 2000. Stopping evolution.")
                break
        return (best_individual,best_robustness,signal,self.gene_length)
        
    # ---------- 动作序列主流程 ----------
    def batch_run(self):
        """
        对动作序列中的每个动作，运行遗传算法生成测试用例。
        返回一个列表，包含每个动作的 (best_individual, best_robustness, signals) 元组。
        """
        # 配置工作1: 将常量，并生成随机值填入常量字典中
        for param in self.params:
            if param.is_constant == "Yes":
                # 查看该变量常量值是否存在
                if param.constant_value is not None:
                    self.constant_dict[param.name] = param.constant_value
                else:
                    if param.data_type == "integer":
                        self.constant_dict[param.name] = random.randint(param.lower_bound, param.upper_bound)
                    elif param.data_type == "boolean":
                        self.constant_dict[param.name] = random.choice([True, False])
                    else:
                        self.constant_dict[param.name] = random.uniform(param.lower_bound, param.upper_bound)
        results = []
        # 配置工作2：根据时序变量t，获取基因长度（仿真时长+1），注意，这种目前只适用于离散周期的情况，后续需要更改


    
        # 生成动作的时序数组，如果没有控制点变量，则调用离散时钟周期的生成方法
        if any(p.is_control_point for p in self.params):
            action_time_sequence = self._generate_time_sequence_continuous()
        else:
            action_time_sequence = self._generate_time_sequence()
        #
        # 遍历动作序列，逐个生成测试用例
        for idx,action_name in enumerate(self.seq):
            action = next((a for a in self.actions if a.name == action_name), None)
            if action is None:
                raise ValueError(f"Action '{action_name}' not found in actions.")
            print(f"Generating test case for action: {action.name}")
            # 配置工作2将STL_str中的常量替换为具体数值
            STL_str_new = action.STL_str
            # for const_name, const_value in self.constant_dict.items():
            #      STL_str_new = STL_str_new.replace(const_name, str(const_value))
            # 配置工作3将STL_str中的时间变量替换为具体时间值
            self.t1 = int(action_time_sequence[idx][0])
            self.t2 = int(action_time_sequence[idx][1])
            STL_str_new = STL_str_new.replace("t1", str(0)).replace("t2", str(self.t2 - self.t1))
            self._build_spec(STL_str_new)

           
            # 运行遗传算法主流程，如果没有控制点变量，则调用普通版本
            if any(p.is_control_point for p in self.params):
                self.gene_length = self.t2 - self.t1  # 更新基因长度为当前动作的持续时间
                ga_result = self._run_control_point(verbose=True)

            else:
                self.gene_length = self.t2 - self.t1 + 1  # 更新基因长度为当前动作的持续时间
                ga_result = self._run(verbose=True)

            results.append((action.name, *ga_result,self.constant_dict))
        if any(p.is_control_point for p in self.params):
            return self.format_cp_testcases(results)
        return results

    # 整理cp的results
    def format_cp_testcases(self, results):
        formatted_results = []
        # 最小周期
        cycle = 0.01
        # 获取控制点列表
        cp_list = []
        # 获取参数化为控制点的变量名称
        p_name = ""
        for param in self.input_params:
            if param.is_control_point:
                cps = []
                p_name = param.name
                for cp in param.control_points:
                    cps.append(cp)
            cp_list.append(cps)
        num_cp = len(cp_list[0])
        start_t = 0
        action_names = []
        for (i_res,res) in enumerate(results):
            action_names.append(res[0])
            signals = res[3]
            action_duration = res[4]
            # 根据控制点个数和动作持续时间，获得控制点时刻列表
            cp_time_points = []
            for i in range(num_cp):
                cp_time = start_t + i * action_duration / (num_cp-1)
                # 从第二个result开始，控制点的第一个时间点加上一个cycle偏移
                if i_res > 0 and i == 0:
                    cp_time += cycle
                cp_time_points.append(cp_time)
            start_t += action_duration
            # 构建控制点信号字典
            cp_signals = {}
            # 为每一个控制点时刻，添加变量值
            for idx,tp in enumerate(cp_time_points):
                cp_signals[tp] = {}                
                # 添加变量值
                cp_param_order = 0
                for param in self.input_params:
                    if param.is_control_point:
                        cp_signals[tp][param.name] = signals[cp_list[cp_param_order][idx]]
                        cp_param_order += 1
                    else:
                        cp_signals[tp][param.name] = signals[param.name]
            formatted_results.append(cp_signals)
         
        # 表头
        headers = ["time"]
        # 添加输入变量
        for param in self.input_params:
            headers.append(param.name)
        # 添加常量
        for var in self.constant_dict:
            headers.append(var)
        return (formatted_results,action_names, headers,self.constant_dict)
        