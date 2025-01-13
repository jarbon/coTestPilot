# Copyright 2025 Jason Arbon (Checkie.ai, Testers.ai)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
coTestPilot - AI-powered page checking extension for Playwright Async Version
This package extends Playwright with AI capabilities for automated testing and bug detection.

Note: This is a light version of the AI Testing Agents available at checkie.ai and testers.ai.
For more powerful testing agents, enhanced reporting capabilities, and professional support,
please visit those websites. Testing services and tool vendors who wish to reuse this code
should contribute to maintaining this public version. Professional and endorsed integrations
into testing tools and services are available through checkie.ai.

Important: This copyright header and attribution must be preserved in all ports and
derivative works, including reverse-engineered implementations. Let's maintain good
open-source citizenship.

Testing Agents:
    - Several built-in testing agent profiles are included by default:
        - General UI/UX expert
        - Accessibility specialist
        - Security tester
        - Performance analyst
        - Content reviewer
    - Create custom testing agents by editing testers.json
    - Each agent has specialized expertise and checking focus
    - Custom check prompts can be easily added for specific testing scenarios
    - Combine multiple agents for comprehensive testing coverage

Customization:
    - Edit testers.json to:
        - Add new testing agents
        - Modify existing agent behaviors
        - Define specialized expertise areas
    - Use custom_prompt parameter for:
        - One-off specialized checks
        - Site-specific testing rules
        - Custom acceptance criteria
        - Domain-specific requirements

Usage:
    from playwright.async_api import async_playwright
    from playwright_cotestpilot import configure_logging, LogLevel

    # Configure logging level and verbosity
    configure_logging(
        level="DEBUG",  # Standard logging level
        console_verbosity=LogLevel.VERBOSE,  # Console output detail level
        config={
            'api_rate_limit': 0.25,  # API calls per second
            'screenshot_retention_days': 7,
            'max_retries': 5
        }
    )

    # Initialize Playwright and navigate to a page
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://example.com')

        # Basic AI check
        result = await page.ai_check(
            console_verbosity=LogLevel.BASIC,  # Control logging for this check
            save_to_file=True,  # Save results to JSON file
            output_dir="ai_check_results"  # Directory for results
        )
        print(f"Found {len(result.bugs)} issues")

        # Generate HTML report from results
        report_path = await page.ai_report(output_dir="ai_check_results")
        print(f"Report generated at: {report_path}")

Features:
    - AI-powered visual analysis using GPT-4 Vision
    - Multiple testing personas with different expertise
    - Automatic screenshot capture and management
    - JSON output with detailed issue reporting
    - HTML report generation with screenshots
    - Configurable rate limiting and retries
    - Comprehensive logging system

Configuration:
    1. Set your OpenAI API key:
       export OPENAI_API_KEY='your-api-key'

    2. Configure logging and settings:
       configure_logging(
           level="DEBUG",
           console_verbosity=LogLevel.VERBOSE,
           config={
               'api_rate_limit': 0.25,        # API calls per second
               'screenshot_retention_days': 7,  # Screenshot retention period
               'max_retries': 5                # API call retry attempts
           }
       )

Output Format:
    Each issue in the results contains:
    - title: Brief description of the issue
    - severity: Impact level (0-3, where 3 is highest)
    - description: Detailed explanation
    - why_fix: Importance/impact of the issue
    - how_to_fix: Suggested resolution
    - confidence: AI confidence score (0-1)

Returns:
    CheckResult object containing:
    - timestamp: Check execution time
    - url: Checked page URL
    - bugs: List of identified issues
    - raw_response: Complete analysis data
    - profile: Testing profile used
    - output_file: Path to saved JSON results
