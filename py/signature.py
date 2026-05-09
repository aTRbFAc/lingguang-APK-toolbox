import os
import sys
import subprocess
import shutil
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

    apksigner_jar = get_resource_path(os.path.join(
        "resources",
        "android-sdk",
        "build-tools",
        "lib",
        "apksigner.jar"
    ))

    bundled_java = get_resource_path(os.path.join("resources", "jre", "bin", "java.exe"))

    if not os.path.exists(apksigner_jar):
        raise FileNotFoundError(f"找不到捆绑的 apksigner.jar: {apksigner_jar}")
    if not os.path.exists(bundled_java):
        raise FileNotFoundError(f"找不到捆绑的 java 可执行文件: {bundled_java}")

    # 显示apksigner版本信息
    try:
        version_cmd = [bundled_java, "-jar", apksigner_jar, "--version"]
        version_result = subprocess.run(version_cmd, capture_output=True, text=True)
        print(f"apksigner版本: {version_result.stdout.strip()}")
    except Exception as e:
        print(f"无法获取apksigner版本: {e}")

    # 在签名之前执行 zipalign
    try:
        zipalign_candidates = [
            get_resource_path(os.path.join("resources", "android-sdk", "build-tools", "zipalign.exe")),
        ]
        zipalign_path = None
        for p in zipalign_candidates:
            if p and os.path.exists(p):
                zipalign_path = p
                break

        if zipalign_path:
            aligned_apk = apk_path + ".aligned.apk"
            za_cmd = [zipalign_path, "-v", "4", apk_path, aligned_apk]
            za = subprocess.run(za_cmd, capture_output=True, text=True)
            if za.returncode == 0:
                try:
                    os.replace(aligned_apk, apk_path)
                    print("zipalign 成功完成")
                except Exception:
                    shutil.copy2(aligned_apk, apk_path)
                    try:
                        os.remove(aligned_apk)
                    except Exception:
                        pass
            else:
                print(f"zipalign 失败，命令: {' '.join(za_cmd)}\nSTDOUT:\n{za.stdout}\nSTDERR:\n{za.stderr}")

    except Exception as e:
        print(f"尝试 zipalign 时出现异常: {e}")

    signed_apk = apk_path + ".signed.apk"

    java_exec = bundled_java
    cmd = [
        java_exec, "-jar", apksigner_jar, "sign",
        "--ks", keystore_path,
        "--ks-key-alias", alias,
        "--ks-pass", f"pass:{store_pass}",
        "--key-pass", f"pass:{key_pass}",
        "--v1-signing-enabled", "true",
        "--v2-signing-enabled", "true",
        "--v3-signing-enabled", "true",
        # "--v4-signing-enabled", "true", V4签名目前正在测试计划中……
        "--min-sdk-version", "21",  # 强制最低API级别
        "--max-sdk-version", "37",  # 设置最高API级别
        "--out", signed_apk,
        apk_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"apksigner 签名失败：\nCMD: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    # 验证签名
    verify_cmd = [
        java_exec, "-jar", apksigner_jar, "verify",
        "--verbose",
        signed_apk
    ]

    verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
    if verify_result.returncode != 0:
        print(f"警告：签名验证失败，但签名过程成功完成\n验证输出：\n{verify_result.stdout}\n{verify_result.stderr}")
    else:
        print(f"签名验证成功：\n{verify_result.stdout}")

    # 替换原始 APK 为签名后的 APK
    try:
        os.replace(signed_apk, apk_path)
    except Exception:
        # 尝试复制作为后备
        shutil.copy2(signed_apk, apk_path)
        try:
            os.remove(signed_apk)
        except Exception:
            pass


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