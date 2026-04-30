import random
from pathlib import Path

from app.node_generator import collect_speeds, generate_asymmetric, generate_multi_speed, generate_symmetric, load_constraints


CONSTRAINTS_PATH = Path("app/database/constrains.json")
CONSTRAINTS_FREE_PATH = Path("app/database/constrains_free.json")


def test_collect_speeds_includes_expected_values():
	constraints = load_constraints(CONSTRAINTS_PATH)
	speeds = collect_speeds(constraints)
	for expected in (1, 10, 25, 40, 100, 400, 800):
		assert expected in speeds


def test_asymmetric_generation_respects_limits():
	constraints = load_constraints(CONSTRAINTS_PATH)
	spec = constraints["profiles"]["enterprise"]["tor"]
	rng = random.Random(7)
	gran = int(spec["port_granularity"])
	max_total = int(spec["max_total_ports"])
	min_up = int(spec["min_up_ports"])
	max_up = int(spec["max_up_ports"])
	for _ in range(50):
		ports = generate_asymmetric(rng, spec)
		assert len(ports) == 2
		down_spd = min(ports.keys())
		up_spd = max(ports.keys())
		n_down = ports[down_spd]
		n_up = ports[up_spd]
		assert n_up % gran == 0
		assert n_down % gran == 0
		assert min_up <= n_up <= max_up
		assert n_down >= gran
		assert n_up + n_down <= max_total


def test_symmetric_generation_respects_limits():
	constraints = load_constraints(CONSTRAINTS_PATH)
	spec = constraints["profiles"]["enterprise"]["spine"]
	rng = random.Random(13)
	gran = int(spec["port_granularity"])
	for _ in range(20):
		ports = generate_symmetric(rng, spec)
		assert len(ports) == 1
		speed, count = next(iter(ports.items()))
		matching = [entry for entry in spec["speeds"] if int(entry["speed"]) == speed]
		assert matching
		entry = matching[0]
		assert count % gran == 0
		assert int(entry["min_ports"]) <= count <= int(entry["max_ports"])


def test_multi_speed_generation_respects_limits():
	constraints = load_constraints(CONSTRAINTS_FREE_PATH)
	spec = constraints["profiles"]["enterprise"]["tor"]
	rng = random.Random(29)
	gran = int(spec["port_granularity"])
	max_total = int(spec["max_total_ports"])
	min_up = int(spec["min_up_ports"])
	max_up = int(spec["max_up_ports"])
	min_mid = int(spec["min_mid_ports"])
	max_mid = int(spec["max_mid_ports"])
	speed_groups = spec["speed_groups"]
	for _ in range(30):
		ports = generate_multi_speed(rng, spec)
		assert len(ports) == 3
		matching = None
		for group in speed_groups:
			if {int(group["down"]), int(group["mid"]), int(group["up"])} == set(ports.keys()):
				matching = group
				break
		assert matching is not None
		n_down = ports[int(matching["down"])]
		n_mid = ports[int(matching["mid"])]
		n_up = ports[int(matching["up"])]
		assert n_down % gran == 0
		assert n_mid % gran == 0
		assert n_up % gran == 0
		assert min_up <= n_up <= max_up
		assert min_mid <= n_mid <= max_mid
		assert n_down >= gran
		assert n_down + n_mid + n_up <= max_total
