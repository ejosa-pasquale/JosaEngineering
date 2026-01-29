import math
from textwrap import dedent

# =========================
# TABELLE (SEMPLIFICATE)
# =========================

SEZIONI = [6, 10, 16, 25, 35, 50, 70, 95]
INTERRUTTORI = [16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160]

# Portate di base Iz per FG16(O)R16 in condizioni standard (semplificate)
PORTATA_BASE = {
    "Interrata": {6: 34, 10: 46, 16: 61, 25: 80, 35: 99, 50: 119, 70: 151, 95: 182},
    "A vista":   {6: 41, 10: 57, 16: 76, 25: 101, 35: 125, 50: 150, 70: 192, 95: 232},
}

# Fattori correttivi temperatura (semplificati)
FATT_TEMP = {30: 1.00, 35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71}

# Fattori correttivi raggruppamento (semplificati)
FATT_RAGGR = {1: 1.00, 2: 0.80, 3: 0.70}


def _fattore_temp(temp_amb: int) -> float:
    keys = sorted(FATT_TEMP.keys())
    sel = max([t for t in keys if t <= temp_amb], default=50)
    return FATT_TEMP.get(sel, 0.71)


def _fattore_raggr(n_linee: int) -> float:
    if n_linee in FATT_RAGGR:
        return FATT_RAGGR[n_linee]
    return 0.70  # cautelativo oltre 3 linee


