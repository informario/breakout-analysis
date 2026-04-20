import pandas as pd
from .switch import Switch


class Modular:
    def __init__(self, data: pd.DataFrame):
        # Find the modular row (type == "modular")
        modular_rows = data[data["type"] == "modular"]
        if modular_rows.empty:
            raise ValueError("No modular switch found in data")
        
        modular_row = modular_rows.iloc[0]
        self.name = modular_row["code"]
        self.family = modular_row["family"]
        self.maxmodules = int(modular_row["maxmodules"]) if pd.notna(modular_row["maxmodules"]) else None

        linecard_rows = data[data["type"] == "linecard"]
        
        self.linecards = []
        for code in linecard_rows["code"].unique():
            code_data = linecard_rows[linecard_rows["code"] == code].reset_index(drop=True)
            switch = Switch(code_data)
            self.linecards.append(switch)


    def get_best_linecard(self, requirement: pd.DataFrame, heuristic="H1"):
        best_linecard = None
        best_result = None
        best_value = -float('inf')
        
        for linecard in self.linecards:
            result = linecard.obtain_max_value_configuration(requirement.copy())
            if result is not None and not result.empty:
                match heuristic:
                    case "H1":
                        value = result['value'].iloc[0]
                    case "H2":
                        value = result['value'].iloc[0] / linecard.cost
                if value > best_value:
                    best_value = value
                    best_linecard = linecard
                    best_result = result
        
        return best_linecard, best_result

    def solve_requirement(self, requirement: pd.DataFrame, heuristic="H1"):
        """selecciona linecards iterativamente,obtiene la mejor linecard
        de forma greedy
        """
        selected_linecards = []
        current_requirement = requirement.copy()
        
        max_iterations = 100
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1

            best_linecard, result = self.get_best_linecard(current_requirement, heuristic)

            if best_linecard is None or result is None:
                break

            selected_linecards.append(result)

            for col in current_requirement.columns:
                if col not in ["code"]:
                    if col in result.columns:
                        config_value = result[col].iloc[0]
                        current_value = current_requirement[col].iloc[0]
                        
                        current_value = 0 if pd.isna(current_value) else float(current_value)
                        config_value = 0 if pd.isna(config_value) else float(config_value)
                        
                        new_value = current_value - config_value
                        
                        current_requirement.at[0, col] = max(0.0, new_value)

            all_satisfied = True
            for col in current_requirement.columns:
                if col not in ["code"]:
                    val = current_requirement[col].iloc[0]
                    if not pd.isna(val) and float(val) > 1e-6:
                        all_satisfied = False
                        break
            
            if all_satisfied:
                break

        if self.maxmodules is not None and len(selected_linecards) > self.maxmodules:
            raise ValueError("the solution exceeds maxmodules")

        if selected_linecards:
            return pd.concat(selected_linecards, ignore_index=True)
        else:
            raise ValueError("this module does not contain linecards that can solve this requirement")



