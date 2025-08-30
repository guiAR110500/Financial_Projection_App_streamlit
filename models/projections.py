from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import pandas as pd

class MetricType(Enum):
    RECEITA = "Receita"
    DESPESA = "Despesa"
    IMPOSTO = "Imposto"
    RESULTADO = "Resultado"
    PATRIMONIO = "Patrimônio"

class TrendType(Enum):
    CRESCIMENTO = "Crescimento"
    DECLINIO = "Declínio"
    ESTAVEL = "Estável"
    VOLATIL = "Volátil"

@dataclass
class Metric:
    """Represents a financial metric"""
    name: str
    value: float
    period: str  # "Mensal", "Trimestral", "Anual"
    type: MetricType
    percentage_change: Optional[float] = None
    trend: Optional[TrendType] = None
    
    def format_value(self) -> str:
        """Format value as currency"""
        return f"R$ {self.value:,.2f}"
    
    def format_percentage(self) -> str:
        """Format percentage change"""
        if self.percentage_change is None:
            return "N/A"
        return f"{self.percentage_change:+.1f}%"

@dataclass
class FluxoCaixaItem:
    """Represents a cash flow item"""
    categoria: str
    subcategoria: str
    valor: float
    tipo: str  # "Entrada", "Saída"
    mes: int
    observacoes: str = ""
    
    @property
    def valor_com_sinal(self) -> float:
        """Get value with appropriate sign"""
        return self.valor if self.tipo == "Entrada" else -self.valor

@dataclass
class DREItem:
    """Represents a DRE (Income Statement) item"""
    ordem: str
    descricao: str
    valor: float
    nivel: int = 0  # Indentation level for display
    tipo: str = "normal"  # "normal", "subtotal", "total"
    formula: Optional[str] = None  # Formula description
    
    def format_description(self) -> str:
        """Format description with appropriate indentation"""
        indent = "    " * self.nivel
        prefix = ""
        
        if self.tipo == "subtotal":
            prefix = "(=) "
        elif self.tipo == "total":
            prefix = "(=) "
        elif self.descricao.startswith("(-)"):
            pass  # Already has prefix
        elif self.descricao.startswith("(+)"):
            pass  # Already has prefix
        else:
            prefix = ""
            
        return f"{indent}{prefix}{self.descricao}"

@dataclass
class ProjecoesPremises:
    """Premises for financial projections"""
    # Período da projeção
    meses_projecao: int = 60  # 5 years
    data_inicio: str = "2024-01-01"
    
    # Parâmetros de inflação
    ipca_projecao: float = 4.5
    igpm_projecao: float = 5.0
    
    # Parâmetros de crescimento
    meta_receita_anual: float = 1000000.0
    meta_margem_liquida: float = 15.0
    meta_ebitda_margin: float = 25.0
    
    # Cenários de projeção
    cenario_otimista_fator: float = 1.2
    cenario_pessimista_fator: float = 0.8
    cenario_realista_fator: float = 1.0
    
    # Sazonalidade
    considerar_sazonalidade: bool = False
    fatores_sazonais: Dict[int, float] = field(default_factory=lambda: {
        1: 0.9, 2: 0.9, 3: 1.1,    # Q1
        4: 1.0, 5: 1.0, 6: 1.2,    # Q2  
        7: 0.8, 8: 0.8, 9: 1.0,    # Q3
        10: 1.1, 11: 1.3, 12: 1.4  # Q4
    })
    
    # Parâmetros de fluxo de caixa
    prazo_medio_recebimento: int = 30  # days
    prazo_medio_pagamento: int = 30   # days
    reserva_minima_caixa: float = 50000.0
    
    # Investimentos planejados
    investimentos_planejados: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metas operacionais
    meta_leads_mensais: int = 1000
    meta_taxa_conversao: float = 45.0
    meta_ticket_medio: float = 2400.0
    meta_lifetime_value: float = 10000.0
    meta_cac: float = 500.0  # Customer Acquisition Cost
    
    # Métricas de RH
    meta_headcount: int = 10
    meta_receita_por_funcionario: float = 125000.0
    meta_custo_folha_percentual: float = 30.0
    
    @property
    def periodo_anos(self) -> int:
        """Get projection period in years"""
        return self.meses_projecao // 12
    
    @property
    def fator_sazonalidade(self, mes: int) -> float:
        """Get seasonality factor for a given month"""
        if not self.considerar_sazonalidade:
            return 1.0
        
        mes_calendario = (mes % 12) + 1
        return self.fatores_sazonais.get(mes_calendario, 1.0)
    
    def get_growth_target(self, year: int) -> float:
        """Get growth target for a specific year"""
        # This could be enhanced to have different targets per year
        base_growth = (self.meta_receita_anual / 12) / 5  # Simplified calculation
        return base_growth * (1.1 ** year)  # 10% year-over-year growth
    
    def get_scenario_factor(self, scenario: str) -> float:
        """Get factor for different scenarios"""
        factors = {
            "otimista": self.cenario_otimista_fator,
            "pessimista": self.cenario_pessimista_fator,
            "realista": self.cenario_realista_fator
        }
        return factors.get(scenario.lower(), 1.0)

