import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
import sqlite3
import hashlib
from datetime import datetime

# --- 設定全域外觀 ---
ctk.set_appearance_mode("Light") # 改成淺色模式比較像網頁
ctk.set_default_color_theme("blue")

# 定義 Redmine 風格顏色
REDMINE_BLUE = "#3E5B76"
REDMINE_LIGHT_BLUE = "#628DB6"
HEADER_TEXT_COLOR = "white"

class RootApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 視窗基本設定
        self.title("MTD_Workplace - Redmine Style")
        self.geometry("1200x800")
        
        # 初始化資料庫
        self.init_db()
        self.current_user = None 

        # 顯示登入畫面
        self.show_login_screen()

    def init_db(self):
        self.conn = sqlite3.connect("redmine_lite.db")
        self.cursor = self.conn.cursor()
        
        # 1. 使用者表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT
            )
        ''')
        
        # 2. Issues 表 (擴充欄位以符合截圖)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracker TEXT,       -- Support / Bug
                subject TEXT,
                status TEXT,        -- New / In Progress...
                priority TEXT,
                assignee TEXT,      -- 指派給誰
                description TEXT,
                start_date TEXT,
                due_date TEXT,
                percent_done INTEGER,
                estimated_hours REAL,
                created_at TEXT,
                created_by TEXT
            )
        ''')
        
        # 3. Wiki 表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wiki (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                content TEXT,
                updated_by TEXT
            )
        ''')

        # 自動遷移資料庫 (防止舊資料報錯)
        columns_to_add = [
            ("tracker", "TEXT"), ("assignee", "TEXT"), ("start_date", "TEXT"),
            ("due_date", "TEXT"), ("percent_done", "INTEGER"), ("estimated_hours", "REAL"),
            ("created_by", "TEXT")
        ]
        for col_name, col_type in columns_to_add:
            try:
                self.cursor.execute(f"ALTER TABLE issues ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass 
        
        self.conn.commit()

    def show_login_screen(self):
        for widget in self.winfo_children(): widget.destroy()
        LoginFrame(self, self.conn)

    def show_main_app(self, username):
        for widget in self.winfo_children(): widget.destroy()
        self.current_user = username
        MainApp(self, self.conn, self.current_user)

# ============================
# 1. 登入畫面 (Login)
# ============================
class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, db_conn):
        super().__init__(master)
        self.master = master
        self.conn = db_conn
        self.cursor = self.conn.cursor()
        self.pack(fill="both", expand=True)
        
        # 背景色
        self.configure(fg_color="#f0f0f0")

        center_frame = ctk.CTkFrame(self, width=400, height=450, fg_color="white", corner_radius=10)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(center_frame, text="MTD_Workplace", font=("Arial", 28, "bold"), text_color=REDMINE_BLUE).pack(pady=(50, 10))
        ctk.CTkLabel(center_frame, text="Login to your account", font=("Arial", 14), text_color="gray").pack(pady=(0, 30))
        
        self.entry_user = ctk.CTkEntry(center_frame, width=280, height=40, placeholder_text="Username")
        self.entry_user.pack(pady=10)
        
        self.entry_pass = ctk.CTkEntry(center_frame, width=280, height=40, placeholder_text="Password", show="*")
        self.entry_pass.pack(pady=10)
        
        ctk.CTkButton(center_frame, text="Login", command=self.login, width=280, height=40, fg_color=REDMINE_BLUE, hover_color=REDMINE_LIGHT_BLUE).pack(pady=20)
        ctk.CTkButton(center_frame, text="Register", command=self.register_popup, width=280, fg_color="transparent", text_color=REDMINE_BLUE, border_width=1, border_color=REDMINE_BLUE).pack(pady=5)

    def login(self):
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest()
        
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user, hashed_pwd))
        if self.cursor.fetchone():
            self.master.show_main_app(user)
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def register_popup(self):
        dialog = ctk.CTkToplevel(self)
        dialog.geometry("300x350")
        dialog.title("Register")
        dialog.transient(self) # 讓視窗浮在上面
        
        ctk.CTkLabel(dialog, text="Create Account", font=("Arial", 18, "bold")).pack(pady=20)
        new_user = ctk.CTkEntry(dialog, placeholder_text="Username")
        new_user.pack(pady=10)
        new_pass = ctk.CTkEntry(dialog, placeholder_text="Password", show="*")
        new_pass.pack(pady=10)
        
        def save_user():
            u = new_user.get()
            p = new_pass.get()
            if not u or not p: return
            self.cursor.execute("SELECT * FROM users WHERE username=?", (u,))
            if self.cursor.fetchone():
                messagebox.showerror("Error", "User already exists")
                return
            self.cursor.execute("INSERT INTO users VALUES (?, ?)", (u, hashlib.sha256(p.encode()).hexdigest()))
            self.conn.commit()
            messagebox.showinfo("Success", "Account created!")
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Sign Up", command=save_user, fg_color=REDMINE_BLUE).pack(pady=20)

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
        self.configure(fg_color="#ffffff")

        # --- Top Header (藍色頂部) ---
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=REDMINE_BLUE)
        self.header.pack(fill="x", side="top")
        
        # 標題
        ctk.CTkLabel(self.header, text="MTD_Workplace", font=("Arial", 24, "bold"), text_color="white").pack(side="left", padx=20, pady=10)
        
        # 右上角資訊
        user_info = f"Logged in as {self.current_user} | My account | Sign out"
        logout_btn = ctk.CTkButton(self.header, text="Sign out", width=60, fg_color="transparent", text_color="white", command=self.master.show_login_screen)
        logout_btn.pack(side="right", padx=10)
        ctk.CTkLabel(self.header, text=f"Logged in as {self.current_user}", text_color="white").pack(side="right", padx=5)

        # --- Menu Tabs (導航列) ---
        self.menu_frame = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color=REDMINE_LIGHT_BLUE)
        self.menu_frame.pack(fill="x", side="top")
        
        self.tabs = ["Overview", "Activity", "Issues", "Wiki", "Files", "Settings"]
        for tab in self.tabs:
            btn = ctk.CTkButton(self.menu_frame, text=tab, width=80, fg_color="transparent", text_color="white", corner_radius=0, hover_color=REDMINE_BLUE,
                                command=lambda t=tab: self.switch_tab(t))
            btn.pack(side="left", padx=2)

        # --- 內容區 ---
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.current_frame = None
        self.switch_tab("Issues") # 預設顯示 Issues

    def switch_tab(self, tab_name):
        if self.current_frame:
            self.current_frame.destroy()
        
        if tab_name == "Issues":
            self.current_frame = IssuesView(self.content_area, self.conn, self.current_user)
        elif tab_name == "Wiki":
            self.current_frame = WikiView(self.content_area, self.conn, self.current_user)
        else:
            self.current_frame = ctk.CTkLabel(self.content_area, text=f"{tab_name} Page (Under Construction)", font=("Arial", 20))
            self.current_frame.pack(pady=50)

# ============================
# 3. Issues 列表視圖
# ============================
class IssuesView(ctk.CTkFrame):
    def __init__(self, master, conn, current_user):
        super().__init__(master, fg_color="transparent")
        self.conn = conn
        self.current_user = current_user
        self.pack(fill="both", expand=True)
        
        # 標題列
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(top_bar, text="Issues", font=("Arial", 24, "bold"), text_color="#333").pack(side="left")
        
        # 綠色 New Issue 按鈕
        ctk.CTkButton(top_bar, text="➕ New issue", fg_color="#4CAF50", width=100, command=self.open_new_issue_window).pack(side="right")

        # 篩選器 (裝飾用)
        filter_frame = ctk.CTkFrame(self, fg_color="#f5f5f5", border_width=1, border_color="#ddd")
        filter_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(filter_frame, text="☑ Status: open", text_color="black").pack(side="left", padx=10, pady=5)

        # --- Treeview 表格 ---
        # 定義欄位符合截圖
        self.columns = ("ID", "Tracker", "Status", "Subject", "Assignee", "% Done", "Created")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="black", rowheight=30, font=("Arial", 11))
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#eee")
        style.map('Treeview', background=[('selected', '#dcebf5')], foreground=[('selected', 'black')])

        self.tree = ttk.Treeview(self, columns=self.columns, show="headings", height=20)
        
        # 設定標題
        self.tree.heading("ID", text="#")
        self.tree.heading("Tracker", text="Tracker")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Subject", text="Subject")
        self.tree.heading("Assignee", text="Assignee")
        self.tree.heading("% Done", text="% Done")
        self.tree.heading("Created", text="Created")
        
        # 設定寬度
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Tracker", width=80)
        self.tree.column("Status", width=80)
        self.tree.column("Subject", width=400)
        self.tree.column("Assignee", width=120)
        self.tree.column("% Done", width=100)
        self.tree.column("Created", width=120)

        self.tree.pack(fill="both", expand=True)
        self.refresh_data()

    def refresh_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        cur = self.conn.cursor()
        cur.execute("SELECT id, tracker, status, subject, assignee, percent_done, created_at FROM issues ORDER BY id DESC")
        for row in cur.fetchall():
            # 加上 % 符號
            percent = f"{row[5]}%" if row[5] is not None else "0%"
            # 插入資料
            self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], percent, row[6]))

    def open_new_issue_window(self):
        # 開啟彈出視窗
        NewIssueWindow(self.master, self.conn, self.current_user, callback=self.refresh_data)

# ============================
# 4. 新增 Issue 彈出視窗 (重點修改)
# ============================
class NewIssueWindow(ctk.CTkToplevel):
    def __init__(self, master, conn, current_user, callback):
        super().__init__(master)
        self.conn = conn
        self.current_user = current_user
        self.callback = callback
        
        self.title("New issue - MTD_Workplace")
        self.geometry("900x750")
        self.configure(fg_color="#f8f8f8")
        
        # 讓視窗置頂
        self.transient(master)
        
        # 標題
        ctk.CTkLabel(self, text="New issue", font=("Arial", 22, "bold"), text_color="#333").pack(anchor="w", padx=20, pady=15)
        
        # --- 表單區域 ---
        form_frame = ctk.CTkFrame(self, fg_color="#fff", border_width=1, border_color="#ddd")
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # 欄位佈局 Grid
        # Tracker
        ctk.CTkLabel(form_frame, text="Tracker *", text_color="#333").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.tracker_cb = ctk.CTkComboBox(form_frame, values=["Support", "Bug", "Feature"])
        self.tracker_cb.grid(row=0, column=1, sticky="w", padx=10)
        
        # Subject
        ctk.CTkLabel(form_frame, text="Subject *", text_color="#333").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.subject_entry = ctk.CTkEntry(form_frame, width=500)
        self.subject_entry.grid(row=1, column=1, columnspan=3, sticky="w", padx=10)
        
        # Description
        ctk.CTkLabel(form_frame, text="Description", text_color="#333").grid(row=2, column=0, sticky="ne", padx=10, pady=10)
        self.desc_text = ctk.CTkTextbox(form_frame, width=500, height=150)
        self.desc_text.grid(row=2, column=1, columnspan=3, sticky="w", padx=10, pady=10)
        
        # --- 下半部屬性 (兩欄式) ---
        # Status
        ctk.CTkLabel(form_frame, text="Status *", text_color="#333").grid(row=3, column=0, sticky="e", padx=10, pady=5)
        self.status_cb = ctk.CTkComboBox(form_frame, values=["New", "In Progress", "Resolved", "Closed"])
        self.status_cb.grid(row=3, column=1, sticky="w", padx=10)
        
        # Start Date
        ctk.CTkLabel(form_frame, text="Start date", text_color="#333").grid(row=3, column=2, sticky="e", padx=10)
        self.start_date_entry = ctk.CTkEntry(form_frame, placeholder_text="YYYY-MM-DD")
        self.start_date_entry.grid(row=3, column=3, sticky="w", padx=10)
        
        # Priority
        ctk.CTkLabel(form_frame, text="Priority *", text_color="#333").grid(row=4, column=0, sticky="e", padx=10, pady=5)
        self.priority_cb = ctk.CTkComboBox(form_frame, values=["Normal", "High", "Urgent"])
        self.priority_cb.grid(row=4, column=1, sticky="w", padx=10)
        
        # Due Date
        ctk.CTkLabel(form_frame, text="Due date", text_color="#333").grid(row=4, column=2, sticky="e", padx=10)
        self.due_date_entry = ctk.CTkEntry(form_frame, placeholder_text="YYYY-MM-DD")
        self.due_date_entry.grid(row=4, column=3, sticky="w", padx=10)
        
        # Assignee
        ctk.CTkLabel(form_frame, text="Assignee", text_color="#333").grid(row=5, column=0, sticky="e", padx=10, pady=5)
        # 這裡撈取所有使用者
        users = [u[0] for u in self.conn.cursor().execute("SELECT username FROM users").fetchall()]
        self.assignee_cb = ctk.CTkComboBox(form_frame, values=users)
        self.assignee_cb.set(self.current_user) # 預設自己
        self.assignee_cb.grid(row=5, column=1, sticky="w", padx=10)
        
        # % Done
        ctk.CTkLabel(form_frame, text="% Done", text_color="#333").grid(row=5, column=2, sticky="e", padx=10)
        self.percent_cb = ctk.CTkComboBox(form_frame, values=["0", "10", "20", "50", "80", "100"])
        self.percent_cb.grid(row=5, column=3, sticky="w", padx=10)

        # Estimated Time
        ctk.CTkLabel(form_frame, text="Estimated time", text_color="#333").grid(row=6, column=2, sticky="e", padx=10)
        self.hours_entry = ctk.CTkEntry(form_frame, placeholder_text="Hours")
        self.hours_entry.grid(row=6, column=3, sticky="w", padx=10)
        
        # 底部按鈕
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Create", command=self.save_issue, fg_color=REDMINE_BLUE).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Create and continue", command=lambda: self.save_issue(close=False), fg_color="transparent", border_width=1, border_color="#ccc", text_color="#333").pack(side="left", padx=10)

    def save_issue(self, close=True):
        tracker = self.tracker_cb.get()
        subject = self.subject_entry.get()
        if not subject:
            messagebox.showwarning("Warning", "Subject cannot be empty")
            return
            
        data = (
            tracker,
            subject,
            self.status_cb.get(),
            self.priority_cb.get(),
            self.assignee_cb.get(),
            self.desc_text.get("0.0", "end"),
            self.start_date_entry.get(),
            self.due_date_entry.get(),
            int(self.percent_cb.get()),
            self.hours_entry.get() or 0,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            self.current_user
        )
        
        self.conn.cursor().execute('''
            INSERT INTO issues (tracker, subject, status, priority, assignee, description, 
            start_date, due_date, percent_done, estimated_hours, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        self.conn.commit()
        
        # 通知主視窗更新
        self.callback()
        
        if close:
            self.destroy()
        else:
            # 清空欄位繼續新增
            self.subject_entry.delete(0, "end")
            self.desc_text.delete("0.0", "end")
            messagebox.showinfo("Created", "Issue created successfully.")

# ============================
# 5. Wiki 視圖 (閱讀模式)
# ============================
class WikiView(ctk.CTkFrame):
    def __init__(self, master, conn, current_user):
        super().__init__(master, fg_color="transparent")
        self.conn = conn
        self.current_user = current_user
        self.pack(fill="both", expand=True)
        
        # 頂部工具列
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(top_bar, text="AE Tool", font=("Arial", 24, "bold"), text_color="#333").pack(side="left")
        
        # 工具按鈕 (New, Edit, Watch...)
        tools = ["New wiki page", "Edit", "Watch", "Lock", "Rename", "Delete", "History"]
        for t in tools:
            icon = "✏️" if t == "Edit" else "➕" if t.startswith("New") else ""
            btn = ctk.CTkButton(top_bar, text=f"{icon} {t}", width=60, fg_color="transparent", text_color="#555", hover_color="#eee",
                                command=lambda x=t: self.handle_tool(x))
            btn.pack(side="left", padx=2)

        # 內容區 (Split View: 左邊內容, 右邊索引)
        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.pack(fill="both", expand=True)
        
        # 左：內容顯示 (模擬網頁文字)
        self.content_text = ctk.CTkTextbox(split_frame, width=800, fg_color="white", text_color="#333", font=("Arial", 14))
        self.content_text.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # 右：索引 (Sidebar)
        sidebar = ctk.CTkFrame(split_frame, width=200, fg_color="#fcfcfc")
        sidebar.pack(side="right", fill="y")
        ctk.CTkLabel(sidebar, text="Wiki", font=("Arial", 14, "bold"), text_color="#333").pack(anchor="w", padx=10, pady=10)
        
        links = ["Start page", "Index by title", "Index by date"]
        for l in links:
            ctk.CTkLabel(sidebar, text=l, text_color=REDMINE_BLUE, cursor="hand2").pack(anchor="w", padx=10, pady=2)
            
        self.load_wiki_content()

    def load_wiki_content(self):
        # 預設載入第一篇 Wiki，如果沒有就顯示範例
        cur = self.conn.cursor()
        cur.execute("SELECT content FROM wiki LIMIT 1")
        row = cur.fetchone()
        
        self.content_text.configure(state="normal")
        if row:
            self.content_text.insert("0.0", row[0])
        else:
            # 顯示類似截圖的範例文字
            example_text = """Description:
In this page will list most of the tool that AE team need.
Adding to be continued....... be maintained by: Charlie......2024.06.05

--------------------------------------------------------------------------------
Formal Working Flow:
[Issue Flow]
    • Item for KUS Group / Product Introduction

1. Presentation Material
................for all the materials as business promotion.

--------------------------------------------------------------------------------
    • Item for Service Tool

1. Service Tool Execution
................for Service Tool guiding including connect setting.
2. Modify White Box Firmware
................for tutorial of how to use service tool to modify white box firmware vesrion.
"""
            self.content_text.insert("0.0", example_text)
        self.content_text.configure(state="disabled") # 閱讀模式不可編輯

    def handle_tool(self, tool_name):
        if tool_name == "Edit":
            # 切換成可編輯模式 (簡單實作)
            self.content_text.configure(state="normal")
            self.content_text.focus()
            messagebox.showinfo("Edit Mode", "You can now edit the text directly. (Save feature to be added)")

if __name__ == "__main__":
    app = RootApp()
    app.mainloop()