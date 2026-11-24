import 'dart:async';
import 'dart:js_interop';
import 'dart:typed_data';
import 'package:web/web.dart' as web;

web.HTMLAudioElement? _player;
String? _audioUrl;
Future<void> stopEvidence() async {
  _player?.pause();
  _player = null;
  if (_audioUrl != null) web.URL.revokeObjectURL(_audioUrl!);
  _audioUrl = null;
}

Future<void> playEvidence(Uint8List bytes) async {
  await stopEvidence();
  _audioUrl = web.URL.createObjectURL(web.Blob([bytes.toJS].toJS, web.BlobPropertyBag(type: 'audio/wav')));
  _player = web.HTMLAudioElement()..src = _audioUrl!;
  await _player!.play().toDart;
}

Future<void> exportEvidence(Uint8List bytes, String filename, String mime) async {
  final blob = web.Blob([bytes.toJS].toJS, web.BlobPropertyBag(type: mime));
  final url = web.URL.createObjectURL(blob);
  web.HTMLAnchorElement()
    ..href = url
    ..download = filename
    ..click();
  Timer(const Duration(seconds: 30), () => web.URL.revokeObjectURL(url));
}
