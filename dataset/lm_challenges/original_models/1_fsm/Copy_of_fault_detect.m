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
       
        spec_model.spec = 'c = (limits > 0.9) and (standby < 0.1) and (supported > 0.9) and (apfail < 0.1) -> (pullup > 0.9)';
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
        if all(robustness_model(2:end) >= 0)
            robustness(i) = 1;
        else
            robustness(i) = -1;

        end
    end
    


 
end
load_system("fsm_12B_fault")
input_name = strcat("fsm_12B",'/FromWorkspace');
for j = 1: num_scenario
        in(j) = Simulink.SimulationInput("fsm_12B");
        % 获取场景对应的matlab表达式字符串
        scenario_str = strcat('testcases','{1,',num2str(j),'}');
        % 设置不同的场景输入
        in(j) = in(j).setBlockParameter(input_name,'VariableName', scenario_str);
        in(j) = in(j).setBlockParameter(input_name,'SampleTime', "1");
        in(j) = setVariable(in(j),'testcases',testcases);
end
out_origin = parsim(in);
robustness = monitorFSM2(out_origin,testcases);

flag = robustness < 0;
killed_count = sum(flag);