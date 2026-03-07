addpath("testcase");
load_system("fsm_12B")

num_scenario = 10;
for i = 1:num_scenario
    % 获取场景文件名称
    scenario_path = strcat("S",num2str(i),"_tc.csv");
    data = readtable(scenario_path);
    time = data.time;
    % 构造数据
    vals = [data.standby data.apfail data.supported data.limits];
    testcase = timeseries(vals);
    testcases{1,i} = testcase;
end
% 随机方案
for i = 1:num_scenario
   testcase = random_testgen();
   testcases{1,i} = testcase;
end
input_name = strcat("fsm_12B",'/FromWorkspace');
for j = 1: num_scenario
        in(j) = Simulink.SimulationInput("fsm_12B");
        % 获取场景对应的matlab表达式字符串
        scenario_str = strcat('testcases','{1,',num2str(j),'}');
        % 设置不同的场景输入
        in(j) = in(j).setBlockParameter(input_name,'VariableName', scenario_str);
        in(j) = in(j).setBlockParameter(input_name,'SampleTime', "1");
        in(j) = setModelParameter(in(j),'CovEnable','on');
        in(j) = setVariable(in(j),'testcases',testcases);
end
out_origin = parsim(in);

coverageData = out_origin(1).covdata;
for i = 2 : num_scenario
    coverageData = coverageData + out_origin(i).covdata;
end




% 初始化用于存储每一步累积覆盖率百分比的数组
cov_trends.decision = zeros(1, num_scenario);
cov_trends.condition = zeros(1, num_scenario);
cov_trends.mcdc = zeros(1, num_scenario);
cov_trends.execution = zeros(1, num_scenario);

% 初始化累积覆盖率对象为空
cumulativeCovData = [];
model_name = 'fsm_12B';

for i = 1 : num_scenario
    currentCov = out_origin(i).covdata;
    
    % 检查当前次仿真是否产生了有效的覆盖率数据
    if isempty(currentCov)
        warning('第 %d 次仿真未产生覆盖率数据', i);
        % 如果没有新数据，保持上一轮的覆盖率（如果是第一次则为0）
        if i > 1
            cov_trends.decision(i) = cov_trends.decision(i-1);
            cov_trends.condition(i) = cov_trends.condition(i-1);
            cov_trends.mcdc(i) = cov_trends.mcdc(i-1);
            cov_trends.execution(i) = cov_trends.execution(i-1);
        end
        continue;
    end
    
    % 累加覆盖率数据
    if isempty(cumulativeCovData)
        cumulativeCovData = currentCov;
    else
        cumulativeCovData = cumulativeCovData + currentCov;
    end
    
    % 提取各类覆盖率信息 (返回格式通常为 [覆盖数, 总数])
    % 注意：如果模型未启用某种覆盖率，info函数可能报错或返回空，这里做简单处理
    try
        d_info = decisioninfo(cumulativeCovData, model_name);
        cov_trends.decision(i) = 100 * d_info(1) / d_info(2);
    catch
        cov_trends.decision(i) = 0;
    end
    
    try
        c_info = conditioninfo(cumulativeCovData, model_name);
        cov_trends.condition(i) = 100 * c_info(1) / c_info(2);
    catch
        cov_trends.condition(i) = 0;
    end
    
    try
        m_info = mcdcinfo(cumulativeCovData, model_name);
        cov_trends.mcdc(i) = 100 * m_info(1) / m_info(2);
    catch
        cov_trends.mcdc(i) = 0;
    end
    
    try
        % 执行覆盖率通常对应 Execution 或 Statement
        e_info = executioninfo(cumulativeCovData, model_name); 
        cov_trends.execution(i) = 100 * e_info(1) / e_info(2);
    catch
        cov_trends.execution(i) = 0;
    end
end

% 生成最终的 HTML 报告
html_str = strcat('report_cumulative.html');
cvhtml(html_str, cumulativeCovData, '-sRT=0');

% --- 绘制累积增长图 ---
fig = figure('Name', 'Cumulative Coverage Growth', 'Color', 'w','Visible','off');
hold on;
x_axis = 1:num_scenario;

