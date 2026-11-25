import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:inspectpin_mobile/features/device/firmware_update_screen.dart';
import 'package:inspectpin_mobile/models/product_models.dart';
import 'package:inspectpin_mobile/services/api_client.dart';
import 'package:material_ui/material_ui.dart';

class _Receiver extends ApiClient {
  _Receiver()
      : super(
            baseUrl: 'http://127.0.0.1:5000',
            storage: const FlutterSecureStorage());
  String? submittedDigest;

  @override
  Future<Map<String, dynamic>> firmwareCatalog(String device) async => {
        'online': true,
        'installed': {'version': '1.1.1', 'build': 'base', 'ota_enabled': true},
        'packages': [
          {
            'version': '1.1.2',
            'size': 1200000,
            'notes': 'Rehearsal',
            'sha256': 'signed-image',
            'compatible': true
          },
        ],
        'update':
            submittedDigest == null ? null : {'state': 'queued', 'bytes': 0},
      };

  @override
  Future<void> installFirmware(String device, String digest) async {
    submittedDigest = digest;
  }
}

void main() {
  testWidgets(
      'OTA requires operator power confirmation and reports queued without claiming success',
      (tester) async {
    final api = _Receiver();
    final device = DeviceSummary.fromJson({'id': 'pin-test', 'online': true});
    await tester.pumpWidget(
        MaterialApp(home: FirmwareUpdateScreen(api: api, device: device)));
    await tester.pumpAndSettle();
    final install =
        find.widgetWithText(FilledButton, 'Install approved firmware');
    await tester.ensureVisible(install);
    expect(tester.widget<FilledButton>(install).onPressed, isNull);
    final confirmation = find.text('I confirmed stable external power');
    await tester.ensureVisible(confirmation);
    await tester.tap(confirmation);
    await tester.pumpAndSettle();
    await tester.ensureVisible(install);
    await tester.tap(install);
    await tester.pumpAndSettle();
    expect(api.submittedDigest, 'signed-image');
    expect(find.text('Last update · queued'), findsOneWidget);
    expect(find.text('Last update · confirmed'), findsNothing);
    await tester.pumpWidget(const SizedBox());
  });
}
