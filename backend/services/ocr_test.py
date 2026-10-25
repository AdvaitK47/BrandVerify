import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

print(pytesseract.get_tesseract_version())

text = pytesseract.image_to_string(Image.open("samples/poster1.jpg"))
print(text)