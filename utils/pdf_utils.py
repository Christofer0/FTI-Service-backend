# utils/pdf_utils.py
import os
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from flask import current_app

# def add_signature_to_pdf(pdf_path, signature_path, qr_path, output_path,dosen_nama):
#     """
#     Menambahkan tanda tangan dan QR code ke PDF
    
#     Args:
#         pdf_path: Path file PDF asli
#         signature_path: Path file PNG tanda tangan  
#         qr_path: Path file PNG QR code
#         output_path: Path output file PDF yang sudah ditandatangani
    
#     Returns:
#         tuple: (success: bool, error_message: str)
#     """
#     try:
#         # Validasi file exist
#         if not os.path.exists(pdf_path):
#             return False, f"PDF file not found: {pdf_path}"
#         if not os.path.exists(signature_path):
#             return False, f"Signature file not found: {signature_path}"
#         if not os.path.exists(qr_path):
#             return False, f"QR code file not found: {qr_path}"
        
#         # Baca PDF asli
#         pdf_reader = PdfReader(pdf_path)
#         pdf_writer = PdfWriter()
        
#         # Copy semua halaman kecuali halaman terakhir
#         total_pages = len(pdf_reader.pages)
#         for i in range(total_pages - 1):
#             pdf_writer.add_page(pdf_reader.pages[i])
        
#         # Ambil halaman terakhir
#         last_page = pdf_reader.pages[-1]
        
#         # Buat overlay dengan tanda tangan dan QR code
#         overlay_buffer = BytesIO()
#         overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=letter)
        
#         # Posisi tanda tangan (kiri bawah)
#         signature_width = 120
#         signature_height = 60
#         signature_x = 50
#         signature_y = 80
        
#         # Posisi QR code (di sebelah kanan tanda tangan)
#         qr_size = 60
#         qr_x = signature_x + signature_width + 20
#         qr_y = signature_y
        
#         # Tambahkan tanda tangan
#         overlay_canvas.drawImage(
#             signature_path, 
#             signature_x, 
#             signature_y, 
#             width=signature_width, 
#             height=signature_height,
#             preserveAspectRatio=True
#         )
        
#         # Tambahkan QR code
#         overlay_canvas.drawImage(
#             qr_path, 
#             qr_x, 
#             qr_y, 
#             width=qr_size, 
#             height=qr_size
#         )
        
#         # Tambahkan text
#         overlay_canvas.setFont("Helvetica", 8)
#         overlay_canvas.drawString(signature_x, signature_y - 15, f"{dosen_nama}")
#         overlay_canvas.drawString(qr_x, qr_y - 15, "QR Verifikasi")
        
#         overlay_canvas.save()
#         overlay_buffer.seek(0)
        
#         # Gabungkan dengan halaman terakhir
#         overlay_pdf = PdfReader(overlay_buffer)
#         overlay_page = overlay_pdf.pages[0]
#         last_page.merge_page(overlay_page)
#         pdf_writer.add_page(last_page)
        
#         # Pastikan direktori output ada
#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
#         # Simpan hasil
#         with open(output_path, 'wb') as output_file:
#             pdf_writer.write(output_file)
        
#         return True, None
        
#     except Exception as e:
#         return False, f"Error processing PDF: {str(e)}"

