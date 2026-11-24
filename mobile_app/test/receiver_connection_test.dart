import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:inspectpin_mobile/services/api_client.dart';
import 'package:inspectpin_mobile/models/product_models.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('receiver changes discard legacy sessions and reject public plaintext',
      () async {
    FlutterSecureStorage.setMockInitialValues(
        {'inspectpin_access_token': 'old'});
    const storage = FlutterSecureStorage();
    final api = ApiClient(baseUrl: 'http://127.0.0.1:5000', storage: storage);
    expect(await api.initialize(), isFalse);
    expect(await storage.read(key: 'inspectpin_access_token'), isNull);
    await api.configureBaseUrl('http://172.20.10.4:5000/');
    expect(api.baseUrl, 'http://172.20.10.4:5000');
    await expectLater(api.configureBaseUrl('http://example.org'),
        throwsA(isA<ApiException>()));
    await api.configureBaseUrl('https://example.org');
    expect(await api.restore(), isFalse);
  });
  test('device registration and stale telemetry cannot establish a live state',
      () {
    DeviceSummary device(Map<String, dynamic> fields) =>
        DeviceSummary.fromJson({'id': 'pin', ...fields});
    expect(device({}).connectionLabel, contains('first heartbeat'));
    expect(
        device({'last_seen': 10, 'online': false, 'reported_state': 'SLEEP'})
            .connectionLabel,
        'Device not responding');
    expect(
        device({
          'last_seen': 10,
          'online': true,
          'reported_state': 'WAITING_FOR_AI'
        }).connectionLabel,
        contains('busy'));
  });
}
