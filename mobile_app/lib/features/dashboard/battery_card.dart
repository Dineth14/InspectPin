import 'package:flutter/material.dart';

import 'battery_status.dart';

class BatteryCard extends StatelessWidget {
  const BatteryCard({super.key, required this.status});

  final BatteryStatus status;

  @override
  Widget build(BuildContext context) {
    final voltage = status.valid && status.voltage != null
        ? '${status.voltage!.toStringAsFixed(2)} V ± ${status.uncertaintyVolts.toStringAsFixed(2)} V'
        : 'Voltage unavailable';
    final percent = status.valid && status.estimatedPercent != null
        ? '${status.estimatedPercent!.round()}% estimated'
        : 'State of charge unavailable';
    final warning = switch (status.warning) {
      BatteryWarning.critical => 'Critically low — finish work and recharge',
      BatteryWarning.low => 'Low battery — recharge soon',
      BatteryWarning.unavailable => 'Battery sensor not verified or disconnected',
      BatteryWarning.none => 'Battery estimate is within configured limits',
    };
    final charging = status.chargeValid
        ? switch (status.chargeState) {
            ChargeState.charging => 'USB charging',
            ChargeState.full => 'Charge complete',
            ChargeState.faultUnsupported => 'Charger fault detection unsupported',
            ChargeState.unknown => 'Charger state unknown',
          }
        : 'Charger state unknown (not inferred from voltage)';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Semantics(
          label: '$voltage, $percent, $warning, $charging',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Battery', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text(voltage),
              Text(percent),
              Text(warning),
              Text(charging),
              Text('Sample age: ${status.sampleAgeMs} ms'),
            ],
          ),
        ),
      ),
    );
  }
}

