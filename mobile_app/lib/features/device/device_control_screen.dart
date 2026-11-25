import 'dart:async';

import 'package:material_ui/material_ui.dart';

import '../../design/components.dart';
import '../../models/product_models.dart';
import '../../services/api_client.dart';
import 'firmware_update_screen.dart';

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
  int soundGroups = 127;
  double soundVolume = 65;
  Map<String, dynamic>? confirmedSound;
  String? status;

  @override
  void initState() {
    super.initState();
    final reported = widget.device.soundSettings;
    if (reported != null) applySound(reported);
  }

  void applySound(Map<String, dynamic> value) {
    confirmedSound = value;
    soundGroups = (value['groups'] as num).toInt();
    soundVolume = (value['volume'] as num).toDouble();
    volume = (value['speech_volume'] as num).toDouble();
  }

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
        setState(() {
          final result = current['result'];
          if (current['status'] == 'completed' &&
              result is Map &&
              result['sound_settings'] is Map<String, dynamic>) {
            applySound(result['sound_settings'] as Map<String, dynamic>);
          }
          status = 'Command ${current['status']}';
          if (result is Map && result['error'] != null) {
            status = '$status · ${result['error']}';
          }
        });
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
                const IpEyebrow('Sound & feedback'),
                Text(confirmedSound == null
                    ? 'Waiting for the device to report its sound settings.'
                    : 'Device confirmed ${confirmedSound!['volume']}% alerts and '
                        '${confirmedSound!['speech_volume']}% AI speech.'),
                if (confirmedSound != null) ...[
                  for (final (bit, title) in const [
                    (1, 'Enable notifications'),
                    (2, 'Startup and connection'),
                    (4, 'Photo and image upload'),
                    (8, 'Voice guidance'),
                    (16, 'Audio recording'),
                    (32, 'Video recording'),
                    (64, 'Warnings and errors'),
                  ])
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(title),
                      value: (soundGroups & bit) != 0,
                      onChanged: busy
                          ? null
                          : (on) => setState(() {
                                soundGroups =
                                    on ? soundGroups | bit : soundGroups & ~bit;
                              }),
                    ),
                  Text('Requested notification volume ${soundVolume.round()}%'),
                  Slider(
                    value: soundVolume,
                    max: 100,
                    divisions: 20,
                    onChanged: busy
                        ? null
                        : (value) => setState(() => soundVolume = value),
                  ),
                  Wrap(spacing: 8, children: [
                    FilledButton(
                        onPressed: busy
                            ? null
                            : () => command('set_sound', {
                                  'groups': soundGroups,
                                  'volume': soundVolume.round()
                                }),
                        child: const Text('Save notification settings')),
                    OutlinedButton(
                        onPressed: busy ? null : () => command('test_sound'),
                        child: const Text('Test saved sound')),
                    OutlinedButton(
                        onPressed: busy
                            ? null
                            : () => command(
                                'set_sound', {'groups': 127, 'volume': 65}),
                        child: const Text('Restore notification defaults')),
                  ]),
                ],
                const Divider(height: 28),
                Text('Requested AI speech volume ${volume.round()}%'),
                Slider(
                    value: volume,
                    min: 0,
                    max: 100,
                    divisions: 20,
                    label: '${volume.round()}%',
                    onChanged: busy
                        ? null
                        : (value) => setState(() => volume = value)),
                OutlinedButton(
                    onPressed: busy
                        ? null
                        : () =>
                            command('set_volume', {'percent': volume.round()}),
                    child: const Text('Save AI speech volume')),
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
          const SizedBox(height: 12),
          IpPanel(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                const IpEyebrow('Firmware'),
                if (widget.device.reportedFirmware case final firmware?)
                  Text('${firmware['version']} · build ${firmware['build']}\n'
                      '${firmware['hardware']} · slot ${firmware['boot_slot'] ?? 'unknown'}\n'
                      '${firmware['ota_enabled'] == true ? 'Wireless updates enabled' : 'USB firmware installation'}')
                else
                  Text(
                      'Registered version ${widget.device.firmwareVersion}. Waiting for a device report.'),
                OutlinedButton(
                    onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (_) => FirmwareUpdateScreen(
                                device: widget.device, api: widget.api))),
                    child: const Text('Firmware update')),
              ])),
        ]),
      );
}
