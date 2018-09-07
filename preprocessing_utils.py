import re
from num2words import num2words


def glove_preprocess(text):
    """
    adapted from https://nlp.stanford.edu/projects/glove/preprocess-twitter.rb

    """
    # Different regex parts for smiley faces
    eyes = "[8:=;]"
    nose = "['`\-]?"
    text = re.sub("https?:* ", "<URL>", text)
    text = re.sub("www.* ", "<URL>", text)
    text = re.sub("\[\[User(.*)\|", '<USER>', text)
    text = re.sub("<3", '<HEART>', text)
    text = re.sub("[-+]?[.\d]*[\d]+[:,.\d]*", "<NUMBER>", text)
    text = re.sub(eyes + nose + "[Dd)]", '<SMILE>', text)
    text = re.sub("[(d]" + nose + eyes, '<SMILE>', text)
    text = re.sub(eyes + nose + "p", '<LOLFACE>', text)
    text = re.sub(eyes + nose + "\(", '<SADFACE>', text)
    text = re.sub("\)" + nose + eyes, '<SADFACE>', text)
    text = re.sub(eyes + nose + "[/|l*]", '<NEUTRALFACE>', text)
    text = re.sub("/", " / ", text)
    text = re.sub("[-+]?[.\d]*[\d]+[:,.\d]*", "<NUMBER>", text)
    text = re.sub("([!]){2,}", "! <REPEAT>", text)
    text = re.sub("([?]){2,}", "? <REPEAT>", text)
    text = re.sub("([.]){2,}", ". <REPEAT>", text)
    pattern = re.compile(r"(.)\1{2,}")
    text = pattern.sub(r"\1" + " <ELONG>", text)

    return text

def preprocess(data, glove = False):


    data[COMMENT] = data[COMMENT].map(lambda x: lower(x)) #lowercase
    data[COMMENT] = data[COMMENT].map(lambda x: rm_breaks(x)) #removing breaks
    if glove:
        data[COMMENT] = data[COMMENT].map(lambda x: glove_preprocess(x))
    data[COMMENT] = data[COMMENT].map(lambda x: expand_contractions(x)) #expanding contractions
    data[COMMENT] = data[COMMENT].map(lambda x: replace_smileys(x)) #replacing smileys
    data[COMMENT] = data[COMMENT].map(lambda x: replace_ip(x)) #replacing ip
    data[COMMENT] = data[COMMENT].map(lambda x: rm_links_text(x)) #removing links
    data[COMMENT] = data[COMMENT].map(lambda x: replace_numbers(x))#replacing numbers
    data[COMMENT] = data[COMMENT].map(lambda x: rm_bigrams(x)) #removing bigrams
    data[COMMENT] = data[COMMENT].map(lambda x: isolate_punc(x)) #isolating punct


    #data[COMMENT] = data[COMMENT].str.replace(r"[^A-Za-z0-9(),!?@\'\`\"\_\n]", " ")
    return data


def lower(text):
    text = text.lower()
    return text


def rm_breaks(text):
    text = text.replace('\n', ' ')
    " ".join(text.split())
    return text




def rm_hyperlinks(words):
    words = [w if not (w.startswith('http') or
                       w.startswith('www') or
                       w.endswith('.com') or
                        w.startswith('en.wikipedia.org/')) else 'url' for w in words]
    return words



def rm_links_text(text):
    text = re.sub("http?s://.* ","url", text)
    text = re.sub("www.* ", "url", text)
    return text


def replace_numbers(text):

    years = re.findall('[1-2][0-9]{3}.', text)
    for n in years:
        try:
            text = text.replace(n[:-1],num2words(int(n[:-1]),to='year') + ' ')
        except:
            continue
    numbers = re.findall('\d{1,2}.[^\d{3,}]', text)
    for n in numbers:
        try:
            text = text.replace(n[:-1],num2words(int(n[:-1])) + ' ')
        except:
            continue
    return text


def rm_links_words(words):
    words = [w for w in words if not (w.startswith('http') or w.startswith('www.') or w.endswith('.com'))]
    return words


def rm_user(text):
    text = re.sub("\[\[User(.*)\|","user-id", text)
    return text


def replace_ip(text):
    text = re.sub("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}","ip-address",text)
    return text


def rm_article_id(text):
    text = re.sub("\d:\d\d\s{0,5}$","article-id" ,text)
    return text


def rm_bigrams(text):
    text = re.sub(r'[-–_]',' ',text)
    return text


