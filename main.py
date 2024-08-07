import streamlit as st
import pandas as pd
import base64
import random
import time
import datetime
import os
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course
import pafy  # for uploading YouTube videos
import plotly.express as px  # to create visualizations at the admin session
import nltk
nltk.download('stopwords')

# Resize the image
def resize_image(image_path, output_path, size=(300, 100)):
    """Resize the image to the specified size and save it to the output path."""
    with Image.open(image_path) as img:
        img = img.resize(size, Image.Resampling.LANCZOS)  # Use LANCZOS for high-quality downsampling
        img.save(output_path)

def fetch_yt_video(link):
    video = pafy.new(link)
    return video.title

def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given pandas dataframe to be downloaded."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some string <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()
    # close open handles
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 🎓**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

# CONNECT TO DATABASE
connection = pymysql.connect(host='localhost', user='root', password='Aprilia_3bee', db='cv')
cursor = connection.cursor()

def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    DB_table_name = 'user_data'
    insert_sql = "INSERT INTO " + DB_table_name + """
    VALUES (0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    rec_values = (name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

st.set_page_config(
   page_title="AI Resume Analyzer",
   page_icon='logo_resized.png',
)

def run():
    # Path to the original logo
    original_logo_path = 'logo.png'
    # Path to save the resized logo
    resized_logo_path = 'logo_resized.png'
    
    # Resize the logo
    resize_image(original_logo_path, resized_logo_path, size=(300, 100))  # Adjust size as needed
    
    img = Image.open(resized_logo_path)
    st.image(img)
    st.title("AI Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    link = '[©Developed by Beatrice](https://www.linkedin.com/in/beatricemangentang/)'
    st.sidebar.markdown(link, unsafe_allow_html=True)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS CV;"""
    cursor.execute(db_sql)

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(500) NOT NULL,
                     Email_ID VARCHAR(500) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field BLOB NOT NULL,
                     User_level BLOB NOT NULL,
                     Actual_skills BLOB NOT NULL,
                     Recommended_skills BLOB NOT NULL,
                     Recommended_courses BLOB NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    
    if choice == 'User':
        st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload your resume, and get smart recommendations</h5>''',
                    unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Uploading your Resume...'):
                time.sleep(4)
                
            # Ensure directory exists
            upload_dir = 'Uploaded_Resumes'
            os.makedirs(upload_dir, exist_ok=True)
            
            save_image_path = os.path.join(upload_dir, pdf_file.name)
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
                
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                # Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello "+ resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown( '''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''',unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >=3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)

                # st.subheader("**Skills Recommendation💡**")
                # Skill shows
                keywords = st_tags(label='### Your Current Skills',
                text='See our skills recommendation below',
                    value=resume_data['skills'], key='1')

                # Keywords
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''
                # Courses recommendation
                for i in resume_data['skills']:
                    # Data science recommendation
                    if i.lower() in ds_keyword:
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms']
                        recommended_skills = [i for i in recommended_skills if i not in resume_data['skills']]
                        rec_course = course_recommender(ds_course)
                        break

                    # Web development recommendation
                    elif i.lower() in web_keyword:
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node JS','React JS','PHP','Laravel','Magento','Wordpress','Javascript','Angular JS','c#','Flask']
                        recommended_skills = [i for i in recommended_skills if i not in resume_data['skills']]
                        rec_course = course_recommender(web_course)
                        break

                    # Android App Development
                    elif i.lower() in android_keyword:
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Android Development','Flutter','Kotlin','XML','Kivy']
                        recommended_skills = [i for i in recommended_skills if i not in resume_data['skills']]
                        rec_course = course_recommender(android_course)
                        break

                    # IOS App Development
                    elif i.lower() in ios_keyword:
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS Development Jobs **")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode']
                        recommended_skills = [i for i in recommended_skills if i not in resume_data['skills']]
                        rec_course = course_recommender(ios_course)
                        break

                    # Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UX','Adobe XD','Figma','Zeplin','Balsamiq','UI','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Photoshop','Editing','Adobe Illustrator','Illustrator','Adobe After Effects','After Effects','Adobe Premier Pro','Premier Pro','Adobe Indesign','Indesign','Wireframe','Solid','Grasp','User Research','User Experience']
                        recommended_skills = [i for i in recommended_skills if i not in resume_data['skills']]
                        rec_course = course_recommender(uiux_course)
                        break

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Insert into table
                insert_data(resume_data['name'], resume_data['email'], str(random.randint(50,100)), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, ', '.join(resume_data['skills']), ', '.join(recommended_skills), ', '.join(rec_course))

            else:
                st.error('Something went wrong..')

    elif choice == 'Admin':
        st.header("**Welcome Admin**")
        st.subheader("**Here is the users' data**")
        sql = "SELECT * FROM user_data"
        cursor.execute(sql)
        df = pd.read_sql(sql, connection)
        st.dataframe(df)
        st.markdown(get_table_download_link(df, 'users_data.csv', 'Download CSV'), unsafe_allow_html=True)

        # Visualizations
        st.subheader("**Resume Score Visualization**")
        score_df = df[['Name', 'resume_score']]
        fig = px.histogram(score_df, x='resume_score', title='Distribution of Resume Scores')
        st.plotly_chart(fig)

        st.subheader("**Users by Predicted Field Visualization**")
        field_df = df[['Predicted_Field']]
        field_df['Predicted_Field'] = field_df['Predicted_Field'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
        field_count = field_df['Predicted_Field'].value_counts()
        fig2 = px.pie(names=field_count.index, values=field_count.values, title='Distribution of Predicted Fields')
        st.plotly_chart(fig2)

        st.subheader("**Users by Experience Level Visualization**")
        level_df = df[['User_level']]
        level_df['User_level'] = level_df['User_level'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
        level_count = level_df['User_level'].value_counts()
        fig3 = px.bar(x=level_count.index, y=level_count.values, title='Distribution of Experience Levels')
        st.plotly_chart(fig3)

        st.subheader("**Skills Analysis**")
        all_skills = df['Actual_skills'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x).str.split(',').explode()
        skills_count = all_skills.value_counts()
        fig4 = px.bar(x=skills_count.index, y=skills_count.values, title='Distribution of Skills')
        st.plotly_chart(fig4)

if __name__ == "__main__":
    run()
