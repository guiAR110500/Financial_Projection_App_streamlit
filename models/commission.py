from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class GrowthType(Enum):
    """Enum for growth types"""
    LINEAR = "Linear"
    EXPONENTIAL = "Exponencial"
    FIXED = "Fixa"


@dataclass
class CommissionLevel:
    """Represents commission parameters for a specific level"""
    inicial_comissao: float
    inicial_meta: float
    final_comissao: float
    final_meta: float
    quantidade: int
    
    def calculate_commission(self, performance_pct: float, segments: int) -> float:
        """Calculate commission based on performance percentage"""
        if performance_pct < self.inicial_meta:
            return 0.0
        elif performance_pct >= self.final_meta:
            return self.final_comissao
        else:
            # Linear interpolation between segments
            segment_size = (self.final_meta - self.inicial_meta) / segments
            commission_increment = (self.final_comissao - self.inicial_comissao) / segments
            
            for i in range(segments):
                segment_min = self.inicial_meta + i * segment_size
                segment_max = self.inicial_meta + (i + 1) * segment_size
                
                if segment_min <= performance_pct < segment_max:
                    return self.inicial_comissao + i * commission_increment
            
            return self.final_comissao


@dataclass
class GrowthParameters:
    """Parameters for commission growth"""
    tipo: GrowthType
    taxa: Optional[float] = None
    taxa_inicial: Optional[float] = None
    taxa_final: Optional[float] = None
    taxas: Optional[Dict[int, float]] = None
    
    def calculate_growth(self, month: int, total_months: int = 60) -> float:
        """Calculate growth multiplier for a given month"""
        if self.tipo == GrowthType.LINEAR:
            return 1.0 + (month * (self.taxa or 0) / 100)
        elif self.tipo == GrowthType.EXPONENTIAL:
            taxa_inicial = (self.taxa_inicial or 0) / 100
            taxa_final = (self.taxa_final or 0) / 100
            taxa_mes = taxa_inicial + (taxa_final - taxa_inicial) * (month / total_months)
            return (1 + taxa_mes) ** month
        elif self.tipo == GrowthType.FIXED and self.taxas:
            segment = min(len(self.taxas), max(1, int(month * len(self.taxas) / total_months) + 1))
            return 1.0 + (self.taxas.get(segment, 0) / 100 * month)
        return 1.0


@dataclass
class RandomParameters:
    """Parameters for random quantity changes"""
    ativo: bool
    intervalo_meses: int = 3
    
    def should_change(self, month: int) -> bool:
        """Check if quantity should change this month"""
        return self.ativo and month > 0 and month % self.intervalo_meses == 0


@dataclass
class CommissionRole:
    """Represents a role with commission structure"""
    nome: str
    niveis: List[str]
    custo_unitario: float
    meta_em_numero: bool
    nivel_inputs: Dict[str, CommissionLevel]
    segmentos: int
    parametros_crescimento: GrowthParameters
    parametros_aleatorio: RandomParameters
    
    def get_level(self, nivel: str) -> Optional[CommissionLevel]:
        """Get commission level parameters"""
        return self.nivel_inputs.get(nivel)
    
    def calculate_meta(self, nivel: str, month: int) -> float:
        """Calculate meta for a specific level and month"""
        level = self.get_level(nivel)
        if not level:
            return 0.0
        
        if self.meta_em_numero:
            meta_base = level.quantidade
        else:
            meta_base = level.quantidade * self.custo_unitario * 10
        
        growth = self.parametros_crescimento.calculate_growth(month)
        return meta_base * growth


@dataclass
class CommissionPremises:
    """Container for all commission premises (Aggregate Root pattern)"""
    cargos_comissao: List[CommissionRole] = field(default_factory=list)
    
    def add_role(self, role: CommissionRole) -> None:
        """Add a commission role"""
        self.cargos_comissao.append(role)
    
    def remove_role(self, index: int) -> None:
        """Remove a commission role by index"""
        if 0 <= index < len(self.cargos_comissao):
            self.cargos_comissao.pop(index)
    
    def get_role(self, nome: str) -> Optional[CommissionRole]:
        """Get role by name"""
        return next((role for role in self.cargos_comissao if role.nome == nome), None)
    
    def clear_roles(self) -> None:
        """Clear all commission roles"""
        self.cargos_comissao.clear()