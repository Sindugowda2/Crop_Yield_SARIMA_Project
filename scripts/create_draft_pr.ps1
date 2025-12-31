# PowerShell helper: create branch, commit, push, and optionally run workflow/create draft PR
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\create_draft_pr.ps1 [-CreatePR]
param(
    [switch]$CreatePR
)

function Abort([string]$msg){ Write-Error $msg; exit 1 }

# Check git
try {
    git --version | Out-Null
} catch {
    Abort "Git not found. Install Git and re-run this script. https://git-scm.com/downloads"
}

# Check repo root
$root = Resolve-Path -Path .
Write-Host "Working directory: $root"

# Create branch
$branch = "feat/auto-manual-map-pr"
Write-Host "Creating branch: $branch"
git checkout -b $branch

# Stage files
$toAdd = @(
    '.github/workflows/auto_manual_map_pr.yml',
    'src/manual_map_updater.py',
    'src/suitability_report.py',
    'data/processed/manual_state_to_subdivision.csv',
    'data/processed/suitability_action_plan.csv',
    'PR_BODY.md'
)

foreach($f in $toAdd){
    if(Test-Path $f){ git add $f } else { Write-Host "(not present, skipping) $f" }
}

# Commit
$commitMsg = "chore(ci): add automated manual mapping PR workflow, updater, and action plan"
git commit -m $commitMsg || Write-Host "Nothing to commit (no changes staged)"

# Push
git push -u origin $branch

# Ask to run workflow or create PR via gh
# If --CreatePR passed, try to use gh to create a draft PR directly
if($CreatePR){
    if((Get-Command gh -ErrorAction SilentlyContinue) -ne $null){
        Write-Host "Creating draft PR via gh..."
        gh pr create --title "chore: auto-update manual mapping & suitability action plan — Automated mapping & action plan" --body-file PR_BODY.md --base main --head $branch --draft
    } else {
        Write-Host "gh CLI not found. To create a draft PR manually, either install gh or trigger the workflow from GitHub Actions UI."
    }
} else {
    Write-Host "To create a draft PR automatically, go to GitHub → Actions → 'Auto Manual Mapping PR' → Run workflow, choose branch: $branch and Run."
    Write-Host "Or run this script with -CreatePR to attempt creating a draft PR via gh CLI if installed."
}

Write-Host "Done. Review changes and the PR on GitHub when it appears."