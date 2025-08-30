from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class RegimeTributario(Enum):
    SIMPLES_NACIONAL = "Simples Nacional"
    LUCRO_PRESUMIDO = "Lucro Presumido"
    LUCRO_REAL = "Lucro Real"

class SimplesNacionalFaixa(Enum):
    FAIXA_1 = "1ª Faixa"  # Até R$ 180.000
    FAIXA_2 = "2ª Faixa"  # De R$ 180.000,01 a R$ 360.000
    FAIXA_3 = "3ª Faixa"  # De R$ 360.000,01 a R$ 720.000
    FAIXA_4 = "4ª Faixa"  # De R$ 720.000,01 a R$ 1.800.000
    FAIXA_5 = "5ª Faixa"  # De R$ 1.800.000,01 a R$ 3.600.000
    FAIXA_6 = "6ª Faixa"  # De R$ 3.600.000,01 a R$ 4.800.000

@dataclass
class SimplesNacionalParams:
    """Parameters for Simples Nacional tax regime"""
    aliquota: float = 6.0  # Base rate percentage
    faixa_atual: SimplesNacionalFaixa = SimplesNacionalFaixa.FAIXA_1
    receita_acumulada_12m: float = 0.0
    
    # Rate ranges for different revenue brackets
    faixas_aliquotas = {
        SimplesNacionalFaixa.FAIXA_1: {"min": 0, "max": 180000, "rate": 4.0},
        SimplesNacionalFaixa.FAIXA_2: {"min": 180000.01, "max": 360000, "rate": 7.3},
        SimplesNacionalFaixa.FAIXA_3: {"min": 360000.01, "max": 720000, "rate": 9.5},
        SimplesNacionalFaixa.FAIXA_4: {"min": 720000.01, "max": 1800000, "rate": 10.7},
        SimplesNacionalFaixa.FAIXA_5: {"min": 1800000.01, "max": 3600000, "rate": 14.3},
        SimplesNacionalFaixa.FAIXA_6: {"min": 3600000.01, "max": 4800000, "rate": 19.0}
    }
    
    def calculate_rate(self, receita_12m: float) -> float:
        """Calculate the appropriate tax rate based on 12-month revenue"""
        for faixa, params in self.faixas_aliquotas.items():
            if params["min"] <= receita_12m <= params["max"]:
                return params["rate"]
        # If above maximum, use the highest rate
        return 19.0

@dataclass
class LucroPresumidoParams:
    """Parameters for Lucro Presumido tax regime"""
    percentual_presuncao_servicos: float = 32.0  # Presumption percentage for services
    percentual_presuncao_vendas: float = 8.0     # Presumption percentage for sales
    
    # Tax rates
    irpj_rate: float = 15.0  # IRPJ rate
    adicional_irpj_rate: float = 10.0  # Additional IRPJ rate (over R$ 20k/month)
    csll_rate: float = 9.0   # CSLL rate
    pis_rate: float = 0.65   # PIS rate
    cofins_rate: float = 3.0 # COFINS rate
    iss_rate: float = 5.0    # ISS rate (varies by municipality)
    
    # Additional parameters
    limite_adicional_irpj: float = 20000.0  # Monthly limit for additional IRPJ
    
    def calculate_presumed_profit(self, receita_bruta_servicos: float, receita_bruta_vendas: float) -> float:
        """Calculate presumed profit"""
        lucro_presumido_servicos = receita_bruta_servicos * (self.percentual_presuncao_servicos / 100)
        lucro_presumido_vendas = receita_bruta_vendas * (self.percentual_presuncao_vendas / 100)
        return lucro_presumido_servicos + lucro_presumido_vendas

