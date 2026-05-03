"""Branded PDF generation for Fisco Facile guides.

Generated on-the-fly with reportlab and styled to match the site identity.
"""
from datetime import datetime, timezone
from io import BytesIO
import os

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ACCENT = HexColor("#CCFF00")
DARK = HexColor("#09090B")
SURFACE = HexColor("#18181B")
LINE = HexColor("#27272A")
MUTED = HexColor("#71717A")
PANEL = HexColor("#F4F4F5")
TEXT = HexColor("#18181B")


def _support_email() -> str:
    return os.environ.get("SUPPORT_EMAIL", "supporto@fiscofacile.it")


def _styles():
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=ACCENT,
            spaceAfter=10,
            alignment=TA_LEFT,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=29,
            leading=34,
            textColor=white,
            spaceAfter=14,
            alignment=TA_LEFT,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=18,
            textColor=HexColor("#D4D4D8"),
            spaceAfter=18,
            alignment=TA_LEFT,
        ),
        "eyebrow": ParagraphStyle(
            "eyebrow",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=MUTED,
            spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=TEXT,
            spaceBefore=10,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            textColor=TEXT,
            spaceBefore=8,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=TEXT,
            spaceAfter=7,
            alignment=TA_LEFT,
        ),
        "body_muted": ParagraphStyle(
            "body_muted",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=MUTED,
            spaceAfter=7,
            alignment=TA_LEFT,
        ),
        "card_title": ParagraphStyle(
            "card_title",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=white,
        ),
        "card_value": ParagraphStyle(
            "card_value",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=HexColor("#D4D4D8"),
        ),
        "step_num": ParagraphStyle(
            "step_num",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=14,
            textColor=black,
            alignment=TA_LEFT,
        ),
        "step_text": ParagraphStyle(
            "step_text",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=14.5,
            textColor=TEXT,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7,
            textColor=MUTED,
            alignment=TA_LEFT,
        ),
    }


