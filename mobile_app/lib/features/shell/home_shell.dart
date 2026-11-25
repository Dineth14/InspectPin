import 'dart:async';
import 'dart:typed_data';
import 'package:material_ui/material_ui.dart';
import '../../design/app_theme.dart';
import '../../design/brand.dart';
import '../../design/components.dart';
import '../../models/product_models.dart';
import '../../services/api_client.dart';
import '../../services/evidence_export.dart';
import '../device/device_control_screen.dart';
import '../settings/ai_configuration_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell(
      {super.key,
      required this.api,
      required this.themeMode,
      required this.onThemeChanged,
      required this.onSignedOut});
  final ApiClient api;
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode> onThemeChanged;
  final VoidCallback onSignedOut;
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> with WidgetsBindingObserver {
  DashboardData? data;
  bool loading = true;
  String? error, notice;
  int tab = Uri.base.queryParameters['view'] == 'inspections' ? 1 : 0;
  String? assistantInspection;
  String? verifyingId, verification;
  Timer? liveTimer;
  bool checkingDevices = false;
  Future<void> updateDevices() async {
    if (data == null || checkingDevices || loading || (tab != 0 && tab != 3)) {
      return;
    }
    checkingDevices = true;
    try {
      final devices = await widget.api.pairedDevices();
      if (mounted && data != null) {
        setState(() {
          data = DashboardData(devices, data!.inspections);
          error = null;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() =>
            error = 'Receiver unreachable. Wake the laptop and check Wi-Fi.');
      }
    } finally {
      checkingDevices = false;
    }
  }

  Future<void> verify(DeviceSummary device) async {
    setState(() {
      verifyingId = device.id;
      verification = 'Waiting for a fresh heartbeat from ${device.id}…';
    });
    final clock = Stopwatch()..start();
    try {
      DateTime? baseline;
      bool initialized = false;
      while (mounted && clock.elapsed.inSeconds < 75) {
        final devices = await widget.api.pairedDevices();
        final current = devices.where((d) => d.id == device.id).firstOrNull;
        if (current == null) {
          verification = 'Device is no longer paired';
          break;
        }
        if (initialized &&
            current.online &&
            current.lastSeen != null &&
            (baseline == null || current.lastSeen!.isAfter(baseline))) {
          verification =
              'Device online · fresh heartbeat ${current.lastSeen!.toLocal()}';
          break;
        }
        if (!initialized) {
          baseline = current.lastSeen;
          initialized = true;
        }
        await Future<void>.delayed(const Duration(seconds: 3));
      }
      if (clock.elapsed.inSeconds >= 75) {
        verification =
            'Device not responding. Wake it with ASK and check Wi-Fi.';
      }
    } catch (_) {
      verification = 'Receiver unreachable. Check laptop and hotspot.';
    }
    if (mounted) {
      setState(() => verifyingId = null);
      await refresh();
    }
  }

  final assistantQuestion = TextEditingController(),
      search = TextEditingController();
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    liveTimer =
        Timer.periodic(const Duration(seconds: 15), (_) => updateDevices());
    if (Uri.base.queryParameters['inspection'] == 'latest') {
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        if (!mounted) return;
        await refresh();
        final latest = data?.inspections.firstOrNull;
        if (mounted && latest != null) await _openInspection(latest.id);
      });
    } else {
      refresh();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    liveTimer?.cancel();
    assistantQuestion.dispose();
    search.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) refresh();
  }

  Future<void> refresh() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final result = await widget.api.dashboard();
      if (mounted) {
        setState(() {
          data = result;
          assistantInspection ??=
              result.inspections.isEmpty ? null : result.inspections.first.id;
        });
      }
    } catch (reason) {
      if (mounted) setState(() => error = reason.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final titles = ['Home', 'Inspections', 'Assistant', 'Device', 'Settings'];
    return Scaffold(
      appBar: AppBar(
          toolbarHeight: 68,
          title: tab == 0
              ? const Padding(
                  padding: EdgeInsets.only(bottom: 7),
                  child: InspectPinWordmark(compact: true))
              : Text(titles[tab]),
          actions: [
            IconButton(
                onPressed: loading ? null : refresh,
                tooltip: 'Refresh',
                icon: const Icon(Icons.refresh)),
            const SizedBox(width: 8)
          ]),
      body: RefreshIndicator(
          onRefresh: refresh,
          child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 18, 16, 28),
              children: [
                if (error != null) IpNotice(text: error!, error: true),
                if (notice != null) IpNotice(text: notice!, error: false),
                if (loading && data == null) const _LoadingView(),
                if (data != null && (error == null || (tab != 0 && tab != 3)))
                  switch (tab) {
                    0 => _home(data!),
                    1 => _history(data!),
                    2 => _assistant(data!),
                    3 => _devices(data!),
                    _ => _settings()
                  }
              ])),
      bottomNavigationBar: NavigationBar(
          selectedIndex: tab,
          onDestinationSelected: (value) => setState(() {
                tab = value;
                notice = null;
              }),
          destinations: const [
            NavigationDestination(
                icon: Icon(Icons.home_outlined),
                selectedIcon: Icon(Icons.home),
                label: 'Home'),
            NavigationDestination(
                icon: Icon(Icons.photo_library_outlined),
                selectedIcon: Icon(Icons.photo_library),
                label: 'Inspections'),
            NavigationDestination(
                icon: Icon(Icons.forum_outlined),
                selectedIcon: Icon(Icons.forum),
                label: 'Assistant'),
            NavigationDestination(
                icon: Icon(Icons.memory_outlined),
                selectedIcon: Icon(Icons.memory),
                label: 'Device'),
            NavigationDestination(icon: Icon(Icons.tune), label: 'Settings')
          ]),
    );
  }

  Widget _home(DashboardData value) {
    final device = value.devices.firstOrNull;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      const IpEyebrow('Inspection control'),
      Text(
          device?.online == true
              ? 'Ready for the next detail.'
              : 'Your inspection record is ready.',
          style: Theme.of(context).textTheme.headlineLarge),
      const SizedBox(height: 8),
      const Text(
          'Live values come from the backend. Simulation is always identified.'),
      const SizedBox(height: 24),
      if (device != null)
        _DeviceHero(
            device: device,
            onCapture: () => _capture(device),
            onAsk: () => setState(() => tab = 2))
      else
        const IpEmptyState(
            icon: Icons.memory_outlined,
            title: 'Pair an InspectPin',
            body:
                'No live device data is available. Pair hardware or start the labelled simulator.'),
      const SizedBox(height: 30),
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const IpEyebrow('Recent evidence'),
          Text('Latest inspections',
              style: Theme.of(context).textTheme.titleLarge)
        ]),
        Text('${value.inspections.length} total',
            style: const TextStyle(color: IpColors.textMuted, fontSize: 11))
      ]),
      const SizedBox(height: 12),
      if (value.inspections.isEmpty)
        const IpEmptyState(
            icon: Icons.center_focus_strong,
            title: 'No inspections yet',
            body:
                'Use PHOTO on the device or request a capture when it is online.')
      else
        for (final item in value.inspections.take(4)) _inspectionRow(item)
    ]);
  }

  Widget _history(DashboardData value) {
    final query = search.text.toLowerCase(),
        items = value.inspections
            .where((item) =>
                '${item.title} ${item.summary}'.toLowerCase().contains(query))
            .toList();
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      const IpEyebrow('Evidence library'),
      Text('Inspection history',
          style: Theme.of(context).textTheme.headlineLarge),
      const SizedBox(height: 8),
      const Text('Search stored images, findings and processing state.'),
      const SizedBox(height: 20),
      TextField(
          controller: search,
          onChanged: (_) => setState(() {}),
          decoration: InputDecoration(
              prefixIcon: const Icon(Icons.search),
              hintText: 'Search title or finding',
              suffixIcon: search.text.isEmpty
                  ? null
                  : IconButton(
                      onPressed: () {
                        search.clear();
                        setState(() {});
                      },
                      icon: const Icon(Icons.close)))),
      const SizedBox(height: 14),
      Text('${items.length} result${items.length == 1 ? '' : 's'}',
          style: const TextStyle(color: IpColors.textMuted, fontSize: 11)),
      const SizedBox(height: 8),
      if (items.isEmpty)
        const IpEmptyState(
            icon: Icons.search_off,
            title: 'No matching evidence',
            body: 'Try another title or clear the search.')
      else
        for (final item in items) _inspectionRow(item)
    ]);
  }

  Widget _inspectionRow(InspectionSummary item) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _InspectionCard(item: item, onTap: () => _openInspection(item.id)),
          Wrap(spacing: 8, children: [
            OutlinedButton(
                onPressed: () => _openInspection(item.id),
                child: const Text('Open inspection')),
            TextButton.icon(
                icon: const Icon(Icons.edit_note),
                label: const Text('Inspector note'),
                onPressed: () => _editInspectionNote(item.id)),
            TextButton.icon(
                icon: const Icon(Icons.download),
                label: const Text('Download PDF'),
                onPressed: () async {
                  try {
                    final bytes = await widget.api.report(item.id);
                    await exportEvidence(
                        bytes, 'InspectPin-${item.id}.pdf', 'application/pdf');
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                          content: Text('Inspection PDF exported')));
                    }
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(context)
                          .showSnackBar(SnackBar(content: Text(e.toString())));
                    }
                  }
                }),
          ]),
          const SizedBox(height: 16)
        ],
      );

  Future<void> _editInspectionNote(String id) async {
    try {
      final inspection = await widget.api.inspection(id);
      if (!mounted) return;
      final value = await _noteDialog(context, inspection.note);
      if (value == null || !mounted) return;
      await widget.api.saveNote(id, value);
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Inspector note saved')));
      await refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  Widget _assistant(DashboardData value) {
    if (value.inspections.isEmpty) {
      return const IpEmptyState(
          icon: Icons.forum_outlined,
          title: 'No inspection context',
          body: 'Capture evidence before asking a grounded question.');
    }
    final selected = value.inspections.firstWhere(
        (item) => item.id == assistantInspection,
        orElse: () => value.inspections.first);
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      const IpEyebrow('Contextual intelligence'),
      Text('Ask InspectPin', style: Theme.of(context).textTheme.headlineLarge),
      const SizedBox(height: 8),
      const Text(
          'Technical answers stay bound to the selected evidence record.'),
      const SizedBox(height: 20),
      IpPanel(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        DropdownButtonFormField<String>(
            initialValue: selected.id,
            decoration: const InputDecoration(labelText: 'Inspection context'),
            items: [
              for (final item in value.inspections)
                DropdownMenuItem(
                    value: item.id,
                    child: Text(item.title, overflow: TextOverflow.ellipsis))
            ],
            onChanged: (id) => setState(() => assistantInspection = id)),
        const SizedBox(height: 16),
        _ContextPreview(item: selected, api: widget.api),
        const Divider(height: 32),
        if (selected.interactions.isEmpty)
          const Padding(
              padding: EdgeInsets.symmetric(vertical: 18),
              child: Text(
                  'Start with a precise question about a visible detail.',
                  textAlign: TextAlign.center))
        else
          for (final turn in selected.interactions) _ConversationTurn(turn),
        const SizedBox(height: 12),
        TextField(
            controller: assistantQuestion,
            maxLength: 500,
            minLines: 3,
            maxLines: 5,
            decoration: const InputDecoration(
                labelText: 'Ask about this evidence',
                hintText: 'What visible marking can you read?')),
        FilledButton.icon(
            onPressed: loading ? null : _askAssistant,
            icon: const Icon(Icons.arrow_upward),
            label: const Text('Ask InspectPin')),
        const SizedBox(height: 8),
        const Text(
            'Answers are advisory and do not replace electrical testing.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 10, color: IpColors.textMuted))
      ]))
    ]);
  }

  Widget _devices(DashboardData value) =>
      Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        const IpEyebrow('Instrument management'),
        Text('Connect Device',
            style: Theme.of(context).textTheme.headlineLarge),
        if (verification != null) Text(verification!),
        const SizedBox(height: 8),
        const Text(
            'Identity, live telemetry and authenticated remote controls.'),
        const SizedBox(height: 20),
        if (value.devices.isEmpty)
          IpEmptyState(
              icon: Icons.memory_outlined,
              title: 'No device paired',
              body:
                  'Pair the ID printed at startup. To configure Wi-Fi over USB, run scripts/configure_usb.ps1 on the laptop.',
              action: FilledButton(
                  onPressed: _showPairDialog,
                  child: const Text('Pair InspectPin')))
        else ...[
          for (final device in value.devices) ...[
            Text(device.connectionLabel),
            Text(device.lastSeen == null
                ? 'Paired · no heartbeat received'
                : 'Last heartbeat: ${device.lastSeen!.toLocal()}'),
            OutlinedButton(
                onPressed: verifyingId == null ? () => verify(device) : null,
                child: const Text('Verify live connection')),
            _DeviceTechnicalCard(
                device: device,
                onCapture: () => _capture(device),
                onManage: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) =>
                        DeviceControlScreen(api: widget.api, device: device)))),
            const SizedBox(height: 12)
          ],
          OutlinedButton.icon(
              onPressed: _showPairDialog,
              icon: const Icon(Icons.add),
              label: const Text('Pair another InspectPin'))
        ]
      ]);

  Widget _settings() =>
      Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        const IpEyebrow('Workspace control'),
        Text('Settings', style: Theme.of(context).textTheme.headlineLarge),
        const SizedBox(height: 20),
        IpPanel(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const IpEyebrow('Appearance'),
          Text('Interface theme',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 14),
          SegmentedButton<ThemeMode>(segments: const [
            ButtonSegment(
                value: ThemeMode.dark,
                label: Text('Midnight'),
                icon: Icon(Icons.dark_mode_outlined)),
            ButtonSegment(
                value: ThemeMode.light,
                label: Text('Precision light'),
                icon: Icon(Icons.light_mode_outlined))
          ], selected: {
            widget.themeMode
          }, onSelectionChanged: (value) => widget.onThemeChanged(value.first))
        ])),
        const SizedBox(height: 12),
        IpPanel(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
              const IpEyebrow('AI providers'),
              Text('Models and credentials',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              const Text(
                  'Select Ollama, OpenAI, Claude, or DeepSeek. Cloud keys remain encrypted on the backend and are never returned to the phone.'),
              const SizedBox(height: 16),
              FilledButton.icon(
                  onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => AiConfigurationScreen(api: widget.api))),
                  icon: const Icon(Icons.psychology_outlined),
                  label: const Text('Configure AI'))
            ])),
        const SizedBox(height: 12),
        const IpPanel(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          IpEyebrow('Connection and privacy'),
          Text('Authenticated remote workspace',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          SizedBox(height: 8),
          Text(
              'Remote backends require HTTPS. Media access is ownership checked. Provider credentials remain on the backend.')
        ])),
        const SizedBox(height: 12),
        IpPanel(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
              const IpEyebrow('Session'),
              Text('Sign out securely',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text('Connected to ${widget.api.baseUrl}',
                  style:
                      const TextStyle(fontSize: 11, color: IpColors.textMuted)),
              const SizedBox(height: 8),
              const Text('Sign out to select a different backend URL.'),
              const SizedBox(height: 16),
              OutlinedButton(
                  onPressed: () async {
                    await widget.api.signOut();
                    widget.onSignedOut();
                  },
                  child: const Text('Sign out'))
            ]))
      ]);

  Future<void> _capture(DeviceSummary device) async {
    try {
      await widget.api.requestPhoto(device.id);
      setState(() => notice = 'Photo command queued for ${device.name}.');
    } catch (reason) {
      setState(() => error = reason.toString());
    }
  }

  Future<void> _askAssistant() async {
    final id = assistantInspection, question = assistantQuestion.text.trim();
    if (id == null || question.isEmpty) return;
    setState(() {
      loading = true;
      error = null;
      notice = 'Analyzing the selected evidence…';
    });
    try {
      final job = await widget.api.askInspection(id, question);
      for (var attempt = 0; attempt < 150; attempt++) {
        final status = await widget.api.processingJob(job['id'] as String);
        if (status['status'] == 'completed') {
          assistantQuestion.clear();
          await refresh();
          if (mounted) {
            setState(
                () => notice = 'Answer stored in the inspection timeline.');
          }
          return;
        }
        if (status['status'] == 'failed') {
          throw ApiException(status['error']?.toString() ?? 'ASSISTANT_FAILED',
              'Assistant processing failed', 422);
        }
        await Future<void>.delayed(const Duration(milliseconds: 200));
      }
      throw TimeoutException('Assistant timed out');
    } catch (reason) {
      if (mounted) setState(() => error = reason.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _openInspection(String id) async {
    try {
      final item = await widget.api.inspection(id);
      if (mounted) {
        await Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => InspectionDetail(
                item: item, api: widget.api, onUpdated: refresh)));
      }
    } catch (reason) {
      if (mounted) setState(() => error = reason.toString());
    }
  }

  Future<void> _showPairDialog() async {
    final id = TextEditingController(),
        name = TextEditingController(text: 'InspectPin');
    await showDialog(
        context: context,
        builder: (dialog) => AlertDialog(
                title: const Text('Pair InspectPin'),
                content: Column(mainAxisSize: MainAxisSize.min, children: [
                  const Text(
                      'Enter the stable ID shown by firmware. BLE discovery is not available.'),
                  const SizedBox(height: 14),
                  TextField(
                      controller: id,
                      decoration:
                          const InputDecoration(labelText: 'Device ID')),
                  const SizedBox(height: 10),
                  TextField(
                      controller: name,
                      decoration:
                          const InputDecoration(labelText: 'Device name'))
                ]),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(dialog),
                      child: const Text('Cancel')),
                  FilledButton(
                      onPressed: () async {
                        try {
                          final token = await widget.api.pair(
                              id: id.text.trim(),
                              name: name.text.trim(),
                              model: 'xiao_esp32s3_sense_dev',
                              hardwareRevision: 'development',
                              firmwareVersion: 'unknown');
                          if (!dialog.mounted) return;
                          Navigator.pop(dialog);
                          if (mounted) {
                            setState(() => notice =
                                'Copy the one-time device credential now: $token');
                            refresh();
                          }
                        } catch (reason) {
                          if (mounted) {
                            setState(() => error = reason.toString());
                          }
                        }
                      },
                      child: const Text('Pair securely'))
                ]));
    id.dispose();
    name.dispose();
  }
}

