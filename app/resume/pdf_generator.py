import io
import logging
from flask import current_app

logger = logging.getLogger(__name__)

def generate_pdf(html_content, stylesheets=None):
    """
    Renders HTML content into a PDF binary string.
    Per project specifications, WeasyPrint is attempted first.
    If WeasyPrint native libraries are missing (common on Windows environments),
    it seamlessly falls back to pure-Python xhtml2pdf.
    """
    # 1. Attempt generation with WeasyPrint
    try:
        from weasyprint import HTML, CSS
        css_objects = [CSS(string=s) for s in stylesheets] if stylesheets else []
        pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=css_objects)
        return pdf_bytes
    except (ImportError, OSError) as e:
        logger.warning(f"WeasyPrint native library unavailable ({e}). Using xhtml2pdf engine fallback.")
    except Exception as e:
        logger.warning(f"WeasyPrint rendering encountered an error ({e}). Trying fallback.")

    # 2. Seamless Fallback with xhtml2pdf
    try:
        from xhtml2pdf import pisa
        output_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=output_buffer)
        if pisa_status.err:
            raise RuntimeError(f"xhtml2pdf encountered errors during PDF rendering: {pisa_status.err}")
        return output_buffer.getvalue()
    except Exception as e:
        logger.error(f"PDF generation failed completely: {e}")
        raise RuntimeError(f"PDF generation failed: {e}")
