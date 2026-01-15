#!/usr/bin/env python3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DOCKERFILE = Path(__file__).parent / "Dockerfile.agent-overlay"
IMAGE_LIST_LITE = Path(__file__).parent / "image_list.txt"
IMAGE_LIST_VERIFIED = Path(__file__).parent / "image_list_verified.txt"
LOG_DIR = Path(__file__).parent / "build_logs"
MAX_WORKERS = 16

def build_one(base_image: str) -> tuple[str, bool, str]:
    """Pull base image and build agent overlay. Returns (image, success, msg)."""
    base_tag = f"{base_image}:latest"
    agent_tag = f"{base_image}-agent:latest"

    # Create log directory and file
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"{base_image.replace('/', '_').replace(':', '_')}.log"

    with open(log_file, "w", buffering=1) as log:
        log.write(f"Building {base_image}\n")
        log.write(f"Base tag: {base_tag}\n")
        log.write(f"Agent tag: {agent_tag}\n\n")
        log.flush()

        # Check if agent image already exists
        r = subprocess.run(["docker", "image", "inspect", agent_tag], capture_output=True, text=True)
        if r.returncode == 0:
            log.write("Image already exists, skipping\n")
            log.flush()
            return base_image, True, "skipped"

        # Pull
        log.write("=" * 60 + "\n")
        log.write("PULLING BASE IMAGE\n")
        log.write("=" * 60 + "\n")
        log.flush()
        r = subprocess.run(["docker", "pull", base_tag], capture_output=True, text=True)
        log.write(r.stdout)
        log.write(r.stderr)
        log.flush()
        if r.returncode != 0:
            log.write(f"\nPull failed with exit code {r.returncode}\n")
            log.flush()
            return base_image, False, f"pull failed (see {log_file.name})"

        # Build
        log.write("\n" + "=" * 60 + "\n")
        log.write("BUILDING AGENT IMAGE\n")
        log.write("=" * 60 + "\n")
        log.flush()
        r = subprocess.run([
            "docker", "build",
            "--network", "host",
            "--build-arg", f"BASE_IMAGE={base_tag}",
            "-t", agent_tag,
            "-f", str(DOCKERFILE),
            str(DOCKERFILE.parent)
        ], capture_output=True, text=True)
        log.write(r.stdout)
        log.write(r.stderr)
        log.flush()
        if r.returncode != 0:
            log.write(f"\nBuild failed with exit code {r.returncode}\n")
            log.flush()
            return base_image, False, f"build failed (see {log_file.name})"

        log.write("\n" + "=" * 60 + "\n")
        log.write("BUILD SUCCESSFUL\n")
        log.write("=" * 60 + "\n")
        log.flush()

    return base_image, True, "ok"

def main():
    dataset = "lite"
    if len(sys.argv) > 1:
        dataset = sys.argv[1].lower()

    if dataset == "verified":
        image_list = IMAGE_LIST_VERIFIED
    elif dataset == "lite":
        image_list = IMAGE_LIST_LITE
    else:
        print(f"Usage: {sys.argv[0]} [lite|verified]")
        print(f"Unknown dataset: {dataset}")
        sys.exit(1)

    if not image_list.exists():
        print(f"Error: Image list not found: {image_list}")
        sys.exit(1)

    images = [l.strip() for l in image_list.read_text().splitlines() if l.strip()]
    total = len(images)
    print(f"Building {total} images from {dataset} dataset with {MAX_WORKERS} workers...")

    success, failed = 0, []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(build_one, img): img for img in images}
        for i, f in enumerate(as_completed(futures), 1):
            img, ok, msg = f.result()
            short = img.split(".")[-1]
            if ok:
                success += 1
                print(f"[{i}/{total}] ✓ {short}")
            else:
                failed.append((img, msg))
                print(f"[{i}/{total}] ✗ {short}: {msg}")

    print(f"\nDone: {success}/{total} succeeded")
    if failed:
        print(f"Failed ({len(failed)}):")
        for img, msg in failed[:10]:
            print(f"  {img}: {msg}")

if __name__ == "__main__":
    main()
