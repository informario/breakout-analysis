from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_LOOKUP_PATH = Path("app/database/price_lookup.csv")
DEFAULT_VENDOR_PATHS = [
    Path("app/database/cisco_oferta.csv"),
    Path("app/database/nokia_oferta.csv"),
    Path("app/database/arista_oferta.csv"),
]


def _load_lookup(lookup_path: Path) -> pd.DataFrame:
    lookup_df = pd.read_csv(lookup_path)
    required_columns = {"code", "cost"}
    missing = required_columns - set(lookup_df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Lookup file is missing columns: {missing_list}")

    if lookup_df["code"].duplicated().any():
        dup_count = int(lookup_df["code"].duplicated().sum())
        print(f"Warning: {dup_count} duplicate code entries in {lookup_path}")
        lookup_df = lookup_df.drop_duplicates(subset=["code"], keep="last")

    return lookup_df[["code", "cost"]]


def _update_vendor_file(vendor_path: Path, lookup_df: pd.DataFrame) -> None:
    vendor_df = pd.read_csv(vendor_path)
    if "code" not in vendor_df.columns:
        raise ValueError(f"Vendor file {vendor_path} is missing 'code' column")

    if "cost" in vendor_df.columns:
        vendor_df = vendor_df.drop(columns=["cost"])

    updated_df = vendor_df.merge(lookup_df, on="code", how="left")
    missing_costs = int(updated_df["cost"].isna().sum())

    updated_df.to_csv(vendor_path, index=False)
    if missing_costs:
        print(f"{vendor_path}: {missing_costs} rows missing cost")
    else:
        print(f"{vendor_path}: costs updated")


def update_vendor_costs(
    lookup_path: Path = DEFAULT_LOOKUP_PATH,
    vendor_paths: list[Path] | None = None,
) -> None:
    if vendor_paths is None:
        vendor_paths = DEFAULT_VENDOR_PATHS

    lookup_df = _load_lookup(lookup_path)
    for vendor_path in vendor_paths:
        _update_vendor_file(vendor_path, lookup_df)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Add cost column to vendor CSVs using a lookup table.",
    )
    parser.add_argument(
        "--lookup",
        type=Path,
        default=DEFAULT_LOOKUP_PATH,
        help="Path to the price lookup CSV.",
    )
    parser.add_argument(
        "--vendors",
        type=Path,
        nargs="*",
        default=DEFAULT_VENDOR_PATHS,
        help="Vendor CSV paths to update.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    update_vendor_costs(lookup_path=args.lookup, vendor_paths=args.vendors)


if __name__ == "__main__":
    main()

