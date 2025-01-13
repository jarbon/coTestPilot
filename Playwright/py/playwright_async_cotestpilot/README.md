# coTestPilot

An AI-powered page checking extension for Playwright that automates web testing and bug detection using GPT-4 Vision.

## Features

- 🤖 AI-powered visual analysis of web pages
- 👥 Multiple testing personas with different expertise
- 🎯 Custom rules and prompts for specialized checking
- 📸 Automatic screenshot capture and storage
- 📊 JSON output for easy integration with testing workflows
- ⚡ Support for async Playwright APIs
- 🔍 High-confidence issue detection
- 📝 Detailed bug reports with severity, description, and fix recommendations



## Installation

Download code locally (PIP insteall coming soon hopefully!)

## Prerequisites

1. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key'
```

2. Install Playwright and browsers:
```bash
pip install playwright
playwright install
```

## Basic Usage

```python
from playwright.async_api import async_playwright
import playwright_async_cotestpilot
import asyncio

# Configure logging and settings
configure_logging(
    level="DEBUG",
    console_verbosity=LogLevel.VERBOSE,
    config={
        'api_rate_limit': 0.25,        # API calls per second
        'screenshot_retention_days': 7,  # Screenshot retention period
        'max_retries': 5                # API call retry attempts
    }
)

async def main():
    # Initialize Playwright and navigate to a page
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://example.com')

        # Basic AI check with additional options
        result = await page.ai_check(
            console_verbosity=LogLevel.BASIC,  # Control logging for this check
            save_to_file=True,                 # Save results to JSON file
            output_dir="ai_check_results"      # Directory for results
        )
        print(f"Found {len(result.bugs)} issues")

        # Generate HTML report
        report_path = await page.ai_report(output_dir="ai_check_results")
        print(f"Report generated at: {report_path}")

# Run the async function
asyncio.run(main())
```

## Advanced Usage

### Using Specific Testing Personas

```python
result = await page.ai_check(
    testers=['Jason', 'Alice'],  # Specify which testing personas to use
    label='homepage'  # Save results to homepage_ai.json
)
```

### Custom Rules and Prompts

```python
result = await page.ai_check(
    custom_rules={
        'check_contrast': True,
        'min_font_size': 12
    },
    custom_prompt="Pay special attention to accessibility issues"
)
```

## Output Format

The tool generates a `CheckResult` object containing:
- `timestamp`: When the check was performed
- `url`: URL of the checked page
- `bugs`: List of identified issues
- `raw_response`: Complete API response
- `profile`: Testing profile used

Each bug report includes:
```json
{
    "title": "Issue title",
    "severity": "high|medium|low",
    "description": "Detailed description of the issue",
    "why_fix": "Impact on user experience",
    "how_to_fix": "Recommended solution",
    "confidence": 0.95
}
```

## Configuration

### Logging

Configure logging level for detailed debugging:

```python
from playwright_cotestpilot import configure_logging

configure_logging(level="DEBUG")  # Options: DEBUG, INFO, WARNING, ERROR
```

### Timeouts

Adjust the maximum time for checks:

```python
result = await page.ai_check(timeout=60000)  # 60 seconds in milliseconds
```

## File Output

Results are automatically saved to JSON files:
- Default: `ai_checks.json`
- Custom: Specify with `label` parameter (e.g., `homepage_ai.json`)
- Screenshots are saved to the `screenshots/` directory

## Testing Personas

The tool includes multiple testing personas with different expertise areas. Each tester brings their unique perspective to the analysis:

- Default tester: Jason
- Testers can be specified by name or expertise description (e.g., 'accessibility expert', 'security specialist')
- Case-insensitive matching for tester names and descriptions
- Multiple testers can be combined for comprehensive analysis

Example:
```python
result = await page.ai_check(
    testers=['Jason', 'accessibility expert', 'security specialist']
)
```

## Custom Testing Personas

You can add your own testing personas by creating or modifying the `testers.json` file in your project directory. Each tester should have a name, expertise, and default prompt. Note that testers can only analyze what is visible in the screenshot and page text - they cannot interact with the page or check dynamic behaviors.

```json
{
  "CustomTester": {
    "name": "CustomTester",
    "expertise": "Brand consistency and content specialist",
    "prompt": "Analyze the page for brand consistency issues, including tone of voice, terminology usage, and adherence to style guidelines. Check for typos, grammatical errors, and unclear messaging."
  }
}
```

Once defined, you can use your custom tester like any built-in persona:

```python
result = await page.ai_check(testers=['CustomTester'])
```

## License

Copyright 2025 Jason Arbon (Checkie.ai, Testers.ai)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Note: This is a light version of the AI Testing Agents available at checkie.ai and testers.ai.
For more powerful testing agents, enhanced reporting capabilities, and professional support,
please visit those websites. Testing services and tool vendors who wish to reuse this code
should contribute to maintaining this public version. Professional and endorsed integrations
into testing tools and services are available through checkie.ai.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Credits

Created by Jason Arbon (Checkie.ai, Testers.ai)
https://www.linkedin.com/in/jasonarbon/ 
https://x.com/home

## Licensing and Attribution

This project is licensed under the Apache License 2.0. While the code may appear simple, it represents significant research, experimentation, and innovation in applying AI to software testing.

### Important Notes:

- Created by Jason Arbon (Checkie.ai, Testers.ai)
- Commercial licensing is available through Checkie.ai for vendors and commercial use
- If you port this to another language or platform, the original copyright header and attribution must be preserved
- Please respect the intellectual property - while the code is open source, it's the result of extensive work and innovation

### For Commercial Use

If you're interested in using this commercially or need a different license, please contact:
- Website: [Checkie.ai](https://checkie.ai) and [Testers.ai](https://testers.ai)
- LinkedIn: [Jason Arbon](https://www.linkedin.com/in/jasonarbon/)

> **Note**: Professional versions available at testers.ai/checkie.ai include additional advanced features such as visual diffing and deeper testing capabilities.

### A Note on the Implementation

While the implementation may appear straightforward, it represents months of careful experimentation and refinement to:
- Optimize prompts for reliable results
- Fine-tune the testing personas
- Balance accuracy with performance
- Handle edge cases gracefully

We encourage contributions and responsible use of this tool while respecting the intellectual property and effort that went into its creation.

## Built-in Testing Personas

The tool includes several built-in testing agent profiles by default:
- General UI/UX expert
- Accessibility specialist
- Security tester
- Performance analyst
- Content reviewer

## Configuration Options

### Logging and Settings

Configure global behavior with detailed options:

```python
configure_logging(
    level="DEBUG",               # Standard logging level
    console_verbosity=LogLevel.VERBOSE,  # Console output detail level
    config={
        'api_rate_limit': 0.25,         # API calls per second
        'screenshot_retention_days': 7,  # Days to keep screenshots
        'max_retries': 5                # API call retry attempts
    }
)
```

### Check-specific Options

Control behavior for individual checks:

```python
result = await page.ai_check(
    console_verbosity=LogLevel.BASIC,  # Logging detail for this check
    save_to_file=True,                 # Save results to JSON
    output_dir="ai_check_results"      # Custom output directory
)
```

## Reports

Generate HTML reports from check results:

```python
report_path = await page.ai_report(output_dir="ai_check_results")
```