# Baneco Transaction Rules

These rules are read by Claude Code and by the Python converter to categorize and assign payees.

## Payee + Category Rules

When a transaction memo matches these patterns, assign both payee and category:

| Pattern (in memo) | Payee | Category |
|---|---|---|
| LAURA ROSAS DAVID | David | Hipoteca |
| DANIELA ALEXANDRA LAURA ROSAS | Daniela | Hipoteca |
| CATARI CEREZO HERNAN | Hernan Catari | Hipoteca |
| NACIONAL SEGUROS | Nacional Seguros | Seguros |
| YPFB | YPFB | Facturas |
| BOLIVIANFOOD | Bolivian Foods | Salidas a Comer |
| HIPERMAXI | Hipermaxi | Compras |
| FARMACORP | Farmacorp | Salud & Bienestar |
| FMC | Farmacorp | Salud & Bienestar |
| DISMATEC | Dismatec | Electrodomésticos |
| YANGO | Yango | Transporte |
| UBER | Uber | Transporte |
| NETFLIX | Netflix | Streaming |
| FIDALGA | Fidalga | Compras |
| TIENDASTRESB | Tiendas Tres B | Compras |
| ICNORTE | IC Norte | Compras |
| FARMACIACHAVEZ | Farmacia Chavez | Salud & Bienestar |
| VIRGINIA MUNOZ ROSALES | Don Tio | Nuestra Casa |
| IMPUESTOS CASA | RUAT | Trámites |
| GITHUB | Github | Suscripciones |
| LEONOR GANADERO DEVOLUCION | Leonor | Prestamos Familiares |
| ALBERTO HUANACO CAPA | Plomero | Nuestra Casa |
| DUKASCOPY CIUDAD MEYRIN | DukasCopy | Conversion USD |
| SERVICIOS FACTURACION MENSUAL | CRE | Facturas |
| INVERSIONES BIENES RAICES | Monumental | Monumental |
| CINEMARK | Cinemark | Entretenimiento |
| ESTACIONDESERVICIOLACSANTACRUZBO | CIMA | Transporte |
| HILDA EDGAR | Nacional Seguros | Seguros [Hilda & Edgar] |
| SORIA GALVARRO RODRIGUEZ | Hybrid | Gimnasio |
| SILVA ANTONIO BERNARDO | Antonio Da Silva | Nuestra Casa |
| REGALO ASHLEY | ROHO HOMECENTER | Otros |
| BABY SHOWER | Mary Luz | Mary Luz |
| MENSUALIDAD FAVIANA | UDI | Educación [Favi] |
| BURGOA CESPEDES | Mercado Paraiso | Compras |
| CHICKENSKINGDOMVELARDESANTACRUZBO | Kingdom | Salidas a Comer |
| CREDITO BABY | Mary Luz | Mary Luz |
| EDGAR HILDA | Nacional Seguros | Seguros [Hilda & Edgar] |
| TALADRO | Roho homecenter f-9 | Nuestra Casa |
| BIENES RAICES MONUMENTAL | Monumental | Monumental |
| SAGUAPAC | Saguapac | Facturas |
| ADOBITO | Incerpaz | Nuestra Casa |
| HOGAR | Tigo | Internet |
| EXAMENES | Incor | Salud & Bienestar |
| RODRIGUEZ MAMANI NANCY | Mercado Paraiso | Compras |
| KINGTOR | Kingdom | Salidas a Comer |
| ZAMBRANA JOSIAS DEVOLUCION | Josias | Prestamos Familiares |
| BECSIMONECAFESANTACRUZBO | BEC CAFE | Comidas |
| LAGAIRACJ SANTACRUZBO | La Gaira | Salidas a Comer |
| ROCIO | Veterinaria 5to Anillo | Max |
| MICHINA | Michina | Max | 
| ACCESORIOS LUKY PIRAI | Accesorios Luky Pirai | Max |
| BARRIGA ELBA GANADERO | Paniagua Barriga | Mary Luz |
| OPENAI CHATGPTSUBSCR | ChatGPT | Suscripciones |
| VARGAS SONY GANADERO | La Fabrica De Ventanas | Nuestra Casa |
| CEMENTO TRANSPORTE | Ferretería Alto San Pedro | Nuestra Casa |
| SERVICIOS CLINICO | Incor | Salud & Bienestar |
| TENNIS MARY | FairPlay | Ropa |
| TIGO STAR | Tigo | Internet |
| PUNTALES | Complexo Equipamiento | Nuestra Casa |
| AMARKET | Amarket | Compras |
| TEJA | Incerpaz | Nuestra Casa |
| SANCHEZ CANCHA | Wally | Gimnasio |
| SERVICIOS POWERS SPORT | Pickleball | Israel |
| CUMPLE MARY | Brasargent | Salidas a Comer |
| UNION WALLY | Wally | Gimnasio |
| CIMA | CIMA | Transporte |
| ACAI ACAI SUPERFOOD | Acai | Salidas a Comer |
| GANADERO ALMUERZOS | Leonor | Comidas |

## Category-Only Rules

When a memo contains these keywords, assign the category (payee determined by AI):

| Keywords | Category |
|---|---|
| carne, pollo, abarrotes, verduras, arroz, queso, pan | Compras |
| gym, calistenia | Gimnasio |
| pickleball | Israel |
| taxi | Transporte |
| seguro | Seguros |
| prestamo, cuota, hipoteca | Hipoteca |
| veterinari, blanquita | Max |
| farmac, medicamento | Salud & Bienestar |
| PAGOS POR SOFTWARE | Conversion USD |
| ropa, pantalon, short, chinela, media | Ropa |
| choqueticlla | Max |
| instalacion | Nuestra Casa |
| materiales | Nuestra Casa |
| gloria | Compras |
| torrejon | Israel |
| drestaurant | Salidas a Comer |
| efectivo | Prestamos Familiares |
| final | Nuestra Casa |
| yepez | Educación [Erika] |
| tratamiento | Max |
| entrada | Entretenimiento |

## AI Guidance

For transactions not matched by rules above:
- POS transactions (DEBITO POR COMPRA POS) with merchant-looking names are usually stores
- TRASP.CTAS.TERCEROS are bank transfers to people
- ACCESORIOS LUKY PIRAI is a pet store -> Max
- BFC, TRANSBFC is a meat shop -> Compras
- If the memo tells Mary or Israel send it to -> Mary Luz or Israel categories respectively
- Always try to extract a payee name from the memo for better matching and reporting, even if it's not in the rules
