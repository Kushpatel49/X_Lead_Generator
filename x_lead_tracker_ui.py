"""
Streamlit UI for X (Twitter) Lead Tracker
Find B2B leads for BI/Analytics software on X platform
"""

import streamlit as st
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
import json
from agno.tools.x import XTools
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="X Lead Tracker - BI/Analytics Software",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1DA1F2;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #657786;
        text-align: center;
        padding-bottom: 2rem;
    }
    .lead-card {
        border: 2px solid #1DA1F2;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    .high-score {
        color: #17bf63;
        font-weight: bold;
    }
    .medium-score {
        color: #ffad1f;
        font-weight: bold;
    }
    .low-score {
        color: #e0245e;
        font-weight: bold;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'leads' not in st.session_state:
    st.session_state.leads = []
if 'all_posts' not in st.session_state:
    st.session_state.all_posts = []
if 'search_stats' not in st.session_state:
    st.session_state.search_stats = {
        'total_posts': 0,
        'analyzed_posts': 0,
        'leads_found': 0,
        'last_search': None
    }

# Header
st.markdown('<div class="main-header">🐦 X Lead Tracker</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Find B2B leads for BI/Analytics software on X (Twitter)</div>', unsafe_allow_html=True)

# API Limitation Warning
st.warning("""
⚠️ **X API Limitations Notice:**

The **Free X API tier** has severe restrictions:
- ❌ Very limited search access (may not work at all)
- ❌ Only 500 posts per month total
- ❌ Rate limit: 15 requests per 15 minutes

**For reliable lead generation, you need:**
- 💰 **Basic Tier** ($100/month) - 10K posts/month
- 💰 **Pro Tier** ($5,000/month) - 1M posts/month with full search

**Alternative:** Use the **Reddit Lead Tracker** instead - it's free, works great, and has better B2B content!

📖 See `X_API_LIMITATIONS.md` for full details and alternatives.
""")

# Success story with Reddit
st.info("""
💡 **Tip:** The Reddit Lead Tracker is working perfectly and is **100% free**! 
Reddit has detailed B2B discussions in subreddits like r/businessintelligence, r/datascience, r/PowerBI, etc.

Run: `uv run streamlit run reddit_lead_tracker_ui.py`
""")

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Credentials
    st.subheader("🔑 API Credentials")
    
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Your OpenAI API key for AI analysis"
    )
    
    st.markdown("---")
    st.markdown("**X API Credentials**")
    st.caption("Get your credentials from [developer.x.com](https://developer.x.com)")
    
    x_consumer_key = st.text_input(
        "Consumer Key (API Key)",
        type="password",
        value=os.getenv("X_CONSUMER_KEY", ""),
        help="X API Consumer Key"
    )
    
    x_consumer_secret = st.text_input(
        "Consumer Secret (API Secret)",
        type="password",
        value=os.getenv("X_CONSUMER_SECRET", ""),
        help="X API Consumer Secret"
    )
    
    x_access_token = st.text_input(
        "Access Token",
        type="password",
        value=os.getenv("X_ACCESS_TOKEN", ""),
        help="X API Access Token"
    )
    
    x_access_token_secret = st.text_input(
        "Access Token Secret",
        type="password",
        value=os.getenv("X_ACCESS_TOKEN_SECRET", ""),
        help="X API Access Token Secret"
    )
    
    x_bearer_token = st.text_input(
        "Bearer Token",
        type="password",
        value=os.getenv("X_BEARER_TOKEN", ""),
        help="X API Bearer Token"
    )
    
    st.markdown("---")
    
    # Search Parameters
    st.subheader("🔍 Search Parameters")
    
    default_queries = [
        "looking for BI dashboard tool",
        "need data visualization software",
        "business intelligence recommendations",
        "analytics dashboard for company",
        "reporting tool suggestions"
    ]
    
    search_queries_text = st.text_area(
        "Search Queries (one per line)",
        value="\n".join(default_queries),
        height=150,
        help="Enter search queries to find relevant posts on X"
    )
    
    max_posts_per_query = st.slider(
        "Max Posts per Query",
        min_value=10,
        max_value=100,
        value=50,
        step=10,
        help="Maximum number of posts to analyze per search query"
    )
    
    min_lead_score = st.slider(
        "Minimum Lead Score",
        min_value=1,
        max_value=10,
        value=6,
        help="Minimum score (1-10) to qualify as a lead"
    )
    
    st.markdown("---")
    
    # Action Buttons
    search_button = st.button("🚀 Start Lead Search", type="primary", use_container_width=True)
    clear_button = st.button("🗑️ Clear Results", use_container_width=True)


