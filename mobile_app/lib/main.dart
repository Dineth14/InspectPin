import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'features/auth/login_screen.dart';
import 'features/shell/home_shell.dart';
import 'services/api_client.dart';

void main() => runApp(const InspectPinApp());

class InspectPinApp extends StatefulWidget {
  const InspectPinApp({super.key});
  @override
  State<InspectPinApp> createState() => _InspectPinAppState();
}

class _InspectPinAppState extends State<InspectPinApp> {
  static const storage = FlutterSecureStorage();
  final api = ApiClient(
    baseUrl: const String.fromEnvironment('INSPECTPIN_API_URL', defaultValue: 'http://10.0.2.2:5000'),
    storage: storage,
  );
  bool loading = true, signedIn = false;

  @override
  void initState() {
    super.initState();
    api.restore().then((value) {
      if (mounted) setState(() { signedIn = value; loading = false; });
    });
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'InspectPin AI',
        debugShowCheckedModeBanner: false,
        themeMode: ThemeMode.system,
        theme: _theme(Brightness.light),
        darkTheme: _theme(Brightness.dark),
        home: loading
            ? const Scaffold(body: Center(child: CircularProgressIndicator()))
            : signedIn
                ? HomeShell(api: api, onSignedOut: () => setState(() => signedIn = false))
                : LoginScreen(api: api, onSignedIn: () => setState(() => signedIn = true)),
      );

  ThemeData _theme(Brightness brightness) {
    const cyan = Color(0xFF22D3C5);
    final dark = brightness == Brightness.dark;
    return ThemeData(
      brightness: brightness,
      colorScheme: ColorScheme.fromSeed(seedColor: cyan, brightness: brightness),
      scaffoldBackgroundColor: dark ? const Color(0xFF071018) : const Color(0xFFF3F7F8),
      cardTheme: CardThemeData(
        color: dark ? const Color(0xFF0D1923) : Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      useMaterial3: true,
    );
  }
}

