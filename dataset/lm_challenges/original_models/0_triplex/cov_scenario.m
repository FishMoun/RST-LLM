%% run_triplex_cov_iter10_no_plot.m
% 迭代10次运行 triplex_12B 覆盖率统计（无画图）
% 每次迭代测试用例目录：./tri_testcase/testcase_{i}/  (i从1开始)
% 每个目录下应包含：S1_tc.csv ... S10_tc.csv

clear; clc;

%% 配置
addpath("testcase");
model_name   = "triplex_12B";
input_block  = model_name + "/FromWorkspace";

num_iter     = 10;   % 外层迭代次数
num_scenario = 10;   % 每次迭代 scenario 数（固定10）
root_tc_dir  = "./tri_testcase_llm";  % 根目录

%% 预分配结果
iter_decision  = zeros(1, num_iter);
iter_condition = zeros(1, num_iter);
iter_mcdc      = zeros(1, num_iter);

% 可选：记录 [hit total] 便于排查分母为0/未启用覆盖率
raw_decision   = zeros(num_iter, 2);
raw_condition  = zeros(num_iter, 2);
raw_mcdc       = zeros(num_iter, 2);

%% 加载模型（只需一次）
load_system(model_name);

%% 外层迭代
for it = 1:num_iter
    fprintf("\n========== Iteration %d/%d ==========\n", it, num_iter);

    tc_dir = fullfile(root_tc_dir, sprintf("testcase_%d", it));
    if ~isfolder(tc_dir)
        error("测试用例目录不存在：%s", tc_dir);
    end

    %% 1) 读取本次迭代的 10 个 CSV，构造 testcases
    testcases = cell(1, num_scenario);

    for s = 1:num_scenario
        scenario_path = fullfile(tc_dir, sprintf("S%d_tc.csv", s));
        if ~isfile(scenario_path)
            error("缺少场景文件：%s", scenario_path);
        end

        data = readtable(scenario_path);

        % 构造 timeseries（与你原脚本一致）
        vals = [data.ia data.ib data.ic data.Tlevel data.PClimit];
        testcase = timeseries(vals);
        testcases{1,s} = testcase;
    end

    %% 2) 构建 parsim 输入
    in = repmat(Simulink.SimulationInput(model_name), 1, num_scenario);

    for j = 1:num_scenario
        scenario_str = sprintf("testcases{1,%d}", j);

        in(j) = in(j).setBlockParameter(input_block, "VariableName", scenario_str);
        in(j) = in(j).setBlockParameter(input_block, "SampleTime", "1");

        % 启用覆盖率
        in(j) = setModelParameter(in(j), "CovEnable", "on");

        % 传入 testcases 到仿真环境（并行 worker 也能拿到）
        in(j) = setVariable(in(j), "testcases", testcases);
    end

    %% 3) 仿真
    out_origin = parsim(in);

    %% 4) 累加覆盖率 covdata
    cumulativeCovData = [];
    for k = 1:num_scenario
        currentCov = out_origin(k).covdata;
        if isempty(currentCov)
            warning("Iteration %d: scenario %d 未产生覆盖率数据，跳过该scenario", it, k);
            continue;
        end

        if isempty(cumulativeCovData)
            cumulativeCovData = currentCov;
        else
            cumulativeCovData = cumulativeCovData + currentCov;
        end
    end

    if isempty(cumulativeCovData)
        warning("Iteration %d: 本轮无有效覆盖率数据，Decision/Condition/MCDC 记为0", it);
        iter_decision(it)  = 0;
        iter_condition(it) = 0;
        iter_mcdc(it)      = 0;
        continue;
    end

    %% 5) 提取 Decision / Condition / MCDC 覆盖率（百分比）
    % Decision
    try
        d_info = decisioninfo(cumulativeCovData, model_name); % [hit total]
        raw_decision(it,:) = d_info;
        iter_decision(it)  = 100 * d_info(1) / max(d_info(2), 1);
    catch
        iter_decision(it) = 0;
    end

    % Condition
    try
        c_info = conditioninfo(cumulativeCovData, model_name);
        raw_condition(it,:) = c_info;
        iter_condition(it)  = 100 * c_info(1) / max(c_info(2), 1);
    catch
        iter_condition(it) = 0;
    end

    % MCDC
    try
        m_info = mcdcinfo(cumulativeCovData, model_name);
        raw_mcdc(it,:) = m_info;
        iter_mcdc(it)  = 100 * m_info(1) / max(m_info(2), 1);
    catch
        iter_mcdc(it) = 0;
    end

    fprintf("Iteration %d coverage: Decision=%.2f%%, Condition=%.2f%%, MCDC=%.2f%%\n", ...
        it, iter_decision(it), iter_condition(it), iter_mcdc(it));
end

%% 6) 10次平均
avg_decision  = mean(iter_decision);
avg_condition = mean(iter_condition);
avg_mcdc      = mean(iter_mcdc);

%% 7) 输出表格 + 结构体
T = table((1:num_iter)', iter_decision', iter_condition', iter_mcdc', ...
    'VariableNames', {'Iteration','DecisionPct','ConditionPct','MCDCPct'});
disp(T);

fprintf("\n===== Average over %d iterations =====\n", num_iter);
fprintf("Decision  Avg: %.2f%%\n", avg_decision);
fprintf("Condition Avg: %.2f%%\n", avg_condition);
fprintf("MCDC      Avg: %.2f%%\n", avg_mcdc);

results.T = T;
results.iter_decision  = iter_decision;
results.iter_condition = iter_condition;
results.iter_mcdc      = iter_mcdc;
results.avg_decision   = avg_decision;
results.avg_condition  = avg_condition;
results.avg_mcdc       = avg_mcdc;
results.raw_decision   = raw_decision;
results.raw_condition  = raw_condition;
results.raw_mcdc       = raw_mcdc;
results.num_iter       = num_iter;
results.num_scenario   = num_scenario;
results.root_tc_dir    = root_tc_dir;