@dataclass
class CashFlowProjection:
    """Represents a cash flow projection"""
    premissas: ProjecoesPremises
    
    # Monthly cash flow data
    receitas_mensais: List[float] = field(default_factory=list)
    despesas_mensais: List[float] = field(default_factory=list)
    impostos_mensais: List[float] = field(default_factory=list)
    investimentos_mensais: List[float] = field(default_factory=list)
    
    # Cash position
    saldo_inicial: float = 100000.0
    saldos_mensais: List[float] = field(default_factory=list)
    
    def calculate_monthly_cash_flow(self) -> List[float]:
        """Calculate net cash flow for each month"""
        cash_flows = []
        
        for i in range(self.premissas.meses_projecao):
            receitas = self.receitas_mensais[i] if i < len(self.receitas_mensais) else 0
            despesas = self.despesas_mensais[i] if i < len(self.despesas_mensais) else 0
            impostos = self.impostos_mensais[i] if i < len(self.impostos_mensais) else 0
            investimentos = self.investimentos_mensais[i] if i < len(self.investimentos_mensais) else 0
            
            net_flow = receitas - despesas - impostos - investimentos
            cash_flows.append(net_flow)
        
        return cash_flows
    
    def calculate_cumulative_balance(self) -> List[float]:
        """Calculate cumulative cash balance"""
        balances = []
        current_balance = self.saldo_inicial
        monthly_flows = self.calculate_monthly_cash_flow()
        
        for flow in monthly_flows:
            current_balance += flow
            balances.append(current_balance)
        
        return balances
    
    def get_months_with_negative_balance(self) -> List[int]:
        """Get months where cash balance goes negative"""
        balances = self.calculate_cumulative_balance()
        return [i for i, balance in enumerate(balances) if balance < 0]
    
    def get_minimum_balance_month(self) -> Tuple[int, float]:
        """Get the month and value of minimum cash balance"""
        balances = self.calculate_cumulative_balance()
        min_balance = min(balances)
        min_month = balances.index(min_balance)
        return min_month, min_balance

@dataclass
class DREProjection:
    """Represents an Income Statement (DRE) projection"""
    premissas: ProjecoesPremises
    
    def generate_dre_structure(self) -> List[DREItem]:
        """Generate the standard DRE structure"""
        return [
            DREItem("1", "Receita Bruta de Vendas", 0, 0, "normal"),
            DREItem("2", "(-) Deduções da Receita Bruta", 0, 1, "normal"),
            DREItem("2.1", "(-) Devoluções de Vendas", 0, 2, "normal"),
            DREItem("2.2", "(-) Abatimentos", 0, 2, "normal"),
            DREItem("2.3", "(-) Impostos e Contribuições s/ Vendas", 0, 2, "normal"),
            DREItem("3", "(=) Receita Líquida de Vendas", 0, 0, "subtotal", "1 - 2"),
            
            DREItem("4", "(-) Custo das Mercadorias/Serviços Vendidos", 0, 0, "normal"),
            DREItem("4.1", "(-) Custo dos Produtos Vendidos", 0, 1, "normal"),
            DREItem("4.2", "(-) Custo dos Serviços Prestados", 0, 1, "normal"),
            DREItem("5", "(=) Resultado Bruto", 0, 0, "subtotal", "3 - 4"),
            
            DREItem("6", "(-) Despesas Operacionais", 0, 0, "normal"),
            DREItem("6.1", "(-) Despesas Administrativas", 0, 1, "normal"),
            DREItem("6.2", "(-) Despesas com Vendas", 0, 1, "normal"),
            DREItem("6.3", "(-) Despesas Financeiras Líquidas", 0, 1, "normal"),
            DREItem("6.4", "(-) Outras Despesas Operacionais", 0, 1, "normal"),
            DREItem("7", "(=) Resultado Operacional (EBITDA/LAJIDA)", 0, 0, "subtotal", "5 - 6"),
            
            DREItem("8", "(-) Depreciações e Amortizações", 0, 0, "normal"),
            DREItem("9", "(=) Resultado Antes dos Tributos s/ Lucro", 0, 0, "subtotal", "7 - 8"),
            
            DREItem("10", "(-) Provisão p/ Imposto de Renda", 0, 0, "normal"),
            DREItem("11", "(-) Provisão p/ Contribuição Social", 0, 0, "normal"),
            DREItem("12", "(=) Resultado do Exercício", 0, 0, "total", "9 - 10 - 11")
        ]
    
    def calculate_margins(self, receita_liquida: float, resultado_bruto: float, 
                         ebitda: float, resultado_liquido: float) -> Dict[str, float]:
        """Calculate key financial margins"""
        if receita_liquida == 0:
            return {
                "margem_bruta": 0,
                "margem_ebitda": 0,
                "margem_liquida": 0
            }
        
        return {
            "margem_bruta": (resultado_bruto / receita_liquida) * 100,
            "margem_ebitda": (ebitda / receita_liquida) * 100,
            "margem_liquida": (resultado_liquido / receita_liquida) * 100
        }

