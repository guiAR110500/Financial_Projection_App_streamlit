import streamlit as st
import pandas as pd
from typing import Optional
from core.base_classes import BasePage, SessionStateManager
from models.investment import InvestmentItem, PartnerInvestment, FutureInvestment, InvestmentPremises
from services.investment_service import InvestmentService
from utils.plot_manager import PlotlyPlotManager
from config.settings import ConfigManager

class PremissasInvestimentosPage(BasePage):
    """Page for investment premises configuration (Single Responsibility Principle)"""
    
    def __init__(self, state_manager: Optional[SessionStateManager] = None,
                 config_manager: Optional[ConfigManager] = None):
        self._config = config_manager or ConfigManager()
        super().__init__(state_manager)
        self._service = InvestmentService()
    
    @property
    def title(self) -> str:
        return "Premissas Investimentos"
    
    @property
    def icon(self) -> str:
        return "💰"
    
    def _initialize_state(self) -> None:
        """Initialize investment premises in state"""
        default_params = {
            'investimentos_iniciais': [],
            'investimentos_socios': [],
            'investimentos_futuros': []
        }
        
        self._state_manager.ensure_state('premissas_investimentos', default_params)
        
        # Load premises into service
        premises_data = self._state_manager.get_state('premissas_investimentos')
        self._service.load_premises(premises_data)
    
    def _render_content(self) -> None:
        """Render the investment premises content"""
        tabs = st.tabs(["Investimento Inicial", "Investimentos dos Sócios", "Investimentos Futuros"])
        
        with tabs[0]:
            self._render_initial_investments()
        
        with tabs[1]:
            self._render_partner_investments()
        
        with tabs[2]:
            self._render_future_investments()
    
    def _render_initial_investments(self) -> None:
        """Render initial investments section"""
        st.write("### Configuração de Investimentos Iniciais")
        st.write("Defina os itens que compõem o investimento inicial do projeto.")
        
        premises = self._service.get_premises()
        
        if premises and premises.investimentos_iniciais:
            self._display_initial_investments(premises)
        
        self._render_new_investment_form()
    
    def _display_initial_investments(self, premises: InvestmentPremises) -> None:
        """Display current initial investments"""
        st.write("#### Investimentos configurados:")
        
        data = []
        for item in premises.investimentos_iniciais:
            data.append({
                "Descrição": item.descricao,
                "Quantidade": item.quantidade,
                "Valor Unitário": f"R$ {item.valor_unitario:,.2f}",
                "Total": f"R$ {item.total:,.2f}"
            })
        
        df_display = pd.DataFrame(data)
        st.dataframe(df_display, use_container_width=True)
        
        st.metric("Investimento Total", f"R$ {premises.total_investimento_inicial:,.2f}")
        
        if st.button("Remover Todos os Itens", key="remove_initial_investments"):
            premises.clear_initial_investments()
            self._update_state_from_premises(premises)
            st.success("Todos os itens foram removidos.")
            st.rerun()
    
    def _render_new_investment_form(self) -> None:
        """Render form for new investment item"""
        st.write("#### Adicionar Novo Item de Investimento")
        
        with st.form("novo_investimento"):
            descricao = st.text_input("Descrição", key="inv_descricao")
            
            col1, col2 = st.columns(2)
            with col1:
                quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
            with col2:
                valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, 
                                                value=0.0, step=100.0, format="%.2f")
            
            total = quantidade * valor_unitario
            st.write(f"Total para este item: R$ {total:,.2f}")
            
            if st.form_submit_button("Adicionar Item"):
                if descricao and valor_unitario > 0:
                    self._add_initial_investment(descricao, quantidade, valor_unitario)
    
    def _add_initial_investment(self, descricao: str, quantidade: int, valor_unitario: float) -> None:
        """Add new initial investment"""
        item = InvestmentItem(descricao, quantidade, valor_unitario)
        premises = self._service.get_premises()
        premises.add_initial_investment(item)
        self._update_state_from_premises(premises)
        st.success(f"Item '{descricao}' adicionado com sucesso!")
        st.rerun()
    
    def _render_partner_investments(self) -> None:
        """Render partner investments section"""
        st.write("### Investimentos dos Sócios")
        st.write("Configure os aportes de capital dos sócios ao longo do tempo.")
        
        premises = self._service.get_premises()
        
        if premises and premises.investimentos_socios:
            self._display_partner_investments(premises)
        
        self._render_new_partner_form()
    
    def _display_partner_investments(self, premises: InvestmentPremises) -> None:
        """Display current partner investments"""
        st.write("#### Aportes configurados:")
        
        data = []
        for inv in premises.investimentos_socios:
            data.append({
                "Valor": f"R$ {inv.valor:,.2f}",
                "Mês Inflow": inv.mes_inflow,
                "Periodicidade": f"A cada {inv.periodicidade} meses" if inv.periodicidade_ativa else "Única"
            })
        
        df_display = pd.DataFrame(data)
        st.dataframe(df_display, use_container_width=True)
        
        if st.button("Remover Todos os Aportes", key="remove_partner_investments"):
            premises.clear_partner_investments()
            self._update_state_from_premises(premises)
            st.success("Todos os aportes foram removidos.")
            st.rerun()
    
    def _render_new_partner_form(self) -> None:
        """Render form for new partner investment"""
        st.write("#### Adicionar Novo Aporte de Capital")
        
        with st.form("novo_aporte"):
            col1, col2 = st.columns(2)
            with col1:
                valor = st.number_input("Valor (R$)", min_value=0.0, step=1000.0, format="%.2f")
                mes_inflow = st.number_input("Mês Inflow", min_value=0, max_value=59, step=1)
            
            with col2:
                periodicidade_ativa = st.checkbox("Possui Periodicidade?")
                periodicidade = st.number_input("Periodicidade (meses)", min_value=1, 
                                              max_value=12, value=3, step=1)
            
            if st.form_submit_button("Adicionar Aporte"):
                if valor > 0:
                    self._add_partner_investment(valor, mes_inflow, periodicidade_ativa, periodicidade)
    
    def _add_partner_investment(self, valor: float, mes_inflow: int, 
                               periodicidade_ativa: bool, periodicidade: int) -> None:
        """Add new partner investment"""
        inv = PartnerInvestment(valor, mes_inflow, periodicidade_ativa, 
                               periodicidade if periodicidade_ativa else 1)
        premises = self._service.get_premises()
        premises.add_partner_investment(inv)
        self._update_state_from_premises(premises)
        st.success(f"Aporte de R$ {valor:,.2f} adicionado com sucesso!")
        st.rerun()
    
    def _render_future_investments(self) -> None:
        """Render future investments section"""
        st.write("### Investimentos Futuros")
        st.write("Configure investimentos futuros para ampliações e melhorias.")
        
        premises = self._service.get_premises()
        
        if premises and premises.investimentos_futuros:
            self._display_future_investments(premises)
        
        self._render_new_future_form()
    
    def _display_future_investments(self, premises: InvestmentPremises) -> None:
        """Display current future investments"""
        st.write("#### Investimentos futuros configurados:")
        
        data = []
        for fut in premises.investimentos_futuros:
            data.append({
                "Descrição": fut.descricao,
                "Valor": f"R$ {fut.valor:,.2f}",
                "Mês Outflow": fut.mes_outflow,
                "Periodicidade": f"A cada {fut.periodicidade} meses" if fut.periodicidade_ativa else "Única"
            })
        
        df_display = pd.DataFrame(data)
        st.dataframe(df_display, use_container_width=True)
        
        if st.button("Remover Todos os Investimentos Futuros", key="remove_future_investments"):
            premises.clear_future_investments()
            self._update_state_from_premises(premises)
            st.success("Todos os investimentos futuros foram removidos.")
            st.rerun()
    
    def _render_new_future_form(self) -> None:
        """Render form for new future investment"""
        st.write("#### Adicionar Novo Investimento Futuro")
        
        with st.form("novo_inv_futuro"):
            descricao = st.text_input("Descrição do Investimento")
            
            col1, col2 = st.columns(2)
            with col1:
                valor = st.number_input("Valor (R$)", min_value=0.0, step=1000.0, format="%.2f")
                mes_outflow = st.number_input("Mês Outflow", min_value=0, max_value=59, step=1)
            
            with col2:
                periodicidade_ativa = st.checkbox("Possui Periodicidade?")
                periodicidade = st.number_input("Periodicidade (meses)", min_value=1, 
                                              max_value=12, value=6, step=1)
            
            if st.form_submit_button("Adicionar Investimento Futuro"):
                if descricao and valor > 0:
                    self._add_future_investment(descricao, valor, mes_outflow, 
                                               periodicidade_ativa, periodicidade)
    
    def _add_future_investment(self, descricao: str, valor: float, mes_outflow: int,
                              periodicidade_ativa: bool, periodicidade: int) -> None:
        """Add new future investment"""
        fut = FutureInvestment(descricao, valor, mes_outflow, periodicidade_ativa,
                              periodicidade if periodicidade_ativa else 1)
        premises = self._service.get_premises()
        premises.add_future_investment(fut)
        self._update_state_from_premises(premises)
        st.success(f"Investimento futuro '{descricao}' adicionado com sucesso!")
        st.rerun()
    
    def _update_state_from_premises(self, premises: InvestmentPremises) -> None:
        """Update session state from premises object"""
        state_data = {
            'investimentos_iniciais': [
                {'descricao': item.descricao, 'quantidade': item.quantidade, 
                 'valor_unitario': item.valor_unitario}
                for item in premises.investimentos_iniciais
            ],
            'investimentos_socios': [
                {'valor': inv.valor, 'mes_inflow': inv.mes_inflow,
                 'periodicidade_ativa': inv.periodicidade_ativa, 'periodicidade': inv.periodicidade}
                for inv in premises.investimentos_socios
            ],
            'investimentos_futuros': [
                {'descricao': fut.descricao, 'valor': fut.valor, 'mes_outflow': fut.mes_outflow,
                 'periodicidade_ativa': fut.periodicidade_ativa, 'periodicidade': fut.periodicidade}
                for fut in premises.investimentos_futuros
            ]
        }
        self._state_manager.set_state('premissas_investimentos', state_data)


