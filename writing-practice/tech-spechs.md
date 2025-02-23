# Technical specs:

**Initialization Step:** 

- When the app first initiates it needs to do the following:
    - Fetch from the GET [localhost:5000/api/groups](http://localhost:5000/api/groups)/:id/raw, this will return a collection of words in json structure. It will have German words with english translation. We need to store this collection of words in memory

**Page States**

- Page states describe the state of the single page app. It will show the behavior from an user’s perspective

**Setup State**

When a user first starts up the app 

They will only see a button called “Generate Sentence” 

When they press the button, the app will generate a sentence using the sentence generator LLM, and the state will move to Practice state 

**Practice State**

When a user is in practice state, 

they will see an english sentence, 

they will also see an upload field under the english sentence

they will see a button called “submit for review” 

when they press the submit for review button, an uploaded image 

will be passed to the Grading System and then will transition to the Review State 

**Review State**

When a user is in the review state, 

the user will still see the english sentence. 

The upload field will be gone. 

The use will now see a review of the output from the Grading System: 

- Transcript of image
- Translation of Transcription
- Grading
    - a letter score using the german grading system
    - a description of whether the attempt was accurate to the english sentence and suggestions.

There will be a button called “Next Question” when clicked 

 it will generate a new question and place the app intro practice state

**Sentence Constructor LLM**  

Generate a simple sentence using the following word {{word}}

you can use the following vocabulary to construct a simple sentence: 

- simple objects - book, car, chicken, ramen
- simple verbs - to run, to eat, to talk
- simple times - tomorrow, today, yesterday.

**Grading System** 

The grading system will do the following: 

- It will transcribe the image using the LLM
- It will use the LLM to produce a literal translation of the transcript
- It will use another LLM to produce a grade
- It will return this data to the frontend app