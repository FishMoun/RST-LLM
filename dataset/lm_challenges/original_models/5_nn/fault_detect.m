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
load_system("nn_12B.mdl")
input_name = strcat("nn_12B",'/FromWorkspace');
for j = 1: num_scenario
        in(j) = Simulink.SimulationInput("nn_12B");
        % 获取场景对应的matlab表达式字符串
        scenario_str = strcat('testcases','{1,',num2str(j),'}');
        % 设置不同的场景输入
        in(j) = in(j).setBlockParameter(input_name,'VariableName', scenario_str);
        in(j) = in(j).setBlockParameter(input_name,'SampleTime', "0.1");
        in(j) = setVariable(in(j),'testcases',testcases);
end
out_origin = parsim(in,'TransferBaseWorkspaceVariables','on');
robustness = monitorNN(out_origin,testcases);

flag = robustness < 0;
killed_count = sum(flag);