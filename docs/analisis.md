# Análisis de Requerimientos — Sistema de Gestión de Activos Creativos

---

## 1. Preguntas clave al cliente

1. **¿Cuántos aprobadores puede tener una pieza? ¿Se requiere aprobación unánime?**
   ¿Existe un solo aprobador por pieza o puede haber múltiples (por ejemplo, revisor interno + cliente final)? ¿Todos deben aprobar para que el asset quede en estado "approved", o basta con uno? ¿Hay un orden secuencial o las aprobaciones son paralelas?

2. **¿Quién puede subir piezas? ¿Solo diseñadores o también clientes?**
   ¿El rol `designer` es el único autorizado para crear assets y subir nuevas versiones? ¿Puede un `reviewer` o un `client` subir su propia versión de referencia? ¿Se requiere que el usuario pertenezca a la misma agencia del proyecto?

3. **¿Qué ocurre con la versión anterior cuando se sube una nueva?**
   ¿Las versiones anteriores quedan disponibles para consulta y descarga, o se "archivan" automáticamente? ¿Se puede volver a una versión anterior si el cliente lo solicita? ¿El historial es visible para todos los roles?

4. **¿Un cliente puede ver las piezas de otros clientes dentro del mismo proyecto?**
   Si un proyecto tiene múltiples clientes finales (por ejemplo, distintas marcas de un grupo empresarial), ¿cada cliente ve solo sus propias piezas o puede ver todas las del proyecto? ¿Existe aislamiento de datos entre clientes dentro de la misma agencia?

5. **¿Hay límite de tamaño de archivo? ¿Los tipos de archivo son restringidos por proyecto o globalmente?**
   ¿Existe un tope máximo (en MB o GB) por archivo, por versión o por proyecto? ¿Los tipos permitidos (`image`, `video`, `pdf`) son fijos o configurables por agencia/proyecto? ¿Se necesita validar el contenido del archivo o solo la extensión/MIME type?

6. **¿Se requiere autenticación? ¿SSO corporativo, OAuth o usuario/contraseña?**
   ¿La plataforma debe integrarse con un proveedor de identidad existente (Google Workspace, Azure AD, Okta)? ¿Los clientes externos acceden con usuario y contraseña propio del sistema o con un link de invitación temporal? ¿Los tokens de sesión tienen expiración configurable?

7. **¿Las notificaciones son por email, dentro del sistema, o ambas?**
   ¿Qué eventos disparan notificaciones: subida de pieza, aprobación, rechazo, nuevo comentario? ¿Las notificaciones son configurables por usuario (opt-in/opt-out)? ¿Existe integración con Slack, Teams u otra herramienta de mensajería?

8. **¿Qué significa "archivar" una pieza para el negocio?**
   ¿"Archivar" implica que la pieza ya no es accesible para el cliente o solo que se oculta de las vistas principales? ¿El archivo es reversible? ¿Los assets archivados siguen contando para el almacenamiento contratado? ¿Solo el `admin` puede archivar o también el `reviewer`?


## 2. Reglas de negocio

### Estados de una pieza

```
pending_review  ──[aprobación]──►  approved
pending_review  ──[rechazo]────►  rejected*
approved        ──[archivar]───►  archived  (solo admin)

* El diseñador puede subir una nueva versión, lo que regresa el asset a pending_review.
```

| Transición              | Quién la ejecuta              | Condición                                  |
|-------------------------|-------------------------------|--------------------------------------------|
| → `approved`            | `reviewer` o `client`         | Decisión `approved` en `approvals`         |
| → `pending_review`      | `designer` (nueva versión)    | Asset estaba en `rejected`                 |
| → `archived`            | `admin`                       | Asset estaba en `approved`                 |

---

### Versionado

- La primera versión de todo asset es siempre `version_number = 1`.
- Cada nueva versión se crea con `version_number = MAX(version_number) + 1` para ese asset.
- Las versiones anteriores son **inmutables**: no se modifican ni eliminan.
- Solo la versión más reciente (`current_version`) puede recibir una aprobación o rechazo activo.
- El campo `current_version` en `assets` se actualiza en cada nueva subida.

---

### Aprobaciones / rechazos

- Solo usuarios con rol `client` o `reviewer` pueden crear registros en `approvals`.
- Al aprobar una versión, el estado del asset pasa a `approved`.
- Al rechazar, el estado vuelve a `pending_review` para que el diseñador suba una nueva versión.
- Una misma versión puede tener múltiples registros en `approvals` si hay varios aprobadores (en implementación futura con flujo multi-firma).
- Las aprobaciones no se modifican ni eliminan una vez registradas (trazabilidad completa).

---

### Comentarios

- Cualquier usuario con acceso al proyecto puede comentar (diseñador, revisor, cliente, admin).
- Los comentarios están asociados a una `asset_version` específica, no al asset completo.
- Los comentarios **no modifican** el estado del asset ni de la versión.
- Los comentarios no se eliminan (soft-delete podría implementarse en el futuro).

---

### Responsables y trazabilidad

- `assets.created_by` → registra quién subió la pieza original.
- `asset_versions.created_by` → registra quién subió cada versión (puede ser distinto del creador del asset).
- `approvals.reviewed_by` → registra quién tomó la decisión de aprobación/rechazo.
- `comments.author_id` → registra quién escribió el comentario.
- Toda acción queda trazada con `created_at` (timestamp inmutable).

---

## 3. Supuestos

1. **No se implementa autenticación** — el `user_id` se recibe directamente en el cuerpo del request. En producción se obtendría del token JWT/sesión.
2. **El almacenamiento de archivos es simulado** — el sistema guarda una URL (`file_url`) como cadena de texto. No hay integración real con S3, GCS u otro proveedor de almacenamiento.
3. **Un solo aprobador es suficiente** — no existe flujo multi-firma ni quórum de aprobadores. La primera decisión registrada determina el estado del asset.
4. **Las agencias de tipo `freelancer` tienen un solo usuario** — esta restricción no se valida en el código; es una convención de uso esperada por el negocio.
5. **No hay notificaciones por email ni en sistema** — ningún evento (subida, aprobación, comentario) dispara notificaciones. Esta funcionalidad se deja para una fase posterior.
6. **Los proyectos pertenecen a una sola agencia** — no existe co-ownership de proyectos entre agencias. La relación `projects.agency_id` es única e inmutable.
7. **Un cliente puede acceder a todos los proyectos de la agencia que lo invitó** — no existe un modelo de permisos granular por proyecto; el acceso es a nivel de agencia.
8. **El versionado es lineal, no ramificado** — no hay branches ni merges de versiones. La cadena de versiones es estrictamente secuencial (1 → 2 → 3 → …).
