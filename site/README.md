# Cum se face situl

**Paginile de produs din rădăcină sunt generate. Nu le edita de mână** — la
următoarea generare se suprascriu și pierzi ce ai scris.

## De ce există folderul ăsta

Paginile erau scrise una câte una, iar header-ul, footer-ul și blocul de meta
erau identice în toate. Între 13% și 30% din fiecare fișier era text repetat.
Într-o singură zi de lucru au fost necesare **patru scripturi separate** doar ca
să țină paginile la fel între ele: unul pentru meta-uri, unul pentru titluri,
unul pentru descrieri, unul pentru culori.

Cu patru produse mai mergea. Cu opt, nu.

## Ce editezi, de fapt

| Vrei să schimbi | Editează |
|---|---|
| Numele, descrierea, culoarea, familia unui produs | `produse.json` |
| Ce arată pagina unui produs (secțiunile ei) | `vitrine/<slug>.html` |
| Header, footer, meta-uri — pentru **toate** paginile deodată | `sablon-produs.html` |

Apoi:

```
python site/construieste.py
```

## Ce se generează singur

- blocul complet de `<head>`: descriere, canonical, favicon, Open Graph, Twitter
- header-ul și navigația
- **footer-ul cu legături către celelalte produse** — se recalculează, deci un
  produs nou apare automat în subsolul tuturor paginilor existente
- `sitemap.xml`

Asta e partea care contează: adaugi al cincilea produs și nu trebuie să te
atingi de primele patru.

## Cum adaugi un produs

1. O intrare nouă în `produse.json` — `slug`, `nume`, `nume_scurt`, `titlu`,
   `descriere`, `familie`, `ordine`, `culoare`, `theme_color`, `body_style`,
   `og_image`, `nav`, `support_mailto`
2. Un fișier `vitrine/<slug>.html` cu secțiunile paginii (ce e între `<main>`
   și `</main>`)
3. Opțional `vitrine/<slug>.dialog.html` și `vitrine/<slug>.js`, dacă pagina are
   galerie cu previzualizare la mărime completă
4. Capturile în `assets/`, plus o imagine de partajare `og-<slug>.jpg` la
   1200×630
5. `python site/construieste.py`

## Fișierele de vitrină

Sunt fragmente, nu pagini întregi: doar conținutul dintre `<main>` și `</main>`.
Prima linie se scrie fără indentare — scriptul o așază el la locul ei.

`<slug>.js` e ce stă între `<script>` și `</script>`, tot fără indentare pe
prima linie.

## Verificat

Când a fost introdus, generatorul a produs paginile **identice byte cu byte** cu
cele scrise de mână, în trei cazuri din patru. Al patrulea diferea printr-o
singură linie goală, pe care celelalte pagini o aveau deja — adică generatorul a
îndreptat o inconsecvență, nu a introdus una.
