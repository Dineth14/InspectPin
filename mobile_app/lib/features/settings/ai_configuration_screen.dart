import 'package:material_ui/material_ui.dart';

import '../../design/app_theme.dart';
import '../../design/components.dart';
import '../../models/product_models.dart';
import '../../services/api_client.dart';

class AiConfigurationScreen extends StatefulWidget {
  const AiConfigurationScreen({super.key, required this.api});
  final ApiClient api;
  @override
  State<AiConfigurationScreen> createState() => _AiConfigurationScreenState();
}

class _AiConfigurationScreenState extends State<AiConfigurationScreen> {
  AiConfiguration? config;
  final llmModel = TextEditingController();
  final visionModel = TextEditingController();
  final ollamaUrl = TextEditingController();
  final openAiKey = TextEditingController();
  final anthropicKey = TextEditingController();
  final deepSeekKey = TextEditingController();
  String llmProvider = 'ollama', visionProvider = 'ollama';
  bool loading = true, saving = false;
  String? message;

  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    llmModel.dispose();
    visionModel.dispose();
    ollamaUrl.dispose();
    openAiKey.dispose();
    anthropicKey.dispose();
    deepSeekKey.dispose();
    super.dispose();
  }

  Future<void> load() async {
    try {
      final value = await widget.api.aiConfiguration();
      if (!mounted) return;
      setState(() {
        config = value;
        llmProvider = value.llmProvider;
        visionProvider = value.visionProvider;
        llmModel.text = value.llmModel;
        visionModel.text = value.visionModel;
        ollamaUrl.text = value.ollamaUrl;
        loading = false;
      });
    } catch (reason) {
      if (mounted) {
        setState(() {
          message = reason.toString();
          loading = false;
        });
      }
    }
  }

  Future<void> save() async {
    setState(() {
      saving = true;
      message = null;
    });
    try {
      final payload = <String, dynamic>{
        'llm_provider': llmProvider,
        'llm_model': llmModel.text.trim(),
        'vision_provider': visionProvider,
        'vision_model': visionModel.text.trim(),
        'ollama_url': ollamaUrl.text.trim(),
      };
      if (openAiKey.text.trim().isNotEmpty) {
        payload['openai_api_key'] = openAiKey.text.trim();
      }
      if (anthropicKey.text.trim().isNotEmpty) {
        payload['anthropic_api_key'] = anthropicKey.text.trim();
      }
      if (deepSeekKey.text.trim().isNotEmpty) {
        payload['deepseek_api_key'] = deepSeekKey.text.trim();
      }
      final value = await widget.api.updateAiConfiguration(payload);
      openAiKey.clear();
      anthropicKey.clear();
      deepSeekKey.clear();
      if (mounted) {
        setState(() {
          config = value;
          message = 'AI configuration saved securely.';
        });
      }
    } catch (reason) {
      if (mounted) setState(() => message = reason.toString());
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Future<void> test() async {
    setState(() {
      saving = true;
      message = 'Testing provider...';
    });
    try {
      final result = await widget.api.testAiConfiguration();
      if (mounted) {
        setState(() => message =
            '${result['provider']} / ${result['model']}: ${result['response']}');
      }
    } catch (reason) {
      if (mounted) setState(() => message = reason.toString());
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  String providerLabel(String value) => switch (value) {
        'ollama' => 'Ollama (local)',
        'openai' => 'OpenAI API',
        'anthropic' => 'Anthropic Claude',
        'deepseek' => 'DeepSeek API',
        'none' => 'Disabled',
        _ => value,
      };

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('AI configuration')),
        body: loading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (message != null)
                    IpNotice(
                        text: message!,
                        error: message!.toLowerCase().contains('error')),
                  IpPanel(
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                        const IpEyebrow('Text reasoning'),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          initialValue: llmProvider,
                          decoration:
                              const InputDecoration(labelText: 'Provider'),
                          items: [
                            for (final value in config!.llmProviders)
                              DropdownMenuItem(
                                  value: value,
                                  child: Text(providerLabel(value)))
                          ],
                          onChanged: saving
                              ? null
                              : (value) => setState(() => llmProvider = value!),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                            controller: llmModel,
                            decoration: const InputDecoration(
                                labelText: 'Text model ID',
                                hintText: 'Enter the provider model ID')),
                        if (llmProvider == 'ollama') ...[
                          const SizedBox(height: 12),
                          TextField(
                              controller: ollamaUrl,
                              keyboardType: TextInputType.url,
                              decoration: const InputDecoration(
                                  labelText: 'Ollama server URL')),
                        ],
                      ])),
                  const SizedBox(height: 12),
                  IpPanel(
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                        const IpEyebrow('Camera understanding'),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          initialValue: visionProvider,
                          decoration: const InputDecoration(
                              labelText: 'Vision provider'),
                          items: [
                            for (final value in config!.visionProviders)
                              DropdownMenuItem(
                                  value: value,
                                  child: Text(providerLabel(value)))
                          ],
                          onChanged: saving
                              ? null
                              : (value) =>
                                  setState(() => visionProvider = value!),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                            controller: visionModel,
                            enabled: visionProvider != 'none',
                            decoration: const InputDecoration(
                                labelText: 'Vision-capable model ID')),
                        const SizedBox(height: 8),
                        const Text(
                            'OpenAI API access is separate from a ChatGPT subscription. Claude API access is separate from a Claude consumer subscription.',
                            style: TextStyle(
                                fontSize: 11, color: IpColors.textMuted)),
                      ])),
                  const SizedBox(height: 12),
                  IpPanel(
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                        const IpEyebrow('Cloud credentials'),
                        const SizedBox(height: 8),
                        TextField(
                            controller: openAiKey,
                            obscureText: true,
                            enableSuggestions: false,
                            autocorrect: false,
                            decoration: InputDecoration(
                                labelText: config!.hasOpenAiKey
                                    ? 'Replace OpenAI API key (optional)'
                                    : 'OpenAI API key')),
                        const SizedBox(height: 12),
                        TextField(
                            controller: anthropicKey,
                            obscureText: true,
                            enableSuggestions: false,
                            autocorrect: false,
                            decoration: InputDecoration(
                                labelText: config!.hasAnthropicKey
                                    ? 'Replace Anthropic API key (optional)'
                                    : 'Anthropic API key')),
                        const SizedBox(height: 12),
                        TextField(
                            controller: deepSeekKey,
                            obscureText: true,
                            enableSuggestions: false,
                            autocorrect: false,
                            decoration: InputDecoration(
                                labelText: config!.hasDeepSeekKey
                                    ? 'Replace DeepSeek API key (optional)'
                                    : 'DeepSeek API key')),
                        const SizedBox(height: 8),
                        const Text(
                            'Keys are write-only: they are sent to the backend once, encrypted at rest, and never returned.',
                            style: TextStyle(
                                fontSize: 11, color: IpColors.textMuted)),
                      ])),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                      onPressed: saving ? null : save,
                      icon: const Icon(Icons.save_outlined),
                      label:
                          Text(saving ? 'Working...' : 'Save configuration')),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                      onPressed: saving ? null : test,
                      icon: const Icon(Icons.network_check),
                      label: const Text('Test saved text provider')),
                  const SizedBox(height: 12),
                  Text('Backend: ${widget.api.baseUrl}',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                          fontSize: 10, color: IpColors.textMuted)),
                ],
              ),
      );
}
