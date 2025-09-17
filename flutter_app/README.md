# DataWipe Flutter App

A comprehensive Flutter application for secure data wiping with certificate generation, integrated with the DataWipe FastAPI backend.

## Features

### 🔐 User Management
- **User Registration**: Complete onboarding with name, organization, and device serial
- **Profile Management**: View and update user profile information
- **Device Association**: Link users with specific devices

### 💾 Device Management
- **Device Detection**: Automatic detection of all connected storage devices
- **Device Information**: Detailed device specs including model, size, type, and health
- **Registration Status**: Track which devices are registered to users
- **Health Monitoring**: Device health status and warnings (HPA/DCO detection)

### 🗑️ Secure Wiping
- **Multiple Standards**: Support for DoD 5220.22-M, NIST 800-88, Gutmann Method, and more
- **Device Selection**: Choose from detected devices for wiping operations
- **Progress Tracking**: Real-time progress monitoring for wipe operations
- **Mock Mode**: Safe testing mode without actual data destruction

### 📄 Certificate Generation
- **Digital Certificates**: Automatic generation of PDF and JSON certificates
- **Digital Signatures**: Cryptographically signed certificates for verification
- **Download Options**: Download certificates in multiple formats
- **Verification**: Online certificate verification

### 📊 History & Analytics
- **Job History**: Complete history of all wipe operations
- **Status Tracking**: Real-time status updates for running jobs
- **Certificate Downloads**: Easy access to generated certificates
- **Analytics**: Device and job statistics

## Screens

### 1. Onboarding Screen
- User registration with name, organization, and device serial
- Form validation and error handling
- Welcome message and app introduction

### 2. Dashboard Screen
- **Overview Tab**: User welcome, device summary, quick actions
- **Devices Tab**: Complete device listing with search and filters
- **Analytics Tab**: Device type distribution, health status, registration stats

### 3. Wipe Screen
- Device selection from detected devices
- Wipe method selection with detailed descriptions
- Target path specification
- Options for certificate generation and mock mode
- Confirmation dialog with operation details

### 4. History Screen
- **All Jobs**: Complete list of all wipe operations
- **Completed**: Successfully completed operations
- **Pending**: Operations waiting to start
- **Failed**: Failed operations with error details
- Job details with progress tracking and certificate downloads

### 5. Settings Screen
- User profile information and statistics
- API configuration and connection testing
- App settings (mock mode, auto-generate certificates)
- Theme selection (system, light, dark)
- Logout and data clearing options

## Architecture

### State Management
- **Provider Pattern**: Used for state management across the app
- **UserProvider**: Manages user authentication and profile data
- **DeviceProvider**: Handles device detection and management
- **JobProvider**: Manages wipe jobs and status tracking

### API Integration
- **RESTful API**: Full integration with FastAPI backend
- **Error Handling**: Comprehensive error handling and user feedback
- **Offline Support**: Local storage for user data and settings

### UI/UX
- **Material Design**: Modern Material Design 3 components
- **Responsive Layout**: Adaptive layouts for different screen sizes
- **Dark/Light Theme**: Support for both themes with system preference
- **Loading States**: Proper loading indicators and progress feedback

## Installation

### Prerequisites
- Flutter SDK (3.0.0 or higher)
- Dart SDK
- Android Studio / VS Code
- DataWipe FastAPI backend running

### Setup
1. Clone the repository
2. Navigate to the Flutter app directory:
   ```bash
   cd flutter_app
   ```

3. Install dependencies:
   ```bash
   flutter pub get
   ```

4. Configure API endpoint in `lib/utils/app_constants.dart`:
   ```dart
   static const String apiBaseUrl = 'http://your-api-server:8000/api/v1';
   ```

5. Run the app:
   ```bash
   flutter run
   ```

## Configuration

### API Settings
- **Base URL**: Configure the FastAPI backend URL
- **Timeout**: Set appropriate timeout values for API calls
- **Mock Mode**: Enable for testing without actual data destruction

### App Settings
- **Auto Generate Certificates**: Automatically create certificates after wipe operations
- **Theme Mode**: Choose between system, light, or dark theme
- **Device Detection**: Configure device detection preferences

## Usage

### First Time Setup
1. Launch the app
2. Complete the onboarding process with your details
3. Verify device detection is working
4. Configure API settings if needed

### Starting a Wipe Operation
1. Navigate to the Wipe screen
2. Select a device from the detected devices
3. Choose a wipe method (DoD, NIST, Gutmann, etc.)
4. Specify the target path
5. Configure options (certificate generation, mock mode)
6. Confirm the operation
7. Monitor progress in the History screen

### Managing Certificates
1. View completed jobs in the History screen
2. Tap on a job to see details
3. Download certificates in PDF or JSON format
4. Verify certificates online

## API Integration

The app integrates with the following FastAPI endpoints:

### Authentication
- `POST /auth/register` - User registration
- `GET /auth/profile/{user_id}` - Get user profile
- `PUT /auth/profile/{user_id}` - Update user profile

### Devices
- `GET /devices/` - List all devices
- `GET /devices/summary` - Device statistics
- `GET /devices/{device_serial}` - Get specific device

### Jobs
- `POST /jobs/start` - Start wipe job
- `GET /jobs/{job_id}/status` - Get job status
- `GET /jobs/` - List jobs
- `POST /jobs/{job_id}/cancel` - Cancel job

### Certificates
- `GET /certificates/` - List certificates
- `GET /downloads/certificate/{id}/pdf` - Download PDF
- `GET /downloads/certificate/{id}/json` - Download JSON

## Security Features

- **Digital Signatures**: All certificates are cryptographically signed
- **Secure Communication**: HTTPS support for API communication
- **Data Validation**: Comprehensive input validation
- **Error Handling**: Secure error messages without sensitive data exposure

## Testing

### Mock Mode
Enable mock mode in settings to test the app without actual data destruction:
- Simulates wipe operations
- Generates test certificates
- Safe for development and testing

### Test Data
The app includes test data generation for:
- Sample devices
- Mock wipe operations
- Test certificates

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check API server is running
   - Verify API URL in settings
   - Check network connectivity

2. **No Devices Detected**
   - Ensure storage devices are connected
   - Check device permissions
   - Try refreshing the device list

3. **Certificate Download Failed**
   - Verify job completed successfully
   - Check certificate generation was enabled
   - Ensure sufficient storage space

### Debug Mode
Enable debug mode for detailed logging:
```bash
flutter run --debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub

## Changelog

### Version 1.0.0
- Initial release
- Complete UI implementation
- FastAPI integration
- Certificate generation
- Device management
- Job tracking and history
