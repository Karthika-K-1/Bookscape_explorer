import streamlit as st
import mysql.connector
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import requests
import numpy as np
r = st.sidebar.radio('NAVIGATION',['Home','Book Search'])
st.markdown("""
<style>
    /* Change the background color of the sidebar to dull red */
    [data-testid=stSidebar] {
        background-color:rgb(219, 161, 161); /* Dull Red */
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        /* Main title customization */
        h1 {
            font-size: 40px;
            color: #B22222;  /* Dark Red */
        }
    </style>
    """, unsafe_allow_html=True)

#Home page
if r=='Home':
    file_path = r"E:\GUVI_data_science\Project_Bookscape_explorer\Image_2.png"
    image = Image.open(file_path)
    # Resize the image with Pillow
    new_width = 3000
    new_height = 1500
    resized_image = image.resize((new_width, new_height))
    # Display the resized image
    st.image(resized_image)
    st.title("BOOKSCAPE EXPLORER")
    st.subheader("UNLEASH THE MAGIC OF READING")  
    st.text("Dive into a world where every page turns into an adventure. Discover books tailored to your passions and interests, all in one place!")

#Function to web scrap book data using google API
def scrap_all(query, API_key, total_books):
    url = "https://www.googleapis.com/books/v1/volumes"
    max_results = 40  # API limit for maxResults
    all_books = []  # To store all fetched books

    for start_index in range(0, total_books, max_results):
        print(start_index)
        params = {
            'q': query,
            'key': API_key,
            'maxResults': min(max_results, total_books - start_index),
            'startIndex': start_index
        }
        response = requests.get(url, params=params)
        data = response.json()
        print(data.keys())
        # Add the fetched items to the list
        #if 'items' in data:
        all_books.extend(data['items'])
    return all_books

#Function to perform data cleaning
def data_clean(d,keyword):
    all_data = []
    for i in d:
        d2 = {'book_id': i['id'],
              'search_key': keyword,
              'book_title': i['volumeInfo'].get('title','NA'),
              'book_subtitle': i['volumeInfo'].get('subtitle','NA'),  #get is used to extract the data if available else get 'NA'
              'book_authors': 'NA' if i['volumeInfo'].get('authors','NA')=='NA' else ', '.join(i['volumeInfo']['authors']),
              'publisher': i['volumeInfo'].get('publisher','NA'),
              'book_description': i['volumeInfo'].get('description','NA'),
              'industryIdentifiers': 'NA' if i['volumeInfo'].get('industryIdentifiers','NA') == 'NA' else next((item['identifier'] for item in i['volumeInfo']['industryIdentifiers'] if item['type'] == 'ISBN_13'), 'NA'),
              'text_readingModes': i['volumeInfo']['readingModes'].get('text','NA'),
              'image_readingModes': i['volumeInfo']['readingModes'].get('image','NA'),
              'pageCount': i['volumeInfo'].get('pageCount','NA'),
              'categories': 'NA' if i['volumeInfo'].get('categories','NA')=='NA' else ', '.join(i['volumeInfo']['categories']),
              'language': i['volumeInfo'].get('language','NA'),
              'imageLinks': 'NA' if i['volumeInfo'].get('imageLinks','NA')=='NA' else i['volumeInfo']['imageLinks'].get('thumbnail','NA'),
              'ratingsCount': i['volumeInfo'].get('ratingsCount','NA'),
              'averageRating': i['volumeInfo'].get('averageRating','NA'),
              'country': i['saleInfo'].get('country','NA'),
              'saleability': i['saleInfo'].get('saleability','NA'),
              'isEbook': i['saleInfo'].get('isEbook','NA'),
              'amount_listPrice': 'NA' if i['saleInfo'].get('listPrice','NA')=='NA' else i['saleInfo']['listPrice'].get('amount','NA'),
              'currencyCode_listPrice': 'NA' if i['saleInfo'].get('listPrice','NA')=='NA' else i['saleInfo']['listPrice'].get('currencyCode','NA'),
              'amount_retailPrice': 'NA' if i['saleInfo'].get('listPrice','NA')=='NA' else i['saleInfo']['retailPrice'].get('amount','NA'),
              'currencyCode_retailPrice': 'NA' if i['saleInfo'].get('listPrice','NA')=='NA' else i['saleInfo']['retailPrice'].get('currencyCode','NA'),
              'buyLink ': i['saleInfo'].get('buyLink','NA'),
              'year': i['volumeInfo'].get('publishedDate','NA')[0:4]
              }
        all_data.append(d2)
    # Convert dictionary to DataFrame
    all_data_df = pd.DataFrame(all_data)

    # Remove duplicate rows (keep the first occurrence)
    all_data_df = all_data_df.drop_duplicates(keep='first')
    # Drop duplicates based on 'book_id', keeping the first occurrence
    all_data_df = all_data_df.drop_duplicates(subset=['book_id'], keep='first')

    # Convert 'NA' or any invalid data to NaN (which will map to NULL in MySQL)
    all_data_df['amount_listPrice'] = pd.to_numeric(all_data_df['amount_listPrice'], errors='coerce')
    all_data_df['amount_retailPrice'] = pd.to_numeric(all_data_df['amount_listPrice'], errors='coerce')
    all_data_df['averageRating'] = pd.to_numeric(all_data_df['averageRating'], errors='coerce')
    all_data_df['pageCount'] = pd.to_numeric(all_data_df['pageCount'], errors='coerce')
    all_data_df['ratingsCount'] = pd.to_numeric(all_data_df['ratingsCount'], errors='coerce')
    all_data_df = all_data_df.replace({np.nan: None})

    # Remove leading/trailing whitespaces
    all_data_df['book_id'] = all_data_df['book_id'].str.strip()

    #To remove symbols
    all_data_df['book_title'] = all_data_df['book_title'].apply(lambda x: str(x).replace('#', '').replace("'", '').replace('"', '').replace('...', '').strip())
    all_data_df['book_subtitle'] = all_data_df['book_subtitle'].apply(lambda x: str(x).replace('#', '').replace("'", '').replace('"', '').replace('...', '').replace('(', '').replace(')', '').replace('-', '').strip())
    all_data_df['book_description'] = all_data_df['book_description'].apply(lambda x: str(x).replace('#', '').replace('"', '').replace('...', '').replace('[', '').replace(']', '').strip()).str.strip("'").str.strip("*").str.strip("-").str.strip("--")
    all_data_df['publisher'] = all_data_df['publisher'].str.replace('"', '')
    return all_data_df

