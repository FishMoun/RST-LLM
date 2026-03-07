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