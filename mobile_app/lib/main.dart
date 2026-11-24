import 'package:material_ui/material_ui.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

import 'features/auth/login_screen.dart';
import 'features/onboarding/onboarding_screen.dart';
import 'features/shell/home_shell.dart';
import 'services/api_client.dart';
import 'design/app_theme.dart';

void main() => runApp(const InspectPinApp());

class InspectPinApp extends StatefulWidget {
  const InspectPinApp({super.key});
  @override
  State<InspectPinApp> createState() => _InspectPinAppState();
}

class _InspectPinAppState extends State<InspectPinApp> {
  static const storage = FlutterSecureStorage();
  static const configuredOrigin = String.fromEnvironment('INSPECTPIN_API_URL');
  static String get defaultOrigin {
    if (configuredOrigin.isNotEmpty) return configuredOrigin;
    if (kIsWeb && Uri.base.scheme == 'https') return Uri.base.origin;
    return kIsWeb ? 'http://127.0.0.1:5000' : 'http://10.0.2.2:5000';
  }

  final api = ApiClient(
    baseUrl: defaultOrigin,
    storage: storage,
  );
  bool loading = true, signedIn = false, onboarded = false;
  ThemeMode themeMode = ThemeMode.dark;

  @override
  void initState() {
    super.initState();
    Future.wait<Object?>([
      api.initialize(),
      storage.read(key: 'inspectpin_onboarded'),
      Future<void>.delayed(const Duration(milliseconds: 650))
    ]).then((values) {
      if (mounted) {
        setState(() {
          signedIn = values[0] as bool;
          onboarded = values[1] == 'true';
          loading = false;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'InspectPin AI',
        debugShowCheckedModeBanner: false,
        themeMode: themeMode,
        theme: InspectPinTheme.light(),
        darkTheme: InspectPinTheme.dark(),
        home: loading
            ? const SplashScreen()
            : !onboarded
                ? OnboardingScreen(onComplete: () async {
                    await storage.write(
                        key: 'inspectpin_onboarded', value: 'true');
                    if (mounted) setState(() => onboarded = true);
                  })
                : signedIn
                    ? HomeShell(
                        api: api,
                        themeMode: themeMode,
                        onThemeChanged: (value) =>
                            setState(() => themeMode = value),
                        onSignedOut: () => setState(() => signedIn = false))
                    : LoginScreen(
                        api: api,
                        onSignedIn: () => setState(() => signedIn = true)),
      );
}
