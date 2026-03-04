import uiautomation as auto
import logging
from PIL import ImageDraw, ImageFont
import pyautogui
from typing import Optional, List
from src.windows.element import WindowsElementNode
import asyncio
import numpy as np
import time

logger = logging.getLogger(__name__)

class WindowsUITreeBuilder:
    def __init__(self):
        self.highlight_index = 0
        self._element_cache = {}
        self._processed_elements = set()
        self.max_depth = 30
        
    def reset_state(self):
        self.highlight_index = 0
        self._element_cache = {}
        self._processed_elements = set()

    def capture_screenshot(self):
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        return screenshot

    def annotate_screenshot(self, root: WindowsElementNode):
        screenshot = self.capture_screenshot()
        img_np = np.array(screenshot)

        # Use PIL to draw red bounding boxes on the image
        draw = ImageDraw.Draw(screenshot)
        try:
            # Arial or default font
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()

        def process_element(element):
            if element.highlight_index is not None and element.on_screen and element.position and element.size:
                x, y = element.position
                w, h = element.size
                
                # Draw rectangle border
                draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                
                # Draw index text
                idx_str = str(element.highlight_index)
                
                # Draw background for the text
                text_bbox = draw.textbbox((x, y), idx_str, font=font)
                draw.rectangle([text_bbox[0], text_bbox[1], text_bbox[2], text_bbox[3]], fill="red")
                draw.text((x, y), idx_str, font=font, fill="white")
                
            for child in element.children:
                process_element(child)

        process_element(root)
        return screenshot
        

    def _is_interactive(self, control: auto.Control) -> bool:
        # Check for standard interactive control types
        interactive_roles = [
            auto.ControlType.ButtonControl,
            auto.ControlType.CheckBoxControl,
            auto.ControlType.ComboBoxControl,
            auto.ControlType.EditControl,
            auto.ControlType.HyperlinkControl,
            auto.ControlType.ListItemControl,
            auto.ControlType.MenuItemControl,
            auto.ControlType.RadioButtonControl,
            auto.ControlType.TabItemControl,
            auto.ControlType.DocumentControl
        ]
        return control.ControlType in interactive_roles

    def build_tree(self, pid: Optional[int] = None) -> WindowsElementNode:
        self.reset_state()
        
        if pid:
            # Find the window by process ID
            auto.SetGlobalSearchTimeout(1.0)
            root_control = auto.WindowControl(searchDepth=1, ProcessId=pid)
            if not root_control.Exists(0, 0):
                root_control = auto.GetRootControl()
        else:
            root_control = auto.GetRootControl()
            
        screen_w, screen_h = pyautogui.size()

        def process_control(control: auto.Control, depth: int) -> Optional[WindowsElementNode]:
            if depth > self.max_depth:
                return None
                
            try:
                rect = control.BoundingRectangle
                x, y, r, b = rect.left, rect.top, rect.right, rect.bottom
                w, h = r - x, b - y
                on_screen = True
                
                # Simple on-screen visibility check
                if w <= 0 or h <= 0 or x >= screen_w or y >= screen_h or r <= 0 or b <= 0:
                    on_screen = False

                if control.IsOffscreen:
                    on_screen = False

                # Skip completely hidden subtrees to optimize speed and prevent token explosion
                if not on_screen and depth > 1:
                    return None

                is_interactive = self._is_interactive(control)
                
                actions = []
                if is_interactive:
                    actions.append("click")
                    
                attributes = {
                    "position": (x, y),
                    "size": (w, h),
                    "title": control.Name,
                    "description": control.LocalizedControlType,
                    "enabled": control.IsEnabled,
                    "actions": actions
                }
                
                node = WindowsElementNode(
                    role=control.LocalizedControlType or str(control.ControlType),
                    identifier=str(control.AutomationId),
                    attributes=attributes,
                    is_visible=not control.IsOffscreen,
                    app_pid=control.ProcessId,
                    on_screen=on_screen,
                    is_interactive=is_interactive,
                    parent=None,
                    children=[]
                )
                
                if on_screen and is_interactive:
                    self.highlight_index += 1
                    node.highlight_index = self.highlight_index
                    self._element_cache[self.highlight_index] = node
                else:
                    node.highlight_index = None

                # Recursively process child nodes
                for child in control.GetChildren():
                    child_node = process_control(child, depth + 1)
                    if child_node:
                        child_node.parent = node
                        node.children.append(child_node)
                        
                return node

            except Exception as e:
                logger.error(f"Error processing control: {e}")
                import traceback
                traceback.print_exc()
                return None

        root_node = process_control(root_control, 0)
        
        # Fallback empty root node
        if not root_node:
           root_node = WindowsElementNode(role="Root", identifier="", attributes={}, is_visible=True, app_pid=0, on_screen=True) 

        return root_node
        
    def get_vision_context(self):
        """Capture the UI tree and annotated screenshot with textual information"""
        root = self.build_tree()
        if root is None:
            return None, ""
            
        annotated_image = self.annotate_screenshot(root)
        elements_text = root._get_visible_clickable_elements_string()
        
        return annotated_image, elements_text
