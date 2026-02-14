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

6. Gestionar archivos ignorados (.gitignore).
   - Revisar el estado actual con `git status`.
   - Identificar archivos o carpetas que NO deben subirse (ej: `.env`, `__pycache__`, carpetas de salida `outputs/`, archivos temporales, builds).
   - Si existen archivos que deben ignorarse pero no están en `.gitignore`, agregarlos al archivo `.gitignore`.
   - Si algún archivo a ignorar YA está trackeado (indexado) en git:
     - Ejecutar `git rm --cached <archivo>` para dejar de trackearlo sin borrarlo localmente.
   - Verificar nuevamente con `git status` que los archivos ignorados ya no aparezcan como pendientes.

7. Preparar todos los archivos (Stage).
   - Comando: `git add .`

8. Confirmar los cambios usando la convención definida.
   - Comando: `git commit -m "feat: Estructura inicial del proyecto y configuración"` (O un mensaje más descriptivo según los cambios).

9. Enviar al repositorio remoto.
   - Comando: `git push -u origin main`
