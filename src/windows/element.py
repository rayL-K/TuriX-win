# --- START OF FILE mac_use/mac/element.py ---
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from functools import cached_property
import logging
logger = logging.getLogger(__name__)
@dataclass
class WindowsElementNode:
    """表示具有增强辅助信息的 Windows 界面元素节点"""
    # 必填字段
    role: str
    identifier: str
    attributes: Dict[str, Any]
    is_visible: bool
    app_pid: int
    on_screen: bool

    # 可选字段
    children: List['WindowsElementNode'] = field(default_factory=list)
    parent: Optional['WindowsElementNode'] = None
    is_interactive: bool = False
    highlight_index: Optional[int] = None
    _element = None  # Store AX element reference

    @property
    def actions(self) -> List[str]:
        """获取此元素适用的交互动作列表。"""
        list_actions = self.attributes.get('actions', [])
        return list_actions

    @property
    def enabled(self) -> bool:
        """检查该元素是否已被启用。"""
        return self.attributes.get('enabled', True)

    @property
    def position(self) -> Optional[tuple]:
        """获取元素的屏幕坐标位置。"""
        return self.attributes.get('position')

    @property
    def size(self) -> Optional[tuple]:
        """获取元素的尺寸。"""
        return self.attributes.get('size')

    def __repr__(self) -> str:
        """包含更多属性信息的增强型字符串表示形式。"""
        role_str = f'<{self.role}'

        # 将重要属性添加到字符串中
        important_attrs = ['title', 'value', 'description', 'enabled']
        for key in important_attrs:
            if key in self.attributes:
                role_str += f' {key}="{self.attributes[key]}"'

        # 附加坐标与尺寸
        if self.position:
            role_str += f' pos={self.position}'
        if self.size:
            role_str += f' size={self.size}'

        role_str += '>'

        # 附加状态提示标签
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
    # 内部方法：一种结构紧凑的元素表示短语（供“短版本”界面视图使用）
    # ------------------------------------------------------------------------
    def _format_short_element(self) -> str:
        """
        生成一个简短、干净的摘要字符串：
         - 使用 highlight_index 或 '_' 作为前缀
         - UI 角色类别
         - 如果存在标题或描述，则予以显示
         - 括号中的位置/尺寸
         - 如果可交互，显示具备的操作
        """
        # 前缀决定：如果是由于上下文被附加到屏幕的则用下划线占位
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

        # 如果交互的，顺势提及操作方法
        extras = []
        if self.is_interactive:
            extras.append('interactive')
            if self.actions:
                extras.append(f'actions={self.actions}')

        if extras:
            role_part += f' [{", ".join(extras)}]'

        return f'{prefix}[:]{role_part}'

    # ------------------------------------------------------------------------
    # 1) 包含较多详细信息的“精简”版本
    # ------------------------------------------------------------------------
    def _get_visible_clickable_elements_string_short(self) -> str:
        """将 UI 树转换为字符串，仅关注支持交互以及提供上下文描述的元素"""
        formatted_text = []
        def process_node(node: 'WindowsElementNode', depth: int) -> None:
            # 拼接属性字符串
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
    # 2) 细节最丰富的“原始”版本
    # ------------------------------------------------------------------------
    def _get_visible_clickable_elements_string_original(self) -> str:
        """
        原始长版本：
        返回界面遍历节点的各种属性、坐标点和交互上下文。
        """
        formatted_text = []
        def process_node(node: 'WindowsElementNode', depth: int) -> None:
            # 构建节点属性串
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
                    
                # 检测当前是不是能提供信息的上下文元素（仅作文本补充说明，无须支持打标和交互）
                if (node.role in ['AXStaticText', 'AXTextField', 'TextControl', 'ImageControl'] and 
                      not node.is_interactive and 
                      (node.parent is None or node.parent.role in ['AXWindow', 'WindowControl'] or node.parent.is_interactive)):
                    # 不可交互仅供大模型阅读上下文的条目使用下划线 "_" 索引
                    
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
            # 返回折叠版字符串
            logger.debug('界面文本提取超长 (Token > 10000)，降级到短版本输出。')
            return ''
        else:
            # 返回原始长版本字符串
            logger.debug(f'占用 Token 数为 {total_tokens}，使用完整原版界面树结构。')
            return self._get_visible_clickable_elements_string_short()
        
    def get_detailed_info(self) -> str:
        """返回包含该元素所有属性的详细字符串。"""
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
        """递归构建界面节点树的多级属性字符串表示。"""
        spaces = " " * indent
        result = (
            f"{spaces}{self.__repr__()}\n{spaces}Details: {self.get_detailed_info()}"
        )
        for child in self.children:
            result += "\n" + child.get_detailed_string(indent + 2)
        return result

    @cached_property
    def accessibility_path(self) -> str:
        """生成指向此元素的独有辅助功能路径（包括更多修饰符）"""
        path_components = []
        current = self
        while current.parent is not None:
            role = current.role

            # 加上标识符使路径具有特异性
            identifiers = []
            if 'title' in current.attributes:
                identifiers.append(f"title={current.attributes['title']}")
            if 'description' in current.attributes:
                identifiers.append(f"desc={current.attributes['description']}")

            # 统计拥有共同类型的兄弟节点
            siblings = [s for s in current.parent.children if s.role == role]
            if len(siblings) > 1:
                idx = siblings.index(current) + 1
                path_component = f"{role}[{idx}]"
            else:
                path_component = role

            # 如果标识符存在即拼接到路径串中
            if identifiers:
                path_component += f"({','.join(identifiers)})"

            path_components.append(path_component)
            current = current.parent

        path_components.reverse()
        return '/' + '/'.join(path_components)

    def find_element_by_path(self, path: str) -> Optional['WindowsElementNode']:
        """根据辅助路径寻找目标元素节点。"""
        if self.accessibility_path == path:
            return self
        for child in self.children:
            result = child.find_element_by_path(path)
            if result:
                return result
        return None

    def find_elements_by_action(self, action: str) -> List['WindowsElementNode']:
        """通过指定行为动作匹配对应的所有元素节点。"""
        elements = []
        if action in self.actions:
            elements.append(self)
        for child in self.children:
            elements.extend(child.find_elements_by_action(action))
        return elements
