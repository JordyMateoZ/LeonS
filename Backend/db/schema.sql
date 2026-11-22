-- ============================================================================
-- LeonS — Esquema de base de datos (SQL Server 2019+)
-- Generado desde los modelos SQLAlchemy 2.0 con: uv run python db/export_schema.py
-- No editar a mano: cambia el modelo y regenera este archivo.
--
-- Base: LeonsDB (producción local) / LeonsDB_Test (pruebas)
-- Collation: Modern_Spanish_CI_AI
--
-- Aplicación recomendada (no destructiva):
--   cd Backend
--   uv run alembic -x target=test upgrade head
--   uv run alembic -x target=main upgrade head
--
-- El esquema se compone de 20 tablas de dominio. Alembic mantiene su
-- propia tabla `alembic_version`, que no forma parte del modelo.
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- contenido_faqs --------------------------------------------------------
CREATE TABLE contenido_faqs (
	id INTEGER NOT NULL IDENTITY, 
	orden SMALLINT NOT NULL, 
	pregunta NVARCHAR(300) NOT NULL, 
	respuesta NVARCHAR(max) NOT NULL, 
	CONSTRAINT [PK_contenido_faqs] PRIMARY KEY (id), 
	CONSTRAINT [UX_contenido_faqs_orden] UNIQUE (orden)
);
GO

-- contenido_pasos -------------------------------------------------------
CREATE TABLE contenido_pasos (
	id INTEGER NOT NULL IDENTITY, 
	orden SMALLINT NOT NULL, 
	titulo NVARCHAR(150) NOT NULL, 
	descripcion NVARCHAR(max) NULL, 
	tipo NVARCHAR(20) NOT NULL DEFAULT N'adopcion', 
	icono NVARCHAR(40) NULL, 
	nota NVARCHAR(300) NULL, 
	CONSTRAINT [PK_contenido_pasos] PRIMARY KEY (id), 
	CONSTRAINT [CK_contenido_pasos_tipo] CHECK (tipo IN ('adopcion', 'refugio', 'requisito')), 
	CONSTRAINT [UX_contenido_pasos_orden] UNIQUE (orden)
);
GO

-- distritos -------------------------------------------------------------
CREATE TABLE distritos (
	id INTEGER NOT NULL IDENTITY, 
	nombre NVARCHAR(80) NOT NULL, 
	provincia NVARCHAR(80) NULL, 
	CONSTRAINT [PK_distritos] PRIMARY KEY (id), 
	CONSTRAINT [UX_distritos_nombre] UNIQUE (nombre)
);
GO

-- migraciones -----------------------------------------------------------
CREATE TABLE migraciones (
	id INTEGER NOT NULL IDENTITY, 
	nombre NVARCHAR(100) NOT NULL, 
	aplicada_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	CONSTRAINT [PK_migraciones] PRIMARY KEY (id), 
	CONSTRAINT [UX_migraciones_nombre] UNIQUE (nombre)
);
GO

-- refugios --------------------------------------------------------------
CREATE TABLE refugios (
	id NVARCHAR(60) NOT NULL, 
	nombre NVARCHAR(150) NOT NULL, 
	orden SMALLINT NULL, 
	descripcion NVARCHAR(max) NULL, 
	distrito_id INTEGER NULL, 
	direccion NVARCHAR(250) NULL, 
	telefono NVARCHAR(30) NULL, 
	whatsapp NVARCHAR(30) NULL, 
	email NVARCHAR(180) NULL, 
	adoptadas_historicas INTEGER NOT NULL DEFAULT 0, 
	en_acogida_actual INTEGER NOT NULL DEFAULT 0, 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	contacto NVARCHAR(120) NULL, 
	cargo NVARCHAR(120) NULL, 
	tipo NVARCHAR(20) NULL, 
	desde SMALLINT NULL, 
	verificado BIT NOT NULL DEFAULT 1, 
	logo NVARCHAR(500) NULL, 
	CONSTRAINT [PK_refugios] PRIMARY KEY (id), 
	CONSTRAINT [CK_refugios_contadores] CHECK (adoptadas_historicas >= 0 AND en_acogida_actual >= 0), 
	CONSTRAINT [CK_refugios_tipo] CHECK (tipo IS NULL OR tipo IN ('constituido', 'independiente')), 
	CONSTRAINT [FK_refugios_distritos] FOREIGN KEY(distrito_id) REFERENCES distritos (id)
);
GO