class _DeviceHero extends StatelessWidget {
  const _DeviceHero(
      {required this.device, required this.onCapture, required this.onAsk});
  final DeviceSummary device;
  final VoidCallback onCapture, onAsk;
  @override
  Widget build(BuildContext context) => IpPanel(
      padding: EdgeInsets.zero,
      child: Column(children: [
        Container(
            height: 218,
            decoration: const BoxDecoration(
                color: IpColors.backgroundDeep,
                borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
            child: Stack(children: [
              const Positioned.fill(child: DeviceConcept(height: 205)),
              Positioned(
                  left: 16, top: 16, child: StatusPill(online: device.online)),
              const Positioned(
                  right: 16,
                  bottom: 12,
                  child: Text('CONCEPT VISUAL',
                      style: TextStyle(
                          fontSize: 8,
                          letterSpacing: 1.3,
                          color: IpColors.textMuted)))
            ])),
        Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(device.name,
                      style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 4),
                  Text(
                      '${device.hardwareRevision} · firmware ${device.firmwareVersion}',
                      style: const TextStyle(
                          fontSize: 11, color: IpColors.textMuted)),
                  const SizedBox(height: 18),
                  Row(children: [
                    Expanded(
                        child: _Metric(
                            icon: Icons.battery_5_bar,
                            label: 'BATTERY',
                            value: device.battery.estimatedPercent == null
                                ? 'Unavailable'
                                : '${device.battery.estimatedPercent!.round()}%')),
                    Expanded(
                        child: _Metric(
                            icon: Icons.sd_card_outlined,
                            label: 'MICROSD',
                            value: device.storageFree == null
                                ? 'Unavailable'
                                : _bytes(device.storageFree!))),
                    Expanded(
                        child: _Metric(
                            icon: Icons.wifi,
                            label: 'STATUS',
                            value: device.online ? 'Online' : 'Offline'))
                  ]),
                  const Divider(height: 30),
                  Row(children: [
                    Expanded(
                        child: FilledButton.icon(
                            onPressed: device.online ? onCapture : null,
                            icon: const Icon(Icons.camera_alt_outlined),
                            label: const Text('Capture'))),
                    const SizedBox(width: 10),
                    Expanded(
                        child: OutlinedButton.icon(
                            onPressed: onAsk,
                            icon: const Icon(Icons.mic_none),
                            label: const Text('Ask')))
                  ])
                ]))
      ]));
}

