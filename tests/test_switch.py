import pytest
import pandas as pd
import numpy as np

from app.model.switch import get_vertices_from_dataframe, Switch


@pytest.fixture
def supply_df():
	df = pd.DataFrame([
		{"code": "S1", "800": "36",  "400": None, "100": None},
		{"code": "S1", "800": None, "400": "72",  "100": None},
		{"code": "S1", "800": None, "400": None, "100": "288"},
	])
	df = df[["code", "800", "400", "100"]]
	return df

@pytest.fixture
def supply_2_df():
	df = pd.DataFrame([
		{"code": "S2", "800": "10", "400": "2"},
		{"code": "S2", "800": None, "400": "12"},
	])
	df = df[["code", "800", "400"]]
	return df

@pytest.fixture
def supply_3_df():
	df = pd.DataFrame([
		{"code": "S2", "800": "10",},
	])
	df = df[["code", "800"]]
	return df

@pytest.fixture
def supply_cisco_92304qc_df():
	df = pd.DataFrame([
		{"code": "92304QC", "100": "8", "40": "56", "10": "None"},
		{"code": "92304QC", "100": "8", "40": "40", "10": "64"},
	])
	df = df[["code", "100", "40", "10"]]
	return df

def test_get_vertices_from_dataframe(supply_df):
	vertices, speeds = get_vertices_from_dataframe(supply_df)
	assert speeds == ["800", "400", "100"]
	expected = np.array([[36.0, 0.0, 0.0], [0.0, 72.0, 0.0], [0.0, 0.0, 288.0]])
	assert np.allclose(np.array(vertices, dtype=float), expected)


def test_switch_check_if_satisfies_true(supply_df):
	sw = Switch(supply_df)
	req = pd.DataFrame([
		{"code": "r",  "800": "36",  "400": None, "100": None},
	])
	assert sw.check_if_satisfies(req) is True

def test_switch_check_if_satisfies_false(supply_df):
	sw = Switch(supply_df)
	req = pd.DataFrame([
		{"code": "r",  "800": "100", "400": None, "100": None},
	])
	assert sw.check_if_satisfies(req) is False

def test_requirement_alignment_subset_of_switch(supply_df):
	sw = Switch(supply_df)
	req = pd.DataFrame([
		{"code": "r", "400": "10"},
	])
	req = req[["400","code"]]
	assert sw.check_if_satisfies(req) is True

def test_supply_not_a_simplex(supply_2_df):
	"""Cuando el polítopo no es un mero simplex tengo que asegurarme que
	estén presentes todas las proyecciones a los ejes, sinó quedaran puntos
	faltantes"""
	sw = Switch(supply_2_df)
	req1 = pd.DataFrame([
		{"code": "r", "800": "10", "400": "2"},
	])
	req2 = pd.DataFrame([
		{"code": "r", "800": "10", "400": "0"},
	])
	req3 = pd.DataFrame([
		{"code": "r", "800": "0", "400": "12"},
	])
	assert sw.check_if_satisfies(req1) is True
	assert sw.check_if_satisfies(req2) is True
	assert sw.check_if_satisfies(req3) is True

def test_obtain_max_value_configuration(supply_2_df):
	"""Una linecard está representada por un polítopo de configuraciones.
	Dado que para todas las configuraciones el costo es el mismo, necesito
	maximizar el valor aportado.
	El valor aportado no es simplemente el punto que maximice throughput,
	porque puede que el requerimiento no necsite tantas puertas	del máximo.
	El algoritmo limita el polítopo al hiperrectángulo descrito por el requerimiento,
	y luego obtiene el punto que maximiza valor"""
	sw = Switch(supply_2_df)
	req = pd.DataFrame([
		{"code": "r", "800": "9", "400": "3"},
	])
	result = sw.obtain_max_value_configuration(req)
	expected = pd.DataFrame([
		{"code": "S2", "800": 9, "400": 3, "value": 9 * 800 + 3 * 400}
	])
	pd.testing.assert_frame_equal(result, expected)

def test_obtain_max_value_when_linecard_not_enough(supply_2_df):
	sw = Switch(supply_2_df)
	req = pd.DataFrame([
		{"code": "r", "800": "19", "400": "3"},
	])
	result = sw.obtain_max_value_configuration(req)
	expected = pd.DataFrame([
		{"code": "S2", "800": 10, "400": 2, "value": 10 * 800 + 2 * 400},
	])
	pd.testing.assert_frame_equal(result, expected)

def test_linecard_only_one_dimension(supply_3_df):
	sw = Switch(supply_3_df)
	req = pd.DataFrame([
		{"code": "r", "800": "10"},
	])
	result = sw.obtain_max_value_configuration(req)
	expected = pd.DataFrame([
		{"code": "S2", "800": 10, "value": 10 * 800},
	])
	pd.testing.assert_frame_equal(result, expected)

def test_cisco_92304qc(supply_cisco_92304qc_df):
	sw = Switch(supply_cisco_92304qc_df)
	req = pd.DataFrame([
		{"code": "r", "100": "0", "40": "40", "10": "64"},
	])
	print("hola")
	res = sw.check_if_satisfies(req)
	print(res)
	assert res is True
