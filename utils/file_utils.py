# utils/file_utils.py
import os
import uuid
from PIL import Image
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename:
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def generate_unique_filename(original_filename):
    """Generate unique filename"""
    if not original_filename:
        return None
    
    # Get file extension
    ext = ''
    if '.' in original_filename:
        ext = '.' + original_filename.rsplit('.', 1)[1].lower()
    
    # Generate unique name
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{timestamp}_{unique_id}{ext}"

def save_uploaded_file(file, subfolder=''):
    """Save uploaded file and return file path"""
    if not file or not allowed_file(file.filename):
        return None, "File type not allowed"
    
    try:
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        
        # Create full path
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if subfolder:
            upload_folder = os.path.join(upload_folder, subfolder)
            os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        
        # Save file
        file.save(file_path)
        
        # Return relative path
        if subfolder:
            return os.path.join(subfolder, filename), None
        else:
            return filename, None
            
    except Exception as e:
        return None, str(e)

def save_and_resize_signature(file,target_size=(724,344)):
    """
    Save and resize signature image to target size
    
    Args:
        file: FileStorage object from Flask
        target_size: Tuple (width, height) for target size
    
    Returns:
        (file_path, error)
    """
    if not file or not file.filename:
        return None, "no file provided"
    
    if not allowed_file(file.filename):
        return None, "File type not allowed, Please upload PNG"
    
    try:
        filename = generate_unique_filename(file.filename)

        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in ['png', 'jpg', 'jpeg', 'gif']:
            return None, "File must be an image (PNG, JPG, JPEG, or GIF)"
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        signature_dir = os.path.join(upload_folder,'signatures')
        os.makedirs(signature_dir,exist_ok=True)

        file_path = os.path.join(signature_dir,filename)

        img = Image.open(file)

        if img.mode in ('RGBA', 'LA','P'):
            
            background = Image.new('RGB',img.size, (255,255,255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background

        img_resized = img.resize(target_size,Image.Resampling.LANCZOS)

        img_resized.save(file_path,quality=95, optimize=True)

        relative_path = os.path.join('signatures',filename)

        return relative_path,None

    except Exception as e:
        return None, f"Failed to process image: {str(e)}"
    

def delete_file(file_path):
    """Delete file from filesystem"""
    if not file_path:
        return False
    
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        full_path = os.path.join(upload_folder, file_path)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False


def get_file_url(file_path):
    """
    Get URL for accessing uploaded file
    Useful for serving files via Flask
    """
    if not file_path:
        return None
    
    # Return URL path (assuming you have route to serve files)
    return f"/uploads/{file_path}"

def is_signature_file(filename):
    """Check if file is valid signature format"""
    SIGNATURE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    if not filename:
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in SIGNATURE_EXTENSIONS

def save_signature_direct(file, subfolder='signatures'):
    """
    Save signature file directly without resize
    (untuk file yang sudah di-resize di frontend)
    
    Args:
        file: FileStorage object from Flask
        subfolder: Subfolder untuk save (default: signatures)
    
    Returns:
        (file_path, error)
    """
    if not file or not file.filename:
        return None, "No file provided"
    
    # Validate file type
    if not allowed_file(file.filename):
        return None, "File type not allowed"
    
    try:
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        
        # Create directory
        upload_folder = current_app.config['UPLOAD_FOLDER']
        target_dir = os.path.join(upload_folder, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)
        
        # Validate dimensions (optional)
        try:
            from PIL import Image
            img = Image.open(file_path)
            if img.width != 724 or img.height != 344:
                # File dari frontend should be 724x344
                # But we can be flexible
                pass
        except:
            pass
        
        # Return relative path
        return os.path.join(subfolder, filename), None
        
    except Exception as e:
        return None, f"Failed to save signature: {str(e)}"
    
def save_signature_smart(file, target_size=(724, 344)):
    """
    Smart save signature:
    - If already target size → save directly
    - If different size → resize
    
    Args:
        file: FileStorage object from Flask
        target_size: Target size (width, height)
    
    Returns:
        (file_path, error)
    """
    if not file or not file.filename:
        return None, "No file provided"
    
    if not allowed_file(file.filename):
        return None, "File type not allowed"
    
    try:
        from PIL import Image
        import io
        
        # Read image
        img = Image.open(file)
        
        # Check if already target size
        if img.width == target_size[0] and img.height == target_size[1]:
            # Already perfect size, save directly
            filename = generate_unique_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            signatures_dir = os.path.join(upload_folder, 'signatures')
            os.makedirs(signatures_dir, exist_ok=True)
            
            file_path = os.path.join(signatures_dir, filename)
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            
            # Save
            img.save(file_path, quality=95, optimize=True)
            
            return os.path.join('signatures', filename), None
        
        else:
            # Need resize, use existing function
            return save_and_resize_signature(file, target_size)
            
    except Exception as e:
        return None, f"Failed to process signature: {str(e)}"