class _Metric extends StatelessWidget {
  const _Metric({required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label, value;
  @override
  Widget build(BuildContext context) => Column(children: [
        Icon(icon, color: IpColors.accent, size: 20),
        const SizedBox(height: 7),
        Text(label,
            style: const TextStyle(
                fontSize: 8, letterSpacing: 1, color: IpColors.textMuted)),
        const SizedBox(height: 4),
        Text(value,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
            maxLines: 1,
            overflow: TextOverflow.ellipsis)
      ]);
}

class _InspectionCard extends StatelessWidget {
  const _InspectionCard({required this.item, required this.onTap});
  final InspectionSummary item;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Card(
          child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: onTap,
              child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Row(children: [
                    Container(
                        width: 62,
                        height: 62,
                        decoration: BoxDecoration(
                            color: IpColors.backgroundDeep,
                            borderRadius: BorderRadius.circular(11)),
                        child: Icon(
                            item.simulated
                                ? Icons.science_outlined
                                : Icons.center_focus_strong,
                            color: item.simulated
                                ? IpColors.warning
                                : IpColors.accent)),
                    const SizedBox(width: 13),
                    Expanded(
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                          Row(children: [
                            Expanded(
                                child: Text(item.title,
                                    style:
                                        Theme.of(context).textTheme.titleMedium,
                                    overflow: TextOverflow.ellipsis)),
                            Text(item.status.toUpperCase(),
                                style: TextStyle(
                                    fontSize: 8,
                                    letterSpacing: 1,
                                    color: item.status == 'completed'
                                        ? IpColors.success
                                        : IpColors.textMuted))
                          ]),
                          const SizedBox(height: 5),
                          Text(
                              item.summary.isEmpty
                                  ? 'Analysis has not completed yet.'
                                  : item.summary,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 11)),
                          const SizedBox(height: 5),
                          Text(
                              '${item.createdAt.toLocal()} · ${item.id.substring(0, 8).toUpperCase()}',
                              style: const TextStyle(
                                  fontSize: 9, color: IpColors.textMuted))
                        ])),
                    const SizedBox(width: 8),
                    const Icon(Icons.chevron_right, color: IpColors.textMuted)
                  ])))));
}

