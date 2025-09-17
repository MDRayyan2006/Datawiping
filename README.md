# DataWipe API

A FastAPI backend application for managing data wiping operations with SQLite database support.

## Features

- **User Management**: Create, read, update, and delete users
- **Wipe Logs**: Track data wiping operations with status management
- **SQLite Database**: Lightweight database with SQLAlchemy ORM
- **Dependency Injection**: Clean database session management
- **RESTful API**: Well-structured endpoints with proper HTTP status codes
- **Data Wiping**: Multiple wipe methods (secure delete, overwrite, shred)

## Project Structure

```
├── main.py                 # FastAPI application entry point
├── database.py            # Database configuration and session management
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── models/               # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── user.py          # User model
│   └── wipe_log.py      # Wipe log model
├── routers/             # API route handlers
│   ├── __init__.py
│   ├── users.py         # User endpoints
│   └── wipe_logs.py     # Wipe log endpoints
└── services/            # Business logic layer
    ├── __init__.py
    ├── user_service.py  # User business logic
    └── wipe_service.py  # Wipe operation logic
```

## Installation

1. **Clone the repository** (if applicable) or ensure you're in the project directory

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check privileges** (recommended):
   ```bash
   python check_privileges.py
   ```

4. **Run the application**:
   
   **Option A: Automatic privilege handling**
   ```bash
   python start_datawipe.py
   ```
   
   **Option B: Direct execution**
   ```bash
   python main.py
   ```
   
   **Option C: Using uvicorn directly**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Privilege Requirements

### Why Elevated Privileges Are Needed

DataWipe requires administrator/root privileges for the following operations:
- **Secure Wiping**: Direct access to storage devices and raw disk sectors
- **Device Detection**: Access to hardware information and device enumeration
- **Certificate Generation**: File system access for certificate storage
- **System Integration**: Access to system-level APIs for device management

### Running with Elevated Privileges

#### Windows
```bash
# Method 1: Use the startup script (recommended)
python start_datawipe.py

# Method 2: Run as administrator manually
# Right-click Command Prompt → "Run as administrator"
python main.py

# Method 3: Use the generated batch file
run_as_admin.bat
```

#### Linux/macOS
```bash
# Method 1: Use the startup script (recommended)
python start_datawipe.py

# Method 2: Use sudo
sudo python3 main.py

# Method 3: Use the generated shell script
sudo ./run_as_root.sh
```

### Mock Mode for Testing

If you don't have elevated privileges or want to test safely:
```bash
# Enable mock mode in the application settings
# This simulates wipe operations without actual data destruction
```

### Creating Elevation Scripts

Generate platform-specific elevation scripts:
```bash
python start_datawipe.py --create-scripts
```

This creates:
- **Windows**: `run_as_admin.bat` and `run_as_admin.ps1`
- **Linux/macOS**: `run_as_root.sh`

4. **Access the API**:
   - API Base URL: `http://localhost:8000`
   - Interactive API docs: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`

## Database Schema

### Users Table
- `id`: Primary key
- `name`: User's full name
- `org`: Organization name
- `device_serial`: Unique device serial number
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Wipe Logs Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `wipe_method`: Method used for wiping (secure_delete, overwrite, shred, crypto_wipe, physical_destruction)
- `start_time`: When the wipe operation started
- `end_time`: When the wipe operation finished
- `verification_status`: Verification status (pending, verified, failed, not_required)
- `certificate_path`: Path to verification certificate (optional)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## API Endpoints

### Users
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/` - Get all users (with pagination and org filtering)
- `GET /api/v1/users/{user_id}` - Get a specific user by ID
- `GET /api/v1/users/device/{device_serial}` - Get a user by device serial
- `PUT /api/v1/users/{user_id}` - Update a user
- `DELETE /api/v1/users/{user_id}` - Delete a user

### Wipe Logs
- `POST /api/v1/wipe-logs/` - Create a new wipe log
- `GET /api/v1/wipe-logs/` - Get wipe logs (with filtering by user, verification status, wipe method)
- `GET /api/v1/wipe-logs/{wipe_log_id}` - Get a specific wipe log
- `PUT /api/v1/wipe-logs/{wipe_log_id}` - Update a wipe log
- `POST /api/v1/wipe-logs/{wipe_log_id}/start` - Start a wipe operation
- `POST /api/v1/wipe-logs/{wipe_log_id}/complete` - Mark wipe as completed
- `POST /api/v1/wipe-logs/{wipe_log_id}/fail` - Mark wipe as failed
- `POST /api/v1/wipe-logs/{wipe_log_id}/execute` - Execute a complete wipe operation

