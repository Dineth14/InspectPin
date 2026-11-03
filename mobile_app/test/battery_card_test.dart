import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:inspectpin_mobile/features/dashboard/battery_card.dart';
import 'package:inspectpin_mobile/features/dashboard/battery_status.dart';

void main() {
  testWidgets('shows voltage percentage warning and truthful charge validity', (tester) async {
    const status = BatteryStatus(
      voltage: 3.38,
      estimatedPercent: 7,
      uncertaintyVolts: 0.08,
      valid: true,
      low: true,
      critical: false,
      chargeState: ChargeState.unknown,
      chargeValid: false,
      sampleAgeMs: 20,
    );
    await tester.pumpWidget(const MaterialApp(home: BatteryCard(status: status)));
    expect(find.textContaining('3.38 V'), findsOneWidget);
    expect(find.text('7% estimated'), findsOneWidget);
    expect(find.textContaining('Low battery'), findsOneWidget);
    expect(find.textContaining('not inferred from voltage'), findsOneWidget);
  });
}

