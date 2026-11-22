"""Esquema inicial de LeonS (18 tablas).

Revision ID: 0001
Revises:
Create Date: 2026-11-18

Refleja el esquema que ya existía en `LeonsDB` antes de la Fase 5.
Las columnas que el contrato JSON necesita y no estaban se agregan en
`0002_contrato_catalogo` (migración aditiva, sin DROP).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contenido_faqs",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("orden", sa.SmallInteger(), nullable=False),
        sa.Column("pregunta", sa.Unicode(length=300), nullable=False),
        sa.Column("respuesta", mssql.NVARCHAR(length=None), nullable=False),
        sa.PrimaryKeyConstraint("id", name="PK_contenido_faqs"),
        sa.UniqueConstraint("orden", name="UX_contenido_faqs_orden"),
    )
    op.create_table(
        "contenido_pasos",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("orden", sa.SmallInteger(), nullable=False),
        sa.Column("titulo", sa.Unicode(length=150), nullable=False),
        sa.Column("descripcion", mssql.NVARCHAR(length=None), nullable=True),
        sa.PrimaryKeyConstraint("id", name="PK_contenido_pasos"),
        sa.UniqueConstraint("orden", name="UX_contenido_pasos_orden"),
    )
    op.create_table(
        "distritos",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("nombre", sa.Unicode(length=80), nullable=False),
        sa.Column("provincia", sa.Unicode(length=80), nullable=True),
        sa.PrimaryKeyConstraint("id", name="PK_distritos"),
        sa.UniqueConstraint("nombre", name="UX_distritos_nombre"),
    )
    op.create_table(
        "migraciones",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("nombre", sa.Unicode(length=100), nullable=False),
        sa.Column(
            "aplicada_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="PK_migraciones"),
        sa.UniqueConstraint("nombre", name="UX_migraciones_nombre"),
    )
    op.create_table(
        "refugios",
        sa.Column("id", sa.Unicode(length=60), nullable=False),
        sa.Column("nombre", sa.Unicode(length=150), nullable=False),
        sa.Column("descripcion", mssql.NVARCHAR(length=None), nullable=True),
        sa.Column("distrito_id", sa.Integer(), nullable=True),
        sa.Column("direccion", sa.Unicode(length=250), nullable=True),
        sa.Column("telefono", sa.Unicode(length=30), nullable=True),
        sa.Column("whatsapp", sa.Unicode(length=30), nullable=True),
        sa.Column("email", sa.Unicode(length=180), nullable=True),
        sa.Column(
            "adoptadas_historicas",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "en_acogida_actual",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "adoptadas_historicas >= 0 AND en_acogida_actual >= 0",
            name="CK_refugios_contadores",
        ),
        sa.ForeignKeyConstraint(
            ["distrito_id"], ["distritos.id"], name="FK_refugios_distritos"
        ),
        sa.PrimaryKeyConstraint("id", name="PK_refugios"),
    )
    op.create_index("IX_refugios_distrito", "refugios", ["distrito_id"], unique=False)

    op.create_table(
        "mascotas",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("refugio_id", sa.Unicode(length=60), nullable=False),
        sa.Column("nombre", sa.Unicode(length=80), nullable=False),
        sa.Column("especie", sa.Unicode(length=20), nullable=False),
        sa.Column("raza", sa.Unicode(length=100), nullable=True),
        sa.Column("sexo", sa.Unicode(length=20), nullable=True),
        sa.Column("edad", sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column("tamano", sa.Unicode(length=20), nullable=True),
        sa.Column("descripcion", mssql.NVARCHAR(length=None), nullable=True),
        sa.Column(
            "estado",
            sa.Unicode(length=20),
            server_default=sa.text("N'disponible'"),
            nullable=False,
        ),
        sa.Column(
            "destacada", sa.Boolean(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("foto_principal", sa.Unicode(length=500), nullable=True),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.Column("actualizado_en", mssql.DATETIME2(), nullable=True),
        sa.CheckConstraint(
            "especie IN ('perro', 'gato')", name="CK_mascotas_especie"
        ),
        sa.CheckConstraint(
            "estado IN ('disponible', 'adoptada', 'en_acogida')",
            name="CK_mascotas_estado",
        ),
        sa.CheckConstraint("edad IS NULL OR edad >= 0", name="CK_mascotas_edad"),
        sa.ForeignKeyConstraint(
            ["refugio_id"], ["refugios.id"], name="FK_mascotas_refugios"
        ),
        sa.PrimaryKeyConstraint("id", name="PK_mascotas"),
    )
    op.create_index(
        "IX_mascotas_catalogo", "mascotas", ["estado", "especie"], unique=False
    )
    op.create_index("IX_mascotas_refugio", "mascotas", ["refugio_id"], unique=False)

    op.create_table(
        "refugio_especies",
        sa.Column("refugio_id", sa.Unicode(length=60), nullable=False),
        sa.Column("especie", sa.Unicode(length=20), nullable=False),
        sa.CheckConstraint(
            "especie IN ('perro', 'gato')", name="CK_refugio_especies_especie"
        ),
        sa.ForeignKeyConstraint(
            ["refugio_id"],
            ["refugios.id"],
            name="FK_refugio_especies_refugios",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("refugio_id", "especie", name="PK_refugio_especies"),
    )

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("nombres", sa.Unicode(length=120), nullable=False),
        sa.Column("apellidos", sa.Unicode(length=120), nullable=True),
        sa.Column("email", sa.Unicode(length=180), nullable=False),
        sa.Column("dni", sa.CHAR(length=8), nullable=True),
        sa.Column("password_hash", sa.Unicode(length=255), nullable=True),
        sa.Column("google_id", sa.Unicode(length=100), nullable=True),
        sa.Column(
            "rol",
            sa.Unicode(length=20),
            server_default=sa.text("N'adoptante'"),
            nullable=False,
        ),
        sa.Column("telefono", sa.Unicode(length=30), nullable=True),
        sa.Column("distrito_id", sa.Integer(), nullable=True),
        sa.Column("refugio_id", sa.Unicode(length=60), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.Column("actualizado_en", mssql.DATETIME2(), nullable=True),
        sa.CheckConstraint(
            "dni IS NULL OR NOT dni LIKE '%[^0-9]%'", name="CK_usuarios_dni"
        ),
        sa.CheckConstraint(
            "rol IN ('adoptante', 'refugio', 'admin')", name="CK_usuarios_rol"
        ),
        sa.ForeignKeyConstraint(
            ["distrito_id"], ["distritos.id"], name="FK_usuarios_distritos"
        ),
        sa.ForeignKeyConstraint(
            ["refugio_id"], ["refugios.id"], name="FK_usuarios_refugios"
        ),
        sa.PrimaryKeyConstraint("id", name="PK_usuarios"),
        sa.UniqueConstraint("email", name="UX_usuarios_email"),
    )
    op.create_index(
        "UX_usuarios_dni",
        "usuarios",
        ["dni"],
        unique=True,
        mssql_where=sa.text("dni IS NOT NULL"),
    )
    op.create_index(
        "UX_usuarios_google",
        "usuarios",
        ["google_id"],
        unique=True,
        mssql_where=sa.text("google_id IS NOT NULL"),
    )

    op.create_table(
        "alertas_rescate",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("especie", sa.Unicode(length=20), nullable=True),
        sa.Column("descripcion", sa.Unicode(length=1000), nullable=False),
        sa.Column("ubicacion", sa.Unicode(length=250), nullable=True),
        sa.Column("distrito_id", sa.Integer(), nullable=True),
        sa.Column("contacto", sa.Unicode(length=100), nullable=True),
        sa.Column(
            "estado",
            sa.Unicode(length=20),
            server_default=sa.text("N'nueva'"),
            nullable=False,
        ),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "especie IS NULL OR especie IN ('perro', 'gato')",
            name="CK_alertas_rescate_especie",
        ),
        sa.CheckConstraint(
            "estado IN ('nueva', 'atendida', 'cerrada')",
            name="CK_alertas_rescate_estado",
        ),
        sa.ForeignKeyConstraint(
            ["distrito_id"], ["distritos.id"], name="FK_alertas_rescate_distritos"
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], name="FK_alertas_rescate_usuarios"
        ),
        sa.PrimaryKeyConstraint("id", name="PK_alertas_rescate"),
    )
    op.create_index(
        "IX_alertas_rescate_fecha", "alertas_rescate", ["creado_en"], unique=False
    )

    op.create_table(
        "favoritos",
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("mascota_id", sa.Integer(), nullable=False),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["mascota_id"],
            ["mascotas.id"],
            name="FK_favoritos_mascotas",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name="FK_favoritos_usuarios",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("usuario_id", "mascota_id", name="PK_favoritos"),
    )
    op.create_index("IX_favoritos_mascota", "favoritos", ["mascota_id"], unique=False)

    op.create_table(
        "mascota_fotos",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("mascota_id", sa.Integer(), nullable=False),
        sa.Column(
            "orden", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("url", sa.Unicode(length=500), nullable=False),
        sa.ForeignKeyConstraint(
            ["mascota_id"],
            ["mascotas.id"],
            name="FK_mascota_fotos_mascotas",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="PK_mascota_fotos"),
    )
    op.create_index(
        "IX_mascota_fotos_mascota",
        "mascota_fotos",
        ["mascota_id", "orden"],
        unique=False,
    )

    op.create_table(
        "mascota_rasgos",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("mascota_id", sa.Integer(), nullable=False),
        sa.Column(
            "orden", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("rasgo", sa.Unicode(length=100), nullable=False),
        sa.ForeignKeyConstraint(
            ["mascota_id"],
            ["mascotas.id"],
            name="FK_mascota_rasgos_mascotas",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="PK_mascota_rasgos"),
    )
    op.create_index(
        "IX_mascota_rasgos_mascota",
        "mascota_rasgos",
        ["mascota_id", "orden"],
        unique=False,
    )

    op.create_table(
        "mascota_salud",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("mascota_id", sa.Integer(), nullable=False),
        sa.Column(
            "orden", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("texto", sa.Unicode(length=200), nullable=False),
        sa.ForeignKeyConstraint(
            ["mascota_id"],
            ["mascotas.id"],
            name="FK_mascota_salud_mascotas",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="PK_mascota_salud"),
    )
    op.create_index(
        "IX_mascota_salud_mascota",
        "mascota_salud",
        ["mascota_id", "orden"],
        unique=False,
    )

    op.create_table(
        "solicitudes",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("codigo", sa.Unicode(length=30), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("mascota_id", sa.Integer(), nullable=False),
        sa.Column("refugio_id", sa.Unicode(length=60), nullable=False),
        sa.Column(
            "estado",
            sa.Unicode(length=20),
            server_default=sa.text("N'activa'"),
            nullable=False,
        ),
        sa.Column("etapa", mssql.TINYINT(), server_default=sa.text("2"), nullable=False),
        sa.Column("motivo_cancelacion", sa.Unicode(length=500), nullable=True),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.Column("actualizado_en", mssql.DATETIME2(), nullable=True),
        sa.CheckConstraint(
            "estado <> 'cancelada' OR motivo_cancelacion IS NOT NULL",
            name="CK_solicitudes_motivo",
        ),
        sa.CheckConstraint(
            "estado IN ('activa', 'cancelada', 'completada')",
            name="CK_solicitudes_estado",
        ),
        sa.CheckConstraint("etapa BETWEEN 1 AND 5", name="CK_solicitudes_etapa"),
        sa.ForeignKeyConstraint(
            ["mascota_id"], ["mascotas.id"], name="FK_solicitudes_mascotas"
        ),
        sa.ForeignKeyConstraint(
            ["refugio_id"], ["refugios.id"], name="FK_solicitudes_refugios"
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], name="FK_solicitudes_usuarios"
        ),
        sa.PrimaryKeyConstraint("id", name="PK_solicitudes"),
        sa.UniqueConstraint("codigo", name="UX_solicitudes_codigo"),
    )
    op.create_index(
        "IX_solicitudes_mascota", "solicitudes", ["mascota_id"], unique=False
    )
    op.create_index(
        "IX_solicitudes_refugio",
        "solicitudes",
        ["refugio_id", "estado", "etapa"],
        unique=False,
    )
    op.create_index(
        "IX_solicitudes_usuario",
        "solicitudes",
        ["usuario_id", "creado_en"],
        unique=False,
    )
    op.create_index(
        "UX_solicitudes_activa",
        "solicitudes",
        ["usuario_id", "mascota_id"],
        unique=True,
        mssql_where=sa.text("estado = 'activa'"),
    )

    op.create_table(
        "citas",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("solicitud_id", sa.Integer(), nullable=False),
        sa.Column("fecha_hora", mssql.DATETIME2(), nullable=False),
        sa.Column("lugar", sa.Unicode(length=200), nullable=True),
        sa.Column("notas", sa.Unicode(length=500), nullable=True),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["solicitud_id"],
            ["solicitudes.id"],
            name="FK_citas_solicitudes",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="PK_citas"),
    )
    op.create_index(
        "IX_citas_solicitud", "citas", ["solicitud_id", "fecha_hora"], unique=False
    )

    op.create_table(
        "mensajes",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("solicitud_id", sa.Integer(), nullable=False),
        sa.Column("autor_id", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Unicode(length=2000), nullable=False),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["autor_id"], ["usuarios.id"], name="FK_mensajes_usuarios"
        ),
        sa.ForeignKeyConstraint(
            ["solicitud_id"],
            ["solicitudes.id"],
            name="FK_mensajes_solicitudes",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="PK_mensajes"),
    )
    op.create_index(
        "IX_mensajes_solicitud",
        "mensajes",
        ["solicitud_id", "creado_en"],
        unique=False,
    )

    op.create_table(
        "seguimiento_fotos",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("solicitud_id", sa.Integer(), nullable=False),
        sa.Column("mes", mssql.TINYINT(), nullable=False),
        sa.Column("archivo", sa.Unicode(length=300), nullable=False),
        sa.Column("mime", sa.Unicode(length=50), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("comentario", sa.Unicode(length=500), nullable=True),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.CheckConstraint("mes IN (1, 3, 6)", name="CK_seguimiento_fotos_mes"),
        sa.CheckConstraint("tamano_bytes > 0", name="CK_seguimiento_fotos_tamano"),
        sa.ForeignKeyConstraint(
            ["solicitud_id"],
            ["solicitudes.id"],
            name="FK_seguimiento_fotos_solicitudes",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="PK_seguimiento_fotos"),
    )
    op.create_index(
        "IX_seguimiento_fotos_solicitud",
        "seguimiento_fotos",
        ["solicitud_id", "mes"],
        unique=False,
    )

    op.create_table(
        "solicitud_eventos",
        sa.Column("id", sa.Integer(), sa.Identity(1, 1), nullable=False),
        sa.Column("solicitud_id", sa.Integer(), nullable=False),
        sa.Column("etapa", mssql.TINYINT(), nullable=False),
        sa.Column("descripcion", sa.Unicode(length=300), nullable=True),
        sa.Column(
            "creado_en",
            mssql.DATETIME2(),
            server_default=sa.text("sysutcdatetime()"),
            nullable=False,
        ),
        sa.CheckConstraint("etapa BETWEEN 1 AND 5", name="CK_solicitud_eventos_etapa"),
        sa.ForeignKeyConstraint(
            ["solicitud_id"],
            ["solicitudes.id"],
            name="FK_solicitud_eventos_solicitudes",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="PK_solicitud_eventos"),
    )
    op.create_index(
        "IX_solicitud_eventos_solicitud",
        "solicitud_eventos",
        ["solicitud_id", "creado_en"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("IX_solicitud_eventos_solicitud", table_name="solicitud_eventos")
    op.drop_table("solicitud_eventos")
    op.drop_index("IX_seguimiento_fotos_solicitud", table_name="seguimiento_fotos")
    op.drop_table("seguimiento_fotos")
    op.drop_index("IX_mensajes_solicitud", table_name="mensajes")
    op.drop_table("mensajes")
    op.drop_index("IX_citas_solicitud", table_name="citas")
    op.drop_table("citas")
    op.drop_index("UX_solicitudes_activa", table_name="solicitudes")
    op.drop_index("IX_solicitudes_usuario", table_name="solicitudes")
    op.drop_index("IX_solicitudes_refugio", table_name="solicitudes")
    op.drop_index("IX_solicitudes_mascota", table_name="solicitudes")
    op.drop_table("solicitudes")
    op.drop_index("IX_mascota_salud_mascota", table_name="mascota_salud")
    op.drop_table("mascota_salud")
    op.drop_index("IX_mascota_rasgos_mascota", table_name="mascota_rasgos")
    op.drop_table("mascota_rasgos")
    op.drop_index("IX_mascota_fotos_mascota", table_name="mascota_fotos")
    op.drop_table("mascota_fotos")
    op.drop_index("IX_favoritos_mascota", table_name="favoritos")
    op.drop_table("favoritos")
    op.drop_index("IX_alertas_rescate_fecha", table_name="alertas_rescate")
    op.drop_table("alertas_rescate")
    op.drop_index("UX_usuarios_google", table_name="usuarios")
    op.drop_index("UX_usuarios_dni", table_name="usuarios")
    op.drop_table("usuarios")
    op.drop_table("refugio_especies")
    op.drop_index("IX_mascotas_refugio", table_name="mascotas")
    op.drop_index("IX_mascotas_catalogo", table_name="mascotas")
    op.drop_table("mascotas")
    op.drop_index("IX_refugios_distrito", table_name="refugios")
    op.drop_table("refugios")
    op.drop_table("migraciones")
    op.drop_table("distritos")
    op.drop_table("contenido_pasos")
    op.drop_table("contenido_faqs")
