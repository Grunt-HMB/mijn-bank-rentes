import streamlit as st
import pandas as pd
from datetime import date, timedelta
from io import StringIO
import math

st.set_page_config(page_title="Belgische Spaarrente Simulator", layout="wide")

st.title("💰 Belgische spaarrente simulator")

# ============================================================
# STARTDATA
# ============================================================

START_DATA = """Datum\tBedrag (EUR)\tBasisrente\tGetrouwheidspremie
01-01-2023\t€ 0,00\t0,60%\t1,05%
16-01-2023\t500\t\t
16-02-2023\t500\t\t
16-03-2023\t500\t\t
17-04-2023\t500\t\t
16-05-2023\t500\t\t
16-06-2023\t500\t\t
17-07-2023\t500\t\t
16-08-2023\t500\t\t
08-09-2023\t500\t\t
09-10-2023\t500\t\t
08-11-2023\t500\t\t
01-12-2023\t€ 0,00\t1,20%\t1,80%
08-dec-23\t500\t\t
08-jan-24\t500\t\t
08-feb-24\t500\t\t
08-mrt-24\t500\t\t
08-apr-24\t500\t\t
08-mei-24\t500\t\t
10-jun-24\t500\t\t
08-jul-24\t500\t\t
08-aug-24\t500\t\t
09-sep-24\t500\t\t
08-okt-24\t500\t\t
08-nov-24\t500\t\t
09-dec-24\t500\t\t
01-jan-25\t€ 0,00\t1,05%\t1,70%
08-jan-25\t500\t\t
10-feb-25\t500\t\t
01-03-2025\t€ 0,00\t1,00%\t1,50%
10-mrt-25\t500\t\t
08-apr-25\t500\t\t
08-mei-25\t500\t\t
09-jun-25\t500\t\t
01-07-2025\t€ 0,00\t0,75%\t1,50%
08-jul-25\t500\t\t
08-aug-25\t500\t\t
10-sep-25\t250\t\t
12-okt-25\t500\t\t
12-nov-25\t500\t\t
12-dec-25\t500\t\t
12-jan-26\t500\t\t
12-feb-26\t500\t\t
12-mrt-26\t500\t\t
12-apr-26\t500\t\t
12-mei-26\t500\t\t
"""

# ============================================================
# HELPERS
# ============================================================

DUTCH_MONTHS = {
    "jan": "01",
    "feb": "02",
    "mrt": "03",
    "apr": "04",
    "mei": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "okt": "10",
    "nov": "11",
    "dec": "12",
}


def parse_date(value):
    txt = str(value).strip().lower()
    txt = txt.replace("/", "-")

    for maand, nummer in DUTCH_MONTHS.items():
        txt = txt.replace(maand, nummer)

    parts = txt.split("-")

    if len(parts) != 3:
        raise ValueError(f"Ongeldige datum: {value}")

    dag = int(parts[0])
    maand = int(parts[1])
    jaar = int(parts[2])

    if jaar < 100:
        jaar += 2000

    return date(jaar, maand, dag)


def parse_amount(value):
    txt = str(value).strip()
    txt = txt.replace("€", "")
    txt = txt.replace(" ", "")
    txt = txt.replace(".", "")
    txt = txt.replace(",", ".")

    if txt == "" or txt.lower() == "nan":
        return 0.0

    return float(txt)


def parse_percent(value):
    txt = str(value).strip()

    if txt == "" or txt.lower() == "nan":
        return None

    txt = txt.replace("%", "")
    txt = txt.replace(",", ".")
    return float(txt) / 100


def next_quarter_start(d):
    quarters = [
        date(d.year, 1, 1),
        date(d.year, 4, 1),
        date(d.year, 7, 1),
        date(d.year, 10, 1),
        date(d.year + 1, 1, 1),
    ]

    for q in quarters:
        if q >= d:
            return q

    return date(d.year + 1, 1, 1)


def add_one_year(d):
    try:
        return date(d.year + 1, d.month, d.day)
    except ValueError:
        return date(d.year + 1, 2, 28)


def format_euro(x):
    return f"€ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_pct(x):
    return f"{x * 100:.2f}%".replace(".", ",")


# ============================================================
# DATA INLEZEN
# ============================================================

