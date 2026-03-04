# --- START OF FILE mac_use/mac/element.py ---
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from functools import cached_property
import logging
logger = logging.getLogger(__name__)
@dataclass
class WindowsElementNode:
    """Simplified Windows UI element node with enhanced accessibility information"""
    # Required fields
    role: str
    identifier: str
    attributes: Dict[str, Any]
    is_visible: bool
    app_pid: int
    on_screen: bool

    # Optional fields
    children: List['WindowsElementNode'] = field(default_factory=list)
    parent: Optional['WindowsElementNode'] = None
    is_interactive: bool = False
    highlight_index: Optional[int] = None
    _element = None  # Store AX element reference

    @property
    def actions(self) -> List[str]:
        """Get the list of interactive actions applicable to this element."""
        list_actions = self.attributes.get('actions', [])
        return list_actions

    @property
    def enabled(self) -> bool:
        """Check if the element is enabled."""
        return self.attributes.get('enabled', True)

    @property
    def position(self) -> Optional[tuple]:
        """Get the screen coordinates of the element."""
        return self.attributes.get('position')

    @property
    def size(self) -> Optional[tuple]:
        """Get the size of the element."""
        return self.attributes.get('size')

    def __repr__(self) -> str:
        """Detailed string representation including more attributes."""
        role_str = f'<{self.role}'

        # Add important attributes to the string
        important_attrs = ['title', 'value', 'description', 'enabled']
        for key in important_attrs:
            if key in self.attributes:
                role_str += f' {key}="{self.attributes[key]}"'

        # Append coordinates and size
        if self.position:
            role_str += f' pos={self.position}'
        if self.size:
            role_str += f' size={self.size}'

        role_str += '>'

        # Append state labels
        extras = []
        if self.is_interactive:
            extras.append('interactive')
            if self.actions:
                extras.append(f'actions={self.actions}')
        if self.highlight_index is not None:
            extras.append(f'highlight:{self.highlight_index}')
        if not self.enabled:
            extras.append('disabled')

        if extras:
            role_str += f' [{", ".join(extras)}]'

        return role_str

    # ------------------------------------------------------------------------
    # Helper: A compact element representation for short UI views
    # ------------------------------------------------------------------------
    def _format_short_element(self) -> str:
        """
        Generate a short, clean summary string:
         - Prefix with highlight_index or '_'
         - UI role
         - Title or description if available
         - Position and size in brackets
         - Available actions if interactive
        """
        # Prefix: use underscore if the element is added as context
        prefix = f'{self.highlight_index}' if self.highlight_index is not None else '_'
        # Basic role
        role_part = f'<{self.role}'
        # Possibly add title
        if 'title' in self.attributes:
            role_part += f' title="{self.attributes["title"]}"'
        # Possibly add description
        if 'description' in self.attributes:
            role_part += f' description="{self.attributes["description"]}"'

        # location/size
        pos = self.attributes.get('position')
        siz = self.attributes.get('size')
        if pos and siz:
            role_part += f' pos={pos} size={siz}'

        role_part += '>'

        # If interactive, include actions
        extras = []
        if self.is_interactive:
            extras.append('interactive')
            if self.actions:
                extras.append(f'actions={self.actions}')

        if extras:
            role_part += f' [{", ".join(extras)}]'

        return f'{prefix}[:]{role_part}'

    # ------------------------------------------------------------------------
    # 1) Short version focusing on interaction and context
    # ------------------------------------------------------------------------
    def _get_visible_clickable_elements_string_short(self) -> str:
        """Convert UI tree to string focusing on interactive and context elements"""
        formatted_text = []
        def process_node(node: 'WindowsElementNode', depth: int) -> None:
            # Concatenate attributes
            if not node.highlight_index or not node.on_screen:
                pass
            elif node.role in ['AXStaticText', 'AXGroup', 'AXImage']:
                pass
            else:
                attrs_str = ''
                important_attrs = ['title', 'value', 'description','position','size']
                # logger.debug(f'Processing node: {node.role} with attributes: {node.attributes}')
                for key in important_attrs:
                    val = node.attributes.get(key)
                    if val is not None and val != "":
                        if key == 'position':
                            attrs_str += f' pos: {val}'
                        elif key == 'size':
                            attrs_str += f' size: {val}'
                        elif key == 'enabled':
                            if not val:
                                attrs_str += f' disabled'
                        else:
                            attrs_str += f' {key}="{val}"'
                if attrs_str != '':
                    formatted_text.append(
                        f'{node.highlight_index}[:]<{node.role}{attrs_str}>'
                    )

            for child in node.children:
                process_node(child, depth + 1)

        process_node(self, 0)
        return '\n'.join(formatted_text)

    # ------------------------------------------------------------------------
    # 2) Original detailed version
    # ------------------------------------------------------------------------
    def _get_visible_clickable_elements_string_original(self) -> str:
        """
        Original detailed version:
        Returns attributes, coordinates, and context for the traversal nodes.
        """
        formatted_text = []
        def process_node(node: 'WindowsElementNode', depth: int) -> None:
            # Build node attribute string
            if not node.on_screen:
                pass
            else:
                if node.highlight_index:
                    attrs_str = ''
                    important_attrs = ['title', 'value', 'description', 'enabled','position','size']
                    # logger.debug(f'Processing node: {node.role} with attributes: {node.attributes}')
                    for key in important_attrs:
                        val = node.attributes.get(key)
                        if val is not None and val != "":
                            if key == 'position':
                                attrs_str += f' pos: {val}'
                            elif key == 'size':
                                attrs_str += f' size: {val}'
                            elif key == 'enabled':
                                if not val:
                                    attrs_str += f' disabled'
                            else:
                                attrs_str += f' {key}="{val}"'

                    formatted_text.append(
                        f'{node.highlight_index}[:]<{node.role}{attrs_str}> [interactive]'
                    )
                    
                # Check if it's an informative context element (not interactive)
                if (node.role in ['AXStaticText', 'AXTextField', 'TextControl', 'ImageControl'] and 
                      not node.is_interactive and 
                      (node.parent is None or node.parent.role in ['AXWindow', 'WindowControl'] or node.parent.is_interactive)):
                    # Use underscore for non-interactive context elements
                    
                    attrs_str = ''
                    important_attrs = ['title', 'value', 'description', 'enabled','position','size']
                    for key in important_attrs:
                        val = node.attributes.get(key)
                        if val is not None and val != "":
                            if key == 'position':
                                attrs_str += f' pos: {val}'
                            elif key == 'size':
                                attrs_str += f' size: {val}'
                            elif key == 'enabled':
                                if not val:
                                    attrs_str += f' disabled'
                            else:
                                attrs_str += f' {key}="{val}"'
                                
                    formatted_text.append(
                        f'_[:]<{node.role}{attrs_str}> [context]'
                    )

            for child in node.children:
                process_node(child, depth + 1)

        process_node(self, 0)
        return '\n'.join(formatted_text)

    def _get_visible_clickable_elements_string(self) -> str:
        def count_tokens(text: str, estimated_tokens_per_character: int = 3) -> int:
            return len(text) // estimated_tokens_per_character
        total_tokens = count_tokens(self._get_visible_clickable_elements_string_original())
        if total_tokens > 10000:
            # Return collapsed version
            logger.debug('UI tree text too long (> 10000 tokens), falling back to short version.')
            return ''
        else:
            # Return original long version string
            logger.debug(f'Token count: {total_tokens}, using full original UI tree structure.')
            return self._get_visible_clickable_elements_string_short()
        
    def get_detailed_info(self) -> str:
        """Return a detailed string containing all attributes."""
        details =[
            f"Role: {self.role}",
            f"Identifier: {self.identifier}",
            f"Interactive: {self.is_interactive}",
            f"Enabled: {self.enabled}",
            f"Visible: {self.is_visible}"
        ]

        if self.actions:
            details.append(f"Actions: {self.actions}")

        if self.position:
            details.append(f"Position: {self.position}")

        if self.size:
            details.append(f"Size: {self.size}")

        for key, value in self.attributes.items():
            if key not in ['actions', 'enabled', 'position', 'size']:
                details.append(f"{key}: {value}")

        return ", ".join(details)

    def get_detailed_string(self, indent: int = 0) -> str:
        """Recursively build a multi-level attribute string for the node tree."""
        spaces = " " * indent
        result = (
            f"{spaces}{self.__repr__()}\n{spaces}Details: {self.get_detailed_info()}"
        )
        for child in self.children:
            result += "\n" + child.get_detailed_string(indent + 2)
        return result

    @cached_property
    def accessibility_path(self) -> str:
        """Generate a unique accessibility path for this element."""
        path_components = []
        current = self
        while current.parent is not None:
            role = current.role

            # Add identifiers for path specificity
            identifiers = []
            if 'title' in current.attributes:
                identifiers.append(f"title={current.attributes['title']}")
            if 'description' in current.attributes:
                identifiers.append(f"desc={current.attributes['description']}")

            # Count siblings with the same role
            siblings = [s for s in current.parent.children if s.role == role]
            if len(siblings) > 1:
                idx = siblings.index(current) + 1
                path_component = f"{role}[{idx}]"
            else:
                path_component = role

            # Append identifier if it exists
            if identifiers:
                path_component += f"({','.join(identifiers)})"

            path_components.append(path_component)
            current = current.parent

        path_components.reverse()
        return '/' + '/'.join(path_components)

    def find_element_by_path(self, path: str) -> Optional['WindowsElementNode']:
        """Find an element node by its accessibility path."""
        if self.accessibility_path == path:
            return self
        for child in self.children:
            result = child.find_element_by_path(path)
            if result:
                return result
        return None

    def find_elements_by_action(self, action: str) -> List['WindowsElementNode']:
        """Find all element nodes by a specific action."""
        elements = []
        if action in self.actions:
            elements.append(self)
        for child in self.children:
            elements.extend(child.find_elements_by_action(action))
        return elements
