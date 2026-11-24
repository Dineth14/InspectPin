"""Bundle only the hosted receiver sources and compiled Flutter web client."""
import tarfile
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    backend = root / "backend"
    web = root / "mobile_app/build/web"
    if not (web / "main.dart.js").is_file() or not (web / "index.html").is_file():
        raise SystemExit("Build mobile_app for web before packaging")
    inputs = [
        *[backend / name for name in ("Dockerfile.hosted", ".dockerignore", "requirements.txt",
                                       "requirements-ai.txt", "receiver.py", "scripts/check_free_catalog.py",
                                       "scripts/download_models.py")],
        *sorted((backend / "inspectpin").glob("*.py")),
        *[root / "deploy/evaluation" / name for name in ("compose.yaml", "Caddyfile", ".env.example", "check_speech.py")],
        root / "docs/ZERO_COST_CLOUD.md",
    ]
    bundle = root / ".build/inspectpin-zero-cost.tar.gz"
    bundle.parent.mkdir(exist_ok=True)
    with tarfile.open(bundle, "w:gz") as archive:
        for path in inputs:
            archive.add(path, arcname=path.relative_to(root), recursive=False)
        for path in sorted(web.rglob("*")):
            if path.is_file() and not path.is_symlink() and not path.name.startswith(".") and path.suffix not in {".map", ".symbols"}:
                archive.add(path, arcname=Path("deploy/evaluation/dashboard") / path.relative_to(web))
    print(f"{bundle} ({bundle.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
