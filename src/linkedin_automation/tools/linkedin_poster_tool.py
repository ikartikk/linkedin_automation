# import time
# import os
# from crewai.tools import tool
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys

# @tool("linkedin_poster_tool")
# def linkedin_poster_tool(post_text: str) -> str:
#     """
#     Automates LinkedIn posting with Selenium (Safari version).
#     Expects input as plain text (no image).
#     Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment variables.
#     """
#     try:
#         linkedin_email = os.getenv("LINKEDIN_EMAIL")
#         linkedin_password = os.getenv("LINKEDIN_PASSWORD")
#         if not linkedin_email or not linkedin_password:
#             return "Error: Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment."

#         # ✅ Use Safari
#         driver = webdriver.Safari()

#         # Open LinkedIn login
#         driver.get("https://www.linkedin.com/login")
#         time.sleep(2)

#         # Login
#         driver.find_element(By.ID, "username").send_keys(linkedin_email)
#         driver.find_element(By.ID, "password").send_keys(linkedin_password, Keys.RETURN)
#         time.sleep(3)

#         # Navigate to feed
#         driver.get("https://www.linkedin.com/feed/")
#         time.sleep(3)

#         # Start post
#         start_post = driver.find_element(By.CLASS_NAME, "share-box-feed-entry__trigger")
#         start_post.click()
#         time.sleep(2)

#         # Enter text
#         post_box = driver.find_element(By.CLASS_NAME, "ql-editor")
#         post_box.send_keys(post_text)
#         time.sleep(2)

#         # Post
#         post_button = driver.find_element(By.XPATH, "//button[contains(., 'Post')]")
#         post_button.click()
#         time.sleep(5)

#         driver.quit()
#         return "✅ LinkedIn post (text only) published successfully."

#     except Exception as e:
#         return f"❌ LinkedIn posting failed (Safari): {str(e)}"



import time
import os
from crewai.tools import tool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

@tool("linkedin_poster_tool")
def linkedin_poster_tool(post_text: str) -> str:
    """
    Automates LinkedIn posting with Selenium (Chrome version).
    Expects input as plain text (no image).
    Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment variables.
    """
    driver = None
    try:
        linkedin_email = os.getenv("LINKEDIN_EMAIL")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD")
        if not linkedin_email or not linkedin_password:
            return "Error: Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in environment."

        # ✅ Chrome setup
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        # Reuse Chrome profile to avoid re-login each time
        chrome_options.add_argument(r"user-data-dir=/tmp/chrome_profile")

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

        # Post
        post_button = driver.find_element(By.XPATH, "//button[contains(@class,'share-actions__primary-action')]//span[text()='Post']")
        post_button.click()
        time.sleep(10)

        return "✅ LinkedIn post (text only) published successfully."

    except Exception as e:
        return f"❌ LinkedIn posting failed: {str(e)}"

    finally:
        if driver:
            driver.quit()
            
