#!/bin/bash
# Quick script to generate Ivy shared segments report
# Usage: ./report_ivy_segments.sh

echo "==================================="
echo "Ivy Lee DNA Segment Report Generator"
echo "==================================="
echo ""

cd "$(dirname "$0")"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

echo "Generating comprehensive DNA segment report for Ivy Lee..."
echo ""

python3 scripts/generate_ivy_segment_report.py

if [ $? -eq 0 ]; then
    echo ""
    echo "==================================="
    echo "✓ Report generated successfully!"
    echo "==================================="
    echo ""
    echo "📄 View the report at:"
    echo "   outputs/ivy_shared_segments_report.md"
    echo ""
    echo "The report includes:"
    echo "  • Summary statistics (Direct cM, TRI, ICW)"
    echo "  • Triangulated segments (TRI)"
    echo "  • In Common With matches (ICW)"
    echo "  • Chromosome breakdowns"
    echo ""
else
    echo ""
    echo "❌ Error generating report. Check the output above for details."
    exit 1
fi
