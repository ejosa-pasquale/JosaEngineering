import math
from textwrap import dedent

# =========================
# TABELLE E COSTANTI
# =========================

SEZIONI = [6, 10, 16, 25, 35, 50, 70, 95]
INTERRUTTORI = [16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160]

# Portate di base Iz per cavo FG16(O)R16 in condizioni standard
PORTATA_BASE = {
    "Interrata": {
        6: 34,
        10: 46,
        16: 61,
        25: 80,
        35: 99,
        50: 119,
        70: 151,
        95: 182
    },
    "A vista": {
        6: 41,
        10: 57,
        16: 76,
        25: 101,
        35: 125,
        50: 150,
        70: 192,
        95: 232
    }
}

# Fattori correttivi temperatura (semplificati)
FATT_TEMP = {
    30: 1.00,
    35: 0.94,
    40: 0.87,
    45: 0.79,
    50: 0.71
}

# Fattori correttivi per raggruppamento (numero linee)
FATT_RAGGR = {
    1: 1.00,
    2: 0.80,
    3: 0.70
}


def genera_progetto_ev(
    nome: str,
    cognome: str,
    indirizzo: str,
    potenza_kw: float,
    distanza_m: float,
    alimentazione: str,
    tipo_posa: str,
    sistema: str = "TT",
    cosphi: float = 0.95,
    temp_amb: int = 30,
    n_linee: int = 1,
    icc_ka: float = 6.0,
    rcd: str = "Tipo A + RDC-DD 6mA DC"
):
    """
    Genera i dati di progetto e la relazione tecnica per una linea EV
    secondo criteri CEI 64-8 (pre-dimensionamento).
    """

    # ---------------------------
    # CONTROLLI DI BASE
    # ---------------------------
    if potenza_kw <= 0 or distanza_m <= 0:
        raise ValueError("Potenza e distanza devono essere maggiori di zero.")

    if tipo_posa not in PORTATA_BASE:
        raise ValueError(f"Tipo di posa non gestito: {tipo_posa}")

    # ---------------------------
    # DATI DI BASE
    # ---------------------------
    trifase = "trifase" in alimentazione.lower()
    tensione = 400 if trifase else 230

    # ---------------------------
    # CORRENTE DI IMPIEGO Ib
    # ---------------------------
    if trifase:
        Ib = (potenza_kw * 1000) / (math.sqrt(3) * tensione * cosphi)
    else:
        Ib = (potenza_kw * 1000) / (tensione * cosphi)

    # ---------------------------
    # SCELTA INTERRUTTORE In
    # ---------------------------
    In = next((i for i in INTERRUTTORI if i >= Ib), None)
    if In is None:
        raise ValueError("Ib troppo elevata: nessuna taglia di interruttore disponibile.")

    # ---------------------------
    # CADUTA DI TENSIONE
    # ---------------------------
    cond_rame = 56  # m/(Ω·mm²)
    dv_max = tensione * 0.04  # 4% della tensione nominale

    if trifase:
        S_cad = (math.sqrt(3) * distanza_m * Ib * cosphi) / (cond_rame * dv_max)
    else:
        S_cad = (2 * distanza_m * Ib * cosphi) / (cond_rame * dv_max)

    # ---------------------------
    # FATTORI CORRETTIVI (temp + raggruppamento)
    # ---------------------------
    # Se la temperatura non è esattamente in tabella, prendo il valore più vicino "verso il basso"
    temp_keys = sorted(FATT_TEMP.keys())
    temp_sel = max([t for t in temp_keys if t <= temp_amb], default=50)
    k_temp = FATT_TEMP.get(temp_sel, 0.71)

    k_ragg = FATT_RAGGR.get(n_linee, 0.7)

    # ---------------------------
    # VERIFICA Ib ≤ In ≤ Iz
    # ---------------------------
    sezione = None
    Iz_finale = None

    for S in SEZIONI:
        if S < S_cad:
            continue

        Iz_base = PORTATA_BASE[tipo_posa].get(S)
        if not Iz_base:
            continue

        Iz = Iz_base * k_temp * k_ragg

        if Ib <= In <= Iz:
            sezione = S
            Iz_finale = Iz
            break

    if sezione is None:
        raise ValueError(
            "Nessuna sezione rispetta contemporaneamente caduta di tensione e Ib ≤ In ≤ Iz."
        )

    # ---------------------------
    # VERIFICA POTERE DI INTERRUZIONE
    # ---------------------------
    Icn_note = "OK (Icn ≥ Icc presunta)" if icc_ka <= 6 else "Verificare potere di interruzione (Icn ≥ Icc)."

    # ---------------------------
    # RELAZIONE TECNICA TESTUALE
    # ---------------------------
    relazione = dedent(f"""
    RELAZIONE TECNICA – IMPIANTO DI RICARICA VEICOLI ELETTRICI
    =======================================================

    Committente: {nome} {cognome}
    Ubicazione: {indirizzo}

    DESCRIZIONE DELL'INTERVENTO
    Installazione di stazione di ricarica per veicoli elettrici
    di potenza nominale {potenza_kw:.1f} kW, alimentata in {alimentazione},
    con sistema di distribuzione {sistema}.

    NORME DI RIFERIMENTO
    - CEI 64-8 (impianti utilizzatori in BT)
    - IEC 61851 (sistemi di ricarica per veicoli elettrici)

    DATI DI PROGETTO
    - Tensione nominale: {tensione} V
    - cosφ di progetto: {cosphi}
    - Temperatura ambiente di riferimento: {temp_amb} °C
    - Numero linee in parallelo/raggruppate: {n_linee}
    - Tipo di posa: {tipo_posa}
    - Lunghezza linea: {distanza_m} m
    - Caduta di tensione ammessa: 4%

    RISULTATI DEL DIMENSIONAMENTO
    - Corrente di impiego Ib = {Ib:.2f} A
    - Interruttore di protezione In = {In} A (curva C)
    - Sezione dei conduttori di fase: {sezione} mm² (cavo FG16(O)R16 0,6/1 kV)
    - Portata del cavo Iz (corretta) = {Iz_finale:.1f} A

    La linea soddisfa la condizione Ib ≤ In ≤ Iz come richiesto dalla CEI 64-8 (§433),
    e la sezione è stata scelta in modo da rispettare il limite di caduta di tensione
    del 4% (CEI 64-8 §525).

    PROTEZIONI
    - Interruttore magnetotermico curva C, In = {In} A
    - Potere di interruzione minimo richiesto: {icc_ka:.1f} kA → {Icn_note}
    - Protezione differenziale: {rcd}

    NOTE
    Le portate dei cavi sono riferite a posa singola, temperatura ambiente indicata
    e assenza di particolari condizioni di derating ulteriori. Eventuali condizioni
    ambientali diverse dovranno essere verificate in fase esecutiva.
    """).strip()

    return {
        "Ib": round(Ib, 2),
        "In": In,
        "Iz": round(Iz_finale, 1),
        "Sezione": sezione,
        "Relazione": relazione
    }
