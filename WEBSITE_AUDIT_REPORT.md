# Website Audit Report - Valley Catholic Basketball Stats

**Date:** February 13, 2026  
**Status:** Comprehensive review of entire application - Frontend, Backend, and Data Flow

---

## 🔴 CRITICAL ISSUES (Fix First)

### 1. **Version Mismatch in Cache Busting**
- **Location:** `templates/base.html` vs `templates/games.html` and `templates/players.html`
- **Issue:** base.html uses `?v=1.7` hardcoded, while games/players templates use `?v={{ timestamp }}`
- **Impact:** The `{{ timestamp }}` variable is never passed from Flask, causing template errors and invalid cache busting
- **Severity:** Users may see outdated JavaScript code
- **Fix:** Use consistent version string across all templates, either `?v=1.7` or define `timestamp` in Flask context

### 2. **Hard-coded Static Values in Dashboard**
- **Location:** `templates/dashboard.html` lines 14-15
- **Issue:** Record shows hardcoded "8-1" and "Win Percentage: 89%" instead of API values
- **Impact:** Dashboard displays stale/incorrect data on page load
- **Fix Required:** Remove hardcoded values and rely only on dynamic API loading

### 3. **LRU_CACHE on Flask Routes is Incorrect**
- **Location:** `src/app.py` lines 135, 235, 356, 509
  - `/api/season-stats`
  - `/api/team-trends`
  - `/api/advanced/patterns`
  - `/api/advanced/volatility`
- **Issue:** `@lru_cache(maxsize=1)` decorator on Flask routes caches indefinitely across ALL users
- **Impact:** 
  - Data changes but API returns stale cached data
  - Users see outdated stats
  - Must restart server to clear cache
- **Fix Required:** Remove `@lru_cache` or implement proper HTTP cache headers (Cache-Control, ETag)

### 4. **XSS Vulnerability - Unsanitized innerHTML**
- **Location:** Multiple JavaScript files:
  - `static/games.js` lines 80+
  - `static/players.js` line ~188-190+
  - `static/dashboard.js` lines 125+
- **Issue:** Using `innerHTML` to insert player/opponent names directly from API without HTML escaping
- **Risk:** High - if database is ever compromised with malicious input, XSS attacks possible
- **Evidence:** `topScorersEl.innerHTML = scorersHtml.join('')` creates unsanitized HTML
- **Fix:** Implement `escapeHtml()` function or use `textContent` instead of `innerHTML`

### 5. **Missing Error Handling in Critical Async Operations**
- **Location:** Multiple JavaScript files  
- **Examples:**
  - `static/players.js` - `loadPlayers()` at line 13 has no catch block
  - `static/games.js` - `loadGames()` at line 8 silently fails
  - `static/dashboard.js` - `loadLeaderboards()` returns empty arrays if API fails
- **Impact:** Silent failures - users see blank UI with no error message
- **Fix:** Add try/catch to all fetch calls and display user-friendly error messages

---

## 🟠 HIGH PRIORITY ISSUES (Fix Soon)

### 6. **Division by Zero Not Prevented**
- **Location:** Multiple places in JavaScript files
- **Examples:**
  - `static/games.js` line 82: `vcFgPct = (game.team_stats.fg / game.team_stats.fga * 100)` - no `fga > 0` check
  - `static/players.js` line 51: `plusMinusPerGame = plusMinus / games` - if `games === 0`, displays "Infinity"
  - `static/trends.js` - multiple division operations without checks
  - `static/dashboard.js` line 134 and similar locations
- **Impact:** UI displays "Infinity", "NaN", or "Infinity%" breaking the interface
- **Fix:** Add `if (denominator > 0)` guards before all divisions

### 7. **Missing Response Status Validation**
- **Location:** `static/ai-insights.js` lines 15-25, `static/players.js` lines 174-177
- **Issue:** Some fetch calls don't check `response.ok` before parsing JSON
- **Example:** `loadStatsContext()` should validate all three responses before using data
- **Impact:** 404 or 500 errors get parsed as JSON, causing cryptic errors
- **Fix:** Check `if (!response.ok) throw new Error('HTTP ' + response.status)` for all fetches

