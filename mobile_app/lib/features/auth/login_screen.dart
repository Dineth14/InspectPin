import 'package:material_ui/material_ui.dart';

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
  late String profile = widget.api.baseUrl.startsWith('https:')
      ? 'Hosted HTTPS'
      : 'Laptop / Local Server';
  String? probe;

  Future<void> configure() async {
    if (profile == 'Hosted HTTPS' &&
        !server.text.trim().startsWith('https://')) {
      throw StateError('Enter a hosted HTTPS address');
    }
    await widget.api.configureBaseUrl(server.text);
  }

  Future<void> test() async {
    setState(() {
      busy = true;
      probe = null;
    });
    try {
      await configure();
      await widget.api.testReceiver();
      if (mounted) {
        setState(
            () => probe = 'Receiver reachable. Sign in to verify your device.');
      }
    } catch (_) {
      if (mounted) {
        setState(() => probe =
            'Receiver unreachable. Check the address, hotspot and laptop receiver.');
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  String? error;

  @override
  void dispose() {
    name.dispose();
    email.dispose();
    password.dispose();
    server.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (!form.currentState!.validate()) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await configure();
      await widget.api.authenticate(
        email: email.text.trim(),
        password: password.text,
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
        body: SafeArea(
            child: ListView(padding: const EdgeInsets.all(24), children: [
          const Align(
              alignment: Alignment.centerLeft,
              child: InspectPinWordmark(compact: true)),
          const SizedBox(height: 48),
          Center(
              child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 440),
                  child: IpPanel(
                    padding: const EdgeInsets.all(26),
                    child: Form(
                        key: form,
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              const IpEyebrow('Secure workspace'),
                              const SizedBox(height: 8),
                              Text(
                                  register
                                      ? 'Create your workspace'
                                      : 'Welcome back',
                                  style: Theme.of(context)
                                      .textTheme
                                      .headlineLarge),
                              const SizedBox(height: 8),
                              Text(register
                                  ? 'Start a private inspection workspace.'
                                  : 'Connect to your local or hosted InspectPin backend.'),
                              const SizedBox(height: 24),
                              DropdownButtonFormField<String>(
                                initialValue: profile,
                                decoration: const InputDecoration(
                                    labelText: 'Connection Manager'),
                                items: [
                                  'Laptop / Local Server',
                                  'Hosted HTTPS',
                                  'Offline recording'
                                ]
                                    .map((p) => DropdownMenuItem(
                                        value: p, child: Text(p)))
                                    .toList(),
                                onChanged: busy
                                    ? null
                                    : (p) => setState(() {
                                          profile = p!;
                                          probe = null;
                                        }),
                              ),
                              Text(profile == 'Offline recording'
                                  ? 'Use the wearable buttons to save evidence on microSD. AI answers require a reachable receiver.'
                                  : profile == 'Hosted HTTPS'
                                      ? 'A hosted receiver has not been configured for this evaluation.'
                                      : 'Connect the board and laptop to the same hotspot. Enter the receiver address printed by Start InspectPin.'),
                              if (profile != 'Offline recording') ...[
                                TextFormField(
                                  controller: server,
                                  enabled: !busy,
                                  onChanged: (_) =>
                                      setState(() => probe = null),
                                  keyboardType: TextInputType.url,
                                  decoration: const InputDecoration(
                                      labelText: 'InspectPin backend URL',
                                      prefixIcon: Icon(Icons.cloud_outlined),
                                      hintText:
                                          'https://inspectpin.example.com'),
                                  validator: (value) => value != null &&
                                          value.trim().startsWith('http')
                                      ? null
                                      : 'Enter the backend URL',
                                ),
                                const SizedBox(height: 12),
                                OutlinedButton(
                                    onPressed: busy ? null : test,
                                    child:
                                        const Text('Test and save receiver')),
                                if (probe != null) Text(probe!),
                                if (register) ...[
                                  TextFormField(
                                      controller: name,
                                      decoration: const InputDecoration(
                                          labelText: 'Full name',
                                          prefixIcon:
                                              Icon(Icons.person_outline)),
                                      validator: (value) =>
                                          value == null || value.trim().isEmpty
                                              ? 'Enter your name'
                                              : null),
                                  const SizedBox(height: 12),
                                ],
                                TextFormField(
                                    controller: email,
                                    keyboardType: TextInputType.emailAddress,
                                    autofillHints: const [AutofillHints.email],
                                    decoration: const InputDecoration(
                                        labelText: 'Email address',
                                        prefixIcon:
                                            Icon(Icons.alternate_email)),
                                    validator: (value) =>
                                        value != null && value.contains('@')
                                            ? null
                                            : 'Enter a valid email'),
                                const SizedBox(height: 12),
                                TextFormField(
                                    controller: password,
                                    obscureText: true,
                                    autofillHints: [
                                      register
                                          ? AutofillHints.newPassword
                                          : AutofillHints.password
                                    ],
                                    decoration: const InputDecoration(
                                        labelText: 'Password',
                                        prefixIcon: Icon(Icons.lock_outline)),
                                    validator: (value) =>
                                        value != null && value.length >= 6
                                            ? null
                                            : 'Use at least 6 characters'),
                                if (error != null) ...[
                                  const SizedBox(height: 12),
                                  IpNotice(text: error!, error: true)
                                ],
                                const SizedBox(height: 20),
                                FilledButton(
                                    onPressed: busy ? null : submit,
                                    child: Text(busy
                                        ? 'Connecting...'
                                        : register
                                            ? 'Create account'
                                            : 'Sign in securely')),
                                TextButton(
                                    onPressed: busy
                                        ? null
                                        : () => setState(() {
                                              register = !register;
                                              error = null;
                                            }),
                                    child: Text(register
                                        ? 'I already have an account'
                                        : 'Create a new account')),
                                const Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Icon(Icons.verified_user_outlined,
                                          size: 16, color: IpColors.textMuted),
                                      SizedBox(width: 7),
                                      Flexible(
                                          child: Text(
                                              'Remote servers require HTTPS. Cloud provider keys remain encrypted on the backend.',
                                              style: TextStyle(
                                                  fontSize: 11,
                                                  color: IpColors.textMuted))),
                                    ]),
                              ],
                            ])),
                  ))),
          const SizedBox(height: 30),
          const Text(
              'Visual analysis is advisory and does not replace electrical testing.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 11, color: IpColors.textMuted)),
        ])),
      );
}
