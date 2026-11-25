import 'dart:async';

import 'package:material_ui/material_ui.dart';

import '../../design/components.dart';
import '../../models/product_models.dart';
import '../../services/api_client.dart';

class FirmwareUpdateScreen extends StatefulWidget {
  const FirmwareUpdateScreen(
      {super.key, required this.device, required this.api});
  final DeviceSummary device;
  final ApiClient api;

  @override
  State<FirmwareUpdateScreen> createState() => _FirmwareUpdateScreenState();
}

class _FirmwareUpdateScreenState extends State<FirmwareUpdateScreen> {
  Map<String, dynamic>? data;
  String? error;
  bool busy = false, power = false;
  Timer? refreshTimer;
  Map<String, dynamic>? get update => data?['update'] as Map<String, dynamic>?;
  bool get active => const [
        'queued',
        'downloading',
        'verifying',
        'installing',
        'restarting'
      ].contains(update?['state']);

  @override
  void initState() {
    super.initState();
    load();
    refreshTimer = Timer.periodic(const Duration(seconds: 4), (_) {
      if (active && !busy) load();
    });
  }

  @override
  void dispose() {
    refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> run(Future<void> Function() action) async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await action();
      final catalog = await widget.api.firmwareCatalog(widget.device.id);
      if (mounted) setState(() => data = catalog);
    } catch (reason) {
      if (mounted) setState(() => error = reason.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> load() => run(() async {});

  @override
  Widget build(BuildContext context) {
    final installed = data?['installed'] as Map?;
    final packages = (data?['packages'] as List? ?? const []).whereType<Map>();
    final phase = update?['state'];
    final connected = data?['online'] == true;
    return Scaffold(
      appBar: AppBar(title: const Text('Firmware update')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (error != null) IpNotice(text: error!, error: true),
        IpPanel(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const IpEyebrow('Installed on device'),
          Text(installed == null
              ? 'Waiting for a device-reported firmware version.'
              : '${installed['version']} · ${installed['build']}'),
          Text(
              '${installed?['hardware'] ?? widget.device.hardwareRevision} · slot ${installed?['boot_slot'] ?? 'unknown'}'),
          Text(connected
              ? 'Receiver has a recent device heartbeat'
              : 'Waiting for device connection'),
          if (installed?['ota_enabled'] != true)
            const Text(
                'USB installation is required to provision secure wireless updates.'),
          if (phase != null) ...[
            const Divider(),
            Text('Last update · $phase'),
            if (update?['bytes'] case final bytes?)
              Text('$bytes bytes received'),
            if (update?['detail'] case final detail?) Text('$detail'),
            if (phase == 'queued')
              OutlinedButton(
                  onPressed: busy
                      ? null
                      : () => run(
                          () => widget.api.cancelFirmware(widget.device.id)),
                  child: const Text('Cancel queued update')),
          ],
          OutlinedButton(
              onPressed: busy ? null : load,
              child: const Text('Check for updates')),
        ])),
        const SizedBox(height: 12),
        IpPanel(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
              const IpEyebrow('Approved firmware'),
              if (packages.isEmpty)
                const Text('No signed packages are available.'),
              if (packages.any((p) => p['compatible'] == true))
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  value: power,
                  onChanged: active
                      ? null
                      : (value) => setState(() => power = value == true),
                  title: const Text('I confirmed stable external power'),
                  subtitle: const Text(
                      'Keep the device powered until it restarts and reports completion.'),
                ),
              for (final package in packages) ...[
                Text('${package['version']} · ${package['size']} bytes'),
                Text('${package['notes'] ?? ''}'),
                Text(package['compatible'] == true
                    ? 'Compatible'
                    : 'Incompatible or already installed'),
                FilledButton(
                  onPressed: active ||
                          busy ||
                          !power ||
                          !connected ||
                          package['compatible'] != true
                      ? null
                      : () => run(() => widget.api.installFirmware(
                          widget.device.id, package['sha256'] as String)),
                  child: const Text('Install approved firmware'),
                ),
              ],
            ])),
        const SizedBox(height: 12),
        const Text(
            'USB recovery: keep the original application backup and use the documented USB recovery procedure from the laptop.'),
      ]),
    );
  }
}
