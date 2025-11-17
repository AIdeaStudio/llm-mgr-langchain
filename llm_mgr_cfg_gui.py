"""
LLM 配置管理器 - 图形化界面
用于管理系统平台配置（llm_mgr_cfg.yaml）
支持平台和模型的添加、编辑、删除操作
"""
import os
import ast
import yaml
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json as json_lib
from llm_mgr import probe_platform_models


class LLMConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM 配置管理器")
        self.root.geometry("1200x800")
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        # 左侧：平台列表
        left_frame = ttk.LabelFrame(main_frame, text="系统平台配置", padding="5")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 平台选择和管理
        platform_header_frame = ttk.Frame(left_frame)
        platform_header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(platform_header_frame, text="选择平台:").pack(side=tk.LEFT, padx=5)
        self.platform_var = tk.StringVar()
        self.platform_combo = ttk.Combobox(platform_header_frame, textvariable=self.platform_var, state='readonly', width=25)
        self.platform_combo.pack(side=tk.LEFT, padx=5)
        self.platform_combo.bind('<<ComboboxSelected>>', self.on_platform_selected)
        
        # 平台管理按钮
        # 平台管理按钮
        ttk.Button(platform_header_frame, text="设为默认", command=self.set_as_default).pack(side=tk.LEFT, padx=2)
        ttk.Button(platform_header_frame, text="添加平台", command=self.add_platform).pack(side=tk.LEFT, padx=2)
        ttk.Button(platform_header_frame, text="删除平台", command=self.delete_platform).pack(side=tk.LEFT, padx=2)
        # 模型列表
        ttk.Label(left_frame, text="当前模型:").grid(row=1, column=0, sticky=(tk.W, tk.N), pady=5)
        
        model_frame = ttk.Frame(left_frame)
        model_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        self.model_listbox = tk.Listbox(model_frame, height=10, width=40)
        model_scrollbar = ttk.Scrollbar(model_frame, orient=tk.VERTICAL, command=self.model_listbox.yview)
        self.model_listbox.configure(yscrollcommand=model_scrollbar.set)
        self.model_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        model_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # 绑定双击事件到编辑
        self.model_listbox.bind('<Double-Button-1>', lambda e: self.edit_model())
        
        # 模型操作按钮
        model_btn_frame = ttk.Frame(left_frame)
        model_btn_frame.grid(row=2, column=1, sticky=tk.E, pady=5, padx=5)
        ttk.Button(model_btn_frame, text="测试选中模型", command=self.test_model).pack(side=tk.LEFT, padx=2)
        ttk.Button(model_btn_frame, text="编辑选中模型", command=self.edit_model).pack(side=tk.LEFT, padx=2)
        ttk.Button(model_btn_frame, text="删除选中模型", command=self.delete_model).pack(side=tk.LEFT, padx=2)
        
        # 平台 URL 编辑
        ttk.Label(left_frame, text="平台 URL:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.platform_url_entry = ttk.Entry(left_frame, width=40)
        self.platform_url_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(left_frame, text="保存平台 URL", command=self.save_platform_url).grid(row=4, column=1, sticky=tk.E, pady=5, padx=5)
        
        # 右侧：探测模型
        right_frame = ttk.LabelFrame(main_frame, text="模型探测", padding="5")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 探测配置区域
        ttk.Label(right_frame, text="Base URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.base_url_entry = ttk.Entry(right_frame, width=40, state='readonly')
        self.base_url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(right_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_key_entry = ttk.Entry(right_frame, width=40)
        self.api_key_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        ttk.Label(right_frame, text="环境变量名:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.env_var_entry = ttk.Entry(right_frame, width=40)
        self.env_var_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # 按钮框架
        button_row_frame = ttk.Frame(right_frame)
        button_row_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_row_frame, text="保存 API Key", command=self.save_api_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row_frame, text="探测可用模型", command=self.probe_models).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row_frame, text="添加模型到平台", command=self.open_add_model_dialog).pack(side=tk.LEFT, padx=5)
        
        # 筛选区域
        filter_frame = ttk.Frame(right_frame)
        filter_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(filter_frame, text="输入模型名称:").pack(side=tk.LEFT, padx=5)
        self.filter_entry = ttk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.filter_entry.bind('<KeyRelease>', self.on_filter_change)
        ttk.Button(filter_frame, text="清除", command=self.clear_filter).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="使用此名称", command=self.use_custom_model_name).pack(side=tk.LEFT, padx=2)
        
        # 探测结果（更大的列表）
        ttk.Label(right_frame, text="探测结果:").grid(row=5, column=0, sticky=(tk.W, tk.N), pady=5)
        
        probe_frame = ttk.Frame(right_frame)
        probe_frame.grid(row=5, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        self.probe_listbox = tk.Listbox(probe_frame, height=20, width=40)
        probe_scrollbar = ttk.Scrollbar(probe_frame, orient=tk.VERTICAL, command=self.probe_listbox.yview)
        self.probe_listbox.configure(yscrollcommand=probe_scrollbar.set)
        self.probe_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        probe_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # 双击直接打开添加对话框
        self.probe_listbox.bind('<Double-Button-1>', lambda e: self.open_add_model_dialog())
        
        # 底部：日志和保存
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        ttk.Label(bottom_frame, text="操作日志:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(bottom_frame, height=8, width=110)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=tk.E, pady=5)
        ttk.Button(button_frame, text="重新加载配置", command=self.reload_config).pack(side=tk.RIGHT, padx=5)
        ttk.Label(button_frame, text="💡 所有操作自动保存", foreground="green").pack(side=tk.RIGHT, padx=10)
        
        # 配置权重
        main_frame.columnconfigure(0, weight=2)  # 左侧更宽
        main_frame.columnconfigure(1, weight=3)  # 右侧相对窄
        main_frame.rowconfigure(0, weight=3)
        main_frame.rowconfigure(1, weight=1)
        
        left_frame.columnconfigure(1, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        right_frame.columnconfigure(1, weight=1)
        right_frame.rowconfigure(5, weight=1)  # 探测结果行可扩展
        
        # 当前配置（内存中）
        self.current_config = None
        self.probe_models_cache = []  # 缓存完整的探测结果
        self._current_platform_original_api_key = None  # 记录原始 api_key 配置（含占位符）
        self.load_config()
    
    def log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
    
    def load_config(self):
        """加载配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "llm_mgr_cfg.yaml")
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}

            if not isinstance(loaded, dict):
                raise ValueError("配置文件格式错误，应为字典结构")

            self.current_config = loaded
            platform_names = list(self.current_config.keys())
            self.platform_combo['values'] = platform_names

            if platform_names:
                # 默认选中第一个平台
                self.platform_var.set(platform_names[0])
                self.on_platform_selected()
            else:
                self.platform_var.set("")

            self.log("✓ 配置加载成功")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {e}")
            self.log(f"✗ 加载配置失败: {e}")
    
    def reload_config(self):
        """重新加载配置"""
        try:
            self.load_config()
            messagebox.showinfo("成功", "配置已重新加载")
        except Exception as e:
            messagebox.showerror("错误", f"重新加载失败: {e}")
    
    def on_platform_selected(self, event=None):
        """平台选择变化时更新模型列表"""
        platform_name = self.platform_var.get()
        if not platform_name or platform_name not in self.current_config:
            return
        
        platform_cfg = self.current_config[platform_name]
        self.model_listbox.delete(0, tk.END)
        
        # 立即清空探测结果列表和缓存
        self.probe_listbox.delete(0, tk.END)
        self.probe_models_cache = []
        
        # 填充 base_url（两个地方，但右侧只读）
        base_url = platform_cfg.get("base_url", "")
        self.base_url_entry.config(state='normal')
        self.base_url_entry.delete(0, tk.END)
        self.base_url_entry.insert(0, base_url)
        self.base_url_entry.config(state='readonly')
        
        self.platform_url_entry.delete(0, tk.END)
        self.platform_url_entry.insert(0, base_url)
        
        # 处理 api_key 和环境变量名
        self.api_key_entry.delete(0, tk.END)
        self.env_var_entry.delete(0, tk.END)
        
        # 保存原始 api_key 配置（含占位符）
        api_key_raw = platform_cfg.get("api_key", "")
        self._current_platform_original_api_key = api_key_raw
        
        if api_key_raw:
            # 去除可能的引号（YAML 需要引号才能保留大括号格式）
            api_key_stripped = api_key_raw.strip("'\"") if isinstance(api_key_raw, str) else ""
            
            # 检查是否为环境变量占位符格式 {ENV_VAR_NAME}
            if api_key_stripped.startswith("{") and api_key_stripped.endswith("}"):
                env_var_name = api_key_stripped[1:-1]  # 提取变量名
                self.env_var_entry.insert(0, env_var_name)
                # 尝试从环境变量读取实际值
                actual_value = self._get_env_var_value(env_var_name)
                if actual_value:
                    self.api_key_entry.insert(0, actual_value)  # 显示实际值
                    self.log(f"✓ 已从环境变量 {env_var_name} 加载 API Key")
                else:
                    self.api_key_entry.insert(0, "")  # 空白，等待用户输入
                    self.log(f"⚠ 环境变量 {env_var_name} 未在系统中找到，请在下方输入密钥并保存以更新该变量")
            else:
                # 明文 API Key - 直接显示，不做任何自动匹配
                self.api_key_entry.insert(0, api_key_raw)
                self.log(f"⚠ 检测到明文 API Key！请填写「环境变量名」并点击「保存 API Key」转换为安全格式")
        
        # 显示模型列表
        models = platform_cfg.get("models", {})
        for display_name, model_config in models.items():
            if isinstance(model_config, str):
                model_id = model_config
            else:
                model_id = model_config.get("model_name", "")
            self.model_listbox.insert(tk.END, f"{display_name} → {model_id}")

        # 异步执行一次模型探测
        self.probe_models(auto_start=True)
    
    def add_platform(self):
        """添加新平台"""
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("添加新平台")
        dialog.geometry("450x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 平台名称
        ttk.Label(dialog, text="平台名称:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # Base URL
        ttk.Label(dialog, text="Base URL:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        url_entry = ttk.Entry(dialog, width=40)
        url_entry.grid(row=1, column=1, padx=10, pady=10)
        url_entry.insert(0, "https://api.example.com/v1")
        
        # API Key (可选)
        ttk.Label(dialog, text="API Key (可选):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        key_entry = ttk.Entry(dialog, width=40)
        key_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # 环境变量名 (可选)
        ttk.Label(dialog, text="环境变量名 (可选):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        env_entry = ttk.Entry(dialog, width=40)
        env_entry.grid(row=3, column=1, padx=10, pady=10)
        
        def do_add():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            key = key_entry.get().strip()
            env_var = env_entry.get().strip()
            
            if not name or not url:
                messagebox.showerror("错误", "平台名称和 Base URL 不能为空", parent=dialog)
                return
            
            # 验证 URL 格式
            if not (url.startswith("http://") or url.startswith("https://")):
                messagebox.showerror("错误", "URL 必须以 http:// 或 https:// 开头", parent=dialog)
                return
            
            # 检查名称冲突
            if name in self.current_config:
                messagebox.showerror("错误", f"平台名称 '{name}' 已存在", parent=dialog)
                return
            
            try:
                # 添加到配置
                new_platform = {
                    "base_url": url,
                    "models": {}
                }
                
                # 处理 API Key（使用占位符格式，yaml.dump 会自动加引号）
                if env_var:
                    new_platform["api_key"] = f"{{{env_var}}}"
                    if key:
                        self._persist_env_var(env_var, key)
                    else:
                        existing_value = self._get_env_var_value(env_var)
                        if not existing_value:
                            messagebox.showerror(
                                "错误",
                                f"未找到环境变量 {env_var} 的值，请填写 API Key 或先在系统中配置该变量",
                                parent=dialog,
                            )
                            return
                        self.log(f"✓ 将复用环境变量 {env_var} 的现有值")
                else:
                    if key:
                        # 警告用户明文保存的风险
                        warning_result = messagebox.askyesno(
                            "🚨 安全警告",
                            "⚠️ 未填写环境变量名，API Key 将以明文形式保存！\n\n"
                            "❌ 明文密钥存在严重安全风险：\n"
                            "  • 任何能访问此文件的人都能窃取您的密钥\n"
                            "  • 可能导致财产损失和隐私泄露\n\n"
                            "🔒 建议：填写「环境变量名」安全存储\n\n"
                            "确定要继续保存明文密钥吗？",
                            icon='warning',
                            default='no',
                            parent=dialog
                        )
                        if not warning_result:
                            return
                        new_platform["api_key"] = key
                        self.log(f"⚠️ 用户选择为新平台 '{name}' 保存明文密钥")
                    else:
                        new_platform["api_key"] = None
                
                self.current_config[name] = new_platform
                
                # 保存到文件
                self._save_config_to_file()
                
                # 刷新界面
                self.platform_combo['values'] = list(self.current_config.keys())
                self.platform_var.set(name)
                self.on_platform_selected()
                
                self.log(f"✓ 已添加新平台: {name}")
                dialog.destroy()
                messagebox.showinfo("成功", f"平台 '{name}' 已添加")
                
            except Exception as e:
                self.log(f"✗ 添加平台失败: {e}")
                messagebox.showerror("错误", f"添加平台失败: {e}", parent=dialog)
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="确定", command=do_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def delete_platform(self):
        """删除选中的平台"""
        platform_name = self.platform_var.get()
        if not platform_name:
            messagebox.showwarning("警告", "请先选择一个平台")
            return
        
        if not messagebox.askyesno("确认", f"确定要删除平台 '{platform_name}' 及其所有模型吗？\n此操作不可恢复！"):
            return
        
        try:
            # 从配置中删除
            del self.current_config[platform_name]
            
            # 保存到文件
            self._save_config_to_file()
            
            # 刷新界面
            self.platform_combo['values'] = list(self.current_config.keys())
            if self.current_config:
                self.platform_var.set(list(self.current_config.keys())[0])
                self.on_platform_selected()
            else:
                self.platform_var.set("")
                self.model_listbox.delete(0, tk.END)
            
            self.log(f"✓ 已删除平台: {platform_name}")
            messagebox.showinfo("成功", f"平台 '{platform_name}' 已删除")
            
        except Exception as e:
            self.log(f"✗ 删除平台失败: {e}")
            messagebox.showerror("错误", f"删除平台失败: {e}")
    
    def save_platform_url(self):
        """保存平台的 base_url"""
        platform_name = self.platform_var.get()
        if not platform_name:
            messagebox.showwarning("警告", "请先选择一个平台")
            return
        
        new_url = self.platform_url_entry.get().strip()
        if not new_url:
            messagebox.showerror("错误", "请填写平台 URL")
            return
        
        # 验证 URL 格式
        if not (new_url.startswith("http://") or new_url.startswith("https://")):
            messagebox.showerror("错误", "URL 必须以 http:// 或 https:// 开头")
            return
        
        try:
            # 更新配置
            self.current_config[platform_name]["base_url"] = new_url
            
            # 立即保存到配置文件
            self._save_config_to_file()
            
            # 刷新显示
            self.on_platform_selected()
            
            self.log(f"✓ 已更新平台 '{platform_name}' 的 URL: {new_url}")
            messagebox.showinfo("成功", f"平台 URL 已更新")
            
        except Exception as e:
            self.log(f"✗ 保存失败: {e}")
            messagebox.showerror("错误", f"保存平台 URL 失败: {e}")
    
    def save_api_key(self):
        """保存 API Key 到配置文件（环境变量格式或明文）"""
        platform_name = self.platform_var.get()
        if not platform_name:
            messagebox.showwarning("警告", "请先选择一个平台")
            return

        env_var_name = self.env_var_entry.get().strip()
        api_key = self.api_key_entry.get().strip()
        
        # 如果没有填写 API Key，直接返回
        if not api_key:
            messagebox.showerror("错误", "请填写 API Key")
            return
        
        # 如果没有填写环境变量名，警告后允许保存明文
        if not env_var_name:
            warning_result = messagebox.askyesno(
                "🚨 安全警告",
                "⚠️ 未填写环境变量名，API Key 将以明文形式保存到配置文件！\n\n"
                "❌ 明文密钥存在严重安全风险：\n"
                "  • 任何能访问此文件的人都能窃取您的密钥\n"
                "  • 可能导致财产损失和隐私泄露\n"
                "  • 不应上传到 Git/GitHub 或分享给他人\n\n"
                "🔒 建议操作：\n"
                "  1. 点击「否」取消保存\n"
                "  2. 填写「环境变量名」(如: OPENAI_API_KEY)\n"
                "  3. 使用环境变量安全存储\n\n"
                "确定要继续保存明文密钥吗？",
                icon='warning',
                default='no'
            )
            
            if not warning_result:
                self.log("✗ 用户取消保存明文密钥")
                return
            
            # 用户确认保存明文
            try:
                self.current_config[platform_name]["api_key"] = api_key
                self._save_config_to_file()
                self._current_platform_original_api_key = api_key
                self.on_platform_selected()
                
                self.log(f"⚠️ 平台 '{platform_name}' 的 API Key 已保存为明文（不建议）")
                messagebox.showinfo("已保存", "API Key 已保存为明文格式\n\n⚠️ 请注意保护此配置文件的安全")
                return
                
            except Exception as e:
                self.log(f"✗ 保存失败: {e}")
                messagebox.showerror("错误", f"保存 API Key 失败: {e}")
                return
        
        # 验证环境变量名格式
        import re
        if not re.match(r'^[A-Z0-9_]+$', env_var_name):
            messagebox.showerror("错误", "环境变量名只能包含大写字母、数字和下划线\n例如: OPENAI_API_KEY")
            return

        try:
            # 检查是否已经是环境变量格式且没有修改
            original_api_key = self._current_platform_original_api_key or ""
            # 去除引号后比较
            original_stripped = original_api_key.strip("'\"") if isinstance(original_api_key, str) else ""
            expected_placeholder = f"{{{env_var_name}}}"
            
            # 如果配置已经是这个占位符，且输入框的值来自环境变量（未手动修改）
            if original_stripped == expected_placeholder:
                # 检查用户是否真的修改了密钥
                current_env_value = self._get_env_var_value(env_var_name)
                if api_key == current_env_value and api_key:
                    # 密钥没变，只是重新加载显示的，不需要更新
                    messagebox.showinfo("提示", f"环境变量 {env_var_name} 配置未发生变化，无需保存")
                    return
            
            persist_note = ""
            if api_key:
                persisted = self._persist_env_var(env_var_name, api_key)
                persist_note = "已写入系统环境变量" if persisted else "已写入当前会话环境变量"
            else:
                existing_value = self._get_env_var_value(env_var_name)
                if not existing_value:
                    messagebox.showerror(
                        "错误",
                        f"未找到环境变量 {env_var_name} 的值，请先在输入框中填写密钥或在系统中配置该变量",
                    )
                    return
                persist_note = "已引用系统环境变量当前值"

            # 保存为标准占位符格式，yaml.dump 会自动添加引号
            self.current_config[platform_name]["api_key"] = expected_placeholder

            self._save_config_to_file()
            self._current_platform_original_api_key = expected_placeholder
            self.on_platform_selected()

            self.log(f"✓ 平台 '{platform_name}' 的 API Key 已更新为环境变量 {env_var_name}")

            messagebox.showinfo(
                "成功",
                f"API Key 已保存！\n\n环境变量: {env_var_name}\n配置文件: {{{env_var_name}}}\n{persist_note}",
            )

        except Exception as e:
            self.log(f"✗ 保存失败: {e}")
            messagebox.showerror("错误", f"保存 API Key 失败: {e}")
    
    def probe_models(self, auto_start=False):
        """探测平台可用模型"""
        base_url = self.base_url_entry.get().strip()
        api_key = self.api_key_entry.get().strip()
        
        if not base_url:
            if not auto_start: # 只有用户手动点击时才警告
                messagebox.showwarning("警告", "请先选择平台（Base URL 将自动填充）")
            return
        
        # 验证 API Key（如果输入框有内容就直接使用，否则从配置读取）
        if not api_key or not api_key.strip():
            if not auto_start: # 只有用户手动点击时才警告
                messagebox.showerror("错误", "请在 API Key 输入框中填写有效的密钥")
            self.log("⚠ API Key 未填写，跳过自动探测。")
            return
        
        self.log(f"正在探测 {base_url} ...")
        self.probe_listbox.delete(0, tk.END)
        
        def do_probe():
            try:
                models = probe_platform_models(base_url, api_key, raise_on_error=True)
                self.root.after(0, lambda res=models: self.show_probe_results(res))
            except Exception as e:
                self.root.after(0, lambda err=str(e): self.show_probe_error(err))
        
        threading.Thread(target=do_probe, daemon=True).start()
    
    def show_probe_results(self, models):
        """显示探测结果"""
        if not models:
            self.log("✗ 未探测到任何模型")
            messagebox.showinfo("结果", "未探测到任何模型")
            return
        
        # 缓存完整结果
        self.probe_models_cache = [model.get('id', '') for model in models]
        
        # 显示所有模型
        self.probe_listbox.delete(0, tk.END)
        for model_id in self.probe_models_cache:
            self.probe_listbox.insert(tk.END, model_id)
        
        self.log(f"✓ 探测到 {len(models)} 个模型")
    
    def show_probe_error(self, error_msg):
        """显示探测错误"""
        self.log(f"✗ 探测失败: {error_msg}")
        messagebox.showerror("探测失败", error_msg)
    
    def on_filter_change(self, event=None):
        """筛选关键字变化时更新列表"""
        keyword = self.filter_entry.get().strip().lower()
        
        self.probe_listbox.delete(0, tk.END)
        
        if not keyword:
            # 没有关键字，显示所有
            for model_id in self.probe_models_cache:
                self.probe_listbox.insert(tk.END, model_id)
        else:
            # 筛选匹配的模型
            filtered = [m for m in self.probe_models_cache if keyword in m.lower()]
            for model_id in filtered:
                self.probe_listbox.insert(tk.END, model_id)
            
            if filtered:
                self.log(f"筛选结果: {len(filtered)} 个模型匹配 '{keyword}'")
            else:
                self.log(f"筛选结果: 没有模型匹配 '{keyword}'")
    
    def clear_filter(self):
        """清除筛选"""
        self.filter_entry.delete(0, tk.END)
        self.on_filter_change()

    def use_custom_model_name(self):
        """使用筛选框中输入的自定义名称打开添加模型对话框"""
        custom_model_id = self.filter_entry.get().strip()
        if not custom_model_id:
            messagebox.showwarning("警告", "请输入要使用的模型名称")
            return
        self.open_add_model_dialog(custom_model_id=custom_model_id)
    
    def open_add_model_dialog(self, custom_model_id=None):
        """打开添加模型对话框"""
        platform_name = self.platform_var.get()
        if not platform_name:
            messagebox.showwarning("警告", "请先选择一个平台")
            return
        
        # 获取选中的模型ID（如果有）
        if custom_model_id:
            selected_model_id = custom_model_id
        else:
            selected_model_id = ""
            selection = self.probe_listbox.curselection()
            if selection:
                selected_model_id = self.probe_listbox.get(selection[0])
        
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(f"添加模型到 {platform_name}")
        dialog.geometry("550x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 显示名称
        ttk.Label(dialog, text="显示名称:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        display_name_entry = ttk.Entry(dialog, width=50)
        display_name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        if selected_model_id:
            display_name_entry.insert(0, selected_model_id)
        
        # 模型ID
        ttk.Label(dialog, text="模型ID:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        model_id_entry = ttk.Entry(dialog, width=50)
        model_id_entry.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        if selected_model_id:
            model_id_entry.insert(0, selected_model_id)
        
        # Extra Body
        ttk.Label(dialog, text="Extra Body (JSON):").grid(row=2, column=0, sticky=(tk.W, tk.N), padx=10, pady=10)
        
        extra_body_frame = ttk.Frame(dialog)
        extra_body_frame.grid(row=2, column=1, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        extra_body_text = tk.Text(extra_body_frame, width=50, height=8)
        extra_body_text.pack(fill=tk.BOTH, expand=True)
        
        # 示例说明
        example_label = ttk.Label(extra_body_frame, 
                                  text='示例1: {"thinkingBudget": 0}\n'
                                       '示例2: {"thinking": {"type": "disabled"}}\n'
                                       '示例3: {"top_k": 40, "temperature": 0.7}',
                                  foreground="gray", 
                                  font=('TkDefaultFont', 8),
                                  justify=tk.LEFT)
        example_label.pack(anchor=tk.W, pady=(5, 0))
        
        def do_add():
            display_name = display_name_entry.get().strip()
            model_id = model_id_entry.get().strip()
            
            if not display_name or not model_id:
                messagebox.showwarning("警告", "请填写显示名称和模型ID", parent=dialog)
                return
            
            # 检查显示名称是否重复
            if display_name in self.current_config[platform_name].get("models", {}):
                if not messagebox.askyesno("确认", 
                    f"显示名称 '{display_name}' 已存在，是否覆盖？", 
                    parent=dialog):
                    return
            
            # 解析 extra_body
            extra_body_str = extra_body_text.get("1.0", tk.END)
            try:
                extra_body = self._parse_extra_body(extra_body_str)
            except ValueError as err:
                messagebox.showerror("错误", str(err), parent=dialog)
                return
            
            # 添加到内存配置
            if "models" not in self.current_config[platform_name]:
                self.current_config[platform_name]["models"] = {}
            
            # 根据是否有 extra_body 选择存储格式
            if extra_body:
                self.current_config[platform_name]["models"][display_name] = {
                    "model_name": model_id,
                    "extra_body": extra_body
                }
            else:
                self.current_config[platform_name]["models"][display_name] = model_id
            
            # 立即保存到配置文件
            try:
                self._save_config_to_file()
                self.log(f"✓ 已添加模型: {display_name} → {model_id}")
                messagebox.showinfo("成功", f"模型 '{display_name}' 已添加", parent=dialog)
            except Exception as e:
                self.log(f"✗ 保存失败: {e}")
                messagebox.showerror("错误", f"添加模型失败: {e}", parent=dialog)
                return
            
            # 刷新显示
            self.on_platform_selected()
            dialog.destroy()
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="添加", command=do_add, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
        # 配置权重
        dialog.columnconfigure(1, weight=1)
        dialog.rowconfigure(2, weight=1)
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def edit_model(self):
        """编辑选中的模型（打开编辑对话框）"""
        platform_name = self.platform_var.get()
        if not platform_name:
            return
        
        selection = self.model_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的模型")
            return
        
        model_str = self.model_listbox.get(selection[0])
        display_name = model_str.split(" → ")[0]
        
        models = self.current_config[platform_name].get("models", {})
        model_config = models.get(display_name)
        
        if not model_config:
            return
        
        # 解析模型配置
        if isinstance(model_config, str):
            model_id = model_config
            extra_body_dict = None
        else:
            model_id = model_config.get("model_name", "")
            extra_body_dict = model_config.get("extra_body")
        
        # 创建编辑对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(f"编辑模型: {display_name}")
        dialog.geometry("550x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 显示名称
        ttk.Label(dialog, text="显示名称:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        display_name_entry = ttk.Entry(dialog, width=50)
        display_name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        display_name_entry.insert(0, display_name)
        # 允许编辑显示名称
        
        # 模型ID
        ttk.Label(dialog, text="模型ID:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        model_id_entry = ttk.Entry(dialog, width=50)
        model_id_entry.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        model_id_entry.insert(0, model_id)
        
        # Extra Body
        ttk.Label(dialog, text="Extra Body (JSON):").grid(row=2, column=0, sticky=(tk.W, tk.N), padx=10, pady=10)
        
        extra_body_frame = ttk.Frame(dialog)
        extra_body_frame.grid(row=2, column=1, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        extra_body_text = tk.Text(extra_body_frame, width=50, height=8)
        extra_body_text.pack(fill=tk.BOTH, expand=True)
        
        if extra_body_dict:
            import json
            extra_body_text.insert("1.0", json.dumps(extra_body_dict, indent=2, ensure_ascii=False))
        
        # 示例说明
        example_label = ttk.Label(extra_body_frame, 
                                  text='示例1: {"thinkingBudget": 0}\n'
                                       '示例2: {"thinking": {"type": "disabled"}}\n'
                                       '示例3: {"top_k": 40, "temperature": 0.7}',
                                  foreground="gray", 
                                  font=('TkDefaultFont', 8),
                                  justify=tk.LEFT)
        example_label.pack(anchor=tk.W, pady=(5, 0))
        
        def do_update():
            new_display_name = display_name_entry.get().strip()
            new_model_id = model_id_entry.get().strip()
            
            if not new_display_name or not new_model_id:
                messagebox.showwarning("警告", "请填写显示名称和模型ID", parent=dialog)
                return
            
            # 如果显示名称被修改，检查是否与其他模型冲突
            if new_display_name != display_name:
                if new_display_name in self.current_config[platform_name].get("models", {}):
                    messagebox.showerror("错误", f"显示名称 '{new_display_name}' 已存在，请使用其他名称", parent=dialog)
                    return
            
            # 解析 extra_body
            extra_body_str = extra_body_text.get("1.0", tk.END)
            try:
                extra_body = self._parse_extra_body(extra_body_str)
            except ValueError as err:
                messagebox.showerror("错误", str(err), parent=dialog)
                return
            
            # 如果显示名称改变，删除旧的配置
            if new_display_name != display_name:
                del self.current_config[platform_name]["models"][display_name]
            
            # 更新配置
            if extra_body:
                self.current_config[platform_name]["models"][new_display_name] = {
                    "model_name": new_model_id,
                    "extra_body": extra_body
                }
            else:
                self.current_config[platform_name]["models"][new_display_name] = new_model_id
            
            # 立即保存到配置文件
            try:
                self._save_config_to_file()
                if new_display_name != display_name:
                    self.log(f"✓ 已更新模型: {display_name} → {new_display_name}")
                else:
                    self.log(f"✓ 已更新模型: {new_display_name}")
                messagebox.showinfo("成功", f"模型已更新", parent=dialog)
            except Exception as e:
                self.log(f"✗ 保存失败: {e}")
                messagebox.showerror("错误", f"更新模型失败: {e}", parent=dialog)
                return
            
            # 刷新显示
            self.on_platform_selected()
            dialog.destroy()
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="保存", command=do_update, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
        # 配置权重
        dialog.columnconfigure(1, weight=1)
        dialog.rowconfigure(2, weight=1)
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def _parse_extra_body(self, text):
        raw_text = (text or "").strip()
        if not raw_text:
            return None

        try:
            parsed = json_lib.loads(raw_text)
        except json_lib.JSONDecodeError:
            try:
                parsed = ast.literal_eval(raw_text)
            except (ValueError, SyntaxError) as exc:
                raise ValueError(f"Extra Body 不是有效的 JSON/字面量:\n{exc}") from exc

        if not isinstance(parsed, dict):
            raise ValueError("Extra Body 必须是一个 JSON 对象，例如 {\"enable_thinking\": true}")

        return parsed

    def _get_env_var_value(self, name: str) -> str:
        if not name:
            return ""

        # 优先从注册表读取（Windows），确保获取最新值
        if os.name == 'nt':
            try:
                import winreg
                
                locations = [
                    (winreg.HKEY_CURRENT_USER, r"Environment"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment"),
                ]

                for hive, path in locations:
                    try:
                        with winreg.OpenKey(hive, path) as key:
                            reg_value, _ = winreg.QueryValueEx(key, name)
                            if reg_value:
                                # 同步到当前进程环境变量
                                os.environ[name] = reg_value
                                return reg_value
                    except FileNotFoundError:
                        continue
                    except OSError:
                        continue
            except ImportError:
                pass

        # 回退到进程环境变量
        value = os.environ.get(name)
        if value:
            return value

        return ""

    def _persist_env_var(self, name: str, value: str) -> bool:
        os.environ[name] = value

        if os.name == 'nt':
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                    0,
                    winreg.KEY_SET_VALUE,
                )
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
                winreg.CloseKey(key)

                import ctypes

                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x1A
                SMTO_ABORTIFHUNG = 0x0002
                result = ctypes.c_long()
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST,
                    WM_SETTINGCHANGE,
                    0,
                    "Environment",
                    SMTO_ABORTIFHUNG,
                    5000,
                    ctypes.byref(result),
                )

                self.log(f"✓ 已将 {name} 写入用户环境变量")
                return True

            except Exception as exc:
                self.log(f"⚠ 写入用户环境变量失败: {exc}")
                self.log("✓ 已更新当前会话环境变量，可手动写入系统环境变量以持久化")
                return False
        else:
            # Linux/macOS: 写入 shell 配置文件
            try:
                shell_configs = [
                    os.path.expanduser("~/.zshrc"),
                    os.path.expanduser("~/.bashrc"),
                    os.path.expanduser("~/.profile"),
                ]
                
                # 选择存在的第一个配置文件
                target_file = None
                for config in shell_configs:
                    if os.path.exists(config):
                        target_file = config
                        break
                
                if not target_file:
                    target_file = os.path.expanduser("~/.bashrc")  # 默认
                
                # 读取现有内容
                content = ""
                if os.path.exists(target_file):
                    with open(target_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                export_line = f'export {name}="{value}"'
                
                # 检查是否已存在该变量
                import re
                if re.search(rf'^export\s+{name}=', content, re.MULTILINE):
                    # 已存在，更新
                    new_content = re.sub(
                        rf'^export\s+{name}=.*$',
                        export_line,
                        content,
                        flags=re.MULTILINE
                    )
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    self.log(f"✓ 已更新 {target_file} 中的 {name}")
                else:
                    # 不存在，追加
                    with open(target_file, 'a', encoding='utf-8') as f:
                        f.write(f'\n# Added by LLM Config Manager\n{export_line}\n')
                    self.log(f"✓ 已追加 {name} 到 {target_file}")
                
                self.log(f"⚠ 请运行 'source {target_file}' 或重启终端使其生效")
                return True
                
            except Exception as exc:
                self.log(f"⚠ 写入配置文件失败: {exc}")
                self.log(f"⚠ 请手动添加到 shell 配置文件:")
                self.log(f"   export {name}='{value}'")
                return False

    def _save_config_to_file(self):
        """内部方法：将配置保存到文件"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "llm_mgr_cfg.yaml")
            
            # 准备保存的配置（保留环境变量占位符格式）
            save_config = {}
            plaintext_keys_found = []
            
            for name, cfg in self.current_config.items():
                save_cfg = dict(cfg)
                save_config[name] = save_cfg
                
                # 安全检查：检测明文 API Key（仅记录日志）
                api_key_value = cfg.get("api_key", "")
                if api_key_value and isinstance(api_key_value, str):
                    candidate = api_key_value.strip()

                    # 去除成对引号（YAML 会以 `'value'` 存储）
                    if (candidate.startswith("'") and candidate.endswith("'")) or (
                        candidate.startswith('"') and candidate.endswith('"')
                    ):
                        candidate = candidate[1:-1].strip()

                    # 检查是否为环境变量占位符格式 {VAR_NAME}
                    is_env_var = False
                    if candidate.startswith("{") and candidate.endswith("}") and len(candidate) > 2:
                        inner_name = candidate[1:-1].strip()
                        if inner_name:
                            import re as _re
                            if _re.fullmatch(r"[A-Z0-9_]+", inner_name):
                                is_env_var = True

                    if not is_env_var:
                        # 检查是否看起来像真实密钥（长度 > 10 且包含字母数字）
                        if len(candidate) > 10 and any(c.isalnum() for c in candidate):
                            plaintext_keys_found.append(name)
            
            # 如果发现明文密钥，记录到日志（不再弹窗，因为在上层已经警告过）
            if plaintext_keys_found:
                platforms_list = ", ".join(plaintext_keys_found)
                self.log(f"⚠️ 检测到明文密钥的平台: {platforms_list}")
            
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(save_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False, default_style="'")
            
            self.log(f"✓ 配置已保存到: {config_path}")
            
        except Exception as e:
            self.log(f"✗ 保存失败: {e}")
            raise

    def test_model(self):
        """测试选中的模型是否可用"""
        platform_name = self.platform_var.get()
        if not platform_name:
            messagebox.showwarning("警告", "请先选择一个平台")
            return

        selection = self.model_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请在左侧选择要测试的模型")
            return

        model_str = self.model_listbox.get(selection[0])
        display_name = model_str.split(" → ")[0]

        models = self.current_config[platform_name].get("models", {})
        model_config = models.get(display_name)
        if not model_config:
            messagebox.showerror("错误", f"未找到模型 '{display_name}' 的配置")
            return

        if isinstance(model_config, str):
            model_id = model_config
            extra_body = None
        else:
            model_id = model_config.get("model_name", "")
            extra_body = model_config.get("extra_body")

        base_url = self.current_config[platform_name].get("base_url", "").strip()
        api_key = self.api_key_entry.get().strip()

        if not base_url:
            messagebox.showerror("错误", "当前平台缺少 Base URL，无法测试模型")
            return
        if not api_key:
            messagebox.showerror("错误", "请填写 API Key 以进行测试")
            return
        if not model_id:
            messagebox.showerror("错误", "模型配置缺少模型 ID")
            return

        self.log(f"正在测试模型: {display_name} ({model_id})...")

        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": "一句话介绍你自己叫什么，由谁开发，用最少的回复。快速回答，无需推理或思考。"}],
            "max_tokens": 16
        }
        if isinstance(extra_body, dict):
            # 不修改原配置，复制后再合并
            payload.update(extra_body)

        url = base_url.rstrip("/")
        if url.endswith("/v1"):
            url = f"{url}/chat/completions"
        elif url.endswith("/v1/"):
            url = f"{url}chat/completions"
        else:
            url = f"{url}/v1/chat/completions"

        def do_test():
            try:
                import requests

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                resp = requests.post(url, headers=headers, json=payload, timeout=30)

                if resp.ok:
                    result = resp.json()
                    self.root.after(0, lambda r=result: self.show_test_result(True, display_name, r))
                else:
                    error_detail = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    self.root.after(0, lambda err=error_detail: self.show_test_result(False, display_name, err))

            except Exception as exc:
                self.root.after(0, lambda err=str(exc): self.show_test_result(False, display_name, err))

        threading.Thread(target=do_test, daemon=True).start()

    def show_test_result(self, success, model_name, result):
        """在主线程中显示测试结果"""
        if success:
            content_preview = ""
            if isinstance(result, dict):
                choices = result.get("choices")
                if isinstance(choices, list) and choices:
                    message_block = choices[0].get("message", {})
                    content_preview = message_block.get("content", "") or "[响应体缺少消息内容]"
                log_payload = json_lib.dumps(result, ensure_ascii=False, indent=2)
            else:
                # 兜底，确保可以显示
                log_payload = str(result)
                content_preview = "[未知格式的响应]"

            if len(log_payload) > 800:
                log_payload = log_payload[:800] + "..."

            self.log(f"✓ 模型 '{model_name}' 测试成功!")
            self.log(f"  响应: {log_payload}")
            messagebox.showinfo("测试成功", f"模型 '{model_name}' 可用！\n\n响应预览（部分模型可能会输出错误的身份信息，属正常现象）:\n{content_preview}")
        else:
            self.log(f"✗ 模型 '{model_name}' 测试失败: {result}")
            messagebox.showerror("测试失败", f"模型 '{model_name}' 测试失败。\n\n错误详情:\n{result}")
    
    def set_as_default(self):
        """将选中的平台设为默认（移动到配置文件第一位）"""
        platform_name = self.platform_var.get()
        if not platform_name:
            messagebox.showwarning("警告", "请先选择一个平台")
            return
        
        if not messagebox.askyesno("确认", f"确定要将 '{platform_name}' 设为默认平台吗？\n它将被移动到配置文件的第一位，在用户没有选中模型的时候优先使用。"):
            return

        try:
            # 获取当前配置的键列表
            keys = list(self.current_config.keys())
            
            # 如果已经是第一个，无需操作
            if keys[0] == platform_name:
                self.log(f"✓ '{platform_name}' 已经是默认平台")
                messagebox.showinfo("提示", f"'{platform_name}' 已经是默认平台。")
                return

            # 重新构建字典，将选中的平台移到第一位
            new_config = {}
            new_config[platform_name] = self.current_config[platform_name]
            
            for key in keys:
                if key != platform_name:
                    new_config[key] = self.current_config[key]
            
            # 更新内存中的配置
            self.current_config = new_config
            
            # 保存到文件
            self._save_config_to_file()
            
            # 刷新界面
            self.platform_combo['values'] = list(self.current_config.keys())
            self.platform_var.set(platform_name) # 保持当前选中状态
            self.on_platform_selected()
            
            self.log(f"✓ 已将 '{platform_name}' 设为默认平台")
            messagebox.showinfo("成功", f"已将 '{platform_name}' 设为默认平台。")
            
        except Exception as e:
            self.log(f"✗ 设置默认平台失败: {e}")
            messagebox.showerror("错误", f"设置默认平台失败: {e}")
    
    def delete_model(self):
        """删除选中的模型"""
        platform_name = self.platform_var.get()
        if not platform_name:
            return
        
        selection = self.model_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的模型")
            return
        
        model_str = self.model_listbox.get(selection[0])
        display_name = model_str.split(" → ")[0]
        
        if not messagebox.askyesno("确认", f"确定要删除模型 '{display_name}' 吗？"):
            return
        
        # 从内存配置中删除
        if display_name in self.current_config[platform_name].get("models", {}):
            del self.current_config[platform_name]["models"][display_name]
            
            # 立即保存到配置文件
            try:
                self._save_config_to_file()
                self.log(f"✓ 已删除模型: {display_name}")
            except Exception as e:
                self.log(f"✗ 保存失败: {e}")
                messagebox.showerror("错误", f"删除模型失败: {e}")
                return
            
            self.on_platform_selected()


def main():
    """主函数：启动 GUI"""
    root = tk.Tk()
    app = LLMConfigGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
