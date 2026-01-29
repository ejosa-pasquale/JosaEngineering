import streamlit as st

from calcolo_ev import genera_progetto_ev, PORTATA_BASE
from documenti_ev import genera_pdf_unico_bytes

st.set_page_config(page_title="Progetto EV – CEI 64-8/722", page_icon="⚡", layout="wide")

st.title("⚡ Progetto linea EV – CEI 64-8 ")
st.caption("Progetto Elettrico - Infrastruttura di Ricarica eVFs ")

st.divider()

c1, c2, c3 = st.columns(3)
with c1:
    nome = st.text_input("Nome", "Mario")
    cognome = st.text_input("Cognome", "Rossi")
    indirizzo = st.text_input("Indirizzo impianto", "Via Garibaldi 1, Mantova")

with c2:
    alimentazione = st.selectbox("Alimentazione", ["Monofase 230 V", "Trifase 400 V"], index=1)
    max_kw = 7.4 if alimentazione == "Monofase 230 V" else 250.0
    potenza_kw = st.number_input("Potenza EVSE (kW)", min_value=1.0, max_value=float(max_kw), value=min(22.0, max_kw), step=0.5)
    distanza_m = st.number_input("Distanza quadro → EVSE (m)", min_value=1.0, max_value=500.0, value=35.0, step=1.0)

with c3:
    tipo_posa = st.selectbox("Tipo posa", list(PORTATA_BASE.keys()))
    sistema = st.selectbox("Sistema di distribuzione", ["TT", "TN-S", "TN-C-S"])
    icc_ka = st.number_input("Icc presunta al punto (kA)", min_value=1.0, max_value=50.0, value=6.0, step=0.5)

st.subheader("Parametri di progetto")
p1, p2, p3, p4 = st.columns(4)
with p1:
    cosphi = st.slider("cosφ", min_value=0.80, max_value=1.00, value=0.95, step=0.01)
with p2:
    temp_amb = st.selectbox("Temperatura ambiente (°C)", [30, 35, 40, 45, 50], index=0)
with p3:
    n_linee = st.number_input("N. linee raggruppate", min_value=1, max_value=10, value=1)
with p4:
    gestione_carichi = st.checkbox("Gestione carichi (load management)", value=False)

st.subheader("CEI 64-8/7 Sez. 722 – Dati EV")
e1, e2, e3, e4 = st.columns(4)
with e1:
    modo_ricarica = st.selectbox("Modo di ricarica", ["Modo 1", "Modo 2", "Modo 3", "Modo 4"], index=2)
with e2:
    tipo_punto = st.selectbox("Punto di connessione", ["Connettore EV", "Presa domestica", "Presa industriale"], index=0)
with e3:
    esterno = st.checkbox("Installazione esterna", value=False)
with e4:
    spd_previsto = st.checkbox("SPD previsto/valutato", value=True)

e5, e6, e7, e8 = st.columns(4)
with e5:
    ip_rating = st.number_input("IP (es. 44)", min_value=0, max_value=99, value=44, step=1)
with e6:
    ik_rating = st.number_input("IK (es. 7)", min_value=0, max_value=10, value=7, step=1)
with e7:
    altezza_presa_m = st.number_input("Altezza punto connessione (m)", min_value=0.0, max_value=3.0, value=1.0, step=0.05)
with e8:
    evse_rdcdd_integrato = st.checkbox("RDC-DD 6mA DC integrato EVSE", value=True)

st.subheader("Protezione differenziale (per punto)")
d1, d2 = st.columns(2)
with d1:
    rcd_tipo = st.selectbox("Tipo RCD", ["Tipo B", "Tipo A + RDC-DD 6mA DC"], index=1)
with d2:
    rcd_idn_ma = st.selectbox("IΔn (mA)", [30, 100, 300], index=0)

st.subheader("Verifiche 4-41 / campo (opzionali ma consigliate)")
v1, v2, v3 = st.columns(3)
with v1:
    ra_ohm = st.number_input("Ra (Ω) – solo TT (se noto)", min_value=0.0, max_value=5000.0, value=0.0, step=1.0)
    ra_enable = st.checkbox("Usa Ra nella verifica TT", value=False)
with v2:
    zs_ohm = st.number_input("Zs (Ω) – solo TN (se noto)", min_value=0.0, max_value=10.0, value=0.0, step=0.01)
    zs_enable = st.checkbox("Usa Zs (nota/verifica TN)", value=False)
with v3:
    t_int = st.number_input("t intervento (s) per I²t (se noto)", min_value=0.0, max_value=10.0, value=0.0, step=0.01)
    t_enable = st.checkbox("Usa t per verifica I²t", value=False)

st.divider()

if "res" not in st.session_state:
    st.session_state.res = None

if st.button("✅ Calcola e genera documenti", type="primary"):
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

if res:
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Ib (A)", f"{res['Ib_a']}")
    m2.metric("In (A)", f"{res['In_a']}")
    m3.metric("Iz (A)", f"{res['Iz_a']}")
    m4.metric("Fase (mm²)", f"{res['sezione_mm2']}")
    m5.metric("PE (mm²)", f"{res['sezione_pe_mm2']}")
    m6.metric("S min caduta (mm²)", f"{res['S_cad_min_mm2']}")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Relazione", "Unifilare", "Planimetria", "Checklist 722", "Check 4-41"])

    with tab1:
        st.text_area("Relazione tecnica", value=res["relazione"], height=420)
    with tab2:
        st.text_area("Dati schema unifilare", value=res["unifilare"], height=420)
    with tab3:
        st.text_area("Note planimetria", value=res["planimetria"], height=420)
    with tab4:
        st.subheader("Esiti OK")
        st.write("\n".join([f"• {x}" for x in res["ok_722"]]) if res["ok_722"] else "—")
        st.subheader("Warning")
        if res["warning_722"]:
            st.warning("\n".join([f"• {x}" for x in res["warning_722"]]))
        else:
            st.write("—")
        st.subheader("Non conformità")
        if res["nonconf_722"]:
            st.error("\n".join([f"• {x}" for x in res["nonconf_722"]]))
        else:
            st.write("—")
    with tab5:
        st.subheader("Esiti OK")
        st.write("\n".join([f"• {x}" for x in res["ok_441"]]) if res["ok_441"] else "—")
        st.subheader("Warning")
        if res["warning_441"]:
            st.warning("\n".join([f"• {x}" for x in res["warning_441"]]))
        else:
            st.write("—")
        st.subheader("Non conformità")
        if res["nonconf_441"]:
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
        label="⬇️ Scarica PDF completo (Relazione + Unifilare + Planimetria + Checklist 722)",
        data=pdf_bytes,
        file_name="Progetto_EV_CEI64-8_722.pdf",
        mime="application/pdf"
    )
