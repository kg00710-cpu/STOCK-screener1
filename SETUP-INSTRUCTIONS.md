# Setting this up — plain-English guide (Mac)

You do NOT need to install anything or type any commands.
Everything below is clicking on a website. Takes about 15 minutes, once.

When you're done, you'll have a web link (works on your laptop AND phone)
that updates itself every 15 minutes during market hours, plus once after
the close — even when your laptop is switched off.

---------------------------------------------------------------------------
STEP 1 — Make a free GitHub account (2 min)   [skip if you have one]
---------------------------------------------------------------------------
1. Go to  https://github.com/signup
2. Enter your email, pick a password and a username, verify your email.
   Choose the FREE plan when offered.

---------------------------------------------------------------------------
STEP 2 — Create a place to put the files (2 min)
---------------------------------------------------------------------------
1. Go to  https://github.com/new
2. "Repository name": type      stock-screener
3. Select  PUBLIC   (Pages needs this on the free plan)
4. TICK the box "Add a README file"      <-- important, do tick it
5. Click the green "Create repository" button.

---------------------------------------------------------------------------
STEP 3 — Upload the files (3 min)
---------------------------------------------------------------------------
1. On your new repository page, click  "Add file"  (grey button, upper right)
   then choose  "Upload files".
2. Open the folder I gave you in Finder.
3. Select ALL the visible items and drag them onto the upload box:
        README.md
        SETUP-INSTRUCTIONS.md
        index.html
        data          (folder)
        scripts       (folder)
        workflow-file (folder)      <-- see STEP 4, this one matters
4. Wait for the upload bars to finish (data.json is biggish, ~30 seconds).
5. Scroll down, click the green  "Commit changes"  button.

---------------------------------------------------------------------------
STEP 4 — Put the schedule file in the right place (3 min)
---------------------------------------------------------------------------
GitHub needs the schedule file inside a folder named ".github/workflows".
Folders starting with a dot are hidden by the Mac Finder, so we do it on the
website instead. It sounds fiddly; it is just typing one line.

1. On your repository page click  "Add file"  ->  "Create new file".
2. In the filename box at the top, type EXACTLY this (including the slashes):

        .github/workflows/update.yml

   As you type each "/", GitHub turns it into a folder automatically.
3. Open the file  workflow-file/update.yml  from the folder I gave you
   (double-click it; it opens in TextEdit).
   Select all the text (Cmd+A), copy it (Cmd+C).
4. Click into the big empty box on GitHub and paste (Cmd+V).
5. Scroll down, click the green  "Commit changes"  button, then "Commit"
   in the pop-up.

---------------------------------------------------------------------------
STEP 5 — Give the robot permission to save data (1 min)
---------------------------------------------------------------------------
1. On your repository, click  "Settings"  (top row, right side).
2. In the left sidebar click  "Actions"  ->  "General".
3. Scroll to the bottom, "Workflow permissions".
4. Select  "Read and write permissions".
5. Click  "Save".

(Without this, the updater can run but can't save the fresh data.)

---------------------------------------------------------------------------
STEP 6 — Turn on the web page (2 min)
---------------------------------------------------------------------------
1. Still in  "Settings", click  "Pages"  in the left sidebar.
2. Under "Build and deployment" -> "Source", choose  "Deploy from a branch".
3. Branch: choose  "main",  folder: choose  "/ (root)".  Click  "Save".
4. Wait 1-2 minutes. The page will show your link, which looks like:

        https://YOUR-USERNAME.github.io/stock-screener/

   Open it. Bookmark it. That's your screener.

---------------------------------------------------------------------------
STEP 7 — Run the updater once, right now (1 min)
---------------------------------------------------------------------------
1. Click the  "Actions"  tab (top row of your repository).
2. If it asks you to enable workflows, click the green button to enable.
3. On the left, click  "Update screener data".
4. On the right, click  "Run workflow"  ->  then the green "Run workflow".
5. Wait ~2 minutes, refresh the page: a green tick means it worked.

From now on it runs by itself. You never have to touch it again.

---------------------------------------------------------------------------
IF SOMETHING LOOKS WRONG
---------------------------------------------------------------------------
* Page says "Couldn't load data/data.json"
  -> Wait 2 minutes after Step 6 and refresh. If it persists, check that the
     "data" folder uploaded (you should see it listed on your repo page).

* Actions tab shows a red X instead of a green tick
  -> Almost always Step 5 was missed. Redo Step 5, then re-run Step 7.

* No "Actions" tab / nothing listed there
  -> The file in Step 4 isn't in the right place. Check your repo shows a
     folder called ".github" — if not, redo Step 4 carefully.

* Everything works but numbers look stale
  -> The market may be closed (it only updates Mon-Fri, 9:15am-3:30pm IST),
     or GitHub's scheduler is running late, which is normal. Use the
     "refresh now" link in the page header, or re-run Step 7 manually.

---------------------------------------------------------------------------
WHAT YOU'RE GETTING (and what you're not)
---------------------------------------------------------------------------
* Updates every 15 minutes during Indian market hours, plus after the close.
* Free. Runs on GitHub's computers, not yours.
* The data is Yahoo Finance's DELAYED daily prices - good for a statistical
  screen, but it is NOT a live tick-by-tick trading feed and has no bid/ask.
* This is a description of recent price behaviour. It is NOT investment advice.
