# LabTrack: Component Inventory Management System 🧪📦

![Status](https://img.shields.io/badge/Status-Active_Development-green)
![Stack](https://img.shields.io/badge/Tech-Python_|_CustomTkinter_|_Supabase-blue)
![Version](https://img.shields.io/badge/Version-10.0-blue)

## 📖 The Story (The "Why")

During a critical robotics competition preparation ("RoboFest"), our university lab faced a major bottleneck: valuable sensors were missing, components were issued without documentation, and broken parts were returned into the "Working" bin, causing delays for other students.

I built **LabTrack** to solve this. It is a desktop application designed for fast-paced engineering labs to track assets, manage student issues, and enforce accountability for equipment conditions.

## 🚀 Key Features

### 1. **Dashboard View**
- **Summary Cards:** Real-time metrics for Total Items, Currently Issued, and Total Students
- **Overdue Tracking:** Visual alerts for items issued for more than 7 days
- **Data Visualization:** Interactive charts showing:
  - Top 5 Components by availability (Bar Chart)
  - Item Status Distribution (Pie Chart)
- **Recent Activity Feed:** Last 5 transactions with timestamps

### 2. **Issue Items**
- **Smart Component Detection:**
  - Scan serial numbers directly
  - Type component names to see available serial numbers
  - Automatic status checking (Available/Issued/Damaged)
- **Cart System:** Add multiple items before finalizing
- **Staff Tracking:** Global issuer selector tracks who issued items
- **Student Selection:** Dropdown with all registered students

### 3. **Returns Management**
- **Student Search:** Quick search by Student ID or Name
- **Active Loans Display:** Shows all items currently issued to selected student
- **Return Actions:**
  - **Return:** Mark item as Available and close transaction
  - **Report Damaged:** Mark item as Damaged and close transaction
- **Split-Screen UI:** Efficient workflow for processing returns

### 4. **Inventory Overview**
- **Component Statistics:** View total quantity, available, issued, and damaged counts
- **Bulk Import:** Import components from CSV files
  - Auto-generates serial numbers
  - Creates inventory records and individual items
- **Add Component:** Dynamic form that adapts to schema changes
- **Real-Time Updates:** Statistics update automatically

### 5. **Catalog (Master Inventory View)**
- **Comprehensive Table:** View all items with full details
- **Advanced Filtering:**
  - Filter by Status (All, Available, Issued, Damaged)
  - Filter by Course (ECE101, CS201, etc.)
  - Search by Serial Number or Component Name
- **Overdue Highlighting:** Items overdue >7 days shown in red
- **Student Tracking:** Shows which student has each issued item
- **Status Badges:** Color-coded pills for quick visual scanning

### 6. **Student Management**
- **Student Database:** Add, view, and remove students
- **Extended Fields:**
  - Student ID (required)
  - Name (required)
  - Phone Number (optional)
  - Email Address (optional)
- **Table View:** Clean display of all student information
- **Quick Actions:** Remove students with confirmation

### 7. **Global Features**
- **Sync Button:** One-click refresh from Supabase database
- **Staff Selector:** Global issuer tracking in header
- **Dark Theme:** Premium "Zinc" monochrome palette
- **Real-Time Sync:** All changes save to Supabase instantly

## 🛠️ Tech Stack

* **Frontend:** Python 3.7+ with CustomTkinter (Modern dark-mode GUI)
* **Backend/DB:** Supabase (PostgreSQL with real-time capabilities)
* **Data Visualization:** Matplotlib (Embedded charts)
* **Data Processing:** Pandas (CSV import functionality)
* **Deployment:** PyInstaller (Windows .exe generation)

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Supabase account (optional - works with mock data for testing)

## ⚡ Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/lab-track.git
cd lab-track
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `customtkinter` - Modern GUI framework
- `supabase` - Database client
- `python-dotenv` - Environment variable management
- `matplotlib` - Data visualization
- `pandas` - CSV processing

### Step 4: Configure Supabase (Optional)

Create a `.env` file in the project root:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

**OR** set environment variables in your system.

**Note:** If Supabase credentials are not provided, the application will use mock data for testing.

### Step 5: Run the Application

```bash
python mainV10.py
```

The application will start with the Dashboard view. If Supabase is configured, you'll see "Connected to Supabase successfully." Otherwise, it will use mock data.

## 📖 How to Use

### **Dashboard**
- View summary statistics at a glance
- Click "Currently Issued" card to navigate to Catalog with Issued filter
- Monitor recent activity in the feed
- View charts for inventory insights

### **Issue Items**
1. Select an **Issuer** (staff member) from the top-right dropdown
2. Select a **Student** from the dropdown
3. **Scan or type:**
   - Enter serial number (e.g., "ARD001") → Directly adds if available
   - Type component name (e.g., "Arduino") → Shows popup with available serials
4. Items are added to the **Cart**
5. Click **"Finalize Issue"** to complete the transaction

### **Returns**
1. **Search for student** in the left column (by ID or name)
2. Click on a student to see their **Active Loans**
3. For each item, choose:
   - **Return** (Green) - Item becomes Available
   - **Report Damaged** (Red) - Item marked as Damaged

### **Inventory**
- View all components with statistics
- **Import CSV:** Click "Import CSV" to bulk import components
  - CSV format: `Component Name`, `Quantity`, `Description`
- **Add Component:** Click "Add Component" to manually add new inventory
  - Form dynamically adapts to schema changes

### **Catalog**
- **Search:** Type in search bar to filter by serial number or component name
- **Filter by Status:** Click pill buttons (All, Available, Issued, Damaged)
- **Filter by Course:** Click course code pills (ECE101, CS201, etc.)
- **Overdue Items:** Shown in red with red borders
- View complete inventory with student assignments

### **Students**
- **Add Student:** Click "Add Student" button
  - Fill in Student ID, Name, Phone (optional), Email (optional)
  - Press Enter or click "Add Student"
- **Remove Student:** Click "Remove" button next to student
  - Confirmation required before deletion

### **Sync Data**
- Click the **"🔄 Sync"** button in the top header
- Refreshes all data from Supabase
- Reloads current view with latest information

## 📦 Creating an Executable (.exe) File

### Prerequisites for Building
- PyInstaller installed: `pip install pyinstaller`
- All dependencies installed in your virtual environment

### Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

### Step 2: Create the Executable

**Basic Command:**
```bash
pyinstaller --onefile --windowed --name "LabTrack" mainV10.py
```

**Recommended Command (with icon and better options):**
```bash
pyinstaller --onefile --windowed --name "LabTrack" --icon=icon.ico --add-data "requirements.txt;." mainV10.py
```

### Step 3: Find Your Executable

After building, find your `.exe` file in:
```
dist/LabTrack.exe
```

### Advanced PyInstaller Options

**Create a spec file for customization:**
```bash
pyinstaller --name "LabTrack" mainV10.py
```

This creates `LabTrack.spec`. Edit it to:
- Add data files
- Include hidden imports
- Customize the build process

**Example spec file modifications:**
```python
# LabTrack.spec
a = Analysis(
    ['mainV10.py'],
    pathex=[],
    binaries=[],
    datas=[('requirements.txt', '.')],  # Include files
    hiddenimports=['customtkinter', 'supabase'],  # Ensure imports
    ...
)
```

Then build with:
```bash
pyinstaller LabTrack.spec
```

### Troubleshooting Build Issues

1. **Missing Modules:** Add to `hiddenimports` in spec file
2. **Large File Size:** Use `--exclude-module` to remove unused modules
3. **Antivirus Warnings:** Common with PyInstaller - add exception if needed
4. **Missing DLLs:** Ensure all system dependencies are available

### Distribution

The `.exe` file is standalone and can be distributed to other Windows machines without Python installed. However, note that:
- The file size will be large (~50-100MB) due to bundled Python and libraries
- First launch may be slower (extraction process)
- Antivirus software may flag it (false positive - common with PyInstaller)

## 🗄️ Database Schema

The application uses the following Supabase tables:

- **`inventory`** - Component types (name, total_qty, course, etc.)
- **`items`** - Individual items (serial_number, status, inventory_id)
- **`students`** - Student records (name, student_id, phone, email)
- **`staff`** - Staff/issuer records (name, staff_id)
- **`transactions`** - Issue records (student_id, status, issue_date, issuer_id)
- **`transaction_items`** - Links transactions to items

## 🎨 Design System

The application uses a premium "Zinc" monochrome palette:
- **Background:** `#09090b` (Very dark)
- **Cards/Sidebar:** `#18181b` (Dark zinc)
- **Borders:** `#27272a` (Subtle gray)
- **Text Primary:** `#fafafa` (High contrast)
- **Text Secondary:** `#a1a1aa` (Lower contrast)
- **Accents:** `#ffffff` (White for active states)

## 🗺️ Roadmap

- [x] Dashboard with metrics and charts
- [x] Issue Items workflow
- [x] Returns management
- [x] Inventory overview
- [x] Catalog with advanced filtering
- [x] Student management
- [x] Bulk CSV import
- [x] Overdue tracking
- [x] Global sync functionality
- [ ] 
- [ ] Battery Management tab
  - Track voltage before charging and after charging
  - Link to battery inventory using unique battery code
  - Record which user charged the battery
  - Charging history and voltage analytics
- [ ] Auto sync function
  - Automatic Supabase synchronization for immediate updates
  - Real-time data refresh without manual sync button
  - Background polling for database changes
- [ ] Low stock alert system
  - Configurable stock limit (n) for each inventory item
  - Visual alerts when quantity falls below threshold
  - Dashboard notifications for low stock items
- [ ] QR Code generation for bin labels
- [ ] Email notifications for overdue items
- [ ] Analytics dashboard for "Most Used Components"
- [ ] Export reports (PDF/Excel)
- [ ] Multi-user role management

## 🐛 Known Issues

- Catalog view requires scrolling to see all items (fixed with scrollable container)
- Large datasets may have slight performance impact (optimization in progress)

## 📝 Notes

- The application works with **mock data** if Supabase is not configured
- All create/update/delete operations automatically sync to Supabase when connected
- The sync button reconnects and refreshes all data instantly
- Form fields dynamically adapt to schema changes (robust design)

## 🤝 Contributing

This is a university project, but suggestions and improvements are welcome!

## 📄 License

See LICENSE file for details.

---

*Developed by Husain Lokhandwala and Falgun Baria for the Department of Mechanical and Aerospace Engineering, IITRAM.*

**Current Version:** 10.0  
**Last Updated:** 2024
