import csv, ast

def learn():
    print('starting learning')
    genre_file = open('./archive/contentDataGenre.csv', encoding='utf-8')
    genre_reader = csv.reader(genre_file)
    desc_file = open('./archive/contentDataPrime.csv', encoding='utf-8')
    desc_reader = csv.reader(desc_file)
    learning_dict = {}
    first_time = True
    unique_words = set() #keep track of unique features in training data
    for desc_row in desc_reader:
        if first_time: #don't use the first one because it is the titles on the excel
            first_time = False
            continue
        id = desc_row[0]
        desc = desc_row[10].lower()
        genre_file.seek(0) # reset the file pointer
        for genre_row in genre_reader:
            if id == genre_row[0]:
                genre = genre_row[1].lower()
                print('learning new words for genre: %s, and ID: %s' % (genre, id))
                learning_dict, unique_words = update_learning(learning_dict, desc, genre, unique_words)
                break
    genre_file.close()
    desc_file.close()
    print('done learning')
    return learning_dict, len(unique_words)

def update_learning(learning_dict : dict, desc, genre, unique_words : set):
    import string
    if genre not in learning_dict:
        learning_dict[genre] = {}
    desc_words = desc.split()
    for word in desc_words:
        #remove all punctiation from the word to avoid the same word being counted as different ones
        clean_word = word.translate(str.maketrans('', '', string.punctuation))
        unique_words.add(clean_word) #keep track of unique features in training data
        if clean_word in learning_dict[genre]:
            learning_dict[genre][clean_word] += 1
        else:
            learning_dict[genre][clean_word] = 1
    return learning_dict, unique_words

def get_num_occurances(word, feature_dict):
    for feature in feature_dict.keys():
        if word == feature:
            return feature_dict[feature]
    return 0

def get_learned_data():
    #check if we have already learned and get the learning dictionary if we have
    #if we have not, learn and save the dictionary in a txt file
    try:
        with open('learning.txt', mode='r', encoding='utf-8') as f:
            learning_dict_str = f.readline()
            num_unique_features = int(f.readline())
        learning_dict = ast.literal_eval(learning_dict_str)
    except FileNotFoundError:
        learning_dict, num_unique_features = learn()
        with open('learning.txt', mode='w', encoding='utf-8') as f:
            f.write(str(learning_dict))
            f.write('\n')
            f.write(str(num_unique_features))
    return learning_dict, num_unique_features

def get_prob_dict(in_movie_desc, learning_dict, num_unique_features):
    '''Get a dictionary of probabilities associated with each genre for the given movie description.'''
    genre_prob_dict = {}
    for genre in learning_dict.keys():
        genre_prob_dict[genre] = 1
        for word in in_movie_desc.split():
            num_occurances  = get_num_occurances(word, learning_dict[genre])
            if num_occurances == 0:
                continue
            #genre_prob_dict[genre] *= num_occurances / len(learning_dict[genre].keys()) #no laplace smoothing
            genre_prob_dict[genre] *= (num_occurances + 1) / (len(learning_dict[genre].keys()) + num_unique_features)
    return genre_prob_dict

def get_all_movie_probs(learning_dict, num_unique_features):
    #check if we have already gotten the probabilities for each movie
    #if we have not, get them and save the dictionary in a txt file
    try:
        with open('movie_probs.txt', mode='r', encoding='utf-8') as f:
            movie_prob_dict_str = f.readline()
        movie_prob_dict = ast.literal_eval(movie_prob_dict_str)
    except FileNotFoundError:
        movie_prob_dict = {}
        desc_file = open('./archive/contentDataPrime.csv', encoding='utf-8')
        desc_reader = csv.reader(desc_file)
        for row in desc_reader:
            id = row[0]
            desc = row[10].lower()
            print('Getting probability dictionary for movie with id: %s' % (id))
            movie_prob_dict[id] = get_prob_dict(desc, learning_dict, num_unique_features)
        with open('movie_probs.txt', mode='w', encoding='utf-8') as f:
            f.write(str(movie_prob_dict))
    return movie_prob_dict

def compare_movies(liked_movie_prob_dict, db_prob_dicts):
    '''Compare movies based on their probability of being each genre by seeing how close each value
    is and taking the average over all of the values.  The most similar movie will be the one with the
    score closest to 0.'''
    import math
    best_score = math.inf
    best_movie_id = -1
    for other_movie_id in db_prob_dicts:
        print('Comparing your movie to movie with id: %s' % (other_movie_id))
        other_prob_dict = db_prob_dicts[other_movie_id]
        sum = 0
        amount = 0
        for genre in liked_movie_prob_dict:
            sum += abs(liked_movie_prob_dict[genre] - other_prob_dict[genre])
            amount += 1
        score = sum / amount
        if score < best_score:
            best_score = score
            best_movie_id = other_movie_id
    return best_movie_id

def get_movie_title_by_id(id):
    file = open('./archive/contentDataPrime.csv', encoding='utf-8')
    reader = csv.reader(file)
    for entry in reader:
        if entry[0] == id:
            return entry[2]
    return 'Movie not found'

def recommend(in_movie_desc, in_movie_review):
    learning_dict, num_unique_features = get_learned_data()
    comb_input = in_movie_desc + ' ' + in_movie_review
    liked_movie_prob_dict = get_prob_dict(comb_input, learning_dict, num_unique_features)
    db_prob_dicts = get_all_movie_probs(learning_dict, num_unique_features)
    reccomendation_id = compare_movies(liked_movie_prob_dict, db_prob_dicts)
    if reccomendation_id == -1:
        print('No recommendation found.')
        return ''
    else:
        return get_movie_title_by_id(reccomendation_id)

movie_description = 'After young Riley is uprooted from her Midwest life and moved to San Francisco, her emotions - Joy, Fear, Anger, Disgust and Sadness - conflict on how best to navigate a new city, house, and school.'
movie_review = 'I like how happy and wholesome the movie is.  It made me feel warm and fuzzy inside.'
print(recommend(movie_description, movie_review))