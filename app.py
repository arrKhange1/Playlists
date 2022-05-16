from flask_sqlalchemy import SQLAlchemy

import pymysql
from db_config import host, user, password, db_name

from flask import Flask, render_template, request

try:
    connection = pymysql.connect(
        host = host,
        user = user,
        password= password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    print("Successfully connected...")


except Exception as ex:
    print("Connection failed...")
    print(ex)


def select_songs():
    result = ()
    with connection.cursor() as cursor:
        query = "SELECT  `song_name`, `author_pseudo` FROM `song` JOIN `author` ON song.author_id = author.author_id"
        cursor.execute(query)
        result = cursor.fetchall()
    return result


def insert_respondent(sex,age,email):
    
    try:

        with connection.cursor() as cursor:
            query = f"INSERT INTO `respondent` (`respondent_sex`,`respondent_age`,`respondent_email`) VALUES ('{sex}',{age},'{email}')"
            print(query)
            cursor.execute(query)
            connection.commit()
        return True
    except:
        print("respondent Error")
        return False
    

def insert_survey_result(form):
    
    if (insert_respondent(form['sex'],form['age'],form['email'])):
        try:

            with connection.cursor() as cursor:
                query = "SELECT * FROM `get_last_respondent_id`"
                cursor.execute(query)

                respondent_id = cursor.fetchall()[0]['respondent_id']
                insert_query = "INSERT INTO `survey_result` (`survey_id`, `song_id`, `respondent_id`) VALUES "
                for i in range(5):
                    song_key_json = f'song{i+1}'
                    
                    cursor.execute(f"SELECT `song_id` FROM `song` WHERE song_name = '{form[song_key_json].split('-')[1].strip()}'")
                    song_id = cursor.fetchall()[0]['song_id']

                    insert_query += f"(1, {song_id}, {respondent_id}),"

                cursor.execute(insert_query[:-1])
                connection.commit()
        except:
            print("survey_result Error")
    


def update_playlist(form):
    
    with connection.cursor() as cursor:
        if (form['sex'] == 'M'):

            cursor.execute("SELECT * FROM get_male_playlist_id")
            playlist_id = cursor.fetchall()[0]['playlist_id']
            
            try:

                cursor.execute(f"DELETE FROM `playlist_inner` WHERE playlist_id = {playlist_id}")

                cursor.execute("SELECT * FROM `songs_for_males_playlist`")
                songs = cursor.fetchall()

                insert_query = "INSERT INTO `playlist_inner` (`playlist_id`, `song_id`) VALUES "
                for song in songs:
                    insert_query += f"({playlist_id}, {song['song_id']}),"
                
                cursor.execute(insert_query[:-1])
                connection.commit()
            except:
                print("update_playlist Error")
                connection.rollback()

            print(songs)

        elif (form['sex'] == 'F'):

            cursor.execute("SELECT * FROM get_female_playlist_id")
            playlist_id = cursor.fetchall()[0]['playlist_id']
            
            try:

                cursor.execute(f"DELETE FROM `playlist_inner` WHERE playlist_id = {playlist_id}")

                cursor.execute("SELECT * FROM `songs_for_females_playlist`")
                songs = cursor.fetchall()

                insert_query = "INSERT INTO `playlist_inner` (`playlist_id`, `song_id`) VALUES "
                for song in songs:
                    insert_query += f"({playlist_id}, {song['song_id']}),"
                
                cursor.execute(insert_query[:-1])
                connection.commit()
            except:
                print("update_playlist Error")
                connection.rollback()
            print(songs)
        
        if (int(form['age']) <= 21):

            cursor.execute("SELECT * FROM get_youngsters_playlist_id")
            playlist_id = cursor.fetchall()[0]['playlist_id']

            try:

                cursor.execute(f"DELETE FROM `playlist_inner` WHERE playlist_id = {playlist_id}")

                cursor.execute("SELECT * FROM `songs_for_youngsters_playlist`")
                songs = cursor.fetchall()

                insert_query = "INSERT INTO `playlist_inner` (`playlist_id`, `song_id`) VALUES "
                for song in songs:
                    insert_query += f"({playlist_id}, {song['song_id']}),"
                
                cursor.execute(insert_query[:-1])
                connection.commit()
            except:
                print("update_playlist Error")
                connection.rollback()
            print(songs)
    
            

app = Flask(__name__)


@app.route("/", methods=['GET','POST'])
def index():
    songs = select_songs()
    if request.method == "POST" and request.form != []:
        insert_survey_result(request.form)
        update_playlist(request.form)

    return render_template("index.html", songs=songs)

@app.route("/playlists_page")
def playlists():

    return render_template("playlists.html")


if __name__ == "__main__":
    app.run(debug=True)