@dataclass
class LucroRealParams:
    """Parameters for Lucro Real tax regime"""
    # Tax rates
    irpj_rate: float = 15.0  # IRPJ rate
    adicional_irpj_rate: float = 10.0  # Additional IRPJ rate (over R$ 20k/month)
    csll_rate: float = 9.0   # CSLL rate
    pis_rate: float = 1.65   # PIS rate (non-cumulative)
    cofins_rate: float = 7.6 # COFINS rate (non-cumulative)
    iss_rate: float = 5.0    # ISS rate
    
    # Additional parameters
    limite_adicional_irpj: float = 20000.0  # Monthly limit for additional IRPJ
    
    # Deductions and adjustments
    deducoes_permitidas: List[str] = field(default_factory=lambda: [
        "Despesas operacionais",
        "Depreciação",
        "Amortização",
        "Provisões"
    ])

@dataclass
class ImpostoCalculado:
    """Represents a calculated tax"""
    nome: str
    base_calculo: float
    aliquota: float
    valor: float
    observacoes: str = ""
    
    @property
    def aliquota_percentual(self) -> str:
        """Get tax rate as formatted percentage"""
        return f"{self.aliquota:.2f}%"

@dataclass
class TributosPremises:
    """Premises for tax calculation"""
    # Tax regime
    regime_tributario: RegimeTributario = RegimeTributario.SIMPLES_NACIONAL
    
    # Regime-specific parameters
    simples_params: SimplesNacionalParams = field(default_factory=SimplesNacionalParams)
    lucro_presumido_params: LucroPresumidoParams = field(default_factory=LucroPresumidoParams)
    lucro_real_params: LucroRealParams = field(default_factory=LucroRealParams)
    
    # Revenue breakdown for tax calculation
    receita_servicos_percentual: float = 100.0  # Percentage of revenue from services
    receita_vendas_percentual: float = 0.0      # Percentage of revenue from sales
    
    # Additional parameters
    considerar_substituicao_tributaria: bool = False
    considerar_retencao_fonte: bool = False
    percentual_retencao_fonte: float = 1.5
    
    # Municipal tax parameters (varies by location)
    aliquota_iss: float = 5.0  # ISS rate
    municipio: str = "São Paulo"
    
    # State tax parameters (if applicable)
    aliquota_icms: float = 18.0  # ICMS rate (for sales)
    estado: str = "SP"
    
    def validate_percentual_receitas(self) -> bool:
        """Validate that revenue percentages sum to 100%"""
        total = self.receita_servicos_percentual + self.receita_vendas_percentual
        return abs(total - 100.0) < 0.01
    
    def get_receita_servicos(self, receita_total: float) -> float:
        """Calculate services revenue portion"""
        return receita_total * (self.receita_servicos_percentual / 100)
    
    def get_receita_vendas(self, receita_total: float) -> float:
        """Calculate sales revenue portion"""
        return receita_total * (self.receita_vendas_percentual / 100)
    
    def calculate_taxes(self, receita_bruta: float, despesas_dedutiveis: float = 0.0) -> List[ImpostoCalculado]:
        """Calculate taxes based on the selected regime"""
        impostos = []
        
        receita_servicos = self.get_receita_servicos(receita_bruta)
        receita_vendas = self.get_receita_vendas(receita_bruta)
        
        if self.regime_tributario == RegimeTributario.SIMPLES_NACIONAL:
            # Calculate cumulative 12-month revenue (simplified for this example)
            receita_12m = receita_bruta * 12  # This should be properly accumulated
            aliquota = self.simples_params.calculate_rate(receita_12m)
            
            valor_simples = receita_bruta * (aliquota / 100)
            impostos.append(ImpostoCalculado(
                nome="Simples Nacional",
                base_calculo=receita_bruta,
                aliquota=aliquota,
                valor=valor_simples,
                observacoes="Unificado: IRPJ, CSLL, PIS, COFINS, ISS"
            ))
            
        elif self.regime_tributario == RegimeTributario.LUCRO_PRESUMIDO:
            params = self.lucro_presumido_params
            
            # Calculate presumed profit
            lucro_presumido = params.calculate_presumed_profit(receita_servicos, receita_vendas)
            
            # IRPJ
            valor_irpj = lucro_presumido * (params.irpj_rate / 100)
            if lucro_presumido > params.limite_adicional_irpj:
                valor_irpj += (lucro_presumido - params.limite_adicional_irpj) * (params.adicional_irpj_rate / 100)
            
            impostos.append(ImpostoCalculado(
                nome="IRPJ",
                base_calculo=lucro_presumido,
                aliquota=params.irpj_rate,
                valor=valor_irpj
            ))
            
            # CSLL
            valor_csll = lucro_presumido * (params.csll_rate / 100)
            impostos.append(ImpostoCalculado(
                nome="CSLL",
                base_calculo=lucro_presumido,
                aliquota=params.csll_rate,
                valor=valor_csll
            ))
            
            # PIS
            valor_pis = receita_bruta * (params.pis_rate / 100)
            impostos.append(ImpostoCalculado(
                nome="PIS",
                base_calculo=receita_bruta,
                aliquota=params.pis_rate,
                valor=valor_pis
            ))
            
            # COFINS
            valor_cofins = receita_bruta * (params.cofins_rate / 100)
            impostos.append(ImpostoCalculado(
                nome="COFINS",
                base_calculo=receita_bruta,
                aliquota=params.cofins_rate,
                valor=valor_cofins
            ))
            
            # ISS (only on services)
            if receita_servicos > 0:
                valor_iss = receita_servicos * (self.aliquota_iss / 100)
                impostos.append(ImpostoCalculado(
                    nome="ISS",
                    base_calculo=receita_servicos,
                    aliquota=self.aliquota_iss,
                    valor=valor_iss
                ))
        
        elif self.regime_tributario == RegimeTributario.LUCRO_REAL:
            params = self.lucro_real_params
            
            # For Lucro Real, we need the actual profit (revenue - deductible expenses)
            lucro_real = receita_bruta - despesas_dedutiveis
            
            # IRPJ
            valor_irpj = max(0, lucro_real * (params.irpj_rate / 100))
            if lucro_real > params.limite_adicional_irpj:
                valor_irpj += (lucro_real - params.limite_adicional_irpj) * (params.adicional_irpj_rate / 100)
            
            impostos.append(ImpostoCalculado(
                nome="IRPJ",
                base_calculo=lucro_real,
                aliquota=params.irpj_rate,
                valor=valor_irpj
            ))
            
            # CSLL
            valor_csll = max(0, lucro_real * (params.csll_rate / 100))
            impostos.append(ImpostoCalculado(
                nome="CSLL",
                base_calculo=lucro_real,
                aliquota=params.csll_rate,
                valor=valor_csll
            ))
            
            # PIS (non-cumulative)
            valor_pis = receita_bruta * (params.pis_rate / 100)
            impostos.append(ImpostoCalculado(
                nome="PIS",
                base_calculo=receita_bruta,
                aliquota=params.pis_rate,
                valor=valor_pis,
                observacoes="Regime não-cumulativo"
            ))
            
            # COFINS (non-cumulative)
            valor_cofins = receita_bruta * (params.cofins_rate / 100)
            impostos.append(ImpostoCalculado(
                nome="COFINS",
                base_calculo=receita_bruta,
                aliquota=params.cofins_rate,
                valor=valor_cofins,
                observacoes="Regime não-cumulativo"
            ))
            
            # ISS (only on services)
            if receita_servicos > 0:
                valor_iss = receita_servicos * (self.aliquota_iss / 100)
                impostos.append(ImpostoCalculado(
                    nome="ISS",
                    base_calculo=receita_servicos,
                    aliquota=self.aliquota_iss,
                    valor=valor_iss
                ))
        
        return impostos
    
    @property
    def total_impostos(self) -> float:
        """Calculate total tax burden (simplified calculation)"""
        if self.regime_tributario == RegimeTributario.SIMPLES_NACIONAL:
            return self.simples_params.aliquota
        elif self.regime_tributario == RegimeTributario.LUCRO_PRESUMIDO:
            params = self.lucro_presumido_params
            return params.irpj_rate + params.csll_rate + params.pis_rate + params.cofins_rate + self.aliquota_iss
        else:  # Lucro Real
            params = self.lucro_real_params
            return params.irpj_rate + params.csll_rate + params.pis_rate + params.cofins_rate + self.aliquota_iss