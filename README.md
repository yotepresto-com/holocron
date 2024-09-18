# Holocron - Sistema de Prevención de Lavado de Dinero

## Descripción

**Holocron** es un sistema de prevención de lavado de dinero (AML - Anti-Money Laundering) diseñado para cumplir con las disposiciones del artículo 58 de la **Ley para Regular las Instituciones de Tecnología Financiera** en México. Este sistema ayuda a identificar, gestionar y reportar actividades sospechosas, evaluar nivel de riesgo, así como a cumplir con las obligaciones de búsqueda en listas de personas bloqueadas y expuestas políticamente.

## Características Principales

El sistema está compuesto por varios módulos que cumplen con las funciones requeridas para la prevención del lavado de dinero, incluyendo:
   
1. **Búsqueda en Listas**:
   - Identificación de usuarios en listas de Personas Bloqueadas (LPB) o Personas Expuestas Políticamente (PEPs) mediante búsquedas manuales y automáticas.
   
2. **Evaluación del Grado de Riesgo**:
   - Evaluación del riesgo de los clientes según el Título 3, Capítulo II de la Ley. La clasificación se reporta al sistema.
   
3. **Buzón Anónimo**:
   - Implementación de un buzón para denuncias anónimas, como lo indica el inciso X del Artículo 56.

4. **Generación de Alertas**: 
   - Genera alertas sobre operaciones relevantes, inusuales y operaciones internas preocupantes, de acuerdo con los incisos VI, VII y XIII del Artículo 56.

5. **Generación de Reportes**:
   - Reportes automáticos y manuales sobre el estado de los usuarios y actividades, de acuerdo con el inciso III del Artículo 56.

## Arquitectura del Sistema

### Backend

El backend está construido en **Python** utilizando **FastAPI**, proporcionando una API RESTful para el manejo de las operaciones del sistema, tales como la creación de alertas, la búsqueda en listas y la evaluación de riesgos.

### Frontend

El frontend del sistema está construido en **React**, proporcionando una interfaz de usuario simple y eficiente para gestionar las operaciones de búsqueda y evaluación de riesgo.

## Instalación y Ejecución

### Requisitos

- **Python 3.12+**
- **PostgreSQL 16**
- **PgFormatter**
- **Node.js y npm** (para el frontend)

### Configuración

1. Clona el repositorio:
```bash
git clone https://github.com/tu-repositorio/holocron.git
cd holocron
```

2.	Instala las dependencias del backend:
```bash
pip install -r requirements.txt
```

3.	Configura la base de datos PostgreSQL y ejecuta el archivo SQL:
```bash
./scripts/setup_database.sh
```

4.	Inicia el servidor de FastAPI:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

5.	Para el frontend, navega a la carpeta frontend e instala las dependencias:
```bash
cd frontend
npm install
npm start
```

# Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un _pull request_ o crea un _issue_ para discutir cualquier cambio importante.

# Licencia
Este proyecto está bajo la Licencia GNU Affero General Public License v3.0 (AGPL-3.0). Consulta el archivo LICENSE.md para más detalles.
