import streamlit as st
from calcolo_ev import genera_progetto_ev, PORTATA_BASE

st.set_page_config(
    page_title="Progetto EV – CEI 64-8",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Dimensionamento linea stazione di ricarica EV – CEI 64-8")

st.markdown(
    "Applicazione di **pre-dimensionamento** per linee di alimentazione di stazioni di ricarica EV "
    "secondo criteri CEI 64-8. I risultati devono essere verificati in sede di progetto esecutivo."
)

st.write("---")

# =========================
# INPUT DATI ANAGRAFICI
# =========================
col1, col2 = st.columns(2)
with col1:
    nome = st.text_input("Nome committente", "Mario")
    potenza_kw = st.number_input("Potenza stazione (kW)", min_value=1.0, max_value=200.0, value=22.0, step=1.0)
    distanza_m = st.number_input("Distanza quadro → colonnina (m)", min_value=1.0, max_value=300.0, value=35.0, step=1.0)
    alimentazione = st.selectbox("Alimentazione", ["Monofase 230 V", "Trifase 400 V"])

with col2:
    cognome = st.text_input("Cognome committente", "Rossi")
    indirizzo = st.text_input("Indirizzo impianto", "Via Garibaldi 1, Mantova")
    tipo_posa = st.selectbox("Tipo di posa", list(PORTATA_BASE.keys()))
    sistema = st.selectbox("Sistema di distribuzione", ["TT", "TN-S", "TN-C-S"])

st.write("---")

# =========================
# PARAMETRI DI PROGETTO
# =========================
st.subheader("Parametri di progetto")

col3, col4, col5 = st.columns(3)
with col3:
    cosphi = st.slider("cosφ di progetto", min_value=0.80, max_value=1.00, value=0.95, step=0.01)
with col4:
    temp_amb = st.selectbox("Temperatura ambiente (°C)", [30, 35, 40, 45, 50], index=0)
with col5:
    n_linee = st.number_input("Numero di linee raggruppate", min_value=1, max_value=10, value=1)

icc_ka = st.number_input("Icc presunta al punto di installazione (kA)", min_value=1.0, max_value=50.0, value=6.0, step=0.5)
rcd = st.selectbox(
    "Tipo di protezione differenziale",
    ["Tipo B", "Tipo A + RDC-DD 6mA DC"]
)

st.write("---")

# =========================
# CALCOLO
# =========================
if st.button("Calcola dimensionamento"):
    try:
        res = genera_progetto_ev(
            nome=nome,
            cognome=cognome,
            indirizzo=indirizzo,
            potenza_kw=potenza_kw,
            distanza_m=distanza_m,
            alimentazione=alimentazione,
            tipo_posa=tipo_posa,
            sistema=sistema,
            cosphi=cosphi,
            temp_amb=temp_amb,
            n_linee=n_linee,
            icc_ka=icc_ka,
            rcd=rcd
        )

        st.success("Calcolo completato con successo.")

        # --- Risultati sintetici ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ib (A)", f"{res['Ib']}")
        c2.metric("In interruttore (A)", f"{res['In']}")
        c3.metric("Iz corretta (A)", f"{res['Iz']}")
        c4.metric("Sezione cavo (mm²)", f"{res['Sezione']}")

        st.write("---")
        st.subheader("Relazione tecnica generata")

        st.text_area("Testo relazione", value=res["Relazione"], height=400)

        st.download_button(
            "⬇️ Scarica relazione in formato .txt",
            data=res["Relazione"],
            file_name="relazione_tecnica_EV.txt",
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"Errore nel calcolo: {e}")
