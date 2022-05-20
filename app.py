
import os

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
        query = "SELECT  `song_name`, `author_pseudo` FROM `song_author` JOIN `author` ON song_author.author_id = author.author_id JOIN `song` ON song_author.song_id = song.song_id"
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
                insert_query = "INSERT INTO `survey_result` (`survey_id`, `composition_id`, `respondent_id`) VALUES "
                for i in range(5):
                    song_key_json = f'song{i+1}'
                    
                    cursor.execute(f"SELECT `id` FROM `song_author` JOIN `song` ON song_author.song_id = song.song_id JOIN `author` ON song_author.author_id = author.author_id WHERE  song_name = '{form[song_key_json].split('-')[1].strip()}' AND author_pseudo = '{form[song_key_json].split('-')[0].strip()}' ")
                    composition_id = cursor.fetchall()[0]['id']

                    insert_query += f"(1, {composition_id}, {respondent_id}),"

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

                insert_query = "INSERT INTO `playlist_inner` (`playlist_id`, `composition_id`) VALUES "
                for song in songs:
                    insert_query += f"({playlist_id}, {song['composition_id']}),"
                
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

                insert_query = "INSERT INTO `playlist_inner` (`playlist_id`, `composition_id`) VALUES "
                for song in songs:
                    insert_query += f"({playlist_id}, {song['composition_id']}),"
                
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

                insert_query = "INSERT INTO `playlist_inner` (`playlist_id`, `composition_id`) VALUES "
                for song in songs:
                    insert_query += f"({playlist_id}, {song['composition_id']}),"
                
                cursor.execute(insert_query[:-1])
                connection.commit()
            except:
                print("update_playlist Error")
                connection.rollback()
            print(songs)


def format_raw_playlists(raw_playlists):
    ready_playlists = {}
    for raw_playlist in raw_playlists:
        if ready_playlists.get((raw_playlist['category_name'], raw_playlist['category_image'])) is None:
            ready_playlists[(raw_playlist['category_name'], raw_playlist['category_image'])] = [raw_playlist['author_pseudo'] + ' - ' + raw_playlist['song_name']]
        else:
            ready_playlists[(raw_playlist['category_name'], raw_playlist['category_image'])].append(raw_playlist['author_pseudo'] + ' - ' + raw_playlist['song_name'])
    print(ready_playlists)
    return ready_playlists       


def write_to_file(data, filename):
    
    with open(filename, 'wb') as file:
        file.write(data)
    print("Данный из blob сохранены в: ", filename, "\n")

def get_ready_playlists():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM `get_each_playlist`")
        raw_playlists = cursor.fetchall()
        
        for raw in raw_playlists:
             photo_path = os.path.join("static\imgs\\", raw['category_name'] + ".jpg")
             write_to_file(raw['category_image'], photo_path)
             raw['category_image'] = photo_path
        
        
        return format_raw_playlists(raw_playlists)

        



app = Flask(__name__)


@app.route("/", methods=['GET','POST']) #unregistered
def unregistered():
    songs = select_songs()
    if request.method == "POST" and request.form != []:
        insert_survey_result(request.form)
        update_playlist(request.form)

    return render_template("unregistered_main.html", songs=songs)

@app.route("/registered", methods=['GET','POST'])
def registered():
    songs = select_songs()
    if request.method == "POST" and request.form != []:
        insert_survey_result(request.form)
        update_playlist(request.form)

    return render_template("registered_main.html", songs=songs)

@app.route("/admin", methods=['GET','POST'])
def admin():
    songs = select_songs()
    if request.method == "POST" and request.form != []:
        insert_survey_result(request.form)
        update_playlist(request.form)

    return render_template("admin_main.html", songs=songs)

@app.route("/registered_playlists")
def registered_playlists():
    playlists = get_ready_playlists()
    return render_template("registered_playlists.html", playlists=playlists.items())

@app.route("/admin_playlists")
def admin_playlists():
    playlists = get_ready_playlists()
    return render_template("admin_playlists.html", playlists=playlists.items())


@app.route("/login")
def login():
    
    return render_template("login.html")


@app.route("/register")
def register():
    
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
