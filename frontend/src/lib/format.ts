// Formattazione all'italiana (virgola decimale) + helper Google Maps.

export const euro = (n: number): string => `${n.toFixed(2).replace('.', ',')} €`

export const ppl = (n: number): string =>
  `${n.toFixed(2).replace('.', ',')} €/L`

/** Link a Google Maps per cercare il supermercato nella zona. */
export const mapsUrl = (supermarket: string, zone: string): string =>
  `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    `${supermarket} ${zone}`
  )}`
