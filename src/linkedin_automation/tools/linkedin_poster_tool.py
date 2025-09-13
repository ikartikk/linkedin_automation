import time
import os
import random
import base64
import pickle
from crewai.tools import tool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def save_session_data(driver, session_file="/tmp/linkedin_session.pkl"):
    """Save cookies and session data to file"""
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(2)
        
        session_data = {
            'cookies': driver.get_cookies(),
            'local_storage': driver.execute_script("return window.localStorage;") or {},
            'session_storage': driver.execute_script("return window.sessionStorage;") or {},
            'user_agent': driver.execute_script("return navigator.userAgent;")
        }
        
        with open(session_file, 'wb') as f:
            pickle.dump(session_data, f)
        
        print("✅ Session data saved")
        return True
    except Exception as e:
        print(f"❌ Failed to save session: {e}")
        return False

def load_session_data(driver, session_file="/tmp/linkedin_session.pkl"):
    """Load cookies and session data from file"""
    try:
        if not os.path.exists(session_file):
            return False
        
        # Check if session file is recent (less than 7 days old)
        file_age = time.time() - os.path.getmtime(session_file)
        if file_age > 7 * 24 * 3600:  # 7 days
            os.remove(session_file)
            return False
        
        with open(session_file, 'rb') as f:
            session_data = pickle.load(f)
        
        # Navigate to LinkedIn first
        driver.get("https://www.linkedin.com")
        time.sleep(2)
        
        # Load cookies
        for cookie in session_data['cookies']:
            try:
                driver.add_cookie(cookie)
            except Exception:
                continue
        
        # Load localStorage if available
        if session_data.get('local_storage'):
            for key, value in session_data['local_storage'].items():
                try:
                    driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
                except Exception:
                    continue
        
        print("✅ Session data loaded")
        return True
    except Exception as e:
        print(f"❌ Failed to load session: {e}")
        return False

def decode_session_from_github():
    """Decode session from GitHub secret"""
    try:
        session_data_b64 = os.getenv("LINKEDIN_SESSION_DATA")
        if not session_data_b64:
            return False
        
        session_bytes = base64.b64decode(session_data_b64)
        session_file = "/tmp/linkedin_session.pkl"
        
        with open(session_file, 'wb') as f:
            f.write(session_bytes)
        
        print("✅ Session decoded from GitHub secrets")
        return True
    except Exception as e:
        print(f"❌ Failed to decode session: {e}")
        return False

def human_like_typing(element, text, min_delay=0.05, max_delay=0.15):
    """Type text with human-like delays"""
    element.clear()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

