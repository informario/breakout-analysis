from __future__ import annotations

import copy
import pandas as pd
import random
from app.model.modular import Modular

from abc import ABC, abstractmethod

try:
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

class State(ABC):
    @abstractmethod
    def score(self) -> float:
        raise NotImplementedError
    @abstractmethod
    def neighbor(self, T) -> "State":
        raise NotImplementedError




class Solution(State):
    _seen_states = set()

    def __init__(self, modular:Modular, req:pd.DataFrame):
        self.modular = modular
        linecards = self.modular.linecards
        speeds = [col for col in req.columns if isinstance(col, str) and col.replace('.', '', 1).isdigit()]
        self.steps = []
        for _ in range(self.modular.maxmodules):
            self.steps.append(linecards.copy())
            #self.steps.append(speeds.copy())
        self.original_steps = [sublist.copy() for sublist in self.steps]
        self.requirement = req
        self.info = None ##Last run pandas dataframe
        self._register_state()

    def _state_key(self):
        return tuple(tuple(linecard.code for linecard in step) for step in self.steps)

    def _register_state(self):
        self.__class__._seen_states.add(self._state_key())

    def neighbor(self, T=None):
        """Genera una solución vecina. El número de cambios depende de la temperatura:
        - T alta: más cambios (exploración)
        - T baja: menos cambios (refinamiento)
        Si una operación falla, intenta la opuesta."""
        max_attempts = 10
        for _ in range(max_attempts):
            new_solution = copy.deepcopy(self)
            
            # Determine number of changes based on temperature
            if T is None or T <= 0:
                num_changes = 1
            else:
                # More changes at higher temperatures
                # num_changes scales with T: at T=1 → 1 change, at T=10 → 1-2 changes, at T=100 → 2-3 changes
                num_changes = max(1, int(T / 10.0) + random.choice([0, 1]))
            
            # Apply multiple changes
            for _ in range(num_changes):
                try_delete = random.choice([True, False])
                
                try:
                    if try_delete:
                        new_solution.delete_random_element()
                    else:
                        new_solution.add_random_element()
                except ValueError:
                    # If one operation fails, try the opposite
                    try:
                        if try_delete:
                            new_solution.add_random_element()
                        else:
                            new_solution.delete_random_element()
                    except ValueError:
                        # If both fail, continue to next iteration
                        pass

            state_key = new_solution._state_key()
            if state_key not in self.__class__._seen_states:
                self.__class__._seen_states.add(state_key)
                return new_solution

        return new_solution
    
    def delete_random_element(self):
        """Randomly deletes one linecard from self.steps"""
        positions = []
        for i in range(len(self.steps)):
            sublist = self.steps[i]
            if isinstance(sublist, list) and len(sublist) > 0:
                for j in range(len(sublist)):
                    positions.append((i, j))
        if not positions:
            raise ValueError("No linecards to delete")
        step_idx, elem_idx = random.choice(positions)
        self.steps[step_idx].pop(elem_idx)

    def add_random_element(self):
        """Randomly adds back one linecard that was deleted from self.steps"""
        deletable_positions = []
        for i in range(len(self.original_steps)):
            original_sublist = self.original_steps[i]
            if isinstance(original_sublist, list):
                # Find linecards in original that are not in current
                for j, element in enumerate(original_sublist):
                    if element not in self.steps[i]:
                        deletable_positions.append((i, element))
        
        if not deletable_positions:
            raise ValueError("No deleted linecards to re-add")
        
        # Randomly select one position and linecard to re-add
        step_idx, element = random.choice(deletable_positions)
        self.steps[step_idx].append(element)

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

        candidate_linecards = [linecard for step in self.steps if isinstance(step, list) for linecard in step]
        available_speeds = set()
        for linecard in candidate_linecards:
            available_speeds.update(linecard.speeds)
        
        req_speeds = [col for col in requirement.columns if col != 'code']
        for speed in req_speeds:
            if speed not in available_speeds:
                raise ValueError("this module does not contain linecards that can solve this requirement")
        
        while not self._requirement_satisfied(requirement) and num_linecards < self.modular.maxmodules:
            if num_linecards >= len(self.steps) or not isinstance(self.steps[num_linecards], list):
                break

            slot_candidates = self.steps[num_linecards]
            if not slot_candidates:
                break

            best_linecard = None
            best_result = None
            best_value = -float('inf')
            
            for linecard in slot_candidates:
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


    def score(self):
        try:
            solution = self.solve(heuristic="H2")
        except ValueError:
            self.info = []
            return float("-inf")
        self.info = [x.code for step in self.steps for x in step]
        total_cost = 0.0
        for linecard_code in solution['code'].unique():
            linecard_rows = solution[solution['code'] == linecard_code]
            count = len(linecard_rows)
            for linecard in self.modular.linecards:
                if linecard.code == linecard_code:
                    total_cost += linecard.cost * count
                    break
        return -total_cost

