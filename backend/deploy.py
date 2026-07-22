import os
import shutil
import zipfile
import subprocess


def main():
    print("Creating Lambda deployment package...")

    # Clean up
    if os.path.exists("lambda-package"):
        shutil.rmtree("lambda-package")
    if os.path.exists("lambda-deployment.zip"):
        os.remove("lambda-deployment.zip")

    # Create package directory
    os.makedirs("lambda-package")

    # Try to install dependencies using Docker, and fall back to local pip if Docker is not available
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{os.getcwd()}:/var/task",
                "--platform",
                "linux/amd64",  # Force x86_64 architecture
                "--entrypoint",
                "",  # Override the default entrypoint
                "public.ecr.aws/lambda/python:3.12",
                "/bin/sh",
                "-c",
                "pip install --target /var/task/lambda-package -r /var/task/requirements.txt --platform manylinux2014_x86_64 --only-binary=:all: --upgrade",
            ],
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("[WARNING] Docker is not running or not installed. Falling back to local pip installation...")
        # Use pip to download Linux-compatible packages for Lambda
        # We need to find a working pip - try conda's pip first, then system pip
        import sys
        pip_commands = [
            # Try conda base pip (known to work on this system)
            [os.path.join(os.environ.get("CONDA_PREFIX", ""), "python.exe"), "-m", "pip"],
            # Try system python
            ["python", "-m", "pip"],
            # Try pip directly
            ["pip"],
        ]
        installed = False
        for pip_cmd in pip_commands:
            try:
                subprocess.run(
                    pip_cmd + [
                        "install",
                        "--target",
                        "lambda-package",
                        "--platform",
                        "manylinux2014_x86_64",
                        "--only-binary=:all:",
                        "--implementation",
                        "cp",
                        "--python-version",
                        "3.12",
                        "-r",
                        "requirements.txt",
                        "--upgrade",
                    ],
                    check=True,
                )
                installed = True
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        if not installed:
            raise RuntimeError("Could not install packages. Please install Docker Desktop or ensure pip is available.")

    # Copy application files
    print("Copying application files...")
    for file in ["server.py", "lambda_handler.py", "context.py", "resources.py"]:
        if os.path.exists(file):
            shutil.copy2(file, "lambda-package/")
    
    # Copy data directory
    if os.path.exists("data"):
        shutil.copytree("data", "lambda-package/data")

    # Create zip
    print("Creating zip file...")
    with zipfile.ZipFile("lambda-deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("lambda-package"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "lambda-package")
                zipf.write(file_path, arcname)

    # Show package size
    size_mb = os.path.getsize("lambda-deployment.zip") / (1024 * 1024)
    print(f"Created lambda-deployment.zip ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()