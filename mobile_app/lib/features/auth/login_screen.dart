import 'package:flutter/material.dart';

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
  final name = TextEditingController(), email = TextEditingController(), password = TextEditingController();
  bool register = false, busy = false;
  String? error;

  @override
  void dispose() { name.dispose(); email.dispose(); password.dispose(); super.dispose(); }

  Future<void> submit() async {
    if (!form.currentState!.validate()) return;
    setState(() { busy = true; error = null; });
    try {
      await widget.api.authenticate(email: email.text.trim(), password: password.text,
          name: register ? name.text.trim() : null);
      widget.onSignedIn();
    } catch (reason) {
      if (mounted) setState(() => error = reason.toString());
    } finally { if (mounted) setState(() => busy = false); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(child: Center(child: SingleChildScrollView(padding: const EdgeInsets.all(24), child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 440), child: Form(key: form, child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            const Icon(Icons.center_focus_strong, size: 62, color: Color(0xFF22D3C5)),
            const SizedBox(height: 20), Text('InspectPin AI', textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineLarge),
            const Text('Camera, voice and inspection evidence', textAlign: TextAlign.center), const SizedBox(height: 36),
            if (register) TextFormField(controller: name, decoration: const InputDecoration(labelText: 'Name'), validator: (value) => value == null || value.trim().isEmpty ? 'Enter your name' : null),
            if (register) const SizedBox(height: 12),
            TextFormField(controller: email, keyboardType: TextInputType.emailAddress, autofillHints: const [AutofillHints.email], decoration: const InputDecoration(labelText: 'Email'), validator: (value) => value != null && value.contains('@') ? null : 'Enter a valid email'),
            const SizedBox(height: 12), TextFormField(controller: password, obscureText: true, autofillHints: [register ? AutofillHints.newPassword : AutofillHints.password], decoration: const InputDecoration(labelText: 'Password'), validator: (value) => value != null && value.length >= 6 ? null : 'Use at least 6 characters'),
            if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
            const SizedBox(height: 20), FilledButton(onPressed: busy ? null : submit, child: Text(busy ? 'Connecting…' : register ? 'Create account' : 'Sign in')),
            TextButton(onPressed: busy ? null : () => setState(() { register = !register; error = null; }), child: Text(register ? 'Use an existing account' : 'Create an account')),
          ])),
        )))),
      );
}
