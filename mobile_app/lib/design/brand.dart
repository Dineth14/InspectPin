import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'app_theme.dart';

class InspectPinWordmark extends StatelessWidget {
  const InspectPinWordmark({super.key, this.compact = false});
  final bool compact;
  @override
  Widget build(BuildContext context) => Semantics(label: 'InspectPin AI', child: ExcludeSemantics(child: Stack(clipBehavior: Clip.none, children: [
    Text.rich(TextSpan(children: [
      const TextSpan(text: 'Inspect'), const TextSpan(text: 'Pin', style: TextStyle(color: IpColors.accent)),
      TextSpan(text: '  AI', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
    ]), style: TextStyle(fontSize: compact ? 20 : 31, height: 1, fontWeight: FontWeight.w900, letterSpacing: compact ? -1.25 : -2)),
    Positioned(left: 1, bottom: compact ? -7 : -10, child: Container(width: compact ? 32 : 48, height: 3, decoration: BoxDecoration(color: IpColors.accent, borderRadius: BorderRadius.circular(3)))),
  ])));
}

class InspectPinMark extends StatelessWidget {
  const InspectPinMark({super.key, this.size = 44}); final double size;
  @override
  Widget build(BuildContext context) => Semantics(label: 'InspectPin AI', child: Container(width: size, height: size,
    decoration: BoxDecoration(color: IpColors.surface, border: Border.all(color: IpColors.border), borderRadius: BorderRadius.circular(size * .24)),
    child: CustomPaint(painter: _MarkPainter()),
  ));
}

class DeviceConcept extends StatelessWidget {
  const DeviceConcept({super.key, this.height = 210}); final double height;
  @override
  Widget build(BuildContext context) => Semantics(label: 'Conceptual InspectPin wearable device illustration', child: SizedBox(height: height, child: CustomPaint(painter: _DevicePainter())));
}

class _MarkPainter extends CustomPainter {
  @override void paint(Canvas canvas, Size size) {
    final white = Paint()..color = IpColors.text, cyan = Paint()..color = IpColors.accent;
    canvas.drawRect(Rect.fromLTWH(size.width*.22, size.height*.25, size.width*.12, size.height*.48), white);
    canvas.drawRect(Rect.fromLTWH(size.width*.44, size.height*.25, size.width*.13, size.height*.48), cyan);
    canvas.drawArc(Rect.fromLTWH(size.width*.48, size.height*.25, size.width*.28, size.height*.27), -math.pi/2, math.pi*1.5, true, cyan);
    canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(size.width*.22, size.height*.79, size.width*.23, size.height*.045), const Radius.circular(3)), cyan);
  }
  @override bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _DevicePainter extends CustomPainter {
  @override void paint(Canvas canvas, Size size) {
    final scale = math.min(size.width / 320, size.height / 210), w = 176*scale, h = 200*scale;
    final left = (size.width-w)/2, top=(size.height-h)/2;
    final body = RRect.fromRectAndRadius(Rect.fromLTWH(left,top,w,h), Radius.circular(28*scale));
    canvas.drawShadow(Path()..addRRect(body), Colors.black, 16, false); canvas.drawRRect(body, Paint()..color=IpColors.surfaceRaised);
    canvas.drawRRect(body, Paint()..style=PaintingStyle.stroke..strokeWidth=1.5..color=IpColors.border);
    final lens=Offset(size.width/2,top+52*scale); canvas.drawCircle(lens,31*scale,Paint()..color=IpColors.backgroundDeep); canvas.drawCircle(lens,20*scale,Paint()..style=PaintingStyle.stroke..strokeWidth=3..color=IpColors.accent); canvas.drawCircle(lens,8*scale,Paint()..color=const Color(0xFF06121D));
    final panel=RRect.fromRectAndRadius(Rect.fromLTWH(left+22*scale,top+99*scale,w-44*scale,34*scale),Radius.circular(10*scale)); canvas.drawRRect(panel,Paint()..color=IpColors.backgroundDeep);
    canvas.drawCircle(Offset(left+w-42*scale,top+116*scale),4*scale,Paint()..color=IpColors.accent);
    for(final x in [left+25*scale,left+94*scale]) { canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(x,top+153*scale,57*scale,25*scale),Radius.circular(8*scale)),Paint()..color=x<left+60*scale?IpColors.surface:IpColors.accent); }
  }
  @override bool shouldRepaint(covariant CustomPainter oldDelegate)=>false;
}