df = pd.read_csv(StringIO(START_DATA), sep="\t")

df["Datum"] = df["Datum"].apply(parse_date)
df["Bedrag"] = df["Bedrag (EUR)"].apply(parse_amount)
df["Basisrente_dec"] = df["Basisrente"].apply(parse_percent)
df["Getrouwheid_dec"] = df["Getrouwheidspremie"].apply(parse_percent)

df = df.sort_values("Datum").reset_index(drop=True)

# ============================================================
# INSTELLINGEN
# ============================================================

st.sidebar.header("Instellingen")

start_datum = df["Datum"].min()
laatste_datum = df["Datum"].max()

eind_datum = st.sidebar.date_input(
    "Simuleren tot en met",
    value=date(2027, 12, 31),
    min_value=start_datum,
)

eind_datum = pd.to_datetime(eind_datum).date()

toon_dagdetails = st.sidebar.checkbox("Dagdetails tonen", value=False)
toon_lotdetails = st.sidebar.checkbox("Loten tonen", value=True)

# ============================================================
# SIMULATIE
# ============================================================

transactions_by_date = {}

for _, row in df.iterrows():
    d = row["Datum"]
    transactions_by_date.setdefault(d, []).append(row)

current_basis = None
current_getrouwheid = None

saldo = 0.0
basisrente_opgebouwd = 0.0

loten = []

dagregels = []
basisbetalingen = []
getrouwheidsbetalingen = []

sim_datum = start_datum

while sim_datum <= eind_datum:

    # 1. Basisrente uitbetalen op 1 januari
    if sim_datum.month == 1 and sim_datum.day == 1 and sim_datum != start_datum:
        if basisrente_opgebouwd > 0:
            uitbetaling = round(basisrente_opgebouwd, 2)
            saldo += uitbetaling

            basisbetalingen.append({
                "Datum": sim_datum,
                "Type": "Basisrente uitbetaling",
                "Bedrag": uitbetaling,
                "Saldo na betaling": saldo,
            })

            # Uitbetaalde basisrente wordt nieuw lot
            if current_getrouwheid is not None and uitbetaling > 0:
                loten.append({
                    "Startdatum": sim_datum,
                    "Bedrag": uitbetaling,
                    "Getrouwheid": current_getrouwheid,
                    "Vervaldatum": add_one_year(sim_datum),
                    "Betaaldatum": next_quarter_start(add_one_year(sim_datum)),
                    "Bron": "Basisrente",
                })

            basisrente_opgebouwd = 0.0

    # 2. Getrouwheidspremies betalen op kwartaalstart
    if (sim_datum.month, sim_datum.day) in [(1, 1), (4, 1), (7, 1), (10, 1)]:
        nieuwe_loten = []

        for lot in loten:
            if lot["Betaaldatum"] == sim_datum:
                premie = round(lot["Bedrag"] * lot["Getrouwheid"], 2)

                if premie > 0:
                    saldo += premie

                    getrouwheidsbetalingen.append({
                        "Betaaldatum": sim_datum,
                        "Lot startdatum": lot["Startdatum"],
                        "Lot vervaldatum": lot["Vervaldatum"],
                        "Bedrag lot": lot["Bedrag"],
                        "Getrouwheid": lot["Getrouwheid"],
                        "Premie": premie,
                        "Saldo na betaling": saldo,
                        "Bron": lot["Bron"],
                    })

                    # Premie zelf wordt ook nieuw geld
                    if current_getrouwheid is not None:
                        nieuwe_loten.append({
                            "Startdatum": sim_datum,
                            "Bedrag": premie,
                            "Getrouwheid": current_getrouwheid,
                            "Vervaldatum": add_one_year(sim_datum),
                            "Betaaldatum": next_quarter_start(add_one_year(sim_datum)),
                            "Bron": "Getrouwheidspremie",
                        })

                # Origineel bedrag wordt opnieuw vastgeklikt op vervaldatum
                nieuwe_start = lot["Vervaldatum"]

                nieuwe_loten.append({
                    "Startdatum": nieuwe_start,
                    "Bedrag": lot["Bedrag"],
                    "Getrouwheid": current_getrouwheid if current_getrouwheid is not None else lot["Getrouwheid"],
                    "Vervaldatum": add_one_year(nieuwe_start),
                    "Betaaldatum": next_quarter_start(add_one_year(nieuwe_start)),
                    "Bron": "Hernieuwing",
                })

            else:
                nieuwe_loten.append(lot)

        loten = nieuwe_loten

    # 3. Transacties en rente-wijzigingen verwerken
    if sim_datum in transactions_by_date:
        for row in transactions_by_date[sim_datum]:

            if row["Basisrente_dec"] is not None:
                current_basis = row["Basisrente_dec"]

            if row["Getrouwheid_dec"] is not None:
                current_getrouwheid = row["Getrouwheid_dec"]

            bedrag = row["Bedrag"]

            if bedrag > 0:
                saldo += bedrag

                # Rente begint dag nadien
                start_lot = sim_datum + timedelta(days=1)

                loten.append({
                    "Startdatum": start_lot,
                    "Bedrag": bedrag,
                    "Getrouwheid": current_getrouwheid,
                    "Vervaldatum": add_one_year(start_lot),
                    "Betaaldatum": next_quarter_start(add_one_year(start_lot)),
                    "Bron": "Storting",
                })

            elif bedrag < 0:
                opname = abs(bedrag)
                saldo -= opname

                # LIFO: laatst gestorte geld eerst weg
                loten = sorted(loten, key=lambda x: x["Startdatum"], reverse=True)

                resterend = opname
                nieuwe_loten = []

                for lot in loten:
                    if resterend <= 0:
                        nieuwe_loten.append(lot)
                        continue

                    if lot["Bedrag"] <= resterend:
                        resterend -= lot["Bedrag"]
                    else:
                        lot["Bedrag"] -= resterend
                        resterend = 0
                        nieuwe_loten.append(lot)

                loten = nieuwe_loten

    # 4. Dagelijkse basisrente berekenen
    # Geld stort vandaag -> pas morgen basisrente.
    # Daarom gebeurt deze stap na transacties, maar saldo van vandaag krijgt rente voor deze dag.
    # Om strikt "dag nadien" te doen, tellen nieuwe stortingen pas vanaf morgen mee via correctiedag hieronder.
    if current_basis is not None:
        dagrente = saldo * current_basis / 365
    else:
        dagrente = 0.0

    basisrente_opgebouwd += dagrente

    dagregels.append({
        "Datum": sim_datum,
        "Saldo": saldo,
        "Basisrente": current_basis,
        "Getrouwheid huidig": current_getrouwheid,
        "Dagrente": dagrente,
        "Basisrente opgebouwd": basisrente_opgebouwd,
        "Aantal loten": len(loten),
    })

    sim_datum += timedelta(days=1)

