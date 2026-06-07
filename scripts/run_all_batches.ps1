# Sequential batch extraction for all queued sources.
# Uses --skip-existing so restarts are safe.
# Run from project root: .\scripts\run_all_batches.ps1

$ErrorActionPreference = "Continue"
$start = Get-Date

function Run-Batch($source, $mode = "motif") {
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] Starting: $source (mode=$mode)"
    if ($mode -eq "equipment") {
        python scripts/batch_extract.py --source $source --mode equipment --skip-existing --output assets/extracted/
    } else {
        python scripts/batch_extract.py --source $source --skip-existing --output assets/extracted/
    }
    $ts2 = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts2] Done: $source"
}

# Shorter batches first so partial progress is usable sooner
Run-Batch "mclean_second"
Run-Batch "maier_arcana"
Run-Batch "khunrath"
Run-Batch "paul_marshall"
Run-Batch "obrist_medieval"

# Equipment pass over Claudiens (athanor, vessel, alembic, etc.)
Run-Batch "claudiens" "equipment"

# New sources (Stolcius and Mylius — download first with fetch_stolcius_mylius.py)
Run-Batch "stolcius"
Run-Batch "mylius_philosophia"

# Rebuild catalogs
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Rebuilding catalogs..."
python scripts/build_catalog.py
python scripts/build_emblem_catalog.py

$elapsed = (Get-Date) - $start
Write-Host "All batches complete. Total time: $($elapsed.ToString('hh\:mm\:ss'))"
