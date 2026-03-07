%% run_killrate_iter10_FSM4.m
% 运行10次，每次随机生成10个testcase，计算 killed_count/10 和平均值

clear; clc;

addpath("testcase");

num_iter     = 10;
num_scenario = 10;

model_name  = "fsm_12B_fault";
input_name  = model_name + "/FromWorkspace";

% 保存每次 killed ratio
killed_ratio_each = zeros(1, num_iter);
killed_count_each = zeros(1, num_iter);

% 只加载一次模型
load_system(model_name);

for it = 1:num_iter
    fprintf("\n========== Iteration %d/%d ==========\n", it, num_iter);

    %% 1) 随机生成 testcases (1 x num_scenario)
    testcases = cell(1, num_scenario);
    for i = 1:num_scenario
        testcases{1,i} = random_testgen();
    end

    %% 2) 构建 parsim 输入
    in = repmat(Simulink.SimulationInput(model_name), 1, num_scenario);

    for j = 1:num_scenario
        scenario_str = sprintf("testcases{1,%d}", j);

        in(j) = in(j).setBlockParameter(input_name, "VariableName", scenario_str);
        in(j) = in(j).setBlockParameter(input_name, "SampleTime", "1");

        % 覆盖率关闭（你要求 off）
        in(j) = setModelParameter(in(j), "CovEnable", "off");

        % 把 testcases 传给仿真（并行worker也能拿到）
        in(j) = setVariable(in(j), "testcases", testcases);
    end

    %% 3) 运行仿真
    out_origin = parsim(in);

    %% 4) 监测并统计 killed
    robustness = monitorFSM2(out_origin, testcases);

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
function[robustness] = monitorFSM2(out,testcases)
    % 读取仿真数据
   
    % 获取该故障模型在某一场景下的数据
    % 配置rtamt
    % 配置rtamt
    mod = py.importlib.import_module('rtamt');
    % 遍历每个场景的测试用例
    for i = 1: 10
        spec_model = mod.StlDiscreteTimeSpecification();
        spec_model.name = 'MyMonitorModel';
        spec_model.declare_var( 'standby', 'float');
        spec_model.declare_var( 'apfail', 'float');
        spec_model.declare_var( 'supported', 'float');
        spec_model.declare_var( 'limits', 'float');
        spec_model.declare_var( 'pullup', 'float');




        spec_model.declare_var( 'c', 'float');
       
        spec_model.spec = 'c = (limits == 1) and (standby == 0) and (supported == 1) and (apfail == 0)';
        spec_model.parse();
       
    
        % 获取某一故障模型的仿真数据
        m1_out = out;
        
        % 获取输出
        m1_s1_out = m1_out(i);

        pullup = m1_s1_out.yout;

        testcase = testcases{i};
        standby = testcase.Data(:,1);
        apfail = testcase.Data(:,2);
        supported = testcase.Data(:,3);
        limits = testcase.Data(:,4);
        
        % 计算鲁棒性值
        for t = 1:10
            model_list = py.list({py.tuple({'pullup', pullup(t)})});
            append(model_list, py.tuple({'standby',standby(t)}));
            append(model_list, py.tuple({'apfail',apfail(t)}));
            append(model_list, py.tuple({'supported',supported(t)}));
            append(model_list, py.tuple({'limits',limits(t)}));
            robustness_model(t) = update(spec_model, t-1, model_list);
        end
        if any(robustness_model(2:end) >= 0)
            robustness(i) = 1;
        else
            robustness(i) = -1;

        end
    end
    


 
end