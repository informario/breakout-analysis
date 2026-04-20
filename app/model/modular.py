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

