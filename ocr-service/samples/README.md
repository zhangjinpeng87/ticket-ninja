# OCR Service Sample Images

This directory contains sample error log images for testing the OCR service.

## Generating Sample Images

### Option 1: Using Conda (Recommended)

Create an isolated conda environment for the samples:

```bash
cd ocr-service/samples

# Create a new conda environment with Python 3.10
conda create -n ocr-samples python=3.10 -y

# Activate the environment
conda activate ocr-samples

# Install dependencies
pip install -r requirements.txt

# Generate sample images
python generate_samples.py
```

To use the environment later:
```bash
conda activate ocr-samples
python generate_samples.py
python test_samples.py  # Test the samples
```

### Option 2: Using pip (System Python)

```bash
cd ocr-service/samples
pip install -r requirements.txt
python generate_samples.py
```

**Note:** Make sure the `python` command you use matches the Python environment where you installed the dependencies. If you see `ModuleNotFoundError: No module named 'PIL'`, check which Python you're using with `which python` and ensure Pillow is installed in that environment.

This will generate several PNG images with different types of error logs:
- `sample_python_error.png` - Python traceback
- `sample_java_error.png` - Java stack trace
- `sample_http_error.png` - HTTP error log
- `sample_database_error.png` - Database connection error
- `sample_simple_error.png` - Simple error message

## Testing with Sample Images

### Using curl (File Upload)

**If you're in the `samples` directory:**
```bash
# Test with Python error sample
curl -X POST http://localhost:8001/extract-error-logs \
  -F "file=@sample_python_error.png"

# Test with Java error sample
curl -X POST http://localhost:8001/extract-error-logs \
  -F "file=@sample_java_error.png"
```

**If you're in the project root or `ocr-service` directory:**
```bash
# Test with Python error sample
curl -X POST http://localhost:8001/extract-error-logs \
  -F "file=@ocr-service/samples/sample_python_error.png"

# Or from ocr-service directory:
curl -X POST http://localhost:8001/extract-error-logs \
  -F "file=@samples/sample_python_error.png"
```

### Using Python Script

Make sure you have activated your conda environment (if using conda):
```bash
conda activate ocr-samples  # If using conda
```

Or install dependencies with pip:
```bash
pip install -r requirements.txt
```

Then test all samples:

```bash
# Test all samples
python test_samples.py

# Test against different OCR service URL
python test_samples.py http://localhost:8001
```

### Expected Output

The OCR service should extract text from these images and identify error patterns. See `expected_output_example.json` for detailed expected responses.

**Example for `sample_python_error.png`:**

**Input:** PNG image with Python traceback

**Expected Output:**
```json
{
  "error_summary": "Detected error: KeyError",
  "full_text": "Traceback (most recent call last):\n  File \"app.py\", line 42, in process_request\n    result = calculate_total(items)\n  File \"utils.py\", line 18, in calculate_total\n    return sum(item['price'] for item in items)\nKeyError: 'price'\n\nError: Missing 'price' key in item dictionary\n    at utils.py:18",
  "error_lines": [
    "Traceback (most recent call last):",
    "KeyError: 'price'",
    "Error: Missing 'price' key in item dictionary"
  ],
  "confidence": 0.8
}
```

Note: Actual OCR output may vary slightly based on image quality and OCR accuracy. The important thing is that error patterns are detected correctly.

## Sample Images Description

### sample_python_error.png
- **Type:** Python traceback
- **Contains:** KeyError exception with stack trace
- **Expected Detection:** KeyError, traceback patterns

### sample_java_error.png
- **Type:** Java stack trace
- **Contains:** NullPointerException with Java stack trace
- **Expected Detection:** NullPointerException, at com.example... patterns

### sample_http_error.png
- **Type:** HTTP error log
- **Contains:** HTTP 500 error with timestamp and details
- **Expected Detection:** ERROR, HTTP Status, TimeoutError

### sample_database_error.png
- **Type:** Database connection error
- **Contains:** PostgreSQL connection error
- **Expected Detection:** ERROR, Connection refused, FATAL

### sample_simple_error.png
- **Type:** Simple error message
- **Contains:** File not found error
- **Expected Detection:** Error, File not found

## Adding Your Own Samples

You can add your own error log screenshots to this directory for testing. Just ensure they are PNG or JPG format and contain readable error text.

## Conda Environment Management

### Creating a Shared Environment

If you want to use the same environment for both OCR service and samples, you can create a single conda environment:

```bash
# From project root
conda create -n ticket-ninja python=3.10 -y
conda activate ticket-ninja

# Install OCR service dependencies
cd ocr-service
pip install -r requirements.txt

# Install sample dependencies
cd samples
pip install -r requirements.txt
```

### Removing the Environment

To remove a conda environment when you're done:
```bash
conda deactivate  # First deactivate if active
conda env remove -n ocr-service  # Remove OCR service environment
conda env remove -n ocr-samples  # Remove samples environment
```

