import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../models/product_models.dart';

class ApiException implements Exception {
  const ApiException(this.code, this.message, this.status);
  final String code, message;
  final int status;
  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({required this.baseUrl, required this.storage});
  String baseUrl;
  final FlutterSecureStorage storage;
  String? _token;

  Future<bool> initialize() async {
    final saved = await storage.read(key: 'inspectpin_api_url');
    if (saved != null && saved.isNotEmpty) baseUrl = saved;
    return restore();
  }

  Future<void> configureBaseUrl(String value) async {
    final normalized = value.trim().replaceFirst(RegExp(r'/+$'), '');
    final uri = Uri.tryParse(normalized);
    if (uri == null ||
        !uri.hasAuthority ||
        (uri.scheme != 'https' && uri.scheme != 'http')) {
      throw const ApiException(
          'INVALID_SERVER_URL', 'Enter a valid HTTP or HTTPS backend URL', 0);
    }
    if (uri.userInfo.isNotEmpty ||
        uri.path.isNotEmpty ||
        uri.hasQuery ||
        uri.hasFragment) {
      throw const ApiException('INVALID_SERVER_URL',
          'Use only the backend origin, without credentials or a path', 0);
    }
    if (uri.scheme == 'http' && !_privateHost(uri.host)) {
      throw const ApiException(
          'HTTPS_REQUIRED', 'Remote backends must use HTTPS', 0);
    }
    baseUrl = normalized;
    await storage.write(key: 'inspectpin_api_url', value: normalized);
  }

  static bool _privateHost(String host) {
    if (host == 'localhost' || host == '127.0.0.1' || host == '10.0.2.2') {
      return true;
    }
    final parts = host.split('.').map(int.tryParse).toList();
    if (parts.length != 4 || parts.any((part) => part == null)) return false;
    final first = parts[0]!, second = parts[1]!;
    return first == 10 ||
        first == 127 ||
        (first == 192 && second == 168) ||
        (first == 172 && second >= 16 && second <= 31);
  }

  Future<bool> restore() async {
    _token = await storage.read(key: 'inspectpin_access_token');
    if (_token == null) return false;
    try {
      await _json('GET', '/api/v1/auth/me');
      return true;
    } on ApiException catch (error) {
      if (error.status == 401) await signOut();
      return false;
    }
  }

  Future<void> authenticate(
      {required String email, required String password, String? name}) async {
    final endpoint = name == null ? 'login' : 'register';
    final result = await _json('POST', '/api/v1/auth/$endpoint', body: {
      'email': email,
      'password': password,
      if (name != null) 'name': name,
    });
    _token = result['access_token'] as String;
    await storage.write(key: 'inspectpin_access_token', value: _token);
  }

  Future<void> signOut() async {
    try {
      if (_token != null) await _json('POST', '/api/v1/auth/logout');
    } catch (_) {/* local sign-out still proceeds */}
    _token = null;
    await storage.delete(key: 'inspectpin_access_token');
  }

  Future<DashboardData> dashboard() async {
    final results = await Future.wait([
      _json('GET', '/api/v1/devices'),
      _json('GET', '/api/v1/inspections?limit=50'),
    ]);
    final devices = (results[0]['items'] as List)
        .whereType<Map<String, dynamic>>()
        .map(DeviceSummary.fromJson)
        .toList();
    final inspections = (results[1]['items'] as List)
        .whereType<Map<String, dynamic>>()
        .map(InspectionSummary.fromJson)
        .toList();
    return DashboardData(devices, inspections);
  }

  Future<InspectionSummary> inspection(String id) async =>
      InspectionSummary.fromJson(await _json('GET', '/api/v1/inspections/$id'));

  Future<void> requestPhoto(String id) async {
    await sendDeviceCommand(id, 'capture_photo');
  }

  Future<Map<String, dynamic>> sendDeviceCommand(String id, String type,
          {Map<String, dynamic> payload = const {}}) async =>
      _json('POST', '/api/v1/devices/$id/commands', body: {
        'type': type,
        'payload': payload,
        'ttl_seconds': 120,
      });

  Future<Map<String, dynamic>> commandStatus(String id) async =>
      _json('GET', '/api/v1/commands/$id');

  Future<AiConfiguration> aiConfiguration() async =>
      AiConfiguration.fromJson(await _json('GET', '/api/v1/settings/ai'));

  Future<AiConfiguration> updateAiConfiguration(
          Map<String, dynamic> value) async =>
      AiConfiguration.fromJson(
          await _json('PATCH', '/api/v1/settings/ai', body: value));

  Future<Map<String, dynamic>> testAiConfiguration() async =>
      _json('POST', '/api/v1/settings/ai/test', body: const {});

  Future<Map<String, dynamic>> askInspection(
          String id, String question) async =>
      _json('POST', '/api/v1/inspections/$id/questions',
          body: {'question': question});

  Future<Map<String, dynamic>> processingJob(String id) async =>
      _json('GET', '/api/v1/processing-jobs/$id');

  Future<Uint8List> media(String id) async {
    final response =
        await http.get(Uri.parse('$baseUrl/api/v1/media/$id'), headers: {
      'Accept': 'image/jpeg',
      if (_token != null) 'Authorization': 'Bearer $_token',
    }).timeout(const Duration(seconds: 20));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException('MEDIA_FAILED', 'Inspection image is unavailable',
          response.statusCode);
    }
    return response.bodyBytes;
  }

  Future<String> pair({
    required String id,
    required String name,
    required String model,
    required String hardwareRevision,
    required String firmwareVersion,
  }) async {
    final result = await _json('POST', '/api/v1/devices/pair', body: {
      'device_id': id,
      'name': name,
      'model': model,
      'hardware_revision': hardwareRevision,
      'firmware_version': firmwareVersion,
    });
    return result['device_token'] as String;
  }

  Future<Map<String, dynamic>> _json(String method, String path,
      {Map<String, dynamic>? body}) async {
    final headers = <String, String>{'Accept': 'application/json'};
    if (_token != null) headers['Authorization'] = 'Bearer $_token';
    if (body != null) headers['Content-Type'] = 'application/json';
    final uri = Uri.parse('$baseUrl$path');
    final response = switch (method) {
      'GET' => await http
          .get(uri, headers: headers)
          .timeout(const Duration(seconds: 15)),
      'POST' => await http
          .post(uri,
              headers: headers, body: body == null ? null : jsonEncode(body))
          .timeout(const Duration(seconds: 65)),
      'PATCH' => await http
          .patch(uri, headers: headers, body: jsonEncode(body ?? const {}))
          .timeout(const Duration(seconds: 20)),
      _ => throw ArgumentError('Unsupported HTTP method'),
    };
    Map<String, dynamic> value = {};
    if (response.body.isNotEmpty) {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) value = decoded;
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final error = value['error'] is Map ? value['error'] as Map : const {};
      throw ApiException(
          error['code']?.toString() ?? 'HTTP_ERROR',
          error['message']?.toString() ?? 'Request failed',
          response.statusCode);
    }
    return value;
  }
}
