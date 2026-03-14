import spacy
from spacy_layout import spaCyLayout
nlp = spacy.load("en_core_web_sm") #for frensh use fr_core_news_md / for english use en_core_web_sm
layout = spaCyLayout(nlp)
doc = layout("C:/Users/loq/Downloads/emails_output/attachments/9576/Rapport.pdf")
print(doc.text)