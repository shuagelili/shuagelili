# Marketplace and Evidence Rules

Read this reference when resolving a marketplace, collecting competitor evidence, or deciding whether a claim is publishable.

## Source priority

Use sources in this order:

1. User-supplied product facts and documents.
2. Authoritative marketplace or product evidence for the resolved site.
3. User-provided keyword workbook metrics.
4. Front-end health snapshots for time, ZIP, and offer state.
5. Competitor observations for comparison and keyword discovery.
6. Analyst inference, clearly labelled in Chinese explanation only.

Never fabricate product attributes, keyword volume, rank, price, rating, review count, BSR, image details, certification, Buy Box, delivery promise, or competitor claims. A blocked page, snippet, incomplete export, or one ZIP snapshot is not proof of a global or persistent state.

## Marketplace resolution

An explicit marketplace or URL wins. Supported health defaults are:

```text
US amazon.com 90001 en-US USD
UK amazon.co.uk SW1A 1AA en-GB GBP
DE amazon.de 10115 de-DE EUR
FR amazon.fr 75001 fr-FR EUR
IT amazon.it 00100 it-IT EUR
ES amazon.es 28001 es-ES EUR
CA amazon.ca M5V 2T6 en-CA CAD
JP amazon.co.jp 100-0001 ja-JP JPY
MX amazon.com.mx 06600 es-MX MXN
AU amazon.com.au 2000 en-AU AUD
```

Record domain, country, locale, currency, postal-code source, retrieval time, and login or personalization limits. For unsupported countries, identify the values from authoritative evidence. If the health adapter cannot execute the site, mark the health check `BLOCKED`; do not fall back to another country.

## Offer and competitor boundaries

ASIN-level evidence does not prove seller, fulfillment, Buy Box, inventory, or delivery. Keep competitor ASINs and URLs explicitly labelled as competitors. Preserve parent/child, pack, bundle, and variant roles. If user parameters conflict with an own listing page, preserve both values, label the conflict in Chinese explanation, and do not use the disputed value in final copy.

## Default field limits

Use the resolved category and marketplace rules when verified. Otherwise use the skill defaults: title alternatives at most 75 characters, Highlights at most 125 characters, exactly five bullets, product description 1,500-2,000 characters, separate frontend/backend keyword fields, and a seven-image plan. If evidence cannot support a 1,500-character description without repetition or invention, keep it shorter and explain the gap.