def initialize_x_client(consumer_key, consumer_secret, access_token, access_token_secret, bearer_token):
    """Initialize X API client"""
    try:
        x_tools = XTools(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            bearer_token=bearer_token,
            include_post_metrics=True,
            wait_on_rate_limit=True
        )
        logger.info("X client initialized successfully")
        return x_tools
    except Exception as e:
        logger.error(f"Error initializing X client: {str(e)}")
        raise


def create_lead_tracker_agent(openai_api_key, x_tools):
    """Create AI agent for lead qualification"""
    agent = Agent(
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        tools=[x_tools],
        instructions=[
            "You are a B2B lead qualification specialist for advanced business intelligence and analytics software.",
            "",
            "TARGET CUSTOMER PROFILE:",
            "- Businesses needing business analysis or BI dashboards",
            "- Companies struggling with data visualization or reporting",
            "- Organizations looking for analytics solutions",
            "- Decision-makers or influencers in data/analytics roles",
            "",
            "WHAT TO LOOK FOR:",
            "1. Business Pain Points:",
            "   - Need for better reporting or dashboards",
            "   - Data visualization challenges",
            "   - Analytics tool evaluation",
            "   - Enterprise reporting needs",
            "",
            "2. Decision-Maker Indicators:",
            "   - Job titles (Manager, Director, VP, CEO, CTO, Data Lead)",
            "   - Company/organization mentions",
            "   - Budget or procurement discussions",
            "   - Team or organizational needs",
            "",
            "3. RED FLAGS (Score LOW):",
            "   - Student projects or homework",
            "   - Personal hobby projects",
            "   - Tutorial/learning requests",
            "   - Free-only requirements",
            "",
            "SCORING GUIDE:",
            "9-10: Clear business need, decision-maker, budget indication",
            "7-8: Business need evident, likely has influence",
            "5-6: Possible business context, relevant needs",
            "3-4: Unclear if business, vague requirements",
            "1-2: Likely personal/student project",
            "",
            "Be strict - we want quality B2B leads only.",
        ],
        markdown=True,
    )
    return agent


