import os
import csv
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QComboBox, QPushButton, QTableWidget, 
                                QTableWidgetItem, QHeaderView, QFrame, QDialog,
                                QTextEdit, QFileDialog, QMessageBox, QSpacerItem,
                                QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QColor, QFont, QTextDocument, QPageSize, QPageLayout, QPixmap

class TestDetailsDialog(QDialog):
    """
    Detailed popup dialog showing all runs and failure reasons for a test session.
    """
    def __init__(self, session_data: Dict[str, Any], db_service, theme: str = "light", parent=None):
        super().__init__(parent)
        self.session_data = session_data
        self.db = db_service
        self.theme = theme
        self.setWindowTitle(f"Test Details - Session #{session_data.get('id')} ({session_data.get('meter_serial_number')})")
        self.resize(600, 500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header Info Card
        info_frame = QFrame(self)
        info_frame.setObjectName("info_frame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)
        
        serial = self.session_data.get("meter_serial_number", "Unknown")
        timestamp = self.session_data.get("timestamp")
        overall = self.session_data.get("overall_results", "N/A")
        
        lbl_title = QLabel(f"Meter Serial: {serial}", self)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0EA5E9;")
        info_layout.addWidget(lbl_title)
        
        lbl_meta = QLabel(f"Tested At: {timestamp} | Overall Result: {overall}", self)
        lbl_meta.setStyleSheet("font-size: 13px; color: #64748B;")
        info_layout.addWidget(lbl_meta)
        
        # Display overall failure reason if present
        fail_reason = self.session_data.get("failure_reason")
        if fail_reason:
            lbl_fail = QLabel(f"Failure Reason: {fail_reason}", self)
            lbl_fail.setWordWrap(True)
            lbl_fail.setStyleSheet("font-size: 13px; font-weight: 600; color: #EF4444; background-color: rgba(239, 68, 68, 0.1); padding: 8px; border-radius: 6px;")
            info_layout.addWidget(lbl_fail)
            
        layout.addWidget(info_frame)
        
        # Test Run Details Log List
        lbl_list_title = QLabel("Execution History & Sub-tests:", self)
        lbl_list_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_list_title)
        
        self.txt_details = QTextEdit(self)
        self.txt_details.setReadOnly(True)
        layout.addWidget(self.txt_details)
        
        # Load run history from DB
        self.load_run_history()
        
        # Footer Action Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_view_graphs = QPushButton("View Captured Graphs", self)
        self.btn_view_graphs.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold;")
        self.btn_view_graphs.clicked.connect(self.view_graphs)
        btn_layout.addWidget(self.btn_view_graphs)
        
        # Check if graphs exist
        import os
        graphs_dir = "logs/graphs"
        has_graphs = False
        if os.path.exists(graphs_dir):
            for file in os.listdir(graphs_dir):
                if file.startswith(f"session_{self.session_data.get('id')}_") and file.endswith(".png"):
                    has_graphs = True
                    break
        self.btn_view_graphs.setVisible(has_graphs)
        
        btn_close = QPushButton("Close", self)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        
        self.apply_theme()
        
    def view_graphs(self):
        import os
        graphs_dir = "logs/graphs"
        images = []
        if os.path.exists(graphs_dir):
            for file in os.listdir(graphs_dir):
                if file.startswith(f"session_{self.session_data.get('id')}_") and file.endswith(".png"):
                    images.append(os.path.join(graphs_dir, file))
                    
        if not images:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Captured Waveform Graphs")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        scroll = QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        vbox = QVBoxLayout(container)
        
        for img_path in images:
            test_name = os.path.basename(img_path).replace(f"session_{self.session_data.get('id')}_", "").replace('.png', '').replace('_', ' ').title()
            lbl_title = QLabel(f"{test_name}")
            lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 15px;")
            vbox.addWidget(lbl_title)
            
            lbl_img = QLabel()
            pixmap = QPixmap(img_path)
            # Scale to fit window width roughly
            scaled_pixmap = pixmap.scaledToWidth(750, Qt.SmoothTransformation)
            lbl_img.setPixmap(scaled_pixmap)
            vbox.addWidget(lbl_img)
            
        vbox.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        btn_close = QPushButton("Close", dialog)
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec()
        
    def load_run_history(self):
        runs = self.db.get_test_run_details(self.session_data.get("id"))
        
        if not runs:
            # Fallback to main record columns if no detailed run history exists yet
            html = "<h3>No detailed execution history logged.</h3>"
            for col in ['g2', 'g3', 'g5', 'g6', 'g7']:
                val = self.session_data.get(col)
                if val:
                    html += f"<p><b>Test {col.upper()}:</b> {val}</p>"
            self.txt_details.setHtml(html)
            return
            
        html = "<table width='100%' cellpadding='6' cellspacing='0' style='border-collapse: collapse;'>"
        html += "<tr style='background-color: rgba(14, 165, 233, 0.1);'>"
        html += "<th>Timestamp</th><th>Test Type</th><th>Status</th><th>Type</th></tr>"
        
        for run in runs:
            ts = run.get("run_timestamp")
            tt = run.get("test_type", "").upper()
            status = run.get("status", "N/A")
            is_sub = "Sub-sequence" if run.get("is_sub_test") else "Main Test"
            reason = run.get("failure_reason")
            
            color = "#10B981" if status == "PASS" else "#EF4444" if status == "FAIL" else "#F59E0B"
            
            html += f"<tr style='border-bottom: 1px solid rgba(148, 163, 184, 0.2);'>"
            html += f"<td>{ts}</td>"
            html += f"<td><b>{tt}</b></td>"
            html += f"<td><span style='color: {color}; font-weight: bold;'>{status}</span></td>"
            html += f"<td><i>{is_sub}</i></td>"
            html += "</tr>"
            
            if reason:
                if status == "PASS" and reason.startswith("Measurements:"):
                    html += f"<tr><td colspan='4' style='padding-left: 20px; color: #10B981; font-size: 12px; background-color: rgba(16, 185, 129, 0.05);'>"
                    html += f"<b>Details:</b> {reason}</td></tr>"
                else:
                    html += f"<tr><td colspan='4' style='padding-left: 20px; color: #EF4444; font-size: 12px; background-color: rgba(239, 68, 68, 0.05);'>"
                    html += f"<b>Error:</b> {reason}</td></tr>"
                
        html += "</table>"
        self.txt_details.setHtml(html)
        
    def apply_theme(self):
        if self.theme == "dark":
            self.setStyleSheet("""
                QDialog { background-color: #0F172A; }
                QFrame#info_frame { background-color: #1E293B; border-radius: 8px; border: 1px solid #334155; padding: 10px; }
                QTextEdit { background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; color: #E2E8F0; }
                QPushButton { background-color: #334155; color: #FFFFFF; border: none; border-radius: 6px; padding: 8px 16px; }
                QPushButton:hover { background-color: #475569; }
                QLabel { color: #F1F5F9; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #F8FAFC; }
                QFrame#info_frame { background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; padding: 10px; }
                QTextEdit { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; color: #1E293B; }
                QPushButton { background-color: #E2E8F0; color: #0F172A; border: none; border-radius: 6px; padding: 8px 16px; }
                QPushButton:hover { background-color: #CBD5E1; }
                QLabel { color: #0F172A; }
            """)


class ReportsPage(QWidget):
    """
    Highly styled interactive Reports Dashboard.
    """
    def __init__(self, device_manager=None, main_window=None):
        super().__init__()
        self.device_manager = device_manager
        self.main_window = main_window
        self.db = getattr(device_manager, "database_service", None) if device_manager else None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title Header
        self.lbl_title = QLabel("Reports & Analytics Dashboard", self)
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0284C7;")
        self.main_layout.addWidget(self.lbl_title)
        
        # 1. Summary Cards Layout
        self.metrics_layout = QHBoxLayout()
        self.metrics_layout.setSpacing(15)
        
        self.card_total = self.create_card("Total Sessions", "0", "#0EA5E9")
        self.card_pass = self.create_card("Pass Rate", "0%", "#10B981")
        self.card_fail = self.create_card("Failed Sessions", "0", "#EF4444")
        
        self.metrics_layout.addWidget(self.card_total)
        self.metrics_layout.addWidget(self.card_pass)
        self.metrics_layout.addWidget(self.card_fail)
        self.main_layout.addLayout(self.metrics_layout)
        
        # 2. Filters Frame
        self.frame_filters = QFrame(self)
        self.frame_filters.setObjectName("frame_filters")
        self.frame_filters.setMinimumHeight(65)
        
        filters_layout = QHBoxLayout(self.frame_filters)
        filters_layout.setContentsMargins(15, 10, 15, 10)
        filters_layout.setSpacing(15)
        
        # Serial Search Input
        self.txt_search_serial = QLineEdit(self)
        self.txt_search_serial.setPlaceholderText("Search Meter Serial...")
        self.txt_search_serial.textChanged.connect(self.load_data)
        filters_layout.addWidget(self.txt_search_serial, 2)
        
        # Status filter
        self.combo_status = QComboBox(self)
        self.combo_status.addItems(["All", "PASS", "FAIL", "CANCELLED"])
        self.combo_status.currentIndexChanged.connect(self.load_data)
        filters_layout.addWidget(self.combo_status, 1)
        
        # Buttons
        self.btn_refresh = QPushButton("Refresh", self)
        self.btn_refresh.clicked.connect(self.load_data)
        filters_layout.addWidget(self.btn_refresh)
        
        self.btn_reset = QPushButton("Reset Filters", self)
        self.btn_reset.clicked.connect(self.reset_filters)
        filters_layout.addWidget(self.btn_reset)
        
        self.main_layout.addWidget(self.frame_filters)
        
        # 3. Table View
        self.table_results = QTableWidget(self)
        self.table_results.setColumnCount(9)
        self.table_results.setHorizontalHeaderLabels([
            "ID", "Timestamp", "Meter Serial", "G2", "G3", "G5", "G6", "G7", "Overall Result"
        ])
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_results.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_results.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_results.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_results.doubleClicked.connect(self.show_details_dialog)
        self.main_layout.addWidget(self.table_results)
        
        # 4. Actions Panel
        self.actions_layout = QHBoxLayout()
        
        self.btn_export_pdf = QPushButton("Export Selected PDF", self)
        self.btn_export_pdf.setStyleSheet("background-color: #EF4444; color: #FFFFFF; border: none;")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        self.actions_layout.addWidget(self.btn_export_pdf)
        
        self.btn_export_csv = QPushButton("Export All to CSV", self)
        self.btn_export_csv.setStyleSheet("background-color: #10B981; color: #FFFFFF; border: none;")
        self.btn_export_csv.clicked.connect(self.export_csv)
        self.actions_layout.addWidget(self.btn_export_csv)
        
        self.actions_layout.addStretch()
        
        self.lbl_help = QLabel("Double-click any row to view complete detailed run logs & failure reasons.", self)
        self.lbl_help.setStyleSheet("color: #64748B; font-style: italic; font-size: 12px;")
        self.actions_layout.addWidget(self.lbl_help)
        
        self.main_layout.addLayout(self.actions_layout)
        
        # Apply styles
        self.update_styles()
        
    def create_card(self, title: str, value: str, color_hex: str) -> QFrame:
        card = QFrame(self)
        card.setObjectName("metric_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(4)
        
        lbl_title = QLabel(title.upper(), card)
        lbl_title.setObjectName("lbl_card_title")
        lbl_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748B; letter-spacing: 1px;")
        layout.addWidget(lbl_title)
        
        lbl_value = QLabel(value, card)
        lbl_value.setObjectName("lbl_card_value")
        lbl_value.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {color_hex};")
        layout.addWidget(lbl_value)
        
        return card
        
    def update_styles(self):
        theme = getattr(self.main_window, "current_theme", "light")
        if theme == "dark":
            bg = "#1E293B"
            border = "#334155"
            table_bg = "#0F172A"
        else:
            bg = "#FFFFFF"
            border = "#E2E8F0"
            table_bg = "#F8FAFC"
            
        self.frame_filters.setStyleSheet(f"""
            QFrame#frame_filters {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
        """)
        
        card_style = f"""
            QFrame#metric_card {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QFrame#metric_card QLabel {{
                border: none;
                background-color: transparent;
            }}
        """
        self.card_total.setStyleSheet(card_style)
        self.card_pass.setStyleSheet(card_style)
        self.card_fail.setStyleSheet(card_style)
        
        self.table_results.setStyleSheet(f"""
            QTableWidget {{
                background-color: {table_bg};
                border: 1px solid {border};
                gridline-color: {border};
            }}
            QHeaderView::section {{
                background-color: {bg};
                border-bottom: 2px solid {border};
            }}
        """)
        
    def reset_filters(self):
        self.txt_search_serial.clear()
        self.combo_status.setCurrentIndex(0)
        self.load_data()
        
    @Slot()
    def load_data(self):
        if not self.db:
            return
            
        filters = {
            "serial_number": self.txt_search_serial.text().strip(),
            "status": self.combo_status.currentText()
        }
        
        try:
            results = self.db.get_all_test_results(filters)
            self.populate_table(results)
            self.calculate_metrics(results)
        except Exception as e:
            print(f"Error loading report data: {e}")
            
    def populate_table(self, results):
        self.table_results.setRowCount(0)
        
        for row_idx, row in enumerate(results):
            self.table_results.insertRow(row_idx)
            
            # Populate columns
            self.table_results.setItem(row_idx, 0, QTableWidgetItem(str(row.get('id'))))
            self.table_results.setItem(row_idx, 1, QTableWidgetItem(str(row.get('timestamp'))))
            self.table_results.setItem(row_idx, 2, QTableWidgetItem(str(row.get('meter_serial_number'))))
            
            # G2-G7 columns
            for col_idx, col_name in enumerate(['g2', 'g3', 'g5', 'g6', 'g7']):
                val = row.get(col_name) or "-"
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if val == "PASS":
                    item.setForeground(QColor("#10B981"))
                elif val == "FAIL":
                    item.setForeground(QColor("#EF4444"))
                elif val == "CANCELLED":
                    item.setForeground(QColor("#F59E0B"))
                self.table_results.setItem(row_idx, col_idx + 3, item)
                
            # Overall Results column
            overall = row.get('overall_results') or "N/A"
            overall_item = QTableWidgetItem(overall)
            overall_item.setTextAlignment(Qt.AlignCenter)
            overall_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            if overall == "PASS":
                overall_item.setForeground(QColor("#10B981"))
            elif overall == "FAIL":
                overall_item.setForeground(QColor("#EF4444"))
            elif overall == "CANCELLED":
                overall_item.setForeground(QColor("#F59E0B"))
            self.table_results.setItem(row_idx, 8, overall_item)
            
    def calculate_metrics(self, results):
        total = len(results)
        passed = sum(1 for r in results if r.get('overall_results') == 'PASS')
        failed = sum(1 for r in results if r.get('overall_results') == 'FAIL')
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        self.card_total.findChild(QLabel, "lbl_card_value").setText(str(total))
        self.card_pass.findChild(QLabel, "lbl_card_value").setText(f"{pass_rate:.1f}%")
        self.card_fail.findChild(QLabel, "lbl_card_value").setText(str(failed))
        
    def show_details_dialog(self, model_index):
        if not self.db:
            return
        row = model_index.row()
        session_id = int(self.table_results.item(row, 0).text())
        
        # Load full row data
        filters = {"serial_number": self.table_results.item(row, 2).text()}
        all_res = self.db.get_all_test_results(filters)
        session_data = next((r for r in all_res if r.get('id') == session_id), None)
        
        if session_data:
            theme = getattr(self.main_window, "current_theme", "light")
            dialog = TestDetailsDialog(session_data, self.db, theme, self)
            dialog.exec()
            
    def export_csv(self):
        if not self.db:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
            
        filters = {
            "serial_number": self.txt_search_serial.text().strip(),
            "status": self.combo_status.currentText()
        }
        
        try:
            results = self.db.get_all_test_results(filters)
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Timestamp", "Meter Serial Number", "G2", "G3", "G5", "G6", "G7", "Overall Result", "Failure Reason"])
                for r in results:
                    writer.writerow([
                        r.get('id'), r.get('timestamp'), r.get('meter_serial_number'),
                        r.get('g2'), r.get('g3'), r.get('g5'), r.get('g6'), r.get('g7'),
                        r.get('overall_results'), r.get('failure_reason')
                    ])
            QMessageBox.information(self, "Success", "Report exported successfully to CSV.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV: {e}")
            
    def export_pdf(self):
        selected_row = self.table_results.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Export PDF", "Please select a test session from the table to export.")
            return
            
        session_id = int(self.table_results.item(selected_row, 0).text())
        serial = self.table_results.item(selected_row, 2).text()
        
        # Load detailed data
        filters = {"serial_number": serial}
        all_res = self.db.get_all_test_results(filters)
        session_data = next((r for r in all_res if r.get('id') == session_id), None)
        
        if not session_data:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF Report", f"Report_{serial}_{session_id}.pdf", "PDF Files (*.pdf)")
        if not file_path:
            return
            
        # Fetch run details
        runs = self.db.get_test_run_details(session_id)
        
        # Build premium HTML report content
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; margin: 30px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .meta-table {{ width: 100%; margin-bottom: 20px; border-collapse: collapse; }}
                .meta-table td {{ padding: 8px; border: 1px solid #E2E8F0; }}
                .meta-header {{ background-color: #F8FAFC; font-weight: bold; width: 30%; }}
                .section-title {{ font-size: 14pt; font-weight: bold; margin-top: 20px; margin-bottom: 5px; color: #0F172A; }}
                .runs-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                .runs-table th {{ background-color: #0EA5E9; color: white; padding: 10px; text-align: left; }}
                .runs-table td {{ padding: 10px; border-bottom: 1px solid #E2E8F0; }}
                .pass {{ color: #10B981; font-weight: bold; }}
                .fail {{ color: #EF4444; font-weight: bold; }}
                .cancel {{ font-weight: bold; color: #F59E0B; }}
                .reason {{ font-size: 10pt; color: #EF4444; background-color: #FEF2F2; padding: 6px; margin: 4px 0; border-radius: 4px; }}
                .details-success {{ font-size: 10pt; color: #10B981; background-color: #ECFDF5; padding: 6px; margin: 4px 0; border-radius: 4px; }}
                .signature-line {{ text-align: center; padding-top: 5px; font-size: 10pt; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2 style="font-size: 18pt; margin-bottom: 5px;">DELHI TEST HOUSE</h2>
                <div style="font-size: 16pt; font-weight: bold; color: #0284C7; margin-bottom: 5px;">METER PERFORMANCE TEST REPORT</div>
                <p style="font-size: 11pt; margin-top: 2px; margin-bottom: 5px;">Safety and Contact Durability Test Results</p>
                <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 5px; margin-bottom: 15px;">
                    <tr><td height="3" bgcolor="#0284C7" style="font-size: 1px; line-height: 1px;">&nbsp;</td></tr>
                </table>
            </div>
            
            <div class="section-title">Session Information</div>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 5px; margin-bottom: 10px;">
                <tr><td height="1" bgcolor="#E2E8F0" style="font-size: 1px; line-height: 1px;">&nbsp;</td></tr>
            </table>
            <table class="meta-table">
                <tr>
                    <td class="meta-header">Session ID</td>
                    <td>#{session_data.get('id')}</td>
                    <td class="meta-header">Test Date/Time</td>
                    <td>{session_data.get('timestamp')}</td>
                </tr>
                <tr>
                    <td class="meta-header">Meter Serial Number</td>
                    <td>{session_data.get('meter_serial_number')}</td>
                    <td class="meta-header">Overall Result</td>
                    <td><span class="{overall.lower() if (overall := session_data.get('overall_results', '')) else ''}">{overall}</span></td>
                </tr>
                """
        
        if session_data.get('failure_reason'):
            html += f"""
                <tr>
                    <td class="meta-header">Primary Failure Reason</td>
                    <td colspan="3" style="color: #EF4444; font-weight: bold;">{session_data.get('failure_reason')}</td>
                </tr>
            """
            
        html += """
            </table>
            
            <div class="section-title">Coagulated Test Summary</div>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 5px; margin-bottom: 10px;">
                <tr><td height="1" bgcolor="#E2E8F0" style="font-size: 1px; line-height: 1px;">&nbsp;</td></tr>
            </table>
            <table class="meta-table" style="text-align: center;">
                <tr style="background-color: #F8FAFC; font-weight: bold;">
                    <td>G2 (Normal Ops)</td>
                    <td>G3 (Endurance)</td>
                    <td>G5 (Fault Make)</td>
                    <td>G6 (Short Circuit)</td>
                    <td>G7 (Min Current)</td>
                </tr>
                <tr>
        """
        
        for col in ['g2', 'g3', 'g5', 'g6', 'g7']:
            val = session_data.get(col) or "-"
            cls = val.lower() if val in ["PASS", "FAIL", "CANCELLED"] else ""
            html += f'<td><span class="{cls}">{val}</span></td>'
            
        html += """
                </tr>
            </table>
            
            <div class="section-title">Detailed Execution Log</div>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 5px; margin-bottom: 10px;">
                <tr><td height="1" bgcolor="#E2E8F0" style="font-size: 1px; line-height: 1px;">&nbsp;</td></tr>
            </table>
        """
        
        if not runs:
            html += "<p>No detailed sub-runs recorded.</p>"
        else:
            html += """
            <table class="runs-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Test Module</th>
                        <th>Execution Status</th>
                        <th>Run Category</th>
                    </tr>
                </thead>
                <tbody>
            """
            for run in runs:
                ts = run.get("run_timestamp")
                tt = run.get("test_type", "").upper()
                status = run.get("status", "N/A")
                cls = status.lower()
                is_sub = "Sub-sequence" if run.get("is_sub_test") else "Main Sequence"
                reason = run.get("failure_reason")
                
                html += f"""
                    <tr>
                        <td>{ts}</td>
                        <td><b>{tt}</b></td>
                        <td><span class="{cls}">{status}</span></td>
                        <td>{is_sub}</td>
                    </tr>
                """
                if reason:
                    is_passing_detail = status == "PASS" and reason.startswith("Measurements:")
                    label = "Details:" if is_passing_detail else "Error Details:"
                    cls_name = "details-success" if is_passing_detail else "reason"
                    html += f"""
                        <tr>
                            <td colspan="4" class="{cls_name}">
                                <b>{label}</b> {reason}
                            </td>
                        </tr>
                    """
            html += "</tbody></table>"
            
        html += """
            <br><br>
            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-top: 40px; border-collapse: collapse;">
                <tr>
                    <td align="left" width="40%" style="border: none;">
                        <br><br>
                        <div style="text-align: center;">___________________________</div>
                        <div class="signature-line">Tested By (Operator)</div>
                    </td>
                    <td width="20%" style="border: none;"></td>
                    <td align="right" width="40%" style="border: none;">
                        <br><br>
                        <div style="text-align: center;">___________________________</div>
                        <div class="signature-line">Verified By (Quality Manager)</div>
                    </td>
                </tr>
            </table>
            """
            
        # Append waveform graphs
        import os
        graphs_dir = "logs/graphs"
        graph_count = 0
        if os.path.exists(graphs_dir):
            for file in os.listdir(graphs_dir):
                if file.startswith(f"session_{session_id}_") and file.endswith(".png"):
                    img_path = os.path.abspath(os.path.join(graphs_dir, file)).replace('\\', '/')
                    test_name = file.replace(f"session_{session_id}_", "").replace(".png", "").replace("_", " ").title()
                    
                    page_break = '<div style="page-break-before: always;"></div>' if graph_count % 2 == 0 else '<div style="margin-top: 40px;"></div>'
                    
                    html += f"""
                    {page_break}
                    <div class="section-title">{test_name} Captured Waveform</div>
                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 5px; margin-bottom: 10px;">
                        <tr><td height="1" bgcolor="#E2E8F0" style="font-size: 1px; line-height: 1px;">&nbsp;</td></tr>
                    </table>
                    <div style="text-align: center; margin-top: 15px;">
                        <img src="{img_path}" width="550" />
                    </div>
                    """
                    
                    graph_count += 1
                    
                    # Look for accompanying JSON metrics file
                    json_path = img_path.replace('.png', '.json')
                    if os.path.exists(json_path):
                        import json
                        try:
                            # Load report fields config
                            config_path = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "device_config.json")
                            report_fields = {}
                            if os.path.exists(config_path):
                                with open(config_path, 'r') as cf:
                                    dev_cfg = json.load(cf)
                                    report_fields = dev_cfg.get("testing", {}).get("report_fields", {})
                            
                            # Fallbacks if config missing
                            show_vrms = report_fields.get("voltage_vrms", True)
                            show_curr = report_fields.get("current_apk", True)
                            show_dur = report_fields.get("duration_ms", True)
                            show_pf = report_fields.get("pf", True)
                                    
                            with open(json_path, 'r') as f:
                                metrics = json.load(f)
                            
                            if metrics:
                                html += """
                                <table class="meta-table" style="margin-top: 15px; width: 60%; margin-left: auto; margin-right: auto; text-align: center;">
                                    <tr>
                                """
                                if show_vrms and "voltage_vrms" in metrics:
                                    html += '<td class="meta-header">Voltage (Vrms)</td>'
                                if show_curr and "measured_current" in metrics:
                                    html += '<td class="meta-header">Current</td>'
                                if show_dur and "pulse_duration" in metrics:
                                    html += '<td class="meta-header">Duration (ms)</td>'
                                if show_pf and "calculated_pf" in metrics:
                                    html += '<td class="meta-header">Power Factor</td>'
                                
                                html += "</tr><tr>"
                                
                                if show_vrms and "voltage_vrms" in metrics:
                                    html += f'<td>{metrics["voltage_vrms"]:.1f} V</td>'
                                if show_curr and "measured_current" in metrics:
                                    curr = metrics["measured_current"]
                                    c_str = f"{curr/1000.0:.3f} kA" if curr >= 1000 else f"{curr:.1f} A"
                                    html += f'<td>{c_str}</td>'
                                if show_dur and "pulse_duration" in metrics:
                                    html += f'<td>{metrics["pulse_duration"]:.2f}</td>'
                                if show_pf and "calculated_pf" in metrics:
                                    html += f'<td>{metrics["calculated_pf"]:.2f}</td>'
                                    
                                html += """
                                    </tr>
                                </table>
                                """
                        except Exception as e:
                            print(f"Error loading metrics for PDF: {e}")
                    
        html += """
        </body>
        </html>
        """
        
        try:
            # Print using PySide6 QTextDocument and QPdfWriter
            doc = QTextDocument()
            doc.setHtml(html)
            
            from PySide6.QtGui import QPdfWriter, QPageLayout
            from PySide6.QtCore import QMarginsF
            writer = QPdfWriter(file_path)
            
            # Setup layout with margins (15mm)
            layout = QPageLayout()
            layout.setPageSize(QPageSize(QPageSize.A4))
            layout.setOrientation(QPageLayout.Orientation.Portrait)
            layout.setMargins(QMarginsF(15, 15, 15, 15))
            writer.setPageLayout(layout)
            
            doc.print_(writer)
            
            QMessageBox.information(self, "Success", "Report exported successfully as PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {e}")
            
    def setupUi(self, dummy):
        # Compatibility stub for main window call to setupUi
        pass