class _ContextPreview extends StatelessWidget {
  const _ContextPreview({required this.item, required this.api});
  final InspectionSummary item;
  final ApiClient api;
  @override
  Widget build(BuildContext context) => Row(children: [
        _EvidenceThumb(mediaId: item.imageMediaId, api: api, size: 80),
        const SizedBox(width: 13),
        Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(item.title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 5),
          Text(item.summary.isEmpty ? 'No summary available.' : item.summary,
              maxLines: 3, overflow: TextOverflow.ellipsis)
        ]))
      ]);
}

class _ConversationTurn extends StatelessWidget {
  const _ConversationTurn(this.turn);
  final InspectionInteraction turn;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Align(
            alignment: Alignment.centerRight,
            child: Container(
                padding: const EdgeInsets.all(11),
                constraints: const BoxConstraints(maxWidth: 290),
                decoration: BoxDecoration(
                    color: IpColors.accent,
                    borderRadius: BorderRadius.circular(12)),
                child: Text(turn.question,
                    style: const TextStyle(
                        color: Color(0xFF03212A),
                        fontSize: 12,
                        fontWeight: FontWeight.w600)))),
        const SizedBox(height: 7),
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const InspectPinMark(size: 28),
          const SizedBox(width: 8),
          Expanded(
              child: Container(
                  padding: const EdgeInsets.all(11),
                  decoration: BoxDecoration(
                      color: IpColors.surfaceRaised,
                      borderRadius: BorderRadius.circular(12)),
                  child: Text(turn.answer.isEmpty ? 'Processing…' : turn.answer,
                      style: const TextStyle(fontSize: 12))))
        ])
      ]));
}