% 绘制四条曲线
plot(x_axis, cov_trends.execution, '-o', 'LineWidth', 1.5, 'DisplayName', 'Execution');
plot(x_axis, cov_trends.decision, '-s', 'LineWidth', 1.5, 'DisplayName', 'Decision');
plot(x_axis, cov_trends.condition, '-^', 'LineWidth', 1.5, 'DisplayName', 'Condition');
plot(x_axis, cov_trends.mcdc, '-d', 'LineWidth', 1.5, 'DisplayName', 'MCDC');

% 图表美化
title('Cumulative Coverage Growth vs Number of Test Cases');
xlabel('Number of Scenarios');
ylabel('Coverage (%)');
ylim([0 100]); % 覆盖率通常在 0-100 之间
grid on;
legend('Location', 'best');

% 可以在每个点显示具体的数值（可选）
% text(x_axis(end), cov_trends.mcdc(end), sprintf('%.1f%%', cov_trends.mcdc(end)), 'VerticalAlignment', 'bottom');

hold off;
% 'Resolution', 300 表示设置为 300 DPI (高清印刷标准)
exportgraphics(fig, 'Coverage_Growth.png', 'Resolution', 300);

% 4. 关闭图形对象释放内存
close(fig);


model_name = 'fsm_12B';

% 存每个 scenario 的覆盖率
cov_each.decision   = zeros(1, num_scenario);
cov_each.condition  = zeros(1, num_scenario);
cov_each.mcdc       = zeros(1, num_scenario);
cov_each.execution  = zeros(1, num_scenario);

% 也可把 [hit total] 存下来，方便看“分母是否为0”
cov_each_raw.decision   = zeros(num_scenario, 2);
cov_each_raw.condition  = zeros(num_scenario, 2);
cov_each_raw.mcdc       = zeros(num_scenario, 2);
cov_each_raw.execution  = zeros(num_scenario, 2);

for i = 1:num_scenario
    currentCov = out_origin(i).covdata;

    if isempty(currentCov)
        warning('第 %d 次仿真未产生覆盖率数据', i);
        cov_each.decision(i)   = 0;
        cov_each.condition(i)  = 0;
        cov_each.mcdc(i)       = 0;
        cov_each.execution(i)  = 0;
        continue;
    end

    % Decision
    try
        d_info = decisioninfo(currentCov, model_name); % [hit total]
        cov_each_raw.decision(i,:) = d_info;
        cov_each.decision(i) = 100 * d_info(1) / max(d_info(2), 1);
    catch
        cov_each.decision(i) = 0;
    end

    % Condition
    try
        c_info = conditioninfo(currentCov, model_name);
        cov_each_raw.condition(i,:) = c_info;
        cov_each.condition(i) = 100 * c_info(1) / max(c_info(2), 1);
    catch
        cov_each.condition(i) = 0;
    end

    % MCDC
    try
        m_info = mcdcinfo(currentCov, model_name);
        cov_each_raw.mcdc(i,:) = m_info;
        cov_each.mcdc(i) = 100 * m_info(1) / max(m_info(2), 1);
    catch
        cov_each.mcdc(i) = 0;
    end

    % Execution / Statement
    try
        e_info = executioninfo(currentCov, model_name);
        cov_each_raw.execution(i,:) = e_info;
        cov_each.execution(i) = 100 * e_info(1) / max(e_info(2), 1);
    catch
        cov_each.execution(i) = 0;
    end
end

for i = 1:num_scenario
    currentCov = out_origin(i).covdata;
    if isempty(currentCov), continue; end

    html_name = sprintf('report_s%02d.html', i);
    cvhtml(html_name, currentCov, '-sRT=0');
end


fig = figure('Name', 'Per-Scenario Coverage', 'Color','w', 'Visible','off');
x = 1:num_scenario;

hold on;
plot(x, cov_each.execution, '-o', 'LineWidth', 1.5, 'DisplayName', 'Execution');
plot(x, cov_each.decision,  '-s', 'LineWidth', 1.5, 'DisplayName', 'Decision');
plot(x, cov_each.condition, '-^', 'LineWidth', 1.5, 'DisplayName', 'Condition');
plot(x, cov_each.mcdc,      '-d', 'LineWidth', 1.5, 'DisplayName', 'MCDC');

title('Per-Scenario Coverage');
xlabel('Scenario Index');
ylabel('Coverage (%)');
ylim([0 100]);
grid on;
legend('Location','best');
hold off;

exportgraphics(fig, 'Coverage_PerScenario.png', 'Resolution', 300);
close(fig);
