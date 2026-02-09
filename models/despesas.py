from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ModoCalculo(Enum):
    PERCENTUAL = "Percentual"
    NOMINAL = "Nominal"

class ModoEnergia(Enum):
    CONSTANTE = "Constante"
    ESTRESSADO = "Estressado"
    EXTREMAMENTE_CONSERVADOR = "Extremamente Conservador"

class TipoCrescimento(Enum):
    LINEAR = "Linear"
    NAO_LINEAR_SEM_DOWNSIDE = "Não Linear S/ Downside"
    NAO_LINEAR_COM_DOWNSIDE = "Não Linear C/ Downside"
    PRODUTIVIDADE = "Produtividade"

class IndexType(Enum):
    IPCA = "IPCA Médio Anual (%)"
    IGPM = "IGP-M Médio Anual (%)"
    SEM_REAJUSTE = "Sem reajuste"

@dataclass
class DespesaItem:
    """Represents an administrative expense item"""
    nome: str
    valor_base: float
    percentual: float = 0.0  # Used in percentage mode
    reajuste_aplicado: bool = False
    index_type: Optional[IndexType] = None

    @property
    def valor_percentual(self) -> float:
        """Calculate value based on percentage"""
        return self.valor_base * (self.percentual / 100) if self.percentual > 0 else self.valor_base

@dataclass
class EquipeMembro:
    """Represents a team member"""
    nome: str
    salario: float
    quantidade: int
    percentual: float = 0.0  # For percentage mode
    sujeito_comissoes: bool = False
    sujeito_aumento_receita: bool = False

    # SDR specific parameters
    taxa_agendamento: float = 30.0
    taxa_comparecimento: float = 70.0
    estimativa_leads: int = 200
    capacidade_leads: int = 750

    # Closer specific parameters
    valor_unitario: float = 2400.0
    taxa_conversao: float = 45.0
    periodicidade: str = "Mensal"
    fator_aceleracao_crescimento: float = 1.0
    crescimento_vendas: str = "Produtividade"
    produtos_por_lead: int = 10
    capacidade_atendimentos: int = 90
    taxa_cancelamento: float = 5.0

    # Marketing parameters
    gasto_mensal: float = 0.0
    cpl_base: float = 0.0
    fator_elasticidade: float = 1.0
    ticket_medio: float = 2400.0

    # Productivity model parameters
    rpe_anual: float = 125000.0
    salario_medio: float = 60000.0
    depreciacao: float = 1.5

    # Growth parameters
    tx_cresc_mensal: float = 0.0
    media_cresc_anual: float = 0.0

    @property
    def custo_total(self) -> float:
        """Calculate total cost for this team member"""
        return self.salario * self.quantidade

    @property
    def tem_beneficios(self) -> bool:
        """Check if member has benefits"""
        # This would be checked against roles_com_beneficios in the premises
        return True  # Default to true for now

@dataclass
class PrestadorServico:
    """Represents a third-party service provider"""
    nome: str
    valor: float
    quantidade: int
    percentual: float = 0.0  # For percentage mode

    @property
    def custo_total(self) -> float:
        """Calculate total cost for this service provider"""
        return self.valor * self.quantidade

@dataclass
class ReajusteConfig:
    """Configuration for periodic adjustments"""
    expenses: List[str]
    index: IndexType

@dataclass
class Equipamento:
    """Represents technology equipment"""
    nome: str
    valor: float
    quantidade: int
    mes_aquisicao: int
    metodo: str  # "Método da Linha Reta" or "Método da Soma dos Dígitos"
    metodo_params: Dict[str, Any]

    @property
    def valor_total(self) -> float:
        """Calculate total acquisition value"""
        return self.valor * self.quantidade

