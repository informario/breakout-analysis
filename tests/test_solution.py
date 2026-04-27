import pandas as pd
import pytest
from app.model.modular import Modular
from app.model.solution import Solution
from tests.test_modular import supply_df, supply_df2, supply_df3

def test_steps(supply_df):
    req = pd.DataFrame([
        {"code": "r", "800": "36", "400": "20", "200":"15"},
    ])
    modular = Modular(supply_df)
    s = Solution(modular, req)
    assert s.steps == [modular.linecards]*modular.maxmodules

def test_delete_random_element(supply_df):
    """Test that delete_random_element removes exactly one element and count is reduced by 1"""
    req = pd.DataFrame([
        {"code": "r", "800": "36", "400": "20", "200":"15"},
    ])
    modular = Modular(supply_df)
    s = Solution(modular, req)
    total_before = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    s.delete_random_element()
    total_after = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    assert total_after == total_before - 1


def test_solve_requirement(supply_df):
    """Debe seleccionar linecards hasta satisfacer completamente el requerimiento"""
    modular = Modular(supply_df)
    requirement = pd.DataFrame([
        {"code": "r", "800": "36", "400": "0"},
    ])
    s = Solution(modular, requirement)
    result = s.solve()

    assert len(result) >= 1

    assert "code" in result.columns
    assert "800" in result.columns

    total_800 = result["800"].sum()
    assert total_800 >= 36

def test_solve_requirement_multiple_linecards(supply_df):
    """cuando requerimiento muy alto seleccionar varias linecards"""
    modular = Modular(supply_df)
    requirement = pd.DataFrame([
        {"code": "r", "800": "100", "400":"20"},
    ])
    s = Solution(modular, requirement)
    result = s.solve()
    
    assert len(result) > 1
    print(result)
    total_800 = result["800"].sum()
    assert total_800 >= 100


def test_solve_requirement_exceeds_maxmodules(supply_df):
    """cuando se necesitan mas linecards que maxmodules levanta error"""
    modular = Modular(supply_df)

    requirement = pd.DataFrame([
        {"code": "r", "800": "200"},
    ])
    
    s = Solution(modular, requirement)
    with pytest.raises(ValueError, match="the solution exceeds maxmodules"):
        s.solve()

def test_solve_requirement_not_available(supply_df):
    """cuando la familia no dispone de un tipo de puerto, levanta error"""
    modular = Modular(supply_df)

    requirement = pd.DataFrame([
        {"code": "r", "777": "5"},
    ])
    
    s = Solution(modular, requirement)
    with pytest.raises(ValueError, match="this module does not contain linecards that can solve this requirement"):
        s.solve()

def test_heuristic_h2_chooses_best_value(supply_df):
    """para 2 opciones que cumplen con el requerimiento, devuelve la más barata"""
    modular = Modular(supply_df)
    requirement = pd.DataFrame([
        {"code": "r", "200": "96"},
    ])
    s = Solution(modular, requirement)
    result = s.solve(heuristic="H2")
    assert len(result) >= 1
    assert result["code"].iloc[0] == "S3"

def test_greedy_is_not_always_the_best(supply_df2):
    """S4 individualmente tiene una mejor relación valor/costo, pero usar 1 solo de S3 es en realidad más barato"""
    modular = Modular(supply_df2)
    requirement = pd.DataFrame([
        {"code": "r", "800": "10"},
    ])
    s = Solution(modular, requirement)
    result = s.solve(heuristic="H2")
    assert len(result) >= 1
    assert result["code"].iloc[0] == "S4"


def test_solve_cisco_small_multi_speed_requirement(supply_df3):
    """Resuelve requerimiento con múltiples velocidades usando cisco_small supply"""
    modular = Modular(supply_df3)
    requirement = pd.DataFrame([{
        'code': 'requirement',
        '100': 16,
        '40': 16,
        '25': 64,
        '10': 64,
    }])
    s = Solution(modular, requirement)
    result = s.solve()

    print(result)
    assert len(result) >= 1
    assert result["100"].sum() >= 16
    assert result["40"].sum() >= 16
    assert result["25"].sum() >= 64
    assert result["10"].sum() >= 64


