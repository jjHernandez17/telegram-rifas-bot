import os
from dotenv import load_dotenv
from database import init_db, get_db, return_db
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# Cargar variables de entorno
load_dotenv()

# =====================
# CONFIGURACIÓN
# =====================
TOKEN = os.getenv("TOKEN")
GRUPO_RIFAS_ID = int(os.getenv("GRUPO_RIFAS_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Estados usuario
NOMBRE, TELEFONO = range(2)

# Estados creación de rifa (admin)
RIFA_NOMBRE, RIFA_PRECIO, RIFA_PREMIO, RIFA_FECHA, RIFA_DESC = range(2, 7)

# =====================
# MEMORIA TEMPORAL
# =====================
NUMEROS_POR_PAGINA = 50

rifas = {}

# =====================
# UTILIDAD: VALIDAR ADMIN
# =====================
async def es_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(
            GRUPO_RIFAS_ID,
            update.effective_user.id
        )
        return member.status in ("administrator", "creator")
    except:
        return False

# =====================
# MENÚ PRINCIPAL
# =====================
async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal con botones de navegación"""
    user_id = update.effective_user.id if hasattr(update, 'effective_user') else update.from_user.id
    
    keyboard = [
        [InlineKeyboardButton("🧑 Registrarse", callback_data="empezar")],
        [InlineKeyboardButton("🎟️ Ver rifas disponibles", callback_data="ver_rifas")],
        [InlineKeyboardButton("🎫 Mis boletas", callback_data="ir_misboletas")],
    ]
    
    # Agregar botón admin si es admin
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Panel Admin", callback_data="ir_admin")])
    
    texto = "📱 *MENÚ PRINCIPAL*\n\nSelecciona una opción:"
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(
            texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# =====================
# BLOQUEAR MENSAJES EN GRUPO
# =====================
async def bloquear_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return

# =====================
# COMANDO DEL GRUPO
# =====================
async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GRUPO_RIFAS_ID:
        return

    keyboard = [
        [InlineKeyboardButton("🎟️ Reservar números", url="https://t.me/QuicksortCol_bot")]
    ]

    await update.message.reply_text(
        "🎉 ¿Quieres participar en la rifa?\n\nPulsa el botón para reservar tus números 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# CHAT PRIVADO - START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    await update.message.reply_text(
        "👋 Bienvenido al bot de rifas.\n\n¡Qué gusto verte por aquí! 🎉",
        parse_mode="Markdown"
    )
    
    await menu_principal(update, context)

# =====================
# REGISTRO DE USUARIO
# =====================
async def empezar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "📝 Escribe tu *nombre completo*:",
        parse_mode="Markdown"
    )
    return NOMBRE

async def ir_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("⛔ No autorizado")
        return
    
    await admin_panel(query, context)

async def ir_misboletas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await mis_boletas_callback(query, context)

async def nueva_compra_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia flujo de nueva compra desde el botón"""
    query = update.callback_query
    await query.answer()
    
    # Verificar que el usuario esté registrado
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("SELECT nombre FROM usuarios WHERE user_id = %s", (query.from_user.id,))
        usuario = cursor.fetchone()
    finally:
        return_db(db)
    
    if not usuario:
        # Usuario no registrado, iniciar registro
        await query.message.reply_text(
            "📝 Primero necesitamos tus datos. Escribe tu *nombre completo*:",
            parse_mode="Markdown"
        )
        return NOMBRE
    
    # Usuario ya registrado, mostrar rifas
    await mostrar_rifas_para_compra(update, context)

async def menu_principal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botón para volver al menú principal"""
    query = update.callback_query
    await query.answer()
    
    await menu_principal(update, context)

async def ver_rifas_disponibles_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra todas las rifas disponibles con su información"""
    query = update.callback_query
    await query.answer()
    
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT r.id, r.nombre, r.precio, r.total_numeros,
                   COUNT(CASE WHEN n.reservado = 1 THEN 1 END) as reservados
            FROM rifas r
            LEFT JOIN numeros n ON r.id = n.rifa_id
            WHERE r.activa = 1
            GROUP BY r.id, r.nombre, r.precio, r.total_numeros
            ORDER BY r.id DESC
        """)

        rifas_list = cursor.fetchall()
    finally:
        return_db(db)

    if not rifas_list:
        keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="menu_principal")]]
        await query.message.reply_text(
            "❌ No hay rifas activas en este momento.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    texto = "🎟️ *RIFAS DISPONIBLES*\n\n"

    for rifa_id, nombre, precio, total_numeros, reservados in rifas_list:
        disponibles = total_numeros - reservados
        porcentaje_vendido = (reservados / total_numeros * 100) if total_numeros > 0 else 0
        
        texto += (
            f"🎯 *{nombre}*\n"
            f"🆔 ID: {rifa_id}\n"
            f"💵 Precio por boleta: ${precio:,}\n"
            f"📊 Disponibles: {disponibles}/{total_numeros} ({porcentaje_vendido:.1f}% vendido)\n"
            f"──────────────\n\n"
        )
    
    keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="menu_principal")]]

    await query.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    await query.answer()
    
    await menu_principal(update, context)

async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre"] = update.message.text

    await update.message.reply_text(
        "📱 Escribe tu *número de celular*.\n\n"
        "⚠️ Asegúrate de que sea correcto.",
        parse_mode="Markdown"
    )
    return TELEFONO

async def recibir_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefono"] = update.message.text

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios 
            (user_id, username, nombre, telefono)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
            username = EXCLUDED.username,
            nombre = EXCLUDED.nombre,
            telefono = EXCLUDED.telefono
        """, (
            update.effective_user.id,
            update.effective_user.username,
            context.user_data["nombre"],
            context.user_data["telefono"]
        ))

        db.commit()
    finally:
        return_db(db)

    await update.message.reply_text(
        "✅ *Datos registrados correctamente*",
        parse_mode="Markdown"
    )

    await mostrar_rifas_para_compra(update, context)
    return ConversationHandler.END

# =====================
# MOSTRAR RIFAS PARA COMPRA
# =====================
async def mostrar_rifas_para_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las rifas disponibles para compra"""
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT id, nombre, precio
            FROM rifas
            WHERE activa = 1
        """)

        rifas_list = cursor.fetchall()
    finally:
        return_db(db)

    if not rifas_list:
        await update.message.reply_text("❌ No hay rifas activas.")
        await menu_principal(update, context)
        return

    texto = "🎟️ *Rifas disponibles:*\n\n"
    keyboard = []

    for rifa_id, nombre, precio in rifas_list:
        texto += (
            f"🆔 ID: {rifa_id}\n"
            f"🎫 {nombre}\n"
            f"💰 Precio: {precio}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"🎟️ {nombre}",
                callback_data=f"rifa_{rifa_id}"
            )
        ])
    
    # Agregar botón para volver al menú
    keyboard.append([InlineKeyboardButton("◀️ Volver", callback_data="menu_principal")])

    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(
            texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# =====================
# MOSTRAR RIFAS (LEGACY)
# =====================
async def mostrar_rifas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias para mantener compatibilidad"""
    await mostrar_rifas_para_compra(update, context)

async def comando_talonario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el admin puede usar este comando.")
        return

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT r.id, r.nombre,
                   COUNT(n.id) as vendidos
            FROM rifas r
            LEFT JOIN numeros n
                ON r.id = n.rifa_id
                AND n.pago_id IN (
                    SELECT id FROM pagos WHERE estado = 'aprobado'
                )
            GROUP BY r.id, r.nombre
        """)

        rifas_list = cursor.fetchall()
    finally:
        return_db(db)

    if not rifas_list:
        await update.message.reply_text("❌ No hay rifas.")
        return

    teclado = []

    for rifa_id, nombre, vendidos in rifas_list:
        teclado.append([
            InlineKeyboardButton(
                f"{nombre} | 🎟️ {vendidos} vendidos",
                callback_data=f"talonario_{rifa_id}"
            )
        ])

    await update.message.reply_text(
        "📒 *¿De qué rifa quieres ver el talonario?*",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def mostrar_talonario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ No autorizado", show_alert=True)
        return

    rifa_id = int(query.data.split("_")[1])

    db = get_db()
    cursor = db.cursor()

    try:
        # Nombre de la rifa
        cursor.execute("SELECT nombre FROM rifas WHERE id = %s", (rifa_id,))
        rifa = cursor.fetchone()

        if not rifa:
            await query.message.reply_text("❌ Rifa no encontrada.")
            return

        nombre_rifa = rifa[0]

        # Talonario
        cursor.execute("""
            SELECT n.numero,
                   u.nombre,
                   u.username,
                   u.telefono
            FROM numeros n
            JOIN pagos p ON n.pago_id = p.id
            JOIN usuarios u ON u.user_id = n.user_id
            WHERE n.rifa_id = %s
            AND p.estado = 'aprobado'
            ORDER BY n.numero
        """, (rifa_id,))

        filas = cursor.fetchall()
    finally:
        return_db(db)

    texto = f"📒 *TALONARIO – {nombre_rifa}*\n\n"

    if not filas:
        texto += "⚠️ Aún no hay números aprobados."
    else:
        for numero, nombre, username, telefono in filas:
            texto += (
                f"{numero:02d} "
                f"{nombre} "
                f"@{username if username else '—'} "
                f"{telefono}\n"
            )

    await query.message.reply_text(texto, parse_mode="Markdown")

def obtener_numeros_pago(pago_id):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT numero
            FROM numeros
            WHERE pago_id = %s
            ORDER BY numero
        """, (pago_id,))

        numeros = [str(n[0]) for n in cursor.fetchall()]
    finally:
        return_db(db)

    return ", ".join(numeros)

async def enviar_comprobante_admin(context, pago_id, user_id, rifa_id, file_id):
    import time

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT username FROM usuarios WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        cursor.execute("SELECT timestamp FROM pagos WHERE id = %s", (pago_id,))
        timestamp = cursor.fetchone()[0]

        cursor.execute("SELECT precio FROM rifas WHERE id = %s", (rifa_id,))
        precio = cursor.fetchone()[0]
    finally:
        return_db(db)

    nombre = user[0] if user else "Sin nombre"
    numeros = obtener_numeros_pago(pago_id)

    cantidad = len(numeros.split(", ")) if numeros else 0
    monto = precio * cantidad

    minutos = int((time.time() - timestamp) / 60)

    texto = (
        "<b>📌 Nuevo comprobante de pago</b>\n\n"
        f"👤 <b>Usuario:</b> {nombre}\n"
        f"🆔 <b>ID:</b> {user_id}\n"
        f"🎟️ <b>Números:</b> {numeros}\n"
        f"� <b>Cantidad:</b> {cantidad} boletas\n"
        f"💵 <b>Valor unitario:</b> ${precio:,}\n"
        f"💰 <b>MONTO ESPERADO:</b> <b>${monto:,}</b>\n"
    )

    if minutos > 10:
        texto += "\n⚠️ <b>Tiempo excedido (+10 min)</b>"

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{pago_id}"),
            InlineKeyboardButton("❌ Liberar", callback_data=f"liberar_{pago_id}")
        ]
    ])

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=file_id,
        caption=texto,
        parse_mode="HTML",
        reply_markup=teclado
    )

# =====================
# MOSTRAR NÚMEROS
# =====================
async def elegir_rifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rifa_id = int(query.data.split("_")[1])

    context.user_data["rifa_id"] = rifa_id
    context.user_data["seleccionados"] = set()
    context.user_data["pagina"] = 0

    await mostrar_numeros(query, context)

async def toggle_numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    numero = int(query.data.split("_")[1])
    seleccionados = context.user_data.setdefault("seleccionados", set())

    if numero in seleccionados:
        seleccionados.remove(numero)
    else:
        seleccionados.add(numero)

    await mostrar_numeros(query, context)

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rifa_id = context.user_data.get("rifa_id")
    seleccionados = context.user_data.get("seleccionados", set())
    user_id = update.effective_user.id

    if not seleccionados:
        await query.message.reply_text("❌ No seleccionaste números.")
        return

    import time
    timestamp = int(time.time())

    db = get_db()
    cursor = db.cursor()

    try:
        # Obtener precio de la rifa
        cursor.execute("SELECT precio FROM rifas WHERE id = %s", (rifa_id,))
        precio_result = cursor.fetchone()
        precio = precio_result[0] if precio_result else 0
        
        # 🔒 Verificar que sigan libres
        placeholders = ",".join(["%s"] * len(seleccionados))
        cursor.execute(f"""
            SELECT numero
            FROM numeros
            WHERE rifa_id = %s
            AND numero IN ({placeholders})
            AND reservado = 1
        """, (rifa_id, *seleccionados))

        ocupados = cursor.fetchall()

        if ocupados:
            db.rollback()
            await query.message.reply_text(
                "⛔ Algunos números ya fueron reservados.\n"
                "Actualizando lista…"
            )
            await mostrar_numeros(query, context)
            return

        # 1️⃣ Crear el pago
        cursor.execute("""
            INSERT INTO pagos (user_id, rifa_id, estado, timestamp)
            VALUES (%s, %s, 'pendiente', %s)
            RETURNING id
        """, (user_id, rifa_id, timestamp))

        pago_id = cursor.fetchone()[0]

        # 2️⃣ Reservar números ligados a ese pago
        cursor.execute(f"""
            UPDATE numeros
            SET reservado = 1,
                user_id = %s,
                pago_id = %s
            WHERE rifa_id = %s
            AND numero IN ({placeholders})
        """, (user_id, pago_id, rifa_id, *seleccionados))

        db.commit()
    finally:
        return_db(db)

    # Calcular monto total
    cantidad_numeros = len(seleccionados)
    monto_total = precio * cantidad_numeros

    # Eliminar el mensaje con la tabla de números
    try:
        await query.message.delete()
    except:
        pass

    await query.message.reply_text(
        "✅ *RESERVA CONFIRMADA*\n\n"
        f"🎟️ *Números elegidos:* {', '.join(map(str, sorted(seleccionados)))}\n"
        f"🔢 *Cantidad de boletas:* {cantidad_numeros}\n"
        f"💵 *Valor unitario:* ${precio:,}\n"
        f"💰 *TOTAL A PAGAR:* ${monto_total:,}\n\n"
        "*Métodos de pago:*\n"
        "🏦 BANCOLOMBIA: `91952487464`\n"
        "📲 NEQUI: `3217895801`\n\n"
        "📸 *Envía ahora el comprobante de pago (foto).*\n"
        "⏳ Tienes *10 minutos* para enviarlo.",
        parse_mode="Markdown"
    )

    context.user_data.clear()

async def ir_pag_0(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["pagina"] = 0
    await mostrar_numeros(query, context)

async def ir_pag_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["pagina"] = 1
    await mostrar_numeros(query, context)

async def mostrar_numeros(query, context: ContextTypes.DEFAULT_TYPE):
    rifa_id = context.user_data["rifa_id"]
    seleccionados = context.user_data.get("seleccionados", set())

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT nombre, precio
            FROM rifas
            WHERE id = %s
        """, (rifa_id,))
        rifa = cursor.fetchone()

        cursor.execute("""
            SELECT numero, reservado
            FROM numeros
            WHERE rifa_id = %s
            ORDER BY numero
        """, (rifa_id,))
        numeros = cursor.fetchall()
    finally:
        return_db(db)

    pagina = context.user_data.get("pagina", 0)

    if pagina == 0:
        numeros = numeros[:50]
    else:
        numeros = numeros[50:100]

    texto = (
        f"🎟️ *{rifa[0]}*\n"
        f"💰 Precio: {rifa[1]}\n\n"
    )

    if seleccionados:
        texto += (
            "🟡 *Seleccionados:* "
            + ", ".join(map(str, sorted(seleccionados)))
            + "\n\n"
        )

    texto += "Selecciona tus números:\n"

    keyboard = []
    fila = []

    for numero, reservado in numeros:
        if reservado:
            btn_text = f"🔴 {numero}"
            data = "no_disponible"
        elif numero in seleccionados:
            btn_text = f"🟡 {numero}"
            data = f"toggle_{numero}"
        else:
            btn_text = f"⚪ {numero}"
            data = f"toggle_{numero}"

        fila.append(InlineKeyboardButton(btn_text, callback_data=data))

        if len(fila) == 5:
            keyboard.append(fila)
            fila = []

    if fila:
        keyboard.append(fila)

    nav = []

    if pagina == 1:
        nav.append(
            InlineKeyboardButton("⬅️ 0–49", callback_data="pag_0")
        )

    nav.append(
        InlineKeyboardButton("✅ Confirmar", callback_data="confirmar")
    )

    if pagina == 0:
        nav.append(
            InlineKeyboardButton("➡️ 50–99", callback_data="pag_1")
        )

    keyboard.append(nav)

    await query.message.edit_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def mis_boletas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT p.id, r.nombre, p.estado, p.timestamp
            FROM pagos p
            JOIN rifas r ON r.id = p.rifa_id
            WHERE p.user_id = %s AND p.estado = 'aprobado'
            ORDER BY p.timestamp DESC
        """, (user_id,))

        pagos = cursor.fetchall()

        if not pagos:
            msg = (
                "📭 *No tienes compras registradas aún.*"
            )
            if hasattr(update, 'message'):
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.reply_text(msg, parse_mode="Markdown")
            return

        texto = "🎟️ *MIS BOLETAS*\n\n"

        import time
        from datetime import datetime

        for pago_id, rifa_nombre, estado, timestamp in pagos:
            cursor.execute("""
                SELECT numero
                FROM numeros
                WHERE pago_id = %s
                ORDER BY numero
            """, (pago_id,))

            numeros = [str(n[0]) for n in cursor.fetchall()]
            fecha = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")

            estado_txt = {
                "pendiente": "⏳ Pendiente de pago",
                "en_revision": "🔍 En revisión",
                "aprobado": "✅ Aprobado",
                "rechazado": "❌ Rechazado"
            }.get(estado, estado)

            texto += (
                f"🎫 *Rifa:* {rifa_nombre}\n"
                f"🎟️ *Números:* {', '.join(numeros) if numeros else '—'}\n"
                f"💳 *Estado:* {estado_txt}\n"
                f"🕒 *Fecha:* {fecha}\n"
                "──────────────\n"
            )
    finally:
        return_db(db)

    if hasattr(update, 'message'):
        await update.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.reply_text(texto, parse_mode="Markdown")

async def mis_boletas_callback(query, context: ContextTypes.DEFAULT_TYPE):
    """Versión para callback de mis_boletas"""
    user_id = query.from_user.id

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT p.id, r.nombre, p.estado, p.timestamp
            FROM pagos p
            JOIN rifas r ON r.id = p.rifa_id
            WHERE p.user_id = %s AND p.estado = 'aprobado'
            ORDER BY p.timestamp DESC
        """, (user_id,))

        pagos = cursor.fetchall()

        if not pagos:
            keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="menu_principal")]]
            await query.message.reply_text(
                "📭 *No tienes compras registradas aún.*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        texto = "🎟️ *MIS BOLETAS*\n\n"

        import time
        from datetime import datetime

        for pago_id, rifa_nombre, estado, timestamp in pagos:
            cursor.execute("""
                SELECT numero
                FROM numeros
                WHERE pago_id = %s
                ORDER BY numero
            """, (pago_id,))

            numeros = [str(n[0]) for n in cursor.fetchall()]
            fecha = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")

            estado_txt = {
                "pendiente": "⏳ Pendiente de pago",
                "en_revision": "🔍 En revisión",
                "aprobado": "✅ Aprobado",
                "rechazado": "❌ Rechazado"
            }.get(estado, estado)

            texto += (
                f"🎫 *Rifa:* {rifa_nombre}\n"
                f"🎟️ *Números:* {', '.join(numeros) if numeros else '—'}\n"
                f"💳 *Estado:* {estado_txt}\n"
                f"🕒 *Fecha:* {fecha}\n"
                "──────────────\n"
            )
    finally:
        return_db(db)

    keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="menu_principal")]]
    await query.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

