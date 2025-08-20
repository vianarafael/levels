#!/bin/bash
# Daily RPG workflow for Levels app

set -e
cd "$(dirname "$0")"
source venv/bin/activate

# Set environment variables
export LEVELS_INBOX="./inbox"
export LEVELS_MEDIA="./media"

echo "⏱️ Levels Time Tracker"
echo "====================="

case "${1:-help}" in
  # Session tracking
  "study")
    if [ -z "$2" ]; then
      echo "Usage: ./daily.sh study <minutes> [notes]"
      echo "Example: ./daily.sh study 45 'Learning about databases'"
      exit 1
    fi
    python3 scripts/add_session.py "$2" study "" "${3:-}"
    ;;
    
  "build")
    if [ -z "$2" ]; then
      echo "Usage: ./daily.sh build <minutes> [notes]"
      echo "Example: ./daily.sh build 60 'Building Todo API'"
      exit 1
    fi
    python3 scripts/add_session.py "$2" build "" "${3:-}"
    ;;
    
  # Quick notes
  "note")
    if [ -z "$2" ]; then
      echo "Usage: ./daily.sh note 'Your note here'"
      exit 1
    fi
    mkdir -p inbox/build/notes
    echo "# Daily Note - $(date +%Y-%m-%d)

$2

---
*Added: $(date)*" >> "inbox/build/notes/$(date +%Y-%m-%d)-notes.md"
    echo "✅ Note added to inbox/build/notes/$(date +%Y-%m-%d)-notes.md"
    ;;
    
  # Book progress
  "book")
    if [ -z "$2" ]; then
      echo "Usage: ./daily.sh book 'Book progress update'"
      exit 1
    fi
    mkdir -p inbox/study/notes
    echo "# Book Progress - $(date +%Y-%m-%d)

$2

---
*Added: $(date)*" >> "inbox/study/notes/$(date +%Y-%m-%d)-books.md"
    echo "✅ Book progress logged to inbox/study/notes/$(date +%Y-%m-%d)-books.md"
    ;;
    
  # Process files and check progress
  "sync")
    echo "🔄 Processing inbox files..."
    python3 -m app.ingest
    echo "✅ Files processed! Check dashboard at http://localhost:8000"
    ;;
    
  # Show current status
  "status")
    echo "📊 Time Tracking Summary:"
    python3 -c "
import sys; sys.path.append('.')
from app.db import conn

with conn() as c:
    # Total time
    study_total = c.execute('SELECT COALESCE(SUM(minutes), 0) as total FROM session_log WHERE kind=\"study\"').fetchone()['total']
    build_total = c.execute('SELECT COALESCE(SUM(minutes), 0) as total FROM session_log WHERE kind=\"build\"').fetchone()['total']
    
    print(f'Study time: {study_total/60:.1f} hours')
    print(f'Build time: {build_total/60:.1f} hours')
    print(f'Total time: {(study_total + build_total)/60:.1f} hours')
    print()
    
    # Simple time breakdown only
    print('Pure time tracking - no categories needed')
    
    print()
    
    # Artifact counts
    artifacts = c.execute('SELECT kind, COUNT(*) n FROM artifact GROUP BY kind ORDER BY kind').fetchall()
    print('Artifacts created:')
    for art in artifacts:
        print(f'  {art[\"kind\"]}: {art[\"n\"]}')
"
    ;;
    
  # Help
  *)
    echo "Daily Time Tracking Commands:"
    echo ""
    echo "📚 STUDY:"
    echo "  ./daily.sh study 45 'Database fundamentals'"
    echo "  ./daily.sh study 30 'Statistics practice'"
    echo ""
    echo "🔨 BUILD:"
    echo "  ./daily.sh build 90 'Todo API endpoints'"
    echo "  ./daily.sh build 60 'Data scraper'"
    echo ""
    echo "📝 QUICK ACTIONS:"
    echo "  ./daily.sh note 'Fixed authentication bug'"
    echo "  ./daily.sh book 'Finished FastAPI chapter 4'"
    echo "  ./daily.sh sync     # Process all files → count artifacts"
    echo "  ./daily.sh status   # Show time tracking summary"
    echo ""
    echo "⏱️ Pure time tracking - study vs build, nothing more"
    ;;
esac
