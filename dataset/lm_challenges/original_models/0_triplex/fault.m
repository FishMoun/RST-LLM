function[robustness] = monitorTRI4(out,testcases)
    % 读取仿真数据
   
    % 获取该故障模型在某一场景下的数据
    % 配置rtamt
    % 配置rtamt
    mod = py.importlib.import_module('rtamt');
    % 遍历每个场景的测试用例
    for i = 1: 10
        spec_model = mod.StlDiscreteTimeSpecification();
        spec_model.name = 'MyMonitorModel';
        spec_model.declare_var( 'PC', 'int');
        spec_model.declare_var('TC', 'int');
        spec_model.declare_var( 'FC', 'int');
        spec_model.declare_var( 'set_val', 'float');
        spec_model.declare_var('Tlevel', 'float');
        spec_model.declare_var( 'PClimit', 'float');
        spec_model.declare_var('ia', 'float');
        spec_model.declare_var( 'ib', 'float');
        spec_model.declare_var('ic', 'float');
        spec_model.declare_var('no_fail','float');
        spec_model.declare_var('single_fail','float');
        spec_model.add_sub_spec('single_fail = FC > 0.1');
        spec_model.declare_var( 'C1', 'float');
        spec_model.declare_var('C2', 'float');
        spec_model.declare_var( 'C3', 'float');
        spec_model.add_sub_spec('C1 = abs(ia - ib) > Tlevel');
        spec_model.add_sub_spec('C2 = abs(ib - ic) > Tlevel');
        spec_model.add_sub_spec('C3 = abs(ia - ic) > Tlevel');
        spec_model.declare_var('fail_in_progress','float');
        spec_model.add_sub_spec('fail_in_progress = ( ((not C1) and C2 and C3) or ((not C2) and C1 and C3) or ((not C3) and C1 and C2) ) and (prev PC <= (PClimit+0.1)) and (PC > -0.1)')
        
        spec_model.declare_var('mid_value','float');
        
        spec_model.declare_var( 'c', 'float');
       
        spec_model.spec = 'c = (single_fail and fail_in_progress) -> (set_val == prev set_val)';
         spec_model.parse();
       
    
        % 获取某一故障模型的仿真数据
        m1_out = out;
        
        % 获取输出
        m1_s1_out = m1_out(i);
        data_m1_s1_out = m1_s1_out.yout.signals;
        PC = data_m1_s1_out(1).values;
        TC = data_m1_s1_out(2).values;
        FC = data_m1_s1_out(3).values;
        set_val = data_m1_s1_out(4).values;
        % 声明mid_value
        mid_value= data_m1_s1_out(5).values;
        %scenario_str = strcat("S",num2str(i),"_tc.csv");
        %T = readtable(scenario_str);
        testcase = testcases{i};
        ia = testcase.Data(:,1);
        ib = testcase.Data(:,2);
        ic = testcase.Data(:,3);
        Tlevel = testcase.Data(:,4);
        PClimit = testcase.Data(:,5);
        
        % 计算鲁棒性值
        for t = 1:30
            model_list = py.list({py.tuple({'PC', PC(t)})});
            append(model_list, py.tuple({'TC',TC(t)}));
            append(model_list, py.tuple({'FC',FC(t)}));
            append(model_list, py.tuple({'set_val',set_val(t)}));
            append(model_list, py.tuple({'mid_value',mid_value(t)}));
            append(model_list, py.tuple({'PClimit',PClimit(t)}));
            append(model_list, py.tuple({'ia',ia(t)}));
            append(model_list, py.tuple({'ib',ib(t)}));
            append(model_list, py.tuple({'ic',ic(t)}));
            append(model_list, py.tuple({'Tlevel',Tlevel(t)}));
            robustness_model(t) = update(spec_model, t-1, model_list);
        end
        if all(robustness_model(2:end) >= 0)
            robustness(i) = 1;
        else
            robustness(i) = -1;

        end
    end
    


 
end
load_system("triplex_12B_fault")


input_name = strcat("triplex_12B_fault",'/FromWorkspace');
for j = 1: num_scenario
        in(j) = Simulink.SimulationInput("triplex_12B_fault");
        % 获取场景对应的matlab表达式字符串
        scenario_str = strcat('testcases','{1,',num2str(j),'}');
        % 设置不同的场景输入
        in(j) = in(j).setBlockParameter(input_name,'VariableName', scenario_str);
        in(j) = in(j).setBlockParameter(input_name,'SampleTime', "1");
        in(j) = setModelParameter(in(j),'CovEnable','off');
        in(j) = setVariable(in(j),'testcases',testcases);
end
out_origin = parsim(in);

robustness = monitorTRI4(out_origin,testcases);

flag = robustness < 0;
killed_count = sum(flag);