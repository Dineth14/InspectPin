enum BatteryWarning { none, low, critical, unavailable }

enum ChargeState { unknown, charging, full, battery, usbIdle, fault, faultUnsupported }

class BatteryStatus {
  const BatteryStatus({
    required this.voltage,
    required this.estimatedPercent,
    required this.uncertaintyVolts,
    required this.valid,
    required this.low,
    required this.critical,
    required this.chargeState,
    required this.chargeValid,
    required this.sampleAgeMs,
  });

  final double? voltage;
  final double? estimatedPercent;
  final double uncertaintyVolts;
  final bool valid;
  final bool low;
  final bool critical;
  final ChargeState chargeState;
  final bool chargeValid;
  final int sampleAgeMs;

  BatteryWarning get warning => !valid
      ? BatteryWarning.unavailable
      : critical
          ? BatteryWarning.critical
          : low
              ? BatteryWarning.low
              : BatteryWarning.none;

  factory BatteryStatus.fromJson(Map<String, Object?> json) {
    final charge = switch (json['charge_state']) {
      'charging' => ChargeState.charging,
      'full' => ChargeState.full,
      'battery' => ChargeState.battery,
      'usb_idle' => ChargeState.usbIdle,
      'fault' => ChargeState.fault,
      'fault_unsupported' => ChargeState.faultUnsupported,
      _ => ChargeState.unknown,
    };
    return BatteryStatus(
      voltage: ((json['voltage_v'] ?? json['battery_voltage']) as num?)?.toDouble(),
      estimatedPercent: ((json['estimated_percent'] ?? json['battery_percent']) as num?)?.toDouble(),
      uncertaintyVolts: (json['uncertainty_v'] as num?)?.toDouble() ?? 0,
      valid: json['valid'] == true || json['battery_percent'] is num,
      low: json['low'] == true,
      critical: json['critical'] == true,
      chargeState: charge,
      chargeValid: json['charge_valid'] == true || const {'charging', 'full', 'battery', 'usb_idle', 'fault'}.contains(json['charge_state']),
      sampleAgeMs: (json['sample_age_ms'] as num?)?.toInt() ?? 0,
    );
  }
}

