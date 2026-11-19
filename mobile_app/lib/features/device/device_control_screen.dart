import 'dart:async';

import 'package:flutter/material.dart';

import '../../design/components.dart';
import '../../models/product_models.dart';
import '../../services/api_client.dart';

class DeviceControlScreen extends StatefulWidget {
  const DeviceControlScreen({super.key, required this.api, required this.device});
  final ApiClient api;
  final DeviceSummary device;
  @override
  State<DeviceControlScreen> createState() => _DeviceControlScreenState();
}

class _DeviceControlScreenState extends State<DeviceControlScreen> {
  bool busy = false, flashlight = false;
  double brightness = 100, volume = 100;
  String? status;

  Future<void> command(String type, [Map<String, dynamic> payload = const {}]) async {
    setState(() { busy = true; status = 'Sending $type...'; });
    try {
      final queued = await widget.api.sendDeviceCommand(widget.device.id, type, payload: payload);
      Map<String, dynamic> current = queued;
      for (var attempt = 0; attempt < 40; attempt++) {
        current = await widget.api.commandStatus(queued['id'] as String);
        final state = current['status']?.toString();
        if (state != 'pending') break;
        await Future<void>.delayed(const Duration(milliseconds: 500));
      }
      if (mounted) setState(() => status = 'Command ${current['status']}: ${current['result'] ?? ''}');
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
      if (status != null) IpNotice(text: status!, error: status!.toLowerCase().contains('failed')),
      IpPanel(child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        const IpEyebrow('Remote capture'),
        const SizedBox(height: 8),
        const Text('The device must be awake, connected, paired, and polling the backend.'),
        const SizedBox(height: 14),
        FilledButton.icon(onPressed: busy || !widget.device.online ? null : () => command('capture_photo'), icon: const Icon(Icons.camera_alt_outlined), label: const Text('Capture photo')),
        OutlinedButton.icon(onPressed: busy || !widget.device.online ? null : () => command('retry_upload'), icon: const Icon(Icons.sync), label: const Text('Retry pending upload')),
      ])),
      const SizedBox(height: 12),
      IpPanel(child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        const IpEyebrow('Flashlight'),
        SwitchListTile(contentPadding: EdgeInsets.zero, title: const Text('White inspection light'), value: flashlight,
          onChanged: busy ? null : (value) { setState(() => flashlight = value); command('set_flashlight', {'enabled': value, 'brightness': brightness.round()}); }),
        Slider(value: brightness, min: 0, max: 255, divisions: 17, label: brightness.round().toString(), onChanged: (value) => setState(() => brightness = value),
      ])),
      const SizedBox(height: 12),
      IpPanel(child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        const IpEyebrow('Audio and haptic'),
        Text('Speaker volume ${volume.round()}%'),
        Slider(value: volume, min: 0, max: 100, divisions: 20, label: '${volume.round()}%', onChanged: (value) => setState(() => volume = value), onChangeEnd: (value) => command('set_volume', {'percent': value.round()})),
        OutlinedButton.icon(onPressed: busy ? null : () => command('vibrate', {'enabled': true, 'intensity': 128}), icon: const Icon(Icons.vibration), label: const Text('Test vibration')),
      ])),
    ]),
  );
}
