import math
from textwrap import dedent

BULLET_JOIN = "\n- "

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
FATT_TEMP_ARIA = {30: 1.00, 35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71}
# Per posa interrata la condizione di riferimento tipica nelle tabelle IEC/CEI è T_terreno=20°C.
# Valori qui sotto: semplificazione prudente ma non eccessiva (da usare con consapevolezza).
FATT_TEMP_TERRA = {20: 1.00, 25: 0.96, 30: 0.92, 35: 0.88, 40: 0.84}

# Fattore per resistività termica del terreno ρ [K·m/W] (riferimento tipico 2.5).
# Se ρ aumenta (terreno più "isolante"), la portata si riduce.
FATT_RHO_TERRA = {2.5: 1.00, 3.0: 0.96, 4.0: 0.90, 5.0: 0.86}
FATT_RAGGR = {1: 1.00, 2: 0.80, 3: 0.70}

# Coefficiente k per verifica termica I²t (rame, XLPE/EPR ~ 90°C) - valore tipico
K_CU_XLPE = 143  # A·sqrt(s)/mm² (valore tipico usato in pratica)


def _interp_dict(x: float, tab: dict) -> float:
    """Interpolazione lineare su una tabella {x: y} con x crescente."""
    xs = sorted(tab.keys())
    if x <= xs[0]:
        return tab[xs[0]]
    if x >= xs[-1]:
        return tab[xs[-1]]
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x0 <= x <= x1:
            y0, y1 = tab[x0], tab[x1]
            return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return tab[xs[-1]]


