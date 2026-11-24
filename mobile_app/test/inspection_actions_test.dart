import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:inspectpin_mobile/features/shell/home_shell.dart';
import 'package:inspectpin_mobile/models/product_models.dart';
import 'package:inspectpin_mobile/services/api_client.dart';

class _Receiver extends ApiClient {
  _Receiver()
      : super(
            baseUrl: 'http://127.0.0.1:5000',
            storage: const FlutterSecureStorage());
  String note = '';
  @override
  Future<InspectionSummary> inspection(String id) async =>
      InspectionSummary.fromJson(
          {'id': id, 'title': 'Test nameplate', 'created_at': 1, 'note': note});
  @override
  Future<DashboardData> dashboard() async =>
      DashboardData([], [await inspection('12345678')]);
  @override
  Future<InspectionSummary> saveNote(String id, String value) {
    note = value;
    return inspection(id);
  }
}

void main() {
  testWidgets('detail keeps note and PDF accessible from the context thread',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(360, 640));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final api = _Receiver();
    await tester.pumpWidget(MaterialApp(
        home: InspectionDetail(
            item: await api.inspection('12345678'),
            api: api,
            onUpdated: () async {})));
    await tester.drag(find.byType(ListView), const Offset(0, -1200));
    await tester.pumpAndSettle();
    expect(find.text('Ask InspectPin').hitTestable(), findsOneWidget);
    expect(find.text('Download PDF').hitTestable(), findsOneWidget);
    await tester.tap(find.text('Inspector note').hitTestable());
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).last, 'Label obscured');
    await tester.tap(find.text('Save note'));
    await tester.pumpAndSettle();
    expect(api.note, 'Label obscured');
    await tester.tap(find.text('Inspector note').hitTestable());
    await tester.pumpAndSettle();
    expect(find.text('Label obscured'), findsOneWidget);
  });

  testWidgets('inspection history exposes opening, notes and PDF on the row',
      (tester) async {
    final api = _Receiver();
    await tester.pumpWidget(MaterialApp(
        home: HomeShell(
            api: api,
            themeMode: ThemeMode.dark,
            onThemeChanged: (_) {},
            onSignedOut: () {})));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Inspections').last);
    await tester.pumpAndSettle();
    expect(find.text('Open inspection'), findsOneWidget);
    expect(find.text('Download PDF'), findsOneWidget);
    final action = find.text('Inspector note');
    await tester.ensureVisible(action);
    await tester.tap(action);
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).last, 'Rated 230 V');
    await tester.tap(find.text('Save note'));
    await tester.pumpAndSettle();
    expect(api.note, 'Rated 230 V');
    await tester.tap(action);
    await tester.pumpAndSettle();
    expect(find.text('Rated 230 V'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });
}
