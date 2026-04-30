# Sistema de Gestión de Activos Creativos

API REST para gestionar el ciclo de vida de piezas creativas (imágenes, videos, PDFs) dentro de proyectos de agencias y freelancers. Permite subir activos, versionar archivos, registrar aprobaciones/rechazos y comentarios, manteniendo trazabilidad completa.

---

## Stack tecnológico

| Componente    | Tecnología                                        |
|---------------|---------------------------------------------------|
| Lenguaje      | Python 3.11+                                      |
| Framework     | FastAPI                                           |
| Base de datos | SQLite (desarrollo) / PostgreSQL (producción)     |
| ORM           | SQLAlchemy 2.0                                    |
| Validación    | Pydantic v2                                       |
| Servidor      | Uvicorn                                           |

---

## Correr localmente

```bash
pip install -r requirements.txt
uvicorn main:app --reload
# Docs: http://localhost:8000/docs
```

---

## Modelo de dominio

```
Agencia → Proyecto → Asset → AssetVersion (historial lineal e inmutable)
```

**Roles:** `admin`, `designer`, `reviewer`, `client`

### Estados de un asset

```
pending_review  ──[reviewer/client aprueba]──►  approved
pending_review  ◄──[designer sube versión]───   rejected
approved        ──[admin archiva]────────────►  archived
```

### Reglas clave

- El `version_number` empieza en 1 y se incrementa como `MAX + 1` por asset. Las versiones anteriores son **inmutables**.
- Solo la versión actual puede recibir una aprobación o rechazo.
- Solo usuarios con rol `client` o `reviewer` pueden registrar aprobaciones.
- Los comentarios se asocian a una `asset_version` específica y **no modifican** el estado del asset.
- Las aprobaciones nunca se modifican ni eliminan (trazabilidad completa).

---

## Flujo de subida de archivo

```mermaid
sequenceDiagram
    participant F as Frontend
    participant API as Backend API
    participant DB as Base de datos
    participant S3 as Storage (S3/GCS)

    F->>API: POST /assets/upload-url {filename, asset_type, file_size}
    API->>S3: genera presigned URL
    S3-->>API: presigned_url (expira en 15 min)
    API->>DB: crea asset en estado "uploading"
    API-->>F: 201 { asset_id, upload_url }

    F->>S3: PUT file (directo, sin pasar por API)
    S3-->>F: 200 OK

    F->>API: PATCH /assets/{id}/confirm
    API->>DB: status "uploading" → "pending_review"
    API-->>F: 200 { asset }

    Note over F,S3: Si el PUT falla, el asset queda en "uploading" y se puede reintentar
```

---

## Supuestos de implementación

1. **Sin autenticación** — el `user_id` se recibe en el cuerpo del request. En producción vendría del JWT/sesión.
2. **Almacenamiento simulado** — `file_url` se guarda como string. No hay integración real con S3/GCS.
3. **Un solo aprobador es suficiente** — la primera decisión registrada determina el estado del asset. El flujo multi-firma queda para una fase posterior.
4. **Sin notificaciones** — ningún evento (subida, aprobación, comentario) dispara emails ni notificaciones en sistema.
5. **Un proyecto pertenece a una sola agencia** — la relación `projects.agency_id` es única e inmutable.
6. **Versionado lineal** — no hay branches ni merges de versiones (1 → 2 → 3 → …).
