import argparse
import os
import re
import unicodedata
from datetime import date
from decimal import Decimal
from io import BytesIO

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "REPLACE_WITH_VALUE_FROM_MANAGE_PY",
)

import django
django.setup()

import pandas as pd
import requests
from django.db import transaction

from tasting.models import Beer, Tasting, TastingBeer


DB = "beer"
XLSX_URL = (
    "https://cdn.sanity.io/files/iv1p66d7/production/"
    "2fe52dd24a0e9f377efd4cd65e2798d2c1a65d12.xlsx"
)


def normalize(value):
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", value.lower())


ALIASES = {
    "name": ["artikkelnavn", "beername", "name", "navn"],
    "brewery": ["produsent", "bryggeri", "brewery", "brewer"],
    "style": ["varegruppe", "style", "stil", "category", "type"],
    "abv": ["alkoholprosent", "abv", "alcohol", "alcpercent"],
    "description": ["description", "beskrivelse"],
    "url": ["sourceurl", "producturl", "url", "produkturl"],
}


def find_column(columns, aliases):
    normalized = {normalize(column): column for column in columns}
    for alias in aliases:
        if normalize(alias) in normalized:
            return normalized[normalize(alias)]
    return None


def cell_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def make_description(row, description_column):
    parts = []
    if description_column:
        text = cell_text(row[description_column])
        if text:
            parts.append(text)

    for column in ("Produksjonsmetode", "Farge", "Lukt", "Smak", "Aroma"):
        if column in row.index:
            text = cell_text(row[column])
            if text:
                parts.append(f"{column}: {text}")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=date.today().year)
    parser.add_argument("--date", help="Actual tasting date, YYYY-MM-DD")
    parser.add_argument("--sheet", help="Sheet name; defaults to the first sheet")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    response = requests.get(XLSX_URL, timeout=60)
    response.raise_for_status()

    sheet = args.sheet if args.sheet else 0
    frame = pd.read_excel(BytesIO(response.content), sheet_name=sheet)
    frame = frame.dropna(how="all")

    print("Workbook columns:", list(frame.columns))
    print(f"Rows to scan: {len(frame)}")

    columns = {
        key: find_column(frame.columns, aliases)
        for key, aliases in ALIASES.items()
    }

    if not columns["name"] or not columns["brewery"]:
        raise SystemExit(
            "Could not identify the beer-name and/or brewery columns. "
            f"Workbook columns are: {list(frame.columns)}. "
            "Add the exact headers to ALIASES in the script."
        )

    beers = []
    for _, row in frame.iterrows():
        name = cell_text(row[columns["name"]])
        if not name:
            continue

        brewery = cell_text(row[columns["brewery"]])
        style = cell_text(row[columns["style"]]) if columns["style"] else ""
        abv_text = cell_text(row[columns["abv"]]) if columns["abv"] else ""
        abv = (
            Decimal(abv_text.replace("%", "").replace(",", "."))
            if abv_text
            else None
        )
        url = cell_text(row[columns["url"]]) if columns["url"] else ""

        beers.append({
            "name": name,
            "brewery": brewery,
            "style": style,
            "abv": abv,
            "description": make_description(row, columns["description"]),
            "url": url,
        })

    if not beers:
        raise SystemExit("No beer rows with names were found.")

    print("Sample mapped beers:")
    for beer in beers[:5]:
        print(f"  {beer['name']} — {beer['brewery']} ({beer['style']})")

    if args.dry_run:
        print("Dry run: no database changes made.")
        return

    tasting_date = date.fromisoformat(args.date) if args.date else None
    date_field = Tasting._meta.get_field("date")

    if tasting_date is None and not date_field.null:
        raise SystemExit(
            "Your Tasting.date field is required. Supply the actual date with "
            "--date YYYY-MM-DD."
        )

    with transaction.atomic(using=DB):
        tasting = Tasting.objects.using(DB).filter(year=args.year).first()

        if tasting is None:
            tasting = Tasting.objects.using(DB).create(
                name=f"Beer tasting {args.year}",
                year=args.year,
                date=tasting_date,
            )

        added = 0
        for position, item in enumerate(beers, start=1):
            defaults = {
                "style": item["style"],
                "description": item["description"],
                "source_url": item["url"],
            }
            if item["abv"] is not None:
                defaults["abv"] = item["abv"]

            beer, _ = Beer.objects.using(DB).get_or_create(
                name=item["name"],
                brewery=item["brewery"],
                defaults=defaults,
            )

            _, created = TastingBeer.objects.using(DB).get_or_create(
                tasting=tasting,
                beer=beer,
                defaults={"position": position},
            )
            added += int(created)

    print(f"Scanned {len(beers)} beers; added {added} to the {args.year} tasting.")


if __name__ == "__main__":
    main()
