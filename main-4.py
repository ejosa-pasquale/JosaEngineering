import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from math import ceil, floor
from datetime import datetime, timedelta
from collections import defaultdict

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="AI-JoSa | EV Optimizer", layout="wide", page_icon="⚡")

# 2. STILE CSS (Tutte le personalizzazioni grafiche)
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; color: #1E293B; }
    .main-header {
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .param-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 1.5rem;
    }
    .section-title {
        color: #1E3A8A;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 5px;
    }
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 15px !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        border-left: 5px solid #3498DB !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #10B981;
        color: white;
        height: 3.5rem;
        font-weight: 700;
        border-radius: 10px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# 3. SISTEMA DI TRADUZIONE
translations = {
    "it": {
        "title": "AI-JoSa ⚡",
        "subtitle": "Ottimizzatore Professionale Infrastruttura EV",
        "step1": "🎯 Obiettivi e Vincoli di Rete",
        "step2": "💰 Parametri Economici ed Efficienza",
        "step3": "🚗 Configurazione Parco Veicoli",
        "budget": "Budget Massimo (€)",
        "power": "Potenza Disponibile (kW)",
        "cost_int": "Costo kWh Interno (€)",
        "cost_ext": "Costo kWh Pubblico (€)",
        "penalty": "Tempo perso per ricarica esterna (min/kWh)",
        "btn_calc": "🚀 GENERA MODELLO OTTIMIZZATO",
        "kpi_ext_energy": "Energia Esterna",
        "kpi_ext_cost": "Costo Extra Anno",
        "kpi_lost_time": "Tempo Perso Anno",
        "tab_plan": "Pianificazione",
        "tab_fleet": "Stato Flotta",
        "tab_compare": "Confronto Soluzioni",
        "footer": "AI-JoSa Suite by EV Field Service"
    },
    "en": {
        "title": "AI-JoSa ⚡",
        "subtitle": "Professional EV Infrastructure Optimizer",
        "step1": "🎯 Goals & Grid Constraints",
        "step2": "💰 Economic & Efficiency Parameters",
        "step3": "🚗 Fleet Configuration",
        "budget": "Max Budget (€)",
        "power": "Available Power (kW)",
        "cost_int": "Internal kWh Cost (€)",
        "cost_ext": "Public kWh Cost (€)",
        "penalty": "Time lost for ext. charging (min/kWh)",
        "btn_calc": "🚀 GENERATE OPTIMIZED MODEL",
        "kpi_ext_energy": "External Energy",
        "kpi_ext_cost": "Extra Yearly Cost",
        "kpi_lost_time": "Time Lost Yearly",
        "tab_plan": "Planning",
        "tab_fleet": "Fleet Status",
        "tab_compare": "Compare Solutions",
        "footer": "AI-JoSa Suite by EV Field Service"
    }
}

def get_text(key):
    lang = st.session_state.get("language", "it")
    return translations.get(lang, "it").get(key, key)

# Selezione lingua
l_col1, l_col2 = st.columns([8, 2])
with l_col2:
    lang_sel = st.selectbox("🌐 Lingua", ["Italiano", "English"])
    st.session_state.language = "it" if lang_sel == "Italiano" else "en"

# 4. HEADER
st.markdown(f"""
    <div class="main-header">
        <h1>{get_text('title')}</h1>
        <p>{get_text('subtitle')}</p>
    </div>
""", unsafe_allow_html=True)

# 5. DATABASE COLONNINE
COL_DB = {
    "AC_22": {"p": 11, "acquisto": 1500, "install": 1650, "maint": 50},
    "DC_20": {"p": 20, "acquisto": 7000, "install": 3000, "maint": 150},
    "DC_30": {"p": 30, "acquisto": 8000, "install": 4500, "maint": 200},
    "DC_50": {"p": 50, "acquisto": 12000, "install": 7500, "maint": 250}
}

# 6. LOGICA DI CALCOLO
def trova_slot(prenotazioni, inizio, fine):
    punti = sorted(list(set([inizio] + [p["inizio"] for p in prenotazioni] + [p["fine"] for p in prenotazioni] + [fine])))
    for i in range(len(punti)-1):
        s_s, s_e = punti[i], punti[i+1]
        if s_s >= inizio and s_e <= fine and (s_e - s_s) >= 0.25:
            if not any(not (s_e <= p["inizio"] + 0.001 or s_s >= p["fine"] - 0.001) for p in prenotazioni):
                return (s_s, s_e)
    return None

