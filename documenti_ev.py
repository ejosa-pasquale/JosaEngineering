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

"""
intestazione_professionale.py

Genera un PDF A4 con intestazione professionale (logo + testo).
Dipendenze: reportlab
Installazione:
    pip install reportlab
Uso:
    python intestazione_professionale.py
oppure importare la funzione generate_letterhead() in altro script.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import os
import math

PAGE_WIDTH, PAGE_HEIGHT = A4

def _scale_image_to_fit(img_path, max_w, max_h):
    """
    Restituisce (width, height) scalati mantenendo aspect ratio per
    adattare un'immagine nelle dimensioni max_w x max_h.
    """
    try:
        img = ImageReader(img_path)
        iw, ih = img.getSize()
    except Exception:
        return None, None
    if iw == 0 or ih == 0:
        return None, None
    ratio = min(max_w / iw, max_h / ih)
    return iw * ratio, ih * ratio

def generate_letterhead(
    output_path: str,
    logo_path: str,
    company_name: str = "EV Field Service",
    vat_text: str = "P.IVA IT03823770783",
    title_line: str = "Ingegnere Pasquale Senese",
    order_line: str = "Ordine Ingegneri Provincia di Milano",
    register_line: str = "Numero iscrizione: 34454",
    page_size=A4,
    margin_mm: float = 20):
    """
    Genera un PDF A4 con intestazione professionale.
    - output_path: percorso file PDF da scrivere
    - logo_path: percorso file immagine del logo (png/jpg)
    - gli altri parametri sono testi visualizzati in intestazione
    """
    page_w, page_h = page_size
    margin = margin_mm * mm

    c = canvas.Canvas(output_path, pagesize=page_size)

    # ---- Header region dimensions ----
    header_height = 40 * mm  # altezza riservata all'intestazione
    logo_max_height = header_height * 0.8
    logo_max_width = 60 * mm

    # Coordinates: origin (0,0) bottom-left
    header_y_top = page_h - margin  # top inside margin
    header_y_bottom = header_y_top - header_height

    # Draw subtle horizontal rule under header
    rule_y = header_y_bottom + 6 * mm
    c.setStrokeColor(colors.HexColor("#d7dbe0"))
    c.setLineWidth(0.6)
    c.line(margin, rule_y, page_w - margin, rule_y)

    # ---- Logo placement (left) ----
    logo_x = margin
    # compute scaled size
    logo_w, logo_h = _scale_image_to_fit(logo_path, logo_max_width, logo_max_height)
    if logo_w and logo_h:
        # vertically center logo within header area
        logo_y = header_y_bottom + (header_height - logo_h) / 2
        try:
            c.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
        except Exception:
            # If drawImage fails, ignore and continue without logo
            logo_w, logo_h = 0, 0
    else:
        # no logo found or not readable
        logo_w, logo_h = 0, 0

    # ---- Text block (right of logo) ----
    text_block_x = logo_x + (logo_w + 8 * mm if logo_w else 0)
    text_block_width = page_w - margin - text_block_x

    # Fonts and sizes
    company_font = "Helvetica-Bold"
    company_font_size = 18
    vat_font = "Helvetica"
    vat_font_size = 9
    title_font = "Helvetica-Bold"
    title_font_size = 10
    meta_font = "Helvetica"
    meta_font_size = 9

    # Company name: align top-left of text block
    text_cursor_y = header_y_top - (company_font_size)  # starting y
    # Slightly nudge down so company name sits visually centered with logo
    text_cursor_y -= 6

    c.setFont(company_font, company_font_size)
    c.setFillColor(colors.HexColor("#0e1921"))  # dark navy
    # Wrap company name if too long: simple approach using split
    c.drawString(text_block_x, text_cursor_y, company_name)

    # VAT text under company name
    text_cursor_y -= (company_font_size + 4)
    c.setFont(vat_font, vat_font_size)
    c.setFillColor(colors.HexColor("#333a40"))
    c.drawString(text_block_x, text_cursor_y, vat_text)

    # On a new line, center the engineer/title block below the rule (or aligned right)
    # We'll center this block horizontally in page width (classic professional look)
    center_x = page_w / 2

    # Compose lines for center block
    center_lines = [
        title_line,
        order_line,
        register_line
    ]
    # vertical placement: slightly below the rule line
    center_start_y = rule_y - 14 * mm

    # Draw each centered line
    c.setFillColor(colors.HexColor("#0e1921"))
    c.setFont(title_font, title_font_size)
    c.drawCentredString(center_x, center_start_y + 12, center_lines[0])

    c.setFont(meta_font, meta_font_size)
    c.setFillColor(colors.HexColor("#4b5560"))
    c.drawCentredString(center_x, center_start_y - 2, center_lines[1])
    c.drawCentredString(center_x, center_start_y - 12, center_lines[2])

    # ---- Optional: small footer with page info (disabled by default) ----
    # footer_text = "EV Field Service - intestazione ufficiale"
    # c.setFont("Helvetica-Oblique", 7)
    # c.setFillColor(colors.HexColor("#9aa3ab"))
    # c.drawRightString(page_w - margin, margin / 2, footer_text)

    # Finalize PDF (single blank page with header)
    c.showPage()
    c.save()
    print(f"PDF generato: {output_path}")

if __name__ == "__main__":
    # esempio di utilizzo
    logo_file = "logo_ev_field_service.png"   # <<-- metti qui il percorso reale del logo
    output_file = "intestazione_ev_field_service_professionale.pdf"

    # se il logo non si trova, il codice genera comunque il PDF senza l'immagine
    if not os.path.isfile(logo_file):
        print(f"ATTENZIONE: logo non trovato in '{logo_file}'. Il PDF verrà comunque generato senza logo.")
    generate_letterhead(
        output_path=output_file,
        logo_path=logo_file,
        company_name="EV Field Service",
        vat_text="P.IVA IT03823770783",
        title_line="Ingegnere Pasquale Senese",
        order_line="Ordine Ingegneri Provincia di Milano",
        register_line="Numero iscrizione: 34454"
    )