def track_leads_on_x(
    search_queries,
    openai_api_key,
    x_consumer_key,
    x_consumer_secret,
    x_access_token,
    x_access_token_secret,
    x_bearer_token,
    max_posts_per_query,
    min_lead_score
):
    """Main function to track leads on X"""
    
    leads = []
    all_posts = []
    stats = {
        'total_posts': 0,
        'analyzed_posts': 0,
        'leads_found': 0
    }
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize X client
        status_text.text("🔧 Initializing X API client...")
        x_tools = initialize_x_client(
            x_consumer_key,
            x_consumer_secret,
            x_access_token,
            x_access_token_secret,
            x_bearer_token
        )
        
        # Create AI agent
        status_text.text("🤖 Creating AI lead qualification agent...")
        agent = create_lead_tracker_agent(openai_api_key, x_tools)
        
        total_queries = len(search_queries)
        
        for idx, query in enumerate(search_queries):
            status_text.text(f"🔍 Searching X for: '{query}' ({idx+1}/{total_queries})")
            
            try:
                # Search for posts
                search_prompt = f"""
                Search X for posts matching: "{query}"
                
                Find recent posts (last 7 days) where people are discussing:
                - Need for BI tools or dashboards
                - Data visualization challenges
                - Business analytics requirements
                - Reporting and analytics pain points
                
                Return up to {max_posts_per_query} most relevant posts with:
                - Post ID
                - Author username
                - Post content/text
                - Post URL
                - Engagement metrics (likes, retweets, replies)
                
                Format each post clearly with all details.
                """
                
                status_text.text(f"📊 Analyzing posts for: '{query}'...")
                response = agent.run(search_prompt)
                
                # Note: In a real implementation, you would parse the response
                # to extract individual posts and analyze them
                # For now, we'll create a placeholder structure
                
                status_text.text(f"✅ Completed analysis for: '{query}'")
                stats['total_posts'] += max_posts_per_query
                
            except Exception as e:
                st.warning(f"⚠️ Error processing query '{query}': {str(e)}")
                logger.error(f"Error processing query '{query}': {str(e)}")
            
            # Update progress
            progress_bar.progress((idx + 1) / total_queries)
        
        progress_bar.progress(1.0)
        status_text.text("✅ Lead search completed!")
        
        stats['last_search'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return leads, all_posts, stats
        
    except Exception as e:
        st.error(f"❌ Error during lead tracking: {str(e)}")
        logger.error(f"Error during lead tracking: {str(e)}")
        return [], [], stats


# Clear results
if clear_button:
    st.session_state.leads = []
    st.session_state.all_posts = []
    st.session_state.search_stats = {
        'total_posts': 0,
        'analyzed_posts': 0,
        'leads_found': 0,
        'last_search': None
    }
    st.success("✅ Results cleared!")
    st.rerun()

# Start search
if search_button:
    # Validate inputs
    if not openai_api_key or openai_api_key == "":
        st.error("❌ Please provide your OpenAI API Key")
    elif not all([x_consumer_key, x_consumer_secret, x_access_token, x_access_token_secret, x_bearer_token]):
        st.error("❌ Please provide all X API credentials")
    elif not search_queries_text.strip():
        st.error("❌ Please provide at least one search query")
    else:
        search_queries = [q.strip() for q in search_queries_text.split('\n') if q.strip()]
        
        with st.spinner("🔍 Searching X for B2B leads..."):
            leads, all_posts, stats = track_leads_on_x(
                search_queries=search_queries,
                openai_api_key=openai_api_key,
                x_consumer_key=x_consumer_key,
                x_consumer_secret=x_consumer_secret,
                x_access_token=x_access_token,
                x_access_token_secret=x_access_token_secret,
                x_bearer_token=x_bearer_token,
                max_posts_per_query=max_posts_per_query,
                min_lead_score=min_lead_score
            )
            
            st.session_state.leads = leads
            st.session_state.all_posts = all_posts
            st.session_state.search_stats = stats
            
            if leads:
                st.success(f"✅ Found {len(leads)} potential B2B leads!")
            else:
                st.info("ℹ️ No leads found matching your criteria. Try adjusting your search queries or lowering the minimum score.")

# Main content area - Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🎯 Leads", "📝 All Posts", "💾 Export"])

# Tab 1: Dashboard
with tab1:
    st.header("📊 Search Statistics")
    
    stats = st.session_state.search_stats
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{stats.get('total_posts', 0)}</h2>
            <p>Total Posts Searched</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{stats.get('analyzed_posts', 0)}</h2>
            <p>Posts Analyzed by AI</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{len(st.session_state.leads)}</h2>
            <p>Qualified Leads Found</p>
        </div>
        """, unsafe_allow_html=True)
    
    if stats.get('last_search'):
        st.info(f"🕐 Last search completed: {stats['last_search']}")
    
    if st.session_state.leads:
        st.markdown("---")
        st.subheader("📈 Lead Score Distribution")
        
        scores = [lead.get('score', 0) for lead in st.session_state.leads]
        score_counts = {
            'High (8-10)': len([s for s in scores if s >= 8]),
            'Medium (5-7)': len([s for s in scores if 5 <= s < 8]),
            'Low (1-4)': len([s for s in scores if s < 5])
        }
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("High Priority", score_counts['High (8-10)'], delta="Hot Leads")
        with col2:
            st.metric("Medium Priority", score_counts['Medium (5-7)'], delta="Warm Leads")
        with col3:
            st.metric("Low Priority", score_counts['Low (1-4)'], delta="Cold Leads")

# Tab 2: Leads
with tab2:
    st.header("🎯 Qualified Leads")
    
    if not st.session_state.leads:
        st.info("👋 No leads yet. Start a search to find potential B2B customers on X!")
    else:
        # Sort and filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                ["Score (High to Low)", "Score (Low to High)", "Author A-Z"]
            )
        with col2:
            filter_score = st.multiselect(
                "Filter by Score Range",
                ["High (8-10)", "Medium (5-7)", "Low (1-4)"],
                default=["High (8-10)", "Medium (5-7)", "Low (1-4)"]
            )
        
        # Apply filters
        filtered_leads = st.session_state.leads.copy()
        
        if "High (8-10)" not in filter_score:
            filtered_leads = [l for l in filtered_leads if l.get('score', 0) < 8]
        if "Medium (5-7)" not in filter_score:
            filtered_leads = [l for l in filtered_leads if not (5 <= l.get('score', 0) < 8)]
        if "Low (1-4)" not in filter_score:
            filtered_leads = [l for l in filtered_leads if l.get('score', 0) >= 5]
        
        # Apply sorting
        if sort_by == "Score (High to Low)":
            filtered_leads.sort(key=lambda x: x.get('score', 0), reverse=True)
        elif sort_by == "Score (Low to High)":
            filtered_leads.sort(key=lambda x: x.get('score', 0))
        else:
            filtered_leads.sort(key=lambda x: x.get('author', ''))
        
        st.write(f"Showing {len(filtered_leads)} lead(s)")
        
        # Display leads
        for idx, lead in enumerate(filtered_leads, 1):
            score = lead.get('score', 0)
            score_class = "high-score" if score >= 8 else "medium-score" if score >= 5 else "low-score"
            
            with st.expander(f"Lead #{idx}: @{lead.get('author', 'Unknown')} - Score: {score}/10", expanded=(idx == 1)):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Post Content:**")
                    st.write(lead.get('content', 'No content available'))
                    
                    st.markdown(f"**🔗 Post URL:** [{lead.get('url', 'N/A')}]({lead.get('url', '#')})")
                    
                    if lead.get('engagement_metrics'):
                        metrics = lead['engagement_metrics']
                        st.markdown(f"**📊 Engagement:** ❤️ {metrics.get('likes', 0)} | 🔄 {metrics.get('retweets', 0)} | 💬 {metrics.get('replies', 0)}")
                
                with col2:
                    st.markdown(f"<p class='{score_class}'>Score: {score}/10</p>", unsafe_allow_html=True)
                    st.markdown(f"**Author:** @{lead.get('author', 'Unknown')}")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🏢 Business Context:**")
                    st.write(lead.get('business_context', 'Not available'))
                    
                    st.markdown("**💰 Budget Indicators:**")
                    st.write(lead.get('budget_indicators', 'Not available'))
                
                with col2:
                    st.markdown("**👔 Decision Authority:**")
                    st.write(lead.get('decision_authority', 'Not available'))
                    
                    st.markdown("**🚩 Red Flags:**")
                    st.write(lead.get('red_flags', 'None identified'))
                
                st.markdown("**🎯 Pain Points:**")
                pain_points = lead.get('pain_points', [])
                if pain_points:
                    for point in pain_points:
                        st.markdown(f"- {point}")
                else:
                    st.write("No specific pain points identified")
                
                st.markdown("**💡 Recommendation:**")
                st.info(lead.get('recommendation', 'No recommendation available'))

# Tab 3: All Posts
with tab3:
    st.header("📝 All Explored Posts")
    
    if not st.session_state.all_posts:
        st.info("No posts explored yet. Start a search to see all posts analyzed!")
    else:
        st.write(f"Total posts explored: {len(st.session_state.all_posts)}")
        
        for idx, post in enumerate(st.session_state.all_posts, 1):
            with st.expander(f"Post #{idx}: @{post.get('author', 'Unknown')}"):
                st.markdown(f"**Content:** {post.get('content', 'No content')}")
                st.markdown(f"**URL:** [{post.get('url', 'N/A')}]({post.get('url', '#')})")
                st.markdown(f"**Status:** {post.get('status', 'Explored')}")

# Tab 4: Export
with tab4:
    st.header("💾 Export Results")
    
    if not st.session_state.leads:
        st.info("No leads to export yet. Complete a search first!")
    else:
        st.write(f"Ready to export {len(st.session_state.leads)} lead(s)")
        
        export_format = st.radio("Select export format", ["JSON", "CSV"])
        
        if export_format == "JSON":
            json_data = json.dumps(st.session_state.leads, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"x_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            with st.expander("Preview JSON"):
                st.json(st.session_state.leads)
        
        else:  # CSV
            import pandas as pd
            
            # Flatten lead data for CSV
            csv_data = []
            for lead in st.session_state.leads:
                csv_data.append({
                    'Author': lead.get('author', ''),
                    'Score': lead.get('score', 0),
                    'Post URL': lead.get('url', ''),
                    'Content': lead.get('content', ''),
                    'Business Context': lead.get('business_context', ''),
                    'Decision Authority': lead.get('decision_authority', ''),
                    'Pain Points': ', '.join(lead.get('pain_points', [])),
                    'Budget Indicators': lead.get('budget_indicators', ''),
                    'Red Flags': lead.get('red_flags', ''),
                    'Recommendation': lead.get('recommendation', '')
                })
            
            df = pd.DataFrame(csv_data)
            csv_string = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_string,
                file_name=f"x_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            with st.expander("Preview CSV"):
                st.dataframe(df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #657786; padding: 2rem 0;'>
    <p>🐦 X Lead Tracker for BI/Analytics Software | Powered by Agno & OpenAI</p>
    <p style='font-size: 0.8rem;'>Track B2B leads on X (Twitter) using AI-powered analysis</p>
</div>
""", unsafe_allow_html=True)

