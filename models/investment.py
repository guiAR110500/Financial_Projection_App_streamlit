from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class InvestmentItem:
    """Represents a single investment item (Value Object pattern)"""
    descricao: str
    quantidade: int
    valor_unitario: float
    
    @property
    def total(self) -> float:
        """Calculate total value for this item"""
        return self.quantidade * self.valor_unitario


@dataclass
class PartnerInvestment:
    """Represents partner capital investment"""
    valor: float
    mes_inflow: int
    periodicidade_ativa: bool
    periodicidade: int = 1
    
    def get_months(self, total_months: int = 60) -> List[int]:
        """Get list of months when this investment occurs"""
        if not self.periodicidade_ativa:
            return [self.mes_inflow] if self.mes_inflow < total_months else []
        
        months = []
        for mes in range(self.mes_inflow, total_months, self.periodicidade):
            months.append(mes)
        return months


@dataclass
class FutureInvestment:
    """Represents future investment/expense"""
    descricao: str
    valor: float
    mes_outflow: int
    periodicidade_ativa: bool
    periodicidade: int = 1
    
    def get_months(self, total_months: int = 60) -> List[int]:
        """Get list of months when this investment occurs"""
        if not self.periodicidade_ativa:
            return [self.mes_outflow] if self.mes_outflow < total_months else []
        
        months = []
        for mes in range(self.mes_outflow, total_months, self.periodicidade):
            months.append(mes)
        return months


@dataclass
class InvestmentPremises:
    """Container for all investment premises (Aggregate Root pattern)"""
    investimentos_iniciais: List[InvestmentItem] = field(default_factory=list)
    investimentos_socios: List[PartnerInvestment] = field(default_factory=list)
    investimentos_futuros: List[FutureInvestment] = field(default_factory=list)
    
    @property
    def total_investimento_inicial(self) -> float:
        """Calculate total initial investment"""
        return sum(item.total for item in self.investimentos_iniciais)
    
    def add_initial_investment(self, item: InvestmentItem) -> None:
        """Add an initial investment item"""
        self.investimentos_iniciais.append(item)
    
    def add_partner_investment(self, investment: PartnerInvestment) -> None:
        """Add a partner investment"""
        self.investimentos_socios.append(investment)
    
    def add_future_investment(self, investment: FutureInvestment) -> None:
        """Add a future investment"""
        self.investimentos_futuros.append(investment)
    
    def clear_initial_investments(self) -> None:
        """Clear all initial investments"""
        self.investimentos_iniciais.clear()
    
    def clear_partner_investments(self) -> None:
        """Clear all partner investments"""
        self.investimentos_socios.clear()
    
    def clear_future_investments(self) -> None:
        """Clear all future investments"""
        self.investimentos_futuros.clear()