from reportlab.pdfgen import canvas


def generate_pdf_report(data, file_path):
    """
    Generates a PDF report and saves it to the specified file path.

    Args:
    data: List containing the data to be included in the report.
    file_path: The file path where the PDF should be saved.
    """
    p = canvas.Canvas(file_path)
    y_position = 800

    p.drawString(100, y_position, "Report")
    y_position -= 50

    for line in data:
        if y_position < 100:
            p.showPage()
            y_position = 800
        p.drawString(100, y_position, str(line))
        y_position -= 20

    p.showPage()
    p.save()
