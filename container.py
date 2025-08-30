from typing import Dict, Any, Type, Optional
from core.base_classes import SessionStateManager
from config.settings import ConfigManager
from utils.plot_manager import PlotlyPlotManager
from utils.data_handler import CSVDataHandler, ExcelDataHandler

class DIContainer:
    """Dependency Injection Container (Dependency Inversion Principle)"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        
        # Register default services
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default services"""
        # Singletons
        self.register_singleton('config_manager', ConfigManager)
        self.register_singleton('state_manager', SessionStateManager)
        
        # Services
        self.register_service('plot_manager', PlotlyPlotManager)
        self.register_service('csv_handler', CSVDataHandler)
        self.register_service('excel_handler', ExcelDataHandler)
    
    def register_service(self, name: str, service_class: Type) -> None:
        """Register a service class"""
        self._services[name] = service_class
    
    def register_singleton(self, name: str, singleton_class: Type) -> None:
        """Register a singleton class"""
        if name not in self._singletons:
            self._singletons[name] = singleton_class()
    
    def register_factory(self, name: str, factory_func) -> None:
        """Register a factory function"""
        self._factories[name] = factory_func
    
    def get(self, name: str) -> Optional[Any]:
        """Get a service instance"""
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]
        
        # Check services
        if name in self._services:
            return self._services[name]()
        
        # Check factories
        if name in self._factories:
            return self._factories[name]()
        
        return None
    
    def create_with_dependencies(self, class_type: Type, **kwargs) -> Any:
        """Create an instance with automatic dependency injection"""
        dependencies = {}
        
        # Get constructor parameters
        import inspect
        sig = inspect.signature(class_type.__init__)
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Check if dependency is provided in kwargs
            if param_name in kwargs:
                dependencies[param_name] = kwargs[param_name]
            # Try to resolve from container
            elif param_name in self._singletons:
                dependencies[param_name] = self._singletons[param_name]
            elif param_name in self._services:
                dependencies[param_name] = self._services[param_name]()
            # Use default if available
            elif param.default != inspect.Parameter.empty:
                continue  # Will use default
            else:
                # Try common naming patterns
                if param_name == 'state_manager':
                    dependencies[param_name] = self.get('state_manager')
                elif param_name == 'config_manager':
                    dependencies[param_name] = self.get('config_manager')
                elif param_name == 'plot_manager':
                    dependencies[param_name] = self.get('plot_manager')
        
        return class_type(**dependencies)


# Global container instance
container = DIContainer()