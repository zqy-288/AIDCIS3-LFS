Write-Host "========================================" -ForegroundColor Green
Write-Host "    Setup GitHub Repository and Push" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`nChecking current Git status..." -ForegroundColor Yellow
git status --short

Write-Host "`nChecking remote repository..." -ForegroundColor Yellow
$remotes = git remote -v
if ($remotes) {
    Write-Host "Remote repository found:" -ForegroundColor Green
    $remotes
} else {
    Write-Host "No remote repository configured." -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "    GitHub Repository Setup Guide" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nTo push your project to GitHub, you need to:" -ForegroundColor White
Write-Host "`n1. CREATE GITHUB REPOSITORY:" -ForegroundColor Yellow
Write-Host "   - Go to https://github.com" -ForegroundColor White
Write-Host "   - Click 'New repository' or '+'" -ForegroundColor White
Write-Host "   - Repository name: AIDCIS2-AIDCIS3" -ForegroundColor White
Write-Host "   - Description: 管孔检测系统上位机软件" -ForegroundColor White
Write-Host "   - Set to Public or Private (your choice)" -ForegroundColor White
Write-Host "   - DO NOT initialize with README (we already have one)" -ForegroundColor Red
Write-Host "   - Click 'Create repository'" -ForegroundColor White

Write-Host "`n2. COPY THE REPOSITORY URL:" -ForegroundColor Yellow
Write-Host "   - After creating, GitHub will show you the repository URL" -ForegroundColor White
Write-Host "   - It looks like: https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git" -ForegroundColor White
Write-Host "   - Copy this URL" -ForegroundColor White

Write-Host "`n3. CONFIGURE REMOTE AND PUSH:" -ForegroundColor Yellow
$repo_url = Read-Host "Enter your GitHub repository URL (or press Enter to skip)"

if ([string]::IsNullOrEmpty($repo_url)) {
    Write-Host "`nSkipped. You can set up the remote later with:" -ForegroundColor Yellow
    Write-Host "git remote add origin https://github.com/YOUR-USERNAME/AIDCIS2-AIDCIS3.git" -ForegroundColor Cyan
    Write-Host "git push -u origin main" -ForegroundColor Cyan
    Write-Host "`nPress any key to continue..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    return
}

Write-Host "`nSetting up remote repository..." -ForegroundColor Yellow
try {
    git remote add origin $repo_url
    Write-Host "Remote added successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to add remote. Trying to update existing remote..." -ForegroundColor Yellow
    git remote set-url origin $repo_url
}

Write-Host "`nAdding any remaining files..." -ForegroundColor Yellow
git add .

Write-Host "`nChecking if there are changes to commit..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "Committing remaining changes..." -ForegroundColor Yellow
    git commit -m "Final cleanup and prepare for GitHub upload"
} else {
    Write-Host "No changes to commit." -ForegroundColor Green
}

Write-Host "`nPushing to GitHub..." -ForegroundColor Yellow
Write-Host "This may take some time due to Git LFS files..." -ForegroundColor Gray

try {
    git push -u origin main
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "           SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    Write-Host "`n✅ Project successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host "`n🎉 Your repository is now available at:" -ForegroundColor Cyan
    Write-Host "   $repo_url" -ForegroundColor White
    
    Write-Host "`n👥 Team members can now:" -ForegroundColor Magenta
    Write-Host "   1. Install Git LFS: https://git-lfs.github.io/" -ForegroundColor White
    Write-Host "   2. Clone: git clone $repo_url" -ForegroundColor White
    Write-Host "   3. Pull LFS files: git lfs pull" -ForegroundColor White
    Write-Host "   4. Install dependencies: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "   5. Run: python src/main.py" -ForegroundColor White
    
    Write-Host "`n📋 Next steps:" -ForegroundColor Magenta
    Write-Host "   - Share the repository URL with your team" -ForegroundColor White
    Write-Host "   - Add collaborators in GitHub repository settings" -ForegroundColor White
    Write-Host "   - Monitor Git LFS usage in repository settings" -ForegroundColor White
    
} catch {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "           PUSH FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    
    Write-Host "`n❌ Failed to push to GitHub. Common issues:" -ForegroundColor Red
    
    Write-Host "`n1. AUTHENTICATION:" -ForegroundColor Yellow
    Write-Host "   - Make sure you're logged into Git" -ForegroundColor White
    Write-Host "   - You may need to set up a Personal Access Token" -ForegroundColor White
    Write-Host "   - Or use GitHub Desktop for easier authentication" -ForegroundColor White
    
    Write-Host "`n2. REPOSITORY ACCESS:" -ForegroundColor Yellow
    Write-Host "   - Make sure the repository exists on GitHub" -ForegroundColor White
    Write-Host "   - Check if you have push permissions" -ForegroundColor White
    Write-Host "   - Verify the repository URL is correct" -ForegroundColor White
    
    Write-Host "`n3. GIT LFS QUOTA:" -ForegroundColor Yellow
    Write-Host "   - GitHub free accounts have 1GB LFS storage limit" -ForegroundColor White
    Write-Host "   - Check your LFS usage in repository settings" -ForegroundColor White
    
    Write-Host "`n4. NETWORK:" -ForegroundColor Yellow
    Write-Host "   - Check your internet connection" -ForegroundColor White
    Write-Host "   - Try again in a few minutes" -ForegroundColor White
    
    Write-Host "`nYou can try pushing again with:" -ForegroundColor Cyan
    Write-Host "git push origin main" -ForegroundColor White
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "     Git LFS File Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nLFS managed files:" -ForegroundColor Yellow
git lfs ls-files

Write-Host "`nRepository size optimization:" -ForegroundColor Green
Write-Host "- Large files are stored in Git LFS" -ForegroundColor White
Write-Host "- Clone speed is optimized" -ForegroundColor White
Write-Host "- Team collaboration is efficient" -ForegroundColor White

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