@dataclass
class MonitoringMetrics:
    """Metrics for monitoring and tracking"""
    # Revenue metrics
    mrr: float = 0.0  # Monthly Recurring Revenue
    arr: float = 0.0  # Annual Recurring Revenue
    revenue_growth_mom: float = 0.0  # Month over Month
    revenue_growth_yoy: float = 0.0  # Year over Year
    
    # Customer metrics
    new_customers: int = 0
    churned_customers: int = 0
    total_customers: int = 0
    churn_rate: float = 0.0
    customer_lifetime_value: float = 0.0
    customer_acquisition_cost: float = 0.0
    
    # Operational metrics
    conversion_rate: float = 0.0
    average_ticket: float = 0.0
    total_leads: int = 0
    qualified_leads: int = 0
    
    # Financial metrics
    gross_margin: float = 0.0
    ebitda_margin: float = 0.0
    net_margin: float = 0.0
    burn_rate: float = 0.0
    runway_months: int = 0
    
    # Team metrics
    total_employees: int = 0
    revenue_per_employee: float = 0.0
    payroll_percentage: float = 0.0
    
    def calculate_arr_from_mrr(self) -> float:
        """Calculate ARR from MRR"""
        return self.mrr * 12
    
    def calculate_runway(self, current_cash: float) -> int:
        """Calculate runway in months based on current burn rate"""
        if self.burn_rate <= 0:
            return 999  # Infinite runway if not burning cash
        return int(current_cash / abs(self.burn_rate))
    
    def calculate_ltv_cac_ratio(self) -> float:
        """Calculate LTV/CAC ratio"""
        if self.customer_acquisition_cost == 0:
            return 0
        return self.customer_lifetime_value / self.customer_acquisition_cost
    
    def get_health_score(self) -> Tuple[str, str]:
        """Get overall business health score"""
        score = 0
        factors = []
        
        # Revenue growth (30% weight)
        if self.revenue_growth_mom >= 10:
            score += 30
            factors.append("Crescimento de receita excelente")
        elif self.revenue_growth_mom >= 5:
            score += 20
            factors.append("Crescimento de receita bom")
        elif self.revenue_growth_mom >= 0:
            score += 10
            factors.append("Crescimento de receita positivo")
        else:
            factors.append("Crescimento de receita negativo")
        
        # Margins (25% weight)
        if self.net_margin >= 20:
            score += 25
            factors.append("Margem líquida excelente")
        elif self.net_margin >= 10:
            score += 20
            factors.append("Margem líquida boa")
        elif self.net_margin >= 5:
            score += 15
            factors.append("Margem líquida aceitável")
        elif self.net_margin >= 0:
            score += 5
            factors.append("Margem líquida baixa")
        else:
            factors.append("Margem líquida negativa")
        
        # Customer metrics (20% weight)
        ltv_cac = self.calculate_ltv_cac_ratio()
        if ltv_cac >= 5:
            score += 20
            factors.append("LTV/CAC excelente")
        elif ltv_cac >= 3:
            score += 15
            factors.append("LTV/CAC bom")
        elif ltv_cac >= 2:
            score += 10
            factors.append("LTV/CAC aceitável")
        else:
            factors.append("LTV/CAC baixo")
        
        # Cash runway (15% weight)
        if self.runway_months >= 18:
            score += 15
            factors.append("Runway de caixa excelente")
        elif self.runway_months >= 12:
            score += 12
            factors.append("Runway de caixa bom")
        elif self.runway_months >= 6:
            score += 8
            factors.append("Runway de caixa aceitável")
        else:
            factors.append("Runway de caixa preocupante")
        
        # Efficiency (10% weight)
        if self.revenue_per_employee >= 100000:
            score += 10
            factors.append("Eficiência por funcionário excelente")
        elif self.revenue_per_employee >= 75000:
            score += 8
            factors.append("Eficiência por funcionário boa")
        elif self.revenue_per_employee >= 50000:
            score += 5
            factors.append("Eficiência por funcionário aceitável")
        else:
            factors.append("Eficiência por funcionário baixa")
        
        # Determine overall health
        if score >= 85:
            health = "Excelente"
        elif score >= 70:
            health = "Bom"
        elif score >= 50:
            health = "Aceitável"
        elif score >= 30:
            health = "Preocupante"
        else:
            health = "Crítico"
        
        return health, "; ".join(factors)