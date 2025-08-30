import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
from core.base_classes import BasePage, SessionStateManager
from models.receitas import ReceitasPremises, CanalVenda, ConversionParams, TipoCrescimento, PeriodicidadeCrescimento
from services.receitas_service import ReceitasService
from utils.plot_manager import PlotlyPlotManager
from config.settings import ConfigManager

class PremissasReceitasPage(BasePage):
    """Page for revenue premises configuration"""
    
    def __init__(self, state_manager: Optional[SessionStateManager] = None,
                 config_manager: Optional[ConfigManager] = None):
        self._config = config_manager or ConfigManager()
        super().__init__(state_manager)
        self._service = ReceitasService()
    
    @property
    def title(self) -> str:
        return "Premissas Receitas"
    
    @property
    def icon(self) -> str:
        return "💲"
    
    def _initialize_state(self) -> None:
        """Initialize revenue premises in state"""
        default_params = {
            # Model configuration
            'modelo_marketing': True,
            'repasse_bruto': 85.0,
            
            # Sales channels
            'canais_venda': [],
            
            # Primary sources
            'fontes_primarias': [],
            
            # Other revenues
            'outras_receitas': [],
            
            # Financial model parameters
            'receita_inicial': 100000.0,
            'valor_unitario': 2400.0,
            'crescimento_receita': 'Linear',
            'tx_cresc_mensal': 5.0,
            'media_cresc_anual': 15.0,
            'fator_crescimento': 0.5,
            'fator_estabilizacao': 0.8,
            
            # Productivity model defaults
            'rpe_anual': 125000.0,
            'salario_medio': 60000.0,
            'depreciacao': 1.5
        }
        
        self._state_manager.ensure_state('premissas_receitas', default_params)
        
        # Load premises into service
        premises_data = self._state_manager.get_state('premissas_receitas')
        self._service.load_premises(premises_data)
    
    def _render_content(self) -> None:
        """Render revenue premises content"""
        st.write("### Configuração de Receitas")
        st.write("Configure os parâmetros para projeção de receitas da empresa.")
        
        # Marketing model is always active
        st.info("**Modelo de Marketing**: Calcula receitas com base nos dados da equipe e conversões.")
        
        # Repasse configuration
        self._render_repasse_config()
        
        # Sales channels from team data
        self._render_marketing_channels()
        
        # Other revenue sources
        self._render_other_revenues()
        
        # Summary
        self._render_summary()
    
    def _render_repasse_config(self) -> None:
        """Render repasse configuration"""
        st.write("### Configurações de Repasse")
        st.write("Defina o percentual de repasse bruto aplicado às receitas.")
        
        repasse = st.slider(
            "Repasse Bruto (%)",
            min_value=1.0,
            max_value=100.0,
            value=self._get_state('repasse_bruto'),
            step=0.5,
            format="%.1f",
            help="Percentual do valor da venda que é efetivamente recebido pela empresa."
        )
        self._update_state('repasse_bruto', repasse)
    
    def _render_marketing_channels(self) -> None:
        """Render marketing channels configuration"""
        st.write("### Canais de Vendas")
        st.info("Os canais de venda são gerados automaticamente a partir dos membros de equipe marcados como 'Sujeito a Aumento de Receita' em 'Premissas Despesas'.")
        
        # Get team members from expenses premises
        team_members = self._get_revenue_team_members()
        
        if not team_members:
            st.warning("Nenhum membro de equipe marcado como 'Sujeito a Aumento de Receita'. Configure os membros de equipe em 'Premissas Despesas'.")
            return
        
        # Generate channels automatically
        canais = []
        for member in team_members:
            canal_data = {
                'descricao': f"Canal - {member['nome']}",
                'gasto_mensal': member.get('gasto_mensal', 5000.0),
                'cpl_base': member.get('cpl_base', 10.0),
                'crescimento_vendas': member.get('crescimento_vendas', 'Linear'),
                'periodicidade': member.get('periodicidade', 'Mensal'),
                'tx_cresc_mensal': member.get('tx_cresc_mensal', 5.0),
                'media_cresc_anual': member.get('media_cresc_anual', 15.0),
                'fator_aceleracao_crescimento': member.get('fator_aceleracao_crescimento', 1.0),
                'rpe_anual': member.get('rpe_anual', 125000.0),
                'salario_medio': member.get('salario_medio', 60000.0),
                'depreciacao': member.get('depreciacao', 1.5),
                'conversion_params': {
                    'fator_elasticidade': member.get('fator_elasticidade', 1.0),
                    'taxa_agendamento': member.get('taxa_agendamento', 30.0),
                    'taxa_comparecimento': member.get('taxa_comparecimento', 70.0),
                    'taxa_conversao': member.get('taxa_conversao', 45.0),
                    'ticket_medio': member.get('ticket_medio', 2400.0)
                }
            }
            canais.append(canal_data)
        
        self._update_state('canais_venda', canais)
        
        # Display channels
        st.write("#### Canais Configurados")
        if canais:
            total_gasto = sum(canal['gasto_mensal'] for canal in canais)
            total_leads_estimados = sum(canal['gasto_mensal'] / canal['cpl_base'] if canal['cpl_base'] > 0 else 0 for canal in canais)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Gasto Mensal", f"R$ {total_gasto:,.2f}")
            with col2:
                st.metric("Leads Estimados/Mês", f"{total_leads_estimados:,.0f}")
            
            # Channel details
            canal_data = []
            for canal in canais:
                conversions = canal['conversion_params']
                leads = canal['gasto_mensal'] / canal['cpl_base'] if canal['cpl_base'] > 0 else 0
                receita_estimada = (leads * 
                                  conversions['taxa_agendamento'] / 100 * 
                                  conversions['taxa_comparecimento'] / 100 * 
                                  conversions['taxa_conversao'] / 100 * 
                                  conversions['ticket_medio'])
                
                canal_data.append({
                    "Canal": canal['descricao'],
                    "Gasto (R$)": f"{canal['gasto_mensal']:,.2f}",
                    "CPL (R$)": f"{canal['cpl_base']:,.2f}",
                    "Leads Est.": f"{leads:,.0f}",
                    "Receita Est. (R$)": f"{receita_estimada:,.2f}",
                    "ROAS": f"{receita_estimada / canal['gasto_mensal']:.2f}x" if canal['gasto_mensal'] > 0 else "N/A"
                })
            
            df_canais = pd.DataFrame(canal_data)
            st.dataframe(df_canais, use_container_width=True)
    
    def _render_other_revenues(self) -> None:
        """Render other revenue sources"""
        st.write("### Outras Receitas")
        st.write("Configure outras fontes de receita não relacionadas aos canais principais.")
        
        outras_receitas = self._get_state('outras_receitas')
        
        # Display current other revenues
        if outras_receitas:
            st.write("#### Receitas Configuradas")
            df_data = []
            for receita in outras_receitas:
                df_data.append({
                    "Descrição": receita.get('descricao', ''),
                    "Valor Mensal (R$)": f"{receita.get('valor_mensal', 0):,.2f}",
                    "Recorrente": "Sim" if receita.get('recorrente', True) else "Não",
                    "Período": f"Mês {receita.get('mes_inicio', 0)} - {receita.get('mes_fim', 59)}"
                })
            
            df_outras = pd.DataFrame(df_data)
            st.dataframe(df_outras, use_container_width=True)
        
        # Form to add other revenues
        with st.expander("Adicionar Nova Receita"):
            with st.form("nova_receita"):
                descricao = st.text_input("Descrição da Receita")
                valor_mensal = st.number_input("Valor Mensal (R$)", min_value=0.0, value=1000.0, step=100.0)
                recorrente = st.checkbox("Receita Recorrente", value=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    mes_inicio = st.number_input("Mês de Início", min_value=0, max_value=59, value=0)
                with col2:
                    mes_fim = st.number_input("Mês de Fim", min_value=0, max_value=59, value=59)
                
                if st.form_submit_button("Adicionar Receita"):
                    if descricao:
                        nova_receita = {
                            'descricao': descricao,
                            'valor_mensal': valor_mensal,
                            'recorrente': recorrente,
                            'mes_inicio': mes_inicio,
                            'mes_fim': mes_fim
                        }
                        
                        outras_receitas = self._get_state('outras_receitas')
                        outras_receitas.append(nova_receita)
                        self._update_state('outras_receitas', outras_receitas)
                        
                        st.success(f"Receita '{descricao}' adicionada com sucesso!")
                        st.rerun()
        
        # Remove other revenues
        if outras_receitas:
            st.write("#### Remover Receitas")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                receitas_nomes = [r.get('descricao', '') for r in outras_receitas]
                receita_selecionada = st.selectbox("Selecione uma receita para remover", receitas_nomes)
            
            with col2:
                if st.button("Remover Receita"):
                    outras_receitas = [r for r in outras_receitas if r.get('descricao') != receita_selecionada]
                    self._update_state('outras_receitas', outras_receitas)
                    st.success(f"Receita {receita_selecionada} removida!")
                    st.rerun()
    
    def _render_summary(self) -> None:
        """Render configuration summary"""
        st.write("### Resumo das Configurações")
        
        canais = self._get_state('canais_venda')
        outras = self._get_state('outras_receitas')
        
        summary_data = [
            ["Modelo de Receitas", "Marketing"],
            ["Repasse Bruto", f"{self._get_state('repasse_bruto')}%"],
            ["Canais de Venda", f"{len(canais)} canais configurados"],
            ["Outras Receitas", f"{len(outras)} fontes configuradas"],
            ["Fonte dos Dados", "Equipe definida em 'Premissas Despesas'"]
        ]
        
        df_summary = pd.DataFrame(summary_data, columns=["Parâmetro", "Valor"])
        st.dataframe(df_summary, use_container_width=True)
        
        # Show total estimated monthly revenue
        if canais:
            total_receita_canais = 0
            for canal in canais:
                conversions = canal['conversion_params']
                leads = canal['gasto_mensal'] / canal['cpl_base'] if canal['cpl_base'] > 0 else 0
                receita = (leads * 
                          conversions['taxa_agendamento'] / 100 * 
                          conversions['taxa_comparecimento'] / 100 * 
                          conversions['taxa_conversao'] / 100 * 
                          conversions['ticket_medio'])
                total_receita_canais += receita
            
            total_outras_receitas = sum(r.get('valor_mensal', 0) for r in outras)
            receita_bruta_total = total_receita_canais + total_outras_receitas
            receita_liquida_total = receita_bruta_total * (self._get_state('repasse_bruto') / 100)
            
            st.write("### Projeção de Receita (Primeiro Mês)")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Receita Canais", f"R$ {total_receita_canais:,.2f}")
            with col2:
                st.metric("Outras Receitas", f"R$ {total_outras_receitas:,.2f}")
            with col3:
                st.metric("Receita Líquida Total", f"R$ {receita_liquida_total:,.2f}")
    
    def _get_revenue_team_members(self) -> List[Dict[str, Any]]:
        """Get team members marked for revenue increase"""
        despesas_data = self._state_manager.get_state('premissas_despesas', {})
        equipe_propria = despesas_data.get('equipe_propria', [])
        
        return [member for member in equipe_propria if member.get('sujeito_aumento_receita', False)]
    
    def _get_state(self, key: str) -> Any:
        """Get value from premises state"""
        premises = self._state_manager.get_state('premissas_receitas')
        return premises.get(key)
    
    def _update_state(self, key: str, value: Any) -> None:
        """Update value in premises state"""
        premises = self._state_manager.get_state('premissas_receitas')
        premises[key] = value
        self._state_manager.set_state('premissas_receitas', premises)
        # Reload premises into service
        self._service.load_premises(premises)


class ReceitasVisualizationPage(BasePage):
    """Page for revenue visualization"""
    
    def __init__(self, state_manager: Optional[SessionStateManager] = None,
                 config_manager: Optional[ConfigManager] = None,
                 plot_manager: Optional[PlotlyPlotManager] = None):
        self._config = config_manager or ConfigManager()
        self._plot_manager = plot_manager or PlotlyPlotManager()
        super().__init__(state_manager)
        self._service = ReceitasService()
    
    @property
    def title(self) -> str:
        return "Receitas"
    
    @property
    def icon(self) -> str:
        return "💰"
    
    def _initialize_state(self) -> None:
        """Initialize visualization state"""
        if 'premissas_receitas' in self._state_manager.get_state('', {}):
            premises_data = self._state_manager.get_state('premissas_receitas')
            self._service.load_premises(premises_data)
    
    def _render_content(self) -> None:
        """Render revenue visualization"""
        if not self._validate_premises():
            return
        
        # Get configuration
        settings = self._config.get_app_settings()
        
        # Visualization options
        col1, col2 = st.columns(2)
        
        with col1:
            time_frame = st.selectbox("Período", settings.time_frames, index=0)
        
        with col2:
            plot_type = st.selectbox("Tipo de Gráfico", settings.plot_types, index=0)
        
        # Calculate revenues
        result = self._service.calculate_revenues(60)
        
        if result.get('success'):
            self._display_revenue_analysis(result, time_frame, plot_type)
        else:
            st.error(f"Erro no cálculo: {result.get('error', 'Erro desconhecido')}")
    
    def _validate_premises(self) -> bool:
        """Validate that premises exist"""
        if 'premissas_receitas' not in self._state_manager.get_state('', {}):
            st.error("Premissas de receitas não definidas. Configure as premissas na página 'Premissas Receitas'.")
            return False
        return True
    
    def _display_revenue_analysis(self, result: Dict[str, Any], time_frame: str, plot_type: str) -> None:
        """Display comprehensive revenue analysis"""
        st.write("### Análise de Receitas")
        
        # Tabs for different revenue categories
        tab1, tab2, tab3 = st.tabs(["Receitas Principais", "Detalhamento do Funil", "Outras Receitas"])
        
        with tab1:
            self._display_main_revenues(result['receitas_principais'], time_frame, plot_type)
        
        with tab2:
            self._display_funnel_details(result.get('detalhamento_funil'), time_frame, plot_type)
        
        with tab3:
            self._display_other_revenues(result.get('outras_receitas'), time_frame, plot_type)
        
        # Performance metrics
        self._display_performance_metrics(result)
    
    def _display_main_revenues(self, df_main: pd.DataFrame, time_frame: str, plot_type: str) -> None:
        """Display main revenues"""
        st.write("#### Receitas Principais")
        
        if df_main.empty:
            st.info("Nenhuma receita calculada.")
            return
        
        # Convert to selected time frame
        df_display = self._convert_timeframe(df_main, time_frame)
        
        # Show dataframe
        st.dataframe(df_display.style.format("{:.2f}"), use_container_width=True)
        
        # Category selection
        categories = df_display.index.tolist()
        selected_categories = st.multiselect(
            "Selecione categorias para visualizar",
            categories,
            default=["Total"] if "Total" in categories else categories[:3]
        )
        
        if selected_categories:
            self._create_revenue_chart(df_display, selected_categories, time_frame, plot_type, "Receitas Principais")
    
    def _display_funnel_details(self, df_funnel: Optional[pd.DataFrame], time_frame: str, plot_type: str) -> None:
        """Display sales funnel details"""
        st.write("#### Detalhamento do Funil de Vendas")
        
        if df_funnel is None or df_funnel.empty:
            st.info("Dados do funil não disponíveis.")
            return
        
        # Convert to selected time frame
        df_display = self._convert_timeframe(df_funnel, time_frame)
        
        # Show dataframe
        st.dataframe(df_display.style.format("{:.2f}"), use_container_width=True)
        
        # Conversion metrics
        self._display_conversion_metrics(df_funnel)
        
        # Category selection for chart
        categories = df_display.index.tolist()
        selected_categories = st.multiselect(
            "Selecione métricas para visualizar",
            categories,
            default=["Receita Bruta", "Leads Totais"] if all(cat in categories for cat in ["Receita Bruta", "Leads Totais"]) else categories[:2],
            key="funnel_categories"
        )
        
        if selected_categories:
            self._create_revenue_chart(df_display, selected_categories, time_frame, plot_type, "Funil de Vendas")
    
    def _display_other_revenues(self, df_outras: Optional[pd.DataFrame], time_frame: str, plot_type: str) -> None:
        """Display other revenues"""
        st.write("#### Outras Receitas")
        
        if df_outras is None or df_outras.empty:
            st.info("Nenhuma outra receita configurada.")
            return
        
        # Convert to selected time frame
        df_display = self._convert_timeframe(df_outras, time_frame)
        
        # Show dataframe
        st.dataframe(df_display.style.format("{:.2f}"), use_container_width=True)
        
        # Category selection
        categories = df_display.index.tolist()
        selected_categories = st.multiselect(
            "Selecione fontes para visualizar",
            categories,
            default=categories[:3] if len(categories) >= 3 else categories,
            key="other_revenues_categories"
        )
        
        if selected_categories:
            self._create_revenue_chart(df_display, selected_categories, time_frame, plot_type, "Outras Receitas")
    
    def _display_conversion_metrics(self, df_funnel: pd.DataFrame) -> None:
        """Display conversion metrics"""
        if df_funnel.empty or len(df_funnel.columns) == 0:
            return
        
        st.write("##### Métricas de Conversão (Primeiro Mês)")
        
        # Get first month data
        first_month_col = df_funnel.columns[0]
        
        try:
            leads = df_funnel.loc["Leads Totais", first_month_col] if "Leads Totais" in df_funnel.index else 0
            agendamentos = df_funnel.loc["Agendamentos", first_month_col] if "Agendamentos" in df_funnel.index else 0
            comparecimentos = df_funnel.loc["Comparecimentos", first_month_col] if "Comparecimentos" in df_funnel.index else 0
            conversoes = df_funnel.loc["Conversões", first_month_col] if "Conversões" in df_funnel.index else 0
            gasto = df_funnel.loc["Gasto Total", first_month_col] if "Gasto Total" in df_funnel.index else 0
            receita = df_funnel.loc["Receita Bruta", first_month_col] if "Receita Bruta" in df_funnel.index else 0
            
            # Calculate rates
            taxa_agendamento = (agendamentos / leads * 100) if leads > 0 else 0
            taxa_comparecimento = (comparecimentos / agendamentos * 100) if agendamentos > 0 else 0
            taxa_conversao = (conversoes / comparecimentos * 100) if comparecimentos > 0 else 0
            cpl = gasto / leads if leads > 0 else 0
            roas = receita / gasto if gasto > 0 else 0
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Taxa Agendamento", f"{taxa_agendamento:.1f}%")
            with col2:
                st.metric("Taxa Comparecimento", f"{taxa_comparecimento:.1f}%")
            with col3:
                st.metric("Taxa Conversão", f"{taxa_conversao:.1f}%")
            with col4:
                st.metric("CPL Médio", f"R$ {cpl:.2f}")
            with col5:
                st.metric("ROAS", f"{roas:.2f}x")
        
        except (KeyError, IndexError):
            st.warning("Dados insuficientes para calcular métricas de conversão.")
    
    def _display_performance_metrics(self, result: Dict[str, Any]) -> None:
        """Display performance metrics"""
        st.write("### Métricas de Performance")
        
        # Calculate 12-month totals
        df_main = result.get('receitas_principais')
        df_outras = result.get('outras_receitas')
        
        main_total = 0
        outras_total = 0
        
        if df_main is not None and not df_main.empty:
            if "Total" in df_main.index:
                main_total = df_main.loc["Total", :11].sum()
            elif "Receita Líquida" in df_main.index:
                main_total = df_main.loc["Receita Líquida", :11].sum()
        
        if df_outras is not None and not df_outras.empty:
            if "Total Outras Receitas" in df_outras.index:
                outras_total = df_outras.loc["Total Outras Receitas", :11].sum()
        
        receita_total = main_total + outras_total
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Receitas Principais (12m)", f"R$ {main_total:,.2f}")
        
        with col2:
            st.metric("Outras Receitas (12m)", f"R$ {outras_total:,.2f}")
        
        with col3:
            st.metric("Receita Total (12m)", f"R$ {receita_total:,.2f}")
        
        # Calculate monthly averages and growth
        if df_main is not None and not df_main.empty and "Total" in df_main.index:
            first_month = df_main.loc["Total", 0] if len(df_main.columns) > 0 else 0
            last_month = df_main.loc["Total", 11] if len(df_main.columns) > 11 else first_month
            
            if first_month > 0:
                growth_rate = ((last_month / first_month) - 1) * 100
            else:
                growth_rate = 0
            
            avg_monthly = receita_total / 12 if receita_total > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Receita Média Mensal", f"R$ {avg_monthly:,.2f}")
            with col2:
                st.metric("Crescimento (1º vs 12º mês)", f"{growth_rate:+.1f}%")
    
    def _convert_timeframe(self, df: pd.DataFrame, time_frame: str) -> pd.DataFrame:
        """Convert monthly data to selected timeframe"""
        if time_frame == "Mensal":
            df_display = df.copy()
            df_display.columns = [f"Mês {i+1}" for i in range(len(df_display.columns))]
            return df_display
        elif time_frame == "Anual":
            years = len(df.columns) // 12
            df_annual = pd.DataFrame(index=df.index, columns=[f"Ano {i+1}" for i in range(years)])
            
            for year in range(years):
                start_month = year * 12
                end_month = min((year + 1) * 12, len(df.columns))
                df_annual[f"Ano {year+1}"] = df.iloc[:, start_month:end_month].sum(axis=1)
            
            return df_annual
        
        return df
    
    def _create_revenue_chart(self, df: pd.DataFrame, categories: List[str], time_frame: str, plot_type: str, chart_title: str) -> None:
        """Create revenue visualization chart"""
        df_plot = df.loc[categories].T
        
        if plot_type == "Gráfico de Linhas":
            fig = self._plot_manager.create_plot(
                df_plot, 'line',
                title=f"{chart_title} - {time_frame}",
                labels={'index': time_frame, 'value': 'Valor (R$)'}
            )
        elif plot_type == "Gráfico de Pizza":
            # Use last period for pie chart
            last_period_data = df_plot.iloc[-1]
            fig = self._plot_manager.create_plot(
                last_period_data.to_frame('Valor').T, 'pie',
                values_column='Valor',
                title=f"{chart_title} - Distribuição"
            )
        else:  # Bar chart
            fig = self._plot_manager.create_plot(
                df_plot, 'bar',
                title=f"{chart_title} - {time_frame}",
                labels={'index': time_frame, 'value': 'Valor (R$)'}
            )
        
        st.plotly_chart(fig, use_container_width=True)