def isolate_punc(text):
    text = re.sub(r'([\'\"\.\(\)\!\?\-\\\/\,])', r' \1 ', text)
    return text


def replace_smileys(text):
    """
    adapted from https://nlp.stanford.edu/projects/glove/preprocess-twitter.rb

    """
    eyes = "[8:=;]"
    nose = "['`\-]?"
    # Different regex parts for smiley faces
    text = re.sub("<3", 'heart emoji', text)
    text = re.sub(eyes + nose + "[Dd)\]]", 'happy smiley', text)
    text = re.sub("[(d]" + nose + eyes, 'happy smiley', text)
    text = re.sub(eyes + nose + "p", 'lol smiley', text)
    text = re.sub(eyes + nose + "\(", 'sad smiley', text)
    text = re.sub("\)" + nose + eyes, 'sad smiley', text)
    text = re.sub(eyes + nose + "[/|l*]", 'neutral smiley', text)

    return text

def _get_contractions():
    contractions = {
        "ain't": "am not", "can't": "cannot", "aren't": "are not", "can't've": "cannot have", "'cause": "because",
        "could've": "could have", "couldn't": "could not", "couldn't've": "could not have", "didn't": "did not",
        "don't": "do not", "doesn't": "does not",            "hadn't": "had not",            "hadn't've": "had not have",
        "hasn't": "has not",            "haven't": "have not",            "he'd": "he had",
        "he'd've": "he would have",            "he'll": "he shall",            "he'll've": "he shall have",            "he's": "he has",
        "how'd": "how did",            "how'd'y": "how do you",            "how'll": "how will",
        "how's": "how has",            "i'd": "i had",
        "i'd've": "i would have",
        "i'll": "i shall",
        "i'll've": "i shall have",
        "i'm": "i am",
        "i've": "i have",
        'marcolfuck':'marcol fuck',
        'wikiprojects':'wiki projects',
        'youbollocks':'you bull shit',
        'ancestryfuck':'ancestry fuck',
        'ricehappy':'rice happy',
        'aidsaids':'aids aids',
        'smileyrick':'smiley rick',
        'wikipediahappy':'wikipedia happy',
        'talkhappy':'talk happy',
        'talklol':'talk lol',
        'userhappy':'user happy',
        'mainpagebg':'mainpage background',
        '@ggot':'faggot',
        'smileyrecious':'smiley recious',
        'nooob':'noob',
        'urlsmiley':'url smiley',
        'ashol':'asshole',
        'smileyp':'smiley',
        'latinus':'latino',
        'userlol':'user lol',
        "god's":'gods',
        "pneis":'penis',
        "else's":'else his',
        'pennnis':'penis',
        'youfuck':'you fuck',
        'phuq':'fuck',
        'philippineslong':'philippines long',
        "women's":'womens',
        'wplol':'wikipedia lol',
        "editor's":'editors',
        'itsuck':'it suck',
        "offfuck":'off fuck',
        'tommytwo':'tommy two',
        "file's":'files',
        "other's":'others',
        "gayfrozen":'gay frozen',
        "mother's":'mothers',
        "gayfag":'gay faggot',
        "ip's":'ips',
        "men's":'mens',
        "today's":'todays',
        "mothjer":'mother mispelled',
        "isn't": "is not",
        "it'd": "it had",
        "anyone's":'anyones',
        "website's":'websites',
        "wiki's":'wikis',
        "page's":'page is',
        "aseven":'as even',
        "wikipedia's":'wikipedias',
        'npov':'neutral point of view',
        "world's":'worlds',
        "user's":'users',
        "securityfuck": 'security fuck',
        "one's":'ones',
        'néger':'nigger',
        "author's":'authors',
        'roflspam':'rofl spam',
        'niggors':'niggers',
        'helloz':'hello',
        'phck':'fuck',
        'bonergasm':'boner orgasm',
        'schäbig':'lame',
        'bitchbot':'bitch robot',
        'donkeysex':'donkey sex',
        'faggt':'faggot',
        'niggerjew':'nigger jew',
        'dixz':'dicks',
        'gayyour':'gay your',
        'smileyo':'smile yo',
        'backgrounhappy':'background happy',
        'vaginapenis':'vagina penis',
        'wphappy':'wp happy',
        'smileyist':'smiley ist',
        'radicalnigger':'radical nigger',
        'oldihappy':'oldi happy',
        'smileyx':'smiley x',
        'peenus':'penis',
        'motherfuckerdie':'motherfucker die',
        'homopetersymonds':'homo peter symonds',
        'honkhonk':'honk honk',
        'analanal':'anal anal',
        "sex'butt":"sex butt",
        "here's":'here is',
        "subject's":'subject is',
        'fucksex':'fuck sex',
        'smileyol':'smiley',
        'yourselfgo':'yourself go',
        "fggt":'faggot',
        "person's":'persons',
        "man's":"mans",
        "article's":'articles',
        "it'd've": "it would have",
        "it'll": "it shall",
        "it'll've": "it shall have",
        "it's": "it has",
        '#zero':'zero',
        'pagedelete':'page delete',
        'addressip':'address ip',
        "image's":'images',
        'imagehappy':'image happy',
        'imagelol':'image lol',
        'slimvirgin':'slim virgin',
        "let's": "let us",
        "ma'am": "madam",
        'b00ll00x':'bull shit',
        "mayn't": "may not",
        "might've": "might have",
        "mightn't": "might not",
        "mightn't've": "might not have",
        "people's":'peoples',
        'cuntfranks':'cunt franks',
        "3rr":'three revert rule',
        '#f5fffa': 'mint green',
        '`':' ',
        'roycy':'badass',
        '@hotmail':'email adress',
        'fvckers':'fuckers',
        'suckernguyen':'sucker nguyen',
        'turkeyfuck':'turkey fuck',
        'wpneutral':'wp neutral',
        'faggotgay':'faggot gay',
        'cuntliz':'cunt liz',
        'smileylease':'smiley lease',
        'sucksgeorge':'sucks george',
        'hornyhorny':'horny horny',
        'headsdick':'heads dick',
        'helloe':'hello',
        'kfuckity':'fuck city',
        'smileyi':'smiley',
        'ballsballs':'balls balls',
        'serbiafack':'serbia fuck',
        "must've": "must have",
        'wikipedialol':'wikipedia lol',
        'wikilove':'wiki love',
        'penispenis':'penis penis',
        'fagsgod':'fags god',
        'nigggers':'niggers',
        'bitchbitch':'bitch bitch',
        "mustn't": "must not",
        "mustn't've": "must not have",
        "needn't": "need not",
        "needn't've": "need not have",
        "o'clock": "of the clock",
        "oughtn't": "ought not",
        "oughtn't've": "ought not have",
        "shan't": "shall not",
        "sha'n't": "shall not",
        "shan't've": "shall not have",
        "she'd": "she had",
        "she'd've": "she would have",
        "she'll": "she shall",
        "she'll've": "she shall have",
        "she's": "she has",
        "should've": "should have",
        "shouldn't": "should not",
        "shouldn't've": "should not have",
        "so've": "so have",
        "so's": "so is",
        "that'd": "that would",
        "that'd've": "that would have",
        "that's": "that is",
        "there'd": "there would",
        "there'd've": "there would have",
        "there's": "there is",
        "they'd": "they had",
        "they'd've": "they would have",
        "they'll": "they will",
        "they'll've": "they will have",
        "they're": "they are",
        "they've": "they have",
        "to've": "to have",
        "wasn't": "was not",
        "we'd": "we would",
        "we'd've": "we would have",
        "we'll": "we will",
        "we'll've": "we will have",
        "we're": "we are",
        "we've": "we have",
        "weren't": "were not",
        "what'll": "what will",
        "what'll've": "what will have",
        "what're": "what are",
        "what's": "what is",
        "what've": "what have",
        "when's": "when is",
        "when've": "when have",
        "where'd": "where did",
        "where's": "where is",
        "where've": "where have",
        "who'll": "who will",
        "who'll've": "who will have",
        "who's": "who is",
        "who've": "who have",
        "why's": "why is",
        "why've": "why have",
        "will've": "will have",
        "won't": "will not",
        "won't've": "will not have",
        "would've": "would have",
        "wouldn't": "would not",
        "wouldn't've": "would not have",
        "y'all": "you all",
        "y'all'd": "you all would",
        "y'all'd've": "you all would have",
        "y'all're": "you all are",
        "y'all've": "you all have",
        "you'd": "you would",
        "you'd've": "you would have",
        "you'll": "you will",
        "you'll've": "you will have",
        "you're": "you are",
        "you've": "you have"
    }
    contractions_re = re.compile('(%s)' % '|'.join(contractions.keys()))
    return contractions, contractions_re

def expand_contractions(text):
    contractions, contractions_re = _get_contractions()
    def replace(match):
        return contractions[match.group(0)]

    return contractions_re.sub(replace, text)
