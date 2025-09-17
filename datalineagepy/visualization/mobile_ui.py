"""
Mobile-optimized UI components for data lineage visualization.
Provides responsive, touch-friendly interfaces for mobile devices.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Set, Tuple
from datetime import datetime
from enum import Enum
import threading
import uuid

try:
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    go = None
    px = None

from .interactive_graph import GraphNode, GraphEdge, NodeType, EdgeType

logger = logging.getLogger(__name__)


class MobileViewType(Enum):
    """Mobile view types."""
    CARD_VIEW = "card_view"
    LIST_VIEW = "list_view"
    TREE_VIEW = "tree_view"
    TIMELINE_VIEW = "timeline_view"
    SEARCH_VIEW = "search_view"
    DETAIL_VIEW = "detail_view"
    GRAPH_VIEW = "graph_view"


class GestureType(Enum):
    """Mobile gesture types."""
    TAP = "tap"
    DOUBLE_TAP = "double_tap"
    LONG_PRESS = "long_press"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    PINCH_ZOOM = "pinch_zoom"
    PAN = "pan"


class ScreenSize(Enum):
    """Mobile screen sizes."""
    SMALL = "small"      # < 576px
    MEDIUM = "medium"    # 576px - 768px
    LARGE = "large"      # 768px - 992px
    EXTRA_LARGE = "xl"   # > 992px


@dataclass
class MobileConfig:
    """Configuration for mobile UI."""
    # Screen settings
    screen_width: int = 375
    screen_height: int = 667
    screen_size: ScreenSize = ScreenSize.MEDIUM
    pixel_density: float = 2.0
    
    # Touch settings
    touch_enabled: bool = True
    min_touch_target: int = 44  # pixels
    touch_feedback: bool = True
    haptic_feedback: bool = True
    
    # Navigation
    navigation_type: str = "bottom_tabs"  # bottom_tabs, drawer, top_tabs
    show_back_button: bool = True
    swipe_navigation: bool = True
    
    # Layout
    card_margin: int = 8
    card_padding: int = 16
    card_border_radius: int = 8
    list_item_height: int = 60
    header_height: int = 56
    footer_height: int = 60
    
    # Typography
    font_size_small: int = 12
    font_size_medium: int = 14
    font_size_large: int = 16
    font_size_xl: int = 20
    line_height: float = 1.4
    
    # Colors (mobile-optimized)
    primary_color: str = "#007AFF"
    secondary_color: str = "#5856D6"
    background_color: str = "#F2F2F7"
    card_background: str = "#FFFFFF"
    text_primary: str = "#000000"
    text_secondary: str = "#6D6D80"
    border_color: str = "#C6C6C8"
    
    # Dark mode
    dark_mode: bool = False
    dark_background: str = "#000000"
    dark_card_background: str = "#1C1C1E"
    dark_text_primary: str = "#FFFFFF"
    dark_text_secondary: str = "#8E8E93"
    
    # Performance
    lazy_loading: bool = True
    virtual_scrolling: bool = True
    max_visible_items: int = 50
    image_compression: bool = True
    
    # Offline support
    offline_mode: bool = True
    cache_size_mb: int = 50
    sync_on_reconnect: bool = True
    
    # Accessibility
    high_contrast: bool = False
    large_text: bool = False
    voice_over: bool = False
    reduced_motion: bool = False


@dataclass
class MobileCard:
    """Mobile card component."""
    id: str
    title: str
    subtitle: str = ""
    description: str = ""
    image_url: str = ""
    badge_text: str = ""
    badge_color: str = "#007AFF"
    
    # Actions
    primary_action: Optional[str] = None
    secondary_actions: List[str] = field(default_factory=list)
    
    # Styling
    background_color: str = "#FFFFFF"
    border_color: str = "#C6C6C8"
    text_color: str = "#000000"
    
    # Data
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # State
    selected: bool = False
    expanded: bool = False
    loading: bool = False
    error: Optional[str] = None


@dataclass
class MobileListItem:
    """Mobile list item component."""
    id: str
    title: str
    subtitle: str = ""
    icon: str = ""
    badge: str = ""
    
    # Actions
    action: Optional[str] = None
    swipe_actions: List[str] = field(default_factory=list)
    
    # Styling
    height: int = 60
    separator: bool = True
    
    # Data
    data: Dict[str, Any] = field(default_factory=dict)
    
    # State
    selected: bool = False
    disabled: bool = False


class MobileRenderer:
    """Mobile UI renderer for data lineage visualization."""
    
    def __init__(self, config: MobileConfig):
        self.config = config
        self.current_view: MobileViewType = MobileViewType.CARD_VIEW
        self.view_stack: List[MobileViewType] = []
        
        # Data
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.cards: Dict[str, MobileCard] = {}
        self.list_items: Dict[str, MobileListItem] = {}
        
        # State
        self.selected_items: Set[str] = set()
        self.search_query: str = ""
        self.filter_criteria: Dict[str, Any] = {}
        
        # Navigation
        self.navigation_history: List[Dict[str, Any]] = []
        self.current_page: int = 0
        self.items_per_page: int = 20
        
        # Gestures
        self.gesture_handlers: Dict[GestureType, List[Callable]] = {
            gesture: [] for gesture in GestureType
        }
        
        # Performance
        self.visible_items: List[str] = []
        self.cached_renders: Dict[str, str] = {}
        
        # Statistics
        self.stats = {
            'total_items': 0,
            'visible_items': 0,
            'cached_renders': 0,
            'gesture_events': 0,
            'view_changes': 0,
            'last_interaction': None,
        }
        
        self._lock = threading.Lock()
        
        if go is None:
            raise ImportError("plotly is required for mobile visualization")
    
    def set_view(self, view_type: MobileViewType):
        """Set the current view type."""
        if view_type != self.current_view:
            self.view_stack.append(self.current_view)
            self.current_view = view_type
            
            with self._lock:
                self.stats['view_changes'] += 1
    
    def go_back(self) -> bool:
        """Go back to the previous view."""
        if self.view_stack:
            self.current_view = self.view_stack.pop()
            return True
        return False
    
    def add_node_as_card(self, node: GraphNode) -> MobileCard:
        """Convert a graph node to a mobile card."""
        card = MobileCard(
            id=node.id,
            title=node.label,
            subtitle=node.node_type.value.replace('_', ' ').title(),
            description=node.tooltip or "",
            badge_text=str(len([e for e in self.edges.values() 
                              if e.source == node.id or e.target == node.id])),
            badge_color=node.color,
            data=node.metadata,
            metadata={'node_type': node.node_type, 'size': node.size}
        )
        
        with self._lock:
            self.cards[card.id] = card
            self.stats['total_items'] = len(self.cards)
        
        return card
    
    def add_node_as_list_item(self, node: GraphNode) -> MobileListItem:
        """Convert a graph node to a mobile list item."""
        item = MobileListItem(
            id=node.id,
            title=node.label,
            subtitle=node.node_type.value.replace('_', ' ').title(),
            icon=self._get_node_icon(node.node_type),
            badge=str(len([e for e in self.edges.values() 
                          if e.source == node.id or e.target == node.id])),
            data=node.metadata
        )
        
        with self._lock:
            self.list_items[item.id] = item
            self.stats['total_items'] = len(self.list_items)
        
        return item
    
    def _get_node_icon(self, node_type: NodeType) -> str:
        """Get icon for node type."""
        icon_map = {
            NodeType.TABLE: "📊",
            NodeType.VIEW: "👁️",
            NodeType.COLUMN: "📝",
            NodeType.TRANSFORMATION: "⚙️",
            NodeType.PIPELINE: "🔄",
            NodeType.DASHBOARD: "📈",
            NodeType.REPORT: "📋",
            NodeType.MODEL: "🤖",
            NodeType.DATASET: "💾",
            NodeType.API: "🔌",
            NodeType.FILE: "📄",
            NodeType.DATABASE: "🗄️",
        }
        return icon_map.get(node_type, "📦")
    
    def render_card_view(self) -> str:
        """Render card view for mobile."""
        if not self.cards:
            return self._render_empty_state("No data available")
        
        # Apply search and filters
        filtered_cards = self._filter_cards()
        
        # Pagination
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_cards = filtered_cards[start_idx:end_idx]
        
        # Update visible items
        self.visible_items = [card.id for card in page_cards]
        
        cards_html = []
        for card in page_cards:
            card_html = self._render_card(card)
            cards_html.append(card_html)
        
        # Wrap in container
        container_html = f"""
        <div class="mobile-card-view" style="
            padding: {self.config.card_margin}px;
            background-color: {self._get_background_color()};
            min-height: 100vh;
        ">
            {self._render_search_bar()}
            <div class="cards-container">
                {''.join(cards_html)}
            </div>
            {self._render_pagination()}
        </div>
        """
        
        return container_html
    
    def render_list_view(self) -> str:
        """Render list view for mobile."""
        if not self.list_items:
            return self._render_empty_state("No items available")
        
        # Apply search and filters
        filtered_items = self._filter_list_items()
        
        # Pagination
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = filtered_items[start_idx:end_idx]
        
        # Update visible items
        self.visible_items = [item.id for item in page_items]
        
        items_html = []
        for item in page_items:
            item_html = self._render_list_item(item)
            items_html.append(item_html)
        
        # Wrap in container
        container_html = f"""
        <div class="mobile-list-view" style="
            background-color: {self._get_background_color()};
            min-height: 100vh;
        ">
            {self._render_search_bar()}
            <div class="list-container">
                {''.join(items_html)}
            </div>
            {self._render_pagination()}
        </div>
        """
        
        return container_html
    
    def render_graph_view(self) -> str:
        """Render simplified graph view for mobile."""
        if not self.nodes:
            return self._render_empty_state("No graph data available")
        
        # Create simplified mobile graph
        try:
            # Use smaller subset for mobile performance
            visible_nodes = list(self.nodes.values())[:self.config.max_visible_items]
            
            # Create mobile-optimized graph
            x_coords = [node.x for node in visible_nodes]
            y_coords = [node.y for node in visible_nodes]
            texts = [node.label[:20] + "..." if len(node.label) > 20 else node.label 
                    for node in visible_nodes]
            colors = [node.color for node in visible_nodes]
            sizes = [max(20, min(40, node.size)) for node in visible_nodes]  # Constrain size for mobile
            
            fig = go.Figure()
            
            # Add nodes
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers+text',
                marker=dict(
                    size=sizes,
                    color=colors,
                    opacity=0.8,
                    line=dict(width=2, color='white')
                ),
                text=texts,
                textposition="middle center",
                textfont=dict(size=self.config.font_size_small),
                hovertemplate='<b>%{text}</b><extra></extra>',
                showlegend=False
            ))
            
            # Mobile-optimized layout
            fig.update_layout(
                width=self.config.screen_width,
                height=self.config.screen_height - 120,  # Account for header/footer
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                plot_bgcolor=self._get_background_color(),
                paper_bgcolor=self._get_background_color(),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                dragmode='pan',
                scrollZoom=True
            )
            
            return fig.to_html(
                include_plotlyjs='cdn',
                config={
                    'displayModeBar': False,
                    'responsive': True,
                    'doubleClick': 'reset',
                    'showTips': False,
                    'scrollZoom': True,
                    'touchZoom': True,
                    'displaylogo': False
                }
            )
            
        except Exception as e:
            logger.error(f"Error rendering mobile graph: {e}")
            return self._render_error_state("Error loading graph")
    
    def _render_card(self, card: MobileCard) -> str:
        """Render a single card."""
        badge_html = ""
        if card.badge_text:
            badge_html = f"""
            <span class="card-badge" style="
                background-color: {card.badge_color};
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: {self.config.font_size_small}px;
                font-weight: bold;
            ">{card.badge_text}</span>
            """
        
        return f"""
        <div class="mobile-card" 
             data-id="{card.id}"
             onclick="handleCardClick('{card.id}')"
             style="
                background-color: {card.background_color};
                border: 1px solid {card.border_color};
                border-radius: {self.config.card_border_radius}px;
                padding: {self.config.card_padding}px;
                margin-bottom: {self.config.card_margin}px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                min-height: {self.config.min_touch_target}px;
             "
             onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.15)'"
             onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'">
            
            <div class="card-header" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            ">
                <h3 style="
                    margin: 0;
                    font-size: {self.config.font_size_large}px;
                    color: {self._get_text_color()};
                    font-weight: 600;
                ">{card.title}</h3>
                {badge_html}
            </div>
            
            <div class="card-subtitle" style="
                font-size: {self.config.font_size_medium}px;
                color: {self._get_secondary_text_color()};
                margin-bottom: 8px;
            ">{card.subtitle}</div>
            
            <div class="card-description" style="
                font-size: {self.config.font_size_small}px;
                color: {self._get_secondary_text_color()};
                line-height: {self.config.line_height};
            ">{card.description}</div>
        </div>
        """
    
    def _render_list_item(self, item: MobileListItem) -> str:
        """Render a single list item."""
        separator_style = "border-bottom: 1px solid " + self.config.border_color if item.separator else ""
        
        badge_html = ""
        if item.badge:
            badge_html = f"""
            <span class="list-badge" style="
                background-color: {self.config.primary_color};
                color: white;
                padding: 2px 6px;
                border-radius: 10px;
                font-size: {self.config.font_size_small}px;
                margin-left: 8px;
            ">{item.badge}</span>
            """
        
        return f"""
        <div class="mobile-list-item"
             data-id="{item.id}"
             onclick="handleListItemClick('{item.id}')"
             style="
                display: flex;
                align-items: center;
                padding: 12px 16px;
                height: {item.height}px;
                background-color: {self._get_card_background()};
                {separator_style};
                cursor: pointer;
                transition: background-color 0.2s;
                min-height: {self.config.min_touch_target}px;
             "
             onmouseover="this.style.backgroundColor='{self._get_hover_color()}'"
             onmouseout="this.style.backgroundColor='{self._get_card_background()}'">
            
            <div class="item-icon" style="
                font-size: {self.config.font_size_large}px;
                margin-right: 12px;
                width: 24px;
                text-align: center;
            ">{item.icon}</div>
            
            <div class="item-content" style="flex: 1;">
                <div class="item-title" style="
                    font-size: {self.config.font_size_medium}px;
                    color: {self._get_text_color()};
                    font-weight: 500;
                    margin-bottom: 2px;
                ">{item.title}</div>
                
                <div class="item-subtitle" style="
                    font-size: {self.config.font_size_small}px;
                    color: {self._get_secondary_text_color()};
                ">{item.subtitle}</div>
            </div>
            
            <div class="item-accessories">
                {badge_html}
                <span style="
                    color: {self._get_secondary_text_color()};
                    font-size: {self.config.font_size_large}px;
                    margin-left: 8px;
                ">›</span>
            </div>
        </div>
        """
    
    def _render_search_bar(self) -> str:
        """Render search bar."""
        return f"""
        <div class="search-bar" style="
            background-color: {self._get_card_background()};
            padding: 12px 16px;
            margin-bottom: 16px;
            border-radius: {self.config.card_border_radius}px;
            border: 1px solid {self.config.border_color};
        ">
            <input type="text" 
                   placeholder="Search..." 
                   value="{self.search_query}"
                   oninput="handleSearch(this.value)"
                   style="
                       width: 100%;
                       border: none;
                       outline: none;
                       font-size: {self.config.font_size_medium}px;
                       color: {self._get_text_color()};
                       background: transparent;
                       min-height: {self.config.min_touch_target}px;
                   ">
        </div>
        """
    
    def _render_pagination(self) -> str:
        """Render pagination controls."""
        total_items = len(self.cards) if self.current_view == MobileViewType.CARD_VIEW else len(self.list_items)
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        
        if total_pages <= 1:
            return ""
        
        prev_disabled = "opacity: 0.5; pointer-events: none;" if self.current_page == 0 else ""
        next_disabled = "opacity: 0.5; pointer-events: none;" if self.current_page >= total_pages - 1 else ""
        
        return f"""
        <div class="pagination" style="
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            gap: 16px;
        ">
            <button onclick="handlePrevPage()" style="
                background-color: {self.config.primary_color};
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: {self.config.card_border_radius}px;
                font-size: {self.config.font_size_medium}px;
                cursor: pointer;
                min-height: {self.config.min_touch_target}px;
                min-width: {self.config.min_touch_target}px;
                {prev_disabled}
            ">‹ Prev</button>
            
            <span style="
                font-size: {self.config.font_size_medium}px;
                color: {self._get_text_color()};
            ">{self.current_page + 1} of {total_pages}</span>
            
            <button onclick="handleNextPage()" style="
                background-color: {self.config.primary_color};
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: {self.config.card_border_radius}px;
                font-size: {self.config.font_size_medium}px;
                cursor: pointer;
                min-height: {self.config.min_touch_target}px;
                min-width: {self.config.min_touch_target}px;
                {next_disabled}
            ">Next ›</button>
        </div>
        """
    
    def _render_empty_state(self, message: str) -> str:
        """Render empty state."""
        return f"""
        <div class="empty-state" style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 50vh;
            text-align: center;
            padding: 40px 20px;
        ">
            <div style="
                font-size: 48px;
                margin-bottom: 16px;
                opacity: 0.5;
            ">📊</div>
            <h3 style="
                font-size: {self.config.font_size_large}px;
                color: {self._get_text_color()};
                margin-bottom: 8px;
            ">{message}</h3>
            <p style="
                font-size: {self.config.font_size_medium}px;
                color: {self._get_secondary_text_color()};
            ">Try adjusting your search or filters</p>
        </div>
        """
    
    def _render_error_state(self, message: str) -> str:
        """Render error state."""
        return f"""
        <div class="error-state" style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 50vh;
            text-align: center;
            padding: 40px 20px;
        ">
            <div style="
                font-size: 48px;
                margin-bottom: 16px;
                color: #FF3B30;
            ">⚠️</div>
            <h3 style="
                font-size: {self.config.font_size_large}px;
                color: {self._get_text_color()};
                margin-bottom: 8px;
            ">{message}</h3>
            <button onclick="location.reload()" style="
                background-color: {self.config.primary_color};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: {self.config.card_border_radius}px;
                font-size: {self.config.font_size_medium}px;
                cursor: pointer;
                margin-top: 16px;
                min-height: {self.config.min_touch_target}px;
            ">Retry</button>
        </div>
        """
    
    def _filter_cards(self) -> List[MobileCard]:
        """Filter cards based on search and criteria."""
        cards = list(self.cards.values())
        
        if self.search_query:
            query = self.search_query.lower()
            cards = [card for card in cards 
                    if query in card.title.lower() or 
                       query in card.subtitle.lower() or 
                       query in card.description.lower()]
        
        return cards
    
    def _filter_list_items(self) -> List[MobileListItem]:
        """Filter list items based on search and criteria."""
        items = list(self.list_items.values())
        
        if self.search_query:
            query = self.search_query.lower()
            items = [item for item in items 
                    if query in item.title.lower() or 
                       query in item.subtitle.lower()]
        
        return items
    
    def _get_background_color(self) -> str:
        """Get background color based on theme."""
        return self.config.dark_background if self.config.dark_mode else self.config.background_color
    
    def _get_card_background(self) -> str:
        """Get card background color based on theme."""
        return self.config.dark_card_background if self.config.dark_mode else self.config.card_background
    
    def _get_text_color(self) -> str:
        """Get text color based on theme."""
        return self.config.dark_text_primary if self.config.dark_mode else self.config.text_primary
    
    def _get_secondary_text_color(self) -> str:
        """Get secondary text color based on theme."""
        return self.config.dark_text_secondary if self.config.dark_mode else self.config.text_secondary
    
    def _get_hover_color(self) -> str:
        """Get hover color."""
        if self.config.dark_mode:
            return "#2C2C2E"
        else:
            return "#F0F0F0"
    
    def handle_gesture(self, gesture: GestureType, data: Dict[str, Any]):
        """Handle mobile gesture."""
        with self._lock:
            self.stats['gesture_events'] += 1
            self.stats['last_interaction'] = datetime.utcnow()
        
        # Call registered handlers
        for handler in self.gesture_handlers.get(gesture, []):
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Error handling gesture {gesture}: {e}")
    
    def search(self, query: str):
        """Set search query."""
        self.search_query = query
        self.current_page = 0  # Reset to first page
    
    def next_page(self):
        """Go to next page."""
        total_items = len(self.cards) if self.current_view == MobileViewType.CARD_VIEW else len(self.list_items)
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
    
    def prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mobile renderer statistics."""
        with self._lock:
            stats = self.stats.copy()
            stats['visible_items'] = len(self.visible_items)
            stats['cached_renders'] = len(self.cached_renders)
            return stats


def create_mobile_renderer(
    screen_width: int = 375,
    screen_height: int = 667,
    dark_mode: bool = False,
    **kwargs
) -> MobileRenderer:
    """Factory function to create mobile renderer."""
    config = MobileConfig(
        screen_width=screen_width,
        screen_height=screen_height,
        dark_mode=dark_mode,
        **kwargs
    )
    return MobileRenderer(config)
