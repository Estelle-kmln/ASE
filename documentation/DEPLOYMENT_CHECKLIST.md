# 🚀 Battlecards Deployment Checklist

## Pre-Deployment Verification

### ✅ Frontend Files
- [x] login.html
- [x] index.html (homepage)
- [x] deck-selection.html
- [x] game.html
- [x] profile.html
- [x] game-history.html
- [x] statistics.html
- [x] rules.html
- [x] welcome.html
- [x] css/styles.css
- [x] js/auth.js
- [x] js/home.js
- [x] js/deck-selection.js
- [x] js/game.js
- [x] js/profile.js
- [x] js/game-history.js

### ✅ Configuration Files
- [x] docker-compose.yml (updated with frontend volume)
- [x] nginx/nginx.conf (updated to serve frontend)

### ✅ Documentation
- [x] frontend/README.md
- [x] frontend/IMPLEMENTATION.md
- [x] QUICK_START.md

## Deployment Steps

### 1. Stop Existing Containers
```powershell
cd microservices
docker compose down
```

### 2. Rebuild with New Configuration
```powershell
docker compose up -d --build
```

### 3. Verify Services
```powershell
docker compose ps
```

Expected output - all services should be "Up" and "healthy":
- postgresql
- auth-service
- card-service
- game-service
- leaderboard-service
- api-gateway

### 4. Check Logs
```powershell
# Check nginx gateway logs
docker compose logs api-gateway

# Should see: "Configuration complete; ready for start up"
```

### 5. Test Frontend Access
Open browser to: `http://localhost:8080`

Expected: Login page loads with Battlecards styling

## Testing Checklist

### Authentication Flow
- [ ] Register new user
- [ ] Logout
- [ ] Login with created user
- [ ] Redirected to homepage after login

### Homepage
- [ ] "Battlecards!" header visible
- [ ] Menu button (☰) works
- [ ] Dropdown menu shows username
- [ ] Two large game buttons visible
- [ ] "LAUNCH A GAME!" button works
- [ ] Modal shows game code
- [ ] "JOIN A GAME!" button works
- [ ] Join modal accepts code input

### Deck Selection
- [ ] Back button visible
- [ ] Manual/Random toggle works
- [ ] +/- buttons work for card selection
- [ ] Total card count updates
- [ ] Cannot exceed 10 cards
- [ ] Confirm button enables when 10 cards selected

### Game Play
- [ ] Quit button visible
- [ ] Player names and scores display
- [ ] Turn number shows
- [ ] Hand displays cards with emojis
- [ ] Can select cards
- [ ] Play button enables when card selected
- [ ] Cards play and reveal
- [ ] Scores update after each round
- [ ] Game over modal appears at end

### Victory/Defeat
- [ ] Victory shows gold crown 👑
- [ ] Defeat shows grey skull 💀
- [ ] Final score displays
- [ ] Return to home button works

### Profile
- [ ] Back button works
- [ ] Profile data loads
- [ ] Edit button enables fields
- [ ] Cancel button reverts changes
- [ ] Save button updates profile
- [ ] Password validation works

### Leaderboard
- [ ] Back button works
- [ ] Match history loads
- [ ] Table displays correctly
- [ ] Pagination works
- [ ] Win/Loss colored correctly

### Menu Navigation
- [ ] Profile link works
- [ ] Leaderboard link works
- [ ] Statistics link works
- [ ] Rules link works
- [ ] Logout works

## API Connectivity Tests

### Test Auth Endpoints
```powershell
# Register
curl -X POST http://localhost:8080/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{\"username\":\"test\",\"password\":\"test123\"}'

# Login
curl -X POST http://localhost:8080/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"username\":\"test\",\"password\":\"test123\"}'
```

### Test Game Endpoints
```powershell
# Create game (use token from login)
curl -X POST http://localhost:8080/api/game/create `
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Common Issues & Solutions

### Issue: Cannot access http://localhost:8080
**Solution:**
```powershell
# Check if api-gateway is running
docker compose ps api-gateway

# View logs
docker compose logs api-gateway

# Restart if needed
docker compose restart api-gateway
```

### Issue: CSS/JS not loading
**Solution:**
```powershell
# Verify volume mount
docker compose config | Select-String "frontend"

# Should see: ../frontend:/usr/share/nginx/html:ro

# Force browser refresh: Ctrl+F5
```

### Issue: API calls failing (CORS errors)
**Solution:**
```powershell
# Check nginx config
docker compose exec api-gateway cat /etc/nginx/nginx.conf

# Verify CORS headers are present
# Restart nginx
docker compose restart api-gateway
```

### Issue: Login not working
**Solution:**
```powershell
# Check auth-service logs
docker compose logs auth-service

# Verify database connection
docker compose logs postgresql
```

### Issue: Game creation/joining fails
**Solution:**
```powershell
# Check game-service logs
docker compose logs game-service

# Verify card-service is healthy
docker compose ps card-service
```

## Performance Checks

### Check Response Times
- [ ] Login < 1 second
- [ ] Homepage load < 500ms
- [ ] Game creation < 1 second
- [ ] Card play < 500ms

### Check Polling Intervals
- [ ] Game status polling: 2-3 seconds
- [ ] Game state polling: 3 seconds
- [ ] No excessive API calls

## Security Checks

- [ ] JWT tokens required for protected routes
- [ ] Passwords not visible in network tab
- [ ] HTTPS redirect working (if SSL enabled)
- [ ] No sensitive data in localStorage (only token)
- [ ] CORS headers properly configured

## Browser Compatibility

Test in:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if available)
- [ ] Mobile browsers

## Mobile Responsiveness

Test on mobile viewport:
- [ ] Login page readable
- [ ] Buttons tap-friendly
- [ ] Game cards selectable
- [ ] Tables scroll horizontally
- [ ] Menu accessible

## Final Sign-Off

- [ ] All services healthy
- [ ] Frontend loads correctly
- [ ] Can create account
- [ ] Can login
- [ ] Can launch game
- [ ] Can join game
- [ ] Can select deck
- [ ] Can play game
- [ ] Can view profile
- [ ] Can view leaderboard
- [ ] All navigation works
- [ ] No console errors
- [ ] Documentation complete

## Rollback Plan

If issues occur:
```powershell
# Stop all services
docker compose down

# Restore previous version (if needed)
git checkout <previous-commit>

# Restart
docker compose up -d
```

## Post-Deployment

### Monitor Logs
```powershell
# Watch all logs
docker compose logs -f

# Watch specific service
docker compose logs -f api-gateway
docker compose logs -f auth-service
docker compose logs -f game-service
```

### Database Backup
```powershell
# Backup database
docker compose exec postgresql pg_dump -U gameuser battlecards > backup.sql
```

## Success Criteria

✅ Application accessible at http://localhost:8080
✅ Users can register and login
✅ Users can create and join games
✅ Gameplay works end-to-end
✅ No critical errors in logs
✅ All pages accessible
✅ All navigation functional
✅ Responsive on mobile
✅ Documentation complete

---

**Deployment Date:** _________________
**Deployed By:** _________________
**Status:** ⬜ Success  ⬜ Issues  ⬜ Rollback

**Notes:**
_______________________________________
_______________________________________
_______________________________________