#Function to create SQL database and table and insert book data into the database
def data_insert(all_data_df):
    mydb=mysql.connector.connect(
        host='localhost',
        user='root',
        password='12345678'
    )
    mycursor=mydb.cursor()

    #To create a database
    query = "CREATE DATABASE IF NOT EXISTS Bookscape_explorer_project"
    mycursor.execute(query)

    #Choose a database
    mydb=mysql.connector.connect(
        host='localhost',
        user='root',
        password='12345678',
        database = 'Bookscape_explorer_project'
    )
    mycursor=mydb.cursor()

    #create a table in the database selected
    query = """create table if not exists books(
            book_id varchar(50),
            search_key varchar(50),
            book_title varchar(500),
            book_subtitle text,
            book_authors text,
            publisher varchar(500),
            book_description text,
            industryIdentifiers text,
            text_readingModes boolean,
            image_readingModes boolean,
            pageCount int,
            categories text,
            language varchar(20),
            imageLinks text,
            ratingsCount int,
            averageRating decimal(10,2),
            country varchar(20),
            saleability varchar(50),
            isEbook boolean,
            amount_listPrice decimal(10,2), 
            currencyCode_listPrice varchar(20),      
            amount_retailPrice decimal(10,2),
            currencyCode_retailPrice varchar(20),
            buyLink text,
            year text,
            PRIMARY KEY (book_id))
            """
    mycursor.execute(query)

    # Generate dynamic placeholders for the query
    columns = ", ".join(all_data_df.columns)  # Creates "column1, column2, column3"
    placeholders = ", ".join(["%s"] * len(all_data_df.columns))  # Creates "%s, %s, %s"

    # Define the SQL insert query
    sql = f"INSERT IGNORE INTO books ({columns}) VALUES ({placeholders})"

    # Convert DataFrame to a list of tuples for batch insertion
    data_tuples = [tuple(row) for row in all_data_df.itertuples(index=False, name=None)]

    # Execute batch insertion
    #mycursor.execute(sql, data_tuples[0])
    mycursor.executemany(sql, data_tuples)

    # Commit changes
    mydb.commit()

    # Close the cursor and connection
    mycursor.close()
    mydb.close()

