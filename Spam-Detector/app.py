# Modules
import pyrebase
import streamlit as st
from datetime import datetime
import requests
import pickle
import string
from nltk.corpus import stopwords
import nltk
from nltk.stem.porter import PorterStemmer
from streamlit_lottie import st_lottie


st.set_page_config(page_title='Spam Detector')
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Configuration Key
firebaseConfig = {
    'apiKey': "",
    'authDomain': "",
    'projectId': "",
    'databaseURL': "",
    'storageBucket': "",
    'messagingSenderId': "",
    'appId': "",
}

# Firebase Authentication
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Database
db = firebase.database()
storage = firebase.storage()
st.sidebar.title("Spam Detector App")

# Authentication
choice = st.sidebar.selectbox('login/Signup', ['Login', 'Sign up'])

# Obtain User Input for email and password
email = st.sidebar.text_input('Please enter your email address', type = 'default')
password = st.sidebar.text_input('Please enter your password',type = 'password')



# Sign up Block
if choice == 'Sign up':
    handle = st.sidebar.text_input(
        'Please input your app handle name', value='Default')
    submit = st.sidebar.button('Create my account')

    if submit:
        user = auth.create_user_with_email_and_password(email, password)
        st.success('Your account is created suceesfully!')
        st.balloons()
        # Sign in
        user = auth.sign_in_with_email_and_password(email, password)
        db.child(user['localId']).child("Handle").set(handle)
        db.child(user['localId']).child("ID").set(user['localId'])
        st.title('Welcome ' + handle)
        st.info('Login via login drop down selection')

# Login Block
if choice == 'Login':
    login = st.sidebar.checkbox('Login/Logout')
    if login:
        user = auth.sign_in_with_email_and_password(email,password)
        st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
        bio = st.radio('Jump to',['Home','Workplace Feeds', 'Model', 'About Us', 'FAQ', 'Contact Us', 'Settings'])
        
# SETTINGS PAGE 
        if bio == 'Settings':  
            # CHECK FOR IMAGE
            nImage = db.child(user['localId']).child("Image").get().val()    
            # IMAGE FOUND     
            if nImage is not None:
                # We plan to store all our image under the child image
                Image = db.child(user['localId']).child("Image").get()
                for img in Image.each():
                    img_choice = img.val()
                    #st.write(img_choice)
                st.image(img_choice)
                exp = st.expander('Change Bio and Image')  
                # User plan to change profile picture  
                with exp:
                    newImgPath = st.text_input('Enter full path of your profile imgae')
                    upload_new = st.button('Upload')
                    if upload_new:
                        uid = user['localId']
                        fireb_upload = storage.child(uid).put(newImgPath,user['idToken'])
                        a_imgdata_url = storage.child(uid).get_url(fireb_upload['downloadTokens']) 
                        db.child(user['localId']).child("Image").push(a_imgdata_url)
                        st.success('Success!')           
            # IF THERE IS NO IMAGE
            else:    
                st.info("No profile picture yet")
                newImgPath = st.text_input('Enter full path of your profile image')
                upload_new = st.button('Upload')
                if upload_new:
                    uid = user['localId']
                    # Stored Initated Bucket in Firebase
                    fireb_upload = storage.child(uid).put(newImgPath,user['idToken'])
                    # Get the url for easy access
                    a_imgdata_url = storage.child(uid).get_url(fireb_upload['downloadTokens']) 
                    # Put it in our real time database
                    db.child(user['localId']).child("Image").push(a_imgdata_url)


