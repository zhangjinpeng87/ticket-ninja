#!/usr/bin/env python3
"""
Generate sample error log images for testing the OCR service.
This script creates PNG images with error log text that can be used for testing.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_error_log_image(text, filename, width=800, padding=20):
    """Create an image with error log text."""
    # Create image with white background
    img = Image.new('RGB', (width, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a monospace font, fallback to default if not available
    try:
        # Try common system fonts
        font_paths = [
            '/System/Library/Fonts/Menlo.ttc',  # macOS
            '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',  # Linux
            'C:/Windows/Fonts/consola.ttf',  # Windows
        ]
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, 16)
                break
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Draw text
    y = padding
    for line in text.split('\n'):
        draw.text((padding, y), line, fill='black', font=font)
        y += 20  # Line height
    
    # Save image
    img.save(filename)
    print(f"Created: {filename}")

def main():
    """Generate sample error log images."""
    samples_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Sample 1: Python Traceback
    python_error = """Traceback (most recent call last):
  File "app.py", line 42, in process_request
    result = calculate_total(items)
  File "utils.py", line 18, in calculate_total
    return sum(item['price'] for item in items)
KeyError: 'price'

Error: Missing 'price' key in item dictionary
    at utils.py:18"""
    
    create_error_log_image(python_error, os.path.join(samples_dir, 'sample_python_error.png'))
    
    # Sample 2: Java Stack Trace
    java_error = """java.lang.NullPointerException
    at com.example.service.PaymentService.processPayment(PaymentService.java:125)
    at com.example.controller.PaymentController.handleRequest(PaymentController.java:45)
    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
    
Caused by: java.sql.SQLException: Connection timeout
    at com.example.db.Database.getConnection(Database.java:89)
    ... 5 more"""
    
    create_error_log_image(java_error, os.path.join(samples_dir, 'sample_java_error.png'))
    
    # Sample 3: HTTP Error
    http_error = """[ERROR] 2024-01-15 14:32:18 - Request failed
HTTP Status: 500 Internal Server Error
Endpoint: POST /api/payments
Request ID: req-abc123-xyz789

Error Details:
- Message: TimeoutError: Connection timeout after 30s
- Service: payment-gateway
- Retry Count: 3
- Failed at: 2024-01-15T14:32:18Z"""
    
    create_error_log_image(http_error, os.path.join(samples_dir, 'sample_http_error.png'))
    
    # Sample 4: Database Error
    db_error = """SQL Error: Connection refused
Database: production_db
Host: db.example.com:5432
User: app_user

ERROR: connection to server at "db.example.com" (192.168.1.100),
port 5432 failed: Connection refused
    Is the server running on that host and accepting
    TCP/IP connections on that port?

FATAL: could not connect to database "production_db"
Retry attempt: 3/5"""
    
    create_error_log_image(db_error, os.path.join(samples_dir, 'sample_database_error.png'))
    
    # Sample 5: Simple Error Message
    simple_error = """Error: File not found
Cannot open file: /path/to/config.json
Please check the file path and permissions."""
    
    create_error_log_image(simple_error, os.path.join(samples_dir, 'sample_simple_error.png'))
    
    print("\nAll sample images generated successfully!")
    print(f"Sample images are in: {samples_dir}")

if __name__ == "__main__":
    main()

