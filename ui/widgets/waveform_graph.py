import math
import random
from PySide6.QtWidgets import QWidget, QPinchGesture
from PySide6.QtCore import Qt, QPoint, QRect, Signal, QEvent
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QMouseEvent, QCursor

class ToolMode:
    RULER = 0
    ZOOM = 1
    PAN = 2

class WaveformGraph(QWidget):
    """
    High-fidelity interactive waveform plotting widget built with PySide6 QPainter.
    Features drag-and-drop cursors, pan/zoom, autozoom detection, and an 
    in-plot floating zoom toolbox with minimap.
    """
    cursors_moved = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_a = None
        self.data_b = None
        self.timebase = 15
        self.range = 10
        self.interval_ms = 0.320
        self.range_volts = 20.0
        
        self.test_id = "unknown"
        self.calculated_pf = None
        self.pulse_duration = None
        
        self.current_tool = ToolMode.RULER
        self.show_zoom_toolbox = False
        
        # Cursor positions in pixels
        self.cursor_1x = -1
        self.cursor_2x = -1
        self.cursor_y1 = -1
        self.cursor_y2 = -1
        self.meas_box_pos = None  # QPoint(x, y) for movable measurements table overlay
        self.drag_meas_offset = QPoint(0, 0)
        self.dragging_cursor = 0  # 0=none, 1=C1, 2=C2, 3=Y1, 4=Y2, 15=meas_table, 10=zoom_rect, 11=pan, 12=v_slider, 13=h_slider, 14=minimap_pan
        
        # Default paddings
        self.pad_left = 65
        self.pad_top = 25
        self.pad_right = 65
        self.pad_bottom = 45

        
        # View limits
        self.view_start_time_ms = 0.0
        self.view_end_time_ms = 0.0
        self.view_min_volt = -15.0
        self.view_max_volt = 15.0
        self.view_min_curr = -15.0
        self.view_max_curr = 15.0
        self.auto_zoom_enabled = False
        self._auto_position_cursors = False
        self.cursor1_t = 0.0
        self.cursor2_t = 0.0
        self.cursor_y1_val = 0.0
        self.cursor_y2_val = 0.0
        
        # Zoom selection rect coords
        self.select_x1 = -1
        self.select_y1 = -1
        self.select_x2 = -1
        self.select_y2 = -1
        
        # Panning variables
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_start_t1 = 0.0
        self.pan_start_v1 = -15.0
        self.pan_start_v2 = 15.0
        
        self.setMouseTracking(True)
        self.grabGesture(Qt.PinchGesture)

    def setData(self, data_a, data_b=None, timebase=15, range_val=10, test_id="unknown"):
        """Updates the graph dataset and resets the viewport."""
        # Unpack if data_a is a dual-channel list for backward compatibility
        if isinstance(data_a, list) and len(data_a) == 2 and isinstance(data_a[0], list):
            data_b = data_a[1]
            data_a = data_a[0]
            
        self.data_a = data_a
        self.data_b = data_b
        self.timebase = timebase
        self.range = range_val
        self.test_id = test_id.lower() if test_id else "unknown"
        # PF and measured current will be explicitly set by the parent (WaveformCard)
        # to respect user overrides.
        
        # Map PicoScope Range constants to actual Volt ranges
        # Mappings: 0->10mV, 1->20mV, 2->50mV, 3->100mV, 4->200mV, 5->500mV, 6->1V, 7->2V, 8->5V, 9->10V, 10->20V
        ranges = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
        self.range_volts = ranges[range_val] if range_val < len(ranges) else 20.0
        
        # If the data represents high currents (e.g. from mock surge peaking at 4500A), 
        # let's set the voltage range dynamically to map properly on the Y-axis.
        max_val = max(abs(x) for x in data_a) if data_a else 0.0
        if max_val > 50.0:
            self.range_volts = max_val * 1.15
        
        interval_ns = 10 * (2 ** timebase)
        self.interval_ms = interval_ns / 1000000.0
        
        if self.data_a:
            total_time = len(self.data_a) * self.interval_ms
            if self.auto_zoom_enabled:
                self.apply_auto_zoom()
            else:
                self.reset_zoom()
        
        self.reset_cursors()
        self.update()

    def reset_cursors(self):
        """Restores measurement cursors to their default locations."""
        total_time = (len(self.data_a) * self.interval_ms) if self.data_a else 100.0
        self.cursor1_t = 0.1 * total_time
        self.cursor2_t = 0.9 * total_time
        self.cursor_y1_val = 0.0
        self.cursor_y2_val = 0.0

    def get_override_duration(self) -> float:
        """Calculates duration (dt) from vertical cursors."""
        return abs(self.cursor2_t - self.cursor1_t)

    def get_override_pf(self) -> float:
        """Calculates PF from vertical cursors."""
        dt = self.get_override_duration()
        if dt <= 0.0: return 1.0
        extra_ms = dt - 10.0
        angle_deg = extra_ms * 18.0
        pf = math.cos(math.radians(angle_deg))
        return max(0.0, min(1.0, pf))
        
    def get_override_current(self) -> float:
        """Calculates current from horizontal cursor using only C2 on the right axis."""
        return abs(self.cursor_y2_val * 600.0)

    def setAutoZoomEnabled(self, enabled):
        """Enables or disables autozooming of transient events."""
        self.auto_zoom_enabled = enabled
        if self.data_a:
            if enabled:
                self.apply_auto_zoom()
            else:
                self.reset_zoom()
            self.update()

    def reset_zoom(self):
        """Resets viewport to show the entire waveform's horizontal range and full voltage/current scale."""
        self.view_start_time_ms = 0.0
        self.view_end_time_ms = (len(self.data_a) * self.interval_ms) if self.data_a else 100.0
        
        max_val = max(abs(x) for x in self.data_a) if self.data_a else 15.0
        limit = max(15.0, max_val * 1.1)
        self.view_min_volt = -limit
        self.view_max_volt = limit
        
        if self.data_b:
            max_c = max(abs(x) for x in self.data_b) if self.data_b else 15.0
            c_limit = max(15.0, max_c * 1.1)
            self.view_min_curr = -c_limit
            self.view_max_curr = c_limit

    def apply_auto_zoom(self):
        """Performs search to locate voltage dip or current surge and focuses the viewport."""
        area = self.detect_interest_area()
        if area:
            t_start, t_end, zoom_start, zoom_end = area
            self.view_start_time_ms = zoom_start
            self.view_end_time_ms = zoom_end
            
            # Automatically set cursors to the measurement duration
            self.cursor1_t = t_start
            self.cursor2_t = t_end
            
            # Also calculate y-values for the cursors
            start_idx = max(0, int(t_start / self.interval_ms))
            end_idx = min(len(self.data_a) - 1 if self.data_a else 0, int(t_end / self.interval_ms))
            
            # Using data_b for current or data_a for voltage
            dataset = self.data_b if self.data_b else self.data_a
            if dataset and start_idx <= end_idx:
                subset = dataset[start_idx:end_idx+1]
                if subset:
                    self.cursor_y1_val = min(subset)
                    self.cursor_y2_val = max(subset)
                else:
                    self.cursor_y1_val = 0.0
                    self.cursor_y2_val = 0.0
            else:
                self.cursor_y1_val = 0.0
                self.cursor_y2_val = 0.0
                
            self._auto_position_cursors = True
            
            # Open measurement tool automatically
            self.show_zoom_toolbox = True
            self.current_tool = ToolMode.RULER
        else:
            self.reset_zoom()

    def detect_interest_area(self):
        """Robust event window detection helper."""
        dataset = self.data_b if (self.data_b and len(self.data_b) >= 100) else self.data_a
        if not dataset or len(dataset) < 100:
            return None

        # 1. Compute moving RMS envelope (1ms window)
        window_size = int(1.0 / self.interval_ms)
        if window_size < 5:
            window_size = 5

        rms = []
        max_rms = 0.0
        n = len(dataset)
        
        half_win = window_size // 2
        for i in range(n):
            start = max(0, i - half_win)
            end = min(n, i + half_win + 1)
            sum_sq = 0.0
            for j in range(start, end):
                sum_sq += dataset[j] * dataset[j]
            val = math.sqrt(sum_sq / (end - start))
            rms.append(val)
            if val > max_rms:
                max_rms = val

        if max_rms == 0.0:
            return None

        # 2. Check if surge (starts near 0) or dip (starts high)
        start_rms = sum(rms[:max(1, int(n * 0.05))]) / max(1, int(n * 0.05))
        is_surge = start_rms < max_rms * 0.25
        
        event_starts = []
        event_ends = []
        
        if is_surge:
            # Surge detection: goes above 8% of peak
            threshold = max_rms * 0.08
            in_event = False
            for i in range(n):
                if not in_event and rms[i] > threshold:
                    event_starts.append(i)
                    in_event = True
                elif in_event and rms[i] < threshold:
                    end = i
                    if (end - event_starts[-1]) * self.interval_ms > 2.0:
                        event_ends.append(end)
                    else:
                        event_starts.pop()
                    in_event = False
            if in_event and len(event_starts) > len(event_ends):
                event_ends.append(n - 1)
        else:
            # Dip detection: drops below 75% of max amplitude
            threshold = max_rms * 0.75
            in_event = False
            for i in range(n):
                if not in_event and rms[i] < threshold:
                    event_starts.append(i)
                    in_event = True
                elif in_event and rms[i] > threshold:
                    end = i
                    if (end - event_starts[-1]) * self.interval_ms > 2.0:
                        event_ends.append(end)
                    else:
                        event_starts.pop()
                    in_event = False
            if in_event and len(event_starts) > len(event_ends):
                event_ends.append(n - 1)

        if not event_starts:
            return None

        # Scale window bounds around event
        t_start = event_starts[0] * self.interval_ms
        t_end = event_ends[-1] * self.interval_ms
        duration = t_end - t_start
        
        # Tight padding to show just the event and a tiny bit of context
        padding = max(duration * 0.1, 2.0)  
        zoom_start = max(0.0, t_start - padding)
        zoom_end = min(n * self.interval_ms, t_end + padding)
        
        return t_start, t_end, zoom_start, zoom_end

    def clamp_view(self):
        """Keeps viewport limits within logical ranges."""
        total_t = (len(self.data_a) * self.interval_ms) if self.data_a else 100.0
        duration = self.view_end_time_ms - self.view_start_time_ms
        if duration > total_t:
            duration = total_t
        if duration <= 0.1:
            duration = 0.1
            
        if self.view_start_time_ms < 0:
            self.view_start_time_ms = 0
            self.view_end_time_ms = duration
        if self.view_end_time_ms > total_t:
            self.view_end_time_ms = total_t
            self.view_start_time_ms = self.view_end_time_ms - duration
            
        max_val = max(abs(x) for x in self.data_a) if self.data_a else 15.0
        limit = max(15.0, max_val * 1.25)
        
        v_range = self.view_max_volt - self.view_min_volt
        if v_range > limit * 2:
            v_range = limit * 2
        if v_range <= 0.5:
            v_range = 0.5
            
        if self.view_min_volt < -limit:
            self.view_min_volt = -limit
            self.view_max_volt = -limit + v_range
        if self.view_max_volt > limit:
            self.view_max_volt = limit
            self.view_min_volt = limit - v_range
            
        if self.data_b:
            max_c = max(abs(x) for x in self.data_b)
            c_limit = max(1.0, max_c * 1.25)
            c_range = self.view_max_curr - self.view_min_curr
            if c_range > c_limit * 2: c_range = c_limit * 2
            if c_range <= 0.5: c_range = 0.5
            if self.view_min_curr < -c_limit:
                self.view_min_curr = -c_limit
                self.view_max_curr = -c_limit + c_range
            if self.view_max_curr > c_limit:
                self.view_max_curr = c_limit
                self.view_min_curr = c_limit - c_range

    def is_cursors_moved(self) -> bool:
        """Helper checking if cursors have moved from defaults."""
        return (abs(self.cursor_1x - (self.pad_left + 40)) > 1 or 
                abs(self.cursor_2x - (self.pad_left + 120)) > 1 or 
                abs(self.cursor_y1 - (self.pad_top + 60)) > 1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Dimensions of active plotting graph field
        graph_w = w - self.pad_left - self.pad_right
        graph_h = h - self.pad_top - self.pad_bottom
        
        # 1. Background
        painter.fillRect(self.rect(), QColor("#FFFFFF"))
        
        if w <= 0 or h <= 0 or graph_w <= 0 or graph_h <= 0:
            return
            
        # Always map physical values to pixels
        view_dur = self.view_end_time_ms - self.view_start_time_ms
        if view_dur > 0:
            self.cursor_1x = self.pad_left + ((self.cursor1_t - self.view_start_time_ms) / view_dur) * graph_w
            self.cursor_2x = self.pad_left + ((self.cursor2_t - self.view_start_time_ms) / view_dur) * graph_w
            
        c_span = self.view_max_curr - self.view_min_curr
        if c_span > 0:
            y2_pct = (self.cursor_y2_val - self.view_min_curr) / c_span
            self.cursor_y2 = self.pad_top + graph_h - (y2_pct * graph_h)

        # Clamp cursors for drawing so they don't spill out of graph area
        self.cursor_1x = max(self.pad_left, min(self.pad_left + graph_w, self.cursor_1x))
        self.cursor_2x = max(self.pad_left, min(self.pad_left + graph_w, self.cursor_2x))
        self.cursor_y2 = max(self.pad_top, min(self.pad_top + graph_h, self.cursor_y2))
            
        # Clip painting to graph active area
        painter.save()
        painter.setClipRect(self.pad_left, self.pad_top, graph_w, graph_h)
        
        # 2. Draw Grid
        pen_grid = QPen(QColor("#E2E8F0"), 1, Qt.SolidLine)
        painter.setPen(pen_grid)
        for i in range(11):
            x = self.pad_left + i * (graph_w / 10.0)
            painter.drawLine(x, self.pad_top, x, self.pad_top + graph_h)
            y = self.pad_top + i * (graph_h / 10.0)
            painter.drawLine(self.pad_left, y, self.pad_left + graph_w, y)
            
        # 3. Center line (0V / 0A axis)
        pen_center = QPen(QColor("#CBD5E1"), 1.5, Qt.SolidLine)
        painter.setPen(pen_center)
        zero_y = self.pad_top + graph_h / 2
        painter.drawLine(self.pad_left, zero_y, self.pad_left + graph_w, zero_y)
        
        # 4. Draw Waveform Data
        if self.data_a and len(self.data_a) > 1:
            self.draw_waveform_path(painter, self.data_a, QColor("#1D4ED8"), graph_w, graph_h, is_current=False)
            
        if self.data_b and len(self.data_b) > 1:
            self.draw_waveform_path(painter, self.data_b, QColor("#EF4444"), graph_w, graph_h, is_current=True)
            
        # 5. Draw Zoom Selection Rectangle
        if self.dragging_cursor == 10:
            pen_sel = QPen(QColor("#3B82F6"), 1, Qt.DashLine)
            painter.setPen(pen_sel)
            painter.setBrush(QBrush(QColor(59, 130, 246, 30)))
            rx = min(self.select_x1, self.select_x2)
            ry = min(self.select_y1, self.select_y2)
            rw = abs(self.select_x2 - self.select_x1)
            rh = abs(self.select_y2 - self.select_y1)
            painter.drawRect(rx, ry, rw, rh)
            
        # 6. Draw Interactive Cursors
        # Cursor vertical C1 (Blue)
        pen_c1 = QPen(QColor("#2563EB"), 1.5, Qt.DashLine)
        painter.setPen(pen_c1)
        painter.drawLine(self.cursor_1x, self.pad_top, self.cursor_1x, self.pad_top + graph_h)
        painter.setPen(QPen(QColor("#2563EB"), 1))
        painter.setBrush(QBrush(QColor("#2563EB")))
        painter.drawPolygon([QPoint(self.cursor_1x - 6, self.pad_top), QPoint(self.cursor_1x + 6, self.pad_top), QPoint(self.cursor_1x, self.pad_top + 10)])
        
        # Cursor vertical C2 (Blue)
        painter.setPen(pen_c1)
        painter.drawLine(self.cursor_2x, self.pad_top, self.cursor_2x, self.pad_top + graph_h)
        painter.setPen(QPen(QColor("#2563EB"), 1))
        painter.setBrush(QBrush(QColor("#2563EB")))
        painter.drawPolygon([QPoint(self.cursor_2x - 6, self.pad_top + graph_h), QPoint(self.cursor_2x + 6, self.pad_top + graph_h), QPoint(self.cursor_2x, self.pad_top + graph_h - 10)])
        
        # Cursor horizontal Y1 (Removed for simpler UI)
        
        # Cursor horizontal Y2 (Red)
        pen_y1 = QPen(QColor("#DC2626"), 1.5, Qt.DashLine)
        painter.setPen(pen_y1)
        painter.drawLine(self.pad_left, self.cursor_y2, self.pad_left + graph_w, self.cursor_y2)
        painter.setPen(QPen(QColor("#DC2626"), 1))
        painter.setBrush(QBrush(QColor("#DC2626")))
        painter.drawPolygon([QPoint(self.pad_left + graph_w, self.cursor_y2 - 6), QPoint(self.pad_left + graph_w, self.cursor_y2 + 6), QPoint(self.pad_left + graph_w - 10, self.cursor_y2)])
        
        painter.restore()

        
        # 7. Draw Axis scale labels (ticks)
        painter.setPen(QPen(QColor("#0F172A")))
        painter.setFont(QFont("Segoe UI", 9))
        
        # Y Axis (Voltage / Current)
        for i in range(11):
            y = self.pad_top + i * (graph_h / 10.0)
            
            # Left Axis (Voltage)
            v = self.view_max_volt - (i * (self.view_max_volt - self.view_min_volt) / 10.0)
            painter.setPen(QPen(QColor("#1D4ED8"))) # Blue for voltage
            painter.drawText(QRect(5, y - 8, self.pad_left - 10, 16), Qt.AlignRight | Qt.AlignVCenter, f"{v:.1f}V" if max(abs(self.view_max_volt), abs(self.view_min_volt)) < 100.0 else f"{v:.0f}V")
            
            # Right Axis (Channel B)
            if self.data_b:
                c = self.view_max_curr - (i * (self.view_max_curr - self.view_min_curr) / 10.0)
                painter.setPen(QPen(QColor("#EF4444"))) # Red for Channel B
                painter.drawText(QRect(w - self.pad_right + 5, y - 8, self.pad_right - 10, 16), Qt.AlignLeft | Qt.AlignVCenter, f"{c:.1f}V" if max(abs(self.view_max_curr), abs(self.view_min_curr)) < 100.0 else f"{c:.0f}V")
            
        # X Axis (Time)
        if self.data_a:
            view_dur = self.view_end_time_ms - self.view_start_time_ms
            use_ms = view_dur < 1000.0
            
            for i in range(11):
                x = self.pad_left + i * (graph_w / 10.0)
                t = self.view_start_time_ms + i * (view_dur / 10.0)
                
                label = f"{t:.1f}" if use_ms else f"{t/1000.0:.3f}"
                painter.drawText(QRect(x - 30, h - self.pad_bottom + 5, 60, 18), Qt.AlignCenter | Qt.AlignTop, label)
                
            axis_lbl = "Time (ms)" if use_ms else "Time (s)"
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(QRect(self.pad_left, h - 22, graph_w, 20), Qt.AlignCenter | Qt.AlignVCenter, axis_lbl)
            
        # 8. Draw Zoom Toggle Button (Top Right corner)
        self.draw_zoom_icon(painter, w - 35, 10)
        
        # 9. Draw interactive Measurement Rulers Overlay
        if self.data_a and len(self.data_a) > 1 and self.is_cursors_moved():
            self.draw_rulers_overlay(painter, graph_w, graph_h, w)
            
        # 10. Draw Zoom toolbox (if toggle active)
        if self.show_zoom_toolbox:
            self.draw_zoom_toolbox(painter, w, h)
            
        # 11. Draw floating Power Factor & Current Badge
        if self.calculated_pf is not None or self.measured_current is not None:
            self.draw_pf_badge(painter)

    def draw_waveform_path(self, painter, dataset, color, graph_w, graph_h, is_current=False):

        """Paints a waveform series on the screen canvas."""
        pen = QPen(color, 1.8, Qt.SolidLine)
        painter.setPen(pen)
        
        view_dur = self.view_end_time_ms - self.view_start_time_ms
        if view_dur <= 0.0:
            view_dur = len(dataset) * self.interval_ms
            
        start_idx = max(0, int(self.view_start_time_ms / self.interval_ms))
        end_idx = min(len(dataset) - 1, int(self.view_end_time_ms / self.interval_ms))
        
        v_min = self.view_min_curr if is_current else self.view_min_volt
        v_max = self.view_max_curr if is_current else self.view_max_volt
        span = v_max - v_min
        if span == 0: span = 1.0
        
        last_pt = None
        for i in range(start_idx, end_idx + 1):
            t_ms = i * self.interval_ms
            
            # Map time to horizontal pixel
            px = self.pad_left + ((t_ms - self.view_start_time_ms) / view_dur) * graph_w
            
            # Map voltage/current value to vertical pixel
            val = dataset[i]
            py = self.pad_top + graph_h - ((val - v_min) / span * graph_h)
            
            curr_pt = QPoint(int(px), int(py))
            if last_pt is not None:
                painter.drawLine(last_pt, curr_pt)
            last_pt = curr_pt

    def draw_zoom_icon(self, painter, x, y):
        """Draws the toggle icon for the Zoom Toolbox."""
        rect = QRect(x, y, 25, 25)
        
        # Hover background styling
        mouse_pos = self.mapFromGlobal(QCursor.pos())
        is_hover = rect.contains(mouse_pos)
        
        painter.setPen(QPen(QColor("#94A3B8"), 1))
        painter.setBrush(QBrush(QColor("#F8FAFC" if not is_hover else "#E2E8F0")))
        painter.drawRoundedRect(rect, 4, 4)
        
        painter.setPen(QPen(QColor("#334155"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(x + 5, y + 5, 8, 8)
        painter.drawLine(x + 12, y + 12, x + 18, y + 18)
        
        # Tiny plus sign
        painter.setPen(QPen(QColor("#334155"), 1))
        painter.drawLine(x + 7, y + 9, x + 11, y + 9)
        painter.drawLine(x + 9, y + 7, x + 9, y + 11)

    def draw_pf_badge(self, painter):
        """Draws a premium styled floating badge/overlay displaying the calculated Power Factor & Measured Current."""
        badge_x = self.pad_left + 15
        badge_y = self.pad_top + 15
        badge_w = 210
        badge_h = 68 if self.measured_current is not None else 52
        
        painter.save()
        # Draw translucent dark background card with subtle blue border
        painter.setPen(QPen(QColor("#3B82F6"), 1))
        painter.setBrush(QBrush(QColor(15, 23, 42, 220))) # 85% opacity Slate 900
        painter.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, 6, 6)
        
        if self.calculated_pf is not None:
            # Draw PF label
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(QPen(QColor("#94A3B8")))
            painter.drawText(QRect(badge_x + 10, badge_y + 4, 100, 16), Qt.AlignLeft | Qt.AlignVCenter, "CALCULATED PF")
            
            # Draw PF value
            painter.setFont(QFont("Segoe UI", 13, QFont.Bold))
            painter.setPen(QPen(QColor("#38BDF8")))
            pf_text = f"{self.calculated_pf:.3f}"
            painter.drawText(QRect(badge_x + 10, badge_y + 20, 80, 20), Qt.AlignLeft | Qt.AlignVCenter, pf_text)
            
            # Draw Pulse Duration text
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(QPen(QColor("#10B981"))) # Emerald Green
            dur_text = f"({self.pulse_duration:.2f} ms)" if self.pulse_duration else ""
            painter.drawText(QRect(badge_x + 95, badge_y + 20, 105, 20), Qt.AlignRight | Qt.AlignVCenter, dur_text)

        if self.measured_current is not None:
            curr_y = badge_y + 42 if self.calculated_pf is not None else badge_y + 6
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(QPen(QColor("#94A3B8")))
            painter.drawText(QRect(badge_x + 10, curr_y, 110, 16), Qt.AlignLeft | Qt.AlignVCenter, "MEASURED CURRENT")
            
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
            painter.setPen(QPen(QColor("#F59E0B"))) # Amber
            curr_text = f"{self.measured_current:.1f} A"
            painter.drawText(QRect(badge_x + 120, curr_y, 80, 16), Qt.AlignRight | Qt.AlignVCenter, curr_text)
        
        painter.restore()


    def draw_rulers_overlay(self, painter, graph_w, graph_h, w):
        """Renders the numerical measurements table based on cursors."""
        view_dur = self.view_end_time_ms - self.view_start_time_ms
        
        # Horizontal values mapping
        t1 = self.cursor1_t
        t2 = self.cursor2_t
        dt = abs(t2 - t1)
        freq = (1000.0 / dt) if dt > 0.0 else 0.0
        rpm = freq * 60.0
        
        # Vertical value mapping (using Channel B scale, displayed as Volts)
        v_y2 = self.cursor_y2_val
        
        # Overlay box properties (support custom position via dragging)
        box_w = 260
        box_h = 135
        if self.meas_box_pos is not None:
            box_x = self.meas_box_pos.x()
            box_y = self.meas_box_pos.y()
        else:
            box_x = w - box_w - 15
            box_y = 15 if not self.show_zoom_toolbox else 255
        
        painter.save()
        
        # Shadow/Card background
        painter.setPen(QPen(QColor("#CBD5E1"), 1))
        painter.setBrush(QBrush(QColor("#F8FAFC")))
        painter.drawRoundedRect(box_x, box_y, box_w, box_h, 6, 6)
        
        # Header title
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#3B82F6")))
        painter.drawRoundedRect(QRect(box_x, box_y, box_w, 24), 6, 6)
        painter.fillRect(QRect(box_x, box_y + 18, box_w, 6), QColor("#3B82F6")) # Flatten header bottom
        
        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(box_x + 8, box_y + 16, "Measurements")
        
        # Reset cross icon
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawLine(box_x + box_w - 16, box_y + 8, box_x + box_w - 8, box_y + 16)
        painter.drawLine(box_x + box_w - 16, box_y + 16, box_x + box_w - 8, box_y + 8)
        
        # Table lines
        r_y = box_y + 24
        row_h = 22
        
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        for r in range(1, 5):
            painter.drawLine(box_x, r_y + r * row_h, box_x + box_w, r_y + r * row_h)
            
        c_x1 = box_x + 65
        c_x2 = box_x + 130
        c_x3 = box_x + 195
        painter.drawLine(c_x1, r_y, c_x1, r_y + 3 * row_h)
        painter.drawLine(c_x2, r_y, c_x2, r_y + 3 * row_h)
        painter.drawLine(c_x3, r_y, c_x3, r_y + 3 * row_h)
        
        # Cell Labels
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QPen(QColor("#64748B")))
        
        painter.drawText(QRect(c_x1, r_y, 65, row_h), Qt.AlignCenter, "C1")
        painter.drawText(QRect(c_x2, r_y, 65, row_h), Qt.AlignCenter, "C2")
        painter.drawText(QRect(c_x3, r_y, 65, row_h), Qt.AlignCenter, "Delta")
        
        # Time row (X indicators)
        painter.setPen(QPen(QColor("#0F172A")))
        # Blue indicator rectangle
        painter.fillRect(box_x + 5, r_y + row_h + 5, 12, 12, QColor("#2563EB"))
        
        painter.drawText(QRect(c_x1, r_y + row_h, 65, row_h), Qt.AlignCenter, f"{t1:.1f}ms")
        painter.drawText(QRect(c_x2, r_y + row_h, 65, row_h), Qt.AlignCenter, f"{t2:.1f}ms")
        painter.drawText(QRect(c_x3, r_y + row_h, 65, row_h), Qt.AlignCenter, f"{dt:.1f}ms")
        
        # Current row (Y indicator)
        painter.fillRect(box_x + 5, r_y + 2 * row_h + 5, 12, 12, QColor("#DC2626"))
        
        painter.drawText(QRect(c_x1, r_y + 2 * row_h, 65, row_h), Qt.AlignCenter, "-")
        painter.drawText(QRect(c_x2, r_y + 2 * row_h, 65, row_h), Qt.AlignCenter, f"{v_y2:.2f}V")
        painter.drawText(QRect(c_x3, r_y + 2 * row_h, 65, row_h), Qt.AlignCenter, "-")

        
        # Frequency and RPM summary row
        painter.drawText(QRect(box_x + 8, r_y + 3 * row_h, box_w - 16, row_h), Qt.AlignLeft | Qt.AlignVCenter, f"Freq: {freq:.1f} Hz")
        painter.drawText(QRect(box_x + 8, r_y + 3 * row_h, box_w - 16, row_h), Qt.AlignRight | Qt.AlignVCenter, f"Speed: {rpm:.0f} RPM")
        
        painter.restore()

    def draw_zoom_toolbox(self, painter, w, h):
        """Draws the detailed minimap zoom control toolbox overlay."""
        box_w = 300
        box_h = 220
        box_x = w - box_w - 15
        box_y = 15
        
        painter.save()
        
        # Outer border / fill
        painter.setPen(QPen(QColor("#CBD5E1"), 1))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRoundedRect(box_x, box_y, box_w, box_h, 6, 6)
        
        # Header
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#3B82F6")))
        painter.drawRoundedRect(QRect(box_x, box_y, box_w, 24), 6, 6)
        painter.fillRect(QRect(box_x, box_y + 18, box_w, 6), QColor("#3B82F6"))
        
        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(box_x + 8, box_y + 16, "Zoom Controller")
        
        # Minimap viewport grid
        map_x = box_x + 35
        map_y = box_y + 35
        map_w = 230
        map_h = 110
        painter.setPen(QPen(QColor("#F1F5F9"), 1))
        painter.setBrush(QBrush(QColor("#F8FAFC")))
        painter.drawRect(map_x, map_y, map_w, map_h)
        
        painter.setPen(QPen(QColor("#E2E8F0"), 1, Qt.DashLine))
        for i in range(1, 5):
            mx = map_x + i * (map_w / 5.0)
            painter.drawLine(mx, map_y, mx, map_y + map_h)
            my = map_y + i * (map_h / 5.0)
            painter.drawLine(map_x, my, map_x + map_w, my)
            
        # Draw mini-representation of data curve
        if self.data_a:
            painter.setPen(QPen(QColor("#2563EB"), 1))
            step = max(1, len(self.data_a) // 150)
            max_v = max(abs(x) for x in self.data_a)
            v_limit = max(15.0, max_v * 1.2)
            
            last_pt = None
            for idx in range(0, len(self.data_a), step):
                mx = map_x + (idx / len(self.data_a)) * map_w
                val = self.data_a[idx]
                my = map_y + map_h/2 - (val / (v_limit * 2.0)) * map_h
                
                curr_pt = QPoint(int(mx), int(my))
                if last_pt is not None:
                    painter.drawLine(last_pt, curr_pt)
                last_pt = curr_pt
                
            # Current view window inside minimap (Yellow rectangle + handles)
            total_t = len(self.data_a) * self.interval_ms
            rx = map_x + (self.view_start_time_ms / total_t) * map_w
            rw = ((self.view_end_time_ms - self.view_start_time_ms) / total_t) * map_w
            
            # Clamp drawing bounds within map frame
            rx = max(map_x, min(map_x + map_w, rx))
            rw = max(10, min(map_w - (rx - map_x), rw))
            
            ry = map_y + (v_limit - self.view_max_volt) / (v_limit * 2.0) * map_h
            rh = (self.view_max_volt - self.view_min_volt) / (v_limit * 2.0) * map_h
            ry = max(map_y, min(map_y + map_h, ry))
            rh = max(5, min(map_h - (ry - map_y), rh))
            
            painter.setPen(QPen(QColor("#F59E0B"), 1.5))
            painter.setBrush(QBrush(QColor(245, 158, 11, 40)))
            painter.drawRect(QRect(int(rx), int(ry), int(rw), int(rh)))
            
        # Left Vertical Slider (Voltage range scale)
        s_y = map_y + 15
        s_h = map_h - 30
        slider_x = box_x + 15
        painter.setPen(QPen(QColor("#E2E8F0"), 4))
        painter.drawLine(slider_x, s_y, slider_x, s_y + s_h)
        
        # Calculate current vertical scale ratio
        limit = max(15.0, (max(abs(x) for x in self.data_a) if self.data_a else 15.0) * 1.25)
        ratio = (self.view_max_volt - self.view_min_volt) / (limit * 2.0)
        knob_y = s_y + (1.0 - ratio) * s_h
        
        painter.setPen(QPen(QColor("#2563EB"), 1))
        painter.setBrush(QBrush(QColor("#3B82F6")))
        painter.drawEllipse(slider_x - 5, int(knob_y) - 5, 10, 10)
        
        # Bottom Horizontal Slider (Time duration scale)
        s_x = map_x + 20
        s_w = map_w - 40
        slider_y = box_y + box_h - 65
        painter.setPen(QPen(QColor("#E2E8F0"), 4))
        painter.drawLine(s_x, slider_y, s_x + s_w, slider_y)
        
        # Calculate time span scale ratio
        total_time = (len(self.data_a) * self.interval_ms) if self.data_a else 100.0
        time_ratio = (self.view_end_time_ms - self.view_start_time_ms) / total_time
        knob_x = s_x + time_ratio * s_w
        
        painter.setPen(QPen(QColor("#2563EB"), 1))
        painter.setBrush(QBrush(QColor("#3B82F6")))
        painter.drawEllipse(int(knob_x) - 5, slider_y - 5, 10, 10)
        
        # Mode selector buttons: Ruler, Zoom, Pan, Reset
        btn_y = box_y + box_h - 40
        btn_w = 60
        btn_h = 26
        
        modes = [
            (ToolMode.RULER, "Measure", box_x + 15),
            (ToolMode.ZOOM, "Zoom", box_x + 85),
            (ToolMode.PAN, "Pan", box_x + 155),
            (-1, "Reset", box_x + 225)
        ]
        
        for mid, text, bx in modes:
            is_active = (mid == self.current_tool)
            painter.setPen(QPen(QColor("#3B82F6" if is_active else "#CBD5E1"), 1))
            painter.setBrush(QBrush(QColor("#2563EB" if is_active else "#FFFFFF")))
            painter.drawRoundedRect(bx, btn_y, btn_w, btn_h, 3, 3)
            
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold if is_active else QFont.Normal))
            painter.setPen(QPen(QColor("#FFFFFF" if is_active else "#1E293B")))
            painter.drawText(QRect(bx, btn_y, btn_w, btn_h), Qt.AlignCenter, text)
            
        painter.restore()

    def mousePressEvent(self, event: QMouseEvent):
        w = self.width()
        h = self.height()
        x = event.position().x()
        y = event.position().y()
        
        # 1. Check zoom icon toggle click
        if w - 35 <= x <= w - 10 and 10 <= y <= 35:
            self.show_zoom_toolbox = not self.show_zoom_toolbox
            self.update()
            return
            
        # 2. Zoom controller box checks
        if self.show_zoom_toolbox:
            box_w = 300
            box_h = 220
            box_x = w - box_w - 15
            box_y = 15
            
            # Verify click fell within box boundaries
            if box_x <= x <= box_x + box_w and box_y <= y <= box_y + box_h:
                # Button click detection
                btn_y = box_y + box_h - 40
                btn_w = 60
                
                # Ruler, Zoom, Pan
                if btn_y <= y <= btn_y + 26:
                    if box_x + 15 <= x <= box_x + 75:
                        self.current_tool = ToolMode.RULER
                    elif box_x + 85 <= x <= box_x + 145:
                        self.current_tool = ToolMode.ZOOM
                    elif box_x + 155 <= x <= box_x + 215:
                        self.current_tool = ToolMode.PAN
                    elif box_x + 225 <= x <= box_x + 285:
                        self.reset_zoom()
                    self.update()
                    return
                    
                # Sliders checks
                # Vertical Slider
                slider_x = box_x + 15
                s_y = box_y + 35 + 15
                s_h = box_h - 110 - 30
                if slider_x - 10 <= x <= slider_x + 10 and box_y + 35 <= y <= box_y + 145:
                    self.dragging_cursor = 12
                    self.handle_vertical_slider(y, box_y + 35, 110)
                    return
                    
                # Horizontal Slider
                slider_y = box_y + box_h - 65
                s_x = box_x + 35 + 20
                s_w = 230 - 40
                if slider_y - 10 <= y <= slider_y + 10 and box_x + 35 <= x <= box_x + 265:
                    self.dragging_cursor = 13
                    self.handle_horizontal_slider(x, box_x + 35, 230)
                    return
                    
                # Minimap check
                map_x = box_x + 35
                map_y = box_y + 35
                map_w = 230
                map_h = 110
                if map_x <= x <= map_x + map_w and map_y <= y <= map_y + map_h:
                    self.dragging_cursor = 14
                    self.handle_minimap_pan(x, map_x, map_w)
                    return
                return
                
        # 3. Measurement Rulers table drag and reset checks
        box_w = 260
        box_h = 135
        if self.meas_box_pos is not None:
            mb_x = self.meas_box_pos.x()
            mb_y = self.meas_box_pos.y()
        else:
            mb_x = w - box_w - 15
            mb_y = 15 if not self.show_zoom_toolbox else 255
            
        # Detect click on reset button (top right cross in overlay box)
        if mb_x + box_w - 20 <= x <= mb_x + box_w - 5 and mb_y + 5 <= y <= mb_y + 20:
            self.reset_cursors()
            self.update()
            return
            
        # Detect click on measurements table header/body for dragging
        if mb_x <= x <= mb_x + box_w and mb_y <= y <= mb_y + box_h:
            self.dragging_cursor = 15
            self.drag_meas_offset = QPoint(int(x - mb_x), int(y - mb_y))
            return

        # 4. Canvas plotting region click checks (Tool based)
        graph_w = w - self.pad_left - self.pad_right
        graph_h = h - self.pad_top - self.pad_bottom
        
        # Tool: Zoom Selection
        if self.show_zoom_toolbox and self.current_tool == ToolMode.ZOOM:
            if self.pad_left <= x <= w - self.pad_right and self.pad_top <= y <= h - self.pad_bottom:
                self.select_x1 = x
                self.select_y1 = y
                self.select_x2 = x
                self.select_y2 = y
                self.dragging_cursor = 10
            return
            
        # Tool: Canvas Panning
        if self.show_zoom_toolbox and self.current_tool == ToolMode.PAN:
            if self.pad_left <= x <= w - self.pad_right and self.pad_top <= y <= h - self.pad_bottom:
                self.pan_start_x = x
                self.pan_start_y = y
                self.pan_start_t1 = self.view_start_time_ms
                self.pan_start_v1 = self.view_min_volt
                self.pan_start_v2 = self.view_max_volt
                self.dragging_cursor = 11
            return
            
        # Default Tool: Ruler cursors drag checks
        if abs(x - self.cursor_1x) < 12:
            self.dragging_cursor = 1
        elif abs(x - self.cursor_2x) < 12:
            self.dragging_cursor = 2
        elif abs(y - self.cursor_y1) < 12:
            self.dragging_cursor = 3
        elif abs(y - self.cursor_y2) < 12:
            self.dragging_cursor = 4
        else:
            self.dragging_cursor = 0

    def mouseMoveEvent(self, event: QMouseEvent):
        x = event.position().x()
        y = event.position().y()
        
        w = self.width()
        h = self.height()
        
        graph_w = w - self.pad_left - self.pad_right
        graph_h = h - self.pad_top - self.pad_bottom
        
        # Constrain movement within canvas boundary
        cx = max(self.pad_left, min(x, self.pad_left + graph_w))
        cy = max(self.pad_top, min(y, self.pad_top + graph_h))
        
        # Update cursor visual styles based on hover location
        if not event.buttons():
            # Hover cursor pointers for draggable areas
            if abs(x - self.cursor_1x) < 10 or abs(x - self.cursor_2x) < 10:
                self.setCursor(QCursor(Qt.SizeHorCursor))
            elif abs(y - self.cursor_y1) < 10 or abs(y - self.cursor_y2) < 10:
                self.setCursor(QCursor(Qt.SizeVerCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))
            return

        if self.dragging_cursor == 1:
            view_dur = self.view_end_time_ms - self.view_start_time_ms
            self.cursor1_t = self.view_start_time_ms + ((cx - self.pad_left) / graph_w) * view_dur
            self.cursors_moved.emit()
            self.update()
        elif self.dragging_cursor == 2:
            view_dur = self.view_end_time_ms - self.view_start_time_ms
            self.cursor2_t = self.view_start_time_ms + ((cx - self.pad_left) / graph_w) * view_dur
            self.cursors_moved.emit()
            self.update()
        elif self.dragging_cursor == 3:
            pass
        elif self.dragging_cursor == 4:
            c_span = self.view_max_curr - self.view_min_curr
            self.cursor_y2_val = self.view_max_curr - ((cy - self.pad_top) / graph_h) * c_span
            self.cursors_moved.emit()
            self.update()
        elif self.dragging_cursor == 15:
            # Dragging measurement overlay table
            new_x = max(0, min(w - 260, x - self.drag_meas_offset.x()))
            new_y = max(0, min(h - 135, y - self.drag_meas_offset.y()))
            self.meas_box_pos = QPoint(int(new_x), int(new_y))
            self.update()

        elif self.dragging_cursor == 10:
            # Zoom selection rect dragging
            self.select_x2 = x
            self.select_y2 = y
            self.update()
        elif self.dragging_cursor == 11:
            # Canvas panning
            dx = x - self.pan_start_x
            dy = y - self.pan_start_y
            
            view_dur = self.pan_start_v2 - self.pan_start_v1 # Using it temporarily for scale math
            duration = self.view_end_time_ms - self.view_start_time_ms
            
            dt = (dx / graph_w) * duration
            dv = (dy / graph_h) * (self.pan_start_v2 - self.pan_start_v1)
            
            self.view_start_time_ms = self.pan_start_t1 - dt
            self.view_end_time_ms = self.view_start_time_ms + duration
            self.view_min_volt = self.pan_start_v1 + dv
            self.view_max_volt = self.pan_start_v2 + dv
            self.clamp_view()
            self.update()
        elif self.dragging_cursor == 12:
            # Vertical Zoom slider scaling
            box_y = 15
            self.handle_vertical_slider(y, box_y + 35, 110)
        elif self.dragging_cursor == 13:
            # Horizontal Zoom slider scaling
            box_w = 300
            box_x = w - box_w - 15
            self.handle_horizontal_slider(x, box_x + 35, 230)
        elif self.dragging_cursor == 14:
            # Minimap panning drag
            box_w = 300
            box_x = w - box_w - 15
            self.handle_minimap_pan(x, box_x + 35, 230)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.dragging_cursor == 10:
            # Finalize zoom from selection rect coordinates
            self.apply_rectangle_zoom()
            
        self.dragging_cursor = 0
        self.select_x1 = -1
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.update()

    def handle_vertical_slider(self, y, map_y, map_h):
        """Processes vertical slider drag to scale vertical amplitude limit."""
        s_y = map_y + 15
        s_h = map_h - 30
        
        ratio = (y - s_y) / s_h
        ratio = max(0.02, min(1.0, 1.0 - ratio))
        
        limit = max(15.0, (max(abs(x) for x in self.data_a) if self.data_a else 15.0) * 1.25)
        new_span = (limit * 2.0) * ratio
        
        center = (self.view_max_volt + self.view_min_volt) / 2.0
        self.view_max_volt = center + new_span / 2.0
        self.view_min_volt = center - new_span / 2.0
        self.clamp_view()
        self.update()

    def handle_horizontal_slider(self, x, map_x, map_w):
        """Processes horizontal slider drag to scale time window size."""
        s_x = map_x + 20
        s_w = map_w - 40
        
        ratio = (x - s_x) / s_w
        ratio = max(0.02, min(1.0, ratio))
        
        total_time = (len(self.data_a) * self.interval_ms) if self.data_a else 100.0
        new_dur = total_time * ratio
        
        center = (self.view_end_time_ms + self.view_start_time_ms) / 2.0
        self.view_start_time_ms = center - new_dur / 2.0
        self.view_end_time_ms = center + new_dur / 2.0
        self.clamp_view()
        self.update()

    def handle_minimap_pan(self, x, map_x, map_w):
        """Pans viewport to follow click position on minimap."""
        total_time = (len(self.data_a) * self.interval_ms) if self.data_a else 100.0
        t = ((x - map_x) / map_w) * total_time
        
        duration = self.view_end_time_ms - self.view_start_time_ms
        self.view_start_time_ms = t - duration / 2.0
        self.view_end_time_ms = self.view_start_time_ms + duration
        self.clamp_view()
        self.update()

    def apply_rectangle_zoom(self):
        """Applies new time/amplitude bounds from zoom drag rectangle selection."""
        if abs(self.select_x1 - self.select_x2) < 5 or abs(self.select_y1 - self.select_y2) < 5:
            return
            
        w = self.width()
        h = self.height()
        graph_w = w - self.pad_left - self.pad_right
        graph_h = h - self.pad_top - self.pad_bottom
        
        x_min = max(self.pad_left, min(self.select_x1, self.select_x2))
        x_max = min(self.pad_left + graph_w, max(self.select_x1, self.select_x2))
        y_min = max(self.pad_top, min(self.select_y1, self.select_y2))
        y_max = min(self.pad_top + graph_h, max(self.select_y1, self.select_y2))
        
        view_dur = self.view_end_time_ms - self.view_start_time_ms
        new_start = self.view_start_time_ms + ((x_min - self.pad_left) / graph_w) * view_dur
        new_end = self.view_start_time_ms + ((x_max - self.pad_left) / graph_w) * view_dur
        
        v_range = self.view_max_volt - self.view_min_volt
        new_max_v = self.view_max_volt - ((y_min - self.pad_top) / graph_h) * v_range
        new_min_v = self.view_max_volt - ((y_max - self.pad_top) / graph_h) * v_range
        
        self.view_start_time_ms = new_start
        self.view_end_time_ms = new_end
        self.view_min_volt = new_min_v
        self.view_max_volt = new_max_v
        self.clamp_view()
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            return
            
        ratio = 0.8 if delta > 0 else 1.25
        
        x = event.position().x()
        w = self.width()
        graph_w = w - self.pad_left - self.pad_right
        
        x = max(self.pad_left, min(x, self.pad_left + graph_w))
        
        duration = self.view_end_time_ms - self.view_start_time_ms
        time_at_x = self.view_start_time_ms + ((x - self.pad_left) / graph_w) * duration
        
        new_duration = duration * ratio
        
        total_time = (len(self.data_a) * self.interval_ms) if self.data_a else 100.0
        if new_duration > total_time:
            new_duration = total_time
            
        pct_x = (x - self.pad_left) / graph_w
        self.view_start_time_ms = time_at_x - new_duration * pct_x
        self.view_end_time_ms = self.view_start_time_ms + new_duration
        self.clamp_view()
        self.update()

    def event(self, event):
        if event.type() == QEvent.Gesture:
            pinch = event.gesture(Qt.PinchGesture)
            if pinch:
                self.pinchEvent(pinch)
                return True
        return super().event(event)
        
    def pinchEvent(self, pinch):
        changeFlags = pinch.changeFlags()
        if changeFlags & QPinchGesture.ScaleFactorChanged:
            factor = pinch.scaleFactor()
            if factor <= 0:
                return
            
            ratio = 1.0 / factor
            
            center = pinch.centerPoint()
            x = center.x()
            
            w = self.width()
            graph_w = w - self.pad_left - self.pad_right
            
            x = max(self.pad_left, min(x, self.pad_left + graph_w))
            duration = self.view_end_time_ms - self.view_start_time_ms
            time_at_x = self.view_start_time_ms + ((x - self.pad_left) / graph_w) * duration
            
            new_duration = duration * ratio
            
            total_time = (len(self.data_a) * self.interval_ms) if self.data_a else 100.0
            if new_duration > total_time:
                new_duration = total_time
                
            pct_x = (x - self.pad_left) / graph_w
            self.view_start_time_ms = time_at_x - new_duration * pct_x
            self.view_end_time_ms = self.view_start_time_ms + new_duration
            self.clamp_view()
            self.update()