class InvestimentosVisualizationPage(BasePage):
    """Page for investment visualization (Single Responsibility Principle)"""
    
    def __init__(self, state_manager: Optional[SessionStateManager] = None,
                 config_manager: Optional[ConfigManager] = None,
                 plot_manager: Optional[PlotlyPlotManager] = None):
        self._config = config_manager or ConfigManager()
        self._plot_manager = plot_manager or PlotlyPlotManager()
        super().__init__(state_manager)
        self._service = InvestmentService()
    
    @property
    def title(self) -> str:
        return "Investimentos"
    
    @property
    def icon(self) -> str:
        return "💰"
    
    def _initialize_state(self) -> None:
        """Initialize investment visualization state"""
        if 'premissas_investimentos' in self._state_manager.get_state('', {}):
            premises_data = self._state_manager.get_state('premissas_investimentos')
            self._service.load_premises(premises_data)
    
    def _render_content(self) -> None:
        """Render investment visualization content"""
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
        
        # Get and display data
        df_display = self._service.get_grouped_flow(time_frame)
        
        if df_display is not None:
            self._display_investment_flow(df_display, time_frame, plot_type)
            self._display_investment_details()
    
    def _validate_premises(self) -> bool:
        """Validate that premises exist"""
        if 'premissas_investimentos' not in self._state_manager.get_state('', {}):
            st.error("Premissas de investimentos não definidas. Por favor, defina as premissas na página 'Premissas Investimentos'.")
            return False
        
        premises = self._service.get_premises()
        if not premises or (not premises.investimentos_iniciais and 
                           not premises.investimentos_socios and 
                           not premises.investimentos_futuros):
            st.warning("Nenhum investimento configurado. Utilize a página 'Premissas Investimentos' para adicionar itens.")
            return False
        
        return True
    
    def _display_investment_flow(self, df_display: pd.DataFrame, time_frame: str, plot_type: str) -> None:
        """Display investment flow data and chart"""
        st.write("### Fluxo de Investimentos")
        st.dataframe(df_display.style.format("{:.2f}"), use_container_width=True)
        
        # Category selection
        categorias = df_display.index.tolist()
        selected_categories = st.multiselect(
            "Selecione as categorias para visualizar", 
            categorias,
            default=["Total"]
        )
        
        if not selected_categories:
            selected_categories = ["Total"]
        
        # Create visualization
        st.write("### Visualização Gráfica")
        self._render_chart(df_display, selected_categories, time_frame, plot_type)
    
    def _render_chart(self, df_display: pd.DataFrame, selected_categories: list, 
                     time_frame: str, plot_type: str) -> None:
        """Render chart based on selected type"""
        df_plot = df_display.loc[selected_categories].T
        
        if plot_type == "Gráfico de Pizza":
            data_pie = {
                'Categoria': selected_categories,
                'Valor': [abs(df_display.loc[cat].sum()) for cat in selected_categories]
            }
            df_pie = pd.DataFrame(data_pie)
            
            fig = self._plot_manager.create_plot(
                df_pie, 'pie',
                values_column='Valor',
                labels_column='Categoria',
                title=f"Distribuição de Investimentos - Total ({time_frame})"
            )
        elif plot_type == "Gráfico de Barras":
            fig = self._plot_manager.create_plot(
                df_plot, 'bar',
                title=f"Fluxo de Investimentos ({time_frame})"
            )
        else:  # Gráfico de Linhas
            fig = self._plot_manager.create_plot(
                df_plot, 'line',
                title=f"Fluxo de Investimentos ({time_frame})"
            )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _display_investment_details(self) -> None:
        """Display detailed investment information"""
        premises = self._service.get_premises()
        
        if premises and premises.investimentos_iniciais:
            with st.expander("Detalhes do Investimento Inicial"):
                st.write("#### Itens do Investimento Inicial")
                
                data = []
                for item in premises.investimentos_iniciais:
                    data.append({
                        "Descrição": item.descricao,
                        "Quantidade": item.quantidade,
                        "Valor Unitário": item.valor_unitario,
                        "Total": item.total
                    })
                
                df = pd.DataFrame(data)
                
                st.dataframe(df.style.format({
                    "Valor Unitário": "R$ {:.2f}",
                    "Total": "R$ {:.2f}"
                }), use_container_width=True)
                
                st.metric("Investimento Inicial Total", f"R$ {premises.total_investimento_inicial:,.2f}")