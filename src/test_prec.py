# -*- coding: utf-8 -*-
from PyPDF2 import PdfReader, PdfWriter
import decimal

def main():
    decimal.getcontext().prec = 19

    with open(r"D:\temp\input.pdf", "rb") as input:
        reader = PdfReader(input)
        writer = PdfWriter()
        page = reader.pages[0]
        page.scale_by(float(decimal.Decimal(10) / decimal.Decimal(7)))
        writer.add_page(page)
        with open(r"D:\temp\output.pdf", "wb") as output:
            writer.write(output)

# Main body
if __name__ == '__main__':
    main()