def get_estadisticas_rifa(rifa_id):
    db = get_db()
    cursor = db.cursor()

    try:
        # Total números
        cursor.execute("""
            SELECT total_numeros FROM rifas WHERE id = %s
        """, (rifa_id,))
        total = cursor.fetchone()[0]

        # Pagos por estado
        cursor.execute("""
            SELECT estado, COUNT(*) 
            FROM pagos
            WHERE rifa_id = %s
            GROUP BY estado
        """, (rifa_id,))

        pagos = {
            "pendiente": 0,
            "en_revision": 0,
            "aprobado": 0,
            "rechazado": 0,
            "expirado": 0
        }

        for estado, cantidad in cursor.fetchall():
            pagos[estado] = cantidad

        # Números vendidos (pagos aprobados)
        cursor.execute("""
            SELECT COUNT(*)
            FROM numeros
            WHERE rifa_id = %s
            AND pago_id IN (
                SELECT id FROM pagos WHERE estado = 'aprobado'
            )
        """, (rifa_id,))
        vendidos = cursor.fetchone()[0]

        # Números reservados (pendiente / en revisión)
        cursor.execute("""
            SELECT COUNT(*)
            FROM numeros
            WHERE rifa_id = %s
            AND pago_id IN (
                SELECT id FROM pagos
                WHERE estado IN ('pendiente', 'en_revision')
            )
        """, (rifa_id,))
        reservados = cursor.fetchone()[0]

        libres = total - vendidos - reservados
    finally:
        return_db(db)

    return {
        "total": total,
        "vendidos": vendidos,
        "reservados": reservados,
        "libres": libres,
        "pagos": pagos
    }

