import pandas as pd
from scrapers import belfius, bnp_fortis, ing_belgie, kbc, santander, medirect, nibc, cbc, argenta, crelan, cph, vdk

def main():
    print("=========================================")
    print("STARTEN CENTRALE BANK SCRAPER")
    print("=========================================\n")

    taken = [
        {"naam": "BNP Paribas Fortis", "func": bnp_fortis.scrape},
        {"naam": "Belfius", "func": belfius.scrape},
        {"naam": "ING België", "func": ing_belgie.scrape_ing_api},
        {"naam": "KBC", "func": kbc.scrape_kbc},
        {"naam": "Santander Consumer Bank", "func": santander.scrape_santander},
        {"naam": "MeDirect", "func": medirect.scrape_medirect_volledig},
        {"naam": "NIBC", "func": nibc.scrape_nibc},
	{"naam": "CBC", "func": cbc.scrape_cbc},
	{"naam": "Argenta", "func": argenta.scrape_argenta},
	{"naam": "Crelan", "func": crelan.scrape_crelan},
	{"naam": "CPH", "func": cph.scrape_cph},
	{"naam": "vdk", "func": vdk.scrape_vdk},
    ]

    alle_dataframes = []

    for taak in taken:
        print(f"Starten met: {taak['naam']}...")
        try:
            df = taak["func"]()
            if df is not None and not df.empty:
                print(f"-> {taak['naam']} succesvol opgehaald.")
                alle_dataframes.append(df)
            else:
                print(f"-> Geen data voor {taak['naam']}.")
        except Exception as e:
            print(f"-> Fout bij {taak['naam']}: {e}")

    # Data samenvoegen
    if alle_dataframes:
        totaal_df = pd.concat(alle_dataframes, ignore_index=True)
        # Sla op in de master file
        totaal_df.to_csv("alle_bankrentes_master.csv", index=False, sep=";", encoding='utf-8-sig')
        print("\n=========================================")
        print("Klaar! Master-bestand opgeslagen: 'alle_bankrentes_master.csv'")
    else:
        print("Geen data gevonden om op te slaan.")

if __name__ == "__main__":
    main()