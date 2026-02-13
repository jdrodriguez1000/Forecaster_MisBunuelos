---
description: Sube el proyecto a GitHub usando el servidor MCP de GitHub, manejando repositorios existentes y siguiendo Conventional Commits.
---

1. Inicializar el repositorio local git (si no está inicializado ya).
   - Comando: `git init -b main`

2. Verificar si ya existe un origen remoto.
   - Comando: `git remote -v`
   - Si existe un remoto 'origin' y apunta al repositorio correcto de GitHub, ir al paso 7.
   - Si no existe remoto, ir al paso 3.

3. Verificar si el repositorio 'Forecaster_MisBunuelos' existe en GitHub.
   - Herramienta: `mcp_remote-github_search_repositories` con consulta `user:@me Forecaster_MisBunuelos`
   - Si existe, obtener la clone_url.
   - Si NO existe, ir al paso 4.

4. Crear el repositorio en GitHub (Solo si no existe).
   - Herramienta: `mcp_remote-github_create_repository`
   - Argumentos:
     - name: "Forecaster_MisBunuelos"
     - private: true
     - description: "Proyecto de forecasting para predicción de ventas de Mis Buñuelos."
   - Obtener la clone_url de la salida.

5. Agregar el origen remoto.
   - Comando: `git remote add origin <CLONE_URL>` (Reemplazar <CLONE_URL> con la URL obtenida)

6. Preparar todos los archivos (Stage).
   - Comando: `git add .`

7. Confirmar los cambios usando la convención definida.
   - Comando: `git commit -m "feat: Estructura inicial del proyecto y configuración"`

8. Enviar al repositorio remoto.
   - Comando: `git push -u origin main`
