"""
Lab Inventory Management System - Modern Dashboard Edition
A desktop application for managing university lab equipment using CustomTkinter and Supabase.

This version features:
- Left sidebar navigation (modern dashboard layout)
- Dashboard view with summary cards and data visualization
- Card-based UI design with dark theme
- Comprehensive educational comments for learning
"""

import customtkinter as ctk
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

# Matplotlib imports for data visualization
# We use TkAgg backend to embed matplotlib figures directly into CustomTkinter
try:
    import matplotlib
    matplotlib.use('TkAgg')  # Set backend before importing pyplot
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: Matplotlib not installed. Charts will not be displayed.")

# Try to import supabase, fall back to mock if not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase not installed. Using mock data.")

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars


class DatabaseManager:
    """Handles all database operations with Supabase."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize database manager.
        If credentials are not provided, uses mock data.
        """
        self.use_mock = False
        
        if url and key and SUPABASE_AVAILABLE:
            try:
                self.client: Client = create_client(url, key)
                # Test connection
                self.client.table('inventory').select('*').limit(1).execute()
                print("Connected to Supabase successfully.")
            except Exception as e:
                print(f"Failed to connect to Supabase: {e}. Using mock data.")
                self.use_mock = True
        else:
            self.use_mock = True
            print("Using mock data. Set SUPABASE_URL and SUPABASE_KEY to connect.")
        
        if self.use_mock:
            self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize mock data for testing without Supabase."""
        self.mock_inventory = [
            {"id": 1, "name": "Arduino", "total_qty": 10},
            {"id": 2, "name": "Raspberry Pi", "total_qty": 5},
            {"id": 3, "name": "Sensor", "total_qty": 20},
        ]
        
        self.mock_items = [
            {"id": 1, "serial_number": "ARD001", "status": "Available", "inventory_id": 1},
            {"id": 2, "serial_number": "ARD002", "status": "Available", "inventory_id": 1},
            {"id": 3, "serial_number": "ARD003", "status": "Issued", "inventory_id": 1},
            {"id": 4, "serial_number": "ARD004", "status": "Damaged", "inventory_id": 1},
            {"id": 5, "serial_number": "RPI001", "status": "Available", "inventory_id": 2},
            {"id": 6, "serial_number": "RPI002", "status": "Available", "inventory_id": 2},
            {"id": 7, "serial_number": "SEN001", "status": "Available", "inventory_id": 3},
        ]
        
        self.mock_students = [
            {"id": 1, "name": "John Doe", "student_id": "STU001"},
            {"id": 2, "name": "Jane Smith", "student_id": "STU002"},
            {"id": 3, "name": "Bob Johnson", "student_id": "STU003"},
        ]
        
        self.mock_transactions = []
        self.mock_transaction_items = []
    
    def get_item_by_serial(self, serial_number: str) -> Optional[Dict]:
        """Get item by serial number."""
        if self.use_mock:
            for item in self.mock_items:
                if item["serial_number"].upper() == serial_number.upper():
                    return item
            return None
        else:
            try:
                result = self.client.table('items').select('*, inventory(*)').eq('serial_number', serial_number).execute()
                if result.data:
                    return result.data[0]
                return None
            except Exception as e:
                print(f"Error fetching item: {e}")
                return None
    
    def get_available_items_by_name(self, component_name: str) -> List[Dict]:
        """Get all available items for a component name."""
        if self.use_mock:
            # Find inventory ID by name
            inventory_id = None
            for inv in self.mock_inventory:
                if inv["name"].upper() == component_name.upper():
                    inventory_id = inv["id"]
                    break
            
            if not inventory_id:
                return []
            
            # Return available items
            available = []
            for item in self.mock_items:
                if item["inventory_id"] == inventory_id and item["status"] == "Available":
                    available.append(item)
            return available
        else:
            try:
                # First get inventory by name
                inv_result = self.client.table('inventory').select('id').ilike('name', f'%{component_name}%').execute()
                if not inv_result.data:
                    return []
                
                inventory_ids = [inv["id"] for inv in inv_result.data]
                
                # Get available items
                result = self.client.table('items').select('*, inventory(*)').in_('inventory_id', inventory_ids).eq('status', 'Available').execute()
                return result.data
            except Exception as e:
                print(f"Error fetching available items: {e}")
                return []
    
    def get_all_students(self) -> List[Dict]:
        """Get all students."""
        if self.use_mock:
            return self.mock_students
        else:
            try:
                result = self.client.table('students').select('*').execute()
                return result.data
            except Exception as e:
                print(f"Error fetching students: {e}")
                return []
    
    def create_transaction(self, student_id: int, item_ids: List[int]) -> Optional[int]:
        """Create a transaction and transaction items."""
        if self.use_mock:
            transaction_id = len(self.mock_transactions) + 1
            self.mock_transactions.append({
                "id": transaction_id,
                "student_id": student_id,
                "status": "Active",
                "created_at": datetime.now().isoformat()
            })
            
            for item_id in item_ids:
                self.mock_transaction_items.append({
                    "id": len(self.mock_transaction_items) + 1,
                    "transaction_id": transaction_id,
                    "item_id": item_id
                })
                # Update item status
                for item in self.mock_items:
                    if item["id"] == item_id:
                        item["status"] = "Issued"
                        break
            
            return transaction_id
        else:
            try:
                # Create transaction
                trans_result = self.client.table('transactions').insert({
                    "student_id": student_id,
                    "status": "Active",
                    "created_at": datetime.now().isoformat()
                }).execute()
                
                transaction_id = trans_result.data[0]["id"]
                
                # Create transaction items and update item status
                for item_id in item_ids:
                    self.client.table('transaction_items').insert({
                        "transaction_id": transaction_id,
                        "item_id": item_id
                    }).execute()
                    
                    self.client.table('items').update({
                        "status": "Issued"
                    }).eq('id', item_id).execute()
                
                return transaction_id
            except Exception as e:
                print(f"Error creating transaction: {e}")
                return None
    
    def get_all_inventory(self) -> List[Dict]:
        """Get all inventory items."""
        if self.use_mock:
            return self.mock_inventory
        else:
            try:
                result = self.client.table('inventory').select('*').execute()
                return result.data
            except Exception as e:
                print(f"Error fetching inventory: {e}")
                return []
    
    def get_all_items(self) -> List[Dict]:
        """Get all items with inventory info."""
        if self.use_mock:
            items_with_inv = []
            for item in self.mock_items:
                inv = next((inv for inv in self.mock_inventory if inv["id"] == item["inventory_id"]), None)
                item_copy = item.copy()
                item_copy["inventory"] = inv
                items_with_inv.append(item_copy)
            return items_with_inv
        else:
            try:
                result = self.client.table('items').select('*, inventory(*)').execute()
                return result.data
            except Exception as e:
                print(f"Error fetching items: {e}")
                return []


class ComponentSelectionPopup(ctk.CTkToplevel):
    """
    Popup window for selecting a component when user types component name.
    
    This popup appears when:
    - User types a component name (e.g., "Arduino")
    - Multiple available serial numbers exist for that component
    
    The popup displays all available serial numbers and allows the user
    to select one, which is then added to the cart.
    """
    
    def __init__(self, parent, available_items: List[Dict], callback):
        """
        Initialize the component selection popup.
        
        Args:
            parent: The parent window (main app window)
            available_items: List of available items for the component
            callback: Function to call when an item is selected
        """
        super().__init__(parent)
        self.callback = callback
        self.selected_item = None
        
        # Window configuration
        # geometry: "widthxheight" in pixels
        # To resize popup: change these values
        self.title("Select Component")
        self.geometry("500x400")
        
        # ============================================================
        # MODAL WINDOW EXPLANATION
        # ============================================================
        # transient(parent): Makes this window a child of parent
        # This ensures the popup stays on top of the parent window
        self.transient(parent)
        
        # grab_set(): Makes the popup modal
        # Modal means: User MUST interact with this window before
        # they can click on the parent window again
        # This prevents accidental clicks outside the popup
        self.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Available Serial Numbers",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Scrollable frame for items
        scroll_frame = ctk.CTkScrollableFrame(self, width=450, height=250)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        if not available_items:
            no_items_label = ctk.CTkLabel(
                scroll_frame,
                text="No available items found.",
                text_color="gray"
            )
            no_items_label.pack(pady=20)
        else:
            for item in available_items:
                item_frame = ctk.CTkFrame(scroll_frame)
                item_frame.pack(fill="x", pady=5, padx=10)
                
                serial_label = ctk.CTkLabel(
                    item_frame,
                    text=f"Serial: {item['serial_number']}",
                    font=ctk.CTkFont(size=14)
                )
                serial_label.pack(side="left", padx=15, pady=10)
                
                select_btn = ctk.CTkButton(
                    item_frame,
                    text="Select",
                    width=100,
                    command=lambda i=item: self._select_item(i)
                )
                select_btn.pack(side="right", padx=15, pady=10)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            self,
            text="Cancel",
            command=self._cancel,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(pady=20)
    
    def _select_item(self, item: Dict):
        """Select an item and close popup."""
        self.selected_item = item
        self.callback(item)
        self.destroy()
    
    def _cancel(self):
        """Cancel selection."""
        self.destroy()


class LabApp(ctk.CTk):
    """
    Main application window with modern sidebar navigation.
    
    This class implements a dashboard-style layout with:
    - Left sidebar for navigation (instead of top tabs)
    - Content area that switches views based on sidebar selection
    - Card-based design for better visual hierarchy
    """
    
    def __init__(self):
        super().__init__()
        
        # ============================================================
        # CONFIG ZONE: Window Configuration
        # ============================================================
        # You can modify these values to change the window appearance:
        self.title("Lab Inventory Management System")
        self.geometry("1400x900")  # Increased size for better dashboard layout
        # To change window size: modify the string above (width x height)
        
        # ============================================================
        # CONFIG ZONE: Theme Configuration
        # ============================================================
        # Set appearance mode: "Dark", "Light", or "System"
        ctk.set_appearance_mode("Dark")
        # Color theme options: "blue", "green", "dark-blue"
        # To use custom colors, you'll need to modify CTkTheme files
        ctk.set_default_color_theme("blue")
        
        # ============================================================
        # CONFIG ZONE: Database Credentials
        # ============================================================
        # PASTE YOUR SUPABASE CREDENTIALS HERE:
        # Option 1: Set environment variables in your system
        # Option 2: Create a .env file in the project root with:
        #   SUPABASE_URL=your_project_url_here
        #   SUPABASE_KEY=your_anon_key_here
        # Option 3: Hardcode them below (NOT RECOMMENDED for production)
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        # If you want to hardcode (for testing only), uncomment below:
        # supabase_url = "your_url_here"
        # supabase_key = "your_key_here"
        
        self.db = DatabaseManager(supabase_url, supabase_key)
        
        # Cart for issue items (stores items before finalizing transaction)
        self.cart_items: List[Dict] = []
        
        # Track current view for sidebar highlighting
        self.current_view = "dashboard"
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """
        Create the main UI with sidebar navigation.
        
        This method sets up:
        1. Left sidebar with navigation buttons
        2. Main content area that displays different views
        3. Initial view (Dashboard) when app starts
        """
        # Create main container using grid for better control
        # Grid allows us to have fixed sidebar and flexible content area
        self.grid_columnconfigure(1, weight=1)  # Content area expands
        self.grid_rowconfigure(0, weight=1)  # Full height
        
        # ============================================================
        # LEFT SIDEBAR NAVIGATION
        # ============================================================
        # Sidebar width: Change 200 to adjust sidebar size (in pixels)
        sidebar_width = 200
        sidebar = ctk.CTkFrame(self, width=sidebar_width, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(4, weight=1)  # Push buttons to top
        
        # Sidebar background color: The frame uses the theme's secondary color
        # To change: modify fg_color parameter (e.g., fg_color="#1a1a1a" for custom dark gray)
        
        # App Title in Sidebar
        title_label = ctk.CTkLabel(
            sidebar,
            text="Lab Track",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(30, 10))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            sidebar,
            text="Inventory System",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Navigation Buttons
        # Button styling: height controls button size, font controls text size
        # To change button colors: modify fg_color and hover_color
        # Available color names: "blue", "green", "red", "gray" or hex codes like "#1f538d"
        
        self.dashboard_btn = ctk.CTkButton(
            sidebar,
            text="📊 Dashboard",
            command=lambda: self._switch_view("dashboard"),
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",  # Left-align text
            fg_color=("gray75", "gray25") if self.current_view == "dashboard" else "transparent",
            text_color=("gray10", "gray90")
        )
        self.dashboard_btn.pack(pady=5, padx=10, fill="x")
        
        self.issue_btn = ctk.CTkButton(
            sidebar,
            text="📦 Issue Items",
            command=lambda: self._switch_view("issue"),
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color=("gray75", "gray25") if self.current_view == "issue" else "transparent",
            text_color=("gray10", "gray90")
        )
        self.issue_btn.pack(pady=5, padx=10, fill="x")
        
        self.returns_btn = ctk.CTkButton(
            sidebar,
            text="↩️ Returns",
            command=lambda: self._switch_view("returns"),
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color=("gray75", "gray25") if self.current_view == "returns" else "transparent",
            text_color=("gray10", "gray90")
        )
        self.returns_btn.pack(pady=5, padx=10, fill="x")
        
        self.inventory_btn = ctk.CTkButton(
            sidebar,
            text="📋 Inventory",
            command=lambda: self._switch_view("inventory"),
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color=("gray75", "gray25") if self.current_view == "inventory" else "transparent",
            text_color=("gray10", "gray90")
        )
        self.inventory_btn.pack(pady=5, padx=10, fill="x")
        
        # ============================================================
        # MAIN CONTENT AREA
        # ============================================================
        # This frame will hold the current view (Dashboard, Issue Items, etc.)
        # Padding: Controls spacing from window edges
        # To change padding: modify padx and pady values (in pixels)
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Show dashboard by default
        self._show_dashboard()
    
    def _switch_view(self, view_name: str):
        """
        Switch between different views in the content area.
        
        This method:
        1. Clears the current content
        2. Updates sidebar button highlights
        3. Shows the selected view
        
        Args:
            view_name: One of "dashboard", "issue", "returns", "inventory"
        """
        self.current_view = view_name
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update button highlights
        # Reset all buttons to transparent
        for btn in [self.dashboard_btn, self.issue_btn, self.returns_btn, self.inventory_btn]:
            btn.configure(fg_color="transparent")
        
        # Highlight active button
        if view_name == "dashboard":
            self.dashboard_btn.configure(fg_color=("gray75", "gray25"))
            self._show_dashboard()
        elif view_name == "issue":
            self.issue_btn.configure(fg_color=("gray75", "gray25"))
            self._show_issue_view()
        elif view_name == "returns":
            self.returns_btn.configure(fg_color=("gray75", "gray25"))
            self._show_returns_view()
        elif view_name == "inventory":
            self.inventory_btn.configure(fg_color=("gray75", "gray25"))
            self._show_inventory_view()
    
    def _show_dashboard(self):
        """
        Display the Dashboard view with summary cards and charts.
        
        This is the home screen that appears when the app starts.
        It includes:
        - Summary cards showing key metrics
        - Bar chart for inventory levels
        - Pie chart for item status distribution
        """
        # Create scrollable container for dashboard content
        # This allows the dashboard to scroll if content exceeds window height
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            scroll_frame,
            text="Dashboard",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(0, 30))
        
        # ============================================================
        # SUMMARY CARDS SECTION
        # ============================================================
        # Card container: Uses a frame to group the three cards horizontally
        # Padding: Controls spacing between cards (pady=vertical, padx=horizontal)
        cards_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        cards_container.pack(fill="x", pady=(0, 30))
        
        # Get data for summary cards
        all_items = self.db.get_all_items()
        all_students = self.db.get_all_students()
        
        total_items = len(all_items)
        issued_count = sum(1 for item in all_items if item.get("status") == "Issued")
        total_students = len(all_students)
        
        # Card dimensions: Change width and height to resize cards
        # Card colors: Modify fg_color to change card background
        # Available colors: hex codes like "#1f538d" or theme colors
        card_width = 280
        card_height = 180
        
        # Card 1: Total Items
        card1 = ctk.CTkFrame(cards_container, width=card_width, height=card_height, corner_radius=15)
        card1.pack(side="left", padx=15, pady=10)
        card1.pack_propagate(False)  # Prevents card from resizing based on content
        
        # Card content: Icon/Emoji, Label, Value
        # Font sizes: Modify size parameter to change text size
        card1_label = ctk.CTkLabel(
            card1,
            text="Total Items",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        card1_label.pack(pady=(20, 5))
        
        card1_value = ctk.CTkLabel(
            card1,
            text=str(total_items),
            font=ctk.CTkFont(size=48, weight="bold")
        )
        card1_value.pack()
        
        # Card 2: Currently Issued
        card2 = ctk.CTkFrame(cards_container, width=card_width, height=card_height, corner_radius=15)
        card2.pack(side="left", padx=15, pady=10)
        card2.pack_propagate(False)
        
        card2_label = ctk.CTkLabel(
            card2,
            text="Currently Issued",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        card2_label.pack(pady=(20, 5))
        
        card2_value = ctk.CTkLabel(
            card2,
            text=str(issued_count),
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color="#4CAF50"  # Green color for issued items
        )
        card2_value.pack()
        
        # Card 3: Total Students
        card3 = ctk.CTkFrame(cards_container, width=card_width, height=card_height, corner_radius=15)
        card3.pack(side="left", padx=15, pady=10)
        card3.pack_propagate(False)
        
        card3_label = ctk.CTkLabel(
            card3,
            text="Total Students",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        card3_label.pack(pady=(20, 5))
        
        card3_value = ctk.CTkLabel(
            card3,
            text=str(total_students),
            font=ctk.CTkFont(size=48, weight="bold")
        )
        card3_value.pack()
        
        # ============================================================
        # CHARTS SECTION
        # ============================================================
        # Charts container: Two charts side by side
        charts_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        charts_container.pack(fill="both", expand=True, pady=20)
        
        if MATPLOTLIB_AVAILABLE:
            # Chart 1: Bar Chart - Top 5 Components by Inventory Level
            self._create_bar_chart(charts_container, all_items)
            
            # Chart 2: Pie Chart - Item Status Distribution
            self._create_pie_chart(charts_container, all_items)
        else:
            # Fallback if matplotlib is not available
            no_charts_label = ctk.CTkLabel(
                charts_container,
                text="Install matplotlib to view charts: pip install matplotlib",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            no_charts_label.pack(pady=50)
    
    def _create_bar_chart(self, parent, all_items: List[Dict]):
        """
        Create a bar chart showing inventory levels for top 5 components.
        
        This method:
        1. Calculates available items per component
        2. Creates a matplotlib figure with dark theme
        3. Embeds it into a CustomTkinter frame
        
        Args:
            parent: The parent frame to embed the chart into
            all_items: List of all items from the database
        """
        # Get inventory data
        inventory_list = self.db.get_all_inventory()
        
        # Calculate available count for each inventory item
        component_data = {}
        for inv in inventory_list:
            available = sum(1 for item in all_items 
                          if item.get("inventory_id") == inv["id"] 
                          and item.get("status") == "Available")
            component_data[inv["name"]] = available
        
        # Sort by value and get top 5
        sorted_components = sorted(component_data.items(), key=lambda x: x[1], reverse=True)[:5]
        component_names = [item[0] for item in sorted_components]
        component_counts = [item[1] for item in sorted_components]
        
        # ============================================================
        # MATPLOTLIB INTEGRATION EXPLANATION
        # ============================================================
        # Step 1: Create a Figure object
        # This is the canvas where matplotlib will draw
        # figsize: (width, height) in inches - adjust to resize chart
        # facecolor: Background color (dark to match app theme)
        # edgecolor: Border color
        fig = Figure(figsize=(5, 4), facecolor="#212121", edgecolor="#212121")
        
        # Step 2: Create a subplot (axes) on the figure
        # 1,1,1 means: 1 row, 1 column, position 1
        # This gives us one plot area
        ax = fig.add_subplot(111)
        
        # Step 3: Configure dark theme for the plot
        # Set background colors to match dark theme
        ax.set_facecolor("#212121")  # Chart background
        fig.patch.set_facecolor("#212121")  # Figure background
        
        # Step 4: Create the bar chart
        # component_names: X-axis labels (component names)
        # component_counts: Y-axis values (available quantities)
        # color: Bar color - change "#1f538d" to any hex color
        bars = ax.bar(component_names, component_counts, color="#1f538d")
        
        # Step 5: Style the chart
        ax.set_title("Top 5 Components - Available Stock", 
                    color="white", fontsize=14, fontweight="bold", pad=20)
        ax.set_xlabel("Component", color="white", fontsize=12)
        ax.set_ylabel("Available Quantity", color="white", fontsize=12)
        
        # Set text colors to white for dark theme
        ax.tick_params(colors="white", labelsize=10)
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['right'].set_color('white')
        ax.spines['left'].set_color('white')
        
        # Rotate x-axis labels if they're long
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        
        # Step 6: Embed the matplotlib figure into CustomTkinter
        # FigureCanvasTkAgg is the bridge between matplotlib and Tkinter
        # master: The parent widget (our CustomTkinter frame)
        # figure: The matplotlib figure we created
        canvas = FigureCanvasTkAgg(fig, master=parent)
        
        # Step 7: Draw the canvas and pack it
        # get_tk_widget(): Gets the Tkinter widget from the canvas
        # This allows us to use it with CustomTkinter's pack/grid system
        canvas.draw()
        canvas.get_tk_widget().pack(side="left", padx=20, pady=10, fill="both", expand=True)
    
    def _create_pie_chart(self, parent, all_items: List[Dict]):
        """
        Create a pie chart showing the distribution of item statuses.
        
        This chart shows the ratio of Available vs Issued vs Damaged items.
        
        Args:
            parent: The parent frame to embed the chart into
            all_items: List of all items from the database
        """
        # Count items by status
        status_counts = {
            "Available": sum(1 for item in all_items if item.get("status") == "Available"),
            "Issued": sum(1 for item in all_items if item.get("status") == "Issued"),
            "Damaged": sum(1 for item in all_items if item.get("status") == "Damaged")
        }
        
        # Filter out zero values for cleaner chart
        labels = []
        sizes = []
        colors_list = []
        
        # Color mapping: Change these hex codes to customize pie slice colors
        color_map = {
            "Available": "#4CAF50",  # Green
            "Issued": "#2196F3",     # Blue
            "Damaged": "#F44336"     # Red
        }
        
        for status, count in status_counts.items():
            if count > 0:
                labels.append(status)
                sizes.append(count)
                colors_list.append(color_map.get(status, "#808080"))
        
        if not sizes:  # No data to display
            return
        
        # Create figure with dark theme
        fig = Figure(figsize=(5, 4), facecolor="#212121", edgecolor="#212121")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#212121")
        fig.patch.set_facecolor("#212121")
        
        # Create pie chart
        # autopct: Shows percentage on each slice
        # startangle: Rotates the pie (90 degrees = starts at top)
        # colors: List of colors for each slice
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors_list
        )
        
        # Style the text
        ax.set_title("Item Status Distribution", 
                    color="white", fontsize=14, fontweight="bold", pad=20)
        
        # Set label colors to white
        for text in texts:
            text.set_color("white")
            text.set_fontsize(12)
        
        # Set percentage text color to white
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
        
        # Embed into CustomTkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side="left", padx=20, pady=10, fill="both", expand=True)
    
    def _show_issue_view(self):
        """
        Display the Issue Items view.
        
        This is the main workflow for issuing items to students.
        It includes:
        - Input field for serial number or component name
        - Cart showing selected items
        - Student selection dropdown
        - Finalize button
        """
        # Create scrollable container
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            scroll_frame,
            text="Issue Items",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(0, 30))
        
        # ============================================================
        # INPUT SECTION CARD
        # ============================================================
        # Card-based design: Using CTkFrame with corner_radius for rounded corners
        # corner_radius: Controls how rounded the corners are (0 = square, 15 = very rounded)
        # fg_color: Frame background color (slightly lighter than main background for card effect)
        input_card = ctk.CTkFrame(scroll_frame, corner_radius=15)
        input_card.pack(pady=20, padx=20, fill="x")
        
        # Padding inside card: Controls spacing between card edge and content
        input_label = ctk.CTkLabel(
            input_card,
            text="Scan Serial # or Type Component Name",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        input_label.pack(pady=(20, 10), padx=20)
        
        # Entry field: height controls input field size
        # placeholder_text: Gray hint text shown when field is empty
        self.issue_entry = ctk.CTkEntry(
            input_card,
            placeholder_text="Enter serial number or component name...",
            height=50,  # Increase for larger input field
            font=ctk.CTkFont(size=16)
        )
        self.issue_entry.pack(pady=10, padx=20, fill="x")
        # Bind Enter key to add item (for faster workflow)
        self.issue_entry.bind("<Return>", lambda e: self._add_to_cart())
        
        # Add button: fg_color controls button color
        # To change button color: use hex code like "#1f538d" or color name
        add_btn = ctk.CTkButton(
            input_card,
            text="Add to List",
            command=self._add_to_cart,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        add_btn.pack(pady=(0, 20), padx=20)
        
        # ============================================================
        # CART SECTION CARD
        # ============================================================
        cart_card = ctk.CTkFrame(scroll_frame, corner_radius=15)
        cart_card.pack(pady=20, padx=20, fill="both", expand=True)
        
        cart_label = ctk.CTkLabel(
            cart_card,
            text="Selected Items",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        cart_label.pack(pady=(20, 10), padx=20)
        
        # Scrollable cart list: Allows scrolling if many items are added
        # height: Initial height of scrollable area
        self.cart_scroll = ctk.CTkScrollableFrame(cart_card, height=300)
        self.cart_scroll.pack(pady=10, padx=20, fill="both", expand=True)
        
        # ============================================================
        # CHECKOUT SECTION CARD
        # ============================================================
        checkout_card = ctk.CTkFrame(cart_card, corner_radius=10)
        checkout_card.pack(pady=10, padx=20, fill="x")
        
        student_label = ctk.CTkLabel(
            checkout_card,
            text="Select Student:",
            font=ctk.CTkFont(size=16)
        )
        student_label.pack(side="left", padx=20, pady=15)
        
        # Dropdown: width controls dropdown width
        self.student_dropdown = ctk.CTkComboBox(
            checkout_card,
            values=[],
            width=350,  # Adjust width as needed
            font=ctk.CTkFont(size=14)
        )
        self.student_dropdown.pack(side="left", padx=10, pady=15)
        
        self._load_students()
        
        # Finalize button: Green color indicates positive action
        # hover_color: Color when mouse hovers over button
        finalize_btn = ctk.CTkButton(
            checkout_card,
            text="Finalize Issue",
            command=self._finalize_issue,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#4CAF50",  # Green
            hover_color="#45a049"  # Darker green on hover
        )
        finalize_btn.pack(side="right", padx=20, pady=15)
        
        # Update cart display
        self._update_cart_display()
    
    def _show_returns_view(self):
        """Display the Returns view (placeholder for future implementation)."""
        label = ctk.CTkLabel(
            self.content_frame,
            text="Returns Management",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        label.pack(pady=50)
        
        info_label = ctk.CTkLabel(
            self.content_frame,
            text="Returns functionality will be implemented here.",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        info_label.pack(pady=20)
    
    def _show_inventory_view(self):
        """Display the Inventory view with detailed inventory information."""
        # Create scrollable container
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            scroll_frame,
            text="Inventory Overview",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(0, 30))
        
        # Load and display inventory
        self._load_inventory_display(scroll_frame)
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="Scan Serial # or Type Component Name",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        input_label.pack(pady=10)
        
        self.issue_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter serial number or component name...",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.issue_entry.pack(pady=10, padx=20, fill="x")
        self.issue_entry.bind("<Return>", lambda e: self._add_to_cart())
        
        add_btn = ctk.CTkButton(
            input_frame,
            text="Add to List",
            command=self._add_to_cart,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        add_btn.pack(pady=10, padx=20)
        
        # Cart section
        cart_frame = ctk.CTkFrame(self.issue_tab, corner_radius=10)
        cart_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        cart_label = ctk.CTkLabel(
            cart_frame,
            text="Selected Items",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        cart_label.pack(pady=10)
        
        # Scrollable cart list
        self.cart_scroll = ctk.CTkScrollableFrame(cart_frame, height=300)
        self.cart_scroll.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Checkout section
        checkout_frame = ctk.CTkFrame(cart_frame, corner_radius=10)
        checkout_frame.pack(pady=10, padx=20, fill="x")
        
        student_label = ctk.CTkLabel(
            checkout_frame,
            text="Select Student:",
            font=ctk.CTkFont(size=14)
        )
        student_label.pack(side="left", padx=20, pady=15)
        
        self.student_dropdown = ctk.CTkComboBox(
            checkout_frame,
            values=[],
            width=300,
            font=ctk.CTkFont(size=14)
        )
        self.student_dropdown.pack(side="left", padx=10, pady=15)
        
        self._load_students()
        
        finalize_btn = ctk.CTkButton(
            checkout_frame,
            text="Finalize Issue",
            command=self._finalize_issue,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        finalize_btn.pack(side="right", padx=20, pady=15)
        
        # Update cart display
        self._update_cart_display()
    
    
    def _load_students(self):
        """Load students into dropdown."""
        students = self.db.get_all_students()
        student_values = [f"{s['name']} ({s['student_id']})" for s in students]
        self.student_dropdown.configure(values=student_values)
        if student_values:
            self.student_dropdown.set(student_values[0])
    
    def _add_to_cart(self):
        """
        Add item to cart based on user input.
        
        This method implements the "smart" logic:
        - If input matches a serial number → Check status and handle accordingly
        - If input is a component name → Show popup with available serial numbers
        
        The method first tries to find by serial number (exact match),
        then falls back to component name search if no serial match is found.
        """
        # Get input text and remove leading/trailing whitespace
        input_text = self.issue_entry.get().strip()
        
        # Validation: Check if input is empty
        if not input_text:
            self._show_error("Please enter a serial number or component name.")
            return
        
        # Strategy: Try serial number lookup first (more specific)
        # This is faster and more accurate than component name search
        item = self.db.get_item_by_serial(input_text)
        
        if item:
            # Found by serial number → Handle based on item status
            self._handle_serial_number(item)
        else:
            # Not found by serial → Try component name search
            # This will show a popup if multiple items are available
            self._handle_component_name(input_text)
    
    def _handle_serial_number(self, item: Dict):
        """
        Handle when user enters a serial number.
        
        This method implements the status checking logic:
        - "Issued" → Show RED error (item already in use)
        - "Damaged" → Show YELLOW warning (ask for confirmation)
        - "Available" → Add directly to cart (green path)
        - Other statuses → Show error (invalid state)
        
        Args:
            item: Dictionary containing item data from database
        """
        # Get status and convert to lowercase for case-insensitive comparison
        status = item.get("status", "").lower()
        
        if status == "issued":
            # RED ERROR: Item is already issued to another student
            # This prevents double-issuing
            self._show_error("Item already issued!", "Error")
            return
        elif status == "damaged":
            # YELLOW WARNING: Item is damaged but can still be issued with confirmation
            # This allows flexibility for special cases
            self._show_warning(item)
        elif status == "available":
            # GREEN PATH: Item is available, add directly to cart
            self._add_item_to_cart(item)
        else:
            # Unknown status: Show error for safety
            self._show_error(f"Item status: {status}. Cannot issue.", "Error")
    
    def _handle_component_name(self, component_name: str):
        """Handle when user enters a component name."""
        available_items = self.db.get_available_items_by_name(component_name)
        
        if not available_items:
            self._show_error(f"No available items found for '{component_name}'.", "Not Found")
            return
        
        # Open popup to select serial number
        popup = ComponentSelectionPopup(self, available_items, self._add_item_to_cart)
        popup.focus()
    
    def _add_item_to_cart(self, item: Dict):
        """Add item to cart."""
        # Check if already in cart
        for cart_item in self.cart_items:
            if cart_item["id"] == item["id"]:
                self._show_error("Item already in cart!", "Duplicate")
                return
        
        self.cart_items.append(item)
        self.issue_entry.delete(0, "end")
        self._update_cart_display()
    
    def _show_error(self, message: str, title: str = "Error"):
        """Show error popup."""
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("400x200")
        popup.transient(self)
        popup.grab_set()
        
        label = ctk.CTkLabel(
            popup,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color="red",
            wraplength=350
        )
        label.pack(pady=30, padx=20)
        
        btn = ctk.CTkButton(
            popup,
            text="OK",
            command=popup.destroy,
            fg_color="red",
            hover_color="darkred"
        )
        btn.pack(pady=20)
    
    def _show_warning(self, item: Dict):
        """Show warning popup for damaged items."""
        popup = ctk.CTkToplevel(self)
        popup.title("Warning")
        popup.geometry("450x250")
        popup.transient(self)
        popup.grab_set()
        
        label = ctk.CTkLabel(
            popup,
            text=f"Item {item['serial_number']} is marked as DAMAGED.\n\nDo you want to issue it anyway?",
            font=ctk.CTkFont(size=14),
            text_color="orange",
            wraplength=400
        )
        label.pack(pady=30, padx=20)
        
        btn_frame = ctk.CTkFrame(popup)
        btn_frame.pack(pady=20)
        
        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="Confirm Issue",
            command=lambda: self._confirm_damaged_issue(item, popup),
            fg_color="orange",
            hover_color="darkorange"
        )
        confirm_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=popup.destroy,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="left", padx=10)
    
    def _confirm_damaged_issue(self, item: Dict, popup):
        """Confirm issuing a damaged item."""
        popup.destroy()
        self._add_item_to_cart(item)
    
    def _update_cart_display(self):
        """Update the cart display."""
        # Clear existing widgets
        for widget in self.cart_scroll.winfo_children():
            widget.destroy()
        
        if not self.cart_items:
            empty_label = ctk.CTkLabel(
                self.cart_scroll,
                text="Cart is empty. Add items to get started.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            empty_label.pack(pady=50)
            return
        
        # Display items
        for item in self.cart_items:
            item_frame = ctk.CTkFrame(self.cart_scroll, corner_radius=5)
            item_frame.pack(fill="x", pady=5, padx=10)
            
            # Get inventory name
            inventory_name = "Unknown"
            if "inventory" in item and item["inventory"]:
                inventory_name = item["inventory"].get("name", "Unknown")
            elif "inventory_id" in item:
                # Fallback for mock data structure
                inv_list = self.db.get_all_inventory()
                for inv in inv_list:
                    if inv["id"] == item["inventory_id"]:
                        inventory_name = inv["name"]
                        break
            
            info_text = f"{inventory_name} - {item['serial_number']}"
            info_label = ctk.CTkLabel(
                item_frame,
                text=info_text,
                font=ctk.CTkFont(size=14)
            )
            info_label.pack(side="left", padx=15, pady=10)
            
            remove_btn = ctk.CTkButton(
                item_frame,
                text="Remove",
                width=100,
                command=lambda i=item: self._remove_from_cart(i),
                fg_color="red",
                hover_color="darkred"
            )
            remove_btn.pack(side="right", padx=15, pady=10)
    
    def _remove_from_cart(self, item: Dict):
        """Remove item from cart."""
        self.cart_items = [i for i in self.cart_items if i["id"] != item["id"]]
        self._update_cart_display()
    
    def _finalize_issue(self):
        """Finalize the issue transaction."""
        if not self.cart_items:
            self._show_error("Cart is empty. Add items before finalizing.", "Empty Cart")
            return
        
        student_value = self.student_dropdown.get()
        if not student_value:
            self._show_error("Please select a student.", "No Student Selected")
            return
        
        # Extract student ID from dropdown value
        students = self.db.get_all_students()
        selected_student = None
        for student in students:
            if f"{student['name']} ({student['student_id']})" == student_value:
                selected_student = student
                break
        
        if not selected_student:
            self._show_error("Invalid student selection.", "Error")
            return
        
        # Create transaction
        item_ids = [item["id"] for item in self.cart_items]
        transaction_id = self.db.create_transaction(selected_student["id"], item_ids)
        
        if transaction_id:
            # Success
            success_popup = ctk.CTkToplevel(self)
            success_popup.title("Success")
            success_popup.geometry("400x200")
            success_popup.transient(self)
            success_popup.grab_set()
            
            label = ctk.CTkLabel(
                success_popup,
                text=f"Transaction #{transaction_id} created successfully!\n\n{len(self.cart_items)} item(s) issued to {selected_student['name']}.",
                font=ctk.CTkFont(size=14),
                text_color="green",
                wraplength=350
            )
            label.pack(pady=30, padx=20)
            
            btn = ctk.CTkButton(
                success_popup,
                text="OK",
                command=lambda: self._close_success_popup(success_popup),
                fg_color="green",
                hover_color="darkgreen"
            )
            btn.pack(pady=20)
        else:
            self._show_error("Failed to create transaction. Please try again.", "Error")
    
    def _close_success_popup(self, popup):
        """Close success popup and clear cart."""
        popup.destroy()
        self.cart_items = []
        self._update_cart_display()
        self.issue_entry.delete(0, "end")
    
    def _load_inventory_display(self, parent):
        """
        Load and display inventory items in a card-based table format.
        
        This method:
        1. Fetches inventory and item data from the database
        2. Calculates statistics (available, issued, damaged counts)
        3. Displays them in a table-like card layout
        
        Args:
            parent: The parent frame to display inventory in
        """
        inventory_list = self.db.get_all_inventory()
        items_list = self.db.get_all_items()
        
        if not inventory_list:
            label = ctk.CTkLabel(
                parent,
                text="No inventory items found.",
                font=ctk.CTkFont(size=16),
                text_color="gray"
            )
            label.pack(pady=50)
            return
        
        # ============================================================
        # TABLE HEADER CARD
        # ============================================================
        # Header card: Slightly different styling to distinguish from data rows
        # corner_radius: Controls rounded corners (5 = slightly rounded)
        header_card = ctk.CTkFrame(parent, corner_radius=10)
        header_card.pack(fill="x", pady=(0, 10), padx=10)
        
        # Column headers: Using grid layout for aligned columns
        # padx: Horizontal padding between columns
        # sticky="w": Left-aligns text within grid cell
        headers = ["Component Name", "Total Quantity", "Available", "Issued", "Damaged"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_card,
                text=header,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            # Grid layout: row=0, column=i (i increases for each header)
            # padx: Spacing between columns (adjust for wider/narrower spacing)
            label.grid(row=0, column=i, padx=30, pady=15, sticky="w")
        
        # ============================================================
        # INVENTORY DATA ROWS (CARD-BASED)
        # ============================================================
        # Each inventory item gets its own card for better visual separation
        for inv in inventory_list:
            # Calculate statistics for this inventory item
            # This loops through all items and counts by status
            available = sum(1 for item in items_list 
                          if item.get("inventory_id") == inv["id"] 
                          and item.get("status") == "Available")
            issued = sum(1 for item in items_list 
                        if item.get("inventory_id") == inv["id"] 
                        and item.get("status") == "Issued")
            damaged = sum(1 for item in items_list 
                         if item.get("inventory_id") == inv["id"] 
                         and item.get("status") == "Damaged")
            
            # Data row card: Each row is a separate card
            # pady: Vertical spacing between rows (increase for more space)
            row_card = ctk.CTkFrame(parent, corner_radius=10)
            row_card.pack(fill="x", pady=8, padx=10)
            
            # Component name
            name_label = ctk.CTkLabel(
                row_card, 
                text=inv["name"], 
                font=ctk.CTkFont(size=15)
            )
            name_label.grid(row=0, column=0, padx=30, pady=12, sticky="w")
            
            # Total quantity
            total_label = ctk.CTkLabel(
                row_card, 
                text=str(inv.get("total_qty", 0)), 
                font=ctk.CTkFont(size=15)
            )
            total_label.grid(row=0, column=1, padx=30, pady=12, sticky="w")
            
            # Available count (green color indicates positive status)
            # text_color: Change hex code to customize color
            # Available colors: "green", "#4CAF50" (green hex), "#00ff00" (bright green)
            avail_label = ctk.CTkLabel(
                row_card, 
                text=str(available), 
                font=ctk.CTkFont(size=15), 
                text_color="#4CAF50"  # Green
            )
            avail_label.grid(row=0, column=2, padx=30, pady=12, sticky="w")
            
            # Issued count (blue color)
            issued_label = ctk.CTkLabel(
                row_card, 
                text=str(issued), 
                font=ctk.CTkFont(size=15), 
                text_color="#2196F3"  # Blue
            )
            issued_label.grid(row=0, column=3, padx=30, pady=12, sticky="w")
            
            # Damaged count (red color indicates warning)
            damaged_label = ctk.CTkLabel(
                row_card, 
                text=str(damaged), 
                font=ctk.CTkFont(size=15), 
                text_color="#F44336"  # Red
            )
            damaged_label.grid(row=0, column=4, padx=30, pady=12, sticky="w")


def main():
    """Main entry point."""
    app = LabApp()
    app.mainloop()


if __name__ == "__main__":
    main()
