import hashlib
import json
import re
import shutil
from pathlib import Path


class Storage:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def directory(self, job_id):
        if not re.fullmatch(r"[0-9a-f]{32}", job_id):
            raise ValueError("Invalid job ID")
        path = self.root / job_id
        if path.is_symlink() or path.resolve().parent != self.root:
            raise ValueError("Unsafe storage directory")
        return path

    def save_input(self, job_id, kind, data):
        folder = self.directory(job_id)
        folder.mkdir(exist_ok=False)
        path = folder / ("input.wav" if kind == "voice" else "input.jpg")
        path.write_bytes(data)
        return path, hashlib.sha256(data).hexdigest()

    def journal(self, job):
        path = self.directory(job["id"])
        temp = path / "job.json.tmp"
        temp.write_text(json.dumps(job, indent=2), encoding="utf-8")
        temp.replace(path / "job.json")

    def remove(self, job_id):
        path = self.directory(job_id)
        if path.exists():
            shutil.rmtree(path)
