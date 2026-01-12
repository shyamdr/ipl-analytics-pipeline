# Security Notice

## ⚠️ IMPORTANT: API Key Security

### Before Pushing to GitHub:

1. **Never commit your actual `.env` file** - It's already in `.gitignore`

2. **If you've already committed `.env` with real keys:**
   ```bash
   # Remove from Git history
   git rm --cached .env
   git commit -m "Remove .env from repository"
   
   # Regenerate ALL API keys immediately:
   # - Google AI API: https://makersuite.google.com/app/apikey
   # - Google Search API: https://console.cloud.google.com/apis/credentials
   ```

3. **Use `.env.example` as a template** - This file is safe to commit

4. **Check Git history for leaked keys:**
   ```bash
   git log --all --full-history -- .env
   ```

### If Keys Were Exposed:
- Regenerate them immediately
- Consider using GitHub's secret scanning alerts
- For production, use AWS Secrets Manager or similar

### Best Practices:
- ✅ Use `.env.example` for documentation
- ✅ Keep `.env` in `.gitignore`
- ✅ Rotate keys regularly
- ✅ Use different keys for dev/prod
- ❌ Never hardcode keys in source files
- ❌ Never commit `.env` to Git
