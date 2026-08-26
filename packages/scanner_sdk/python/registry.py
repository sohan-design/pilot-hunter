"""Central registry of active scanner plugins."""

from __future__ import annotations

from typing import List

from packages.scanner_sdk.python.base import BaseScanner


def get_registered_scanners() -> List[BaseScanner]:
    """Return all scanner plugins available to the pipeline (priority order)."""
    from packages.scanner_sdk.python.ats_seeds import apply_ats_seed_environment
    from scanners.ashby.scanner import AshbyScanner
    from scanners.company_pages.scanner import CompanyPagesScanner
    from scanners.greenhouse.scanner import GreenhouseScanner
    from scanners.hackernews.scanner import HackerNewsScanner
    from scanners.lever.scanner import LeverScanner
    from scanners.linkedin.scanner import LinkedInScanner
    from scanners.remoteok.scanner import RemoteOkScanner
    from scanners.remotive.scanner import RemotiveScanner
    from scanners.smartrecruiters.scanner import SmartRecruitersScanner
    from scanners.teamtailor.scanner import TeamtailorScanner
    from scanners.wellfound.scanner import WellfoundScanner
    from scanners.weworkremotely.scanner import WeWorkRemotelyScanner
    from scanners.workable.scanner import WorkableScanner
    from scanners.workday.scanner import WorkdayScanner

    apply_ats_seed_environment()

    # Priority: LinkedIn + Wellfound first, then design-friendly public boards, then ATS.
    return [
        LinkedInScanner(),
        WellfoundScanner(),
        WeWorkRemotelyScanner(),
        RemotiveScanner(),
        RemoteOkScanner(),
        AshbyScanner(),
        LeverScanner(),
        GreenhouseScanner(),
        WorkableScanner(),
        SmartRecruitersScanner(),
        TeamtailorScanner(),
        WorkdayScanner(),
        HackerNewsScanner(),
        CompanyPagesScanner(),
    ]
