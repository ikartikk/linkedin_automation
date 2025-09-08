import time
import os
from crewai.tools import tool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

@tool("linkedin_poster_tool")
def linkedin_poster_tool(post_data: dict) -> str:
    """
    Automates LinkedIn posting with Selenium (Chrome version).
    Expects input as a dict: {"text": "...", "image_path": "..."}.
    Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment variables.
    """
    driver = None
    linkedin_email = os.getenv("LINKEDIN_EMAIL")
    linkedin_password = os.getenv("LINKEDIN_PASSWORD")
    if not linkedin_email or not linkedin_password:
        return "Error: Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment."
    
    if not isinstance(post_data, dict) or "text" not in post_data:
        return "Error: post_data must be a dict with at least a 'text' key."

    post_text = post_data.get("text", "")
    image_path = post_data.get("image_path")

    # ✅ Chrome setup
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    # Reuse Chrome profile to avoid re-login each time
    chrome_options.add_argument(r"user-data-dir=/tmp/chrome_profile")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    # Open LinkedIn login
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)

    # If not already logged in, do login
    if "login" in driver.current_url:
        driver.find_element(By.ID, "username").send_keys(linkedin_email)
        driver.find_element(By.ID, "password").send_keys(linkedin_password)
        driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
        time.sleep(5)

    # Navigate to feed
    driver.get("https://www.linkedin.com/feed/")
    time.sleep(5)

    start_post = driver.find_element(By.XPATH, "//button//strong[text()='Start a post']")
    start_post.click()
    time.sleep(3)

    # Enter text
    post_box = driver.find_element(By.XPATH, "//div[contains(@class,'ql-editor')]")
    post_box.send_keys(post_text)
    time.sleep(2)

    add_media_btn = driver.find_element(By.XPATH, "//button[@aria-label='Add media']")
    add_media_btn.click()
    time.sleep(2)

    # Find file input and send file path
    file_input = driver.find_element(By.XPATH, "//input[@type='file']")
    file_input.send_keys(os.path.abspath(image_path))

    # Wait for upload preview
    time.sleep(5)

    next_button = driver.find_element(By.XPATH, "//button[@aria-label='Next']")
    next_button.click()
    time.sleep(2)

    # Post
    post_button = driver.find_element(By.XPATH, "//button[contains(@class,'share-actions__primary-action')]//span[text()='Post']")
    post_button.click()
    time.sleep(10)


    driver.quit()
            
