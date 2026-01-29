from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet


def _p(text: str, style):
    safe = escape(text).replace("\n", "<br/>")
    return Paragraph(safe, style)


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

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []

    story.append(_p("RELAZIONE TECNICA", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(_p(relazione, styles["BodyText"]))

    story.append(PageBreak())

    story.append(_p("DATI PER SCHEMA UNIFILARE", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(_p(unifilare, styles["BodyText"]))

    story.append(PageBreak())

    story.append(_p("NOTE PLANIMETRIA", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(_p(planimetria, styles["BodyText"]))

    story.append(PageBreak())

    story.append(_p("CHECK-LIST CEI 64-8/7 – SEZIONE 722", styles["Title"]))
    story.append(Spacer(1, 12))

    def block(title, items):
        story.append(_p(title, styles["Heading2"]))
        story.append(_p("- " + "\n- ".join(items) if items else "- (nessuno)", styles["BodyText"]))
        story.append(Spacer(1, 10))

    block("Esiti OK", ok_722)
    block("Warning", warning_722)
    block("Non conformità", nonconf_722)

    doc.build(story)
    return buf.getvalue()
