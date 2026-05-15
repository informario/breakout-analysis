import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull
from scipy.optimize import linprog
from itertools import combinations


def get_numeric_feature_columns(df: pd.DataFrame) -> list:
    return [col for col in df.columns if _is_numeric_string(col)]

def _is_numeric_string(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_vertices_from_dataframe(data: pd.DataFrame):
    speeds = get_numeric_feature_columns(data)
    vertices = []
    speeds_data = data[speeds]

    speeds_data = speeds_data.apply(pd.to_numeric, errors="coerce")
    speeds_data = speeds_data.dropna(how="all", axis=1)

    speeds = speeds_data.columns.tolist()

    for _, row in speeds_data.iterrows():
        values = []
        nonzero_indices = []

        for i, speed in enumerate(speeds):
            val = row[speed]
            if pd.notna(val) and val != 0:
                values.append(float(val))
                nonzero_indices.append(i)
            else:
                values.append(0.0)

        # agregar el punto original
        vertices.append(values)

        # si hay más de una coordenada activa, agregar proyecciones
        # generar todas las combinaciones posibles de coordenadas no-cero (excepto el punto original)
        if len(nonzero_indices) > 1:
            # generar combinaciones desde tamaño n-1 hasta tamaño 1
            for r in range(len(nonzero_indices) - 1, 0, -1):
                for combo in combinations(nonzero_indices, r):
                    proj = [0.0] * len(speeds)
                    for idx in combo:
                        proj[idx] = values[idx]
                    vertices.append(proj)

    return vertices, speeds


class Switch:
    def __init__(self, data: pd.DataFrame):
        self.code = data["code"].iloc[0]
        cost_value = data["cost"].iloc[0] if "cost" in data.columns else 1
        self.cost = float(cost_value) if pd.notna(cost_value) else 1.0
        vertices, self.speeds = get_vertices_from_dataframe(data)

        origin = np.array([0.0] * len(self.speeds))
        polytope_vertices = np.vstack([np.array(vertices, dtype=float), origin])

        # Handle 1-dimensional case separately (ConvexHull requires at least 2D)
        if len(self.speeds) == 1:
            self.hull = None
            self.A = None
            self.b = None
            self.max_value = np.max(polytope_vertices)
        else:
            self.hull = ConvexHull(polytope_vertices)
            # ecuaciones de las caras: Ax + b <= 0
            self.A = self.hull.equations[:, :-1]
            self.b = self.hull.equations[:, -1]

    def normalize_requirement_dataframe(self, requirements:pd.DataFrame):
        if requirements.shape[0] < 1:
            print("requirements should contain at least 1 row")
            return False

        req_df = requirements.copy()
        req_speeds = get_numeric_feature_columns(req_df)

        if not req_speeds:
            #print("no numeric speed columns found in requirements")
            return False

        nonnull_counts = req_df[req_speeds].notna().sum(axis=1)
        selected_row_idx = nonnull_counts.idxmax()
        selected_row = req_df.loc[selected_row_idx]

        if not set(req_speeds).issubset(set(self.speeds)):
            #print("requirements contain speeds not available on this Switch")
            return False

        aligned_point = []
        for speed in self.speeds:
            if speed in req_df.columns and pd.notna(selected_row.get(speed)):
                aligned_point.append(float(selected_row[speed]))
            else:
                aligned_point.append(0.0)

        return aligned_point


    def check_if_satisfies(self, requirements: pd.DataFrame) -> bool:
        aligned_point = self.normalize_requirement_dataframe(requirements)
        if not aligned_point:
            return False

        point = np.array(aligned_point, dtype=float)

        # Handle 1D case
        if len(self.speeds) == 1:
            return point[0] <= self.max_value + 1e-12

        return np.all(self.A @ point + self.b <= 1e-12).item()


    def obtain_max_value_configuration(self, requirements:pd.DataFrame):
        for col in get_numeric_feature_columns(requirements):
            if col not in self.speeds:
                requirements.drop(col, axis=1, inplace=True)
        aligned_point = self.normalize_requirement_dataframe(requirements)
        if not aligned_point:
            return None

        c_value = np.array([float(x) for x in self.speeds])
        upper_bounds = np.array(aligned_point)  # ejemplo

        # Handle 1D case
        if len(self.speeds) == 1:
            # For 1D, just take the minimum of the requirement and max available
            optimal_value = min(upper_bounds[0], self.max_value)
            result_data = {"code": self.code}
            result_data[self.speeds[0]] = int(round(optimal_value))
            total_value = int(float(self.speeds[0])) * int(round(optimal_value))
            result_data["value"] = total_value
            return pd.DataFrame([result_data])

        A = self.hull.equations[:, :-1]  # todo menos la última columna
        b = -self.hull.equations[:, -1]  # última columna negada
        result = linprog(
            c=-c_value,
            A_ub=A,
            b_ub=b,
            bounds=[(None, u) for u in upper_bounds],  # xᵢ <= uᵢ
            method="highs"
        )
        result_data = {"code": self.code}
        for speed, value in zip(self.speeds, result.x):
            # Round to nearest integer
            result_data[speed] = int(round(value))
        
        # Calculate total value with integer values
        total_value = sum(int(float(speed)) * int(round(result.x[i])) for i, speed in enumerate(self.speeds))
        result_data["value"] = total_value
        
        return pd.DataFrame([result_data])