"""

import logging
from typing import Optional, Dict, Any, Union, List, TypedDict
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dataclasses import dataclass
from datetime import datetime, timedelta
import inspect
import requests
import re
import os
import json
import os.path
import logging.handlers
from enum import Enum
import time
import warnings
import glob
import shutil
from jinja2 import Template

# Suppress urllib3 deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='urllib3')

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class CheckResult:
    """Contains the results of a page check operation."""
    timestamp: datetime
    url: str
    bugs: list
    raw_response: Dict[str, Any]
    profile: str
    output_file: Optional[str] = None  # Add new field for output file path

try:
    # Get the directory containing this file
    package_dir = os.path.dirname(os.path.abspath(__file__))
    testers_path = os.path.join(package_dir, 'testers.json')
    
    with open(testers_path, 'r') as f:
        TESTERS = json.load(f)['testers']
    logger.info(f"Loaded {len(TESTERS)} testers from {testers_path}")
except FileNotFoundError:
    logger.warning(f"testers.json not found at {testers_path}. No testing agents will be available.")
    TESTERS = []
except json.JSONDecodeError:
    logger.error(f"testers.json at {testers_path} is invalid. No testing agents will be available.")
    TESTERS = []
except KeyError:
    logger.error(f"testers.json at {testers_path} missing 'reporters' key. No testing agents will be available.")
    TESTERS = []

class LogLevel(Enum):
    NONE = 0
    BASIC = 1
    VERBOSE = 2

# Add new configuration class
class Config(TypedDict):
    api_rate_limit: float  # Calls per second
    screenshot_retention_days: int
    max_retries: int

# Default configuration
DEFAULT_CONFIG = Config(
    api_rate_limit=1.0,  # One call per second
    screenshot_retention_days=30,
    max_retries=3
)

# Add rate limiting
class RateLimiter:
    def __init__(self, calls_per_second: float):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()

# Initialize rate limiter
api_rate_limiter = RateLimiter(DEFAULT_CONFIG['api_rate_limit'])

# Configure logging with file handler
def configure_logging(
    level: str = "INFO",
    console_verbosity: LogLevel = LogLevel.BASIC,
    config: Optional[Config] = None
) -> logging.Logger:
    """
    Configure logging and global settings
    
    Args:
        level: Standard logging level ("DEBUG", "INFO", etc.)
        console_verbosity: Controls console output verbosity
        config: Optional configuration dictionary
        
    Returns:
        The configured logger instance
    """
    global DEFAULT_CONFIG
    if config:
        DEFAULT_CONFIG.update(config)
    try:
        logging_level = getattr(logging, level.upper())
        logger = logging.getLogger(__name__)
        logger.setLevel(logging_level)
        
        # Properly close existing handlers before clearing
        for handler in logger.handlers:
            handler.close()
        logger.handlers.clear()
        
        # File handler - always logs everything to ai_checks.log
        file_handler = logging.handlers.RotatingFileHandler(
            'ai_checks.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)
        
        # Console handler - controlled by console_verbosity
        if console_verbosity != LogLevel.NONE:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG if console_verbosity == LogLevel.VERBOSE else logging.INFO)
            console_handler.setFormatter(logging.Formatter(
                '%(levelname)s: %(message)s' if console_verbosity == LogLevel.BASIC else 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(console_handler)
        
        return logger
            
    except Exception as e:
        print(f"Error configuring logging: {str(e)}")
        # Fallback to basic configuration
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

def check(self: WebDriver, 
          profile_search: Optional[str] = None,
          custom_rules: Optional[Dict[str, Any]] = None,
          custom_prompt: Optional[str] = None,
          output: str = 'return list of issues as an array of JSON objects with properties: title, severity, description, why_fix, how_to_fix, confidence (a number between 0 and 1)',
          testers: Optional[List[str]] = None,
          label: Optional[str] = None,
          timeout: int = 30000,
          console_verbosity: LogLevel = LogLevel.BASIC,
          save_to_file: bool = True,
          output_dir: Optional[str] = "ai_check_results") -> CheckResult:
    """
    Performs an AI-powered check of the current page.
    """
    try:
        logger.info(f"Starting page check with profile: {profile_search}")
        
        # Ensure screenshot directory exists
        os.makedirs("screenshots", exist_ok=True)
        
        # Capture and save screenshot (Selenium version)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/check_{timestamp}.png"
        self.get_screenshot_as_file(screenshot_path)
        
        # Convert screenshot to base64
        with open(screenshot_path, "rb") as image_file:
            import base64
            screenshot_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Validate inputs
        if timeout < 1000:
            logger.warning("Timeout too low, setting to minimum 1000ms")
            timeout = 1000
            
        if custom_rules is not None and not isinstance(custom_rules, dict):
            logger.error("custom_rules must be a dictionary")
            raise ValueError("custom_rules must be a dictionary")

        # Select testers - default to just Jason if no testers specified
        selected_testers = []
        
        if testers is None:
            selected_testers = [t for t in TESTERS if t['name'].lower() == 'jason']
        else:
            selected_testers = [
                t for t in TESTERS 
                if any(requested.lower() in t['name'].lower() for requested in testers)
            ]
            if not selected_testers:
                logger.warning(f"No matching testers found for {testers}. Using Jason as default tester.")
                selected_testers = [t for t in TESTERS if t['name'].lower() == 'jason']
        
        # Get current page URL and content (Selenium version)
        url = self.current_url
        page_text = self.find_element("tag name", "body").text
        
        all_findings = []
        
        # Run analysis with each selected tester
        for tester in selected_testers:
            # Generate vision prompt for this specific tester
            vision_prompt = f"""Please analyze this webpage for any errors, issues, or problems.

