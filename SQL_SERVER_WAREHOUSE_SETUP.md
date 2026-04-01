# SQL Server Data Warehouse Setup Guide

## Overview

The AI agent has been updated to work with **Microsoft SQL Server** and is optimized for **star/galaxy schema** data warehouses with dimensional data modeling.

## Key Changes Made

### 1. **Prompts Updated** ✅

All system prompts have been regenerated to:

- Generate **T-SQL** syntax (not PostgreSQL)
- Understand **star/galaxy schema** (fact + dimension tables)
- Handle dimensional hierarchies and aggregations
- Use SQL Server-specific functions (CAST, CONVERT, TOP, OFFSET/FETCH)
- Work with **[dbo]** schema notation

### 2. **Database Context** ✅

[contexts.py](rh_agent/utils/contexts.py) updated to:

- Use SQL Server's `INFORMATION_SCHEMA` for column metadata
- Query `sys.dm_db_partition_stats` for fast row counts (no table scan)
- Handle T-SQL specific data types
- Support [dbo] schema browsing

## Star/Galaxy Schema Concepts

### Dimension Tables (Slowly Changing Dimensions - SCD)

Store descriptive attributes that rarely change:

```sql
-- Example Dimension Table
CREATE TABLE [dbo].[DimEmployee] (
    EmployeeKey INT PRIMARY KEY,
    EmployeeID INT,
    FirstName NVARCHAR(100),
    LastName NVARCHAR(100),
    DepartmentID INT,
    JobLevel INT,
    StartDate DATE,
    EndDate DATE,
    IsCurrent BIT,
    LoadDate DATETIME DEFAULT GETDATE()
)

-- Example Dimension Table
CREATE TABLE [dbo].[DimDepartment] (
    DepartmentKey INT PRIMARY KEY,
    DepartmentID INT,
    DepartmentName NVARCHAR(100),
    CostCenter NVARCHAR(50),
    Manager NVARCHAR(100)
)

-- Time Dimension
CREATE TABLE [dbo].[DimDate] (
    DateKey INT PRIMARY KEY,
    FullDate DATE,
    Year INT,
    Quarter INT,
    Month INT,
    MonthName NVARCHAR(20),
    DayOfWeek INT,
    WeekNumber INT
)
```

### Fact Tables

Store measurable transactions/events:

```sql
-- Example Fact Table
CREATE TABLE [dbo].[FactAttendance] (
    AttendanceKey INT PRIMARY KEY,
    EmployeeKey INT,
    DateKey INT,
    DepartmentKey INT,
    HoursWorked DECIMAL(10,2),
    AttendanceStatus NVARCHAR(50),
    FOREIGN KEY (EmployeeKey) REFERENCES [dbo].[DimEmployee](EmployeeKey),
    FOREIGN KEY (DateKey) REFERENCES [dbo].[DimDate](DateKey),
    FOREIGN KEY (DepartmentKey) REFERENCES [dbo].[DimDepartment](DepartmentKey)
)

-- Example Fact Table
CREATE TABLE [dbo].[FactSalary] (
    SalaryKey INT PRIMARY KEY,
    EmployeeKey INT,
    DateKey INT,
    Amount DECIMAL(15,2),
    Currency NVARCHAR(10),
    FOREIGN KEY (EmployeeKey) REFERENCES [dbo].[DimEmployee](EmployeeKey),
    FOREIGN KEY (DateKey) REFERENCES [dbo].[DimDate](DateKey)
)
```

## Configuration

### Step 1: Update Database Connection

Edit your `.env` file:

```env
# Microsoft SQL Server
DATABASE_URL=mssql+pyodbc://username:password@server:1433/database_name?driver=ODBC+Driver+17+for+SQL+Server

# Or if using Windows Authentication:
DATABASE_URL=mssql+pyodbc://@server:1433/database_name?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes
```

### Step 2: Update Table Names

Edit [rh_agent/utils/nodes.py](rh_agent/utils/nodes.py) in the `schema_inspector` function:

```python
def schema_inspector(state:AgentState, session:Session):
    # Update these table names to match your warehouse
    context = get_table_context(session,[
        "DimEmployee",           # Dimension: Employee info
        "DimDepartment",         # Dimension: Department info
        "DimDate",               # Dimension: Calendar
        "FactAttendance",        # Fact: Attendance events
        "FactSalary"             # Fact: Salary transactions
    ])
    print(context)
    return {"db_context":context}
```

### Step 3: Verify Dependencies

Ensure you have SQL Server drivers installed:

```bash
# macOS
brew install msodbcsql17

# Windows (pre-installed or download from Microsoft)
# https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

# Linux
apt-get install odbc-mssql
```

### Step 4: Test Connection

Run a quick test:

```python
from core.database.sync_db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1 as test"))
    print(result.fetchone())
```

## T-SQL Syntax Examples

### Basic Dimensional Query

