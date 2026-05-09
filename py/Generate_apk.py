import os
import sys
import zipfile
import tempfile
import shutil
import re
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, simpledialog
import xml.etree.ElementTree as ET

from py.resource_utils import get_resource_path

ANDROID_NS = "http://schemas.android.com/apk/res/android"


# 单窗体输入 Keystore 别名和密码
class KeystoreDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        super().__init__(parent, title=title)

    def body(self, master):
        tk.Label(master, text="签名别名:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.alias_var = tk.StringVar()
        self.alias_entry = tk.Entry(master, textvariable=self.alias_var)
        self.alias_entry.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(master, text="Keystore 密码:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.storepass_var = tk.StringVar()
        self.storepass_entry = tk.Entry(master, textvariable=self.storepass_var, show='*')
        self.storepass_entry.grid(row=1, column=1, pady=5, padx=5)

        tk.Label(master, text="Key 密码:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.keypass_var = tk.StringVar()
        self.keypass_entry = tk.Entry(master, textvariable=self.keypass_var, show='*')
        self.keypass_entry.grid(row=2, column=1, pady=5, padx=5)

        return self.alias_entry

    def apply(self):
        self.result = (
            self.alias_var.get().strip(),
            self.storepass_var.get(),
            self.keypass_var.get()
        )


class APKGenerator:
    def __init__(self):
        self.apk_info = {
            'app_name': '', 'version_code': '', 'version_name': '',
            'package_name': '', 'icon_path': '',
            'orientation': 'portrait', 'fullscreen': False,
            'use_custom_keystore': False
        }

        self.jre_java = get_resource_path(
            os.path.join("resources", "jre", "bin", "java.exe")
        )
        self.apktool_jar = get_resource_path(
            os.path.join("resources", "apktool.jar")
        )

    def modify_androidmanifest_apktool(self, apk_path):
        decode_dir = None
        try:
            decode_dir = tempfile.mkdtemp(prefix="apktool_decode_")

            subprocess.run(
                [self.jre_java, "-jar", self.apktool_jar, "d", apk_path, "-o", decode_dir, "--force"],
                check=True, capture_output=True, text=True
            )

            manifest_path = os.path.join(decode_dir, "AndroidManifest.xml")
            tree = ET.parse(manifest_path)
            root = tree.getroot()

            root.set("package", self.apk_info["package_name"])
            root.set(f"{{{ANDROID_NS}}}versionCode", self.apk_info["version_code"])
            root.set(f"{{{ANDROID_NS}}}versionName", self.apk_info["version_name"])

            app = root.find("application")
            if app is not None:
                app.set(f"{{{ANDROID_NS}}}label", self.apk_info["app_name"])

            provider_authority = f"{self.apk_info['package_name']}.fileProvider"
            for provider in root.findall('.//provider'):
                auth = provider.get(f"{{{ANDROID_NS}}}authorities")
                if auth == "com.template.lingguang.fileProvider":
                    provider.set(f"{{{ANDROID_NS}}}authorities", provider_authority)

            try:
                launcher_activity = None
                for activity in root.findall('.//activity'):
                    for intent in activity.findall('intent-filter'):
                        has_main = any(a.get(f"{{{ANDROID_NS}}}name") == 'android.intent.action.MAIN' for a in intent.findall('action'))
                        has_launcher = any(c.get(f"{{{ANDROID_NS}}}name") == 'android.intent.category.LAUNCHER' for c in intent.findall('category'))
                        if has_main and has_launcher:
                            launcher_activity = activity
                            break
                    if launcher_activity is not None:
                        break

                orientation_val = self.apk_info.get('orientation', 'portrait')
                fullscreen_val = bool(self.apk_info.get('fullscreen', False))

                if launcher_activity is not None:
                    launcher_activity.set(f"{{{ANDROID_NS}}}screenOrientation", orientation_val)

                    if fullscreen_val:
                        launcher_activity.set(f"{{{ANDROID_NS}}}theme", "@android:style/Theme.NoTitleBar.Fullscreen")
                    else:
                        if f"{{{ANDROID_NS}}}theme" in launcher_activity.attrib:
                            del launcher_activity.attrib[f"{{{ANDROID_NS}}}theme"]
            except Exception:
                pass

            tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

            rebuilt_apk_path = apk_path.replace(".apk", "_rebuilt.apk")
            subprocess.run(
                [self.jre_java, "-jar", self.apktool_jar, "b", decode_dir, "-o", rebuilt_apk_path],
                check=True, capture_output=True, text=True
            )

            shutil.move(rebuilt_apk_path, apk_path)
            return True

        except Exception as e:
            raise RuntimeError(f"修改AndroidManifest失败: {str(e)}")

    def sign_apk_internal(self, unsigned_apk_path):
        try:
            if bool(self.apk_info.get('use_custom_keystore', False)):
                keystore_path = filedialog.askopenfilename(
                    title="选择签名证书",
                    filetypes=[("Keystore 文件", "*.jks;*.keystore;*.p12;*.pfx"), ("所有文件", "*")]
                )
                if not keystore_path:
                    raise RuntimeError("用户取消选择签名证书")
                
                dlg = KeystoreDialog(None, title="签名信息")
                if not getattr(dlg, 'result', None):
                    raise RuntimeError("用户取消输入签名信息")
                alias, store_pass, key_pass = dlg.result
                
                if not alias:
                    raise RuntimeError("未输入签名别名")
                if not store_pass:
                    raise RuntimeError("未输入Keystore密码")
                if not key_pass:
                    key_pass = store_pass
            else:
                keystore_path = get_resource_path(
                    os.path.join("key", "lingguang_apktool.jks")
                )
                alias = "lingguang_apktool"
                store_pass = "lingguang.apktool.atrbfac.key"
                key_pass = store_pass

            if not os.path.exists(keystore_path):
                raise FileNotFoundError(f"未找到签名证书: {keystore_path}")

            try:
                from py.signature import sign_apk
            except Exception as e:
                raise RuntimeError(f"导入签名模块失败: {e}")

            try:
                sign_apk(unsigned_apk_path, keystore_path, alias, store_pass, key_pass)
            except subprocess.CalledProcessError as e:
                error_msg = str(e)
                if "Keystore was tampered with" in error_msg or "Password verification failed" in error_msg:
                    raise RuntimeError("签名失败：请检查密钥库密码是否正确\n\n常见原因：\n1. 密码输入错误\n2. 密钥库已损坏\n3. 别名或密码不匹配")
                elif "alias does not exist" in error_msg.lower():
                    raise RuntimeError("签名失败：签名别名不存在")
                else:
                    raise RuntimeError(f"签名失败：{error_msg}")
            except Exception as e:
                raise RuntimeError(f"签名失败：{str(e)}")

            return keystore_path

        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"签名过程中发生错误：{str(e)}")

    def prepare_apk_files(self, extracted_path):
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="apk_build_")

            orientation = str(self.apk_info.get("orientation", "portrait"))
            fullscreen = bool(self.apk_info.get("fullscreen", False))

            if orientation == "portrait" and not fullscreen:
                template_name = "S.apk"
            elif orientation == "landscape" and not fullscreen:
                template_name = "H.apk"
            elif orientation == "portrait" and fullscreen:
                template_name = "SQ.apk"
            elif orientation == "landscape" and fullscreen:
                template_name = "HQ.apk"
            else:
                template_name = "S.apk"

            template_apk = get_resource_path(os.path.join("apk_template", template_name))

            if not os.path.exists(template_apk):
                raise FileNotFoundError(f"未找到模板 APK: {template_apk}")

            temp_apk_path = os.path.join(temp_dir, "temp.apk")
            shutil.copy2(template_apk, temp_apk_path)

            try:
                if not self.modify_androidmanifest_apktool(temp_apk_path):
                    raise RuntimeError("使用 apktool 修改模板 AndroidManifest 失败")
            except Exception as e:
                raise RuntimeError(f"修改模板 AndroidManifest 失败: {e}")

            extract_dir = os.path.join(temp_dir, "extract")
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(temp_apk_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            assets_webapp_dir = os.path.join(extract_dir, "assets", "webapp")
            os.makedirs(assets_webapp_dir, exist_ok=True)

            # 复制HTML文件
            shutil.copy2(extracted_path, os.path.join(assets_webapp_dir, "index.html"))

            # 检查并复制资源文件夹
            extracted_dir = os.path.dirname(extracted_path)
            resource_dir = os.path.join(extracted_dir, "index_files")

            if os.path.exists(resource_dir) and os.path.isdir(resource_dir):
                target_resource_dir = os.path.join(assets_webapp_dir, "index_files")
                
                # 确保目标文件夹存在
                os.makedirs(target_resource_dir, exist_ok=True)
                
                print(f"正在复制资源文件: {resource_dir} -> {target_resource_dir}")
                
                # 复制资源文件夹中的所有内容到目标文件夹
                for item in os.listdir(resource_dir):
                    source_path = os.path.join(resource_dir, item)
                    target_path = os.path.join(target_resource_dir, item)
                    
                    if os.path.isfile(source_path):
                        # 复制文件
                        shutil.copy2(source_path, target_path)
                        print(f"  复制文件: {item}")
                    elif os.path.isdir(source_path):
                        # 复制文件夹
                        if os.path.exists(target_path):
                            # 如果目标文件夹已存在，合并内容
                            for sub_item in os.listdir(source_path):
                                sub_source = os.path.join(source_path, sub_item)
                                sub_target = os.path.join(target_path, sub_item)
                                if os.path.isfile(sub_source):
                                    shutil.copy2(sub_source, sub_target)
                                else:
                                    shutil.copytree(sub_source, sub_target, dirs_exist_ok=True)
                        else:
                            # 如果目标文件夹不存在，直接复制
                            shutil.copytree(source_path, target_path)
                        print(f"  复制文件夹: {item}")
                
                print(f"资源复制完成，共处理了 {len(os.listdir(resource_dir))} 个项")
                
                # 打印调试信息
                print("目标资源文件夹内容:")
                for root, dirs, files in os.walk(target_resource_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, target_resource_dir)
                        rel_path = rel_path.replace('\\', '/')
                        print(f"  - {rel_path}")
            else:
                print(f"未找到资源文件夹: {resource_dir}")

            # 复制应用图标
            if self.apk_info.get("icon_path"):
                res_mipmap_dir = os.path.join(extract_dir, "res", "mipmap")
                os.makedirs(res_mipmap_dir, exist_ok=True)
                shutil.copy2(self.apk_info["icon_path"], os.path.join(res_mipmap_dir, "icon.png"))
            
            unsigned_apk_path = os.path.join(temp_dir, "unsigned.apk")
            with zipfile.ZipFile(unsigned_apk_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(extract_dir):
                    for f in files:
                        zipf.write(
                            os.path.join(root, f),
                            os.path.relpath(os.path.join(root, f), extract_dir)
                        )
        
            keystore_used_path = self.sign_apk_internal(unsigned_apk_path)
        
            safe_name = re.sub(r'[^\w\-_]', '_', self.apk_info['app_name'])
            safe_ver = re.sub(r'[^\w\-_.]', '_', self.apk_info['version_name'])
        
            output_apk_path = filedialog.asksaveasfilename(
                title="保存APK文件",
                defaultextension=".apk",
                initialfile=f"{safe_name}_{safe_ver}.apk",
                filetypes=[("APK文件", "*.apk")]
            )
        
            if not output_apk_path:
                return None, "用户取消"
        
            shutil.move(unsigned_apk_path, output_apk_path)
            return output_apk_path, keystore_used_path
        
        except Exception as e:
            raise
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def generate_apk_with_info(self, extracted_path):
        if not extracted_path or not os.path.exists(extracted_path):
            raise FileNotFoundError("未找到提取的 HTML 文件！")
        return self.prepare_apk_files(extracted_path)

    def show_apk_info_dialog(self, extracted_path):
        colors = {
            'primary': '#4361ee',
            'primary_light': '#e0e7ff',
            'secondary': '#6c757d',
            'success': '#28a745',
            'info': '#17a2b8',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'light': '#f8f9fa',
            'dark': '#343a40',
            'white': '#ffffff',
            'border': '#dee2e6',
            'text_primary': '#212529',
            'text_secondary': '#6c757d',
            'accent': '#4361ee',
        }
        
        fonts = {
            'h1': ('Microsoft YaHei', 20, 'bold'),
            'h2': ('Microsoft YaHei', 16, 'bold'),
            'h3': ('Microsoft YaHei', 14, 'bold'),
            'body': ('Microsoft YaHei', 11),
            'small': ('Microsoft YaHei', 10),
            'mono': ('Consolas', 10)
        }
        
        apk_dialog = tk.Tk()
        apk_dialog.title("APK信息设置")
        apk_dialog.geometry("500x600")
        apk_dialog.configure(bg=colors['light'])
        apk_dialog.resizable(False, False)

        try:
            icon_path = get_resource_path(os.path.join("icon", "icon.ico"))
            apk_dialog.iconbitmap(icon_path)
        except Exception:
            pass

        apk_dialog.update_idletasks()
        width = 500
        height = 600
        screen_width = apk_dialog.winfo_screenwidth()
        screen_height = apk_dialog.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        apk_dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        main_container = tk.Frame(apk_dialog, bg=colors['light'], padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        title_frame = tk.Frame(main_container, bg=colors['light'])
        title_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            title_frame,
            text="APK信息设置",
            font=fonts['h2'],
            bg=colors['light'],
            fg=colors['primary']
        ).pack()
        
        form_card = tk.Frame(
            main_container,
            bg=colors['white'],
            relief='solid',
            bd=1
        )
        form_card.pack(fill=tk.BOTH, expand=True, pady=10)
        form_frame = tk.Frame(form_card, bg=colors['white'], padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        entries = {}
        labels = [
            ("软件名称:", "app_name", "灵光应用"),
            ("版本号:", "version_code", "1"),
            ("版本名称:", "version_name", "1.0.0"),
            ("包名:", "package_name", "")
        ]

        for i, (label_text, key, default) in enumerate(labels):
            tk.Label(
                form_frame,
                text=label_text,
                font=fonts['body'],
                bg=colors['white'],
                fg=colors['text_secondary'],
                anchor='w'
            ).grid(row=i, column=0, sticky='w', pady=5, padx=5)

            e = tk.Entry(
                form_frame,
                font=fonts['body'],
                bg=colors['white'],
                fg=colors['text_primary'],
                relief='solid',
                bd=1
            )
            e.insert(0, default)
            e.grid(row=i, column=1, sticky='ew', pady=5, padx=5)
            entries[key] = e

        row = len(labels)
        tk.Label(
            form_frame,
            text="应用图标:",
            font=fonts['body'],
            bg=colors['white'],
            fg=colors['text_secondary'],
            anchor='w'
        ).grid(row=row, column=0, sticky='w', pady=5, padx=5)
        
        icon_frame = tk.Frame(form_frame, bg=colors['white'])
        icon_frame.grid(row=row, column=1, sticky='ew', pady=5, padx=5)
        
        icon_label = tk.Label(
            icon_frame,
            text="未选择图标",
            font=fonts['small'],
            bg=colors['white'],
            fg=colors['text_secondary'],
            anchor='w'
        )
        icon_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def select_icon():
            f = filedialog.askopenfilename(
                filetypes=[("图片文件", "*.png")]
            )
            if f:
                self.apk_info['icon_path'] = f
                name = os.path.basename(f)
                icon_label.config(
                    text=name[:20] + ("..." if len(name) > 20 else ""),
                    fg=colors['text_primary']
                )
        
        tk.Button(
            icon_frame,
            text="选择图标",
            font=fonts['body'],
            bg=colors['light'],
            fg=colors['primary'],
            activebackground=colors['border'],
            activeforeground=colors['primary'],
            relief='flat',
            bd=1,
            cursor='hand2',
            command=select_icon
        ).pack(side=tk.RIGHT)
        
        row += 1
        tk.Label(
            form_frame,
            text="屏幕方向:",
            font=fonts['body'],
            bg=colors['white'],
            fg=colors['text_secondary'],
            anchor='w'
        ).grid(row=row, column=0, sticky='w', pady=5, padx=5)
        
        orientation_frame = tk.Frame(form_frame, bg=colors['white'])
        orientation_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        
        orientation_var = tk.StringVar(value="portrait")
        fullscreen_var = tk.BooleanVar(value=False)

        def update_selection_state():
            orientation = str(orientation_var.get())
            fullscreen = bool(fullscreen_var.get())
            self.apk_info['orientation'] = orientation
            self.apk_info['fullscreen'] = fullscreen

        def set_orientation(value):
            orientation_var.set(value)
            update_selection_state()

        def on_fullscreen_toggle():
            current = fullscreen_var.get()
            new = not current
            fullscreen_var.set(new)
            update_selection_state()

        ttk.Radiobutton(
            orientation_frame,
            text="竖屏",
            variable=orientation_var,
            value="portrait",
            command=lambda: set_orientation("portrait")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            orientation_frame,
            text="横屏",
            variable=orientation_var,
            value="landscape",
            command=lambda: set_orientation("landscape")
        ).pack(side=tk.LEFT, padx=5)

        row += 1
        tk.Checkbutton(
            form_frame,
            text="全屏显示",
            variable=fullscreen_var,
            command=on_fullscreen_toggle,
            bg=colors['white'],
            font=fonts['body'],
            fg=colors['text_primary']
        ).grid(row=row, column=1, sticky='w', pady=5, padx=5)

        row += 1
        self.custom_keystore_checked = False
        
        def on_custom_keystore_click():
            self.custom_keystore_checked = not self.custom_keystore_checked
            if self.custom_keystore_checked:
                custom_checkbox.select()
            else:
                custom_checkbox.deselect()
            self.apk_info['use_custom_keystore'] = self.custom_keystore_checked

        custom_checkbox = tk.Checkbutton(
            form_frame,
            text="使用独立签名文件",
            command=on_custom_keystore_click,
            bg=colors['white'],
            font=fonts['body'],
            fg=colors['text_primary']
        )
        custom_checkbox.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        custom_checkbox.deselect()

        form_frame.columnconfigure(1, weight=1)
        
        tk.Label(
            main_container,
            text="提示：图标请使用PNG格式，尺寸为512x512像素",
            font=fonts['small'],
            bg=colors['light'],
            fg=colors['text_secondary']
        ).pack(pady=10)
        
        button_frame = tk.Frame(main_container, bg=colors['light'])
        button_frame.pack(fill=tk.X, pady=10)
        
        def generate_apk():
            try:
                self.apk_info.update({
                    k: entries[k].get().strip()
                    for k in ['app_name', 'version_code', 'version_name', 'package_name']
                })
                update_selection_state()
                
                self.apk_info['use_custom_keystore'] = self.custom_keystore_checked

                if not all([
                    self.apk_info["app_name"],
                    self.apk_info["version_code"].isdigit(),
                    self.apk_info["version_name"],
                    self.apk_info["package_name"]
                ]):
                    messagebox.showwarning("提示", "请填写所有必填信息！")
                    return

                apk_path, keystore_path = self.generate_apk_with_info(extracted_path)

                if apk_path:
                    messagebox.showinfo(
                        "成功",
                        f"APK生成成功！\n\n"
                        f"应用名称: {self.apk_info['app_name']}\n"
                        f"版本: {self.apk_info['version_name']}\n"
                        f"包名: {self.apk_info['package_name']}\n"
                        f"屏幕方向: {self.apk_info['orientation']}\n"
                        f"显示模式: {'全屏' if self.apk_info['fullscreen'] else '非全屏'}\n\n"
                        f"签名密钥: {os.path.basename(keystore_path)}\n\n"
                        f"APK文件已保存至:\n{apk_path}"
                    )
                    apk_dialog.destroy()

            except Exception as e:
                messagebox.showerror("APK生成失败", str(e))
        
        tk.Button(
            button_frame,
            text="生成APK",
            font=fonts['body'],
            bg=colors['primary'],
            fg='white',
            activebackground='#3a56d4',
            activeforeground='white',
            relief='flat',
            bd=1,
            cursor='hand2',
            command=generate_apk
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            button_frame,
            text="取消",
            font=fonts['body'],
            bg=colors['light'],
            fg=colors['text_secondary'],
            activebackground=colors['border'],
            activeforeground=colors['text_secondary'],
            relief='flat',
            bd=1,
            cursor='hand2',
            command=apk_dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        apk_dialog.update()
        apk_dialog.mainloop()


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <extracted_html_path>")
        sys.exit(1)

    extracted_html = sys.argv[1]
    APKGenerator().show_apk_info_dialog(extracted_html)


if __name__ == "__main__":
    main()
