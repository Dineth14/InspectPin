import 'dart:typed_data';
import 'package:flutter/services.dart';

Future<void> playEvidence(Uint8List bytes) => const MethodChannel('ai.inspectpin.mobile/evidence')
    .invokeMethod<void>('play', bytes);
Future<void> stopEvidence() => const MethodChannel('ai.inspectpin.mobile/evidence').invokeMethod<void>('stop');

Future<void> exportEvidence(Uint8List bytes, String filename, String mime) =>
    const MethodChannel('ai.inspectpin.mobile/evidence').invokeMethod<void>(
        'save', {'bytes': bytes, 'name': filename, 'mime': mime});