def genera_progetto_ev(
    # anagrafica
    nome: str,
    cognome: str,
    indirizzo: str,
    # dati elettrici
    potenza_kw: float,
    distanza_m: float,
    alimentazione: str,   # "Monofase 230 V" / "Trifase 400 V"
    tipo_posa: str,       # "Interrata" / "A vista"
    # parametri progetto
    sistema: str = "TT",
    cosphi: float = 0.95,
    temp_amb: int = 30,
    n_linee: int = 1,
    icc_ka: float = 6.0,
    # EV / 722
    modo_ricarica: str = "Modo 3",
    tipo_punto: str = "Connettore EV",        # "Connettore EV" / "Presa domestica" / "Presa industriale"
    esterno: bool = False,
    ip_rating: int = 44,
    ik_rating: int = 7,
    altezza_presa_m: float = 1.0,
    spd_previsto: bool = True,
    gestione_carichi: bool = False,
    # differenziale
    rcd_tipo: str = "Tipo A + RDC-DD 6mA DC",
    rcd_idn_ma: int = 30
):
    """
    Pre-dimensionamento linea EV con criteri CEI 64-8:
    - Ib, scelta In, verifica Ib ≤ In ≤ Iz (con derating)
    - sezione per caduta di tensione (limite 4%)
    - check-list prescrizioni Sez. 722 (warning/non conformità)
    - testi: Relazione, Unifilare (testo), Planimetria (testo)
    """

    # ---------------------------
    # CONTROLLI INPUT
    # ---------------------------
    if potenza_kw <= 0 or distanza_m <= 0:
        raise ValueError("Potenza e distanza devono essere > 0.")
    if tipo_posa not in PORTATA_BASE:
        raise ValueError(f"Tipo posa non gestito: {tipo_posa}")
    if rcd_idn_ma not in (30, 100, 300):
        raise ValueError("IΔn tipica: 30/100/300 mA (imposta un valore standard).")

    trifase = "trifase" in alimentazione.lower()
    tensione = 400 if trifase else 230

    # ---------------------------
    # LIMITE MONOFASE 7,4 kW
    # ---------------------------
    if (not trifase) and (potenza_kw > 7.4):
        raise ValueError("In monofase la potenza massima ammessa è 7,4 kW. Seleziona trifase o riduci la potenza.")

    # ---------------------------
    # Ib
    # ---------------------------
    if trifase:
        Ib = (potenza_kw * 1000) / (math.sqrt(3) * tensione * cosphi)
    else:
        Ib = (potenza_kw * 1000) / (tensione * cosphi)

    # ---------------------------
    # In
    # ---------------------------
    In = next((i for i in INTERRUTTORI if i >= Ib), None)
    if In is None:
        raise ValueError("Ib troppo elevata: nessuna taglia interruttore disponibile in tabella.")

    # ---------------------------
    # Sezione per caduta di tensione (ΔV ≤ 4%)
    # CEI 64-8 §525 (criterio di progetto)
    # modello semplificato resistivo rame
    # ---------------------------
    cond_rame = 56  # m/(Ω·mm²)
    dv_max = tensione * 0.04

    if trifase:
        S_cad = (math.sqrt(3) * distanza_m * Ib * cosphi) / (cond_rame * dv_max)
    else:
        S_cad = (2 * distanza_m * Ib * cosphi) / (cond_rame * dv_max)

    # ---------------------------
    # Iz con fattori correttivi (temp + raggruppamento)
    # ---------------------------
    k_temp = _fattore_temp(temp_amb)
    k_ragg = _fattore_raggr(n_linee)

    sezione = None
    Iz_corr = None
    Iz_base_sel = None

    for S in SEZIONI:
        if S < S_cad:
            continue

        Iz_base = PORTATA_BASE[tipo_posa].get(S)
        if not Iz_base:
            continue

        Iz = Iz_base * k_temp * k_ragg

        # CEI 64-8 §433: Ib ≤ In ≤ Iz
        if Ib <= In <= Iz:
            sezione = S
            Iz_corr = Iz
            Iz_base_sel = Iz_base
            break

    if sezione is None:
        raise ValueError("Nessuna sezione soddisfa ΔV≤4% e Ib ≤ In ≤ Iz (con derating).")

    # ---------------------------
    # Check Icn vs Icc (semplificato)
    # ---------------------------
    if icc_ka <= 6:
        icn_note = "Icn minimo 6 kA (verifica puntuale con dati di fornitura)."
    elif icc_ka <= 10:
        icn_note = "Richiedere interruttore con Icn ≥ 10 kA."
    else:
        icn_note = "Richiedere interruttore con Icn adeguato (≥ Icc presunta)."

    # ---------------------------
    # CHECK-LIST 722 (pulita e coerente al caso)
    # ---------------------------
    warning_722 = []
    nonconf_722 = []
    ok_722 = []

    modo_norm = modo_ricarica.strip().lower()
    evse_dc = (modo_norm == "modo 4")

    # circuito dedicato: assunto vero (stai dimensionando una linea dedicata)
    ok_722.append("Circuito dedicato per punto di ricarica (linea dedicata dimensionata).")

    # contemporaneità/gestione carichi: solo se più linee/punti
    if n_linee > 1:
        if gestione_carichi:
            ok_722.append("Gestione carichi/contemporaneità: prevista.")
        else:
            warning_722.append("Più linee/punti senza gestione carichi: assumere contemporaneità = 1 e verificare potenza disponibile.")
    else:
        ok_722.append("Singola linea/punto: contemporaneità non critica.")

    # differenziale per punto: IΔn <= 30 mA (qui la rendiamo stringente)
    if rcd_idn_ma > 30:
        nonconf_722.append("Protezione differenziale per punto: richiesto IΔn ≤ 30 mA (impostato valore superiore).")
    else:
        ok_722.append("Differenziale per punto: IΔn ≤ 30 mA.")

    # DC fault protection: SOLO per Modo 3 (AC)
    if modo_norm == "modo 3":
        if ("tipo b" not in rcd_tipo.lower()) and ("6ma" not in rcd_tipo.lower()):
            nonconf_722.append("Modo 3: richiesto RCD Tipo B oppure Tipo A + rilevazione 6 mA DC (se non integrata nell’EVSE).")
        else:
            ok_722.append("Protezione guasti DC coerente (Tipo B o A+6mA DC).")

    # Modo 1/2 con presa domestica: limiti/prassi
    if modo_norm in ("modo 1", "modo 2") and tipo_punto == "Presa domestica":
        if In > 16:
            nonconf_722.append("Modo 1/2 con presa domestica: corrente > 16 A non ammessa per presa domestica (adeguare).")
        else:
            warning_722.append("Modo 1/2 con presa domestica: raccomandato solo per ricariche occasionali e con componenti idonei.")

    # SPD: nota solo se pertinente (qui: warning se assente)
    if not spd_previsto:
        warning_722.append("SPD non previsto: valutare protezione da sovratensioni in base a rischio e impianto.")
    else:
        ok_722.append("SPD previsto/valutato.")

    # esterno: IP/IK solo se esterno
    if esterno:
        if ip_rating < 44:
            nonconf_722.append("Installazione esterna: richiesto grado di protezione almeno IP44.")
        else:
            ok_722.append(f"Installazione esterna: IP{ip_rating} conforme (≥ IP44).")

        if ik_rating < 7:
            warning_722.append("Installazione esterna/pubblica: valutare protezione meccanica (raccomandato IK07 o misure equivalenti).")
        else:
            ok_722.append(f"Protezione meccanica: IK{ik_rating} adeguato (≥ IK07).")

    # altezza raccomandata
    if not (0.5 <= altezza_presa_m <= 1.5):
        warning_722.append("Altezza punto di connessione fuori intervallo raccomandato 0,5–1,5 m.")
    else:
        ok_722.append("Altezza punto di connessione in intervallo raccomandato (0,5–1,5 m).")

    # ---------------------------
    # TESTI DOCUMENTALI PULITI (solo note pertinenti)
    # ---------------------------

    # Nota DC fault: SOLO per Modo 3 (AC)
    nota_dc_fault = ""
    if modo_norm == "modo 3":
        nota_dc_fault = (
            "Nota (CEI 64-8/7-722): per il Modo 3 è richiesta protezione contro guasti in DC "
            "(RCD Tipo B oppure Tipo A + rilevazione 6 mA DC se non integrata nell’EVSE)."
        )

    # Nota prese domestiche: SOLO se Modo 1/2 + presa domestica
    nota_presa_dom = ""
    if modo_norm in ("modo 1", "modo 2") and tipo_punto == "Presa domestica":
        nota_presa_dom = "Nota: Modo 1/2 con presa domestica raccomandato solo per ricariche occasionali con componenti idonei."

    # Nota SPD: pulita
    nota_spd = "SPD previsto/valutato." if spd_previsto else "SPD non previsto: valutare protezione da sovratensioni in base a rischio e impianto."

    # Riferimenti normativi: essenziali + SPD solo se previsto/valutato
    riferimenti_normativi = dedent("""
    RIFERIMENTI NORMATIVI E LEGISLATIVI
    - Legge 186/68: regola dell’arte.
    - D.M. 37/08: realizzazione impianti all’interno degli edifici (ove applicabile).
    - CEI 64-8: impianti elettrici utilizzatori in BT:
      • Parte 4-41: protezione contro i contatti elettrici.
      • Parte 4-43: protezione contro le sovracorrenti.
      • Parte 5-52: condutture (scelta e posa).
      • Parte 5-53: apparecchi di manovra e protezione.
      • Parte 5-54: impianti di terra ed equipotenzialità.
      • Parte 7-722: alimentazione dei veicoli elettrici.
    - IEC/CEI EN 61851-1: sistemi di ricarica conduttiva dei veicoli elettrici.
    """).strip()
    if spd_previsto:
        riferimenti_normativi += "\n- CEI EN 62305 / CEI 81-10: valutazione protezione contro sovratensioni (quando applicabile)."

    relazione = dedent(f"""
    RELAZIONE TECNICA – INFRASTRUTTURA DI RICARICA VEICOLI ELETTRICI
    ===============================================================

    DATI GENERALI
    Committente: {nome} {cognome}
    Ubicazione: {indirizzo}
    Sistema di distribuzione: {sistema}
    Alimentazione EVSE: {alimentazione}
    Modo di ricarica: {modo_ricarica}
    Punto di connessione: {tipo_punto}
    Installazione esterna: {"Sì" if esterno else "No"}{f" (IP{ip_rating}/IK{ik_rating})" if esterno else ""}
    Altezza punto di connessione: {altezza_presa_m:.2f} m

    {riferimenti_normativi}

    DESCRIZIONE DELL’INTERVENTO
    Installazione di EVSE di potenza nominale {potenza_kw:.1f} kW alimentata tramite linea dedicata dal quadro elettrico.

    CRITERI DI PROGETTO (CEI 64-8)
    - Caduta di tensione di progetto: ΔV ≤ 4% (CEI 64-8 §525).
    - Verifica sovraccarico: Ib ≤ In ≤ Iz (CEI 64-8 §433).
    - Portate cavo: condizioni standard con fattori correttivi:
      • Temperatura {temp_amb} °C → kT={k_temp:.2f}
      • Raggruppamento n={n_linee} → kG={k_ragg:.2f}
    - Cavo: FG16(O)R16 0,6/1 kV (rame).

    DIMENSIONAMENTO LINEA
    - Tensione: {tensione} V
    - cosφ: {cosphi:.2f}
    - Lunghezza: {distanza_m:.1f} m
    - Ib = {Ib:.2f} A
    - In = {In} A (curva C)
    - Sezione fase: {sezione} mm²
    - Iz_base = {Iz_base_sel} A | Iz_corr = {Iz_corr:.1f} A
    - Verifica Ib ≤ In ≤ Iz: {"OK" if (Ib <= In <= Iz_corr) else "NON OK"}

    PROTEZIONI
    - Sovracorrenti: interruttore MT dedicato alla linea EV.
    - Cortocircuito: Icc presunta = {icc_ka:.1f} kA → {icn_note}
    - Differenziale: {rcd_tipo}, IΔn = {rcd_idn_ma} mA.
    {nota_dc_fault if nota_dc_fault else ""}
    {nota_spd}

    PRESCRIZIONI CEI 64-8/7 – SEZIONE 722 (CHECK-LIST)
    Esiti OK:
    {("- " + "\\n- ".join(ok_722)) if ok_722 else "- (nessuno)"}

    Warning:
    {("- " + "\\n- ".join(warning_722)) if warning_722 else "- (nessuno)"}

    Non conformità:
    {("- " + "\\n- ".join(nonconf_722)) if nonconf_722 else "- (nessuna)"}

    {nota_presa_dom if nota_presa_dom else ""}

    NOTE FINALI
    Le verifiche costituiscono pre-dimensionamento coerente con CEI 64-8. La scelta finale dispositivi va confermata con dati reali e schede EVSE.
    """).strip()

    unifilare = dedent(f"""
    DATI PER SCHEMA UNIFILARE – LINEA EV
    ===================================

    QUADRO → LINEA DEDICATA EVSE → EVSE

    1) Protezione di linea:
       - Magnetotermico: In = {In} A, curva C, poli: {"4P" if trifase else "2P"}
       - Potere interruzione: {icn_note}
       - Verifica: Ib={Ib:.2f} A ≤ In={In} A ≤ Iz={Iz_corr:.1f} A (OK)

    2) Differenziale per punto:
       - Tipo: {rcd_tipo}
       - IΔn: {rcd_idn_ma} mA
    {("   - " + nota_dc_fault) if nota_dc_fault else ""}

    3) Linea:
       - Cavo: FG16(O)R16 0,6/1 kV (rame)
       - Sezione fase: {sezione} mm²
       - Posa: {tipo_posa}
       - Lunghezza: {distanza_m:.1f} m
       - Caduta di tensione: ΔV ≤ 4% (criterio di progetto)

    4) SPD:
       - {"Previsto/valutato" if spd_previsto else "Non previsto"}

    5) Carico:
       - EVSE {potenza_kw:.1f} kW, {alimentazione}, {modo_ricarica}
    """).strip()

    planimetria = dedent(f"""
    NOTE PLANIMETRIA – PERCORSO LINEA EV
    ===================================

    Ubicazione: {indirizzo}
    Linea dedicata dal quadro al punto EVSE.
    Lunghezza: {distanza_m:.1f} m
    Posa: {tipo_posa}

    - Interrata: cavidotto idoneo, profondità ~0,8 m, nastro segnalazione, pozzetti ai cambi direzione.
    - A vista: canalina/tubazione idonea, fissaggi adeguati.

    Installazione esterna: {"Sì" if esterno else "No"}
    {(f"- Requisiti: IP≥44 (IP{ip_rating}) e protezione meccanica adeguata (IK{ik_rating})." if esterno else "")}
    Altezza punto di connessione: {altezza_presa_m:.2f} m (raccomandato 0,5–1,5 m).
    """).strip()

    return {
        # numeri
        "tensione_v": tensione,
        "Ib_a": round(Ib, 2),
        "In_a": In,
        "Iz_a": round(Iz_corr, 1),
        "sezione_mm2": sezione,
        "S_cad_min_mm2": round(S_cad, 2),
        "k_temp": round(k_temp, 2),
        "k_ragg": round(k_ragg, 2),
        # testi
        "relazione": relazione,
        "unifilare": unifilare,
        "planimetria": planimetria,
        # 722
        "ok_722": ok_722,
        "warning_722": warning_722,
        "nonconf_722": nonconf_722,
        # utili
        "trifase": trifase,
        "modo_dc": evse_dc,
    }
