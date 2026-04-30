# Sistema de Gestión de Activos Creativos

API REST para gestionar el ciclo de vida de piezas creativas (imágenes, videos, PDFs) dentro de proyectos de agencias y freelancers. Permite subir activos, versionar archivos, registrar aprobaciones/rechazos y comentarios, manteniendo trazabilidad completa.

---

## Stack tecnológico

| Componente   | Tecnología                          |
|--------------|-------------------------------------|
| Lenguaje     | Python 3.11+                        |
| Framework    | FastAPI 0.115                       |
| Base de datos| SQLite (desarrollo) / PostgreSQL (producción) |
| ORM          | SQLAlchemy 2.0                      |
| Validación   | Pydantic v2                         |
| Servidor     | Uvicorn                             |

---

```mermaid
---
title: sequence
---
sequenceDiagram
    participant F as Frontend
    participant API as Backend API
    participant DB as Base de datos
    participant S3 as Storage (S3/GCS)

    F->>API: POST /assets/upload-url<br/>{filename, asset_type, file_size}
    F->>S3: genera presigned URL
    S3-->>F: presigned_url (expira en 15min)
    API->>DB: crea asset en estado "uploading"
    API-->>F: 201 { asset_id, upload_url }

    F->>S3: PUT file (directo, sin pasar por API)
    S3-->>F: 200 OK

    F->>API: PATCH /assets/{id}/confirm
    API->>DB: status "uploading" → "pending_review"
    API-->>F: 200 { asset }

    Note over F,S3: Si el PUT falla, el asset<br/>queda en "uploading" y<br/>se puede reintentar

```