class _DeviceTechnicalCard extends StatelessWidget {
  const _DeviceTechnicalCard(
      {required this.device, required this.onCapture, required this.onManage});
  final DeviceSummary device;
  final VoidCallback onCapture, onManage;
  @override
  Widget build(BuildContext context) => IpPanel(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(children: [
          Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                StatusPill(online: device.online),
                const SizedBox(height: 12),
                Text(device.name,
                    style: Theme.of(context).textTheme.titleLarge),
                Text(device.id,
                    style: const TextStyle(
                        fontSize: 10, color: IpColors.textMuted))
              ])),
          const SizedBox(width: 115, child: DeviceConcept(height: 100))
        ]),
        const Divider(height: 28),
        _Spec('Hardware revision', device.hardwareRevision),
        _Spec('Firmware', device.firmwareVersion),
        _Spec(
            'Battery',
            device.battery.estimatedPercent == null
                ? 'Unavailable'
                : '${device.battery.estimatedPercent!.round()}% estimated'),
        _Spec(
            'Storage',
            device.storageFree == null
                ? 'Unavailable'
                : _bytes(device.storageFree!)),
        const SizedBox(height: 14),
        FilledButton.icon(
            onPressed: device.online ? onCapture : null,
            icon: const Icon(Icons.camera_alt_outlined),
            label: const Text('Capture inspection')),
        const SizedBox(height: 8),
        OutlinedButton.icon(
            onPressed: onManage,
            icon: const Icon(Icons.settings_remote_outlined),
            label: const Text('Remote controls'))
      ]));
}

