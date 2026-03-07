function [testcase] = random_testgen()
    standby = randi([0,1], 10, 1);
    apfail = randi([0,1], 10, 1);
    sensor_good = randi([0,1], 10, 1);
    limits = randi([0,1], 10, 1);

    vals = [standby apfail sensor_good limits];
  
    testcase = timeseries(vals);
end