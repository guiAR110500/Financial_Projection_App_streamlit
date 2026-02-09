# Import remaining pages from original file (to be gradually migrated)
import sys

import streamlit as st

from config.settings import ConfigManager
from container import container
from core.base_classes import SessionStateManager
from pages.despesas_pages import DespesasAdministrativasPage, PremissasDespesasPage

# Import all refactored pages
from pages.investment_pages import (
    InvestimentosVisualizationPage,
    PremissasInvestimentosPage,
)
from pages.receitas_pages import PremissasReceitasPage, ReceitasVisualizationPage
from utils.ui_components import load_css

sys.path.append('.')
from DashVita2 import (
    ComissaoVendas,
    CustosTecnologia,
    Equipe,
    MetasColabs,
    PaginaAcompanhamento,
    PremissasComissao,
    PremissasProjeções,
    PremissasTributos,
    ProjeçãodeFluxodeCaixa,
    ProjeçãoDRE,
    ProjeçãoInicial,
    Tributos,
)


class Application:
    """Main application class following SOLID principles"""

    def __init__(self):
        # Get dependencies from container
        self.config_manager: ConfigManager = container.get('config_manager')  # type: ignore[assignment]
        self.state_manager: SessionStateManager = container.get('state_manager')  # type: ignore[assignment]

        # Initialize pages with dependency injection
        self._initialize_pages()
        self._initialize_navigation()

    def _initialize_pages(self) -> None:
        """Initialize all application pages"""
        # Create pages using dependency injection
        self.page_groups = {
            "Página Inicial": [
                PaginaAcompanhamento(),
                MetasColabs(),
                ProjeçãoInicial()
            ],
            "Investimentos": [
                container.create_with_dependencies(PremissasInvestimentosPage),
                container.create_with_dependencies(InvestimentosVisualizationPage)
            ],
            "Despesas": [
                container.create_with_dependencies(PremissasDespesasPage),
                container.create_with_dependencies(DespesasAdministrativasPage),
                Equipe(),
                CustosTecnologia()
            ],
            "Receitas": [
                container.create_with_dependencies(PremissasReceitasPage),
                container.create_with_dependencies(ReceitasVisualizationPage)
            ],
            "Comissões": [
                PremissasComissao(),
                ComissaoVendas()
            ],
            "Tributos": [
                PremissasTributos(),
                Tributos()
            ],
            "Projeções": [
                PremissasProjeções(),
                ProjeçãodeFluxodeCaixa(),
                ProjeçãoDRE()
            ]
        }

        # Update page configuration
        page_config = self.config_manager.get_page_config()
        for group_name, pages in self.page_groups.items():
            page_config.add_group(group_name, pages)

    def _initialize_navigation(self) -> None:
        """Initialize navigation state"""
        if 'current_group' not in st.session_state:
            st.session_state.current_group = list(self.page_groups.keys())[0]

        if 'current_page' not in st.session_state:
            current_group = st.session_state.current_group
            if current_group in self.page_groups and self.page_groups[current_group]:
                st.session_state.current_page = self.page_groups[current_group][0].title

    def render_sidebar(self) -> None:
        """Render the sidebar navigation"""
        settings = self.config_manager.get_app_settings()

        # Display logo
        try:
            st.sidebar.image(settings.logo_path, width=300)
        except Exception:
            pass  # Logo not found, continue without it

        # Navigation header
        st.sidebar.markdown("""
        <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 15px'>
            <h2 style='text-align: center; color: #262730; margin: 0px'>Navegação</h2>
        </div>
        """, unsafe_allow_html=True)

        # Initialize navigation state
        if 'nav_view' not in st.session_state:
            st.session_state.nav_view = "groups"

        # Render navigation
        if st.session_state.nav_view == "pages":
            self._render_page_navigation()
        else:
            self._render_group_navigation()

        # Footer
        st.sidebar.markdown("<hr style='margin-top: 15px;'>", unsafe_allow_html=True)
        st.sidebar.markdown(
            f"<div style='text-align: center; color: #888888; font-size: 12px'>"
            f"{settings.app_title} {settings.app_version}</div>",
            unsafe_allow_html=True
        )

    def _render_group_navigation(self) -> None:
        """Render group-based navigation"""
        st.sidebar.markdown("#### Selecione um grupo:")

        for group_name in self.page_groups.keys():
            if st.sidebar.button(f"📁 {group_name}", key=f"group_{group_name}",
                               use_container_width=True):
                st.session_state.current_group = group_name
                st.session_state.nav_view = "pages"
                if self.page_groups[group_name]:
                    st.session_state.current_page = self.page_groups[group_name][0].title

    def _render_page_navigation(self) -> None:
        """Render page-based navigation"""
        if st.sidebar.button("← Voltar para Grupos", use_container_width=True):
            st.session_state.nav_view = "groups"

        st.sidebar.markdown("<hr>", unsafe_allow_html=True)

        current_group = st.session_state.current_group
        st.sidebar.markdown(f"#### Páginas em {current_group}:")

        pages_in_group = self.page_groups.get(current_group, [])
        for page in pages_in_group:
            page_title = f"{page.icon} {page.title}"
            if st.sidebar.button(page_title, key=f"page_{page.title}",
                               use_container_width=True):
                st.session_state.current_page = page.title

    def render_current_page(self) -> None:
        """Render the currently selected page"""
        current_group = st.session_state.get('current_group')
        current_page = st.session_state.get('current_page')

        if current_group and current_group in self.page_groups:
            for page in self.page_groups[current_group]:
                if page.title == current_page:
                    page.render()
                    break

    def run(self) -> None:
        """Run the application"""
        # Load CSS
        load_css()

        # Render sidebar
        self.render_sidebar()

        # Render current page
        self.render_current_page()


def main():
    """Main entry point"""
    # Configure Streamlit page
    st.set_page_config(
        page_title="TuaVita Dashboard",
        page_icon="📊",
        layout="wide"
    )

    # Create and run application
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
