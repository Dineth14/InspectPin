{{flutter_js}}
{{flutter_build_config}}

const release = {{flutter_service_worker_version}};
for (const build of _flutter.buildConfig.builds) {
  if (release && build.mainJsPath) {
    build.mainJsPath += '?release=' + encodeURIComponent(release);
  }
}
_flutter.loader.load({ serviceWorkerSettings: { serviceWorkerVersion: release } });
