import argparse
from pathlib import Path

from app.node_generator import generate_csv


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Generate realistic switch port tuples from constraints.",
	)
	parser.add_argument(
		"--constraints",
		type=Path,
		default=Path("app/database/constrains.json"),
		help="Path to constraints JSON.",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path("generated_ports.csv"),
		help="Output CSV path.",
	)
	parser.add_argument(
		"--rows",
		type=int,
		default=1000,
		help="Total rows to generate (ignored if --rows-per-combo is set).",
	)
	parser.add_argument(
		"--rows-per-combo",
		type=int,
		default=None,
		help="Rows to generate per profile/role combination.",
	)
	parser.add_argument(
		"--seed",
		type=int,
		default=None,
		help="Optional random seed for reproducibility.",
	)
	return parser


def main() -> None:
	parser = build_parser()
	args = parser.parse_args()
	generate_csv(
		constraints_path=args.constraints,
		output_path=args.output,
		rows=args.rows,
		seed=args.seed,
		rows_per_combo=args.rows_per_combo,
	)
	print(f"Wrote {args.output}")


if __name__ == "__main__":
	main()