class _Spec extends StatelessWidget {
  const _Spec(this.label, this.value);
  final String label, value;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(children: [
        Expanded(
            child: Text(label,
                style:
                    const TextStyle(fontSize: 11, color: IpColors.textMuted))),
        Flexible(
            child: Text(value,
                textAlign: TextAlign.right,
                style:
                    const TextStyle(fontSize: 11, fontWeight: FontWeight.w700)))
      ]));
}

class _EvidenceThumb extends StatelessWidget {
  const _EvidenceThumb(
      {required this.mediaId, required this.api, this.size = 100});
  final String? mediaId;
  final ApiClient api;
  final double size;
  @override
  Widget build(BuildContext context) {
    if (mediaId == null) {
      return Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
              color: IpColors.backgroundDeep,
              borderRadius: BorderRadius.circular(10)),
          child: const Icon(Icons.image_not_supported_outlined,
              color: IpColors.textMuted));
    }
    return FutureBuilder<Uint8List>(
        future: api.media(mediaId!),
        builder: (context, snapshot) => Container(
            width: size,
            height: size,
            clipBehavior: Clip.antiAlias,
            decoration: BoxDecoration(
                color: IpColors.backgroundDeep,
                borderRadius: BorderRadius.circular(10)),
            child: snapshot.hasData
                ? Image.memory(snapshot.data!, fit: BoxFit.cover)
                : snapshot.hasError
                    ? const Icon(Icons.broken_image_outlined)
                    : const Center(
                        child: CircularProgressIndicator(strokeWidth: 2))));
  }
}

Future<String?> _noteDialog(BuildContext context, String initial) {
  String draft = initial;
  return showDialog<String>(
      context: context,
      builder: (dialog) => AlertDialog(
              title: const Text('Inspector note'),
              content: TextFormField(
                  initialValue: initial,
                  autofocus: true,
                  minLines: 3,
                  maxLines: 8,
                  maxLength: 2000,
                  onChanged: (value) => draft = value,
                  decoration: const InputDecoration(labelText: 'Observation')),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(dialog),
                    child: const Text('Cancel')),
                FilledButton(
                    onPressed: () => Navigator.pop(dialog, draft),
                    child: const Text('Save note')),
              ]));
}

class InspectionDetail extends StatefulWidget {
  const InspectionDetail(
      {super.key,
      required this.item,
      required this.api,
      required this.onUpdated});
  final InspectionSummary item;
  final ApiClient api;
  final Future<void> Function() onUpdated;
  @override
  State<InspectionDetail> createState() => _InspectionDetailState();
}