# model page
        elif bio == 'Model':
            
            def load_lottieurl(url):
                r = requests.get(url)
                if r.status_code != 200:
                    return None
                return r.json()

            lottie_animation = load_lottieurl("https://lottie.host/7d8c4032-899d-49a0-b04f-955e409368fb/8oYY96I9oq.json")

            ps = PorterStemmer()


            def transform_text(text):
                text = text.lower()
                text = nltk.word_tokenize(text)

                y = []
                for i in text:
                    if i.isalnum():
                        y.append(i)

                text = y[:]
                y.clear()

                for i in text:
                    if i not in stopwords.words('english') and i not in string.punctuation:
                        y.append(i)

                text = y[:]
                y.clear()

                for i in text:
                    y.append(ps.stem(i))

                return " ".join(y)

            tfidf = pickle.load(open('vectorizer1.pkl','rb'))
            # print(tfidf)
            model = pickle.load(open('model1.pkl','rb'))

            st.title("Email/SMS Spam Classifier")
            st.write("---")
            with st.container():
                st_lottie(lottie_animation, height=220, key="spam detection")
                

            input_sms = st.text_area("Enter the message")

            if st.button('Predict'):
                # 1. preprocess
                transformed_sms = transform_text(input_sms)
                # 2. vectorize
                vector_input = tfidf.transform([transformed_sms])
                # 3. predict
                result = model.predict(vector_input)[0]
                # 4. Display
                if result == 1:
                    st.header("Spam")
                elif transformed_sms == '':
                    st.warning("Please provide text above")
                else:
                    st.header("Not Spam")
                
               
                now_chat = datetime.now()
                dt_string_chat = now_chat.strftime("%d/%m/%Y %H:%M:%S")              
                input_sms = {'Message:' : input_sms,'Timestamp' : dt_string_chat}                           
                results_chat = db.child(user['localId']).child("Posts_chat").push(input_sms)

            st.subheader("Previously Searched")
            all_posts_chat = db.child(user['localId']).child("Posts_chat").get()
            if all_posts_chat.val() is not None:    
                for Posts_chat in reversed(all_posts_chat.each()):
                        #st.write(Posts.key()) # Morty
                        st.code(Posts_chat.val(),language = '')

# About us section
        elif bio == 'About Us':
            st.title("About us")
            st.write("---")
            st.write("Welcome, We are your trusted partner in the battle against spam messages. We are dedicated to creating a safer online environment by harnessing cutting-edge technology to detect and prevent spam messages in real-time. In an era where digital communication is at the heart of our personal and professional lives, spam messages have become an ever-present nuisance. They clutter our inboxes, disrupt our workflow, and sometimes even pose security risks. At [Your Company Name], we understand the frustration and potential harm that spam can cause, which is why we are committed to providing effective solutions.")

            st.subheader("Our mission")
            st.write("Our mission is clear: to empower individuals and organizations to regain control of their digital communication by identifying and filtering out spam messages seamlessly and efficiently. We believe that everyone deserves to have a spam-free inbox, where valuable messages can be received without distraction or concern.")

            st.subheader("What We Offer:")
            st.write("Text Analysis Tool: Simply paste any text content into our tool, and we'll analyze it in real-time to             detect and flag potential spam.")
            st.subheader("How We Detect Spam")
            st.write("At the core of our service is advanced machine learning technology. Our team of dedicated experts has developed a sophisticated algorithm that analyzes input text and assigns a spam probability score. This score is based on a wide range of factors, including content, sender reputation, and behavioral patterns. By constantly learning and adapting to new spam tactics, our system stays ahead of the game, ensuring that even the most subtle forms of spam are identified and eliminated.")

            st.write("we take pride in being your dependable partner in the fight against spam. Whether you are an individual looking to clean up your personal inbox or a business seeking to protect your employees and customers, we are here to help. Join us in making the digital world a safer and more enjoyable place")

# FAQ Section
        elif bio == 'FAQ':
            st.title("Frequently Asked Questions (FAQ's)")
            st.write("---")
            st.subheader("How does the Text Analysis Tool work?")
            st.write("The Text Analysis Tool utilizes advanced algorithms and machine learning models to analyze text content. It examines the content's structure, language, and patterns to determine whether it is spam or legitimate.")

            st.subheader("Is the Text Analysis Tool free to use?")
            st.write("Yes, our Text Analysis Tool is available for free, ensuring accessibility to everyone. ")

            st.subheader("How accurate is the spam detection?")
            st.write("Our spam detection system boasts high accuracy and precision. We continually refine our algorithms to minimize false positives, ensuring reliable results.")

            st.subheader("Do I need technical expertise to use the tool?")
            st.write("No, you don't need technical expertise to use our tool. It is designed to be user-friendly and straightforward, requiring no special skills.")

            st.subheader("What types of text can I analyze?")
            st.write("You can analyze various types of text content, including emails, messages, social media posts, and more. Our tool is versatile and suitable for different text formats.")

            st.subheader("How long does it take to get results?")
            st.write("Our Text Analysis Tool provides results within seconds. It offers near-instantaneous analysis, allowing you to make decisions promptly.")

            st.subheader("What should I do if the tool detects spam?")
            st.write("If spam is detected, we recommend avoiding interaction with the content. Our tool is designed to help you identify potentially harmful or unwanted content.")

            st.subheader("Is my data secure during the analysis process?")
            st.write("Yes, we take data privacy seriously. Your text content is analyzed securely, and we have measures in place to protect your data throughout the process.")

            st.subheader("Can I use the tool on mobile devices?")
            st.write("Yes, our Text Analysis Tool is mobile-friendly and compatible with various devices, including mobile phones and tablets.")

            st.subheader("Is customer support available if I encounter issues?")
            st.write("Absolutely. Our dedicated support team is here to assist you with any questions or issues you may encounter. You can reach out to us through out Contact page.")


