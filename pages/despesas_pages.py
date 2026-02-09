import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
from core.base_classes import BasePage, SessionStateManager
from models.despesas import DespesasPremises, EquipeMembro, PrestadorServico, ModoCalculo, ModoEnergia, Equipamento
from services.despesas_service import DespesasService
from utils.plot_manager import PlotlyPlotManager
from config.settings import ConfigManager

class PremissasDespesasPage(BasePage):
    """Page for expenses premises configuration"""
    
    def __init__(self, state_manager: Optional[SessionStateManager] = None,
                 config_manager: Optional[ConfigManager] = None):
        self._config = config_manager or ConfigManager()
        self._service = DespesasService()
        super().__init__(state_manager)
    
    @property
    def title(self) -> str:
        return "Premissas Despesas"
    
    @property
    def icon(self) -> str:
        return "📝"
    
    def _initialize_state(self) -> None:
        """Initialize expenses premises in state"""
        default_params = {
            # General parameters
            'ipca_medio_anual': 4.5,
            'igpm_medio_anual': 5.0,
            'modo_calculo': 'Percentual',
            'budget_mensal': 30000.0,
            'mes_inicio_despesas': 0,
            
            # Energy mode
            'modo_energia': 'Constante',
            'consumo_mensal_kwh': 2000.0,
            
            # Administrative expenses (nominal values)
            'aluguel': 8000.0,
            'condominio': 1500.0,
            'iptu': 1000.0,
            'internet': 350.0,
            'material_escritorio': 800.0,
            'treinamentos': 2000.0,
            'manutencao_conservacao': 1200.0,
            'seguros_funcionarios': 2000.0,
            'licencas_telefonia': 500.0,
            'licencas_crm': 1000.0,
            'telefonica': 500.0,
            
            # Percentages for percentage mode
            'perc_agua_luz': 5.0,
            'perc_aluguel_condominio_iptu': 35.0,
            'perc_internet': 1.2,
            'perc_material_escritorio': 2.7,
            'perc_treinamentos': 6.7,
            'perc_manutencao_conservacao': 4.0,
            'perc_seguros_funcionarios': 6.7,
            'perc_licencas_telefonia': 1.7,
            'perc_licencas_crm': 3.3,
            'perc_telefonica': 1.7,
            
            # Team parameters
            'equipe_modo_calculo': 'Nominal',
            'budget_equipe_propria': 50000.0,
            'budget_terceiros': 10000.0,
            'encargos_sociais_perc': 68.0,
            'vale_alimentacao': 30.0,
            'vale_transporte': 12.0,
            'roles_com_beneficios': [],
            
            # Team and service providers
            'equipe_propria': [],
            'terceiros': [],
            
            # Bonus parameters
            'benchmark_anual_bonus': 10.0,
            'lucro_liquido_inicial': 100000.0,
            'crescimento_lucro': 15.0,
            
            # Technology costs
            'desenvolvimento_ferramenta': 0.0,
            'manutencao_ferramenta': 0.0,
            'inovacao': 0.0,
            'licencas_software': 2513.0,
            'equipamentos': [],
        }
        
        self._state_manager.ensure_state('premissas_despesas', default_params)
        
        # Load premises into service
        premises_data = self._state_manager.get_state('premissas_despesas')
        self._service.load_premises(premises_data)
    
    def _render_content(self) -> None:
        """Render the expenses premises content"""
        tabs = st.tabs(["Configurações Gerais", "Despesas Administrativas", "Equipe", "Tecnologia", "Reajustes"])
        
        with tabs[0]:
            self._render_general_config()
        
        with tabs[1]:
            self._render_administrative_expenses()
        
        with tabs[2]:
            self._render_team_config()
        
        with tabs[3]:
            self._render_technology_costs()
        
        with tabs[4]:
            self._render_adjustments()
    
    def _render_general_config(self) -> None:
        """Render general configuration"""
        st.write("### Configurações Gerais")
        st.write("Defina os parâmetros gerais para cálculo das despesas.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._update_state('ipca_medio_anual', st.slider(
                "IPCA Médio Anual (%)",
                min_value=0.0,
                max_value=20.0,
                value=self._get_state('ipca_medio_anual'),
                step=0.1,
                format="%.1f",
                help="Taxa média de inflação anual utilizada para correção monetária."
            ))
            
            self._update_state('modo_calculo', st.selectbox(
                "Modo de Cálculo",
                ["Percentual", "Nominal"],
                index=0 if self._get_state('modo_calculo') == "Percentual" else 1,
                help="Escolha entre cálculo percentual ou nominal."
            ))
            
            if self._get_state('modo_calculo') == "Percentual":
                self._update_state('budget_mensal', st.slider(
                    "Orçamento Mensal Total (R$)",
                    min_value=1000.0,
                    max_value=100000.0,
                    value=self._get_state('budget_mensal'),
                    step=1000.0,
                    format="%.2f",
                    help="Orçamento mensal total disponível para despesas administrativas."
                ))
        
        with col2:
            self._update_state('igpm_medio_anual', st.slider(
                "IGP-M Médio Anual (%)",
                min_value=0.0,
                max_value=20.0,
                value=self._get_state('igpm_medio_anual'),
                step=0.1,
                format="%.1f",
                help="Taxa média do IGP-M anual utilizada para correção monetária."
            ))
            
            self._update_state('modo_energia', st.selectbox(
                "Modo de Cálculo de Energia",
                ["Constante", "Estressado", "Extremamente Conservador"],
                index=["Constante", "Estressado", "Extremamente Conservador"].index(self._get_state('modo_energia')),
                help="Escolha o modo de cálculo para energia elétrica."
            ))
    
    def _render_administrative_expenses(self) -> None:
        """Render administrative expenses configuration"""
        st.write("### Despesas Administrativas")
        st.write("Defina os valores para cada tipo de despesa administrativa.")
        
        # Month start configuration
        self._update_state('mes_inicio_despesas', st.slider(
            "Mês de Início das Despesas",
            min_value=0,
            max_value=24,
            value=self._get_state('mes_inicio_despesas'),
            step=1,
            help="Mês a partir do qual as despesas administrativas serão aplicadas."
        ))
        
        modo_calculo = self._get_state('modo_calculo')
        
        # Energy costs
        st.write("#### Água e Luz")
        if modo_calculo == "Nominal":
            self._update_state('consumo_mensal_kwh', st.slider(
                "Consumo Mensal (kWh)",
                min_value=0.0,
                max_value=10000.0,
                value=self._get_state('consumo_mensal_kwh'),
                step=100.0,
                format="%.2f",
                help="Consumo mensal de energia elétrica em kWh"
            ))
        else:
            self._update_state('perc_agua_luz', st.slider(
                "Água e Luz (%)",
                min_value=0.0,
                max_value=100.0,
                value=self._get_state('perc_agua_luz'),
                step=0.1,
                format="%.1f",
                help="Percentual do orçamento destinado a água e luz."
            ))
        
        # Rent, condo, IPTU
        st.write("#### Aluguéis, Condomínios e IPTU")
        if modo_calculo == "Nominal":
            col1, col2, col3 = st.columns(3)
            with col1:
                self._update_state('aluguel', st.slider(
                    "Aluguel (R$)",
                    min_value=0.0,
                    max_value=50000.0,
                    value=self._get_state('aluguel'),
                    step=100.0,
                    format="%.2f"
                ))
            with col2:
                self._update_state('condominio', st.slider(
                    "Condomínio (R$)",
                    min_value=0.0,
                    max_value=10000.0,
                    value=self._get_state('condominio'),
                    step=100.0,
                    format="%.2f"
                ))
            with col3:
                self._update_state('iptu', st.slider(
                    "IPTU (R$)",
                    min_value=0.0,
                    max_value=10000.0,
                    value=self._get_state('iptu'),
                    step=100.0,
                    format="%.2f"
                ))
        else:
            self._update_state('perc_aluguel_condominio_iptu', st.slider(
                "Aluguéis, Condomínios e IPTU (%)",
                min_value=0.0,
                max_value=100.0,
                value=self._get_state('perc_aluguel_condominio_iptu'),
                step=0.1,
                format="%.1f"
            ))
        
        # Other expenses
        st.write("#### Outras Despesas")
        self._render_other_expenses(modo_calculo)
        
        # Percentage validation
        if modo_calculo == "Percentual":
            self._validate_percentages()
    
    def _render_other_expenses(self, modo_calculo: str) -> None:
        """Render other expense categories"""
        col1, col2 = st.columns(2)
        
        expenses = [
            ('internet', 'Internet', 5000.0, 'perc_internet'),
            ('material_escritorio', 'Material de Escritório', 5000.0, 'perc_material_escritorio'),
            ('treinamentos', 'Treinamentos', 10000.0, 'perc_treinamentos'),
            ('manutencao_conservacao', 'Manutenção & Conservação', 10000.0, 'perc_manutencao_conservacao'),
        ]
        
        expenses_2 = [
            ('seguros_funcionarios', 'Seguros Funcionários', 10000.0, 'perc_seguros_funcionarios'),
            ('licencas_telefonia', 'Licenças de Telefonia', 5000.0, 'perc_licencas_telefonia'),
            ('licencas_crm', 'Licenças CRM', 10000.0, 'perc_licencas_crm'),
            ('telefonica', 'Telefônica', 5000.0, 'perc_telefonica'),
        ]
        
        with col1:
            for key, label, max_val, perc_key in expenses:
                if modo_calculo == "Nominal":
                    self._update_state(key, st.slider(
                        f"{label} (R$)",
                        min_value=0.0,
                        max_value=max_val,
                        value=self._get_state(key),
                        step=10.0 if max_val <= 5000 else 100.0,
                        format="%.2f"
                    ))
                else:
                    self._update_state(perc_key, st.slider(
                        f"{label} (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=self._get_state(perc_key),
                        step=0.1,
                        format="%.1f"
                    ))
        
        with col2:
            for key, label, max_val, perc_key in expenses_2:
                if modo_calculo == "Nominal":
                    self._update_state(key, st.slider(
                        f"{label} (R$)",
                        min_value=0.0,
                        max_value=max_val,
                        value=self._get_state(key),
                        step=50.0 if 'licenca' in key else 100.0,
                        format="%.2f"
                    ))
                else:
                    self._update_state(perc_key, st.slider(
                        f"{label} (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=self._get_state(perc_key),
                        step=0.1,
                        format="%.1f"
                    ))
    
    def _render_team_config(self) -> None:
        """Render team configuration"""
        st.write("### Configurações da Equipe")
        st.write("Defina os parâmetros relacionados à equipe da empresa.")
        
        # Team calculation mode
        equipe_modo = st.selectbox(
            "Modo de Cálculo da Equipe",
            ["Percentual", "Nominal"],
            index=0 if self._get_state('equipe_modo_calculo') == "Percentual" else 1
        )
        self._update_state('equipe_modo_calculo', equipe_modo)
        
        # Budget configuration for percentage mode
        if equipe_modo == "Percentual":
            col1, col2 = st.columns(2)
            with col1:
                self._update_state('budget_equipe_propria', st.slider(
                    "Budget Equipe Própria (R$)",
                    min_value=0.0,
                    max_value=200000.0,
                    value=self._get_state('budget_equipe_propria'),
                    step=1000.0,
                    format="%.2f"
                ))
            with col2:
                self._update_state('budget_terceiros', st.slider(
                    "Budget Terceiros (R$)",
                    min_value=0.0,
                    max_value=100000.0,
                    value=self._get_state('budget_terceiros'),
                    step=1000.0,
                    format="%.2f"
                ))
        
        # Team members management
        self._render_team_members()
        
        # Service providers management
        self._render_service_providers()
        
        # Social charges and benefits
        self._render_benefits_config()
        
        # Profit bonuses
        self._render_bonus_config()
    
    def _render_team_members(self) -> None:
        """Render team members section"""
        st.write("#### Equipe Própria")
        
        equipe = self._get_state('equipe_propria')
        if equipe:
            # Display current team
            df_data = []
            for member in equipe:
                df_data.append({
                    "Cargo": member.get('nome', ''),
                    "Salário (R$)": f"{member.get('salario', 0):,.2f}",
                    "Quantidade": member.get('quantidade', 1),
                    "Comissões": "Sim" if member.get('sujeito_comissoes', False) else "Não",
                    "Aumento Receita": "Sim" if member.get('sujeito_aumento_receita', False) else "Não"
                })
            
            df_team = pd.DataFrame(df_data)
            st.dataframe(df_team, use_container_width=True)
        
        # Add new team member form
        with st.expander("Adicionar Novo Membro da Equipe"):
            self._render_new_team_member_form()
        
        # Remove team members
        if equipe:
            self._render_team_member_removal()
    
    def _render_new_team_member_form(self) -> None:
        """Render form to add new team member"""
        with st.form("novo_membro_equipe"):
            nome = st.selectbox("Cargo", [
                "CEO", "CFO", "Head de Vendas", "SDR", "Closer", 
                "Account Manager", "TI", "Social Media", "Outros"
            ])
            
            if nome == "Outros":
                nome = st.text_input("Nome do Cargo Customizado")
            
            salario = st.number_input("Salário (R$)", min_value=0.0, value=5000.0, step=100.0)
            quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
            
            col1, col2 = st.columns(2)
            with col1:
                sujeito_comissoes = st.checkbox("Sujeito ao Regime de Comissões")
            with col2:
                sujeito_aumento_receita = st.checkbox("Sujeito a Aumento de Receita")
            
            # Role-specific parameters
            extra_params = {}
            if nome == "SDR":
                st.write("##### Parâmetros Específicos para SDR")
                extra_params.update({
                    'taxa_agendamento': st.slider("Taxa de Agendamento (%)", 1.0, 100.0, 30.0),
                    'taxa_comparecimento': st.slider("Taxa de Comparecimento (%)", 1.0, 100.0, 70.0),
                    'estimativa_leads': st.slider("Estimativa de Leads (mensal)", 50, 1000, 200, 50),
                    'capacidade_leads': 750
                })
            elif nome == "Closer":
                st.write("##### Parâmetros Específicos para Closer")
                extra_params.update({
                    'valor_unitario': st.number_input("Valor Unitário Médio (R$)", min_value=10.0, value=2400.0, step=100.0),
                    'taxa_conversao': st.slider("Taxa de Conversão (%)", 1.0, 100.0, 45.0),
                    'taxa_cancelamento': st.slider("Taxa de Cancelamento (%)", 0.0, 100.0, 5.0, 0.5),
                    'periodicidade': st.selectbox("Periodicidade", ["Mensal", "Trimestral", "Semestral", "Anual"]),
                    'fator_aceleracao_crescimento': st.slider("Fator de Aceleração", 0.1, 5.0, 1.0, 0.1),
                    'produtos_por_lead': st.slider("Produtos por Lead", 1, 100, 10, 5),
                    'capacidade_atendimentos': st.number_input("Atendimentos por Closer", 10, 500, 90, 10),
                    'crescimento_vendas': 'Produtividade'
                })
            
            if st.form_submit_button("Adicionar Membro"):
                if nome:
                    member_data = {
                        'nome': nome,
                        'salario': salario,
                        'quantidade': quantidade,
                        'sujeito_comissoes': sujeito_comissoes,
                        'sujeito_aumento_receita': sujeito_aumento_receita,
                        **extra_params
                    }
                    
                    equipe = self._get_state('equipe_propria')
                    equipe.append(member_data)
                    self._update_state('equipe_propria', equipe)
                    
                    st.success(f"Membro {nome} adicionado com sucesso!")
                    st.rerun()
    
    def _render_team_member_removal(self) -> None:
        """Render team member removal section"""
        st.write("#### Remover Membros da Equipe")
        
        equipe = self._get_state('equipe_propria')
        
        col1, col2 = st.columns([3, 1])
        with col1:
            member_names = [member.get('nome', '') for member in equipe]
            selected_member = st.selectbox("Selecione um membro para remover", member_names)
        
        with col2:
            if st.button("Remover Membro"):
                equipe = [m for m in equipe if m.get('nome') != selected_member]
                self._update_state('equipe_propria', equipe)
                st.success(f"Membro {selected_member} removido!")
                st.rerun()
        
        if st.button("Remover Todos os Membros"):
            self._update_state('equipe_propria', [])
            st.success("Todos os membros foram removidos!")
            st.rerun()
    
    def _render_service_providers(self) -> None:
        """Render service providers section"""
        st.write("#### Terceiros - Prestadores de Serviços")
        
        terceiros = self._get_state('terceiros')
        if terceiros:
            # Display current providers
            df_data = []
            for provider in terceiros:
                df_data.append({
                    "Prestador": provider.get('nome', ''),
                    "Valor (R$)": f"{provider.get('valor', 0):,.2f}",
                    "Quantidade": provider.get('quantidade', 1),
                    "Total (R$)": f"{provider.get('valor', 0) * provider.get('quantidade', 1):,.2f}"
                })
            
            df_providers = pd.DataFrame(df_data)
            st.dataframe(df_providers, use_container_width=True)
        else:
            st.info("Nenhum prestador de serviço adicionado.")
        
        # Add new service provider form
        with st.expander("Adicionar Novo Prestador de Serviço"):
            with st.form("novo_prestador"):
                nome = st.text_input("Nome do Prestador de Serviço")
                valor = st.number_input("Valor (R$)", min_value=0.0, value=2000.0, step=100.0)
                quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
                
                if st.form_submit_button("Adicionar Prestador"):
                    if nome:
                        provider_data = {
                            'nome': nome,
                            'valor': valor,
                            'quantidade': quantidade
                        }
                        
                        terceiros = self._get_state('terceiros')
                        terceiros.append(provider_data)
                        self._update_state('terceiros', terceiros)
                        
                        st.success(f"Prestador {nome} adicionado com sucesso!")
                        st.rerun()
        
        # Remove service providers
        if terceiros:
            st.write("##### Remover Prestadores")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                provider_names = [p.get('nome', '') for p in terceiros]
                selected_provider = st.selectbox("Selecione um prestador para remover", provider_names)
            
            with col2:
                if st.button("Remover Prestador"):
                    terceiros = [p for p in terceiros if p.get('nome') != selected_provider]
                    self._update_state('terceiros', terceiros)
                    st.success(f"Prestador {selected_provider} removido!")
                    st.rerun()
    
    def _render_benefits_config(self) -> None:
        """Render benefits configuration"""
        st.write("#### Encargos Sociais e Benefícios")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._update_state('encargos_sociais_perc', st.slider(
                "Encargos Sociais (%)",
                min_value=0.0,
                max_value=100.0,
                value=self._get_state('encargos_sociais_perc'),
                step=1.0,
                format="%.1f"
            ))
            
            self._update_state('vale_alimentacao', st.slider(
                "Vale Alimentação (R$/dia)",
                min_value=0.0,
                max_value=100.0,
                value=self._get_state('vale_alimentacao'),
                step=1.0,
                format="%.2f"
            ))
        
        with col2:
            self._update_state('vale_transporte', st.slider(
                "Vale Transporte (R$/dia)",
                min_value=0.0,
                max_value=50.0,
                value=self._get_state('vale_transporte'),
                step=0.5,
                format="%.2f"
            ))
        
        # Roles with benefits
        equipe = self._get_state('equipe_propria')
        if equipe:
            role_names = [member.get('nome', '') for member in equipe]
            current_roles_with_benefits = self._get_state('roles_com_beneficios')
            
            selected_roles = st.multiselect(
                "Cargos que receberão benefícios:",
                options=role_names,
                default=[role for role in current_roles_with_benefits if role in role_names]
            )
            
            self._update_state('roles_com_beneficios', selected_roles)
    
    def _render_bonus_config(self) -> None:
        """Render bonus configuration"""
        st.write("#### Bônus dos Lucros")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._update_state('benchmark_anual_bonus', st.slider(
                "Benchmark Anual para Bônus (%)",
                min_value=0.0,
                max_value=50.0,
                value=self._get_state('benchmark_anual_bonus'),
                step=0.5,
                format="%.1f"
            ))
            
            self._update_state('lucro_liquido_inicial', st.slider(
                "Lucro Líquido Inicial (R$)",
                min_value=0.0,
                max_value=1000000.0,
                value=self._get_state('lucro_liquido_inicial'),
                step=10000.0,
                format="%.2f"
            ))
        
        with col2:
            self._update_state('crescimento_lucro', st.slider(
                "Crescimento Anual do Lucro (%)",
                min_value=0.0,
                max_value=100.0,
                value=self._get_state('crescimento_lucro'),
                step=1.0,
                format="%.1f"
            ))
    
    def _render_technology_costs(self) -> None:
        """Render technology costs configuration"""
        st.write("### Custos de Tecnologia")
        st.write("Defina os valores para os custos relacionados à tecnologia.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._update_state('desenvolvimento_ferramenta', st.slider(
                "Desenvolvimento da Ferramenta (R$)",
                min_value=0.0,
                max_value=50000.0,
                value=self._get_state('desenvolvimento_ferramenta'),
                step=1000.0,
                format="%.2f"
            ))
            
            self._update_state('manutencao_ferramenta', st.slider(
                "Manutenção da Ferramenta (R$)",
                min_value=0.0,
                max_value=20000.0,
                value=self._get_state('manutencao_ferramenta'),
                step=500.0,
                format="%.2f"
            ))
        
        with col2:
            self._update_state('inovacao', st.slider(
                "Inovação (R$)",
                min_value=0.0,
                max_value=30000.0,
                value=self._get_state('inovacao'),
                step=1000.0,
                format="%.2f"
            ))
            
            self._update_state('licencas_software', st.slider(
                "Licenças de Software (R$)",
                min_value=0.0,
                max_value=10000.0,
                value=self._get_state('licencas_software'),
                step=100.0,
                format="%.2f"
            ))
        
        # Equipment management (simplified)
        st.write("#### Equipamentos")
        equipamentos = self._get_state('equipamentos')
        
        if equipamentos:
            st.write(f"Total de equipamentos cadastrados: {len(equipamentos)}")
        else:
            st.info("Nenhum equipamento cadastrado.")
    
    def _render_adjustments(self) -> None:
        """Render adjustment configuration"""
        st.write("### Reajustes")
        st.write("Configure os reajustes aplicados às despesas.")
        
        st.info("Configuração de reajustes será implementada em versão futura.")
    
    def _validate_percentages(self) -> None:
        """Validate percentage mode totals"""
        total_perc = (
            self._get_state('perc_agua_luz') +
            self._get_state('perc_aluguel_condominio_iptu') +
            self._get_state('perc_internet') +
            self._get_state('perc_material_escritorio') +
            self._get_state('perc_treinamentos') +
            self._get_state('perc_manutencao_conservacao') +
            self._get_state('perc_seguros_funcionarios') +
            self._get_state('perc_licencas_telefonia') +
            self._get_state('perc_licencas_crm') +
            self._get_state('perc_telefonica')
        )
        
        st.write(f"Soma dos percentuais: {total_perc:.1f}%")
        
        if abs(total_perc - 100.0) > 0.1:
            st.warning("⚠️ A soma dos percentuais deve ser igual a 100%.")
        else:
            st.success("✅ Percentuais balanceados corretamente.")
    
    def _get_state(self, key: str) -> Any:
        """Get value from premises state"""
        premises = self._state_manager.get_state('premissas_despesas')
        return premises.get(key)
    
    def _update_state(self, key: str, value: Any) -> None:
        """Update value in premises state"""
        premises = self._state_manager.get_state('premissas_despesas')
        premises[key] = value
        self._state_manager.set_state('premissas_despesas', premises)
        # Reload premises into service
        self._service.load_premises(premises)


