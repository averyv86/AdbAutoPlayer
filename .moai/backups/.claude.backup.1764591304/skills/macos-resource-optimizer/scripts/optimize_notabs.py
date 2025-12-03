#!/usr/bin/env python3
"""Quick optimization without tab suspension."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from optimize import MemoryOptimizer
import asyncio

async def main():
    # Create optimizer with medium risk tolerance
    optimizer = MemoryOptimizer(
        dry_run=False,
        auto_approve=True,
        risk_tolerance="medium"
    )
    
    # Analyze system
    analysis = optimizer.analyze_system()
    optimizer.print_analysis_toon(analysis)
    
    # Filter out tab suspension optimization
    filtered_optimizations = [
        opt for opt in optimizer.optimizations
        if opt.name != "browser_tab_suspension"
    ]
    optimizer.optimizations = filtered_optimizations
    
    # Execute remaining optimizations
    await optimizer.execute_all()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
