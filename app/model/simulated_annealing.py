import math
import random


class SimulatedAnnealing:
    def __init__(self, l: float, t: float, state, *state_args, **state_kwargs):
        self.l = l
        self.t = t
        self.s = state(*state_args, **state_kwargs) if callable(state) else state
        self.best = self.s
        self.history = []
        self.attempt_history = []
        self._record(self.s, self.history)

    def choose(self, neighbor):
        current = self.s
        best = self.best
        n_score = neighbor.score()
        c_score = current.score()
        b_score = best.score()

        if n_score > c_score:
            return neighbor

        eps = 1e-12
        prob = 2 * math.exp((n_score - c_score) / max(self.t, eps))
        prob2 = 2 * math.exp((c_score - b_score) / max(self.t, eps))

        if random.random() < prob2:
            return best
        if random.random() < prob:
            return neighbor
        return current

    def _snapshot(self, state):
        steps_snapshot = [
            [linecard.code for linecard in step]
            for step in getattr(state, "steps", [])
            if isinstance(step, list)
        ]
        return steps_snapshot

    def _record(self, state, history_list):
        score = state.score()
        steps_snapshot = self._snapshot(state)
        history_list.append((steps_snapshot, score, self.t))

    def history_arrays(self):
        """Return separate lists for accepted step history, score, and temperature."""
        step_history = [h[0] for h in self.history]
        score_list = [h[1] for h in self.history]
        temp_list = [h[2] for h in self.history]
        return step_history, score_list, temp_list

    def attempt_history_arrays(self):
        """Return separate lists for attempted step history, score, and temperature."""
        step_history = [h[0] for h in self.attempt_history]
        score_list = [h[1] for h in self.attempt_history]
        temp_list = [h[2] for h in self.attempt_history]
        return step_history, score_list, temp_list

    def cool(self):
        self.t *= math.exp(-self.l)

    def run(self):
        while self.t > 0.001:
            neighbor = self.s.neighbor(self.t)
            self._record(neighbor, self.attempt_history)
            self.s = self.choose(neighbor)
            if self.s.score() > self.best.score():
                self.best = self.s
            self._record(self.s, self.history)
            self.cool()
        return self.best