async def stats_rifa(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No autorizado.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usa: /stats_rifa <id_rifa>")
        return

    rifa_id = int(context.args[0])
    stats = get_estadisticas_rifa(rifa_id)

    texto = (
        f"📊 *Estadísticas – Rifa #{rifa_id}*\n\n"
        f"🎟 Total números: *{stats['total']}*\n"
        f"🟢 Vendidos: *{stats['vendidos']}*\n"
        f"🟡 Reservados: *{stats['reservados']}*\n"
        f"⚪ Libres: *{stats['libres']}*\n\n"
        f"💰 *Pagos*\n"
        f"✅ Aprobados: *{stats['pagos']['aprobado']}*\n"
        f"⏳ En revisión: *{stats['pagos']['en_revision']}*\n"
        f"🕒 Pendientes: *{stats['pagos']['pendiente']}*\n"
        f"❌ Rechazados: *{stats['pagos']['rechazado']}*\n"
        f"⏰ Expirados: *{stats['pagos']['expirado']}*"
    )

    await update.message.reply_text(texto, parse_mode="Markdown")

async def expirar_pagos_y_liberar_job(context: ContextTypes.DEFAULT_TYPE):
    import time
    ahora = int(time.time())

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT id, user_id, timestamp
            FROM pagos
            WHERE estado = 'pendiente'
        """)

        pagos = cursor.fetchall()

        for pago_id, user_id, timestamp in pagos:
            minutos = (ahora - timestamp) // 60

            if minutos >= 10:
                # Liberar números
                cursor.execute("""
                    UPDATE numeros
                    SET reservado = 0,
                        user_id = NULL,
                        pago_id = NULL
                    WHERE pago_id = %s
                """, (pago_id,))

                # Marcar como expirado
                cursor.execute("""
                    UPDATE pagos
                    SET estado = 'expirado'
                    WHERE id = %s
                """, (pago_id,))

                # Avisar al usuario
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "⏱ *Tiempo expirado*\n\n"
                            "No enviaste el comprobante dentro de los 10 minutos.\n"
                            "🎟️ Los números fueron liberados automáticamente.\n\n"
                            "Si deseas participar nuevamente, escribe /start."
                        ),
                        parse_mode="Markdown"
                    )
                except:
                    pass

        db.commit()
    finally:
        return_db(db)

# =====================
# CREACIÓN DE RIFAS (ADMIN)
# =====================
async def crear_rifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text("❌ Usa este comando en privado.")
        return ConversationHandler.END

    if not await es_admin(update, context):
        await update.message.reply_text("⛔ No tienes permisos.")
        return ConversationHandler.END

    await update.message.reply_text(
        "🎟️ *Creación de rifa*\n\nEscribe el *nombre de la rifa*:",
        parse_mode="Markdown"
    )
    return RIFA_NOMBRE

async def rifa_nombre(update, context):
    # Inicializar si no existe (por si viene del callback)
    if "rifa" not in context.user_data:
        context.user_data["rifa"] = {}
    
    context.user_data["rifa"]["nombre"] = update.message.text
    await update.message.reply_text("💰 Precio por boleta:")
    return RIFA_PRECIO

async def rifa_precio(update, context):
    if "rifa" not in context.user_data:
        context.user_data["rifa"] = {}
    context.user_data["rifa"]["precio"] = update.message.text
    await update.message.reply_text("🏆 Premio de la rifa:")
    return RIFA_PREMIO

async def rifa_premio(update, context):
    if "rifa" not in context.user_data:
        context.user_data["rifa"] = {}
    context.user_data["rifa"]["premio"] = update.message.text
    await update.message.reply_text("📅 Fecha del sorteo:")
    return RIFA_FECHA

async def rifa_fecha(update, context):
    if "rifa" not in context.user_data:
        context.user_data["rifa"] = {}
    context.user_data["rifa"]["fecha"] = update.message.text
    await update.message.reply_text(
        "📝 Descripción (o escribe *ninguna*):",
        parse_mode="Markdown"
    )
    return RIFA_DESC

async def rifa_desc(update, context):
    if "rifa" not in context.user_data:
        await update.message.reply_text("❌ Error: sesión expirada. Intenta de nuevo.")
        return ConversationHandler.END
    
    rifa = context.user_data["rifa"]

    db = get_db()
    cursor = db.cursor()

    try:
        # 1️⃣ Insertar rifa
        cursor.execute("""
            INSERT INTO rifas (nombre, precio, total_numeros)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (
            rifa["nombre"],
            int(rifa["precio"]),
            100
        ))

        rifa_id = cursor.fetchone()[0]

        # 2️⃣ Crear los números (0 al 99)
        for i in range(0, 100):
            cursor.execute("""
                INSERT INTO numeros (rifa_id, numero)
                VALUES (%s, %s)
            """, (rifa_id, i))

        db.commit()
    finally:
        return_db(db)

    await update.message.reply_text(
        f"✅ *Rifa creada correctamente*\n\n"
        f"🆔 ID: {rifa_id}\n"
        f"🎫 {rifa['nombre']}",
        parse_mode="Markdown"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")]]
    await update.message.reply_text(
        "¿Qué deseas hacer ahora?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ConversationHandler.END

async def recibir_comprobante(update, context):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file_id = photo.file_id

    import time
    ahora = int(time.time())

    db = get_db()
    cursor = db.cursor()

    try:
        # Validar que hay un pago pendiente
        cursor.execute("""
            SELECT id, rifa_id, timestamp, estado
            FROM pagos
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (user_id,))

        pago = cursor.fetchone()

        if not pago:
            await update.message.reply_text(
                "❌ No tienes ningún pago pendiente.\n\n"
                "Escribe /start para comenzar nuevamente."
            )
            return
        
        pago_id, rifa_id, inicio, estado = pago
        
        # Solo aceptar comprobante si el pago está en estado "pendiente"
        if estado != "pendiente":
            await update.message.reply_text(
                "⚠️ No puedes enviar comprobante ahora.\n\n"
                "Escribe /start para hacer una nueva compra."
            )
            return

        minutos = (ahora - inicio) // 60

        if minutos >= 10:
            await update.message.reply_text(
                "⏱ *Tiempo expirado*\n\n"
                "El plazo para enviar el comprobante terminó.\n"
                "🎟️ Los números ya fueron liberados.\n\n"
                "Para participar nuevamente escribe /start.",
                parse_mode="Markdown"
            )
            return

        cursor.execute("""
            UPDATE pagos
            SET comprobante = %s, estado = 'en_revision'
            WHERE id = %s
        """, (file_id, pago_id))

        db.commit()
    finally:
        return_db(db)

    await enviar_comprobante_admin(
        context,
        pago_id,
        user_id,
        rifa_id,
        file_id
    )

    await update.message.reply_text(
        "📸 *Comprobante recibido*\n\n"
        "⏳ El administrador lo revisará.",
        parse_mode="Markdown"
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Manejar tanto Update como CallbackQuery
    if hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
    else:
        user_id = update.from_user.id
    
    if user_id != ADMIN_ID:
        if hasattr(update, 'message'):
            await update.message.reply_text("⛔ Acceso denegado")
        else:
            await update.callback_query.message.reply_text("⛔ Acceso denegado")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_stats")],
        [InlineKeyboardButton("📥 Pagos pendientes", callback_data="admin_pagos")],
        [InlineKeyboardButton("📒 Talonario", callback_data="admin_talonario")],
        [InlineKeyboardButton("📄 PDF Talonario", callback_data="admin_pdf_talonario")],
        [InlineKeyboardButton("🖼️ Imagen Talonario", callback_data="admin_imagen_talonario")],
        [InlineKeyboardButton("🎟️ Crear rifa", callback_data="admin_crear_rifa")],
        [InlineKeyboardButton("🗑️ Eliminar rifa", callback_data="admin_eliminar_rifa")],
        [InlineKeyboardButton("◀️ Volver", callback_data="menu_principal")],
    ]

    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            "🛠 *PANEL ADMIN*\n\nSelecciona una opción:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.message.reply_text(
            "🛠 *PANEL ADMIN*\n\nSelecciona una opción:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def admin_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT r.id, r.nombre,
            COUNT(n.id),
            SUM(CASE WHEN n.reservado = 1 THEN 1 ELSE 0 END)
            FROM rifas r
            LEFT JOIN numeros n ON r.id = n.rifa_id
            GROUP BY r.id, r.nombre
        """)

        texto = "📊 *ESTADÍSTICAS*\n\n"
        for rifa_id, nombre, total, reservados in cursor.fetchall():
            reservados = reservados or 0
            texto += (
                f"🎯 *{nombre}*\n"
                f"Total: {total}\n"
                f"Reservados: {reservados}\n"
                f"Libres: {total - reservados}\n\n"
            )
    finally:
        return_db(db)

    keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")]]
    await query.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_pagos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT id, user_id, rifa_id
            FROM pagos
            WHERE estado = 'en_revision'
        """)

        pagos = cursor.fetchall()
    finally:
        return_db(db)

    if not pagos:
        keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")]]
        await query.message.reply_text(
            "✅ No hay pagos pendientes.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    for pago_id, user_id, rifa_id in pagos:
        keyboard = [
            [
                InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{pago_id}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{pago_id}")
            ]
        ]

        await query.message.reply_text(
            f"💳 *Pago ID:* {pago_id}\n"
            f"👤 Usuario: `{user_id}`\n"
            f"🎟 Rifa: `{rifa_id}`",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def admin_talonario_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback para ver el talonario desde el panel admin"""
    query = update.callback_query
    await query.answer()
    
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT r.id, r.nombre,
                   COUNT(n.id) as vendidos
            FROM rifas r
            LEFT JOIN numeros n
                ON r.id = n.rifa_id
                AND n.pago_id IN (
                    SELECT id FROM pagos WHERE estado = 'aprobado'
                )
            GROUP BY r.id, r.nombre
        """)

        rifas_list = cursor.fetchall()
    finally:
        return_db(db)

    if not rifas_list:
        keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")]]
        await query.message.reply_text(
            "❌ No hay rifas.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    teclado = []

    for rifa_id, nombre, vendidos in rifas_list:
        teclado.append([
            InlineKeyboardButton(
                f"{nombre} | 🎟️ {vendidos} vendidos",
                callback_data=f"talonario_{rifa_id}"
            )
        ])
    
    teclado.append([InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")])

    await query.message.reply_text(
        "📒 *¿De qué rifa quieres ver el talonario?*",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def admin_crear_rifa_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback para crear rifa desde el panel admin - Entry point del ConversationHandler"""
    query = update.callback_query
    await query.answer()
    
    # Reinicializar el estado de la rifa
    context.user_data["rifa"] = {}
    
    await query.message.reply_text(
        "🎟️ *Creación de rifa*\n\nEscribe el *nombre de la rifa*:",
        parse_mode="Markdown"
    )
    return RIFA_NOMBRE

async def admin_eliminar_rifa_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback para eliminar rifa desde el panel admin"""
    query = update.callback_query
    await query.answer()
    
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT id, nombre FROM rifas")
        rifas_list = cursor.fetchall()
    finally:
        return_db(db)

    if not rifas_list:
        keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")]]
        await query.message.reply_text(
            "❌ No hay rifas para eliminar.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    teclado = []
    for rifa_id, nombre in rifas_list:
        teclado.append([
            InlineKeyboardButton(
                f"🗑️ {nombre}",
                callback_data=f"confirmar_eliminar_{rifa_id}"
            )
        ])
    
    teclado.append([InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")])

    await query.message.reply_text(
        "🗑️ *Selecciona la rifa a eliminar:*",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def confirmar_eliminar_rifa_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirmar eliminación de rifa"""
    query = update.callback_query
    await query.answer()

    rifa_id = int(query.data.split("_")[2])

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT nombre FROM rifas WHERE id = %s", (rifa_id,))
        rifa = cursor.fetchone()

        if not rifa:
            await query.message.reply_text("❌ Rifa no encontrada.")
            return

        # Eliminar la rifa (CASCADE elimina números y pagos)
        cursor.execute("DELETE FROM rifas WHERE id = %s", (rifa_id,))
        db.commit()
    finally:
        return_db(db)

    keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")]]
    await query.message.reply_text(
        f"✅ Rifa *{rifa[0]}* eliminada correctamente.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_pdf_talonario_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback para generar PDF del talonario desde el panel admin"""
    query = update.callback_query
    await query.answer()
    
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT r.id, r.nombre,
                   COUNT(n.id) as vendidos
            FROM rifas r
            LEFT JOIN numeros n
                ON r.id = n.rifa_id
                AND n.pago_id IN (
                    SELECT id FROM pagos WHERE estado = 'aprobado'
                )
            GROUP BY r.id, r.nombre
        """)

        rifas_list = cursor.fetchall()
    finally:
        return_db(db)

    if not rifas_list:
        keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")]]
        await query.message.reply_text(
            "❌ No hay rifas.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    teclado = []

    for rifa_id, nombre, vendidos in rifas_list:
        teclado.append([
            InlineKeyboardButton(
                f"📄 {nombre} | 🎟️ {vendidos} vendidos",
                callback_data=f"generar_pdf_{rifa_id}"
            )
        ])
    
    teclado.append([InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")])

    await query.message.reply_text(
        "📄 *¿De qué rifa quieres generar el PDF del talonario?*",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def generar_pdf_talonario_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera PDF del talonario de una rifa"""
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ No autorizado", show_alert=True)
        return

    rifa_id = int(query.data.split("_")[2])

    await query.message.reply_text("⏳ Generando PDF del talonario...")

    try:
        pdf_path = await generar_pdf_talonario(rifa_id)
        
        # Enviar PDF al admin
        with open(pdf_path, 'rb') as pdf_file:
            await query.message.reply_document(
                document=pdf_file,
                caption="📄 *Talonario de la rifa*",
                parse_mode="Markdown"
            )
        
        # Eliminar archivo temporal
        import os
        os.remove(pdf_path)
        
    except Exception as e:
        await query.message.reply_text(f"❌ Error al generar PDF: {str(e)}")

async def generar_pdf_talonario(rifa_id):
    """Genera el archivo PDF del talonario"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from datetime import datetime
    import tempfile
    import os

    db = get_db()
    cursor = db.cursor()

    try:
        # Información de la rifa
        cursor.execute("SELECT nombre FROM rifas WHERE id = %s", (rifa_id,))
        rifa = cursor.fetchone()

        if not rifa:
            raise Exception("Rifa no encontrada")

        nombre_rifa = rifa[0]

        # Talonario completo
        cursor.execute("""
            SELECT n.numero,
                   COALESCE(u.nombre, 'DISPONIBLE') as nombre,
                   COALESCE(u.username, '') as username,
                   COALESCE(u.telefono, '') as telefono,
                   CASE 
                       WHEN p.estado = 'aprobado' THEN 'VENDIDO'
                       WHEN p.estado = 'pendiente' THEN 'RESERVADO'
                       WHEN p.estado = 'en_revision' THEN 'EN REVISIÓN'
                       ELSE 'DISPONIBLE'
                   END as estado
            FROM numeros n
            LEFT JOIN pagos p ON n.pago_id = p.id
            LEFT JOIN usuarios u ON u.user_id = n.user_id
            WHERE n.rifa_id = %s
            ORDER BY n.numero
        """, (rifa_id,))

        datos = cursor.fetchall()
    finally:
        return_db(db)

    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.close()

    # Crear PDF
    doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centrado
    )

    story.append(Paragraph(f"TALONARIO - {nombre_rifa}", title_style))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Tabla de datos
    table_data = [['#', 'Nombre', 'Usuario', 'Teléfono', 'Estado']]
    
    for numero, nombre, username, telefono, estado in datos:
        table_data.append([
            str(numero).zfill(2),
            nombre[:20],  # Limitar longitud
            f"@{username[:15]}" if username else "",
            telefono[:15],
            estado
        ])

    # Crear tabla
    table = Table(table_data, colWidths=[0.5*inch, 2*inch, 1.5*inch, 1.5*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))

    story.append(table)
    doc.build(story)

    return temp_file.name

async def admin_imagen_talonario_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback para generar imagen del talonario desde el panel admin"""
    query = update.callback_query
    await query.answer()
    
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT r.id, r.nombre,
                   COUNT(n.id) as vendidos
            FROM rifas r
            LEFT JOIN numeros n
                ON r.id = n.rifa_id
                AND n.pago_id IN (
                    SELECT id FROM pagos WHERE estado = 'aprobado'
                )
            GROUP BY r.id, r.nombre
        """)

        rifas_list = cursor.fetchall()
    finally:
        return_db(db)

    if not rifas_list:
        keyboard = [[InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")]]
        await query.message.reply_text(
            "❌ No hay rifas.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    teclado = []

    for rifa_id, nombre, vendidos in rifas_list:
        teclado.append([
            InlineKeyboardButton(
                f"🖼️ {nombre} | 🎟️ {vendidos} vendidos",
                callback_data=f"generar_imagen_{rifa_id}"
            )
        ])
    
    teclado.append([InlineKeyboardButton("◀️ Volver", callback_data="ir_admin")])

    await query.message.reply_text(
        "🖼️ *¿De qué rifa quieres generar la imagen del talonario?*",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown"
    )

async def generar_imagen_talonario_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera imagen del talonario de una rifa"""
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ No autorizado", show_alert=True)
        return

    rifa_id = int(query.data.split("_")[2])

    await query.message.reply_text("⏳ Generando imagen del talonario...")

    try:
        imagen_path = await generar_imagen_talonario(rifa_id)
        
        # Enviar imagen al admin
        with open(imagen_path, 'rb') as imagen_file:
            await query.message.reply_photo(
                photo=imagen_file,
                caption="🖼️ *Talonario visual de la rifa*\n\n🟢 = Disponible\n🔴 = Vendido\n🟡 = Reservado\n🟠 = En Revisión",
                parse_mode="Markdown"
            )
        
        # Eliminar archivo temporal
        import os
        os.remove(imagen_path)
        
    except Exception as e:
        await query.message.reply_text(f"❌ Error al generar imagen: {str(e)}")

async def generar_imagen_talonario(rifa_id):
    """Genera la imagen visual del talonario"""
    from PIL import Image, ImageDraw, ImageFont
    import tempfile
    import os

    db = get_db()
    cursor = db.cursor()

    try:
        # Información de la rifa
        cursor.execute("SELECT nombre FROM rifas WHERE id = %s", (rifa_id,))
        rifa = cursor.fetchone()

        if not rifa:
            raise Exception("Rifa no encontrada")

        nombre_rifa = rifa[0]

        # Obtener números y sus estados
        cursor.execute("""
            SELECT n.numero,
                   CASE 
                       WHEN p.estado = 'aprobado' THEN 'VENDIDO'
                       WHEN p.estado = 'pendiente' THEN 'RESERVADO'
                       WHEN p.estado = 'en_revision' THEN 'EN_REVISION'
                       ELSE 'DISPONIBLE'
                   END as estado
            FROM numeros n
            LEFT JOIN pagos p ON n.pago_id = p.id
            WHERE n.rifa_id = %s
            ORDER BY n.numero
        """, (rifa_id,))

        numeros_data = cursor.fetchall()
    finally:
        return_db(db)

    # Crear diccionario de estados
    estados = {num[0]: num[1] for num in numeros_data}

    # Ruta de la imagen base diseñada
    base_dir = os.path.dirname(__file__)
    base_path = os.path.join(base_dir, "Tabla diseñada.png")

    # Abrir imagen base y preparar para dibujar overlays
    img = Image.open(base_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Parámetros de la cuadrícula (coordenadas exactas medidas - NUEVA IMAGEN)
    TABLE_X0 = 95      # borde izquierdo de la tabla
    TABLE_Y0 = 360      # borde superior de la tabla
    CELL_W = 82         # ancho de celda
    CELL_H = 102        # alto de celda

    # Colores para las marcas (RGBA)
    colores_estado = {
        'VENDIDO': (229, 57, 53, 255),      # rojo
        'RESERVADO': (251, 192, 45, 255),   # amarillo
        'EN_REVISION': (251, 140, 0, 255)   # naranja
    }

    # Tamaños de marcas (proporcionales al tamaño de celda)
    marca_offset = 15   # tamaño de la X vendida
    marca_radio = 12    # radio de círculos
    marca_width = 3     # grosor de líneas

    # Dibujar marcas sobre la imagen base (00-99)
    for num in range(0, 100):
        fila = num // 10
        columna = num % 10

        # Centro geométrico de la celda
        centro_x = int(TABLE_X0 + columna * CELL_W + CELL_W / 2)
        centro_y = int(TABLE_Y0 + fila * CELL_H + CELL_H / 2)

        estado = estados.get(num, 'DISPONIBLE')

        # Marcar según estado
        if estado == 'VENDIDO':
            # X roja
            draw.line([(centro_x - marca_offset, centro_y - marca_offset), 
                      (centro_x + marca_offset, centro_y + marca_offset)], 
                     fill=colores_estado['VENDIDO'], width=marca_width)
            draw.line([(centro_x - marca_offset, centro_y + marca_offset), 
                      (centro_x + marca_offset, centro_y - marca_offset)], 
                     fill=colores_estado['VENDIDO'], width=marca_width)
        elif estado == 'RESERVADO':
            # Círculo amarillo
            draw.ellipse([(centro_x - marca_radio, centro_y - marca_radio), 
                         (centro_x + marca_radio, centro_y + marca_radio)], 
                        outline=colores_estado['RESERVADO'], width=marca_width)
        elif estado == 'EN_REVISION':
            # Círculo naranja con línea horizontal
            draw.ellipse([(centro_x - marca_radio, centro_y - marca_radio), 
                         (centro_x + marca_radio, centro_y + marca_radio)], 
                        outline=colores_estado['EN_REVISION'], width=marca_width)
            draw.line([(centro_x - marca_radio, centro_y), 
                      (centro_x + marca_radio, centro_y)], 
                     fill=colores_estado['EN_REVISION'], width=marca_width)

    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_file.close()
    
    # Guardar imagen
    img.save(temp_file.name, 'PNG')
    
    return temp_file.name

async def approbar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pago_id = int(query.data.split("_")[1])

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            UPDATE pagos SET estado = 'aprobado' WHERE id = %s
        """, (pago_id,))

        db.commit()
    finally:
        return_db(db)

    await query.message.reply_text("✅ Pago aprobado correctamente.")

async def rechazar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pago_id = int(query.data.split("_")[1])

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            UPDATE numeros
            SET reservado = 0, user_id = NULL, pago_id = NULL
            WHERE pago_id = %s
        """, (pago_id,))

        cursor.execute("""
            UPDATE pagos SET estado = 'rechazado' WHERE id = %s
        """, (pago_id,))

        db.commit()
    finally:
        return_db(db)

    await query.message.reply_text("❌ Pago rechazado y números liberados.")

async def eliminar_rifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No autorizado.")
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ Uso correcto:\n/eliminar_rifa <id_rifa>"
        )
        return

    try:
        rifa_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ El ID debe ser un número.")
        return

    db = get_db()
    cursor = db.cursor()

    try:
        # Verificar que la rifa exista
        cursor.execute(
            "SELECT nombre FROM rifas WHERE id = %s",
            (rifa_id,)
        )
        rifa = cursor.fetchone()

        if not rifa:
            await update.message.reply_text("❌ La rifa no existe.")
            return

        nombre_rifa = rifa[0]

        # 🧨 BORRADO TOTAL
        cursor.execute("DELETE FROM numeros WHERE rifa_id = %s", (rifa_id,))
        cursor.execute("DELETE FROM pagos WHERE rifa_id = %s", (rifa_id,))
        cursor.execute("DELETE FROM rifas WHERE id = %s", (rifa_id,))

        db.commit()
    finally:
        return_db(db)

    await update.message.reply_text(
        "🧨 *RIFA ELIMINADA CORRECTAMENTE*\n\n"
        f"🎟️ Rifa: *{nombre_rifa}*\n"
        f"🆔 ID: `{rifa_id}`\n\n"
        "📉 Todos los números, pagos y reservas fueron eliminados.",
        parse_mode="Markdown"
    )

async def acciones_admin(update, context):
    query = update.callback_query
    await query.answer()

    accion, pago_id = query.data.split("_")
    pago_id = int(pago_id)

    db = get_db()
    cursor = db.cursor()

    try:
        # Obtener datos del pago
        cursor.execute("""
            SELECT user_id, rifa_id
            FROM pagos
            WHERE id = %s
        """, (pago_id,))
        pago = cursor.fetchone()

        if not pago:
            await query.edit_message_caption("❌ Pago no encontrado.")
            return

        user_id, rifa_id = pago

        if accion == "aprobar":
            # Obtener números del pago
            cursor.execute("""
                SELECT numero FROM numeros WHERE pago_id = %s ORDER BY numero
            """, (pago_id,))
            numeros = [str(n[0]) for n in cursor.fetchall()]
            numeros_texto = ", ".join(numeros)

            # Aprobar pago
            cursor.execute("""
                UPDATE pagos
                SET estado = 'aprobado'
                WHERE id = %s
            """, (pago_id,))

            db.commit()

            # 📩 Avisar al usuario
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ *Pago APROBADO*\n\n"
                    "🎉 Tu comprobante fue verificado correctamente.\n"
                    f"🎟️ *Tus números:* {numeros_texto}\n"
                    "Tus números ya están asegurados.\n\n"
                    "Puedes comunicarte con el admin si tienes alguna duda\n"
                    "¡Mucha suerte en la rifa! 🍀"
                ),
                parse_mode="Markdown"
            )

            texto_admin = "✅ *Pago APROBADO*"

        else:  # liberar / rechazar
            # Liberar SOLO los números de este pago
            cursor.execute("""
                UPDATE numeros
                SET reservado = 0,
                    user_id = NULL,
                    pago_id = NULL
                WHERE pago_id = %s
            """, (pago_id,))

            cursor.execute("""
                UPDATE pagos
                SET estado = 'rechazado'
                WHERE id = %s
            """, (pago_id,))

            db.commit()

            # 📩 Avisar al usuario
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ *Pago RECHAZADO*\n\n"
                    "🚫 El comprobante no pudo ser validado.\n"
                    "🎟️ Los números de esta compra fueron liberados.\n\n"
                    "Puedes comunicarte con el admin si tienes alguna duda\n"
                    "Puedes intentar comprar nuevamente cuando quieras."
                ),
                parse_mode="Markdown"
            )

            texto_admin = "❌ *Pago RECHAZADO — Números liberados*"

        # Actualizar mensaje del admin
        await query.edit_message_caption(
            caption=texto_admin,
            parse_mode="Markdown"
        )
    finally:
        return_db(db)

