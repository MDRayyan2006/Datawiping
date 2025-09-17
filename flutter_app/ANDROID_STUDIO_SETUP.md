# Android Studio Setup Guide for DataWipe App

## Overview

This guide provides step-by-step instructions for setting up the DataWipe Flutter application in Android Studio with all security configurations and dependencies.

## Prerequisites

### 1. Software Requirements
- **Android Studio**: Latest stable version (Arctic Fox or newer)
- **Flutter SDK**: Version 3.0.0 or newer
- **Dart SDK**: Version 3.0.0 or newer
- **Java Development Kit**: JDK 11 or newer
- **Android SDK**: API level 21 (Android 5.0) or newer

### 2. Platform Requirements
- **Windows**: Windows 10 or newer
- **macOS**: macOS 10.14 or newer
- **Linux**: Ubuntu 18.04 or newer

## Installation Steps

### 1. Install Android Studio

1. Download Android Studio from [developer.android.com](https://developer.android.com/studio)
2. Run the installer and follow the setup wizard
3. Install the recommended SDK components
4. Set up the Android Virtual Device (AVD) if needed

### 2. Install Flutter SDK

1. Download Flutter SDK from [flutter.dev](https://flutter.dev/docs/get-started/install)
2. Extract to a suitable location (e.g., `C:\flutter` on Windows)
3. Add Flutter to your PATH environment variable
4. Run `flutter doctor` to verify installation

### 3. Configure Android Studio for Flutter

1. Open Android Studio
2. Install Flutter and Dart plugins:
   - Go to `File > Settings > Plugins`
   - Search for "Flutter" and install
   - Search for "Dart" and install
   - Restart Android Studio

## Project Setup

### 1. Import the Project

1. Open Android Studio
2. Select `Open an existing Android Studio project`
3. Navigate to the `flutter_app` directory
4. Select the project and click `OK`

### 2. Configure Project Settings

#### Gradle Configuration
The project is already configured with:
- **Build Tools**: Latest version
- **Compile SDK**: Latest version
- **Target SDK**: Latest version
- **Min SDK**: API level 21

#### Security Configuration
The project includes:
- **ProGuard Rules**: Code obfuscation and optimization
- **Network Security Config**: TLS enforcement and certificate pinning
- **Manifest Permissions**: Biometric and security permissions

### 3. Install Dependencies

1. Open the terminal in Android Studio
2. Run the following commands:
```bash
flutter pub get
flutter pub upgrade
```

### 4. Configure Signing (Optional)

For release builds, configure app signing:

1. Create a keystore file:
```bash
keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

2. Create `android/key.properties`:
```properties
storePassword=<password from previous step>
keyPassword=<password from previous step>
keyAlias=upload
storeFile=<location of the key store file>
```

3. Update `android/app/build.gradle.kts`:
```kotlin
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}
```

## Security Configuration

### 1. ProGuard Configuration

The project includes comprehensive ProGuard rules in `android/app/proguard-rules.pro`:

- **Code Obfuscation**: Protects against reverse engineering
- **Encryption Protection**: Keeps encryption classes intact
- **Logging Removal**: Removes debug logs from release builds
- **Optimization**: Optimizes code for better performance

### 2. Network Security

Network security is configured in `android/app/src/main/res/xml/network_security_config.xml`:

- **TLS Enforcement**: Requires TLS 1.2+ for all connections
- **Certificate Pinning**: Supports certificate pinning for production
- **Cleartext Prevention**: Prevents unencrypted HTTP traffic
- **Localhost Exception**: Allows localhost for development

### 3. Manifest Security

Security permissions are configured in `android/app/src/main/AndroidManifest.xml`:

- **Biometric Permissions**: Fingerprint and face authentication
- **Network Permissions**: Internet and network state access
- **Storage Permissions**: Secure file access
- **Security Configuration**: Network security config reference

## Development Workflow

### 1. Running the App

#### Debug Mode
```bash
flutter run
```

#### Release Mode
```bash
flutter run --release
```

#### Profile Mode
```bash
flutter run --profile
```

### 2. Building the App

#### Debug Build
```bash
flutter build apk --debug
```

#### Release Build
```bash
flutter build apk --release
```

#### App Bundle (Recommended for Play Store)
```bash
flutter build appbundle --release
```

### 3. Testing

#### Unit Tests
```bash
flutter test
```

#### Integration Tests
```bash
flutter drive --target=test_driver/app.dart
```

## Security Features

### 1. Encryption

The app implements comprehensive encryption:

- **AES-256-GCM**: For data encryption
- **PBKDF2**: For key derivation
- **Secure Random**: For key generation
- **Key Rotation**: For enhanced security

### 2. Biometric Authentication

Biometric authentication is supported:

- **Fingerprint**: Android fingerprint authentication
- **Face ID**: Android face authentication
- **Fallback**: Device credentials as fallback
- **Security Levels**: Configurable security levels

### 3. Secure Storage

Data is stored securely:

- **EncryptedSharedPreferences**: For Android
- **Keychain**: For iOS
- **File Encryption**: For local files
- **Key Destruction**: For secure deletion

## Troubleshooting

### 1. Common Issues

#### Flutter Doctor Issues
```bash
flutter doctor -v
```
Follow the recommendations to fix any issues.

#### Gradle Build Issues
```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter pub get
```

#### Dependency Issues
```bash
flutter pub deps
flutter pub upgrade
```

### 2. Security Configuration Issues

#### ProGuard Issues
- Check `proguard-rules.pro` for missing rules
- Verify class names and packages
- Test release builds thoroughly

#### Network Security Issues
- Verify `network_security_config.xml`
- Check certificate configurations
- Test with different network conditions

#### Biometric Issues
- Verify device biometric setup
- Check manifest permissions
- Test on different devices

### 3. Performance Issues

#### Build Performance
- Enable Gradle daemon
- Increase heap size in `gradle.properties`
- Use parallel builds

#### Runtime Performance
- Profile the app with `flutter run --profile`
- Use Flutter Inspector for UI debugging
- Monitor memory usage

## Best Practices

### 1. Development

- **Code Quality**: Use linting and formatting
- **Testing**: Write comprehensive tests
- **Documentation**: Document security features
- **Version Control**: Use proper Git workflow

### 2. Security

- **Regular Updates**: Keep dependencies updated
- **Security Audits**: Regular security reviews
- **Key Management**: Proper key rotation
- **Monitoring**: Monitor security events

### 3. Deployment

- **Signing**: Use proper app signing
- **Obfuscation**: Enable ProGuard for release
- **Testing**: Test on multiple devices
- **Monitoring**: Monitor app performance

## Additional Resources

### 1. Documentation

- [Flutter Documentation](https://flutter.dev/docs)
- [Android Studio Documentation](https://developer.android.com/studio)
- [Security Best Practices](https://developer.android.com/topic/security/best-practices)

### 2. Tools

- [Flutter Inspector](https://flutter.dev/docs/development/tools/flutter-inspector)
- [Dart DevTools](https://dart.dev/tools/dart-devtools)
- [Android Studio Profiler](https://developer.android.com/studio/profile)

### 3. Community

- [Flutter Community](https://flutter.dev/community)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/flutter)
- [GitHub Issues](https://github.com/flutter/flutter/issues)

## Support

For technical support or questions:

1. Check the troubleshooting section
2. Review the security documentation
3. Contact the development team
4. Submit issues on the project repository

## Conclusion

This setup guide provides comprehensive instructions for configuring the DataWipe app in Android Studio with all security features enabled. Follow the steps carefully to ensure proper security configuration and optimal development experience.

Remember to:
- Keep dependencies updated
- Test security features thoroughly
- Follow security best practices
- Monitor app performance and security