def linkedin_login_with_session(driver, linkedin_email, linkedin_password):
    """Login with session persistence"""
    wait = WebDriverWait(driver, 20)
    
    # If running in GitHub Actions, decode session from secrets
    if os.getenv("GITHUB_ACTIONS"):
        print("🔧 Running in GitHub Actions, loading session...")
        decode_session_from_github()
    
    # Try to load existing session first
    if load_session_data(driver):
        print("🔄 Testing saved session...")
        driver.get("https://www.linkedin.com/feed/")
        print("⏳ LinkedIn feed loading...")
        time.sleep(5)
        
        # Check if we're logged in
        current_url = driver.current_url
        if "feed" in current_url or "home" in current_url:
            try:
                # Double check by looking for navigation elements
                wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'global-nav__primary-link')]")))
                print("✅ Session login successful!")
                return True
            except TimeoutException:
                print("⚠️ Session expired, will try fresh login")
    
    # Fresh login required
    print("🔑 Performing fresh login...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(random.uniform(3, 6))
    
    try:
        wait.until(EC.presence_of_element_located((By.ID, "username")))
        
        # Enter credentials with human-like typing
        username_field = driver.find_element(By.ID, "username")
        human_like_typing(username_field, linkedin_email)
        time.sleep(random.uniform(1, 2))
        
        password_field = driver.find_element(By.ID, "password")
        human_like_typing(password_field, linkedin_password)
        time.sleep(random.uniform(1, 2))
        
        # Click login button
        try:
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            driver.execute_script("arguments[0].click();", login_button)
        except:
            password_field.send_keys(Keys.RETURN)
        
        print("⏳ Waiting for login...")
        time.sleep(8)
        
        current_url = driver.current_url
        
        # Handle post-login scenarios
        if "challenge" in current_url or "checkpoint" in current_url:
            print("🛡️ Security challenge detected, waiting...")
            # Wait for challenge to resolve
            for i in range(30):  # Wait up to 5 minutes
                time.sleep(10)
                current_url = driver.current_url
                if "feed" in current_url or "home" in current_url:
                    print("✅ Challenge resolved!")
                    save_session_data(driver)
                    return True
            return False
                
        elif "feed" in current_url or "home" in current_url:
            print("✅ Login successful!")
            save_session_data(driver)
            return True
        
        return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

@tool("linkedin_poster_tool")
def linkedin_poster_tool(post_data: dict) -> str:
    """
    Automates LinkedIn posting with session persistence.
    Expects input as a dict: {"text": "..."}.
    Requires LINKEDIN_EMAIL, LINKEDIN_PASSWORD, and LINKEDIN_SESSION_DATA in environment.
    """
    driver = None
    
    try:
        linkedin_email = os.getenv("LINKEDIN_EMAIL")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD")
        
        if not linkedin_email or not linkedin_password:
            return "❌ Error: Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment."
        
        if not isinstance(post_data, dict) or "text" not in post_data:
            return "❌ Error: post_data must be a dict with at least a 'text' key."
        
        post_text = post_data.get("text", "")
        
        # Chrome setup for GitHub Actions
        chrome_options = Options()
        #chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        os.getenv("GITHUB_ACTIONS") = True
        # Profile directory
        profile_dir = "/tmp/chrome_profile" if os.getenv("GITHUB_ACTIONS") else "./chrome_profile"
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        
        driver = webdriver.Chrome(service=Service(), options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        wait = WebDriverWait(driver, 30)
        
        # Login with session persistence
        if not linkedin_login_with_session(driver, linkedin_email, linkedin_password):
            return "❌ Error: Failed to login to LinkedIn."
        
        # Navigate to feed if needed
        current_url = driver.current_url
        if "feed" not in current_url:
            driver.get("https://www.linkedin.com/feed/")
            time.sleep(5)
        
        # Find "Start a post" button
        print("🔍 Looking for 'Start a post' button...")
        start_post_selectors = [
            "//button//span[contains(text(), 'Start a post')]",
            "//button//strong[text()='Start a post']",
            "//div[contains(@class, 'share-box-feed-entry__trigger')]",
            "//button[contains(@class, 'share-box-feed-entry__trigger')]",
            "//span[text()='Start a post']/ancestor::button"
        ]
        
        start_post = None
        for selector in start_post_selectors:
            try:
                start_post = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                break
            except TimeoutException:
                continue
        
        if not start_post:
            return "❌ Error: Could not find 'Start a post' button."
        
        driver.execute_script("arguments[0].click();", start_post)
        print("✅ Clicked 'Start a post' button")
        time.sleep(3)
        
        # Find post composer
        print("✏️ Looking for post composer...")
        post_box_selectors = [
            "//div[contains(@class,'ql-editor')]",
            "//div[@role='textbox']",
            "//div[contains(@class, 'editor-content')]",
            "//div[@contenteditable='true']"
        ]
        
        post_box = None
        for selector in post_box_selectors:
            try:
                post_box = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                break
            except TimeoutException:
                continue
        
        if not post_box:
            return "❌ Error: Could not find post text box."
        
        # Enter text
        post_box.click()
        time.sleep(1)
        post_box.send_keys(Keys.CONTROL + "a")
        time.sleep(0.5)
        human_like_typing(post_box, post_text, 0.02, 0.08)
        print("✅ Entered post text")
        time.sleep(2)
        
        # Find and click post button
        print("📤 Looking for Post button...")
        post_button_selectors = [
            "//button[contains(@class,'share-actions__primary-action')]//span[text()='Post']",
            "//button//span[text()='Post']",
            "//button[contains(@class, 'share-actions__primary-action')]",
            "//button[contains(@class, 'artdeco-button--primary')][contains(.,'Post')]"
        ]
        
        post_button = None
        for selector in post_button_selectors:
            try:
                post_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                break
            except TimeoutException:
                continue
        
        if not post_button:
            return "❌ Error: Could not find Post button."
        
        driver.execute_script("arguments[0].click();", post_button)
        print("✅ Clicked Post button")
        time.sleep(8)
        
        return "✅ Successfully posted to LinkedIn!"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"
        
    finally:
        if driver:
            # Save session before closing
            try:
                current_url = driver.current_url
                if "linkedin.com" in current_url and "login" not in current_url:
                    save_session_data(driver)
            except:
                pass
            driver.quit()
            print("🔒 Browser closed")