IMPORTANT: Only return high-confidence issues. It is perfectly acceptable to return no issues if none are found with high confidence.
For each issue found, include a confidence score between 0 and 1, where:
- 1.0 means absolutely certain this is an issue
- 0.8-0.9 means very confident
- 0.7-0.8 means reasonably confident
- Below 0.7 should not be reported

Severity levels (0-3):
0 = Cosmetic: Minor visual or text issues that don't impact functionality or understanding
1 = Low: Issues that cause minor inconvenience but don't prevent core functionality
2 = Medium: Issues that significantly impact user experience or partially break functionality
3 = High: Critical issues that prevent core functionality or severely impact user experience or the business.

Page URL: {url}
Page Text Content:
{page_text}

You are {tester['name']}, and this is your expertise and background:
{tester['biography']}

Please identify any:
1. Visual errors or layout issues
2. Content errors or inconsistencies
3. Functionality problems that are visible
4. Any other issues that might affect user experience

Output format: {output}

Example format:
[
    {{
        "title": "Broken image link",
        "severity": "high",
        "description": "Image on homepage fails to load",
        "why_fix": "Impacts user experience and site professionalism",
        "how_to_fix": "Update image source URL or replace missing image",
        "confidence": 0.95,
        "related_context_if_any": "The image is a logo and its url is 'https://www.google.com/images/branding/googlelogo/2x/googlelogo_light_color_272x92dp.png' and is used in the header"
    }}
]

return only the JSON array, no other text or comments.

{custom_prompt if custom_prompt else ''}"""

            # Add rate limiting before API calls
            api_rate_limiter.wait()
            
            # Add retries for API calls
            retries = DEFAULT_CONFIG['max_retries']
            while retries > 0:
                try:
                    vision_response = chat_vision(vision_prompt, screenshot_base64)
                    break
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        raise
                    logger.warning(f"API call failed, retrying... ({retries} attempts left)")
                    time.sleep(2)
            
            # Add tester's issues to results
            all_findings.append({
                'tester': tester['name'],
                'biography': tester['biography'],
                'issues': vision_response
            })
        
        # Prepare results for saving
        check_result = {
            'timestamp': timestamp,
            'url': url,
            'screenshot': screenshot_path,
            'testers_results': all_findings
        }
        
        # Extract all issues from testers_results
        all_issues = []
        for tester_result in all_findings:
            try:
                if isinstance(tester_result['issues'], str):
                    issues = json.loads(tester_result['issues'])
                else:
                    issues = tester_result['issues']
                all_issues.extend(issues)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Error parsing issues from tester {tester_result.get('tester')}: {str(e)}")

        # Only save to file if save_to_file is True
        output_file_path = None
        if save_to_file:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{label}_{timestamp_str}_ai.json" if label else f"ai_checks_{timestamp_str}.json"
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_file_path = os.path.join(output_dir, output_file)
            
            with open(output_file_path, 'w') as f:
                json.dump(check_result, f, indent=2)
            
            logger.info(f"AI check results saved to {output_file}")
        
        return CheckResult(
            timestamp=datetime.now(),
            url=url,
            bugs=all_issues,
            raw_response=check_result,
            profile=profile_search or "default",
            output_file=output_file_path
        )
            
    except Exception as e:
        logger.exception(f"Critical error during page check: {str(e)}")
        return CheckResult(
            timestamp=datetime.now(),
            url=self.current_url if hasattr(self, 'current_url') else "unknown",
            bugs=[],
            raw_response={"error": str(e)},
            profile=profile_search or "default",
            output_file=None
        )

def _sync_impl(driver: WebDriver, url: str, profile_search: str, custom_rules: dict, page_text: str, screenshot: str):
    """Internal sync implementation for Selenium"""
    metadata = {
        "title": driver.title,
        "url": driver.current_url,
        "viewport": {
            "width": driver.execute_script("return window.innerWidth"),
            "height": driver.execute_script("return window.innerHeight")
        }
    }
    
    check_data = {
        "url": url,
        "metadata": metadata,
        "profile": profile_search,
        "custom_rules": custom_rules
    }
    
    return CheckResult(
        timestamp=datetime.now(),
        url=url,
        bugs=[],
        raw_response=check_data,
        profile=profile_search or "default",
        output_file=None
    )

def ai_report(self: WebDriver, output_dir: str = "ai_check_results") -> str:
    """
    Generate an HTML report from AI check results
    
    Args:
        self: Selenium WebDriver instance
        output_dir: Directory containing JSON result files
        
    Returns:
        Path to the generated HTML report
    """
    try:
        logger.info(f"Generating report from results in {output_dir}")
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(output_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Find all JSON files in the output directory
        json_files = glob.glob(os.path.join(output_dir, "ai_*.json"))
        
        # Collect all results
        all_results = []
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    results = json.load(f)
                    if isinstance(results, list):
                        all_results.extend(results)
                    else:
                        all_results.append(results)
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {str(e)}")
        
        # Get template from package directory
        package_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(package_dir, 'report_template.html')
        
        # Copy screenshots to reports directory
        for result in all_results:
            if 'screenshot' in result:
                screenshot_path = result['screenshot']
                if os.path.exists(screenshot_path):
                    dest_path = os.path.join(reports_dir, os.path.basename(screenshot_path))
                    shutil.copy2(screenshot_path, dest_path)
                    # Update path in result to be relative
                    result['screenshot'] = os.path.join('reports', os.path.basename(screenshot_path))
        
        # Generate report
        with open(template_path, 'r') as f:
            template = Template(f.read())
            
        report_html = template.render(
            results=all_results,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Save report
        report_path = os.path.join(output_dir, 'ai_check_report.html')
        with open(report_path, 'w') as f:
            f.write(report_html)
            
        logger.info(f"Report generated at {report_path}")
        return report_path
        
    except Exception as e:
        logger.exception(f"Error generating report: {str(e)}")
        raise

# Now attach methods to WebDriver class
setattr(webdriver.Remote, "ai_check", check)
setattr(webdriver.Remote, "ai_report", ai_report)
setattr(webdriver.Chrome, "ai_check", check)
setattr(webdriver.Chrome, "ai_report", ai_report)
setattr(webdriver.Firefox, "ai_check", check)
setattr(webdriver.Firefox, "ai_report", ai_report)
setattr(webdriver.Safari, "ai_check", check)
setattr(webdriver.Safari, "ai_report", ai_report)
setattr(webdriver.Edge, "ai_check", check)
setattr(webdriver.Edge, "ai_report", ai_report)

def getTimeStampStr():
    """Returns current timestamp as a formatted string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Get API key from environment variable
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    alert('jj')
    logger.warning("OPENAI_API_KEY environment variable not set. GPT chat functionality will not work.")

