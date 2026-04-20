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

@pytest.fixture
def supply_df2():
    df = pd.DataFrame([
        {"code": "M2x4", "800": None, "cost": None, "type": "modular", "maxmodules": "4", "family":None},
        {"code": "S5", "800": "10", "type": "linecard", "family": "M1", "cost":"1000"},
        {"code": "S3", "800": "10", "type": "linecard", "family": "M1", "cost":"100"},
        {"code": "S4", "800": "4", "type": "linecard", "family": "M1", "cost": "30"},
    ])
    df = df[["code", "800", "cost", "type", "family", "maxmodules"]]
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
