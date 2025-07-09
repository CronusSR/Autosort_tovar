# modern_ui_components.py
"""
🎨 СОВРЕМЕННЫЕ UI КОМПОНЕНТЫ
Минималистичный дизайн для системы анализа складов
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def apply_modern_styles():
    """Применяет современные CSS стили"""
    st.markdown("""
    <style>
    /* ===== ГЛОБАЛЬНЫЕ СТИЛИ ===== */
    .main {
        padding: 0rem 1rem;
    }
    
    /* ===== СОВРЕМЕННАЯ ЦВЕТОВАЯ СХЕМА ===== */
    :root {
        --primary-color: #6366f1;
        --primary-light: #818cf8;
        --primary-dark: #4f46e5;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --bg-color: #f8fafc;
        --card-bg: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* ===== ЗАГОЛОВКИ ===== */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border-color);
    }
    
    .subsection-title {
        font-size: 1.25rem;
        font-weight: 500;
        color: var(--text-primary);
        margin: 1.5rem 0 0.75rem 0;
    }
    
    /* ===== КАРТОЧКИ ===== */
    .metric-card {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
        text-align: center;
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    
    .metric-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }
    
    .metric-card .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }
    
    .metric-card .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* ===== STATUS BADGES ===== */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-critical {
        background-color: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
    }
    
    .status-warning {
        background-color: #fffbeb;
        color: #d97706;
        border: 1px solid #fed7aa;
    }
    
    .status-good {
        background-color: #f0fdf4;
        color: #16a34a;
        border: 1px solid #bbf7d0;
    }
    
    .status-excess {
        background-color: #f0f9ff;
        color: #0284c7;
        border: 1px solid #bae6fd;
    }
    
    /* ===== КНОПКИ ===== */
    .stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: var(--shadow);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-lg);
    }
    
    /* ===== ИНФОРМАЦИОННЫЕ БЛОКИ ===== */
    .info-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-left: 4px solid var(--primary-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-left: 4px solid var(--success-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left: 4px solid var(--warning-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* ===== ТАБЛИЦЫ ===== */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: var(--shadow);
    }
    
    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background-color: var(--card-bg);
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    /* ===== ПРОГРЕСС БАР ===== */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
        border-radius: 9999px;
    }
    
    /* ===== СЕЛЕКТБОКСЫ ===== */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    /* ===== ЧИСЛО ИНПУТЫ ===== */
    .stNumberInput > div > div {
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    /* ===== ФАЙЛ АПЛОАДЕР ===== */
    .stFileUploader > div {
        border-radius: 12px;
        border: 2px dashed var(--border-color);
        background: var(--bg-color);
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        border-color: var(--primary-color);
        background: rgba(99, 102, 241, 0.05);
    }
    
    /* ===== АНИМАЦИИ ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* ===== СЕТКА ===== */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def modern_header(title, subtitle=None, icon="🏭"):
    """Современный заголовок страницы"""
    st.markdown(f"""
    <div class="fade-in">
        <h1 class="main-title">{icon} {title}</h1>
        {f'<p style="color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 2rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def metric_card(label, value, delta=None, delta_color="normal", icon="📊"):
    """Современная карточка метрики"""
    delta_html = ""
    if delta:
        delta_color_map = {
            "normal": "#64748b",
            "positive": "#10b981", 
            "negative": "#ef4444"
        }
        color = delta_color_map.get(delta_color, "#64748b")
        delta_html = f'<p style="color: {color}; font-size: 0.875rem; margin-top: 0.5rem;">{delta}</p>'
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def status_badge(status, text=None):
    """Современный бейдж статуса"""
    status_map = {
        'critical': ('status-critical', '🔴 Критично'),
        'warning': ('status-warning', '🟡 Внимание'), 
        'good': ('status-good', '🟢 Норма'),
        'excess': ('status-excess', '🟠 Избыток'),
        'no_sales': ('status-badge', '⚫ Нет продаж'),
        'empty': ('status-badge', '⚪ Пусто')
    }
    
    css_class, default_text = status_map.get(status, ('status-badge', status))
    display_text = text or default_text
    
    return f'<span class="status-badge {css_class}">{display_text}</span>'

def info_card(content, card_type="info", icon="ℹ️"):
    """Современная информационная карточка"""
    card_class = f"{card_type}-card"
    st.markdown(f"""
    <div class="{card_class}">
        <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
            <div style="font-size: 1.25rem;">{icon}</div>
            <div>{content}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def section_divider(title=None):
    """Современный разделитель секций"""
    if title:
        st.markdown(f'<h2 class="section-title">{title}</h2>', unsafe_allow_html=True)
    else:
        st.markdown('<hr style="border: none; height: 1px; background: var(--border-color); margin: 2rem 0;">', unsafe_allow_html=True)

def subsection_header(title, icon="📋"):
    """Заголовок подсекции"""
    st.markdown(f'<h3 class="subsection-title">{icon} {title}</h3>', unsafe_allow_html=True)

def create_modern_chart(data, chart_type="bar", title="", color_scheme="blues"):
    """Создает современный график с минималистичным дизайном"""
    
    # Современная цветовая схема
    color_schemes = {
        "blues": ["#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe"],
        "greens": ["#10b981", "#34d399", "#6ee7b7", "#9decdb"], 
        "oranges": ["#f59e0b", "#fbbf24", "#fcd34d", "#fde68a"],
        "reds": ["#ef4444", "#f87171", "#fca5a5", "#fecaca"]
    }
    
    colors = color_schemes.get(color_scheme, color_schemes["blues"])
    
    if chart_type == "bar":
        fig = px.bar(
            data, 
            title=title,
            color_discrete_sequence=colors
        )
    elif chart_type == "pie":
        fig = px.pie(
            data,
            title=title, 
            color_discrete_sequence=colors
        )
    else:
        fig = px.line(
            data,
            title=title,
            color_discrete_sequence=colors
        )
    
    # Современный стиль графика
    fig.update_layout(
        font_family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        font_size=12,
        title_font_size=16,
        title_font_weight="bold",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Убираем сетку и делаем оси минимальными
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#f1f5f9", zeroline=False)
    
    return fig

def modern_table_container(df, title="", height=400):
    """Контейнер для современной таблицы"""
    if title:
        subsection_header(title, "📊")
    
    st.markdown("""
    <div style="background: white; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0;">
    """, unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True, height=height)
    
    st.markdown("</div>", unsafe_allow_html=True)

def loading_spinner(text="Загрузка..."):
    """Современный спиннер загрузки"""
    return st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 2rem;">
        <div style="margin-right: 1rem;">
            <div style="width: 20px; height: 20px; border: 2px solid #e2e8f0; border-top: 2px solid #6366f1; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>
        <span style="color: #64748b;">{text}</span>
    </div>
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)

def modern_progress_indicator(current_step, total_steps, steps_names):
    """Современный индикатор прогресса"""
    progress_html = '<div style="display: flex; align-items: center; margin: 2rem 0; padding: 1rem; background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">'
    
    for i, step_name in enumerate(steps_names):
        # Определяем статус шага
        if i < current_step:
            status = "completed"
            color = "#10b981"
            icon = "✓"
        elif i == current_step:
            status = "current"
            color = "#6366f1"
            icon = str(i + 1)
        else:
            status = "pending"
            color = "#e2e8f0"
            icon = str(i + 1)
        
        # Круг с номером/галочкой
        progress_html += f"""
        <div style="display: flex; flex-direction: column; align-items: center; flex: 1;">
            <div style="width: 32px; height: 32px; border-radius: 50%; background: {color}; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-bottom: 0.5rem;">
                {icon}
            </div>
            <span style="font-size: 0.875rem; text-align: center; color: {'#1e293b' if status != 'pending' else '#94a3b8'};">{step_name}</span>
        </div>
        """
        
        # Линия между шагами (кроме последнего)
        if i < len(steps_names) - 1:
            line_color = "#10b981" if i < current_step else "#e2e8f0"
            progress_html += f'<div style="flex: 1; height: 2px; background: {line_color}; margin: 0 1rem; margin-top: 16px;"></div>'
    
    progress_html += '</div>'
    
    st.markdown(progress_html, unsafe_allow_html=True)