import streamlit as st
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .interfaces import IPage, IStateManager

class BasePage(IPage):
    """Base class for all pages following Template Method pattern"""
    
    def __init__(self, state_manager: Optional[IStateManager] = None):
        self._state_manager = state_manager or SessionStateManager()
        self._initialize_state()
    
    @abstractmethod
    def _initialize_state(self) -> None:
        """Initialize page-specific state"""
        pass
    
    @abstractmethod
    def _render_content(self) -> None:
        """Render the main page content"""
        pass
    
    def render(self) -> None:
        """Template method for rendering pages"""
        self._render_header()
        self._render_content()
        self._render_footer()
    
    def _render_header(self) -> None:
        """Render page header"""
        from utils.ui_components import styled_title
        styled_title(f"{self.icon} {self.title}")
    
    def _render_footer(self) -> None:
        """Override in subclasses if footer needed"""
        pass


class SessionStateManager(IStateManager):
    """Manages Streamlit session state (Single Responsibility Principle)"""
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value by key"""
        return st.session_state.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """Set state value for key"""
        st.session_state[key] = value
    
    def update_state(self, key: str, updates: Dict[str, Any]) -> None:
        """Update state with partial updates"""
        if key not in st.session_state:
            st.session_state[key] = {}
        
        if isinstance(st.session_state[key], dict):
            st.session_state[key].update(updates)
        else:
            raise ValueError(f"State at key '{key}' is not a dictionary")
    
    def ensure_state(self, key: str, default_value: Any) -> None:
        """Ensure state exists with default value if not present"""
        if key not in st.session_state:
            st.session_state[key] = default_value


class BaseCalculator(ICalculator):
    """Base class for calculators (Single Responsibility Principle)"""
    
    def __init__(self, state_manager: Optional[IStateManager] = None):
        self._state_manager = state_manager or SessionStateManager()
    
    @abstractmethod
    def _validate_inputs(self, **kwargs) -> bool:
        """Validate calculation inputs"""
        pass
    
    @abstractmethod
    def _perform_calculation(self, **kwargs) -> Dict[str, Any]:
        """Perform the actual calculation"""
        pass
    
    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Template method for calculations"""
        if not self._validate_inputs(**kwargs):
            raise ValueError("Invalid inputs for calculation")
        
        return self._perform_calculation(**kwargs)