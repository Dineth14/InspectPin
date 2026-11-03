import 'package:flutter_test/flutter_test.dart';
import 'package:inspectpin_mobile/features/dashboard/battery_status.dart';

void main() {
  test('parses calibrated battery estimate and critical warning', () {
    final status = BatteryStatus.fromJson({
      'voltage_v': 3.24,
      'estimated_percent': 2.0,
      'uncertainty_v': 0.08,
      'valid': true,
      'low': true,
      'critical': true,
      'charge_state': 'unknown',
      'charge_valid': false,
      'sample_age_ms': 500,
    });
    expect(status.warning, BatteryWarning.critical);
    expect(status.chargeState, ChargeState.unknown);
    expect(status.chargeValid, isFalse);
  });

  test('never converts an invalid voltage into a charging state', () {
    final status = BatteryStatus.fromJson({
      'voltage_v': 4.2,
      'estimated_percent': 100,
      'valid': true,
      'charge_state': 'full',
      'charge_valid': false,
    });
    expect(status.estimatedPercent, 100);
    expect(status.chargeValid, isFalse);
  });
}

