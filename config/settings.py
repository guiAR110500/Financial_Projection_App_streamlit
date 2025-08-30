from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

@dataclass
class AppSettings:
    """Application settings (Single Responsibility Principle)"""
    
    # UI Settings
    logo_path: str = "C:\\Users\\Guilherme\\Documents\\Scratch\\TuaVitaLogo.jpg"
    app_title: str = "TuaVita Dashboard"
    app_version: str = "v1.0"
    
    # Data Settings
    default_months: int = 60
    default_csv_separator: str = ";"
    
    # Financial Settings
    default_ticket_medio: float = 2400.0
    default_tax_rate: float = 0.15
    
    # Visualization Settings
    plot_types: list = None
    time_frames: list = None
    
    def __post_init__(self):
        if self.plot_types is None:
            self.plot_types = ["Gráfico de Barras", "Gráfico de Linhas", "Gráfico de Pizza"]
        if self.time_frames is None:
            self.time_frames = ["Mensal", "Trimestral", "Semestral", "Anual"]
    
    @classmethod
    def from_env(cls) -> 'AppSettings':
        """Create settings from environment variables"""
        return cls(
            logo_path=os.getenv('APP_LOGO_PATH', cls.logo_path),
            app_title=os.getenv('APP_TITLE', cls.app_title),
            app_version=os.getenv('APP_VERSION', cls.app_version),
            default_months=int(os.getenv('DEFAULT_MONTHS', cls.default_months)),
            default_csv_separator=os.getenv('CSV_SEPARATOR', cls.default_csv_separator),
            default_ticket_medio=float(os.getenv('DEFAULT_TICKET_MEDIO', cls.default_ticket_medio)),
            default_tax_rate=float(os.getenv('DEFAULT_TAX_RATE', cls.default_tax_rate))
        )


@dataclass
class PageConfig:
    """Configuration for page groups and navigation"""
    
    page_groups: Dict[str, list] = None
    
    def __post_init__(self):
        if self.page_groups is None:
            # This will be populated dynamically
            self.page_groups = {}
    
    def add_group(self, group_name: str, pages: list) -> None:
        """Add a page group"""
        self.page_groups[group_name] = pages
    
    def get_group(self, group_name: str) -> Optional[list]:
        """Get pages in a group"""
        return self.page_groups.get(group_name)
    
    def get_all_groups(self) -> Dict[str, list]:
        """Get all page groups"""
        return self.page_groups


class ConfigManager:
    """Manages application configuration (Singleton pattern)"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.app_settings = AppSettings.from_env()
            self.page_config = PageConfig()
            self._initialized = True
    
    def get_app_settings(self) -> AppSettings:
        """Get application settings"""
        return self.app_settings
    
    def get_page_config(self) -> PageConfig:
        """Get page configuration"""
        return self.page_config
    
    def update_settings(self, **kwargs) -> None:
        """Update application settings"""
        for key, value in kwargs.items():
            if hasattr(self.app_settings, key):
                setattr(self.app_settings, key, value)