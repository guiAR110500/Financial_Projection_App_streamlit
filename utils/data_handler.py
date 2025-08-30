import pandas as pd
import streamlit as st
from typing import Optional
from core.interfaces import IDataHandler

class CSVDataHandler(IDataHandler):
    """Handles CSV data operations (Single Responsibility Principle)"""
    
    def load_data(self, source: str, separator: str = ';') -> Optional[pd.DataFrame]:
        """Load data from CSV file
        
        Args:
            source: File path to load
            separator: CSV separator character
            
        Returns:
            DataFrame or None if error
        """
        try:
            return pd.read_csv(source, sep=separator)
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo {source}: {e}")
            return None
    
    def save_data(self, data: pd.DataFrame, destination: str, separator: str = ';') -> bool:
        """Save DataFrame to CSV file
        
        Args:
            data: DataFrame to save
            destination: File path to save to
            separator: CSV separator character
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data.to_csv(destination, sep=separator, index=False)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar o arquivo {destination}: {e}")
            return False


class ExcelDataHandler(IDataHandler):
    """Handles Excel data operations (Single Responsibility Principle)"""
    
    def load_data(self, source: str, sheet_name: str = 0) -> Optional[pd.DataFrame]:
        """Load data from Excel file
        
        Args:
            source: File path to load
            sheet_name: Sheet name or index to load
            
        Returns:
            DataFrame or None if error
        """
        try:
            return pd.read_excel(source, sheet_name=sheet_name)
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo Excel {source}: {e}")
            return None
    
    def save_data(self, data: pd.DataFrame, destination: str, sheet_name: str = 'Sheet1') -> bool:
        """Save DataFrame to Excel file
        
        Args:
            data: DataFrame to save
            destination: File path to save to
            sheet_name: Sheet name to save to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with pd.ExcelWriter(destination, engine='openpyxl') as writer:
                data.to_excel(writer, sheet_name=sheet_name, index=False)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar o arquivo Excel {destination}: {e}")
            return False