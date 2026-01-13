"""
Generador de tablas/cuadros para reportes.

Genera todas las tablas estadísticas con formato adecuado
para exportación a Excel y Word.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd

from ..models.report_data import PeriodData, ReportData
from ..core.period_comparator import PeriodComparator, MultiPeriodComparator
from ..utils.constants import (
    DIAS_SEMANA,
    FranjaHoraria,
    SIMBOLOS_DELITOS,
    SimboloDelito,
)


@dataclass
class TableConfig:
    """Configuración para generación de tabla."""
    titulo: str
    incluir_porcentaje: bool = True
    incluir_total: bool = True
    incluir_grafico: bool = True
    ordenar_por_valor: bool = True


class TableGenerator:
    """
    Generador de tablas estadísticas para reportes S.I.D.I.C.
    
    Genera todas las tablas necesarias con formato consistente.
    """
    
    def __init__(self, report_data: ReportData):
        """
        Inicializa el generador.
        
        Args:
            report_data: Datos del reporte a generar.
        """
        self.report = report_data
        self.periodo = report_data.periodo_principal
    
    # ═══════════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════════════════
    
    def _calcular_porcentaje(self, valor: int, total: int) -> float:
        """Calcula porcentaje con manejo de división por cero."""
        if total == 0:
            return 0.0
        return round((valor / total) * 100, 2)
    
    def _format_porcentaje(self, valor: float) -> str:
        """Formatea porcentaje para mostrar."""
        return f"{valor:.2f}%"
    
    def _conteo_a_dataframe(
        self,
        conteo: Dict[str, int],
        columna_nombre: str,
        columna_valor: str,
        ordenar: bool = True
    ) -> pd.DataFrame:
        """
        Convierte un diccionario de conteo a DataFrame.
        """
        items = list(conteo.items())
        if ordenar:
            items = sorted(items, key=lambda x: -x[1])
        
        total = sum(conteo.values())
        
        data = []
        for nombre, valor in items:
            data.append({
                columna_nombre: nombre,
                columna_valor: valor,
                'Porcentaje': self._format_porcentaje(
                    self._calcular_porcentaje(valor, total)
                )
            })
        
        # Agregar fila de total
        data.append({
            columna_nombre: 'TOTAL',
            columna_valor: total,
            'Porcentaje': '100,00%'
        })
        
        return pd.DataFrame(data)
    
    def _generar_tabla_comparativa_multi(
        self,
        titulo_columna: str,
        comparaciones: list,
        totales: list = None,
        total_label: str = 'TOTAL'
    ) -> pd.DataFrame:
        """
        Genera una tabla comparativa para múltiples períodos (2-4).
        
        Args:
            titulo_columna: Nombre de la primera columna (categoría)
            comparaciones: Lista de MultiComparacionItem
            totales: Lista opcional de totales por período [total_p1, total_p2, ...]
        
        Returns:
            DataFrame con columnas dinámicas según cantidad de períodos
        """
        periodos = self.report.periodos
        num_periodos = len(periodos)
        
        data = []
        
        for comp in comparaciones:
            fila = {titulo_columna: comp.categoria.replace('_', ' ')}
            
            # Agregar valores de cada período
            for i, p in enumerate(periodos):
                fila[p.rango_fechas] = comp.valores[i]
            
            # Columnas de diferencia y variación
            if num_periodos == 2:
                # Para 2 períodos: columnas simples Dif. y Var.%
                fila['Dif.'] = comp.diferencia_formateada(1)
                fila['Var.%'] = f"{comp.porcentaje_formateado(1)} {comp.tendencia_icono(1)}"
            else:
                # Para 3-4 períodos: columnas separadas por período
                for i in range(1, num_periodos):
                    fila[f'Dif. P{i+1}'] = comp.diferencia_formateada(i)
                    fila[f'Var. P{i+1}'] = f"{comp.porcentaje_formateado(i)} {comp.tendencia_icono(i)}"
            
            data.append(fila)
        
        # Agregar fila de total si se proporcionan totales
        if totales and len(totales) == num_periodos:
            fila_total = {titulo_columna: total_label}
            
            for i, p in enumerate(periodos):
                fila_total[p.rango_fechas] = totales[i]
            
            if num_periodos == 2:
                diff = totales[1] - totales[0]
                pct = ((totales[1] - totales[0]) / totales[0] * 100) if totales[0] > 0 else 0
                signo_d = "+" if diff > 0 else ""
                signo_p = "+" if pct > 0 else ""
                icono = "▲" if diff > 0 else ("▼" if diff < 0 else "─")
                fila_total['Dif.'] = f"{signo_d}{diff}"
                fila_total['Var.%'] = f"{signo_p}{pct:.2f}% {icono}"
            else:
                for i in range(1, num_periodos):
                    diff = totales[i] - totales[0]
                    pct = ((totales[i] - totales[0]) / totales[0] * 100) if totales[0] > 0 else 0
                    signo_d = "+" if diff > 0 else ""
                    signo_p = "+" if pct > 0 else ""
                    icono = "▲" if diff > 0 else ("▼" if diff < 0 else "─")
                    fila_total[f'Dif. P{i+1}'] = f"{signo_d}{diff}"
                    fila_total[f'Var. P{i+1}'] = f"{signo_p}{pct:.2f}% {icono}"
            
            data.append(fila_total)
        
        return pd.DataFrame(data)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CUADRO DE REFERENCIA (Layout 2 columnas: Consumados | Tentativas)
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_cuadro_referencia(self) -> pd.DataFrame:
        """
        Genera el cuadro de referencia para mapas.
        
        Incluye símbolos, categorías, subtotales y totales.
        Formato agrupado por categoría (ROBOS, TENTATIVAS, HURTOS, etc.)
        """
        if not self.periodo:
            return pd.DataFrame()
        
        filas = self.periodo.cuadro_referencia()
        
        data = []
        for fila in filas:
            tipo = fila['tipo']
            texto = fila['texto']
            cantidad = fila['cantidad']
            
            # Obtener símbolo si es delito
            simbolo = ""
            color = ""
            if tipo == 'delito':
                # Buscar símbolo con múltiples variaciones
                simbolo, color = self._buscar_simbolo_delito(texto)
            elif tipo == 'indicacion':
                if 'ESCLARECIDO' in texto.upper():
                    simbolo = "○"
                    color = "#00FF00"
                else:
                    simbolo = "○"
                    color = "#FFFFFF"
            elif tipo == 'comisaria':
                simbolo = "Ⓟ"
                color = "#0000FF"
            
            data.append({
                'Símbolo': simbolo,
                'Tipo': tipo,
                'Descripción': texto.replace('_', ' '),
                'Cantidad': cantidad if cantidad is not None else '',
                'Color': color
            })
        
        return pd.DataFrame(data)
    
    def _buscar_simbolo_delito(self, texto: str) -> tuple:
        """
        Busca el símbolo y color para un delito.
        
        Intenta múltiples variaciones del nombre para encontrar coincidencia.
        Usa símbolos ASCII compatibles con Excel/Word.
        
        Returns:
            Tupla (simbolo, color)
        """
        from ..core.field_mapper import normalizar_delito
        
        # Variaciones a probar
        variaciones = [
            texto,  # Original
            texto.replace('_', ' '),  # Sin guiones bajos
            texto.replace(' ', '_'),  # Con guiones bajos
            normalizar_delito(texto),  # Normalizado
            normalizar_delito(texto.replace('_', ' ')),  # Normalizado sin guiones
        ]
        
        # Buscar en cada variación
        for variacion in variaciones:
            if variacion in SIMBOLOS_DELITOS:
                sim = SIMBOLOS_DELITOS[variacion]
                return sim.simbolo, sim.color
        
        # Búsqueda parcial como último recurso
        texto_upper = texto.upper().replace('_', ' ')
        for key, sim in SIMBOLOS_DELITOS.items():
            key_clean = key.replace('_', ' ')
            if key_clean in texto_upper or texto_upper in key_clean:
                return sim.simbolo, sim.color
        
        # Símbolo genérico basado en tipo de delito (ASCII compatible)
        texto_upper = texto.upper()
        if 'TENTATIVA' in texto_upper:
            if 'ROBO' in texto_upper:
                return "a", "#FF0000"  # Tentativa de robo - triángulo vacío rojo
            elif 'HURTO' in texto_upper:
                return "o", "#0000FF"  # Tentativa de hurto - círculo vacío azul
            else:
                return "d", "#808080"  # Otra tentativa
        elif 'ROBO' in texto_upper:
            return "A", "#FF0000"  # Robo - triángulo relleno rojo
        elif 'HURTO' in texto_upper:
            return "O", "#0000FF"  # Hurto - círculo relleno azul
        elif 'ESTAFA' in texto_upper:
            return "D", "#00FF00"  # Estafa - rombo verde
        else:
            return "X", "#808080"  # Genérico
    
    def generar_cuadro_referencia_doble_columna(self) -> pd.DataFrame:
        """
        Genera el cuadro de referencia con layout de 2 columnas.
        
        Columna izquierda: Delitos consumados
        Columna derecha: Tentativas correspondientes
        
        Returns:
            DataFrame con columnas:
            - Símbolo_Consumado, Delito_Consumado, Cant_Consumado, Color_Consumado
            - Símbolo_Tentativa, Delito_Tentativa, Cant_Tentativa, Color_Tentativa
        """
        from ..utils.constants import ORDEN_DELITOS_CONSUMADOS, ORDEN_DELITOS_TENTATIVAS
        from ..core.field_mapper import normalizar_delito
        
        if not self.periodo:
            return pd.DataFrame()
        
        # Obtener conteo de delitos
        conteo = self.periodo.conteo_por_delito()
        
        # Normalizar claves del conteo
        conteo_normalizado = {}
        for k, v in conteo.items():
            k_norm = normalizar_delito(k)
            if k_norm in conteo_normalizado:
                conteo_normalizado[k_norm] += v
            else:
                conteo_normalizado[k_norm] = v
        
        data = []
        
        # Iterar sobre las listas ordenadas
        for i, delito_cons in enumerate(ORDEN_DELITOS_CONSUMADOS):
            delito_tent = ORDEN_DELITOS_TENTATIVAS[i] if i < len(ORDEN_DELITOS_TENTATIVAS) else ""
            
            # Consumado
            sim_cons = SIMBOLOS_DELITOS.get(delito_cons)
            cant_cons = conteo_normalizado.get(delito_cons, 0)
            
            # Tentativa
            sim_tent = SIMBOLOS_DELITOS.get(delito_tent)
            cant_tent = conteo_normalizado.get(delito_tent, 0)
            
            row = {
                'Símbolo': sim_cons.simbolo if sim_cons else '',
                'Delito Consumado': delito_cons.replace('_', ' '),
                'Cant': cant_cons,
                'Color': sim_cons.color if sim_cons else '',
                'Símbolo_T': sim_tent.simbolo if sim_tent else '',
                'Tentativa': delito_tent.replace('TENTATIVA DE ', '').replace('_', ' ') if delito_tent else '',
                'Cant_T': cant_tent,
                'Color_T': sim_tent.color if sim_tent else '',
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    # ═══════════════════════════════════════════════════════════════════════
    # DELITOS CON MODALIDADES
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_delitos(self) -> pd.DataFrame:
        """
        Genera tabla de delitos con modalidades.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        conteo = self.periodo.conteo_por_delito()
        
        return self._conteo_a_dataframe(
            conteo,
            'DELITOS CON MODALIDADES',
            self.periodo.rango_fechas
        )
    
    def generar_tabla_delitos_comparativa(self) -> pd.DataFrame:
        """
        Genera tabla comparativa de delitos entre múltiples períodos (2-4).
        
        Columnas: Categoría | P1 | P2 | [P3] | [P4] | Dif P2 | Var P2 | [Dif P3] | [Var P3] | [Dif P4] | [Var P4]
        """
        if not self.report.es_comparativo:
            return self.generar_tabla_delitos()
        
        periodos = self.report.periodos
        if len(periodos) < 2:
            return self.generar_tabla_delitos()
        
        try:
            comparator = MultiPeriodComparator(periodos)
            comparaciones = comparator.comparar_delitos()
            totales = [p.total_hechos for p in periodos]
            return self._generar_tabla_comparativa_multi(
                'DELITOS CON MODALIDADES',
                comparaciones,
                totales=totales,
                total_label='TOTAL DE HECHOS'
            )
        
        except Exception as e:
            print(f"Error generando tabla comparativa de delitos: {e}")
            return self.generar_tabla_delitos()
    
    # ═══════════════════════════════════════════════════════════════════════
    # DÍAS DE LA SEMANA
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_dias_semana(self) -> pd.DataFrame:
        """
        Genera tabla de hechos por día de la semana.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        conteo = self.periodo.conteo_por_dia_semana()
        
        # Ordenar por cantidad, no por día
        return self._conteo_a_dataframe(
            conteo,
            'DÍAS DE LA SEMANA EN QUE OCURRIERON LOS HECHOS',
            self.periodo.rango_fechas
        )
    
    def generar_tabla_dias_semana_comparativa(self) -> pd.DataFrame:
        """
        Genera tabla comparativa de hechos por día de la semana entre múltiples períodos (2-4).
        """
        if not self.report.es_comparativo:
            return self.generar_tabla_dias_semana()
        
        periodos = self.report.periodos
        if len(periodos) < 2:
            return self.generar_tabla_dias_semana()
        
        try:
            comparator = MultiPeriodComparator(periodos)
            comparaciones = comparator.comparar_dias_semana()
            
            # Calcular totales por período
            totales = [sum(comp.valores[i] for comp in comparaciones) for i in range(len(periodos))]
            
            return self._generar_tabla_comparativa_multi(
                'DÍAS DE LA SEMANA EN QUE OCURRIERON LOS HECHOS',
                comparaciones,
                totales
            )
        except Exception as e:
            print(f"Error generando tabla comparativa días semana: {e}")
            return self.generar_tabla_dias_semana()
    
    # ═══════════════════════════════════════════════════════════════════════
    # FRANJA HORARIA
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_franja_horaria(self) -> pd.DataFrame:
        """
        Genera tabla de hechos por franja horaria.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        conteo = self.periodo.conteo_por_franja_horaria()
        
        return self._conteo_a_dataframe(
            conteo,
            'FRANJA HORARIA EN QUE OCURRIERON LOS HECHOS',
            self.periodo.rango_fechas
        )
    
    def generar_tabla_franja_horaria_comparativa(self) -> pd.DataFrame:
        """
        Genera tabla comparativa de hechos por franja horaria entre múltiples períodos (2-4).
        """
        if not self.report.es_comparativo:
            return self.generar_tabla_franja_horaria()
        
        periodos = self.report.periodos
        if len(periodos) < 2:
            return self.generar_tabla_franja_horaria()
        
        try:
            comparator = MultiPeriodComparator(periodos)
            comparaciones = comparator.comparar_franjas_horarias()
            
            # Calcular totales por período
            totales = [sum(comp.valores[i] for comp in comparaciones) for i in range(len(periodos))]
            
            return self._generar_tabla_comparativa_multi(
                'FRANJA HORARIA EN QUE OCURRIERON LOS HECHOS',
                comparaciones,
                totales
            )
        except Exception as e:
            print(f"Error generando tabla comparativa franja horaria: {e}")
            return self.generar_tabla_franja_horaria()
    
    # ═══════════════════════════════════════════════════════════════════════
    # MOVILIDAD
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_movilidad(self) -> pd.DataFrame:
        """
        Genera tabla de medios de movilidad utilizados.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        conteo = self.periodo.conteo_por_movilidad()
        
        return self._conteo_a_dataframe(
            conteo,
            'MEDIOS DE MOVILIDAD UTILIZADOS',
            self.periodo.rango_fechas
        )
    
    def generar_tabla_movilidad_comparativa(self) -> pd.DataFrame:
        """
        Genera tabla comparativa de medios de movilidad entre múltiples períodos (2-4).
        """
        if not self.report.es_comparativo:
            return self.generar_tabla_movilidad()
        
        periodos = self.report.periodos
        if len(periodos) < 2:
            return self.generar_tabla_movilidad()
        
        try:
            comparator = MultiPeriodComparator(periodos)
            comparaciones = comparator.comparar_movilidad()
            
            # Calcular totales por período
            totales = [sum(comp.valores[i] for comp in comparaciones) for i in range(len(periodos))]
            
            return self._generar_tabla_comparativa_multi(
                'MEDIOS DE MOVILIDAD UTILIZADOS',
                comparaciones,
                totales
            )
        except Exception as e:
            print(f"Error generando tabla comparativa movilidad: {e}")
            return self.generar_tabla_movilidad()
    
    # ═══════════════════════════════════════════════════════════════════════
    # ARMAS EN ROBOS AGRAVADOS
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_armas(self) -> pd.DataFrame:
        """
        Genera tabla de armas/medios en robos agravados.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        conteo = self.periodo.conteo_por_arma()
        
        if not conteo or sum(conteo.values()) == 0:
            return pd.DataFrame({
                'MEDIOS O ARMAS UTILIZADAS EN ROBOS AGRAVADOS': ['Sin datos'],
                self.periodo.rango_fechas: [0],
                'Porcentaje': ['0,00%']
            })
        
        return self._conteo_a_dataframe(
            conteo,
            'MEDIOS O ARMAS UTILIZADAS EN ROBOS AGRAVADOS',
            self.periodo.rango_fechas
        )
    
    def generar_tabla_armas_comparativa(self) -> pd.DataFrame:
        """
        Genera tabla comparativa de armas/medios entre múltiples períodos (2-4).
        """
        if not self.report.es_comparativo:
            return self.generar_tabla_armas()
        
        periodos = self.report.periodos
        if len(periodos) < 2:
            return self.generar_tabla_armas()
        
        try:
            comparator = MultiPeriodComparator(periodos)
            comparaciones = comparator.comparar_armas()
            
            if not comparaciones:
                return self.generar_tabla_armas()
            
            # Calcular totales por período
            totales = [sum(comp.valores[i] for comp in comparaciones) for i in range(len(periodos))]
            
            return self._generar_tabla_comparativa_multi(
                'MEDIOS O ARMAS UTILIZADAS EN ROBOS AGRAVADOS',
                comparaciones,
                totales
            )
        except Exception as e:
            print(f"Error generando tabla comparativa armas: {e}")
            return self.generar_tabla_armas()
    
    # ═══════════════════════════════════════════════════════════════════════
    # ÁMBITO DE OCURRENCIA
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_ambito(self) -> pd.DataFrame:
        """
        Genera tabla de ámbito de ocurrencia delictual.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        conteo = self.periodo.conteo_por_ambito()
        
        return self._conteo_a_dataframe(
            conteo,
            'AMBITO DE OCURRENCIA DELICTUAL',
            self.periodo.rango_fechas
        )
    
    def generar_tabla_ambito_comparativa(self) -> pd.DataFrame:
        """
        Genera tabla comparativa de ámbito de ocurrencia entre múltiples períodos (2-4).
        """
        if not self.report.es_comparativo:
            return self.generar_tabla_ambito()
        
        periodos = self.report.periodos
        if len(periodos) < 2:
            return self.generar_tabla_ambito()
        
        try:
            comparator = MultiPeriodComparator(periodos)
            comparaciones = comparator.comparar_ambitos()
            
            # Calcular totales por período
            totales = [sum(comp.valores[i] for comp in comparaciones) for i in range(len(periodos))]
            
            return self._generar_tabla_comparativa_multi(
                'AMBITO DE OCURRENCIA DELICTUAL',
                comparaciones,
                totales
            )
        except Exception as e:
            print(f"Error generando tabla comparativa ámbito: {e}")
            return self.generar_tabla_ambito()
    
    # ═══════════════════════════════════════════════════════════════════════
    # MATRICES (DELITO × DIMENSIÓN)
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_matriz_delito_dia(self) -> pd.DataFrame:
        """
        Genera matriz de delitos CON MODALIDAD por día de la semana.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        # Usar matriz con modalidades
        matriz = self.periodo.matriz_delito_modalidad_dia()
        
        if not matriz:
            return pd.DataFrame()
        
        # Construir DataFrame
        data = []
        for delito, dias in sorted(matriz.items()):
            fila = {'DELITO': delito.replace('_', ' ')}
            total_delito = 0
            for dia in DIAS_SEMANA:
                valor = dias.get(dia, 0)
                fila[dia[:3].upper()] = valor  # LUN, MAR, MIÉ...
                total_delito += valor
            fila['TOTAL DELITO'] = total_delito
            data.append(fila)
        
        # Fila de totales por día
        fila_total = {'DELITO': 'TOTAL POR DÍA'}
        total_general = 0
        for dia in DIAS_SEMANA:
            total_dia = sum(dias.get(dia, 0) for dias in matriz.values())
            fila_total[dia[:3].upper()] = total_dia
            total_general += total_dia
        fila_total['TOTAL DELITO'] = total_general
        data.append(fila_total)
        
        return pd.DataFrame(data)
    
    def generar_matriz_delito_franja(self) -> pd.DataFrame:
        """
        Genera matriz de delitos CON MODALIDAD por franja horaria.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        # Usar matriz con modalidades
        matriz = self.periodo.matriz_delito_modalidad_franja()
        
        if not matriz:
            return pd.DataFrame()
        
        # Nombres cortos de franjas
        franjas_cortas = {
            f.display_name: f.nombre[:6].upper()
            for f in FranjaHoraria
        }
        
        data = []
        for delito, franjas in sorted(matriz.items()):
            fila = {'DELITO': delito.replace('_', ' ')}
            total_delito = 0
            for franja_full, franja_corta in franjas_cortas.items():
                valor = franjas.get(franja_full, 0)
                fila[franja_corta] = valor
                total_delito += valor
            fila['TOTAL'] = total_delito
            data.append(fila)
        
        # Fila de totales
        fila_total = {'DELITO': 'TOTAL POR FRANJA'}
        total_general = 0
        for franja_full, franja_corta in franjas_cortas.items():
            total_franja = sum(franjas.get(franja_full, 0) for franjas in matriz.values())
            fila_total[franja_corta] = total_franja
            total_general += total_franja
        fila_total['TOTAL'] = total_general
        data.append(fila_total)
        
        return pd.DataFrame(data)
    
    # ═══════════════════════════════════════════════════════════════════════
    # MENCIONADOS
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_mencionados(self) -> pd.DataFrame:
        """
        Genera tabla de personas mencionadas.
        """
        if not self.periodo or not self.periodo.mencionados:
            return pd.DataFrame({
                '#': ['-'],
                'Alias': ['Sin mencionados en el período'],
                'Delito': ['-'],
                'Dirección': ['-'],
                'Fecha': ['-'],
                'Hora': ['-'],
                'Datos': ['-']
            })
        
        data = []
        for i, m in enumerate(self.periodo.mencionados, 1):
            row = m.to_report_row()
            row['#'] = i
            data.append(row)
        
        # Reordenar columnas
        df = pd.DataFrame(data)
        cols = ['#', 'Alias', 'Delito', 'Dirección del Hecho', 'Fecha', 'Hora', 'Datos Filiatorios']
        return df[[c for c in cols if c in df.columns]]
    
    # ═══════════════════════════════════════════════════════════════════════
    # APREHENDIDOS
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_aprehendidos(self) -> pd.DataFrame:
        """
        Genera tabla de personas aprehendidas.
        """
        if not self.periodo or not self.periodo.aprehendidos:
            return pd.DataFrame({
                '#': ['-'],
                'Nombre/Alias': ['Sin aprehendidos en el período'],
                'Clasificación': ['-'],
                'Delito': ['-'],
                'Fecha': ['-'],
                'Edad': ['-'],
                'Sexo': ['-']
            })
        
        data = []
        for i, a in enumerate(self.periodo.aprehendidos, 1):
            row = a.to_report_row()
            row['#'] = i
            data.append(row)
        
        df = pd.DataFrame(data)
        cols = ['#', 'Nombre/Alias', 'Clasificación', 'Delito', 'Fecha', 'Edad', 'Sexo']
        return df[[c for c in cols if c in df.columns]]
    
    def generar_tabla_aprehendidos_clasificacion(self) -> pd.DataFrame:
        """
        Genera resumen de aprehendidos por clasificación.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        conteo = self.periodo.conteo_aprehendidos_clasificacion()
        
        return self._conteo_a_dataframe(
            conteo,
            'CLASIFICACIÓN',
            'CANTIDAD'
        )
    
    def generar_tabla_aprehendidos_clasificacion_comparativa(self) -> pd.DataFrame:
        """
        Genera tabla comparativa de aprehendidos por clasificación entre múltiples períodos (2-4).
        """
        if not self.report.es_comparativo:
            return self.generar_tabla_aprehendidos_clasificacion()
        
        periodos = self.report.periodos
        if len(periodos) < 2:
            return self.generar_tabla_aprehendidos_clasificacion()
        
        try:
            comparator = MultiPeriodComparator(periodos)
            comparaciones = comparator.comparar_aprehendidos()
            
            if not comparaciones:
                return self.generar_tabla_aprehendidos_clasificacion()
            
            # Calcular totales por período
            totales = [sum(comp.valores[i] for comp in comparaciones) for i in range(len(periodos))]
            
            return self._generar_tabla_comparativa_multi(
                'CLASIFICACIÓN',
                comparaciones,
                totales
            )
        except Exception as e:
            print(f"Error generando tabla comparativa aprehendidos: {e}")
            return self.generar_tabla_aprehendidos_clasificacion()
    
    # ═══════════════════════════════════════════════════════════════════════
    # ESCLARECIMIENTO
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_esclarecimiento(self) -> pd.DataFrame:
        """
        Genera tabla de índice de esclarecimiento.
        """
        if not self.periodo:
            return pd.DataFrame()
        
        conteo = self.periodo.conteo_esclarecimiento()
        
        return self._conteo_a_dataframe(
            conteo,
            'ESTADO DE ESCLARECIMIENTO',
            'CANTIDAD'
        )
    
    def generar_tabla_esclarecimiento_comparativa(self) -> pd.DataFrame:
        """
        Genera tabla comparativa de esclarecimiento entre múltiples períodos (2-4).
        """
        if not self.report.es_comparativo:
            return self.generar_tabla_esclarecimiento()
        
        periodos = self.report.periodos
        if len(periodos) < 2:
            return self.generar_tabla_esclarecimiento()
        
        try:
            comparator = MultiPeriodComparator(periodos)
            comparaciones = comparator.comparar_esclarecimiento()
            
            # Calcular totales por período
            totales = [sum(comp.valores[i] for comp in comparaciones) for i in range(len(periodos))]
            
            return self._generar_tabla_comparativa_multi(
                'ESTADO DE ESCLARECIMIENTO',
                comparaciones,
                totales
            )
        except Exception as e:
            print(f"Error generando tabla comparativa esclarecimiento: {e}")
            return self.generar_tabla_esclarecimiento()
    
    # ═══════════════════════════════════════════════════════════════════════
    # CUADRO COMPARATIVO GENERAL
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_tabla_comparativa_general(self) -> pd.DataFrame:
        """
        Genera cuadro comparativo general entre múltiples períodos (2-4).
        """
        if not self.report.es_comparativo:
            return pd.DataFrame()
        
        periodos = self.report.periodos
        if len(periodos) < 2:
            return pd.DataFrame()
        
        try:
            comparator = MultiPeriodComparator(periodos)
            filas = comparator.to_comparison_table()
            
            if not filas:
                return pd.DataFrame()
            
            return pd.DataFrame(filas)
        
        except Exception as e:
            print(f"Error generando tabla comparativa general: {e}")
            return pd.DataFrame()
    
    # ═══════════════════════════════════════════════════════════════════════
    # GENERAR TODAS LAS TABLAS
    # ═══════════════════════════════════════════════════════════════════════
    
    def generar_todas(self) -> Dict[str, pd.DataFrame]:
        """
        Genera todas las tablas del reporte.
        
        Para reportes comparativos, genera automáticamente las versiones
        comparativas de todas las tablas que lo soporten.
        
        Returns:
            Diccionario {nombre_tabla: DataFrame}
        """
        tablas = {}
        es_comparativo = self.report.es_comparativo
        
        # Generar cada tabla con manejo de errores
        try:
            tablas['cuadro_referencia'] = self.generar_cuadro_referencia()
        except Exception as e:
            print(f"Error generando cuadro_referencia: {e}")
            tablas['cuadro_referencia'] = pd.DataFrame()
        
        # DELITOS - Comparativo si aplica
        try:
            if es_comparativo:
                tablas['delitos'] = self.generar_tabla_delitos_comparativa()
            else:
                tablas['delitos'] = self.generar_tabla_delitos()
        except Exception as e:
            print(f"Error generando tabla delitos: {e}")
            tablas['delitos'] = pd.DataFrame()
        
        # DÍAS SEMANA - Comparativo si aplica
        try:
            if es_comparativo:
                tablas['dias_semana'] = self.generar_tabla_dias_semana_comparativa()
            else:
                tablas['dias_semana'] = self.generar_tabla_dias_semana()
        except Exception as e:
            print(f"Error generando dias_semana: {e}")
            tablas['dias_semana'] = pd.DataFrame()
        
        # FRANJA HORARIA - Comparativo si aplica
        try:
            if es_comparativo:
                tablas['franja_horaria'] = self.generar_tabla_franja_horaria_comparativa()
            else:
                tablas['franja_horaria'] = self.generar_tabla_franja_horaria()
        except Exception as e:
            print(f"Error generando franja_horaria: {e}")
            tablas['franja_horaria'] = pd.DataFrame()
        
        # MOVILIDAD - Comparativo si aplica
        try:
            if es_comparativo:
                tablas['movilidad'] = self.generar_tabla_movilidad_comparativa()
            else:
                tablas['movilidad'] = self.generar_tabla_movilidad()
        except Exception as e:
            print(f"Error generando movilidad: {e}")
            tablas['movilidad'] = pd.DataFrame()
        
        # ARMAS - Comparativo si aplica
        try:
            if es_comparativo:
                tablas['armas'] = self.generar_tabla_armas_comparativa()
            else:
                tablas['armas'] = self.generar_tabla_armas()
        except Exception as e:
            print(f"Error generando armas: {e}")
            tablas['armas'] = pd.DataFrame()
        
        # ÁMBITO - Comparativo si aplica
        try:
            if es_comparativo:
                tablas['ambito'] = self.generar_tabla_ambito_comparativa()
            else:
                tablas['ambito'] = self.generar_tabla_ambito()
        except Exception as e:
            print(f"Error generando ambito: {e}")
            tablas['ambito'] = pd.DataFrame()
        
        # MATRICES - Por ahora solo período único (estructuras complejas)
        try:
            tablas['matriz_delito_dia'] = self.generar_matriz_delito_dia()
        except Exception as e:
            print(f"Error generando matriz_delito_dia: {e}")
            tablas['matriz_delito_dia'] = pd.DataFrame()
        
        try:
            tablas['matriz_delito_franja'] = self.generar_matriz_delito_franja()
        except Exception as e:
            print(f"Error generando matriz_delito_franja: {e}")
            tablas['matriz_delito_franja'] = pd.DataFrame()
        
        # MENCIONADOS - Lista detallada, no aplica comparativo
        try:
            tablas['mencionados'] = self.generar_tabla_mencionados()
        except Exception as e:
            print(f"Error generando mencionados: {e}")
            tablas['mencionados'] = pd.DataFrame()
        
        # APREHENDIDOS - Lista detallada, no aplica comparativo
        try:
            tablas['aprehendidos'] = self.generar_tabla_aprehendidos()
        except Exception as e:
            print(f"Error generando aprehendidos: {e}")
            tablas['aprehendidos'] = pd.DataFrame()
        
        # APREHENDIDOS CLASIFICACIÓN - Comparativo si aplica
        try:
            if es_comparativo:
                tablas['aprehendidos_clasificacion'] = self.generar_tabla_aprehendidos_clasificacion_comparativa()
            else:
                tablas['aprehendidos_clasificacion'] = self.generar_tabla_aprehendidos_clasificacion()
        except Exception as e:
            print(f"Error generando aprehendidos_clasificacion: {e}")
            tablas['aprehendidos_clasificacion'] = pd.DataFrame()
        
        # ESCLARECIMIENTO - Comparativo si aplica
        try:
            if es_comparativo:
                tablas['esclarecimiento'] = self.generar_tabla_esclarecimiento_comparativa()
            else:
                tablas['esclarecimiento'] = self.generar_tabla_esclarecimiento()
        except Exception as e:
            print(f"Error generando esclarecimiento: {e}")
            tablas['esclarecimiento'] = pd.DataFrame()
        
        # Tabla comparativa general solo para reportes comparativos
        if es_comparativo:
            try:
                tablas['comparativa_general'] = self.generar_tabla_comparativa_general()
            except Exception as e:
                print(f"Error generando comparativa_general: {e}")
                tablas['comparativa_general'] = pd.DataFrame()
        
        return tablas