### 8. **Console.log Statements Left in Production**
- **Location:** Multiple JavaScript files -19 instances found
  - `static/trends.js` lines 50, 937, 945, 955, 963
  - `static/players.js` lines 98, 102, 103, 106, 109, 171, 173, 188, 189, 636, 637, 639, 775, 776, 780, 787
- **Issue:** `console.log()` statements are used for debugging but left in production code
- **Impact:** Pollutes browser console, could reveal data structure info if sensitive
- **Fix:** Remove all debug console.log statements or use a proper logging library

### 9. **Missing Global State Reset in reload_data Endpoint**
- **Location:** `src/app.py` lines 115-132 (`/api/reload-data`)
- **Issue:** When data is reloaded, `advanced_calc` is reset but Flask's `@lru_cache` decorators aren't cleared
- **Impact:** After reload, some endpoints still return cached stale data
- **Fix:** Clear all cached functions when reload is called (see issue #3)

### 10. **Chart.js Charts Not Properly Destroyed**
- **Location:** `static/dashboard.js` line 19, `static/trends.js` lines 76-80
- **Issue:** Charts are created but never `.destroy()` called when page changes or chart is replaced
- **Impact:** Memory leaks - charts accumulate in memory as users navigate
- **Evidence:** `if (teamCharts.scoring) teamCharts.scoring.destroy();` exists but not consistent
- **Fix:** Always call `.destroy()` before creating new charts or when removing from DOM

### 11. **Uncaught TypeError with Missing Data**
- **Location:** `static/players.js` line 18 and similar sorting operations
- **Issue:** `allPlayers.sort((a, b) => a.number - b.number)` assumes `number` property exists
- **Impact:** If roster data is missing or incomplete, sorting fails silently
- **Fix:** Add filter/validation: `allPlayers.filter(p => p.number).sort(...)`

### 12. **Race Condition in Promise.all()**
- **Location:** `static/trends.js` lines 32-36 and similar multi-async sections
- **Issue:** `Promise.all()` fails if any one fetch fails, leaving app in partial state
- **Impact:** If one API endpoint is slow/down, entire page fails to load
- **Fix:** Use `.allSettled()` instead to handle partial failures gracefully

---

## 🟡 MEDIUM PRIORITY ISSUES (Improve UX)

### 13. **Inconsistent Error Messages Across Endpoints**
- **Location:** Various API routes in `src/app.py`
- **Issue:** Error responses use different formats - some return `{"error": "..."}`, others different structures
- **Impact:** Frontend has no consistent error handling pattern
- **Fix:** Standardize all error responses to: `{"error": "message", "code": "ERROR_CODE"}`

### 14. **No Loading States for Long-Running Operations**
- **Location:** AI analysis endpoints (can take 5-15 seconds)
- **Issue:** No visual feedback while waiting for response - appears frozen
- **Fix:** Add loading spinner, progress indicator, or "thinking..." message

### 15. **No Request Timeout Implementation**
- **Location:** All `fetch()` calls in JavaScript
- **Issue:** If API hangs, fetch waits indefinitely with no timeout
- **Fix:** Wrap fetch with AbortController to set 30-second timeout

### 16. **Accessibility Issues**
- **Location:** Multiple HTML templates
- **Issues:**
  - Modals don't trap focus (keyboard users can tab out)
  - No keyboard navigation (should close modals with Escape key)
  - Some form inputs missing labels/aria-labels
  - Color-only indicators (red/green) need text alternatives
- **Fix:** Add aria attributes, keyboard handlers, focus trapping

### 17. **Input Validation Only on Client Side**
- **Location:** Player names in JavaScript filters and form inputs
- **Issue:** While basic length checks exist, no server-side validation of player names
- **Impact:** Malformed requests could reach API (though server does validate)
- **Fix:** Add server-side validation for all user inputs

### 18. **No Search Debouncing in Filter Operations**  
- **Location:** `static/players.js` `filterPlayers()` and `static/games.js` `filterGames()`
- **Issue:** Filter function runs on every keystroke without debouncing
- **Impact:** With large datasets, excessive re-renders could cause lag
- **Fix:** Add 300ms debounce to search input handlers

### 19. **Modal Visibility Not Hidden by Default in CSS**
- **Location:** `static/style.css` - `.modal` styling
- **Issue:** Modal uses `.show` class to display but default is `display: none` yet `.show` uses `display: flex`
- **Impact:** Potential flashing on page load if JavaScript hasn't run
- **Fix:** Ensure modals are properly hidden initially

### 20. **Player Detail Modal Not Context-Aware**
- **Location:** `static/players.js` modal display
- **Issue:** Modal shows same data whether user is in "Cards" or "Rankings" view
- **Impact:** Confusing when filtered by specific stat but modal doesn't reflect filter
- **Fix:** Store context of where modal was opened from

---

## 🔵 LOW PRIORITY ISSUES (Nice to Have)

### 21. **AI Insights Page Stats Panel Unclear**
- **Location:** `templates/ai-insights.html` and `static/ai-insights.js`
- **Issue:** Stats panel toggles but purpose not obvious to new users
- **Fix:** Add help text or tooltip explaining the panel

### 22. **No Rate Limiting on API Endpoints**
- **Location:** All API routes in `src/app.py`
- **Issue:** No protection against repeated requests or bot attacks
- **Fix:** Add Flask-Limiter or similar to rate limit endpoints

### 23. **Season Analysis API Could Timeout**
- **Location:** `src/app.py` `/api/season-analysis` route
- **Issue:** Makes one API call per game (20+ calls) sequentially - could hit timeouts
- **Impact:** Season analysis fails on larger seasons
- **Fix:** Implement parallel/batched AI API calls with circuit breaker

### 24. **No Dark/Light Mode Toggle**
- **Location:** Application-wide
- **Issue:** App is dark-themed but no option for light mode
- **Fix:** Could add theme toggle in navbar (nice-to-have)

### 25. **Documentation Structure Scattered**
- **Location:** Root directory has multiple README files
- **Issue:** `README.md`, `READ_ME_FIRST.txt`, `START_HERE.txt`, `GITHUB_READY.md`, etc.
- **Fix:** Consolidate into single clear documentation structure

### 26. **Missing "No Data" States**
- **Location:** Various pages (Games, Players, Trends)
- **Issue:** If data is empty, pages show empty grids
- **Fix:** Display helpful "No data available" messages

### 27. **Admin Panel Missing**
- **Location:** Would be useful to have
- **Issue:** No interface to manage excluded players or reload data manually
- **Fix:** Could create admin dashboard for data management

### 28. **Chart.js Responsive Issues on Mobile**
- **Location:** `static/dashboard.js` and `static/trends.js`
- **Issue:** Charts look small on mobile, text hard to read
- **Fix:** Adjust chart options for mobile viewport

---

## ✅ WHAT'S WORKING WELL

1. ✓ Clean separation of concerns (templates, static, API)
2. ✓ Good responsive design for mobile devices
3. ✓ Comprehensive statistics calculations
4. ✓ Advanced stats with multiple metrics
5. ✓ Security headers implemented correctly
6. ✓ Proper environment variable usage (.env)
7. ✓ Good logging structure with logger
8. ✓ Database migration support
9. ✓ Modal implementations work correctly
10. ✓ Search/filter functionality works well
11. ✓ API endpoints properly structured
12. ✓ AI integration is functional

---

## 🔧 RECOMMENDED FIX PRIORITY

### Phase 1: Critical Bugs (Do First - 4-6 hours)
1. Remove or fix `@lru_cache` decorators on Flask routes
2. Fix version mismatch in template cache busting
3. Add error handling to all fetch calls  
4. Fix division by zero issues
5. Implement XSS protection with HTML escaping

### Phase 2: High Priority (1-2 days)
6. Remove all console.log statements
7. Implement chart destruction on page changes
8. Fix Promise.all() race conditions
9. Add response status validation to all fetches
10. Clear caches when data is reloaded

### Phase 3: Medium Priority (1-2 days)
11. Add loading states for long operations
12. Implement request timeouts
13. Add keyboard navigation to modals
14. Standardize error response format
15. Add input validation feedback

---

## 📊 SUMMARY

- **Total Issues Found:** 28
- **Critical:** 5
- **High Priority:** 7  
- **Medium Priority:** 8
- **Low Priority:** 8

**Estimated Effort to Fix All:**
- Critical Issues: 4-6 hours
- High Priority: 6-8 hours
- Medium Priority: 4-6 hours
- Low Priority: 2-4 hours
- **Total: 16-24 hours**

**Quick Wins (30 minutes each):**
- Remove console.log statements
- Fix hardcoded dashboard values
- Add null checks before divisions