def simulazione(config, veicoli, costi, t_ac, t_dc, penalty):
    stazioni = []
    for tipo, q in config.items():
        for i in range(q):
            stazioni.append({"nome": f"{tipo}_{i+1}", "p": COL_DB[tipo]["p"], "prenotazioni": [], "max": t_ac if "AC" in tipo else t_dc})
    
    veicoli_sim = []
    for v in veicoli:
        if v.get("gruppo"):
            for i in range(v["quantita"]):
                veicoli_sim.append({"nome": f"{v['nome']}_{i+1}", "energia": v["energia"], "inizio": v["inizio"], "fine": v["fine"], "rim": v["energia"]})
        else:
            veicoli_sim.append({**v, "rim": v["energia"]})

    for _ in range(50):
        progress = False
        to_serve = sorted([v for v in veicoli_sim if v["rim"] > 0.1], key=lambda x: (x["fine"], -x["rim"]))
        for v in to_serve:
            for s in stazioni:
                if len(s["prenotazioni"]) >= s["max"]: continue
                slot = trova_slot(s["prenotazioni"], v["inizio"], v["fine"])
                if slot:
                    e = min(v["rim"], (slot[1]-slot[0])*s["p"])
                    if e > 0.1:
                        s["prenotazioni"].append({"veicolo": v["nome"], "inizio": slot[0], "fine": slot[0]+(e/s["p"]), "energia": e})
                        v["rim"] -= e
                        progress = True; break
        if not progress: break

    e_tot = sum(v["energia"] for v in veicoli_sim)
    e_int = sum(v["energia"] - v["rim"] for v in veicoli_sim)
    e_ext = e_tot - e_int
    c_acq = sum(COL_DB[t]["acquisto"] * q for t, q in config.items())
    c_ins = sum(COL_DB[t]["install"] * q for t, q in config.items())
    c_mnt = sum(COL_DB[t]["maint"] * q for t, q in config.items())
    
    return {
        "config": config, "stazioni": stazioni, "veicoli": veicoli_sim,
        "kpi": {
            "e_int": e_int, "e_ext": e_ext, "e_tot": e_tot,
            "c_cap": c_acq + c_ins, "c_acq": c_acq, "c_ins": c_ins, "c_mnt": c_mnt,
            "risparmio": e_int * (costi["pub"] - costi["pri"]),
            "costo_ext": e_ext * costi["pub"] * 365,
            "tempo_perso": (e_ext * penalty / 60) * 365
        }
    }

