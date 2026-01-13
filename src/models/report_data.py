"""
Modelos de datos para reportes y períodos.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Optional, Any
from collections import Counter

from .crime_record import CrimeRecord
from .mentioned_person import MentionedPerson
from .apprehended import Apprehended
from ..utils.date_utils import format_date_range
from ..utils.constants import (
    DIAS_SEMANA,
    FranjaHoraria,
    CategoriaDelito,
    CLASIFICACION_APREHENDIDOS,
)


@dataclass
class PeriodData:
    """
    Datos procesados para un período específico.
    
    Contiene todos los conteos y agregaciones necesarios
    para generar los cuadros del informe.
    """
    
    # Identificación del período
    nombre: str = ""
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    
    # Registros del período
    hechos: List[CrimeRecord] = field(default_factory=list)
    mencionados: List[MentionedPerson] = field(default_factory=list)
    aprehendidos: List[Apprehended] = field(default_factory=list)
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPIEDADES BÁSICAS
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def rango_fechas(self) -> str:
        """Rango de fechas formateado."""
        if self.fecha_inicio and self.fecha_fin:
            return format_date_range(self.fecha_inicio, self.fecha_fin)
        return self.nombre
    
    @property
    def total_hechos(self) -> int:
        """Total de hechos delictuales."""
        return len(self.hechos)
    
    @property
    def total_mencionados(self) -> int:
        """Total de personas mencionadas."""
        return len(self.mencionados)
    
    @property
    def total_aprehendidos(self) -> int:
        """Total de personas aprehendidas."""
        return len(self.aprehendidos)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONTEOS POR CATEGORÍA
    # ═══════════════════════════════════════════════════════════════════════
    
    def conteo_por_delito(self) -> Dict[str, int]:
        """Conteo de hechos por tipo de delito CON MODALIDAD."""
        return dict(Counter(h.delito_con_modalidad for h in self.hechos if h.delito_con_modalidad))
    
    def conteo_por_categoria(self) -> Dict[str, int]:
        """Conteo de hechos por categoría (ROBOS, HURTOS, OTROS)."""
        counter = Counter(h.categoria.value for h in self.hechos)
        return dict(counter)
    
    def conteo_por_dia_semana(self) -> Dict[str, int]:
        """Conteo de hechos por día de la semana."""
        result = {dia: 0 for dia in DIAS_SEMANA}
        for h in self.hechos:
            dia = h.dia_semana
            if dia and dia in result:
                result[dia] += 1
        return result
    
    def conteo_por_franja_horaria(self) -> Dict[str, int]:
        """Conteo de hechos por franja horaria."""
        result = {f.display_name: 0 for f in FranjaHoraria}
        for h in self.hechos:
            franja = h.franja_horaria
            if franja:
                result[franja.display_name] += 1
        return result
    
    def conteo_por_movilidad(self) -> Dict[str, int]:
        """Conteo de hechos por medio de movilidad."""
        counter = Counter(
            h.movilidad if h.movilidad else "#NO_CONSTA"
            for h in self.hechos
        )
        return dict(counter)
    
    def conteo_por_arma(self) -> Dict[str, int]:
        """Conteo de armas/medios en robos agravados."""
        robos_agravados = [h for h in self.hechos if h.es_robo_agravado]
        counter = Counter(
            h.arma_medio if h.arma_medio else "#NO_CONSTA"
            for h in robos_agravados
        )
        return dict(counter)
    
    def conteo_por_ambito(self) -> Dict[str, int]:
        """Conteo de hechos por ámbito de ocurrencia."""
        counter = Counter(
            h.ambito if h.ambito else "#NO_CONSTA"
            for h in self.hechos
        )
        return dict(counter)
    
    def conteo_esclarecimiento(self) -> Dict[str, int]:
        """Conteo por estado de esclarecimiento."""
        counter = Counter(h.tipo_esclarecimiento for h in self.hechos)
        return dict(counter)
    
    def conteo_aprehendidos_clasificacion(self) -> Dict[str, int]:
        """Conteo de aprehendidos por clasificación."""
        result = {c: 0 for c in CLASIFICACION_APREHENDIDOS}
        for a in self.aprehendidos:
            clasif = a.clasificacion_normalizada
            if clasif in result:
                result[clasif] += 1
            else:
                result[clasif] = 1
        return result
    
    # ═══════════════════════════════════════════════════════════════════════
    # MATRICES (DELITO × DIMENSIÓN)
    # ═══════════════════════════════════════════════════════════════════════
    
    def matriz_delito_dia(self) -> Dict[str, Dict[str, int]]:
        """
        Matriz de delitos por día de la semana.
        
        Returns:
            {delito: {día: cantidad}}
        """
        delitos = sorted(set(h.delito for h in self.hechos if h.delito))
        matriz = {
            delito: {dia: 0 for dia in DIAS_SEMANA}
            for delito in delitos
        }
        
        for h in self.hechos:
            if h.delito and h.dia_semana:
                matriz[h.delito][h.dia_semana] += 1
        
        return matriz
    
    def matriz_delito_franja(self) -> Dict[str, Dict[str, int]]:
        """
        Matriz de delitos por franja horaria.
        
        Returns:
            {delito: {franja: cantidad}}
        """
        franjas = [f.display_name for f in FranjaHoraria]
        delitos = sorted(set(h.delito for h in self.hechos if h.delito))
        matriz = {
            delito: {franja: 0 for franja in franjas}
            for delito in delitos
        }
        
        for h in self.hechos:
            if h.delito and h.franja_horaria:
                matriz[h.delito][h.franja_horaria.display_name] += 1
        
        return matriz
    
    def matriz_delito_modalidad_dia(self) -> Dict[str, Dict[str, int]]:
        """
        Matriz de delitos CON MODALIDAD por día de la semana.
        
        Returns:
            {delito_con_modalidad: {día: cantidad}}
        """
        delitos = sorted(set(h.delito_con_modalidad for h in self.hechos if h.delito_con_modalidad))
        matriz = {
            delito: {dia: 0 for dia in DIAS_SEMANA}
            for delito in delitos
        }
        
        for h in self.hechos:
            if h.delito_con_modalidad and h.dia_semana:
                matriz[h.delito_con_modalidad][h.dia_semana] += 1
        
        return matriz
    
    def matriz_delito_modalidad_franja(self) -> Dict[str, Dict[str, int]]:
        """
        Matriz de delitos CON MODALIDAD por franja horaria.
        
        Returns:
            {delito_con_modalidad: {franja: cantidad}}
        """
        franjas = [f.display_name for f in FranjaHoraria]
        delitos = sorted(set(h.delito_con_modalidad for h in self.hechos if h.delito_con_modalidad))
        matriz = {
            delito: {franja: 0 for franja in franjas}
            for delito in delitos
        }
        
        for h in self.hechos:
            if h.delito_con_modalidad and h.franja_horaria:
                matriz[h.delito_con_modalidad][h.franja_horaria.display_name] += 1
        
        return matriz
    
    # ═══════════════════════════════════════════════════════════════════════
    # CUADRO DE REFERENCIA
    # ═══════════════════════════════════════════════════════════════════════
    
    def cuadro_referencia(self) -> List[Dict[str, Any]]:
        """
        Genera el cuadro de referencia para mapas.
        
        Agrupa por categoría (ROBOS, TENTATIVA ROBOS, HURTOS, TENTATIVA HURTOS, ESTAFAS)
        y muestra subtotales.
        """
        conteo = self.conteo_por_delito()  # Usa delito_con_modalidad
        categorias = self.conteo_por_categoria()
        esclarecidos = self.conteo_esclarecimiento()
        
        filas = []
        
        # ROBOS CONSUMADOS
        robos = [
            (delito, cant) for delito, cant in conteo.items()
            if any(h.delito_con_modalidad == delito and h.categoria == CategoriaDelito.ROBO 
                   for h in self.hechos)
        ]
        if robos:
            filas.append({"tipo": "categoria", "texto": "ROBOS", "cantidad": None})
            for delito, cant in sorted(robos, key=lambda x: -x[1]):
                filas.append({"tipo": "delito", "texto": delito, "cantidad": cant})
            filas.append({
                "tipo": "subtotal",
                "texto": "SUBTOTAL - ROBOS",
                "cantidad": categorias.get(CategoriaDelito.ROBO.value, 0)
            })
        
        # TENTATIVAS DE ROBO
        tentativas_robo = [
            (delito, cant) for delito, cant in conteo.items()
            if any(h.delito_con_modalidad == delito and h.categoria == CategoriaDelito.TENTATIVA_ROBO 
                   for h in self.hechos)
        ]
        if tentativas_robo:
            filas.append({"tipo": "categoria", "texto": "TENTATIVAS DE ROBO", "cantidad": None})
            for delito, cant in sorted(tentativas_robo, key=lambda x: -x[1]):
                filas.append({"tipo": "delito", "texto": delito, "cantidad": cant})
            filas.append({
                "tipo": "subtotal",
                "texto": "SUBTOTAL - TENTATIVAS ROBO",
                "cantidad": categorias.get(CategoriaDelito.TENTATIVA_ROBO.value, 0)
            })
        
        # HURTOS CONSUMADOS
        hurtos = [
            (delito, cant) for delito, cant in conteo.items()
            if any(h.delito_con_modalidad == delito and h.categoria == CategoriaDelito.HURTO 
                   for h in self.hechos)
        ]
        if hurtos:
            filas.append({"tipo": "categoria", "texto": "HURTOS", "cantidad": None})
            for delito, cant in sorted(hurtos, key=lambda x: -x[1]):
                filas.append({"tipo": "delito", "texto": delito, "cantidad": cant})
            filas.append({
                "tipo": "subtotal",
                "texto": "SUBTOTAL - HURTOS",
                "cantidad": categorias.get(CategoriaDelito.HURTO.value, 0)
            })
        
        # TENTATIVAS DE HURTO
        tentativas_hurto = [
            (delito, cant) for delito, cant in conteo.items()
            if any(h.delito_con_modalidad == delito and h.categoria == CategoriaDelito.TENTATIVA_HURTO 
                   for h in self.hechos)
        ]
        if tentativas_hurto:
            filas.append({"tipo": "categoria", "texto": "TENTATIVAS DE HURTO", "cantidad": None})
            for delito, cant in sorted(tentativas_hurto, key=lambda x: -x[1]):
                filas.append({"tipo": "delito", "texto": delito, "cantidad": cant})
            filas.append({
                "tipo": "subtotal",
                "texto": "SUBTOTAL - TENTATIVAS HURTO",
                "cantidad": categorias.get(CategoriaDelito.TENTATIVA_HURTO.value, 0)
            })
        
        # ESTAFAS
        estafas = [
            (delito, cant) for delito, cant in conteo.items()
            if any(h.delito_con_modalidad == delito and h.categoria == CategoriaDelito.ESTAFA 
                   for h in self.hechos)
        ]
        if estafas:
            filas.append({"tipo": "categoria", "texto": "ESTAFAS", "cantidad": None})
            for delito, cant in sorted(estafas, key=lambda x: -x[1]):
                filas.append({"tipo": "delito", "texto": delito, "cantidad": cant})
            filas.append({
                "tipo": "subtotal",
                "texto": "SUBTOTAL - ESTAFAS",
                "cantidad": categorias.get(CategoriaDelito.ESTAFA.value, 0)
            })
        
        # TOTAL
        filas.append({
            "tipo": "total",
            "texto": "TOTAL DELITOS REGISTRADOS",
            "cantidad": self.total_hechos
        })
        
        # ESCLARECIDOS
        if any(v > 0 for k, v in esclarecidos.items() if k != "NO_ESCLARECIDO"):
            filas.append({"tipo": "separador", "texto": "INDICACIONES", "cantidad": None})
            for tipo, cant in esclarecidos.items():
                if cant > 0 and tipo != "NO_ESCLARECIDO":
                    texto = tipo.replace("_", " ").title()
                    filas.append({"tipo": "indicacion", "texto": f"Hechos {texto}", "cantidad": cant})
            total_escl = sum(v for k, v in esclarecidos.items() if k != "NO_ESCLARECIDO")
            filas.append({
                "tipo": "subtotal",
                "texto": "TOTAL HECHOS ESCLARECIDOS",
                "cantidad": total_escl
            })
        
        return filas


@dataclass
class ReportData:
    """
    Contenedor principal de datos para generación de reportes.
    
    Puede contener uno o más períodos para comparación.
    """
    
    # Información general
    titulo: str = "INFORME DELICTUAL"
    jurisdiccion: str = ""
    fecha_generacion: Optional[date] = None
    
    # Períodos
    periodos: List[PeriodData] = field(default_factory=list)
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPIEDADES
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def es_comparativo(self) -> bool:
        """Indica si hay múltiples períodos para comparar."""
        return len(self.periodos) > 1
    
    @property
    def periodo_principal(self) -> Optional[PeriodData]:
        """Primer período (el principal)."""
        return self.periodos[0] if self.periodos else None
    
    @property
    def periodo_comparacion(self) -> Optional[PeriodData]:
        """Segundo período (para comparación). Mantiene compatibilidad."""
        return self.periodos[1] if len(self.periodos) > 1 else None
    
    @property
    def periodos_comparacion(self) -> List[PeriodData]:
        """Todos los períodos de comparación (excluyendo el principal)."""
        return self.periodos[1:] if len(self.periodos) > 1 else []
    
    @property
    def num_periodos(self) -> int:
        """Número total de períodos."""
        return len(self.periodos)
    
    def get_periodo(self, index: int) -> Optional[PeriodData]:
        """Obtiene un período por índice."""
        if 0 <= index < len(self.periodos):
            return self.periodos[index]
        return None
    
    # ═══════════════════════════════════════════════════════════════════════
    # MÉTODOS
    # ═══════════════════════════════════════════════════════════════════════
    
    def agregar_periodo(self, periodo: PeriodData) -> None:
        """Agrega un período al reporte."""
        self.periodos.append(periodo)
    
    def comparar_conteos(
        self,
        conteo_a: Dict[str, int],
        conteo_b: Dict[str, int]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compara dos conteos y calcula variaciones.
        
        Returns:
            {categoria: {periodo_a, periodo_b, diferencia, porcentaje}}
        """
        todas_claves = set(conteo_a.keys()) | set(conteo_b.keys())
        resultado = {}
        
        for clave in todas_claves:
            val_a = conteo_a.get(clave, 0)
            val_b = conteo_b.get(clave, 0)
            diferencia = val_b - val_a
            
            if val_a > 0:
                porcentaje = ((val_b - val_a) / val_a) * 100
            elif val_b > 0:
                porcentaje = 100.0  # Nuevo (no existía antes)
            else:
                porcentaje = 0.0
            
            resultado[clave] = {
                "periodo_a": val_a,
                "periodo_b": val_b,
                "diferencia": diferencia,
                "porcentaje": round(porcentaje, 2),
                "tendencia": "subio" if diferencia > 0 else ("bajo" if diferencia < 0 else "igual")
            }
        
        return resultado
