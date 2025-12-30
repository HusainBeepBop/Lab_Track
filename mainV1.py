"""
Lab Inventory Management System
A desktop application for managing university lab equipment using CustomTkinter and Supabase.
"""

import customtkinter as ctk
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

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
    """Popup window for selecting a component when user types component name."""
    
    def __init__(self, parent, available_items: List[Dict], callback):
        super().__init__(parent)
        self.callback = callback
        self.selected_item = None
        
        self.title("Select Component")
        self.geometry("500x400")
        
        # Make it modal
        self.transient(parent)
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
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Lab Inventory Management System")
        self.geometry("1200x800")
        
        # Set appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize database
        # Try to get credentials from environment variables
        # You can set these in your system or create a .env file
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.db = DatabaseManager(supabase_url, supabase_key)
        
        # Cart for issue items
        self.cart_items: List[Dict] = []
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the main UI with tabs."""
        # Create tabview
        self.tabview = ctk.CTkTabview(self, width=1180, height=750)
        self.tabview.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Create tabs
        self.issue_tab = self.tabview.add("Issue Items")
        self.returns_tab = self.tabview.add("Returns")
        self.inventory_tab = self.tabview.add("Inventory")
        self.students_tab = self.tabview.add("Students")
        
        # Build each tab
        self._build_issue_tab()
        self._build_returns_tab()
        self._build_inventory_tab()
        self._build_students_tab()
    
    def _build_issue_tab(self):
        """Build the Issue Items tab."""
        # Input section frame
        input_frame = ctk.CTkFrame(self.issue_tab, corner_radius=10)
        input_frame.pack(pady=20, padx=20, fill="x")
        
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
    
    def _build_returns_tab(self):
        """Build the Returns tab."""
        label = ctk.CTkLabel(
            self.returns_tab,
            text="Returns Management",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        label.pack(pady=50)
        
        info_label = ctk.CTkLabel(
            self.returns_tab,
            text="Returns functionality will be implemented here.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        info_label.pack(pady=20)
    
    def _build_inventory_tab(self):
        """Build the Inventory tab."""
        label = ctk.CTkLabel(
            self.inventory_tab,
            text="Inventory Overview",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        label.pack(pady=20)
        
        # Scrollable frame for inventory items
        scroll_frame = ctk.CTkScrollableFrame(self.inventory_tab, width=1100, height=600)
        scroll_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self._load_inventory_display(scroll_frame)
    
    def _build_students_tab(self):
        """Build the Students tab."""
        label = ctk.CTkLabel(
            self.students_tab,
            text="Student Management",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        label.pack(pady=20)
        
        # Scrollable frame for students
        scroll_frame = ctk.CTkScrollableFrame(self.students_tab, width=1100, height=600)
        scroll_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self._load_students_display(scroll_frame)
    
    def _load_students(self):
        """Load students into dropdown."""
        students = self.db.get_all_students()
        student_values = [f"{s['name']} ({s['student_id']})" for s in students]
        self.student_dropdown.configure(values=student_values)
        if student_values:
            self.student_dropdown.set(student_values[0])
    
    def _add_to_cart(self):
        """Add item to cart based on input (serial number or component name)."""
        input_text = self.issue_entry.get().strip()
        
        if not input_text:
            self._show_error("Please enter a serial number or component name.")
            return
        
        # Check if it's a serial number (try to find by serial first)
        item = self.db.get_item_by_serial(input_text)
        
        if item:
            # It's a serial number
            self._handle_serial_number(item)
        else:
            # It might be a component name
            self._handle_component_name(input_text)
    
    def _handle_serial_number(self, item: Dict):
        """Handle when user enters a serial number."""
        status = item.get("status", "").lower()
        
        if status == "issued":
            self._show_error("Item already issued!", "Error")
            return
        elif status == "damaged":
            self._show_warning(item)
        elif status == "available":
            self._add_item_to_cart(item)
        else:
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
        """Load and display inventory items."""
        inventory_list = self.db.get_all_inventory()
        items_list = self.db.get_all_items()
        
        if not inventory_list:
            label = ctk.CTkLabel(
                parent,
                text="No inventory items found.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            label.pack(pady=50)
            return
        
        # Header
        header_frame = ctk.CTkFrame(parent, corner_radius=5)
        header_frame.pack(fill="x", pady=5, padx=10)
        
        headers = ["Component Name", "Total Quantity", "Available", "Issued", "Damaged"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            label.grid(row=0, column=i, padx=20, pady=10, sticky="w")
        
        # Calculate counts for each inventory item
        for inv in inventory_list:
            available = sum(1 for item in items_list 
                          if item.get("inventory_id") == inv["id"] and item.get("status") == "Available")
            issued = sum(1 for item in items_list 
                        if item.get("inventory_id") == inv["id"] and item.get("status") == "Issued")
            damaged = sum(1 for item in items_list 
                         if item.get("inventory_id") == inv["id"] and item.get("status") == "Damaged")
            
            row_frame = ctk.CTkFrame(parent, corner_radius=5)
            row_frame.pack(fill="x", pady=5, padx=10)
            
            name_label = ctk.CTkLabel(row_frame, text=inv["name"], font=ctk.CTkFont(size=14))
            name_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
            
            total_label = ctk.CTkLabel(row_frame, text=str(inv.get("total_qty", 0)), font=ctk.CTkFont(size=14))
            total_label.grid(row=0, column=1, padx=20, pady=10, sticky="w")
            
            avail_label = ctk.CTkLabel(row_frame, text=str(available), font=ctk.CTkFont(size=14), text_color="green")
            avail_label.grid(row=0, column=2, padx=20, pady=10, sticky="w")
            
            issued_label = ctk.CTkLabel(row_frame, text=str(issued), font=ctk.CTkFont(size=14), text_color="blue")
            issued_label.grid(row=0, column=3, padx=20, pady=10, sticky="w")
            
            damaged_label = ctk.CTkLabel(row_frame, text=str(damaged), font=ctk.CTkFont(size=14), text_color="red")
            damaged_label.grid(row=0, column=4, padx=20, pady=10, sticky="w")
    
    def _load_students_display(self, parent):
        """Load and display students."""
        students = self.db.get_all_students()
        
        if not students:
            label = ctk.CTkLabel(
                parent,
                text="No students found.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            label.pack(pady=50)
            return
        
        # Header
        header_frame = ctk.CTkFrame(parent, corner_radius=5)
        header_frame.pack(fill="x", pady=5, padx=10)
        
        headers = ["Student ID", "Name"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            label.grid(row=0, column=i, padx=50, pady=10, sticky="w")
        
        # Student rows
        for student in students:
            row_frame = ctk.CTkFrame(parent, corner_radius=5)
            row_frame.pack(fill="x", pady=5, padx=10)
            
            id_label = ctk.CTkLabel(row_frame, text=student["student_id"], font=ctk.CTkFont(size=14))
            id_label.grid(row=0, column=0, padx=50, pady=10, sticky="w")
            
            name_label = ctk.CTkLabel(row_frame, text=student["name"], font=ctk.CTkFont(size=14))
            name_label.grid(row=0, column=1, padx=50, pady=10, sticky="w")


def main():
    """Main entry point."""
    app = LabApp()
    app.mainloop()


if __name__ == "__main__":
    main()
