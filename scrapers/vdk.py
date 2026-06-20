import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

URL = "https://www.vdk.be/nl/particulieren/sparen-en-beleggen/snel-naar/gereglementeerde-spaarrekeningen-gecommercialiseerd-door"


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clean_percentage(value):
    value = clean_text(value)
    value = value.replace(" op jaarbasis", "")
    return value.strip()


def scrape_vdk():
    print("VDK spaarrentes ophalen...")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n")

    pattern = re.compile(
        r"(Ritme Spaarrekening|You Count Spaarrekening|SpaarPlus Rekening|Rentespaarrekening)\s+"
        r"Categorie\s+"
        r"Basisrente\s+"
        r"Getrouwheidspremie\s+"
        r"Optelling van basisrente\s+en getrouwheidspremie\s+"
        r"Toepasselijke\s+voorwaarden\s+"
        r"([A-Z])\s+"
        r"([\d,]+%\s+op jaarbasis)\s+"
        r"([\d,]+%\s+op jaarbasis)\s+"
        r"([\d,]+%\s+op jaarbasis)",
        re.IGNORECASE
    )

    resultaten = []

    for match in pattern.finditer(text):
        spaarrekening = clean_text(match.group(1))
        basisrente = clean_percentage(match.group(3))
        getrouwheidspremie = clean_percentage(match.group(4))
        totale_rente = clean_percentage(match.group(5))

        resultaten.append({
            "Bank": "VDK Bank",
            "Spaarrekening": spaarrekening,
            "Basisrente": basisrente,
            "Getrouwheidspremie": getrouwheidspremie,
            "Totale Rente": totale_rente,
        })

    df = pd.DataFrame(resultaten)

    if df.empty:
        raise ValueError("Geen VDK spaarrentes gevonden.")

    return df


def scrape():
    return scrape_vdk()


if __name__ == "__main__":
    df = scrape_vdk()
    print(df.to_string(index=False))
    df.to_csv("vdk_rentes.csv", index=False, sep=";", encoding="utf-8-sig")
    print("Opgeslagen als vdk_rentes.csv")