CREATE INDEX [IX_refugios_distrito] ON refugios (distrito_id);
GO

-- mascotas --------------------------------------------------------------
CREATE TABLE mascotas (
	id INTEGER NOT NULL IDENTITY, 
	refugio_id NVARCHAR(60) NOT NULL, 
	nombre NVARCHAR(80) NOT NULL, 
	especie NVARCHAR(20) NOT NULL, 
	raza NVARCHAR(100) NULL, 
	sexo NVARCHAR(20) NULL, 
	edad NUMERIC(3, 1) NULL, 
	tamano NVARCHAR(20) NULL, 
	descripcion NVARCHAR(max) NULL, 
	estado NVARCHAR(20) NOT NULL DEFAULT N'disponible', 
	destacada BIT NOT NULL DEFAULT 0, 
	foto_principal NVARCHAR(500) NULL, 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	actualizado_en DATETIME2 NULL, 
	nombre_corto NVARCHAR(40) NULL, 
	peso_kg NUMERIC(4, 1) NULL, 
	lugar NVARCHAR(120) NULL, 
	etiqueta NVARCHAR(60) NULL, 
	etiqueta_icono NVARCHAR(40) NULL, 
	energia NVARCHAR(40) NULL, 
	urgente BIT NOT NULL DEFAULT 0, 
	foto_alt NVARCHAR(300) NULL, 
	vacunado BIT NULL, 
	esterilizado BIT NULL, 
	distrito_id INTEGER NULL, 
	etiqueta_clase NVARCHAR(80) NULL, 
	cita_texto NVARCHAR(500) NULL, 
	cita_autor NVARCHAR(120) NULL, 
	CONSTRAINT [PK_mascotas] PRIMARY KEY (id), 
	CONSTRAINT [CK_mascotas_especie] CHECK (especie IN ('perro', 'gato')), 
	CONSTRAINT [CK_mascotas_estado] CHECK (estado IN ('disponible', 'adoptada', 'en_acogida')), 
	CONSTRAINT [CK_mascotas_edad] CHECK (edad IS NULL OR edad >= 0), 
	CONSTRAINT [CK_mascotas_sexo] CHECK (sexo IS NULL OR sexo IN ('Macho', 'Hembra')), 
	CONSTRAINT [CK_mascotas_tamano] CHECK (tamano IS NULL OR tamano IN ('Pequeño', 'Mediano', 'Grande')), 
	CONSTRAINT [FK_mascotas_refugios] FOREIGN KEY(refugio_id) REFERENCES refugios (id), 
	CONSTRAINT [FK_mascotas_distritos] FOREIGN KEY(distrito_id) REFERENCES distritos (id)
);
GO

CREATE INDEX [IX_mascotas_catalogo] ON mascotas (estado, especie) INCLUDE (destacada, nombre);
GO

CREATE INDEX [IX_mascotas_refugio] ON mascotas (refugio_id);
GO

-- refugio_especies ------------------------------------------------------
CREATE TABLE refugio_especies (
	refugio_id NVARCHAR(60) NOT NULL, 
	especie NVARCHAR(20) NOT NULL, 
	CONSTRAINT [PK_refugio_especies] PRIMARY KEY (refugio_id, especie), 
	CONSTRAINT [CK_refugio_especies_especie] CHECK (especie IN ('perro', 'gato')), 
	CONSTRAINT [FK_refugio_especies_refugios] FOREIGN KEY(refugio_id) REFERENCES refugios (id) ON DELETE CASCADE
);
GO

