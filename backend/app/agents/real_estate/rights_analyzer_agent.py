"""Rights Analyzer Agent — Derechos del Piso/Construcción/Suelo/Herencias."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RightType(str, Enum):
    PISO_RIGHTS = "derechos_piso"
    CONSTRUCTION_RIGHTS = "derechos_construccion"
    LAND_RIGHTS = "derechos_suelo"
    INHERITANCE_RIGHTS = "derechos_herencia"


@dataclass
class DerechosPiso:
    """Derechos del Piso (Apartment/Unit Rights)."""

    superficie_construida: float  # Built area in sqm
    superficie_util: float  # Usable area
    uso_exclusivo: List[str] = field(default_factory=list)  # Exclusive use areas
    mejoras_permitidas: List[str] = field(default_factory=list)  # Allowed improvements
    restricciones_disposicion: List[str] = field(default_factory=list)  # Disposition restrictions
    deuda_expensas: Optional[float] = None  # Outstanding HOA fees
    porcentaje_condominio: float = 0.0  # Condominium percentage
    pueden_alquilar: bool = True
    pueden_hipotecar: bool = True
    notas_restricciones: str = ""


@dataclass
class DerechosConstruction:
    """Derechos de Construcción (Construction Rights)."""

    densidad_permitida: float  # Maximum density
    altura_maxima: float  # Max height in meters
    ocupacion_planta: float  # Floor occupancy percentage
    setbacks: Dict[str, float] = field(default_factory=dict)  # Building setbacks
    usos_permitidos: List[str] = field(default_factory=list)  # Permitted uses
    restricciones_zonificacion: List[str] = field(default_factory=list)  # Zoning restrictions
    posibilidad_ampliacion: bool = False
    altura_actual: Optional[float] = None
    densidad_actual: Optional[float] = None
    potencial_construccion_adicional: Optional[float] = None  # Additional buildable sqm


@dataclass
class DerechosSuelo:
    """Derechos del Suelo (Land Rights)."""

    area_total: float  # Total land area in sqm
    area_construccion: float  # Buildable area
    derechos_minerales: bool = False  # Mineral rights
    derechos_agua: Optional[str] = None  # Water rights type
    derechos_agricolas: Optional[str] = None  # Agricultural rights
    servidumbres: List[str] = field(default_factory=list)  # Easements
    limitaciones_naturales: List[str] = field(default_factory=list)  # Natural limitations
    riesgo_ambiental: Optional[str] = None  # Environmental risk level
    pendiente_terreno: Optional[float] = None  # Slope percentage


@dataclass
class DerechosHerencia:
    """Derechos de Herencia (Inheritance Rights)."""

    tipo_sucesion: str  # Type of succession (testada/intestada)
    numero_herederos: int
    reparto_porcentajes: Dict[str, float] = field(default_factory=dict)  # Heir percentages
    conflictos_pendientes: List[str] = field(default_factory=list)  # Outstanding conflicts
    impuestos_herencia: float = 0.0  # Inheritance taxes owed
    proceso_legalizacion: bool = False  # Legalization in progress
    documentos_requeridos: List[str] = field(default_factory=list)  # Required documents
    fecha_defuncion: Optional[datetime] = None
    testamento_disponible: bool = False
    status_legalizacion: str = "pendiente"  # pending/in_progress/complete


class RightsAnalyzerAgent:
    """Analyze property rights (piso, construcción, suelo, herencias)."""

    def __init__(self):
        self.analyses: Dict[str, Dict[str, Any]] = {}
        self.compliance_issues: Dict[str, List[str]] = {}

    def analyze_property_rights(self, property_data: Dict[str, Any], region: str = "Argentina") -> Dict[str, Any]:
        """Comprehensive rights analysis for property."""
        property_id = property_data.get("property_id", "unknown")

        rights_analysis = {
            "property_id": property_id,
            "region": region,
            "derechos_piso": None,
            "derechos_construccion": None,
            "derechos_suelo": None,
            "derechos_herencia": None,
            "overall_risk_level": "low",
            "critical_issues": [],
            "recommendations": [],
        }

        # Analyze based on property type and data
        if self._is_apartment_or_unit(property_data):
            rights_analysis["derechos_piso"] = self._analyze_derechos_piso(property_data, region)

        rights_analysis["derechos_construccion"] = self._analyze_derechos_construccion(property_data, region)
        rights_analysis["derechos_suelo"] = self._analyze_derechos_suelo(property_data, region)

        # Check for inheritance issues
        if property_data.get("in_inheritance_process"):
            rights_analysis["derechos_herencia"] = self._analyze_derechos_herencia(property_data, region)

        # Assess overall risk
        critical_issues = []
        if rights_analysis["derechos_piso"]:
            if rights_analysis["derechos_piso"].deuda_expensas and rights_analysis["derechos_piso"].deuda_expensas > 0:
                critical_issues.append(f"Outstanding HOA fees: ${rights_analysis['derechos_piso'].deuda_expensas:,.0f}")

        if rights_analysis["derechos_herencia"]:
            if rights_analysis["derechos_herencia"].conflictos_pendientes:
                critical_issues.extend(rights_analysis["derechos_herencia"].conflictos_pendientes)

        rights_analysis["critical_issues"] = critical_issues
        rights_analysis["overall_risk_level"] = self._assess_risk_level(rights_analysis)
        rights_analysis["recommendations"] = self._generate_rights_recommendations(rights_analysis)

        self.analyses[property_id] = rights_analysis
        logger.info(f"Rights analysis for {property_id}: risk_level={rights_analysis['overall_risk_level']}")

        return rights_analysis

    def _is_apartment_or_unit(self, property_data: Dict[str, Any]) -> bool:
        """Check if property is apartment/condo unit."""
        property_type = property_data.get("property_type", "").lower()
        return any(t in property_type for t in ["apartment", "condo", "unit", "piso"])

    def _analyze_derechos_piso(self, property_data: Dict[str, Any], region: str) -> DerechosPiso:
        """Analyze apartment/unit rights."""
        derechos = DerechosPiso(
            superficie_construida=property_data.get("built_area", 0),
            superficie_util=property_data.get("usable_area", 0),
            uso_exclusivo=property_data.get("exclusive_use_areas", []),
            mejoras_permitidas=property_data.get("allowed_improvements", []),
            restricciones_disposicion=property_data.get("disposition_restrictions", []),
            deuda_expensas=property_data.get("outstanding_hoa_fees", 0),
            porcentaje_condominio=property_data.get("condominium_percentage", 0),
            pueden_alquilar=property_data.get("can_rent", True),
            pueden_hipotecar=property_data.get("can_mortgage", True),
        )

        # Check regional rules
        if region.lower() == "argentina":
            derechos.notas_restricciones = self._get_argentina_piso_restrictions()
        elif region.lower() == "mexico":
            derechos.notas_restricciones = self._get_mexico_piso_restrictions()

        return derechos

    def _analyze_derechos_construccion(self, property_data: Dict[str, Any], region: str) -> DerechosConstruction:
        """Analyze construction rights."""
        derechos = DerechosConstruction(
            densidad_permitida=property_data.get("max_density", 0),
            altura_maxima=property_data.get("max_height", 0),
            ocupacion_planta=property_data.get("floor_occupancy", 0),
            setbacks=property_data.get("setbacks", {}),
            usos_permitidos=property_data.get("permitted_uses", []),
            restricciones_zonificacion=property_data.get("zoning_restrictions", []),
            posibilidad_ampliacion=property_data.get("can_expand", False),
            altura_actual=property_data.get("current_height"),
            densidad_actual=property_data.get("current_density"),
            potencial_construccion_adicional=property_data.get("additional_buildable_sqm"),
        )

        return derechos

    def _analyze_derechos_suelo(self, property_data: Dict[str, Any], region: str) -> DerechosSuelo:
        """Analyze land rights."""
        derechos = DerechosSuelo(
            area_total=property_data.get("land_area", 0),
            area_construccion=property_data.get("buildable_area", 0),
            derechos_minerales=property_data.get("has_mineral_rights", False),
            derechos_agua=property_data.get("water_rights_type"),
            derechos_agricolas=property_data.get("agricultural_rights_type"),
            servidumbres=property_data.get("easements", []),
            limitaciones_naturales=property_data.get("natural_limitations", []),
            riesgo_ambiental=property_data.get("environmental_risk_level"),
            pendiente_terreno=property_data.get("slope_percentage"),
        )

        return derechos

    def _analyze_derechos_herencia(self, property_data: Dict[str, Any], region: str) -> DerechosHerencia:
        """Analyze inheritance rights."""
        derechos = DerechosHerencia(
            tipo_sucesion=property_data.get("succession_type", "testada"),
            numero_herederos=property_data.get("number_of_heirs", 0),
            reparto_porcentajes=property_data.get("heir_percentages", {}),
            conflictos_pendientes=property_data.get("inheritance_conflicts", []),
            impuestos_herencia=property_data.get("inheritance_taxes_owed", 0),
            proceso_legalizacion=property_data.get("legalization_in_progress", False),
            documentos_requeridos=property_data.get("required_documents", []),
            fecha_defuncion=property_data.get("death_date"),
            testamento_disponible=property_data.get("will_available", False),
            status_legalizacion=property_data.get("legalization_status", "pendiente"),
        )

        return derechos

    def _get_argentina_piso_restrictions(self) -> str:
        """Argentina-specific piso restrictions."""
        return """
        - Ley de Propiedad Horizontal: HOA governed by Ley 13.512
        - Common expenses mandatory
        - Cannot alter exterior or shared elements
        - Rental restricted by building rules if condo
        """

    def _get_mexico_piso_restrictions(self) -> str:
        """Mexico-specific piso restrictions."""
        return """
        - Condominio rules per state law
        - Cuota de mantenimiento mandatory
        - Restrictions vary by state/municipality
        - Some restrictions on foreign ownership
        """

    def _assess_risk_level(self, analysis: Dict[str, Any]) -> str:
        """Assess overall risk level of property rights."""
        risk_factors = 0

        if analysis.get("critical_issues"):
            risk_factors += len(analysis["critical_issues"])

        if analysis.get("derechos_herencia"):
            if analysis["derechos_herencia"].conflictos_pendientes:
                risk_factors += 3
            if analysis["derechos_herencia"].status_legalizacion != "complete":
                risk_factors += 2

        if analysis.get("derechos_piso"):
            if not analysis["derechos_piso"].pueden_hipotecar:
                risk_factors += 2

        if risk_factors == 0:
            return "low"
        elif risk_factors <= 2:
            return "moderate"
        elif risk_factors <= 4:
            return "high"
        else:
            return "critical"

    def _generate_rights_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on rights analysis."""
        recommendations = []

        if analysis.get("derechos_herencia"):
            herencia = analysis["derechos_herencia"]
            if herencia.status_legalizacion != "complete":
                recommendations.append("Complete inheritance legalization before closing")
            if herencia.conflictos_pendientes:
                recommendations.append("Resolve inheritance conflicts with legal counsel")
            if herencia.numero_herederos > 1:
                recommendations.append("Ensure all heirs consent to sale in writing")

        if analysis.get("derechos_piso"):
            piso = analysis["derechos_piso"]
            if piso.deuda_expensas and piso.deuda_expensas > 0:
                recommendations.append(f"Clear HOA debt of ${piso.deuda_expensas:,.0f} before closing")
            if not piso.pueden_hipotecar:
                recommendations.append("This unit cannot be mortgaged - cash sale only")
            if not piso.pueden_alquilar:
                recommendations.append("This unit cannot be rented - owner-occupied only")

        if analysis.get("derechos_construccion"):
            construccion = analysis["derechos_construccion"]
            if construccion.posibilidad_ampliacion:
                recommendations.append(
                    f"Property can be expanded by {construccion.potencial_construccion_adicional} sqm"
                )

        if analysis.get("overall_risk_level") in ["high", "critical"]:
            recommendations.append("MANDATORY: Consult with real estate attorney before proceeding")

        return recommendations

    def check_inheritance_legality(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Detailed check for inheritance-related properties."""
        if property_id not in self.analyses:
            return None

        analysis = self.analyses[property_id]
        herencia = analysis.get("derechos_herencia")

        if not herencia:
            return None

        return {
            "property_id": property_id,
            "succession_type": herencia.tipo_sucesion,
            "is_testamentary": herencia.tipo_sucesion == "testada",
            "heirs_count": herencia.numero_herederos,
            "outstanding_taxes": herencia.impuestos_herencia,
            "legalization_complete": herencia.status_legalizacion == "complete",
            "conflicts": herencia.conflictos_pendientes,
            "can_sell": herencia.status_legalizacion == "complete" and len(herencia.conflictos_pendientes) == 0,
            "required_steps": self._get_inheritance_required_steps(herencia),
        }

    def _get_inheritance_required_steps(self, herencia: DerechosHerencia) -> List[str]:
        """Get required steps for inheritance completion."""
        steps = []

        if not herencia.testamento_disponible:
            steps.append("Obtain/validate will")

        if herencia.status_legalizacion != "complete":
            steps.append("Complete succession legalization process")

        if herencia.impuestos_herencia > 0:
            steps.append(f"Pay inheritance taxes: ${herencia.impuestos_herencia:,.0f}")

        if len(herencia.conflictos_pendientes) > 0:
            steps.append("Resolve inheritance conflicts")

        if herencia.numero_herederos > 1:
            steps.append("Obtain written consent from all heirs")

        return steps
