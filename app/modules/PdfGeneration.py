from flask import Flask, send_file
from fpdf import FPDF
import io
import os


class PdfGeneration:
    @staticmethod
    def header(pdf):
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'PDF Header', 0, 1, 'C')

    @staticmethod
    def footer(pdf):
        pdf.set_y(-15)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 10, f'Page {pdf.page_no()}', 0, 0, 'C')

    @staticmethod
    def chapter_title(pdf, chapter_title):
        pdf.set_font('Arial', 'B', 12)
        pdf.multi_cell(0, 10, chapter_title)
        pdf.ln(10)

    @staticmethod
    def chapter_body(pdf, body):
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 10, body)
        pdf.ln()

    @staticmethod
    def generate_pdf(data):
        pdf = FPDF()
        pdf.add_page()

        PdfGeneration.header(pdf)
        for item in data:
            PdfGeneration.chapter_title(pdf, item['item'])
            PdfGeneration.chapter_body(pdf, item['answer'])
            # PdfGeneration.chapter_body(pdf, item['source_documents'])
            # PdfGeneration.chapter_body(pdf, item['metadata'])
        
        
        PdfGeneration.footer(pdf)

        pdf_output = io.BytesIO()
        pdf_string = pdf.output(dest='S').encode('latin1')  # Generate PDF as a string
        pdf_output.write(pdf_string)
        pdf_output.seek(0)

         # Specify the folder path to save the PDF
        folder_path = '/usr/app/app/data'
        file_path = os.path.join(folder_path, 'output.pdf')
        
        # Save the PDF file
        with open(file_path, 'wb') as f:
            f.write(pdf_string)

        return 'data'#send_file(file_path, as_attachment=True)
