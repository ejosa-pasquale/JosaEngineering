#!/usr/bin/env python3
# documenti_ev.py
# Esempio completo: header con logo + linea, footer fisso, numeri di pagina "Pagina X di Y"
# Modifica logo_path, output_pdf e la funzione create_story() per adattarlo al tuo contenuto reale.

from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib import utils

# ---------------------------
# Configurazioni (modifica qui)
# ---------------------------
output_pdf = "intestazione_ev_field_service.pdf"
logo_path = "logo_ev_field_service.png"  # <- percorso del tuo logo (modifica se necessario)

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 2 * cm
RIGHT_MARGIN = 2 * cm
TOP_MARGIN = 4 * cm     # maggiore per lasciare spazio all'intestazione
BOTTOM_MARGIN = 2.5 * cm

# Footer text (modifica con i tuoi dati)
FOOTER_TEXT_LEFT = "Ingegnere Pasquale Senese — Via Esempio 1, Milano — Tel: +39 012 3456789"

# ---------------------------
# Stili
# ---------------------------
styles = getSampleStyleSheet()
body_style = styles["Normal"]
h1_style = ParagraphStyle("Heading1", parent=styles["Heading1"], spaceAfter=12)

# ---------------------------
# Utility per immagini (mantiene aspect ratio)
# ---------------------------
def get_image_size(path, width=None, height=None):
    """
    Restituisce (width, height) calcolati per l'immagine mantenendo l'aspect ratio.
    Se width è fornito e height no -> calcola height proporzionale, e viceversa.
    """
    try:
        img = utils.ImageReader(path)
        iw, ih = img.getSize()
    except Exception:
        return (None, None)
    if width and not height:
        height = width * (ih / iw)
    if height and not width:
        width = height * (iw / ih)
    return (width, height)

# ---------------------------
# Funzioni per header/footer
# ---------------------------
def draw_header(canvas, doc):
    """
    Disegna logo, testo intestazione e linea orizzontale in cima alla pagina.
    Viene chiamata su ogni pagina tramite onFirstPage/onLaterPages.
    """
    canvas.saveState()

    # posizione logo (angolo inferiore-left)
    logo_width_desired = 6 * cm
    logo_w, logo_h = get_image_size(logo_path, width=logo_width_desired)
    if logo_w and logo_h:
        logo_x = LEFT_MARGIN
        logo_y = PAGE_HEIGHT - (1 * cm) - logo_h  # 1cm dal bordo superiore, poi logo_h in altezza
        try:
            canvas.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
        except Exception:
            # se non trova/legge logo, skip senza crash
            pass

    # testo intestazione (a destra del logo)
    text_x = LEFT_MARGIN + (logo_w or logo_width_desired) + (0.6 * cm)
    text_y_top = PAGE_HEIGHT - (1.1 * cm)  # un po' sotto il bordo superiore

    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(text_x, text_y_top, "Ingegnere Pasquale Senese")
    canvas.setFont("Helvetica", 9)
    canvas.drawString(text_x, text_y_top - 12, "Ordine Ingegneri Provincia di Milano")
    canvas.drawString(text_x, text_y_top - 24, "Numero iscrizione: 34454")

    # linea orizzontale sotto l'intestazione
    # calcola y della linea come la minima altezza occupata (logo o testo) meno piccolo offset
    lowest_header_y = min(text_y_top - 24, (logo_y if (logo_w and logo_h) else PAGE_HEIGHT - 2*cm))
    line_y = lowest_header_y - (0.4 * cm)
    canvas.setLineWidth(0.8)
    canvas.line(LEFT_MARGIN, line_y, PAGE_WIDTH - RIGHT_MARGIN, line_y)

    canvas.restoreState()

def draw_footer(canvas, doc):
    """
    Disegna il footer fisso; il numero di pagina è disegnato dalla NumberedCanvas.
    """
    canvas.saveState()
    footer_y = BOTTOM_MARGIN - (1.3 * cm)  # dentro il bottom margin

    canvas.setFont("Helvetica", 8)
    # testo a sinistra
    canvas.drawString(LEFT_MARGIN, footer_y, FOOTER_TEXT_LEFT)
    canvas.restoreState()

# ---------------------------
# Canvas personalizzata per "Pagina X di Y"
# ---------------------------
class NumberedCanvas(rl_canvas.Canvas):
    """
    Canvas che salva lo stato di ogni pagina e alla fine scrive "Pagina X di Y" su ogni pagina.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        # salva lo stato corrente della pagina (dizionario) e inizia una nuova pagina
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        # numero totale pagine
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            # disegna il numero di pagina sulla pagina corrente
            self.draw_page_number(total_pages)
            # mostra la pagina (questa chiamata scrive effettivamente la pagina nel PDF)
            super().showPage()
        super().save()

    def draw_page_number(self, total_pages):
        page_num = self.getPageNumber()
        text = f"Pagina {page_num} di {total_pages}"
        self.setFont("Helvetica", 8)
        # drawRightString: allinea a destra per rimanere dentro i margini
        x = PAGE_WIDTH - RIGHT_MARGIN
        y = BOTTOM_MARGIN - (1.3 * cm)
        self.drawRightString(x, y, text)

# ---------------------------
# Funzione che crea il contenuto (story)
# ---------------------------
def create_story():
    """
    Qui costruisci il tuo 'story' esattamente come lo fai ora in documenti_ev.py.
    Ho messo un esempio con vari paragrafi; sostituisci o estendi questa funzione
    con il codice reale che genera il contenuto del tuo PDF.
    """
    story = []

    # Esempio: titolo e paragrafi multipli per generare più pagine
    story.append(Paragraph("Relazione Tecnica - Esempio", h1_style))
    example_text = (
        "Questo paragrafo è un testo di esempio per mostrare la formattazione "
        "e l'effetto di multipli paragrafi all'interno del PDF. "
        "Sostituisci questo contenuto con il tuo story reale."
    )
    for i in range(1, 35):
        story.append(Paragraph(f"<b>Sezione {i}</b><br/>{example_text}", body_style))
        story.append(Spacer(1, 0.4 * cm))

    # Se vuoi forzare una nuova pagina: story.append(PageBreak())
    return story

# ---------------------------
# Creazione del documento e build
# ---------------------------
def build_pdf():
    # crea il template SimpleDocTemplate (assicurati topMargin sufficientemente grande)
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=RIGHT_MARGIN,
        leftMargin=LEFT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN
    )

    # ottieni lo story (sostituisci create_story con la tua logica se necessario)
    story = create_story()

    # build con header/footer e canvas personalizzato per il numero pagine
    doc.build(
        story,
        onFirstPage=lambda canv, doc_obj: (draw_header(canv, doc_obj), draw_footer(canv, doc_obj)),
        onLaterPages=lambda canv, doc_obj: (draw_header(canv, doc_obj), draw_footer(canv, doc_obj)),
        canvasmaker=NumberedCanvas
    )

    print(f"PDF creato: {output_pdf}")

# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    build_pdf()
