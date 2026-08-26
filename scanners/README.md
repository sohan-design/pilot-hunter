# Per-source job discovery plugins

Each scanner lives in its own folder and implements `discover_jobs()`, `normalize()`, and `health_check()` via `packages/scanner_sdk`.

| Folder             | Source                   | Config (comma-separated)                                 | Notes |
| ------------------ | ------------------------ | -------------------------------------------------------- | ----- |
| `linkedin/`        | LinkedIn guest job cards | `LINKEDIN_JOB_QUERIES`, `LINKEDIN_JOB_LOCATIONS`         | Priority; defaults to Product Designer / India / Remote |
| `wellfound/`       | Wellfound search Apollo  | `WELLFOUND_SEARCH_PATHS`                                 | Priority; design paths in `ats-seeds.json` |
| `weworkremotely/`  | We Work Remotely RSS     | None                                                     | Design category RSS first |
| `remotive/`        | Remotive public API      | None                                                     | Design category + product designer search |
| `remoteok/`        | RemoteOK JSON API        | None                                                     | Design titles only |
| `ashby/`           | Ashby posting API        | `ASHBY_JOB_BOARD_SLUGS`                                  | |
| `lever/`           | Lever postings API       | `LEVER_COMPANY_SITES`                                    | Includes Figma |
| `greenhouse/`      | Greenhouse Job Board API | `GREENHOUSE_BOARD_TOKENS`                                | Includes Canva |
| `workable/`        | Workable widget API      | `WORKABLE_ACCOUNT_SLUGS`                                 | |
| `smartrecruiters/` | SmartRecruiters API      | `SMARTRECRUITERS_COMPANIES`                              | |
| `teamtailor/`      | Teamtailor jobs.json     | `TEAMTAILOR_COMPANY_SLUGS`                               | |
| `workday/`         | Workday CXS jobs API     | `WORKDAY_CAREER_SITES`                                   | |
| `hackernews/`      | HN Who is Hiring         | None (Algolia public API)                                | |
| `company_pages/`   | Company career pages     | None (Google, Microsoft, EPAM, Globant, Datadog, Stripe) | |

**Naukri:** no public unauthenticated job API (requires proprietary App Id headers). India Product Designer coverage uses LinkedIn guest search + ATS boards instead.

Legacy: `GREENHOUSE_BOARD_TOKEN` (single board) is still supported.

Set `ATS_DISCOVERY_ENABLED=true` to merge reviewed identifiers from
`scanners/ats-seeds.json` with explicitly configured Greenhouse, Lever, Workable,
Ashby, and Wellfound values. Explicit environment values always take precedence and are never
removed.

Orchestration: `scraper/scanner_engine.py` via `get_registered_scanners()` (LinkedIn / Wellfound first).

Health checks: `npm run scanner:health`

## Example `.env`

```bash
GREENHOUSE_BOARD_TOKENS=stripe,canva
LEVER_COMPANY_SITES=netflix,spotify,figma
SMARTRECRUITERS_COMPANIES=Visa,Square
TEAMTAILOR_COMPANY_SLUGS=spotify,klarna
WORKABLE_ACCOUNT_SLUGS=company-slug
ASHBY_JOB_BOARD_SLUGS=Ashby,Linear,Notion
WORKDAY_CAREER_SITES=nvidia:wd5:NVIDIAExternalCareerSite
# Optional — often blocked server-side (HTTP 403)
WELLFOUND_SEARCH_PATHS=/role/l/product-designer/remote,/role/l/product-designer/bengaluru
LINKEDIN_JOB_QUERIES=Senior Product Designer,Product Designer,UI UX Designer
LINKEDIN_JOB_LOCATIONS=Bengaluru,India,Remote
```

Scanners with unset env vars skip discovery gracefully (except LinkedIn/Remotive/RemoteOK/WWR which use built-in design defaults) and report healthy in health checks.

## Attribution

- **RemoteOK**: When displaying RemoteOK listings, link to [remoteok.com](https://remoteok.com) (shown in dashboard Scan Insights).
- **LinkedIn**: Guest search cards only; open the LinkedIn URL for full JD / salary.

## Rate limits

Public APIs are polled with a shared 10s timeout and scanner-engine rate limiting. Prefer modest `SCANNER_MAX_LIMIT_PER_SOURCE` values for Workday detail fetches (one extra GET per job for descriptions).
