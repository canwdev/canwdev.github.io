适用于迁移游戏库或更换盘符的情况。修改为相对路径后再次迁移游戏库也会方便很多。

使用 powershell 批量修改 Playnite LiteDB 数据库 Game 表的 InstallDirectory 字段，查找旧路径并替换为新的相对路径。无需复杂的开发环境或数据库编辑软件。

需要注意的是：
- `$LiteDbDllPath`：LiteDB 动态链接库位置，必须指定
- `$DbFilePath`：数据库位置，必须指定
- `$SearchText`：查找内容，旧的路径
- `$ReplaceText`：替换内容，`{PlayniteDir}` 是 Playnite 软件目录变量，如果设置为 `{PlayniteDir}\..\` 表示使用 Playnite 软件目录的上一级目录

将以下脚本保存为 `update-lite-db.ps1`
```powershell
# ---------------------------------------------
# USER CONFIGURATION (用户配置)
# ---------------------------------------------
$LiteDbDllPath = "E:\Games\Playnite\LiteDB.dll"
$DbFilePath = "E:\Games\Playnite\library\games.db"

# 查找内容，旧的路径
$SearchText = "F:\Games\"
# 替换内容，{PlayniteDir} 是 Playnite 软件目录变量
$ReplaceText = "{PlayniteDir}\..\"

$CollectionName = "Game"
$FieldName = "InstallDirectory"

# ---------------------------------------------
# 1. Load LiteDB DLL (加载 LiteDB DLL)
# ---------------------------------------------
try {
    Add-Type -Path $LiteDbDllPath
    Write-Host "LiteDB DLL loaded successfully."
} catch {
    Write-Error "Failed to load LiteDB DLL. Please check the path: $LiteDbDllPath"
    exit
}

# ---------------------------------------------
# 2. Define Variables and Types (定义变量和类型)
# ---------------------------------------------
$LiteDatabaseType = [LiteDB.LiteDatabase]
$QueryType = [LiteDB.Query]
$db = $null # Initialize $db outside try block

# ---------------------------------------------
# 3. Execute Database Update (执行数据库更新操作)
# ---------------------------------------------
try {
    # Establish database connection
    $db = New-Object $LiteDatabaseType -ArgumentList $DbFilePath
    $collection = $db.GetCollection($CollectionName)

    # Construct the query condition: Find documents where InstallDirectory starts with the search path
    # Using StartsWith is efficient as it uses the LiteDB index
    $queryCondition = $QueryType::StartsWith($FieldName, $SearchText)
    
    # Get the count of documents to be updated
    $count = $collection.Count($queryCondition)
    
    if ($count -eq 0) {
        Write-Host "No records found matching the search text ('$SearchText')."
    } else {
        Write-Host "Found $count records to update..."

        $updatedCount = 0
        
        # Find all documents matching the criteria and iterate
        $collection.Find($queryCondition) | ForEach-Object {
            $doc = $_
            
            # Get current value (as a string)
            $currentValue = $doc[$FieldName].AsString

            # Perform string replacement
            # Note: The 'Replace' method works on the string value
            $newValue = $currentValue.Replace($SearchText, $ReplaceText)
            
            # Update the BsonDocument field value
            $doc[$FieldName] = $newValue
            
            # Commit the update back to the database
            if ($collection.Update($doc)) {
                $updatedCount++
            }
        }
        
        Write-Host "Batch replacement completed. Successfully updated $updatedCount records."
    }

} catch {
    Write-Error "Database operation failed:"
    Write-Error $_.Exception.Message
} finally {
    # Ensure the database connection is closed and resources are released
    if ($db -ne $null) {
        $db.Dispose()
        Write-Host "Database connection closed."
    }
}
```

1. 退出 Playnite 防止数据库文件锁定
2. 保存脚本为 `update-lite-db.ps1`，然后用终端定位到脚本文件目录，运行 `powershell .\update-lite-db.ps1`
3. 当看到以下输出说明修改成功，如果无法执行 ps1 脚本，请参考 [[Windows 脚本 + 常用命令#无法加载文件 xxx.ps1，因为在此系统上禁止运行脚本]]

```
LiteDB DLL loaded successfully.
Found 29 records to update...
Batch replacement completed. Successfully updated 29 records.
Database connection closed.
```