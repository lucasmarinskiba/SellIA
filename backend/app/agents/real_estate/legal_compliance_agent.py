"""Legal Compliance Agent — Regulatory checks, required docs, disclosures."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ComplianceCheckResult:
    """Compliance check results."""

    property_id: str
    compliant: bool
    severity_level: str  # low, medium, high, critical
    issues: List[Dict[str, Any]] = field(default_factory=list)
    missing_documents: List[str] = field(default_factory=list)
    required_disclosures: List[str] = field(default_factory=list)
    estimated_remediation_days: int = 0
    recommendations: List[str] = field(default_factory=list)


class LegalComplianceAgent:
    """Check regulatory compliance and required documentation."""

    def __init__(self, region: str = "Argentina"):
        self.region = region
        self.compliance_checks: Dict[str, ComplianceCheckResult] = {}

    def perform_compliance_check(self, property_data: Dict[str, Any]) -> ComplianceCheckResult:
        """Comprehensive legal compliance check."""
        property_id = property_data.get("property_id", "unknown")

        issues = []
        missing_docs = []
        required_disclosures = []
        severity_level = "low"
        estimated_days = 0

        # Check title status
        if not property_data.get("clear_title"):
            issues.append({"type": "title", "description": "Title not clear - liens or encumbrances present"})
            missing_docs.append("Clear title report")
            severity_level = "high"
            estimated_days += 30

        # Check required documents
        required_docs = self._get_required_documents(self.region)
        for doc in required_docs:
            if not property_data.get(f"has_{doc}"):
                missing_docs.append(doc)
                estimated_days += 5

        # Check mandatory disclosures
        required_discs = self._get_required_disclosures(self.region, property_data)
        for disc in required_discs:
            if not property_data.get(f"disclosed_{disc}"):
                required_disclosures.append(disc)

        # Check HOA/community status
        if property_data.get("is_condo"):
            if not property_data.get("hoa_approval"):
                issues.append({"type": "hoa", "description": "HOA approval not confirmed"})
                severity_level = "medium"

        # Check environmental compliance
        environmental_risk = property_data.get("environmental_risk_level", "low")
        if environmental_risk in ["medium", "high"]:
            missing_docs.append("Environmental assessment report")
            severity_level = "medium"

        # Check property tax status
        if property_data.get("property_tax_delinquent"):
            issues.append({"type": "taxes", "description": "Property taxes delinquent"})
            severity_level = "high"
            estimated_days += 15

        # Check utilities and services
        utilities = property_data.get("utilities_connected", [])
        if len(utilities) < 3:  # Should have water, electric, gas/sewage
            issues.append({"type": "utilities", "description": "Not all utilities connected"})
            severity_level = "medium"

        compliant = severity_level in ["low", "medium"] and len(issues) == 0

        recommendations = self._generate_compliance_recommendations(issues, missing_docs)

        result = ComplianceCheckResult(
            property_id=property_id,
            compliant=compliant,
            severity_level=severity_level,
            issues=issues,
            missing_documents=missing_docs,
            required_disclosures=required_disclosures,
            estimated_remediation_days=estimated_days,
            recommendations=recommendations,
        )

        self.compliance_checks[property_id] = result
        logger.info(f"Compliance check for {property_id}: {severity_level} severity, compliant={compliant}")

        return result

    def _get_required_documents(self, region: str) -> List[str]:
        """Get region-specific required documents."""
        if region.lower() == "argentina":
            return [
                "title_deed",
                "property_registry_extract",
                "municipal_certificate",
                "land_survey",
                "construction_permit",
                "final_inspection_certificate",
                "property_tax_receipt",
            ]
        elif region.lower() == "mexico":
            return [
                "escritura_publica",
                "copia_catastral",
                "copia_registro_publico",
                "recibo_predial",
                "comprobante_servicios",
            ]
        else:
            return ["title_deed", "property_survey", "property_tax_records"]

    def _get_required_disclosures(self, region: str, property_data: Dict[str, Any]) -> List[str]:
        """Get region-specific required disclosures."""
        disclosures = [
            "property_condition",
            "previous_damage",
            "repairs_history",
            "known_defects",
        ]

        if property_data.get("has_pool"):
            disclosures.append("pool_condition_and_maintenance")

        if property_data.get("is_flood_zone"):
            disclosures.append("flood_zone_status")

        if property_data.get("is_historic_property"):
            disclosures.append("historic_designation_restrictions")

        return disclosures

    def _generate_compliance_recommendations(self, issues: List[Dict[str, Any]], missing_docs: List[str]) -> List[str]:
        """Generate recommendations to achieve compliance."""
        recommendations = []

        for issue in issues:
            issue_type = issue.get("type", "")
            if issue_type == "title":
                recommendations.append("Obtain title insurance and clear any liens before closing")
            elif issue_type == "hoa":
                recommendations.append("Contact HOA for approval documentation")
            elif issue_type == "taxes":
                recommendations.append("Settle delinquent property taxes before transfer")
            elif issue_type == "utilities":
                recommendations.append("Ensure all utilities are properly connected and registered")

        for doc in missing_docs:
            recommendations.append(f"Obtain: {doc}")

        return recommendations

    def check_disclosure_compliance(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Detailed disclosure compliance check."""
        if property_id not in self.compliance_checks:
            return None

        result = self.compliance_checks[property_id]

        return {
            "property_id": property_id,
            "required_disclosures": result.required_disclosures,
            "all_disclosed": all(f"disclosed_{d}" for d in result.required_disclosures),
            "missing_disclosures": [d for d in result.required_disclosures if not f"disclosed_{d}"],
            "disclosure_deadline": "Before signing purchase agreement",
            "penalty_for_non_disclosure": "Buyer can rescind, sue for damages",
        }

    def verify_documentation_complete(self, property_id: str) -> bool:
        """Verify all documentation is complete."""
        if property_id not in self.compliance_checks:
            return False

        result = self.compliance_checks[property_id]
        return len(result.missing_documents) == 0 and result.compliant
