# 🎯 ACTION PLAN - NEXT STEPS

## ✅ CÔNG VIỆC ĐÃ HOÀN THÀNH

### 1. Automatic Refactor ✅
- ✅ Chạy `refactor_app_auto.py` thành công
- ✅ Tạo file `app.py.refactored` (2225 dòng)
- ✅ Tạo báo cáo `refactor_report.txt`

### 2. Changes Applied (12 changes)
1. ✅ Added dual-mode imports
2. ✅ Commented out old `get_db()` function
3. ✅ Commented out old `query_db()` function
4. ✅ Commented out old `execute_db()` function
5. ✅ Replaced 4 SELECT TOP N patterns
6. ✅ Replaced 1 GETDATE() calls
7. ✅ Replaced 2 row locking patterns
8. ✅ Replaced 17 ISNULL() calls
9. ⚠️  Added warning for 78 placeholders (MANUAL REVIEW REQUIRED)
10. ✅ Updated webhook import to dual-mode version
11. ✅ Added initialization code
12. ✅ Updated main block with `init_db()`

---

## 🚧 CÔNG VIỆC CÒN LẠI

### ⚠️ CRITICAL: Manual Review Required

#### Issue 1: Placeholders (78 instances)
**Problem**: SQL Server dùng `?`, PostgreSQL dùng `%s`

**Current state**: File có 78 chỗ dùng `?` placeholder

**Solution Options**:

**Option A: Use db_utils functions (RECOMMENDED)**
- `query_db()` và `execute_db()` từ `db_utils.py` đã tự động xử lý placeholders
- Không cần sửa gì nếu đang dùng 2 functions này
- ✅ **KHUYẾN NGHỊ**: Kiểm tra xem 78 placeholders có phải đang dùng `query_db()` / `execute_db()` không

**Option B: Fix direct cursor.execute() calls**
- Nếu có `cursor.execute("... WHERE id = ?", [id])` trực tiếp
- Cần đổi thành: `cursor.execute(f"... WHERE id = {'%s' if IS_POSTGRESQL else '?'}", [id])`
- Script `fix_placeholders.py` đã tạo sẵn (chưa chạy)

#### Issue 2: LIMIT Clauses (4 instances)
**Problem**: Đã thay `SELECT TOP N` → `SELECT {sql_limit(N)}` nhưng chưa thêm `{sql_limit_clause(N)}` ở cuối query

**Example**:
```python
# Current (incomplete):
query = f"SELECT {sql_limit(10)} * FROM vehicles WHERE status='parked'"

# Should be:
query = f"SELECT {sql_limit(10)} * FROM vehicles WHERE status='parked' {sql_limit_clause(10)}"
```

**Action**: Tìm 4 chỗ có `{sql_limit(` và thêm `{sql_limit_clause(N)}` ở cuối query

---

## 📋 STEP-BY-STEP ACTION PLAN

### PHASE 1: REVIEW (30 phút)

#### Step 1.1: Check Placeholders
```bash
# Kiểm tra xem 78 placeholders đang dùng function nào
grep -n "?" app.py.refactored | head -20
```

**Nếu hầu hết dùng `query_db()` / `execute_db()`**:
- ✅ Không cần fix (db_utils đã xử lý)
- Chỉ cần fix các `cursor.execute()` trực tiếp

**Nếu nhiều `cursor.execute()` trực tiếp**:
- ⚠️ Cần chạy `fix_placeholders.py`
- Hoặc sửa thủ công

#### Step 1.2: Fix LIMIT Clauses
```bash
# Tìm các chỗ cần thêm LIMIT clause
grep -n "sql_limit(" app.py.refactored
```

Sửa 4 chỗ này thủ công (xem ví dụ ở trên)

#### Step 1.3: Review Import Section
```bash
# Kiểm tra imports đã đúng chưa
head -100 app.py.refactored | grep -A 20 "DUAL-MODE"
```

Đảm bảo có:
- ✅ `from db_utils import ...`
- ✅ `from fix_payment_webhook_dual import payment_result_route`

---

### PHASE 2: TEST LOCAL (30 phút)

#### Step 2.1: Backup Original
```bash
cp app.py app.py.original_backup
```

#### Step 2.2: Test Refactored Version
```bash
# Rename để test
mv app.py app.py.old
mv app.py.refactored app.py

# Run app
python app.py
```

**Expected Output**:
```
🗄️  Using SQL Server (Local)
✅ Database initialized (dual-mode)
 * Running on http://0.0.0.0:5000
```

