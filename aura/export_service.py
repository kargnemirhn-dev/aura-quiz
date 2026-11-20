import io
import time
from typing import List, Dict, Any
from aura.config import settings

# Pre-import openpyxl & reportlab for zero latency on requests
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_excel_report(players: List[Dict[str, Any]]) -> bytes:
    """Generates a professional XLSX Excel report for the summit quiz results"""
    if not OPENPYXL_AVAILABLE:
        return _generate_csv_fallback(players)

    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Zirve Sıralaması"

        # Title Block
        ws.merge_cells("A1:F1")
        title_cell = ws["A1"]
        title_cell.value = f"{settings.PROJECT_NAME} - Resmi Sonuç Raporu"
        title_cell.font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="1E1B4B", end_color="1E1B4B", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 35

        # Subtitle
        ws.merge_cells("A2:F2")
        sub_cell = ws["A2"]
        sub_cell.value = f"Oluşturulma Tarihi: {time.strftime('%d.%m.%Y %H:%M:%S')} | Toplam Katılımcı: {len(players)}"
        sub_cell.font = Font(name="Arial", size=9, italic=True, color="64748B")
        sub_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 20

        # Headers
        headers = ["Sıra", "Avatar", "İsim Soyisim", "Okul / Kurum", "Toplam Puan", "Seri"]
        ws.append([]) # row 3 blank
        ws.append(headers) # row 4
        ws.row_dimensions[4].height = 25

        header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
        header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style='thin', color="CBD5E1"),
            right=Side(style='thin', color="CBD5E1"),
            top=Side(style='thin', color="CBD5E1"),
            bottom=Side(style='thin', color="CBD5E1")
        )

        for col_idx in range(1, 7):
            cell = ws.cell(row=4, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        # Rows
        if not players:
            ws.append(["-", "🚀", "Henüz katılımcı kaydı yok", "-", 0, "0x"])
            r = ws.max_row
            for col_idx in range(1, 7):
                ws.cell(row=r, column=col_idx).border = thin_border
        else:
            for p in players:
                row_data = [
                    p.get("rank", 0),
                    p.get("avatar", "🚀"),
                    p.get("name", ""),
                    p.get("school", "Bağımsız"),
                    p.get("score", 0),
                    f"{p.get('streak', 0)}x"
                ]
                ws.append(row_data)
                current_row = ws.max_row
                ws.row_dimensions[current_row].height = 22

                # Highlight Top 3
                rank = p.get("rank", 0)
                row_fill = None
                if rank == 1:
                    row_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid") # Gold
                elif rank == 2:
                    row_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid") # Silver
                elif rank == 3:
                    row_fill = PatternFill(start_color="FFEDD5", end_color="FFEDD5", fill_type="solid") # Bronze

                for col_idx in range(1, 7):
                    c = ws.cell(row=current_row, column=col_idx)
                    c.border = thin_border
                    c.font = Font(name="Arial", size=10, bold=(rank <= 3))
                    if row_fill:
                        c.fill = row_fill
                    if col_idx in (1, 2, 5, 6):
                        c.alignment = Alignment(horizontal="center", vertical="center")
                    else:
                        c.alignment = Alignment(horizontal="left", vertical="center")

        # Auto column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    except Exception:
        return _generate_csv_fallback(players)


def _generate_csv_fallback(players: List[Dict[str, Any]]) -> bytes:
    """UTF-8 BOM CSV Fallback (Native Excel Compatible)"""
    output = io.StringIO()
    output.write('\ufeff')
    output.write(f'"{settings.PROJECT_NAME} - Sıralama Raporu"\n')
    output.write(f'"Tarih: {time.strftime("%d.%m.%Y %H:%M:%S")}"\n\n')
    output.write("Sıra;Avatar;İsim Soyisim;Okul / Kurum;Puan;Seri\n")
    for p in players:
        output.write(f"{p.get('rank')};{p.get('avatar')};\"{p.get('name')}\";\"{p.get('school')}\";{p.get('score')};{p.get('streak')}\n")
    return output.getvalue().encode("utf-8-sig")


def generate_pdf_report(players: List[Dict[str, Any]]) -> bytes:
    """Generates an official PDF report for summit quiz results using ReportLab"""
    if not REPORTLAB_AVAILABLE:
        # Minimal valid PDF fallback if library missing
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n206\n%%EOF\n"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E1B4B'),
        alignment=1 # Center
    )
    sub_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        alignment=1 # Center
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0F172A')
    )

    elements = []

    # Header
    elements.append(Paragraph(settings.PROJECT_NAME, title_style))
    elements.append(Paragraph("Aura Bilgi Yarışması - Resmi Sonuç Belgesi", sub_style))
    elements.append(Paragraph(f"Tarih: {time.strftime('%d.%m.%Y %H:%M')} | Toplam Yarışmacı: {len(players)}", sub_style))
    elements.append(Spacer(1, 16))

    # Table Data
    table_data = [["Sıra", "İsim Soyisim", "Okul / Kurum", "Puan", "Seri"]]
    if not players:
        table_data.append(["-", Paragraph("Henüz katılımcı kaydı bulunmuyor", cell_style), Paragraph("Bağımsız", cell_style), "0 P", "0x"])
    else:
        for p in players[:50]:
            table_data.append([
                f"#{p.get('rank', 0)}",
                Paragraph(p.get('name', ''), cell_style),
                Paragraph(p.get('school', 'Bağımsız'), cell_style),
                f"{p.get('score', 0)} P",
                f"{p.get('streak', 0)}x"
            ])

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (4, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]

    # Only apply highlight to rows that exist
    num_rows = len(table_data)
    if num_rows > 1:
        style_cmds.append(('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#FEF3C7'))) # 1st
    if num_rows > 2:
        style_cmds.append(('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#F1F5F9'))) # 2nd
    if num_rows > 3:
        style_cmds.append(('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#FFEDD5'))) # 3rd

    t = Table(table_data, colWidths=[45, 175, 195, 65, 45])
    t.setStyle(TableStyle(style_cmds))
    elements.append(t)

    # Footer note
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Bu belge AI ERA: Teknoloji & Girişimcilik Zirvesi yarışma motoru tarafından dijital olarak üretilmiştir.", sub_style))

    doc.build(elements)
    return buffer.getvalue()
