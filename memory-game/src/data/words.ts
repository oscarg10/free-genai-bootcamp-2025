interface WordPair {
  german: string;
  english: string;
}

export const words: { [key in 'easy' | 'medium' | 'hard']: WordPair[] } = {
  easy: [
    { german: 'Hund', english: 'dog' },
    { german: 'Katze', english: 'cat' },
    { german: 'Haus', english: 'house' },
    { german: 'Baum', english: 'tree' },
    { german: 'Buch', english: 'book' },
    { german: 'Auto', english: 'car' },
  ],
  medium: [
    { german: 'Bibliothek', english: 'library' },
    { german: 'Schlüssel', english: 'key' },
    { german: 'Schmetterling', english: 'butterfly' },
    { german: 'Regenschirm', english: 'umbrella' },
    { german: 'Krankenhaus', english: 'hospital' },
    { german: 'Universität', english: 'university' },
    { german: 'Spielzeug', english: 'toy' },
    { german: 'Frühstück', english: 'breakfast' },
  ],
  hard: [
    { german: 'Geschwindigkeit', english: 'speed' },
    { german: 'Sehenswürdigkeit', english: 'sight' },
    { german: 'Wahrscheinlichkeit', english: 'probability' },
    { german: 'Naturwissenschaft', english: 'science' },
    { german: 'Unabhängigkeit', english: 'independence' },
    { german: 'Zusammenarbeit', english: 'cooperation' },
    { german: 'Verantwortung', english: 'responsibility' },
    { german: 'Entwicklung', english: 'development' },
    { german: 'Freundschaft', english: 'friendship' },
    { german: 'Möglichkeit', english: 'possibility' },
  ]
};