#Function to execute SQL queries 
def execute_query(query):
    mydb = mysql.connector.connect(
        host='localhost',
        user='root',
        password='12345678',
        database = 'Bookscape_explorer_project'
    )
    mycursor = mydb.cursor()
    mycursor.execute(query)
    data = mycursor.fetchall()
    column_names = [desc[0] for desc in mycursor.description]
    mycursor.close()
    mydb.close()
    return data, column_names

#Function to truncate the database table
def truncate():
    query = 'TRUNCATE TABLE books;'
    mydb = mysql.connector.connect(
        host='localhost',
        user='root',
        password='12345678',
        database = 'Bookscape_explorer_project'
    )
    mycursor = mydb.cursor()
    mycursor.execute(query)
    mycursor.close()
    mydb.close()

#Dictionary with questions and corresponding SQL queries
questions = {
    'Check Availability of eBooks vs Physical Books': {
        'query': 'select count(*),isEbook from books group by isEbook;',
        'index': 1},
    'Find the Publisher with the Most Books Published': {
        'query':"select publisher,count(publisher) publisher_count from books group by publisher having publisher_count = ( select max(c) from (select count(publisher) c from books where publisher != 'NA' group by publisher)a );",
        'index': 2},
    'Identify the Publisher with the Highest Average Rating': {
        'query': "select publisher PUBLISHER,averageRating AVERAGE_RATING from books where averageRating = (select max(averageRating) from books) and publisher != 'NA';",
        'index': 3},
    'Get the Top 5 Most Expensive Books by Retail Price': {
        'query': "select book_title BOOK,amount_retailPrice RETAIL_PRICE from books order by amount_retailPrice desc limit 5;",
        'index': 4},
    'Find Books Published After 2010 with at Least 500 Pages': {
        'query': "select book_title BOOK,year YEAR,pageCount PAGES from books where year>2010 and pageCount>=500;",
        'index': 5},
    'List Books with Discounts Greater than 20%': {
        'query': "select book_title from books where (((amount_listPrice - amount_retailPrice)/amount_listPrice) * 100) > 20;",
        'index': 6},
    'Find the Average Page Count for eBooks vs Physical Books': {
        'query': "select isEbook,avg(pageCount) from books group by isEbook;",
        'index': 7},
    'Find the Top 3 Authors with the Most Books': {
        'query': "select book_authors,count(*) book_count from books where book_authors != 'NA' group by book_authors order by book_count desc limit 3;",
        'index': 8},
    'List Publishers with More than 10 Books': {
        'query': "select publisher PUBLISHER,count(book_title) NUMBER_OF_BOOKS from books group by publisher having NUMBER_OF_BOOKS>10 and publisher != 'NA' order by NUMBER_OF_BOOKS desc;",
        'index': 9},
    'Find the Average Page Count for Each Category': {
        'query': "select categories CATEGORIES,round(avg(pageCount),0) PAGES from books where categories != 'NA' group by categories;",
        'index': 10},
    'Retrieve Books with More than 3 Authors': {
        'query': "select book_title BOOKS,book_authors AUTHORS from books where (length(book_authors) - length(REPLACE(book_authors, ',', ''))) + 1 > 3;",
        'index': 11},
    'Books with Ratings Count Greater Than the Average': {
        'query': "select book_title BOOKS,ratingsCount RATINGS_COUNT from books where ratingsCount> (select avg(ratingsCount) from books where ratingsCount is not null);",
        'index': 12},
    'Books with the Same Author Published in the Same Year': {
        'query': "select book_title BOOKS,book_authors AUTHORS,year YEAR from books where book_authors != 'NA' and year != 'NA' group by year,book_authors,book_title having count(year)>2 and count(book_authors)>2;",
        'index': 13},
    'Books with Specific Keyword in the Title': {
        'query': "select book_title BOOKS from books",
        'index': 14},
    'Year with the Highest Average Book Price': {
        'query': "select year YEAR,avg(amount_retailPrice) AVERAGE_PRICE from books group by year order by average_price desc limit 1;",
        'index': 15},
    'Count Authors Who Published 3 Consecutive Years': {
        'query': "select book_authors AUTHORS from (select distinct book_authors, year from books) as distinct_publications group by book_authors having count(distinct year) >= 3 and max(year) - min(year) >= 2;",
        'index': 16},
    'Authors who have published books in the same year but under different publishers': {
        'query': "select book_authors AUTHORS,year YEAR,count(distinct publisher) PUBLISHER_COUNT,count(*) BOOK_COUNT from books where book_authors != 'NA' and year != 'NA' group by book_authors,year having count(distinct publisher) > 1;",
        'index': 17},
    'Average amount_retailPrice of eBooks and physical books': {
        'query': "select isEbook BOOK_TYPE,avg(amount_retailPrice) AVERAGE_RETAIL_PRICE from books where isEbook is not null group by isEbook;",
        'index': 18},
    'Books that have an averageRating that is more than two standard deviations away from the average rating of all books': {
        'query': "select book_title BOOKS,averageRating AVERAGE_RATING,ratingsCount RATINGS_COUNT from books where averageRating > ((select avg(averageRating) from books) + 2 * (select stddev_samp(averageRating) from books))or averagerating < ((select avg(averagerating) from books) - 2 * (select stddev_samp(averagerating) from books));",
        'index': 19},
    'Which publisher has the highest average rating among its books, but only for publishers that have published more than 10 books': {
        'query': "select publisher PUBLISHER, avg(averageRating) AVERAGE_RATING, count(book_title) NUMBER_OF_BOOKS from books group by publisher having count(*) > 10 order by average_rating desc limit 1;",
        'index': 20},   
}

