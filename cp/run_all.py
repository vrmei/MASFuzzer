"""
Oracle Cross-Validation Pipeline - Master Runner
Executes all 3 phases sequentially:
  Phase 1: Config B (Worker-Only) re-evaluation with GPT-4o-mini
  Phase 2: Config A (Full-MAS) slice re-evaluation with GPT-4o-mini
  Phase 3: Cohen's Kappa + robustness_report.md generation

Usage:
  python cross_validation/run_all.py          # Run all phases
  python cross_validation/run_all.py --phase 1   # Run only Phase 1
  python cross_validation/run_all.py --phase 2   # Run only Phase 2
  python cross_validation/run_all.py --phase 3   # Run only Phase 3
"""
import sys
import os
import argparse

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="Oracle Cross-Validation Pipeline")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3], default=None,
                        help="Run specific phase only (1, 2, or 3)")
    args = parser.parse_args()

    if args.phase is None or args.phase == 1:
        print("\n" + "#" * 60)
        print("# PHASE 1: Config B Worker-Only Cross-Validation")
        print("#" * 60)
        from cross_validation.run_phase1_configB import run_phase1
        run_phase1()

    if args.phase is None or args.phase == 2:
        print("\n" + "#" * 60)
        print("# PHASE 2: Config A Full-MAS Slice Cross-Validation")
        print("#" * 60)
        from cross_validation.run_phase2_configA import run_phase2
        run_phase2()

    if args.phase is None or args.phase == 3:
        print("\n" + "#" * 60)
        print("# PHASE 3: Cohen's Kappa & Robustness Report")
        print("#" * 60)
        from cross_validation.run_phase3_kappa_report import run_phase3
        run_phase3()

    print("\n" + "=" * 60)
    print("✅ Pipeline Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
