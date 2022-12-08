# -*- coding: utf-8 -*-

from PyPDF2 import PdfWriter, PdfReader
import decimal

def main():
    reader1 = PdfReader(r"D:\temp\test.pdf")
    reader2 = PdfReader(r"D:\temp\test.pdf")
    writer = PdfWriter()

    decimal.getcontext().prec = 19

    for n in range(len(reader1.pages)):
        if n % 2 == 0:
            ratio = decimal.Decimal(1049 / 2056)
        else:
            ratio = decimal.Decimal(1014 / 2056)

        left_side = reader1.pages[n]
        print(left_side.mediabox.right)
        left_side.mediabox.upper_right = (
            left_side.mediabox.right * ratio,
            left_side.mediabox.top,
        )
        writer.add_page(left_side)

        right_side = reader2.pages[n]
        right_side.mediabox.upper_left = (
            right_side.mediabox.right * ratio,
            right_side.mediabox.top,
        )
        writer.add_page(right_side)

    # write to document-output.pdf
    with open(r"D:\temp\test_output.pdf", "wb") as fp:
        writer.write(fp)


# Main body
if __name__ == '__main__':
    main()