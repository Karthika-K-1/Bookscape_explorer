# Bookscape_explorer
An interactive web application to explore book data. 

# Introduction
BookScape Explorer is an interactive web application designed to help users discover, analyze, and explore book data from various sources. The project integrates the Google Books API to fetch data about books, stores this data in a well-structured SQL database, and provides powerful insights through SQL queries. The application aims to provide a comprehensive platform for readers, researchers, and book enthusiasts to explore books, analyze trends, and make informed reading choices.

# Objectives
1) To collect and store book data from Google Books API into a structured SQL database.
2) To develop a Streamlit web application having a user-friendly interface to allow users to search and explore book data.
3) To analyze the books by creating SQL queries

# Skills & Technologies Used
Programming Languages: Python (VS Code)
Web Framework: Streamlit
Database Management System: SQL (MySQL)
API Integration: Google Books API
Data Analysis: SQL Queries, Pandas
Visualization Tool: Streamlit (Tables, Charts, Dashboards)

# Data Cleaning
1) Once book details are extracted through API, relevant data is further extracted as dictionary. Pagination is used while extracting 500 data using API as only 40 books are vailable in one page.
2) For each field, .get() used to safely retrieve the value, providing a default value ('NA') if the field is not found. This ensures that missing or empty data doesn't result in errors. In some cases, specific fields like book_authors and categories are processed to join multiple values into a comma-separated string (if they are lists)
3) The dictionary is converted to dataframe to apply further data cleaning.
4) Removed all the duplicate data.
5) In fields where data is missing, 'NA' is used as a placeholder, making it clear that the data is unavailable. For the field, industryIdentifiers (ISBN numbers),the next() function to find the ISBN-13 value is used. If no matching value is found, it defaults to 'NA'.
6) If any values are non-numeric, they are converted to numeric data and coerced to NaN if 'NA' is present. The NaN values are further converted to None. This ensures that when the dataframe is written to a database (MySQL), the NaN values will be stored as NULL (which is the equivalent of missing data in MySQL).
7) Any leading or trailing whitespace,unwanted symbols (such as #, ', ", ..., and brackets)  are removed.

# Data Storage
MySQL database named 'bookscape_explorer_project' is created along with table named 'books'. When the user gives the input search key in the streamlit application,
the book data related to the search key are extracted using the google API key. After the data cleaning process is completed, the cleaned data is stored in the SQL database. SQL queries are executed based on the choice of the user. For every new search key the database gets truncated.

# Conclusion
The BookScape Explorer project successfully achieves its objective of creating a comprehensive, user-friendly platform for exploring and analyzing book data. By integrating the Google Books API, we were able to extract extensive information on a wide range of books, process and clean this data, and store it in a well-structured SQL database for efficient analysis. The use of Streamlit provided an interactive and visually appealing interface for users to explore books, analyze trends, and make data-driven decisions.

Through the implementation of SQL queries, the project offers actionable insights, such as identifying trending genres, popular authors, and books with high ratings. Libraries, bookstores, and readers can use these insights to make informed decisions, fostering better engagement with the world of books.
