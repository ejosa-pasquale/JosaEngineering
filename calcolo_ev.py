import math
from textwrap import dedent


def genera_relazione_tecnica(d: dict, riferimenti_normativi: str = "") -> str:
    """Genera la relazione tecnica (testo) con sezioni descrittive + normative."""
    from textwrap import dedent
    return dedent(f"""
    RELAZIONE TECNICA – INFRASTRUTTURA DI RICARICA VEICOLI ELETTRICI
    ===============================================================

    DATI GENERALI
    Committente: {d['nome']} {d['cognome']}
    Ubicazione: {d['indirizzo']}
    Sistema di distribuzione: {d.get('sistema','TT')}
    N. Wallbox: {d.get('n_wallbox',1)}
    Potenza nominale wallbox: {d.get('potenza_kw',0):.1f} kW
    Modo di ricarica: {d.get('modo_ricarica','Modo 3')}

    {riferimenti_normativi}

    1. PREMESSA
    Il progetto a cui fa riferimento il presente documento è relativo alla realizzazione degli impianti elettrici necessari per connettere n. {d.get('n_wallbox',1)} wallbox di ricarica per veicoli elettrici da ubicare presso il box auto sito in {d['indirizzo']}, vista l’intenzione del {d['nome']} {d['cognome']} di dotare il proprio ricovero auto di una postazione di ricarica.
    Nel presente progetto si è naturalmente tenuto conto della destinazione d’uso sia degli spazi già disponibili, valutando la configurazione degli stessi e sia degli ingombri delle apparecchiature che dovranno essere utilizzati.

    2. OPERE IMPIANTISTICHE PREVISTE
    Le opere impiantistiche che si prevede di realizzare sono esclusivamente legate all’installazione della sola Wallbox di ricarica veicoli elettrici, che verrà alimentata da una fornitura e relativo quadro elettrico dedicato all’utenza atta a ricaricare il veicolo elettrico; tramite tubazioni esistenti verrà derivato dallo stesso verso il parcheggio sito in {d['indirizzo']}.

    3. DISTRIBUZIONE ELETTRICA
    La colonnina di ricarica da {d.get('potenza_kw',0):.1f} kW sarà alimentata in bassa tensione (BT) prelevando l’energia dal punto di consegna dell’ente distributore dell’Energia (e-distribuzione) esistente che è in BT.

    3.1 DESCRIZIONE QUADRI E DISTRIBUZIONE IN B.T.
    La distribuzione in B.T. avverrà partendo dal locale contatori tramite un nuovo quadretto atto a proteggere la linea che alimenta la futura wallbox (QE Generale). Il locale tecnico che ospita tutti i contatori del complesso vedrà la presenza di un ulteriore gruppo di misura oltre che il nuovo interruttore atto ad alimentare la colonnina di ricarica posta al piano seminterrato nel rispettivo parcheggio auto. Nella progettazione dei quadri, particolare cura è stata posta sia al fine di garantire la massima selettività possibile, in caso di cortocircuito, tra gli interruttori posti a valle e quelli posti a monte, sia al fine di garantire la distinzione fisica dei vari moduli dei quadri e delle relative linee in uscita dagli stessi.

    3.1.1 QUADRO GENERALE
    Lo schema unifilare e la relativa carpenteria sono riportati negli elaborati grafici allegati. Esso è conforme alle norme CEI 17-13/1, CEI 17-113, CEI 17-114, CEI EN 61439-1, CEI EN 61439-2 per le apparecchiature costruite in fabbrica.
    La distribuzione dal quadro generale ai quadri posti ad esso in cascata avviene mediante cavi multipolari FG16OM16, della sezione indicata negli elaborati progettuali, posati in tubo. Per la linea partente dal quadro si distribuisce anche il conduttore di protezione (FS17 giallo verde) dimensionato secondo CEI 64-8.

    3.1.2 DISTRIBUZIONE ELETTRICA DI ZONA
    La distribuzione alle varie zone avviene attraverso tubazione in PVC; si precisa che il ricovero auto è alimentato con una tubazione indipendente. Il collegamento al quadro immediatamente a monte sarà effettuato sempre con cavi multipolari del tipo FG16OM16, come anche il collegamento da quadri a singole utenze, quali appunto la colonnina.

    4. SICUREZZA ELETTRICA COLONNINE DI RICARICA
    L’impianto è conforme alla Circolare 05 novembre 2018, n. 2 (VVF) “Linee guida per l’installazione di infrastrutture per la ricarica dei veicoli elettrici”. In particolare, si considerano a regola dell’arte le stazioni di ricarica conformi a CEI 64-8/7-722, CEI EN 61851 e CEI EN 62196.
    La stazione di ricarica è collegata al dispositivo di comando di sgancio di emergenza dedicato e integrata con lo sgancio generale dell’edificio (se presente). L’area sarà segnalata con idonea cartellonistica. In attraversamento di compartimentazioni, dovranno essere impiegati sistemi di sigillatura REI idonei (es. collari REI su tubazioni plastiche).

    5. COORDINAMENTO CON IMPIANTO DI TERRA ESISTENTE
    Nel caso specifico di sistema TT, la protezione dai contatti indiretti sarà garantita rispettando la relazione Rt ≤ 50 / Id, con protezioni differenziali coordinate.

    5.1 DIMENSIONAMENTO IMPIANTO DI TERRA
    L’impianto di messa a terra è unico per tutto l’edificio; il collegamento avverrà in prossimità della barra equipotenziale esistente, secondo quanto previsto negli elaborati e quanto riscontrato in sito. Il nuovo quadro di BT sarà completo di barra EQP.

    6. CRITERI DI DIMENSIONAMENTO ADOTTATI
    Il dimensionamento delle condutture e il coordinamento dei dispositivi di protezione è stato eseguito valutando correnti di impiego, cadute di tensione e verifiche termiche, in conformità alla norma CEI 64-8.
    """).strip()


