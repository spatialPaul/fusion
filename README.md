# Fusion Nuvolo–ArcGIS Integration

This repository provides foundational Python modules for integrating Nuvolo lease records with ArcGIS feature services. It establishes reusable API clients, data models, and synchronization utilities that can be composed into automation pipelines or application backends.

## Features
- Typed configuration objects for Nuvolo and ArcGIS connections.
- API clients that encapsulate authentication and pagination concerns.
- Data models describing lease metadata shared between platforms.
- Synchronization service that translates Nuvolo lease records into ArcGIS feature payloads and vice-versa.
- Command line entry point for running targeted synchronization jobs.

## Getting Started
1. Create a Python 3.11 virtual environment.
2. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```
3. Export the required environment variables (see `src/fusion/config.py`).
4. Execute the synchronization CLI:
   ```bash
   python -m fusion.cli sync-from-nuvolo --since "2024-01-01"
   ```

## Next Steps
- Implement persistence for mapping ArcGIS Global IDs back into Nuvolo.
- Expand automated tests and logging.
- Integrate with orchestration platforms (ServiceNow Flow Designer, Azure Functions, etc.).
