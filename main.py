import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import moviepy.editor as mp
from faster_whisper import WhisperModel
import threading

# 设置模型路径
model_dir = "./models"


# 创建主界面
class TranscribeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper 转写工具")
        self.root.geometry("600x800")

        # 选择文件按钮
        self.label_files = tk.Label(root, text="选择视频或音频文件:")
        self.label_files.pack(pady=10)
        self.btn_select_files = tk.Button(root, text="选择文件", command=self.select_files)
        self.btn_select_files.pack()

        # 已选择文件显示
        self.selected_files_text = tk.Text(root, height=5, width=50)
        self.selected_files_text.pack(pady=10)

        # 选择保存目录
        self.label_save_dir = tk.Label(root, text="选择保存目录:")
        self.label_save_dir.pack(pady=10)
        self.btn_select_save_dir = tk.Button(root, text="选择保存地址", command=self.select_save_dir)
        self.btn_select_save_dir.pack()

        # 已选择保存目录显示
        self.selected_save_dir_text = tk.Text(root, height=2, width=50)
        self.selected_save_dir_text.pack(pady=10)

        # 选择模型
        self.label_model = tk.Label(root, text="选择Whisper模型:")
        self.label_model.pack(pady=10)
        self.model_var = tk.StringVar(root)
        self.model_var.set("base")  # 默认模型
        self.option_menu = tk.OptionMenu(root, self.model_var, "large-v3", "large-v1", "medium", "base", "small")
        self.option_menu.pack()

        # 选择语言
        self.label_language = tk.Label(root, text="选择语言:")
        self.label_language.pack(pady=10)
        self.language_var = tk.StringVar(root)
        self.language_var.set("zh")  # 默认自动检测语言
        self.language_menu = tk.OptionMenu(root, self.language_var, "en", "zh", "es", "fr", "de", "ja", "ko")
        self.language_menu.pack()

        # 选择CPU/GPU
        self.label_device = tk.Label(root, text="选择设备:")
        self.label_device.pack(pady=10)
        self.device_var = tk.StringVar(value="cpu")
        self.radio_cpu = tk.Radiobutton(root, text="CPU", variable=self.device_var, value="cpu")
        self.radio_gpu = tk.Radiobutton(root, text="GPU (CUDA)", variable=self.device_var, value="cuda")  # 修改为cuda
        self.radio_cpu.pack()
        self.radio_gpu.pack()

        # 是否保存为一个txt文件
        self.save_as_one_var = tk.BooleanVar(value=False)
        self.check_save_as_one = tk.Checkbutton(root, text="保存为一个txt文件", variable=self.save_as_one_var)
        self.check_save_as_one.pack()

        # 转写按钮
        self.btn_transcribe = tk.Button(root, text="开始转写", command=self.start_transcription)
        self.btn_transcribe.pack(pady=20)

        # 转写进度显示
        self.progress_text = tk.Text(root, height=10, width=50)
        self.progress_text.pack(pady=10)

        # 存储文件和保存路径
        self.files = []
        self.save_dir = ""

    def select_files(self):
        # 选择视频或音频文件，支持多种格式
        self.files = filedialog.askopenfilenames(
            title="选择视频或音频文件",
            filetypes=[
                ("视频/音频文件", "*.mp4 *.mov *.avi *.mkv *.mp3 *.wav"),
                ("所有文件", "*.*")
            ]
        )
        self.progress_text.insert(tk.END, f"选择了 {len(self.files)} 个文件。\n")
        # 显示已选择的文件
        self.selected_files_text.delete(1.0, tk.END)
        self.selected_files_text.insert(tk.END, "\n".join(self.files))

    def select_save_dir(self):
        # 选择保存目录
        self.save_dir = filedialog.askdirectory(title="选择保存目录")
        self.progress_text.insert(tk.END, f"选择的保存目录: {self.save_dir}\n")
        # 显示已选择的保存路径
        self.selected_save_dir_text.delete(1.0, tk.END)
        self.selected_save_dir_text.insert(tk.END, self.save_dir)

    def start_transcription(self):
        # 检查是否选择了文件和保存路径
        if not self.files:
            messagebox.showerror("错误", "请先选择视频或音频文件！")
            return
        if not self.save_dir:
            messagebox.showerror("错误", "请先选择保存目录！")
            return

        # 开始转写任务
        self.progress_text.insert(tk.END, "开始转写...\n")
        threading.Thread(target=self.transcribe).start()  # 使用线程避免界面冻结

    def transcribe(self):
        # 加载选定的模型
        model_name = self.model_var.get()
        device = self.device_var.get()  # 使用"cuda"代替"gpu"
        language = self.language_var.get()
        model = WhisperModel(os.path.join("./models", model_name), device=device)
        save_as_one = self.save_as_one_var.get()

        # 如果保存为一个文件
        if save_as_one:
            result_file = os.path.join(self.save_dir, "transcription.txt")
            with open(result_file, "w", encoding="utf-8") as f:
                for file_path in self.files:
                    self.progress_text.insert(tk.END, f"正在转写 {file_path}...\n")
                    self.transcribe_file(file_path, model, f, language)
        else:
            # 每个文件保存为单独的txt文件
            for file_path in self.files:
                self.progress_text.insert(tk.END, f"正在转写 {file_path}...\n")
                result_file = os.path.join(self.save_dir, os.path.basename(file_path) + ".txt")
                with open(result_file, "w", encoding="utf-8") as f:
                    self.transcribe_file(file_path, model, f, language)

        self.progress_text.insert(tk.END, "转写完成！\n")

    def transcribe_file(self, file_path, model, file_obj, language):
        # 检查文件扩展名，确定是否需要提取音频
        video_formats = [".mp4", ".mov", ".avi", ".mkv"]
        audio_formats = [".mp3", ".wav"]

        if any(file_path.endswith(ext) for ext in video_formats):
            # 提取音频
            video = mp.VideoFileClip(file_path)
            audio_path = file_path.rsplit(".", 1)[0] + ".mp3"
            video.audio.write_audiofile(audio_path, codec='mp3')
        elif any(file_path.endswith(ext) for ext in audio_formats):
            audio_path = file_path
        else:
            self.progress_text.insert(tk.END, f"不支持的文件格式: {file_path}\n")
            return

        # 进行语音识别
        segments, info = model.transcribe(audio_path, language=language, condition_on_previous_text=False)
        for segment in segments:
            start_time = segment.start
            end_time = segment.end
            text = segment.text
            file_obj.write(f"[{start_time:.2f} - {end_time:.2f}]: {text}\n")

        # 删除临时音频文件
        if file_path.endswith(tuple(video_formats)):
            os.remove(audio_path)

# 启动应用
if __name__ == "__main__":
    root = tk.Tk()
    app = TranscribeApp(root)
    root.mainloop()
