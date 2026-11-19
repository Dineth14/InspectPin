import 'package:flutter/material.dart';

import '../../design/app_theme.dart';
import '../../design/brand.dart';
import '../../design/components.dart';
import '../../services/api_client.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.api, required this.onSignedIn});
  final ApiClient api;
  final VoidCallback onSignedIn;
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final form = GlobalKey<FormState>();
  final name = TextEditingController();
  final email = TextEditingController();
  final password = TextEditingController();
  late final server = TextEditingController(text: widget.api.baseUrl);
  bool register = false, busy = false;
  String? error;

  @override
  void dispose() {
    name.dispose(); email.dispose(); password.dispose(); server.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (!form.currentState!.validate()) return;
    setState(() { busy = true; error = null; });
    try {
      await widget.api.configureBaseUrl(server.text);
      await widget.api.authenticate(
        email: email.text.trim(), password: password.text,
        name: register ? name.text.trim() : null,
      );
      widget.onSignedIn();
    } catch (reason) {
      if (mounted) setState(() => error = reason.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(child: ListView(padding: const EdgeInsets.all(24), children: [
      const Align(alignment: Alignment.centerLeft, child: InspectPinWordmark(compact: true)),
      const SizedBox(height: 48),
      Center(child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 440), child: IpPanel(
        padding: const EdgeInsets.all(26),
        child: Form(key: form, child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          const IpEyebrow('Secure workspace'),
          const SizedBox(height: 8),
          Text(register ? 'Create your workspace' : 'Welcome back', style: Theme.of(context).textTheme.headlineLarge),
          const SizedBox(height: 8),
          Text(register ? 'Start a private inspection workspace.' : 'Connect to your local or hosted InspectPin backend.'),
          const SizedBox(height: 24),
          TextFormField(
            controller: server, keyboardType: TextInputType.url,
            decoration: const InputDecoration(labelText: 'InspectPin backend URL', prefixIcon: Icon(Icons.cloud_outlined), hintText: 'https://inspectpin.example.com'),
            validator: (value) => value != null && value.trim().startsWith('http') ? null : 'Enter the backend URL',
          ),
          const SizedBox(height: 12),
          if (register) ...[
            TextFormField(controller: name, decoration: const InputDecoration(labelText: 'Full name', prefixIcon: Icon(Icons.person_outline)), validator: (value) => value == null || value.trim().isEmpty ? 'Enter your name' : null),
            const SizedBox(height: 12),
          ],
          TextFormField(controller: email, keyboardType: TextInputType.emailAddress, autofillHints: const [AutofillHints.email], decoration: const InputDecoration(labelText: 'Email address', prefixIcon: Icon(Icons.alternate_email)), validator: (value) => value != null && value.contains('@') ? null : 'Enter a valid email'),
          const SizedBox(height: 12),
          TextFormField(controller: password, obscureText: true, autofillHints: [register ? AutofillHints.newPassword : AutofillHints.password], decoration: const InputDecoration(labelText: 'Password', prefixIcon: Icon(Icons.lock_outline)), validator: (value) => value != null && value.length >= 6 ? null : 'Use at least 6 characters'),
          if (error != null) ...[const SizedBox(height: 12), IpNotice(text: error!, error: true)],
          const SizedBox(height: 20),
          FilledButton(onPressed: busy ? null : submit, child: Text(busy ? 'Connecting...' : register ? 'Create account' : 'Sign in securely')),
          TextButton(onPressed: busy ? null : () => setState(() { register = !register; error = null; }), child: Text(register ? 'I already have an account' : 'Create a new account')),
          const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            Icon(Icons.verified_user_outlined, size: 16, color: IpColors.textMuted),
            SizedBox(width: 7),
            Flexible(child: Text('Remote servers require HTTPS. Cloud provider keys remain encrypted on the backend.', style: TextStyle(fontSize: 11, color: IpColors.textMuted))),
          ]),
        ])),
      ))),
      const SizedBox(height: 30),
      const Text('Visual analysis is advisory and does not replace electrical testing.', textAlign: TextAlign.center, style: TextStyle(fontSize: 11, color: IpColors.textMuted)),
    ])),
  );
}
