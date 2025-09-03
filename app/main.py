"""
Trading Analysis Platform - Main Flask Application
Built for real-time comprehensive market analysis with Kite Connect integration
"""

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path for importing our analysis engines
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from kite_auth_wrapper import KiteAuth
from comprehensive_market_analyzer import ComprehensiveMarketAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app with correct template and static paths
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Initialize Kite Auth with error handling
try:
    kite_auth = KiteAuth()
    logger.info(f"KiteAuth initialized with API key: {kite_auth.api_key[:10]}...")
except Exception as e:
    logger.error(f"Failed to initialize KiteAuth: {e}")
    kite_auth = None

@app.route('/')
def landing():
    """Landing page with product intro and CTA"""
    return render_template('landing.html')

@app.route('/auth/login')
def auth_login():
    """Redirect to Kite Connect for authentication"""
    try:
        if kite_auth is None:
            return render_template('error.html', error="Kite authentication not configured. Please check API credentials.")
        
        login_url = kite_auth.get_login_url()
        logger.info(f"Redirecting to Kite login URL: {login_url}")
        return redirect(login_url)
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return render_template('error.html', error=f"Authentication service error: {str(e)}")

@app.route('/auth/callback')
def auth_callback():
    """Handle Kite Connect authentication callback"""
    try:
        # Debug: Log all request parameters
        logger.info(f"Callback received with args: {dict(request.args)}")
        
        request_token = request.args.get('request_token')
        if not request_token:
            # Check if there's an error from Kite
            error = request.args.get('error', 'No request token received')
            logger.error(f"Authentication callback failed: {error}")
            return render_template('error.html', error=f"Authentication failed: {error}")
        
        logger.info(f"Request token received: {request_token[:10]}...")
        
        # Generate access token
        access_token = kite_auth.generate_access_token(request_token)
        
        # Store in session
        session['access_token'] = access_token
        session['authenticated'] = True
        session['auth_time'] = datetime.now().isoformat()
        
        logger.info("User successfully authenticated, redirecting to dashboard")
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Authentication callback error: {e}")
        return render_template('error.html', error=f"Authentication failed: {str(e)}")

@app.route('/dashboard')
def dashboard():
    """Main dashboard - requires authentication"""
    if not session.get('authenticated'):
        return redirect(url_for('landing'))
    
    try:
        # Get user's portfolio/watchlist for stock selection
        kite = kite_auth.get_authenticated_kite(session.get('access_token'))
        
        # Try to get holdings, handle gracefully if fails
        try:
            holdings = kite.holdings()
            portfolio_stocks = [h['tradingsymbol'] for h in holdings] if holdings else []
        except:
            portfolio_stocks = []
            logger.warning("Could not fetch holdings - using default stocks")
        
        # Popular stocks for analysis if no portfolio
        default_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ITC', 'SBIN', 'BAJFINANCE']
        
        available_stocks = portfolio_stocks + default_stocks
        
        return render_template('dashboard.html', 
                             stocks=list(set(available_stocks))[:20],  # Remove duplicates, limit to 20
                             portfolio_count=len(portfolio_stocks))
                             
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('error.html', error="Could not load dashboard")

@app.route('/analyze/<symbol>')
def analyze_stock(symbol):
    """Stock analysis page"""
    if not session.get('authenticated'):
        return redirect(url_for('landing'))
    
    return render_template('analysis.html', symbol=symbol.upper())

@app.route('/api/analyze/<symbol>')
def api_analyze(symbol):
    """API endpoint for comprehensive stock analysis"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Initialize analyzer with user's access token
        access_token = session.get('access_token')
        kite = kite_auth.get_authenticated_kite(access_token)
        
        # Create analyzer instance
        analyzer = ComprehensiveMarketAnalyzer(symbol.upper(), kite)
        
        # Generate comprehensive analysis
        analysis_result = analyzer.generate_comprehensive_analysis()
        
        logger.info(f"Generated analysis for {symbol}")
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Analysis error for {symbol}: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/search/<query>')
def api_search_stocks(query):
    """API endpoint for stock search"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        access_token = session.get('access_token')
        kite = kite_auth.get_authenticated_kite(access_token)
        
        # Search instruments
        instruments = kite.instruments()
        
        # Filter by query (symbol or company name)
        query_upper = query.upper()
        matches = []
        
        for instrument in instruments:
            if (instrument['segment'] == 'NSE' and 
                instrument['instrument_type'] == 'EQ' and
                (query_upper in instrument['tradingsymbol'].upper() or 
                 query_upper in instrument['name'].upper())):
                
                matches.append({
                    'symbol': instrument['tradingsymbol'],
                    'name': instrument['name'],
                    'exchange': instrument['exchange']
                })
                
                if len(matches) >= 10:  # Limit results
                    break
        
        return jsonify(matches)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('landing'))

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)