import streamlit as st
from calcolo_ev import genera_progetto_ev
from documenti_ev import genera_pdf_unico_bytes
from schemi_ev import genera_schema_svg

st.set_page_config(
    page_title="EV Project Pro – CEI 64-8/722",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
h1, h2, h3 { color:#0A3D62; }
.stMetric { background:#F4F6F7; padding:15px; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ EV Project Pro")
st.caption("Progettazione infrastrutture di ricarica – conforme CEI 64-8/722")

# =====================
# DATI TECNICO
# =====================
with st.expander("✍️ Dati tecnico firmatario", expanded=True):
    t1, t2, t3 = st.columns(3)
    with t1:
        tecnico = st.text_input("Tecnico")
    with t2:
        albo = st.text_input("Albo professionale")
    with t3:
        iscrizione = st.text_input("N° iscrizione")

# =====================
# DATI IMPIANTO
# =====================
st.subheader("⚙️ Dati impianto")
c1, c2, c3, c4 = st.columns(4)

with c1:
    alimentazione = st.selectbox("Alimentazione", ["Monofase 230 V", "Trifase 400 V"])
with c2:
    potenza_kw = st.number_input("Potenza EVSE [kW]", 1.0, 250.0, 22.0)
with c3:
    distanza_m = st.number_input("Lunghezza linea [m]", 1.0, 200.0, 30.0)
with c4:
    sistema = st.selectbox("Sistema di terra", ["TT", "TN-S", "TN-C-S"])

# =====================
# EV
# =====================
st.subheader("🚗 Parametri EV")
e1, e2, e3 = st.columns(3)
with e1:
    modo = st.selectbox("Modo di ricarica", ["Modo 3", "Modo 4"])
with e2:
    tipo_punto = st.selectbox("Connessione", ["Connettore EV", "Presa industriale"])
with e3:
    esterno = st.checkbox("Installazione esterna")

# =====================
# CALCOLO
# =====================
if st.button("✅ Genera progetto", type="primary"):
    res = genera_progetto_ev(
        alimentazione, potenza_kw, distanza_m,
        sistema, modo, tipo_punto, esterno,
        tecnico, albo, iscrizione
    )

    st.success("Progetto conforme")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ib [A]", res["Ib"])
    m2.metric("In [A]", res["In"])
    m3.metric("Iz [A]", res["Iz"])
    m4.metric("Sezione [mm²]", res["sezione"])

    svg = genera_schema_svg(res)
    st.image(svg)

    pdf = genera_pdf_unico_bytes(res)
    st.download_button("⬇️ Scarica fascicolo PDF", pdf, "Fascicolo_EV.pdf")
