clear; clc;

addpath("testcase");

num_iter     = 5;
num_scenario = 10;

model_name  = "integrator_12B_fault";
input_name  = model_name + "/FromWorkspace";

% 保存每次 killed ratio
killed_ratio_each = zeros(1, num_iter);
killed_count_each = zeros(1, num_iter);

% 只加载一次模型
load_system(model_name);
root_tc_dir  = "./tui_testcase_fault_llm";  % 根目录
for it = 1:num_iter
    fprintf("\n========== Iteration %d/%d ==========\n", it, num_iter);

    tc_dir = fullfile(root_tc_dir, sprintf("testcase_%d", it));
    if ~isfolder(tc_dir)
        error("测试用例目录不存在：%s", tc_dir);
    end
    for s = 1:num_scenario
        % 获取场景文件名称
        scenario_path = fullfile(tc_dir, sprintf("S%d_tc.csv", s));
        if ~isfile(scenario_path)
            error("缺少场景文件：%s", scenario_path);
        end
        data = readtable(scenario_path);
        Ts = 0.1;
        time = data.time;
        tStart = time(1);
        tEnd   = time(end);
        N = floor((tEnd - tStart) / Ts);
        tq = tStart + (0:N)' * Ts;
        % 构造数据
        vals = [data.xin data.reset data.ic data.TL data.BL data.T];
        xq = interp1(time, vals, tq, 'pchip');
        testcase = timeseries(xq,tq);
        testcases{1,s} = testcase;
    end

    %% 2) 构建 parsim 输入
    in = repmat(Simulink.SimulationInput(model_name), 1, num_scenario);

    for j = 1:num_scenario
        scenario_str = sprintf("testcases{1,%d}", j);

        in(j) = in(j).setBlockParameter(input_name, "VariableName", scenario_str);
        in(j) = in(j).setBlockParameter(input_name, "SampleTime", "0.1");

        % 覆盖率关闭（你要求 off）
        in(j) = setModelParameter(in(j), "CovEnable", "off");

        % 把 testcases 传给仿真（并行worker也能拿到）
        in(j) = setVariable(in(j), "testcases", testcases);
    end

    %% 3) 运行仿真
    out_origin = parsim(in);

    %% 4) 监测并统计 killed
    robustness = monitorTUI(out_origin, testcases);

    flag = robustness < 0;
    killed_count = sum(flag);

    killed_count_each(it) = killed_count;
    killed_ratio_each(it) = killed_count / num_scenario;

    fprintf("Iteration %d: killed_count = %d/%d, killed_ratio = %.2f\n", ...
        it, killed_count, num_scenario, killed_ratio_each(it));
end

%% 5) 平均值
avg_killed_ratio = mean(killed_ratio_each);

fprintf("\n===== Summary =====\n");
disp(table((1:num_iter)', killed_count_each', killed_ratio_each', ...
    'VariableNames', {'Iteration','KilledCount','KilledRatio'}));

fprintf("Average killed_ratio over %d iterations: %.4f\n", num_iter, avg_killed_ratio);


%% ===========================
%  Monitor function
% ===========================
function[robustness] = monitorTUI(out,testcases)
    % 读取仿真数据
   
    % 获取该故障模型在某一场景下的数据
    % 配置rtamt
    % 配置rtamt
    mod = py.importlib.import_module('rtamt');
    % 遍历每个场景的测试用例
    for i = 1: 10
        spec_model = mod.StlDiscreteTimeSpecification();
        spec_model.name = 'MyMonitorModel';
        spec_model.declare_var( 'xin', 'float');
        spec_model.declare_var( 'T', 'float');
        spec_model.declare_var( 'TL', 'float');
        spec_model.declare_var( 'BL', 'float');
        spec_model.declare_var( 'reset', 'float');
        spec_model.declare_var( 'ic', 'float');
        spec_model.declare_var( 'yout', 'float');




        spec_model.declare_var( 'c', 'float');
       
        spec_model.spec = 'c = (yout <= TL)';
        spec_model.parse();
       
    
        % 获取某一故障模型的仿真数据
        m1_out = out;
        
        % 获取输出
        m1_s1_out = m1_out(i);
        yout = m1_s1_out.yout;
       
        
        testcase = testcases{i};
        TL = testcase.Data(:,4);
        
        % 计算鲁棒性值
        for t = 1:201
            model_list = py.list({py.tuple({'TL', TL(t)})});
            append(model_list, py.tuple({'yout',yout(t)}));
            
            robustness_model(t) = update(spec_model, t-1, model_list);
        end
        if all(robustness_model(2:end) >= 0)
            robustness(i) = 1;
        else
            robustness(i) = -1;

        end
    end
    


 
end
% load_system("integrator_12B_fault")
% input_name = strcat("integrator_12B_fault",'/FromWorkspace');
% for j = 1: num_scenario
%         in(j) = Simulink.SimulationInput("integrator_12B_fault");
%         % 获取场景对应的matlab表达式字符串
%         scenario_str = strcat('testcases','{1,',num2str(j),'}');
%         % 设置不同的场景输入
%         in(j) = in(j).setBlockParameter(input_name,'VariableName', scenario_str);
%         in(j) = in(j).setBlockParameter(input_name,'SampleTime', "0.1");
%         in(j) = setVariable(in(j),'testcases',testcases);
% end
% out_origin = parsim(in);
robustness = monitorTUI(out_origin,testcases);

flag = robustness < 0;
killed_count = sum(flag);