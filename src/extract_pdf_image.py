# -*- coding: utf-8 -*-
from PyPDF2 import PdfReader

reader = PdfReader(r"D:\Data\Psychology\Psychology and Life 20th.pdf")

page = reader.pages[237]
count = 0

print(page.extract_text())
print("num images: " + str(len(page.images)))

for image_file_object in page.images:
    with open(str(count) + image_file_object.name, "wb") as fp:
        fp.write(image_file_object.data)
        count += 1