"""Constraint-driven generator for realistic switch port tuples."""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class GenerationRequest:
	profile: str
	role: str
	ports: Dict[int, int]


def load_constraints(path: str | Path) -> dict:
	with Path(path).open("r", encoding="utf-8") as handle:
		return json.load(handle)


def weighted_choice(rng: random.Random, items: List[dict], weight_key: str = "weight") -> dict:
	total = sum(float(item[weight_key]) for item in items)
	if total <= 0:
		raise ValueError("Weights must sum to a positive number.")
	threshold = rng.random() * total
	for item in items:
		threshold -= float(item[weight_key])
		if threshold <= 0:
			return item
	return items[-1]


def sample_step(rng: random.Random, min_value: int, max_value: int, step: int) -> int:
	if step <= 0:
		raise ValueError("Step must be a positive integer.")
	if min_value > max_value:
		raise ValueError("Min value cannot exceed max value.")
	choices = list(range(min_value, max_value + 1, step))
	if not choices:
		raise ValueError("No available choices for the given range and step.")
	return rng.choice(choices)


def align_to_granularity(value: float, granularity: int) -> int:
	if granularity <= 1:
		return int(round(value))
	return int(round(value / granularity) * granularity)


def find_feasible_up_ports(
	min_up: int,
	max_up: int,
	gran: int,
	down_spd: int,
	up_spd: int,
	oversub_min: float,
	max_total: int,
) -> List[int]:
	choices = list(range(min_up, max_up + 1, gran))
	feasible: List[int] = []
	for n_up in choices:
		n_down_min = oversub_min * n_up * up_spd / down_spd
		n_down = align_to_granularity(n_down_min, gran)
		n_down = max(gran, n_down)
		if n_up + n_down <= max_total:
			feasible.append(n_up)
	return feasible


def generate_asymmetric(rng: random.Random, spec: dict, max_attempts: int = 400) -> Dict[int, int]:
	gran = int(spec["port_granularity"])
	max_total = int(spec["max_total_ports"])
	min_up = int(spec["min_up_ports"])
	max_up = int(spec["max_up_ports"])
	oversub_min, oversub_max = spec["oversub_range"]
	for _ in range(max_attempts):
		speed_pair = weighted_choice(rng, spec["speed_pairs"], "weight")
		down_spd = int(speed_pair["down"])
		up_spd = int(speed_pair["up"])
		feasible_up = find_feasible_up_ports(
			min_up,
			max_up,
			gran,
			down_spd,
			up_spd,
			float(oversub_min),
			max_total,
		)
		if not feasible_up:
			continue
		n_up = rng.choice(feasible_up)
		oversub = rng.uniform(float(oversub_min), float(oversub_max))
		n_down_raw = oversub * n_up * up_spd / down_spd
		n_down = align_to_granularity(n_down_raw, gran)
		n_down = max(gran, n_down)
		if n_up + n_down > max_total:
			continue
		if down_spd == up_spd:
			return {down_spd: n_down + n_up}
		return {down_spd: n_down, up_spd: n_up}
	raise RuntimeError("Failed to generate a valid asymmetric tuple within constraints.")

def _feasible_mid_up_pairs(
	min_up: int, max_up: int,
	min_mid: int, max_mid: int,
	gran: int,
	down_spd: int, mid_spd: int, up_spd: int,
	oversub_min: float,
	max_total: int,
) -> List[Tuple[int, int]]:
	"""Return all (n_up, n_mid) pairs where at oversub_min at least gran down ports fit."""
	pairs: List[Tuple[int, int]] = []
	for n_up in range(min_up, max_up + 1, gran):
		for n_mid in range(min_mid, max_mid + 1, gran):
			n_down_min = align_to_granularity(
				oversub_min * (n_up * up_spd + n_mid * mid_spd) / down_spd, gran
			)
			n_down_min = max(gran, n_down_min)
			if n_up + n_mid + n_down_min <= max_total:
				pairs.append((n_up, n_mid))
	return pairs


