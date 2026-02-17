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

## AI Guidance

For transactions not matched by rules above:
- POS transactions (DEBITO POR COMPRA POS) with merchant-looking names are usually stores
- TRASP.CTAS.TERCEROS are bank transfers to people
- ACCESORIOS LUKY PIRAI is a pet store -> Max
- BFC, TRANSBFC is a meat shop -> Compras
- Always try to extract a payee name from the memo for better matching and reporting, even if it's not in the rules