# =====================
# CONVERSACIONES
# =====================
async def rechazar_archivo_durante_registro(update, context):
    """Rechaza archivos/fotos durante el registro"""
    await update.message.reply_text(
        "❌ Durante el registro solo puedo recibir texto.\n\n"
        "Por favor, continúa escribiendo la información que te solicito."
    )

user_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(empezar, pattern="^empezar$")],
    states={
        NOMBRE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre),
            MessageHandler(filters.PHOTO | filters.Document.ALL, rechazar_archivo_durante_registro)
        ],
        TELEFONO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_telefono),
            MessageHandler(filters.PHOTO | filters.Document.ALL, rechazar_archivo_durante_registro)
        ],
    },
    fallbacks=[],
    per_message=False,
)

admin_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(admin_crear_rifa_callback, pattern="^admin_crear_rifa$")
    ],
    states={
        RIFA_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, rifa_nombre)],
        RIFA_PRECIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, rifa_precio)],
        RIFA_PREMIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, rifa_premio)],
        RIFA_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, rifa_fecha)],
        RIFA_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, rifa_desc)],
    },
    fallbacks=[],
    per_message=False,
)

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(elegir_rifa, pattern="^rifa_"))

    app.add_handler(
        MessageHandler(filters.ALL & filters.Chat(GRUPO_RIFAS_ID), bloquear_grupo),
        group=1
    )

    app.add_handler(CallbackQueryHandler(toggle_numero, pattern="^toggle_"))
    app.add_handler(CallbackQueryHandler(confirmar, pattern="^confirmar$"))
    app.add_handler(CallbackQueryHandler(ir_pag_0, pattern="^pag_0$"))
    app.add_handler(CallbackQueryHandler(ir_pag_1, pattern="^pag_1$"))
    
    # Nuevos handlers para botones
    app.add_handler(CallbackQueryHandler(ir_admin, pattern="^ir_admin$"))
    app.add_handler(CallbackQueryHandler(ir_misboletas, pattern="^ir_misboletas$"))
    app.add_handler(CallbackQueryHandler(nueva_compra_callback, pattern="^nueva_compra$"))
    app.add_handler(CallbackQueryHandler(menu_principal_callback, pattern="^menu_principal$"))
    app.add_handler(CallbackQueryHandler(ver_rifas_disponibles_callback, pattern="^ver_rifas$"))
    
    # Handlers para admin desde callbacks
    app.add_handler(CallbackQueryHandler(admin_talonario_callback, pattern="^admin_talonario$"))
    app.add_handler(CallbackQueryHandler(admin_pdf_talonario_callback, pattern="^admin_pdf_talonario$"))
    app.add_handler(CallbackQueryHandler(generar_pdf_talonario_callback, pattern="^generar_pdf_"))
    app.add_handler(CallbackQueryHandler(admin_imagen_talonario_callback, pattern="^admin_imagen_talonario$"))
    app.add_handler(CallbackQueryHandler(generar_imagen_talonario_callback, pattern="^generar_imagen_"))
    app.add_handler(CallbackQueryHandler(admin_eliminar_rifa_callback, pattern="^admin_eliminar_rifa$"))
    app.add_handler(CallbackQueryHandler(confirmar_eliminar_rifa_callback, pattern="^confirmar_eliminar_"))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comprar", comprar))

    app.add_handler(user_conv)
    app.add_handler(admin_conv)
    
    app.add_handler(MessageHandler(filters.PHOTO, recibir_comprobante))
    app.add_handler(
        CallbackQueryHandler(acciones_admin, pattern="^(aprobar|liberar)_"))
    app.add_handler(CommandHandler("misboletas", mis_boletas))

    app.add_handler(CommandHandler("estadisticas", stats_rifa))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_estadisticas, pattern="admin_stats"))
    app.add_handler(CallbackQueryHandler(admin_pagos, pattern="admin_pagos"))

    app.add_handler(CallbackQueryHandler(approbar_pago, pattern="aprobar_"))
    app.add_handler(CallbackQueryHandler(rechazar_pago, pattern="rechazar_"))

    app.add_handler(CommandHandler("talonario", comando_talonario))
    app.add_handler(CallbackQueryHandler(mostrar_talonario, pattern="^talonario_"))
    app.add_handler(CommandHandler("eliminar_rifa", eliminar_rifa))

    job_queue = app.job_queue
    job_queue.run_repeating(
        expirar_pagos_y_liberar_job,
        interval=60,
        first=10
    )

    print("🤖 Bot corriendo...")
    app.run_polling()
