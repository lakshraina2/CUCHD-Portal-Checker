import tkinter as tk
from tkinter import ttk, messagebox
import threading
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import io
import time
import traceback # Import traceback for detailed error logging

class CUCHDPortalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CUCHD Student Portal Checker")
        self.root.geometry("1500x800")
        self.root.resizable(False, False)
        self.driver = None

        # Apply a ttk theme for better aesthetics
        self.style = ttk.Style()
        self.style.theme_use('clam') # 'clam', 'alt', 'default', 'classic' are common options

        # Configure some common styles
        self.style.configure('TLabel', font=('Helvetica', 10))
        self.style.configure('TButton', font=('Helvetica', 10, 'bold'))
        self.style.configure('TEntry', font=('Helvetica', 10))
        self.style.configure('TLabelframe.Label', font=('Helvetica', 12, 'bold')) # For section titles

        # Main title for the application (optional, but adds visual appeal)
        self.title_label = ttk.Label(root, text="CUCHD Student Portal Utilities", font=('Helvetica', 16, 'bold'))
        self.title_label.pack(pady=10)

        # Login Frame
        credentials_frame = ttk.LabelFrame(root, text="Login Credentials")
        credentials_frame.pack(fill="x", padx=15, pady=(0, 10)) # Increased padding

        ttk.Label(credentials_frame, text="UID/Username:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.uid_entry = ttk.Entry(credentials_frame, width=40)
        self.uid_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ttk.Label(credentials_frame, text="Password:").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.pwd_entry = ttk.Entry(credentials_frame, show="*", width=40)
        self.pwd_entry.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        # Make columns expandable within credentials_frame
        credentials_frame.grid_columnconfigure(1, weight=1)
        credentials_frame.grid_columnconfigure(3, weight=1)


        # Buttons
        button_frame = ttk.Frame(root)
        button_frame.pack(fill="x", padx=15, pady=(5, 10)) # Increased padding

        self.login_btn = ttk.Button(button_frame, text="Login & Fetch Data", width=25, command=self.start_full_fetch)
        self.login_btn.pack(side="left", padx=(0, 5), expand=True) # Aligned left
        self.clear_btn = ttk.Button(button_frame, text="Clear Data", width=25, command=self.clear_data)
        self.clear_btn.pack(side="right", padx=(5, 0), expand=True) # Aligned right


        # Activity Log
        log_frame = ttk.LabelFrame(root, text="Activity Log")
        log_frame.pack(fill="both", expand=False, padx=15, pady=10) # Increased padding
        self.activity_log = tk.Text(log_frame, height=8, wrap="word", font=('Helvetica', 9)) # Slightly smaller font for log
        self.activity_log.pack(fill="both", expand=True, padx=5, pady=5) # Padding inside log frame
        self.log("GUI Initialized. Please login to continue.")

        # Data Tabs
        data_frame = ttk.LabelFrame(root, text="Fetched Data")
        data_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15)) # Increased padding
        self.notebook = ttk.Notebook(data_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5) # Padding inside data frame

        self.attendance_tab = ttk.Frame(self.notebook)
        self.attendance_table = self.create_table(self.attendance_tab)
        self.notebook.add(self.attendance_tab, text="Attendance")

        self.marks_tab = ttk.Frame(self.notebook)
        self.marks_table = self.create_table(self.marks_tab)
        self.notebook.add(self.marks_tab, text="Marks")

        self.timetable_tab = ttk.Frame(self.notebook)
        self.timetable_table = self.create_table(self.timetable_tab)
        self.notebook.add(self.timetable_tab, text="Timetable")

        # Marks Calculator Tab
        self.calculator_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.calculator_tab, text="Marks Calculator")
        self.setup_calculator_tab()


    # Moved methods to be defined immediately after __init__ to resolve AttributeError
    def start_full_fetch(self):
        uid = self.uid_entry.get().strip()
        pwd = self.pwd_entry.get().strip()
        if not uid or not pwd:
            messagebox.showerror("Input Error", "Please enter both UID and Password.")
            return
        threading.Thread(target=self.full_fetch, args=(uid, pwd), daemon=True).start()

    def get_captcha_input_gui(self, image_data):
        root = tk.Toplevel()
        root.title("Enter Captcha")
        root.geometry("300x200")
        root.attributes("-topmost", True)
        captcha_var = tk.StringVar()

        image = Image.open(io.BytesIO(image_data))
        photo = ImageTk.PhotoImage(image)

        label_image = ttk.Label(root, image=photo)
        label_image.image = photo
        label_image.pack(pady=5)

        ttk.Label(root, text="Please enter the captcha:").pack(pady=5)
        entry = ttk.Entry(root, textvariable=captcha_var, justify="center")
        entry.pack(pady=5)
        entry.focus_set()

        ttk.Button(root, text="Submit", command=root.destroy).pack(pady=10)
        root.bind("<Return>", lambda e=None: root.destroy())
        root.grab_set()
        root.wait_window()
        return captcha_var.get()

    
    
    def bind_mousewheel_to_children(self, widget):
        def _bind_all_children(w):
            w.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
            w.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
            for child in w.winfo_children():
                _bind_all_children(child)
        _bind_all_children(widget)

    def setup_calculator_tab(self):
        # Frame for course selection
        selection_frame = ttk.LabelFrame(self.calculator_tab, text="Select Course")
        selection_frame.pack(fill="x", padx=15, pady=10) # Increased padding

        ttk.Label(selection_frame, text="Select Subject:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.course_var = tk.StringVar()
        self.course_combobox = ttk.Combobox(selection_frame, textvariable=self.course_var, state="readonly", width=50) # Increased width
        self.course_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        selection_frame.grid_columnconfigure(1, weight=1) # Make combobox column expandable

        # Frame for calculator type
        type_frame = ttk.LabelFrame(self.calculator_tab, text="Course Type")
        type_frame.pack(fill="x", padx=15, pady=10) # Increased padding

        self.course_type = tk.StringVar(value="non-hybrid")
        ttk.Radiobutton(type_frame, text="Regular Course", variable=self.course_type, value="non-hybrid").pack(anchor="w", padx=10, pady=5)
        ttk.Radiobutton(type_frame, text="Hybrid Course (with worksheets)", variable=self.course_type, value="hybrid").pack(anchor="w", padx=10, pady=5)

        # Calculation button
        ttk.Button(self.calculator_tab, text="Load Calculator", command=self.load_calculator, style='TButton').pack(pady=15) # Increased padding

        # Calculator container - now a scrollable area
        scroll_container = ttk.Frame(self.calculator_tab)
        scroll_container.pack(fill="both", expand=True, padx=15, pady=10) # Increased padding

        self.canvas = tk.Canvas(scroll_container, bg="white") # Set background for canvas
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.scrollable_calc_frame = ttk.Frame(self.canvas)
        # Store the item ID when creating the window
        self.window_item_id = self.canvas.create_window((0, 0), window=self.scrollable_calc_frame, anchor="nw")

        self.scrollable_calc_frame.bind("<Configure>", self.on_frame_configure)
        # Update inner frame width on canvas resize using itemconfig
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.window_item_id, width=e.width))

        # Bind mouse wheel events to the canvas and the scrollable frame
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # For Windows/macOS
        self.canvas.bind("<Button-4>", self._on_mousewheel)   # For Linux (scroll up)
        self.canvas.bind("<Button-5>", self._on_mousewheel)   # For Linux (scroll down)
        self.scrollable_calc_frame.bind("<MouseWheel>", self._on_mousewheel)  # For Windows/macOS
        self.scrollable_calc_frame.bind("<Button-4>", self._on_mousewheel)   # For Linux (scroll up)
        self.scrollable_calc_frame.bind("<Button-5>", self._on_mousewheel)   # For Linux (scroll down)


        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Results display (this label will still exist but now the primary output is a messagebox)
        self.result_var = tk.StringVar()
        # Removed the label from direct packing, as results will be in a pop-up
        # ttk.Label(self.calculator_tab, textvariable=self.result_var, font=('Helvetica', 12, 'bold')).pack(pady=10)

    def on_frame_configure(self, event):
        """Update the scrollregion of the canvas when the inner frame changes size"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.delta: # For Windows/macOS
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else: # For Linux/X11
            if event.num == 4: # Scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5: # Scroll down
                self.canvas.yview_scroll(1, "units")


    def update_course_list(self):
        """Update the dropdown with courses from marks data"""
        courses = set()
        for child in self.marks_table.get_children():
            course = self.marks_table.item(child)['values'][0]
            courses.add(course)
        self.course_combobox['values'] = sorted(courses)

    
    def load_calculator(self):
        """Load the appropriate calculator based on course type"""
        # Clear previous calculator
        for widget in self.scrollable_calc_frame.winfo_children(): # Clear widgets from the scrollable frame
            widget.destroy()

        course = self.course_var.get()
        if not course:
            messagebox.showerror("Error", "Please select a course first")
            return

        if self.course_type.get() == "hybrid":
            self.setup_hybrid_calculator()
        else:
            self.setup_nonhybrid_calculator()

        # Update scroll region after loading new widgets
        self.canvas.update_idletasks() # Ensure widgets are rendered before calculating bbox
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.bind_mousewheel_to_children(self.scrollable_calc_frame)


    def setup_hybrid_calculator(self):
        """Create hybrid calculator inputs"""
        inputs = [
            ("Assignment Marks", "assignment"),
            ("Attendance Marks", "attendance"),
            ("Surprise Test Marks (out of 12)", "surprise_test"),
            ("Quiz Marks", "quiz"),
            ("MST 1 Marks", "mst_1"),
            ("MST 2 Marks", "mst_2"),
            ("End Sem Practical Marks", "end"),
            ("Lab MST Marks (out of 10)", "labmst")
        ]

        # Use a sub-frame for the main inputs for better organization
        main_inputs_frame = ttk.LabelFrame(self.scrollable_calc_frame, text="Internal Assessment Marks")
        main_inputs_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.hybrid_vars = {}
        for i, (label, name) in enumerate(inputs):
            ttk.Label(main_inputs_frame, text=label + ":").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            self.hybrid_vars[name] = tk.StringVar()
            ttk.Entry(main_inputs_frame, textvariable=self.hybrid_vars[name], width=10).grid(row=i, column=1, padx=5, pady=5, sticky="w")
        
        main_inputs_frame.grid_columnconfigure(1, weight=1) # Allow entry column to expand

        # Worksheet inputs frame
        worksheet_frame = ttk.LabelFrame(self.scrollable_calc_frame, text="Worksheet Marks (out of 30 each)")
        worksheet_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        worksheet_frame.grid_columnconfigure(1, weight=1) # For entry column

        self.worksheet_vars = []
        for i in range(10): # Loop from 0 to 9 for worksheets
            ttk.Label(worksheet_frame, text=f"Worksheet {i+1}:").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            var = tk.StringVar()
            ttk.Entry(worksheet_frame, textvariable=var, width=10).grid(row=i, column=1, padx=5, pady=5, sticky="w")
            self.worksheet_vars.append(var)

        # Calculate button
        ttk.Button(self.scrollable_calc_frame, text="Calculate Internal Marks", command=self.calculate_hybrid, style='TButton').grid(row=1, column=0, columnspan=2, padx=10, pady=20) # Centered below frames
        
        self.scrollable_calc_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_calc_frame.grid_columnconfigure(1, weight=1)


    def setup_nonhybrid_calculator(self):
        """Create non-hybrid calculator inputs"""
        inputs = [
            ("Assignment Marks", "assignment"),
            ("Attendance Marks", "attendance"),
            ("Surprise Test Marks (out of 12)", "surprise_test"),
            ("Quiz Marks", "quiz"),
            ("MST 1 Marks", "mst_1"),
            ("MST 2 Marks", "mst_2")
        ]

        # Use a sub-frame for the inputs
        nonhybrid_inputs_frame = ttk.LabelFrame(self.scrollable_calc_frame, text="Internal Assessment Marks")
        nonhybrid_inputs_frame.pack(padx=10, pady=10, fill="x", expand=True)
        
        self.nonhybrid_vars = {}
        for i, (label, name) in enumerate(inputs):
            ttk.Label(nonhybrid_inputs_frame, text=label + ":").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            self.nonhybrid_vars[name] = tk.StringVar()
            ttk.Entry(nonhybrid_inputs_frame, textvariable=self.nonhybrid_vars[name], width=10).grid(row=i, column=1, padx=5, pady=5, sticky="w")
        
        nonhybrid_inputs_frame.grid_columnconfigure(1, weight=1) # Allow entry column to expand


        # Calculate button
        ttk.Button(self.scrollable_calc_frame, text="Calculate Internal Marks", command=self.calculate_nonhybrid, style='TButton').pack(pady=20)


    def calculate_hybrid(self):
        self.log("Attempting to calculate hybrid marks...") # Log entry point
        try:
            # Get all input values
            assignment = float(self.hybrid_vars["assignment"].get())
            attendance = float(self.hybrid_vars["attendance"].get())
            surprise_test = float(self.hybrid_vars["surprise_test"].get())
            quiz = float(self.hybrid_vars["quiz"].get())
            mst_1 = float(self.hybrid_vars["mst_1"].get())
            mst_2 = float(self.hybrid_vars["mst_2"].get())
            end = float(self.hybrid_vars["end"].get())
            labmst = float(self.hybrid_vars["labmst"].get())

            # Calculate worksheet total
            worksheet_total = 0
            for var in self.worksheet_vars:
                # Handle empty string or non-numeric input for worksheets
                try:
                    worksheet_total += float(var.get())
                except ValueError:
                    # Treat empty worksheet fields as 0 for calculation
                    worksheet_total += 0

            # Perform calculations
            s = (surprise_test / 12) * 4
            n = (labmst / 10) * 15
            worksheet = (worksheet_total / 300) * 45
            m = (mst_1 + mst_2) / 2

            total = ((assignment + quiz + m + attendance + s + worksheet + end + n) / 140) * 70
            
            # Display result in a pop-up window
            messagebox.showinfo("Internal Marks Calculation", f"Your internal marks for {self.course_var.get()}: {total:.2f}")
            self.log("Hybrid marks calculated and displayed in pop-up.")

        except ValueError as e:
            messagebox.showerror("Input Error", "Please enter valid numbers in all fields")
            self.log(f"Input Error in Hybrid Calculator: {e}")
        except Exception as e:
            messagebox.showerror("Calculation Error", "An unexpected error occurred during calculation. Check the log.")
            self.log(f"Error in Hybrid Calculator: {e}\n{traceback.format_exc()}") # Log full traceback


    def calculate_nonhybrid(self):
        self.log("Attempting to calculate non-hybrid marks...") # Log entry point
        try:
            # Get all input values
            assignment = float(self.nonhybrid_vars["assignment"].get())
            attendance = float(self.nonhybrid_vars["attendance"].get())
            surprise_test = float(self.nonhybrid_vars["surprise_test"].get())
            quiz = float(self.nonhybrid_vars["quiz"].get())
            mst_1 = float(self.nonhybrid_vars["mst_1"].get())
            mst_2 = float(self.nonhybrid_vars["mst_2"].get())

            # Perform calculations
            s = (surprise_test / 12) * 4
            m = (mst_1 + mst_2) / 2
            total = assignment + quiz + m + attendance + s
            
            # Display result in a pop-up window
            messagebox.showinfo("Internal Marks Calculation", f"Your internal marks for {self.course_var.get()}: {total:.2f}")
            self.log("Non-hybrid marks calculated and displayed in pop-up.")

        except ValueError as e:
            messagebox.showerror("Input Error", "Please enter valid numbers in all fields")
            self.log(f"Input Error in Non-Hybrid Calculator: {e}")
        except Exception as e:
            messagebox.showerror("Calculation Error", "An unexpected error occurred during calculation. Check the log.")
            self.log(f"Error in Non-Hybrid Calculator: {e}\n{traceback.format_exc()}") # Log full traceback

    def full_fetch(self, uid, pwd):
        try:
            self.log("Starting headless browser and logging in...")
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)

            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            wait = WebDriverWait(self.driver, 30)

            self.driver.get("https://students.cuchd.in/")
            wait.until(EC.presence_of_element_located((By.ID, "txtUserId"))).send_keys(uid)
            self.driver.find_element(By.ID, "btnNext").click()

            wait.until(EC.presence_of_element_located((By.ID, "txtLoginPassword"))).send_keys(pwd)
            captcha_element = wait.until(EC.presence_of_element_located((By.ID, "imgCaptcha")))
            captcha_data = captcha_element.screenshot_as_png
            captcha_text = self.get_captcha_input_gui(captcha_data)
            self.driver.find_element(By.ID, "txtcaptcha").send_keys(captcha_text)
            self.driver.find_element(By.ID, "btnLogin").click()

            wait.until(EC.url_contains("StudentHome.aspx"))
            self.log("✅ Login successful!")

            # Fetch all data:
            self.fetch_attendance()
            self.fetch_marks()
            self.fetch_timetable()

            # Update course list in calculator
            self.update_course_list()

        except Exception as e:
            self.log("❌ Login or fetch failed: " + str(e))

    def fetch_attendance(self):
        try:
            self.log("Fetching attendance...")
            self.driver.get("https://students.cuchd.in/frmStudentCourseWiseAttendanceSummary.aspx?type=etgkYfqBdH1fSfc255iYGw==")
            time.sleep(3)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            table = soup.find("table", {"id": "SortTable"})
            if not table:
                self.log("❌ Attendance table not found.")
                return
            headers = [th.text.strip() for th in table.find_all("th")]
            rows = [[td.text.strip() for td in tr.find_all("td")[:-1]] for tr in table.find("tbody").find_all("tr")]
            df = pd.DataFrame(rows, columns=headers[:-1])
            self.populate_table(self.attendance_table, df)
            self.log("✅ Attendance fetched.")
        except Exception as e:
            self.log("❌ Error fetching attendance: " + str(e))

    def fetch_marks(self):
        try:
            self.log("Fetching marks...")
            self.driver.get("https://students.cuchd.in/frmStudentMarksView.aspx")
            time.sleep(3)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            all_data = []
            for div in soup.select(".ui-accordion-content"):
                course = div.find_previous("h3").get_text(strip=True)
                table = div.find("table")
                if not table: continue
                headers = [th.get_text(strip=True) for th in table.find_all("th")]
                for row in table.find("tbody").find_all("tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) == len(headers):
                        record = dict(zip(headers, cells))
                        record["Course"] = course
                        all_data.append(record)
            df = pd.DataFrame(all_data)
            if not df.empty:
                df = df[["Course"] + [col for col in df.columns if col != "Course"]]
            self.populate_table(self.marks_table, df)
            self.log("✅ Marks fetched.")
        except Exception as e:
            self.log("❌ Error fetching marks: " + str(e))

    def fetch_timetable(self):
        try:
            self.log("Fetching timetable...")
            self.driver.get("https://students.cuchd.in/frmMyTimeTable.aspx")
            time.sleep(3)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Debug: Print raw HTML of course detail table
            course_table_html = soup.find("table", {"id": "ContentPlaceHolder1_grdCourseDetail"})
            if not course_table_html:
                self.log("⚠️ Course detail table not found")

            # Get course code to title mapping
            course_mapping = {}
            if course_table_html:
                for row in course_table_html.find_all("tr")[1:]:  # skip header
                    cols = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cols) >= 2:
                        code = cols[0].strip()
                        title = cols[1].strip()
                        course_mapping[code] = title
                        # Debug: Log the mapping
                        self.log(f"Mapping: {code} → {title}")

            # Get timetable
            timetable = soup.find("table", {"id": "ContentPlaceHolder1_grdMain"})
            if not timetable:
                self.log("❌ Timetable table not found.")
                return

            headers = [th.get_text(strip=True) for th in timetable.find("tr").find_all("th")]
            rows = []

            for tr in timetable.find_all("tr")[1:]:
                cols = [td.get_text(strip=True) for td in tr.find_all("td")]
                if not cols:
                    continue

                processed_cols = []
                for col in cols:
                    # Try to find course code in the cell text
                    found_code = None
                    for code in course_mapping:
                        if code in col:  # Look for code anywhere in cell text
                            found_code = code
                            break

                    if found_code:
                        # Replace just the code portion, keep any other text
                        new_text = col.replace(found_code, course_mapping[found_code])
                        processed_cols.append(new_text)
                    else:
                        processed_cols.append(col)

                rows.append(processed_cols)

            df = pd.DataFrame(rows, columns=headers)
            self.populate_table(self.timetable_table, df)
            self.log("✅ Timetable fetched with course titles.")

        except Exception as e:
            self.log(f"❌ Error fetching timetable: {str(e)}")
            import traceback
            self.log(traceback.format_exc())


    def create_table(self, parent):
        tree = ttk.Treeview(parent)
        tree.pack(fill="both", expand=True, padx=5, pady=5) # Added padding to treeview
        return tree

    def populate_table(self, tree, df):
        tree.delete(*tree.get_children())
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))

    def clear_data(self):
        self.attendance_table.delete(*self.attendance_table.get_children())
        self.marks_table.delete(*self.marks_table.get_children())
        self.timetable_table.delete(*self.timetable_table.get_children())
        self.activity_log.delete("1.0", "end")
        self.result_var.set("") # Clear the label text as well
        self.log("🧹 Cleared all data.")

    def log(self, message):
        self.activity_log.insert("end", message + "\n")
        self.activity_log.see("end")

# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = CUCHDPortalGUI(root)
    root.mainloop()
