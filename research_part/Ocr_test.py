from completed_project.Ocr_methodes import Ocr_pdf, Ocr_picture, Ocr_pdf_Init

layout = Ocr_pdf_Init()
pdf_content = Ocr_pdf("C:/Users/loq/Downloads/emails_output/attachments/9576/Rapport.pdf", layout)
print(f"{pdf_content._.markdown}")
print("\n\n-----------------------------------\n\n")
pic_content = Ocr_picture("D:/studying/3eme info(DSI33)/PFE/emails_output/images/9833/Asset11.png")
print(f"{pic_content}")