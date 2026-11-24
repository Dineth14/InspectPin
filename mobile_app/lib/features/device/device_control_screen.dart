import 'dart:async';

import 'package:material_ui/material_ui.dart';

import '../../design/components.dart';
import '../../models/product_models.dart';
import '../../services/api_client.dart';

class DeviceControlScreen extends StatefulWidget {
  const DeviceControlScreen(
      {super.key, required this.api, required this.device});
  final ApiClient api;
  final DeviceSummary device;
  @override
  State<DeviceControlScreen> createState() => _DeviceControlScreenState();
}

class _DeviceControlScreenState extends State<DeviceControlScreen> {
  bool busy = false;
  double volume = 100, idleSeconds = 300;
  String? status;

  Future<void> command(String type,
      [Map<String, dynamic> payload = const {}]) async {
    setState(() {
      busy = true;
      status = 'Sending $type...';
    });
    try {
      final queued = await widget.api
          .sendDeviceCommand(widget.device.id, type, payload: payload);
      Map<String, dynamic> current = queued;
      final deadline = DateTime.now().add(const Duration(seconds: 125));
      while (mounted && DateTime.now().isBefore(deadline)) {
        current = await widget.api.commandStatus(queued['id'] as String);
        final state = current['status']?.toString();
        if (state != 'pending' && state != 'accepted') break;
        if (mounted) setState(() => status = 'Command $state');
        await Future<void>.delayed(const Duration(seconds: 2));
      }
      if (mounted) {
        setState(() => status =
            'Command ${current['status']}: ${current['result'] ?? ''}');
      }
    } catch (reason) {
      if (mounted) setState(() => status = reason.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(widget.device.name)),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          if (status != null)
            IpNotice(
                text: status!, error: status!.toLowerCase().contains('failed')),
          IpPanel(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                const IpEyebrow('Remote capture'),
                const SizedBox(height: 8),
                const Text(
                    'The device must be awake, connected, paired, and polling the backend.'),
                const SizedBox(height: 14),
                FilledButton.icon(
                    onPressed: busy || !widget.device.online
                        ? null
                        : () => command('capture_photo'),
                    icon: const Icon(Icons.camera_alt_outlined),
                    label: const Text('Capture photo')),
                OutlinedButton.icon(
                    onPressed: busy || !widget.device.online
                        ? null
                        : () => command('retry_upload'),
                    icon: const Icon(Icons.sync),
                    label: const Text('Retry pending upload')),
              ])),
          const SizedBox(height: 12),
          IpPanel(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                const IpEyebrow('Audio and power'),
                Text('Speaker volume ${volume.round()}%'),
                Slider(
                    value: volume,
                    min: 0,
                    max: 100,
                    divisions: 20,
                    label: '${volume.round()}%',
                    onChanged: (value) => setState(() => volume = value),
                    onChangeEnd: (value) =>
                        command('set_volume', {'percent': value.round()})),
                const Divider(height: 28),
                Text('Automatic sleep after ${idleSeconds.round()} seconds'),
                Slider(
                    value: idleSeconds,
                    min: 30,
                    max: 1800,
                    divisions: 59,
                    label: '${idleSeconds.round()} s',
                    onChanged: (value) => setState(() => idleSeconds = value)),
                OutlinedButton.icon(
                    onPressed: busy
                        ? null
                        : () => command('set_idle_timeout',
                            {'seconds': idleSeconds.round()}),
                    icon: const Icon(Icons.bedtime_outlined),
                    label: const Text('Save sleep timeout')),
              ])),
        ]),
      );
}