def generate_multi_speed(rng: random.Random, spec: dict, max_attempts: int = 400) -> Dict[int, int]:
	gran = int(spec["port_granularity"])
	max_total = int(spec["max_total_ports"])
	min_up = int(spec["min_up_ports"])
	max_up = int(spec["max_up_ports"])
	min_mid = int(spec["min_mid_ports"])
	max_mid = int(spec["max_mid_ports"])
	oversub_min, oversub_max = float(spec["oversub_range"][0]), float(spec["oversub_range"][1])

	# Build a list of groups that have at least one feasible (n_up, n_mid) pair,
	# so weighted_choice never lands on a permanently infeasible group.
	feasible_groups: List[dict] = []
	for group in spec["speed_groups"]:
		pairs = _feasible_mid_up_pairs(
			min_up, max_up, min_mid, max_mid, gran,
			int(group["down"]), int(group["mid"]), int(group["up"]),
			oversub_min, max_total,
		)
		if pairs:
			feasible_groups.append({**group, "_pairs": pairs})

	if not feasible_groups:
		raise RuntimeError("No feasible (n_up, n_mid) pair exists for any speed_group in this spec.")

	for _ in range(max_attempts):
		group = weighted_choice(rng, feasible_groups, "weight")
		down_spd = int(group["down"])
		mid_spd  = int(group["mid"])
		up_spd   = int(group["up"])

		n_up, n_mid = rng.choice(group["_pairs"])

		oversub = rng.uniform(oversub_min, oversub_max)
		n_down_raw = oversub * (n_up * up_spd + n_mid * mid_spd) / down_spd
		n_down = align_to_granularity(n_down_raw, gran)
		n_down = max(gran, n_down)

		# oversub_max can push n_down over the limit even though oversub_min passed
		if n_up + n_mid + n_down > max_total:
			continue

		# Merge speeds that happen to be equal to avoid redundant keys
		result: Dict[int, int] = {}
		for spd, cnt in [(down_spd, n_down), (mid_spd, n_mid), (up_spd, n_up)]:
			result[spd] = result.get(spd, 0) + cnt
		return result

	raise RuntimeError("Failed to generate a valid multi_speed tuple within constraints.")


def generate_symmetric(rng: random.Random, spec: dict) -> Dict[int, int]:
	speed_entry = weighted_choice(rng, spec["speeds"], "weight")
	speed = int(speed_entry["speed"])
	gran = int(spec["port_granularity"])
	min_ports = int(speed_entry["min_ports"])
	max_ports = int(speed_entry["max_ports"])
	n_ports = sample_step(rng, min_ports, max_ports, gran)
	return {speed: n_ports}


def generate_ports(rng: random.Random, profile_spec: dict, role: str) -> Dict[int, int]:
	role_spec = profile_spec[role]
	port_type = role_spec["port_type"]
	if port_type == "asymmetric":
		return generate_asymmetric(rng, role_spec)
	if port_type == "symmetric":
		return generate_symmetric(rng, role_spec)
	if port_type == "multi_speed":
		return generate_multi_speed(rng, role_spec)
	raise ValueError(f"Unsupported port_type: {port_type}")


def collect_speeds(constraints: dict) -> List[int]:
	speeds: set[int] = set()
	for profile_spec in constraints["profiles"].values():
		for role_spec in profile_spec.values():
			port_type = role_spec["port_type"]
			if port_type == "asymmetric":
				for pair in role_spec["speed_pairs"]:
					speeds.add(int(pair["down"]))
					speeds.add(int(pair["up"]))
			elif port_type == "multi_speed":
				for group in role_spec["speed_groups"]:
					speeds.add(int(group["down"]))
					speeds.add(int(group["mid"]))
					speeds.add(int(group["up"]))
			else:  # symmetric
				for entry in role_spec["speeds"]:
					speeds.add(int(entry["speed"]))
	return sorted(speeds)


def generate_requests(
	constraints: dict,
	rng: random.Random,
	rows: int,
	rows_per_combo: int | None = None,
) -> List[GenerationRequest]:
	profiles = constraints["profiles"]
	requests: List[GenerationRequest] = []
	if rows_per_combo is not None:
		for profile_name, profile_spec in profiles.items():
			for role in profile_spec.keys():
				for _ in range(rows_per_combo):
					ports = generate_ports(rng, profile_spec, role)
					requests.append(GenerationRequest(profile_name, role, ports))
		return requests
	profile_names = list(profiles.keys())
	for _ in range(rows):
		profile_name = rng.choice(profile_names)
		profile_spec = profiles[profile_name]
		role = rng.choice(list(profile_spec.keys()))
		ports = generate_ports(rng, profile_spec, role)
		requests.append(GenerationRequest(profile_name, role, ports))
	return requests


def write_csv(output_path: str | Path, requests: Iterable[GenerationRequest], speeds: List[int]) -> None:
	output_path = Path(output_path)
	speed_columns = [str(speed) for speed in speeds]
	fieldnames = ["profile", "role", *speed_columns]
	with output_path.open("w", newline="", encoding="utf-8") as handle:
		writer = csv.DictWriter(handle, fieldnames=fieldnames)
		writer.writeheader()
		for request in requests:
			row = {"profile": request.profile, "role": request.role}
			for speed in speeds:
				row[str(speed)] = int(request.ports.get(speed, 0))
			writer.writerow(row)


def generate_csv(
	constraints_path: str | Path,
	output_path: str | Path,
	rows: int,
	seed: int | None = None,
	rows_per_combo: int | None = None,
) -> Tuple[List[GenerationRequest], List[int]]:
	constraints = load_constraints(constraints_path)
	rng = random.Random(seed)
	requests = generate_requests(constraints, rng, rows, rows_per_combo=rows_per_combo)
	speeds = collect_speeds(constraints)
	write_csv(output_path, requests, speeds)
	return requests, speeds