#!/usr/bin/env python3
"""
FOSS Data Platform - Visual Consistency Checker
Ensures all pages have consistent layout, styling, and design elements
"""

import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Set, Any

class VisualConsistencyChecker:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.pages = [
            "/",
            "/pipeline-management",
            "/pipeline-control", 
            "/data-browser",
            "/storage-management",
            "/bi-dashboard",
            "/health",
            "/metrics",
            "/streaming"
        ]
        
        # Expected consistent elements
        self.required_elements = {
            'navbar': 'Navigation bar',
            'container': 'Bootstrap container',
            'bootstrap': 'Bootstrap CSS',
            'font-awesome': 'Font Awesome icons',
            'card': 'Card components',
            'btn': 'Button components'
        }
        
        # Expected consistent styling
        self.expected_styles = {
            'bg-primary': 'Primary background colors',
            'text-white': 'White text on colored backgrounds',
            'shadow-sm': 'Subtle shadows',
            'border-0': 'No borders on cards'
        }
        
    def check_page(self, page_path: str) -> Dict[str, any]:
        """Check a single page for consistency"""
        try:
            response = requests.get(f"{self.base_url}{page_path}", timeout=10)
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'elements': {},
                    'styles': {},
                    'layout': {}
                }
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for required elements
            elements = {}
            for element, description in self.required_elements.items():
                if element == 'navbar':
                    elements[element] = bool(soup.find('nav'))
                elif element == 'container':
                    elements[element] = bool(soup.find(class_=re.compile(r'container')))
                elif element == 'bootstrap':
                    elements[element] = 'bootstrap' in response.text.lower()
                elif element == 'font-awesome':
                    elements[element] = 'font-awesome' in response.text.lower()
                elif element == 'card':
                    elements[element] = bool(soup.find(class_=re.compile(r'card')))
                elif element == 'btn':
                    elements[element] = bool(soup.find(class_=re.compile(r'btn')))
            
            # Check for consistent styling
            styles = {}
            for style, description in self.expected_styles.items():
                styles[style] = style in response.text
            
            # Check layout consistency
            layout = {
                'has_header': bool(soup.find('h1') or soup.find('h2')),
                'has_footer': bool(soup.find('footer') or 'footer' in response.text.lower()),
                'uses_grid': bool(soup.find(class_=re.compile(r'row|col-'))),
                'responsive': bool(soup.find('meta', {'name': 'viewport'}))
            }
            
            # Check page layout (enhanced)
            page_layout = self.check_page_layout(response.text)
            
            return {
                'success': True,
                'elements': elements,
                'styles': styles,
                'layout': layout,
                'page_layout': page_layout,
                'content_length': len(response.text)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'elements': {},
                'styles': {},
                'layout': {}
            }
    
    def check_page_layout(self, html_content: str) -> Dict[str, Any]:
        """Check page layout and structure"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check container usage
        container_fluid = soup.find_all(class_='container-fluid')
        container = soup.find_all(class_='container')
        
        # Check for layout issues
        layout_issues = []
        if container_fluid:
            layout_issues.append(f'Uses container-fluid ({len(container_fluid)} instances) - may be too wide')
        if not container:
            layout_issues.append('No container class found - layout may be broken')
        
        # Check for proper responsive design
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if not viewport_meta:
            layout_issues.append('Missing viewport meta tag - not responsive')
        
        # Check for proper Bootstrap structure
        bootstrap_links = soup.find_all('link', href=lambda x: x and 'bootstrap' in x)
        if not bootstrap_links:
            layout_issues.append('Bootstrap CSS not properly linked')
        
        # Check for proper navigation structure
        navbar = soup.find('nav', class_='navbar')
        if not navbar:
            layout_issues.append('Missing or malformed navigation bar')
        
        # Check for proper card structure
        cards = soup.find_all(class_='card')
        if not cards:
            layout_issues.append('No cards found - may be missing content structure')
        
        return {
            'container_fluid_count': len(container_fluid),
            'container_count': len(container),
            'has_viewport_meta': bool(viewport_meta),
            'has_bootstrap': len(bootstrap_links) > 0,
            'has_navbar': bool(navbar),
            'card_count': len(cards),
            'layout_issues': layout_issues,
            'layout_score': max(0, 5 - len(layout_issues)) / 5
        }
    
    def check_all_pages(self) -> Dict[str, Dict]:
        """Check all pages for consistency"""
        results = {}
        
        print("🔍 Checking visual consistency across all pages...")
        print("=" * 70)
        
        for page in self.pages:
            print(f"Checking {page}...")
            results[page] = self.check_page(page)
            
            if results[page]['success']:
                print(f"  ✅ Loaded successfully")
            else:
                print(f"  ❌ Failed: {results[page]['error']}")
        
        return results
    
    def analyze_consistency(self, results: Dict[str, Dict]) -> Dict[str, any]:
        """Analyze consistency across all pages"""
        print("\n📊 Analyzing consistency...")
        print("=" * 70)
        
        # Count successful page loads
        successful_pages = [p for p, r in results.items() if r['success']]
        failed_pages = [p for p, r in results.items() if not r['success']]
        
        print(f"Successful pages: {len(successful_pages)}/{len(self.pages)}")
        if failed_pages:
            print(f"Failed pages: {failed_pages}")
        
        if not successful_pages:
            return {'error': 'No pages loaded successfully'}
        
        # Analyze element consistency
        element_consistency = {}
        for element in self.required_elements:
            present_count = sum(1 for r in results.values() 
                              if r['success'] and r['elements'].get(element, False))
            element_consistency[element] = {
                'present': present_count,
                'total': len(successful_pages),
                'percentage': (present_count / len(successful_pages)) * 100
            }
        
        # Analyze style consistency
        style_consistency = {}
        for style in self.expected_styles:
            present_count = sum(1 for r in results.values() 
                              if r['success'] and r['styles'].get(style, False))
            style_consistency[style] = {
                'present': present_count,
                'total': len(successful_pages),
                'percentage': (present_count / len(successful_pages)) * 100
            }
        
        # Analyze layout consistency
        layout_consistency = {}
        for layout_element in ['has_header', 'has_footer', 'uses_grid', 'responsive']:
            present_count = sum(1 for r in results.values() 
                              if r['success'] and r['layout'].get(layout_element, False))
            layout_consistency[layout_element] = {
                'present': present_count,
                'total': len(successful_pages),
                'percentage': (present_count / len(successful_pages)) * 100
            }
        
        return {
            'element_consistency': element_consistency,
            'style_consistency': style_consistency,
            'layout_consistency': layout_consistency,
            'overall_score': self.calculate_overall_score(element_consistency, style_consistency, layout_consistency)
        }
    
    def calculate_overall_score(self, elements: Dict, styles: Dict, layout: Dict) -> float:
        """Calculate overall consistency score"""
        total_checks = len(elements) + len(styles) + len(layout)
        total_percentage = 0
        
        for category in [elements, styles, layout]:
            for item in category.values():
                total_percentage += item['percentage']
        
        return total_percentage / total_checks if total_checks > 0 else 0
    
    def print_consistency_report(self, analysis: Dict[str, any]):
        """Print detailed consistency report"""
        print("\n📋 VISUAL CONSISTENCY REPORT")
        print("=" * 70)
        
        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return
        
        print(f"Overall Consistency Score: {analysis['overall_score']:.1f}%")
        print()
        
        # Element consistency
        print("🔧 REQUIRED ELEMENTS:")
        for element, data in analysis['element_consistency'].items():
            status = "✅" if data['percentage'] == 100 else "⚠️" if data['percentage'] >= 80 else "❌"
            print(f"  {status} {element}: {data['present']}/{data['total']} ({data['percentage']:.1f}%)")
        
        print()
        
        # Style consistency
        print("🎨 STYLING CONSISTENCY:")
        for style, data in analysis['style_consistency'].items():
            status = "✅" if data['percentage'] == 100 else "⚠️" if data['percentage'] >= 80 else "❌"
            print(f"  {status} {style}: {data['present']}/{data['total']} ({data['percentage']:.1f}%)")
        
        print()
        
        # Layout consistency
        print("📐 LAYOUT CONSISTENCY:")
        for layout, data in analysis['layout_consistency'].items():
            status = "✅" if data['percentage'] == 100 else "⚠️" if data['percentage'] >= 80 else "❌"
            print(f"  {status} {layout}: {data['present']}/{data['total']} ({data['percentage']:.1f}%)")
        
        # Layout issues
        layout_issues = []
        for page_data in results.values():
            if page_data.get('success') and 'page_layout' in page_data:
                page_layout = page_data['page_layout']
                if page_layout.get('layout_issues'):
                    layout_issues.extend(page_layout['layout_issues'])
        
        if layout_issues:
            print("\n🚨 LAYOUT ISSUES DETECTED:")
            unique_issues = list(set(layout_issues))
            for issue in unique_issues:
                count = layout_issues.count(issue)
                print(f"  ⚠️  {issue} (affects {count} pages)")
        else:
            print("\n✅ No layout issues detected")
        
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        if analysis['overall_score'] >= 95:
            print("  🎉 Excellent consistency! Your platform looks professional and unified.")
        elif analysis['overall_score'] >= 80:
            print("  👍 Good consistency with minor improvements needed.")
        elif analysis['overall_score'] >= 60:
            print("  ⚠️  Moderate consistency issues. Consider standardizing layouts.")
        else:
            print("  🚨 Significant consistency issues. Major layout standardization needed.")
    
    def run_full_check(self):
        """Run complete visual consistency check"""
        print("🎨 FOSS Data Platform - Visual Consistency Checker")
        print("=" * 70)
        
        # Check all pages
        results = self.check_all_pages()
        
        # Analyze consistency
        analysis = self.analyze_consistency(results)
        
        # Print report
        self.print_consistency_report(analysis)
        
        return analysis

def main():
    """Main checker runner"""
    checker = VisualConsistencyChecker()
    
    try:
        analysis = checker.run_full_check()
        
        # Exit with error code if consistency is poor
        if 'overall_score' in analysis and analysis['overall_score'] < 60:
            print("\n❌ Visual consistency check failed!")
            sys.exit(1)
        else:
            print("\n✅ Visual consistency check completed!")
            
    except KeyboardInterrupt:
        print("\n⚠️  Check interrupted by user")
    except Exception as e:
        print(f"\n💥 Check failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