# Contact us section
        elif bio == 'Contact Us':
            st.title("Contact Us")
            st.header(":mailbox: Get In Touch With Us!")


            contact_form = """
            <form action="https://formsubmit.co/sanyamsethiya20274@acropolis.in" method="POST">
                <input type="hidden" name="_captcha" value="false">
                <input type="text" name="name" placeholder="Your name" required>
                <input type="email" name="email" placeholder="Your email" required>
                <textarea name="message" placeholder="Your message here"></textarea>
                <button type="submit">Send</button>
            </form>
            """

            st.markdown(contact_form, unsafe_allow_html=True)

            # Use Local CSS File
            def local_css(file_name):
                with open(file_name) as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


            local_css("style/ContactFormStyle.css")

# HOME PAGE
        elif bio == 'Home':
            col1, col2 = st.columns(2)
            
            # col for Profile picture
            with col1:
                # db = firebase.database()
                # db.child(user['localId']).child("Handle").set(handle)
                # st.title('Hello' + handle)
                nImage = db.child(user['localId']).child("Image").get().val()         
                if nImage is not None:
                    val = db.child(user['localId']).child("Image").get()
                    for img in val.each():
                        img_choice = img.val()
                    st.image(img_choice,use_column_width=True)
                else:
                    st.info("No profile picture yet. Go to settings and choose one!")
                
                post = st.text_input("Let's share my current mood as a post!",max_chars = 200)
                add_post = st.button('Share Posts')
            if add_post:   
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")              
                post = {'Post:' : post,
                        'Timestamp' : dt_string}                           
                results = db.child(user['localId']).child("Posts").push(post)
                st.success('Success!') 

            # This coloumn for the post Display
            with col2:
                
                all_posts = db.child(user['localId']).child("Posts").get()
                if all_posts.val() is not None:    
                    for Posts in reversed(all_posts.each()):
                            #st.write(Posts.key()) # Morty
                            st.code(Posts.val(),language = '') 

        
# WORKPLACE FEED PAGE
        else:
            all_users = db.get()
            res = []
            # Store all the users handle name
        
            for users_handle in all_users.each():
                try:
                     k = users_handle.val()["Handle"]
                     res.append(k)
                except KeyError:
                    print("The 'Handle' key is not found in the dictionary.")

            # Total users
            nl = len(res)
            st.write('Total users here: '+ str(nl)) 
            
            # Allow the user to choose which other user he/she wants to see 
            choice = st.selectbox('My Collegues',res)
            push = st.button('Show Profile')
            
            # Show the choosen Profile
            if push:
                for users_handle in all_users.each():
                    k = users_handle.val()["Handle"]
                    # 
                    if k == choice:
                        lid = users_handle.val()["ID"]
                        
                        handlename = db.child(lid).child("Handle").get().val()             
                        
                        st.markdown(handlename, unsafe_allow_html=True)
                        
                        nImage = db.child(lid).child("Image").get().val()         
                        if nImage is not None:
                            val = db.child(lid).child("Image").get()
                            for img in val.each():
                                img_choice = img.val()
                                st.image(img_choice)
                        else:
                            st.info("No profile picture yet. Go to Edit Profile and choose one!")
 
                        # All posts
                        all_posts = db.child(lid).child("Posts").get()
                        if all_posts.val() is not None:    
                            for Posts in reversed(all_posts.each()):
                                st.code(Posts.val(),language = '')
