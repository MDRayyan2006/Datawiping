# Windows App Integration Guide

## Certificate Status for Wipe Operations

This guide explains how the Windows app should handle certificate generation and status after wipe operations.

## API Endpoints

### 1. Wipe File/Folder/Drive
**POST** `/api/v1/wipe/{file|folder|drive}?user_id={user_id}`

**Response includes certificate status:**
```json
{
  "success": true,
  "method": "single_pass",
  "target": "C:\\test\\file.txt",
  "size_bytes": 1024,
  "size_human": "1.0 KB",
  "passes_completed": 1,
  "total_passes": 1,
  "duration_seconds": 0.5,
  "error_message": null,
  "verification_hash": "abc123...",
  "mock_mode": false,
  "completed_at": "2025-09-19T23:41:28.123456",
  "certificate_id": "CERT-20250919234128-7679783f",
  "certificate_path": "certificates\\CERT-20250919234128-7679783f",
  "certificate_status": "completed",
  "download_urls": {
    "pdf": "/api/v1/downloads/certificate/CERT-20250919234128-7679783f/pdf",
    "json": "/api/v1/downloads/certificate/CERT-20250919234128-7679783f/json",
    "signature": "/api/v1/downloads/certificate/CERT-20250919234128-7679783f/signature",
    "package": "/api/v1/downloads/certificate/CERT-20250919234128-7679783f/zip"
  }
}
```

### 2. Check Certificate Status
**GET** `/api/v1/wipe/certificate/{certificate_id}/status`

**Response:**
```json
{
  "certificate_id": "CERT-20250919234128-7679783f",
  "status": "completed",
  "created_at": "2025-09-19T18:11:28",
  "files_exist": true,
  "download_urls": {
    "pdf": "/api/v1/downloads/certificate/CERT-20250919234128-7679783f/pdf",
    "json": "/api/v1/downloads/certificate/CERT-20250919234128-7679783f/json",
    "signature": "/api/v1/downloads/certificate/CERT-20250919234128-7679783f/signature",
    "package": "/api/v1/downloads/certificate/CERT-20250919234128-7679783f/zip"
  }
}
```

## Certificate Status Values

- `"completed"` - Certificate generated successfully and ready for download
- `"failed"` - Certificate generation failed
- `"not_required"` - No certificate needed (wipe failed)
- `"generating"` - Certificate is being generated (rare, as generation is synchronous)

## Windows App Implementation

### 1. After Wipe Completion
```csharp
// Check the wipe response
if (wipeResponse.Success && wipeResponse.CertificateStatus == "completed")
{
    // Certificate is ready
    ShowCertificateReady(wipeResponse.CertificateId, wipeResponse.DownloadUrls);
}
else if (wipeResponse.CertificateStatus == "failed")
{
    // Show error message
    ShowCertificateError("Certificate generation failed");
}
```

### 2. Polling Certificate Status (if needed)
```csharp
// Poll certificate status if needed
var statusResponse = await httpClient.GetAsync($"/api/v1/wipe/certificate/{certificateId}/status");
var status = await statusResponse.Content.ReadFromJsonAsync<CertificateStatus>();

if (status.Status == "completed")
{
    // Certificate is ready
    ShowCertificateReady(certificateId, status.DownloadUrls);
}
```

### 3. Download Certificate
```csharp
// Download certificate files
var pdfUrl = $"http://localhost:8000{downloadUrls.Pdf}";
var pdfResponse = await httpClient.GetAsync(pdfUrl);
var pdfBytes = await pdfResponse.Content.ReadAsByteArrayAsync();

// Save or display the certificate
File.WriteAllBytes("certificate.pdf", pdfBytes);
```

## Key Points for Windows App

1. **Certificate Status is Immediate**: The `certificate_status` field in the wipe response is set to `"completed"` immediately when the wipe finishes successfully.

2. **No Polling Required**: Since certificate generation is synchronous, the Windows app should not need to poll for status.

3. **Download URLs Available**: All download URLs are provided in the wipe response when `certificate_status` is `"completed"`.

4. **Error Handling**: Check `certificate_status` for `"failed"` and handle accordingly.

## Troubleshooting

### If Windows App Shows "Certificate Generation in Process"

1. **Check Response Format**: Ensure the Windows app is reading the `certificate_status` field correctly.

2. **Verify Certificate Status**: The status should be `"completed"` immediately after a successful wipe.

3. **Check Download URLs**: Ensure the Windows app is using the provided download URLs correctly.

4. **Test API Directly**: Use the test script to verify the API is working correctly.

## Test Script

Run `python test_windows_app_integration.py` to test the complete flow and verify certificate status is working correctly.
