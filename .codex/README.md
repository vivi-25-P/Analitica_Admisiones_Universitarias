# MCP local de Power BI

config.toml registra el ejecutable ya instalado mediante la extensión de VS Code. Es una configuración específica de este PC y del ejecutor WSL. Está excluida de Git y no contiene credenciales.

El servidor arranca en modo de solo lectura. La primera comprobación es descubrir el modelo abierto y consultar sus medidas. No se cambia el modelo, el PBIP o el PBIX con esta configuración.

Para cargar un servidor nuevo, reiniciar la conexión MCP o volver a abrir la sesión de Codex sobre este proyecto. Si el proyecto no está reconocido como confiable, Codex puede omitir su configuración local. No se cambia automáticamente la confianza del proyecto.

El formato permissions.allow no pertenece a la configuración de Codex. La selección de herramientas se expresa con enabled_tools y disabled_tools dentro de mcp_servers. Los nombres concretos deben comprobarse con tools/list antes de establecer una lista. Permitir una herramienta de operaciones no distingue por sí solo lecturas y escrituras.

El argumento --read-only debe conservarse durante las comprobaciones. Los cambios de modelo requieren una configuración de escritura posterior y una revisión del modelo concreto. La aceptación de la licencia del servidor es independiente de los permisos. En este equipo el usuario ya la autorizó y la configuración local utiliza --accept-eula. Cada integrante debe revisar y aceptar la licencia en su propia instalación. Para consultar el dashboard no se necesita instalar este MCP.