-- usuarios --------------------------------------------------------------
CREATE TABLE usuarios (
	id INTEGER NOT NULL IDENTITY, 
	nombres NVARCHAR(120) NOT NULL, 
	apellidos NVARCHAR(120) NULL, 
	email NVARCHAR(180) NOT NULL, 
	dni CHAR(8) NULL, 
	password_hash NVARCHAR(255) NULL, 
	google_id NVARCHAR(100) NULL, 
	rol NVARCHAR(20) NOT NULL DEFAULT N'adoptante', 
	telefono NVARCHAR(30) NULL, 
	distrito_id INTEGER NULL, 
	refugio_id NVARCHAR(60) NULL, 
	activo BIT NOT NULL DEFAULT 1, 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	actualizado_en DATETIME2 NULL, 
	CONSTRAINT [PK_usuarios] PRIMARY KEY (id), 
	CONSTRAINT [CK_usuarios_rol] CHECK (rol IN ('adoptante', 'refugio', 'admin')), 
	CONSTRAINT [CK_usuarios_dni] CHECK (dni IS NULL OR NOT dni LIKE '%[^0-9]%'), 
	CONSTRAINT [UX_usuarios_email] UNIQUE (email), 
	CONSTRAINT [FK_usuarios_distritos] FOREIGN KEY(distrito_id) REFERENCES distritos (id), 
	CONSTRAINT [FK_usuarios_refugios] FOREIGN KEY(refugio_id) REFERENCES refugios (id)
);
GO

CREATE UNIQUE INDEX [UX_usuarios_google] ON usuarios (google_id) WHERE google_id IS NOT NULL;
GO

CREATE UNIQUE INDEX [UX_usuarios_dni] ON usuarios (dni) WHERE dni IS NOT NULL;
GO

-- alertas_rescate -------------------------------------------------------
CREATE TABLE alertas_rescate (
	id INTEGER NOT NULL IDENTITY, 
	usuario_id INTEGER NULL, 
	nombre NVARCHAR(120) NOT NULL, 
	especie NVARCHAR(20) NULL, 
	descripcion NVARCHAR(1000) NOT NULL, 
	ubicacion NVARCHAR(250) NULL, 
	distrito_id INTEGER NULL, 
	contacto NVARCHAR(100) NULL, 
	mensaje NVARCHAR(1000) NULL, 
	estado NVARCHAR(20) NOT NULL DEFAULT N'nueva', 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	CONSTRAINT [PK_alertas_rescate] PRIMARY KEY (id), 
	CONSTRAINT [CK_alertas_rescate_especie] CHECK (especie IS NULL OR especie IN ('perro', 'gato')), 
	CONSTRAINT [CK_alertas_rescate_estado] CHECK (estado IN ('nueva', 'atendida', 'cerrada')), 
	CONSTRAINT [FK_alertas_rescate_usuarios] FOREIGN KEY(usuario_id) REFERENCES usuarios (id), 
	CONSTRAINT [FK_alertas_rescate_distritos] FOREIGN KEY(distrito_id) REFERENCES distritos (id)
);
GO

CREATE INDEX [IX_alertas_rescate_fecha] ON alertas_rescate (creado_en);
GO

-- favoritos -------------------------------------------------------------
CREATE TABLE favoritos (
	usuario_id INTEGER NOT NULL, 
	mascota_id INTEGER NOT NULL, 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	CONSTRAINT [PK_favoritos] PRIMARY KEY (usuario_id, mascota_id), 
	CONSTRAINT [FK_favoritos_usuarios] FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE, 
	CONSTRAINT [FK_favoritos_mascotas] FOREIGN KEY(mascota_id) REFERENCES mascotas (id) ON DELETE CASCADE
);
GO

CREATE INDEX [IX_favoritos_mascota] ON favoritos (mascota_id);
GO

-- mascota_cuidados ------------------------------------------------------
CREATE TABLE mascota_cuidados (
	id INTEGER NOT NULL IDENTITY, 
	mascota_id INTEGER NOT NULL, 
	orden SMALLINT NOT NULL DEFAULT 0, 
	icono NVARCHAR(40) NOT NULL, 
	titulo NVARCHAR(120) NOT NULL, 
	texto NVARCHAR(max) NOT NULL, 
	CONSTRAINT [PK_mascota_cuidados] PRIMARY KEY (id), 
	CONSTRAINT [FK_mascota_cuidados_mascotas] FOREIGN KEY(mascota_id) REFERENCES mascotas (id) ON DELETE CASCADE
);
GO

CREATE INDEX [IX_mascota_cuidados_mascota] ON mascota_cuidados (mascota_id, orden);
GO

