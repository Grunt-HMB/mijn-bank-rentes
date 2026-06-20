import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🏦 ING Spaar-Simulator: Belgisch Bankmodel")

# --- Sliders ---
col1, col2 = st.columns(2)
with col1:
    inleg = st.slider("Maandelijkse inleg (€)", 0, 2000, 500, 50)
    basis_rate = st.slider("Basisrente (%)", 0.0, 5.0, 1.2, 0.01) / 100
with col2:
    jaren = st.slider("Aantal jaren", 1, 5, 1)
    premie_rate = st.slider("Getrouwheidspremie (%)", 0.0, 5.0, 0.5, 0.01) / 100

# --- Berekening volgens jouw specificatie ---
start_datum = datetime(2023, 1, 1)
data = []
saldo = 0
transacties = [] 
opgebouwde_basisrente = 0.0

for d in range(jaren * 365):
    huidige_dag = start_datum + timedelta(days=d)
    
    # 1. Stortingen (Op de 1e van de maand)
    if huidige_dag.day == 1:
        saldo += inleg
        transacties.append((huidige_dag, inleg))
        data.append({"Datum": huidige_dag, "Type": "Storting", "Bedrag": inleg, "Saldo": saldo})
        
    # 2. Basisrente opbouw (dagelijks, maar storting pas op 1 januari)
    opgebouwde_basisrente += (saldo * basis_rate) / 365
    
    # Storting basisrente op 1 januari van elk jaar
    if huidige_dag.month == 1 and huidige_dag.day == 1 and d > 0:
        data.append({"Datum": huidige_dag, "Type": "Basisrente Storting", "Bedrag": round(opgebouwde_basisrente, 2), "Saldo": saldo})
        opgebouwde_basisrente = 0.0
        
    # 3. Getrouwheidspremie (per kwartaal: 1 jan, 1 apr, 1 jul, 1 okt)
    if huidige_dag.day == 1 and huidige_dag.month in [1, 4, 7, 10]:
        for t_datum, t_bedrag in transacties:
            # Check of het bedrag de 365-dagen termijn heeft voltooid voor dit kwartaal
            if huidige_dag >= t_datum + timedelta(days=365):
                p_rente = t_bedrag * premie_rate
                # Voeg alleen toe als het nog niet eerder is uitgekeerd (eenvoudige check)
                data.append({"Datum": huidige_dag, "Type": "Getrouwheidspremie", "Bedrag": round(p_rente, 2), "Saldo": saldo})
                # Verwijder uit lijst na uitkering om dubbeltelling te voorkomen
                transacties.remove((t_datum, t_bedrag))

# --- Weergave ---
df = pd.DataFrame(data)
# Filter & Tabel
selected_types = st.multiselect("Filter op type:", options=df["Type"].unique(), default=df["Type"].unique())
filtered_df = df[df["Type"].isin(selected_types)].copy()
filtered_df["Datum"] = filtered_df["Datum"].dt.strftime("%d-%m-%Y")
st.dataframe(filtered_df, use_container_width=True)