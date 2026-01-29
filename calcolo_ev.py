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
    # prende il valore tabellato più vicino verso il basso, default 50°C se >50
    keys = sorted(FATT_TEMP.keys())
    sel = max([t for t in keys if t <= temp_amb], default=50)
    return FATT_TEMP.get(sel, 0.71)


def _fattore_raggr(n_linee: int) -> float:
    if n_linee in FATT_RAGGR:
        return FATT_RAGGR[n_linee]
    # oltre 3 linee: imposto cautelativo
    return 0.70


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
        raise ValueError("IΔn ammessa tipica: 30/100/300 mA (imposta un valore standard).")

    trifase = "trifase" in alimentazione.lower()
    tensione = 400 if trifase else 230

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
    # CEI 64-8 Parte 5-52 (portate e derating)
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
        raise ValueError("Nessuna sezione soddisfa contemporaneamente ΔV≤4% e Ib ≤ In ≤ Iz (con derating).")

    # ---------------------------
    # Check Icn vs Icc (semplificato)
    # ---------------------------
    # Nota: qui non scegliamo un interruttore specifico (marca/modello),
    # ma diamo un'indicazione: se Icc > 6kA, richiedere Icn superiore.
    if icc_ka <= 6:
        icn_note = "Icn minimo 6 kA (verifica puntuale con dati di fornitura)."
    elif icc_ka <= 10:
        icn_note = "Richiedere interruttore con Icn ≥ 10 kA."
    else:
        icn_note = "Richiedere interruttore con Icn adeguato (≥ Icc presunta)."

    # ---------------------------
    # CHECK-LIST 722 (Warning / Non conformità)
    # ---------------------------
    warning_722 = []
    nonconf_722 = []
    ok_722 = []

    # Circuito dedicato per punto di ricarica: qui è assunto vero (stai dimensionando la linea dedicata)
    ok_722.append("Circuito dedicato per punto di ricarica (linea dedicata dimensionata).")

    # fattore di utilizzazione/contemporaneità (nota progettuale)
    if not gestione_carichi and n_linee > 1:
        warning_722.append("Più punti/linee senza gestione carichi: assumere contemporaneità = 1 (verificare potenza disponibile).")
    else:
        ok_722.append("Gestione carichi/contemporaneità: impostata o non necessaria.")

    # differenziale: almeno Tipo A, IΔn ≤ 30 mA per punto (prassi 722)
    if rcd_idn_ma > 30:
        nonconf_722.append("Protezione differenziale: per punto EV è richiesto IΔn ≤ 30 mA (impostato valore superiore).")
    else:
        ok_722.append("Differenziale per punto: IΔn ≤ 30 mA.")

    # DC fault protection (Modo 3 tipicamente): Tipo B o A + 6 mA DC (se non integrato nell’EVSE)
    if modo_ricarica.strip().lower() == "modo 3":
        if ("tipo b" not in rcd_tipo.lower()) and ("6ma" not in rcd_tipo.lower()):
            nonconf_722.append("Modo 3: richiesto RCD Tipo B oppure Tipo A + rilevazione 6 mA DC (se non integrata nell’EVSE).")
        else:
            ok_722.append("Protezione guasti DC coerente (Tipo B o A+6mA DC).")

    # Modo 1/2 con presa domestica: limitazioni d’uso (occasionali) e corrente tipica 16A
    if modo_ricarica.strip().lower() in ("modo 1", "modo 2") and tipo_punto == "Presa domestica":
        if In > 16:
            nonconf_722.append("Modo 1/2 con presa domestica: corrente > 16 A non ammessa per presa domestica (adeguare).")
        else:
            warning_722.append("Modo 1/2 con presa domestica: usare solo per ricariche occasionali e con componenti idonei.")

    # SPD raccomandato (nota pratica)
    if not spd_previsto:
        warning_722.append("SPD non previsto: per EV è fortemente raccomandato valutare protezione da sovratensioni.")
    else:
        ok_722.append("SPD previsto/valutato (raccomandato per protezione EVSE/veicolo).")

    # installazione esterna: IP/IK
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
    # TESTI DOCUMENTALI (Relazione, Unifilare, Planimetria)
    # ---------------------------

    riferimenti_normativi = dedent("""
    RIFERIMENTI NORMATIVI E LEGISLATIVI
    - Legge 186/68: regola dell’arte.
    - D.M. 37/08: realizzazione impianti all’interno degli edifici (ove applicabile).
    - CEI 64-8: Impianti elettrici utilizzatori in bassa tensione:
      • Parte 4-41: Protezione contro i contatti elettrici (contatti diretti/indiretti).
      • Parte 4-43: Protezione contro le sovracorrenti (sovraccarico/cortocircuito).
      • Parte 5-52: Scelta e messa in opera delle condutture.
      • Parte 5-53: Apparecchi di manovra e protezione.
      • Parte 5-54: Impianti di terra, conduttori di protezione ed equipotenzialità.
      • Parte 7-722: Alimentazione dei veicoli elettrici (prescrizioni specifiche EV).
    - IEC/CEI EN 61851-1: sistemi di ricarica conduttiva dei veicoli elettrici.
    - CEI EN 62305 / CEI 81-10: protezione contro i fulmini (valutazione SPD “quando applicabile”).
    """).strip()

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
    Installazione esterna: {"Sì" if esterno else "No"} (IP{ip_rating} / IK{ik_rating})
    Altezza punto di connessione: {altezza_presa_m:.2f} m

    {riferimenti_normativi}

    DESCRIZIONE DELL’INTERVENTO
    L’intervento prevede l’installazione di una stazione di ricarica per veicoli elettrici (EVSE)
    di potenza nominale {potenza_kw:.1f} kW, alimentata mediante linea dedicata dal quadro elettrico.

    CRITERI DI PROGETTO (CEI 64-8)
    - Caduta di tensione di progetto: ΔV ≤ 4% (CEI 64-8 §525).
    - Verifica sovraccarico: Ib ≤ In ≤ Iz (CEI 64-8 §433).
    - Portate cavo: tabella semplificata riferita a condizioni standard; applicati fattori correttivi:
      • Temperatura ambiente {temp_amb} °C → kT={k_temp:.2f}
      • Raggruppamento linee n={n_linee} → kG={k_ragg:.2f}
    - Cavo previsto: FG16(O)R16 0,6/1 kV (rame).

    DIMENSIONAMENTO LINEA
    - Tensione nominale: {tensione} V
    - cosφ di progetto: {cosphi:.2f}
    - Lunghezza linea: {distanza_m:.1f} m
    - Corrente di impiego: Ib = {Ib:.2f} A
    - Protezione magnetotermica: In = {In} A (curva C)
    - Sezione conduttori di fase: {sezione} mm²
    - Portata base (condizioni standard): Iz_base = {Iz_base_sel} A
    - Portata corretta (derating): Iz = {Iz_corr:.1f} A
    - Verifica CEI 64-8 §433: Ib ≤ In ≤ Iz → {("OK" if (Ib <= In <= Iz_corr) else "NON OK")}

    PROTEZIONI
    - Sovracorrenti: interruttore magnetotermico dedicato alla linea EV.
    - Cortocircuito: Icc presunta al punto di installazione = {icc_ka:.1f} kA → {icn_note}
    - Differenziale: {rcd_tipo}, IΔn = {rcd_idn_ma} mA.
      Per ricarica EV è richiesta protezione differenziale per punto con IΔn ≤ 30 mA e,
      per il Modo 3, protezione contro guasti DC (Tipo B o Tipo A con 6 mA DC se non integrato nell’EVSE).
    - SPD: {"Previsto/valutato" if spd_previsto else "Non previsto"} (raccomandato valutare in base a rischio e impianto).

    PRESCRIZIONI SPECIFICHE CEI 64-8/7 – SEZIONE 722 (CHECK-LIST)
    Esiti OK:
    {("- " + "\\n- ".join(ok_722)) if ok_722 else "- (nessuno)"}

    Warning:
    {("- " + "\\n- ".join(warning_722)) if warning_722 else "- (nessuno)"}

    Non conformità:
    {("- " + "\\n- ".join(nonconf_722)) if nonconf_722 else "- (nessuna)"}

    NOTE FINALI
    Le verifiche svolte costituiscono un pre-dimensionamento coerente con CEI 64-8.
    La scelta finale dei dispositivi (MT/Idn/Icn, SPD, IP/IK) deve essere confermata con:
    - dati di corto circuito del punto di installazione,
    - documentazione tecnica dell’EVSE (presenza RDC-DD 6 mA DC integrata),
    - condizioni reali di posa (temperatura, raggruppamenti, percorsi, ambienti).
    """).strip()

    unifilare = dedent(f"""
    DATI PER SCHEMA UNIFILARE – LINEA EV (CEI 64-8 / 722)
    =====================================================

    QUADRO DI ORIGINE → LINEA DEDICATA EVSE → EVSE

    1) Protezione di linea (dedicata):
       - Interruttore magnetotermico: In = {In} A, curva C, poli: {"4P" if trifase else "2P"}
       - Potere di interruzione (Icn): {icn_note}
       - Coordinamento sovraccarico: Ib={Ib:.2f} A ≤ In={In} A ≤ Iz={Iz_corr:.1f} A (OK)

    2) Protezione differenziale (per punto di ricarica – CEI 64-8/7-722):
       - Tipo: {rcd_tipo}
       - Sensibilità: IΔn = {rcd_idn_ma} mA
       - Nota DC: per Modo 3 richiesto Tipo B oppure Tipo A + rilevazione 6 mA DC (se non integrata nell’EVSE)

    3) Linea di alimentazione:
       - Cavo: FG16(O)R16 0,6/1 kV (rame)
       - Sezione fase: {sezione} mm²
       - Posa: {tipo_posa}
       - Lunghezza: {distanza_m:.1f} m
       - Caduta di tensione: ΔV ≤ 4% (criterio di progetto)

    4) SPD:
       - {"Previsto/valutato" if spd_previsto else "Non previsto"} (valutare secondo rischio e impianto)

    5) Carico:
       - EVSE {potenza_kw:.1f} kW, {alimentazione}, {modo_ricarica}
    """).strip()

    planimetria = dedent(f"""
    NOTE PLANIMETRIA – PERCORSO LINEA EV
    ===================================

    Ubicazione: {indirizzo}
    Linea dedicata dal quadro elettrico al punto EVSE.
    Lunghezza stimata: {distanza_m:.1f} m
    Modalità di posa: {tipo_posa}

    Prescrizioni:
    - Se posa interrata:
      • cavidotto corrugato doppia parete Ø 80 mm (o adeguato), profondità minima ~0,8 m;
      • segnalazione con nastro; pozzetti/ispezioni ai cambi di direzione.
    - Se posa a vista:
      • canalina metallica/tubazione protettiva idonea all’ambiente; fissaggi adeguati.

    Installazione esterna: {"Sì" if esterno else "No"}
    - Requisiti consigliati: IP ≥ 44; protezione meccanica (IK) adeguata; protezione urti/urti accidentali.
    Altezza punto di connessione: {altezza_presa_m:.2f} m (raccomandato 0,5–1,5 m).
    """).strip()

    return {
        # risultati numerici
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
    }