### Storage Detection
- `GET /api/v1/storage/devices` - Get all connected storage devices
- `GET /api/v1/storage/devices/{device_path}` - Get specific device information
- `GET /api/v1/storage/summary` - Get storage summary statistics
- `GET /api/v1/storage/devices/by-type/{device_type}` - Filter devices by type
- `GET /api/v1/storage/devices/with-hpa` - Get devices with HPA enabled
- `GET /api/v1/storage/devices/with-dco` - Get devices with DCO enabled
- `GET /api/v1/storage/health` - Get health status of all devices
- `POST /api/v1/storage/devices/{device_path}/refresh` - Refresh device information

### Secure Wiping
- `POST /api/v1/wipe/file` - Securely wipe a single file
- `POST /api/v1/wipe/folder` - Securely wipe all files in a folder
- `POST /api/v1/wipe/drive` - Securely wipe an entire drive
- `GET /api/v1/wipe/methods` - Get information about wipe methods
- `GET /api/v1/wipe/status` - Get current wipe operation status
- `GET /api/v1/wipe/operations` - Get list of active operations
- `POST /api/v1/wipe/operations/{id}/cancel` - Cancel an active operation
- `POST /api/v1/wipe/test` - Test wipe operation with temporary file

### Certificate Management
- `GET /api/v1/certificates/` - Get all certificates with pagination
- `GET /api/v1/certificates/{certificate_id}` - Get specific certificate
- `GET /api/v1/certificates/user/{user_id}` - Get certificates by user
- `GET /api/v1/certificates/device/{device_serial}` - Get certificates by device
- `GET /api/v1/certificates/org/{org}` - Get certificates by organization
- `POST /api/v1/certificates/search` - Search certificates with filters
- `GET /api/v1/certificates/stats` - Get certificate statistics
- `POST /api/v1/certificates/{certificate_id}/verify` - Verify certificate signature
- `POST /api/v1/certificates/{certificate_id}/invalidate` - Invalidate certificate
- `DELETE /api/v1/certificates/{certificate_id}` - Delete certificate
- `GET /api/v1/certificates/{certificate_id}/files` - Get certificate file paths
- `GET /api/v1/certificates/{certificate_id}/download/{type}` - Download certificate files

### User Authentication & Registration
- `POST /api/v1/auth/register` - Register a new user with device
- `GET /api/v1/auth/profile/{user_id}` - Get user profile with statistics
- `PUT /api/v1/auth/profile/{user_id}` - Update user profile
- `GET /api/v1/auth/device/{device_serial}` - Get user by device serial
- `GET /api/v1/auth/org/{org}` - Get users by organization
- `DELETE /api/v1/auth/{user_id}` - Delete user and associated data

### Device Management
- `GET /api/v1/devices/` - List all detected devices with registration status
- `GET /api/v1/devices/summary` - Get device statistics and summary
- `GET /api/v1/devices/registered` - Get only registered devices
- `GET /api/v1/devices/unregistered` - Get only unregistered devices
- `GET /api/v1/devices/by-type/{device_type}` - Get devices by type
- `GET /api/v1/devices/{device_serial}` - Get specific device by serial
- `POST /api/v1/devices/register` - Register a device with a user
- `GET /api/v1/devices/health` - Get device health status

### Job Management
- `POST /api/v1/jobs/start` - Start a new wipe job
- `GET /api/v1/jobs/{job_id}/status` - Get job status and progress
- `GET /api/v1/jobs/` - List all jobs with filtering
- `GET /api/v1/jobs/user/{user_id}` - Get jobs for specific user
- `POST /api/v1/jobs/{job_id}/cancel` - Cancel a running job
- `GET /api/v1/jobs/stats` - Get job statistics

### File Downloads
- `GET /api/v1/downloads/certificate/{certificate_id}/pdf` - Download certificate PDF
- `GET /api/v1/downloads/certificate/{certificate_id}/json` - Download certificate JSON
- `GET /api/v1/downloads/certificate/{certificate_id}/signature` - Download signature file
- `GET /api/v1/downloads/certificate/{certificate_id}/zip` - Download complete package
- `GET /api/v1/downloads/job/{job_id}/certificate` - Get job certificate info
- `GET /api/v1/downloads/user/{user_id}/certificates` - Get user certificates
- `GET /api/v1/downloads/verify/{certificate_id}` - Verify certificate online

## Usage Examples

### Create a User
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "org": "Acme Corporation",
    "device_serial": "DEV001-ACME-2024"
  }'
```

### Create a Wipe Log
```bash
curl -X POST "http://localhost:8000/api/v1/wipe-logs/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "wipe_method": "secure_delete",
    "certificate_path": "/certificates/wipe_cert_001.pem"
  }'
```

### Start a Wipe Operation
```bash
curl -X POST "http://localhost:8000/api/v1/wipe-logs/1/start"
```

### Execute a Complete Wipe Operation
```bash
curl -X POST "http://localhost:8000/api/v1/wipe-logs/1/execute"
```

### Get All Storage Devices
```bash
curl -X GET "http://localhost:8000/api/v1/storage/devices"
```

### Get Storage Summary
```bash
curl -X GET "http://localhost:8000/api/v1/storage/summary"
```

### Get Devices with HPA
```bash
curl -X GET "http://localhost:8000/api/v1/storage/devices/with-hpa"
```

### Wipe a File (DoD 5220.22-M)
```bash
curl -X POST "http://localhost:8000/api/v1/wipe/file" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/sensitive/file.txt",
    "method": "dod_5220_22_m",
    "mock_mode": false
  }'
