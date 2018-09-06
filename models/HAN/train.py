import re, os, gc, time, pandas as pd, numpy as np
import tqdm

np.random.seed(32)

from nltk import tokenize, word_tokenize
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Dense, Input, LSTM, GRU, Embedding, Dropout, Activation, Conv1D
from keras.layers import Bidirectional, Add, Flatten, TimeDistributed,CuDNNGRU,CuDNNLSTM
from keras.optimizers import Adam, RMSprop
from keras.models import Model, load_model
from custom_keras_classes import AttentionWeightedAverage, RocAucEvaluation






embed_size = 300
max_features = 150000
max_text_len = 150
max_sent = 5

# EMBEDDING_FILE = "../input/glove840b300dtxt/glove.840B.300d.txt
EMBEDDING_FILE = "crawl-300d-2M.vec/crawl-300d-2M.vec"


def clean_corpus(comment):
    comment = comment.replace('&', ' and ')
    comment = comment.replace('0', ' zero ')
    comment = comment.replace('1', ' one ')
    comment = comment.replace('2', ' two ')
    comment = comment.replace('3', ' three ')
    comment = comment.replace('4', ' four ')
    comment = comment.replace('5', ' five ')
    comment = comment.replace('6', ' six ')
    comment = comment.replace('7', ' seven ')
    comment = comment.replace('8', ' eight ')
    comment = comment.replace('9', ' nine ')
    comment = comment.replace('\'ve', ' have ')
    comment = comment.replace('\'d', ' would ')
    comment = comment.replace('\'m', ' am ')
    comment = comment.replace('n\'t', ' not ')
    comment = comment.replace('\'s', ' is ')
    comment = comment.replace('\'r', ' are ')
    comment = re.sub(r"\\", "", comment)
    comment = word_tokenize(comment)
    comment = " ".join(word for word in comment)
    return comment.strip().lower()


tic = time.time()
categories = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
train = pd.read_csv("train.csv")
test = pd.read_csv("test.csv")
Y = train[categories].values

train["comment_text"].fillna("no comment", inplace = True)
train["comment_text"] = train["comment_text"].apply(lambda x: clean_corpus(x))

test["comment_text"].fillna("no comment", inplace = True)
test["comment_text"] = test["comment_text"].apply(lambda x: clean_corpus(x))

train["sentences"] = train["comment_text"].apply(lambda x: tokenize.sent_tokenize(x))
test["sentences"] = test["comment_text"].apply(lambda x: tokenize.sent_tokenize(x))
toc = time.time()
print(toc-tic)


from keras.preprocessing.text import Tokenizer, text_to_word_sequence

raw_text = train["comment_text"]
tk = Tokenizer(num_words = max_features, lower = True)
tk.fit_on_texts(raw_text)

def sentenize(data):
    comments = data["sentences"]
    sent_matrix = np.zeros((len(comments), max_sent, max_text_len), dtype = "int32")
    for i, sentences in enumerate(comments):
        for j, sent in enumerate(sentences):
            if j < max_sent:
                wordTokens = text_to_word_sequence(sent)
                k=0
                for _, word in enumerate(wordTokens):
                    try:
                        if k < max_text_len and tk.word_index[word] < max_features:
                            sent_matrix[i, j, k] = tk.word_index[word]
                            k = k+1
                    except:
                            sent_matrix[i, j, k] = 0
                            k = k+1
    return sent_matrix

X = sentenize(train)
X_test = sentenize(test)

del train, test
gc.collect()

tic = time.time()
def get_coefs(word,*arr): return word, np.asarray(arr, dtype = "float32")
embeddings_index = dict(get_coefs(*o.strip().split()) for o in open(EMBEDDING_FILE))

word_index = tk.word_index
nb_words = min(max_features, len(word_index))
embedding_matrix = np.zeros((nb_words, embed_size))
for word, i in word_index.items():
    if i >= max_features: continue
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None: embedding_matrix[i] = embedding_vector
toc = time.time()
print(toc-tic)


from keras.callbacks import EarlyStopping, ModelCheckpoint

