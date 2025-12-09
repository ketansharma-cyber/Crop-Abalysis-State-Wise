import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Crop Production & Yield Dashboard",
    page_icon="$$$$",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main {
        padding: 1rem 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    h1 {
        color: #2c5f2d;
        text-align: center;
        font-weight: 700;
        margin-bottom: 30px;
    }
    .filter-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    
    df = pd.read_csv('India Agriculture Crop Production.csv')
    df.columns = df.columns.str.strip()
    df['Production'] = pd.to_numeric(df['Production'], errors='coerce')
    df['Area'] = pd.to_numeric(df['Area'], errors='coerce')
    df['Yield'] = pd.to_numeric(df['Yield'], errors='coerce')
    df['Year_Start'] = df['Year'].str.split('-').str[0].astype(int)
    return df

@st.cache_data
def load_geojson():
   
    with open('india_state_geo.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_correlation_matrix(df):
    
    corr_data = df[['Area', 'Production', 'Yield']].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_data.values,
        x=['Area', 'Production', 'Yield'],
        y=['Area', 'Production', 'Yield'],
        colorscale='RdYlGn',
        zmid=0,
        text=corr_data.values.round(3),
        texttemplate='%{text}',
        textfont={"size": 14},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title='Correlation Matrix',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig

def map_state_names(df):
   
    state_mapping = {
        'Andaman and Nicobar Islands': 'Andaman and Nicobar',
        'Telangana': 'Telangana', 
        'Dadra and Nagar Haveli': 'Dadra and Nagar Haveli',
        'Daman and Diu': 'Daman and Diu'
    }
    
    df_copy = df.copy()
    df_copy['State_Mapped'] = df_copy['State'].replace(state_mapping)
    return df_copy

def main():
   
    with st.spinner('Loading data...'):
        df = load_data()
        geojson = load_geojson()
  
    st.title(" Crop Production & Yield Dashboard")
    
    
    tab1, tab2 = st.tabs(["Dashboard", "Map View"])
    
    with tab1:
      
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            states = sorted(df['State'].dropna().unique())
            selected_states = st.multiselect("State (multi-select)", states, default=[states[0]] if states else [])
        
        with col2:
            if selected_states:
                districts = sorted(df[df['State'].isin(selected_states)]['District'].dropna().unique())
                selected_districts = st.multiselect("District (multi-select)", districts, default=[districts[0]] if districts else [])
            else:
                selected_districts = st.multiselect("District (multi-select)", [], default=[])
        
        with col3:
            crops = sorted(df['Crop'].dropna().unique())
            selected_crops = st.multiselect("Crop (multi-select)", crops, default=['Rice'] if 'Rice' in crops else [crops[0]])
        
        with col4:
            seasons = sorted(df['Season'].dropna().unique())
            selected_seasons = st.multiselect("Season (multi-select)", seasons, default=['Kharif'] if 'Kharif' in seasons else [seasons[0]])
        
        with col5:
           
            from datetime import datetime
            current = datetime.now().year  # Get current year dynamically
            years = list(range(1990, current+1))  
            years.reverse()  # Show newest first
            selected_years = st.multiselect("Year Selector (multi-select)", years, default=years[:5] if len(years) >= 5 else years)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
       
        filtered_df = df.copy()
        if selected_states:
            filtered_df = filtered_df[filtered_df['State'].isin(selected_states)]
        if selected_districts:
            filtered_df = filtered_df[filtered_df['District'].isin(selected_districts)]
        if selected_crops:
            filtered_df = filtered_df[filtered_df['Crop'].isin(selected_crops)]
        if selected_seasons:
            filtered_df = filtered_df[filtered_df['Season'].isin(selected_seasons)]
        if selected_years:
            filtered_df = filtered_df[filtered_df['Year_Start'].isin(selected_years)]
        
       
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Correlation Matrix")
            if len(filtered_df) > 0:
                fig_corr = create_correlation_matrix(filtered_df)
                st.plotly_chart(fig_corr, width='stretch')
            else:
                st.info("No data available for selected filters")
        
        with col2:
            st.subheader("Time series")
            st.markdown("*(Time Series chart with Years in X-axis and Area, Production and Yield on Y-axis >> preferably on one chart >> can be broken into multiple charts as well)*")
            if len(filtered_df) > 0:
                yearly_data = filtered_df.groupby('Year_Start').agg({
                    'Area': 'sum',
                    'Production': 'sum',
                    'Yield': 'mean'
                }).reset_index()
                
                
                fig_ts = go.Figure()
                fig_ts.add_trace(go.Scatter(x=yearly_data['Year_Start'], y=yearly_data['Area'], 
                                           name='Area', mode='lines+markers', line=dict(color='blue')))
                fig_ts.add_trace(go.Scatter(x=yearly_data['Year_Start'], y=yearly_data['Production'], 
                                           name='Production', mode='lines+markers', line=dict(color='green')))
                fig_ts.add_trace(go.Scatter(x=yearly_data['Year_Start'], y=yearly_data['Yield'], 
                                           name='Yield', mode='lines+markers', line=dict(color='orange'), yaxis='y2'))
                
                fig_ts.update_layout(
                    xaxis=dict(title='Year'),
                    yaxis=dict(title='Area & Production', side='left'),
                    yaxis2=dict(title='Yield', overlaying='y', side='right'),
                    height=300,
                    legend=dict(x=0, y=1.1, orientation='h'),
                    margin=dict(l=50, r=50, t=30, b=50)
                )
                st.plotly_chart(fig_ts, width='stretch')
        
       
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top Producing Districts")
            st.markdown("*Bar chart (top producing districts)*")
            if len(filtered_df) > 0:
                district_prod = filtered_df.groupby('District')['Production'].sum().sort_values(ascending=False).head(10).reset_index()
                fig_districts = px.bar(district_prod, x='District', y='Production', 
                                      color='Production', color_continuous_scale='Greens')
                fig_districts.update_layout(height=300, xaxis_tickangle=-45, 
                                           margin=dict(l=50, r=50, t=30, b=100))
                st.plotly_chart(fig_districts, width='stretch')
        
        with col2:
            st.subheader("Yield")
            st.markdown("*Map (choropleth of yield) >> preferably at district level, but, state level accepted*")
            if len(filtered_df) > 0:
               
                mapped_df = map_state_names(filtered_df)
                state_yield = mapped_df.groupby('State_Mapped')['Yield'].mean().reset_index()
                state_yield = state_yield.rename(columns={'State_Mapped': 'State'})
                
                fig_yield_map = px.choropleth(
                    state_yield,
                    geojson=geojson,
                    locations='State',
                    featureidkey='properties.NAME_1',
                    color='Yield',
                    color_continuous_scale='YlGn',
                    hover_data={'Yield': ':.2f'}
                )
                fig_yield_map.update_geos(fitbounds="locations", visible=False)
                fig_yield_map.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig_yield_map, width='stretch')
        
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Yield vs Production Area")
            st.markdown("*Scatter Plot*")
            if len(filtered_df) > 0:
                scatter_data = filtered_df.groupby('District').agg({
                    'Area': 'sum',
                    'Yield': 'mean',
                    'Production': 'sum'
                }).reset_index()
                
                fig_scatter = px.scatter(scatter_data, x='Area', y='Yield', 
                                        size='Production', hover_data=['District'],
                                        color='Production', color_continuous_scale='Viridis')
                fig_scatter.update_layout(height=300, margin=dict(l=50, r=50, t=30, b=50))
                st.plotly_chart(fig_scatter, width='stretch')
        
        with col2:
            st.subheader("Crop-wise Production")
            st.markdown("*Time series chart with years in X- axis and crop-wise production for multiple crops in Y-axis*")
            if len(filtered_df) > 0:
                crop_yearly = filtered_df.groupby(['Year_Start', 'Crop'])['Production'].sum().reset_index()
                fig_crop_prod = px.line(crop_yearly, x='Year_Start', y='Production', 
                                       color='Crop', markers=True)
                fig_crop_prod.update_layout(height=300, 
                                           xaxis_title='Year',
                                           yaxis_title='Production',
                                           legend=dict(x=0, y=1.1, orientation='h'),
                                           margin=dict(l=50, r=50, t=30, b=50))
                st.plotly_chart(fig_crop_prod, width='stretch')
    
    with tab2:
        st.subheader("Map View")
        st.info(" View map >> select State >> shows district-level bars and trend")
        
      
        if len(df) > 0:
            # Map state names for GeoJSON matching
            mapped_df = map_state_names(df)
            state_data = mapped_df.groupby('State_Mapped').agg({
                'Production': 'sum',
                'Area': 'sum',
                'Yield': 'mean'
            }).reset_index()
            state_data = state_data.rename(columns={'State_Mapped': 'State'})
            
            fig_map = px.choropleth(
                state_data,
                geojson=geojson,
                locations='State',
                featureidkey='properties.NAME_1',
                color='Production',
                hover_name='State',
                hover_data={'Production': ':,.0f', 'Area': ':,.0f', 'Yield': ':.2f'},
                color_continuous_scale='Greens',
                title='State-wise Production Distribution'
            )
            
            fig_map.update_geos(fitbounds="locations", visible=False)
            fig_map.update_layout(height=600, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_map, width='stretch')
            
           
            st.markdown("---")
            selected_state_map = st.selectbox("Select State to view district-level analysis", 
                                             [''] + sorted(df['State'].unique().tolist()))
            
            if selected_state_map:
                state_df = df[df['State'] == selected_state_map]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"District-level Production: {selected_state_map}")
                    district_data = state_df.groupby('District')['Production'].sum().sort_values(ascending=False).head(15).reset_index()
                    fig_district_bars = px.bar(district_data, x='District', y='Production',
                                              color='Production', color_continuous_scale='Blues')
                    fig_district_bars.update_layout(xaxis_tickangle=-45, height=400)
                    st.plotly_chart(fig_district_bars, width='stretch')
                
                with col2:
                    st.subheader(f"Production Trend: {selected_state_map}")
                    yearly_trend = state_df.groupby('Year_Start')['Production'].sum().reset_index()
                    fig_trend = px.line(yearly_trend, x='Year_Start', y='Production', 
                                       markers=True, line_shape='spline')
                    fig_trend.update_traces(line_color='#2c5f2d', line_width=3)
                    fig_trend.update_layout(height=400)
                    st.plotly_chart(fig_trend, width='stretch')
    
   
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 10px;'>
            <p> Crop Production & Yield Dashboard | Data Source: Ministry of Agriculture & Farmers Welfare</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
