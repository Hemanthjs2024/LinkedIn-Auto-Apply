from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import os
import re # Import the regular expression module

app = Flask(__name__)
CORS(app) # Enable CORS for all origins

# --- Email Sender ---
def send_email(user_email, email_password, subject, external_jobs):
    msg = MIMEMultipart("alternative")
    msg['From'] = user_email
    msg['To'] = user_email
    msg['Subject'] = subject

    html = """
    <html><body>
    <h3>Company Website Application Links</h3>
    <table border='1' cellpadding='5' cellspacing='0'>
        <tr><th>Company Name</th><th>Job Link</th></tr>
    """
    for company, link in external_jobs:
        html += f"<tr><td>{company}</td><td><a href='{link}'>{link}</a></td></tr>"
    html += "</table></body></html>"

    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(user_email, email_password)
        server.sendmail(user_email, user_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise

# --- Load previously applied jobs ---
def load_applied_jobs():
    track_file = "applied_jobs.json"
    if os.path.exists(track_file):
        try:
            with open(track_file, 'r') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()

# --- Save applied job URL ---
def save_applied_job(url, applied_jobs):
    track_file = "applied_jobs.json"
    applied_jobs.add(url)
    try:
        with open(track_file, 'w') as f:
            json.dump(list(applied_jobs), f)
    except IOError as e:
        print(f"Failed to save applied jobs: {e}")

@app.route('/run-bot', methods=['POST'])
def run_bot():
    data = request.get_json()
    linkedin_email = data.get('linkedinEmail')
    linkedin_password = data.get('linkedinPassword')
    user_email = data.get('userEmail')
    email_password = data.get('emailPassword')
    keywords_str = data.get('keywords', "")
    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

    if not all([linkedin_email, linkedin_password, user_email, email_password, keywords]):
        return jsonify({"success": False, "error": "Missing required form data."}), 400

    driver = None # Initialize driver to None
    try:
        # --- Setup Chrome ---
        options = Options()
        options.add_argument("--start-maximized")
        # options.add_argument("--headless") # Uncomment for headless mode
        options.add_argument('--no-sandbox') # Required for some environments
        options.add_argument('--disable-dev-shm-usage') # Required for some environments

        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20) # Increased wait time

        # --- Login to LinkedIn ---
        driver.get("https://www.linkedin.com/login")
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(linkedin_email)
        driver.find_element(By.ID, "password").send_keys(linkedin_password)
        driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
        time.sleep(5) # Wait for login to complete

        # Check if login was successful (you might need a more robust check)
        if "feed" not in driver.current_url:
             # Attempt to handle potential verification step, if any
             try:
                 # Look for common elements on verification pages
                 wait.until(EC.presence_of_element_located((By.ID, "email-or-phone")))
                 return jsonify({"success": False, "error": "LinkedIn login failed. Please check credentials or if there's a verification step."}), 401
             except:
                  # If no verification element found, assume incorrect credentials
                 return jsonify({"success": False, "error": "LinkedIn login failed. Please check your email and password."}), 401

        external_links = []
        applied_jobs = load_applied_jobs()

        # --- Job Search and Apply ---
        for keyword in keywords:
            print(f"Searching for keyword: {keyword}")
            driver.get("https://www.linkedin.com/jobs/search/?keywords=" + keyword.replace(" ", "%20"))
            time.sleep(5) # Let jobs load

            # Scroll to load more jobs - example (adjust range as needed)
            # You might need a more sophisticated scrolling mechanism for a lot of jobs
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # time.sleep(3)

            jobs = driver.find_elements(By.CLASS_NAME, "job-card-container")
            print(f"Found {len(jobs)} jobs for {keyword}")
            for i, job in enumerate(jobs[:10]): # Process first 10 jobs per keyword
                try:
                    # Use a more reliable method to get job URL/ID if available
                    # This might need adjustment based on LinkedIn's HTML structure
                    job_link_element = job.find_element(By.CSS_SELECTOR, 'a.job-card-container__link')
                    job_url = job_link_element.get_attribute("href")

                    if not job_url:
                        print(f"Skipping job {i}: Could not get job URL.")
                        continue

                    # Extract job ID from URL (LinkedIn job URLs usually contain an ID)
                    job_id_match = re.search(r'/jobs/(\d+)/', job_url)
                    job_id = job_id_match.group(1) if job_id_match else job_url # Use URL as ID if ID not found

                    if job_id in applied_jobs:
                        print(f"Skipping job {i}: Already applied (ID: {job_id})")
                        continue

                    print(f"Processing job {i+1} (ID: {job_id})")
                    # Click the job card element
                    job.click()
                    time.sleep(3) # Wait for details to load

                    # Switch to the job details pane (usually an iframe or a specific div)
                    # This part is highly dependent on LinkedIn's page structure
                    # You might need to inspect the page to find the correct element
                    # For now, we assume details load on the same page structure after clicking

                    try:
                        # Check for Easy Apply button
                        # Using WebDriverWait for more robust element finding
                        easy_apply_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".jobs-apply-button")))

                        if "Easy Apply" in easy_apply_btn.text:
                            print("Found Easy Apply button")
                            easy_apply_btn.click()
                            time.sleep(3) # Wait for apply modal/page to load

                            # --- Handle Easy Apply form ---
                            step = 1
                            while True:
                                print(f"Processing Easy Apply step {step}")
                                time.sleep(2)

                                # Fill input fields
                                # This part needs to be made more robust. LinkedIn forms vary.
                                # You need to identify input fields by more specific attributes (name, data-test-id, etc.)
                                # and map them to your formData keys (userEmail, emailPassword etc. might not apply here)
                                # This example is very basic and likely needs significant customization.

                                inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="text"], input[type="email"], input[type="tel"], input[type="url"], input[type="number"]')
                                for input_tag in inputs:
                                     try:
                                         # Example: Trying to fill phone number (needs robust locator)
                                         label = input_tag.get_attribute("aria-label") or ""
                                         placeholder = input_tag.get_attribute("placeholder") or ""
                                         value = input_tag.get_attribute("value") or ""

                                         # This mapping logic is highly speculative and will likely fail on most forms.
                                         # You need to inspect actual application forms and write specific logic.
                                         if ("phone" in label.lower() or "phone" in placeholder.lower()) and value.strip() == "":
                                              # Replace with actual phone number logic if needed
                                              print(f"Attempting to fill phone field: {label} / {placeholder}")
                                              # input_tag.send_keys("YOUR_PHONE_NUMBER") # <<< FILL YOUR PHONE NUMBER OR REMOVE
                                         # Add more specific input filling logic here

                                     except Exception as input_e:
                                         print(f"Error filling input: {input_e}")
                                         continue

                                # Select dropdowns
                                # Similar to inputs, this needs specific logic per form.
                                dropdowns = driver.find_elements(By.CSS_SELECTOR, 'select')
                                for select_tag in dropdowns:
                                     try:
                                         label = select_tag.get_attribute("aria-label") or ""
                                         # Add specific dropdown selection logic here
                                         # Example: Select first option (likely not desired)
                                         # options = select_tag.find_elements(By.TAG_NAME, 'option')
                                         # if options: options[0].click()
                                     except Exception as select_e:
                                         print(f"Error selecting dropdown: {select_e}")
                                         continue

                                # Handle file uploads (Resume/Cover Letter)
                                # This requires finding the input[type='file'] element and sending the file path.
                                # Example (needs actual file path and locator):
                                # try:
                                #     upload_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]') # Find the file input element
                                #     upload_input.send_keys("path/to/your/resume.pdf") # Send the absolute path to your file
                                #     print("Attempted to upload resume.")
                                # except Exception as upload_e:
                                #     print(f"Error handling file upload: {upload_e}")
                                #     pass # File upload might be optional

                                # Check for 'Review' button (last step before submit)
                                try:
                                     review_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Review')] | //button[contains(span/text(), 'Review')] | //button[contains(span/span/text(), 'Review')] ")
                                     print("Found Review button.")
                                     review_btn.click()
                                     time.sleep(2)
                                     continue # Continue to the next step (submit)
                                except:
                                    pass # No review button, likely directly to next or submit

                                # Click next or submit button
                                try:
                                    # Prioritize Submit button if available
                                    submit_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Submit application')] | //button[contains(span/text(), 'Submit application')] | //button[contains(span/span/text(), 'Submit application')] | //button[contains(@aria-label, 'Apply')] | //button[contains(span/text(), 'Apply')] | //button[contains(span/span/text(), 'Apply')] ")
                                    print("Found Submit/Apply button. Clicking.")
                                    submit_btn.click()
                                    print(f"✅ Applied for job (ID: {job_id})")
                                    save_applied_job(job_id, applied_jobs)
                                    time.sleep(3) # Wait for submission to process

                                    # Look for the close button on the confirmation modal/page
                                    try:
                                        close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".artdeco-modal__dismiss")))
                                        close_btn.click()
                                        print("Closed application modal.")
                                        time.sleep(2)
                                    except:
                                        print("Could not find modal close button, continuing...")
                                        # If no modal close button, navigate back or refresh to exit application flow
                                        # driver.get("https://www.linkedin.com/jobs/") # Example navigation

                                    break # Exit the Easy Apply loop after submission
                                except:
                                    try:
                                        # If no Submit button, look for Next/Continue button
                                        next_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Continue')] | //button[contains(span/text(), 'Continue')] | //button[contains(span/span/text(), 'Continue')] | //button[contains(@aria-label, 'Next')] | //button[contains(span/text(), 'Next')] | //button[contains(span/span/text(), 'Next')] ")
                                        print(f"Found Next/Continue button. Clicking step {step}.")
                                        next_btn.click()
                                        step += 1
                                        time.sleep(2)
                                        continue # Continue to the next step
                                    except:
                                        # If neither Submit nor Next found, assume form completed or stuck
                                        print(f"❗ Easy Apply form stuck or completed at step {step}. Exiting form for job ID: {job_id}")
                                        # Attempt to close modal if it's still open
                                        try:
                                            cancel_btn = driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__dismiss")
                                            cancel_btn.click()
                                            print("Attempted to close stuck modal.")
                                            time.sleep(2)
                                        except:
                                            print("Could not find cancel button for stuck modal.")
                                        break # Exit the Easy Apply loop

                        else: # Not an Easy Apply job
                            print("Not an Easy Apply job.")
                            company_name = "Unknown"
                            try:
                                # Attempt to get company name from job details pane
                                company_element = driver.find_element(By.CSS_SELECTOR, '.jobs-unified-top-card__company-name a')
                                company_name = company_element.text.strip()
                                print(f"Found company name: {company_name}")
                            except Exception as company_e:
                                print(f"Could not find company name: {company_e}")
                                pass # Continue if company name not found
                            print(f"External link for job ID {job_id}: {driver.current_url}")
                            external_links.append((company_name, driver.current_url))

                    except Exception as easy_apply_check_e:
                        print(f"Could not find Easy Apply button or encountered error: {easy_apply_check_e}")
                        # If Easy Apply button not found, it's likely an external application
                        company_name = "Unknown"
                        try:
                            company_element = driver.find_element(By.CSS_SELECTOR, '.jobs-unified-top-card__company-name a')
                            company_name = company_element.text.strip()
                            print(f"Found company name (external): {company_name}")
                        except Exception as company_e:
                            print(f"Could not find company name (external): {company_e}")
                            pass
                        print(f"External link for job ID {job_id}: {driver.current_url}")
                        external_links.append((company_name, driver.current_url))

                except Exception as job_process_e:
                    print(f"Error processing job {i+1}: {job_process_e}")
                    continue # Continue to the next job even if one fails

        # --- Send external job links ---
        if external_links:
            send_email(user_email, email_password, "LinkedIn Job Bot: Company Website Application Links", external_links)

        print("✅ All job searches and applications processed.")
        return jsonify({"success": True, "message": "Job automation completed."})

    except Exception as e:
        print(f"An error occurred during the bot run: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        # --- Clean up ---
        if driver:
            driver.quit()
            print("WebDriver quit.")

@app.route("/", methods=["GET"])
def home():
    return "Hello, your bot backend is running!"

if __name__ == '__main__':
    # Use 0.0.0.0 to make the server accessible externally (e.g., from your frontend)
    # debug=True is useful for development, but should be False in production
    app.run(host='0.0.0.0', port=5000, debug=True) 