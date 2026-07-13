---
title: Meter Test System - User Manual
version: 1.0
date: 2026-06-20
---

# Cover Page

**Software Name:** Meter Test System (PerformanceTester)
**Version:** 1.0.0
**Company Name:** [Company Name]
**Document Version:** 1.0
**Release Date:** 20/06/2026

[INSERT SOFTWARE LOGO HERE]

[INSERT APPLICATION SCREENSHOT HERE]

---

# Revision History

| Version | Date       | Author  | Description     |
| ------- | ---------- | ------- | --------------- |
| 1.0     | 20/06/2026 | Company | Initial Release |

---

# Table of Contents
1. [Introduction](#1-introduction)
2. [System Requirements](#2-system-requirements)
3. [Installation Guide](#3-installation-guide)
4. [Getting Started](#4-getting-started)
5. [User Interface Overview](#5-user-interface-overview)
6. [Login and User Management](#6-login-and-user-management)
7. [Core Workflow](#7-core-workflow)
8. [Feature-by-Feature Guide](#8-feature-by-feature-guide)
9. [Data Entry Guide](#9-data-entry-guide)
10. [Reports and Exports](#10-reports-and-exports)
11. [Settings and Configuration](#11-settings-and-configuration)
12. [Notifications and Alerts](#12-notifications-and-alerts)
13. [Troubleshooting Guide](#13-troubleshooting-guide)
14. [Frequently Asked Questions (FAQ)](#14-frequently-asked-questions-faq)
15. [Best Practices](#15-best-practices)
16. [Maintenance Procedures](#16-maintenance-procedures)
17. [Glossary](#17-glossary)
18. [Support Information](#18-support-information)
19. [Appendix A – Screen Catalog](#appendix-a--screen-catalog)
20. [Appendix B – Process Flow Diagrams](#appendix-b--process-flow-diagrams)

---

# 1. Introduction

## Purpose of the software
The Meter Test System (PerformanceTester) is an advanced, industrial-grade software platform designed to automate the testing, validation, and performance analysis of electrical energy meters. The software seamlessly orchestrates complex test sequences including Fault Current Making Capacity (FCMC) and Short Circuit Current Capacity (SCCC) tests while interfacing with Programmable Logic Controllers (PLCs), Multi-Function Meters (MFMs), Energy Meters (via DLMS/Serial), and high-precision oscilloscopes (PicoScope).

## Intended users
This manual is intended for testing engineers, laboratory technicians, quality assurance personnel, and system administrators who operate or maintain the Meter Test System in an industrial laboratory environment.

## System overview
The software acts as the central command hub for the testing rig. It manages hardware connections asynchronously, ensures operator safety via hardware and software interlocks, executes customizable test sequences, monitors real-time variables (Voltage, Current, Power Factor), and generates comprehensive PDF/CSV reports.

## Key capabilities
* Automated FCMC and SCCC test sequencing.
* Real-time hardware control via Modbus TCP/RTU.
* DLMS and Serial meter communication profile management.
* High-speed waveform capture and analysis via PicoScope.
* Dynamic UI with light/dark theme support.
* Comprehensive centralized logging and error handling.

## Benefits
* **Increased Efficiency:** Automates manual testing procedures, reducing test cycle times.
* **Enhanced Accuracy:** Captures precise waveform data and meter readings without human error.
* **Safety First:** Integrated emergency stop mechanisms and hardware interlock monitoring.
* **Traceability:** Automatic database logging and report generation for all test runs.

[INSERT SYSTEM OVERVIEW DIAGRAM]

---

# 2. System Requirements

To ensure optimal performance and stability, the host computer running the Meter Test System must meet the following requirements.

| Component | Minimum Requirement | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 (64-bit) | Windows 11 (64-bit) |
| **Processor** | Intel Core i3 or equivalent | Intel Core i5/i7 or equivalent |
| **RAM** | 4 GB | 8 GB or higher |
| **Disk Space** | 500 MB free space | 1 GB SSD free space |
| **Network** | Ethernet Port (for PLC) | Gigabit Ethernet Port |
| **Ports** | Minimum 2x USB 2.0/3.0 | 4x USB 3.0 (for PicoScope & COM) |
| **Display** | 1366x768 Resolution | 1920x1080 (Full HD) Resolution |
| **Software** | MySQL Server 8.0+ | MySQL Server 8.0+ |

> [!NOTE] 
> Dedicated COM ports (or reliable USB-to-RS485 adapters) are strictly required for reliable communication with the MFM and Energy Meters.

---

# 3. Installation Guide

This section provides step-by-step installation instructions for deploying the Meter Test System on a new workstation.

## 3.1. Downloading software
1. Obtain the official software installation package (`MeterTestSystem_Setup.exe`) from your system administrator or the official company portal.
2. Download and install the MySQL Server 8.0 installer from the official MySQL website.
3. Download the PicoScope SDK and Drivers from the Pico Technology website.

## 3.2. Installing prerequisites
1. **Install MySQL:** Run the MySQL installer. Setup a root user and make note of the password. Create a new database named `meter_test_db`.
2. **Install Drivers:** Run the PicoScope driver installer and follow the on-screen prompts. Plug in any USB-to-Serial adapters and allow Windows to install the respective VCP (Virtual COM Port) drivers.

## 3.3. Running installer
1. Run `MeterTestSystem_Setup.exe` with Administrator privileges.
2. Follow the Installation Wizard instructions.
3. Choose the default installation directory (e.g., `C:\Program Files\Company\MeterTestSystem`).
4. Click **Install** and wait for the process to complete.
5. Check "Launch Meter Test System" and click **Finish**.

## 3.4. First launch
Upon the first launch, the application will attempt to connect to the database and hardware. If the default configuration does not match your environment, hardware status indicators will show disconnected states. Navigate to the **Settings** page immediately to configure your environment.

[INSERT INSTALLER SCREENSHOT]
[INSERT INSTALLATION WIZARD SCREENSHOT]

---

# 4. Getting Started

## 4.1. Launching the software
Double-click the **Meter Test System** icon on your desktop or launch it from the Windows Start Menu. The application will initialize the core services, establish database connections, and spin up background threads for device communication.

## 4.2. Initial setup
Before running any tests, you must ensure the system is communicating with all hardware.
1. Look at the bottom status bar to verify the Database Connection Status.
2. Look at the Hardware Status indicators on the Dashboard. 
3. If any device (PLC, MFM, Energy Meter, or PicoScope) is disconnected, proceed to the Settings page.

## 4.3. First-time configuration
1. Open the **Settings** page from the left navigation sidebar.
2. Update the **Database Configuration** with your MySQL host, user, password, and database name.
3. Update the **Hardware Configuration** (COM Ports, IP Addresses, Baud rates).
4. Click **Save Settings** and then click **Reload Devices** to restart the connection threads.

## 4.4. Understanding the interface
The application features a modern, sidebar-driven interface.
* **Left Sidebar:** Used for navigating between different modules (Dashboard, Logs, Debug, Reports, Sequence, Profiles, Settings).
* **Main Content Area:** Displays the active module.
* **Top Bar:** Contains the Page Title and the Light/Dark theme toggle switch.
* **Status Bar:** Displays active hardware status, active alarms, and the Emergency Stop button.

[INSERT SCREENSHOT – HOME SCREEN]
[INSERT SCREENSHOT – MAIN DASHBOARD]

---

# 5. User Interface Overview

The software interface is divided into seven major screens accessible via the collapsible sidebar. 

[INSERT SCREENSHOT – SIDEBAR NAVIGATION]

### Screen Components

| Component | Description |
| :--- | :--- |
| **Hamburger Menu** | Expands or collapses the sidebar for more screen real-estate. |
| **Test Dashboard** | The main execution screen for running and monitoring tests. |
| **System Logs** | Displays real-time application and communication logs. |
| **Debug Screen** | Provides manual control over individual PLC coils and meter registers. |
| **Reports** | Interface for viewing, filtering, and exporting historical test data. |
| **Sequence Viewer** | Allows users to build and modify automated test step sequences. |
| **Meter Profiles** | Database of specific meter models and their communication commands (DLMS/Serial). |
| **Settings** | System-wide configuration for database, UI, and hardware connections. |
| **Theme Toggle** | A button located in the top-right corner to switch between Light and Dark modes. |
| **Emergency Stop** | A critical safety button that halts all hardware operations instantly. |

---

# 6. Login and User Management

> [!NOTE]
> Depending on your organization's deployment, User Authentication may be enabled or disabled globally.

## 6.1. Login procedure
1. Upon launching, the Login Prompt will appear.
2. Enter your assigned **Username** and **Password**.
3. Click **Login**. Incorrect credentials will display an access denied warning.

## 6.2. Logout procedure
1. Click on the User Profile icon in the top right corner.
2. Select **Logout** from the dropdown menu.
3. The application will return to the Login screen. Active tests must be aborted prior to logging out.

## 6.3. User roles and Access permissions
* **Operator:** Can view the dashboard, run existing test sequences, and view reports. Cannot modify settings, profiles, or trigger manual debug coils.
* **Technician/Engineer:** Can run tests, modify sequence configurations, create meter profiles, and use the debug screen.
* **Administrator:** Has full access, including database configuration, user management, and core system settings.

[INSERT SCREENSHOT – LOGIN SCREEN]
[INSERT SCREENSHOT – USER MANAGEMENT SCREEN]

---

# 7. Core Workflow

This section outlines the primary operating procedures of the software.

## 7.1. Executing a Standard Test (FCMC/SCCC)

**Purpose:** To perform a predefined Fault Current Making Capacity or Short Circuit Current Capacity test on a connected energy meter.

**Prerequisites:** 
* Meter physically connected to the test rig.
* PLC, PicoScope, and MFM connected and communicating (Status: Green).
* Load banks properly configured.

**Step-by-step procedure:**
1. Navigate to the **Test Dashboard**.
2. Select the target **Meter Profile** from the dropdown menu.
3. Select the desired **Test Sequence** (e.g., FCMC Standard Test).
4. Verify the safety perimeter is clear.
5. Click the **Start Test** button.
6. Observe the real-time progress bar and current active step.
7. The system will automatically trigger the necessary PLC coils (e.g., closing contactors), read data from the MFM, and communicate with the Energy Meter.
8. Wait for the sequence to complete. A "Test Completed Successfully" prompt will appear.

**Expected results:**
The test data, including pass/fail status and PicoScope waveform captures, are saved to the database. A quick summary report is displayed.

**Common mistakes:**
* Forgetting to acknowledge the Fusing Mode on the hardware panel before starting an SCCC test.
* Running a test with the wrong meter profile selected, causing communication timeouts.

[INSERT SCREENSHOT – WORKFLOW DIAGRAM]
[INSERT SCREENSHOT – TEST EXECUTION DASHBOARD]

---

# 8. Feature-by-Feature Guide

## 8.1. Test Dashboard
### Purpose
The central hub for initiating and monitoring automated tests.
### When to Use
Use this screen whenever you are actively testing a device.
### How to Use
1. Verify hardware statuses at the bottom of the screen.
2. Select the Test Sequence and Meter Profile.
3. Press **Start** to begin, **Stop** to halt normally, or **Abort/EMERGENCY STOP** for immediate termination.
### Expected Result
The test runs automatically through its defined steps, updating the UI with live MFM readings (Voltage, Current, Power Factor).
[INSERT SCREENSHOT – TEST DASHBOARD]

## 8.2. Meter Profiles
### Purpose
To define how the software communicates with various brands and models of energy meters.
### When to Use
Use this when introducing a new type of meter to the laboratory.
### How to Use
1. Navigate to **Meter Profiles**.
2. Click **Add New Profile**.
3. Select the communication mode (Serial or DLMS).
4. Input the serial settings (Baudrate) or DLMS settings (Client/Server addresses, Authentication keys).
5. Define the command dictionary (e.g., Command Name: `read_serial_number`, Value: `7E A0...`).
6. Click **Save**.
### Notes
Ensure hexadecimal strings are formatted correctly based on the protocol requirements.
[INSERT SCREENSHOT – METER PROFILES PAGE]

## 8.3. Sequence Viewer
### Purpose
To view, build, and modify the automated steps that make up a test.
### When to Use
When test standards change or a new type of test workflow is required.
### How to Use
1. Open the **Sequence Viewer**.
2. Select an existing sequence to edit, or create a new one.
3. Add steps to the sequence. A step can be: `TRIGGER_COIL`, `READ_METER`, `WAIT`, or `CAPTURE_WAVEFORM`.
4. Arrange the steps using the up/down arrows.
5. Click **Save Sequence**.
[INSERT SCREENSHOT – SEQUENCE VIEWER PAGE]

## 8.4. System Logs
### Purpose
To provide a diagnostic view of all background software activities.
### When to Use
Whenever an error occurs or a test behaves unexpectedly.
### How to Use
1. Open the **System Logs** page.
2. Review the color-coded logs (INFO = Blue/White, WARNING = Yellow, ERROR = Red).
3. Use the **Filter** dropdown to show only Errors.
4. Click **Export** to save the log to a text file for IT support.
[INSERT SCREENSHOT – SYSTEM LOGS PAGE]

## 8.5. Debug Screen
### Purpose
Manual override and testing of individual hardware components.
### When to Use
During calibration, maintenance, or when troubleshooting a specific hardware failure.
### How to Use
1. Open the **Debug Screen**.
2. To toggle a PLC relay, locate the coil (e.g., `CONTACTOR_120A_LOAD_BANK`) and click the **Toggle** switch.
3. To read the MFM, click **Read Registers** to view raw voltage and current values.
### Notes
> [!WARNING]
> Use extreme caution on this screen. Manually activating contactors out of sequence can damage hardware or pose safety risks.
[INSERT SCREENSHOT – DEBUG PAGE]

## 8.6. Reports
### Purpose
To search, view, and export historical test data.
### When to Use
To generate documentation for clients or internal quality audits.
### How to Use
1. Open the **Reports** page.
2. Use the date-range picker and serial number search field to find a specific test run.
3. Select the test from the table.
4. Click **Generate PDF**.
[INSERT SCREENSHOT – REPORTS PAGE]

---

# 9. Data Entry Guide

When configuring the system, particularly in the Settings, Sequence Viewer, or Meter Profiles screens, adhere to the following rules:

* **Required fields:** Highlighted with a red asterisk (*). The system will not save the form if these are empty.
* **IP Addresses:** Must follow valid IPv4 format (e.g., `192.168.0.123`).
* **COM Ports:** Enter exactly as shown in Windows Device Manager (e.g., `COM1`, `COM12`).
* **Validation rules:** Baud rates must be standard integers (9600, 19200, 115200). DLMS keys must be valid Base64 or Hex strings depending on the standard.
* **Save operations:** Always click the **Save** or **Apply** button at the bottom of the form. Changes are not saved automatically.
* **Delete operations:** Deleting a profile or sequence will prompt a confirmation dialog. Deleted configurations cannot be recovered.

[INSERT SCREENSHOT – DATA ENTRY SCREEN]

---

# 10. Reports and Exports

The software provides robust reporting capabilities to ensure traceability of all meter tests.

## Generating reports
Navigate to the Reports module, select a completed test, and click **Generate Report**. The system compiles the test metadata, pass/fail status, MFM readings, and any PicoScope waveform snapshots into a formatted document.

## Exporting data
Data can be exported in two formats:
1. **PDF:** Best for sharing with clients and final documentation. Includes charts and formatting.
2. **CSV:** Best for internal engineering analysis. Exports raw data points from the test run.

## Filters and Search tools
You can filter the historical test database by:
* Test Date (Start and End)
* Meter Serial Number
* Test Type (FCMC / SCCC)
* Result (Pass / Fail)

[INSERT SCREENSHOT – REPORT GENERATION PAGE]
[INSERT SCREENSHOT – EXPORT DIALOG]

---

# 11. Settings and Configuration

The Settings page is restricted to administrative users and dictates how the software interacts with the physical world.

| Setting | Description | Recommended Value |
| :--- | :--- | :--- |
| **DB Host** | IP address of the MySQL Server. | `localhost` or `127.0.0.1` |
| **DB User** | MySQL username. | `root` |
| **DB Password** | MySQL password. | *(Your secure password)* |
| **PLC IP Address** | Network IP of the Modbus TCP PLC. | `192.168.0.123` |
| **PLC Port** | Modbus TCP Port. | `502` |
| **Energy Meter Port** | COM port for direct meter communication. | Varies (e.g., `COM5`) |
| **MFM Meter Port** | COM port for the Multi-Function Meter. | Varies (e.g., `COM6`) |
| **MFM Slave ID** | Modbus RTU Slave ID of the MFM. | `1` |
| **Safety: Max Voltage** | Software cutoff limit for voltage. | `250.0` V |
| **Safety: Max Current** | Software cutoff limit for current. | `10.0` A |

[INSERT SCREENSHOT – SETTINGS PAGE]

---

# 12. Notifications and Alerts

The software uses a standardized alert system to keep the operator informed of system state.

* **Information (Blue/Green):** Routine operations, test step completions, successful connections.
* **Warning (Yellow):** Non-critical issues such as a temporary meter timeout that will be retried, or a sequence step taking longer than expected.
* **Error (Red):** Critical failures. e.g., Database connection lost, PLC disconnected, Modbus CRC error.
* **Emergency Stop (Flashing Red):** Indicates the physical or software E-STOP has been triggered. All automated processes are locked out until the system is reset.

[INSERT SCREENSHOT – ALERT EXAMPLE]

---

# 13. Troubleshooting Guide

If you encounter issues, consult this table before contacting technical support.

| Problem | Possible Cause | Solution |
| :--- | :--- | :--- |
| **Application fails to launch** | Missing Python libraries or corrupted installation. | Re-run the installer or contact IT to verify the Python environment. |
| **Database connection failed** | MySQL service is not running or credentials changed. | Open Windows Services, ensure 'MySQL80' is running. Check Settings page. |
| **PLC connection timeout** | Incorrect IP or network cable unplugged. | Ping the PLC IP from command prompt. Check ethernet cables. |
| **Energy Meter timeout** | Incorrect COM port or Baud rate. | Verify COM port in Windows Device Manager. Check Meter Profile baud rate. |
| **PicoScope not found** | USB cable disconnected or drivers missing. | Replug the USB. Reinstall PicoScope SDK drivers. |
| **Emergency stop triggers randomly** | Physical E-STOP button is slightly depressed or wiring loose. | Check the physical button on the test rig control panel. |
| **MFM meter reads 0 V / 0 A** | Modbus communicating, but CT/PT not wired. | Check the physical voltage and current sensing lines on the MFM. |
| **DLMS authentication failed** | Incorrect password, Client ID, or System Title. | Edit the Meter Profile and double-check the DLMS keys provided by the manufacturer. |
| **Report generation fails** | The target PDF file is currently open in Adobe Reader. | Close the PDF file and try generating the report again. |
| **Modbus CRC error** | Electrical noise on the RS485 line or incorrect parity. | Ensure RS485 cables are shielded. Verify parity (NONE/EVEN/ODD) in settings. |
| **Cannot save meter profile** | Database write permissions restricted. | Ensure the MySQL user has INSERT/UPDATE privileges. |
| **Application crashes during test** | Insufficient RAM or huge PicoScope buffer. | Close background applications. Check PicoScope capture duration settings. |
| **Sequence Viewer shows blank** | Database tables are empty or corrupted. | Restore database from backup or manually create a new sequence. |
| **Logs not updating** | Logging level set too high (e.g., Critical Only). | Restart the application to reset logger defaults. |
| **FCMC test fails to start** | Load bank contactor interlock active. | Ensure the test rig is in the correct initial state before starting. |
| **SCCC test fails to start** | Pre-fusing mode not acknowledged on PLC. | Manually acknowledge the Fusing Mode via the hardware panel or Debug screen. |
| **Relay clicks but no power applied** | PLC coil activated, but physical contactor is faulty. | Hardware issue. Have an electrician inspect the 120A contactors. |
| **Hardware status shows "Disconnected"** | App started before USB devices were plugged in. | Go to Settings and click **Reload Devices**. |
| **Unknown device type error** | Corruption in `device_config.json`. | Contact support to restore the default configuration files. |
| **UI freezes during capture** | PicoScope driver blocking the main thread. | Ensure the software is running the latest version with asynchronous drivers. |

---

# 14. Frequently Asked Questions (FAQ)

### 1. What is the purpose of this software?
It automates the testing of electrical energy meters, specifically controlling high-current tests (FCMC/SCCC) while logging data safely and accurately.

### 2. What does FCMC mean?
Fault Current Making Capacity. It tests the meter's ability to safely close its internal switch into a short-circuit fault condition.

### 3. What does SCCC mean?
Short Circuit Current Capacity. It tests the meter's ability to withstand a massive short-circuit current for a brief duration while its switch is already closed.

### 4. How do I add a new meter to the system?
Navigate to the **Meter Profiles** page, click "Add New Profile", define the serial or DLMS parameters, and save.

### 5. Can I test multiple meters at once?
Currently, the software is designed for single-station precision testing. Multi-station testing requires a different hardware rig and software version.

### 6. How do I change the database password?
Change it in MySQL using standard database tools, then update the password in the software's **Settings** page.

### 7. What do I do if an Emergency Stop is triggered?
Ensure the hardware area is safe. Clear the physical E-STOP button (twist to release), then acknowledge the software alarm to resume operations.

### 8. How do I export my test results?
Go to the **Reports** page, find your test, and click **Export PDF** or **Export CSV**.

### 9. Is an internet connection required?
No. The software runs completely offline on the local network (for the PLC) and local database.

### 10. Where are the system logs saved?
Logs are visible in the **System Logs** UI and are also saved to the `logs/` directory in the application installation folder.

### 11. How do I change from Serial to DLMS communication?
In the **Test Dashboard**, simply select a Meter Profile that is configured for DLMS. The system dynamically switches drivers in the background.

### 12. Can I manually trigger PLC coils for testing?
Yes, using the **Debug Screen**. Administrative access is required, and it should only be done by trained personnel.

### 13. What is the PicoScope used for?
It captures high-resolution, microsecond-level voltage and current waveforms during the split-second short circuit events for detailed analysis.

### 14. How often should I backup the database?
It is recommended to run a MySQL database dump weekly, or implement an automated daily backup script on the host PC.

### 15. What are the minimum system requirements?
Windows 10, Core i3, 4GB RAM. See Section 2 for detailed requirements.

### 16. How do I view past reports?
All past tests are permanently stored. Use the **Reports** page and its date-filter tools to browse history.

### 17. Can I customize the test sequence?
Yes. Engineers can use the **Sequence Viewer** to add, remove, or modify steps (like changing wait times or trigger sequences).

### 18. Does the software support Dark Mode?
Yes. Click the Theme Toggle switch in the top right corner of the application window to switch between Light and Dark aesthetics.

### 19. What should I do if a test aborts unexpectedly?
Check the **System Logs** immediately to identify the failure point (e.g., meter stopped responding, or safety current limit exceeded).

### 20. Who do I contact for support?
Check the Support Information section of this manual for contact details.

---

# 15. Best Practices

* **Always Verify Connections:** Before starting a day of testing, briefly use the Debug screen to ping the MFM and PLC to ensure hardware is responsive.
* **Database Backups:** Ensure IT has scheduled a daily automated backup of the `meter_test_db` MySQL database to prevent data loss.
* **Profile Management:** Do not edit "Default" meter profiles. If a test standard changes, create a new profile (e.g., "MeterBrandX_v2") to preserve historical test integrity.
* **Safety First:** Never bypass physical interlocks or rely solely on software safety cutoffs. Always use the physical E-STOP if a hazardous condition arises.
* **Log Retention:** Periodically clear out old text log files from the `logs/` directory to save disk space, though they are generally very small.

---

# 16. Maintenance Procedures

To keep the Meter Test System running smoothly:

## 16.1. Backup procedures
Use MySQL Workbench or the `mysqldump` command-line utility to export the entire database structure and data. 

## 16.2. Software updates
When a new version is released, close the application completely. Run the new installer. Your database and configuration files (`device_config.json`, `modbus_config.json`) will be preserved automatically.

## 16.3. Database maintenance
If the database grows exceptionally large (after tens of thousands of tests), consider archiving tests older than 3 years to maintain query performance on the Reports page.

[INSERT SCREENSHOT – MAINTENANCE SCREEN]

---

# 17. Glossary

* **PLC (Programmable Logic Controller):** The industrial computer responsible for opening and closing high-power contactors.
* **MFM (Multi-Function Meter):** A secondary reference meter used to measure the gross voltage and current running through the test rig.
* **DLMS (Device Language Message Specification):** A global standard for smart meter communication.
* **FCMC:** Fault Current Making Capacity.
* **SCCC:** Short Circuit Current Capacity.
* **PicoScope:** A PC-based high-resolution digital oscilloscope.
* **Modbus RTU/TCP:** An industrial communication protocol used to talk to the PLC and MFM.
* **Coil:** In Modbus terminology, a discrete ON/OFF binary output (e.g., a relay or contactor).

---

# 18. Support Information

If you require technical assistance, bug reporting, or feature requests, please reach out to our dedicated support team.

**Company Name:** Company Technologies Ltd.
**Support Email:** support@company-tech-domain.com
**Support Phone:** +1 (800) 555-0199
**Website:** www.company-tech-domain.com/support
**Business Hours:** Monday - Friday, 9:00 AM to 5:00 PM (EST)

---

# Appendix A – Screen Catalog

This appendix serves as a visual index of all major application interfaces.

| Screen Name | Purpose |
| :--- | :--- |
| **Login Screen** | User authentication. |
| **Home / Dashboard Screen** | Main testing and execution hub. |
| **System Logs Screen** | Diagnostic logging and system event tracing. |
| **Debug Screen** | Manual hardware control and register polling. |
| **Reports Screen** | Historical data viewing and exporting. |
| **Sequence Viewer Screen** | Test step programming and automation design. |
| **Meter Profiles Screen** | Management of communication protocols and device keys. |
| **Settings Screen** | System-wide hardware and database configuration. |
| **User Management Screen** | Administrator control of operator accounts. |

[INSERT SCREENSHOT – LOGIN SCREEN]
[INSERT SCREENSHOT – HOME / DASHBOARD SCREEN]
[INSERT SCREENSHOT – SYSTEM LOGS SCREEN]
[INSERT SCREENSHOT – DEBUG SCREEN]
[INSERT SCREENSHOT – REPORTS SCREEN]
[INSERT SCREENSHOT – SEQUENCE VIEWER SCREEN]
[INSERT SCREENSHOT – METER PROFILES SCREEN]
[INSERT SCREENSHOT – SETTINGS SCREEN]
[INSERT SCREENSHOT – USER MANAGEMENT SCREEN]

---

# Appendix B – Process Flow Diagrams

Visual representations of the core testing logic and system architecture.

[INSERT SCREENSHOT – PROCESS FLOW DIAGRAM - SYSTEM ARCHITECTURE]
[INSERT SCREENSHOT – PROCESS FLOW DIAGRAM - FCMC TEST LOGIC]
[INSERT SCREENSHOT – PROCESS FLOW DIAGRAM - SCCC TEST LOGIC]
[INSERT SCREENSHOT – PROCESS FLOW DIAGRAM - DLMS AUTHENTICATION WORKFLOW]

---
*End of Document*
