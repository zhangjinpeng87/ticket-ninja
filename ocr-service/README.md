# OCR Service - Error Log Recognition

This is a standalone FastAPI service that receives screenshot images and extracts textual error logs using OCR (Optical Character Recognition).

## Features

- Receives screenshot images (PNG, JPG, etc.)
- Uses EasyOCR to extract text from images
- Identifies error log patterns (exceptions, stack traces, error messages)
- Returns structured error information with confidence scores

## Setup

### Option 1: Using Conda (Recommended for Local Development)

Create an isolated conda environment:

```bash
# Create a new conda environment with Python 3.10
conda create -n ocr-service python=3.10 -y

# Activate the environment
conda activate ocr-service

# Install dependencies
pip install -r requirements.txt
```

To use the environment:
```bash
# Activate the environment before running
conda activate ocr-service

# Now run the service
python main.py
```

To deactivate when done:
```bash
conda deactivate
```

### Option 2: Using pip (System Python)

```bash
pip install -r requirements.txt
```

**Note:** EasyOCR will download model files on first run (~100MB). This happens automatically.

## Running the Service

### Option 1: Direct Python

Make sure you have activated your conda environment (if using conda):
```bash
conda activate ocr-service  # If using conda
python main.py
```

### Option 2: Using uvicorn

Make sure you have activated your conda environment (if using conda):
```bash
conda activate ocr-service  # If using conda
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Option 3: Using Docker

#### Build and run from ocr-service directory:
```bash
cd ocr-service
docker build -t ticket-ninja-ocr-service .
docker run -p 8001:8001 ticket-ninja-ocr-service
```

#### Or build from project root using dockerfile in docker/ directory:
```bash
docker build -f docker/Dockerfile.ocr-service -t ticket-ninja-ocr-service .
docker run -p 8001:8001 ticket-ninja-ocr-service
```

#### Using docker-compose (runs both OCR service and AI Gateway):
```bash
cd docker
docker-compose up
```

The service will start on `http://localhost:8001`

## API Endpoints

### Health Check
```
GET /health
```

### Extract Error Logs (File Upload)
```
POST /extract-error-logs
Content-Type: multipart/form-data
Body: file (image file)
```

### Extract Error Logs (Base64)
```
POST /extract-error-logs-base64
Content-Type: application/json
Body: {"image_data": "data:image/png;base64,..."}
```

## Response Format

```json
{
  "error_summary": "Detected error: TimeoutError at /api/payments",
  "full_text": "Full OCR extracted text...",
  "error_lines": [
    "TimeoutError: Connection timeout",
    "at com.example.service.payment..."
  ],
  "confidence": 0.8
}
```

## Configuration

The service can be configured via environment variables:
- `PORT`: Server port (default: 8001)
- `HOST`: Server host (default: 0.0.0.0)

## Integration with AI Gateway

The AI Gateway (`ai-gateway/app/services/screenshot.py`) calls this service when processing screenshots. Set the `OCR_SERVICE_URL` environment variable in the AI Gateway to point to this service:

```bash
# If using conda, activate the environment first
conda activate ocr-service  # If using conda

# Set the OCR service URL
export OCR_SERVICE_URL=http://localhost:8001
```

**Note:** Make sure the OCR service is running before starting the AI Gateway. If using conda, activate the OCR service environment in one terminal and run the OCR service, then start the AI Gateway in another terminal.

## Error Patterns Detected

The service looks for common error indicators:
- Exception types (Error, Exception)
- Stack traces
- Error keywords (fatal, critical, failed, timeout)
- Log patterns with timestamps and error markers

## Sample Images and Testing

Sample error log images are available in the `samples/` directory for testing:
- Generate sample images: `cd samples && python generate_samples.py`
- Test samples against the service: `cd samples && python test_samples.py`
- See `samples/README.md` for detailed usage instructions

Sample images include:
- Python tracebacks
- Java stack traces
- HTTP error logs
- Database connection errors
- Simple error messages
