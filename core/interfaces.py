from abc import ABC, abstractmethod
from typing import Optional, Any, Dict

class IDataHandler(ABC):
    """Interface for data handling operations (Interface Segregation Principle)"""
    
    @abstractmethod
    def load_data(self, source: str) -> Optional[Any]:
        """Load data from a source"""
        pass
    
    @abstractmethod
    def save_data(self, data: Any, destination: str) -> bool:
        """Save data to a destination"""
        pass


class IPlotManager(ABC):
    """Interface for plot management (Interface Segregation Principle)"""
    
    @abstractmethod
    def create_plot(self, data: Any, plot_type: str, **kwargs) -> Any:
        """Create a plot based on type and data"""
        pass


class IPage(ABC):
    """Interface for page rendering (Single Responsibility Principle)"""
    
    @abstractmethod
    def render(self) -> None:
        """Render the page content"""
        pass
    
    @property
    @abstractmethod
    def title(self) -> str:
        """Return the page title"""
        pass
    
    @property
    @abstractmethod
    def icon(self) -> str:
        """Return the page icon"""
        pass


class ICalculator(ABC):
    """Interface for calculation operations (Single Responsibility Principle)"""
    
    @abstractmethod
    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Perform calculations and return results"""
        pass


class IStateManager(ABC):
    """Interface for state management (Single Responsibility Principle)"""
    
    @abstractmethod
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value by key"""
        pass
    
    @abstractmethod
    def set_state(self, key: str, value: Any) -> None:
        """Set state value for key"""
        pass
    
    @abstractmethod
    def update_state(self, key: str, updates: Dict[str, Any]) -> None:
        """Update state with partial updates"""
        pass