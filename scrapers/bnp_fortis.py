# scrapers/bnp_fortis.py
import re
import pandas as pd
import requests


def scrape():
    print("BNP Paribas Fortis live downloaden...")
    url = "https://www.bnpparibasfortis.be/nl/public/particulieren/sparen-en-beleggen/spaarrekening-vergelijken"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Fout bij BNP: Statuscode {response.status_code}")
            return None

        html_text = response.text
        basisrentes = re.findall(r"([0-9.,]+)%\s*basisrente", html_text)
        premies = re.findall(r"([0-9.,]+)%\s*getrouwheidspremie", html_text)

        rekeningen = [
            "Spaarrekening Boost (Cat. B)",
            "Spaarrekening Plus (Cat. B)",
            "Spaarrekening (Cat. A)",
        ]

        if len(basisrentes) >= 3 and len(premies) >= 3:
            data = []
            for i in range(3):
                b_rente = basisrentes[i]
                g_premie = premies[i]

                totaal = float(b_rente.replace(",", ".")) + float(
                    g_premie.replace(",", ".")
                )
                totaal_str = f"{totaal:.2f}%".replace(".", ",")

                data.append(
                    {
                        "Bank": "BNP Paribas Fortis",  # Handig voor het centrale overzicht straks!
                        "Spaarrekening": rekeningen[i],
                        "Basisrente": f"{b_rente}%",
                        "Getrouwheidspremie": f"{g_premie}%",
                        "Totale Rente": totaal_str,
                    }
                )

            # Geef het DataFrame terug aan het hoofdprogramma
            return pd.DataFrame(data)

        else:
            print("BNP data structuur kon niet worden gelezen via RegEx.")
            return None

    except Exception as e:
        print(f"Fout in BNP module: {e}")
        return None