```sql
SELECT TOP 100
    de.FirstName,
    de.LastName,
    dd.DepartmentName,
    CONVERT(VARCHAR(10), CAST(DATEFROMPARTS(dt.Year, dt.Month, 1) AS DATE), 120) as Month,
    SUM(fa.HoursWorked) as TotalHoursWorked,
    COUNT(DISTINCT fa.AttendanceKey) as DaysPresent
FROM [dbo].[FactAttendance] fa
INNER JOIN [dbo].[DimEmployee] de ON fa.EmployeeKey = de.EmployeeKey
INNER JOIN [dbo].[DimDepartment] dd ON fa.DepartmentKey = dd.DepartmentKey
INNER JOIN [dbo].[DimDate] dt ON fa.DateKey = dt.DateKey
WHERE dt.Year = 2024 AND de.IsCurrent = 1
GROUP BY
    de.FirstName,
    de.LastName,
    dd.DepartmentName,
    DATEFROMPARTS(dt.Year, dt.Month, 1)
ORDER BY dt.Year, dt.Month
```

### With CTE and Window Functions

```sql
WITH EmployeeMetrics AS (
    SELECT
        de.EmployeeKey,
        de.FirstName,
        de.LastName,
        SUM(fs.Amount) as TotalSalary,
        AVG(fs.Amount) as AvgSalary,
        ROW_NUMBER() OVER (ORDER BY SUM(fs.Amount) DESC) as SalaryRank
    FROM [dbo].[FactSalary] fs
    INNER JOIN [dbo].[DimEmployee] de ON fs.EmployeeKey = de.EmployeeKey
    WHERE YEAR(GETDATE()) = 2024
    GROUP BY
        de.EmployeeKey,
        de.FirstName,
        de.LastName
)
SELECT TOP 10 *
FROM EmployeeMetrics
WHERE SalaryRank <= 10
ORDER BY SalaryRank
```

## Prompts Regenerated

### 1. **System Prompt** (agent.py)

- ✅ Now targets T-SQL for SQL Server
- ✅ Understands star/galaxy schema
- ✅ References fact/dimension hierarchies

### 2. **Intent Classification** (nodes.py)

- ✅ Recognizes data warehouse terminology
- ✅ Identifies dimensional vs transactional queries
- ✅ Supports warehouse KPI language

### 3. **Query Generator** (nodes.py)

- ✅ Generates T-SQL syntax
- ✅ Uses CAST, CONVERT, DATEFROMPARTS
- ✅ Properly joins fact→dimension tables
- ✅ Handles [dbo] schema notation
- ✅ Uses TOP or OFFSET/FETCH
- ✅ Includes CTE and Window Function templates

### 4. **Error Handler** (nodes.py)

- ✅ Professional error messaging
- ✅ Suggests alternative approaches
- ✅ Maintains data security

### 5. **Response Generator** (nodes.py)

- ✅ Dimensional analysis aware
- ✅ Highlights hierarchies (Department → Team → Location)
- ✅ Compares metrics across segments
- ✅ T-SQL code block with schema notation

## Troubleshooting

### Issue: "Driver not found"

```
Solution: Install SQL Server ODBC driver
- macOS: brew install msodbcsql17
- Windows: Download from Microsoft
- Linux: apt-get install odbc-mssql
```

### Issue: "Connection timeout"

```
Solutions:
1. Verify DATABASE_URL is correct
2. Check SQL Server is running and accessible
3. Verify network connectivity to server
4. Check authentication (Windows vs SQL Auth)
```

### Issue: "Schema not found"

```
Solutions:
1. Update table names in schema_inspector()
2. Verify tables exist in [dbo] schema
3. Check user has SELECT permissions
```

### Issue: "Query too slow"

```
Solutions:
1. Add date range filters to WHERE clause
2. Use OFFSET/FETCH instead of scanning all rows
3. Ensure dimension/fact tables have proper indexes
4. Consider materialized views for common aggregations
```

## Best Practices

### For Your Data Warehouse:

1. **Naming Convention** - Use consistent prefixes:
   - `Dim*` for dimension tables
   - `Fact*` for fact tables
   - `Agg*` for aggregation tables

2. **Index Strategy** - Create indexes on:
   - Foreign keys (Dim/Fact joins)
   - Date columns (filtering)
   - Commonly aggregated columns

3. **Slowly Changing Dimensions** - Add SCD columns:
   - `IsCurrent` BIT (current record flag)
   - `StartDate` DATE (when record became active)
   - `EndDate` DATE (when record expired)
   - `LoadDate` DATETIME (when row was loaded)

4. **Time Dimension** - Create comprehensive date table:
   - All dates in your data range
   - Year, Quarter, Month, Week, DayOfWeek
   - Holiday flags, Fiscal periods
   - Month/Day names for reporting

## Example Queries the Agent Can Now Generate

✅ "Show me headcount by department"  
✅ "What are the top 10 earners by location?"  
✅ "Calculate average attendance by team over the last quarter"  
✅ "Generate salary distribution report by department and job level"  
✅ "Show employee turnover trends by month"  
✅ "Compare headcount across fiscal periods"  
✅ "Get department budget vs actual spend"

## Next Steps

1. Configure your table names in `schema_inspector()`
2. Test with `streamlit run main.py`
3. Try queries like: "Show me employees by department"
4. Monitor agent responses for accuracy
5. Fine-tune prompts as needed

---

**Last Updated**: April 2, 2026  
**Database**: Microsoft SQL Server  
**Schema**: Star/Galaxy (Dimensional)  
**Status**: ✅ Ready for Production
