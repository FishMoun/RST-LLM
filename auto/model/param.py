import re
class Param:
    def __init__(self, name: str, data_type: any, description: str, port_type: str,is_constant: str,test_config):
        # 变量名称
        self.name = name
        # 变量数据类型
        self.data_type = data_type
        # 变量描述  
        self.description = description
        # 变量端口类型（输入/输出）
        self.port_type = port_type
        # 变量是否为常数
        self.is_constant = is_constant
        # 变量上界
        self.upper_bound = None
        # 变量下界
        self.lower_bound = None
        # 是否为控制点变量
        self.is_control_point = False
        # 控制点变量名称
        self.control_points = []
        # 变量常数值
        self.constant_value = None
        # 根据测试配置设置变量上界和下界
        self._set_bounds(test_config)

    
    # ----------- 变量范围解析 ----------
    def _parse_range(self, expr: str):
        paramParser = ParamParser(expr)
        parsed = paramParser.get_expr_results()
        if self.data_type == "integer":
            bounds = [int(parsed.low), int(parsed.high)]
        else:
            bounds = [float(parsed.low), float(parsed.high)]
        return bounds

    # ---------- 变量上下界设置 ----------
    def _set_bounds(self,test_config):
        pattern = rf'(?<![A-Za-z0-9_]){self.name}(?![A-Za-z0-9_])'
        for expr in test_config:
            if re.search(pattern, expr):
                # 识别是否为控制点变量:xin=pchip(c1,c2,c3), 
                if "pchip" in expr:
                    self.is_control_point = True
                    # 提取控制点变量名称,'c1','c2','c3'
                    control_point_names = re.findall(r'pchip\((.*?)\)', expr)
                    if control_point_names:
                        points = control_point_names[0].split(',')
                        self.control_points = [point.strip() for point in points]
                    continue
                # 常值设置: 正则识别'T=0.1'模式
                elif re.match(rf'^{self.name}\s*=\s*[-+]?\d*\.?\d+$', expr):
                    value_str = expr.split('=')[1].strip()
                    if self.data_type == "integer":
                        self.constant_value = int(value_str)
                    else:
                        self.constant_value = float(value_str)
                    continue
                # 找到包含变量的表达式，解析上下界
                bounds = self._parse_range(expr)
                if bounds is not None:
                    self.lower_bound, self.upper_bound = bounds
                    return
    


from pyparsing import Word, nums, alphas, delimitedList, oneOf, Literal, Optional, Suppress
from pyparsing import pyparsing_common as ppc
class ParamParser:
    # ===== 基础元素 =====
    
    number = ppc.number()# 支持整数和小数
    variable = Word(alphas, alphas + nums + '_')  # 变量名
    var_list = delimitedList(variable)
    compare = oneOf("≤ < >= > <= =")                 # 比较符
    # ===== 新增支持: t ∈ N =====
    in_symbol = Literal("ϵ")
    natural_set = Literal("N")

    var_in_naturals = (variable("var") + in_symbol + natural_set("set"))

    # ===== 普通区间表达式（可用于单变量或多变量表）=====
    range_expr = number("low") + compare + var_list("vars") + compare + number("high")

    # ===== 综合规则：支持可选的 “t ∈ N,” 前缀 =====
    full_expr = Optional(var_in_naturals + Suppress(","))("prefix") + range_expr

    def __init__(self,expr:str):
        self.expr = self.full_expr.parseString(expr)

    def get_expr_results(self):
        return self.expr

# 测试
def main():
    expr = "t ∈ N, 5 < t < 15"
    parser = ParamParser(expr)
    result = parser.get_expr_results()
    print(result)

if __name__ == "__main__":
    main()

