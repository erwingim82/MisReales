import flet as ft
import traceback
from datetime import datetime
import urllib.parse 

def main(page: ft.Page):
    try:
        page.title = "Mis Reales"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = ft.colors.BLACK  # Evita el destello negro inicial

        def fmt(valor):
            if valor is None: return "0,00"
            s = f"{float(valor):,.2f}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")

        def parse_float(texto):
            if not texto: return 0.0
            texto = str(texto).strip()
            if "." in texto and "," in texto:
                texto = texto.replace(".", "").replace(",", ".")
            elif "," in texto:
                texto = texto.replace(",", ".")
            return float(texto)

        def notificar(mensaje, color=ft.colors.GREEN_700):
            page.open(ft.SnackBar(ft.Text(mensaje, color=ft.colors.WHITE), bgcolor=color, duration=3000))

        def mostrar_registro():
            page.clean()
            
            txt_nombre = ft.TextField(label="Nombre", border_color=ft.colors.BLUE_400)
            txt_apellido = ft.TextField(label="Apellido", border_color=ft.colors.BLUE_400)
            txt_correo = ft.TextField(label="Correo Electrónico", keyboard_type=ft.KeyboardType.EMAIL, border_color=ft.colors.BLUE_400)
            txt_telefono = ft.TextField(label="Teléfono (Ej: +584140124578)", keyboard_type=ft.KeyboardType.PHONE, border_color=ft.colors.BLUE_400)

            def guardar_usuario(e):
                if not all([txt_nombre.value, txt_apellido.value, txt_correo.value, txt_telefono.value]):
                    return notificar("Por favor completa todos los campos", ft.colors.RED_700)
                
                try:
                    page.client_storage.set("usuario", {
                        "nombre": txt_nombre.value.strip(),
                        "apellido": txt_apellido.value.strip(),
                        "correo": txt_correo.value.strip(),
                        "telefono": txt_telefono.value.strip()
                    })
                    
                    if not page.client_storage.contains_key("movimientos"):
                        page.client_storage.set("movimientos", [])
                        
                    notificar("Perfil creado con éxito", ft.colors.GREEN_700)
                    construir_interfaz_principal()
                except Exception as ex:
                    notificar(f"Error al guardar: {ex}", ft.colors.RED_700)

            tarjeta_registro = ft.Card(
                elevation=8,
                color=ft.colors.with_opacity(0.9, ft.colors.BLUE_GREY_900),
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text("Bienvenido a tu Bitácora", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                        ft.Text("Configura tu perfil para continuar.", size=14, color=ft.colors.WHITE70),
                        ft.Divider(color=ft.colors.TRANSPARENT),
                        txt_nombre, txt_apellido, txt_correo, txt_telefono,
                        ft.FilledButton("Guardar y Entrar", on_click=guardar_usuario, style=ft.ButtonStyle(bgcolor=ft.colors.INDIGO_500), width=300)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            )

            # Fondo seguro con imagen y respaldo de color sólido
            imagen_fondo = ft.Image(src="Fondo.jpeg", fit=ft.ImageFit.COVER, opacity=0.25)
            page.add(ft.Stack([ft.Container(bgcolor=ft.colors.BLACK, expand=True), ft.Container(content=imagen_fondo, expand=True, alignment=ft.alignment.center), ft.Container(content=tarjeta_registro, alignment=ft.alignment.center, padding=20)], expand=True))

        def construir_interfaz_principal():
            page.clean()
            
            saldo_usd_actual = 0.0 
            saldo_bs_actual = 0.0
            
            datos_usuario = page.client_storage.get("usuario")
            if not datos_usuario:
                return mostrar_registro()
                
            dialogo_acerca = ft.AlertDialog(
                title=ft.Text("Acerca de", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                content=ft.Column([
                    ft.Text("Mis Reales", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Versión 1.4\n\nControl y registro de finanzas personales.", size=14, text_align=ft.TextAlign.CENTER),
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                actions=[ft.TextButton("Cerrar", on_click=lambda e: page.close(dialogo_acerca))]
            )

            txt_pantalla_calc = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, read_only=True, border_color=ft.colors.BLUE_400, text_size=20)

            def click_calculadora(e):
                tecla = e.control.data
                if tecla == "C": txt_pantalla_calc.value = "0"
                elif tecla == "=":
                    try: txt_pantalla_calc.value = str(eval(txt_pantalla_calc.value))
                    except: txt_pantalla_calc.value = "Error"
                else:
                    if txt_pantalla_calc.value in ["0", "Error"]: txt_pantalla_calc.value = tecla
                    else: txt_pantalla_calc.value += tecla
                page.update()

            def crear_boton_calc(texto, color_fondo=ft.colors.SURFACE_VARIANT):
                return ft.ElevatedButton(text=texto, data=texto, on_click=click_calculadora, style=ft.ButtonStyle(bgcolor=color_fondo, color=ft.colors.WHITE), expand=True)

            dialogo_calculadora = ft.AlertDialog(
                title=ft.Text("Calculadora", weight=ft.FontWeight.BOLD),
                content=ft.Container(width=250, content=ft.Column([
                    txt_pantalla_calc,
                    ft.Row([crear_boton_calc("7"), crear_boton_calc("8"), crear_boton_calc("9"), crear_boton_calc("/", ft.colors.INDIGO_500)]),
                    ft.Row([crear_boton_calc("4"), crear_boton_calc("5"), crear_boton_calc("6"), crear_boton_calc("*", ft.colors.INDIGO_500)]),
                    ft.Row([crear_boton_calc("1"), crear_boton_calc("2"), crear_boton_calc("3"), crear_boton_calc("-", ft.colors.INDIGO_500)]),
                    ft.Row([crear_boton_calc("C", ft.colors.RED_400), crear_boton_calc("0"), crear_boton_calc("="), crear_boton_calc("+", ft.colors.INDIGO_500)]),
                ], tight=True)),
                actions=[ft.TextButton("Cerrar", on_click=lambda e: page.close(dialogo_calculadora))]
            )

            tasas_guardadas = page.client_storage.get("tasas_guardadas") or {"bcv": "", "eur": "", "usdt": ""}
            
            # --- ASIGNACIÓN DE COLORES A LAS TASAS ---
            txt_tasa_bcv_conv = ft.TextField(label="Tasa BCV", value=tasas_guardadas.get("bcv", ""), width=85, height=45, text_size=11, content_padding=5, keyboard_type=ft.KeyboardType.NUMBER, text_style=ft.TextStyle(color=ft.colors.CYAN))
            txt_tasa_eur_conv = ft.TextField(label="Tasa EUR", value=tasas_guardadas.get("eur", ""), width=85, height=45, text_size=11, content_padding=5, keyboard_type=ft.KeyboardType.NUMBER, text_style=ft.TextStyle(color=ft.colors.ORANGE))
            txt_tasa_usdt_conv = ft.TextField(label="Tasa USDT", value=tasas_guardadas.get("usdt", ""), width=85, height=45, text_size=11, content_padding=5, keyboard_type=ft.KeyboardType.NUMBER, text_style=ft.TextStyle(color=ft.colors.PINK))

            txt_monto_conv = ft.TextField(label="Monto", value="0", width=120, height=45, text_size=13, keyboard_type=ft.KeyboardType.NUMBER)
            drop_tipo_conv = ft.Dropdown(options=[ft.dropdown.Option("Divisas a Bs"), ft.dropdown.Option("Bs a Divisas")], value="Divisas a Bs", width=130, height=45, content_padding=5, text_size=12)
            
            lbl_res_bcv = ft.Text("A tasa BCV: 0,00", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_300, size=14)
            lbl_res_eur = ft.Text("A tasa EUR: 0,00", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_300, size=14)
            lbl_res_usdt = ft.Text("A tasa USDT: 0,00", weight=ft.FontWeight.BOLD, color=ft.colors.TEAL_300, size=14)

            def ejecutar_conversion(e=None):
                page.client_storage.set("tasas_guardadas", {"bcv": txt_tasa_bcv_conv.value, "eur": txt_tasa_eur_conv.value, "usdt": txt_tasa_usdt_conv.value})
                txt_tasa_bcv.value = txt_tasa_bcv_conv.value
                calcular_equivalentes() 

                try:
                    monto = parse_float(txt_monto_conv.value)
                    t_bcv = parse_float(txt_tasa_bcv_conv.value)
                    t_eur = parse_float(txt_tasa_eur_conv.value)
                    t_usdt = parse_float(txt_tasa_usdt_conv.value)

                    if drop_tipo_conv.value == "Divisas a Bs":
                        lbl_res_bcv.value = f"A tasa BCV: Bs {fmt(monto * t_bcv) if t_bcv > 0 else '0,00'}"
                        lbl_res_eur.value = f"A tasa EUR: Bs {fmt(monto * t_eur) if t_eur > 0 else '0,00'}"
                        lbl_res_usdt.value = f"A tasa USDT: Bs {fmt(monto * t_usdt) if t_usdt > 0 else '0,00'}"
                    else:  
                        lbl_res_bcv.value = f"A tasa BCV: $ {fmt(monto / t_bcv) if t_bcv > 0 else '0,00'}"
                        lbl_res_eur.value = f"A tasa EUR: € {fmt(monto / t_eur) if t_eur > 0 else '0,00'}"
                        lbl_res_usdt.value = f"A tasa USDT: ₮ {fmt(monto / t_usdt) if t_usdt > 0 else '0,00'}"
                except Exception: pass
                page.update()

            txt_monto_conv.on_change = drop_tipo_conv.on_change = ejecutar_conversion
            txt_tasa_bcv_conv.on_change = txt_tasa_eur_conv.on_change = txt_tasa_usdt_conv.on_change = ejecutar_conversion

            # --- FUNCIÓN Y BOTÓN CLEAN ---
            def limpiar_tasas(e):
                txt_tasa_bcv_conv.value = ""
                txt_tasa_eur_conv.value = ""
                txt_tasa_usdt_conv.value = ""
                txt_monto_conv.value = "0"
                lbl_res_bcv.value = "A tasa BCV: 0,00"
                lbl_res_eur.value = "A tasa EUR: 0,00"
                lbl_res_usdt.value = "A tasa USDT: 0,00"
                ejecutar_conversion()
                page.update()

            boton_clean = ft.ElevatedButton(
                text="Clean",
                icon=ft.icons.CLEANING_SERVICES,
                color=ft.colors.WHITE,
                bgcolor=ft.colors.RED_400,
                on_click=limpiar_tasas
            )

            dialogo_convertidor = ft.AlertDialog(
                title=ft.Text("Convertidor", weight=ft.FontWeight.BOLD, size=18),
                content=ft.Container(
                    width=300,
                    content=ft.Column([
                        ft.Text("1. Ingresa las tasas de hoy:", size=12, color=ft.colors.WHITE70),
                        ft.Row([txt_tasa_bcv_conv, txt_tasa_eur_conv, txt_tasa_usdt_conv], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(),
                        ft.Text("2. Calcula tus montos:", size=12, color=ft.colors.WHITE70),
                        ft.Row([txt_monto_conv, drop_tipo_conv], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(
                            padding=15, bgcolor=ft.colors.SURFACE_VARIANT, border_radius=10,
                            content=ft.Column([lbl_res_bcv, lbl_res_eur, lbl_res_usdt], spacing=5)
                        )
                    ], tight=True)
                ),
                actions=[boton_clean, ft.TextButton("Cerrar", on_click=lambda e: page.close(dialogo_convertidor))]
            )

            opcion_exportar = ft.Dropdown(label="Enviar reporte mediante:", options=[ft.dropdown.Option("WhatsApp"), ft.dropdown.Option("Correo Electrónico")], value="WhatsApp", border_color=ft.colors.BLUE_400)

            def procesar_exportacion(e):
                try:
                    historial = page.client_storage.get("movimientos") or []
                    if not historial: return notificar("No hay movimientos registrados para exportar.", ft.colors.ORANGE_700)

                    ing_usd = sum([m["monto"] for m in historial if m["tipo"] == "Ingreso" and m.get("moneda", "$") == "$"])
                    egr_usd = sum([m["monto"] for m in historial if m["tipo"] == "Egreso" and m.get("moneda", "$") == "$"])
                    ing_bs = sum([m["monto"] for m in historial if m["tipo"] == "Ingreso" and m.get("moneda", "$") == "Bs"])
                    egr_bs = sum([m["monto"] for m in historial if m["tipo"] == "Egreso" and m.get("moneda", "$") == "Bs"])
                    
                    s_usd = ing_usd - egr_usd
                    s_bs = ing_bs - egr_bs

                    reporte = f"📊 *REPORTE DE MIS REALES*\n\n👤 *Usuario:* {datos_usuario['nombre']} {datos_usuario['apellido']}\n\n"
                    reporte += f"💵 *SALDO EN DÓLARES:* ${fmt(s_usd)}\n(+ Ingresos: ${fmt(ing_usd)} | - Egresos: ${fmt(egr_usd)})\n\n"
                    reporte += f"🇻🇪 *SALDO EN BOLÍVARES:* Bs {fmt(s_bs)}\n(+ Ingresos: Bs {fmt(ing_bs)} | - Egresos: Bs {fmt(egr_bs)})\n\n"
                    reporte += "*DETALLE DE MOVIMIENTOS:*\n"
                    
                    for mov in historial:
                        icono = "🟢" if mov["tipo"] == "Ingreso" else "🔴"
                        moneda = mov.get("moneda", "$")
                        reporte += f"{icono} {mov['fecha']} | {mov['concepto']}: {moneda} {fmt(mov['monto'])}\n"

                    reporte_codificado = urllib.parse.quote(reporte)
                    page.close(dialogo_exportar)
                    
                    if opcion_exportar.value == "WhatsApp":
                        page.launch_url(f"https://wa.me/{datos_usuario['telefono'].replace('+', '').replace(' ', '')}?text={reporte_codificado}")
                    else:
                        page.launch_url(f"mailto:{datos_usuario['correo']}?subject=Reporte de Movimientos&body={reporte_codificado}")
                except Exception as ex:
                    notificar(f"Error al generar reporte: {ex}", ft.colors.RED_700)

            dialogo_exportar = ft.AlertDialog(title=ft.Text("Exportar Movimientos"), content=ft.Column([ft.Text("Genera un reporte detallado de tus finanzas."), opcion_exportar], tight=True), actions=[ft.FilledButton("Compartir", on_click=procesar_exportacion, style=ft.ButtonStyle(bgcolor=ft.colors.INDIGO_500)), ft.TextButton("Cancelar", on_click=lambda e: page.close(dialogo_exportar))])

            meses_dict = {"Todos": "Todos", "Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04", "Mayo": "05", "Junio": "06", "Julio": "07", "Agosto": "08", "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"}
            drop_filtro_mes = ft.Dropdown(label="Mes", options=[ft.dropdown.Option(mes) for mes in meses_dict.keys()], value="Todos", width=140, border_color=ft.colors.BLUE_400)
            drop_filtro_anio = ft.Dropdown(label="Año", options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(str(y)) for y in range(2024, 2031)], value="Todos", width=100, border_color=ft.colors.BLUE_400)
            lista_historial_detallado = ft.ListView(expand=True, spacing=5)
            lbl_resumen_filtro = ft.Text("...", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)

            def actualizar_historial_filtrado(e=None):
                lista_historial_detallado.controls.clear()
                movimientos = page.client_storage.get("movimientos") or []
                ing_usd, egr_usd, ing_bs, egr_bs = 0.0, 0.0, 0.0, 0.0

                for mov in reversed(movimientos):
                    try: dia, mes, anio = mov["fecha"].split("/")
                    except: continue
                    
                    filtro_mes = meses_dict[drop_filtro_mes.value]
                    if (filtro_mes != "Todos" and mes != filtro_mes) or (drop_filtro_anio.value != "Todos" and anio != drop_filtro_anio.value): continue
                    
                    moneda = mov.get("moneda", "$")
                    if mov["tipo"] == "Ingreso":
                        if moneda == "$": ing_usd += mov["monto"]
                        else: ing_bs += mov["monto"]
                        color, icono = ft.colors.GREEN_400, ft.icons.ARROW_UPWARD
                    else:
                        if moneda == "$": egr_usd += mov["monto"]
                        else: egr_bs += mov["monto"]
                        color, icono = ft.colors.RED_400, ft.icons.ARROW_DOWNWARD
                    
                    lista_historial_detallado.controls.append(
                        ft.ListTile(leading=ft.Icon(icono, color=color, size=24), title=ft.Text(mov["concepto"], weight=ft.FontWeight.BOLD, size=14), subtitle=ft.Text(mov["fecha"], size=12), trailing=ft.Text(f"{moneda} {fmt(mov['monto'])}", color=color, weight=ft.FontWeight.BOLD), bgcolor=ft.colors.SURFACE_VARIANT, dense=True)
                    )

                s_usd = ing_usd - egr_usd
                s_bs = ing_bs - egr_bs
                lbl_resumen_filtro.value = f"Saldo $: {fmt(s_usd)}  |  Saldo Bs: {fmt(s_bs)}"
                lbl_resumen_filtro.color = ft.colors.BLUE_200 if (s_usd >= 0 and s_bs >= 0) else ft.colors.ORANGE_300
                page.update()

            drop_filtro_mes.on_change = drop_filtro_anio.on_change = actualizar_historial_filtrado
            dialogo_historico = ft.AlertDialog(title=ft.Text("Histórico", weight=ft.FontWeight.BOLD), content=ft.Container(width=320, height=500, content=ft.Column([ft.Row([drop_filtro_mes, drop_filtro_anio], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Container(content=lbl_resumen_filtro, padding=10, alignment=ft.alignment.center, bgcolor=ft.colors.SURFACE_VARIANT, border_radius=10), ft.Divider(), lista_historial_detallado])), actions=[ft.TextButton("Cerrar", on_click=lambda e: page.close(dialogo_historico))])

            # --- APP BAR CON COLORES ACTUALIZADOS ---
            page.appbar = ft.AppBar(
                title=ft.Row([
                    ft.Image(src="logo_bf.png", width=32, height=32, fit=ft.ImageFit.CONTAIN, error_content=ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET, color=ft.colors.BLUE_300)),
                    ft.Text("BF", weight=ft.FontWeight.BOLD, size=20)
                ], tight=True, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                center_title=True, bgcolor=ft.colors.SURFACE_VARIANT, elevation=5,
                actions=[
                    ft.IconButton(icon=ft.icons.PRICE_CHANGE, tooltip="Convertidor", icon_color=ft.colors.AMBER_700, on_click=lambda e: [ejecutar_conversion(), page.open(dialogo_convertidor)]),
                    ft.IconButton(icon=ft.icons.CURRENCY_EXCHANGE, tooltip="Ver Al Cambio", icon_color=ft.colors.AMBER_700, on_click=lambda e: page.launch_url("https://alcambio.app/")),
                    ft.IconButton(icon=ft.icons.CALCULATE, tooltip="Calculadora", icon_color=ft.colors.AMBER_700, on_click=lambda e: page.open(dialogo_calculadora)),
                    ft.IconButton(icon=ft.icons.SHARE, tooltip="Exportar", icon_color=ft.colors.GREEN, on_click=lambda e: page.open(dialogo_exportar)),
                    ft.IconButton(icon=ft.icons.HELP_OUTLINE, tooltip="Acerca de", icon_color=ft.colors.AMBER_700, on_click=lambda e: page.open(dialogo_acerca))
                ]
            )

            lbl_eq_bcv = ft.Text("Consolidado: Bs 0,00", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_200, size=13)
            lbl_eq_usd = ft.Text("Consolidado: $ 0,00", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_200, size=13)

            def calcular_equivalentes(e=None):
                page.client_storage.set("tasas_guardadas", {"bcv": txt_tasa_bcv.value, "eur": txt_tasa_eur_conv.value, "usdt": txt_tasa_usdt_conv.value})
                try:
                    t_bcv = parse_float(txt_tasa_bcv.value)
                    if t_bcv > 0:
                        total_bs_consolidado = saldo_bs_actual + (saldo_usd_actual * t_bcv)
                        total_usd_consolidado = saldo_usd_actual + (saldo_bs_actual / t_bcv)
                        lbl_eq_bcv.value = f"Total en Bs: {fmt(total_bs_consolidado)}"
                        lbl_eq_usd.value = f"Total en $: {fmt(total_usd_consolidado)}"
                    else:
                        lbl_eq_bcv.value = lbl_eq_usd.value = "Ingresa la tasa"
                except: pass
                page.update()

            txt_tasa_bcv = ft.TextField(label="Tasa BCV", value=tasas_guardadas.get("bcv", ""), width=120, height=45, content_padding=5, text_size=13, keyboard_type=ft.KeyboardType.NUMBER, on_change=calcular_equivalentes)

            panel_conversiones = ft.ExpansionTile(
                title=ft.Text("Calcular Patrimonio Total", size=13, color=ft.colors.WHITE70), collapsed_text_color=ft.colors.WHITE70, text_color=ft.colors.WHITE, icon_color=ft.colors.WHITE70,
                controls=[
                    ft.Container(
                        padding=ft.padding.only(left=10, right=10, bottom=10),
                        content=ft.Column([
                            ft.Text("Unifica tus saldos usando la tasa del día.", size=11, color=ft.colors.WHITE54),
                            ft.Row([txt_tasa_bcv, ft.Column([lbl_eq_bcv, lbl_eq_usd], spacing=2)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ])
                    )
                ]
            )

            lbl_saldo_usd = ft.Text("$ 0,00", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
            lbl_saldo_bs = ft.Text("Bs 0,00", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)
            
            lbl_detalles_usd = ft.Text("Ing: $0,00 | Egr: $0,00", size=11, color=ft.colors.WHITE54)
            lbl_detalles_bs = ft.Text("Ing: Bs0,00 | Egr: Bs0,00", size=11, color=ft.colors.WHITE54)

            tarjeta_balance = ft.Card(
                elevation=8, color=ft.colors.BLUE_GREY_900,
                content=ft.Container(
                    padding=ft.padding.only(top=15, left=15, right=15),
                    content=ft.Column([
                        ft.Row([
                            ft.Column([ft.Text("SALDO $", size=12, color=ft.colors.WHITE70, weight=ft.FontWeight.BOLD), lbl_saldo_usd, lbl_detalles_usd], expand=1),
                            ft.Container(width=1, height=60, bgcolor=ft.colors.WHITE24),
                            ft.Column([ft.Text("SALDO Bs", size=12, color=ft.colors.WHITE70, weight=ft.FontWeight.BOLD), lbl_saldo_bs, lbl_detalles_bs], expand=1, alignment=ft.MainAxisAlignment.END),
                        ]),
                        ft.Divider(color=ft.colors.WHITE24),
                        panel_conversiones
                    ])
                )
            )

            lista_movimientos = ft.ListView(expand=True, spacing=10, padding=10)

            def cargar_datos():
                nonlocal saldo_usd_actual, saldo_bs_actual
                lista_movimientos.controls.clear()
                try:
                    movimientos = page.client_storage.get("movimientos") or []
                    ing_usd, egr_usd, ing_bs, egr_bs = 0.0, 0.0, 0.0, 0.0

                    for mov in reversed(movimientos):
                        moneda = mov.get("moneda", "$") 
                        
                        if mov["tipo"] == "Ingreso":
                            if moneda == "$": ing_usd += mov["monto"]
                            else: ing_bs += mov["monto"]
                            color, icono = ft.colors.GREEN_400, ft.icons.ARROW_UPWARD
                        else:
                            if moneda == "$": egr_usd += mov["monto"]
                            else: egr_bs += mov["monto"]
                            color, icono = ft.colors.RED_400, ft.icons.ARROW_DOWNWARD
                        
                        lista_movimientos.controls.append(
                            ft.ListTile(leading=ft.Icon(icono, color=color, size=30), title=ft.Text(mov["concepto"], weight=ft.FontWeight.BOLD), subtitle=ft.Text(mov["fecha"]), trailing=ft.Text(f"{moneda} {fmt(mov['monto'])}", color=color, weight=ft.FontWeight.BOLD, size=16), bgcolor=ft.colors.SURFACE_VARIANT)
                        )
                    
                    saldo_usd_actual = ing_usd - egr_usd
                    saldo_bs_actual = ing_bs - egr_bs
                    
                    lbl_saldo_usd.value = f"$ {fmt(saldo_usd_actual)}"
                    lbl_saldo_bs.value = f"Bs {fmt(saldo_bs_actual)}"
                    lbl_saldo_usd.color = ft.colors.RED_200 if saldo_usd_actual < 0 else ft.colors.BLUE_200
                    lbl_saldo_bs.color = ft.colors.RED_200 if saldo_bs_actual < 0 else ft.colors.BLUE_200
                    
                    lbl_detalles_usd.value = f"Ing: ${fmt(ing_usd)} | Egr: ${fmt(egr_usd)}"
                    lbl_detalles_bs.value = f"Ing: Bs{fmt(ing_bs)} | Egr: Bs{fmt(egr_bs)}"
                    
                    calcular_equivalentes() 
                except Exception as ex: notificar(f"Error Cargando: {ex}", ft.colors.RED_500)
                page.update()

            drop_tipo = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Ingreso"), ft.dropdown.Option("Egreso")], value="Ingreso", border_color=ft.colors.BLUE_400, width=130)
            drop_moneda = ft.Dropdown(label="Moneda", options=[ft.dropdown.Option("$"), ft.dropdown.Option("Bs")], value="$", border_color=ft.colors.BLUE_400, width=100)
            txt_concepto = ft.TextField(label="Concepto", border_color=ft.colors.BLUE_400)
            txt_monto = ft.TextField(label="Monto", keyboard_type=ft.KeyboardType.NUMBER, border_color=ft.colors.BLUE_400)
            
            def cambiar_fecha(e):
                if selector_fecha.value:
                    boton_fecha.text = selector_fecha.value.strftime("%d/%m/%Y")
                    page.update()

            selector_fecha = ft.DatePicker(first_date=datetime(2020, 1, 1), last_date=datetime(2030, 12, 31), on_change=cambiar_fecha)
            boton_fecha = ft.OutlinedButton(text=datetime.now().strftime("%d/%m/%Y"), icon=ft.icons.CALENDAR_MONTH, on_click=lambda e: page.open(selector_fecha))

            def guardar_movimiento(e):
                if not txt_concepto.value or not txt_monto.value: return notificar("Completa todos los campos", ft.colors.RED_700)
                try: 
                    monto_float = parse_float(txt_monto.value)
                    if monto_float <= 0: raise ValueError
                except: return notificar("El monto es inválido", ft.colors.RED_700)
                
                try:
                    movimientos = page.client_storage.get("movimientos") or []
                    movimientos.append({"tipo": drop_tipo.value, "moneda": drop_moneda.value, "concepto": txt_concepto.value, "monto": monto_float, "fecha": boton_fecha.text})
                    page.client_storage.set("movimientos", movimientos)
                    
                    page.close(dialogo_registro)
                    notificar("Registro guardado con éxito", ft.colors.GREEN_700)
                    txt_concepto.value = txt_monto.value = ""
                    cargar_datos()
                except Exception as ex: notificar(f"Error al guardar: {ex}", ft.colors.RED_700)

            dialogo_registro = ft.AlertDialog(title=ft.Text("Nuevo Registro"), content=ft.Column([ft.Row([drop_tipo, drop_moneda], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), txt_concepto, txt_monto, ft.Row([ft.Text("Fecha:"), boton_fecha], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)], tight=True), actions=[ft.FilledButton("Guardar", on_click=guardar_movimiento), ft.TextButton("Cancelar", on_click=lambda e: page.close(dialogo_registro))])
            
            # --- BOTÓN DE SIGNO '+' EN AZUL ---
            page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ADD, bgcolor=ft.colors.BLUE, on_click=lambda e: page.open(dialogo_registro))
            
            boton_historial = ft.Container(content=ft.FilledButton("Ver Historial", icon=ft.icons.MANAGE_SEARCH, style=ft.ButtonStyle(bgcolor=ft.colors.INDIGO_500), on_click=lambda e: [actualizar_historial_filtrado(), page.open(dialogo_historico)], width=300), padding=10, alignment=ft.alignment.center)

            imagen_fondo = ft.Image(src="Fondo.jpeg", fit=ft.ImageFit.COVER, opacity=0.25)
            contenido_principal = ft.Column([tarjeta_balance, ft.Container(content=ft.Text("Últimos Movimientos", weight=ft.FontWeight.BOLD), padding=10), lista_movimientos, boton_historial], expand=True)

            page.add(ft.Stack([ft.Container(bgcolor=ft.colors.BLACK, expand=True), ft.Container(content=imagen_fondo, expand=True, alignment=ft.alignment.center), contenido_principal], expand=True))
            cargar_datos()

        if page.client_storage.contains_key("usuario"): construir_interfaz_principal()
        else: mostrar_registro()

    except Exception as e:
        error_trace = traceback.format_exc()
        page.clean()
        page.add(
            ft.ListView([
                ft.Text("Error crítico detectado", color=ft.colors.RED_ACCENT, size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Mensaje: {e}", color=ft.colors.AMBER, size=14),
                ft.Text(error_trace, size=10, selectable=True, color=ft.colors.WHITE70)
            ], expand=True, padding=20)
        )
        page.update()

ft.app(target=main)
