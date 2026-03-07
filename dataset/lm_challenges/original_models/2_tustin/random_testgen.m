% TUI random test generator (PCHIP template)
% Given constraints:
% 1) xin is PCHIP with 3 control points: -1 <= xin <= 1
% 2) -10 <= TL <= 10
% 3) -10 <= BL <= 10
% 4) t_end = 20 (simulation time)
% 5) -10 <= ic <= 10
% 6) T = 0.1
% Input order: [data.xin data.reset data.ic data.TL data.BL data.T]

function testcase = random_testgen()

    %% Sample time (match TUI sample time)
    Ts = 0.1;

    %% Time definition (3 control points for pchip)
    time   = [0; 10; 20];
    tStart = time(1);
    tEnd   = time(end);
    N      = floor((tEnd - tStart) / Ts);
    tq     = tStart + (0:N)' * Ts;

    %% ===============================
    %  Continuous input: xin (pchip)
    %% ===============================

    % xin domain: [-1, 1]
    c1 = -1 + 2 * rand;
    c2 = -1 + 2 * rand;
    c3 = -1 + 2 * rand;
    xin_pts = [c1; c2; c3];

    %% ===============================
    %  Discrete / constant inputs
    %% ===============================

    % reset (Boolean 0/1) -- kept constant over the run (3 control points)
    reset_val = randi([0,1]);
    reset_pts = reset_val * ones(3,1);

    % TL, BL in [-10, 10], enforce BL <= TL
    BL  = -10 + 20 * rand;
    TL  = -10 + 20 * rand;

    TL_pts = TL * ones(3,1);
    BL_pts = BL * ones(3,1);

    % ic in [-10, 10] (kept constant over the run)
    ic = -10 + 20 * rand;
    ic_pts = ic * ones(3,1);

    % T is constant 0.1 (kept constant over the run)
    T = 0.1;
    T_pts = T * ones(3,1);

    %% ===============================
    %  Construct input matrix (3-point values)
    %% ===============================

    % Order must match Simulink Inport order:
    % [xin reset ic TL BL T]
    vals = [ ...
        xin_pts, ...
        reset_pts, ...
        ic_pts, ...
        TL_pts, ...
        BL_pts, ...
        T_pts ...
    ];

    %% Interpolation (continuous evolution for xin; others remain constant)
    xq = interp1(time, vals, tq, 'pchip');

    %% Output timeseries
    testcase = timeseries(xq, tq);

end