def build_model(rnn_units = 0, de_units = 0, lr = 0.0):
    encoder_inp = Input(shape = (max_text_len,), dtype = "int32")
    endcoder = Embedding(nb_words, embed_size, weights = [embedding_matrix],
                        input_length = max_text_len, trainable = False)(encoder_inp)
    endcoder = Bidirectional(CuDNNLSTM(rnn_units, return_sequences = True))(endcoder)
    endcoder = TimeDistributed(Dense(de_units, activation = "relu"))(endcoder)
    endcoder = AttentionWeightedAverage()(endcoder)
    Encoder = Model(encoder_inp, endcoder)

    decoder_inp = Input(shape = (max_sent, max_text_len), dtype = "int32")
    decoder = TimeDistributed(Encoder)(decoder_inp)
    decoder = Bidirectional(CuDNNLSTM(rnn_units, return_sequences = True))(decoder)
    decoder = TimeDistributed(Dense(de_units, activation = "relu"))(decoder)
    Decoder = AttentionWeightedAverage()(decoder)
    #Decoder = Dropout(0.7)(Decoder)
    out = Dense(6, activation = "sigmoid")(Decoder)
    model = Model(decoder_inp, out)
    model.compile(loss = "binary_crossentropy", optimizer = Adam(lr = lr),  metrics = ["accuracy"])
    return model
model = build_model(rnn_units = 64, de_units = 64, lr = 1e-3)
model.summary()


fold_count = 10
fold_size = len(X) // 10
for fold_id in range(0, fold_count):
    fold_start = fold_size * fold_id
    fold_end = fold_start + fold_size

    if fold_id == fold_size - 1:
        fold_end = len(X)

    X_valid = X[fold_start:fold_end]
    Y_valid = Y[fold_start:fold_end]
    X_train = np.concatenate([X[:fold_start], X[fold_end:]])
    Y_train = np.concatenate([Y[:fold_start], Y[fold_end:]])

    model = build_model(rnn_units = 64, de_units = 64, lr = 1e-3)
    file_path = "HAN_%s_.hdf5" %fold_id
    ra_val = RocAucEvaluation(validation_data = (X_valid, Y_valid), interval = 1)
    check_point = ModelCheckpoint(file_path, monitor = "val_loss", mode = "min", save_best_only = True, verbose = 1)
    history = model.fit(X_train, Y_train, batch_size = 128, epochs = 3, validation_data = (X_valid, Y_valid),
                    verbose = 1, callbacks = [ra_val, check_point])


list_of_preds = []
list_of_vals = []
list_of_y = []
fold_count = 10
fold_size = len(X) // 10
for fold_id in range(0, fold_count):
    fold_start = fold_size * fold_id
    fold_end = fold_start + fold_size

    if fold_id == fold_size - 1:
        fold_end = len(X)

    X_valid = X[fold_start:fold_end]
    Y_valid = Y[fold_start:fold_end]
    X_train = np.concatenate([X[:fold_start], X[fold_end:]])
    Y_train = np.concatenate([Y[:fold_start], Y[fold_end:]])

    file_path = 'HAN_' + str(fold_id) + '_.hdf5'
    model = load_model(file_path, custom_objects = {"AttentionWeightedAverage": AttentionWeightedAverage})
    preds = model.predict(X_test, batch_size = 1024, verbose = 1)
    list_of_preds.append(preds)
    vals = model.predict(X_valid, batch_size = 1024, verbose = 1)
    list_of_vals.append(vals)
    list_of_y.append(Y_valid)

test_predicts = np.zeros(list_of_preds[0].shape)
for fold_predict in list_of_preds:
    test_predicts += fold_predict

test_predicts /= len(list_of_preds)
submission = pd.read_csv('sample_submission.csv')
submission[categories] = test_predicts
submission.to_csv('l2_test_data.csv', index=False)

l2_data = pd.DataFrame(columns=['logits_' + c for c in categories]+categories)
l2_data[['logits_' + c for c in categories]] = pd.DataFrame(np.concatenate(list_of_vals,axis = 0))
l2_data[categories] = pd.DataFrame(np.concatenate(list_of_y,axis = 0))
l2_data.to_csv('l2_train_data.csv')