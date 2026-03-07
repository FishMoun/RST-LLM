function [testcase] = random_testgen()
    Ts = 1;
    ia = 20*rand(31,1);
    ib = 20*rand(31,1);
    ic = 20*rand(31,1);

    Tlevel = rand*ones(31,1);
    PClimit = randi(5)*ones(31,1);
    
    % 构造数据
    vals = [ia ib ic Tlevel PClimit];
    testcase = timeseries(vals);
end