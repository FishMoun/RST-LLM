function [testcase] = random_testgen()
    cx1 = -2 + 4*rand;
    cx2 = -2 + 4*rand;
    cx3 = -2 + 4*rand;
    cy1 = -2 + 4*rand;
    cy2 = -2 + 4*rand;
    cy3 = -2 + 4*rand;
    Ts = 0.1;
    time = [0;50;100];
    tStart = time(1);
    tEnd   = time(end);
    N = floor((tEnd - tStart) / Ts);
    tq = tStart + (0:N)' * Ts;
    x = [cx1;cx2;cx3];
    y = [cy1;cy2;cy3];

    % 构造数据
    vals = [x y];
    xq = interp1(time, vals, tq, 'pchip');
    testcase = timeseries(xq,tq);
end