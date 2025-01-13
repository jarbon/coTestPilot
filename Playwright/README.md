# coTestPilot

An AI-powered page checking extension for Playwright that automates web testing and bug detection using GPT-4 Vision.

## Features

- 🤖 AI-powered visual analysis of web pages
- 👥 Multiple testing personas with different expertise
- 🎯 Custom rules and prompts for specialized checking
- 📸 Automatic screenshot capture and storage
- 📊 JSON output for easy integration with testing workflows
- ⚡ Support for async and sync Playwright APIs
- 🔍 High-confidence issue detection
- 📝 Detailed bug reports with severity, description, and fix recommendations


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
https://x.com/jarbon

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