# Module 3 — Test, Containerize, and Deploy TaskFlow

TaskFlow is a full-stack mini Kanban board originally built for Module 2.
This Module 3 version extends it with containerization, PostgreSQL,
end-to-end testing, CI/CD, and deployment.

## Local Development

This module includes a Docker Compose stack for local development.

### Starting the Stack

```bash
cd module-3
docker compose up -d --build
```

### Checking Status

```bash
docker compose ps
```

### Stopping the Stack

```bash
docker compose down
```

Data is persisted in a named volume (`taskflow_postgres_data`) and survives
`docker compose down` cycles.

### Access URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