def _draw_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, A4[1] - 0.45 * cm, A4[0], 0.45 * cm, fill=1, stroke=0)
    canvas.setFillColor(SURFACE)
    canvas.roundRect(2 * cm, 2 * cm, A4[0] - 4 * cm, 2.7 * cm, 16, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2.3 * cm, 4.05 * cm, "Brand guide digitale")
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(2.3 * cm, 3.25 * cm, "Fisco")
    canvas.setFillColor(ACCENT)
    canvas.drawString(4.25 * cm, 3.25 * cm, ".")
    canvas.setFillColor(white)
    canvas.drawString(4.7 * cm, 3.25 * cm, "Facile")
    canvas.setFillColor(HexColor("#A1A1AA"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(
        2.3 * cm,
        2.55 * cm,
        "Guide operative pensate per essere chiare, veloci e subito utili.",
    )
    canvas.restoreState()


def _draw_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, A4[1] - 1.1 * cm, A4[0], 1.1 * cm, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(2 * cm, A4[1] - 0.72 * cm, "FISCO FACILE")
    canvas.setFillColor(white)
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 0.72 * cm, f"Pag. {doc.page}")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(
        2 * cm,
        0.85 * cm,
        "Documento ad uso personale. Le procedure complesse richiedono sempre verifica professionale.",
    )
    canvas.restoreState()


def _accent_bullet(text: str, styles) -> Paragraph:
    return Paragraph(f'<font color="#CCFF00">&#9679;</font> {text}', styles["body"])


def _cover_meta_table(package_name: str, buyer_email: str | None, styles):
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    rows = [[
        Paragraph("Pacchetto", styles["card_title"]),
        Paragraph("Emissione", styles["card_title"]),
        Paragraph("Supporto", styles["card_title"]),
    ], [
        Paragraph(package_name.upper(), styles["card_value"]),
        Paragraph(today, styles["card_value"]),
        Paragraph(_support_email(), styles["card_value"]),
    ]]
    if buyer_email:
        rows.extend([[
            Paragraph("Licenza", styles["card_title"]),
            Paragraph("Acquirente", styles["card_title"]),
            Paragraph("Formato", styles["card_title"]),
        ], [
            Paragraph("Uso personale", styles["card_value"]),
            Paragraph(buyer_email, styles["card_value"]),
            Paragraph("PDF scaricabile", styles["card_value"]),
        ]])

    table = Table(rows, colWidths=[5.1 * cm, 5.1 * cm, 5.1 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _summary_table(styles):
    rows = [[
        Paragraph("Tempo medio", styles["eyebrow"]),
        Paragraph("Obiettivo", styles["eyebrow"]),
        Paragraph("Esito atteso", styles["eyebrow"]),
    ], [
        Paragraph("5-20 minuti", styles["body"]),
        Paragraph("Seguire la pratica senza incertezza", styles["body"]),
        Paragraph("Procedura conclusa e ricevuta salvata", styles["body"]),
    ]]
    table = Table(rows, colWidths=[5.1 * cm, 5.1 * cm, 5.1 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("BACKGROUND", (0, 1), (-1, 1), white),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#E4E4E7")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E4E4E7")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _inside_card(styles):
    bullets = [
        "mappa rapida della procedura",
        "requisiti da preparare prima di iniziare",
        "step numerati da seguire in ordine",
        "errori frequenti e note finali utili",
    ]
    rows = [[Paragraph("Dentro questa guida", styles["h2"])]]
    for bullet in bullets:
        rows.append([_accent_bullet(bullet, styles)])

    table = Table(rows, colWidths=[15.3 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FCFDF7")),
        ("BOX", (0, 0), (-1, -1), 1, ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _step_table(items, styles):
    rows = []
    for index, text in enumerate(items, start=1):
        rows.append([
            Paragraph(str(index), styles["step_num"]),
            Paragraph(text, styles["step_text"]),
        ])

    table = Table(rows, colWidths=[1.1 * cm, 14.2 * cm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), ACCENT),
        ("BACKGROUND", (1, 0), (1, -1), white),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#D4D4D8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E4E4E7")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _note_box(title: str, text: str, styles, accent_color=ACCENT):
    rows = [
        [Paragraph(title, styles["h2"])],
        [Paragraph(text, styles["body"])],
    ]
    table = Table(rows, colWidths=[15.3 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 1, accent_color),
        ("LINEBEFORE", (0, 0), (0, -1), 6, accent_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def generate_guide_pdf(
    title: str,
    package_name: str,
    guide_index: int,
    total: int,
    buyer_email: str = None,
) -> bytes:
    """Generate a branded PDF guide aligned with the website visual identity."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.1 * cm,
        bottomMargin=1.8 * cm,
        title=title,
        author="Fisco Facile",
    )
    s = _styles()
    story = []

    story.append(Spacer(1, 3.2 * cm))
    story.append(Paragraph(
        f"GUIDA {guide_index:02d} / {total:02d}  |  {package_name.upper()}",
        s["cover_kicker"],
    ))
    story.append(Paragraph(title, s["cover_title"]))
    story.append(Paragraph(
        "Una guida operativa pensata come il sito: diretta, leggibile e subito utile. "
        "Niente linguaggio tecnico superfluo, solo passaggi chiari e azionabili.",
        s["cover_subtitle"],
    ))
    story.append(Spacer(1, 0.6 * cm))
    story.append(_cover_meta_table(package_name, buyer_email, s))
    story.append(PageBreak())

    story.append(Paragraph("Panoramica rapida", s["h1"]))
    story.append(Paragraph(
        "Prima di iniziare, qui sotto trovi i tre punti chiave della pratica e una mappa veloce del contenuto.",
        s["body_muted"],
    ))
    story.append(_summary_table(s))
    story.append(Spacer(1, 0.45 * cm))
    story.append(_inside_card(s))
    story.append(Spacer(1, 0.45 * cm))

    story.append(Paragraph("1. A cosa serve questa procedura", s["h1"]))
    story.append(Paragraph(
        f"Questa guida ti accompagna nell'esecuzione di <b>{title}</b>. "
        "L'obiettivo e toglierti attrito e dubbi durante i passaggi principali, "
        "cosi puoi chiudere la pratica in autonomia nei casi standard.",
        s["body"],
    ))
    story.append(Paragraph(
        "Quando la situazione e complessa, resta comunque consigliato il confronto con un commercialista o con un consulente abilitato.",
        s["body_muted"],
    ))

    story.append(Paragraph("2. Cosa preparare prima di iniziare", s["h1"]))
    for bullet in [
        "SPID livello 2 oppure CIE con PIN attivo.",
        "Codice fiscale e i documenti specifici della pratica.",
        "Un indirizzo email valido per eventuali ricevute o conferme.",
        "5 minuti di calma per seguire i passaggi senza interruzioni.",
    ]:
        story.append(_accent_bullet(bullet, s))

    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("3. Procedura step by step", s["h1"]))
    story.append(_step_table([
        "Accedi al portale ufficiale collegato alla pratica e apri la sezione corretta.",
        "Effettua il login con le credenziali richieste e verifica i tuoi dati principali.",
        "Compila i campi obbligatori seguendo l'ordine mostrato dalla piattaforma.",
        "Controlla il riepilogo finale con attenzione prima di confermare.",
        "Invia la pratica e salva subito la ricevuta o il protocollo generato.",
    ], s))

    story.append(Spacer(1, 0.45 * cm))
    story.append(_note_box(
        "Errori comuni da evitare",
        "Gli errori piu frequenti sono tre: credenziali non aggiornate, IBAN o dati anagrafici inseriti male e mancato controllo del riepilogo finale. Bastano pochi secondi di verifica per evitare rifacimenti o scarti.",
        s,
        accent_color=HexColor("#A3A3A3"),
    ))

    story.append(Spacer(1, 0.45 * cm))
    story.append(_note_box(
        "Riferimenti e supporto",
        f"La guida e aggiornata al 2026 e segue la logica operativa dei portali ufficiali. Se hai bisogno di orientamento, puoi scrivere a {_support_email()}.",
        s,
    ))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("FAQ rapide", s["h1"]))
    story.append(Paragraph(
        "<b>Posso rifare la procedura se sbaglio?</b> Dipende dal servizio, ma nella maggior parte dei casi puoi reinviare o correggere prima della chiusura definitiva.",
        s["body"],
    ))
    story.append(Paragraph(
        "<b>Devo stampare tutto?</b> No. Ti conviene salvare il PDF e stampare solo la ricevuta o i passaggi che vuoi tenere sottomano.",
        s["body"],
    ))

    doc.build(story, onFirstPage=_draw_cover, onLaterPages=_draw_page)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
