import 'dart:async';

import 'package:flutter/material.dart';

import '../../models/product_models.dart';
import '../../services/api_client.dart';
import '../dashboard/battery_card.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key, required this.api, required this.onSignedOut});
  final ApiClient api;
  final VoidCallback onSignedOut;
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> with WidgetsBindingObserver {
  DashboardData? data;
  bool loading = true;
  String? error, notice;
  int tab = 0;
  String? assistantInspection;
  final assistantQuestion = TextEditingController();

  @override
  void initState() { super.initState(); WidgetsBinding.instance.addObserver(this); refresh(); }
  @override
  void dispose() { WidgetsBinding.instance.removeObserver(this); assistantQuestion.dispose(); super.dispose(); }
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) { if (state == AppLifecycleState.resumed) refresh(); }

  Future<void> refresh() async {
    setState(() { loading = true; error = null; });
    try { final result = await widget.api.dashboard(); if (mounted) setState(() { data = result; assistantInspection ??= result.inspections.isEmpty ? null : result.inspections.first.id; }); }
    catch (reason) { if (mounted) setState(() => error = reason.toString()); }
    finally { if (mounted) setState(() => loading = false); }
  }

  @override
  Widget build(BuildContext context) {
    final titles = ['Home', 'Inspections', 'Assistant', 'Devices', 'Account'];
    return Scaffold(
      appBar: AppBar(title: Text(titles[tab]), actions: [IconButton(onPressed: loading ? null : refresh, tooltip: 'Refresh', icon: const Icon(Icons.refresh))]),
      body: RefreshIndicator(onRefresh: refresh, child: ListView(padding: const EdgeInsets.all(16), children: [
        if (loading && data == null) const Padding(padding: EdgeInsets.all(80), child: Center(child: CircularProgressIndicator())),
        if (error != null) MessageCard(error!, Icons.error_outline, Theme.of(context).colorScheme.error),
        if (notice != null) MessageCard(notice!, Icons.check_circle_outline, const Color(0xFF22A99D)),
        if (data != null) switch (tab) { 0 => _home(data!), 1 => _inspections(data!), 2 => _assistant(data!), 3 => _devices(data!), _ => _account() },
      ])),
      bottomNavigationBar: NavigationBar(selectedIndex: tab, onDestinationSelected: (value) => setState(() { tab = value; notice = null; }), destinations: const [
        NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
        NavigationDestination(icon: Icon(Icons.photo_library_outlined), label: 'History'),
        NavigationDestination(icon: Icon(Icons.chat_bubble_outline), label: 'Assistant'),
        NavigationDestination(icon: Icon(Icons.memory_outlined), label: 'Devices'),
        NavigationDestination(icon: Icon(Icons.person_outline), label: 'Account'),
      ]),
    );
  }

  Widget _home(DashboardData value) => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(value.devices.any((item) => item.online) ? 'Ready to inspect' : 'Waiting for your InspectPin', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 6), const Text('All values below are reported by the backend. Simulator data is labelled.'), const SizedBox(height: 16),
        if (value.devices.isEmpty) const EmptyCard('No paired device. Pair hardware or start the desktop simulator.'),
        for (final device in value.devices.take(1)) ...[DeviceCard(device: device, onCapture: () => _capture(device)), BatteryCard(status: device.battery)],
        const SizedBox(height: 20), Text('Recent inspections', style: Theme.of(context).textTheme.titleLarge),
        for (final inspection in value.inspections.take(5)) InspectionTile(inspection, onTap: () => _openInspection(inspection.id)),
      ]);

  Widget _inspections(DashboardData value) => value.inspections.isEmpty
      ? const EmptyCard('No inspections have been stored.')
      : Column(children: [for (final item in value.inspections) InspectionTile(item, onTap: () => _openInspection(item.id))]);
  Widget _assistant(DashboardData value) {
    if (value.inspections.isEmpty) return const EmptyCard('Capture or upload an inspection before asking a grounded question.');
    return Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Text('Contextual assistant', style: Theme.of(context).textTheme.titleLarge), const SizedBox(height: 12),
      DropdownButtonFormField<String>(initialValue: assistantInspection, decoration: const InputDecoration(labelText: 'Inspection'),
        items: [for (final item in value.inspections) DropdownMenuItem(value: item.id, child: Text(item.title, overflow: TextOverflow.ellipsis))],
        onChanged: (selected) => setState(() => assistantInspection = selected)),
      const SizedBox(height: 12), TextField(controller: assistantQuestion, maxLength: 500, minLines: 3, maxLines: 5, decoration: const InputDecoration(labelText: 'Question', hintText: 'What visible marking can you read?')),
      FilledButton(onPressed: loading ? null : _askAssistant, child: const Text('Ask InspectPin')),
      const SizedBox(height: 10), const Text('The answer is bound to the selected stored image and remains advisory.', style: TextStyle(fontSize: 12)),
    ])));
  }
  Widget _devices(DashboardData value) => Column(children: [
        for (final device in value.devices) DeviceCard(device: device, onCapture: () => _capture(device)),
        OutlinedButton.icon(onPressed: _showPairDialog, icon: const Icon(Icons.add), label: const Text('Pair development device')),
      ]);
  Widget _account() => Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text('Privacy and account', style: Theme.of(context).textTheme.titleLarge), const SizedBox(height: 8),
        const Text('Media access is ownership-protected. AI credentials remain on the backend. Account deletion requires an administrator in this prototype.'),
        const SizedBox(height: 20), OutlinedButton(onPressed: () async { await widget.api.signOut(); widget.onSignedOut(); }, child: const Text('Sign out')),
      ])));

  Future<void> _capture(DeviceSummary device) async {
    try { await widget.api.requestPhoto(device.id); setState(() => notice = 'Photo command queued for ${device.name}.'); }
    catch (reason) { setState(() => error = reason.toString()); }
  }
  Future<void> _askAssistant() async {
    final inspection = assistantInspection, question = assistantQuestion.text.trim();
    if (inspection == null || question.isEmpty) return;
    setState(() { loading = true; error = null; notice = 'Question queued…'; });
    try {
      final job = await widget.api.askInspection(inspection, question);
      for (var attempt = 0; attempt < 150; attempt++) {
        final status = await widget.api.processingJob(job['id'] as String);
        if (status['status'] == 'completed') { assistantQuestion.clear(); await refresh(); if (mounted) setState(() => notice = 'Answer stored in the inspection timeline.'); return; }
        if (status['status'] == 'failed') throw ApiException(status['error']?.toString() ?? 'ASSISTANT_FAILED', 'Assistant processing failed', 422);
        await Future<void>.delayed(const Duration(milliseconds: 200));
      }
      throw const TimeoutException('Assistant timed out');
    } catch (reason) { if (mounted) setState(() => error = reason.toString()); }
    finally { if (mounted) setState(() => loading = false); }
  }
  Future<void> _openInspection(String id) async {
    try {
      final item = await widget.api.inspection(id);
      if (mounted) await Navigator.of(context).push(MaterialPageRoute(builder: (_) => InspectionDetail(item)));
    } catch (reason) { if (mounted) setState(() => error = reason.toString()); }
  }

  Future<void> _showPairDialog() async {
    final id = TextEditingController(), name = TextEditingController(text: 'InspectPin');
    await showDialog(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('Pair development device'), content: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: id, decoration: const InputDecoration(labelText: 'Device ID')),
        TextField(controller: name, decoration: const InputDecoration(labelText: 'Device name')),
        const SizedBox(height: 12), const Text('The returned device credential is shown once. Provision it securely on the device; do not share it.'),
      ]), actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Cancel')), FilledButton(onPressed: () async {
        try {
          final token = await widget.api.pair(id: id.text.trim(), name: name.text.trim(), model: 'xiao_esp32s3_sense_dev', hardwareRevision: 'development', firmwareVersion: 'unknown');
          if (!dialogContext.mounted) return;
          Navigator.pop(dialogContext);
          if (mounted) { setState(() => notice = 'Device credential (copy once): $token'); refresh(); }
        } catch (reason) { if (mounted) setState(() => error = reason.toString()); }
      }, child: const Text('Pair'))],
    ));
    id.dispose(); name.dispose();
  }
}