class _InspectionDetailState extends State<InspectionDetail> {
  Future<void> editNote() async {
    final value = await _noteDialog(context, item.note);
    if (value == null || !mounted) return;
    setState(() => busy = true);
    try {
      final saved = await widget.api.saveNote(item.id, value);
      if (!mounted) return;
      setState(() => item = saved);
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Inspector note saved')));
      await widget.onUpdated();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  String? preparingVideo;
  Future<void> openVideo(String id) async {
    setState(() => preparingVideo = id);
    try {
      final data =
          await widget.api.playback(id, () => mounted && preparingVideo == id);
      if (mounted) await playVideo(data);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => preparingVideo = null);
    }
  }

  Future<void> playRecording(String id) async {
    try {
      final bytes = await widget.api.media(id);
      if (mounted) await playEvidence(bytes);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  Future<void> exportFile([Map<String, dynamic>? media]) async {
    setState(() => busy = true);
    try {
      final mime = media?['content_type'] as String? ?? 'application/pdf';
      final id = media?['id'] as String? ?? item.id;
      final bytes = media == null
          ? await widget.api.report(id)
          : await widget.api.media(id);
      final extension = switch (mime) {
        'image/jpeg' => 'jpg',
        'audio/wav' => 'wav',
        'application/pdf' => 'pdf',
        _ => 'avi',
      };
      await exportEvidence(bytes, 'inspectpin-$id.$extension', mime);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  late InspectionSummary item = widget.item;
  final question = TextEditingController();
  bool busy = false;
  String? message;
  @override
  void dispose() {
    question.dispose();
    unawaited(stopEvidence());
    super.dispose();
  }

  Future<void> ask() async {
    if (question.text.trim().isEmpty) return;
    setState(() {
      busy = true;
      message = 'Analyzing the selected evidence…';
    });
    try {
      final job = await widget.api.askInspection(item.id, question.text.trim());
      for (var i = 0; i < 150; i++) {
        final status = await widget.api.processingJob(job['id'] as String);
        if (status['status'] == 'completed') {
          item = await widget.api.inspection(item.id);
          question.clear();
          await widget.onUpdated();
          setState(() => message = 'Answer added to this inspection.');
          return;
        }
        if (status['status'] == 'failed') {
          throw Exception('Assistant processing failed');
        }
        await Future<void>.delayed(const Duration(milliseconds: 200));
      }
    } catch (reason) {
      setState(() => message = reason.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(
          title: Text(item.title),
          bottom: PreferredSize(
              preferredSize: const Size.fromHeight(48),
              child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    Flexible(
                        child: TextButton(
                            onPressed: busy ? null : editNote,
                            child: const FittedBox(
                                fit: BoxFit.scaleDown,
                                child: Text('Inspector note')))),
                    Flexible(
                        child: TextButton(
                            onPressed: busy ? null : () => exportFile(),
                            child: const FittedBox(
                                fit: BoxFit.scaleDown,
                                child: Text('Download PDF')))),
                  ]))),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (item.note.isNotEmpty)
          ListTile(
              title: const Text('Saved inspector note'),
              subtitle: Text(item.note)),
        for (final media in item.recordings) ...[
          if (item.recordingSeconds != null)
            Text(
                '${media['content_type'] == 'audio/wav' ? 'Audio' : 'Silent video'} · ${item.recordingSeconds!.toStringAsFixed(1)} s'),
          if (media['content_type'] == 'audio/wav')
            Wrap(children: [
              TextButton(
                  onPressed: () => playRecording(media['id'] as String),
                  child: const Text('Play recording')),
              TextButton(onPressed: stopEvidence, child: const Text('Stop')),
            ]),
          if (media['content_type'] == 'video/x-msvideo')
            TextButton(
                onPressed: preparingVideo != null
                    ? null
                    : () => openVideo(media['id'] as String),
                child: Text(preparingVideo == media['id']
                    ? 'Preparing silent video…'
                    : 'Play silent video')),
          if (media['content_type'] == 'video/x-msvideo')
            _RecordingPreview(api: widget.api, id: media['id'] as String),
          OutlinedButton(
            onPressed: busy ? null : () => exportFile(media),
            child: Text(
                'Download original ${media['content_type'] == 'audio/wav' ? 'WAV' : 'silent AVI'} · ${media['byte_size']} bytes'),
          ),
        ],
        if (item.simulated)
          const IpNotice(
              text: 'Simulator result — not a physical inspection.',
              error: false),
        IpPanel(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const IpEyebrow('Original evidence'),
          const SizedBox(height: 10),
          AspectRatio(
              aspectRatio: 4 / 3,
              child: ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: item.imageMediaId == null
                      ? const ColoredBox(
                          color: IpColors.backgroundDeep,
                          child: Icon(Icons.image_not_supported_outlined))
                      : FutureBuilder<Uint8List>(
                          future: widget.api.media(item.imageMediaId!),
                          builder: (context, snapshot) => snapshot.hasData
                              ? InteractiveViewer(
                                  minScale: 1,
                                  maxScale: 4,
                                  child: Image.memory(snapshot.data!,
                                      fit: BoxFit.contain))
                              : const ColoredBox(
                                  color: IpColors.backgroundDeep,
                                  child: Center(
                                      child: CircularProgressIndicator()))))),
          const SizedBox(height: 8),
          const Text('Pinch to zoom. Original media remains unchanged.',
              style: TextStyle(fontSize: 10, color: IpColors.textMuted)),
          if (item.imageMediaId != null)
            OutlinedButton.icon(
                icon: const Icon(Icons.download),
                label: const Text('Download original photo'),
                onPressed: busy
                    ? null
                    : () => exportFile({
                          'id': item.imageMediaId,
                          'content_type': 'image/jpeg'
                        })),
        ])),
        const SizedBox(height: 12),
        IpPanel(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const IpEyebrow('AI analysis'),
          Text(item.summary.isEmpty ? 'Analysis pending' : item.summary,
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 14),
          if (item.findings.isEmpty)
            const Text('No structured findings are available.')
          else
            for (final finding in item.findings)
              Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(13),
                  decoration: const BoxDecoration(
                      color: IpColors.surfaceRaised,
                      border: Border(
                          left: BorderSide(color: IpColors.accent, width: 2))),
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(finding.severity.toUpperCase(),
                            style: const TextStyle(
                                fontSize: 8,
                                letterSpacing: 1,
                                color: IpColors.accent)),
                        const SizedBox(height: 6),
                        Text(finding.description),
                        if (finding.evidence.isNotEmpty) ...[
                          const SizedBox(height: 5),
                          Text('Evidence: ${finding.evidence}',
                              style: const TextStyle(
                                  fontSize: 10, color: IpColors.textMuted))
                        ]
                      ])),
          const Divider(),
          const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Icon(Icons.verified_user_outlined,
                size: 17, color: IpColors.textMuted),
            SizedBox(width: 8),
            Expanded(
                child: Text(
                    'Visual advisory only. Verify with electrical testing and qualified personnel.',
                    style: TextStyle(fontSize: 10, color: IpColors.textMuted)))
          ])
        ])),
        const SizedBox(height: 12),
        IpPanel(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
              const IpEyebrow('Context thread'),
              if (item.interactions.isEmpty)
                const Padding(
                    padding: EdgeInsets.symmetric(vertical: 14),
                    child: Text('No follow-up questions yet.',
                        textAlign: TextAlign.center))
              else
                for (final turn in item.interactions) _ConversationTurn(turn),
              TextField(
                  controller: question,
                  maxLength: 500,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(
                      labelText: 'Ask about this evidence')),
              const SizedBox(height: 10),
              FilledButton.icon(
                  onPressed: busy ? null : ask,
                  icon: const Icon(Icons.arrow_upward),
                  label: Text(busy ? 'Analyzing…' : 'Ask InspectPin')),
              if (message != null) ...[
                const SizedBox(height: 8),
                Text(message!,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                        fontSize: 10, color: IpColors.textMuted))
              ]
            ])),
        Padding(
          padding: const EdgeInsets.only(top: 12),
          child: Wrap(spacing: 12, children: [
            OutlinedButton.icon(
                onPressed: busy ? null : editNote,
                icon: const Icon(Icons.edit_note),
                label: Text(item.note.isEmpty
                    ? 'Add inspector note'
                    : 'Edit inspector note')),
            OutlinedButton.icon(
                onPressed: busy ? null : () => exportFile(),
                icon: const Icon(Icons.download),
                label: const Text('Download inspection report')),
          ]),
        )
      ]));
}

