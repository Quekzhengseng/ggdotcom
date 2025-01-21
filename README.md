# ggdotcom
**File structure**
The project consist of BACKEND and FRONTEND folder within the same git repo. Both are deployed online as of now.

Accessing the app:
Website can be https://ggdotcom.vercel.app , currently no login is required for ease of use and judging. 
You will not be able to deploy the backend locally as all the APIs calls are made online through render. However, you will be able to run the frontend folder. Regardless, please use the online website for judging. 

Frontend Setup Instructions:
Clone frontend/app into a folder. In terminal, run npm i followed by npm run dev. A localhost of the website should then run.

Instructions to note:
 - As there is no authentication, do run the website one person at a time due to database clashing.
 - Running the app outside of Chinatown or in the heartlands might give less than desirable results due to lack of RAG documents inputted
 - Users can either use the a) start tour app or b) Simulator
   
   a)  The tour app have several functions;
     1. Enabling auto location will prompt the LLM for a response every 150 seconds.
     2. Sending a photo or text will prompt the LLM for a response in regards to the photo or said text.
     3. The response will be converted to audio output for the user to hear. Currently, text only output has not been added.
        
   b) The tour app simulator
      You will be able to see all the functions of the app in the simulator, it will auto run 5 different coordinates along chinatown, with one request being made with text and another made with a photo.

   c) The map app
    1. Able to see nearby landmarks within your location
    2. Able to genAI the locations replies as well as questioning of the location itself
    3. Able to filter the nearby locations either by prominence or distance, colour of the pin represent as such.
  
  d) The map simulator
   1. The map simulator is able to run through the coordinate of chinatown to scan the nearby landmarks

Things to note when running the deployed app:
 - Currently, when running both the simulator and the app, each interval of msg with AUTO LOCATION turned on will take 5 and 150 seconds respectively. This timing is currently fixed.
 - Currently, questions or photos will be taken with respect with the location. Hence, giving a photo of the merlion while physically at the west side of Singapore would cause the LLM to reject the statement due to our prompt that is given.


Deployement Infrastructure:
FRONTEND 
- Deployed on VERCEL
  
  a) DATA
  - requires location
  - text prompt / Image
    
  b) API CALLS
  - /chat using method post with location/text/image call for response
  - /messages using method get to retrieve all past messages


BACKEND 
- Deployed on RENDER (https://ggdotcom.onrender.com)
  
  a) DATA
  - ChromaDB embeddings stored in firebase
  - Stores replies from ChatGPT in firestore
    
  b) API Calls
  - Firebase calls
  - OpenAI calls
  - Google Map calls

Things to note regarding infrastructure:
- Due to the free tier of render, inactivity will cause the system to shutdown. Currently, this is mitigated via starting a monitor on uptimerobot with a interval of every 14 minute to ping the render to prevent shutdown.
- There is currently no scalling or load balancing with free tier of render, multiple users on the app will cause some delay in response.
- The team is currently using paid for OpenAI key, please use the app with discretion as we have only inputted 10 dollar in total.

Future Improvements:
- Shift to production based cloud platforms to allow for load balancing
- Improved RAG documents to other parts of Singapore
- Authentication when in production

Contributors:
Quek Zheng Seng, Brejesh, Dwight, Alyssa

**Any questions regarding backend infrastructure or if the website is down, contact @quekkyz on telegram. Thank you.**
