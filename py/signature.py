import os
import sys
import subprocess
import argparse

try:
    from py.resource_utils import get_resource_path
except ImportError:
    def get_resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, relative_path)


def sign_apk(apk_path, keystore_path, alias, store_pass, key_pass):
    if not os.path.exists(apk_path):
        raise FileNotFoundError(f"APK 不存在: {apk_path}")
    if not os.path.exists(keystore_path):
        raise FileNotFoundError(f"Keystore 不存在: {keystore_path}")

    apksigner = get_resource_path(os.path.join(
        "resources",
        "android-sdk",
        "build-tools",
        "apksigner.bat"
    ))

    if not os.path.exists(apksigner):
        raise FileNotFoundError(f"找不到 apksigner: {apksigner}")

    cmd = [
        apksigner, "sign",
        "--ks", keystore_path,
        "--ks-key-alias", alias,
        "--ks-pass", f"pass:{store_pass}",
        "--key-pass", f"pass:{key_pass}",
        apk_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"apksigner 签名失败：\n{result.stderr}\n{result.stdout}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("apk")
    parser.add_argument("keystore")
    parser.add_argument("alias")
    parser.add_argument("storepass")
    parser.add_argument("keypass")

    args = parser.parse_args()

    try:
        sign_apk(args.apk, args.keystore, args.alias, args.storepass, args.keypass)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