class DespesasAdministrativasPage(BasePage):
    """Page for administrative expenses visualization"""
    
    def __init__(self, state_manager: Optional[SessionStateManager] = None,
                 config_manager: Optional[ConfigManager] = None,
                 plot_manager: Optional[PlotlyPlotManager] = None):
        self._config = config_manager or ConfigManager()
        self._plot_manager = plot_manager or PlotlyPlotManager()
        self._service = DespesasService()
        super().__init__(state_manager)
    
    @property
    def title(self) -> str:
        return "Despesas Administrativas"
    
    @property
    def icon(self) -> str:
        return "📊"
    
    def _initialize_state(self) -> None:
        """Initialize visualization state"""
        premises_data = self._state_manager.get_state('premissas_despesas')
        if premises_data is not None:
            self._service.load_premises(premises_data)
    
    def _render_content(self) -> None:
        """Render administrative expenses visualization"""
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
        
        # Calculate expenses
        result = self._service.calculate_expenses(60)
        
        if result.get('success'):
            self._display_expenses_analysis(result, time_frame, plot_type)
        else:
            st.error(f"Erro no cálculo: {result.get('error', 'Erro desconhecido')}")
    
    def _validate_premises(self) -> bool:
        """Validate that premises exist"""
        if self._state_manager.get_state('premissas_despesas') is None:
            st.error("Premissas de despesas não definidas. Configure as premissas na página 'Premissas Despesas'.")
            return False
        return True
    
    def _display_expenses_analysis(self, result: Dict[str, Any], time_frame: str, plot_type: str) -> None:
        """Display comprehensive expenses analysis"""
        st.write("### Análise de Despesas")
        
        # Tabs for different expense categories
        tab1, tab2, tab3 = st.tabs(["Despesas Administrativas", "Custos de Equipe", "Custos de Tecnologia"])
        
        with tab1:
            self._display_admin_expenses(result['despesas_administrativas'], time_frame, plot_type)
        
        with tab2:
            self._display_team_costs(result['custos_equipe'], time_frame, plot_type)
        
        with tab3:
            self._display_technology_costs(result['custos_tecnologia'], time_frame, plot_type)
        
        # Summary metrics
        self._display_summary_metrics(result)
    
    def _display_admin_expenses(self, df_admin: pd.DataFrame, time_frame: str, plot_type: str) -> None:
        """Display administrative expenses"""
        st.write("#### Despesas Administrativas")
        
        # Convert to selected time frame
        df_display = self._convert_timeframe(df_admin, time_frame)
        
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
            self._create_expense_chart(df_display, selected_categories, time_frame, plot_type, "Despesas Administrativas")
    
    def _display_team_costs(self, df_team: pd.DataFrame, time_frame: str, plot_type: str) -> None:
        """Display team costs"""
        st.write("#### Custos de Equipe")
        
        if df_team.empty:
            st.info("Nenhum custo de equipe calculado.")
            return
        
        # Convert to selected time frame for multi-index dataframe
        df_display = self._convert_multiindex_timeframe(df_team, time_frame)
        
        # Show dataframe
        st.dataframe(df_display.style.format("{:.2f}"), use_container_width=True)
        
        # Category selection
        main_categories = df_display.index.get_level_values(0).unique().tolist()
        selected_category = st.selectbox(
            "Selecione uma categoria principal",
            main_categories,
            index=len(main_categories) - 1 if "TOTAL" in main_categories else 0
        )
        
        # Filter by selected category
        category_data = df_display.loc[selected_category]
        if isinstance(category_data, pd.Series):
            category_data = category_data.to_frame().T
        
        self._create_expense_chart(category_data, category_data.index.tolist(), time_frame, plot_type, "Custos de Equipe")
    
    def _display_technology_costs(self, df_tech: pd.DataFrame, time_frame: str, plot_type: str) -> None:
        """Display technology costs"""
        st.write("#### Custos de Tecnologia")
        
        if df_tech.empty:
            st.info("Nenhum custo de tecnologia calculado.")
            return
        
        # Convert to selected time frame
        df_display = self._convert_timeframe(df_tech, time_frame)
        
        # Show dataframe
        st.dataframe(df_display.style.format("{:.2f}"), use_container_width=True)
        
        # Category selection
        categories = df_display.index.tolist()
        selected_categories = st.multiselect(
            "Selecione categorias para visualizar",
            categories,
            default=["Total"] if "Total" in categories else categories[:3],
            key="tech_categories"
        )
        
        if selected_categories:
            self._create_expense_chart(df_display, selected_categories, time_frame, plot_type, "Custos de Tecnologia")
    
    def _display_summary_metrics(self, result: Dict[str, Any]) -> None:
        """Display summary metrics"""
        st.write("### Métricas Resumo")
        
        # Calculate totals for first year (12 months)
        admin_total = result['despesas_administrativas']['Total'][:12].sum() if 'Total' in result['despesas_administrativas'].columns else 0
        
        team_total = 0
        if not result['custos_equipe'].empty:
            team_data = result['custos_equipe']
            if ("TOTAL", "Total Custos de Equipe") in team_data.index:
                team_total = team_data.loc[("TOTAL", "Total Custos de Equipe"), 1:12].sum()
        
        tech_total = result['custos_tecnologia'].loc['Total', :11].sum() if 'Total' in result['custos_tecnologia'].index else 0
        
        total_expenses = admin_total + team_total + tech_total
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Despesas Admin. (12m)", f"R$ {admin_total:,.2f}")
        
        with col2:
            st.metric("Custos Equipe (12m)", f"R$ {team_total:,.2f}")
        
        with col3:
            st.metric("Custos Tecnologia (12m)", f"R$ {tech_total:,.2f}")
        
        with col4:
            st.metric("Total Despesas (12m)", f"R$ {total_expenses:,.2f}")
    
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
    
    def _convert_multiindex_timeframe(self, df: pd.DataFrame, time_frame: str) -> pd.DataFrame:
        """Convert monthly data to selected timeframe for multi-index dataframes"""
        if time_frame == "Mensal":
            return df
        elif time_frame == "Anual":
            years = len(df.columns) // 12
            annual_columns = [f"Ano {i+1}" for i in range(years)]
            df_annual = pd.DataFrame(index=df.index, columns=annual_columns)
            
            for year in range(years):
                start_month = year * 12 + 1
                end_month = min((year + 1) * 12 + 1, len(df.columns) + 1)
                available_cols = [col for col in range(start_month, end_month) if col in df.columns]
                
                if available_cols:
                    df_annual[f"Ano {year+1}"] = df[available_cols].sum(axis=1)
                else:
                    df_annual[f"Ano {year+1}"] = 0
            
            return df_annual
        
        return df
    
    def _create_expense_chart(self, df: pd.DataFrame, categories: List[str], time_frame: str, plot_type: str, chart_title: str) -> None:
        """Create expense visualization chart"""
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