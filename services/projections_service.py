from typing import Any, Dict, Optional

import pandas as pd

from core.base_classes import BaseCalculator
from models.projections import (
    CashFlowProjection,
    DREProjection,
    MonitoringMetrics,
    ProjecoesPremises,
)


class ProjectionsCalculator(BaseCalculator):
    """Calculator for financial projections"""

    def __init__(self, premises: ProjecoesPremises):
        self.premises = premises
        self.cash_flow = CashFlowProjection(premises)
        self.dre = DREProjection(premises)

    def _validate_inputs(self, **kwargs) -> bool:
        """Validate calculation inputs"""
        return self.premises is not None

    def _perform_calculation(self, receitas_data: Optional[pd.DataFrame] = None,
                           despesas_data: Optional[pd.DataFrame] = None,
                           impostos_data: Optional[pd.DataFrame] = None, **kwargs) -> Dict[str, Any]:
        """Calculate financial projections"""
        try:
            # Generate cash flow projection
            df_cash_flow = self._generate_cash_flow_projection(receitas_data, despesas_data, impostos_data)

            # Generate DRE projection
            df_dre = self._generate_dre_projection(receitas_data, despesas_data, impostos_data)

            # Calculate monitoring metrics
            metrics = self._calculate_monitoring_metrics(df_cash_flow, df_dre)

            return {
                'cash_flow': df_cash_flow,
                'dre': df_dre,
                'monitoring_metrics': metrics,
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def _generate_cash_flow_projection(self, receitas_data: Optional[pd.DataFrame],
                                     despesas_data: Optional[pd.DataFrame],
                                     impostos_data: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Generate cash flow projection"""
        months = self.premises.meses_projecao

        # Initialize cash flow structure
        cash_flow_items = [
            "Entradas de Caixa",
            "Receitas de Vendas",
            "Outras Receitas",
            "Total Entradas",
            "Saídas de Caixa",
            "Despesas Operacionais",
            "Impostos e Tributos",
            "Investimentos",
            "Total Saídas",
            "Fluxo Líquido",
            "Saldo Acumulado"
        ]

        df = pd.DataFrame(0.0, index=cash_flow_items, columns=range(months))

        # Initialize cash balance
        saldo_inicial = 100000.0  # Default initial cash
        saldo_acumulado = saldo_inicial

        for month in range(months):
            # Calculate entries
            receitas_vendas = self._get_monthly_value(receitas_data, month, "Total") if receitas_data is not None else 0
            outras_receitas = 0  # Would be calculated from other revenue sources
            total_entradas = receitas_vendas + outras_receitas

            # Calculate exits
            despesas_operacionais = self._get_monthly_value(despesas_data, month, "Total") if despesas_data is not None else 0
            impostos = self._get_monthly_value(impostos_data, month, "Total Impostos") if impostos_data is not None else 0
            investimentos = self._calculate_monthly_investments(month)
            total_saidas = despesas_operacionais + impostos + investimentos

            # Calculate net flow
            fluxo_liquido = total_entradas - total_saidas
            saldo_acumulado += fluxo_liquido

            # Apply seasonality if configured
            if self.premises.considerar_sazonalidade:
                seasonal_factor = self.premises.fator_sazonalidade(month)
                receitas_vendas *= seasonal_factor
                total_entradas = receitas_vendas + outras_receitas
                fluxo_liquido = total_entradas - total_saidas
                saldo_acumulado = saldo_inicial + sum([df.loc["Fluxo Líquido", m] for m in range(month + 1)])

            # Store values
            df.loc["Receitas de Vendas", month] = receitas_vendas
            df.loc["Outras Receitas", month] = outras_receitas
            df.loc["Total Entradas", month] = total_entradas
            df.loc["Despesas Operacionais", month] = despesas_operacionais
            df.loc["Impostos e Tributos", month] = impostos
            df.loc["Investimentos", month] = investimentos
            df.loc["Total Saídas", month] = total_saidas
            df.loc["Fluxo Líquido", month] = fluxo_liquido
            df.loc["Saldo Acumulado", month] = saldo_acumulado

        return df

    def _generate_dre_projection(self, receitas_data: Optional[pd.DataFrame],
                               despesas_data: Optional[pd.DataFrame],
                               impostos_data: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Generate DRE (Income Statement) projection"""
        months = self.premises.meses_projecao

        # Get DRE structure
        dre_items = self.dre.generate_dre_structure()
        index_tuples = [(item.ordem, item.descricao) for item in dre_items]

        # Create multi-index DataFrame
        index = pd.MultiIndex.from_tuples(index_tuples, names=['Ordem', 'Descrição'])
        df = pd.DataFrame(0.0, index=index, columns=range(months))

        for month in range(months):
            # Revenue section
            receita_bruta = self._get_monthly_value(receitas_data, month, "Receita Bruta") if receitas_data is not None else 0
            if receita_bruta == 0 and receitas_data is not None:
                receita_bruta = self._get_monthly_value(receitas_data, month, "Total")

            impostos_sobre_vendas = self._get_monthly_value(impostos_data, month, "Total Impostos") if impostos_data is not None else 0
            receita_liquida = receita_bruta - impostos_sobre_vendas

            # Cost section (simplified - would need actual cost data)
            custo_servicos = receita_liquida * 0.3  # Assuming 30% cost ratio
            resultado_bruto = receita_liquida - custo_servicos

            # Operational expenses
            despesas_administrativas = self._get_monthly_value(despesas_data, month, "despesas_administrativas") if despesas_data is not None else 0
            despesas_vendas = self._get_monthly_value(despesas_data, month, "custos_equipe") if despesas_data is not None else 0
            despesas_financeiras = 0  # Would be calculated from financial data
            outras_despesas = self._get_monthly_value(despesas_data, month, "custos_tecnologia") if despesas_data is not None else 0

            total_despesas_operacionais = despesas_administrativas + despesas_vendas + despesas_financeiras + outras_despesas
            ebitda = resultado_bruto - total_despesas_operacionais

            # Depreciation and amortization
            depreciacao = self._calculate_monthly_depreciation(month)
            resultado_antes_tributos = ebitda - depreciacao

            # Taxes on profit
            ir_provisionado = max(0, resultado_antes_tributos * 0.15) if resultado_antes_tributos > 0 else 0
            cs_provisionado = max(0, resultado_antes_tributos * 0.09) if resultado_antes_tributos > 0 else 0
            resultado_liquido = resultado_antes_tributos - ir_provisionado - cs_provisionado

            # Store values in DRE
            df.loc[("1", "Receita Bruta de Vendas"), month] = receita_bruta
            df.loc[("2.3", "(-) Impostos e Contribuições s/ Vendas"), month] = -impostos_sobre_vendas
            df.loc[("3", "(=) Receita Líquida de Vendas"), month] = receita_liquida
            df.loc[("4.2", "(-) Custo dos Serviços Prestados"), month] = -custo_servicos
            df.loc[("5", "(=) Resultado Bruto"), month] = resultado_bruto
            df.loc[("6.1", "(-) Despesas Administrativas"), month] = -despesas_administrativas
            df.loc[("6.2", "(-) Despesas com Vendas"), month] = -despesas_vendas
            df.loc[("6.3", "(-) Despesas Financeiras Líquidas"), month] = -despesas_financeiras
            df.loc[("6.4", "(-) Outras Despesas Operacionais"), month] = -outras_despesas
            df.loc[("7", "(=) Resultado Operacional (EBITDA/LAJIDA)"), month] = ebitda
            df.loc[("8", "(-) Depreciações e Amortizações"), month] = -depreciacao
            df.loc[("9", "(=) Resultado Antes dos Tributos s/ Lucro"), month] = resultado_antes_tributos
            df.loc[("10", "(-) Provisão p/ Imposto de Renda"), month] = -ir_provisionado
            df.loc[("11", "(-) Provisão p/ Contribuição Social"), month] = -cs_provisionado
            df.loc[("12", "(=) Resultado do Exercício"), month] = resultado_liquido

        return df

    def _calculate_monitoring_metrics(self, df_cash_flow: pd.DataFrame, df_dre: pd.DataFrame) -> MonitoringMetrics:
        """Calculate key monitoring metrics"""
        metrics = MonitoringMetrics()

        # Get recent month data (last month)
        last_month = df_cash_flow.shape[1] - 1

        # Revenue metrics
        if "Receitas de Vendas" in df_cash_flow.index:
            current_revenue = df_cash_flow.loc["Receitas de Vendas", last_month]
            previous_revenue = df_cash_flow.loc["Receitas de Vendas", last_month - 1] if last_month > 0 else current_revenue

            metrics.mrr = current_revenue
            metrics.arr = current_revenue * 12

            if previous_revenue > 0:
                metrics.revenue_growth_mom = ((current_revenue / previous_revenue) - 1) * 100

        # Get 12-month revenue for YoY comparison
        if last_month >= 12:
            revenue_12m_ago = df_cash_flow.loc["Receitas de Vendas", last_month - 12]
            current_revenue = df_cash_flow.loc["Receitas de Vendas", last_month]
            if revenue_12m_ago > 0:
                metrics.revenue_growth_yoy = ((current_revenue / revenue_12m_ago) - 1) * 100

        # Financial metrics from DRE
        if not df_dre.empty:
            # Get margin metrics
            receita_liquida = df_dre.loc[("3", "(=) Receita Líquida de Vendas"), last_month]
            resultado_bruto = df_dre.loc[("5", "(=) Resultado Bruto"), last_month]
            ebitda = df_dre.loc[("7", "(=) Resultado Operacional (EBITDA/LAJIDA)"), last_month]
            resultado_liquido = df_dre.loc[("12", "(=) Resultado do Exercício"), last_month]

            if receita_liquida > 0:
                metrics.gross_margin = (resultado_bruto / receita_liquida) * 100
                metrics.ebitda_margin = (ebitda / receita_liquida) * 100
                metrics.net_margin = (resultado_liquido / receita_liquida) * 100

        # Cash flow metrics
        if "Fluxo Líquido" in df_cash_flow.index:
            # Calculate average burn rate (negative cash flow)
            recent_flows = [df_cash_flow.loc["Fluxo Líquido", m] for m in range(max(0, last_month - 5), last_month + 1)]
            avg_flow = sum(recent_flows) / len(recent_flows)

            if avg_flow < 0:
                metrics.burn_rate = abs(avg_flow)

                # Calculate runway
                current_cash = df_cash_flow.loc["Saldo Acumulado", last_month]
                metrics.runway_months = metrics.calculate_runway(current_cash)

        # Operational metrics (simplified - would need actual customer data)
        metrics.conversion_rate = 45.0  # Default from premises
        metrics.average_ticket = 2400.0  # Default from premises

        # Team metrics (would need actual team data)
        metrics.total_employees = 10  # Default from premises
        if metrics.total_employees > 0 and metrics.mrr > 0:
            metrics.revenue_per_employee = (metrics.mrr * 12) / metrics.total_employees

        return metrics

    def _get_monthly_value(self, df: pd.DataFrame, month: int, column_or_index: str) -> float:
        """Safely get a monthly value from a dataframe"""
        if df is None or df.empty:
            return 0.0

        try:
            if column_or_index in df.columns and month < len(df):
                return df.loc[df.index[0], column_or_index] if len(df) == 1 else df.iloc[month][column_or_index]
            elif column_or_index in df.index and month < df.shape[1]:
                return df.loc[column_or_index, month]
            else:
                return 0.0
        except (KeyError, IndexError):
            return 0.0

    def _calculate_monthly_investments(self, month: int) -> float:
        """Calculate planned investments for a given month"""
        total_investment = 0.0

        for investment in self.premises.investimentos_planejados:
            investment_month = investment.get('mes', 0)
            if month == investment_month:
                total_investment += investment.get('valor', 0.0)

        return total_investment

    def _calculate_monthly_depreciation(self, month: int) -> float:
        """Calculate monthly depreciation (simplified)"""
        # This is a simplified calculation - would need actual asset data
        base_depreciation = 1000.0  # Base monthly depreciation
        return base_depreciation * (1 + (month / 60))  # Slightly increasing over time

class ProjectionsService:
    """Service for managing financial projections"""

    def __init__(self):
        self.premises: Optional[ProjecoesPremises] = None

    def load_premises(self, premises_data: Dict[str, Any]) -> None:
        """Load premises from dictionary data"""
        self.premises = self._dict_to_premises(premises_data)

    def get_premises(self) -> Optional[ProjecoesPremises]:
        """Get current premises"""
        return self.premises

    def calculate_projections(self, receitas_data: Optional[pd.DataFrame] = None,
                            despesas_data: Optional[pd.DataFrame] = None,
                            impostos_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Calculate financial projections using the calculator"""
        if not self.premises:
            return {'error': 'Premises not loaded', 'success': False}

        calculator = ProjectionsCalculator(self.premises)
        return calculator.calculate(
            receitas_data=receitas_data,
            despesas_data=despesas_data,
            impostos_data=impostos_data
        )

    def get_scenario_analysis(self, receitas_data: pd.DataFrame, despesas_data: pd.DataFrame,
                            impostos_data: pd.DataFrame) -> Dict[str, Any]:
        """Perform scenario analysis (optimistic, realistic, pessimistic)"""
        if not self.premises:
            return {'error': 'Premises not loaded'}

        scenarios = {}

        for scenario_name in ['pessimista', 'realista', 'otimista']:
            factor = self.premises.get_scenario_factor(scenario_name)

            # Adjust revenue data by scenario factor
            adjusted_receitas = receitas_data * factor

            # Calculate projections for this scenario
            result = self.calculate_projections(adjusted_receitas, despesas_data, impostos_data)

            if result.get('success'):
                scenarios[scenario_name] = {
                    'cash_flow': result['cash_flow'],
                    'dre': result['dre'],
                    'metrics': result['monitoring_metrics']
                }

        return scenarios

    def get_breakeven_analysis(self, despesas_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate breakeven analysis"""
        if not self.premises:
            return {'error': 'Premises not loaded'}

        # Calculate average monthly expenses
        if despesas_data.empty:
            return {'error': 'Expense data required for breakeven analysis'}

        total_despesas_col = None
        for col in despesas_data.columns:
            if 'total' in col.lower():
                total_despesas_col = col
                break

        if total_despesas_col is None:
            # Sum all expense columns
            avg_monthly_expenses = despesas_data.sum(axis=1).mean()
        else:
            avg_monthly_expenses = despesas_data[total_despesas_col].mean()

        # Assume average margin
        assumed_margin = 0.7  # 70% margin

        # Calculate breakeven revenue needed
        breakeven_revenue = avg_monthly_expenses / assumed_margin

        # Calculate breakeven in units (if we have average ticket)
        breakeven_units = breakeven_revenue / self.premises.meta_ticket_medio

        return {
            'breakeven_revenue_monthly': breakeven_revenue,
            'breakeven_revenue_annual': breakeven_revenue * 12,
            'breakeven_units_monthly': breakeven_units,
            'breakeven_units_annual': breakeven_units * 12,
            'average_monthly_expenses': avg_monthly_expenses,
            'assumed_margin': assumed_margin * 100
        }

    def _dict_to_premises(self, data: Dict[str, Any]) -> ProjecoesPremises:
        """Convert dictionary to ProjecoesPremises object"""
        premises = ProjecoesPremises()

        # Basic parameters
        premises.meses_projecao = data.get('meses_projecao', 60)
        premises.data_inicio = data.get('data_inicio', '2024-01-01')
        premises.ipca_projecao = data.get('ipca_projecao', 4.5)
        premises.igpm_projecao = data.get('igpm_projecao', 5.0)

        # Growth targets
        premises.meta_receita_anual = data.get('meta_receita_anual', 1000000.0)
        premises.meta_margem_liquida = data.get('meta_margem_liquida', 15.0)
        premises.meta_ebitda_margin = data.get('meta_ebitda_margin', 25.0)

        # Scenario factors
        premises.cenario_otimista_fator = data.get('cenario_otimista_fator', 1.2)
        premises.cenario_pessimista_fator = data.get('cenario_pessimista_fator', 0.8)
        premises.cenario_realista_fator = data.get('cenario_realista_fator', 1.0)

        # Seasonality
        premises.considerar_sazonalidade = data.get('considerar_sazonalidade', False)
        if 'fatores_sazonais' in data:
            premises.fatores_sazonais = data['fatores_sazonais']

        # Cash flow parameters
        premises.prazo_medio_recebimento = data.get('prazo_medio_recebimento', 30)
        premises.prazo_medio_pagamento = data.get('prazo_medio_pagamento', 30)
        premises.reserva_minima_caixa = data.get('reserva_minima_caixa', 50000.0)

        # Operational targets
        premises.meta_leads_mensais = data.get('meta_leads_mensais', 1000)
        premises.meta_taxa_conversao = data.get('meta_taxa_conversao', 45.0)
        premises.meta_ticket_medio = data.get('meta_ticket_medio', 2400.0)
        premises.meta_lifetime_value = data.get('meta_lifetime_value', 10000.0)
        premises.meta_cac = data.get('meta_cac', 500.0)

        # HR metrics
        premises.meta_headcount = data.get('meta_headcount', 10)
        premises.meta_receita_por_funcionario = data.get('meta_receita_por_funcionario', 125000.0)
        premises.meta_custo_folha_percentual = data.get('meta_custo_folha_percentual', 30.0)

        # Planned investments
        premises.investimentos_planejados = data.get('investimentos_planejados', [])

        return premises