@dataclass
class DespesasPremises:
    """Premises for administrative expenses"""
    # General parameters
    ipca_medio_anual: float = 4.5
    igpm_medio_anual: float = 5.0
    modo_calculo: ModoCalculo = ModoCalculo.PERCENTUAL
    budget_mensal: float = 30000.0
    mes_inicio_despesas: int = 0

    # Energy mode
    modo_energia: ModoEnergia = ModoEnergia.CONSTANTE
    consumo_mensal_kwh: float = 2000.0

    # Administrative expenses (nominal values)
    aluguel: float = 8000.0
    condominio: float = 1500.0
    iptu: float = 1000.0
    internet: float = 350.0
    material_escritorio: float = 800.0
    treinamentos: float = 2000.0
    manutencao_conservacao: float = 1200.0
    seguros_funcionarios: float = 2000.0
    licencas_telefonia: float = 500.0
    licencas_crm: float = 1000.0
    telefonica: float = 500.0
    marketing_publicidade: float = 5000.0

    # Percentages for percentage mode
    perc_agua_luz: float = 5.0
    perc_aluguel_condominio_iptu: float = 35.0
    perc_internet: float = 1.2
    perc_material_escritorio: float = 2.7
    perc_treinamentos: float = 6.7
    perc_manutencao_conservacao: float = 4.0
    perc_seguros_funcionarios: float = 6.7
    perc_licencas_telefonia: float = 1.7
    perc_licencas_crm: float = 3.3
    perc_telefonica: float = 1.7
    perc_marketing_publicidade: float = 16.7

    # Team parameters
    equipe_modo_calculo: str = "Nominal"
    budget_equipe_propria: float = 50000.0
    budget_terceiros: float = 10000.0
    encargos_sociais_perc: float = 68.0
    vale_alimentacao: float = 30.0
    vale_transporte: float = 12.0
    roles_com_beneficios: List[str] = field(default_factory=list)

    # Team members
    equipe_propria: List[EquipeMembro] = field(default_factory=list)
    terceiros: List[PrestadorServico] = field(default_factory=list)

    # Bonus parameters
    benchmark_anual_bonus: float = 10.0
    lucro_liquido_inicial: float = 100000.0
    crescimento_lucro: float = 15.0

    # Technology costs
    desenvolvimento_ferramenta: float = 0.0
    manutencao_ferramenta: float = 0.0
    inovacao: float = 0.0
    licencas_software: float = 2513.0
    equipamentos: List[Equipamento] = field(default_factory=list)

    # Reajustes
    reajustes: Dict[str, ReajusteConfig] = field(default_factory=dict)

    @property
    def total_despesas_fixas(self) -> float:
        """Calculate total fixed expenses"""
        if self.modo_calculo == ModoCalculo.NOMINAL:
            return (self.aluguel + self.condominio + self.iptu + self.internet +
                   self.material_escritorio + self.treinamentos + self.manutencao_conservacao +
                   self.seguros_funcionarios + self.licencas_telefonia + self.licencas_crm +
                   self.telefonica + self.marketing_publicidade)
        else:
            return self.budget_mensal

    @property
    def folha_pagamento_base(self) -> float:
        """Calculate base payroll"""
        return sum(membro.custo_total for membro in self.equipe_propria)

    @property
    def custo_terceiros_total(self) -> float:
        """Calculate total third-party costs"""
        return sum(prestador.custo_total for prestador in self.terceiros)

    def clear_equipe(self) -> None:
        """Clear all team members"""
        self.equipe_propria = []

    def clear_terceiros(self) -> None:
        """Clear all service providers"""
        self.terceiros = []

    def add_team_member(self, membro: EquipeMembro) -> None:
        """Add a team member"""
        self.equipe_propria.append(membro)

    def add_service_provider(self, prestador: PrestadorServico) -> None:
        """Add a service provider"""
        self.terceiros.append(prestador)

    def remove_team_member(self, nome: str) -> None:
        """Remove a team member by name"""
        self.equipe_propria = [m for m in self.equipe_propria if m.nome != nome]

    def remove_service_provider(self, nome: str) -> None:
        """Remove a service provider by name"""
        self.terceiros = [p for p in self.terceiros if p.nome != nome]
