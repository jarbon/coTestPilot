"""
Playwright AI Testing Suite (Async Version)
=========================================

This test suite demonstrates the usage of playwright-cotestpilot for automated AI-powered testing.

How to run these tests:
1. From command line:
   python -m unittest test.py

2. With verbose output:
   python -m unittest -v test.py

Requirements:
- playwright >= 1.41.0
- playwright-cotestpilot >= 0.1.0

Note: Before running, ensure browsers are installed:
    playwright install chromium

For more information, visit:
https://github.com/your-repo/playwright-cotestpilot
"""

import unittest
import asyncio
from unittest import skipIf
from playwright.async_api import async_playwright
import time
import playwright_async_cotestpilot
import json
import os
import logging

# Add logging configuration
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TestGoogleNavigation(unittest.IsolatedAsyncioTestCase):  # Changed base class
    async def asyncSetUp(self):  # Changed to async setup
        """Set up test environment before each test"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def asyncTearDown(self):  # Changed to async teardown
        """Clean up after each test"""
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def test_google_navigation(self):  # Made test async
        """Test navigation to Google homepage"""
        try:
            logger.info("Navigating to Google...")
            await self.page.goto('https://www.google.com')
            await self.page.wait_for_load_state('networkidle')
            
            result =  await self.page.ai_check()
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise
        
        await asyncio.sleep(1)

    async def test_ai_check_with_testers(self):  # Made test async
        """Test AI checks with specific testing personas"""
        await self.page.goto('https://www.google.com')
        await self.page.wait_for_load_state('networkidle')
        
        result = await self.page.ai_check(
            testers=['Jason', 'Alice'],
            label='google_homepage'
        )
        
        # Verify the result structure
        self.assertTrue(hasattr(result, 'raw_response'))
        self.assertTrue(hasattr(result, 'profile'))
        self.assertEqual(result.profile, 'default')
        
        await asyncio.sleep(1)

    async def test_ai_check_with_custom_rules(self):  # Made test async
        """Test AI checks with custom accessibility rules"""
        await self.page.goto('https://www.google.com')
        await self.page.wait_for_load_state('networkidle')
        
        result = await self.page.ai_check(
            custom_rules={
                'check_contrast': True,
                'min_font_size': 12
            },
            custom_prompt="Pay special attention to accessibility issues"
        )
        
        self.assertTrue(hasattr(result, 'raw_response'))
        self.assertIsInstance(result.raw_response, dict)
        
        await asyncio.sleep(2)

    async def test_check_result_structure(self):  # Made test async
        """Test the basic structure of CheckResult object"""
        await self.page.goto('https://www.google.com')
        await self.page.wait_for_load_state('networkidle')
        
        result = await self.page.ai_check()
        
        # Verify all required attributes are present
        required_fields = ['timestamp', 'url', 'bugs', 'raw_response', 'profile']
        for field in required_fields:
            self.assertTrue(hasattr(result, field), f"Missing field: {field}")
        
        # Verify timestamp is a datetime object
        from datetime import datetime
        self.assertIsInstance(result.timestamp, datetime)
        
        # Verify URL matches
        self.assertEqual(result.url, 'https://www.google.com/')

    async def test_bug_report_format(self):  # Made test async
        """Test the structure of individual bug reports"""
        await self.page.goto('https://www.google.com')
        await self.page.wait_for_load_state('networkidle')
        
        result = await self.page.ai_check()
        
        # Check if bugs is a list
        self.assertIsInstance(result.bugs, list)
        
        # If any bugs are found, verify their structure
        if result.bugs:
            bug = result.bugs[0]  # Test first bug
            required_bug_fields = [
                'title',
                'severity',
                'description',
                'why_fix',
                'how_to_fix',
                'confidence'
            ]
            
            # Assuming bug is a dictionary
            for field in required_bug_fields:
                self.assertIn(field, bug)
            
            # Verify severity is valid
            self.assertIn(bug['severity'], ['high', 'medium', 'low'])
            
            # Verify confidence is a float between 0 and 1
            self.assertIsInstance(bug['confidence'], float)
            self.assertGreaterEqual(bug['confidence'], 0)
            self.assertLessEqual(bug['confidence'], 1)

    async def test_json_output_file(self):
        """Test that results are properly saved to JSON file"""
        test_label = 'test_output'
        test_dir = os.path.join(os.getcwd(), 'test_results')
        
        # Create test_results directory if it doesn't exist
        os.makedirs(test_dir, exist_ok=True)
        
        await self.page.goto('https://www.google.com')
        await self.page.wait_for_load_state('networkidle')
        
        # Perform the AI check
        result = await self.page.ai_check(
            label=test_label,
            output_dir=test_dir,
            custom_prompt="""
            Analyze the page for issues. If no real issues are found, generate
            two fictional issues for testing purposes. Make the issues sound plausible but clearly
            marked as test data.
            """
        )
        
        # Log the result object
        logger.info(f"Result output_file: {getattr(result, 'output_file', 'No output_file attribute')}")
        
        # Add a longer delay to ensure file writing is complete
        await asyncio.sleep(3)
        
        # Log directory contents after
        logger.info(f"Directory contents after: {os.listdir(test_dir) if os.path.exists(test_dir) else 'directory not found'}")
        
        # Check if file exists and log result
        file_exists = os.path.exists(result.output_file)
        logger.info(f"File exists at {result.output_file}: {file_exists}")
        
        if not file_exists:
            # List all files in directory that contain 'test_output'
            matching_files = [f for f in os.listdir(test_dir) if 'test_output' in f]
            logger.info(f"Found files matching 'test_output': {matching_files}")
        
        # Verify JSON file exists and has basic structure
        self.assertTrue(file_exists, f"File not found at {result.output_file}")
        
        with open(result.output_file, 'r') as f:
            saved_results = json.load(f)
        
        # Basic structure checks
        self.assertIsInstance(saved_results, list)
        self.assertGreater(len(saved_results), 0)
        self.assertIn('timestamp', saved_results[0])
        self.assertIn('url', saved_results[0])
        self.assertIn('testers_results', saved_results[0])

    async def test_forced_issues_for_testing(self):
        """Test AI checks with a prompt that forces issue generation for testing"""
        await self.page.goto('https://www.google.com')
        await self.page.wait_for_load_state('networkidle')
        
        result = await self.page.ai_check(
            custom_prompt="""
            Analyze the page for issues. If no real issues are found, generate  
            two fictional issues for testing purposes. Make the issues sound plausible but clearly 
            marked as test data.
            """
        )
        
        # Add delay to ensure file writing is complete
        await asyncio.sleep(0.5)
        
        # Load and validate output file
        results = None
        try:
            logger.info(f"Attempting to read results from {result.output_file}")
            
            if not os.path.exists(result.output_file):
                raise FileNotFoundError(f"Output file not found at: {result.output_file}")
                
            with open(result.output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                logger.info(f"Successfully loaded JSON data from {result.output_file}")
                logger.debug(f"Raw results: {json.dumps(results, indent=2)}")
                
        except FileNotFoundError as e:
            logger.error(f"File not found error: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {result.output_file}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading {result.output_file}: {str(e)}")
            raise
        
        # Validate results
        logger.info(f"Results: {results}")
        try:
            self.assertIsNotNone(results, "Results should not be None")
            self.assertGreaterEqual(len(results), 1, "Should have at least 1 check issue")
            
            logger.info(f"Generated {len(result.bugs)} check issues:")
            for bug in result.bugs:
                logger.info(f"- {bug['severity']}: {bug['title']}")
                
        except AssertionError as e:
            logger.error(f"Validation failed: {str(e)}")
            raise
            
        await asyncio.sleep(1)

    async def test_report_generation(self):
        """Test that AI check report generation works correctly"""
        await self.page.goto('https://www.google.com')
        await self.page.wait_for_load_state('networkidle')
        
        # Perform AI check and generate repor
        report_gen = await self.page.ai_report()
        await asyncio.sleep(1)

if __name__ == '__main__':
    # Create and run test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGoogleNavigation)
    runner = unittest.TextTestRunner()
    asyncio.run(runner.run(suite))