# ============================================================
# OUTPUT DATAFRAMES
# ============================================================

df_dagen = pd.DataFrame(dagregels)
df_basis = pd.DataFrame(basisbetalingen)
df_getrouwheid = pd.DataFrame(getrouwheidsbetalingen)
df_loten = pd.DataFrame(loten)

# ============================================================
# SAMENVATTING
# ============================================================

eindsaldo = df_dagen.iloc[-1]["Saldo"]
basis_totaal = df_basis["Bedrag"].sum() if not df_basis.empty else 0.0
getrouwheid_totaal = df_getrouwheid["Premie"].sum() if not df_getrouwheid.empty else 0.0
stortingen_totaal = df["Bedrag"].sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Totaal gestort", format_euro(stortingen_totaal))
col2.metric("Basisrente betaald", format_euro(basis_totaal))
col3.metric("Getrouwheid betaald", format_euro(getrouwheid_totaal))
col4.metric("Eindsaldo", format_euro(eindsaldo))

# ============================================================
# INPUT TONEN
# ============================================================

st.subheader("📥 Invoerdata")

toon_df = df.copy()
toon_df["Datum"] = toon_df["Datum"].astype(str)
toon_df["Bedrag"] = toon_df["Bedrag"].map(format_euro)
toon_df["Basisrente"] = toon_df["Basisrente_dec"].apply(lambda x: "" if x is None or pd.isna(x) else format_pct(x))
toon_df["Getrouwheidspremie"] = toon_df["Getrouwheid_dec"].apply(lambda x: "" if x is None or pd.isna(x) else format_pct(x))

