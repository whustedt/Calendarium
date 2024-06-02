from datetime import datetime, date
from flask import jsonify, url_for
from babel.dates import format_date
from os import path, makedirs
import zipfile
from io import BytesIO
from urllib.parse import urlparse
import requests
from werkzeug.utils import secure_filename

def handle_image_upload(entry_id, file, giphy_url, upload_folder, allowed_extensions):
    """Handle Giphy URL or file upload."""
    if giphy_url:
        filename = download_giphy_image(giphy_url, entry_id, upload_folder)
    else:
        filename = handle_image(file, entry_id, upload_folder, allowed_extensions)

    return filename

def download_giphy_image(url, entry_id, upload_folder):
    """Download and save a Giphy image from a valid URL to the specified folder."""
    if not is_valid_giphy_url(url):
        return None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = f"{entry_id}.gif"
            filepath = path.join(upload_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filename
    except requests.RequestException:
        return None

def is_valid_giphy_url(url):
    """Check if a URL is a valid Giphy URL by its domain and path."""
    try:
        parsed_url = urlparse(url)
        return parsed_url.netloc.startswith("media") and parsed_url.netloc.endswith(".giphy.com") and parsed_url.path.startswith("/media/")
    except ValueError:
        return False

def handle_image(file, entry_id, upload_folder, allowed_extensions):
    """Handles image upload and saves it with a new filename based on entry ID."""
    if file and allowed_file(file.filename, allowed_extensions):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1]
        filename = f"{entry_id}.{ext}"
        filepath = path.join(upload_folder, filename)
        file.save(filepath)
        return filename
    return None

def parse_date(date_str):
    """Parses a date string formatted as 'YYYY-MM-DD' into a date object."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

def allowed_file(filename, allowed_extensions):
    """Checks if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def create_upload_folder(upload_folder):
    """Creates the upload folder if it doesn't exist."""
    if not path.exists(upload_folder):
        makedirs(upload_folder, exist_ok=True)

def get_formatted_entries(entries):
    """Formats entries for display, including additional attributes."""
    data = []
    today = str(date.today())
    index = next((i for i, entry in enumerate(entries) if entry.date >= today), len(entries))

    for i, entry in enumerate(entries):
        entry_data = {
            'date': entry.date,
            'date_formatted': format_date(parse_date(entry.date), 'd. MMMM', locale='de_DE'),
            'category': entry.category,
            'title': entry.title,
            'description': entry.description,
            'last_updated_by': entry.last_updated_by,
            'color': entry.color,
            'image_url': url_for('uploaded_file', filename=entry.image_filename) if entry.image_filename else None,
            'image_url_external': url_for('uploaded_file', filename=entry.image_filename, _external=True) if entry.image_filename else None,
            'index': i - index,
            'isToday': entry.date == today
        }
        data.append(entry_data)

    return data

def create_zip(entries, upload_folder):
    """Creates a zip file containing entries data and associated images."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Add entries.json file
        entries_json = jsonify(entries).get_data(as_text=True)
        zip_file.writestr('entries.json', entries_json)
        
        # Add image files
        for entry in entries:
            if entry['image_url']:
                image_filename = entry['image_url'].split('/')[-1]
                image_path = path.join(upload_folder, image_filename)
                if path.exists(image_path):
                    zip_file.write(image_path, arcname=image_filename)
    
    zip_buffer.seek(0)
    return zip_buffer
