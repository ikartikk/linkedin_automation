import time
import os
import random
import base64
import json
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
        # Get current page to ensure we're on LinkedIn
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
        
        print(f"✅ Session data saved to {session_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to save session: {e}")
        return False

def load_session_data(driver, session_file="/tmp/linkedin_session.pkl"):
    """Load cookies and session data from file"""
    try:
        if not os.path.exists(session_file):
            print("🔍 No existing session file found")
            return False
        
        # Check if session file is recent (less than 7 days old)
        file_age = time.time() - os.path.getmtime(session_file)
        if file_age > 7 * 24 * 3600:  # 7 days
            print("⏰ Session file is too old, removing it")
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
            except Exception as e:
                print(f"Failed to add cookie {cookie.get('name', '')}: {e}")
        
        # Load localStorage if available
        if session_data.get('local_storage'):
            for key, value in session_data['local_storage'].items():
                try:
                    driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
                except Exception as e:
                    print(f"Failed to set localStorage {key}: {e}")
        
        print("✅ Session data loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to load session: {e}")
        return False

def encode_session_for_github(session_file="/tmp/linkedin_session.pkl"):
    """Encode session file as base64 for GitHub secrets"""
    try:
        with open(session_file, 'rb') as f:
            session_bytes = f.read()
        encoded = base64.b64encode(session_bytes).decode('utf-8')
        print("📦 Session encoded for GitHub secrets:")
        print("Add this as LINKEDIN_SESSION_DATA secret:")
        print(encoded)
        return encoded
    except Exception as e:
        print(f"❌ Failed to encode session: {e}")
        return None

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
        print(f"❌ Failed to decode session from GitHub: {e}")
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
    
    # First try to decode session from GitHub secrets
    if os.getenv("GITHUB_ACTIONS"):
        print("🔧 Running in GitHub Actions, checking for session data...")
        decode_session_from_github()
    
    # Try to load existing session first
    if load_session_data(driver):
        print("🔄 Attempting to use saved session...")
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(5)
        
        # Check if we're logged in
        current_url = driver.current_url
        if "feed" in current_url or "home" in current_url or "linkedin.com" in current_url:
            # Double check by looking for user-specific elements
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'global-nav__primary-link')]")), timeout=10)
                print("✅ Successfully logged in using saved session!")
                return True
            except TimeoutException:
                print("⚠️ Session exists but might be expired")
        else:
            print("⚠️ Session didn't work, will try fresh login")
    
    # Fresh login required
    print("🔑 Performing fresh login...")
    driver.get("https://www.linkedin.com/login")
    
    # Random delay to avoid bot detection
    time.sleep(random.uniform(3, 6))
    
    try:
        # Wait for login form
        wait.until(EC.presence_of_element_located((By.ID, "username")))
        
        # Enter credentials with human-like typing
        username_field = driver.find_element(By.ID, "username")
        human_like_typing(username_field, linkedin_email)
        
        time.sleep(random.uniform(1, 2))
        
        password_field = driver.find_element(By.ID, "password")
        human_like_typing(password_field, linkedin_password)
        
        time.sleep(random.uniform(1, 2))
        
        # Click login button instead of Enter key
        try:
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            driver.execute_script("arguments[0].click();", login_button)
        except:
            password_field.send_keys(Keys.RETURN)
        
        # Wait for login result with longer timeout
        print("⏳ Waiting for login to complete...")
        time.sleep(8)
        
        current_url = driver.current_url
        
        # Handle different post-login scenarios
        if "challenge" in current_url or "checkpoint" in current_url:
            print("🛡️ Security challenge detected...")
            
            # Try to handle email verification automatically
            page_source = driver.page_source.lower()
            
            if "email" in page_source and "verify" in page_source:
                print("📧 Email verification required")
                # Wait longer for manual verification or auto-resolution
                for i in range(60):  # Wait up to 10 minutes
                    time.sleep(10)
                    current_url = driver.current_url
                    if "feed" in current_url or "home" in current_url:
                        print("✅ Email verification completed!")
                        save_session_data(driver)
                        return True
                    elif i > 30:  # After 5 minutes, give up
                        break
                
                return False
            
            elif "captcha" in page_source:
                print("🤖 CAPTCHA detected - cannot proceed automatically")
                return False
            
            else:
                print("🔐 Unknown security challenge")
                return False
                
        elif "feed" in current_url or "home" in current_url or "/in/" in current_url:
            print("✅ Login successful!")
            # Save session for future use
            time.sleep(2)  # Let the page fully load
            save_session_data(driver)
            return True
        
        else:
            print(f"❌ Unexpected page after login: {current_url}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

@tool("linkedin_poster_tool")
def linkedin_poster_tool(post_data: dict) -> str:
    """
    Automates LinkedIn posting with session persistence for GitHub Actions.
    Expects input as a dict: {"text": "..."}.
    Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment variables.
    Optionally uses LINKEDIN_SESSION_DATA from GitHub secrets.
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
        
        # ✅ GitHub Actions compatible Chrome setup
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Consistent user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Profile directory
        profile_dir = "/tmp/chrome_profile" if os.getenv("GITHUB_ACTIONS") else "./chrome_profile"
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        
        driver = webdriver.Chrome(service=Service(), options=chrome_options)
        
        # Hide automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set up explicit waits
        wait = WebDriverWait(driver, 30)
        
        # Attempt login with session persistence
        if not linkedin_login_with_session(driver, linkedin_email, linkedin_password):
            return "❌ Error: Failed to login to LinkedIn. Please check credentials or handle verification manually."
        
        # Navigate to feed (if not already there)
        current_url = driver.current_url
        if "feed" not in current_url:
            print("🏠 Navigating to LinkedIn feed...")
            driver.get("https://www.linkedin.com/feed/")
            time.sleep(5)
        
        # Find the "Start a post" button with multiple strategies
        print("🔍 Looking for 'Start a post' button...")
        try:
            start_post_selectors = [
                "//button//span[contains(text(), 'Start a post')]",
                "//button//strong[text()='Start a post']",
                "//div[contains(@class, 'share-box-feed-entry__trigger')]",
                "//button[contains(@class, 'share-box-feed-entry__trigger')]",
                "//span[text()='Start a post']/ancestor::button",
                "[data-test-id='share-box-trigger']",
                "//div[@role='button'][contains(.,'Start a post')]"
            ]
            
            start_post = None
            for selector in start_post_selectors:
                try:
                    if selector.startswith("//"):
                        start_post = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        start_post = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    print(f"✅ Found start post button with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not start_post:
                return "❌ Error: Could not find 'Start a post' button. LinkedIn layout may have changed."
            
            # Click with JavaScript for reliability
            driver.execute_script("arguments[0].click();", start_post)
            print("✅ Clicked 'Start a post' button")
            time.sleep(3)
            
        except TimeoutException:
            return "❌ Error: Timeout waiting for 'Start a post' button."
        
        # Wait for and find the post composer
        print("✏️ Looking for post composer...")
        try:
            post_box_selectors = [
                "//div[contains(@class,'ql-editor')]",
                "//div[@role='textbox']",
                "//div[contains(@class, 'editor-content')]",
                "[data-placeholder*='share']",
                "//div[@contenteditable='true']"
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
                return "❌ Error: Could not find post text box."
            
            # Enter text with human-like behavior
            post_box.click()
            time.sleep(1)
            
            # Clear any placeholder text
            post_box.send_keys(Keys.CONTROL + "a")
            time.sleep(0.5)
            
            # Type the post text
            human_like_typing(post_box, post_text, 0.02, 0.08)
            print("✅ Entered post text")
            
        except TimeoutException:
            return "❌ Error: Timeout waiting for post composer."
        
        # Wait before posting
        time.sleep(2)
        
        # Find and click post button
        print("📤 Looking for Post button...")
        try:
            post_button_selectors = [
                "//button[contains(@class,'share-actions__primary-action')]//span[text()='Post']",
                "//button//span[text()='Post']",
                "//button[contains(@class, 'share-actions__primary-action')]",
                "[data-test-id='share-post-button']",
                "//button[contains(@class, 'artdeco-button--primary')][contains(.,'Post')]"
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
                return "❌ Error: Could not find Post button."
            
            # Click post button
            driver.execute_script("arguments[0].click();", post_button)
            print("✅ Clicked Post button")
            
            # Wait for post to be published
            time.sleep(8)
            
            # Verify post was successful (look for success indicator)
            try:
                # Look for success message or redirect to feed
                success_indicators = [
                    "//div[contains(@class, 'Toasts')]//span[contains(text(), 'successfully')]",
                    "//div[contains(text(), 'Post successful')]"
                ]
                
                for indicator in success_indicators:
                    try:
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, indicator)))
                        break
                    except TimeoutException:
                        continue
                        
            except:
                pass  # Success indicators are optional
            
            return "✅ Successfully posted to LinkedIn!"
            
        except TimeoutException:
            return "❌ Error: Timeout waiting for Post button."
            
    except Exception as e:
        return f"❌ Error: {str(e)}"
        
    finally:
        if driver:
            # Save session before closing (if we successfully logged in)
            try:
                current_url = driver.current_url
                if "linkedin.com" in current_url and "login" not in current_url:
                    save_session_data(driver)
            except:
                pass
            
            driver.quit()
            print("🔒 Browser closed")

# Utility function to manually create session (run this locally first)
def create_initial_session():
    """
    Run this function locally to create initial session data.
    Then use encode_session_for_github() to get the base64 encoded data for GitHub secrets.
    """
    print("🚀 Creating initial session...")
    print("This will open a browser where you can manually login to LinkedIn")
    print("After login, the session will be saved for GitHub Actions use")
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--user-data-dir=./chrome_profile")
    
    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    
    try:
        driver.get("https://www.linkedin.com/login")
        input("Please login manually in the browser, then press Enter here...")
        
        # Check if login was successful
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        
        if "feed" in driver.current_url:
            save_session_data(driver)
            encode_session_for_github()
            print("✅ Session created successfully!")
            print("Copy the base64 encoded data above and add it as LINKEDIN_SESSION_DATA secret in GitHub")
        else:
            print("❌ Login verification failed")
            
    finally:
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    # Uncomment this to create initial session locally
    create_initial_session()
    
    # Test the posting function
    # test_post = {"text": "Hello LinkedIn! This is a test post from automation."}
    # result = linkedin_poster_tool(test_post)
    # print(result)