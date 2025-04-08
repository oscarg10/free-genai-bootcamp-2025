import { WordSet, Category } from '../types';

export const wordSets: Record<Category, WordSet> = {
    general: {
        category: 'general',
        words: [
            {
                german: 'Hallo',
                english: 'Hello',
                examples: [
                    'Hallo, wie geht es dir?',
                    'Hallo zusammen!'
                ],
                category: 'general',
                difficulty: 'easy'
            },
            {
                german: 'Danke',
                english: 'Thank you',
                examples: [
                    'Danke für deine Hilfe.',
                    'Vielen Danke!'
                ],
                category: 'general',
                difficulty: 'easy'
            }
        ]
    },
    cooking: {
        category: 'cooking',
        words: [
            {
                german: 'der Koch',
                english: 'the cook',
                examples: [
                    'Der Koch bereitet das Essen zu.',
                    'Ich möchte Koch werden.'
                ],
                category: 'cooking',
                difficulty: 'easy'
            },
            {
                german: 'die Küche',
                english: 'the kitchen',
                examples: [
                    'Die Küche ist sehr sauber.',
                    'Ich koche gerne in der Küche.'
                ],
                category: 'cooking',
                difficulty: 'easy'
            }
        ]
    },
    travel: {
        category: 'travel',
        words: [
            {
                german: 'der Zug',
                english: 'the train',
                examples: [
                    'Der Zug fährt um 9 Uhr ab.',
                    'Ich nehme den Zug nach Berlin.'
                ],
                category: 'travel',
                difficulty: 'easy'
            },
            {
                german: 'der Flughafen',
                english: 'the airport',
                examples: [
                    'Der Flughafen ist sehr groß.',
                    'Wir treffen uns am Flughafen.'
                ],
                category: 'travel',
                difficulty: 'easy'
            }
        ]
    },
    business: {
        category: 'business',
        words: [
            {
                german: 'das Büro',
                english: 'the office',
                examples: [
                    'Das Büro öffnet um 9 Uhr.',
                    'Ich arbeite im Büro.'
                ],
                category: 'business',
                difficulty: 'easy'
            },
            {
                german: 'der Termin',
                english: 'the appointment',
                examples: [
                    'Ich habe einen Termin um 14 Uhr.',
                    'Der Termin wurde verschoben.'
                ],
                category: 'business',
                difficulty: 'easy'
            }
        ]
    },
    technology: {
        category: 'technology',
        words: [
            {
                german: 'der Computer',
                english: 'the computer',
                examples: [
                    'Der Computer ist neu.',
                    'Ich arbeite am Computer.'
                ],
                category: 'technology',
                difficulty: 'easy'
            },
            {
                german: 'das Internet',
                english: 'the internet',
                examples: [
                    'Das Internet ist langsam.',
                    'Ich surfe im Internet.'
                ],
                category: 'technology',
                difficulty: 'easy'
            }
        ]
    }
};
