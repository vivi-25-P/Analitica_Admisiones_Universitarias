# Abrir el dashboard en Windows

Cada integrante necesita el repositorio completo, Power BI Desktop y Python. El modelo utiliza el Excel entregable y seis CSV del análisis administrativo. Docker no es necesario para este origen Excel.

Cierra el proyecto en Power BI antes de configurar su ruta. Desde PowerShell, situado en la raíz del repositorio, ejecuta:

```powershell
uv run python scripts/configurar_powerbi_windows.py
```

Si no utilizas uv, el configurador solo requiere la biblioteca estándar de Python:

```powershell
python scripts/configurar_powerbi_windows.py
```

Abre `DashboardAdmisiones/DashboardAdmisiones.pbip` desde esta carpeta y pulsa Actualizar. El configurador comprueba la presencia del Excel y los seis CSV y cambia únicamente el parámetro RutaProyecto. Conserva el diseño, las medidas y la caché. Si el proyecto ya estaba abierto, ciérralo antes de ejecutar el comando para que una sesión anterior no sobrescriba el archivo actualizado.

También puedes cambiar RutaProyecto desde Transformar datos, Administrar parámetros, indicando la carpeta raíz del repositorio en tu equipo. La función ArchivoProyecto añade las ubicaciones relativas de las siete fuentes. Se admiten espacios y carpetas de otras unidades. Cada persona configura su propia carpeta una vez y repite el ajuste si mueve el repositorio. El PBIP no detecta automáticamente dónde se encuentra el repositorio.

Para comprobar las fuentes sin modificar archivos:

```powershell
python scripts/configurar_powerbi_windows.py --comprobar
```

Antes de compartir cambios, revisa el diff: un cambio que contenga únicamente tu carpeta personal en RutaProyecto no debe incluirse en un commit compartido. Las credenciales y la caché local tampoco se versionan.

El generador `scripts/construir_dashboard_powerbi.py` reconstruye el proyecto y puede sustituir ajustes guardados desde Desktop. Úsalo solo cuando quieras regenerarlo deliberadamente. Para experimentar, proporciona `--destino` con otra carpeta. El argumento avanzado `--excel` admite un archivo externo, pero en ese caso su ubicación absoluta también debe estar disponible en el equipo receptor y el configurador estándar rechazará esa estructura, que espera las siete fuentes del repositorio.

Para trabajar en equipo se comparte el PBIP junto con sus carpetas Report y SemanticModel y las fuentes. Para una entrega con los datos importados, abre y actualiza el proyecto y guarda una copia PBIX desde Desktop. El receptor podrá consultar los datos importados, aunque necesitará configurar sus fuentes para actualizarlos.

## Después de recibir estos cambios

Cierra Power BI Desktop y PowerPoint antes de actualizar el repositorio. Revisa `git status` y conserva primero cualquier trabajo propio. Si Git indica cambios locales o conflictos, resuélvelos antes de continuar. Evita descartar archivos o guardar una sesión antigua de Power BI sobre los archivos recibidos.

Con el árbol de trabajo preparado, utiliza desde la raíz:

```powershell
git pull --ff-only
python scripts/configurar_powerbi_windows.py
python scripts/configurar_powerbi_windows.py --comprobar
```

El configurador funciona sin uv. Si tu instalación utiliza el lanzador de Windows, puedes sustituir `python` por `py`. Después abre `powerbi/DashboardAdmisiones/DashboardAdmisiones.pbip` y pulsa Actualizar. Comprueba como referencia general 5.500 registros, 1.179 Matriculado y 21,4 %. Las cifras cambian al aplicar los filtros correspondientes.

Si únicamente modificaste RutaProyecto en una sesión anterior, guarda ese cambio temporalmente con `git stash push -m "ruta local de Power BI" -- powerbi/DashboardAdmisiones/DashboardAdmisiones.SemanticModel/definition/expressions.tmdl`, realiza el pull y ejecuta de nuevo el configurador. No hace falta reaplicar el stash de esa ruta. Conserva el respaldo hasta comprobar que el proyecto abre. Esta instrucción solo aplica cuando ese archivo contiene exclusivamente tu cambio de ruta; los cambios de consultas deben revisarse como trabajo propio.

El proyecto incluye Inicio y seis páginas de análisis. Para la sustentación actual se utiliza la presentación terminada en `_v3.pptx`; la original y la v2 son respaldos conservados. Las notas orientan una exposición de trece minutos y los cuatro anexos están ocultos. No necesitas instalar el MCP para consultar el dashboard. Su configuración y la caché son locales.

## Formato guardado por Desktop

El proyecto actual utiliza PBIR: las páginas y los visuales están en `DashboardAdmisiones.Report/definition/`. Se versiona esa carpeta completa. Desktop sustituyó el antiguo report.json situado en la raíz del informe; el nuevo report.json dentro de definition contiene la configuración general.

El configurador de rutas sigue funcionando porque las consultas permanecen en el modelo TMDL. El generador completo rechaza un destino PBIR existente para proteger el trabajo guardado; solo puede generar una copia en otro destino. El script de filtros comprueba los segmentadores PBIR y conserva el ajuste actual. El script de portada reconoce Inicio sin duplicarlo. Para cambios nuevos de diseño en PBIR utiliza Desktop.
