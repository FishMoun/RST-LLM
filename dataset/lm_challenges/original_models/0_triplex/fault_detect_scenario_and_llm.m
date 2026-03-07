%% run_killrate_iter10_TRI4.m
% 运行10次，每次随机生成10个testcase，计算 killed_count/10 和平均值

clear; clc;

addpath("testcase");

num_iter     = 10;
num_scenario = 10;

model_name  = "triplex_12B_fault";
input_name  = model_name + "/FromWorkspace";
root_tc_dir  = "./tri_testcase_llm_fault";  % 根目录
% 保存每次 killed ratio
killed_ratio_each = zeros(1, num_iter);
killed_count_each = zeros(1, num_iter);

% 只加载一次模型
load_system(model_name);

for it = 1:num_iter
    fprintf("\n========== Iteration %d/%d ==========\n", it, num_iter);
    if it == 2 || it == 8 || it == 10
        continue;
    end
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
    robustness = monitorTRI4(out_origin, testcases, num_scenario);

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
function robustness = monitorTRI4(out, testcases, num_scenario)
    % out: parsim输出数组
    % testcases: 1 x num_scenario cell，每个是timeseries(Data列: ia ib ic Tlevel PClimit)
    % 返回 robustness: 1 x num_scenario (>=0 视为通过，<0 视为未通过；这里按你原逻辑输出 +1/-1)

    robustness = ones(1, num_scenario);  % 预分配

    % 导入 rtamt
    mod = py.importlib.import_module('rtamt');

    for i = 1:num_scenario
        % --- 每个scenario创建一个新spec，避免状态残留 ---
        spec_model = mod.StlDiscreteTimeSpecification();
        spec_model.name = 'MyMonitorModel';

        % 变量声明
        spec_model.declare_var('PC', 'int');
        spec_model.declare_var('TC', 'int');
        spec_model.declare_var('FC', 'int');
        spec_model.declare_var('set_val', 'float');
        spec_model.declare_var('Tlevel', 'float');
        spec_model.declare_var('PClimit', 'float');
        spec_model.declare_var('ia', 'float');
        spec_model.declare_var('ib', 'float');
        spec_model.declare_var('ic', 'float');

        spec_model.declare_var('no_fail', 'float');
        spec_model.declare_var('single_fail', 'float');
        spec_model.add_sub_spec('single_fail = FC > 0.1');

        spec_model.declare_var('C1', 'float');
        spec_model.declare_var('C2', 'float');
        spec_model.declare_var('C3', 'float');
        spec_model.add_sub_spec('C1 = abs(ia - ib) > Tlevel');
        spec_model.add_sub_spec('C2 = abs(ib - ic) > Tlevel');
        spec_model.add_sub_spec('C3 = abs(ia - ic) > Tlevel');

        spec_model.declare_var('fail_in_progress', 'float');
        spec_model.add_sub_spec([ ...
            'fail_in_progress = ( ((not C1) and C2 and C3) or ((not C2) and C1 and C3) or ((not C3) and C1 and C2) ) ' ...
            'and (prev PC <= (PClimit+0.1)) and (PC > -0.1)' ...
        ]);

        % mid_value 在你的代码里读了，但 spec 里没用到；保留声明不影响
        spec_model.declare_var('mid_value', 'float');

        spec_model.declare_var('c', 'float');
        spec_model.spec = 'c = (single_fail and fail_in_progress) -> (set_val == prev set_val)';
        spec_model.parse();

        % --- 取仿真输出 ---
        m1_s1_out = out(i);
        data_out  = m1_s1_out.yout.signals;

        PC       = data_out(1).values;
        TC       = data_out(2).values;
        FC       = data_out(3).values;
        set_val  = data_out(4).values;
        mid_value= data_out(5).values;

        % --- 取输入 testcase ---
        testcase = testcases{1,i};
        ia      = testcase.Data(:,1);
        ib      = testcase.Data(:,2);
        ic      = testcase.Data(:,3);
        Tlevel  = testcase.Data(:,4);
        PClimit = testcase.Data(:,5);

        % 在线更新的鲁棒性
        T = 30;  % 你原脚本写死1:30，这里保持一致
        robustness_model = zeros(1, T);

        for t = 1:T
            model_list = py.list();

            model_list.append(py.tuple({'PC',       double(PC(t))}));
            model_list.append(py.tuple({'TC',       double(TC(t))}));
            model_list.append(py.tuple({'FC',       double(FC(t))}));
            model_list.append(py.tuple({'set_val',  double(set_val(t))}));
            model_list.append(py.tuple({'mid_value',double(mid_value(t))}));

            model_list.append(py.tuple({'PClimit',  double(PClimit(t))}));
            model_list.append(py.tuple({'ia',       double(ia(t))}));
            model_list.append(py.tuple({'ib',       double(ib(t))}));
            model_list.append(py.tuple({'ic',       double(ic(t))}));
            model_list.append(py.tuple({'Tlevel',   double(Tlevel(t))}));

            % rtamt在线更新：time从0开始，所以用 (t-1)
            robustness_model(t) = double(update(spec_model, t-1, model_list));
        end

        % 你原逻辑：robustness_model(2:end) 全部 >=0 就认为通过
        if all(robustness_model(2:end) >= 0)
            robustness(i) = 1;
        else
            robustness(i) = -1;
        end
    end
end
