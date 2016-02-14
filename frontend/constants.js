exports.SNIPPET_SIZE = 120
exports.TITLE_LENGTH = 40
exports.SNIPPET_LENGTH = 160
exports.MAX_LENGTH_URL_DISP = 50
exports.CACHE_TIMEOUT_IN_SEC = 3600
exports.SERP_RESULTS_NUMBER = 10
exports.DEFAULT_QUERY = 1229065
exports.SESSION_COLLECTION_NAME = 'sessions'
exports.THANK_MESSAGES = [
    'Welcome, your highness, to my humble land or research!\n Please provide your judgment over my subjects.',
    'Every click you make is a step towards heaven for me, my lord.',
    'Your majesty is a grand lord! Working for his people!',
    'I always thought you were the most enlighened of all, Sir.',
    'Please continue pushing science forward, we need you!',
    // 'There is no rest for the wicked!',
    // 'If everyone were as hardworking as you,\n I would not even had to do research on that!',
    // 'And maybe we would both be somewhere on some sunny beach...',
    // 'With well-and-safely-designed robots serving us lemonade.',
    // 'Or, maybe, we would be fighting against robots.\n This is still an open question.',
    // 'Do you think we should do research about fighting robots?',
    // TODO add many more!

    'In any case, you are done! Thanks to you...\n<span class="hooray">I am now a free man!</span>'
]

exports.SURVEY_PAGE_COUNT = exports.THANK_MESSAGES.length - 1 /* hehe, why not */ -1 /* because the last message isn't a survey page */
