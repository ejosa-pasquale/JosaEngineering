import streamlit as st
import pandas as pd
import plotly.express as px
from math import ceil, floor
from datetime import datetime, timedelta
from collections import defaultdict

# Page configuration
st.set_page_config(page_title="AI-JoSa", layout="wide", page_icon="⚡")

# --- Miglioramento Grafico (Punto 1) ---
st.markdown("""
<style>
    /* Sfondo e font */
    .stApp { background-color: #F8FAFC; color: #1E293B; }
    
    /* Card Moderne per KPI */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1) !important;
        border-left: 5px solid #3498DB !important;
    }
    
    /* Header e Sidebar */
    h1, h2, h3 { color: #1E3A8A !important; font-weight: 700; }
    .stSidebar { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    
    /* Pulsanti */
    .stButton>button {
        width: 100%;
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #1D4ED8; transform: translateY(-1px); }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab-list"] button {
        background-color: #F1F5F9;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #2563EB !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Translations (Invariate) ---
translations = {
    "it": {
        "app_title": "⚡ AI-JoSa ⚡",
        "tab1_title": "🔌 Ottimizzatore Colonnine ⚙️",
        "optimizer_header": "🔌 Ottimizzatore Infrastruttura Colonnine",
        "optimizer_intro": "Questa sezione ti aiuta a trovare la configurazione ottimale di colonnine di ricarica per il tuo parco veicoli.",
        "sidebar_config_params": "⚙️ Parametri di Configurazione",
        "sidebar_config_intro": "Definisci il budget e i costi per l'ottimizzazione.",
        "economic_tech_params": "Parametri Economici e Tecnici",
        "budget_available": "Budget disponibile (€)",
        "budget_help": "Costo massimo totale per colonnine e installazione.",
        "max_power_kw": "Potenza Massima Totale Impianto (kW)",
        "max_power_help": "La potenza massima complessiva supportata.",
        "alpha_weight": "Peso efficienza temporale (α)",
        "alpha_help": "Bilancia l'importanza tra tempo ed energia.",
        "ac_turns": "Turnazioni giornaliere AC",
        "ac_turns_help": "Veicoli medi per colonnina AC al giorno.",
        "dc_turns": "Turnazioni giornaliere DC",
        "dc_turns_help": "Veicoli medi per colonnina DC al giorno.",
        "energy_costs": "Costi Energia",
        "private_charge_cost": "Costo kWh interno (€)",
        "private_charge_help": "Costo energia ricarica in sede.",
        "public_charge_cost": "Costo kWh pubblico (€)",
        "public_charge_help": "Costo stimato ricarica pubblica.",
        "modify_charger_costs": "⚡ Modifica Costi Colonnine",
        "modify_charger_intro": "Personalizza i costi per ogni tipo.",
        "unit_cost": "Costo unità (€)",
        "unit_cost_help": "Costo acquisto {type}.",
        "installation_cost": "Costo installazione (€)",
        "installation_cost_help": "Costo installazione {type}.",
        "annual_maintenance_cost": "Costo manutenzione annuale (€)",
        "annual_maintenance_cost_help": "Manutenzione annuale {type}.",
        "vehicle_config": "🚗 Configurazione Veicoli",
        "vehicle_config_intro": "Definisci il tuo parco veicoli.",
        "input_mode": "Modalità inserimento",
        "single_vehicles": "Singoli veicoli",
        "vehicle_groups": "Gruppi di veicoli",
        "input_mode_help": "Scegli come inserire i dati.",
        "num_single_vehicles": "Numero veicoli",
        "num_single_vehicles_help": "Quanti veicoli configurare?",
        "single_vehicle": "Veicolo {i}",
        "vehicle_name": "Nome veicolo {i}",
        "daily_km": "Km giornalieri",
        "daily_km_help": "Chilometri percorsi in un giorno.",
        "consumption_kwh_km": "Consumo (kWh/km)",
        "consumption_kwh_km_help": "Consumo medio per km.",
        "stop_start_time": "Inizio sosta (h)",
        "stop_start_time_help": "Ora di arrivo (24h).",
        "stop_end_time": "Fine sosta (h)",
        "stop_end_time_help": "Ora di partenza (24h).",
        "num_vehicle_groups": "Numero gruppi",
        "group_name": "Nome gruppo {i}",
        "group_quantity": "Quantità",
        "group_quantity_help": "Veicoli nel gruppo.",
        "group_daily_km": "Km (per veicolo)",
        "group_consumption": "Consumo (kWh/km)",
        "group_stop_start": "Inizio sosta (h)",
        "group_stop_end": "Fine sosta (h)",
        "calculate_optimization": "🔍 Calcola Ottimizzazione Infrastruttura",
        "add_vehicle_warning": "Aggiungi almeno un veicolo.",
        "analysis_in_progress": "Analisi in corso...",
        "no_solution_found": "❌ Nessuna soluzione trovata.",
        "optimization_results": "📊 Risultati Ottimizzazione",
        "selected_solution": "✅ Configurazione Attiva",
        "current_config_display": "Dettaglio per:",
        "chargers_label": "Colonnine {type}",
        "total_chargers": "Totale Unità",
        "total_chargers_help": "Configurazione: {config_str}",
        "kpi_header": "Indicatori di Performance (KPI)",
        "total_initial_cost": "Costo Iniziale",
        "budget_percentage": "{percent:.1f}% del budget",
        "internal_energy_charged": "Energia Interna",
        "total_request_percentage": "{percent:.1f}% copertura",
        "estimated_annual_savings": "Risparmio Annuo",
        "vs_public_charges": "vs ricariche pubbliche",
        "combined_efficiency": "Efficienza Sistema",
        "combined_efficiency_help": "Tempo: {temp_eff:.1f}% | Energia: {energy_eff:.1f}%",
        "estimated_external_charge_cost": "Costo Ricarica Esterna",
        "avg_daily_external_cost": "Costo Giornaliero Esterno",
        "external_cost_help": "Energia caricata esternamente a €{cost:.2f}/kWh.",
        "partial_charge_warning": "⚠️ Energia residua esterna: {energy:.1f} kWh.",
        "full_charge_success": "✅ Carica completa garantita per tutti i veicoli.",
        "detailed_planning_tab": "Pianificazione",
        "vehicle_summary_tab": "Riepilogo Veicoli",
        "all_configs_tab": "Confronto Soluzioni",
        "detailed_optimization_analysis_tab": "Analisi Dettagliata",
        "gantt_intro": "Schema ricarica giornaliero.",
        "gantt_warning": "Molti veicoli, visualizzazione ridotta.",
        "charge_details": "📅 Registro Ricariche",
        "no_actual_charges": "Nessuna ricarica effettuata.",
        "no_chargers_configured": "Configurazione non valida.",
        "vehicle_charge_summary": "🚗 Stato Ricarica Veicoli",
        "vehicle_charge_summary_intro": "Riepilogo energia per singola unità.",
        "type_col": "Tipo",
        "name_col": "Nome",
        "energy_req_col": "Richiesta (kWh)",
        "internal_energy_col": "Interna (kWh)",
        "external_energy_col": "Esterna (kWh)",
        "charge_status_col": "Stato",
        "coverage_detail_col": "Dettagli",
        "complete_status": "✅ OK",
        "partial_status": "⚠️ Parziale",
        "complete_count": "{charged}/{total} completi",
        "charge_count": "{count} sessioni",
        "no_charge": "Senza carica",
        "all_tested_configs": "⚙️ Tutte le configurazioni testate",
        "configs_evaluated": "Soluzioni analizzate: **{count}**",
        "configs_order_info": "Ordinate per copertura energetica e costo.",
        "cost_analysis_selected_solution": "📈 Analisi Costi",
        "charger_cost_pie": "Acquisto",
        "installation_cost_pie": "Installazione",
        "maintenance_cost_pie": "Manutenzione (10y)",
        "cost_distribution_title": "Distribuzione Investimento",
        "no_config_to_analyze": "Nessun dato.",
        "detailed_optimization_analysis": "Dettaglio Efficienza",
        "detailed_opt_intro": "Metriche avanzate.",
        "energy_charged_by_type": "Energia per Tipo Colonnina",
        "no_energy_charged": "Nessuna ricarica registrata.",
        "vehicle_charge_status": "Status Parco Veicoli",
        "fully_charged": "Carica Totale",
        "partially_charged": "Carica Parziale",
        "not_charged": "Non Caricati",
        "charge_status_distribution": "Distribuzione Stato Carica",
        "energy_req_vs_charged_top10": "Energia Richiesta vs Erogata (Top 10)",
        "no_vehicle_data_for_chart": "Dati non sufficienti.",
        "footer_text": "Suite AI-Josa by EV Field Service - Strumenti Smart per la Mobilità Elettrica",
        "colonnina_label": "Unità",
        "vehicle_label": "Veicolo",
        "start_time_label": "Inizio",
        "end_time_label": "Fine",
        "charge_time_label": "Durata",
        "energy_kwh_label": "kWh",
        "charger_type_label": "Tipo",
        "hour_of_day": "Ora",
        "charger": "Punto Ricarica",
        "no_charge_gantt": "Inattiva",
        "gantt_chart_title": "Cronoprogramma Ricariche",
        "config_label": "Configurazione",
        "total_initial_cost_label": "Investimento",
        "budget_utilization_label": "Utilizzo Budget",
        "vehicles_served_percentage": "% Copertura",
        "num_chargers_label": "Num. Unità",
        "temporal_efficiency_label": "Eff. Tempo",
        "energy_efficiency_label": "Eff. Energia",
        "combined_efficiency_label": "Eff. Globale",
        "daily_external_cost_label": "Costo Esterno/Day",
        "total_installed_power_label": "Potenza (kW)",
        "power": "Potenza",
        "kw": "kW",
        "cost_unit": "Prezzo",
        "euro": "€",
        "group_label": "Gruppo",
        "single_label": "Singolo"
    },
    "en": {
        "app_title": "⚡ AI-JoSa ⚡",
        "tab1_title": "🔌 Optimizer ⚙️",
        "optimizer_header": "🔌 Infrastructure Optimizer",
        "optimizer_intro": "Optimize your charging fleet based on budget and power constraints.",
        "sidebar_config_params": "⚙️ Settings",
        "sidebar_config_intro": "Define constraints.",
        "economic_tech_params": "Tech & Econ Parameters",
        "budget_available": "Budget (€)",
        "budget_help": "Max cost for hardware and install.",
        "max_power_kw": "Grid Power (kW)",
        "max_power_help": "Max total system power.",
        "alpha_weight": "Weight (α)",
        "alpha_help": "Time vs Energy balance.",
        "ac_turns": "AC Turns",
        "ac_turns_help": "Avg vehicles/AC per day.",
        "dc_turns": "DC Turns",
        "dc_turns_help": "Avg vehicles/DC per day.",
        "energy_costs": "Energy Prices",
        "private_charge_cost": "Internal cost (€)",
        "private_charge_help": "Cost per kWh at depot.",
        "public_charge_cost": "Public cost (€)",
        "public_charge_help": "Public roaming cost.",
        "modify_charger_costs": "⚡ Hardware Costs",
        "modify_charger_intro": "Edit unit costs.",
        "unit_cost": "Unit Cost (€)",
        "unit_cost_help": "{type} price.",
        "installation_cost": "Installation (€)",
        "installation_cost_help": "{type} install cost.",
        "annual_maintenance_cost": "Maintenance (€)",
        "annual_maintenance_cost_help": "Yearly cost for {type}.",
        "vehicle_config": "🚗 Fleet Config",
        "vehicle_config_intro": "Add your vehicles.",
        "input_mode": "Input mode",
        "single_vehicles": "Singles",
        "vehicle_groups": "Groups",
        "input_mode_help": "Select input style.",
        "num_single_vehicles": "Quantity",
        "num_single_vehicles_help": "How many units?",
        "single_vehicle": "Vehicle {i}",
        "vehicle_name": "Name {i}",
        "daily_km": "Daily distance",
        "daily_km_help": "Km per day.",
        "consumption_kwh_km": "Cons (kWh/km)",
        "consumption_kwh_km_help": "Efficiency.",
        "stop_start_time": "Arrival (h)",
        "stop_start_time_help": "Start time (24h).",
        "stop_end_time": "Departure (h)",
        "stop_end_time_help": "End time (24h).",
        "num_vehicle_groups": "Group count",
        "group_name": "Group name {i}",
        "group_quantity": "Units",
        "group_quantity_help": "Vehicles in group.",
        "group_daily_km": "Km/unit",
        "group_consumption": "Cons (kWh/km)",
        "group_stop_start": "Arrival (h)",
        "group_stop_end": "Departure (h)",
        "calculate_optimization": "🔍 Calculate Optimization",
        "add_vehicle_warning": "Add at least 1 vehicle.",
        "analysis_in_progress": "Processing...",
        "no_solution_found": "❌ No valid solution.",
        "optimization_results": "📊 Analytics",
        "selected_solution": "✅ Active Config",
        "current_config_display": "Details for:",
        "chargers_label": "{type} Units",
        "total_chargers": "Total Hardware",
        "total_chargers_help": "Mix: {config_str}",
        "kpi_header": "Performance (KPIs)",
        "total_initial_cost": "Initial CAPEX",
        "budget_percentage": "{percent:.1f}% budget",
        "internal_energy_charged": "Depot Energy",
        "total_request_percentage": "{percent:.1f}% coverage",
        "estimated_annual_savings": "Est. Savings",
        "vs_public_charges": "vs public roaming",
        "combined_efficiency": "System Efficiency",
        "combined_efficiency_help": "Time: {temp_eff:.1f}% | Energy: {energy_eff:.1f}%",
        "estimated_external_charge_cost": "External Cost",
        "avg_daily_external_cost": "Daily OPEX (Ext)",
        "external_cost_help": "Energy needed externally at €{cost:.2f}/kWh.",
        "partial_charge_warning": "⚠️ Roaming needed: {energy:.1f} kWh.",
        "full_charge_success": "✅ 100% internal charge achievable.",
        "detailed_planning_tab": "Timeline",
        "vehicle_summary_tab": "Fleet Status",
        "all_configs_tab": "Comparisons",
        "detailed_optimization_analysis_tab": "Detailed Metrics",
        "gantt_intro": "Daily charging schedule.",
        "gantt_warning": "Density warning.",
        "charge_details": "📅 Charge Log",
        "no_actual_charges": "No data.",
        "no_chargers_configured": "Invalid config.",
        "vehicle_charge_summary": "🚗 Fleet Charging Summary",
        "vehicle_charge_summary_intro": "Energy breakdown per unit.",
        "type_col": "Type",
        "name_col": "Name",
        "energy_req_col": "Req (kWh)",
        "internal_energy_col": "Internal (kWh)",
        "external_energy_col": "External (kWh)",
        "charge_status_col": "Status",
        "coverage_detail_col": "Details",
        "complete_status": "✅ OK",
        "partial_status": "⚠️ Partial",
        "complete_count": "{charged}/{total} full",
        "charge_count": "{count} sessions",
        "no_charge": "Uncharged",
        "all_tested_configs": "⚙️ All Scenarios",
        "configs_evaluated": "Scenarios evaluated: **{count}**",
        "configs_order_info": "Ranked by coverage and cost.",
        "cost_analysis_selected_solution": "📈 Financials",
        "charger_cost_pie": "Hardware",
        "installation_cost_pie": "Install",
        "maintenance_cost_pie": "OPEX (10y)",
        "cost_distribution_title": "CAPEX Distribution",
        "no_config_to_analyze": "No data.",
        "detailed_optimization_analysis": "System Detail",
        "detailed_opt_intro": "Advanced metrics.",
        "energy_charged_by_type": "Energy by Charger Type",
        "no_energy_charged": "No sessions.",
        "vehicle_charge_status": "Fleet Readiness",
        "fully_charged": "Ready (100%)",
        "partially_charged": "Partial",
        "not_charged": "Empty",
        "charge_status_distribution": "Readiness Distribution",
        "energy_req_vs_charged_top10": "Req vs Charged (Top 10)",
        "no_vehicle_data_for_chart": "Insufficient data.",
        "footer_text": "AI-Josa Suite by EV Field Service - Smart EV Planning Tools",
        "colonnina_label": "Unit",
        "vehicle_label": "Vehicle",
        "start_time_label": "Start",
        "end_time_label": "End",
        "charge_time_label": "Duration",
        "energy_kwh_label": "kWh",
        "charger_type_label": "Type",
        "hour_of_day": "Hour",
        "charger": "Station",
        "no_charge_gantt": "Idle",
        "gantt_chart_title": "Charging Timeline",
        "config_label": "Config",
        "total_initial_cost_label": "CAPEX",
        "budget_utilization_label": "Budget Used",
        "vehicles_served_percentage": "Coverage",
        "num_chargers_label": "Units",
        "temporal_efficiency_label": "Time Eff.",
        "energy_efficiency_label": "Energy Eff.",
        "combined_efficiency_label": "Overall Eff.",
        "daily_external_cost_label": "Ext Cost/Day",
        "total_installed_power_label": "Power (kW)",
        "power": "Power",
        "kw": "kW",
        "cost_unit": "Unit Cost",
        "euro": "€",
        "group_label": "Group",
        "single_label": "Single"
    }
}

def get_text(key):
    lang = st.session_state.get("language", "it")
    return translations.get(lang, translations["it"]).get(key, key)

# Language selector
st.sidebar.header("🌐 Language / Lingua")
st.session_state.language = st.sidebar.radio(
    "Choose your language / Scegli la tua lingua",
    ["it", "en"],
    format_func=lambda x: "Italiano" if x == "it" else "English",
    key="language_selector"
)

# Title
st.title(get_text("app_title"))

# Tabs
tabs = st.tabs([get_text("tab1_title")])
tab1 = tabs[0]

# Constants
MIN_DURATA_RICARICA = 0.25
MIN_INTERVALLO_RICARICA = 0.5

with tab1:
    st.header(get_text("optimizer_header"))
    st.markdown(get_text("optimizer_intro"))

    COLONNINE_TAB1 = {
        "AC_22": {"potenza_effettiva": 11, "costo_colonnina": 1500, "costo_installazione": 1650, "costo_manutenzione_anno": 50, "colore": "#808080"},
        "DC_20": {"potenza_effettiva": 20, "costo_colonnina": 7000, "costo_installazione": 3000, "costo_manutenzione_anno": 150, "colore": "#00FF00"},
        "DC_30": {"potenza_effettiva": 30, "costo_colonnina": 8000, "costo_installazione": 4500, "costo_manutenzione_anno": 200, "colore": "#0000FF"},
        "DC_50": {"potenza_effettiva": 50, "costo_colonnina": 12000, "costo_installazione": 7500, "costo_manutenzione_anno": 250, "colore": "#FFA500"},
        "DC_60": {"potenza_effettiva": 60, "costo_colonnina": 15000, "costo_installazione": 9000, "costo_manutenzione_anno": 300, "colore": "#FF4500"},
        "DC_90": {"potenza_effettiva": 90, "costo_colonnina": 20000, "costo_installazione": 13500, "costo_manutenzione_anno": 400, "colore": "#FF0000"}
    }

    # --- Utility Functions ---
    def calcola_tempo_ricarica(energia, potenza):
        return max(MIN_DURATA_RICARICA, ceil((energia / potenza) * 4) / 4)

    def trova_slot_disponibile(prenotazioni, inizio, fine):
        prenotazioni.sort(key=lambda x: x["inizio"])
        best_slot = None
        max_duration = 0.0
        potential_start = max(inizio, 0.0)
        potential_end = fine
        if prenotazioni:
            potential_end = min(fine, prenotazioni[0]["inizio"] - MIN_INTERVALLO_RICARICA)
        if potential_end - potential_start >= MIN_DURATA_RICARICA:
            max_duration = potential_end - potential_start
            best_slot = (potential_start, potential_end)
        for i in range(len(prenotazioni)):
            current_end = prenotazioni[i]["fine"]
            next_start = prenotazioni[i+1]["inizio"] if i+1 < len(prenotazioni) else 24.0
            slot_start = max(inizio, current_end + MIN_INTERVALLO_RICARICA)
            slot_end = min(fine, next_start - MIN_INTERVALLO_RICARICA)
            if slot_end - slot_start > max_duration and slot_end - slot_start >= MIN_DURATA_RICARICA:
                max_duration = slot_end - slot_start
                best_slot = (slot_start, slot_end)
        if not best_slot and prenotazioni:
            potential_start = max(inizio, prenotazioni[-1]["fine"] + MIN_INTERVALLO_RICARICA)
            potential_end = fine
            if potential_end - potential_start >= MIN_DURATA_RICARICA:
                best_slot = (potential_start, potential_end)
        return best_slot

    def espandi_veicoli(veicoli):
        out = []
        for v in veicoli:
            if v.get("gruppo", False):
                for i in range(v["quantita"]):
                    out.append({
                        "nome": f"{v['nome']}_{i+1}",
                        "km": v["km"],
                        "consumo": v["consumo"],
                        "energia": v["km"] * v["consumo"],
                        "inizio": v["inizio"],
                        "fine": v["fine"],
                        "gruppo_origine": v["nome"]
                    })
            else:
                out.append(v.copy())
        return out

    def simula_ricariche(config, veicoli, costi, turnazioni_ac=3, turnazioni_dc=8):
        colonnine = []
        for tipo, q in config.items():
            for i in range(q):
                max_pren = turnazioni_ac if tipo == "AC_22" else turnazioni_dc
                colonnine.append({"tipo": tipo, "nome": f"{tipo}_{i+1}", "potenza": COLONNINE_TAB1[tipo]["potenza_effettiva"], "prenotazioni": [], "max_prenotazioni": max_pren})
        
        veicoli_singoli = espandi_veicoli(veicoli)
        energia_totale = sum(v["energia"] for v in veicoli_singoli)
        for v in veicoli_singoli:
            v["energia_rimanente"] = v["energia"]
            v["ricariche"] = []
            v["prossimo_inizio_ricarica_disponibile"] = v["inizio"]

        max_iter = 24 * 4 * max(1, len(veicoli_singoli))
        for _ in range(max_iter):
            to_serve = sorted([v for v in veicoli_singoli if v["energia_rimanente"] > 0], key=lambda x: (x["fine"], -x["energia_rimanente"]))
            if not to_serve: break
            charged_this_iter = set()
            for v in to_serve:
                if v["nome"] in charged_this_iter: continue
                best = {"col": None, "start": None, "end": None, "energia": 0, "full": False}
                for col in colonnine:
                    if len(col["prenotazioni"]) >= col["max_prenotazioni"]: continue
                    slot = trova_slot_disponibile(col["prenotazioni"], max(v["inizio"], v["prossimo_inizio_ricarica_disponibile"]), v["fine"])
                    if not slot: continue
                    durata = slot[1] - slot[0]
                    energia_pot = col["potenza"] * durata
                    energia_possibile = min(v["energia_rimanente"], energia_pot)
                    if energia_possibile <= 0: continue
                    can_full = abs(energia_possibile - v["energia_rimanente"]) < 0.01
                    if can_full and not best["full"]:
                        best = {"col": col, "start": slot[0], "end": slot[1], "energia": energia_possibile, "full": True}
                    elif energia_possibile > best["energia"] and not best["full"]:
                        best = {"col": col, "start": slot[0], "end": slot[1], "energia": energia_possibile, "full": False}
                
                if best["col"]:
                    durata_final = best["energia"] / best["col"]["potenza"]
                    pren = {"veicolo": v["nome"], "inizio": best["start"], "fine": best["start"] + durata_final, "energia": best["energia"], "tempo_ricarica": durata_final}
                    best["col"]["prenotazioni"].append(pren)
                    v["energia_rimanente"] -= best["energia"]
                    v["ricariche"].append({"colonnina": best["col"]["nome"], "inizio": pren["inizio"], "fine": pren["fine"], "energia": pren["energia"]})
                    v["prossimo_inizio_ricarica_disponibile"] = pren["fine"] + MIN_INTERVALLO_RICARICA
                    charged_this_iter.add(v["nome"])
            if not charged_this_iter: break

        energia_interna = sum(v["energia"] - v["energia_rimanente"] for v in veicoli_singoli)
        return {
            "config": config,
            "colonnine": colonnine,
            "veicoli_originali": veicoli,
            "veicoli_singoli": veicoli_singoli,
            "kpi": {
                "energia_totale": energia_totale,
                "energia_interna": energia_interna,
                "energia_esterna": energia_totale - energia_interna,
                "costo_totale": sum((COLONNINE_TAB1[t]["costo_colonnina"] + COLONNINE_TAB1[t]["costo_installazione"]) * q for t, q in config.items()),
                "veicoli_serviti": sum(1 for v in veicoli_singoli if v["energia_rimanente"] < v["energia"])
            }
        }

    def calcola_kpi_avanzati(risultato, costi, alpha=0.5):
        if not risultato: return
        ore_utilizzo = sum(sum(p["tempo_ricarica"] for p in col["prenotazioni"]) for col in risultato["colonnine"])
        energia_erogata = sum(sum(p["energia"] for p in col["prenotazioni"]) for col in risultato["colonnine"])
        energia_massima = sum(col["potenza"] * 24 for col in risultato["colonnine"])
        eff_temporale = ore_utilizzo / (24 * len(risultato["colonnine"])) if risultato["colonnine"] else 0
        eff_energetica = energia_erogata / energia_massima if energia_massima > 0 else 0
        risultato["kpi"].update({
            "efficienza_temporale": eff_temporale,
            "efficienza_energetica": eff_energetica,
            "efficienza_combinata": alpha * eff_temporale + (1 - alpha) * eff_energetica,
            "risparmio_vs_pubblico": risultato["kpi"]["energia_interna"] * (costi["pubblico"] - costi["privato"]),
            "costo_manutenzione_annuale": sum(COLONNINE_TAB1[t]["costo_manutenzione_anno"] * q for t, q in risultato["config"].items())
        })

    def ottimizza_configurazione(veicoli, budget, costi, alpha=0.5, max_power_kw=100, turnazioni_ac=3, turnazioni_dc=8):
        configurazioni = []
        # Bruteforce semplificato per esempio
        for q_ac in range(min(20, floor(budget/3150)) + 1):
            for t_dc in ["DC_20", "DC_30", "DC_50"]:
                cost_dc = COLONNINE_TAB1[t_dc]["costo_colonnina"] + COLONNINE_TAB1[t_dc]["costo_installazione"]
                for q_dc in range(min(5, floor(budget/cost_dc)) + 1):
                    if q_ac == 0 and q_dc == 0: continue
                    cfg = {}
                    if q_ac > 0: cfg["AC_22"] = q_ac
                    if q_dc > 0: cfg[t_dc] = q_dc
                    
                    p_tot = sum(COLONNINE_TAB1[t]["potenza_effettiva"] * q for t,q in cfg.items())
                    c_tot = sum((COLONNINE_TAB1[t]["costo_colonnina"] + COLONNINE_TAB1[t]["costo_installazione"]) * q for t,q in cfg.items())
                    
                    if p_tot <= max_power_kw and c_tot <= budget:
                        configurazioni.append(cfg)

        risultati = []
        for cfg in configurazioni:
            res = simula_ricariche(cfg, veicoli, costi, turnazioni_ac, turnazioni_dc)
            calcola_kpi_avanzati(res, costi, alpha)
            # Punteggio per ordinamento
            internal_pct = res["kpi"]["energia_interna"] / res["kpi"]["energia_totale"] if res["kpi"]["energia_totale"] > 0 else 0
            res["score"] = (-internal_pct, res["kpi"]["costo_totale"])
            risultati.append(res)
        
        risultati.sort(key=lambda x: x["score"])
        return risultati[0] if risultati else None, risultati

    # --- Sidebar Inputs ---
    def input_parametri():
        st.sidebar.header(get_text("sidebar_config_params"))
        budget = st.sidebar.slider(get_text("budget_available"), 5000, 200000, 30000, 500)
        max_p = st.sidebar.slider(get_text("max_power_kw"), 10, 500, 100, 10)
        alpha = st.sidebar.slider(get_text("alpha_weight"), 0.0, 1.0, 0.5, 0.1)
        t_ac = st.sidebar.slider(get_text("ac_turns"), 1, 10, 3)
        t_dc = st.sidebar.slider(get_text("dc_turns"), 1, 20, 8)
        c_priv = st.sidebar.number_input(get_text("private_charge_cost"), 0.1, 0.5, 0.25)
        c_pub = st.sidebar.number_input(get_text("public_charge_cost"), 0.3, 1.0, 0.55)
        return {"budget": budget, "max_power_kw": max_p, "alpha": alpha, "turnazioni_ac": t_ac, "turnazioni_dc": t_dc, "costo_privato": c_priv, "costo_pubblico": c_pub}

    def input_veicoli():
        st.sidebar.header(get_text("vehicle_config"))
        mode = st.sidebar.radio(get_text("input_mode"), [get_text("single_vehicles"), get_text("vehicle_groups")])
        veicoli = []
        if mode == get_text("single_vehicles"):
            n = st.sidebar.number_input(get_text("num_single_vehicles"), 1, 50, 3)
            for i in range(n):
                with st.sidebar.expander(get_text("single_vehicle").format(i=i+1)):
                    nome = st.text_input(get_text("vehicle_name").format(i=i+1), f"V_{i+1}")
                    km = st.number_input(get_text("daily_km"), 10, 500, 100, key=f"km_{i}")
                    cons = st.number_input(get_text("consumption_kwh_km"), 0.1, 0.5, 0.18, key=f"c_{i}")
                    start = st.number_input(get_text("stop_start_time"), 0.0, 23.0, 18.0, key=f"s_{i}")
                    end = st.number_input(get_text("stop_end_time"), 0.0, 24.0, 8.0, key=f"e_{i}")
                    veicoli.append({"nome": nome, "km": km, "consumo": cons, "energia": km*cons, "inizio": start, "fine": end if end > start else end + 24, "gruppo": False})
        else:
            n_g = st.sidebar.number_input(get_text("num_vehicle_groups"), 1, 10, 1)
            for i in range(n_g):
                with st.sidebar.expander(get_text("group_name").format(i=i+1)):
                    nome = st.text_input(get_text("group_name").format(i=i+1), f"G_{i+1}")
                    q = st.number_input(get_text("group_quantity"), 1, 100, 5, key=f"q_g{i}")
                    km = st.number_input(get_text("group_daily_km"), 10, 500, 80, key=f"km_g{i}")
                    cons = st.number_input(get_text("group_consumption"), 0.1, 0.5, 0.2, key=f"c_g{i}")
                    start = st.number_input(get_text("group_stop_start"), 0.0, 23.0, 19.0, key=f"s_g{i}")
                    end = st.number_input(get_text("group_stop_end"), 0.0, 24.0, 7.0, key=f"e_g{i}")
                    veicoli.append({"nome": nome, "quantita": q, "km": km, "consumo": cons, "energia": km*cons, "inizio": start, "fine": end if end > start else end + 24, "gruppo": True})
        return veicoli

    # --- Main Logic ---
    params = input_parametri()
    veicoli = input_veicoli()

    if st.button(get_text("calculate_optimization")):
        with st.spinner(get_text("analysis_in_progress")):
            best, all_res = ottimizza_configurazione(veicoli, params["budget"], {"privato": params["costo_privato"], "pubblico": params["costo_pubblico"]}, params["alpha"], params["max_power_kw"], params["turnazioni_ac"], params["turnazioni_dc"])
            st.session_state.risultati_ottimizzazione = all_res
            st.session_state.selected_config_index = 0

    if st.session_state.get("risultati_ottimizzazione"):
        res_list = st.session_state.risultati_ottimizzazione
        
        # --- Punto 2: Selettore Dinamico ---
        st.subheader(get_text("optimization_results"))
        options = [f"Soluzione {i+1}: " + " + ".join(f"{q}x{t}" for t,q in r["config"].items()) for i, r in enumerate(res_list)]
        
        selection = st.selectbox(
            get_text("current_config_display"),
            range(len(options)),
            format_func=lambda x: options[x],
            index=st.session_state.selected_config_index,
            key="active_selector"
        )
        st.session_state.selected_config_index = selection
        current = res_list[selection]

        # --- Punto 1: KPI con Card Grafiche ---
        st.markdown(f"### {get_text('selected_solution')}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(get_text("total_initial_cost"), f"€{current['kpi']['costo_totale']:,.0f}", get_text("budget_percentage").format(percent=current['kpi']['costo_totale']/params['budget']*100))
        c2.metric(get_text("internal_energy_charged"), f"{current['kpi']['energia_interna']:,.1f} kWh", get_text("total_request_percentage").format(percent=current['kpi']['energia_interna']/current['kpi']['energia_totale']*100))
        c3.metric(get_text("estimated_annual_savings"), f"€{current['kpi']['risparmio_vs_pubblico']*365:,.0f}")
        c4.metric(get_text("combined_efficiency"), f"{current['kpi']['efficienza_combinata']*100:.1f}%")

        # Tabs Dettaglio
        t1, t2, t3 = st.tabs([get_text("detailed_planning_tab"), get_text("vehicle_summary_tab"), get_text("all_configs_tab")])
        
        with t1:
            # Gantt
            g_data = []
            for col in current["colonnine"]:
                for p in col["prenotazioni"]:
                    g_data.append({
                        "Task": col["nome"],
                        "Start": datetime(2025,1,1) + timedelta(hours=p["inizio"]),
                        "Finish": datetime(2025,1,1) + timedelta(hours=p["fine"]),
                        "Vehicle": p["veicolo"],
                        "Energy": f"{p['energy']:.1f} kWh"
                    })
            if g_data:
                df_g = pd.DataFrame(g_data)
                fig = px.timeline(df_g, x_start="Start", x_end="Finish", y="Task", color="Vehicle", title=get_text("gantt_chart_title"), template="plotly_white")
                fig.update_xaxes(tickformat="%H:%M")
                st.plotly_chart(fig, use_container_width=True)
        
        with t2:
            rows = []
            for v in current["veicoli_singoli"]:
                rows.append({
                    "Name": v["nome"],
                    "Requested": f"{v['energia']:.1f}",
                    "Charged": f"{v['energia']-v['energia_rimanente']:.1f}",
                    "Status": "✅" if v["energia_rimanente"] < 0.1 else "⚠️"
                })
            st.table(pd.DataFrame(rows))
            
        with t3:
            comp = []
            for r in res_list:
                comp.append({
                    "Config": str(r["config"]),
                    "Cost": f"€{r['kpi']['costo_totale']}",
                    "Coverage": f"{r['kpi']['energia_interna']/r['kpi']['energia_totale']*100:.1f}%"
                })
            st.dataframe(pd.DataFrame(comp), use_container_width=True)

st.markdown("---")
st.markdown(f"<div style='text-align:center; color:gray; font-size:12px;'>{get_text('footer_text')}</div>", unsafe_allow_html=True)
