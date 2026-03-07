
%% 基本配置
model_name   = "nn_12B";
input_block  = model_name + "/FromWorkspace";
num_scenario = 10;      % 每次迭代跑多少个 scenario
num_iter     = 10;      % 外层迭代次数

% 预分配结果
iter_cov.decision  = zeros(1, num_iter);
iter_cov.condition = zeros(1, num_iter);
iter_cov.mcdc      = zeros(1, num_iter);

% 可选：记录每次迭代的 [hit total]，便于排查分母为 0
iter_cov_raw.decision  = zeros(num_iter, 2);
iter_cov_raw.condition = zeros(num_iter, 2);
iter_cov_raw.mcdc      = zeros(num_iter, 2);

%% 加载模型（只需一次）
load_system(model_name);

%% 外层迭代
for it = 1:num_iter
    fprintf("========== Iteration %d/%d ==========\n", it, num_iter);

    %% 1) 生成 testcases（1 x num_scenario）
    testcases = cell(1, num_scenario);
    for i = 1:num_scenario
        testcases{1,i} = random_testgen();
    end

    %% 2) 构建 parsim 输入
    in = repmat(Simulink.SimulationInput(model_name), 1, num_scenario);

    for j = 1:num_scenario
        % 注意：VariableName 传入字符串表达式，引用 workspace 中的 testcases
        scenario_str = sprintf("testcases{1,%d}", j);

        in(j) = in(j).setBlockParameter(input_block, "VariableName", scenario_str);
        in(j) = in(j).setBlockParameter(input_block, "SampleTime", "0.1");

        % 启用覆盖率
        in(j) = setModelParameter(in(j), "CovEnable", "on");

        % 把 testcases 放进仿真 workspace（每个 in 都设置一遍，保证并行 worker 也拿得到）
        in(j) = setVariable(in(j), "testcases", testcases);
    end

    %% 3) 并行仿真
    out_origin = parsim(in,'TransferBaseWorkspaceVariables','on');

    %% 4) 累计覆盖率（把 10 个 scenario covdata 叠加）
    cumulativeCovData = [];

    for k = 1:num_scenario
        currentCov = out_origin(k).covdata;

        if isempty(currentCov)
            warning("Iteration %d: scenario %d 未产生覆盖率数据，跳过该 scenario", it, k);
            continue;
        end

        if isempty(cumulativeCovData)
            cumulativeCovData = currentCov;
        else
            cumulativeCovData = cumulativeCovData + currentCov;
        end
    end

    if isempty(cumulativeCovData)
        warning("Iteration %d: 没有任何有效覆盖率数据，本轮覆盖率记为 0", it);
        iter_cov.decision(it)  = 0;
        iter_cov.condition(it) = 0;
        iter_cov.mcdc(it)      = 0;
        continue;
    end

    %% 5) 提取 Decision / Condition / MCDC 覆盖率
    % Decision
    try
        d_info = decisioninfo(cumulativeCovData, model_name);  % [hit total]
        iter_cov_raw.decision(it,:) = d_info;
        iter_cov.decision(it) = 100 * d_info(1) / max(d_info(2), 1);
    catch
        iter_cov.decision(it) = 0;
    end

    % Condition
    try
        c_info = conditioninfo(cumulativeCovData, model_name);
        iter_cov_raw.condition(it,:) = c_info;
        iter_cov.condition(it) = 100 * c_info(1) / max(c_info(2), 1);
    catch
        iter_cov.condition(it) = 0;
    end

    % MCDC
    try
        m_info = mcdcinfo(cumulativeCovData, model_name);
        iter_cov_raw.mcdc(it,:) = m_info;
        iter_cov.mcdc(it) = 100 * m_info(1) / max(m_info(2), 1);
    catch
        iter_cov.mcdc(it) = 0;
    end

    fprintf("Iteration %d coverage: Decision=%.2f%%, Condition=%.2f%%, MCDC=%.2f%%\n", ...
        it, iter_cov.decision(it), iter_cov.condition(it), iter_cov.mcdc(it));
end

%% 6) 计算 10 次平均覆盖率
avg_cov.decision  = mean(iter_cov.decision);
avg_cov.condition = mean(iter_cov.condition);
avg_cov.mcdc      = mean(iter_cov.mcdc);

%% 7) 汇总输出
results.iter_cov      = iter_cov;
results.avg_cov       = avg_cov;
results.iter_cov_raw  = iter_cov_raw;
results.num_iter      = num_iter;
results.num_scenario  = num_scenario;

% 命令行表格输出（更直观）
T = table((1:num_iter)', iter_cov.decision', iter_cov.condition', iter_cov.mcdc', ...
    'VariableNames', {'Iteration','DecisionPct','ConditionPct','MCDCPct'});
disp(T);

fprintf("\n===== Average over %d iterations =====\n", num_iter);
fprintf("Decision  Avg: %.2f%%\n", avg_cov.decision);
fprintf("Condition Avg: %.2f%%\n", avg_cov.condition);
fprintf("MCDC      Avg: %.2f%%\n", avg_cov.mcdc);
