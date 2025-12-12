#!/usr/bin/env python3
"""Coverage Audit Script - Audit project coverage for retry & error intelligence.

Usage:
    python scripts/coverage_audit.py [--format json|text]
    python scripts/coverage_audit.py --retry-only
    python scripts/coverage_audit.py --ei-only

Examples:
    # Full audit report
    python scripts/coverage_audit.py
    
    # Export to JSON
    python scripts/coverage_audit.py --format json
    
    # Only retry coverage
    python scripts/coverage_audit.py --retry-only
    
    # Only error intelligence coverage
    python scripts/coverage_audit.py --ei-only
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import get_logger
from agents.project_manager.workers import CoverageAuditTool, StructureScanner


def main():
    parser = argparse.ArgumentParser(
        description="Audit retry error recovery and error intelligence coverage"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--retry-only",
        action="store_true",
        help="Only audit retry error recovery coverage"
    )
    parser.add_argument(
        "--ei-only",
        action="store_true",
        help="Only audit error intelligence coverage"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (for JSON format)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed method-level information"
    )
    
    args = parser.parse_args()
    
    # Initialize
    logger = get_logger("CoverageAudit")
    logger.info("Starting coverage audit...")
    
    # Scan project structure
    scanner = StructureScanner(logger)
    structure = scanner.discover_structure()
    logger.info(f"Found {len(structure.get('agents', {}))} agents")
    
    # Run audits
    audit_tool = CoverageAuditTool(logger)
    
    if args.retry_only:
        # Retry only
        retry_audit = audit_tool.audit_retry_coverage(structure)
        
        if args.format == "json":
            output = json.dumps(retry_audit, indent=2)
            if args.output:
                Path(args.output).write_text(output)
                logger.info(f"Audit results saved to {args.output}")
            else:
                print(output)
        else:
            print("\n" + retry_audit["summary"])
            if args.verbose:
                print("\nDETAILED BREAKDOWN:")
                print("="*70)
                for agent_name, info in retry_audit["agents_detail"].items():
                    print(f"\n{agent_name}:")
                    print(f"  Covered: {info.get('covered')}")
                    print(f"  Coverage: {info.get('percentage', 0):.1f}%")
                    if info.get('workers_retry'):
                        print(f"  Workers:")
                        for worker, w_info in info['workers_retry'].items():
                            print(f"    {worker}: {w_info['retry_count']}/{w_info['total_methods']} methods")
    
    elif args.ei_only:
        # EI only
        ei_audit = audit_tool.audit_error_intelligence_coverage(structure)
        
        if args.format == "json":
            output = json.dumps(ei_audit, indent=2)
            if args.output:
                Path(args.output).write_text(output)
                logger.info(f"Audit results saved to {args.output}")
            else:
                print(output)
        else:
            print("\n" + ei_audit["summary"])
            if args.verbose and ei_audit["missing_integrations"]:
                print("\nMISSING INTEGRATIONS:")
                print("="*70)
                for agent, workers in ei_audit["missing_integrations"].items():
                    print(f"\n{agent}:")
                    for worker in workers:
                        print(f"  - {worker}")
    
    else:
        # Combined audit
        combined = audit_tool.audit_combined(structure)
        
        if args.format == "json":
            # Remove remediation_plan for JSON
            json_output = {
                "retry_audit": combined["retry_audit"],
                "ei_audit": combined["ei_audit"],
                "combined_coverage": combined["combined_coverage"],
                "critical_gaps": combined["critical_gaps"]
            }
            output = json.dumps(json_output, indent=2)
            if args.output:
                Path(args.output).write_text(output)
                logger.info(f"Audit results saved to {args.output}")
            else:
                print(output)
        else:
            audit_tool.print_audit_report(combined)
            
            if args.verbose:
                print("\nDETAILED BREAKDOWN:")
                print("="*70)
                
                print("\nRETRY ERROR RECOVERY:")
                for agent_name, info in combined["retry_audit"]["agents_detail"].items():
                    status = "✅" if info.get('covered') else "❌"
                    print(f"  {status} {agent_name}")
                    if info.get('workers_retry'):
                        for worker, w_info in info['workers_retry'].items():
                            pct = w_info.get('percentage', 0)
                            print(f"      {worker}: {pct:.0f}%")
                
                print("\nERROR INTELLIGENCE:")
                for agent_name, info in combined["ei_audit"]["agents_detail"].items():
                    status = "✅" if info.get('covered') else "❌"
                    print(f"  {status} {agent_name}")
                    if info.get('workers_with_ei'):
                        print(f"      With EI: {', '.join(info['workers_with_ei'])}")
                    if info.get('workers_without_ei'):
                        print(f"      Missing EI: {', '.join(info['workers_without_ei'])}")
    
    logger.info("Coverage audit complete")


if __name__ == "__main__":
    main()