-- mascota_fotos ---------------------------------------------------------
CREATE TABLE mascota_fotos (
	id INTEGER NOT NULL IDENTITY, 
	mascota_id INTEGER NOT NULL, 
	orden SMALLINT NOT NULL DEFAULT 0, 
	url NVARCHAR(500) NOT NULL, 
	alt NVARCHAR(300) NULL, 
	CONSTRAINT [PK_mascota_fotos] PRIMARY KEY (id), 
	CONSTRAINT [FK_mascota_fotos_mascotas] FOREIGN KEY(mascota_id) REFERENCES mascotas (id) ON DELETE CASCADE
);
GO

CREATE INDEX [IX_mascota_fotos_mascota] ON mascota_fotos (mascota_id, orden);
GO

-- mascota_historia ------------------------------------------------------
CREATE TABLE mascota_historia (
	id INTEGER NOT NULL IDENTITY, 
	mascota_id INTEGER NOT NULL, 
	orden SMALLINT NOT NULL DEFAULT 0, 
	texto NVARCHAR(max) NOT NULL, 
	CONSTRAINT [PK_mascota_historia] PRIMARY KEY (id), 
	CONSTRAINT [FK_mascota_historia_mascotas] FOREIGN KEY(mascota_id) REFERENCES mascotas (id) ON DELETE CASCADE
);
GO

CREATE INDEX [IX_mascota_historia_mascota] ON mascota_historia (mascota_id, orden);
GO

-- mascota_rasgos --------------------------------------------------------
CREATE TABLE mascota_rasgos (
	id INTEGER NOT NULL IDENTITY, 
	mascota_id INTEGER NOT NULL, 
	orden SMALLINT NOT NULL DEFAULT 0, 
	rasgo NVARCHAR(100) NOT NULL, 
	icono NVARCHAR(40) NULL, 
	clase NVARCHAR(200) NULL, 
	icono_clase NVARCHAR(40) NULL, 
	CONSTRAINT [PK_mascota_rasgos] PRIMARY KEY (id), 
	CONSTRAINT [FK_mascota_rasgos_mascotas] FOREIGN KEY(mascota_id) REFERENCES mascotas (id) ON DELETE CASCADE
);
GO

CREATE INDEX [IX_mascota_rasgos_mascota] ON mascota_rasgos (mascota_id, orden);
GO

-- mascota_salud ---------------------------------------------------------
CREATE TABLE mascota_salud (
	id INTEGER NOT NULL IDENTITY, 
	mascota_id INTEGER NOT NULL, 
	orden SMALLINT NOT NULL DEFAULT 0, 
	texto NVARCHAR(200) NOT NULL, 
	ok BIT NOT NULL DEFAULT 1, 
	CONSTRAINT [PK_mascota_salud] PRIMARY KEY (id), 
	CONSTRAINT [FK_mascota_salud_mascotas] FOREIGN KEY(mascota_id) REFERENCES mascotas (id) ON DELETE CASCADE
);
GO

CREATE INDEX [IX_mascota_salud_mascota] ON mascota_salud (mascota_id, orden);
GO

-- solicitudes -----------------------------------------------------------
CREATE TABLE solicitudes (
	id INTEGER NOT NULL IDENTITY, 
	codigo NVARCHAR(30) NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	mascota_id INTEGER NOT NULL, 
	refugio_id NVARCHAR(60) NOT NULL, 
	estado NVARCHAR(20) NOT NULL DEFAULT N'activa', 
	etapa TINYINT NOT NULL DEFAULT 2, 
	motivo_cancelacion NVARCHAR(500) NULL, 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	actualizado_en DATETIME2 NULL, 
	CONSTRAINT [PK_solicitudes] PRIMARY KEY (id), 
	CONSTRAINT [CK_solicitudes_estado] CHECK (estado IN ('activa', 'cancelada', 'completada')), 
	CONSTRAINT [CK_solicitudes_etapa] CHECK (etapa BETWEEN 1 AND 5), 
	CONSTRAINT [CK_solicitudes_motivo] CHECK (estado <> 'cancelada' OR motivo_cancelacion IS NOT NULL), 
	CONSTRAINT [UX_solicitudes_codigo] UNIQUE (codigo), 
	CONSTRAINT [FK_solicitudes_usuarios] FOREIGN KEY(usuario_id) REFERENCES usuarios (id), 
	CONSTRAINT [FK_solicitudes_mascotas] FOREIGN KEY(mascota_id) REFERENCES mascotas (id), 
	CONSTRAINT [FK_solicitudes_refugios] FOREIGN KEY(refugio_id) REFERENCES refugios (id)
);
GO