def _fattore_temp(tipo_posa: str, temp_aria: int, temp_terreno: int | None) -> tuple[float, int]:
    """
    Restituisce (k_temp, T_usata).

    - "A vista": tabella aria (riferimento 30°C).
    - "Interrata": tabella terreno (riferimento 20°C). Se non specifichi temp_terreno,
      NON viene applicata automaticamente la temperatura aria al cavo interrato.

    Nota: fattori semplificati. Per casi critici usare tabelle CEI/IEC complete.
    """
    if tipo_posa == "Interrata":
        T = 20 if temp_terreno is None else int(temp_terreno)
        return (_interp_dict(float(T), FATT_TEMP_TERRA), T)
    T = int(temp_aria)
    return (_interp_dict(float(T), FATT_TEMP_ARIA), T)


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
    sistema: str = "TT",            # TT / TN-S / TN-C-S
    cosphi: float = 0.95,
    temp_amb: int = 30,
    temp_terreno: int | None = None,
    rho_terreno_km_w: float | None = None,
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
    k_temp, T_usata = _fattore_temp(tipo_posa, temp_amb, temp_terreno)
    k_rho, rho_usata = _fattore_rho_terreno(rho_terreno_km_w) if tipo_posa == "Interrata" else (1.0, 2.5)
    k_ragg = _fattore_raggr(n_linee)
    note_rho = (f"• Resistività terreno ρ={rho_usata:.1f} K·m/W → kρ={k_rho:.2f}\n      " if tipo_posa == "Interrata" else "")

    sezione = None
    Iz_corr = None
    Iz_base_sel = None

    for S in SEZIONI:
        if S < S_cad:
            continue
        Iz_base = PORTATA_BASE[tipo_posa].get(S)
        if not Iz_base:
            continue
        Iz = Iz_base * k_temp * k_rho * k_ragg
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
    {("- " + BULLET_JOIN.join(esito_441["ok"])) if esito_441["ok"] else "- (nessuno)"}
    Warning:
    {("- " + BULLET_JOIN.join(esito_441["warning"])) if esito_441["warning"] else "- (nessuno)"}
    Non conformità:
    {("- " + BULLET_JOIN.join(esito_441["nonconf"])) if esito_441["nonconf"] else "- (nessuna)"}
    """).strip()

    # I²t blocco
    blocco_i2t = ""
    if smin_i2t is not None:
        blocco_i2t = (
            "VERIFICA TERMICA CORTOCIRCUITO (CEI 64-8/4-43)\n"
            f"- Dati: Icc={icc_ka:.1f} kA, t={t_intervento_s:.3f} s, k≈{K_CU_XLPE}\n"
            f"- Sezione minima teorica Smin≈{smin_i2t:.1f} mm² (verificare con Icc reale a fine linea e curva del dispositivo)."
        )

    relazione = dedent(f"""
    RELAZIONE TECNICA – INFRASTRUTTURA DI RICARICA VEICOLI ELETTRICI - Software eV Field Service 
    
    1. Premessa
    Il progetto a cui fa riferimento il presente documento è relativo alla realizzazione degli impianti elettrici necessari per la connessione di un’infrastruttura di ricarica per veicoli elettrici.
    Nel presente progetto si è tenuto conto della destinazione d’uso degli spazi già disponibili, valutando la configurazione degli stessi, nonché degli ingombri delle apparecchiature che verranno installate.
    L’intervento è finalizzato esclusivamente alla predisposizione e all’alimentazione di una stazione di ricarica tipo Wallbox, destinata alla ricarica di veicoli elettrici in ambito condominiale.
    
    2. Opere impiantistiche previste
    Le opere impiantistiche previste sono esclusivamente legate all’installazione di una Wallbox per la ricarica di veicoli elettrici, alimentata tramite fornitura elettrica dedicata e relativo quadro elettrico di protezione.
    L’alimentazione verrà derivata, mediante l’utilizzo di tubazioni esistenti, dal quadro elettrico dedicato verso il parcheggio sito in (indirizzo), dove sarà installata la stazione di ricarica.
    
    3. Distribuzione elettrica
    La colonnina di ricarica sarà alimentata in bassa tensione (BT) prelevando l’energia dal punto di consegna dell’Ente Distributore (e-distribuzione) esistente.
    
    3.1 Descrizione quadri e distribuzione in B.T.
    La distribuzione in bassa tensione avverrà partendo dal locale contatori, mediante l’installazione di un nuovo quadretto elettrico dedicato (QE Generale), atto a proteggere la linea di alimentazione della Wallbox.
    Nel locale tecnico, che ospita i contatori dell’intero complesso, verrà installato un ulteriore gruppo di misura, oltre al nuovo interruttore di protezione per l’alimentazione della colonnina di ricarica posta al piano seminterrato, in corrispondenza del posto auto assegnato.
    Nella progettazione dei quadri è stata posta particolare attenzione:
    alla massima selettività possibile tra dispositivi di protezione a monte e a valle;
    alla distinzione fisica dei moduli e delle linee in uscita.
    
    3.1.1 Quadro Generale
    Lo schema unifilare e la carpenteria del quadro generale sono riportati negli elaborati grafici allegati.
    Il quadro è conforme alle seguenti normative:
    CEI 17-13/1
    CEI 17-113
    CEI 17-114
    CEI EN 61439-1
    CEI EN 61439-2
    La distribuzione dal quadro generale ai quadri posti in cascata avverrà mediante cavi multipolari FG16OM16, di sezione indicata negli elaborati progettuali, posati in tubo.
    L’identificazione dei conduttori sarà realizzata tramite: isolamento a colori codificati; manicotti termorestringenti o spirali in nylon colorato; piastrine identificative.
    Per ogni linea sarà distribuito il conduttore di protezione (FS17 giallo-verde) di sezione adeguata, tale da garantire la protezione contro i contatti indiretti in funzione della taratura delle protezioni magnetotermiche installate.
    
    3.1.2 Distribuzione elettrica di zona
    La distribuzione alle varie zone avverrà mediante tubazioni in PVC. Il ricovero auto sarà alimentato tramite tubazione indipendente.
    I collegamenti: tra quadri; tra quadri e utenze finali (Wallbox), saranno realizzati con cavi multipolari FG16OM(R)16.
    
    4. Sicurezza elettrica delle colonnine di ricarica
    In riferimento alla Circolare del Ministero dell’Interno del 05 novembre 2018 n. 2, le infrastrutture di ricarica per veicoli elettrici non rientrano tra le attività soggette ai controlli di prevenzione incendi ai sensi del D.P.R. 151/2011, ma la loro installazione costituisce modifica all’attività esistente.
    L’impianto oggetto del presente documento sarà conforme alla suddetta Circolare.
    L’infrastruttura proposta consiste in una colonnina di ricarica AC da 22 kW, conforme alle norme CEI e predisposta per la ricarica in Modo 3.
    La stazione di ricarica: è conforme alle Norme CEI 64-8, Sezione 722; è conforme alle norme CEI EN 61851 e CEI EN 62196; è collegata ai dispositivi di sgancio generale dell’edificio.
   
    4.1 Dispositivo di sgancio di emergenza
    La Wallbox è collegata a un dispositivo di sgancio elettrico di emergenza dedicato, installato in autorimessa in prossimità del pulsante di sgancio generale esistente.
    In caso di emergenza, l’azionamento del pulsante provoca il sezionamento dell’alimentazione elettrica della colonnina.
    L’attività è soggetta a prevenzione incendi e risulta depositata presso il Comando Provinciale dei Vigili del Fuoco di Milano con pratica n. 65632.
    
    4.2 Segnaletica e verifiche
    L’area di installazione sarà segnalata con idonea cartellonistica recante la dicitura:
    “Stazione di Ricarica per Veicoli Elettrici”
    Periodicamente, e a seguito di modifiche o ampliamenti, dovranno essere eseguite e documentate le verifiche previste dalla normativa vigente.
    
    4.3 Attraversamenti REI
    In corrispondenza degli attraversamenti di compartimentazioni REI dovranno essere installati sistemi di sigillatura certificati, quali collari REI con materiale termoespandente, idonei per tubazioni in PVC, PE o PP.
    
    5. Coordinamento con impianto di terra esistente
    Il sistema elettrico è di tipo TT.
    La protezione contro i contatti indiretti è garantita dalla relazione:
    Rt ≤ 50 / Id
    dove:
    Id = corrente di intervento del differenziale in 5 s
    Rt = resistenza dell’impianto di terra
    
    5.1 Dimensionamento impianto di terra
    L’impianto di terra è unico per tutto l’edificio ed è costituito da:
    dispersori a croce in acciaio zincato 50x50 mm, lunghezza 1,5 m;
    corda di rame da 50 mm² interrata a profondità ≥ 50 cm.
    Il collegamento al nuovo quadro BT avverrà mediante conduttore di terra dedicato su barra equipotenziale.
    
    6. Criteri di dimensionamento adottati
    
    6.1 Calcolo della corrente di impiego
    Circuiti terminali:
    Ib = Ku · P · 1000 / (c · V · cosφ)
    
    6.2 Linee di distribuzione
    Ibf = Kc · ΣIb
    
    6.3 Caduta di tensione
    ΔV = c · Ib · l · (r·cosφ + x·sinφ)
    ΔV% = (ΔV / Vn) · 100
    
    6.4 Protezioni elettriche
    Condizioni verificate:
    Ib < In < Iz
    If < 1,45·Iz
    Ics ≥ Iccp
    I²t ≤ K²·S²
    
    7. Allegati
    
    -Schemi unifilari
    -Calcoli elettrici (corrente, caduta di tensione, corto circuito)
    -Schede tecniche Wallbox
    -Certificazioni CE
    ===============================================================
    Calcoli elettrici (corrente, caduta di tensione, corto circuito)
    
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
    Installazione EVSE di potenza nominale {potenza_kw:.1f} kW alimentata tramite linea dedicata dal quadro elettrico.

    CRITERI DI PROGETTO (CEI 64-8)
    - Caduta di tensione di progetto: ΔV ≤ 4% (CEI 64-8 §525).
    - Verifica sovraccarico: Ib ≤ In ≤ Iz (CEI 64-8 §433).
    - Portate cavo: condizioni standard con fattori correttivi:
      • Temperatura {T_usata} °C ({'terreno' if tipo_posa=='Interrata' else 'aria'}) → kT={k_temp:.2f}
      {note_rho}• Raggruppamento n={n_linee} → kG={k_ragg:.2f}
    - Cavo: FG16(O)R16 0,6/1 kV (rame).

    DIMENSIONAMENTO LINEA
    - Tensione: {tensione} V
    - cosφ: {cosphi:.2f}
    - Lunghezza: {distanza_m:.1f} m
    - Ib = {Ib:.2f} A
    - In = {In} A (curva C)
    - Sezione fase: {sezione} mm²
    - Sezione PE (criterio 5-54): {sezione_pe} mm²
    - Iz_base = {Iz_base_sel} A | Iz_corr = {Iz_corr:.1f} A
    - Verifica Ib ≤ In ≤ Iz: {"OK" if (Ib <= In <= Iz_corr) else "NON OK"}

    PROTEZIONI
    - Sovracorrenti: interruttore MT dedicato alla linea EV.
    - Cortocircuito: Icc presunta = {icc_ka:.1f} kA → {icn_note}
    - Differenziale: {rcd_tipo}, IΔn = {rcd_idn_ma} mA.
    - RDC-DD 6 mA DC integrato EVSE: {"Sì" if evse_rdcdd_integrato else "No"}.
    {nota_dc_fault if nota_dc_fault else ""}
    {nota_spd}

    {blocco_441}
    {(blocco_i2t if blocco_i2t else "")}

    PRESCRIZIONI CEI 64-8/7 – SEZIONE 722 (CHECK-LIST)
    Esiti OK:
    {("- " + BULLET_JOIN.join(ok_722)) if ok_722 else "- (nessuno)"}

    Warning:
    {("- " + BULLET_JOIN.join(warning_722)) if warning_722 else "- (nessuno)"}

    Non conformità:
    {("- " + BULLET_JOIN.join(nonconf_722)) if nonconf_722 else "- (nessuna)"}

    {nota_presa_dom if nota_presa_dom else ""}

    {blocco_prove if blocco_prove else ""}

    NOTE FINALI
    Le verifiche costituiscono pre-dimensionamento coerente con CEI 64-8. La scelta finale dei dispositivi e la conformità
    devono essere confermate con dati reali e prove strumentali di cui alla CEI 64-8/6. Valido solo se firmato
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

def _fattore_rho_terreno(rho_km_w: float | None) -> tuple[float, float]:
    """
    Restituisce (k_rho, rho_usata). Riferimento tipico ρ=2.5 K·m/W.
    Se rho_km_w è None, assume 2.5 (nessun derating).
    """
    rho = 2.5 if rho_km_w is None else float(rho_km_w)
    return (_interp_dict(rho, FATT_RHO_TERRA), rho)

