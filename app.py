import time
import csv
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from colorama import init, Fore
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Initialize Flask app
app = Flask(__name__)

# Initialize Colorama
init(autoreset=True)

# Set up output directory
OUTPUT_DIR = '/app/data'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_text_safely(element):
    try:
        return element.inner_text().strip()
    except Exception:
        return ""

def get_chain_images(element):
    try:
        images = element.query_selector_all("img")
        return [img.get_attribute("src") for img in images] if images else []
    except Exception:
        return []

def scrape_defillama_data():
    investors = []
    deals = []
    round_types = []
    project_categories = []
    project_names = []
    chain_images = []
    median_amounts = []
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_filename = os.path.join(OUTPUT_DIR, f"defillama_data_{timestamp}.txt")
    csv_filename = os.path.join(OUTPUT_DIR, f"defillama_data_{timestamp}.csv")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        
        try:
            url = "https://defillama.com/raises/investors"
            page.goto(url)
            print(Fore.GREEN + "Website loaded successfully!")
            time.sleep(5)
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Investor', 'Deals', 'Median Amount', 'Chains', 'Top Project Category', 'Top Round Type', 'Projects'])
            
            scroll_step = 300
            current_position = 0

            while True:
                try:
                    page.mouse.wheel(0, scroll_step)
                    current_position += scroll_step
                    time.sleep(1.5)

                    # Get element groups
                    elements_200px = page.query_selector_all("div[style*='min-width: 200px']")
                    elements_120px = page.query_selector_all("div[style*='min-width: 120px']")
                    elements_140px = page.query_selector_all("div[style*='min-width: 140px']")
                    elements_160px = page.query_selector_all("div[style*='min-width: 160px']")
                    elements_240px = page.query_selector_all("div[style*='min-width: 240px']")
                    chain_elements = page.query_selector_all("div.flex.items-center.justify-end")

                    current_data = {
                        'investors': [get_text_safely(e) for e in elements_200px],
                        'deals': [],
                        'round_types': [],
                        'categories': [get_text_safely(e) for e in elements_160px],
                        'names': [get_text_safely(e) for e in elements_240px],
                        'chains': [get_chain_images(e) for e in chain_elements],
                        'amounts': [get_text_safely(e) for e in elements_140px]
                    }

                    for e in elements_120px:
                        txt = get_text_safely(e)
                        if txt.replace('+', '').isdigit():
                            current_data['deals'].append(txt)
                        else:
                            current_data['round_types'].append(txt)

                    with open(txt_filename, 'a', encoding='utf-8') as txtfile, \
                         open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                        csv_writer = csv.writer(csvfile)

                        for i in range(len(current_data['investors'])):
                            investor = current_data['investors'][i]
                            deal = current_data['deals'][i] if i < len(current_data['deals']) else "N/A"
                            median_amount = current_data['amounts'][i] if i < len(current_data['amounts']) else "N/A"
                            round_type = current_data['round_types'][i] if i < len(current_data['round_types']) else "N/A"
                            category = current_data['categories'][i] if i < len(current_data['categories']) else "N/A"
                            project_name = current_data['names'][i] if i < len(current_data['names']) else "N/A"
                            chains = current_data['chains'][i] if i < len(current_data['chains']) else []

                            if investor not in investors:
                                investors.append(investor)
                                deals.append(deal)
                                median_amounts.append(median_amount)
                                round_types.append(round_type)
                                project_categories.append(category)
                                project_names.append(project_name)
                                chain_images.append(chains)

                                txt_data = f"""Investor: {investor}
Deals: {deal}
Median Amount: {median_amount}
Round Type: {round_type}
Project Category: {category}
Project Name: {project_name}
Chain Images: {', '.join(chains) if chains else "N/A"}
{'-' * 50}

"""
                                txtfile.write(txt_data)
                                csv_writer.writerow([
                                    investor,
                                    deal,
                                    median_amount,
                                    ', '.join(chains) if chains else "N/A",
                                    category,
                                    round_type,
                                    project_name
                                ])

                                print(txt_data)

                    # Break if no new data is loaded (or we scrolled too far)
                    if current_position > 30000:  # tweak as needed
                        print(Fore.GREEN + "Scrolled far enough, assuming end of data.")
                        break

                except PlaywrightTimeout:
                    print(Fore.YELLOW + "Timeout occurred. Trying again...")
                    continue
                except Exception as e:
                    print(Fore.RED + f"Unexpected error: {str(e)}")
                    break
                    
        except Exception as e:
            print(Fore.RED + f"An error occurred: {str(e)}")
        finally:
            browser.close()
            
    print(Fore.GREEN + f"\nData saved to {txt_filename} and {csv_filename}")
    
    return {
        "filename": csv_filename,
        "txt_filename": txt_filename,
        "count": len(investors),
        "status": "success"
    }

# Routes for the web application
@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>DeFi Llama Scraper</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }
            button:hover { background-color: #45a049; }
            #status { margin-top: 20px; }
            #files { margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>DeFi Llama Investor Data Scraper</h1>
        <p>This application scrapes investor data from DeFi Llama and saves it as CSV and TXT files.</p>
        <button id="startBtn" onclick="startScraping()">Start Scraping</button>
        <div id="status"></div>
        <div id="files"></div>
        
        <script>
            function startScraping() {
                document.getElementById('status').innerHTML = '<p>Scraping in progress... This may take several minutes.</p>';
                document.getElementById('startBtn').disabled = true;
                
                fetch('/scrape', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('status').innerHTML = 
                            `<p>Scraping completed! Collected ${data.count} investors.</p>`;
                        document.getElementById('files').innerHTML = 
                            `<p>Files saved:</p>
                             <ul>
                                <li><a href="/download?file=${encodeURIComponent(data.filename)}">Download CSV</a></li>
                                <li><a href="/download?file=${encodeURIComponent(data.txt_filename)}">Download TXT</a></li>
                             </ul>`;
                        document.getElementById('startBtn').disabled = false;
                    })
                    .catch(error => {
                        document.getElementById('status').innerHTML = 
                            `<p>Error: ${error.message}</p>`;
                        document.getElementById('startBtn').disabled = false;
                    });
            }
        </script>
    </body>
    </html>
    """

@app.route('/scrape', methods=['POST'])
def scrape():
    result = scrape_defillama_data()
    return jsonify(result)

@app.route('/download')
def download():
    file_path = request.args.get('file')
    if not file_path or not os.path.exists(file_path):
        return "File not found", 404
    
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/api/data', methods=['GET'])
def get_data():
    # Get list of data files
    files = []
    for file in os.listdir(OUTPUT_DIR):
        if file.endswith('.csv'):
            files.append(file)
    
    # Return the most recent file by default
    if files:
        files.sort(reverse=True)
        latest_file = os.path.join(OUTPUT_DIR, files[0])
        
        data = []
        with open(latest_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        return jsonify(data)
    
    return jsonify({"error": "No data available"}), 404

# Run the Flask app when this script is executed directly
if __name__ == "__main__":
    # For local development
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)