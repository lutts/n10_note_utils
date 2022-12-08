import pytesseract
from PIL import ImageGrab


def imToString():

	# Path of tesseract executable
    pytesseract.pytesseract.tesseract_cmd =r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    # ImageGrab-To capture the screen image in a loop.
    # Bbox used to capture a specific area.
    cap = ImageGrab.grab(bbox=(104, 1858, 299, 1896))

    # Converted the image to monochrome for it to be easily
    # read by the OCR and obtained the output String.
    tesstr = pytesseract.image_to_string(cap, lang ='eng+chi_sim')
    print(tesstr)

    cap = ImageGrab.grab(bbox=(586, 0, 2641, 57))
    tesstr = pytesseract.image_to_string(cap, lang ='eng+chi_sim')
    print(tesstr)

# Calling the function
imToString()
