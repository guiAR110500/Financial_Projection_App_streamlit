from typing import Any, Dict, List, Optional

import pandas as pd

from core.base_classes import BaseCalculator
from models.tributos import RegimeTributario, TributosPremises


class TributosCalculator(BaseCalculator):
    """Calculator for tax calculations"""

    def __init__(self, premises: TributosPremises):
        self.premises = premises

    def _validate_inputs(self, **kwargs) -> bool:
        """Validate calculation inputs"""
        return self.premises is not None

    def _perform_calculation(self, **kwargs) -> Dict[str, Any]:
        """Calculate taxes for the specified revenue and expense data"""
        try:
            receitas_mensais: List[float] = kwargs.get('receitas_mensais', [])
            despesas_mensais: Optional[List[float]] = kwargs.get('despesas_mensais')
            months = len(receitas_mensais)
            if despesas_mensais is None:
                despesas_mensais = [0.0] * months

            df_tributos = self._calculate_monthly_taxes(receitas_mensais, despesas_mensais)

            return {
                'tributos_mensais': df_tributos,
                'regime_tributario': self.premises.regime_tributario.value,
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def _calculate_monthly_taxes(self, receitas: List[float], despesas: List[float]) -> pd.DataFrame:
        """Calculate monthly taxes based on regime"""
        months = len(receitas)

        if self.premises.regime_tributario == RegimeTributario.SIMPLES_NACIONAL:
            return self._calculate_simples_nacional(receitas, months)
        elif self.premises.regime_tributario == RegimeTributario.LUCRO_PRESUMIDO:
            return self._calculate_lucro_presumido(receitas, months)
        else:  # Lucro Real
            return self._calculate_lucro_real(receitas, despesas, months)

    def _calculate_simples_nacional(self, receitas: List[float], months: int) -> pd.DataFrame:
        """Calculate taxes under Simples Nacional regime"""
        df = pd.DataFrame(0.0, index=["Simples Nacional", "Total Impostos"], columns=range(months))

        # Track 12-month rolling revenue for rate calculation
        receita_12m_rolling = 0.0

        for month in range(months):
            receita_mensal = receitas[month]

            # Update 12-month rolling revenue
            if month < 12:
                receita_12m_rolling += receita_mensal
            else:
                # Remove the revenue from 12 months ago and add current month
                receita_12m_rolling = receita_12m_rolling - receitas[month - 12] + receita_mensal

            # Calculate appropriate tax rate
            aliquota = self.premises.simples_params.calculate_rate(receita_12m_rolling)

            # Calculate Simples Nacional tax
            imposto_simples = receita_mensal * (aliquota / 100)

            df.loc["Simples Nacional", month] = imposto_simples
            df.loc["Total Impostos", month] = imposto_simples

        return df

    def _calculate_lucro_presumido(self, receitas: List[float], months: int) -> pd.DataFrame:
        """Calculate taxes under Lucro Presumido regime"""
        taxes = ["IRPJ", "CSLL", "PIS", "COFINS", "ISS", "Total Impostos"]
        df = pd.DataFrame(0.0, index=taxes, columns=range(months))

        params = self.premises.lucro_presumido_params

        for month in range(months):
            receita_mensal = receitas[month]

            # Split revenue between services and sales
            receita_servicos = self.premises.get_receita_servicos(receita_mensal)
            receita_vendas = self.premises.get_receita_vendas(receita_mensal)

            # Calculate presumed profit
            lucro_presumido = params.calculate_presumed_profit(receita_servicos, receita_vendas)

            # IRPJ calculation
            irpj = lucro_presumido * (params.irpj_rate / 100)
            if lucro_presumido > params.limite_adicional_irpj:
                adicional_irpj = (lucro_presumido - params.limite_adicional_irpj) * (params.adicional_irpj_rate / 100)
                irpj += adicional_irpj

            # CSLL calculation
            csll = lucro_presumido * (params.csll_rate / 100)

            # PIS calculation
            pis = receita_mensal * (params.pis_rate / 100)

            # COFINS calculation
            cofins = receita_mensal * (params.cofins_rate / 100)

            # ISS calculation (only on services)
            iss = receita_servicos * (self.premises.aliquota_iss / 100)

            # Apply retention if configured
            if self.premises.considerar_retencao_fonte:
                retencao = receita_mensal * (self.premises.percentual_retencao_fonte / 100)
                # Reduce PIS and COFINS by retention amount
                pis = max(0, pis - retencao * 0.3)  # 30% of retention applies to PIS
                cofins = max(0, cofins - retencao * 0.7)  # 70% of retention applies to COFINS

            total_impostos = irpj + csll + pis + cofins + iss

            df.loc["IRPJ", month] = irpj
            df.loc["CSLL", month] = csll
            df.loc["PIS", month] = pis
            df.loc["COFINS", month] = cofins
            df.loc["ISS", month] = iss
            df.loc["Total Impostos", month] = total_impostos

        return df

    def _calculate_lucro_real(self, receitas: List[float], despesas: List[float], months: int) -> pd.DataFrame:
        """Calculate taxes under Lucro Real regime"""
        taxes = ["IRPJ", "CSLL", "PIS", "COFINS", "ISS", "Total Impostos"]
        df = pd.DataFrame(0.0, index=taxes, columns=range(months))

        params = self.premises.lucro_real_params

        for month in range(months):
            receita_mensal = receitas[month]
            despesa_mensal = despesas[month] if month < len(despesas) else 0

            # Split revenue between services and sales
            receita_servicos = self.premises.get_receita_servicos(receita_mensal)
            _receita_vendas = self.premises.get_receita_vendas(receita_mensal)

            # Calculate actual profit (revenue - deductible expenses)
            lucro_real = receita_mensal - despesa_mensal

            # IRPJ calculation (only on positive profit)
            irpj = 0
            if lucro_real > 0:
                irpj = lucro_real * (params.irpj_rate / 100)
                if lucro_real > params.limite_adicional_irpj:
                    adicional_irpj = (lucro_real - params.limite_adicional_irpj) * (params.adicional_irpj_rate / 100)
                    irpj += adicional_irpj

            # CSLL calculation (only on positive profit)
            csll = 0
            if lucro_real > 0:
                csll = lucro_real * (params.csll_rate / 100)

            # PIS calculation (non-cumulative, on gross revenue)
            pis = receita_mensal * (params.pis_rate / 100)

            # COFINS calculation (non-cumulative, on gross revenue)
            cofins = receita_mensal * (params.cofins_rate / 100)

            # ISS calculation (only on services)
            iss = receita_servicos * (self.premises.aliquota_iss / 100)

            # Apply retention if configured
            if self.premises.considerar_retencao_fonte:
                retencao = receita_mensal * (self.premises.percentual_retencao_fonte / 100)
                # In Lucro Real, retention can be offset against calculated taxes
                irpj = max(0, irpj - retencao * 0.4)  # 40% of retention applies to IRPJ
                csll = max(0, csll - retencao * 0.3)  # 30% of retention applies to CSLL
                pis = max(0, pis - retencao * 0.15)   # 15% of retention applies to PIS
                cofins = max(0, cofins - retencao * 0.15)  # 15% of retention applies to COFINS

            total_impostos = irpj + csll + pis + cofins + iss

            df.loc["IRPJ", month] = irpj
            df.loc["CSLL", month] = csll
            df.loc["PIS", month] = pis
            df.loc["COFINS", month] = cofins
            df.loc["ISS", month] = iss
            df.loc["Total Impostos", month] = total_impostos

        return df

    def calculate_annual_summary(self, df_monthly: pd.DataFrame) -> pd.DataFrame:
        """Calculate annual tax summary"""
        years = df_monthly.shape[1] // 12
        annual_columns = [f"Ano {i+1}" for i in range(years)]

        df_annual = pd.DataFrame(0.0, index=df_monthly.index, columns=annual_columns)

        for year in range(years):
            start_month = year * 12
            end_month = min((year + 1) * 12, df_monthly.shape[1])

            for tax_type in df_monthly.index:
                annual_sum = df_monthly.loc[tax_type, start_month:end_month-1].sum()
                df_annual.loc[tax_type, f"Ano {year+1}"] = annual_sum

        return df_annual

class TributosService:
    """Service for managing tax calculations"""

    def __init__(self):
        self.premises: Optional[TributosPremises] = None

    def load_premises(self, premises_data: Dict[str, Any]) -> None:
        """Load premises from dictionary data"""
        self.premises = self._dict_to_premises(premises_data)

    def get_premises(self) -> Optional[TributosPremises]:
        """Get current premises"""
        return self.premises

    def calculate_taxes(self, receitas_mensais: List[float],
                       despesas_mensais: Optional[List[float]] = None) -> Dict[str, Any]:
        """Calculate taxes using the calculator"""
        if not self.premises:
            return {'error': 'Premises not loaded', 'success': False}

        calculator = TributosCalculator(self.premises)
        return calculator.calculate(receitas_mensais=receitas_mensais, despesas_mensais=despesas_mensais)

    def get_monthly_summary(self, month: int, receita: float, despesa: float = 0) -> Dict[str, Any]:
        """Get tax summary for a specific month"""
        if not self.premises:
            return {}

        # Calculate taxes for a single month
        result = self.calculate_taxes([receita], [despesa])
        if not result.get('success'):
            return {'error': result.get('error', 'Calculation failed')}

        df_tributos = result['tributos_mensais']

        summary = {
            'regime': self.premises.regime_tributario.value,
            'impostos': {}
        }

        # Extract tax amounts
        for tax_type in df_tributos.index:
            if tax_type != "Total Impostos":
                summary['impostos'][tax_type] = df_tributos.loc[tax_type, 0]

        summary['total_impostos'] = df_tributos.loc["Total Impostos", 0]

        # Calculate effective tax rate
        if receita > 0:
            summary['aliquota_efetiva'] = (summary['total_impostos'] / receita) * 100
        else:
            summary['aliquota_efetiva'] = 0

        return summary

    def get_tax_efficiency_analysis(self, receitas_anuais: List[float],
                                   despesas_anuais: Optional[List[float]] = None) -> Dict[str, Any]:
        """Analyze tax efficiency across different regimes"""
        if not receitas_anuais or self.premises is None:
            return {}

        original_regime = self.premises.regime_tributario
        efficiency_analysis = {}

        # Test each regime
        for regime in RegimeTributario:
            self.premises.regime_tributario = regime

            # Convert annual to monthly (simplified)
            receitas_mensais = []
            despesas_mensais = []

            for i, receita_anual in enumerate(receitas_anuais):
                receita_mensal = receita_anual / 12
                despesa_anual = despesas_anuais[i] if despesas_anuais and i < len(despesas_anuais) else 0
                despesa_mensal = despesa_anual / 12

                receitas_mensais.extend([receita_mensal] * 12)
                despesas_mensais.extend([despesa_mensal] * 12)

            result = self.calculate_taxes(receitas_mensais, despesas_mensais)

            if result.get('success'):
                df_tributos = result['tributos_mensais']
                total_taxes = df_tributos.loc["Total Impostos"].sum()
                total_revenue = sum(receitas_mensais)

                efficiency_analysis[regime.value] = {
                    'total_impostos': total_taxes,
                    'aliquota_media': (total_taxes / total_revenue * 100) if total_revenue > 0 else 0,
                    'economia_vs_simples': 0  # Will be calculated after all regimes
                }

        # Calculate savings compared to Simples Nacional
        simples_total = efficiency_analysis.get(RegimeTributario.SIMPLES_NACIONAL.value, {}).get('total_impostos', 0)

        for regime_name, data in efficiency_analysis.items():
            if simples_total > 0:
                data['economia_vs_simples'] = ((simples_total - data['total_impostos']) / simples_total) * 100

        # Restore original regime
        self.premises.regime_tributario = original_regime

        return efficiency_analysis

    def _dict_to_premises(self, data: Dict[str, Any]) -> TributosPremises:
        """Convert dictionary to TributosPremises object"""
        premises = TributosPremises()

        # Tax regime
        regime_str = data.get('regime_tributario', 'Simples Nacional')
        if regime_str == 'Lucro Presumido':
            premises.regime_tributario = RegimeTributario.LUCRO_PRESUMIDO
        elif regime_str == 'Lucro Real':
            premises.regime_tributario = RegimeTributario.LUCRO_REAL
        else:
            premises.regime_tributario = RegimeTributario.SIMPLES_NACIONAL

        # Revenue breakdown
        premises.receita_servicos_percentual = data.get('receita_servicos_percentual', 100.0)
        premises.receita_vendas_percentual = data.get('receita_vendas_percentual', 0.0)

        # Additional parameters
        premises.considerar_substituicao_tributaria = data.get('considerar_substituicao_tributaria', False)
        premises.considerar_retencao_fonte = data.get('considerar_retencao_fonte', False)
        premises.percentual_retencao_fonte = data.get('percentual_retencao_fonte', 1.5)
        premises.aliquota_iss = data.get('aliquota_iss', 5.0)
        premises.municipio = data.get('municipio', 'São Paulo')
        premises.aliquota_icms = data.get('aliquota_icms', 18.0)
        premises.estado = data.get('estado', 'SP')

        # Regime-specific parameters
        simples_data = data.get('simples_params', {})
        premises.simples_params.aliquota = simples_data.get('aliquota', 6.0)

        lucro_presumido_data = data.get('lucro_presumido_params', {})
        if lucro_presumido_data:
            premises.lucro_presumido_params.percentual_presuncao_servicos = lucro_presumido_data.get('percentual_presuncao_servicos', 32.0)
            premises.lucro_presumido_params.percentual_presuncao_vendas = lucro_presumido_data.get('percentual_presuncao_vendas', 8.0)

        lucro_real_data = data.get('lucro_real_params', {})
        if lucro_real_data:
            premises.lucro_real_params.deducoes_permitidas = lucro_real_data.get('deducoes_permitidas', premises.lucro_real_params.deducoes_permitidas)

        return premises
