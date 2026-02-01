from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape
import re
from typing import Iterable, List

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def _p(text: str, style):
    safe = escape(text).replace("\n", "<br/>")
    return Paragraph(safe, style)


def _extract_formula_lines(relazione: str, max_lines: int = 40) -> List[str]:
    """
    Estrae righe 'formula-like' dalla relazione (senza alterare i calcoli).
    Criterio: presenza di '=', '≤', '>=', '<=', '∆', 'Δ', 'I2t', 'k2', 'sqrt', ecc.
    """
    if not relazione:
        return []

    lines = []
    for raw in relazione.splitlines():
        s = raw.strip()
        if not s:
            continue
        if any(tok in s for tok in ["=", "≤", "≥", "<=", ">=", "∆", "Δ", "I2t", "I²t", "k2", "K2", "√", "sqrt", "cosφ", "sinφ"]):
            # evita righe lunghissime "discorsive"
            if len(s) > 180:
                continue
            lines.append(s)

    # dedup mantenendo ordine
    seen = set()
    out = []
    for s in lines:
        if s not in seen:
            out.append(s)
            seen.add(s)
        if len(out) >= max_lines:
            break
    return out


def _page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(200 * mm, 12 * mm, f"Pag. {doc.page}")
    canvas.restoreState()


def genera_pdf_unico_bytes(
    relazione: str,
    unifilare: str,
    planimetria: str,
    ok_722: Iterable[str],
    warning_722: Iterable[str],
    nonconf_722: Iterable[str],
):
    """
    PDF tecnico EV:
    - Relazione completa
    - Schema unifilare (testo / note)
    - Planimetria (testo / note)
    - Check-list CEI 64-8/722
    - In fondo: 'Conformità e Formule di verifica' (come richiesto)
    """
    buf = BytesIO()
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Relazione tecnica EV – CEI 64-8/722",
    )

    story = []

    # =========================
    # Copertina breve
    # =========================
    story.append(_p("RELAZIONE TECNICA – INFRASTRUTTURA DI RICARICA EV", styles["Title"]))
    story.append(Spacer(1, 6))
    story.append(_p("CEI 64-8 (Sez. 722)", styles["Heading2"]))
    story.append(Spacer(1, 14))

    # =========================
    # Relazione completa
    # =========================
    story.append(_p("RELAZIONE COMPLETA", styles["Title"]))
    story.append(Spacer(1, 10))

    # Blocco richiesto: inizio pagina dopo "RELAZIONE COMPLETA" (duplicato, resta anche in fondo)
    dati_norme_blocco = """DATI GENERALI
Committente: Mario Rossi
Ubicazione: Via Garibaldi 1, Mantova
Sistema di distribuzione: TT
Alimentazione EVSE: Trifase 400 V
Modo di ricarica: Modo 3
Punto di connessione: Connettore EV
Installazione esterna: No
Altezza punto di connessione: 1.00 m

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
- CEI EN 62305 / CEI 81-10: valutazione protezione contro sovratensioni (quando applicabile).
"""
    story.append(_p(dati_norme_blocco, styles["BodyText"]))
    story.append(Spacer(1, 10))
    story.append(_p(relazione or "—", styles["BodyText"]))

    story.append(PageBreak())

    # =========================
    # Schema unifilare
    # =========================
    story.append(_p("SCHEMA UNIFILARE", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(_p(unifilare or "—", styles["BodyText"]))

    story.append(PageBreak())

    # =========================
    # Planimetria
    # =========================
    story.append(_p("PLANIMETRIA", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(_p(planimetria or "—", styles["BodyText"]))

    story.append(PageBreak())

    # =========================
    # Checklist 722 (tabella chiara)
    # =========================
    story.append(_p("CHECK-LIST CEI 64-8/7 – SEZIONE 722", styles["Title"]))
    story.append(Spacer(1, 10))

    def _fmt(items: Iterable[str]) -> str:
        items = list(items or [])
        if not items:
            return "—"
        return "\n".join([f"• {x}" for x in items])

    data = [
        ["Esiti OK", _fmt(ok_722)],
        ["Warning", _fmt(warning_722)],
        ["Non conformità", _fmt(nonconf_722)],
    ]

    table = Table(data, colWidths=[40*mm, 150*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,2), colors.whitesmoke),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOX", (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(table)

    story.append(PageBreak())

    # =========================
    # Conformità + Formule (IN FONDO, come richiesto)
    # =========================
    story.append(_p("CONFORMITÀ E FORMULE DI VERIFICA", styles["Title"]))
    story.append(Spacer(1, 10))

    story.append(_p("Conforme: CEI 64-8 (Sez. 722)", styles["BodyText"]))
    story.append(Spacer(1, 6))

    # Blocco richiesto mantenuto anche in fondo (duplicato)
    story.append(_p(dati_norme_blocco, styles["BodyText"]))
    story.append(Spacer(1, 10))

    # Formule: estrazione "ingegnere-friendly" (senza note inutili)
    formula_lines = _extract_formula_lines(relazione)
    if formula_lines:
        story.append(_p("FORMULE E VERIFICHE (estratto)", styles["Heading2"]))
        story.append(Spacer(1, 6))
        story.append(_p("\n".join(formula_lines), styles["BodyText"]))
    else:
        story.append(_p("FORMULE E VERIFICHE (estratto)", styles["Heading2"]))
        story.append(_p("—", styles["BodyText"]))

    doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return buf.getvalue()
