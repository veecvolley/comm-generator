# ## GET FULL PLANNING
# curl -X POST 'https://www.ffvbbeach.org/ffvbapp/resu/vbspo_calendrier_export_club.php' \
#      -H 'Content-Type: application/x-www-form-urlencoded' \
#      -d 'cnclub=0775819&cal_saison=2024/2025&typ_edition=E&type=RES&poule=1MB' \
#      > export20242025.csv
# iconv -f latin1 -t utf-8 export20242025.csv > export20242025_utf8.csv

## GET FULL PLANNING
# curl -X POST 'https://www.ffvbbeach.org/ffvbapp/resu/vbspo_calendrier_export_club.php' \
#      -H 'Content-Type: application/x-www-form-urlencoded' \
#      -d 'cnclub=0775819&cal_saison=2025/2026&typ_edition=E&type=RES&poule=1MB' \
#      > export20252026.csv
# iconv -f latin1 -t utf-8 export20252026.csv > export20252026_utf8.csv

# ## GET CALENDAR
# ## Ex: https://www.ffvbbeach.org/ffvbapp/resu/vbspo_calendrier.php?saison=2025%2F2026&codent=LIIDF&poule=2FC&calend=COMPLET&equipe=4&x=10&y=8
# curl -X POST 'https://www.ffvbbeach.org/ffvbapp/resu/vbspo_calendrier_export.php' \
#      -H 'Content-Type: application/x-www-form-urlencoded' \
#      -d 'cal_saison=2025/2026&cal_codent=LIIDF&cal_codpoule=2FC&typ_edition=E&type=RES&rech_equipe=4&cal_coddiv&cal_codtour' \
#      > calend20252026.csv
# iconv -f latin1 -t utf-8 calend20252026.csv > calend20252026_utf8.csv

# ## GET MATCH PDF
# curl -X POST 'https://www.ffvbbeach.org/ffvbapp/adressier/fiche_match_ffvb.php' \
#      -H 'Content-Type: application/x-www-form-urlencoded' \
#      -d 'codmatch=2FCA007&codent=LIIDF' \
#      > gymnase.pdf

# curl -v 'https://www.ffvbbeach.org/ffvbapp/resu/planning_club_class.php?cnclub=0775819&saison=2024%2F2025' \
#      | pup 'table tr json{}' \
#      | jq -r '.. | objects | select(.class? == "titrepoule") | .text| gsub("&#39;"; "\u0027")'

curl -X POST "https://www.ffvbbeach.org/ffvbapp/resu/vbspo_calendrier_export.php" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "cal_saison=2025/2026" \
  -d "cal_codent=LIIDF" \
  -d "cal_coddiv=QCM" \
  -d "typ_edition=E" \
  -d "type=RES" \
  -d "rech_equipe="