from IPython.display import display, Markdown
import pdfplumber


class PDFLoader:
    def __init__(self):
        pass

    def extract_text_from_pdf(self, pdf_path):
        """
            Extract entire text from a PDF file using pdfplumber.
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"

            return text
        
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None
    


# Global instance of PDFLoader
pdf_loader = PDFLoader()