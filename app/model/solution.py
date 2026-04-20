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
        self.requirement = req

    def neighbor(self, current_solution):
        """Genera una solución vecina, ya sea eliminar una speed o una linecard de algún step.
        Returns a new Solution object without modifying the original."""
        new_solution = Solution(self.modular, current_solution)
        new_solution.steps = [sublist.copy() for sublist in self.steps]
        positions = []
        for i, sublist in enumerate(new_solution.steps):
            if isinstance(sublist, list) and len(sublist) > 0:
                for j in range(len(sublist)):
                    positions.append((i, j))
        if not positions:
            raise ValueError("No elements to delete")
        step_idx, elem_idx = random.choice(positions)
        new_solution.steps[step_idx].pop(elem_idx)
        
        return new_solution
    
    def delete_random_element(self):
        """Randomly deletes one element (either a linecard or a speed) from self.steps"""
        positions = []
        for i, sublist in enumerate(self.steps):
            if isinstance(sublist, list) and len(sublist) > 0:
                for j in range(len(sublist)):
                    positions.append((i, j))
        if not positions:
            raise ValueError("No elements to delete")
        step_idx, elem_idx = random.choice(positions)
        self.steps[step_idx].pop(elem_idx)

    def solve(self):
        requirement = self.requirement.copy()
        selected_linecards = []
        results = []
        
        # Iterar sobre pares de (linecards, speeds)
        for i in range(0, len(self.steps), 2):
            if i + 1 >= len(self.steps):
                break
                
            linecards_list = self.steps[i]
            speeds_list = self.steps[i + 1]
            
            best_linecard = None
            best_result = None
            best_value = -float('inf')
            
            for linecard in linecards_list:
                # Filtrar requirement para que solo contenga las velocidades disponibles en speeds_list
                available_speeds = speeds_list
                filtered_cols = [col for col in available_speeds if col in requirement.columns]
                filtered_requirement = requirement[filtered_cols] if filtered_cols else requirement[['code']]
                result = linecard.obtain_max_value_configuration(filtered_requirement.copy())
                if result is not None and not result.empty:
                    value = result['value'].iloc[0] / linecard.cost
                    if value > best_value:
                        best_value = value
                        best_linecard = linecard
                        best_result = result
            
            selected_linecards.append(best_linecard)
            results.append(best_result)
        
        # Combinar resultados en un DataFrame
        if results and any(r is not None for r in results):
            final_result = pd.concat([r for r in results if r is not None], ignore_index=True)
            return final_result
        else:
            return pd.DataFrame()
