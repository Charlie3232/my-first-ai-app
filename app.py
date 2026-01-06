import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
import sqlite3
import hashlib # 用來加密密碼
from datetime import datetime

# --- 設定外觀 ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RootApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 視窗基本設定
        self.title("研發知識庫系統 (Knowledge Database)")
        self.geometry("1100x700")
        
        # 初始化資料庫 (含自動升級)
        self.init_db()
        self.current_user = None # 紀錄現在是誰登入

        # 這裡決定一開始顯示什麼畫面
        self.show_login_screen()

    def init_db(self):
        self.conn = sqlite3.connect("redmine_lite.db")
        self.cursor = self.conn.cursor()
        
        # 1. 建立使用者表 (Users)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT
            )
        ''')
        
        # 2. 建立 Issues 表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                status TEXT,
                priority TEXT,
                description TEXT,
                created_at TEXT,
                created_by TEXT  -- 新增：紀錄是誰建立的
            )
        ''')
        
        # 3. 建立 Wiki 表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wiki (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                content TEXT,
                updated_by TEXT -- 新增：紀錄最後修改人
            )
        ''')

        # --- 資料庫遷移 (Migration) ---
        # 怕你之前的資料庫沒有 create_by 欄位，這裡檢查並自動補上，以免報錯
        try:
            self.cursor.execute("ALTER TABLE issues ADD COLUMN created_by TEXT")
        except sqlite3.OperationalError:
            pass # 代表欄位已經存在，忽略錯誤
            
        try:
            self.cursor.execute("ALTER TABLE wiki ADD COLUMN updated_by TEXT")
        except sqlite3.OperationalError:
            pass 

        self.conn.commit()

    # ============================
    # 畫面路由 (Router)
    # ============================
    def show_login_screen(self):
        # 清空視窗上的舊東西
        for widget in self.winfo_children():
            widget.destroy()
            
        LoginFrame(self, self.conn)

    def show_main_app(self, username):
        # 清空視窗上的舊東西
        for widget in self.winfo_children():
            widget.destroy()
            
        self.current_user = username
        MainApp(self, self.conn, self.current_user)


# ============================
# 1. 登入畫面 (Login Frame)
# ============================
class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, db_conn):
        super().__init__(master)
        self.master = master
        self.conn = db_conn
        self.cursor = self.conn.cursor()
        
        self.pack(fill="both", expand=True)
        
        # 介面置中容器
        self.center_frame = ctk.CTkFrame(self, width=400, height=500)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # 標題與作者
        ctk.CTkLabel(self.center_frame, text="Knowledge Database", font=("Arial", 32, "bold")).pack(pady=(50, 10))
        ctk.CTkLabel(self.center_frame, text="Author: Charlie", font=("Arial", 14), text_color="gray").pack(pady=(0, 40))
        
        # 輸入框
        self.entry_user = ctk.CTkEntry(self.center_frame, width=250, placeholder_text="使用者名稱 (Username)")
        self.entry_user.pack(pady=10)
        
        self.entry_pass = ctk.CTkEntry(self.center_frame, width=250, placeholder_text="密碼 (Password)", show="*")
        self.entry_pass.pack(pady=10)
        
        # 按鈕
        ctk.CTkButton(self.center_frame, text="登入 (Login)", command=self.login, width=250, height=40).pack(pady=20)
        ctk.CTkButton(self.center_frame, text="建立新帳號 (Register)", command=self.register_popup, width=250, fg_color="transparent", border_width=1).pack(pady=10)

    def login(self):
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        
        # 簡單加密檢查 (SHA256)
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest()
        
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user, hashed_pwd))
        if self.cursor.fetchone():
            # 登入成功，切換到主畫面
            self.master.show_main_app(user)
        else:
            messagebox.showerror("錯誤", "帳號或密碼錯誤！")

    def register_popup(self):
        # 彈出註冊視窗
        dialog = ctk.CTkToplevel(self)
        dialog.geometry("300x300")
        dialog.title("註冊")
        
        ctk.CTkLabel(dialog, text="設定使用者名稱").pack(pady=10)
        new_user = ctk.CTkEntry(dialog)
        new_user.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="設定密碼").pack(pady=10)
        new_pass = ctk.CTkEntry(dialog, show="*")
        new_pass.pack(pady=5)
        
        def save_user():
            u = new_user.get()
            p = new_pass.get()
            if not u or not p:
                return
            
            # 檢查帳號是否重複
            self.cursor.execute("SELECT * FROM users WHERE username=?", (u,))
            if self.cursor.fetchone():
                messagebox.showerror("錯誤", "此帳號已存在")
                return
            
            # 存入資料庫
            hashed_p = hashlib.sha256(p.encode()).hexdigest()
            self.cursor.execute("INSERT INTO users VALUES (?, ?)", (u, hashed_p))
            self.conn.commit()
            messagebox.showinfo("成功", "帳號建立成功，請登入！")
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="確認建立", command=save_user).pack(pady=20)


# ============================
# 2. 主程式畫面 (Main App)
# ============================
class MainApp(ctk.CTkFrame):
    def __init__(self, master, db_conn, current_user):
        super().__init__(master)
        self.master = master
        self.conn = db_conn
        self.cursor = self.conn.cursor()
        self.current_user = current_user
        
        self.pack(fill="both", expand=True)

        # --- 佈局 ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左側選單
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 顯示歡迎詞
        ctk.CTkLabel(self.sidebar, text=f"Welcome,\n{self.current_user}", font=("Arial", 18, "bold")).pack(pady=30)
        
        self.btn_issues = ctk.CTkButton(self.sidebar, text="📋 問題追蹤 (Issues)", command=self.show_issues)
        self.btn_issues.pack(pady=10, padx=20, fill="x")
        
        self.btn_wiki = ctk.CTkButton(self.sidebar, text="📚 知識庫 (Wiki)", command=self.show_wiki)
        self.btn_wiki.pack(pady=10, padx=20, fill="x")

        # 登出按鈕
        ctk.CTkButton(self.sidebar, text="🚪 登出", command=self.master.show_login_screen, fg_color="#c0392b").pack(side="bottom", pady=20, padx=20, fill="x")

        # 右側內容區
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        
        self.frame_issues = None
        self.frame_wiki = None
        
        # 預設顯示 Issues
        self.show_issues()

    def show_issues(self):
        if self.frame_wiki: self.frame_wiki.pack_forget()
        if not self.frame_issues: self.setup_issues_ui()
        self.frame_issues.pack(fill="both", expand=True)
        self.refresh_issue_list()

    def show_wiki(self):
        if self.frame_issues: self.frame_issues.pack_forget()
        if not self.frame_wiki: self.setup_wiki_ui()
        self.frame_wiki.pack(fill="both", expand=True)
        self.refresh_wiki_list()

    # --- Issues UI ---
    def setup_issues_ui(self):
        self.frame_issues = ctk.CTkFrame(self.content_area, fg_color="transparent")
        ctk.CTkLabel(self.frame_issues, text="問題追蹤清單", font=("Arial", 20, "bold")).pack(pady=10, padx=20, anchor="w")

        # Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])

        cols = ("ID", "狀態", "優先級", "主旨", "建立者", "時間")
        self.tree_issues = ttk.Treeview(self.frame_issues, columns=cols, show="headings", height=8)
        
        for c in cols: self.tree_issues.heading(c, text=c)
        self.tree_issues.column("ID", width=40); self.tree_issues.column("狀態", width=80)
        self.tree_issues.column("建立者", width=100); self.tree_issues.column("主旨", width=300)
        
        self.tree_issues.pack(padx=20, fill="x")
        self.tree_issues.bind("<<TreeviewSelect>>", self.on_issue_select)

        # 編輯區
        self.detail_frame = ctk.CTkFrame(self.frame_issues)
        self.detail_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        f1 = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        f1.pack(fill="x", pady=5)
        
        self.entry_subject = ctk.CTkEntry(f1, placeholder_text="主旨", width=300); self.entry_subject.pack(side="left", padx=5)
        self.combo_status = ctk.CTkComboBox(f1, values=["New", "Processing", "Done"], width=100); self.combo_status.pack(side="left", padx=5)
        self.combo_priority = ctk.CTkComboBox(f1, values=["Normal", "Urgent"], width=100); self.combo_priority.pack(side="left", padx=5)

        self.text_desc = ctk.CTkTextbox(self.detail_frame, height=100)
        self.text_desc.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkButton(self.detail_frame, text="新增 Issue", command=self.add_issue, fg_color="green").pack(side="right", padx=10, pady=5)

    def refresh_issue_list(self):
        for i in self.tree_issues.get_children(): self.tree_issues.delete(i)
        self.cursor.execute("SELECT id, status, priority, subject, created_by, created_at, description FROM issues ORDER BY id DESC")
        for row in self.cursor.fetchall():
            # row: (id, status, priority, subject, created_by, created_at, desc)
            self.tree_issues.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], row[5]))

    def add_issue(self):
        sub = self.entry_subject.get()
        if not sub: return
        
        # 這裡會把 self.current_user (登入者) 寫進資料庫
        self.cursor.execute("INSERT INTO issues (subject, status, priority, description, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                            (sub, self.combo_status.get(), self.combo_priority.get(), self.text_desc.get("0.0", "end"), 
                             datetime.now().strftime("%Y-%m-%d %H:%M"), self.current_user))
        self.conn.commit()
        self.refresh_issue_list()
        self.entry_subject.delete(0, "end"); self.text_desc.delete("0.0", "end")

    def on_issue_select(self, event):
        sel = self.tree_issues.selection()
        if sel:
            item = self.tree_issues.item(sel[0])
            idx = item['values'][0]
            self.cursor.execute("SELECT * FROM issues WHERE id=?", (idx,))
            data = self.cursor.fetchone()
            if data:
                # 簡單回填 (實際專案可以做得更細)
                self.text_desc.delete("0.0", "end")
                self.text_desc.insert("0.0", f"建立者: {data[6]}\n內容: {data[4]}")

    # --- Wiki UI ---
    def setup_wiki_ui(self):
        self.frame_wiki = ctk.CTkFrame(self.content_area, fg_color="transparent")
        ctk.CTkLabel(self.frame_wiki, text="Wiki 知識庫", font=("Arial", 20, "bold")).pack(pady=10, padx=20, anchor="w")
        
        paned = tk.PanedWindow(self.frame_wiki, orient="horizontal", bg="#2b2b2b")
        paned.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left List
        self.wiki_list = tk.Listbox(paned, bg="#333", fg="white", borderwidth=0)
        paned.add(self.wiki_list, width=200)
        self.wiki_list.bind("<<ListboxSelect>>", self.load_wiki)
        
        # Right Edit
        right = ctk.CTkFrame(paned)
        paned.add(right)
        
        f_top = ctk.CTkFrame(right)
        f_top.pack(fill="x")
        self.entry_wiki_title = ctk.CTkEntry(f_top, placeholder_text="頁面標題")
        self.entry_wiki_title.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(f_top, text="儲存 / 新增", command=self.save_wiki).pack(side="right", padx=5)
        
        self.text_wiki = ctk.CTkTextbox(right)
        self.text_wiki.pack(fill="both", expand=True, pady=5)

    def refresh_wiki_list(self):
        self.wiki_list.delete(0, "end")
        self.cursor.execute("SELECT title FROM wiki")
        for r in self.cursor.fetchall(): self.wiki_list.insert("end", r[0])

    def save_wiki(self):
        title = self.entry_wiki_title.get()
        content = self.text_wiki.get("0.0", "end")
        if not title: return
        
        # 嘗試更新，如果沒有就新增 (Upsert 邏輯)
        self.cursor.execute("SELECT * FROM wiki WHERE title=?", (title,))
        if self.cursor.fetchone():
            self.cursor.execute("UPDATE wiki SET content=?, updated_by=? WHERE title=?", (content, self.current_user, title))
        else:
            self.cursor.execute("INSERT INTO wiki (title, content, updated_by) VALUES (?, ?, ?)", (title, content, self.current_user))
        self.conn.commit()
        messagebox.showinfo("成功", "Wiki 已儲存")
        self.refresh_wiki_list()

    def load_wiki(self, event):
        sel = self.wiki_list.curselection()
        if sel:
            title = self.wiki_list.get(sel[0])
            self.cursor.execute("SELECT * FROM wiki WHERE title=?", (title,))
            data = self.cursor.fetchone() # (id, title, content, updated_by)
            if data:
                self.entry_wiki_title.delete(0, "end"); self.entry_wiki_title.insert(0, data[1])
                self.text_wiki.delete("0.0", "end"); self.text_wiki.insert("0.0", data[2])


if __name__ == "__main__":
    app = RootApp()
    app.mainloop()