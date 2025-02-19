import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import webbrowser
import threading
import time



df = pd.read_csv('games.csv')


# Data preprocessing
# Filtering data for the period 1990-2010 since this period represents 
# the most complete and reliable gaming industry data
# Remove rows with missing values to ensure data quality
df = df[(df['Year_of_Release'] >= 1990) & (df['Year_of_Release'] <= 2010)]
df = df.dropna()

# Changed data type 'User_Score' to numeric 
df['User_Score'] = pd.to_numeric(df['User_Score'], errors='coerce')
df = df.dropna()  


app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])


dropdown_style = {
    'backgroundColor': '#333',
    'color': 'white'
}

# Layout 
app.layout = html.Div(style={'padding': '15px'}, children=[
    html.H1("Дашборд аналитики игровой индустрии", style={'textAlign': 'center', 'margin': '20px'}),
    
    html.Div("Этот дашборд анализирует данные игровой индустрии с 1990 по 2010 год. Используйте различные фильтры для просмотра статистики игр по платформам, жанрам и году выпуска.", 
             style={'textAlign': 'center', 'margin': '20px', 'fontSize': '16px'}),
    
    # Filter
    dbc.Row([
        # Filter 1: Platform filter
        dbc.Col([
            html.H4("Платформа"),
            dcc.Dropdown(
                id='platform-filter',
                options=[{'label': platform, 'value': platform} for platform in sorted(df['Platform'].unique())],
                multi=True,
                placeholder="Выберите платформу",
                style=dropdown_style
            )
        ], width=4),
        
        # Filter 2: Genre filter
        dbc.Col([
            html.H4("Жанр"),
            dcc.Dropdown(
                id='genre-filter',
                options=[{'label': genre, 'value': genre} for genre in sorted(df['Genre'].unique())],
                multi=True,
                placeholder="Выберите жанр",
                style=dropdown_style
            )
        ], width=4),
        
        # Filter 3: Year range filter
        dbc.Col([
            html.H4("Год выпуска"),
            dcc.RangeSlider(
                id='year-filter',
                min=1990,
                max=2010,
                step=1,
                marks={i: str(i) for i in range(1990, 2011, 5)},
                value=[1990, 2010]
            )
        ], width=4)
    ], style={'margin': '20px'}),
    
    # Graph 
    dbc.Row([
        # graph 1: Total number of games 
        dbc.Col([
            dcc.Graph(id='total-games-graph')
        ], width=4),
        
        # graph 2: user's average score
        dbc.Col([
            dcc.Graph(id='user-score-graph')
        ], width=4),
        
        # Graph 3: critic's average score
        dbc.Col([
            dcc.Graph(id='critic-score-graph')
        ], width=4)
    ]),
    
    dbc.Row([
        # graph 4: Average age ratings by genre 
        dbc.Col([
            dcc.Graph(id='age-rating-graph')
        ], width=4),
        
        # graph 5: scatter plot - rates of users vs critics
        dbc.Col([
            dcc.Graph(id='user-critic-scatter')
        ], width=4),
        
        # Graph 6: cumulative area of game releases by year/platform
        dbc.Col([
            dcc.Graph(id='year-platform-release')
        ], width=4)
    ])
])