# =========================
# TABELLE (SEMPLIFICATE)
# =========================

SEZIONI = [6, 10, 16, 25, 35, 50, 70, 95]
INTERRUTTORI = [16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160]

# Portate base Iz per FG16(O)R16 in condizioni standard (semplificate)
PORTATA_BASE = {
    "Interrata": {6: 34, 10: 46, 16: 61, 25: 80, 35: 99, 50: 119, 70: 151, 95: 182},
    "A vista":   {6: 41, 10: 57, 16: 76, 25: 101, 35: 125, 50: 150, 70: 192, 95: 232},
}

# Fattori correttivi (semplificati)
FATT_TEMP = {30: 1.00, 35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71}
FATT_RAGGR = {1: 1.00, 2: 0.80, 3: 0.70}

# Coefficiente k per verifica termica I²t (rame, XLPE/EPR ~ 90°C) - valore tipico
K_CU_XLPE = 143  # A·sqrt(s)/mm² (valore tipico usato in pratica)


def _fattore_temp(temp_amb: int) -> float:
    keys = sorted(FATT_TEMP.keys())
    sel = max([t for t in keys if t <= temp_amb], default=50)
    return FATT_TEMP.get(sel, 0.71)


def _fattore_raggr(n_linee: int) -> float:
    if n_linee in FATT_RAGGR:
        return FATT_RAGGR[n_linee]
    return 0.70


def _pe_da_fase(sez_fase_mm2: int) -> int:
    """
    CEI 64-8 (Parte 5-54), criterio semplificato tipo 543.1.2 (rame):
    - Sfase ≤ 16 -> SPE = Sfase
    - 16 < Sfase ≤ 35 -> SPE = 16
    - Sfase > 35 -> SPE = Sfase/2
    """
    if sez_fase_mm2 <= 16:
        return sez_fase_mm2
    if sez_fase_mm2 <= 35:
        return 16
    return int(math.ceil(sez_fase_mm2 / 2))


