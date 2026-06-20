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

LAATSTE_CSV = "laatste_bankrentes.csv"
LAATSTE_LOG = "laatste_log.csv"
LAATSTE_TIJD = "laatste_tijd.txt"

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
    if os.path.exists(LAATSTE_TIJD):
        with open(LAATSTE_TIJD, "r", encoding="utf-8") as f:
            laatste_tijd = f.read().strip()

        st.info(f"Laatste run: {laatste_tijd}")
    else:
        st.info("Nog geen vorige run gevonden.")

    if os.path.exists(LAATSTE_CSV):
        st.subheader("📊 Laatste opgeslagen bankrentes")

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
        st.info("Nog geen opgeslagen bankrentes beschikbaar.")

    if os.path.exists(LAATSTE_LOG):
        with st.expander("📋 Laatste logboek bekijken"):
            log_df = pd.read_csv(LAATSTE_LOG, sep=";", encoding="utf-8-sig")
            st.dataframe(log_df, use_container_width=True)


def wachtwoord_ok():
    st.sidebar.subheader("🔒 Beheer")

    wachtwoord = st.sidebar.text_input(
        "Wachtwoord om scraper te starten",
        type="password"
    )

    juist_wachtwoord = st.secrets.get("APP_PASSWORD", "")

    if wachtwoord == "":
        return False

    if juist_wachtwoord == "":
        st.sidebar.error("APP_PASSWORD ontbreekt in Streamlit Secrets.")
        return False

    if wachtwoord == juist_wachtwoord:
        st.sidebar.success("Toegang OK")
        return True

    st.sidebar.error("Fout wachtwoord")
    return False


toon_laatste_resultaat()

if wachtwoord_ok():
    if st.sidebar.button("🚀 Start alle scrapers"):
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

        with open(LAATSTE_TIJD, "w", encoding="utf-8") as f:
            f.write(datumtijd)

        st.subheader("📋 Logboek")
        st.dataframe(log_df, use_container_width=True)

        fouten_df = log_df[log_df["Status"] == "Fout"]

        if not fouten_df.empty:
            st.subheader("❌ Details van fouten")

            for _, rij in fouten_df.iterrows():
                with st.expander(f"Fout bij {rij['Bank']}"):
                    st.code(rij["Details"])

        if not totaal_df.empty:
            st.subheader("📊 Nieuwe bankrentes")
            st.dataframe(totaal_df, use_container_width=True)

            csv_data = totaal_df.to_csv(
                index=False,
                sep=";",
                encoding="utf-8-sig"
            ).encode("utf-8-sig")

            datum = datetime.now().strftime("%Y%m%d_%H%M%S")
            bestandsnaam = f"alle_bankrentes_master_{datum}.csv"

            st.download_button(
                label="⬇️ Download nieuwe CSV",
                data=csv_data,
                file_name=bestandsnaam,
                mime="text/csv"
            )

        st.success(f"Nieuwe gegevens opgeslagen op {datumtijd}")
else:
    st.sidebar.info("Alleen met wachtwoord kan je de scraper starten.")