CREATE UNIQUE INDEX [UX_solicitudes_activa] ON solicitudes (usuario_id, mascota_id) WHERE estado = 'activa';
GO

CREATE INDEX [IX_solicitudes_usuario] ON solicitudes (usuario_id, creado_en);
GO

CREATE INDEX [IX_solicitudes_refugio] ON solicitudes (refugio_id, estado, etapa);
GO

CREATE INDEX [IX_solicitudes_mascota] ON solicitudes (mascota_id);
GO

-- citas -----------------------------------------------------------------
CREATE TABLE citas (
	id INTEGER NOT NULL IDENTITY, 
	solicitud_id INTEGER NOT NULL, 
	fecha_hora DATETIME2 NOT NULL, 
	lugar NVARCHAR(200) NULL, 
	notas NVARCHAR(500) NULL, 
	coordinadora NVARCHAR(120) NULL, 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	CONSTRAINT [PK_citas] PRIMARY KEY (id), 
	CONSTRAINT [FK_citas_solicitudes] FOREIGN KEY(solicitud_id) REFERENCES solicitudes (id) ON DELETE CASCADE
);
GO

CREATE INDEX [IX_citas_solicitud] ON citas (solicitud_id, fecha_hora);
GO

-- mensajes --------------------------------------------------------------
CREATE TABLE mensajes (
	id INTEGER NOT NULL IDENTITY, 
	solicitud_id INTEGER NOT NULL, 
	autor_id INTEGER NOT NULL, 
	texto NVARCHAR(2000) NOT NULL, 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	CONSTRAINT [PK_mensajes] PRIMARY KEY (id), 
	CONSTRAINT [FK_mensajes_solicitudes] FOREIGN KEY(solicitud_id) REFERENCES solicitudes (id) ON DELETE CASCADE, 
	CONSTRAINT [FK_mensajes_usuarios] FOREIGN KEY(autor_id) REFERENCES usuarios (id)
);
GO

CREATE INDEX [IX_mensajes_solicitud] ON mensajes (solicitud_id, creado_en);
GO

-- seguimiento_fotos -----------------------------------------------------
CREATE TABLE seguimiento_fotos (
	id INTEGER NOT NULL IDENTITY, 
	solicitud_id INTEGER NOT NULL, 
	mes TINYINT NOT NULL, 
	archivo NVARCHAR(300) NOT NULL, 
	mime NVARCHAR(50) NOT NULL, 
	tamano_bytes INTEGER NOT NULL, 
	comentario NVARCHAR(500) NULL, 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	CONSTRAINT [PK_seguimiento_fotos] PRIMARY KEY (id), 
	CONSTRAINT [CK_seguimiento_fotos_mes] CHECK (mes IN (1, 3, 6)), 
	CONSTRAINT [CK_seguimiento_fotos_tamano] CHECK (tamano_bytes > 0), 
	CONSTRAINT [FK_seguimiento_fotos_solicitudes] FOREIGN KEY(solicitud_id) REFERENCES solicitudes (id) ON DELETE CASCADE
);
GO

CREATE INDEX [IX_seguimiento_fotos_solicitud] ON seguimiento_fotos (solicitud_id, mes);
GO

-- solicitud_eventos -----------------------------------------------------
CREATE TABLE solicitud_eventos (
	id INTEGER NOT NULL IDENTITY, 
	solicitud_id INTEGER NOT NULL, 
	etapa TINYINT NOT NULL, 
	descripcion NVARCHAR(300) NULL, 
	creado_en DATETIME2 NOT NULL DEFAULT sysutcdatetime(), 
	CONSTRAINT [PK_solicitud_eventos] PRIMARY KEY (id), 
	CONSTRAINT [CK_solicitud_eventos_etapa] CHECK (etapa BETWEEN 1 AND 5), 
	CONSTRAINT [FK_solicitud_eventos_solicitudes] FOREIGN KEY(solicitud_id) REFERENCES solicitudes (id) ON DELETE CASCADE
);
GO

CREATE INDEX [IX_solicitud_eventos_solicitud] ON solicitud_eventos (solicitud_id, creado_en);
GO


-- ============================================================================
-- Fin del esquema. 20 tablas de dominio.
-- ============================================================================
