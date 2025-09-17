# Flutter Setup and Running Instructions

## Prerequisites

### 1. Install Flutter
Visit the official Flutter website: https://flutter.dev/docs/get-started/install

#### Windows:
1. Download Flutter SDK from https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.16.0-stable.zip
2. Extract to `C:\flutter`
3. Add `C:\flutter\bin` to your PATH environment variable
4. Run `flutter doctor` to check installation

#### macOS:
```bash
# Using Homebrew
brew install --cask flutter

# Or download manually from https://flutter.dev/docs/get-started/install/macos
```

#### Linux:
```bash
# Download and extract Flutter
cd ~/development
wget https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.16.0-stable.tar.xz
tar xf flutter_linux_3.16.0-stable.tar.xz
export PATH="$PATH:`pwd`/flutter/bin"
```

### 2. Install Dependencies
```bash
# Install Android Studio (for Android development)
# Install Xcode (for iOS development on macOS)
# Install VS Code with Flutter extension (recommended)
```

### 3. Verify Installation
```bash
flutter doctor
```

## Running the DataWipe Flutter App

### 1. Navigate to Flutter App Directory
```bash
cd flutter_app
```

### 2. Get Dependencies
```bash
flutter pub get
```

### 3. Run the App

#### For Web:
```bash
flutter run -d web-server --web-port 3000
```

#### For Android:
```bash
flutter run -d android
```

#### For iOS (macOS only):
```bash
flutter run -d ios
```

#### For Desktop:
```bash
# Windows
flutter run -d windows

# macOS
flutter run -d macos

# Linux
flutter run -d linux
```

### 4. Development Mode
```bash
# Hot reload enabled
flutter run --hot

# Debug mode
flutter run --debug
```

## Troubleshooting

### Common Issues:

1. **Flutter not found**: Make sure Flutter is in your PATH
2. **No devices found**: Run `flutter devices` to see available devices
<!-- 3. **Dependencies issues**: Run `flutter clean && flutter pub get` -->
4. **Build errors**: Check `flutter doctor` for missing dependencies

### Useful Commands:
```bash
# Check Flutter installation
flutter doctor

# List available devices
flutter devices

# # Clean build cache
# flutter clean

# Get dependencies
flutter pub get

# Run tests
flutter test

# Build for release
flutter build web
flutter build apk
flutter build ios
```

## App Features

The DataWipe Flutter app includes:

- **Onboarding Screen**: User registration and organization setup
- **Dashboard**: Device detection and system overview
- **Wipe Screen**: Secure data wiping with progress tracking
- **History Screen**: Past wipe operations and certificate downloads
- **Settings Screen**: Configuration and preferences

## API Integration

The Flutter app connects to the FastAPI backend running on `http://localhost:8000`. Make sure the backend is running before starting the Flutter app.

## Development Tips

1. Use `flutter run --hot` for faster development
2. Check the console for API connection issues
3. Use the Flutter Inspector in VS Code for UI debugging
4. Test on multiple devices/screen sizes
5. Use `flutter analyze` to check code quality

## Building for Production

### Web:
```bash
flutter build web
# Output will be in build/web/
```

### Android:
```bash
flutter build apk --release
# Output will be in build/app/outputs/flutter-apk/
```

### iOS:
```bash
flutter build ios --release
# Open Xcode to archive and distribute
```

## Support

For Flutter-specific issues:
- Flutter Documentation: https://flutter.dev/docs
- Flutter Community: https://flutter.dev/community
- Stack Overflow: https://stackoverflow.com/questions/tagged/flutter
