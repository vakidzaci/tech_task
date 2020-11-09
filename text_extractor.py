import cv2
from tika import parser # pip install tika
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def text_extractor(file_b):
    raw = parser.from_buffer(file_b)
    return raw['content'].strip()