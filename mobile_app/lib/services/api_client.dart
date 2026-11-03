import 'dart:convert';

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
  final String baseUrl;
  final FlutterSecureStorage storage;
  String? _token;

  Future<bool> restore() async {
    _token = await storage.read(key: 'inspectpin_access_token');
    if (_token == null) return false;
    try { await _json('GET', '/api/v1/auth/me'); return true; }
    on ApiException catch (error) {
      if (error.status == 401) await signOut();
      return false;
    }
  }

  Future<void> authenticate({required String email, required String password, String? name}) async {
    final endpoint = name == null ? 'login' : 'register';
    final result = await _json('POST', '/api/v1/auth/$endpoint', body: {
      'email': email, 'password': password, if (name != null) 'name': name,
    });
    _token = result['access_token'] as String;
    await storage.write(key: 'inspectpin_access_token', value: _token);
  }

  Future<void> signOut() async {
    try { if (_token != null) await _json('POST', '/api/v1/auth/logout'); } catch (_) { /* local sign-out still proceeds */ }
    _token = null;
    await storage.delete(key: 'inspectpin_access_token');
  }

  Future<DashboardData> dashboard() async {
    final results = await Future.wait([
      _json('GET', '/api/v1/devices'),
      _json('GET', '/api/v1/inspections?limit=50'),
    ]);
    final devices = (results[0]['items'] as List).whereType<Map<String, dynamic>>().map(DeviceSummary.fromJson).toList();
    final inspections = (results[1]['items'] as List).whereType<Map<String, dynamic>>().map(InspectionSummary.fromJson).toList();
    return DashboardData(devices, inspections);
  }

  Future<InspectionSummary> inspection(String id) async =>
      InspectionSummary.fromJson(await _json('GET', '/api/v1/inspections/$id'));

  Future<void> requestPhoto(String id) async {
    await _json('POST', '/api/v1/devices/$id/commands', body: {'type': 'capture_photo', 'payload': {}});
  }

  Future<Map<String, dynamic>> askInspection(String id, String question) async =>
      _json('POST', '/api/v1/inspections/$id/questions', body: {'question': question});

  Future<Map<String, dynamic>> processingJob(String id) async =>
      _json('GET', '/api/v1/processing-jobs/$id');

  Future<String> pair({
    required String id, required String name, required String model,
    required String hardwareRevision, required String firmwareVersion,
  }) async {
    final result = await _json('POST', '/api/v1/devices/pair', body: {
      'device_id': id, 'name': name, 'model': model,
      'hardware_revision': hardwareRevision, 'firmware_version': firmwareVersion,
    });
    return result['device_token'] as String;
  }

  Future<Map<String, dynamic>> _json(String method, String path, {Map<String, dynamic>? body}) async {
    final headers = <String, String>{'Accept': 'application/json'};
    if (_token != null) headers['Authorization'] = 'Bearer $_token';
    if (body != null) headers['Content-Type'] = 'application/json';
    final uri = Uri.parse('$baseUrl$path');
    final response = switch (method) {
      'GET' => await http.get(uri, headers: headers).timeout(const Duration(seconds: 15)),
      'POST' => await http.post(uri, headers: headers, body: body == null ? null : jsonEncode(body)).timeout(const Duration(seconds: 15)),
      _ => throw ArgumentError('Unsupported HTTP method'),
    };
    Map<String, dynamic> value = {};
    if (response.body.isNotEmpty) {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) value = decoded;
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final error = value['error'] is Map ? value['error'] as Map : const {};
      throw ApiException(error['code']?.toString() ?? 'HTTP_ERROR', error['message']?.toString() ?? 'Request failed', response.statusCode);
    }
    return value;
  }
}
