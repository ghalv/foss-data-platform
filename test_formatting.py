import re

def post_process_formatting(text):
    '''Post-process LLM response to fix formatting issues.'''

    # AGGRESSIVE FIXES - handle any format the AI produces

    # Step 1: Remove markdown code blocks but preserve bullet points
    # Remove code block markers but keep the content with bullets
    text = re.sub(r'```\w*\n?', '', text)
    text = re.sub(r'```\s*$', '', text)

    # Step 2: Fix service names - multiple patterns to catch different formats
    service_names = r'(minio|kafka|flink|trino|grafana|jupyter|zookeeper|postgres|redis|flink-taskmanager)'

    # Handle bullet point lists: preserve bullets and add proper spacing after the list
    # Look for patterns like "- service\n- service\n- service\nThese" and add spacing
    text = re.sub(rf'(\s*-\s*\w+)\s*\n(\s*-\s*\w+)\s*\n(\s*-\s*\w+)\s*\n\s*(These|The|This)', r'\1\n\2\n\3\n\n\4', text, flags=re.IGNORECASE)

    # Handle cases where bullets are already properly formatted but need spacing
    text = re.sub(rf'(\s*-\s*\w+\s*\n\s*-\s*\w+\s*\n\s*-\s*\w+)\s*\n\s*(These|The|This)', r'\1\n\n\2', text, flags=re.IGNORECASE)

    # Clean up excessive spacing: reduce multiple newlines but keep some structure
    text = re.sub(r'\n{4,}', '\n\n', text)

    # Fix 'Unhealthy services:' header with single newline
    text = re.sub(r'(\n\s*)Unhealthy services:', r'\nUnhealthy services:', text)

    # Fix missing line breaks after numbers in lists
    text = re.sub(r'(\d+)\.\s*([A-Z])', r'\1.\n\n\2', text)

    # Ensure proper spacing after periods
    text = re.sub(r'\.([A-Z])', r'. \1', text)

    # Fix double spaces
    text = re.sub(r'  +', ' ', text)

    return text

# Test with the exact AI response format
test_input = '''```
- dagster
- dbt
- flink

These services are unhealthy and may be causing issues.
```'''

print('RAW INPUT:')
print(repr(test_input))
print()
print('FORMATTED OUTPUT:')
result = post_process_formatting(test_input)
print(repr(result))
print()
print('DISPLAY:')
print(result)
print()
print('ANALYSIS:')
print('- Bullet points preserved:', '- dagster' in result and '- dbt' in result and '- flink' in result)
print('- Proper spacing after list:', '\n\nThese' in result)
print('- No excessive spacing:', result.count('\n\n\n') == 0)
