#!/bin/bash
# Clean up bloated files for MVP

echo "🧹 Cleaning up bloated files..."

# Remove old backend files (keep only mvp_main.py and requirements-mvp.txt)
echo "Removing old backend files..."
cd backend
rm -f main.py main_*.py simple_*.py deploy_*.py test_*.py
rm -f conftest.py fix_imports.py performance_config.py server_test.py startup_check.py
rm -rf agents/ crews/ tools/ middleware/ database/ services/ api/
cd ..

# Remove old test/seed files from root
echo "Removing old test/seed files..."
rm -f test_*.py seed_*.py fix_*.py create_*.sql
rm -f mcp_server.py setup_supabase.py
rm -f health_report.json system_test_results.json
rm -f *.log team_mapping.txt

# Remove old documentation (keep only MVP readme)
echo "Removing old documentation..."
rm -f AGENT_INTEGRATION_PLAN.md CLAUDE_DESKTOP_MCP_SETUP.md DATABASE_SETUP.md
rm -f DEPLOYMENT_GUIDE.md FRONTEND_ENHANCEMENTS.md FRONTEND_OPTIMIZATION_REPORT.md
rm -f IMPLEMENTATION_COMPLETE.md LAUNCH_CHECKLIST.md PUBLICATION_CHECKLIST.md
rm -f RUN_SYSTEM.md SECURITY.md SETUP_GUIDE.md
rm -f claude.md baseball-trade-rules.txt baseball-trade-env-example.sh

# Remove old requirements files (keep only mvp version)
echo "Removing old requirements files..."
rm -f requirements.txt requirements-*.txt
# Keep requirements-mvp.txt in backend/

# Remove Docker files (not needed for Railway/Vercel)
echo "Removing Docker files..."
rm -f Dockerfile* docker-compose.yml

# Remove supabase (not in MVP)
echo "Removing supabase files..."
rm -rf supabase/
rm -f supabase_schema.sql

# Keep .env but remove example
rm -f .env.example

echo "✅ Cleanup complete!"
echo ""
echo "📁 Remaining MVP files:"
echo "  backend/mvp_main.py"
echo "  backend/requirements-mvp.txt"
echo "  frontend/src/app/page.tsx"
echo "  README-MVP.md"
echo "  Procfile"
echo "  railway.json"
echo "  vercel.json"
echo ""
echo "🚀 Ready to deploy!"