def genera_progetto_ev(
    # anagrafica
    nome: str,
    cognome: str,
    indirizzo: str,
    # dati elettrici
    potenza_kw: float,
    distanza_m: float,
    alimentazione: str,
    tipo_posa: str,
    # parametri progetto
    n_wallbox: int = 1,
    sistema: str = "TT",            # TT / TN-S / TN-C-S
    cosphi: float = 0.95,
    temp_amb: int = 30,
    n_linee: int = 1,
    icc_ka: float = 6.0,
    # EV / 722
    modo_ricarica: str = "Modo 3",
    tipo_punto: str = "Connettore EV",
    esterno: bool = False,
    ip_rating: int = 44,
    ik_rating: int = 7,
    altezza_presa_m: float = 1.0,
    spd_previsto: bool = True,
    gestione_carichi: bool = False,
    # differenziale
    rcd_tipo: str = "Tipo A + RDC-DD 6mA DC",
    rcd_idn_ma: int = 30,
    evse_rdcdd_integrato: bool = True,   # RDC-DD 6mA DC integrato nell'EVSE?
    # verifiche 4-41 / campo
    ra_ohm: float | None = None,         # resistenza di terra (TT) se disponibile
    ul_v: float = 50.0,                  # tensione limite ordinaria
    zs_ohm: float | None = None,         # impedenza anello guasto (TN) se disponibile
    # verifica termica I²t (facoltativa)
    t_intervento_s: float | None = None  # tempo intervento protezione (s) se disponibile
):
    """
    Pre-dimensionamento + relazione tecnica con:
    - Ib, In, sezione per ΔV ≤ 4%, verifica Ib ≤ In ≤ Iz
    - PE (5-54) in modo semplificato
    - verifica contatti indiretti:
      * TT: Ra·IΔn ≤ UL (se Ra fornita)
      * TN: nota/verifica con Zs/tempi (se dati non forniti)
    - verifica termica corto (I²t) se Icc e t sono forniti
    - checklist 722 coerente
    - note obbligatorie per prove in campo dove necessario
    """

    # ---------------------------
    # CONTROLLI INPUT
    # ---------------------------
    if potenza_kw <= 0 or distanza_m <= 0:
        raise ValueError("Potenza e distanza devono essere > 0.")
    if tipo_posa not in PORTATA_BASE:
        raise ValueError(f"Tipo posa non gestito: {tipo_posa}")
    if rcd_idn_ma not in (30, 100, 300):
        raise ValueError("IΔn tipica: 30/100/300 mA.")

    trifase = "trifase" in alimentazione.lower()
    tensione = 400 if trifase else 220

    # Monofase max 7.4 kW
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
    # Sezione per caduta di tensione (ΔV ≤ 4%) – modello semplificato
    # ---------------------------
    cond_rame = 56
    dv_max = tensione * 0.04

    if trifase:
        S_cad = (math.sqrt(3) * distanza_m * Ib * cosphi) / (cond_rame * dv_max)
    else:
        S_cad = (2 * distanza_m * Ib * cosphi) / (cond_rame * dv_max)

    # ---------------------------
    # Iz con derating
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
        if Ib <= In <= Iz:
            sezione = S
            Iz_corr = Iz
            Iz_base_sel = Iz_base
            break

    if sezione is None:
        raise ValueError("Nessuna sezione soddisfa ΔV≤4% e Ib ≤ In ≤ Iz (con derating).")

    # ---------------------------
    # PE (5-54) – regola semplificata
    # ---------------------------
    sezione_pe = _pe_da_fase(int(sezione))

    # ---------------------------
    # Icn vs Icc (semplificato)
    # ---------------------------
    if icc_ka <= 6:
        icn_note = "Icn minimo 6 kA (verifica puntuale con dati di fornitura)."
    elif icc_ka <= 10:
        icn_note = "Richiedere interruttore con Icn ≥ 10 kA."
    else:
        icn_note = "Richiedere interruttore con Icn adeguato (≥ Icc presunta)."

    # ---------------------------
    # Verifica termica corto (I²t) – se t disponibile
    # Icc (kA) -> A
    # Smin = I * sqrt(t) / k
    # ---------------------------
    note_verifiche_campo = []
    smin_i2t = None
    if t_intervento_s is not None:
        if t_intervento_s <= 0:
            raise ValueError("Tempo intervento deve essere > 0")
        Icc_A = icc_ka * 1000
        smin_i2t = (Icc_A * math.sqrt(t_intervento_s)) / K_CU_XLPE
        # Nota: è una verifica cautelativa se Icc riferita al punto; per correttezza serve Icc alla fine linea.
    else:
        note_verifiche_campo.append("Verifica termica corto circuito (I²t) da eseguire con Icc locale e tempi reali dell’interruttore (CEI 64-8/4-43).")

    # ---------------------------
    # CHECK 4-41 (contatti indiretti)
    # ---------------------------
    esito_441 = {"ok": [], "warning": [], "nonconf": []}

    # TT: Ra * IΔn ≤ UL
    if sistema.strip().upper().startswith("TT"):
        if ra_ohm is not None:
            Idn_A = rcd_idn_ma / 1000.0
            val = ra_ohm * Idn_A
            if val <= ul_v:
                esito_441["ok"].append(f"TT: verifica Ra·IΔn ≤ {ul_v:.0f}V → {val:.1f}V (OK).")
            else:
                esito_441["nonconf"].append(f"TT: verifica Ra·IΔn ≤ {ul_v:.0f}V → {val:.1f}V (NON CONFORME).")
        else:
            esito_441["warning"].append("TT: inserire Ra (Ω) per verifica Ra·IΔn ≤ UL; in alternativa verificare in campo (CEI 64-8/4-41).")
            note_verifiche_campo.append("Misurare Ra e verificare intervento differenziale/tempi (CEI 64-8/6 prove).")

    # TN: serve Zs e curva/tempi – qui se Zs manca mettiamo nota
    else:
        if zs_ohm is not None:
            esito_441["warning"].append("TN: Zs fornita, ma per verifica completa servono Ia/curve e tempi di intervento (CEI 64-8/4-41). Verificare con dati del dispositivo.")
        else:
            esito_441["warning"].append("TN: verificare in campo impedenza anello di guasto (Zs) e tempi di intervento (CEI 64-8/4-41).")
            note_verifiche_campo.append("Misurare Zs e verificare tempi di intervento per la protezione contro i contatti indiretti (CEI 64-8/6).")

    # ---------------------------
    # CHECKLIST 722 (pulita)
    # ---------------------------
    warning_722, nonconf_722, ok_722 = [], [], []
    modo_norm = modo_ricarica.strip().lower()

    ok_722.append("Circuito dedicato per punto di ricarica (linea dedicata dimensionata).")

    if n_linee > 1:
        if gestione_carichi:
            ok_722.append("Gestione carichi/contemporaneità: prevista.")
        else:
            warning_722.append("Più linee/punti senza gestione carichi: assumere contemporaneità = 1 e verificare potenza disponibile.")
    else:
        ok_722.append("Singola linea/punto: contemporaneità non critica.")

    # Idn punto: 30 mA
    if rcd_idn_ma > 30:
        nonconf_722.append("Differenziale per punto: richiesto IΔn ≤ 30 mA (impostato valore superiore).")
    else:
        ok_722.append("Differenziale per punto: IΔn ≤ 30 mA.")

    # DC fault: Modo 3 (AC) – dipende da RDC-DD integrato
    if modo_norm == "modo 3":
        if evse_rdcdd_integrato:
            # basta Tipo A 30 mA (se EVSE garantisce 6mA DC interno)
            if "tipo a" in rcd_tipo.lower() or "tipo b" in rcd_tipo.lower():
                ok_722.append("Modo 3: RDC-DD 6 mA DC integrato nell’EVSE (RCD a monte coerente).")
            else:
                warning_722.append("Modo 3: RDC-DD integrato, ma verificare tipo RCD a monte (almeno Tipo A 30 mA).")
        else:
            # serve Tipo B oppure A + 6mA (dispositivo esterno)
            if ("tipo b" not in rcd_tipo.lower()) and ("6ma" not in rcd_tipo.lower()):
                nonconf_722.append("Modo 3: senza RDC-DD integrato, richiesto RCD Tipo B oppure Tipo A + dispositivo 6 mA DC.")
            else:
                ok_722.append("Modo 3: protezione guasti DC coerente (Tipo B o A+6mA).")

    # Modo 1/2 presa domestica
    if modo_norm in ("modo 1", "modo 2") and tipo_punto == "Presa domestica":
        if In > 16:
            nonconf_722.append("Modo 1/2 con presa domestica: corrente > 16 A non ammessa (adeguare).")
        else:
            warning_722.append("Modo 1/2 con presa domestica: raccomandato solo per ricariche occasionali.")

    if not spd_previsto:
        warning_722.append("SPD non previsto: valutare protezione da sovratensioni in base a rischio e impianto.")
    else:
        ok_722.append("SPD previsto/valutato.")

    if esterno:
        if ip_rating < 44:
            nonconf_722.append("Installazione esterna: richiesto IP ≥ 44.")
        else:
            ok_722.append(f"Installazione esterna: IP{ip_rating} conforme (≥ IP44).")
        if ik_rating < 7:
            warning_722.append("Installazione esterna/pubblica: valutare protezione meccanica (raccomandato IK07 o misure equivalenti).")
        else:
            ok_722.append(f"Protezione meccanica: IK{ik_rating} adeguato (≥ IK07).")

    if not (0.5 <= altezza_presa_m <= 1.5):
        warning_722.append("Altezza punto di connessione fuori intervallo raccomandato 0,5–1,5 m.")
    else:
        ok_722.append("Altezza punto di connessione in intervallo raccomandato (0,5–1,5 m).")

    # ---------------------------
    # TESTI PULITI (solo note pertinenti)
    # ---------------------------
    nota_dc_fault = ""
    if modo_norm == "modo 3" and (not evse_rdcdd_integrato):
        nota_dc_fault = (
            "Nota (CEI 64-8/7-722): in assenza di RDC-DD 6 mA DC integrato nell’EVSE, "
            "è richiesto RCD Tipo B oppure RCD Tipo A + dispositivo 6 mA DC."
        )

    nota_presa_dom = ""
    if modo_norm in ("modo 1", "modo 2") and tipo_punto == "Presa domestica":
        nota_presa_dom = "Nota: Modo 1/2 con presa domestica raccomandato solo per ricariche occasionali con componenti idonei."

    nota_spd = "SPD previsto/valutato." if spd_previsto else "SPD non previsto: valutare protezione da sovratensioni in base a rischio e impianto."

    riferimenti_normativi = dedent("""
    RIFERIMENTI NORMATIVI E LEGISLATIVI
    - Legge 186/68: regola dell’arte.
    - D.M. 37/08: realizzazione impianti all’interno degli edifici (ove applicabile).
    - CEI 64-8:
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

    # blocco verifiche campo (CEI 64-8/6)
    blocco_prove = ""
    if note_verifiche_campo:
        blocco_prove = "PROVE E VERIFICHE IN CAMPO (CEI 64-8/6)\n- " + "\n- ".join(note_verifiche_campo)

    # blocco 4-41
    blocco_441 = dedent(f"""
    VERIFICA PROTEZIONE CONTRO CONTATTI INDIRETTI (CEI 64-8/4-41)
    Esiti OK:
    {("- " + "\\n- ".join(esito_441["ok"])) if esito_441["ok"] else "- (nessuno)"}
    Warning:
    {("- " + "\\n- ".join(esito_441["warning"])) if esito_441["warning"] else "- (nessuno)"}
    Non conformità:
    {("- " + "\\n- ".join(esito_441["nonconf"])) if esito_441["nonconf"] else "- (nessuna)"}
    """).strip()

    # I²t blocco
    blocco_i2t = ""
    if smin_i2t is not None:
        blocco_i2t = (
            "VERIFICA TERMICA CORTOCIRCUITO (CEI 64-8/4-43)\n"
            f"- Dati: Icc={icc_ka:.1f} kA, t={t_intervento_s:.3f} s, k≈{K_CU_XLPE}\n"
            f"- Sezione minima teorica Smin≈{smin_i2t:.1f} mm² (verificare con Icc reale a fine linea e curva del dispositivo)."
        )

    relazione = genera_relazione_tecnica({
        "nome": nome,
        "cognome": cognome,
        "indirizzo": indirizzo,
        "n_wallbox": n_wallbox,
        "potenza_kw": potenza_kw,
        "sistema": sistema,
        "modo_ricarica": modo_ricarica,
    }, riferimenti_normativi=riferimenti_normativi)

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
       - RDC-DD 6mA DC integrato EVSE: {"Sì" if evse_rdcdd_integrato else "No"}
    {("   - " + nota_dc_fault) if nota_dc_fault else ""}

    3) Linea:
       - Cavo: FG16(O)R16 0,6/1 kV (rame)
       - Sezione fase: {sezione} mm²
       - Sezione PE: {sezione_pe} mm²
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
        "sezione_pe_mm2": sezione_pe,
        "S_cad_min_mm2": round(S_cad, 2),
        "k_temp": round(k_temp, 2),
        "k_ragg": round(k_ragg, 2),
        "Smin_i2t_mm2": round(smin_i2t, 1) if smin_i2t is not None else None,
        # testi
        "relazione": relazione,
        "unifilare": unifilare,
        "planimetria": planimetria,
        # 722
        "ok_722": ok_722,
        "warning_722": warning_722,
        "nonconf_722": nonconf_722,
        # 4-41
        "ok_441": esito_441["ok"],
        "warning_441": esito_441["warning"],
        "nonconf_441": esito_441["nonconf"],
    }
