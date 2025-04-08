import { WordSet, Category } from '../types';

export const wordSets: Record<Category, WordSet> = {
    general: {
        category: 'general',
        words: [
            // Easy words
            {
                german: 'Hallo',
                english: 'Hello',
                examples: ['Hallo, wie geht es dir?', 'Hallo zusammen!'],
                category: 'general',
                difficulty: 'easy'
            },
            {
                german: 'Danke',
                english: 'Thank you',
                examples: ['Danke für deine Hilfe.', 'Vielen Danke!'],
                category: 'general',
                difficulty: 'easy'
            },
            {
                german: 'Bitte',
                english: 'Please',
                examples: ['Bitte schön!', 'Ja bitte?'],
                category: 'general',
                difficulty: 'easy'
            },
            {
                german: 'Ja',
                english: 'Yes',
                examples: ['Ja, das stimmt.', 'Ja, gerne!'],
                category: 'general',
                difficulty: 'easy'
            },
            // Medium words
            {
                german: 'vielleicht',
                english: 'maybe',
                examples: ['Vielleicht später.', 'Ich komme vielleicht.'],
                category: 'general',
                difficulty: 'medium'
            },
            {
                german: 'natürlich',
                english: 'naturally',
                examples: ['Natürlich helfe ich dir.', 'Das ist natürlich wichtig.'],
                category: 'general',
                difficulty: 'medium'
            },
            // Hard words
            {
                german: 'selbstverständlich',
                english: 'of course',
                examples: ['Das ist selbstverständlich.', 'Selbstverständlich mache ich das.'],
                category: 'general',
                difficulty: 'hard'
            },
            {
                german: 'wahrscheinlich',
                english: 'probably',
                examples: ['Das ist wahrscheinlich richtig.', 'Ich komme wahrscheinlich später.'],
                category: 'general',
                difficulty: 'hard'
            }
        ]
    },
    cooking: {
        category: 'cooking',
        words: [
            // Easy words
            {
                german: 'der Koch',
                english: 'the cook',
                examples: ['Der Koch bereitet das Essen zu.', 'Ich möchte Koch werden.'],
                category: 'cooking',
                difficulty: 'easy'
            },
            {
                german: 'die Küche',
                english: 'the kitchen',
                examples: ['Die Küche ist sehr sauber.', 'Ich koche gerne in der Küche.'],
                category: 'cooking',
                difficulty: 'easy'
            },
            {
                german: 'das Brot',
                english: 'the bread',
                examples: ['Das Brot ist frisch.', 'Ich kaufe Brot.'],
                category: 'cooking',
                difficulty: 'easy'
            },
            {
                german: 'der Teller',
                english: 'the plate',
                examples: ['Der Teller ist leer.', 'Bitte gib mir einen Teller.'],
                category: 'cooking',
                difficulty: 'easy'
            },
            // Medium words
            {
                german: 'die Zutaten',
                english: 'the ingredients',
                examples: ['Die Zutaten sind frisch.', 'Ich kaufe die Zutaten.'],
                category: 'cooking',
                difficulty: 'medium'
            },
            {
                german: 'das Rezept',
                english: 'the recipe',
                examples: ['Das Rezept ist einfach.', 'Ich folge dem Rezept.'],
                category: 'cooking',
                difficulty: 'medium'
            },
            // Hard words
            {
                german: 'die Küchenmaschine',
                english: 'the food processor',
                examples: ['Die Küchenmaschine ist kaputt.', 'Ich benutze die Küchenmaschine.'],
                category: 'cooking',
                difficulty: 'hard'
            },
            {
                german: 'der Schnellkochtopf',
                english: 'the pressure cooker',
                examples: ['Der Schnellkochtopf spart Zeit.', 'Ich koche mit dem Schnellkochtopf.'],
                category: 'cooking',
                difficulty: 'hard'
            }
        ]
    },
    // ... similar pattern for other categories
    travel: {
        category: 'travel',
        words: [
            // Easy words for travel category
            {
                german: 'der Zug',
                english: 'the train',
                examples: ['Der Zug fährt um 9 Uhr ab.', 'Ich nehme den Zug nach Berlin.'],
                category: 'travel',
                difficulty: 'easy'
            },
            {
                german: 'der Flughafen',
                english: 'the airport',
                examples: ['Der Flughafen ist sehr groß.', 'Wir treffen uns am Flughafen.'],
                category: 'travel',
                difficulty: 'easy'
            },
            // Add more words with medium and hard difficulty
            {
                german: 'die Reise',
                english: 'the journey',
                examples: ['Die Reise war lang.', 'Ich plane eine Reise.'],
                category: 'travel',
                difficulty: 'medium'
            },
            {
                german: 'die Verspätung',
                english: 'the delay',
                examples: ['Der Zug hat Verspätung.', 'Es gibt eine Verspätung.'],
                category: 'travel',
                difficulty: 'hard'
            }
        ]
    },
    business: {
        category: 'business',
        words: [
            // Easy words for business category
            {
                german: 'das Büro',
                english: 'the office',
                examples: ['Das Büro öffnet um 9 Uhr.', 'Ich arbeite im Büro.'],
                category: 'business',
                difficulty: 'easy'
            },
            {
                german: 'der Termin',
                english: 'the appointment',
                examples: ['Ich habe einen Termin um 14 Uhr.', 'Der Termin wurde verschoben.'],
                category: 'business',
                difficulty: 'easy'
            },
            // Add more words with medium and hard difficulty
            {
                german: 'die Besprechung',
                english: 'the meeting',
                examples: ['Die Besprechung beginnt gleich.', 'Wir haben eine wichtige Besprechung.'],
                category: 'business',
                difficulty: 'medium'
            },
            {
                german: 'die Geschäftsführung',
                english: 'the management',
                examples: ['Die Geschäftsführung hat entschieden.', 'Er gehört zur Geschäftsführung.'],
                category: 'business',
                difficulty: 'hard'
            }
        ]
    },
    technology: {
        category: 'technology',
        words: [
            // Easy words for technology category
            {
                german: 'der Computer',
                english: 'the computer',
                examples: ['Der Computer ist neu.', 'Ich arbeite am Computer.'],
                category: 'technology',
                difficulty: 'easy'
            },
            {
                german: 'das Internet',
                english: 'the internet',
                examples: ['Das Internet ist langsam.', 'Ich surfe im Internet.'],
                category: 'technology',
                difficulty: 'easy'
            },
            // Add more words with medium and hard difficulty
            {
                german: 'die Software',
                english: 'the software',
                examples: ['Die Software muss aktualisiert werden.', 'Ich entwickle Software.'],
                category: 'technology',
                difficulty: 'medium'
            },
            {
                german: 'die Künstliche Intelligenz',
                english: 'artificial intelligence',
                examples: ['Die Künstliche Intelligenz entwickelt sich schnell.', 'Er forscht über Künstliche Intelligenz.'],
                category: 'technology',
                difficulty: 'hard'
            }
        ]
    }
};