```

### Wipe a Folder (NIST 800-88)
```bash
curl -X POST "http://localhost:8000/api/v1/wipe/folder" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/sensitive/folder",
    "method": "nist_800_88",
    "mock_mode": false
  }'
```

### Test Wipe Operation
```bash
curl -X POST "http://localhost:8000/api/v1/wipe/test?method=single_pass&mock_mode=true"
```

### Get All Certificates
```bash
curl -X GET "http://localhost:8000/api/v1/certificates/"
```

### Verify Certificate
```bash
curl -X POST "http://localhost:8000/api/v1/certificates/CERT-20240115103000-abc123def/verify"
```

### Get Certificate Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/certificates/stats"
```

### Register a New User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "org": "Acme Corporation",
    "device_serial": "DEV001-ACME-2024",
    "email": "john.doe@acme.com",
    "notes": "IT Department"
  }'
```

### List All Devices
```bash
curl -X GET "http://localhost:8000/api/v1/devices/"
```

### Start a Wipe Job
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "target_path": "/sensitive/data/file.txt",
    "wipe_method": "dod_5220_22_m",
    "generate_certificate": true,
    "mock_mode": true,
    "notes": "Secure wipe of sensitive file"
  }'
```

### Check Job Status
```bash
curl -X GET "http://localhost:8000/api/v1/jobs/1/status"
```

### Download Certificate PDF
```bash
curl -X GET "http://localhost:8000/api/v1/downloads/certificate/CERT-20240115103000-abc123def/pdf" \
  --output certificate.pdf
```

## Wipe Methods

### Secure Wiping Standards
1. **DoD 5220.22-M**: Department of Defense standard (3 passes: 0x00, 0xFF, 0x00)
2. **NIST 800-88**: National Institute of Standards and Technology standard (1 pass with zeros)
3. **Gutmann Method**: 35-pass secure deletion method for highly sensitive data

### Custom Methods
4. **Single Pass**: Single pass overwrite with zeros
5. **Random Data**: Single pass with random data
6. **Zero Overwrite**: Single pass with zeros

### Legacy Methods (from wipe_logs)
7. **secure_delete**: Multiple random overwrites for secure deletion
8. **overwrite**: Simple overwrite method
9. **shred**: Pattern-based overwriting
10. **crypto_wipe**: Cryptographic wipe using encryption keys
11. **physical_destruction**: Physical destruction method

## Storage Detection Features

The storage detection service provides comprehensive information about connected storage devices:

### Device Information
- **Model and Serial**: Device manufacturer and serial number
- **Size and Capacity**: Total size, used space, and available space
- **Device Type**: HDD, SSD, USB, NVMe, SATA, SCSI
- **Partitions**: Detailed partition information including mount points and filesystem types

### Advanced Features
- **HPA Detection**: Host Protected Area presence detection
- **DCO Detection**: Device Configuration Overlay presence detection
- **Health Monitoring**: Temperature, health status, and rotation rate
- **Cross-Platform**: Windows (WMI + diskpart) and Linux (lsblk + hdparm) support

### Testing Services

```bash
# Test privilege checking functionality
python test_privileges.py

# Test storage detection functionality
python test_storage.py

# Test wipe service functionality
python test_wipe.py

# Test certificate service functionality
python test_certificates.py

# Test all FastAPI routers
python test_routers.py

# Test the complete setup
python test_setup.py
```

### Testing Privilege Functionality

```bash
# Test privilege checker standalone
python check_privileges.py

# Test privilege integration with wipe service
python test_privileges.py

# Test with different privilege levels
# Run without elevation to test warning messages
# Run with elevation to test full functionality
```

## Database Initialization

The project includes a comprehensive database initialization script:

```bash
# Create tables and seed with sample data
python init_db.py

# Create tables only
python init_db.py create

# Reset database (drop, create, and seed)
python init_db.py reset

# Verify database setup
python init_db.py verify
```

## Development

The application uses:
- **FastAPI** for the web framework
- **SQLAlchemy** for ORM and database management
- **Pydantic** for data validation and serialization
- **SQLite** for the database (easily configurable for other databases)
- **psutil** for system information and storage detection
- **Cross-platform system commands** for advanced storage analysis
- **cryptography** for digital signatures and certificate generation
- **reportlab** for PDF report generation

## Security Notes

- The wipe operations are designed for local file system operations
- Ensure proper file permissions and access controls
- Consider implementing authentication and authorization for production use
- The CORS middleware is currently configured to allow all origins (configure properly for production)

## License

This project is provided as-is for educational and development purposes.
