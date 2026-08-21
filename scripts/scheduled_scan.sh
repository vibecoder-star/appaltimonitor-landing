#!/bin/bash
# AppaltiMonitor — Scheduled Tasks
# Add to crontab with: crontab -e
# Or run manually: bash /opt/autonomous-venture-engine/appalti-monitor/scripts/scheduled_scan.sh

# Daily TED scan and report generation
# 0 8 * * * cd /opt/autonomous-venture-engine/appalti-monitor && python3 -c "from commercial_pipeline import CommercialPipeline; p = CommercialPipeline(); p.run_scheduled_scan()" >> /opt/autonomous-venture-engine/appalti-monitor/data/logs/scheduled_scan.log 2>&1

# Trial expiration check
# 0 9 * * * cd /opt/autonomous-venture-engine/appalti-monitor && python3 -c "from commercial_pipeline import CommercialPipeline; p = CommercialPipeline(); p.run_scheduled_scan()" >> /opt/autonomous-venture-engine/appalti-monitor/data/logs/trial_check.log 2>&1

# Weekly summary report (Monday 9 AM)
# 0 9 * * 1 cd /opt/autonomous-venture-engine/appalti-monitor && python3 -c "from commercial_pipeline import CommercialPipeline; p = CommercialPipeline(); print('Weekly summary:', p.run_scheduled_scan())" >> /opt/autonomous-venture-engine/appalti-monitor/data/logs/weekly_summary.log 2>&1

# To install: crontab -e
# Paste the above lines (uncommented)
# To verify: crontab -l

echo "AppaltiMonitor Scheduled Tasks"
echo "=============================="
echo ""
echo "Add these lines to crontab (crontab -e):"
echo ""
echo "# Daily TED scan"
echo "0 8 * * * cd /opt/autonomous-venture-engine/appalti-monitor && python3 -c \"from commercial_pipeline import CommercialPipeline; p = CommercialPipeline(); p.run_scheduled_scan()\" >> /opt/autonomous-venture-engine/appalti-monitor/data/logs/scheduled_scan.log 2>&1"
echo ""
echo "# Trial expiration check"
echo "0 9 * * * cd /opt/autonomous-venture-engine/appalti-monitor && python3 -c \"from commercial_pipeline import CommercialPipeline; p = CommercialPipeline(); p.run_scheduled_scan()\" >> /opt/autonomous-venture-engine/appalti-monitor/data/logs/trial_check.log 2>&1"
