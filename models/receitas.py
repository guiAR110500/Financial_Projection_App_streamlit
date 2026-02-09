from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class TipoCrescimento(Enum):
    LINEAR = "Linear"
    NAO_LINEAR_SEM_DOWNSIDE = "Não Linear S/ Downside"
    NAO_LINEAR_COM_DOWNSIDE = "Não Linear C/ Downside"
    PRODUTIVIDADE = "Produtividade"

class PeriodicidadeCrescimento(Enum):
    MENSAL = "Mensal"
    TRIMESTRAL = "Trimestral"
    SEMESTRAL = "Semestral"
    ANUAL = "Anual"

@dataclass
class ConversionParams:
    """Parameters for sales conversion funnel"""
    fator_elasticidade: float = 1.0
    taxa_agendamento: float = 30.0  # Percentage
    taxa_comparecimento: float = 70.0  # Percentage
    taxa_conversao: float = 45.0  # Percentage
    ticket_medio: float = 2400.0

    @property
    def taxa_agendamento_decimal(self) -> float:
        """Get appointment rate as decimal"""
        return self.taxa_agendamento / 100

    @property
    def taxa_comparecimento_decimal(self) -> float:
        """Get attendance rate as decimal"""
        return self.taxa_comparecimento / 100

    @property
    def taxa_conversao_decimal(self) -> float:
        """Get conversion rate as decimal"""
        return self.taxa_conversao / 100

    def calculate_conversions(self, leads: float) -> Dict[str, float]:
        """Calculate full conversion funnel"""
        agendamentos = leads * self.taxa_agendamento_decimal
        comparecimentos = agendamentos * self.taxa_comparecimento_decimal
        conversoes = comparecimentos * self.taxa_conversao_decimal
        faturamento = conversoes * self.ticket_medio

        return {
            'leads': leads,
            'agendamentos': agendamentos,
            'comparecimentos': comparecimentos,
            'conversoes': conversoes,
            'faturamento': faturamento
        }

@dataclass
class CanalVenda:
    """Represents a sales channel"""
    descricao: str
    gasto_mensal: float
    cpl_base: float  # Cost per lead base
    crescimento_vendas: TipoCrescimento
    periodicidade: PeriodicidadeCrescimento

    # Growth parameters
    tx_cresc_mensal: float = 5.0
    media_cresc_anual: float = 15.0
    fator_aceleracao_crescimento: float = 1.0

    # Productivity model parameters
    rpe_anual: float = 125000.0
    salario_medio: float = 60000.0
    depreciacao: float = 1.5

    # Conversion parameters
    conversion_params: ConversionParams = field(default_factory=ConversionParams)

    def calculate_adjusted_cpl(self, gasto: float) -> float:
        """Calculate adjusted CPL based on spending"""
        if self.cpl_base <= 0:
            return 0

        # Apply elasticity factor
        elasticity_factor = self.conversion_params.fator_elasticidade
        if elasticity_factor == 1:
            # Linear relationship
            return self.cpl_base * (gasto / self.gasto_mensal) if self.gasto_mensal > 0 else self.cpl_base
        else:
            # Non-linear relationship with elasticity
            ratio = gasto / self.gasto_mensal if self.gasto_mensal > 0 else 1
            adjustment = ratio ** (1 / elasticity_factor)
            return self.cpl_base * adjustment

@dataclass
class FontePrimaria:
    """Represents a primary revenue source"""
    descricao: str
    valor_mensal: float
    periodo_inicio: int  # Month to start
    periodo_fim: int  # Month to end
    taxa_crescimento_mensal: float = 0.0  # Monthly growth rate

    def valor_com_crescimento(self, mes: int) -> float:
        """Calculate value with growth for a specific month"""
        if mes < self.periodo_inicio or mes > self.periodo_fim:
            return 0.0

        meses_desde_inicio = mes - self.periodo_inicio
        fator_crescimento = (1 + self.taxa_crescimento_mensal / 100) ** meses_desde_inicio
        return self.valor_mensal * fator_crescimento

@dataclass
class OutraReceita:
    """Represents other revenue sources"""
    descricao: str
    valor_mensal: float
    recorrente: bool = True
    mes_inicio: int = 0
    mes_fim: int = 59

    def valor_no_mes(self, mes: int) -> float:
        """Get value for a specific month"""
        if mes >= self.mes_inicio and mes <= self.mes_fim:
            return self.valor_mensal
        return 0.0

@dataclass
class ReceitasPremises:
    """Premises for revenue calculation"""
    # Model configuration
    modelo_marketing: bool = True
    repasse_bruto: float = 85.0

    # Sales channels
    canais_venda: List[CanalVenda] = field(default_factory=list)

    # Primary sources
    fontes_primarias: List[FontePrimaria] = field(default_factory=list)

    # Other revenues
    outras_receitas: List[OutraReceita] = field(default_factory=list)

    # Financial model parameters (for non-marketing model)
    receita_inicial: float = 100000.0
    valor_unitario: float = 2400.0
    crescimento_receita: TipoCrescimento = TipoCrescimento.LINEAR
    tx_cresc_mensal: float = 5.0
    media_cresc_anual: float = 15.0
    fator_crescimento: float = 0.5
    fator_estabilizacao: float = 0.8

    # Productivity model defaults
    rpe_anual: float = 125000.0
    salario_medio: float = 60000.0
    depreciacao: float = 1.5

    @property
    def repasse_decimal(self) -> float:
        """Get repasse as decimal"""
        return self.repasse_bruto / 100

    @property
    def total_gasto_canais(self) -> float:
        """Calculate total spending on sales channels"""
        return sum(canal.gasto_mensal for canal in self.canais_venda)

    @property
    def cpl_medio(self) -> float:
        """Calculate average CPL across channels"""
        if not self.canais_venda:
            return 0.0
        return sum(canal.cpl_base for canal in self.canais_venda) / len(self.canais_venda)

    def clear_canais(self) -> None:
        """Clear all sales channels"""
        self.canais_venda = []

    def clear_fontes_primarias(self) -> None:
        """Clear all primary sources"""
        self.fontes_primarias = []

    def clear_outras_receitas(self) -> None:
        """Clear all other revenues"""
        self.outras_receitas = []

    def add_canal_venda(self, canal: CanalVenda) -> None:
        """Add a sales channel"""
        self.canais_venda.append(canal)

    def add_fonte_primaria(self, fonte: FontePrimaria) -> None:
        """Add a primary revenue source"""
        self.fontes_primarias.append(fonte)

    def add_outra_receita(self, receita: OutraReceita) -> None:
        """Add another revenue source"""
        self.outras_receitas.append(receita)

    def remove_canal_venda(self, descricao: str) -> None:
        """Remove a sales channel by description"""
        self.canais_venda = [c for c in self.canais_venda if c.descricao != descricao]

    def remove_fonte_primaria(self, descricao: str) -> None:
        """Remove a primary source by description"""
        self.fontes_primarias = [f for f in self.fontes_primarias if f.descricao != descricao]

    def remove_outra_receita(self, descricao: str) -> None:
        """Remove another revenue by description"""
        self.outras_receitas = [r for r in self.outras_receitas if r.descricao != descricao]
