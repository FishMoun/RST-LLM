num_iter     = 10;
num_scenario = 10;

model_name  = "nn_12B";
input_name  = model_name + "/FromWorkspace";

% 保存每次 killed ratio
killed_ratio_each = zeros(1, num_iter);
killed_count_each = zeros(1, num_iter);

% 只加载一次模型
load_system(model_name);
root_tc_dir = 'nn_testcase_coverage_scenario';
for it = 1:num_iter
    fprintf("\n========== Iteration %d/%d ==========\n", it, num_iter);

    tc_dir = fullfile(root_tc_dir, sprintf("testcase_%d", it));
    if ~isfolder(tc_dir)
        error("测试用例目录不存在：%s", tc_dir);
    end
    for s = 1:num_scenario
    % 获取场景文件名称
        scenario_path = fullfile(tc_dir, sprintf("S%d_tc.csv", s));
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
    robustness = monitorNN(out_origin, testcases);

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


    


 

robustness = monitorNN(out_origin,testcases);

flag = robustness < 0;
killed_count = sum(flag);


function[robustness] = monitorNN(out,testcases)
    % 读取仿真数据
   
    % 获取该故障模型在某一场景下的数据
    % 配置rtamt
    % 配置rtamt
    mod = py.importlib.import_module('rtamt');
    % 遍历每个场景的测试用例
    for i = 1: 10
        spec_model = mod.StlDiscreteTimeSpecification();
        spec_model.name = 'MyMonitorModel';
        spec_model.declare_var( 'x', 'float');
        spec_model.declare_var( 'y', 'float');
        spec_model.declare_var( 'z', 'float');





        spec_model.declare_var( 'c', 'float');
       
        spec_model.spec = 'c = (z <= 1.1)';
        spec_model.parse();
       
    
        % 获取某一故障模型的仿真数据
        m1_out = out;
        
        % 获取输出
        m1_s1_out = m1_out(i);
        z = m1_s1_out.yout;


        testcase = testcases{i};
        x = testcase.Data(:,1);
        y = testcase.Data(:,2);

        
        % 计算鲁棒性值
        for t = 1:1000
            model_list = py.list({py.tuple({'x', x(t)})});
            append(model_list, py.tuple({'y',y(t)}));
            append(model_list, py.tuple({'z',z(t)}));
            robustness_model(t) = update(spec_model, t-1, model_list);
        end
        if all(robustness_model(2:end) >= 0)
            robustness(i) = 1;
        else
            robustness(i) = -1;

        end
    end
    


 
end