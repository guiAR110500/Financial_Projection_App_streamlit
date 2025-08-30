import pandas as pd
import numpy as np
import random
from typing import Dict, List, Optional, Any
from models.despesas import DespesasPremises, EquipeMembro, PrestadorServico, ModoCalculo, ModoEnergia, IndexType
from core.base_classes import BaseCalculator

class DespesasCalculator(BaseCalculator):
    """Calculator for administrative expenses"""
    
    def __init__(self, premises: DespesasPremises):
        self.premises = premises
    
    def _validate_inputs(self, **kwargs) -> bool:
        """Validate calculation inputs"""
        return self.premises is not None
    
    def _perform_calculation(self, months: int = 60, **kwargs) -> Dict[str, Any]:
        """Calculate administrative expenses for the specified period"""
        try:
            df_despesas = self._generate_expenses_dataframe(months)
            df_equipe = self._generate_team_dataframe(months)
            df_tecnologia = self._generate_technology_dataframe(months)
            
            return {
                'despesas_administrativas': df_despesas,
                'custos_equipe': df_equipe,
                'custos_tecnologia': df_tecnologia,
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }
    
    def _generate_expenses_dataframe(self, months: int) -> pd.DataFrame:
        """Generate administrative expenses dataframe"""
        # Initialize dataframe
        df = pd.DataFrame(index=range(months))
        df.index.name = 'Mês'
        
        # Calculate monthly inflation rates
        ipca_monthly = (1 + self.premises.ipca_medio_anual / 100) ** (1/12) - 1
        igpm_monthly = (1 + self.premises.igpm_medio_anual / 100) ** (1/12) - 1
        
        # Initialize expense arrays
        expenses = {
            'Água, Luz': [],
            'Aluguéis, Condomínios e IPTU': [],
            'Internet': [],
            'Material de Escritório': [],
            'Treinamentos': [],
            'Manutenção & Conservação': [],
            'Seguros Funcionarios': [],
            'Licenças de Telefonia': [],
            'Licenças CRM': [],
            'Telefônica': []
        }
        
        for month in range(months):
            # Apply start month filter
            if month < self.premises.mes_inicio_despesas:
                for expense_name in expenses:
                    expenses[expense_name].append(0.0)
                continue
            
            if self.premises.modo_calculo == ModoCalculo.PERCENTUAL:
                # Calculate based on budget percentages
                budget = self._apply_inflation_to_budget(month, self.premises.budget_mensal, ipca_monthly)
                
                expenses['Água, Luz'].append(budget * self.premises.perc_agua_luz / 100)
                expenses['Aluguéis, Condomínios e IPTU'].append(budget * self.premises.perc_aluguel_condominio_iptu / 100)
                expenses['Internet'].append(budget * self.premises.perc_internet / 100)
                expenses['Material de Escritório'].append(budget * self.premises.perc_material_escritorio / 100)
                expenses['Treinamentos'].append(budget * self.premises.perc_treinamentos / 100)
                expenses['Manutenção & Conservação'].append(budget * self.premises.perc_manutencao_conservacao / 100)
                expenses['Seguros Funcionarios'].append(budget * self.premises.perc_seguros_funcionarios / 100)
                expenses['Licenças de Telefonia'].append(budget * self.premises.perc_licencas_telefonia / 100)
                expenses['Licenças CRM'].append(budget * self.premises.perc_licencas_crm / 100)
                expenses['Telefônica'].append(budget * self.premises.perc_telefonica / 100)
            else:
                # Calculate based on nominal values with inflation
                base_values = {
                    'Água, Luz': self.premises.consumo_mensal_kwh,
                    'Aluguéis, Condomínios e IPTU': self.premises.aluguel + self.premises.condominio + self.premises.iptu,
                    'Internet': self.premises.internet,
                    'Material de Escritório': self.premises.material_escritorio,
                    'Treinamentos': self.premises.treinamentos,
                    'Manutenção & Conservação': self.premises.manutencao_conservacao,
                    'Seguros Funcionarios': self.premises.seguros_funcionarios,
                    'Licenças de Telefonia': self.premises.licencas_telefonia,
                    'Licenças CRM': self.premises.licencas_crm,
                    'Telefônica': self.premises.telefonica
                }
                
                for expense_name, base_value in base_values.items():
                    inflated_value = self._apply_inflation(base_value, month, ipca_monthly)
                    
                    # Special handling for energy costs
                    if expense_name == 'Água, Luz':
                        inflated_value = self._calculate_energy_cost(inflated_value, month, self.premises.modo_energia)
                    
                    expenses[expense_name].append(inflated_value)
        
        # Add to dataframe
        for expense_name, values in expenses.items():
            df[expense_name] = values
        
        # Calculate total
        df['Total'] = df.sum(axis=1)
        
        return df
    
    def _generate_team_dataframe(self, months: int) -> pd.DataFrame:
        """Generate team costs dataframe"""
        # Create index structure
        indices = []
        
        # Add team member salaries
        for member in self.premises.equipe_propria:
            indices.append(("Equipe Própria", f"Salário {member.nome}"))
        
        # Add fixed categories
        indices.append(("Encargos Sociais", "Encargos Sociais"))
        indices.append(("Despesas com Alimentação e Transporte", "Alimentação e Transporte"))
        
        # Add service providers
        for provider in self.premises.terceiros:
            indices.append(("Terceiros - Prestadores de Serviços", provider.nome))
        
        # Add bonuses
        for member in self.premises.equipe_propria:
            indices.append(("Bônus dos Lucros", f"Bônus {member.nome}"))
        
        indices.append(("TOTAL", "Total Custos de Equipe"))
        
        # Create dataframe
        idx = pd.MultiIndex.from_tuples(indices)
        df = pd.DataFrame(0.0, index=idx, columns=range(1, months + 1))
        
        # Calculate inflation factors
        ipca_monthly = (1 + self.premises.ipca_medio_anual / 100) ** (1/12) - 1
        
        for month in range(1, months + 1):
            month_idx = month - 1
            inflation_factor = (1 + ipca_monthly) ** month_idx
            
            team_total = 0
            
            # Calculate team member costs
            for member in self.premises.equipe_propria:
                salary_cost = self._calculate_member_salary_cost(member, inflation_factor)
                df.loc[("Equipe Própria", f"Salário {member.nome}"), month] = salary_cost
                team_total += salary_cost
            
            # Calculate social security charges
            social_charges = team_total * (self.premises.encargos_sociais_perc / 100)
            df.loc[("Encargos Sociais", "Encargos Sociais"), month] = social_charges
            
            # Calculate benefits
            benefits_total = self._calculate_benefits(inflation_factor)
            df.loc[("Despesas com Alimentação e Transporte", "Alimentação e Transporte"), month] = benefits_total
            
            # Calculate service provider costs
            for provider in self.premises.terceiros:
                provider_cost = self._calculate_provider_cost(provider, inflation_factor)
                df.loc[("Terceiros - Prestadores de Serviços", provider.nome), month] = provider_cost
            
            # Calculate bonuses (only in January after year 1)
            if month > 12 and month % 12 == 1:
                for member in self.premises.equipe_propria:
                    bonus = self._calculate_bonus(member, month)
                    df.loc[("Bônus dos Lucros", f"Bônus {member.nome}"), month] = bonus
            
            # Calculate total
            monthly_total = 0
            for idx in df.index:
                if idx[0] != "TOTAL":
                    monthly_total += df.loc[idx, month]
            df.loc[("TOTAL", "Total Custos de Equipe"), month] = monthly_total
        
        return df
    
    def _generate_technology_dataframe(self, months: int) -> pd.DataFrame:
        """Generate technology costs dataframe"""
        categories = [
            "Desenvolvimento da ferramenta",
            "Manutenção da ferramenta", 
            "Inovação",
            "Licenças de software",
            "Aquisição de Equipamentos",
            "Depreciação de Equipamentos",
            "Total"
        ]
        
        df = pd.DataFrame(0.0, index=categories, columns=range(months))
        
        # Base values
        base_values = {
            "Desenvolvimento da ferramenta": self.premises.desenvolvimento_ferramenta,
            "Manutenção da ferramenta": self.premises.manutencao_ferramenta,
            "Inovação": self.premises.inovacao,
            "Licenças de software": self.premises.licencas_software
        }
        
        ipca_monthly = (1 + self.premises.ipca_medio_anual / 100) ** (1/12) - 1
        
        for month in range(months):
            inflation_factor = (1 + ipca_monthly) ** month
            
            # Basic technology costs with inflation
            for category, base_value in base_values.items():
                df.loc[category, month] = base_value * inflation_factor
            
            # Equipment acquisition costs
            equipment_cost = 0
            for equipment in self.premises.equipamentos:
                if month == equipment.mes_aquisicao:
                    equipment_cost += equipment.valor_total
            df.loc["Aquisição de Equipamentos", month] = equipment_cost
            
            # Equipment depreciation
            depreciation = self._calculate_equipment_depreciation(month)
            df.loc["Depreciação de Equipamentos", month] = depreciation
            
            # Calculate total
            df.loc["Total", month] = df.loc[df.index != 'Total', month].sum()
        
        return df
    
    def _apply_inflation_to_budget(self, month: int, base_budget: float, inflation_rate: float) -> float:
        """Apply inflation to budget"""
        return base_budget * ((1 + inflation_rate) ** month)
    
    def _apply_inflation(self, base_value: float, month: int, inflation_rate: float) -> float:
        """Apply inflation to a base value"""
        return base_value * ((1 + inflation_rate) ** month)
    
    def _calculate_energy_cost(self, base_cost: float, month: int, mode: ModoEnergia) -> float:
        """Calculate energy costs with tariff flags"""
        if mode == ModoEnergia.CONSTANTE:
            return base_cost
        
        # Apply tariff flags based on mode
        if mode == ModoEnergia.EXTREMAMENTE_CONSERVADOR:
            # Always red flag - highest cost
            return base_cost * 1.25
        
        # Stressed mode - random tariff flags
        seed = month // 2  # Same flag for 2 consecutive months
        random.seed(seed)
        flag_multipliers = [1.0, 1.05, 1.15, 1.25]  # Green, Yellow, Red P1, Red P2
        multiplier = random.choice(flag_multipliers)
        
        return base_cost * multiplier
    
    def _calculate_member_salary_cost(self, member: EquipeMembro, inflation_factor: float) -> float:
        """Calculate salary cost for a team member"""
        if self.premises.equipe_modo_calculo == "Percentual":
            budget = self.premises.budget_equipe_propria
            base_salary = (member.percentual / 100 * budget) / member.quantidade if member.quantidade > 0 else 0
        else:
            base_salary = member.salario
        
        return base_salary * member.quantidade * inflation_factor
    
    def _calculate_benefits(self, inflation_factor: float) -> float:
        """Calculate total benefits costs"""
        total_benefits = 0
        working_days = 20
        
        for member in self.premises.equipe_propria:
            if member.nome in self.premises.roles_com_beneficios:
                daily_benefit = (self.premises.vale_alimentacao + self.premises.vale_transporte)
                monthly_benefit = daily_benefit * working_days * member.quantidade
                total_benefits += monthly_benefit * inflation_factor
        
        return total_benefits
    
    def _calculate_provider_cost(self, provider: PrestadorServico, inflation_factor: float) -> float:
        """Calculate cost for a service provider"""
        if self.premises.equipe_modo_calculo == "Percentual":
            budget = self.premises.budget_terceiros
            base_value = (provider.percentual / 100 * budget) / provider.quantidade if provider.quantidade > 0 else 0
        else:
            base_value = provider.valor
        
        return base_value * provider.quantidade * inflation_factor
    
    def _calculate_bonus(self, member: EquipeMembro, month: int) -> float:
        """Calculate bonus for a team member"""
        year = (month - 1) // 12
        
        # Calculate profit growth
        previous_profit = self.premises.lucro_liquido_inicial * ((1 + self.premises.crescimento_lucro / 100) ** (year - 1))
        current_profit = self.premises.lucro_liquido_inicial * ((1 + self.premises.crescimento_lucro / 100) ** year)
        
        growth_percentage = ((current_profit / previous_profit) - 1) * 100
        
        if growth_percentage > self.premises.benchmark_anual_bonus:
            excess_value = current_profit - (previous_profit * (1 + self.premises.benchmark_anual_bonus / 100))
            
            # Get bonus percentage for this member (simplified - would need proper mapping)
            bonus_percentage = 1.0  # Default 1%
            return excess_value * (bonus_percentage / 100)
        
        return 0.0
    
    def _calculate_equipment_depreciation(self, month: int) -> float:
        """Calculate equipment depreciation for a given month"""
        total_depreciation = 0
        
        for equipment in self.premises.equipamentos:
            if month >= equipment.mes_aquisicao:
                months_since_acquisition = month - equipment.mes_aquisicao
                
                if equipment.metodo == "Método da Linha Reta":
                    annual_depreciation = equipment.metodo_params.get('depreciacao_anual', 0)
                    monthly_depreciation = (annual_depreciation / 12) * equipment.quantidade
                    total_depreciation += monthly_depreciation
                
                elif equipment.metodo == "Método da Soma dos Dígitos":
                    year_since_acquisition = (months_since_acquisition // 12) + 1
                    depreciation_years = equipment.metodo_params.get('depreciacao_anos', [])
                    
                    if year_since_acquisition <= len(depreciation_years):
                        annual_depreciation = depreciation_years[year_since_acquisition - 1] * equipment.quantidade
                        monthly_depreciation = annual_depreciation / 12
                        total_depreciation += monthly_depreciation
        
        return total_depreciation

class DespesasService:
    """Service for managing administrative expenses"""
    
    def __init__(self):
        self.premises: Optional[DespesasPremises] = None
    
    def load_premises(self, premises_data: Dict[str, Any]) -> None:
        """Load premises from dictionary data"""
        # Convert dict to DespesasPremises object
        self.premises = self._dict_to_premises(premises_data)
    
    def get_premises(self) -> Optional[DespesasPremises]:
        """Get current premises"""
        return self.premises
    
    def calculate_expenses(self, months: int = 60) -> Dict[str, Any]:
        """Calculate all expenses using the calculator"""
        if not self.premises:
            return {'error': 'Premises not loaded', 'success': False}
        
        calculator = DespesasCalculator(self.premises)
        return calculator.calculate(months=months)
    
    def get_monthly_summary(self, month: int) -> Dict[str, float]:
        """Get expense summary for a specific month"""
        if not self.premises:
            return {}
        
        result = self.calculate_expenses()
        if not result.get('success'):
            return {}
        
        summary = {}
        
        # Administrative expenses
        df_admin = result['despesas_administrativas']
        if month < len(df_admin):
            summary['despesas_administrativas'] = df_admin.loc[month, 'Total']
        
        # Team costs
        df_team = result['custos_equipe']
        if month + 1 in df_team.columns:
            summary['custos_equipe'] = df_team.loc[("TOTAL", "Total Custos de Equipe"), month + 1]
        
        # Technology costs
        df_tech = result['custos_tecnologia']
        if month < len(df_tech.columns):
            summary['custos_tecnologia'] = df_tech.loc["Total", month]
        
        summary['total_despesas'] = sum(summary.values())
        
        return summary
    
    def _dict_to_premises(self, data: Dict[str, Any]) -> DespesasPremises:
        """Convert dictionary to DespesasPremises object"""
        premises = DespesasPremises()
        
        # Basic parameters
        premises.ipca_medio_anual = data.get('ipca_medio_anual', 4.5)
        premises.igpm_medio_anual = data.get('igpm_medio_anual', 5.0)
        premises.modo_calculo = ModoCalculo.PERCENTUAL if data.get('modo_calculo') == 'Percentual' else ModoCalculo.NOMINAL
        premises.budget_mensal = data.get('budget_mensal', 30000.0)
        premises.mes_inicio_despesas = data.get('mes_inicio_despesas', 0)
        
        # Energy parameters
        modo_energia_str = data.get('modo_energia', 'Constante')
        premises.modo_energia = ModoEnergia.CONSTANTE
        if modo_energia_str == 'Estressado':
            premises.modo_energia = ModoEnergia.ESTRESSADO
        elif modo_energia_str == 'Extremamente Conservador':
            premises.modo_energia = ModoEnergia.EXTREMAMENTE_CONSERVADOR
        
        # Administrative expenses
        premises.consumo_mensal_kwh = data.get('consumo_mensal_kwh', 2000.0)
        premises.aluguel = data.get('aluguel', 8000.0)
        premises.condominio = data.get('condominio', 1500.0)
        premises.iptu = data.get('iptu', 1000.0)
        premises.internet = data.get('internet', 350.0)
        premises.material_escritorio = data.get('material_escritorio', 800.0)
        premises.treinamentos = data.get('treinamentos', 2000.0)
        premises.manutencao_conservacao = data.get('manutencao_conservacao', 1200.0)
        premises.seguros_funcionarios = data.get('seguros_funcionarios', 2000.0)
        premises.licencas_telefonia = data.get('licencas_telefonia', 500.0)
        premises.licencas_crm = data.get('licencas_crm', 1000.0)
        premises.telefonica = data.get('telefonica', 500.0)
        
        # Percentages
        premises.perc_agua_luz = data.get('perc_agua_luz', 5.0)
        premises.perc_aluguel_condominio_iptu = data.get('perc_aluguel_condominio_iptu', 35.0)
        premises.perc_internet = data.get('perc_internet', 1.2)
        premises.perc_material_escritorio = data.get('perc_material_escritorio', 2.7)
        premises.perc_treinamentos = data.get('perc_treinamentos', 6.7)
        premises.perc_manutencao_conservacao = data.get('perc_manutencao_conservacao', 4.0)
        premises.perc_seguros_funcionarios = data.get('perc_seguros_funcionarios', 6.7)
        premises.perc_licencas_telefonia = data.get('perc_licencas_telefonia', 1.7)
        premises.perc_licencas_crm = data.get('perc_licencas_crm', 3.3)
        premises.perc_telefonica = data.get('perc_telefonica', 1.7)
        
        # Team parameters
        premises.equipe_modo_calculo = data.get('equipe_modo_calculo', 'Nominal')
        premises.budget_equipe_propria = data.get('budget_equipe_propria', 50000.0)
        premises.budget_terceiros = data.get('budget_terceiros', 10000.0)
        premises.encargos_sociais_perc = data.get('encargos_sociais_perc', 68.0)
        premises.vale_alimentacao = data.get('vale_alimentacao', 30.0)
        premises.vale_transporte = data.get('vale_transporte', 12.0)
        premises.roles_com_beneficios = data.get('roles_com_beneficios', [])
        
        # Team members
        equipe_data = data.get('equipe_propria', [])
        for member_data in equipe_data:
            member = EquipeMembro(
                nome=member_data.get('nome', ''),
                salario=member_data.get('salario', 0.0),
                quantidade=member_data.get('quantidade', 1),
                percentual=member_data.get('percentual', 0.0),
                sujeito_comissoes=member_data.get('sujeito_comissoes', False),
                sujeito_aumento_receita=member_data.get('sujeito_aumento_receita', False)
            )
            premises.equipe_propria.append(member)
        
        # Service providers
        terceiros_data = data.get('terceiros', [])
        for provider_data in terceiros_data:
            provider = PrestadorServico(
                nome=provider_data.get('nome', ''),
                valor=provider_data.get('valor', 0.0),
                quantidade=provider_data.get('quantidade', 1),
                percentual=provider_data.get('percentual', 0.0)
            )
            premises.terceiros.append(provider)
        
        # Bonus parameters
        premises.benchmark_anual_bonus = data.get('benchmark_anual_bonus', 10.0)
        premises.lucro_liquido_inicial = data.get('lucro_liquido_inicial', 100000.0)
        premises.crescimento_lucro = data.get('crescimento_lucro', 15.0)
        
        # Technology costs
        premises.desenvolvimento_ferramenta = data.get('desenvolvimento_ferramenta', 0.0)
        premises.manutencao_ferramenta = data.get('manutencao_ferramenta', 0.0)
        premises.inovacao = data.get('inovacao', 0.0)
        premises.licencas_software = data.get('licencas_software', 2513.0)
        
        return premises