#### Step 2.3: Test Features
- [ ] Truy cập http://localhost:5000
- [ ] Đăng nhập admin
- [ ] Xem dashboard
- [ ] Test xe vào bãi
- [ ] Test xe ra bãi
- [ ] Test nạp tiền

**If errors occur**:
1. Check logs
2. Fix issues
3. Repeat test

**If all tests pass**:
- ✅ Proceed to Phase 3

---

### PHASE 3: COMMIT & PUSH (15 phút)

#### Step 3.1: Git Status
```bash
git status
```

#### Step 3.2: Add Files
```bash
git add app.py
git add db_utils.py
git add fix_payment_webhook_dual.py
git add schema_postgresql.sql
git add render.yaml
git add .env.example
git add requirements.txt
```

#### Step 3.3: Commit
```bash
git commit -m "Add dual-mode support for Render deployment

- Refactored app.py to support both SQL Server (local) and PostgreSQL (Render)
- Added db_utils.py for automatic database detection
- Added fix_payment_webhook_dual.py for dual-mode webhook
- Added schema_postgresql.sql for PostgreSQL schema
- Added render.yaml for Infrastructure as Code
- Updated requirements.txt with psycopg2-binary and gunicorn

Changes:
- Auto-detect environment based on DATABASE_URL
- Convert SQL syntax (TOP N, GETDATE(), row locking, ISNULL)
- Connection pooling for PostgreSQL
- Idempotency and race condition handling
"
```

#### Step 3.4: Push
```bash
git push origin main
```

---

### PHASE 4: DEPLOY TO RENDER (1-2 giờ)

Follow: `CHECKLIST_DEPLOY_RENDER.md`

#### Quick Steps:
1. ✅ Tạo PostgreSQL Database trên Render
2. ✅ Chạy `schema_postgresql.sql`
3. ✅ Tạo Web Service
4. ✅ Cấu hình Environment Variables
5. ✅ Deploy
6. ✅ Test

---

## 🔍 TROUBLESHOOTING

### Issue: Import Error
```
ModuleNotFoundError: No module named 'db_utils'
```

**Solution**:
```bash
# Kiểm tra file tồn tại
ls -la db_utils.py

# Nếu không có, tạo lại từ backup hoặc documentation
```

### Issue: Syntax Error in Queries
```
OperationalError: syntax error at or near "{"
```

**Solution**:
- Kiểm tra f-string có đúng không
- Đảm bảo `{sql_limit()}` được evaluate đúng
- Review query syntax

### Issue: Placeholder Error
```
TypeError: not all arguments converted during string formatting
```

**Solution**:
- Kiểm tra số lượng `?` hoặc `%s` khớp với số parameters
- Review placeholder conversion

---

## 📊 PROGRESS TRACKER

### Refactoring Progress
- [x] Run automatic refactor script
- [ ] Review placeholders (78 instances)
- [ ] Fix LIMIT clauses (4 instances)
- [ ] Test on Local (SQL Server)
- [ ] Fix any errors
- [ ] Commit and push
- [ ] Deploy to Render
- [ ] Test on Production

### Estimated Time Remaining
- Review & Fix: 30-60 phút
- Test Local: 30 phút
- Commit & Push: 15 phút
- Deploy: 1-2 giờ
- **Total**: 2.5-4 giờ

---

## 🎯 SUCCESS CRITERIA

### Local (SQL Server)
- [ ] App starts without errors
- [ ] Logs show: `🗄️ Using SQL Server (Local)`
- [ ] All features work
- [ ] No database errors

### Render (PostgreSQL)
- [ ] Build succeeds
- [ ] App starts without errors
- [ ] Logs show: `🐘 Using PostgreSQL (Render)`
- [ ] HTTPS accessible
- [ ] All features work
- [ ] MoMo webhook works

---

## 📞 SUPPORT

### If Stuck:
1. Check `refactor_report.txt` for details
2. Check `MIGRATION_GUIDE_APP_PY.md` for examples
3. Check `HUONG_DAN_DEPLOY_RENDER.md` for deployment help
4. Check logs for specific errors

### Files Created:
- `app.py.refactored` - Refactored app
- `refactor_report.txt` - Refactor report
- `refactor_app_auto.py` - Auto refactor script
- `fix_placeholders.py` - Placeholder fix script (optional)
- `ACTION_PLAN_NEXT_STEPS.md` - This file

---

**Tác giả**: KIRO AI Assistant  
**Ngày tạo**: 2026-04-21  
**Phiên bản**: 1.0.0  
**Status**: Ready for Manual Review
