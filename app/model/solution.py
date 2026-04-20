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
        """Genera una solución vecina, ya sea eliminar una speed o una linecard de algún step."""
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

    def solve(self, heuristic="H1"):
        """resuelve el requerimiento seleccionando linecards de forma greedy.
        levanta valueerror si el requerimiento no puede ser satisfecho o excede maxmodules."""
        requirement = self.requirement.copy()
        for col in requirement.columns:
            if col != 'code':
                requirement[col] = pd.to_numeric(requirement[col], errors='coerce')
        
        selected_linecards = []
        results = []
        num_linecards = 0
        
        req_speeds = [col for col in requirement.columns if col != 'code']
        available_speeds = set()
        for linecard in self.modular.linecards:
            available_speeds.update(linecard.speeds)
        
        for speed in req_speeds:
            if speed not in available_speeds:
                raise ValueError("this module does not contain linecards that can solve this requirement")
        
        while not self._requirement_satisfied(requirement) and num_linecards < self.modular.maxmodules:
            best_linecard = None
            best_result = None
            best_value = -float('inf')
            
            for linecard in self.modular.linecards:
                # Obtener la mejor configuración para esta linecard
                result = linecard.obtain_max_value_configuration(requirement.copy())
                if result is not None and not result.empty:
                    if heuristic == "H1":
                        value = result['value'].iloc[0]
                    elif heuristic == "H2":
                        value = result['value'].iloc[0] / linecard.cost
                    else:
                        value = result['value'].iloc[0]
                    
                    if value > best_value:
                        best_value = value
                        best_linecard = linecard
                        best_result = result
            
            if best_linecard is None:
                raise ValueError("this module does not contain linecards that can solve this requirement")
            
            selected_linecards.append(best_linecard)
            results.append(best_result)
            num_linecards += 1
            
            for col in requirement.columns:
                if col != 'code' and col in best_result.columns:
                    requirement[col] = requirement[col] - best_result[col]
        
        if not self._requirement_satisfied(requirement):
            raise ValueError("the solution exceeds maxmodules")
        
        if results and any(r is not None for r in results):
            final_result = pd.concat([r for r in results], ignore_index=True)
            return final_result
        else:
            return pd.DataFrame()
    
    def _requirement_satisfied(self, requirement):
        """verifica si el requerimiento está completamente satisfecho (todos los valores <= 0)"""
        req_speeds = [col for col in requirement.columns if col != 'code']
        for speed in req_speeds:
            if requirement[speed].iloc[0] > 0:
                return False
        return True
