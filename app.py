import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
import sqlite3
from datetime import datetime

# --- 設定外觀 ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MiniRedmine(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. 初始化視窗
        self.title("Mini Redmine - 研發專案管理")
        self.geometry("1100x700")

        # 2. 初始化資料庫
        self.init_db()

        # 3. 版面配置 (Grid)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 左側選單 (Sidebar) ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo = ctk.CTkLabel(self.sidebar, text="REDMINE\nLITE", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.pack(pady=30)

        self.btn_issues = ctk.CTkButton(self.sidebar, text="📋 問題追蹤 (Issues)", command=self.show_issues_frame)
        self.btn_issues.pack(pady=10, padx=20, fill="x")

        self.btn_wiki = ctk.CTkButton(self.sidebar, text="📚 知識庫 (Wiki)", command=self.show_wiki_frame)
        self.btn_wiki.pack(pady=10, padx=20, fill="x")
        
        # --- 右側主畫面區 ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew")

        # 建立兩個分頁 Frame
        self.frame_issues = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frame_wiki = ctk.CTkFrame(self.main_area, fg_color="transparent")

        # 預設先建立介面
        self.setup_issues_ui()
        self.setup_wiki_ui()

        # 預設顯示 Issues
        self.show_issues_frame()

    # ==========================
    # 資料庫邏輯 (SQLite)
    # ==========================
    def init_db(self):
        self.conn = sqlite3.connect("redmine_lite.db")
        self.cursor = self.conn.cursor()
        
        # 建立 Issues 表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                status TEXT,
                priority TEXT,
                description TEXT,
                created_at TEXT
            )
        ''')
        
        # 建立 Wiki 表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wiki (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                content TEXT
            )
        ''')
        self.conn.commit()

    # ==========================
    # 畫面切換邏輯
    # ==========================
    def show_issues_frame(self):
        self.frame_wiki.pack_forget()
        self.frame_issues.pack(fill="both", expand=True)
        self.refresh_issue_list()

    def show_wiki_frame(self):
        self.frame_issues.pack_forget()
        self.frame_wiki.pack(fill="both", expand=True)
        self.refresh_wiki_list()

    # ==========================
    # 功能 1: Issues (問題追蹤)
    # ==========================
    def setup_issues_ui(self):
        # 標題
        ctk.CTkLabel(self.frame_issues, text="問題列表 (Issue List)", font=("Arial", 20, "bold")).pack(pady=10, padx=20, anchor="w")

        # 上半部：列表 (Treeview) - 需設定 Style 讓它在深色模式好看一點
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])

        columns = ("ID", "狀態", "優先級", "主旨", "建立時間")
        self.tree_issues = ttk.Treeview(self.frame_issues, columns=columns, show="headings", height=10)
        
        # 設定欄寬與標題
        self.tree_issues.heading("ID", text="ID"); self.tree_issues.column("ID", width=50, anchor="center")
        self.tree_issues.heading("狀態", text="狀態"); self.tree_issues.column("狀態", width=80, anchor="center")
        self.tree_issues.heading("優先級", text="優先級"); self.tree_issues.column("優先級", width=80, anchor="center")
        self.tree_issues.heading("主旨", text="主旨"); self.tree_issues.column("主旨", width=400)
        self.tree_issues.heading("建立時間", text="建立時間"); self.tree_issues.column("建立時間", width=150, anchor="center")
        
        self.tree_issues.pack(padx=20, fill="x")
        self.tree_issues.bind("<<TreeviewSelect>>", self.on_issue_select)

        # 下半部：新增/編輯區
        self.issue_detail_frame = ctk.CTkFrame(self.frame_issues)
        self.issue_detail_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # 輸入欄位
        f1 = ctk.CTkFrame(self.issue_detail_frame, fg_color="transparent")
        f1.pack(fill="x", pady=5)
        
        ctk.CTkLabel(f1, text="主旨:").pack(side="left", padx=5)
        self.entry_subject = ctk.CTkEntry(f1, width=400)
        self.entry_subject.pack(side="left", padx=5)
        
        ctk.CTkLabel(f1, text="狀態:").pack(side="left", padx=5)
        self.combo_status = ctk.CTkComboBox(f1, values=["New", "In Progress", "Resolved", "Closed"], width=120)
        self.combo_status.pack(side="left", padx=5)
        
        ctk.CTkLabel(f1, text="優先級:").pack(side="left", padx=5)
        self.combo_priority = ctk.CTkComboBox(f1, values=["Normal", "High", "Urgent"], width=120)
        self.combo_priority.pack(side="left", padx=5)

        ctk.CTkLabel(self.issue_detail_frame, text="詳細描述:").pack(anchor="w", padx=5)
        self.text_description = ctk.CTkTextbox(self.issue_detail_frame, height=150)
        self.text_description.pack(fill="both", expand=True, padx=5, pady=5)

        # 按鈕區
        btn_frame = ctk.CTkFrame(self.issue_detail_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(btn_frame, text="➕ 新增 Issue", command=self.add_issue, fg_color="green").pack(side="right", padx=10)
        ctk.CTkButton(btn_frame, text="💾 更新選取項目", command=self.update_issue).pack(side="right", padx=10)
        ctk.CTkButton(btn_frame, text="🧹 清空欄位", command=self.clear_issue_form, fg_color="gray").pack(side="right", padx=10)

    def refresh_issue_list(self):
        for item in self.tree_issues.get_children():
            self.tree_issues.delete(item)
        
        self.cursor.execute("SELECT * FROM issues ORDER BY id DESC")
        rows = self.cursor.fetchall()
        for row in rows:
            self.tree_issues.insert("", "end", values=(row[0], row[2], row[3], row[1], row[5]))

    def add_issue(self):
        subject = self.entry_subject.get()
        status = self.combo_status.get()
        priority = self.combo_priority.get()
        desc = self.text_description.get("0.0", "end")
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        if not subject:
            return

        self.cursor.execute("INSERT INTO issues (subject, status, priority, description, created_at) VALUES (?, ?, ?, ?, ?)",
                            (subject, status, priority, desc, time_str))
        self.conn.commit()
        self.refresh_issue_list()
        self.clear_issue_form()

    def on_issue_select(self, event):
        selected = self.tree_issues.selection()
        if selected:
            item = self.tree_issues.item(selected[0])
            issue_id = item['values'][0]
            
            self.cursor.execute("SELECT * FROM issues WHERE id=?", (issue_id,))
            data = self.cursor.fetchone()
            if data:
                self.entry_subject.delete(0, "end"); self.entry_subject.insert(0, data[1])
                self.combo_status.set(data[2])
                self.combo_priority.set(data[3])
                self.text_description.delete("0.0", "end"); self.text_description.insert("0.0", data[4])

    def update_issue(self):
        selected = self.tree_issues.selection()
        if not selected:
            return
        issue_id = self.tree_issues.item(selected[0])['values'][0]
        
        self.cursor.execute('''
            UPDATE issues SET subject=?, status=?, priority=?, description=? WHERE id=?
        ''', (self.entry_subject.get(), self.combo_status.get(), self.combo_priority.get(), self.text_description.get("0.0", "end"), issue_id))
        self.conn.commit()
        self.refresh_issue_list()

    def clear_issue_form(self):
        self.entry_subject.delete(0, "end")
        self.text_description.delete("0.0", "end")
        # 清除選取狀態
        if self.tree_issues.selection():
            self.tree_issues.selection_remove(self.tree_issues.selection()[0])

    # ==========================
    # 功能 2: Wiki (知識庫)
    # ==========================
    def setup_wiki_ui(self):
        ctk.CTkLabel(self.frame_wiki, text="研發知識庫 (Wiki)", font=("Arial", 20, "bold")).pack(pady=10, padx=20, anchor="w")

        # 左右佈局
        paned = tk.PanedWindow(self.frame_wiki, orient="horizontal", sashwidth=5, bg="#2b2b2b")
        paned.pack(fill="both", expand=True, padx=20, pady=10)

        # 左：頁面列表
        left_frame = ctk.CTkFrame(paned, width=250)
        paned.add(left_frame)

        ctk.CTkLabel(left_frame, text="頁面列表").pack(pady=5)
        
        self.wiki_listbox = tk.Listbox(left_frame, bg="#333", fg="white", font=("Arial", 12), borderwidth=0, selectbackground="#1f538d")
        self.wiki_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.wiki_listbox.bind("<<ListboxSelect>>", self.on_wiki_select)
        
        self.entry_wiki_title = ctk.CTkEntry(left_frame, placeholder_text="輸入新頁面標題...")
        self.entry_wiki_title.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(left_frame, text="➕ 建立新頁面", command=self.add_wiki_page).pack(fill="x", padx=5, pady=5)

        # 右：編輯區
        right_frame = ctk.CTkFrame(paned)
        paned.add(right_frame)

        self.lbl_wiki_current = ctk.CTkLabel(right_frame, text="請選擇或建立頁面", font=("Arial", 16, "bold"))
        self.lbl_wiki_current.pack(pady=10, anchor="w", padx=10)

        self.text_wiki_content = ctk.CTkTextbox(right_frame, font=("Arial", 14))
        self.text_wiki_content.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkButton(right_frame, text="💾 儲存內容 (Save)", command=self.save_wiki_content, fg_color="green").pack(anchor="e", padx=10, pady=10)

    def refresh_wiki_list(self):
        self.wiki_listbox.delete(0, "end")
        self.cursor.execute("SELECT title FROM wiki")
        for row in self.cursor.fetchall():
            self.wiki_listbox.insert("end", row[0])

    def add_wiki_page(self):
        title = self.entry_wiki_title.get()
        if not title: return
        try:
            self.cursor.execute("INSERT INTO wiki (title, content) VALUES (?, ?)", (title, ""))
            self.conn.commit()
            self.refresh_wiki_list()
            self.entry_wiki_title.delete(0, "end")
        except sqlite3.IntegrityError:
            messagebox.showerror("錯誤", "該頁面標題已存在")

    def on_wiki_select(self, event):
        selection = self.wiki_listbox.curselection()
        if selection:
            title = self.wiki_listbox.get(selection[0])
            self.lbl_wiki_current.configure(text=title)
            
            self.cursor.execute("SELECT content FROM wiki WHERE title=?", (title,))
            data = self.cursor.fetchone()
            if data:
                self.text_wiki_content.delete("0.0", "end")
                self.text_wiki_content.insert("0.0", data[0])

    def save_wiki_content(self):
        title = self.lbl_wiki_current.cget("text")
        if title == "請選擇或建立頁面": return
        
        content = self.text_wiki_content.get("0.0", "end")
        self.cursor.execute("UPDATE wiki SET content=? WHERE title=?", (content, title))
        self.conn.commit()
        messagebox.showinfo("成功", "Wiki 內容已儲存！")

if __name__ == "__main__":
    app = MiniRedmine()
    app.mainloop()