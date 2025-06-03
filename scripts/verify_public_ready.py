#!/usr/bin/env python3
"""
Public Repository Readiness Verification Script
Checks for sensitive data, credentials, and company-specific information.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict

class RepositoryVerifier:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.issues = []
        self.warnings = []
        self.passed_checks = []
        
    def add_issue(self, check: str, description: str, files: List[str] = None):
        """Add a critical issue that blocks publication."""
        self.issues.append({
            "check": check,
            "description": description,
            "files": files or []
        })
        
    def add_warning(self, check: str, description: str, files: List[str] = None):
        """Add a warning that should be reviewed."""
        self.warnings.append({
            "check": check,
            "description": description,
            "files": files or []
        })
        
    def add_pass(self, check: str, description: str):
        """Add a passed check."""
        self.passed_checks.append({
            "check": check,
            "description": description
        })

    def check_sensitive_files(self):
        """Check for sensitive files that shouldn't be committed."""
        sensitive_patterns = [
            r'test\.env$',
            r'test_local\.env$',
            r'\.env\.local$',
            r'\.env\.development$',
            r'\.env\.production$',
            r'.*\.env\.backup$',
        ]
        
        found_files = []
        for pattern in sensitive_patterns:
            for file_path in self.repo_path.rglob("*"):
                if file_path.is_file() and re.search(pattern, str(file_path.name)):
                    # Check if file is tracked by git
                    try:
                        result = subprocess.run(
                            ["git", "ls-files", str(file_path.relative_to(self.repo_path))],
                            cwd=self.repo_path,
                            capture_output=True,
                            text=True
                        )
                        if result.stdout.strip():
                            found_files.append(str(file_path.relative_to(self.repo_path)))
                    except:
                        pass
        
        if found_files:
            self.add_issue(
                "Sensitive Files in Repository",
                "Found sensitive environment files tracked by Git",
                found_files
            )
        else:
            self.add_pass(
                "Sensitive Files Check",
                "No sensitive files found in Git tracking"
            )

    def check_api_keys(self):
        """Check for API keys and secrets in files."""
        api_key_patterns = [
            r'sk-proj-[A-Za-z0-9_-]+',  # OpenAI API keys
            r'sk-[A-Za-z0-9_-]{20,}',   # Other OpenAI keys
            r'xapp-[A-Za-z0-9_-]+',     # Other API patterns
            r'Bearer [A-Za-z0-9_-]{20,}', # Bearer tokens
        ]
        
        found_keys = []
        exclude_files = {'.git', 'node_modules', '__pycache__', '.env.example', 'test.env.example'}
        
        for file_path in self.repo_path.rglob("*"):
            if (file_path.is_file() and 
                not any(exclude in str(file_path) for exclude in exclude_files) and
                file_path.suffix in ['.py', '.js', '.ts', '.json', '.yml', '.yaml', '.md', '.sh', '.env']):
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern in api_key_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            # Skip if it's clearly a placeholder
                            if any(placeholder in match.group().lower() for placeholder in 
                                  ['your-', 'example', 'placeholder', 'template', 'xxx']):
                                continue
                                
                            found_keys.append({
                                'file': str(file_path.relative_to(self.repo_path)),
                                'pattern': pattern,
                                'match': match.group()[:20] + "..." if len(match.group()) > 20 else match.group()
                            })
                except:
                    pass
        
        if found_keys:
            files = [key['file'] for key in found_keys]
            self.add_issue(
                "API Keys Found",
                f"Found {len(found_keys)} potential API keys in files",
                files
            )
        else:
            self.add_pass(
                "API Keys Check",
                "No API keys found in repository files"
            )

    def check_company_references(self):
        """Check for company-specific references."""
        company_patterns = [
            r'zgcompanies\.com',
            r'@zgcompanies\.com',
            r'smanji@',
            r'ZG Companies',
        ]
        
        found_refs = []
        exclude_files = {'.git', 'node_modules', '__pycache__', 'scripts/sanitize_references.py', 'PUBLISH_CHECKLIST.md'}
        
        for file_path in self.repo_path.rglob("*"):
            if (file_path.is_file() and 
                not any(exclude in str(file_path) for exclude in exclude_files) and
                file_path.suffix in ['.py', '.js', '.ts', '.json', '.yml', '.yaml', '.md', '.sh']):
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern in company_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            found_refs.append(str(file_path.relative_to(self.repo_path)))
                            break
                except:
                    pass
        
        if found_refs:
            self.add_warning(
                "Company References Found",
                f"Found company-specific references in {len(found_refs)} files. Run sanitization script.",
                found_refs
            )
        else:
            self.add_pass(
                "Company References Check",
                "No company-specific references found"
            )

    def check_personal_info(self):
        """Check for personal information."""
        personal_patterns = [
            r'\bSuleman\b',
            r'suleman',
        ]
        
        found_personal = []
        exclude_files = {'.git', 'scripts/sanitize_references.py', 'PUBLISH_CHECKLIST.md'}
        
        for file_path in self.repo_path.rglob("*"):
            if (file_path.is_file() and 
                not any(exclude in str(file_path) for exclude in exclude_files) and
                file_path.suffix in ['.py', '.js', '.ts', '.json', '.yml', '.yaml', '.md', '.sh']):
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern in personal_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            found_personal.append(str(file_path.relative_to(self.repo_path)))
                            break
                except:
                    pass
        
        if found_personal:
            self.add_warning(
                "Personal Information Found",
                f"Found personal information in {len(found_personal)} files",
                found_personal
            )
        else:
            self.add_pass(
                "Personal Information Check",
                "No personal information found"
            )

    def check_gitignore_patterns(self):
        """Check if .gitignore contains necessary patterns."""
        gitignore_path = self.repo_path / ".gitignore"
        required_patterns = [
            'test.env',
            'test_local.env',
            '*.env.local',
            '.env.development',
            '.env.production',
        ]
        
        if not gitignore_path.exists():
            self.add_issue(
                "Missing .gitignore",
                ".gitignore file not found",
                []
            )
            return
            
        try:
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in gitignore_content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                self.add_warning(
                    "Incomplete .gitignore",
                    f"Missing {len(missing_patterns)} required patterns in .gitignore",
                    missing_patterns
                )
            else:
                self.add_pass(
                    ".gitignore Check",
                    "All required patterns found in .gitignore"
                )
        except:
            self.add_issue(
                ".gitignore Read Error",
                "Could not read .gitignore file",
                []
            )

    def run_all_checks(self):
        """Run all verification checks."""
        print("🔍 Repository Public Readiness Verification")
        print("=" * 50)
        print(f"📁 Repository: {self.repo_path}")
        print()
        
        checks = [
            ("Checking for sensitive files...", self.check_sensitive_files),
            ("Checking for API keys...", self.check_api_keys),
            ("Checking for company references...", self.check_company_references),
            ("Checking for personal information...", self.check_personal_info),
            ("Checking .gitignore patterns...", self.check_gitignore_patterns),
        ]
        
        for description, check_func in checks:
            print(f"🔍 {description}")
            try:
                check_func()
            except Exception as e:
                self.add_issue(
                    "Check Error",
                    f"Error running check: {description} - {str(e)}",
                    []
                )
        
        self.print_results()
        return len(self.issues) == 0

    def print_results(self):
        """Print verification results."""
        print("\n" + "=" * 50)
        print("📊 VERIFICATION RESULTS")
        print("=" * 50)
        
        # Print passed checks
        if self.passed_checks:
            print(f"\n✅ PASSED CHECKS ({len(self.passed_checks)}):")
            for check in self.passed_checks:
                print(f"   ✅ {check['check']}: {check['description']}")
        
        # Print warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   ⚠️  {warning['check']}: {warning['description']}")
                if warning['files']:
                    for file in warning['files'][:5]:  # Show max 5 files
                        print(f"      📄 {file}")
                    if len(warning['files']) > 5:
                        print(f"      ... and {len(warning['files']) - 5} more files")
        
        # Print critical issues
        if self.issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   ❌ {issue['check']}: {issue['description']}")
                if issue['files']:
                    for file in issue['files'][:5]:  # Show max 5 files
                        print(f"      📄 {file}")
                    if len(issue['files']) > 5:
                        print(f"      ... and {len(issue['files']) - 5} more files")
        
        # Overall status
        print("\n" + "=" * 50)
        if self.issues:
            print("❌ REPOSITORY NOT READY FOR PUBLIC RELEASE")
            print(f"   Critical issues must be fixed: {len(self.issues)}")
            if self.warnings:
                print(f"   Warnings to review: {len(self.warnings)}")
        elif self.warnings:
            print("⚠️  REPOSITORY MOSTLY READY - REVIEW WARNINGS")
            print(f"   Warnings to review: {len(self.warnings)}")
        else:
            print("✅ REPOSITORY READY FOR PUBLIC RELEASE")
            print("   All checks passed!")
        
        print("=" * 50)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Verify repository is ready for public release')
    parser.add_argument('--directory', '-d', default='.', help='Repository directory to check')
    args = parser.parse_args()
    
    verifier = RepositoryVerifier(args.directory)
    success = verifier.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 