# 7. INTERFACCIA DI INSERIMENTO (USER FRIENDLY)
st.markdown(f'<div class="section-title">{get_text("step1")}</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1: budget = st.number_input(get_text("budget"), 5000, 300000, 60000, step=5000)
with c2: power = st.number_input(get_text("power"), 10, 1000, 100, step=10)

st.markdown(f'<div class="section-title">{get_text("step2")}</div>', unsafe_allow_html=True)
c3, c4, c5 = st.columns(3)
with c3: c_pri = st.number_input(get_text("cost_int"), 0.1, 0.6, 0.22)
with c4: c_pub = st.number_input(get_text("cost_ext"), 0.3, 1.5, 0.65)
with c5: penalty = st.slider(get_text("penalty"), 0, 60, 15)

st.markdown(f'<div class="section-title">{get_text("step3")}</div>', unsafe_allow_html=True)
v_mode = st.radio("Metodo:", ["Singoli", "Gruppi"], horizontal=True)
v_data = []
if v_mode == "Singoli":
    nv = st.number_input("N. Veicoli", 1, 50, 4)
    cols = st.columns(2)
    for i in range(nv):
        with cols[i%2].expander(f"🚗 Veicolo {i+1}"):
            v_data.append({
                "nome": st.text_input("ID", f"V{i+1}", key=f"n{i}"),
                "energia": st.number_input("Km/gg", 10, 500, 100, key=f"k{i}") * st.number_input("Consumo", 0.1, 0.4, 0.2, key=f"c{i}"),
                "inizio": st.slider("Arrivo", 0.0, 24.0, 18.0, key=f"a{i}"),
                "fine": st.slider("Partenza", 0.0, 48.0, 32.0, key=f"d{i}"),
                "gruppo": False
            })
else:
    ng = st.number_input("N. Gruppi", 1, 10, 1)
    for i in range(ng):
        with st.expander(f"🚛 Gruppo {i+1}"):
            gc1, gc2 = st.columns(2)
            name = gc1.text_input("Nome", "Flotta A", key=f"gn{i}")
            qty = gc1.number_input("Quantità", 1, 100, 10, key=f"gq{i}")
            km = gc2.number_input("Km/gg", 10, 500, 120, key=f"gk{i}")
            cons = gc2.number_input("Consumo", 0.1, 0.4, 0.2, key=f"gc{i}")
            v_data.append({"nome": name, "quantita": qty, "energia": km*cons, "inizio": 18.0, "fine": 32.0, "gruppo": True})

# 8. ESECUZIONE
if st.button(get_text("btn_calc")):
    results = []
    for q_ac in range(12):
        for q_dc in range(6):
            if q_ac == 0 and q_dc == 0: continue
            for t_dc in ["DC_20", "DC_30", "DC_50"]:
                cfg = {k: v for k, v in {"AC_22": q_ac, t_dc: q_dc}.items() if v > 0}
                cost = sum((COL_DB[t]["acquisto"] + COL_DB[t]["install"]) * q for t, q in cfg.items())
                if cost <= budget and sum(COL_DB[t]["p"] * q for t, q in cfg.items()) <= power:
                    results.append(simulazione(cfg, v_data, {"pri": c_pri, "pub": c_pub}, 2, 6, penalty))
    st.session_state.res = sorted(results, key=lambda x: x["kpi"]["e_int"], reverse=True)

# 9. OUTPUT RISULTATI
if "res" in st.session_state and st.session_state.res:
    st.divider()
    curr = st.session_state.res[st.selectbox("🏆 Scegli Soluzione:", range(len(st.session_state.res)), format_func=lambda i: f"SOL {i+1} - Copertura {st.session_state.res[i]['kpi']['e_int']/st.session_state.res[i]['kpi']['e_tot']*100:.1f}%")]
    k = curr["kpi"]

    ck1, ck2, ck3, ck4 = st.columns(4)
    ck1.metric("CAPEX", f"€{k['c_cap']:,}")
    ck2.metric("Risparmio/Anno", f"€{k['risparmio']*365:,.0f}")
    ck3.metric("Copertura", f"{k['e_int']/k['e_tot']*100:.1f}%")
    ck4.metric("ROI", f"{k['c_cap']/(k['risparmio']*365) if k['risparmio']>0 else 0:.1f} anni")

    st.warning("⚠️ **Analisi Costi Ricarica Esterna**")
    ce1, ce2, ce3 = st.columns(3)
    ce1.metric(get_text("kpi_ext_energy"), f"{k['e_ext']:.1f} kWh/gg")
    ce2.metric(get_text("kpi_ext_cost"), f"€{k['costo_ext']:,.0f}")
    ce3.metric(get_text("kpi_lost_time"), f"{k['tempo_perso']:.0f} ore")

    t1, t2, t3 = st.tabs([get_text("tab_plan"), get_text("tab_fleet"), get_text("tab_compare")])
    with t1:
        cp1, cp2 = st.columns([1, 2])
        # Grafico Budget (RICHIESTA UTENTE)
        
        cp1.plotly_chart(go.Figure(data=[go.Pie(labels=['Hardware', 'Installazione', 'Manutenzione'], values=[k['c_acq'], k['c_ins'], k['c_mnt']], hole=.4)]), use_container_width=True)
        # Grafico Gantt
        g_d = []
        for s in curr["stazioni"]:
            for p in s["prenotazioni"]:
                b = datetime(2025, 1, 1)
                g_d.append({"Stazione": s["nome"], "Inizio": b + timedelta(hours=p["inizio"]), "Fine": b + timedelta(hours=p["fine"]), "Veicolo": p["veicolo"]})
        if g_d: cp2.plotly_chart(px.timeline(pd.DataFrame(g_d), x_start="Inizio", x_end="Fine", y="Stazione", color="Veicolo", template="plotly_white"), use_container_width=True)

    with t2:
        st.table(pd.DataFrame([{"ID": v["nome"], "Interno (kWh)": f"{v['energia']-v['rim']:.1f}", "Esterno (kWh)": f"{v['rim']:.1f}", "Stato": "✅" if v["rim"] < 0.1 else "⚠️"} for v in curr["veicoli"]]))

    with t3:
        st.dataframe(pd.DataFrame([{
            "Rank": i+1, "Config": str(r["config"]), "CAPEX": f"€{r['kpi']['c_cap']:,}", "Extra-Costo": f"€{r['kpi']['costo_ext']:,.0f}", "Tempo Perso (h)": f"{r['kpi']['tempo_perso']:.0f}"
        } for i, r in enumerate(st.session_state.res)]), use_container_width=True)

st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #64748B;'>{get_text('footer')}</div>", unsafe_allow_html=True)
