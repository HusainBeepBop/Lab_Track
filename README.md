# LabTrack: Component Inventory Management System 🧪📦

![Status](https://img.shields.io/badge/Status-Active_Development-green)
![Stack](https://img.shields.io/badge/Tech-Electron_|_React_|_Supabase-blue)

## 📖 The Story (The "Why")
During a critical robotics competition preparation ("RoboFest"), our university lab faced a major bottleneck: valuable sensors were missing, components were issued without documentation, and broken parts were returned into the "Working" bin, causing delays for other students.

I built **LabTrack** to solve this. It is a desktop application designed for fast-paced engineering labs to track assets, manage student issues, and enforce accountability for equipment conditions.

## 🚀 Key Features

### 1. Dynamic Inventory Tracking
- **Customizable Fields:** Not all components are the same. A Raspberry Pi needs a "MAC Address" field, while a resistor just needs a count. LabTrack uses **JSONB** to allow the professor to add custom data fields on the fly.
- **Real-Time Sync:** Built on **Supabase**, ensuring that if the Lab Assistant updates stock on the main PC, the Professor sees it instantly on their laptop.

### 2. Granular Return Logic
- **Condition Reporting:** When a student returns items, the system forces a check: *Working, Damaged,* or *Lost*.
- **Automatic Sorting:** "Damaged" items are isolated in the database and not added back to the available stock pool, preventing broken sensors from being re-issued.

### 3. Student Accountability
- Tracks history of issues and returns.
- Calculates overdue times automatically.
- "Notes" feature for specific comments on transaction items (e.g., "Returned without battery box").

## 🛠️ Tech Stack

* **Frontend:** React (Vite) + TypeScript
* **Styling:** Tailwind CSS + Shadcn UI
* **Wrapper:** Electron (for native Windows .exe deployment)
* **Backend/DB:** Supabase (PostgreSQL)

## 📸 Screenshots
*(To be added)*

## ⚡ How to Run Locally

1.  **Clone the repo**
    ```bash
    git clone [https://github.com/yourusername/lab-track.git](https://github.com/yourusername/lab-track.git)
    ```
2.  **Install dependencies**
    ```bash
    npm install
    ```
3.  **Setup Environment**
    Create a `.env` file with your Supabase credentials:
    ```
    VITE_SUPABASE_URL=your_url
    VITE_SUPABASE_ANON_KEY=your_key
    ```
4.  **Run in Development Mode**
    ```bash
    npm run dev:electron
    ```

## 🗺️ Roadmap
- [ ] QR Code generation for bin labels.
- [ ] Email notifications for overdue items.
- [ ] Analytics dashboard for "Most Used Components."

---
*Developed by Husain Lokhandwala for the Department of Mechanical and Aerospace Engineering, IITRAM.*