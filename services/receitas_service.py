import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from models.receitas import ReceitasPremises, CanalVenda, ConversionParams, TipoCrescimento, PeriodicidadeCrescimento
from core.base_classes import BaseCalculator

class ReceitasCalculator(BaseCalculator):
    """Calculator for revenue projections"""
    
    def __init__(self, premises: ReceitasPremises):
        self.premises = premises
    
    def _validate_inputs(self, **kwargs) -> bool:
        """Validate calculation inputs"""
        return self.premises is not None
    
    def _perform_calculation(self, months: int = 60, **kwargs) -> Dict[str, Any]:
        """Calculate revenue projections for the specified period"""
        try:
            if self.premises.modelo_marketing:
                # Marketing-based revenue calculation
                df_revenue = self._calculate_marketing_revenue(months)
                df_detailed = self._calculate_detailed_funnel(months)
            else:
                # Financial model-based revenue calculation  
                df_revenue = self._calculate_financial_model_revenue(months)
                df_detailed = pd.DataFrame()
            
            # Calculate other revenues
            df_outras = self._calculate_other_revenues(months)
            
            return {
                'receitas_principais': df_revenue,
                'outras_receitas': df_outras,
                'detalhamento_funil': df_detailed,
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def _calculate_marketing_revenue(self, months: int) -> pd.DataFrame:
        """Calculate revenue based on marketing channels"""
        # Create index structure
        indices = ["Receita Bruta"]
        
        # Add channels
        for canal in self.premises.canais_venda:
            indices.append(f"Canal - {canal.descricao}")
        
        # Add primary sources
        for fonte in self.premises.fontes_primarias:
            indices.append(f"Fonte - {fonte.descricao}")
        
        indices.extend(["Receita Líquida", "Total"])
        
        # Create dataframe
        df = pd.DataFrame(0.0, index=indices, columns=range(months))
        
        for month in range(months):
            total_bruto = 0
            
            # Calculate channel revenues
            for canal in self.premises.canais_venda:
                revenue = self._calculate_channel_revenue(canal, month)
                df.loc[f"Canal - {canal.descricao}", month] = revenue
                total_bruto += revenue
            
            # Calculate primary source revenues
            for fonte in self.premises.fontes_primarias:
                if month >= fonte.periodo_inicio and month <= fonte.periodo_fim:
                    months_since_start = month - fonte.periodo_inicio
                    growth_factor = (1 + fonte.taxa_crescimento_mensal / 100) ** months_since_start
                    revenue = fonte.valor_mensal * growth_factor
                    df.loc[f"Fonte - {fonte.descricao}", month] = revenue
                    total_bruto += revenue
            
            # Apply repasse
            receita_liquida = total_bruto * self.premises.repasse_decimal
            
            df.loc["Receita Bruta", month] = total_bruto
            df.loc["Receita Líquida", month] = receita_liquida  
            df.loc["Total", month] = receita_liquida
        
        return df
    
    def _calculate_financial_model_revenue(self, months: int) -> pd.DataFrame:
        """Calculate revenue based on financial growth model"""
        df = pd.DataFrame(0.0, index=["Receita"], columns=range(months))
        
        base_revenue = self.premises.receita_inicial / 12  # Monthly base
        
        for month in range(months):
            if self.premises.crescimento_receita == TipoCrescimento.LINEAR:
                growth_factor = (1 + self.premises.tx_cresc_mensal / 100) ** month
            elif self.premises.crescimento_receita == TipoCrescimento.PRODUTIVIDADE:
                growth_factor = self._calculate_productivity_growth(month)
            else:
                growth_factor = self._calculate_non_linear_growth(month)
            
            revenue = base_revenue * growth_factor * self.premises.repasse_decimal
            df.loc["Receita", month] = revenue
        
        return df
    
    def _calculate_other_revenues(self, months: int) -> pd.DataFrame:
        """Calculate other revenue sources"""
        if not self.premises.outras_receitas:
            return pd.DataFrame()
        
        indices = [receita.descricao for receita in self.premises.outras_receitas]
        indices.append("Total Outras Receitas")
        
        df = pd.DataFrame(0.0, index=indices, columns=range(months))
        
        for month in range(months):
            total = 0
            
            for receita in self.premises.outras_receitas:
                value = receita.valor_no_mes(month)
                df.loc[receita.descricao, month] = value
                total += value
            
            df.loc["Total Outras Receitas", month] = total
        
        return df
    
    def _calculate_detailed_funnel(self, months: int) -> pd.DataFrame:
        """Calculate detailed sales funnel metrics"""
        funnel_metrics = [
            "Gasto Total", "Leads Totais", "Agendamentos", 
            "Comparecimentos", "Conversões", "Receita Bruta"
        ]
        
        df = pd.DataFrame(0.0, index=funnel_metrics, columns=range(months))
        
        for month in range(months):
            total_gasto = 0
            total_leads = 0
            total_agendamentos = 0
            total_comparecimentos = 0
            total_conversoes = 0
            total_receita = 0
            
            for canal in self.premises.canais_venda:
                gasto = self._calculate_channel_spending(canal, month)
                cpl_adjusted = canal.calculate_adjusted_cpl(gasto)
                
                if cpl_adjusted > 0:
                    leads = gasto / cpl_adjusted
                else:
                    leads = 0
                
                conversions = canal.conversion_params.calculate_conversions(leads)
                
                total_gasto += gasto
                total_leads += leads
                total_agendamentos += conversions['agendamentos']
                total_comparecimentos += conversions['comparecimentos']
                total_conversoes += conversions['conversoes']
                total_receita += conversions['faturamento']
            
            df.loc["Gasto Total", month] = total_gasto
            df.loc["Leads Totais", month] = total_leads
            df.loc["Agendamentos", month] = total_agendamentos
            df.loc["Comparecimentos", month] = total_comparecimentos
            df.loc["Conversões", month] = total_conversoes
            df.loc["Receita Bruta", month] = total_receita
        
        return df
    
    def _calculate_channel_revenue(self, canal: CanalVenda, month: int) -> float:
        """Calculate revenue for a specific channel and month"""
        gasto = self._calculate_channel_spending(canal, month)
        cpl_adjusted = canal.calculate_adjusted_cpl(gasto)
        
        if cpl_adjusted <= 0:
            return 0
        
        leads = gasto / cpl_adjusted
        conversions = canal.conversion_params.calculate_conversions(leads)
        
        return conversions['faturamento']
    
    def _calculate_channel_spending(self, canal: CanalVenda, month: int) -> float:
        """Calculate spending for a specific channel and month"""
        base_spending = canal.gasto_mensal
        
        # Apply growth based on channel configuration
        if canal.crescimento_vendas == TipoCrescimento.LINEAR:
            growth_factor = (1 + canal.tx_cresc_mensal / 100) ** month
        elif canal.crescimento_vendas == TipoCrescimento.PRODUTIVIDADE:
            growth_factor = self._calculate_productivity_growth_for_channel(canal, month)
        else:
            growth_factor = self._calculate_non_linear_growth_for_channel(canal, month)
        
        # Apply acceleration factor
        growth_factor *= canal.fator_aceleracao_crescimento
        
        # Apply periodicity
        if canal.periodicidade != PeriodicidadeCrescimento.MENSAL:
            growth_factor = self._apply_periodicity_adjustment(growth_factor, month, canal.periodicidade)
        
        return base_spending * growth_factor
    
    def _calculate_productivity_growth(self, month: int) -> float:
        """Calculate productivity-based growth factor"""
        # Get payroll data (simplified - would need actual payroll calculation)
        payroll_factor = 1 + (month * 0.05)  # Simplified payroll growth
        
        # Calculate productivity ratio
        monthly_rpe = self.premises.rpe_anual / 12
        productivity_ratio = monthly_rpe / (self.premises.salario_medio / 12)
        
        # Apply depreciation
        depreciation_factor = (1 - self.premises.depreciacao / 100) ** month
        
        return payroll_factor * productivity_ratio * depreciation_factor
    
    def _calculate_productivity_growth_for_channel(self, canal: CanalVenda, month: int) -> float:
        """Calculate productivity-based growth for a specific channel"""
        payroll_factor = 1 + (month * 0.05)
        monthly_rpe = canal.rpe_anual / 12
        productivity_ratio = monthly_rpe / (canal.salario_medio / 12)
        depreciation_factor = (1 - canal.depreciacao / 100) ** month
        
        return payroll_factor * productivity_ratio * depreciation_factor
    
    def _calculate_non_linear_growth(self, month: int) -> float:
        """Calculate non-linear growth factor"""
        if self.premises.crescimento_receita == TipoCrescimento.NAO_LINEAR_SEM_DOWNSIDE:
            # Sigmoid-like growth without downside
            x = month / 12  # Convert to years
            return 1 + (self.premises.media_cresc_anual / 100) * (1 / (1 + np.exp(-self.premises.fator_crescimento * (x - 1))))
        else:
            # With downside - includes volatility
            base_growth = self._calculate_non_linear_growth(month)  # Recursive call to get base
            volatility = np.random.normal(0, 0.1) if hasattr(np, 'random') else 0  # 10% volatility
            return max(0.5, base_growth * (1 + volatility))  # Minimum 50% of original revenue
    
    def _calculate_non_linear_growth_for_channel(self, canal: CanalVenda, month: int) -> float:
        """Calculate non-linear growth for a specific channel"""
        if canal.crescimento_vendas == TipoCrescimento.NAO_LINEAR_SEM_DOWNSIDE:
            x = month / 12
            return 1 + (canal.media_cresc_anual / 100) * (1 / (1 + np.exp(-canal.fator_aceleracao_crescimento * (x - 1))))
        else:
            base_growth = self._calculate_non_linear_growth_for_channel(canal, month)
            volatility = np.random.normal(0, 0.1) if hasattr(np, 'random') else 0
            return max(0.5, base_growth * (1 + volatility))
    
    def _apply_periodicity_adjustment(self, growth_factor: float, month: int, periodicity: PeriodicidadeCrescimento) -> float:
        """Apply periodicity adjustments to growth"""
        if periodicity == PeriodicidadeCrescimento.TRIMESTRAL:
            # Apply growth only every 3 months
            if month % 3 != 0:
                return 1.0
            return growth_factor
        elif periodicity == PeriodicidadeCrescimento.SEMESTRAL:
            # Apply growth only every 6 months
            if month % 6 != 0:
                return 1.0
            return growth_factor
        elif periodicity == PeriodicidadeCrescimento.ANUAL:
            # Apply growth only every 12 months
            if month % 12 != 0:
                return 1.0
            return growth_factor
        
        return growth_factor  # Monthly - no adjustment needed

class ReceitasService:
    """Service for managing revenue calculations"""
    
    def __init__(self):
        self.premises: Optional[ReceitasPremises] = None
    
    def load_premises(self, premises_data: Dict[str, Any]) -> None:
        """Load premises from dictionary data"""
        self.premises = self._dict_to_premises(premises_data)
    
    def get_premises(self) -> Optional[ReceitasPremises]:
        """Get current premises"""
        return self.premises
    
    def calculate_revenues(self, months: int = 60) -> Dict[str, Any]:
        """Calculate all revenues using the calculator"""
        if not self.premises:
            return {'error': 'Premises not loaded', 'success': False}
        
        calculator = ReceitasCalculator(self.premises)
        return calculator.calculate(months=months)
    
    def get_monthly_summary(self, month: int) -> Dict[str, float]:
        """Get revenue summary for a specific month"""
        if not self.premises:
            return {}
        
        result = self.calculate_revenues()
        if not result.get('success'):
            return {}
        
        summary = {}
        
        # Main revenues
        df_main = result['receitas_principais']
        if month < len(df_main.columns) and "Total" in df_main.index:
            summary['receitas_principais'] = df_main.loc["Total", month]
        
        # Other revenues
        df_outras = result['outras_receitas']
        if not df_outras.empty and month < len(df_outras.columns):
            if "Total Outras Receitas" in df_outras.index:
                summary['outras_receitas'] = df_outras.loc["Total Outras Receitas", month]
        
        summary['receita_total'] = sum(summary.values())
        
        return summary
    
    def get_channel_performance(self, month: int) -> List[Dict[str, Any]]:
        """Get performance metrics for all channels in a specific month"""
        if not self.premises:
            return []
        
        result = self.calculate_revenues()
        if not result.get('success'):
            return []
        
        channel_performance = []
        
        df_funnel = result.get('detalhamento_funil')
        if df_funnel is not None and not df_funnel.empty and month < len(df_funnel.columns):
            # This is simplified - in a full implementation, we'd have per-channel metrics
            total_gasto = df_funnel.loc["Gasto Total", month] if "Gasto Total" in df_funnel.index else 0
            total_leads = df_funnel.loc["Leads Totais", month] if "Leads Totais" in df_funnel.index else 0
            total_receita = df_funnel.loc["Receita Bruta", month] if "Receita Bruta" in df_funnel.index else 0
            
            for i, canal in enumerate(self.premises.canais_venda):
                # Simplified metrics - would need per-channel calculation
                channel_gasto = total_gasto / len(self.premises.canais_venda) if self.premises.canais_venda else 0
                channel_leads = total_leads / len(self.premises.canais_venda) if self.premises.canais_venda else 0  
                channel_receita = total_receita / len(self.premises.canais_venda) if self.premises.canais_venda else 0
                
                roas = channel_receita / channel_gasto if channel_gasto > 0 else 0
                cpl = channel_gasto / channel_leads if channel_leads > 0 else 0
                
                channel_performance.append({
                    'canal': canal.descricao,
                    'gasto': channel_gasto,
                    'leads': channel_leads,
                    'receita': channel_receita,
                    'roas': roas,
                    'cpl': cpl
                })
        
        return channel_performance
    
    def _dict_to_premises(self, data: Dict[str, Any]) -> ReceitasPremises:
        """Convert dictionary to ReceitasPremises object"""
        premises = ReceitasPremises()
        
        # Basic configuration
        premises.modelo_marketing = data.get('modelo_marketing', True)
        premises.repasse_bruto = data.get('repasse_bruto', 85.0)
        
        # Financial model parameters
        premises.receita_inicial = data.get('receita_inicial', 100000.0)
        premises.valor_unitario = data.get('valor_unitario', 2400.0)
        
        # Growth configuration
        crescimento_str = data.get('crescimento_receita', 'Linear')
        if crescimento_str == 'Linear':
            premises.crescimento_receita = TipoCrescimento.LINEAR
        elif crescimento_str == 'Não Linear S/ Downside':
            premises.crescimento_receita = TipoCrescimento.NAO_LINEAR_SEM_DOWNSIDE
        elif crescimento_str == 'Não Linear C/ Downside':
            premises.crescimento_receita = TipoCrescimento.NAO_LINEAR_COM_DOWNSIDE
        else:
            premises.crescimento_receita = TipoCrescimento.PRODUTIVIDADE
        
        premises.tx_cresc_mensal = data.get('tx_cresc_mensal', 5.0)
        premises.media_cresc_anual = data.get('media_cresc_anual', 15.0)
        premises.fator_crescimento = data.get('fator_crescimento', 0.5)
        premises.fator_estabilizacao = data.get('fator_estabilizacao', 0.8)
        
        # Productivity parameters
        premises.rpe_anual = data.get('rpe_anual', 125000.0)
        premises.salario_medio = data.get('salario_medio', 60000.0)
        premises.depreciacao = data.get('depreciacao', 1.5)
        
        # Sales channels
        canais_data = data.get('canais_venda', [])
        for canal_data in canais_data:
            conversion_data = canal_data.get('conversion_params', {})
            conversion_params = ConversionParams(
                fator_elasticidade=conversion_data.get('fator_elasticidade', 1.0),
                taxa_agendamento=conversion_data.get('taxa_agendamento', 30.0),
                taxa_comparecimento=conversion_data.get('taxa_comparecimento', 70.0),
                taxa_conversao=conversion_data.get('taxa_conversao', 45.0),
                ticket_medio=conversion_data.get('ticket_medio', 2400.0)
            )
            
            # Parse growth type
            crescimento_canal = canal_data.get('crescimento_vendas', 'Linear')
            if crescimento_canal == 'Linear':
                growth_type = TipoCrescimento.LINEAR
            elif crescimento_canal == 'Não Linear S/ Downside':
                growth_type = TipoCrescimento.NAO_LINEAR_SEM_DOWNSIDE
            elif crescimento_canal == 'Não Linear C/ Downside':
                growth_type = TipoCrescimento.NAO_LINEAR_COM_DOWNSIDE
            else:
                growth_type = TipoCrescimento.PRODUTIVIDADE
            
            # Parse periodicity
            periodicidade_str = canal_data.get('periodicidade', 'Mensal')
            if periodicidade_str == 'Trimestral':
                periodicity = PeriodicidadeCrescimento.TRIMESTRAL
            elif periodicidade_str == 'Semestral':
                periodicity = PeriodicidadeCrescimento.SEMESTRAL
            elif periodicidade_str == 'Anual':
                periodicity = PeriodicidadeCrescimento.ANUAL
            else:
                periodicity = PeriodicidadeCrescimento.MENSAL
            
            canal = CanalVenda(
                descricao=canal_data.get('descricao', ''),
                gasto_mensal=canal_data.get('gasto_mensal', 0.0),
                cpl_base=canal_data.get('cpl_base', 10.0),
                crescimento_vendas=growth_type,
                periodicidade=periodicity,
                tx_cresc_mensal=canal_data.get('tx_cresc_mensal', 5.0),
                media_cresc_anual=canal_data.get('media_cresc_anual', 15.0),
                fator_aceleracao_crescimento=canal_data.get('fator_aceleracao_crescimento', 1.0),
                rpe_anual=canal_data.get('rpe_anual', 125000.0),
                salario_medio=canal_data.get('salario_medio', 60000.0),
                depreciacao=canal_data.get('depreciacao', 1.5),
                conversion_params=conversion_params
            )
            
            premises.canais_venda.append(canal)
        
        return premises