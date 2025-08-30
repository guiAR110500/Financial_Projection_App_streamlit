import pandas as pd
from typing import Optional, Dict
from models.investment import InvestmentPremises, InvestmentItem, PartnerInvestment, FutureInvestment
from core.base_classes import BaseCalculator

class InvestmentCalculator(BaseCalculator):
    """Service for investment calculations (Single Responsibility Principle)"""
    
    def __init__(self, premises: InvestmentPremises):
        super().__init__()
        self.premises = premises
    
    def _validate_inputs(self, **kwargs) -> bool:
        """Validate that premises are available"""
        return self.premises is not None
    
    def _perform_calculation(self, **kwargs) -> Dict[str, pd.DataFrame]:
        """Calculate investment flows"""
        total_months = kwargs.get('total_months', 60)
        df = self._generate_investment_dataframe(total_months)
        
        return {
            'investment_flow': df,
            'total_initial': self.premises.total_investimento_inicial
        }
    
    def _generate_investment_dataframe(self, total_months: int = 60) -> pd.DataFrame:
        """Generate investment dataframe for specified months"""
        meses = range(total_months)
        
        # Create DataFrame with investment categories
        df = pd.DataFrame(0.0, 
                         index=pd.Index(["Investimento Inicial", "Investimentos dos Sócios", 
                                       "Investimentos Futuros", "Total"]), 
                         columns=meses)
        
        # Initial Investment (month 0 only)
        df.loc["Investimento Inicial", 0] = -self.premises.total_investimento_inicial
        
        # Partner Investments
        for inv in self.premises.investimentos_socios:
            for month in inv.get_months(total_months):
                df.loc["Investimentos dos Sócios", month] += inv.valor
        
        # Future Investments
        for inv in self.premises.investimentos_futuros:
            for month in inv.get_months(total_months):
                df.loc["Investimentos Futuros", month] -= inv.valor
        
        # Calculate totals
        for mes in meses:
            df.loc["Total", mes] = (
                df.loc["Investimento Inicial", mes] +
                df.loc["Investimentos dos Sócios", mes] +
                df.loc["Investimentos Futuros", mes]
            )
        
        return df
    
    def group_by_period(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """Group dataframe by period (quarterly, semi-annual, or annual)"""
        if period == "Mensal":
            return df
        
        # Define group size
        group_sizes = {
            "Trimestral": 3,
            "Semestral": 6,
            "Anual": 12
        }
        
        group_size = group_sizes.get(period, 1)
        
        # Create new DataFrame
        periods = [f"{period} {i//group_size + 1}" 
                  for i in range(0, df.shape[1], group_size)]
        df_grouped = pd.DataFrame(index=df.index, columns=pd.Index(periods))
        
        # Group the data
        for i, period_name in enumerate(periods):
            start = i * group_size
            end = min((i + 1) * group_size, df.shape[1])
            
            for idx in df.index:
                df_grouped.loc[idx, period_name] = df.loc[idx, start:end-1].sum()
        
        return df_grouped


class InvestmentService:
    """Service facade for investment operations (Facade pattern)"""
    
    def __init__(self):
        self._premises: Optional[InvestmentPremises] = None
        self._calculator: Optional[InvestmentCalculator] = None
    
    def load_premises(self, data: Dict) -> None:
        """Load investment premises from dictionary"""
        self._premises = InvestmentPremises()
        
        # Load initial investments
        for item_data in data.get('investimentos_iniciais', []):
            item = InvestmentItem(**item_data)
            self._premises.add_initial_investment(item)
        
        # Load partner investments
        for inv_data in data.get('investimentos_socios', []):
            inv = PartnerInvestment(**inv_data)
            self._premises.add_partner_investment(inv)
        
        # Load future investments
        for fut_data in data.get('investimentos_futuros', []):
            fut = FutureInvestment(**fut_data)
            self._premises.add_future_investment(fut)
        
        self._calculator = InvestmentCalculator(self._premises)
    
    def get_premises(self) -> Optional[InvestmentPremises]:
        """Get current premises"""
        return self._premises
    
    def calculate_flows(self, total_months: int = 60) -> Optional[Dict]:
        """Calculate investment flows"""
        if not self._calculator:
            return None
        
        return self._calculator.calculate(total_months=total_months)
    
    def get_grouped_flow(self, period: str) -> Optional[pd.DataFrame]:
        """Get investment flow grouped by period"""
        if not self._calculator:
            return None
        
        result = self.calculate_flows()
        if result:
            df = result['investment_flow']
            return self._calculator.group_by_period(df, period)
        
        return None