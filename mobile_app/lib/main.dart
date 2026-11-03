import 'package:flutter/material.dart';

import 'features/dashboard/battery_card.dart';
import 'features/dashboard/battery_status.dart';

void main() => runApp(const InspectPinApp());

class InspectPinApp extends StatelessWidget {
  const InspectPinApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'InspectPin',
        theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
        home: Scaffold(
          appBar: AppBar(title: const Text('InspectPin dashboard')),
          body: const BatteryCard(
            status: BatteryStatus(
              voltage: null,
              estimatedPercent: null,
              uncertaintyVolts: 0.08,
              valid: false,
              low: false,
              critical: false,
              chargeState: ChargeState.unknown,
              chargeValid: false,
              sampleAgeMs: 0,
            ),
          ),
        ),
      );
}

