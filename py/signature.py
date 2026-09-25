import os
import sys
import subprocess
import shutil
import argparse

try:
    from py.resource_utils import get_local_tool_path, get_resource_path
except ImportError:
    def get_resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, relative_path)

    def get_local_tool_path(tool_name, environment_variable=None, android_sdk=False):
        raise ImportError("无法导入本地工具路径解析模块")


def sign_apk(apk_path, keystore_path, alias, store_pass, key_pass):
    if not os.path.exists(apk_path):
        raise FileNotFoundError(f"APK 不存在: {apk_path}")
    if not os.path.exists(keystore_path):
        raise FileNotFoundError(f"Keystore 不存在: {keystore_path}")

    # 使用本机 Java、Android SDK Build-Tools 中的 apksigner/zipalign。
    local_java = get_local_tool_path("java", "JAVA_HOME")
    apksigner_path = get_local_tool_path(
        "apksigner", "APKSIGNER_PATH", android_sdk=True
    )
    zipalign_path = get_local_tool_path(
        "zipalign", "ZIPALIGN_PATH", android_sdk=True
    )

    if not local_java:
        raise FileNotFoundError(
            "未找到本地 Java。请安装 JDK，并设置 JAVA_HOME 或将 java 加入 PATH。"
        )
    if not apksigner_path:
        raise FileNotFoundError(
            "未找到 apksigner。请安装 Android SDK Build-Tools，并设置 "
            "ANDROID_SDK_ROOT/ANDROID_HOME 或将 apksigner 加入 PATH。"
        )

    apksigner_command = [apksigner_path]
    if apksigner_path.lower().endswith(".jar"):
        apksigner_command = [local_java, "-jar", apksigner_path]

    # 显示apksigner版本信息
    try:
        version_cmd = apksigner_command + ["--version"]
        version_result = subprocess.run(version_cmd, capture_output=True, text=True)
        print(f"apksigner版本: {version_result.stdout.strip()}")
    except Exception as e:
        print(f"无法获取apksigner版本: {e}")

    # 在签名之前执行 zipalign
    try:
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

    cmd = apksigner_command + [
        "sign",
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
    verify_cmd = apksigner_command + [
        "verify",
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