class _RecordingPreview extends StatefulWidget {
  const _RecordingPreview({required this.api, required this.id});
  final ApiClient api;
  final String id;
  @override
  State<_RecordingPreview> createState() => _RecordingPreviewState();
}

class _RecordingPreviewState extends State<_RecordingPreview> {
  Future<Uint8List>? preview;
  @override
  Widget build(BuildContext context) => Column(children: [
        TextButton(
            onPressed: () => setState(() {
                  preview = preview == null
                      ? widget.api.media(widget.id, preview: true)
                      : null;
                }),
            child: Text(
                preview == null ? 'Play silent preview' : 'Close preview')),
        if (preview != null)
          FutureBuilder<Uint8List>(
              future: preview,
              builder: (context, result) {
                if (result.hasError) {
                  return const Text(
                      'Preview unavailable. Download the original below.');
                }
                return result.hasData
                    ? Image.memory(result.data!)
                    : const CircularProgressIndicator();
              }),
      ]);
}

class _LoadingView extends StatelessWidget {
  const _LoadingView();
  @override
  Widget build(BuildContext context) => Column(children: [
        for (var i = 0; i < 3; i++)
          Container(
              height: i == 0 ? 330 : 110,
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                  color: IpColors.surface,
                  borderRadius: BorderRadius.circular(16)))
      ]);
}

String _bytes(int value) {
  if (value < 1024) return '$value B';
  if (value < 1024 * 1024) return '${(value / 1024).toStringAsFixed(1)} KB';
  if (value < 1024 * 1024 * 1024) {
    return '${(value / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
  return '${(value / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
}

extension _FirstOrNull<T> on List<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
