"""
Comparador de períodos.

Genera las comparaciones estadísticas entre múltiples períodos
para los cuadros comparativos del informe.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from ..models.report_data import PeriodData


class Tendencia(Enum):
    """Tendencia de variación."""
    SUBIO = "subio"
    BAJO = "bajo"
    IGUAL = "igual"
    NUEVO = "nuevo"


@dataclass
class ComparacionItem:
    """Resultado de comparación para un ítem."""
    categoria: str
    valor_periodo_a: int
    valor_periodo_b: int
    diferencia: int
    porcentaje: float
    tendencia: Tendencia
    
    @property
    def tendencia_icono(self) -> str:
        """Icono de tendencia."""
        iconos = {
            Tendencia.SUBIO: "▲",
            Tendencia.BAJO: "▼",
            Tendencia.IGUAL: "─",
            Tendencia.NUEVO: "★"
        }
        return iconos.get(self.tendencia, "")
    
    @property
    def tendencia_color(self) -> str:
        """Color según tendencia (para delitos, subir es malo)."""
        colores = {
            Tendencia.SUBIO: "#FF3B3B",   # Rojo (malo)
            Tendencia.BAJO: "#00FF88",     # Verde (bueno)
            Tendencia.IGUAL: "#808080",    # Gris
            Tendencia.NUEVO: "#FFaa00"     # Naranja
        }
        return colores.get(self.tendencia, "#808080")
    
    @property
    def porcentaje_formateado(self) -> str:
        """Porcentaje formateado con signo."""
        if self.tendencia == Tendencia.NUEVO:
            return "NUEVO"
        signo = "+" if self.porcentaje > 0 else ""
        return f"{signo}{self.porcentaje:.2f}%"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'categoria': self.categoria,
            'periodo_a': self.valor_periodo_a,
            'periodo_b': self.valor_periodo_b,
            'diferencia': self.diferencia,
            'porcentaje': self.porcentaje,
            'porcentaje_str': self.porcentaje_formateado,
            'tendencia': self.tendencia.value,
            'tendencia_icono': self.tendencia_icono,
            'tendencia_color': self.tendencia_color
        }


class PeriodComparator:
    """
    Comparador de períodos para análisis estadístico.
    
    Genera comparaciones entre dos o más períodos con
    cálculo de variaciones absolutas y porcentuales.
    """
    
    def __init__(
        self,
        periodo_a: PeriodData,
        periodo_b: PeriodData
    ):
        """
        Inicializa el comparador.
        
        Args:
            periodo_a: Período base (anterior)
            periodo_b: Período a comparar (actual)
        """
        self.periodo_a = periodo_a
        self.periodo_b = periodo_b
    
    # ═══════════════════════════════════════════════════════════════════════
    # CÁLCULO DE VARIACIÓN
    # ═══════════════════════════════════════════════════════════════════════
    
    def _calcular_variacion(
        self,
        valor_a: int,
        valor_b: int
    ) -> tuple[int, float, Tendencia]:
        """
        Calcula la variación entre dos valores.
        
        Returns:
            (diferencia, porcentaje, tendencia)
        """
        diferencia = valor_b - valor_a
        
        if valor_a == 0:
            if valor_b > 0:
                return diferencia, 100.0, Tendencia.NUEVO
            else:
                return 0, 0.0, Tendencia.IGUAL
        
        porcentaje = ((valor_b - valor_a) / valor_a) * 100
        
        if diferencia > 0:
            tendencia = Tendencia.SUBIO
        elif diferencia < 0:
            tendencia = Tendencia.BAJO
        else:
            tendencia = Tendencia.IGUAL
        
        return diferencia, round(porcentaje, 2), tendencia
    
    def _comparar_conteos(
        self,
        conteo_a: Dict[str, int],
        conteo_b: Dict[str, int]
    ) -> List[ComparacionItem]:
        """
        Compara dos diccionarios de conteos.
        
        Returns:
            Lista de ComparacionItem ordenada por diferencia descendente.
        """
        todas_claves = sorted(set(conteo_a.keys()) | set(conteo_b.keys()))
        resultados = []
        
        for clave in todas_claves:
            val_a = conteo_a.get(clave, 0)
            val_b = conteo_b.get(clave, 0)
            
            diferencia, porcentaje, tendencia = self._calcular_variacion(val_a, val_b)
            
            resultados.append(ComparacionItem(
                categoria=clave,
                valor_periodo_a=val_a,
                valor_periodo_b=val_b,
                diferencia=diferencia,
                porcentaje=porcentaje,
                tendencia=tendencia
            ))
        
        # Ordenar por valor del período B (actual) descendente
        return sorted(resultados, key=lambda x: -x.valor_periodo_b)
    
    # ═══════════════════════════════════════════════════════════════════════
    # COMPARACIONES ESPECÍFICAS
    # ═══════════════════════════════════════════════════════════════════════
    
    def comparar_delitos(self) -> List[ComparacionItem]:
        """Compara los delitos por tipo."""
        return self._comparar_conteos(
            self.periodo_a.conteo_por_delito(),
            self.periodo_b.conteo_por_delito()
        )
    
    def comparar_categorias(self) -> List[ComparacionItem]:
        """Compara por categoría (ROBOS, HURTOS)."""
        return self._comparar_conteos(
            self.periodo_a.conteo_por_categoria(),
            self.periodo_b.conteo_por_categoria()
        )
    
    def comparar_dias_semana(self) -> List[ComparacionItem]:
        """Compara por día de la semana."""
        return self._comparar_conteos(
            self.periodo_a.conteo_por_dia_semana(),
            self.periodo_b.conteo_por_dia_semana()
        )
    
    def comparar_franjas_horarias(self) -> List[ComparacionItem]:
        """Compara por franja horaria."""
        return self._comparar_conteos(
            self.periodo_a.conteo_por_franja_horaria(),
            self.periodo_b.conteo_por_franja_horaria()
        )
    
    def comparar_movilidad(self) -> List[ComparacionItem]:
        """Compara por medio de movilidad."""
        return self._comparar_conteos(
            self.periodo_a.conteo_por_movilidad(),
            self.periodo_b.conteo_por_movilidad()
        )
    
    def comparar_armas(self) -> List[ComparacionItem]:
        """Compara por arma/medio utilizado."""
        return self._comparar_conteos(
            self.periodo_a.conteo_por_arma(),
            self.periodo_b.conteo_por_arma()
        )
    
    def comparar_ambitos(self) -> List[ComparacionItem]:
        """Compara por ámbito de ocurrencia."""
        return self._comparar_conteos(
            self.periodo_a.conteo_por_ambito(),
            self.periodo_b.conteo_por_ambito()
        )
    
    def comparar_esclarecimiento(self) -> List[ComparacionItem]:
        """Compara por estado de esclarecimiento."""
        return self._comparar_conteos(
            self.periodo_a.conteo_esclarecimiento(),
            self.periodo_b.conteo_esclarecimiento()
        )
    
    def comparar_aprehendidos(self) -> List[ComparacionItem]:
        """Compara clasificación de aprehendidos."""
        return self._comparar_conteos(
            self.periodo_a.conteo_aprehendidos_clasificacion(),
            self.periodo_b.conteo_aprehendidos_clasificacion()
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # RESUMEN GENERAL
    # ═══════════════════════════════════════════════════════════════════════
    
    def resumen_general(self) -> Dict[str, ComparacionItem]:
        """
        Genera un resumen general de las comparaciones principales.
        
        Returns:
            Diccionario con indicadores clave comparados.
        """
        indicadores = {}
        
        # Total hechos
        diff, pct, tend = self._calcular_variacion(
            self.periodo_a.total_hechos,
            self.periodo_b.total_hechos
        )
        indicadores['total_hechos'] = ComparacionItem(
            categoria="Total Delitos",
            valor_periodo_a=self.periodo_a.total_hechos,
            valor_periodo_b=self.periodo_b.total_hechos,
            diferencia=diff,
            porcentaje=pct,
            tendencia=tend
        )
        
        # Total robos
        cat_a = self.periodo_a.conteo_por_categoria()
        cat_b = self.periodo_b.conteo_por_categoria()
        diff, pct, tend = self._calcular_variacion(
            cat_a.get('ROBOS', 0),
            cat_b.get('ROBOS', 0)
        )
        indicadores['total_robos'] = ComparacionItem(
            categoria="Total Robos",
            valor_periodo_a=cat_a.get('ROBOS', 0),
            valor_periodo_b=cat_b.get('ROBOS', 0),
            diferencia=diff,
            porcentaje=pct,
            tendencia=tend
        )
        
        # Total hurtos
        diff, pct, tend = self._calcular_variacion(
            cat_a.get('HURTOS', 0),
            cat_b.get('HURTOS', 0)
        )
        indicadores['total_hurtos'] = ComparacionItem(
            categoria="Total Hurtos",
            valor_periodo_a=cat_a.get('HURTOS', 0),
            valor_periodo_b=cat_b.get('HURTOS', 0),
            diferencia=diff,
            porcentaje=pct,
            tendencia=tend
        )
        
        # Total aprehendidos
        diff, pct, tend = self._calcular_variacion(
            self.periodo_a.total_aprehendidos,
            self.periodo_b.total_aprehendidos
        )
        indicadores['total_aprehendidos'] = ComparacionItem(
            categoria="Total Aprehendidos",
            valor_periodo_a=self.periodo_a.total_aprehendidos,
            valor_periodo_b=self.periodo_b.total_aprehendidos,
            diferencia=diff,
            porcentaje=pct,
            tendencia=tend
        )
        
        # Total mencionados
        diff, pct, tend = self._calcular_variacion(
            self.periodo_a.total_mencionados,
            self.periodo_b.total_mencionados
        )
        indicadores['total_mencionados'] = ComparacionItem(
            categoria="Total Mencionados",
            valor_periodo_a=self.periodo_a.total_mencionados,
            valor_periodo_b=self.periodo_b.total_mencionados,
            diferencia=diff,
            porcentaje=pct,
            tendencia=tend
        )
        
        # Esclarecidos
        escl_a = self.periodo_a.conteo_esclarecimiento()
        escl_b = self.periodo_b.conteo_esclarecimiento()
        total_escl_a = sum(v for k, v in escl_a.items() if k != 'NO_ESCLARECIDO')
        total_escl_b = sum(v for k, v in escl_b.items() if k != 'NO_ESCLARECIDO')
        diff, pct, tend = self._calcular_variacion(total_escl_a, total_escl_b)
        indicadores['total_esclarecidos'] = ComparacionItem(
            categoria="Hechos Esclarecidos",
            valor_periodo_a=total_escl_a,
            valor_periodo_b=total_escl_b,
            diferencia=diff,
            porcentaje=pct,
            tendencia=tend
        )
        
        return indicadores
    
    def to_comparison_table(self) -> List[Dict[str, Any]]:
        """
        Genera tabla de comparación general para el reporte.
        
        Returns:
            Lista de filas para la tabla comparativa.
        """
        resumen = self.resumen_general()
        
        filas = []
        orden = [
            'total_hechos',
            'total_robos', 
            'total_hurtos',
            'total_esclarecidos',
            'total_aprehendidos',
            'total_mencionados'
        ]
        
        for key in orden:
            if key in resumen:
                item = resumen[key]
                filas.append({
                    'indicador': item.categoria,
                    self.periodo_a.rango_fechas: item.valor_periodo_a,
                    self.periodo_b.rango_fechas: item.valor_periodo_b,
                    'diferencia': f"{'+' if item.diferencia > 0 else ''}{item.diferencia}",
                    'variacion': f"{item.porcentaje_formateado} {item.tendencia_icono}",
                    'color': item.tendencia_color
                })
        
        return filas


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARADOR MULTI-PERÍODO (2-4 períodos)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MultiComparacionItem:
    """Resultado de comparación para un ítem contra múltiples períodos."""
    categoria: str
    valores: List[int]  # Valores por período [P1, P2, P3, P4...]
    diferencias: List[int]  # Diferencias vs P1 [0, P2-P1, P3-P1, P4-P1...]
    porcentajes: List[float]  # Porcentajes vs P1
    tendencias: List[Tendencia]  # Tendencias vs P1
    
    def get_valor(self, idx: int) -> int:
        """Obtiene valor para período específico."""
        return self.valores[idx] if idx < len(self.valores) else 0
    
    def get_diferencia(self, idx: int) -> int:
        """Obtiene diferencia vs P1 para período específico."""
        return self.diferencias[idx] if idx < len(self.diferencias) else 0
    
    def get_porcentaje(self, idx: int) -> float:
        """Obtiene porcentaje vs P1 para período específico."""
        return self.porcentajes[idx] if idx < len(self.porcentajes) else 0.0
    
    def get_tendencia(self, idx: int) -> Tendencia:
        """Obtiene tendencia vs P1 para período específico."""
        return self.tendencias[idx] if idx < len(self.tendencias) else Tendencia.IGUAL
    
    def porcentaje_formateado(self, idx: int) -> str:
        """Porcentaje formateado con signo para un período."""
        if idx == 0:
            return "-"  # P1 es la referencia
        tend = self.get_tendencia(idx)
        if tend == Tendencia.NUEVO:
            return "NUEVO"
        pct = self.get_porcentaje(idx)
        signo = "+" if pct > 0 else ""
        return f"{signo}{pct:.2f}%"
    
    def diferencia_formateada(self, idx: int) -> str:
        """Diferencia formateada con signo."""
        if idx == 0:
            return "-"  # P1 es la referencia
        diff = self.get_diferencia(idx)
        signo = "+" if diff > 0 else ""
        return f"{signo}{diff}"
    
    def tendencia_icono(self, idx: int) -> str:
        """Icono de tendencia para un período."""
        if idx == 0:
            return ""
        iconos = {
            Tendencia.SUBIO: "▲",
            Tendencia.BAJO: "▼",
            Tendencia.IGUAL: "─",
            Tendencia.NUEVO: "★"
        }
        return iconos.get(self.get_tendencia(idx), "")
    
    def tendencia_color(self, idx: int) -> str:
        """Color de tendencia para un período."""
        if idx == 0:
            return "#808080"
        colores = {
            Tendencia.SUBIO: "#FF3B3B",   # Rojo (malo)
            Tendencia.BAJO: "#00FF88",     # Verde (bueno)
            Tendencia.IGUAL: "#808080",    # Gris
            Tendencia.NUEVO: "#FFaa00"     # Naranja
        }
        return colores.get(self.get_tendencia(idx), "#808080")


class MultiPeriodComparator:
    """
    Comparador para múltiples períodos (2-4).
    
    Compara todos los períodos contra el período principal (P1).
    Las variaciones y diferencias se calculan respecto a P1.
    """
    
    def __init__(self, periodos: List['PeriodData']):
        """
        Inicializa el comparador multi-período.
        
        Args:
            periodos: Lista de períodos (mínimo 2, máximo 4).
                      El primero es el principal (referencia).
        """
        if len(periodos) < 2:
            raise ValueError("Se requieren al menos 2 períodos para comparar")
        if len(periodos) > 4:
            raise ValueError("Máximo 4 períodos permitidos")
        
        self.periodos = periodos
        self.num_periodos = len(periodos)
        self.periodo_principal = periodos[0]
    
    def _calcular_variacion_vs_principal(
        self,
        valor_principal: int,
        valor_comparar: int
    ) -> Tuple[int, float, Tendencia]:
        """
        Calcula variación de un valor respecto al período principal.
        
        Returns:
            (diferencia, porcentaje, tendencia)
        """
        diferencia = valor_comparar - valor_principal
        
        if valor_principal == 0:
            if valor_comparar > 0:
                return diferencia, 100.0, Tendencia.NUEVO
            else:
                return 0, 0.0, Tendencia.IGUAL
        
        porcentaje = ((valor_comparar - valor_principal) / valor_principal) * 100
        
        if diferencia > 0:
            tendencia = Tendencia.SUBIO
        elif diferencia < 0:
            tendencia = Tendencia.BAJO
        else:
            tendencia = Tendencia.IGUAL
        
        return diferencia, round(porcentaje, 2), tendencia
    
    def _comparar_conteos_multi(
        self,
        conteos: List[Dict[str, int]]
    ) -> List[MultiComparacionItem]:
        """
        Compara diccionarios de conteos de múltiples períodos.
        
        Args:
            conteos: Lista de diccionarios de conteo, uno por período.
        
        Returns:
            Lista de MultiComparacionItem ordenada por valor del período principal.
        """
        # Obtener todas las claves únicas
        todas_claves = set()
        for conteo in conteos:
            todas_claves.update(conteo.keys())
        todas_claves = sorted(todas_claves)
        
        resultados = []
        
        for clave in todas_claves:
            valores = []
            diferencias = []
            porcentajes = []
            tendencias = []
            
            valor_p1 = conteos[0].get(clave, 0)
            
            for i, conteo in enumerate(conteos):
                valor = conteo.get(clave, 0)
                valores.append(valor)
                
                if i == 0:
                    # Período principal - es la referencia
                    diferencias.append(0)
                    porcentajes.append(0.0)
                    tendencias.append(Tendencia.IGUAL)
                else:
                    # Comparar vs período principal
                    diff, pct, tend = self._calcular_variacion_vs_principal(valor_p1, valor)
                    diferencias.append(diff)
                    porcentajes.append(pct)
                    tendencias.append(tend)
            
            resultados.append(MultiComparacionItem(
                categoria=clave,
                valores=valores,
                diferencias=diferencias,
                porcentajes=porcentajes,
                tendencias=tendencias
            ))
        
        # Ordenar por valor del período principal (descendente)
        return sorted(resultados, key=lambda x: -x.valores[0])
    
    # ═══════════════════════════════════════════════════════════════════════
    # COMPARACIONES ESPECÍFICAS
    # ═══════════════════════════════════════════════════════════════════════
    
    def comparar_delitos(self) -> List[MultiComparacionItem]:
        """Compara delitos entre todos los períodos."""
        conteos = [p.conteo_por_delito() for p in self.periodos]
        return self._comparar_conteos_multi(conteos)
    
    def comparar_categorias(self) -> List[MultiComparacionItem]:
        """Compara categorías entre todos los períodos."""
        conteos = [p.conteo_por_categoria() for p in self.periodos]
        return self._comparar_conteos_multi(conteos)
    
    def comparar_dias_semana(self) -> List[MultiComparacionItem]:
        """Compara días de la semana entre todos los períodos."""
        conteos = [p.conteo_por_dia_semana() for p in self.periodos]
        return self._comparar_conteos_multi(conteos)
    
    def comparar_franjas_horarias(self) -> List[MultiComparacionItem]:
        """Compara franjas horarias entre todos los períodos."""
        conteos = [p.conteo_por_franja_horaria() for p in self.periodos]
        return self._comparar_conteos_multi(conteos)
    
    def comparar_movilidad(self) -> List[MultiComparacionItem]:
        """Compara medios de movilidad entre todos los períodos."""
        conteos = [p.conteo_por_movilidad() for p in self.periodos]
        return self._comparar_conteos_multi(conteos)
    
    def comparar_armas(self) -> List[MultiComparacionItem]:
        """Compara armas/medios entre todos los períodos."""
        conteos = [p.conteo_por_arma() for p in self.periodos]
        return self._comparar_conteos_multi(conteos)
    
    def comparar_ambitos(self) -> List[MultiComparacionItem]:
        """Compara ámbitos de ocurrencia entre todos los períodos."""
        conteos = [p.conteo_por_ambito() for p in self.periodos]
        return self._comparar_conteos_multi(conteos)
    
    def comparar_esclarecimiento(self) -> List[MultiComparacionItem]:
        """Compara estados de esclarecimiento entre todos los períodos."""
        conteos = [p.conteo_esclarecimiento() for p in self.periodos]
        return self._comparar_conteos_multi(conteos)
    
    def comparar_aprehendidos(self) -> List[MultiComparacionItem]:
        """Compara clasificación de aprehendidos entre todos los períodos."""
        conteos = [p.conteo_aprehendidos_clasificacion() for p in self.periodos]
        return self._comparar_conteos_multi(conteos)
    
    # ═══════════════════════════════════════════════════════════════════════
    # RESUMEN Y TABLA GENERAL
    # ═══════════════════════════════════════════════════════════════════════
    
    def resumen_general(self) -> Dict[str, MultiComparacionItem]:
        """
        Genera resumen general de indicadores clave.
        
        Returns:
            Diccionario con indicadores comparados multi-período.
        """
        indicadores = {}
        
        # Total hechos
        valores = [p.total_hechos for p in self.periodos]
        indicadores['total_hechos'] = self._crear_item_resumen("Total Delitos", valores)
        
        # Total robos
        valores = [p.conteo_por_categoria().get('ROBOS', 0) for p in self.periodos]
        indicadores['total_robos'] = self._crear_item_resumen("Total Robos", valores)
        
        # Total hurtos
        valores = [p.conteo_por_categoria().get('HURTOS', 0) for p in self.periodos]
        indicadores['total_hurtos'] = self._crear_item_resumen("Total Hurtos", valores)
        
        # Total aprehendidos
        valores = [p.total_aprehendidos for p in self.periodos]
        indicadores['total_aprehendidos'] = self._crear_item_resumen("Total Aprehendidos", valores)
        
        # Total mencionados
        valores = [p.total_mencionados for p in self.periodos]
        indicadores['total_mencionados'] = self._crear_item_resumen("Total Mencionados", valores)
        
        # Esclarecidos
        valores = []
        for p in self.periodos:
            escl = p.conteo_esclarecimiento()
            total = sum(v for k, v in escl.items() if k != 'NO_ESCLARECIDO')
            valores.append(total)
        indicadores['total_esclarecidos'] = self._crear_item_resumen("Hechos Esclarecidos", valores)
        
        return indicadores
    
    def _crear_item_resumen(self, categoria: str, valores: List[int]) -> MultiComparacionItem:
        """Crea un MultiComparacionItem a partir de valores."""
        diferencias = [0]  # P1 es referencia
        porcentajes = [0.0]
        tendencias = [Tendencia.IGUAL]
        
        for i in range(1, len(valores)):
            diff, pct, tend = self._calcular_variacion_vs_principal(valores[0], valores[i])
            diferencias.append(diff)
            porcentajes.append(pct)
            tendencias.append(tend)
        
        return MultiComparacionItem(
            categoria=categoria,
            valores=valores,
            diferencias=diferencias,
            porcentajes=porcentajes,
            tendencias=tendencias
        )
    
    def to_comparison_table(self) -> List[Dict[str, Any]]:
        """
        Genera tabla de comparación general multi-período.
        
        Returns:
            Lista de filas para la tabla comparativa.
        """
        resumen = self.resumen_general()
        
        filas = []
        orden = [
            'total_hechos',
            'total_robos',
            'total_hurtos',
            'total_esclarecidos',
            'total_aprehendidos',
            'total_mencionados'
        ]
        
        for key in orden:
            if key in resumen:
                item = resumen[key]
                fila = {'indicador': item.categoria}
                
                # Agregar columnas por período
                for i, periodo in enumerate(self.periodos):
                    fila[periodo.rango_fechas] = item.valores[i]
                
                # Agregar columnas de diferencia y variación (solo para P2, P3, P4)
                for i in range(1, self.num_periodos):
                    periodo = self.periodos[i]
                    fila[f'Dif. P{i+1}'] = item.diferencia_formateada(i)
                    fila[f'Var. P{i+1}'] = f"{item.porcentaje_formateado(i)} {item.tendencia_icono(i)}"
                
                filas.append(fila)
        
        return filas
    
    def get_nombres_periodos(self) -> List[str]:
        """Obtiene los nombres/rangos de todos los períodos."""
        return [p.rango_fechas for p in self.periodos]
