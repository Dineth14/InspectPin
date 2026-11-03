import 'package:flutter/material.dart';

abstract final class IpColors {
  static const background = Color(0xFF081525);
  static const backgroundDeep = Color(0xFF060E19);
  static const surface = Color(0xFF102036);
  static const surfaceRaised = Color(0xFF152A42);
  static const accent = Color(0xFF00DFE8);
  static const text = Color(0xFFF7FAFF);
  static const textSecondary = Color(0xFFB0C0D3);
  static const textMuted = Color(0xFF8196AE);
  static const border = Color(0xFF29415B);
  static const success = Color(0xFF35CBA3);
  static const warning = Color(0xFFF4B860);
  static const error = Color(0xFFF1717F);
}

abstract final class IpSpace {
  static const x1 = 4.0, x2 = 8.0, x3 = 12.0, x4 = 16.0, x5 = 24.0, x6 = 32.0, x7 = 48.0;
}

abstract final class InspectPinTheme {
  static ThemeData dark() => _theme(Brightness.dark);
  static ThemeData light() => _theme(Brightness.light);

  static ThemeData _theme(Brightness brightness) {
    final dark = brightness == Brightness.dark;
    final background = dark ? IpColors.background : const Color(0xFFEDF4F6);
    final surface = dark ? IpColors.surface : Colors.white;
    final text = dark ? IpColors.text : const Color(0xFF102433);
    final secondary = dark ? IpColors.textSecondary : const Color(0xFF455F70);
    final border = dark ? IpColors.border : const Color(0xFFC8D8DF);
    final scheme = ColorScheme.fromSeed(seedColor: IpColors.accent, brightness: brightness,
      surface: surface, error: IpColors.error);
    return ThemeData(
      brightness: brightness, colorScheme: scheme, scaffoldBackgroundColor: background,
      useMaterial3: true,
      textTheme: TextTheme(
        displayLarge: TextStyle(fontSize: 44, height: .98, fontWeight: FontWeight.w800, letterSpacing: -2.4, color: text),
        headlineLarge: TextStyle(fontSize: 32, height: 1.04, fontWeight: FontWeight.w800, letterSpacing: -1.2, color: text),
        headlineSmall: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, letterSpacing: -.7, color: text),
        titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: text),
        titleMedium: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: text),
        bodyLarge: TextStyle(fontSize: 15, height: 1.55, color: secondary),
        bodyMedium: TextStyle(fontSize: 13, height: 1.5, color: secondary),
        labelLarge: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: text),
        labelSmall: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1.4, color: secondary),
      ),
      cardTheme: CardThemeData(color: surface, elevation: 0, margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(side: BorderSide(color: border), borderRadius: BorderRadius.circular(16))),
      dividerTheme: DividerThemeData(color: border),
      navigationBarTheme: NavigationBarThemeData(height: 72, backgroundColor: dark ? IpColors.backgroundDeep : Colors.white,
        indicatorColor: IpColors.accent.withValues(alpha: .12), labelTextStyle: WidgetStateProperty.resolveWith((states) => TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: states.contains(WidgetState.selected) ? IpColors.accent : secondary))),
      inputDecorationTheme: InputDecorationTheme(filled: true, fillColor: dark ? IpColors.backgroundDeep : const Color(0xFFF6FAFB),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15), border: OutlineInputBorder(borderSide: BorderSide(color: border), borderRadius: BorderRadius.circular(10)),
        enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: border), borderRadius: BorderRadius.circular(10)),
        focusedBorder: OutlineInputBorder(borderSide: const BorderSide(color: IpColors.accent, width: 1.5), borderRadius: BorderRadius.circular(10))),
      filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(backgroundColor: IpColors.accent, foregroundColor: const Color(0xFF03212A), minimumSize: const Size(48, 48), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)), textStyle: const TextStyle(fontWeight: FontWeight.w800))),
      outlinedButtonTheme: OutlinedButtonThemeData(style: OutlinedButton.styleFrom(minimumSize: const Size(48, 48), side: BorderSide(color: border), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)), textStyle: const TextStyle(fontWeight: FontWeight.w700))),
      appBarTheme: AppBarTheme(backgroundColor: background, surfaceTintColor: Colors.transparent, elevation: 0, centerTitle: false, titleTextStyle: TextStyle(color: text, fontSize: 18, fontWeight: FontWeight.w800)),
    );
  }
}
