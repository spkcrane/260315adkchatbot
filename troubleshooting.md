# Troubleshooting Guide

## 🔧 Common Issues & Solutions

### ADK Authentication Problems

**Issue:** `Error: Unable to authenticate with Google ADK`
```
Error: 3 INVALID_ARGUMENT: Request contains an invalid argument
```

**Solutions:**
1. **Check Service Account Key:**
   ```bash
   # Verify key file exists and is readable
   ls -la $GOOGLE_APPLICATION_CREDENTIALS
   cat $GOOGLE_APPLICATION_CREDENTIALS | head -5
   ```

2. **Verify Environment Variable:**
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS
   # Should point to valid JSON file
   ```

3. **Test Authentication:**
   ```bash
   gcloud auth application-default print-access-token
   ```

4. **Check Project Permissions:**
   - Ensure service account has ADK permissions
   - Verify project ID is correct

---

### LINE Webhook Setup Issues

**Issue:** `Webhook verification failed`
```
Error: Webhook URL is not responding
```

**Solutions:**
1. **Check Server Accessibility:**
   ```bash
   # Test webhook endpoint
   curl -X GET https://your-domain.com/webhook
   ```

2. **Verify SSL Certificate:**
   - LINE requires HTTPS
   - Use services like ngrok for testing: `ngrok http 3000`

3. **Check Channel Configuration:**
   - Verify Channel Access Token
   - Confirm Webhook URL in LINE Console

4. **Test Webhook Response:**
   ```javascript
   // Should return 200 OK for GET requests
   app.get('/webhook', (req, res) => {
     res.status(200).send('OK');
   });
   ```

---

### Memory Persistence Errors

**Issue:** `Memory not persisting between sessions`
```
Error: Unable to save/load memory data
```

**Solutions:**
1. **Check Database Connection:**
   ```javascript
   // Test database connectivity
   const db = new Database(process.env.DATABASE_URL);
   await db.connect();
   ```

2. **Verify Memory Configuration:**
   ```javascript
   const memory = new PersistentMemory({
     storage: 'database', // or 'file', 'redis'
     connectionString: process.env.DATABASE_URL
   });
   ```

3. **Check File Permissions (File Storage):**
   ```bash
   ls -la memory/
   chmod 755 memory/
   ```

---

### Agent Response Issues

**Issue:** `Agent not responding correctly`
```
Agent returns unexpected or empty responses
```

**Solutions:**
1. **Check Agent Configuration:**
   ```javascript
   const agent = new Agent({
     name: 'SalesAgent',
     tools: [/* required tools */],
     memory: memoryInstance
   });
   ```

2. **Verify Tool Integration:**
   - Ensure tools are properly imported
   - Check tool authentication/credentials

3. **Test Individual Components:**
   ```javascript
   // Test agent initialization
   await agent.initialize();

   // Test tool execution
   const result = await tool.execute({ input: 'test' });
   ```

---

### Deployment Issues

**Issue:** `Application fails to start in production`
```
Error: Port already in use or connection refused
```

**Solutions:**
1. **Check Environment Variables:**
   ```bash
   # Production environment
   NODE_ENV=production
   PORT=8080
   DATABASE_URL=postgresql://...
   ```

2. **Verify Dependencies:**
   ```bash
   npm ls --depth=0
   # Check for missing packages
   ```

3. **Test Build Process:**
   ```bash
   npm run build
   npm run start
   ```

---

### Performance Issues

**Issue:** `Slow response times`
```
Response time > 5 seconds
```

**Solutions:**
1. **Optimize Memory Usage:**
   - Use efficient storage backends (Redis vs Database)
   - Implement memory cleanup strategies

2. **Check Network Latency:**
   ```bash
   # Test API response times
   curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com
   ```

3. **Monitor Resource Usage:**
   ```bash
   # Check CPU/Memory
   top -p $(pgrep node)
   ```

---

## 🆘 Emergency Contacts

- **Technical Support:** [email/phone]
- **LINE Developer Support:** [LINE Support Link]
- **Google Cloud Support:** [Cloud Support Link]

## 📝 Debug Checklist

- [ ] Environment variables set correctly
- [ ] Dependencies installed (`npm install`)
- [ ] Database/services running
- [ ] Network connectivity
- [ ] Authentication credentials valid
- [ ] Logs checked for error messages

## 🔍 Log Analysis

**Enable Debug Logging:**
```javascript
process.env.DEBUG = 'adk:*';
process.env.LINE_BOT_DEBUG = true;
```

**Common Log Patterns:**
- `Authentication failed` → Check credentials
- `Connection timeout` → Network issues
- `Invalid request` → API parameter errors
- `Memory full` → Storage capacity issues

---

*If you encounter issues not covered here, please document the error and contact support with relevant logs.*