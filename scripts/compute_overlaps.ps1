$csv = 'c:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-\scripts\csvsegmatch_.csv'
$outdir = 'c:\Users\irato\OneDrive\Documents\genealogy.2\genealogy-\Research Data'
New-Item -ItemType Directory -Path $outdir -Force | Out-Null
$inputs = @(
 @{Kit='QE3391961'; Chr='4'; Start=144586417; End=174173743; cM=29.3; SNPs=3836; Name='Brian Tucker'},
 @{Kit='WB1786370'; Chr='4'; Start=146220802; End=174130503; cM=28.4; SNPs=4183; Name='Shannon Fields'},
 @{Kit='M299649'; Chr='4'; Start=155182784; End=174447389; cM=19.6; SNPs=1603; Name='Jay William Cannon'},
 @{Kit='M162434'; Chr='4'; Start=158737934; End=174824576; cM=16.2; SNPs=2089; Name='William Kinsey'},
 @{Kit='A015583'; Chr='4'; Start=158782030; End=174190222; cM=15.6; SNPs=1880; Name='Riah Lee Kinsey'},
 @{Kit='A015583_2'; Chr='4'; Start=183121231; End=186031823; cM=9.9; SNPs=698; Name='Riah Lee Kinsey'},
 @{Kit='M162434_2'; Chr='4'; Start=183141735; End=186397351; cM=11.2; SNPs=790; Name='William Kinsey'},
 @{Kit='QE3391961_2'; Chr='4'; Start=184280695; End=188289740; cM=13.9; SNPs=1164; Name='Brian Tucker'},
 @{Kit='M499246'; Chr='8'; Start=29630942; End=66299820; cM=25.3; SNPs=2546; Name='James Whitehead'},
 @{Kit='T852796'; Chr='8'; Start=29630942; End=61815886; cM=22.7; SNPs=3146; Name='WEB'},
 @{Kit='M952876'; Chr='8'; Start=29860405; End=72603480; cM=32.5; SNPs=3152; Name='David Bass'},
 @{Kit='T210295'; Chr='8'; Start=29860405; End=72301132; cM=31.8; SNPs=4503; Name='Shawn Crawford'},
 @{Kit='TY9717559'; Chr='8'; Start=29860405; End=59692275; cM=20.0; SNPs=3394; Name='Amber Wilder Hurd'},
 @{Kit='A001971'; Chr='8'; Start=30864339; End=72355403; cM=30.7; SNPs=4370; Name='DJ'},
 @{Kit='A028206'; Chr='8'; Start=42086472; End=70607929; cM=20.3; SNPs=2676; Name='SN'},
 @{Kit='A370591'; Chr='8'; Start=53433015; End=72280705; cM=18.7; SNPs=2531; Name='Philip Ashley Hutson'}
)

$rows = Import-Csv -Path $csv
$out = @()
foreach($i in $inputs){
    foreach($r in $rows){
        if([string]$r.chr -eq $i.Chr){
            $rStart = [int]($r.Start -replace '\s','')
            $rEnd = [int]($r.End -replace '\s','')
            $overlapStart = [math]::Max($rStart, $i.Start)
            $overlapEnd = [math]::Min($rEnd, $i.End)
            if($overlapStart -le $overlapEnd){
                $rLen = $rEnd - $rStart + 1
                $overlapLen = $overlapEnd - $overlapStart + 1
                $rC = [double]($r.'Segment cM' -replace '\s','')
                if($rLen -gt 0){ $overlap_cM_est = [math]::Round($rC * ($overlapLen / $rLen),2) } else { $overlap_cM_est = 0 }
                $out += New-Object psobject -Property @{input_kit=$i.Kit; input_name=$i.Name; Chr=$i.Chr; input_start=$i.Start; input_end=$i.End; input_cM=$i.cM; matched_kit=$r.MatchedKit; matched_name=$r.MatchedName; matched_start=$rStart; matched_end=$rEnd; matched_cM=$rC; overlap_start=$overlapStart; overlap_end=$overlapEnd; overlap_len=$overlapLen; overlap_cM_est=$overlap_cM_est}
            }
        }
    }
}
$outpath = Join-Path $outdir 'overlaps_from_user_segments.csv'
$out | Export-Csv -Path $outpath -NoTypeInformation -Encoding UTF8
Write-Output "WROTE $outpath with $($out.Count) rows"
