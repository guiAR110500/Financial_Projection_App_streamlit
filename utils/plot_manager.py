import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Any, Optional, Dict
from core.interfaces import IPlotManager

class PlotlyPlotManager(IPlotManager):
    """Manages plot creation using Plotly (Single Responsibility Principle)"""
    
    def create_plot(self, data: Any, plot_type: str, **kwargs) -> Any:
        """Factory method for creating different plot types
        
        Args:
            data: Data for plotting
            plot_type: Type of plot to create
            **kwargs: Additional plot parameters
            
        Returns:
            Plotly figure object
        """
        plot_methods = {
            'bar': self._create_bar_plot,
            'line': self._create_line_plot,
            'pie': self._create_pie_plot,
            'scatter': self._create_scatter_plot,
            'area': self._create_area_plot
        }
        
        method = plot_methods.get(plot_type.lower())
        if not method:
            raise ValueError(f"Unsupported plot type: {plot_type}")
        
        return method(data, **kwargs)
    
    def _create_bar_plot(self, data: pd.DataFrame, x_column: str, y_column: str, 
                        title: str = "", **kwargs) -> go.Figure:
        """Create a bar plot
        
        Args:
            data: DataFrame with data
            x_column: Column name for x-axis
            y_column: Column name for y-axis
            title: Plot title
            
        Returns:
            Plotly figure
        """
        fig = px.bar(
            data,
            x=x_column,
            y=y_column,
            title=title,
            labels={y_column: y_column, x_column: x_column},
            **kwargs
        )
        
        fig.update_layout(
            title_x=0.5,
            xaxis_title=x_column,
            yaxis_title=y_column,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def _create_line_plot(self, data: pd.DataFrame, x_column: Optional[str] = None, 
                         y_column: Optional[str] = None, title: str = "", 
                         markers: bool = True, **kwargs) -> go.Figure:
        """Create a line plot
        
        Args:
            data: DataFrame with data
            x_column: Column name for x-axis (optional)
            y_column: Column name for y-axis (optional)
            title: Plot title
            markers: Whether to show markers
            
        Returns:
            Plotly figure
        """
        if x_column and y_column:
            fig = px.line(
                data,
                x=x_column,
                y=y_column,
                title=title,
                markers=markers,
                **kwargs
            )
        else:
            fig = px.line(
                data,
                title=title,
                markers=markers,
                **kwargs
            )
        
        fig.update_layout(
            title_x=0.5,
            xaxis_title=x_column or "Index",
            yaxis_title=y_column or "Value"
        )
        
        return fig
    
    def _create_pie_plot(self, data: pd.DataFrame, values_column: str, 
                        labels_column: str, title: str = "", 
                        hole: float = 0.3, **kwargs) -> go.Figure:
        """Create a pie/donut plot
        
        Args:
            data: DataFrame with data
            values_column: Column name for values
            labels_column: Column name for labels
            title: Plot title
            hole: Size of hole for donut chart (0 for pie)
            
        Returns:
            Plotly figure
        """
        # Use absolute values for pie chart
        data_for_pie = data.copy()
        data_for_pie[values_column] = data_for_pie[values_column].abs()
        
        fig = px.pie(
            data_for_pie,
            values=values_column,
            names=labels_column,
            title=title,
            hole=hole,
            **kwargs
        )
        
        fig.update_layout(title_x=0.5)
        
        return fig
    
    def _create_scatter_plot(self, data: pd.DataFrame, x_column: str, y_column: str,
                           title: str = "", size_column: Optional[str] = None,
                           color_column: Optional[str] = None, **kwargs) -> go.Figure:
        """Create a scatter plot
        
        Args:
            data: DataFrame with data
            x_column: Column name for x-axis
            y_column: Column name for y-axis
            title: Plot title
            size_column: Column for bubble size (optional)
            color_column: Column for color mapping (optional)
            
        Returns:
            Plotly figure
        """
        fig = px.scatter(
            data,
            x=x_column,
            y=y_column,
            title=title,
            size=size_column,
            color=color_column,
            **kwargs
        )
        
        fig.update_layout(
            title_x=0.5,
            xaxis_title=x_column,
            yaxis_title=y_column
        )
        
        return fig
    
    def _create_area_plot(self, data: pd.DataFrame, x_column: Optional[str] = None,
                         y_column: Optional[str] = None, title: str = "",
                         **kwargs) -> go.Figure:
        """Create an area plot
        
        Args:
            data: DataFrame with data
            x_column: Column name for x-axis (optional)
            y_column: Column name for y-axis (optional)
            title: Plot title
            
        Returns:
            Plotly figure
        """
        if x_column and y_column:
            fig = px.area(
                data,
                x=x_column,
                y=y_column,
                title=title,
                **kwargs
            )
        else:
            fig = px.area(
                data,
                title=title,
                **kwargs
            )
        
        fig.update_layout(
            title_x=0.5,
            xaxis_title=x_column or "Index",
            yaxis_title=y_column or "Value"
        )
        
        return fig