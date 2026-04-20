import pandas as pd
import random
from app.model.modular import Modular


class Solution:
    def __init__(self, modular:Modular, req:pd.DataFrame):
        self.modular = modular
        linecards = self.modular.linecards
        speeds = [col for col in req.columns if isinstance(col, str) and col.replace('.', '', 1).isdigit()]
        # Create copies of linecards and speeds for each module to avoid shared references
        self.steps = []
        for _ in range(self.modular.maxmodules):
            self.steps.append(linecards.copy())
            self.steps.append(speeds.copy())

    def neighbor(self, current_solution):
        """Genera una solución vecina, ya sea eliminar una speed o una linecard de algún step"""
        positions = []
        for i, sublist in enumerate(self.steps):
            if isinstance(sublist, list) and len(sublist) > 0:
                for j in range(len(sublist)):
                    positions.append((i, j))
        if not positions:
            raise ValueError("No elements to delete")
        step_idx, elem_idx = random.choice(positions)
        self.steps[step_idx].pop(elem_idx)
