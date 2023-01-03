import traceback
import pandas as pd
import jellyfish._jellyfish as pyjellyfish
import enchant


def edecoded(data):
    for index,row in data.iterrows():
        word = str(row['word'])
        encoded = pyjellyfish.metaphone(word)
        data.loc[index,'code'] = encoded
    return data


def is_english(word):
    d = enchant.Dict("en_US")
    result = d.check(str(word))
    result_str = str(result)
    return result_str
    

def suggest_english(word):
    d = enchant.Dict("en_US")
    result = d.suggest(str(word))
    return result

    
def match_datasets(data,model):
    data = edecoded(data)
    for i in data.index:
        word = str(data['word'][i])
        for j in model.index:
            comparing_word = str(model['correct_word'][j])
            if word == comparing_word :
                data.loc[i,'compared_word']= model['correct_word'][j]
    return data          
    
def rank_words(data):
    #### add a new column named count and assign all value as 1
    encoded_data = edecoded(data)

    ### Grouping and extracting highest repeating word in each category
    encoded_data['count'] = 1
    dff = encoded_data.groupby(['word','code'], as_index=False)['count'].count()
    new_df = dff.sort_values('count', ascending=False).drop_duplicates('code').sort_index()
    
    ### Changing dataframe column name to expected name
    new_df.rename(columns = {'word':'suggested_word'}, inplace = True)
    
    ### Dropping Unexpected column
    new_df_drop = new_df.drop("count", axis='columns')
    return new_df_drop

def corrected_words(match_datasets,rank_words):
    df = pd.merge(left = match_datasets, right = rank_words, how = 'left', on = 'code' )
    df = df.drop("count", axis='columns')
    for index,row in df.iterrows():
        word = str(row['word'])
        compared_word = str(row['compared_word'])
        suggested_word = str(row['suggested_word'])
        #
        if compared_word == 'nan':
            if len(word) < 6 :
                if pyjellyfish.hamming_distance(word,suggested_word) <= 1:
                    if pyjellyfish.damerau_levenshtein_distance(word,suggested_word) <= 2:
                        df.loc[index,'compared_word'] = suggested_word
            
            elif len(word) >= 6 :
                if pyjellyfish.hamming_distance(word,suggested_word) <= 2:
                    if pyjellyfish.damerau_levenshtein_distance(word,suggested_word) <= 2:
                        df.loc[index,'compared_word'] = suggested_word
        
    new_df_drop = df.drop("suggested_word", axis='columns')            
    return new_df_drop


def all_matching_codes(df):
    data = df.groupby('code')['word'].apply(list)
    df_join = pd.merge(left = df, right = data, how = 'inner', on = 'code' )
    df_join.rename(columns = {'word_x':'word', 'code':'code',
                              'compared_word':'compared_word','word_y':'word_list'}, inplace = True)
    return df_join


def words(df):
    for index,row in df.iterrows():
        word = row['word']
        english = is_english(word)
        print(english)
        df.loc[index,'flag'] = english
        if english.lower() == 'false':
            word_list = suggest_english(word)
            df.loc[index,'suggested_word'] = str(word_list)
    return df
                                
# def levenshtein(df):
    

if __name__ == '__main__':

    try:
        keyword_data = pd.read_csv("Splitted_keywords.csv")
        data_model = pd.read_csv("Data_With_Bangla.csv")
        bangla_match_datasets = match_datasets(keyword_data,data_model)
        top_rank_words = rank_words(keyword_data)
        corrected_words_list = corrected_words(bangla_match_datasets ,top_rank_words)
        matching_codes = all_matching_codes(corrected_words_list)
        result = words(matching_codes)
        #result = all_matching_codes(corrected_words_list)
        # # loc_edecoded(data)
        # # loc_edecoded(keyword_data)
        # result = match_datasets(keyword_data,data_model)
        # result.to_csv('Result.csv',index=False)
        result.to_csv('test_dictionary.csv',index=False)
        
    except Exception as e:
        print(e)
        print(traceback.print_exc())