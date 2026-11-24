import '../features/dashboard/battery_status.dart';

class DeviceSummary {
  const DeviceSummary({
    required this.id,
    required this.name,
    required this.online,
    required this.hardwareRevision,
    required this.firmwareVersion,
    required this.lastSeen,
    required this.storageFree,
    required this.storageTotal,
    required this.battery,
  });
  final String id, name, hardwareRevision, firmwareVersion;
  final bool online;
  final DateTime? lastSeen;
  final int? storageFree, storageTotal;
  final BatteryStatus battery;

  factory DeviceSummary.fromJson(Map<String, dynamic> json) => DeviceSummary(
        id: json['id'] as String,
        name: json['name'] as String? ?? 'InspectPin',
        online: json['online'] == true,
        hardwareRevision: json['hardware_revision'] as String? ?? 'Unknown',
        firmwareVersion: json['firmware_version'] as String? ?? 'Unknown',
        lastSeen: json['last_seen'] is num
            ? DateTime.fromMillisecondsSinceEpoch(
                ((json['last_seen'] as num) * 1000).round())
            : null,
        storageFree: (json['storage_free'] as num?)?.toInt(),
        storageTotal: (json['storage_total'] as num?)?.toInt(),
        battery: BatteryStatus.fromJson(json),
      );
}

class Finding {
  const Finding(this.description, this.severity, this.evidence);
  final String description, severity, evidence;
  factory Finding.fromJson(Map<String, dynamic> json) => Finding(
        json['description']?.toString() ?? 'No description',
        json['severity']?.toString() ?? 'observation',
        json['evidence']?.toString() ?? '',
      );
}

class InspectionSummary {
  const InspectionSummary({
    required this.id,
    required this.title,
    required this.status,
    required this.summary,
    required this.createdAt,
    required this.simulated,
    required this.findings,
    required this.imageMediaId,
    required this.interactions,
  });
  final String id, title, status, summary;
  final DateTime createdAt;
  final bool simulated;
  final List<Finding> findings;
  final String? imageMediaId;
  final List<InspectionInteraction> interactions;
  factory InspectionSummary.fromJson(Map<String, dynamic> json) =>
      InspectionSummary(
        id: json['id'] as String,
        title: json['title'] as String? ?? 'Inspection',
        status: json['status'] as String? ?? 'unknown',
        summary: json['summary'] as String? ?? '',
        createdAt: DateTime.fromMillisecondsSinceEpoch(
            ((json['created_at'] as num) * 1000).round()),
        simulated: json['simulated'] == true || json['simulated'] == 1,
        findings: (json['findings'] as List? ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(Finding.fromJson)
            .toList(),
        imageMediaId: json['image_media_id'] as String?,
        interactions: (json['voice_interactions'] as List? ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(InspectionInteraction.fromJson)
            .toList(),
      );
}

class InspectionInteraction {
  const InspectionInteraction(
      {required this.id,
      required this.question,
      required this.answer,
      required this.status});
  final String id, question, answer, status;
  factory InspectionInteraction.fromJson(Map<String, dynamic> json) =>
      InspectionInteraction(
          id: json['id']?.toString() ?? '',
          question: json['question']?.toString() ??
              json['transcript']?.toString() ??
              '',
          answer: json['ai_response']?.toString() ?? '',
          status: json['status']?.toString() ?? 'unknown');
}

class DashboardData {
  const DashboardData(this.devices, this.inspections);
  final List<DeviceSummary> devices;
  final List<InspectionSummary> inspections;
}

class AiConfiguration {
  const AiConfiguration({
    required this.llmProvider,
    required this.llmModel,
    required this.visionProvider,
    required this.visionModel,
    required this.ollamaUrl,
    required this.hasOpenAiKey,
    required this.hasAnthropicKey,
    required this.hasDeepSeekKey,
    required this.llmProviders,
    required this.visionProviders,
  });
  final String llmProvider, llmModel, visionProvider, visionModel, ollamaUrl;
  final bool hasOpenAiKey, hasAnthropicKey, hasDeepSeekKey;
  final List<String> llmProviders, visionProviders;
  factory AiConfiguration.fromJson(Map<String, dynamic> json) =>
      AiConfiguration(
        llmProvider: json['llm_provider']?.toString() ?? 'ollama',
        llmModel: json['llm_model']?.toString() ?? '',
        visionProvider: json['vision_provider']?.toString() ?? 'none',
        visionModel: json['vision_model']?.toString() ?? '',
        ollamaUrl: json['ollama_url']?.toString() ?? 'http://127.0.0.1:11434',
        hasOpenAiKey: json['has_openai_key'] == true,
        hasAnthropicKey: json['has_anthropic_key'] == true,
        hasDeepSeekKey: json['has_deepseek_key'] == true,
        llmProviders: (json['supported_llm_providers'] as List? ?? const [])
            .map((e) => e.toString())
            .toList(),
        visionProviders:
            (json['supported_vision_providers'] as List? ?? const [])
                .map((e) => e.toString())
                .toList(),
      );
}
