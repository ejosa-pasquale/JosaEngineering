import streamlit as st

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))  # ensure local imports work when run from project root

from calcolo_ev import genera_progetto_ev, PORTATA_BASE
from documenti_ev import genera_pdf_unico_bytes

# =========================
# Config & Theme
# =========================
st.set_page_config(
    page_title="Progetto EV – CEI 64-8/7.22",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
<style>
/* layout polish */
.block-container { padding-top: 1.25rem; padding-bottom: 3rem; }
h1 { letter-spacing: -0.02em; }
.small-muted { color: rgba(49,51,63,0.70); font-size: 0.95rem; }
.card {
  background: #ffffff;
  border: 1px solid rgba(49,51,63,0.12);
  border-radius: 14px;
  padding: 14px 16px;
}
hr { margin: 1.1rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("⚡ Progettazione Ricarica Veicoli Elettrici (EV) – CEI 64-8 Sez. 7.22")
st.caption("Calcolo, verifica sezione linea, protezioni e relazione tecnica – eV Field Service")

with st.sidebar:
    st.header("🧭 Guida rapida")
    st.markdown(
        """
- Inserisci i **dati impianto** (alimentazione, potenza, lunghezza).
- Completa i **parametri di progetto** (cosφ, temperatura, raggruppamento).
- Inserisci i **dati EV (Sez. 7.22)** (modo, punto, esterno, IP/IK, SPD).
- Premi **Calcola** e scarica il **PDF**.

**Nota “a prova di ingegnere elettrico”**
- Il software non “inventa” dati: se una verifica richiede un valore non noto (es. Ra o Zs) puoi abilitarla solo se lo inserisci.
"""
    )
    st.divider()
    st.markdown(
        '<div class="small-muted">Suggerimento: passa col mouse sull’icona ℹ️ per i dettagli tecnici dei parametri.</div>',
        unsafe_allow_html=True,
    )

st.divider()

# =========================
# Input area (guided)
# =========================

st.subheader("1) Dati generali")
c1, c2, c3 = st.columns(3)
with c1:
    nome = st.text_input("Nome", "Mario", help="Dati anagrafici per intestazione relazione.")
    cognome = st.text_input("Cognome", "Rossi", help="Dati anagrafici per intestazione relazione.")
    indirizzo = st.text_input(
        "Indirizzo impianto",
        "Via Garibaldi 1, Mantova",
        help="Ubicazione dell’impianto (compare nella relazione).",
    )

st.subheader("2) Dati impianto")
i1, i2, i3, i4 = st.columns(4)
with i1:
    alimentazione = st.selectbox(
        "Alimentazione",
        ["Monofase 230 V", "Trifase 400 V"],
        index=1,
        help="Tensione nominale del sistema (230 V monofase o 400 V trifase).",
    )
    max_kw = 7.4 if alimentazione == "Monofase 230 V" else 250.0

with i2:
    potenza_kw = st.number_input(
        "Potenza EVSE (kW)",
        min_value=1.0,
        max_value=float(max_kw),
        value=min(22.0, max_kw),
        step=0.5,
        help="Potenza nominale della stazione di ricarica (EVSE). In monofase, limite tipico 7,4 kW.",
    )

with i3:
    distanza_m = st.number_input(
        "Distanza quadro → EVSE (m)",
        min_value=1.0,
        max_value=500.0,
        value=35.0,
        step=1.0,
        help="Lunghezza reale del percorso cavo (non in linea d’aria). Influisce su ΔV e Zs.",
    )

with i4:
    icc_ka = st.number_input(
        "Icc presunta al punto (kA)",
        min_value=1.0,
        max_value=50.0,
        value=6.0,
        step=0.5,
        help="Corrente di cortocircuito presunta al punto di consegna/derivazione. Serve per scelta potere d’interruzione e verifiche.",
    )

i5, i6 = st.columns(2)
with i5:
    tipo_posa = st.selectbox(
        "Tipo posa",
        list(PORTATA_BASE.keys()),
        help="Metodo di posa (CEI 64-8 / tabelle portata). Determina Iz di base.",
    )
with i6:
    sistema = st.selectbox(
        "Sistema di distribuzione",
        ["TT", "TN-S", "TN-C-S"],
        help="TT: verifica tipica Ra·Id ≤ 50 V. TN: verifica Zs/impedenza anello e tempi di intervento.",
    )

st.subheader("3) Parametri di progetto")
p1, p2, p3, p4 = st.columns(4)
with p1:
    cosphi = st.slider(
        "cosφ",
        min_value=0.80,
        max_value=1.00,
        value=0.95,
        step=0.01,
        help="Fattore di potenza. Influisce sulla corrente Ib: Ib ↑ se cosφ ↓.",
    )
with p2:
    temp_amb = st.selectbox(
        "Temperatura ambiente (°C)",
        [30, 35, 40, 45, 50],
        index=0,
        help="Temperatura di riferimento per il fattore di correzione (kT) della portata Iz.",
    )
with p3:
    n_linee = st.number_input(
        "N. linee raggruppate",
        min_value=1,
        max_value=10,
        value=1,
        help="Raggruppamento di cavi (kG). Più linee → Iz effettiva diminuisce.",
    )
with p4:
    gestione_carichi = st.checkbox(
        "Gestione carichi (load management)",
        value=False,
        help="Se presente, può ridurre la potenza simultanea richiesta e migliorare compatibilità con fornitura.",
    )

st.subheader("4) CEI 64-8/7 Sez. 7.22 – Dati EV")
e1, e2, e3, e4 = st.columns(4)
with e1:
    modo_ricarica = st.selectbox(
        "Modo di ricarica",
        ["Modo 1", "Modo 2", "Modo 3", "Modo 4"],
        index=2,
        help="Classificazione IEC/CEI EN 61851. Tipico per infrastrutture: Modo 3 (AC) o Modo 4 (DC).",
    )
with e2:
    tipo_punto = st.selectbox(
        "Punto di connessione",
        ["Connettore EV", "Presa domestica", "Presa industriale"],
        index=0,
        help="Tipo di connessione lato utente. Presa domestica ha vincoli più severi in corrente/uso.",
    )
with e3:
    esterno = st.checkbox(
        "Installazione esterna",
        value=False,
        help="Se esterno, verificare IP/IK, protezioni meccaniche, UV, drenaggi e condizioni ambientali.",
    )
with e4:
    spd_previsto = st.checkbox(
        "SPD previsto/valutato",
        value=True,
        help="Protezione contro sovratensioni (SPD). Coordinare con analisi rischio e livello di impianto.",
    )

e5, e6, e7, e8 = st.columns(4)
with e5:
    ip_rating = st.number_input(
        "IP (es. 44)",
        min_value=0,
        max_value=99,
        value=44,
        step=1,
        help="Grado di protezione IP dell’apparecchiatura in sito. Tipico esterno ≥ IP44 (valutare caso per caso).",
    )
with e6:
    ik_rating = st.number_input(
        "IK (es. 7)",
        min_value=0,
        max_value=10,
        value=7,
        step=1,
        help="Resistenza agli urti (IK). Per aree accessibili al pubblico spesso ≥ IK07.",
    )
with e7:
    altezza_presa_m = st.number_input(
        "Altezza punto connessione (m)",
        min_value=0.0,
        max_value=3.0,
        value=1.0,
        step=0.05,
        help="Altezza installazione del punto di connessione (ergonomia/sicurezza).",
    )
with e8:
    evse_rdcdd_integrato = st.checkbox(
        "RDC-DD 6mA DC integrato EVSE",
        value=True,
        help="Dispositivo di rilevamento DC 6 mA integrato. Influenza scelta RCD (es. Tipo A + RDC-DD).",
    )

st.subheader("5) Protezione differenziale (per punto)")
d1, d2 = st.columns(2)
with d1:
    rcd_tipo = st.selectbox(
        "Tipo RCD",
        ["Tipo B", "Tipo A + RDC-DD 6mA DC"],
        index=1,
        help="Per EV: richieste/soluzioni tipiche includono Tipo B oppure Tipo A con RDC-DD 6 mA DC integrato/esterno.",
    )
with d2:
    rcd_idn_ma = st.selectbox(
        "IΔn (mA)",
        [30, 100, 300],
        index=0,
        help="Corrente differenziale nominale. 30 mA tipico per protezione addizionale; 100/300 mA per scopi selettivi/incendio (da progetto).",
    )

st.subheader("6) Verifiche 4-41 / campo (opzionali ma consigliate)")
v1, v2, v3 = st.columns(3)
with v1:
    ra_ohm = st.number_input(
        "Ra (Ω) – solo TT (se noto)",
        min_value=0.0,
        max_value=5000.0,
        value=0.0,
        step=1.0,
        help="Resistenza di terra dell’impianto (TT). Se la conosci, abilita la verifica Ra·Id ≤ 50 V.",
    )
    ra_enable = st.checkbox(
        "Usa Ra nella verifica TT",
        value=False,
        help="Abilita la verifica solo se Ra è stata misurata o stimata con criterio.",
    )
with v2:
    zs_ohm = st.number_input(
        "Zs (Ω) – solo TN (se noto)",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.01,
        help="Impedenza anello di guasto (TN). Se nota, abilita la verifica dei tempi di intervento/protezioni.",
    )
    zs_enable = st.checkbox(
        "Usa Zs (nota/verifica TN)",
        value=False,
        help="Abilita solo se Zs è nota (misura o calcolo) e coerente col punto considerato.",
    )
with v3:
    t_int = st.number_input(
        "t intervento (s) per I²t (se noto)",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.01,
        help="Tempo di intervento della protezione (per verifica termica I²t).",
    )
    t_enable = st.checkbox(
        "Usa t per verifica I²t",
        value=False,
        help="Abilita se il tempo è noto (da curva dispositivo o selettività).",
    )

st.divider()

if "res" not in st.session_state:
    st.session_state.res = None

# =========================
# Action
# =========================
left, right = st.columns([1, 2])
with left:
    calcola = st.button("✅ Calcola e genera documenti", type="primary")
with right:
    st.markdown(
        '<div class="card"><b>Controllo rapido:</b> se sei in monofase, la potenza massima ammessa qui è 7,4 kW. '
        "Per potenze superiori seleziona trifase.</div>",
        unsafe_allow_html=True,
    )

if calcola:
    if alimentazione == "Monofase 230 V" and potenza_kw > 7.4:
        st.error("Monofase: potenza > 7,4 kW non ammessa.")
        st.stop()

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
            n_linee=int(n_linee),
            icc_ka=icc_ka,
            modo_ricarica=modo_ricarica,
            tipo_punto=tipo_punto,
            esterno=esterno,
            ip_rating=int(ip_rating),
            ik_rating=int(ik_rating),
            altezza_presa_m=float(altezza_presa_m),
            spd_previsto=spd_previsto,
            gestione_carichi=gestione_carichi,
            rcd_tipo=rcd_tipo,
            rcd_idn_ma=int(rcd_idn_ma),
            evse_rdcdd_integrato=evse_rdcdd_integrato,
            ra_ohm=(float(ra_ohm) if ra_enable else None),
            zs_ohm=(float(zs_ohm) if zs_enable else None),
            t_intervento_s=(float(t_int) if t_enable else None),
        )
        st.session_state.res = res
        st.success("Calcolo completato.")
    except Exception as e:
        st.session_state.res = None
        st.error(f"Errore: {e}")

res = st.session_state.res

# =========================
# Output
# =========================
if res:
    st.subheader("Risultati principali")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Ib [A]", res.get("Ib_a", "—"))
    m2.metric("In [A]", res.get("In_a", "—"))
    m3.metric("Iz [A]", res.get("Iz_a", "—"))
    m4.metric("Sezione [mm²]", res.get("sezione_mm2", "—"))
    m5.metric("ΔV [%]", res.get("dv_percent", res.get("deltaV_percent", "—")))
    m6.metric("Esito", "OK" if (not res.get("nonconf_722")) else "ATTENZIONE")

    st.divider()

    t1, t2, t3 = st.tabs(["📄 Relazione", "✅ Checklist 7.22", "🧪 Verifiche 4-41"])
    with t1:
        st.text_area("Relazione tecnica (anteprima)", res.get("relazione", ""), height=320)
        st.caption("Suggerimento: scarica il PDF per l’impaginazione completa e le sezioni formattate.")

    with t2:
        c_ok, c_warn, c_bad = st.columns(3)
        with c_ok:
            st.subheader("OK")
            if res.get("ok_722"):
                st.success("\n".join([f"• {x}" for x in res["ok_722"]]))
            else:
                st.write("—")
        with c_warn:
            st.subheader("Warning")
            if res.get("warning_722"):
                st.warning("\n".join([f"• {x}" for x in res["warning_722"]]))
            else:
                st.write("—")
        with c_bad:
            st.subheader("Non conformità")
            if res.get("nonconf_722"):
                st.error("\n".join([f"• {x}" for x in res["nonconf_722"]]))
            else:
                st.write("—")

    with t3:
        c_ok, c_warn, c_bad = st.columns(3)
        with c_ok:
            st.subheader("OK")
            if res.get("ok_441"):
                st.success("\n".join([f"• {x}" for x in res["ok_441"]]))
            else:
                st.write("—")
        with c_warn:
            st.subheader("Warning")
            if res.get("warning_441"):
                st.warning("\n".join([f"• {x}" for x in res["warning_441"]]))
            else:
                st.write("—")
        with c_bad:
            st.subheader("Non conformità")
            if res.get("nonconf_441"):
                st.error("\n".join([f"• {x}" for x in res["nonconf_441"]]))
            else:
                st.write("—")

    st.divider()

    pdf_bytes = genera_pdf_unico_bytes(
        relazione=res["relazione"],
        unifilare=res["unifilare"],
        planimetria=res["planimetria"],
        ok_722=res["ok_722"],
        warning_722=res["warning_722"],
        nonconf_722=res["nonconf_722"],
    )

    st.download_button(
        label="⬇️ Scarica PDF completo (Relazione Tecnica + Note per Unifilare + Note per Planimetria)",
        data=pdf_bytes,
        file_name="Progetto_EV_CEI64-8_722.pdf",
        mime="application/pdf",
    )
