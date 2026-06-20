import pandas as pd
from playwright.sync_api import sync_playwright

def scrape_kbc():
    print("KBC spaarrentes ophalen...")
    url = "https://www.kbc.be/particulieren/nl/sparen/gereglementeerde-spaarrekeningen.html"
    data = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("table", timeout=15000)
            
            # We zoeken alle containers
            tabel_containers = page.query_selector_all("div[data-component-type='table']")
            
            for container in tabel_containers:
                table = container.query_selector("table")
                if not table: continue
                
                # Veilig de titel ophalen
                titel_element = table.evaluate_handle("el => el.querySelector('b')")
                titel = titel_element.evaluate("el => el.innerText") if titel_element else "KBC Spaarrekening"
                
                rows = table.query_selector_all("tr")
                for row in rows:
                    cols = row.query_selector_all("td")
                    if len(cols) >= 3:
                        text_basis = cols[1].inner_text()
                        if "%" in text_basis:
                            # Opschonen
                            basis_raw = text_basis.replace('op jaarbasis', '').strip()
                            getrouw_raw = cols[2].inner_text().replace('op jaarbasis', '').strip()
                            
                            # Berekening
                            try:
                                b_val = float(basis_raw.replace('%', '').replace(',', '.'))
                                g_val = float(getrouw_raw.replace('%', '').replace(',', '.'))
                                totaal = f"{(b_val + g_val):.2f}".replace('.', ',') + "%"
                            except:
                                totaal = "N/B"
                                
                            data.append({
                                "Bank": "KBC België",
                                "Spaarrekening": str(titel).strip(),
                                "Basisrente": basis_raw,
                                "Getrouwheidspremie": getrouw_raw,
                                "Totale Rente": totaal
                            })
        except Exception as e:
            print(f"Fout tijdens KBC scraping: {e}")
        finally:
            browser.close()
            
    return pd.DataFrame(data)

if __name__ == "__main__":
    df = scrape_kbc()
    if not df.empty:
        df.to_csv("KBC_Rentes.csv", sep=';', index=False, encoding='utf-8-sig')
        print(df.to_string(index=False))
        print("\nSucces! De data staat in KBC_Rentes.csv")
    else:
        print("Geen data gevonden.")