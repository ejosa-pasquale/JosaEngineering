from io import BytesIO
import re
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def _p(text: str, style):
    """Paragraph safe-escape helper."""
    safe = escape(text).replace("\n", "<br/>")
    return Paragraph(safe, style)


def _extract_formula_lines(relazione: str) -> list[str]:
    """Estrae righe 'utili' (formule/verifiche) dalla relazione per una sezione riassuntiva.
    Non modifica i calcoli: serve solo a rendere più leggibile il report.
    """
    lines = []
    for raw in relazione.splitlines():
        s = raw.strip()
        if not s:
            continue
        # euristiche: righe con simboli matematici o confronti tipici impiantistici
        if any(tok in s for tok in ["=", "≤", "≥", "Ib", "In", "Iz", "ΔV", "IΔn", "Ra", "Zs", "k", "I²t", "U0", "Un"]):
            # evita righe troppo lunghe (paragrafi)
            if len(s) <= 140:
                lines.append(s)
    # de-dup preservando ordine
    seen = set()
    out = []
    for s in lines:
        key = s.replace(" ", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    # limita: meglio poche righe “forti” che pagine di rumore
    return out[:18]


def _add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(A4[0] - 36, 20, f"Pag. {doc.page}")
    canvas.restoreState()


def genera_pdf_unico_bytes(
    relazione: str,
    unifilare: str,
    planimetria: str,
    ok_722=None,
    warning_722=None,
    nonconf_722=None
) -> bytes:
    ok_722 = ok_722 or []
    warning_722 = warning_722 or []
    nonconf_722 = nonconf_722 or []

    buf = BytesIO()
    styles = getSampleStyleSheet()

    # Stili “più professionali”
    styles.add(ParagraphStyle(
        name="SmallMuted",
        parent=styles["BodyText"],
        fontSize=9,
        leading=11,
        textColor=colors.grey,
    ))
    styles.add(ParagraphStyle(
        name="Mono",
        parent=styles["BodyText"],
        fontName="Courier",
        fontSize=9.5,
        leading=12,
    ))

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=36
    )

    story = []

    # =========================
    # Copertina breve
    # =========================
    story.append(_p("RELAZIONE TECNICA – INFRASTRUTTURA DI RICARICA EV", styles["Title"]))
    story.append(Spacer(1, 6))
    story.append(_p("Conforme: CEI 64-8 (Sez. 722) – Report generato dal software", styles["SmallMuted"]))
    story.append(Spacer(1, 14))

    # =========================
    # Sezione “Formule & Verifiche” (derivata)
    # =========================
    formulae = _extract_formula_lines(relazione)
    if formulae:
        story.append(_p("FORMULE E VERIFICHE (estratto)", styles["Heading2"]))
        story.append(Spacer(1, 6))
        story.append(_p("Le righe seguenti sono estratte automaticamente dalla relazione per rendere immediati calcoli e condizioni di verifica.", styles["SmallMuted"]))
        story.append(Spacer(1, 8))

        for s in formulae:
            story.append(_p(s, styles["Mono"]))
            story.append(Spacer(1, 2))

        story.append(Spacer(1, 10))

    # =========================
    # Relazione completa (testo originale)
    # =========================
    story.append(_p("RELAZIONE COMPLETA", styles["Heading2"]))
    story.append(Spacer(1, 8))
    story.append(_p(relazione, styles["BodyText"]))
    story.append(PageBreak())

    # =========================
    # Unifilare (testo/descrizione)
    # =========================
    story.append(_p("DATI PER SCHEMA UNIFILARE", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(_p("Nota: questa sezione riporta le informazioni utilizzate per lo schema unifilare.", styles["SmallMuted"]))
    story.append(Spacer(1, 10))
    story.append(_p(unifilare, styles["BodyText"]))
    story.append(PageBreak())

    # =========================
    # Planimetria
    # =========================
    story.append(_p("NOTE PLANIMETRIA", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(_p(planimetria, styles["BodyText"]))
    story.append(PageBreak())

    # =========================
    # Checklist 722 (più leggibile)
    # =========================
    story.append(_p("CHECK-LIST CEI 64-8/7 – SEZIONE 722", styles["Title"]))
    story.append(Spacer(1, 12))

    def _items_to_rows(items):
        if not items:
            return [["—", "(nessuno)"]]
        return [[str(i+1), it] for i, it in enumerate(items)]

    def add_table(title, items, accent):
        story.append(_p(title, styles["Heading2"]))
        story.append(Spacer(1, 6))
        data = _items_to_rows(items)
        tbl = Table(data, colWidths=[22, A4[0] - 36 - 36 - 22])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("TEXTCOLOR", (0,0), (-1,-1), colors.black),
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 9.8),
            ("LINEBELOW", (0,0), (-1,-1), 0.25, colors.lightgrey),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LINEBEFORE", (0,0), (0,-1), 2.0, accent),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 12))

    add_table("Esiti OK", ok_722, colors.green)
    add_table("Warning", warning_722, colors.orange)
    add_table("Non conformità", nonconf_722, colors.red)

    doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    return buf.getvalue()
