import os
import sys
import zipfile
import tempfile
import shutil
import re
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import xml.etree.ElementTree as ET

ANDROID_NS = "http://schemas.android.com/apk/res/android"

def get_resource_path(relative_path):
    """获取资源的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(base_dir, relative_path)


class APKGenerator:
    def __init__(self):
        self.apk_info = {
            'app_name': '', 'version_code': '', 'version_name': '',
            'package_name': '', 'icon_path': '',
            'orientation': 'portrait', 'fullscreen': False
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
                    # 设置屏幕方向
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
            print("apktool 执行失败:", e)
            raise
        finally:
            if decode_dir and os.path.exists(decode_dir):
                shutil.rmtree(decode_dir, ignore_errors=True)

    def sign_apk_internal(self, unsigned_apk_path):
        keystore_path = get_resource_path(
            os.path.join("key", "lingguang_apktool.jks")
        )
        alias = "lingguang_apktool"
        password = "lingguang.apktool.atrbfac.key"

        if not os.path.exists(keystore_path):
            raise FileNotFoundError(f"未找到签名证书: {keystore_path}")

        try:
            from py.signature import sign_apk
        except Exception as e:
            raise RuntimeError(f"导入签名模块失败: {e}")

        try:
            sign_apk(unsigned_apk_path, keystore_path, alias, password, password)
        except Exception as e:
            raise RuntimeError(f"签名失败：{e}")

        return keystore_path

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

            print(f"当前选择模板: {template_name} (orientation={orientation}, fullscreen={fullscreen})")
            print(f"模板完整路径: {template_apk}")

            if not os.path.exists(template_apk):
                raise FileNotFoundError(f"未找到模板 APK: {template_apk}")

            temp_apk_path = os.path.join(temp_dir, "temp.apk")
            shutil.copy2(template_apk, temp_apk_path)

            try:
                if not self.modify_androidmanifest_apktool(temp_apk_path):
                    raise RuntimeError("使用 apktool 修改模板 AndroidManifest 失败")
            except Exception as e:
                print(f"修改模板 AndroidManifest 失败: {e}")
                raise

            extract_dir = os.path.join(temp_dir, "extract")
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(temp_apk_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            assets_webapp_dir = os.path.join(extract_dir, "assets", "webapp")
            os.makedirs(assets_webapp_dir, exist_ok=True)
            shutil.copy2(extracted_path, os.path.join(assets_webapp_dir, "index.html"))

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
            import traceback
            traceback.print_exc()
            raise
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def generate_apk_with_info(self, extracted_path):
        if not extracted_path or not os.path.exists(extracted_path):
            raise FileNotFoundError("未找到提取的 HTML 文件！")
        return self.prepare_apk_files(extracted_path)

    def show_apk_info_dialog(self, extracted_path):
        # 颜色方案
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
        
        # 字体设置
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

        # 设置窗口图标
        try:
            icon_path = get_resource_path(os.path.join("icon", "icon.ico"))
            apk_dialog.iconbitmap(icon_path)
        except Exception as e:
            print(f"APK设置窗口图标加载失败: {e}")
            pass

        # 居中显示
        apk_dialog.update_idletasks()
        width = 500
        height = 600
        screen_width = apk_dialog.winfo_screenwidth()
        screen_height = apk_dialog.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        apk_dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # 主容器
        main_container = tk.Frame(apk_dialog, bg=colors['light'], padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_frame = tk.Frame(main_container, bg=colors['light'])
        title_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            title_frame,
            text="APK信息设置",
            font=fonts['h2'],
            bg=colors['light'],
            fg=colors['primary']
        ).pack()
        
        # 表单卡片
        form_card = tk.Frame(
            main_container,
            bg=colors['white'],
            relief='solid',
            bd=1
        )
        form_card.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 表单内容
        form_frame = tk.Frame(form_card, bg=colors['white'], padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        entries = {}
        labels = [
            ("软件名称:", "app_name", "灵光应用"),
            ("版本号:", "version_code", "1"),
            ("版本名称:", "version_name", "1.0.0"),
            ("包名:", "package_name", "")
        ]
        
        for i, (label, key, default) in enumerate(labels):
            # 标签
            tk.Label(
                form_frame,
                text=label,
                font=fonts['body'],
                bg=colors['white'],
                fg=colors['text_secondary'],
                anchor='w'
            ).grid(row=i, column=0, sticky='w', pady=5, padx=5)
            
            # 输入框
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
        
        # 图标选择
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
        
        # 屏幕方向
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
            try:
                current = bool(fullscreen_var.get())
            except Exception:
                current = False
            new = not current
            fullscreen_var.set(new)
            update_selection_state()

        ttk.Radiobutton(
            orientation_frame,
            text="竖屏",
            variable=orientation_var,
            value="portrait",
            command=lambda v='portrait': set_orientation(v)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            orientation_frame,
            text="横屏",
            variable=orientation_var,
            value="landscape",
            command=lambda v='landscape': set_orientation(v)
        ).pack(side=tk.LEFT, padx=5)

        # 全屏选项
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
        
        # 设置列权重
        form_frame.columnconfigure(1, weight=1)
        
        # 提示信息
        tk.Label(
            main_container,
            text="提示：图标请使用PNG格式，尺寸为512x512像素",
            font=fonts['small'],
            bg=colors['light'],
            fg=colors['text_secondary']
        ).pack(pady=10)
        
        # 按钮区域
        button_frame = tk.Frame(main_container, bg=colors['light'])
        button_frame.pack(fill=tk.X, pady=10)
        
        def generate_apk():
            try:
                update_selection_state()
                print(f"用户选择: orientation={self.apk_info['orientation']}, fullscreen={self.apk_info['fullscreen']}")
                self.apk_info.update({
                    k: entries[k].get().strip()
                    for k in ['app_name', 'version_code', 'version_name', 'package_name']
                })

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
                messagebox.showerror("错误", f"APK生成失败：\n{str(e)}")
        
        # 生成按钮
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
        
        # 取消按钮
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
