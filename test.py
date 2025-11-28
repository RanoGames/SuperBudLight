# local_messenger.py
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import socket
import threading
import sys

class MessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Локальный мессенджер")
        self.root.geometry("500x500")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Сетевые переменные
        self.sock = None
        self.conn = None
        self.is_server = None
        self.running = False

        # Основной интерфейс
        self.chat_area = scrolledtext.ScrolledText(root, state='disabled', wrap='word')
        self.chat_area.pack(padx=10, pady=10, fill='both', expand=True)

        self.input_frame = tk.Frame(root)
        self.input_frame.pack(padx=10, pady=(0, 10), fill='x')

        self.message_entry = tk.Entry(self.input_frame, font=("Arial", 12))
        self.message_holder = tk.StringVar()
        self.message_entry.config(textvariable=self.message_holder)
        self.message_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.input_frame, text="Отправить", command=self.send_message)
        self.send_button.pack(side='right')

        # Выбор роли
        self.choose_role()

    def choose_role(self):
        role = simpledialog.askstring("Роль", "Введите 'server' или 'client':")
        if not role:
            self.root.quit()
            return

        role = role.strip().lower()
        if role == "server":
            self.start_as_server()
        elif role == "client":
            self.start_as_client()
        else:
            messagebox.showerror("Ошибка", "Введите 'server' или 'client'")
            self.choose_role()

    def start_as_server(self):
        self.is_server = True
        self.add_message("[Система] Ожидание подключения...")
        threading.Thread(target=self.run_server, daemon=True).start()

    def start_as_client(self):
        self.is_server = False
        server_ip = simpledialog.askstring("IP сервера", "Введите IP-адрес сервера:")
        if not server_ip:
            self.root.quit()
            return
        self.add_message(f"[Система] Подключение к {server_ip}...")
        threading.Thread(target=self.run_client, args=(server_ip,), daemon=True).start()

    def run_server(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', 12345))
                s.listen()
                self.sock = s
                self.running = True
                conn, addr = s.accept()
                self.conn = conn
                self.add_message(f"[Система] Подключён: {addr}")

                while self.running:
                    try:
                        data = conn.recv(1024)
                        if not data:
                            break
                        msg = data.decode('utf-8')
                        self.add_message(f"Друг: {msg}")
                    except ConnectionAbortedError:
                        break
        except Exception as e:
            if self.running:
                self.add_message(f"[Ошибка] Сервер: {e}")

    def run_client(self, server_ip):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((server_ip, 12345))
            self.sock = s
            self.conn = s
            self.running = True
            self.add_message("[Система] Подключено!")

            while self.running:
                try:
                    data = s.recv(1024)
                    if not data:
                        break
                    msg = data.decode('utf-8')
                    self.add_message(f"Друг: {msg}")
                except ConnectionAbortedError:
                    break
        except Exception as e:
            if self.running:
                self.add_message(f"[Ошибка] Клиент: {e}")

    def send_message(self, event=None):
        if not self.conn or not self.running:
            messagebox.showwarning("Ошибка", "Нет подключения!")
            return

        msg = self.message_holder.get().strip()
        if not msg:
            return

        try:
            self.conn.sendall(msg.encode('utf-8'))
            self.add_message(f"Ты: {msg}")
            self.message_holder.set("")
        except Exception as e:
            self.add_message(f"[Ошибка отправки] {e}")

    def add_message(self, text):
        self.chat_area.config(state='normal')
        self.chat_area.insert('end', text + '\n')
        self.chat_area.config(state='disabled')
        self.chat_area.yview('end')  # Прокрутка вниз

    def on_closing(self):
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MessengerApp(root)
    root.mainloop()