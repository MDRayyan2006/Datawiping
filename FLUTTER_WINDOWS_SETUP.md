# Flutter Windows Setup Guide for DataWipe App

This guide will walk you through setting up and running the DataWipe Flutter app on Windows.

## Prerequisites

- Windows 10/11 (64-bit)
- At least 8GB RAM
- 10GB free disk space
- Administrator privileges (for some steps)

## Step 1: Install Flutter SDK

### 1.1 Download Flutter
1. Go to [https://flutter.dev/docs/get-started/install/windows](https://flutter.dev/docs/get-started/install/windows)
2. Click "Download Flutter SDK"
3. Download the latest stable release (e.g., `flutter_windows_3.16.0-stable.zip`)

### 1.2 Extract Flutter
1. Extract the downloaded ZIP file to `C:\flutter`
2. **Important**: Do NOT extract to a path with spaces (like `C:\Program Files\`)

### 1.3 Add Flutter to PATH
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Under "System Variables", find and select "Path", click "Edit"
4. Click "New" and add: `C:\flutter\bin`
5. Click "OK" on all dialogs

### 1.4 Verify Flutter Installation
1. Open a new Command Prompt or PowerShell
2. Run: `flutter --version`
3. You should see Flutter version information

## Step 2: Install Android Studio

### 2.1 Download Android Studio
1. Go to [https://developer.android.com/studio](https://developer.android.com/studio)
2. Download Android Studio for Windows
3. Run the installer as Administrator

### 2.2 Install Android Studio
1. Follow the installation wizard
2. **Important**: Make sure to install:
   - Android SDK
   - Android SDK Platform
   - Android Virtual Device
   - Performance (Intel HAXM) - if available

### 2.3 Configure Android SDK
1. Open Android Studio
2. Go to "File" → "Settings" (or "Android Studio" → "Preferences" on Mac)
3. Navigate to "Appearance & Behavior" → "System Settings" → "Android SDK"
4. Install the latest Android SDK Platform (API level 33 or higher)
5. Install Android SDK Build-Tools
6. Note the SDK location (usually `C:\Users\[username]\AppData\Local\Android\Sdk`)

## Step 3: Set Up Flutter for Windows Development

### 3.1 Enable Windows Desktop Support
```bash
flutter config --enable-windows-desktop
```

### 3.2 Enable Web Support (Optional)
```bash
flutter config --enable-web
```

### 3.3 Run Flutter Doctor
```bash
flutter doctor
```

### 3.4 Fix Any Issues
- If you see red X marks, follow the suggested fixes
- Common issues and solutions:
  - **Android SDK not found**: Add Android SDK to PATH
  - **Android licenses not accepted**: Run `flutter doctor --android-licenses`
  - **Visual Studio not found**: Install Visual Studio Community with C++ workload

## Step 4: Install Visual Studio (Required for Windows Desktop)

### 4.1 Download Visual Studio
1. Go to [https://visualstudio.microsoft.com/downloads/](https://visualstudio.microsoft.com/downloads/)
2. Download Visual Studio Community (free)

### 4.2 Install with Required Components
1. Run the installer
2. Select "Desktop development with C++" workload
3. Make sure these components are selected:
   - MSVC v143 - VS 2022 C++ x64/x86 build tools
   - Windows 10/11 SDK
   - CMake tools for Visual Studio
4. Click "Install"

## Step 5: Set Up the DataWipe Flutter App

### 5.1 Navigate to Flutter App Directory
```bash
cd D:\datawi\flutter_app
```

### 5.2 Install Dependencies
```bash
flutter pub get
```

### 5.3 Check Flutter Doctor Again
```bash
flutter doctor
```
Make sure all checkmarks are green.

## Step 6: Run the Flutter App

### 6.1 Start the Backend API (Required)
1. Open a new terminal/command prompt
2. Navigate to the main project directory:
   ```bash
   cd D:\datawi
   ```
3. Start the FastAPI backend:
   ```bash
   python main.py
   ```
4. Wait for the message: "Server will be available at: http://localhost:8000"

### 6.2 Run Flutter App on Windows Desktop
1. Open a new terminal/command prompt
2. Navigate to the Flutter app directory:
   ```bash
   cd D:\datawi\flutter_app
   ```
3. Run the app:
   ```bash
   flutter run -d windows
   ```

### 6.3 Alternative: Run Flutter App on Web
1. In the same Flutter app directory:
   ```bash
   flutter run -d web-server --web-port 3001
   ```
2. Open your browser and go to: `http://localhost:3001`

## Step 7: Verify Everything is Working

### 7.1 Check Backend API
- Open browser and go to: `http://localhost:8000/docs`
- You should see the FastAPI documentation

### 7.2 Check Flutter App
- The Flutter app should open in a new window
- You should see the DataWipe interface
- Try navigating between tabs (Dashboard, Wipe Data, History, Settings)

## Troubleshooting

### Common Issues and Solutions

#### 1. Flutter Doctor Shows Issues
```bash
# Accept Android licenses
flutter doctor --android-licenses

# Update Flutter
flutter upgrade

# Clean and get packages
# flutter clean
flutter pub get
```

#### 2. "flutter: command not found"
- Make sure Flutter is added to your PATH
- Restart your terminal/command prompt
- Try running: `C:\flutter\bin\flutter --version`

#### 3. Android SDK Issues
- Make sure Android Studio is installed
- Set ANDROID_HOME environment variable to your SDK path
- Add `%ANDROID_HOME%\tools` and `%ANDROID_HOME%\platform-tools` to PATH

#### 4. Visual Studio Issues
- Make sure Visual Studio is installed with C++ workload
- Run Visual Studio Installer and modify installation
- Install "Desktop development with C++" workload

#### 5. Backend API Not Starting
- Make sure Python dependencies are installed:
  ```bash
  pip install -r requirements.txt
  ```
- Check if port 8000 is already in use
- Try running with different port:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8001
  ```

#### 6. Flutter App Can't Connect to Backend
- Make sure the backend is running on `http://localhost:8000`
- Check the API URL in Flutter app settings
- Verify firewall isn't blocking the connection

## Development Commands

### Useful Flutter Commands
```bash
# Check available devices
flutter devices

# Run on specific device
flutter run -d windows
flutter run -d web-server --web-port 3001

# Hot reload (while app is running)
# Press 'r' in the terminal

# Hot restart (while app is running)
# Press 'R' in the terminal

# Stop the app
# Press 'q' in the terminal

# Build for release
flutter build windows
flutter build web
```

### Backend Commands
```bash
# Start backend
python main.py

# Start with different port
uvicorn main:app --host 0.0.0.0 --port 8001

# Install dependencies
pip install -r requirements.txt

# Check backend health
curl http://localhost:8000/health
```

## File Structure
```
D:\datawi\
├── main.py                 # FastAPI backend
├── requirements.txt        # Python dependencies
├── flutter_app/           # Flutter frontend
│   ├── lib/
│   ├── pubspec.yaml
│   └── ...
├── web_frontend/          # Alternative web frontend
└── ...
```

## Next Steps

1. **Test the App**: Try all features (device detection, user registration, wipe operations)
2. **Customize**: Modify the UI, add new features, or change the backend logic
3. **Build for Production**: Use `flutter build windows` to create a distributable executable
4. **Deploy**: Package the app for distribution

## Support

If you encounter issues:
1. Check the Flutter documentation: [https://flutter.dev/docs](https://flutter.dev/docs)
2. Check the FastAPI documentation: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
3. Review the error messages in the terminal
4. Make sure all prerequisites are properly installed

---

**Note**: This guide assumes you're running Windows 10/11 with administrator privileges. Some steps may require elevated permissions.
