import unittest
from unittest import skipIf
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import selenium_cotestpilot
import json
import os
import logging
from datetime import datetime

# Add logging configuration
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TestGoogleNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)
        logger.info("Test suite setup complete")
        

    @classmethod
    def tearDownClass(cls):
        """Clean up once after all tests"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
            logger.info("Browser session closed")

    def setUp(self):
        """Reset browser state before each test"""
        self.driver.delete_all_cookies()
        logger.info("Test setup: Cookies cleared")

    def test_google_navigation(self):
        """Test navigation to Google homepage"""
        logger.info("Running test_google_navigation")
        try:
            self.driver.get('https://www.google.com')
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            result = self.driver.ai_check()
            logger.info(f"Successfully loaded Google! Page title: {self.driver.title}")
            self.assertIn("Google", self.driver.title)
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise

    def test_ai_check_with_testers(self):
        """Test AI checks with specific testing personas"""
        logger.info("Running test_ai_check_with_testers")
        self.driver.get('https://www.google.com')
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        result = self.driver.ai_check(
            testers=['Jason', 'Alice'],
            label='google_homepage'
        )
        
        self.assertTrue(hasattr(result, 'raw_response'))
        self.assertTrue(hasattr(result, 'profile'))
        self.assertEqual(result.profile, 'default')

    def test_ai_check_with_custom_rules(self):
        """Test AI checks with custom accessibility rules"""
        logger.info("Running test_ai_check_with_custom_rules")
        self.driver.get('https://www.google.com')
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        result = self.driver.ai_check(
            custom_rules={
                'check_contrast': True,
                'min_font_size': 12
            },
            custom_prompt="Pay special attention to accessibility issues"
        )
        
        self.assertTrue(hasattr(result, 'raw_response'))
        self.assertIsInstance(result.raw_response, dict)

    def test_check_result_structure(self):
        """Test the basic structure of CheckResult object"""
        logger.info("Running test_check_result_structure")
        self.driver.get('https://www.google.com')
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        result = self.driver.ai_check()
        
        required_fields = ['timestamp', 'url', 'bugs', 'raw_response', 'profile']
        for field in required_fields:
            self.assertTrue(hasattr(result, field), f"Missing field: {field}")
        
        self.assertIsInstance(result.timestamp, datetime)
        self.assertEqual(result.url, 'https://www.google.com/')

    def test_bug_report_format(self):
        """Test the structure of individual bug reports"""
        logger.info("Running test_bug_report_format")
        self.driver.get('https://www.google.com')
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        result = self.driver.ai_check()
        
        self.assertIsInstance(result.bugs, list)
        
        if result.bugs:
            bug = result.bugs[0]
            required_bug_fields = [
                'title',
                'severity',
                'description',
                'why_fix',
                'how_to_fix',
                'confidence'
            ]
            
            for field in required_bug_fields:
                self.assertIn(field, bug)
            
            self.assertIsInstance(bug['confidence'], float)
            self.assertGreaterEqual(bug['confidence'], 0)
            self.assertLessEqual(bug['confidence'], 1)

    def test_json_output_file(self):
        """Test that results are properly saved to JSON file"""
        logger.info("Running test_json_output_file")
        test_label = 'test_output'
        test_dir = os.path.join(os.path.dirname(__file__), 'test_results')
        os.makedirs(test_dir, exist_ok=True)
        
        self.driver.get('https://www.google.com')
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        result = self.driver.ai_check(
            custom_prompt="""
            Analyze the page for issues. If no real issues are found, generate 2  
            fictional issues for testing purposes. Make the issues sound plausible but clearly 
            marked as test data.
            """,
            label=test_label,
            output_dir=test_dir
        )
        
        self.assertTrue(len(result.bugs) > 0, "No issues were found in the results")
        
        self.assertTrue(os.path.exists(result.output_file))
        
        with open(result.output_file, 'r') as f:
            saved_results = json.load(f)
        
        self.assertIn('timestamp', saved_results)
        self.assertIn('url', saved_results)
        self.assertIn('testers_results', saved_results)
        self.assertTrue(len(saved_results['testers_results']) > 0, "No issues were found in the saved JSON file")

    def test_report_generation(self):
        """Test that AI check report generation works correctly"""
        logger.info("Running test_report_generation")
        self.driver.get('https://www.google.com')
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        report_path = self.driver.ai_report()
        self.assertTrue(os.path.exists(report_path))

if __name__ == '__main__':
    unittest.main(verbosity=2)