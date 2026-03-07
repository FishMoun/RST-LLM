addpath("testcase");
load_system("nn_12B.mdl")

num_scenario = 30;
for i = 1:num_scenario
    % 获取场景文件名称
    scenario_path = strcat("S",num2str(i),"_tc.csv");
    data = readtable(scenario_path);
    Ts = 0.1;
    time = data.time;
    tStart = time(1);
    tEnd   = time(end);
    N = floor((tEnd - tStart) / Ts);
    tq = tStart + (0:N)' * Ts;
    % 构造数据
    vals = [data.x data.y];
    xq = interp1(time, vals, tq, 'pchip');
    testcase = timeseries(xq,tq);
    testcases{1,i} = testcase;
end
% 随机方案
% for i = 1:num_scenario
%    testcase = random_testgen();
%    testcases{1,i} = testcase;
% end



input_name = strcat("nn_12B",'/FromWorkspace');
for j = 1: num_scenario
        in(j) = Simulink.SimulationInput("nn_12B");
        % 获取场景对应的matlab表达式字符串
        scenario_str = strcat('testcases','{1,',num2str(j),'}');
        % 设置不同的场景输入
        in(j) = in(j).setBlockParameter(input_name,'VariableName', scenario_str);
        in(j) = in(j).setBlockParameter(input_name,'SampleTime', "0.1");
        in(j) = setModelParameter(in(j),'CovEnable','on');
        in(j) = setVariable(in(j),'testcases',testcases);
end
out_origin = parsim(in,'TransferBaseWorkspaceVariables','on');

coverageData = out_origin(1).covdata;
for i = 2 : num_scenario
    coverageData = coverageData + out_origin(i).covdata;
end
html_str = strcat('report_se.html');
cvhtml(html_str, coverageData,'-sRT=0');