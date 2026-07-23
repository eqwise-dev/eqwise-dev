#!/usr/bin/env python3
"""Fooienteller - houd bij hoeveel fooien er in een restaurant worden gegeven."""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DATA_FILE = Path(__file__).parent / "fooien_data.json"


def datum_type(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"ongeldige datum '{value}', gebruik YYYY-MM-DD")
    return value


def load_data(path: Path) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(path: Path, records: list) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def next_id(records: list) -> int:
    return max((r["id"] for r in records), default=0) + 1


def cmd_add(args, path):
    if args.bedrag <= 0:
        print("Bedrag moet groter dan 0 zijn.", file=sys.stderr)
        sys.exit(1)

    records = load_data(path)
    now = datetime.now()
    record = {
        "id": next_id(records),
        "bedrag": round(args.bedrag, 2),
        "medewerker": args.medewerker,
        "tafel": args.tafel,
        "notitie": args.notitie,
        "datum": args.datum or now.strftime("%Y-%m-%d"),
        "tijd": now.strftime("%H:%M:%S"),
    }
    records.append(record)
    save_data(path, records)

    extra = f" voor {record['medewerker']}" if record["medewerker"] else ""
    print(f"Fooi toegevoegd (#{record['id']}): €{record['bedrag']:.2f}{extra} op {record['datum']}")


def cmd_verwijder(args, path):
    records = load_data(path)
    remaining = [r for r in records if r["id"] != args.id]
    if len(remaining) == len(records):
        print(f"Geen fooi gevonden met id {args.id}", file=sys.stderr)
        sys.exit(1)
    save_data(path, remaining)
    print(f"Fooi #{args.id} verwijderd")


def filter_records(records: list, datum: str = None, medewerker: str = None) -> list:
    result = records
    if datum:
        result = [r for r in result if r["datum"] == datum]
    if medewerker:
        result = [r for r in result if (r.get("medewerker") or "").lower() == medewerker.lower()]
    return result


def cmd_lijst(args, path):
    records = filter_records(load_data(path), args.datum, args.medewerker)
    if not records:
        print("Geen fooien gevonden.")
        return

    for r in sorted(records, key=lambda r: (r["datum"], r["tijd"])):
        extra = []
        if r.get("medewerker"):
            extra.append(r["medewerker"])
        if r.get("tafel"):
            extra.append(f"tafel {r['tafel']}")
        if r.get("notitie"):
            extra.append(r["notitie"])
        extra_str = f" ({', '.join(extra)})" if extra else ""
        print(f"#{r['id']:<4} {r['datum']} {r['tijd']}  €{r['bedrag']:.2f}{extra_str}")


def cmd_totaal(args, path):
    records = filter_records(load_data(path), args.datum, args.medewerker)
    if not records:
        print("Geen fooien gevonden.")
        return

    totaal = sum(r["bedrag"] for r in records)
    print(f"Totaal: €{totaal:.2f} over {len(records)} fooi(en), gemiddeld €{totaal / len(records):.2f}")

    if args.per_dag:
        per_dag = {}
        for r in records:
            per_dag[r["datum"]] = per_dag.get(r["datum"], 0.0) + r["bedrag"]
        print("\nPer dag:")
        for d in sorted(per_dag):
            print(f"  {d}: €{per_dag[d]:.2f}")

    if args.per_medewerker:
        per_medewerker = {}
        for r in records:
            naam = r.get("medewerker") or "(onbekend)"
            per_medewerker[naam] = per_medewerker.get(naam, 0.0) + r["bedrag"]
        print("\nPer medewerker:")
        for naam in sorted(per_medewerker, key=lambda n: -per_medewerker[n]):
            print(f"  {naam}: €{per_medewerker[naam]:.2f}")


def parse_args():
    parser = argparse.ArgumentParser(description="Houd fooien in een restaurant bij.")
    parser.add_argument(
        "--bestand", type=Path, default=DEFAULT_DATA_FILE,
        help=f"Pad naar het databestand (standaard: {DEFAULT_DATA_FILE.name})",
    )
    sub = parser.add_subparsers(dest="commando", required=True)

    p_add = sub.add_parser("add", help="Voeg een fooi toe")
    p_add.add_argument("bedrag", type=float, help="Bedrag van de fooi in euro's")
    p_add.add_argument("--medewerker", help="Naam van de medewerker die de fooi ontving")
    p_add.add_argument("--tafel", help="Tafelnummer")
    p_add.add_argument("--notitie", help="Extra notitie")
    p_add.add_argument("--datum", type=datum_type, help="Datum (YYYY-MM-DD), standaard vandaag")
    p_add.set_defaults(func=cmd_add)

    p_verwijder = sub.add_parser("verwijder", help="Verwijder een fooi op id")
    p_verwijder.add_argument("id", type=int)
    p_verwijder.set_defaults(func=cmd_verwijder)

    p_lijst = sub.add_parser("lijst", help="Toon alle fooien")
    p_lijst.add_argument("--datum", type=datum_type, help="Filter op datum (YYYY-MM-DD)")
    p_lijst.add_argument("--medewerker", help="Filter op medewerker")
    p_lijst.set_defaults(func=cmd_lijst)

    p_totaal = sub.add_parser("totaal", help="Toon totalen")
    p_totaal.add_argument("--datum", type=datum_type, help="Filter op datum (YYYY-MM-DD)")
    p_totaal.add_argument("--medewerker", help="Filter op medewerker")
    p_totaal.add_argument("--per-dag", action="store_true", help="Toon uitsplitsing per dag")
    p_totaal.add_argument("--per-medewerker", action="store_true", help="Toon uitsplitsing per medewerker")
    p_totaal.set_defaults(func=cmd_totaal)

    return parser.parse_args()


def main():
    args = parse_args()
    args.func(args, args.bestand)


if __name__ == "__main__":
    main()
