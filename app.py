import sys
import asyncio
import traceback
import os

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd
from datetime import datetime

from scrapers import (
    belfius,
    bnp_fortis,
    ing_belgie,
    kbc,
    santander,
    medirect,
    nibc,
    cbc,
    argenta,
    crelan,
    cph,
    vdk,
)

st.set_page_config(
    page_title="Bankrentes Scraper",
    layout="wide"
)

st.title("🏦 Centrale Bankrente Scraper")

RESULTATEN_BESTAND = "laatste_bankrentes.csv"

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
    {"naam": "VDK", "func": vdk.scrape_vdk},
]


def run_scrapers():
    alle_dataframes = []
    logregels = []

    progress = st.progress(0)
    status = st.empty()

    totaal_taken = len(taken)

    for index, taak in enumerate(taken, start=1):
        naam = taak["naam"]
        status.info(f"Bezig met: {naam}...")

        try:
            df = taak["func"]()

            if df is not None and not df.empty:
                df["Bank opgehaald via"] = naam
                alle_dataframes.append(df)

                logregels.append({
                    "Bank": naam,
                    "Status": "OK",
                    "Melding": f"{len(df)} rijen opgehaald",
                    "Details": ""
                })
            else:
                logregels.append({
                    "Bank": naam,
                    "Status": "Geen data",
                    "Melding": "Scraper gaf geen rijen terug",
                    "Details": ""
                })

        except Exception as e:
            logregels.append({
                "Bank": naam,
                "Status": "Fout",
                "Melding": repr(e),
                "Details": traceback.format_exc()
            })

        progress.progress(index / totaal_taken)

    status.success("Scraping voltooid.")

    if alle_dataframes:
        totaal_df = pd.concat(alle_dataframes, ignore_index=True)
    else:
        totaal_df = pd.DataFrame()

    log_df = pd.DataFrame(logregels)

    return totaal_df, log_df


if os.path.exists(RESULTATEN_BESTAND):
    st.subheader("📊 Laatste opgeslagen resultaten")

    opgeslagen_df = pd.read_csv(
        RESULTATEN_BESTAND,
        sep=";",
        encoding="utf-8-sig"
    )

    st.dataframe(opgeslagen_df, use_container_width=True)

    st.info(
        f"Laatst opgeslagen: "
        f"{datetime.fromtimestamp(os.path.getmtime(RESULTATEN_BESTAND)).strftime('%d/%m/%Y %H:%M:%S')}"
    )

    st.markdown("---")


if st.button("🚀 Start alle scrapers"):
    totaal_df, log_df = run_scrapers()

    st.subheader("📋 Logboek")
    st.dataframe(log_df, use_container_width=True)

    fouten_df = log_df[log_df["Status"] == "Fout"]

    if not fouten_df.empty:
        st.subheader("❌ Details van fouten")

        for _, rij in fouten_df.iterrows():
            with st.expander(f"Fout bij {rij['Bank']}"):
                st.code(rij["Details"])

    if not totaal_df.empty:
        totaal_df.to_csv(
            RESULTATEN_BESTAND,
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

        st.subheader("📊 Alle bankrentes")
        st.dataframe(totaal_df, use_container_width=True)

        totaal_df.to_csv(
            "alle_bankrentes_master.csv",
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

        csv_data = totaal_df.to_csv(
            index=False,
            sep=";",
            encoding="utf-8-sig"
        ).encode("utf-8-sig")

        datum = datetime.now().strftime("%Y%m%d_%H%M%S")
        bestandsnaam = f"alle_bankrentes_master_{datum}.csv"

        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=bestandsnaam,
            mime="text/csv"
        )
    else:
        st.warning("Geen data gevonden om op te slaan.")
else:
    st.info("Klik op de knop om de bankrentes op te halen.")