def add_signature_to_pdf(
    pdf_path,
    signature_path,
    qr_path,
    output_path,
    dosen_nama,
    jabatan_dosen,
    nama_jenis_permohonan,
    signed_at
):
    try:
        if not os.path.exists(pdf_path):
            return False, f"PDF file not found: {pdf_path}"
        if not os.path.exists(signature_path):
            return False, f"Signature file not found: {signature_path}"
        if not os.path.exists(qr_path):
            return False, f"QR code file not found: {qr_path}"
        
        if nama_jenis_permohonan.lower() == "review":
            pass
            #  tambahkan tulisan di bawah jabatan. seperti dibawah ini
            #  silahkan mengirimkan transkip nilai kembali saat akan
            #  mendaftar yudisium agar mendapatkan tanda tangan Kaprodi

        pdf_reader = PdfReader(pdf_path)
        pdf_writer = PdfWriter()

        for i in range(len(pdf_reader.pages) - 1):
            pdf_writer.add_page(pdf_reader.pages[i])

        last_page = pdf_reader.pages[-1]

        overlay_buffer = BytesIO()
        overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=letter)

        # ================= POSISI =================
        signature_x = 50
        signature_y = 80
        signature_width = 120
        signature_height = 60

        qr_size = 60
        qr_x = signature_x + signature_width + 40
        qr_y = signature_y

        text_y = signature_y + signature_height + 10

        # ================= TEXT ATAS =================
        overlay_canvas.setFont("Helvetica", 9)

        # Nama jenis permohonan (kiri)
        overlay_canvas.drawString(
            signature_x,
            text_y,
            f"ACC {nama_jenis_permohonan} ({signed_at})"
        )
        



        # ================= TTD =================
        overlay_canvas.drawImage(
            signature_path,
            signature_x,
            signature_y,
            width=signature_width,
            height=signature_height,
            preserveAspectRatio=True
        )

        # ================= QR =================
        overlay_canvas.drawImage(
            qr_path,
            qr_x,
            qr_y,
            width=qr_size,
            height=qr_size
        )

        # ================= TEXT BAWAH =================
        overlay_canvas.setFont("Helvetica", 8)

        name_y = signature_y - 20
        line_y = name_y - 5
        jabatan_y = line_y - 10

        # Nama dosen
        overlay_canvas.drawString(signature_x, name_y, dosen_nama)

        # Garis bawah (pakai line)
        text_width = overlay_canvas.stringWidth(dosen_nama, "Helvetica", 8)
        overlay_canvas.line(signature_x, line_y, signature_x + text_width, line_y)

        # Jabatan dosen
        overlay_canvas.drawString(signature_x, jabatan_y, jabatan_dosen)

        # Khusus REVIEW
        overlay_canvas.drawString(signature_x, jabatan_y, jabatan_dosen)
        # ================= CATATAN KHUSUS REVIEW =================
        if nama_jenis_permohonan.lower() == "review":
            overlay_canvas.setFont("Helvetica", 7)

            review_notes = [
                "Silahkan mengirimkan transkip nilai kembali saat akan",
                "mendaftar yudisium agar mendapatkan tanda tangan Kaprodi"
            ]

            note_y = jabatan_y - 12
            for line in review_notes:
                overlay_canvas.drawString(signature_x, note_y, line)
                note_y -= 10

        # ================= LABEL QR (CENTER) =================
        label_text = "Verify"
        overlay_canvas.setFont("Helvetica", 8)

        text_width = overlay_canvas.stringWidth(label_text, "Helvetica", 8)
        label_x = qr_x + (qr_size / 2) - (text_width / 2)
        label_y = qr_y - 15

        overlay_canvas.drawString(label_x, label_y, label_text)

        overlay_canvas.save()
        overlay_buffer.seek(0)

        overlay_pdf = PdfReader(overlay_buffer)
        last_page.merge_page(overlay_pdf.pages[0])
        pdf_writer.add_page(last_page)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pdf_writer.write(f)

        return True, None

    except Exception as e:
        return False, f"Error processing PDF: {str(e)}"

def get_full_file_path(relative_path, base_folder='uploads'):
    """
    Get full file path from relative path
    
    Args:
        relative_path: Path relatif file (misal: 'permohonan/file.pdf' atau 'qr_xxx.png')
        base_folder: 'uploads', 'signed', atau 'qr_codes'
    
    Returns:
        str: Full absolute path
    """
    if base_folder == 'uploads':
        base_path = current_app.config['UPLOAD_FOLDER']
    elif base_folder == 'signed':
        base_path = current_app.config['UPLOAD_SIGNED']  
    elif base_folder == 'qr_codes':
        base_path = current_app.config['QR_CODE_FOLDER']
    else:
        base_path = current_app.config['UPLOAD_FOLDER']
    
    return os.path.join(base_path, relative_path)