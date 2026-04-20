import pandas as pd
import pytest
from app.model.modular import Modular
from app.model.solution import Solution
from tests.test_modular import supply_df

def test_steps(supply_df):
    req = pd.DataFrame([
        {"code": "r", "800": "36", "400": "20", "200":"15"},
    ])
    modular = Modular(supply_df)
    s = Solution(modular, req)
    assert s.steps == [modular.linecards,["800", "400", "200"]]*modular.maxmodules

def test_delete_random_element(supply_df):
    """Test that delete_random_element removes exactly one element and count is reduced by 1"""
    req = pd.DataFrame([
        {"code": "r", "800": "36", "400": "20", "200":"15"},
    ])
    modular = Modular(supply_df)
    s = Solution(modular, req)
    total_before = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    s.neighbor()
    total_after = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    assert total_after == total_before - 1
