# 📋 Public Repository Publishing Checklist

Use this checklist to ensure your repository is ready for public release.

## ✅ **CRITICAL SECURITY STEPS** (Must Complete)

### 1. Remove Sensitive Files from Repository
- [ ] Run: `git rm --cached test.env test_local.env`
- [ ] Verify files are in `.gitignore` 
- [ ] Confirm files still exist locally but not in git tracking

### 2. Sanitize Company References
- [ ] Run: `python3 scripts/sanitize_references.py --dry-run --verbose`
- [ ] Review changes that will be made
- [ ] Run: `python3 scripts/sanitize_references.py` (live changes)
- [ ] Verify all `zgcompanies.com` → `example.com` changes
- [ ] Verify all `smanji@` → `admin@example.com` changes

### 3. Update Example Files
- [ ] Verify `env.example` contains only placeholder values
- [ ] Verify `test.env.example` contains only placeholder values
- [ ] Check no real API keys in any `.example` files

### 4. Clean Git History (if needed)
- [ ] Check if sensitive files were previously committed: `git log --name-only --oneline | grep -E "test\.env|test_local\.env"`
- [ ] If found, consider: `git filter-branch` or create fresh repository

## ✅ **DOCUMENTATION UPDATES**

### 5. Update README.md
- [ ] Replace company-specific references
- [ ] Add generic setup instructions
- [ ] Update contact information to be generic
- [ ] Verify all URLs are generic or localhost

### 6. Update Contributing Guidelines
- [ ] Review `CONTRIBUTING.md` for company references
- [ ] Ensure security guidelines are appropriate for public
- [ ] Update contact information

### 7. License and Legal
- [ ] Verify `LICENSE` is appropriate (currently MIT)
- [ ] Ensure no proprietary information in license
- [ ] Check copyright notices are generic

## ✅ **VERIFICATION STEPS**

### 8. Security Scan
Run the verification script:
```bash
python3 scripts/verify_public_ready.py
```

### 9. Manual Verification
- [ ] Search for API keys: `grep -r "sk-proj\|sk-" . --exclude-dir=.git`
- [ ] Search for company references: `grep -r "zgcompanies\|smanji" . --exclude-dir=.git`
- [ ] Search for personal info: `grep -r "Suleman" . --exclude-dir=.git`
- [ ] Check `.gitignore` includes all sensitive patterns

### 10. Test Fresh Clone
- [ ] Clone to new directory: `git clone . ../emailprocer-test`
- [ ] Verify no sensitive files in fresh clone
- [ ] Test setup process with `REPOSITORY_SETUP.md`

## ✅ **FINAL PREPARATION**

### 11. Repository Settings
- [ ] Set repository to public
- [ ] Add appropriate topics/tags
- [ ] Configure branch protection if needed
- [ ] Set up issue templates if desired

### 12. Documentation Review
- [ ] Update project description
- [ ] Ensure all documentation is public-appropriate
- [ ] Add badges (build status, license, etc.)
- [ ] Update any internal links to be public URLs

## 🔍 **AUTOMATED VERIFICATION**

Use these commands to verify repository readiness:

```bash
# Check for sensitive patterns
grep -r "sk-proj\|sk-" . --exclude-dir=.git || echo "✅ No API keys found"
grep -r "@zgcompanies\|smanji@" . --exclude-dir=.git || echo "✅ No company emails found"  
grep -r "zgcompanies\.com" . --exclude-dir=.git || echo "✅ No company domains found"

# Check ignored files status
git status --ignored | grep -E "test\.env|test_local\.env" && echo "✅ Sensitive files properly ignored"

# Verify no staged sensitive files
git diff --cached --name-only | grep -E "\.env$|test.*\.env$" && echo "❌ Sensitive files staged!" || echo "✅ No sensitive files staged"
```

## 🚨 **EMERGENCY ROLLBACK**

If sensitive information is accidentally published:

1. **Immediate Actions:**
   ```bash
   # Make repository private immediately
   # Rotate all exposed credentials (API keys, secrets)
   # Remove sensitive commits from history
   ```

2. **Credential Rotation:**
   - [ ] Rotate OpenAI API keys
   - [ ] Rotate M365 application secrets
   - [ ] Update webhook URLs
   - [ ] Change database passwords

3. **Notification:**
   - [ ] Notify team of exposure
   - [ ] Document incident
   - [ ] Review security procedures

## ✅ **READY FOR PUBLISH**

- [ ] All security steps completed
- [ ] All documentation updated  
- [ ] All verification checks passed
- [ ] Team review completed
- [ ] Emergency procedures documented

**Final verification date:** `_____________`  
**Verified by:** `_____________`  
**Ready for public release:** ☐ YES ☐ NO 