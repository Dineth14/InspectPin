"""Independent real-model check: python -m scripts.vision_check JPEG QUESTION."""
import argparse
import json
import time
from pathlib import Path

from inspectpin.config import Settings
from inspectpin.errors import ServiceError
from inspectpin.vision import Vision


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("image", type=Path)
    p.add_argument("question")
    p.add_argument("--follow-up", action="append", default=[])
    p.add_argument("--url", default="http://127.0.0.1:11434")
    p.add_argument("--model", default="qwen2.5vl:3b")
    p.add_argument("--timeout", type=float, default=120)
    args = p.parse_args()
    settings = Settings(vision_provider="ollama", vision_model=args.model, ollama_url=args.url,
                        request_timeout=args.timeout)
    settings.validate()
    if args.image.stat().st_size > settings.vision_max_image_bytes:
        raise SystemExit("JPEG exceeds VISION_MAX_IMAGE_BYTES")
    image = args.image.read_bytes()
    provider, history = Vision(settings), []
    for question in [args.question, *args.follow_up]:
        started = time.monotonic()
        try:
            answer = provider.answer(image, question, history)
        except ServiceError as exc:
            print(json.dumps({"error": exc.as_dict(), "seconds": round(time.monotonic()-started, 3)}))
            raise SystemExit(1) from None
        print(json.dumps({"model": args.model, "question": question, "answer": answer,
                          "seconds": round(time.monotonic()-started, 3), "image_bytes": len(image)}, indent=2))
        history.extend([{"role": "user", "content": question}, {"role": "assistant", "content": answer}])
        history = history[-12:]


if __name__ == "__main__":
    main()
