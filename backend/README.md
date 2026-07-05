🚀 How to Run the Friction AI Project (Super Easy Setup Guide)

Hey team! The code is ready. Follow these exact steps to get it running on your screen. Do not skip any steps!

Phase 1: Download the Code
Open VS Code.

At the very top of your screen, click Terminal, then click New Terminal.

Copy and paste this exact command into the terminal and hit Enter:
git clone https://github.com/TharunRam08/friction_hackathon

Once it finishes downloading, go to the top left of VS Code, click File > Open Folder, and select the new friction_hackathon folder.

Phase 2: Start the Dashboard (The UI)
At the top of your screen, click Terminal > New Terminal again.

Type this and press Enter to go into the frontend folder:
cd frontend

Type this and press Enter to download the required files (this takes a minute):
npm install

Type this and press Enter to turn on the screen:
npm run dev
(Leave this terminal window open and running!)

Phase 3: Start the AI Brain (The Backend)
Look at your terminal panel. Click the + (Plus) icon on the top right of that panel to open a second, brand new terminal tab.

Type this and press Enter to go into the backend folder:
cd backend

Type this and press Enter to create a safe Python workspace:
python -m venv venv

Now, turn that workspace on:

If you use Windows: type venv\Scripts\activate and press Enter.

If you use a Mac: type source venv/bin/activate and press Enter.
(You will know it worked if you see a little (venv) appear at the start of your typing line!)

Type this and press Enter to download the AI tools:
pip install -r requirements.txt

Phase 4: Add the Secret Key
Look at your file list on the far left of VS Code. Click the backend folder to open it.

Right-click inside that backend folder and click New File.

Name this new file exactly this: .env (Do not forget the dot at the beginning!)

Open that file and paste our secret team key inside it exactly like this:
GEMINI_API_KEY=[PASTE_YOUR_API_KEY_HERE]

Save the file (Ctrl + S or Cmd + S).

Phase 5: Turn It On!
Go back to your second terminal (the backend one where you typed the Python stuff).

Type this and press Enter to start the engine:
uvicorn main:app --reload

Open Google Chrome (or Safari) and type this into the web address bar:
http://localhost:5173

You are in! Type a business scenario, hit the Reason button, and watch it work. Let me know if you get stuck on any step!
