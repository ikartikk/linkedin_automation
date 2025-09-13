import time
import os
from crewai.tools import tool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

@tool("linkedin_poster_tool")
def linkedin_poster_tool(post_data: dict) -> str:
    """
    Automates LinkedIn posting with Selenium (GitHub Actions compatible).
    Expects input as a dict: {"text": "..."}.
    Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment variables.
    """
    driver = None
    
    try:
        linkedin_email = os.getenv("LINKEDIN_EMAIL")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD")
        
        if not linkedin_email or not linkedin_password:
            return "Error: Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment."
        
        if not isinstance(post_data, dict) or "text" not in post_data:
            return "Error: post_data must be a dict with at least a 'text' key."
        
        post_text = post_data.get("text", "")
        
        # ✅ GitHub Actions compatible Chrome setup
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        chrome_options.add_argument("--disable-javascript")  # We'll enable it selectively
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Use /tmp for profile in GitHub Actions
        profile_dir = "/tmp/chrome_profile" if os.getenv("GITHUB_ACTIONS") else "./chrome_profile"
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        
        # Re-enable JavaScript for LinkedIn
        chrome_options.add_argument("--enable-javascript")
        
        driver = webdriver.Chrome(service=Service(), options=chrome_options)
        
        # Set up explicit waits
        wait = WebDriverWait(driver, 20)
        
        # Open LinkedIn login
        print("Opening LinkedIn login page...")
        driver.get("https://www.linkedin.com/login")
        
        # Wait for and check if we need to login
        try:
            wait.until(EC.presence_of_element_located((By.ID, "username")))
            
            if "login" in driver.current_url:
                print("Logging in...")
                username_field = driver.find_element(By.ID, "username")
                username_field.clear()
                username_field.send_keys(linkedin_email)
                
                password_field = driver.find_element(By.ID, "password")
                password_field.clear()
                password_field.send_keys(linkedin_password)
                password_field.send_keys(Keys.RETURN)
                
                # Wait for login to complete
                wait.until(lambda d: "login" not in d.current_url or "challenge" in d.current_url)
                
                # Handle potential CAPTCHA or verification
                if "challenge" in driver.current_url:
                    return "Error: LinkedIn requires additional verification. Please login manually first."
                    
        except TimeoutException:
            print("Already logged in or login page didn't load properly")
        
        # Navigate to feed
        print("Navigating to LinkedIn feed...")
        driver.get("https://www.linkedin.com/feed/")
        
        # Wait for feed to load and find the "Start a post" button
        print("Looking for 'Start a post' button...")
        try:
            # Try multiple possible selectors for the start post button
            start_post_selectors = [
                "//button//span[contains(text(), 'Start a post')]",
                "//button//strong[text()='Start a post']",
                "//div[contains(@class, 'share-box-feed-entry__trigger')]",
                "//button[contains(@class, 'share-box-feed-entry__trigger')]",
                "//span[text()='Start a post']/ancestor::button",
                "[data-test-id='share-box-trigger']"
            ]
            
            start_post = None
            for selector in start_post_selectors:
                try:
                    if selector.startswith("//"):
                        start_post = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        start_post = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    print(f"Found start post button with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not start_post:
                # Fallback: look for any clickable element that might be the post trigger
                print("Trying fallback selectors...")
                fallback_selectors = [
                    "//div[contains(text(), 'Start a post')]",
                    "//div[contains(@class, 'share-box')]//button"
                ]
                for selector in fallback_selectors:
                    try:
                        start_post = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except TimeoutException:
                        continue
            
            if not start_post:
                return "Error: Could not find 'Start a post' button. LinkedIn layout may have changed."
            
            # Click the start post button
            driver.execute_script("arguments[0].click();", start_post)
            print("Clicked 'Start a post' button")
            
        except TimeoutException:
            return "Error: Timeout waiting for 'Start a post' button to appear."
        
        # Wait for post composer to open
        print("Waiting for post composer...")
        try:
            post_box_selectors = [
                "//div[contains(@class,'ql-editor')]",
                "//div[@role='textbox']",
                "//div[contains(@class, 'editor-content')]",
                "[data-placeholder*='share']"
            ]
            
            post_box = None
            for selector in post_box_selectors:
                try:
                    if selector.startswith("//"):
                        post_box = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        post_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not post_box:
                return "Error: Could not find post text box."
            
            # Clear any existing text and enter new text
            post_box.clear()
            post_box.click()
            post_box.send_keys(post_text)
            print("Entered post text")
            
        except TimeoutException:
            return "Error: Timeout waiting for post composer to open."
        
        # Wait a moment for text to be entered
        time.sleep(2)
        
        # Find and click post button
        print("Looking for Post button...")
        try:
            post_button_selectors = [
                "//button[contains(@class,'share-actions__primary-action')]//span[text()='Post']",
                "//button//span[text()='Post']",
                "//button[contains(@class, 'share-actions__primary-action')]",
                "[data-test-id='share-post-button']"
            ]
            
            post_button = None
            for selector in post_button_selectors:
                try:
                    if selector.startswith("//"):
                        post_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        post_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not post_button:
                return "Error: Could not find Post button."
            
            # Click post button
            driver.execute_script("arguments[0].click();", post_button)
            print("Clicked Post button")
            
            # Wait for post to be published
            time.sleep(5)
            
            return "✅ Successfully posted to LinkedIn!"
            
        except TimeoutException:
            return "Error: Timeout waiting for Post button."
            
    except Exception as e:
        return f"Error: {str(e)}"
        
    finally:
        if driver:
            driver.quit()
            print("Browser closed")















# import time
# import os
# from crewai.tools import tool
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options

# @tool("linkedin_poster_tool")
# def linkedin_poster_tool(post_data: dict) -> str:
#     """
#     Automates LinkedIn posting with Selenium (Chrome version).
#     Expects input as a dict: {"text": "..."}.
#     Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment variables.
#     """
#     driver = None
#     linkedin_email = os.getenv("LINKEDIN_EMAIL")
#     linkedin_password = os.getenv("LINKEDIN_PASSWORD")
#     if not linkedin_email or not linkedin_password:
#         return "Error: Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment."
    
#     if not isinstance(post_data, dict) or "text" not in post_data:
#         return "Error: post_data must be a dict with at least a 'text' key."

#     post_text = post_data.get("text", "")
#     #image_path = post_data.get("image_path")

#     # ✅ Chrome setup
#     chrome_options = Options()
#     chrome_options.add_argument("--start-maximized")
#     # Reuse Chrome profile to avoid re-login each time
#     chrome_options.add_argument(r"user-data-dir=/tmp/chrome_profile")
#     chrome_options.add_argument("--headless=new")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")

#     driver = webdriver.Chrome(service=Service(), options=chrome_options)

#     # Open LinkedIn login
#     driver.get("https://www.linkedin.com/login")
#     time.sleep(3)

#     # If not already logged in, do login
#     if "login" in driver.current_url:
#         driver.find_element(By.ID, "username").send_keys(linkedin_email)
#         driver.find_element(By.ID, "password").send_keys(linkedin_password)
#         driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
#         time.sleep(5)

#     # Navigate to feed
#     driver.get("https://www.linkedin.com/feed/")
#     time.sleep(5)

#     start_post = driver.find_element(By.XPATH, "//button//strong[text()='Start a post']")
#     start_post.click()
#     time.sleep(3)

#     # Enter text
#     post_box = driver.find_element(By.XPATH, "//div[contains(@class,'ql-editor')]")
#     post_box.send_keys(post_text)
#     time.sleep(2)

#     # add_media_btn = driver.find_element(By.XPATH, "//button[@aria-label='Add media']")
#     # add_media_btn.click()
#     # time.sleep(2)

#     # # Find file input and send file path
#     # file_input = driver.find_element(By.XPATH, "//input[@type='file']")
#     # file_input.send_keys(os.path.abspath(image_path))

#     # # Wait for upload preview
#     # time.sleep(5)

#     # next_button = driver.find_element(By.XPATH, "//button[@aria-label='Next']")
#     # next_button.click()
#     # time.sleep(2)

#     # Post
#     post_button = driver.find_element(By.XPATH, "//button[contains(@class,'share-actions__primary-action')]//span[text()='Post']")
#     post_button.click()
#     time.sleep(10)


#     driver.quit()
            