# BOOK SEARCH PAGE
if r == 'Book Search':
    st.title("LET'S EXPLORE SOME BOOKS!!")
    
    if "data_inserted" not in st.session_state:
        st.session_state.data_inserted = False  # To track if data is inserted
    if "keyword" not in st.session_state:
        st.session_state.keyword = None  # To store the search keyword

    # Keyword input and data fetching
    st.session_state.keyword = st.text_input("Enter the keyword to search!")
        
    if st.button('Submit'):
            if st.session_state.keyword:
                # Truncate the table to remove old data
                truncate()
                API_key = "AIzaSyBu7caYGH0Z2sf9_ZjeucQv41eDXBy4URo"
                book_num = 500
                d = scrap_all(st.session_state.keyword, API_key, book_num)
                all_data_df = data_clean(d,st.session_state.keyword)   
                data_insert(all_data_df)
                st.session_state.data_inserted = True
                st.success(f"Submitted successfully! Now you can get answers to the following queries related to books on {st.session_state.keyword}")
            else:
                st.warning("Please enter a keyword!")

    # Query selection and execution
    if st.session_state.data_inserted:
        sb = st.selectbox('Choose your query', list(questions.keys()))
        
        if sb:
            quest_details = questions[sb]
            quest_query = quest_details["query"]
            quest_no = quest_details["index"]
            data, column_names = execute_query(quest_query)
            df = pd.DataFrame(data, columns=column_names)
            df.index = range(1, len(df) + 1)

            # Handle query-specific display logic
            if quest_no == 1:
                st.write('Number of eBooks available: ' + str(df.iloc[1, 0]))
                st.write('Number of Physical Books available: ' + str(df.iloc[0, 0]))
            elif quest_no == 2:
                st.write(df.iloc[0, 0] + ' with ' + str(df.iloc[0, 1]) + ' books published')
            elif quest_no == 6:
                if df.empty:
                    st.write('Oops! No books with discount greater than 20%')
                else:
                    st.write(df)
            elif quest_no == 7:
                st.write('Average page count for eBooks: ' + str(round(df.iloc[1, 1], 0)))
                st.write('Average page count for Physical Books: ' + str(round(df.iloc[0, 1], 0)))
            elif quest_no == 8:
                fig1, ax1 = plt.subplots()
                ax1.pie(df['book_count'], labels=df['book_authors'], autopct='%1.1f%%', shadow=True, startangle=90)
                ax1.axis('equal')
                st.pyplot(fig1)
            elif quest_no == 14:
                word = st.text_input("Enter the keyword")
                if word:
                    quest_query = f"select book_title BOOKS from books where book_title like '%{word}%'"
                    data, column_names = execute_query(quest_query)
                    df = pd.DataFrame(data, columns=column_names)
                    df.index = range(1, len(df) + 1)
                    st.write(df)
            elif quest_no == 18:
                st.write('Average retail price for eBooks: ' + str(round(df.iloc[1, 1], 0)))
                st.write('Average retail price for Physical Books: Retail price not available')
            else:
                st.write(df)

           