def gptchat(prompt, add_time=True):
    """
    Send a prompt to GPT and get the response
    
    Args:
        prompt: The text prompt to send to GPT
        add_time: Whether to prepend current timestamp to prompt
        
    Returns:
        Cleaned response content from GPT
        
    Raises:
        RuntimeError: If OPENAI_API_KEY environment variable is not set
    """
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable must be set to use GPT chat functionality")

    #this avoids the AI making mistakes as it can think it is a time in the past.    
    if add_time:
        prompt = "Current time: %s\n%s" % (getTimeStampStr(), prompt)
    
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": 4096,
        "format": "json"
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    resp = response.json()
    #print('RESP:%s' % (resp))
    
    choices = resp['choices']
    zero = choices[0]
    msg = zero['message']
    content = msg['content']
    cleaned_content = re.sub(r'```.*?\n|```', '', content)
    #print('cleaned_content', cleaned_content)

    return cleaned_content

def chat_vision(prompt, base64_image, add_time=True):
    """Enhanced error handling for vision API calls"""
    try:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable must be set")
        
        if not base64_image:
            raise ValueError("base64_image cannot be empty")
            
        if not prompt:
            raise ValueError("prompt cannot be empty")
            
        if add_time:
            prompt = "Current time: %s\n%s" % (getTimeStampStr(), prompt)
        #return gptchat(prompt)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4000,
            "format": "json"
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", 
                               headers=headers, 
                               json=payload,
                               timeout=30)  # Add timeout
        response.raise_for_status()  # Raise exception for bad status codes
        
        resp = response.json()
        #print('RESP:%s' % (resp))
        choices = resp['choices']
        zero = choices[0]
        msg = zero['message']
        content = msg['content']
        cleaned_content = re.sub(r'```.*?\n|```', '', content)
        #print('cleaned_content', cleaned_content)
        ret = json.loads(cleaned_content)

        return ret
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return "[]"  # Return empty JSON array as fallback
    except Exception as e:
        logger.exception(f"Error in chat_vision: {str(e)}")
        return "[]"  # Return empty JSON array as fallback

# Print initialization message
print('coTestPilot initialized')

# Configure logging
configure_logging(
    level="DEBUG",
    config={
        'api_rate_limit': 0.25,  # One call every 4 seconds
        'screenshot_retention_days': 7,
        'max_retries': 5
    }
)