import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextDocument, QPdfWriter, QPageLayout, QPageSize
from PySide6.QtCore import QMarginsF

def render_pdf(html_content, output_path):
    app = QApplication.instance() or QApplication(sys.argv)
    doc = QTextDocument()
    doc.setHtml(html_content)
    
    writer = QPdfWriter(output_path)
    layout = QPageLayout()
    layout.setPageSize(QPageSize(QPageSize.A4))
    layout.setOrientation(QPageLayout.Orientation.Portrait)
    layout.setMargins(QMarginsF(15, 15, 15, 15))
    writer.setPageLayout(layout)
    
    doc.print_(writer)
    print(f"PDF rendered to {output_path}")

session_data = {
    'id': 39,
    'timestamp': '2026-06-23 17:02:58',
    'meter_serial_number': 'LSCS_DEV_02',
    'overall_results': 'PASS',
    'failure_reason': None,
    'g2': 'PASS',
    'g3': '-',
    'g5': '-',
    'g6': '-',
    'g7': '-'
}
runs = [
    {
        "run_timestamp": "2026-06-23 17:02:58",
        "test_type": "g2",
        "status": "PASS",
        "is_sub_test": False,
        "failure_reason": None
    }
]

overall = session_data.get('overall_results', '')

# Updated HTML/CSS content using table-based dividers and inline styling for sizes
modified_html = f"""
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
                .cancel {{ color: #F59E0B; font-weight: bold; }}
                .reason {{ font-size: 10pt; color: #EF4444; background-color: #FEF2F2; padding: 6px; margin: 4px 0; border-radius: 4px; }}
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
    modified_html += f'<td><span class="{cls}">{val}</span></td>'
    
modified_html += """
                </tr>
            </table>
            
            <div class="section-title">Detailed Execution Log</div>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 5px; margin-bottom: 10px;">
                <tr><td height="1" bgcolor="#E2E8F0" style="font-size: 1px; line-height: 1px;">&nbsp;</td></tr>
            </table>
        """

if not runs:
    modified_html += "<p>No detailed sub-runs recorded.</p>"
else:
    modified_html += """
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
        
        modified_html += f"""
            <tr>
                <td>{ts}</td>
                <td><b>{tt}</b></td>
                <td><span class="{cls}">{status}</span></td>
                <td>{is_sub}</td>
            </tr>
        """
        if reason:
            modified_html += f"""
                <tr>
                    <td colspan="4" class="reason">
                        <b>Error Details:</b> {reason}
                    </td>
                </tr>
            """
    modified_html += "</tbody></table>"
    
modified_html += """
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
</body>
</html>
"""

if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    render_pdf(modified_html, os.path.join(output_dir, "test_modified.pdf"))