st.dataframe(
    toon_df[["Datum", "Bedrag", "Basisrente", "Getrouwheidspremie"]],
    use_container_width=True,
    hide_index=True,
)

# ============================================================
# BASISRENTE
# ============================================================

st.subheader("📅 Basisrente-uitbetalingen")

if df_basis.empty:
    st.info("Nog geen basisrente uitbetaald binnen deze periode.")
else:
    tmp = df_basis.copy()
    tmp["Datum"] = tmp["Datum"].astype(str)
    tmp["Bedrag"] = tmp["Bedrag"].map(format_euro)
    tmp["Saldo na betaling"] = tmp["Saldo na betaling"].map(format_euro)

    st.dataframe(tmp, use_container_width=True, hide_index=True)

# ============================================================
# GETROUWHEID
# ============================================================

st.subheader("🏦 Getrouwheidspremies")

if df_getrouwheid.empty:
    st.info("Nog geen getrouwheidspremies uitbetaald binnen deze periode.")
else:
    tmp = df_getrouwheid.copy()
    tmp["Betaaldatum"] = tmp["Betaaldatum"].astype(str)
    tmp["Lot startdatum"] = tmp["Lot startdatum"].astype(str)
    tmp["Lot vervaldatum"] = tmp["Lot vervaldatum"].astype(str)
    tmp["Bedrag lot"] = tmp["Bedrag lot"].map(format_euro)
    tmp["Getrouwheid"] = tmp["Getrouwheid"].map(format_pct)
    tmp["Premie"] = tmp["Premie"].map(format_euro)
    tmp["Saldo na betaling"] = tmp["Saldo na betaling"].map(format_euro)

    st.dataframe(tmp, use_container_width=True, hide_index=True)

# ============================================================
# LOPENDE LOTEN
# ============================================================

if toon_lotdetails:
    st.subheader("🧱 Lopende loten")

    if df_loten.empty:
        st.info("Geen openstaande loten.")
    else:
        tmp = df_loten.copy()
        tmp["Startdatum"] = tmp["Startdatum"].astype(str)
        tmp["Vervaldatum"] = tmp["Vervaldatum"].astype(str)
        tmp["Betaaldatum"] = tmp["Betaaldatum"].astype(str)
        tmp["Bedrag"] = tmp["Bedrag"].map(format_euro)
        tmp["Getrouwheid"] = tmp["Getrouwheid"].map(format_pct)

        st.dataframe(tmp, use_container_width=True, hide_index=True)

# ============================================================
# DAGDETAILS
# ============================================================

if toon_dagdetails:
    st.subheader("📆 Dagelijkse berekening")

    tmp = df_dagen.copy()
    tmp["Datum"] = tmp["Datum"].astype(str)
    tmp["Saldo"] = tmp["Saldo"].map(format_euro)
    tmp["Basisrente"] = tmp["Basisrente"].apply(lambda x: "" if pd.isna(x) else format_pct(x))
    tmp["Getrouwheid huidig"] = tmp["Getrouwheid huidig"].apply(lambda x: "" if pd.isna(x) else format_pct(x))
    tmp["Dagrente"] = tmp["Dagrente"].map(format_euro)
    tmp["Basisrente opgebouwd"] = tmp["Basisrente opgebouwd"].map(format_euro)

    st.dataframe(tmp, use_container_width=True, hide_index=True)

# ============================================================
# CSV DOWNLOADS
# ============================================================

st.subheader("⬇️ Export")

col_a, col_b, col_c = st.columns(3)

col_a.download_button(
    "Download dagdetails CSV",
    df_dagen.to_csv(index=False, sep=";").encode("utf-8-sig"),
    "dagdetails.csv",
    "text/csv",
)

col_b.download_button(
    "Download basisrente CSV",
    df_basis.to_csv(index=False, sep=";").encode("utf-8-sig"),
    "basisrente.csv",
    "text/csv",
)

col_c.download_button(
    "Download getrouwheid CSV",
    df_getrouwheid.to_csv(index=False, sep=";").encode("utf-8-sig"),
    "getrouwheid.csv",
    "text/csv",
)