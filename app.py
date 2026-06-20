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

LAATSTE_CSV = "laatste_bankrentes.csv"
LAATSTE_LOG = "laatste_log.csv"
LAATSTE_INFO = "laatste_update.txt"

st.title("🏦 Bankrentes België")

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


def toon_laatste_resultaat():
    st.subheader("📊 Laatste gevonden bankrentes")

    if os.path.exists(LAATSTE_INFO):
        with open(LAATSTE_INFO, "r", encoding="utf-8") as f:
            laatste_update = f.read().strip()
        st.info(f"Laatste update: {laatste_update}")
    else:
        st.warning("Er is nog geen vorige run gevonden.")

    if os.path.exists(LAATSTE_CSV):
        df = pd.read_csv(LAATSTE_CSV, sep=";", encoding="utf-8-sig")
        st.dataframe(df, use_container_width=True)

        csv_data = df.to_csv(
            index=False,
            sep=";",
            encoding="utf-8-sig"
        ).encode("utf-8-sig")

        st.download_button(
            label="⬇️ Download laatste CSV",
            data=csv_data,
            file_name="laatste_bankrentes.csv",
            mime="text/csv"
        )
    else:
        st.info("Nog geen opgeslagen resultaat beschikbaar.")

    if os.path.exists(LAATSTE_LOG):
        with st.expander("📋 Laatste logboek bekijken"):
            log_df = pd.read_csv(LAATSTE_LOG, sep=";", encoding="utf-8-sig")
            st.dataframe(log_df, use_container_width=True)


def controleer_wachtwoord():
    st.sidebar.subheader("🔒 Beheer")

    wachtwoord = st.sidebar.text_input(
        "Wachtwoord",
        type="password"
    )

    juist_wachtwoord = st.secrets.get("APP_PASSWORD", "")

    if wachtwoord and wachtwoord == juist_wachtwoord:
        st.sidebar.success("Ingelogd")
        return True

    if wachtwoord:
        st.sidebar.error("Fout wachtwoord")

    return False


toon_laatste_resultaat()

is_admin = controleer_wachtwoord()

if is_admin:
    st.sidebar.markdown("---")

    if st.sidebar.button("🚀 Scraper nu starten"):
        totaal_df, log_df = run_scrapers()

        datumtijd = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        totaal_df.to_csv(
            LAATSTE_CSV,
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

        log_df.to_csv(
            LAATSTE_LOG,
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

        with open(LAATSTE_INFO, "w", encoding="utf-8") as f:
            f.write(datumtijd)

        st.success(f"Nieuwe gegevens opgeslagen op {datumtijd}")
        st.rerun()