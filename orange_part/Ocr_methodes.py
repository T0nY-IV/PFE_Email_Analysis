import spacy
from PIL import Image
from spacy_layout import spaCyLayout
import pytesseract 


def Ocr_pdf_Init():
    nlp = spacy.load("en_core_web_sm") #for frensh use fr_core_news_md / for english use en_core_web_sm
    layout = spaCyLayout(nlp)
    return layout

def Ocr_pdf(path, layout):
    doc_content = layout(path)
    return doc_content #you can use .text(to see text) | ._.markdown(for more details such as titles, pictures and tables places) | ._.tables (to extarct tables) | ._.pages[n-1] (select the page you want form n pages)

def Ocr_picture(path):
    return pytesseract.image_to_string(Image.open(path))

