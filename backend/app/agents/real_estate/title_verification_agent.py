"""Title Verification Agent — Title search, liens, encumbrances."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TitleIssue:
    """Title issue or lien."""

    issue_type: str
    description: str
    amount: Optional[float] = None
    holder: Optional[str] = None
    priority_order: int = 0  # For liens
    resolvable: bool = True


@dataclass
class TitleReport:
    """Title search and verification report."""

    property_id: str
    title_clear: bool
    liens: List[TitleIssue] = field(default_factory=list)
    encumbrances: List[TitleIssue] = field(default_factory=list)
    easements: List[TitleIssue] = field(default_factory=list)
    other_issues: List[TitleIssue] = field(default_factory=list)
    title_insurance_available: bool = True
    title_insurance_cost: float = 0.0
    estimated_clear_date: Optional[datetime] = None
    attorney_recommendation: str = ""


class TitleVerificationAgent:
    """Verify property title and identify issues."""

    def __init__(self):
        self.title_reports: Dict[str, TitleReport] = {}

    def perform_title_search(self, property_data: Dict[str, Any]) -> TitleReport:
        """Perform comprehensive title search and verification."""
        property_id = property_data.get("property_id", "unknown")

        liens = []
        encumbrances = []
        easements = []
        other_issues = []

        # Check for liens
        if property_data.get("has_mortgage"):
            liens.append(
                TitleIssue(
                    issue_type="mortgage",
                    description="Existing mortgage lien",
                    amount=property_data.get("remaining_mortgage_balance", 0),
                    holder=property_data.get("lender_name"),
                    priority_order=1,
                    resolvable=True,
                )
            )

        if property_data.get("property_tax_delinquent"):
            liens.append(
                TitleIssue(
                    issue_type="tax_lien",
                    description="Property tax lien",
                    amount=property_data.get("delinquent_taxes", 0),
                    holder="Tax Collector",
                    priority_order=0,  # Tax liens are first priority
                    resolvable=True,
                )
            )

        if property_data.get("hoa_debt"):
            liens.append(
                TitleIssue(
                    issue_type="hoa_lien",
                    description="HOA lien for unpaid fees",
                    amount=property_data.get("hoa_debt_amount", 0),
                    holder="Homeowners Association",
                    resolvable=True,
                )
            )

        # Check for encumbrances
        if property_data.get("has_easement"):
            encumbrances.append(
                TitleIssue(
                    issue_type="easement",
                    description="Utility easement",
                    holder="Utility company",
                    resolvable=False,
                )
            )

        if property_data.get("has_right_of_way"):
            encumbrances.append(
                TitleIssue(
                    issue_type="right_of_way",
                    description="Right of way for public/private use",
                    resolvable=False,
                )
            )

        # Check for other issues
        if property_data.get("title_discrepancy"):
            other_issues.append(
                TitleIssue(
                    issue_type="description_discrepancy",
                    description="Property description mismatch in records",
                    resolvable=True,
                )
            )

        if property_data.get("unpaid_judgments"):
            other_issues.append(
                TitleIssue(
                    issue_type="judgment_lien",
                    description="Judgment lien from court case",
                    amount=property_data.get("judgment_amount", 0),
                    resolvable=True,
                )
            )

        # Determine if title is clear
        title_clear = len(liens) == 0 and len(other_issues) == 0

        # Calculate title insurance cost
        purchase_price = property_data.get("purchase_price", 300000)
        title_insurance_cost = purchase_price * 0.006  # 0.6% of purchase price

        # Estimate clear date
        days_to_clear = 0
        for issue in liens + other_issues:
            if issue.resolvable:
                days_to_clear += 15

        estimated_clear = None
        if days_to_clear > 0:
            from datetime import timedelta

            estimated_clear = datetime.utcnow() + timedelta(days=days_to_clear)

        # Generate attorney recommendation
        attorney_rec = self._generate_attorney_recommendation(liens, encumbrances, other_issues, title_clear)

        report = TitleReport(
            property_id=property_id,
            title_clear=title_clear,
            liens=liens,
            encumbrances=encumbrances,
            easements=easements,
            other_issues=other_issues,
            title_insurance_available=title_clear,
            title_insurance_cost=title_insurance_cost,
            estimated_clear_date=estimated_clear,
            attorney_recommendation=attorney_rec,
        )

        self.title_reports[property_id] = report
        logger.info(f"Title search for {property_id}: clear={title_clear}, issues={len(liens + encumbrances + other_issues)}")

        return report

    def _generate_attorney_recommendation(self, liens: List[TitleIssue], encumbrances: List[TitleIssue], other_issues: List[TitleIssue],
                                        title_clear: bool) -> str:
        """Generate attorney recommendation."""
        if title_clear:
            return "Title is clear. Proceed with title insurance and closing."

        issues = liens + other_issues
        resolvable_count = sum(1 for i in issues if i.resolvable)
        non_resolvable_count = sum(1 for i in issues if not i.resolvable)

        if non_resolvable_count > 0:
            return "Title has non-resolvable issues. Consult title attorney before proceeding."

        if resolvable_count > 0:
            return f"Title has {resolvable_count} resolvable issues. Estimated {self.title_reports.get(list(self.title_reports.keys())[0]).estimated_clear_date.strftime('%B %d')} to clear with proper remediation."

        return "Consult title attorney for detailed review."

    def resolve_title_issue(self, property_id: str, issue_type: str, resolution_action: str) -> Dict[str, Any]:
        """Record title issue resolution."""
        if property_id not in self.title_reports:
            return {"error": "Title report not found"}

        report = self.title_reports[property_id]

        # Find and remove issue
        for issue_list in [report.liens, report.other_issues]:
            for issue in issue_list:
                if issue.issue_type == issue_type:
                    issue_list.remove(issue)
                    logger.info(f"Resolved {issue_type} for {property_id}: {resolution_action}")

        # Update title clear status
        report.title_clear = len(report.liens) == 0 and len(report.other_issues) == 0

        return {
            "property_id": property_id,
            "issue_type": issue_type,
            "resolution": resolution_action,
            "title_now_clear": report.title_clear,
        }

    def generate_title_commitment(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Generate title commitment document."""
        if property_id not in self.title_reports:
            return None

        report = self.title_reports[property_id]

        return {
            "property_id": property_id,
            "document_type": "Title Commitment",
            "date": datetime.utcnow().isoformat(),
            "title_company": "Sample Title Insurance Company",
            "insurance_commitment_amount": 300000,  # Purchase price
            "title_status": "Clear" if report.title_clear else "Subject to",
            "subject_to_items": [
                {"item": f"{issue.issue_type}: {issue.description}"} for issue in report.liens + report.other_issues
            ],
            "exceptions": [
                {"exception": f"{easement.description}"} for easement in report.easements
            ],
        }

    def verify_title_insurance_options(self, property_id: str) -> Dict[str, Any]:
        """Provide title insurance options and recommendations."""
        if property_id not in self.title_reports:
            return {}

        report = self.title_reports[property_id]

        return {
            "property_id": property_id,
            "owner_policy_available": report.title_clear,
            "lender_policy_available": True,
            "owner_policy_cost": report.title_insurance_cost,
            "lender_policy_cost": report.title_insurance_cost * 0.5,
            "recommendation": "Obtain both owner's and lender's policies" if report.title_clear else "Resolve title issues first",
            "coverage_includes": [
                "Loss from defects in title",
                "Hidden liens or encumbrances",
                "Unknown heirs or claims",
                "Forged documents",
                "Undisclosed easements",
            ],
        }
