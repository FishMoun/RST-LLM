import random
from pyModelChecking import Kripke, LTL

class LTLActionGenerator_pyMC:
    def __init__(self, actions, formula_str, seq_len=10, tries=200, verbose=False):
        self.actions = actions
        self.formula_str = formula_str
        self.seq_len = seq_len
        self.tries = tries
        self.verbose = verbose
        self.parser = LTL.Parser()


    def random_sequence(self):
        """随机生成长度在 1 ~ seq_len 之间的动作序列，且不出现连续相同动作"""
        length = random.randint(1, self.seq_len)

        if not self.actions:
            return []

        # 如果只有一个动作可选，那么长度只能是 1，否则无法避免连续重复
        if len(self.actions) == 1:
            return [self.actions[0]]  # 或者 raise ValueError("actions 只有一个元素，无法生成无连续重复序列")

        seq = []
        prev = None
        for _ in range(length):
            # 候选动作：排除上一个动作
            candidates = self.actions if prev is None else [a for a in self.actions if a != prev]
            action = random.choice(candidates)
            seq.append(action)
            prev = action

        return seq


    def build_kripke(self, seq):
        """将动作序列转成 Kripke 结构"""
        states = [f"s{i}" for i in range(len(seq))]
        transitions = {(states[i], states[i+1]) for i in range(len(seq)-1)}
        # 最后一个状态自环
        transitions.add((states[-1], states[-1]))

        # 状态标签：每步仅该动作为真
        labeling = {s: {seq[i]} for i, s in enumerate(states)}

        return Kripke(S=set(states), R=transitions, L=labeling)

    def fitness(self, seq):
        # 评估seq是否包含了所有动作
        if not all(action in seq for action in self.actions):
            return -10  # 未包含所有动作，惩罚较大

        """评估序列是否满足公式"""
        K = self.build_kripke(seq)
        
        formula = self.parser(self.formula_str)
        result = LTL.modelcheck(K, formula)
        return 10 if len(result) > 0 else -10

    def mutate(self, seq, rate=0.3):
        new_seq = seq[:]
        for i in range(len(seq)):
            if random.random() < rate:
                new_seq[i] = random.choice(self.actions)
        # 有概率变异长度
        for _ in range(2):
            if random.random() < rate:
                if len(new_seq) < self.seq_len and random.random() < 0.5:
                    new_seq.append(random.choice(self.actions))
                elif len(new_seq) > 1:
                    new_seq.pop(random.randint(0, len(new_seq)-1))
                # 判断变异体是否出现了连续相同动作，若有则重新变异该位置动作
        for i in range(1, len(new_seq)):
            if new_seq[i] == new_seq[i-1]:
                candidates = [a for a in self.actions if a != new_seq[i-1]]
                new_seq[i] = random.choice(candidates)
        return new_seq

    def search(self):
        best_seq = None
        best_score = float("-inf")

        current = self.random_sequence()
        if len(self.actions) == 1:
            return current, self.fitness(current)
        current_score = self.fitness(current)

        for i in range(self.tries):
            candidate = self.mutate(current)
            candidate_score = self.fitness(candidate)

            if candidate_score >= current_score:
                current = candidate
                current_score = candidate_score
                if current_score > best_score:
                    best_seq = current
                    best_score = current_score

            if self.verbose and i % 100 == 0:
                print(f"[{i}] best_score={best_score}, current={current}")

            if best_score >= 10:
                break
        
        return best_seq, best_score


# ----------------------------------------
# 示例运行
# ----------------------------------------
if __name__ == "__main__":
   

    actions = ["A1", "A2"]
    formula = "A G(A1  --> F A2)"  # 若A1发生，则未来必有A2
    generator = LTLActionGenerator_pyMC(actions, formula, seq_len=10, tries=500, verbose=True)
    seq, score = generator.search()

    print("\n✅ Found sequence:")
    print(seq)
    print("Fitness:", score)
