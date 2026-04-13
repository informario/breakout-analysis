import pytest
import pandas as pd
from app.model.modular import Modular

@pytest.fixture
def supply_df():
    df = pd.DataFrame([
        {"code": "M1x4", "800": None, "400": None, "100": None, "1000": None, "500": None, "200": None, "cost": None, "type": "modular", "family": None, "maxmodules": "4"},
        {"code": "S1", "800": "36", "400": None, "100": None, "cost": 10, "type": "linecard", "family": "M1", "maxmodules": None},
        {"code": "S1", "800": None, "400": "72", "100": None, "cost": 10, "type": "linecard", "family": "M1", "maxmodules": None},
        {"code": "S1", "800": None, "400": None, "100": "288", "cost": 10, "type": "linecard", "family": "M1", "maxmodules": None},
        {"code": "S2", "1000": "24", "500": None, "200": None, "cost": 15, "type": "linecard", "family": "M1", "maxmodules": None},
        {"code": "S2", "1000": None, "500": "48", "200": None, "cost": 15, "type": "linecard", "family": "M1", "maxmodules": None},
        {"code": "S2", "1000": None, "500": None, "200": "192", "cost": 15, "type": "linecard", "family": "M1", "maxmodules": None},
        {"code": "S3", "1000": "16", "500": None, "200": None, "cost": 10, "type": "linecard", "family": "M1", "maxmodules": None},
        {"code": "S3", "1000": None, "500": "24", "200": None, "cost": 10, "type": "linecard", "family": "M1", "maxmodules": None},
        {"code": "S3", "1000": None, "500": None, "200": "96", "cost": 10, "type": "linecard", "family": "M1", "maxmodules": None},
    ])
    df = df[["code", "1000", "800", "500", "400", "200", "100",  "cost", "type", "family", "maxmodules"]] #ensures order
    return df

def test_modular_init(supply_df):
    modular = Modular(supply_df)
    assert modular.name == "M1x4"
    assert modular.family is None
    assert len(modular.linecards) == 3
    assert modular.linecards[0].code == "S1"
    assert modular.linecards[1].code == "S2"
    
    
def test_linecard_init(supply_df):
    modular = Modular(supply_df)
    s1_linecard = modular.linecards[0]
    assert s1_linecard.code == "S1"
    assert s1_linecard.speeds == ["800", "400", "100"]
    
    s2_linecard = modular.linecards[1]
    assert s2_linecard.code == "S2"
    assert s2_linecard.speeds == ["1000", "500", "200"]

def test_best_fitting_linecard_is_selected(supply_df):
    modular = Modular(supply_df)
    requirement = pd.DataFrame([
        {"code":"r", "800": "36",},
    ])
    best_linecard, result = modular.get_best_linecard(requirement)
    assert best_linecard.code == "S1"
    assert result is not None
    assert "value" in result.columns


def test_solve_requirement(supply_df):
    """Debe seleccionar linecards hasta satisfacer completamente el requerimiento"""
    modular = Modular(supply_df)
    requirement = pd.DataFrame([
        {"code": "r", "800": "36", "400": "0"},
    ])
    result = modular.solve_requirement(requirement)
    
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
    result = modular.solve_requirement(requirement)
    
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
    
    with pytest.raises(ValueError, match="the solution exceeds maxmodules"):
        modular.solve_requirement(requirement)

def test_solve_requirement_not_available(supply_df):
    """cuando la familia no dispone de un tipo de puerto, levanta error"""
    modular = Modular(supply_df)

    requirement = pd.DataFrame([
        {"code": "r", "777": "5"},
    ])
    
    with pytest.raises(ValueError, match="this module does not contain linecards that can solve this requirement"):
        modular.solve_requirement(requirement)

def test_heuristic_h2_chooses_best_value(supply_df):
    """para 2 opciones que cumplen con el requerimiento, devuelve la más barata"""
    modular = Modular(supply_df)
    requirement = pd.DataFrame([
        {"code": "r", "200": "96"},
    ])
    result = modular.solve_requirement(requirement, heuristic="H2")
    assert len(result) >= 1
    assert result["code"].iloc[0] == "S3"