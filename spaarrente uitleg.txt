import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(layout="wide")
st.title("🏦 ING Tempo Sparen: Correcte Simulator")

# Sliders
col1, col2 = st.columns(2)
with col1:
    stort_bedrag = st.slider("Maandelijks stortingsbedrag (€)", 0, 1000, 500, step=25)
    jaren = st.slider("Looptijd (jaren)", 1, 15, 5)
with col2:
    basis_rente_pct = st.slider("Basisrente (%)", 0.0, 5.0, 1.5, step=0.05)
    getrouw_rente_pct = st.slider("Getrouwheidspremie (%)", 0.0, 5.0, 1.5, step=0.05)

def run_simulation():
    stortingen = []
    logboek = []
    saldo = 0
    start_datum = date(2026, 1, 1)
    eind_datum = start_datum + relativedelta(years=jaren)
    
    current_date = start_datum
    while current_date <= eind_datum:
        # 1. Maandelijkse storting
        if current_date.day == 1:
            stortingen.append({'datum': current_date, 'bedrag': float(stort_bedrag)})
            saldo += float(stort_bedrag)
            logboek.append({'Datum': current_date, 'Type': 'Maandelijkse Storting', 'Bedrag': float(stort_bedrag), 'Saldo': float(saldo)})
        
        # 2. Basisrente (Jaarlijks op 01/01, PAS NA 1 JAAR)
        # We checken of het jaar > startjaar is
        if current_date.month == 1 and current_date.day == 1 and current_date.year > start_datum.year:
            # Rente over saldo van het voorgaande jaar
            rente_bedrag = saldo * (basis_rente_pct / 100)
            saldo += rente_bedrag
            logboek.append({'Datum': current_date, 'Type': 'Basisrente', 'Bedrag': float(rente_bedrag), 'Saldo': float(saldo)})
            
        # 3. Getrouwheidspremie (Pas na 12 maanden rijping)
        if current_date.day == 1 and current_date.month in [1, 4, 7, 10]:
            premie_kwartaal = 0
            for s in stortingen:
                if current_date >= (s['datum'] + relativedelta(years=1)):
                    # Check of deze storting in dit kwartaal zijn '12-maanden-verjaardag' heeft
                    if current_date.month == s['datum'].month:
                        premie_kwartaal += (s['bedrag'] * (getrouw_rente_pct / 100))
            
            if premie_kwartaal > 0:
                saldo += premie_kwartaal
                logboek.append({'Datum': current_date, 'Type': 'Getrouwheidspremie', 'Bedrag': float(premie_kwartaal), 'Saldo': float(saldo)})
        
        current_date += relativedelta(months=1)
    return pd.DataFrame(logboek)

if st.button("Start Correcte Simulatie"):
    df = run_simulation()
    
    # Filterlijst
    alle_types = ['Maandelijkse Storting', 'Basisrente', 'Getrouwheidspremie']
    selected_types = st.multiselect("Filter op transactietype:", options=alle_types, default=alle_types)
    df_filtered = df[df['Type'].isin(selected_types)]
    
    st.dataframe(df_filtered.style.format({"Bedrag": "{:.2f} €", "Saldo": "{:.2f} €"}), use_container_width=True)