class DeviceCard extends StatelessWidget {
  const DeviceCard({super.key, required this.device, required this.onCapture});
  final DeviceSummary device; final VoidCallback onCapture;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
    Row(children: [Expanded(child: Text(device.name, style: Theme.of(context).textTheme.titleLarge)), Icon(device.online ? Icons.cloud_done : Icons.cloud_off, color: device.online ? const Color(0xFF22D3C5) : null), Text(device.online ? ' Online' : ' Offline')]),
    const SizedBox(height: 10), Text('${device.hardwareRevision} · firmware ${device.firmwareVersion}'),
    const SizedBox(height: 12), FilledButton.icon(onPressed: device.online ? onCapture : null, icon: const Icon(Icons.camera_alt_outlined), label: const Text('Request photo')),
  ])));
}

class InspectionTile extends StatelessWidget {
  const InspectionTile(this.item, {super.key, required this.onTap});
  final InspectionSummary item; final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Card(child: ListTile(onTap: onTap,
    leading: CircleAvatar(child: Text(item.simulated ? 'SIM' : 'IMG', style: const TextStyle(fontSize: 10))),
    title: Text(item.title), subtitle: Text(item.summary.isEmpty ? 'Status: ${item.status}' : item.summary, maxLines: 2, overflow: TextOverflow.ellipsis), trailing: const Icon(Icons.chevron_right),
  ));
}

class InspectionDetail extends StatelessWidget {
  const InspectionDetail(this.item, {super.key}); final InspectionSummary item;
  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: Text(item.title)), body: ListView(padding: const EdgeInsets.all(16), children: [
    if (item.simulated) const MessageCard('Simulator result — not a physical inspection.', Icons.science_outlined, Colors.orange),
    Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Analysis', style: Theme.of(context).textTheme.titleLarge), const SizedBox(height: 10), Text(item.summary.isEmpty ? 'Analysis is not complete.' : item.summary),
      for (final finding in item.findings) ListTile(contentPadding: EdgeInsets.zero, title: Text(finding.description), subtitle: Text('${finding.severity}${finding.evidence.isEmpty ? '' : ' · ${finding.evidence}'}')),
      const Divider(), const Text('Advisory visual analysis only. It does not replace electrical testing or a qualified safety inspection.', style: TextStyle(fontSize: 12)),
    ])),
  ]));
}

class MessageCard extends StatelessWidget {
  const MessageCard(this.text, this.icon, this.color, {super.key});
  final String text; final IconData icon; final Color color;
  @override Widget build(BuildContext context) => Card(color: color.withValues(alpha: .12), child: ListTile(leading: Icon(icon, color: color), title: Text(text)));
}
class EmptyCard extends StatelessWidget {
  const EmptyCard(this.text, {super.key}); final String text;
  @override Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(32), child: Text(text, textAlign: TextAlign.center)));
}