# Callback
@callback(
    [Output('total-games-graph', 'figure'),
     Output('user-score-graph', 'figure'),
     Output('critic-score-graph', 'figure'),
     Output('age-rating-graph', 'figure'),
     Output('user-critic-scatter', 'figure'),
     Output('year-platform-release', 'figure')],
    [Input('platform-filter', 'value'),
     Input('genre-filter', 'value'),
     Input('year-filter', 'value')]
)
def update_graphs(selected_platforms, selected_genres, years_range):
    
    filtered_df = df.copy()
    
    if selected_platforms and len(selected_platforms) > 0:
        filtered_df = filtered_df[filtered_df['Platform'].isin(selected_platforms)]
    
    if selected_genres and len(selected_genres) > 0:
        filtered_df = filtered_df[filtered_df['Genre'].isin(selected_genres)]
    
    filtered_df = filtered_df[(filtered_df['Year_of_Release'] >= years_range[0]) & 
                             (filtered_df['Year_of_Release'] <= years_range[1])]
    
    # Handling when the graph is empty
    if filtered_df.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Нет данных",
            template="plotly_dark",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "Нет данных, соответствующих выбранным фильтрам",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 20}
            }]
        )
        return [empty_fig] * 6
    
    # graph 1: Total number of games 
    total_games_fig = go.Figure(go.Indicator(
        mode="number",
        value=len(filtered_df),
        title={'text': "Всего игр", 'font': {'size': 18}}
    ))
    total_games_fig.update_layout(template="plotly_dark", height=250)
    
    # graph 2: user's average score
    user_score_fig = go.Figure(go.Indicator(
        mode="number",
        value=filtered_df['User_Score'].mean(),
        number={'valueformat': '.2f'},
        title={'text': "Средняя оценка пользователей", 'font': {'size': 18}}
    ))
    user_score_fig.update_layout(template="plotly_dark", height=250)
    
    # Graph 3: critic's average score
    critic_score_fig = go.Figure(go.Indicator(
        mode="number",
        value=filtered_df['Critic_Score'].mean(),
        number={'valueformat': '.2f'},
        title={'text': "Средняя оценка критиков", 'font': {'size': 18}}
    ))
    critic_score_fig.update_layout(template="plotly_dark", height=250)
    
    # graph 4: Average age ratings by genre 
    rating_map = {'E': 1, 'E10+': 2, 'T': 3, 'M': 4}
    filtered_df['Rating_Numeric'] = filtered_df['Rating'].map(rating_map)
    
    age_rating_by_genre = filtered_df.groupby('Genre')['Rating_Numeric'].mean().reset_index()
    
    # bar graph 
    age_rating_fig = px.bar(
    age_rating_by_genre, 
    x='Genre', 
    y='Rating_Numeric',
    title='Средний возрастной рейтинг по жанрам',
    labels={'Rating_Numeric': 'Средний возрастной рейтинг', 'Genre': 'Жанр'},
    opacity=0.7  
)
    
    # added line graph 
    age_rating_line = px.line(
        age_rating_by_genre, 
        x='Genre', 
        y='Rating_Numeric',
        markers=True  
    )
    
    # connected two graphs 
    for trace in age_rating_line.data:
        age_rating_fig.add_trace(trace)
    
    age_rating_fig.update_layout(
        template="plotly_dark", 
        xaxis_tickangle=-45,
        height=380, 
        margin=dict(t=40, l=50, r=30, b=80),  
        title_font=dict(size=15),
        title_x=0.5

    )
    
    # graph 5: scatter plot - rates of users vs critics
    user_critic_scatter = px.scatter(
        filtered_df,
        x='Critic_Score',
        y='User_Score',
        color='Genre',
        hover_name='Name',
        title='Сравнение оценок пользователей и критиков',
        labels={'Critic_Score': 'Оценка критиков', 'User_Score': 'Оценка пользователей'}
    )
    user_critic_scatter.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(t=40, l=50, r=30, b=60), 
        title_font=dict(size=15),
        title_x=0.5

    )
    
    # Graph 6: cumulative area of game releases by year/platform
    platform_year_count = filtered_df.groupby(['Year_of_Release', 'Platform']).size().reset_index(name='Count')
    
    year_platform_fig = px.area(
        platform_year_count,
        x='Year_of_Release',
        y='Count',
        color='Platform',
        title='Игры по годам и платформам',
        labels={'Year_of_Release': 'Год выпуска', 'Count': 'Количество игр'}
    )
    year_platform_fig.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(t=40, l=50, r=30, b=60),
        title_font=dict(size=15),
        title_x=0.5

    )
    
    return [total_games_fig, user_score_fig, critic_score_fig, 
            age_rating_fig, user_critic_scatter, year_platform_fig]

# implemented application 
if __name__ == '__main__':
    
    # Add basic CSS for better readability
    # This fixes visibility issues with dropdown menus and slider marks in dark mode
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                
                .VirtualizedSelectOption {
                    background-color: #333;
                    color: white;
                }
                
                .VirtualizedSelectFocusedOption {
                    background-color: #555;
                }
                
                .rc-slider-mark-text {
                    color: white;
                }
            </style>
            {%scripts%}
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    def open_browser():
        time.sleep(1.5)  
        webbrowser.open('http://127.0.0.1:8050/')

    threading.Thread(target=open_browser, daemon=True).start()
    app.run_server(debug=True)

