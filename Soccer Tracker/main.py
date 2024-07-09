import os
import requests
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Label, Frame, Canvas, Text, BOTH
from PIL import Image, ImageTk, ImageEnhance
import http.client
import json
from io import BytesIO
import requests

leagues_info = {
    "Premier League": {"id": "39", "logo": "PremierLeague.png"},
    "La Liga": {"id": "140", "logo": "LaLiga.png"},
    "Ligue 1": {"id": "61", "logo": "Ligue1.png"},
    "Serie A": {"id": "135", "logo": "SeriaA.png"},
    "Bundesliga": {"id": "78", "logo": "Bundesliga.png"}
}

API_KEY = os.environ.get('FOOTBALL_API_KEY')
if not API_KEY:
    raise ValueError("API Key not found in environment variables")

headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

class LeagueGUI:
    def __init__(self, master):
        #Creates the OG window 
        self.master = master
        self.master.title("Top 5 Leagues Stats")
        self.master.geometry("600x770")

        self.tree_frame = tk.Frame(master)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        #tree that displays leagues \

        self.tree = ttk.Treeview(self.tree_frame, columns=("League",), show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        self.image_refs = {}  
        self.load_leagues()

        self.selection_frame = tk.Frame(master)
        self.selection_frame.pack(pady=20)

        self.selected_label = tk.Label(self.selection_frame, text="")
        self.selected_label.pack()

        self.year_label = tk.Label(self.selection_frame, text="Enter Season:")
        self.year_label.pack()

        self.year_entry = tk.Entry(self.selection_frame)
        self.year_entry.pack()

        self.submit_button = tk.Button(self.selection_frame, text="Finalize", command=self.Load_league_season)
        self.submit_button.pack()

        # need these for future methods to display info 
        self.selected_league = None
        self.current_standings = None
        self.current_season = None


    # first window, displays the top five leagues 
    def load_leagues(self):

        
        style = ttk.Style()
        style.configure("Treeview", rowheight=60, font=('Arial', 10, 'bold'))
        
        
        #different greens 
        dark_green = '#1B8A4A' 
        light_green = '#2ECC71'  
        
        for i, (league_name, info) in enumerate(leagues_info.items()):
            img = Image.open(info["logo"])
            img = img.resize((50, 50), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            tag = f"row{(i % 2)}"

            item = self.tree.insert("", tk.END, values=(league_name,), image=photo, tags=(tag, "selectable"))
           
            self.image_refs[league_name] = photo

            self.tree.insert("", tk.END, text="", values=(" ",), tags=(f"spacer{i % 2}",))

        #darker green rows
        self.tree.tag_configure("row0", background=dark_green, foreground="white")
        self.tree.tag_configure("row1", background=dark_green, foreground="white")

        #lighter green rows
        self.tree.tag_configure("spacer0", background=light_green)
        self.tree.tag_configure("spacer1", background=light_green)
        
        self.tree.tag_bind("spacer0", "<<TreeviewSelect>>", self.prevent_spacer_selection)
        self.tree.tag_bind("spacer1", "<<TreeviewSelect>>", self.prevent_spacer_selection)

    #doesnt allow user to hover over the spacer rows so it doesnt ruin the color scheme 
    def prevent_spacer_selection(self, event):
        self.tree.selection_remove(self.tree.selection())

    #allows user to hover over the league and select them 
    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            league_name = self.tree.item(selected_item)["values"][0]
            if league_name and league_name.strip() != "":
                self.selected_label.config(text=f"Selected League: {league_name}")
                self.selected_league = leagues_info[league_name]["id"]
                self.year_label.config(text="Enter Season Year:")
            else:
                self.tree.selection_remove(selected_item)

    #loading the standings window, this is where we make the api call 
    def Load_league_season(self):
        if not self.selected_league:
            messagebox.showerror("Error", "Please select a league first")
            return

        year = self.year_entry.get()
        if not year.isdigit():
            messagebox.showerror("Invalid input", "Please enter a valid year")
            return

        conn = http.client.HTTPSConnection("v3.football.api-sports.io")

        endpoint = f"/standings?league={self.selected_league}&season={year}"
        
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read().decode("utf-8")

        if res.status == 200:
            json_data = json.loads(data)
            self.display_standings(json_data, year)
        else:
            messagebox.showerror("Error", f"Failed to fetch data: {res.status} {res.reason}")

        conn.close()

    #crazy method chat gpt gave me, makes sense retroactivey 
    def create_gradient(self, canvas, color1, color2, width, height):
        r1, g1, b1 = self.master.winfo_rgb(color1)
        r2, g2, b2 = self.master.winfo_rgb(color2)
        r_ratio = (r2 - r1) / height
        g_ratio = (g2 - g1) / height
        b_ratio = (b2 - b1) / height
        for i in range(height):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = f'#{nr:04x}{ng:04x}{nb:04x}'
            canvas.create_line(0, i, width, i, fill=color)

    #how we display the Standings info 
    def display_standings(self, data, year):
        standings_window = Toplevel(self.master)
        standings_window.title(f"{self.get_league_name()} Standings {year}")
        standings_window.geometry("750x1100")
        standings_window.attributes('-alpha', 0.9)

        #parsing the api call 
        standings = data['response'][0]['league']['standings']
        if isinstance(standings, list) and len(standings) > 0:
            standings = standings[0]

        sorted_standings = sorted(standings, key=lambda x: int(x.get('points', '0')), reverse=True)
        self.current_standings = sorted_standings
        self.current_season = year

        #get the colors for the gradient 
        colors = self.get_league_colors()

        canvas = Canvas(standings_window, width=750, height=1100, bg=colors['bg'])
        canvas.pack(fill="both", expand=True)

    
        self.create_gradient(canvas, colors['bg'], colors['gradient_end'], 750, 1100)

    
        logo_path = self.get_league_logo()
        
        if logo_path:
            logo_img = Image.open(logo_path)
            #custom dimensions for each image cuz they are weird
            resize_dimensions = {
                "SerieA.png": (200, 200),
                "PremierLeague.png": (200, 200),
                "LaLiga.png": (200, 100),
                "Ligue1.png": (100, 200),
                "Bundesliga.png": (200, 200)
            }       

            if logo_path in resize_dimensions:
                logo_img = logo_img.resize(resize_dimensions[logo_path], Image.LANCZOS)
            else:
                logo_img = logo_img.resize((150, 150), Image.LANCZOS)

            #adds at top of the page, 
            logo_photo = ImageTk.PhotoImage(logo_img)
            canvas.create_image(375, 100, image=logo_photo)
            canvas.image = logo_photo  

        main_frame = Frame(canvas, bg='white', bd=2, relief='solid')  
        main_frame.place(relx=0.5, rely=0.45, anchor="center")

        headers = ['Pos', 'Team', 'MP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts']
        for col, header in enumerate(headers):
            Label(main_frame, text=header, font=('Arial', 10, 'bold'), 
                    bg=colors['bg'], fg=colors['header_fg']).grid(row=0, column=col, padx=5, pady=5, sticky='w')

        # A lot going on, essentially creating all the rows and columns of the tree. Adding the name, wins, etc..
        for row, team in enumerate(sorted_standings, start=1):
            bg_color = 'white' if row % 2 == 0 else '#f0f0f0'
            Label(main_frame, text=str(row), bg=bg_color, fg=colors['text']).grid(row=row, column=0, padx=5, pady=2, sticky='w')
            Label(main_frame, text=team.get('team', {}).get('name', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=1, padx=5, pady=2, sticky='w')
            
            all_stats = team.get('all', {})
            Label(main_frame, text=all_stats.get('played', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=2, padx=5, pady=2)
            Label(main_frame, text=all_stats.get('win', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=3, padx=5, pady=2)
            Label(main_frame, text=all_stats.get('draw', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=4, padx=5, pady=2)
            Label(main_frame, text=all_stats.get('lose', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=5, padx=5, pady=2)
            
            #could also maybe implement this at the bottom for more info 
            goals = all_stats.get('goals', {})


            Label(main_frame, text=goals.get('for', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=6, padx=5, pady=2)
            Label(main_frame, text=goals.get('against', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=7, padx=5, pady=2)
            
            Label(main_frame, text=team.get('goalsDiff', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=8, padx=5, pady=2)
            Label(main_frame, text=team.get('points', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=9, padx=5, pady=2)

        analysis_frame = Frame(canvas, bg='white')
        analysis_frame.place(relx=0.5, rely=0.85, anchor="center", width=700)

        analysis_label = Label(analysis_frame, text="Type Team Name for Further Stats", bg='white', font=('Arial', 10, 'bold'))
        analysis_label.pack(pady=(10, 5))

        self.analysis_text = Text(analysis_frame, height=1, width=15)
        self.analysis_text.pack(pady=5)

        analysis_button = tk.Button(analysis_frame, text="More Info", command=self.get_analysis)
        analysis_button.pack(pady=5)

        button_frame = Frame(canvas, bg=colors['bg'])
        button_frame.place(relx=0.5, rely=0.95, anchor="center")

        for widget in main_frame.winfo_children():
            if isinstance(widget, Label) and widget.cget("text") not in headers:
                widget.bind("<Button-1>", lambda e, w=widget: self.on_team_select(w))

    # window that displays the desired team stats 
    def display_team_stats(self, team_stats):
        stats_window = Toplevel(self.master)
        stats_window.title(f"Team Statistics: {team_stats['response']['team']['name']}")
        stats_window.geometry("600x500")

       #creates window/canvas
        canvas = Canvas(stats_window, width=600, height=500)
        canvas.pack(fill="both", expand=True)

      
        self.create_gradient(canvas, "#1a237e", "#4a148c", 600, 500)

    
        main_frame = Frame(canvas, bg="white", bd=2, relief="raised")
        main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

        logo_url = team_stats['response']['team']['logo']
        logo_image = self.get_image_from_url(logo_url, (100, 100))
        if logo_image:
            logo_label = Label(main_frame, image=logo_image, bg="white")
            logo_label.image = logo_image
            logo_label.pack(pady=(20, 10))


        Label(main_frame, text=team_stats['response']['team']['name'], 
            font=("Arial", 18, "bold"), bg="white", fg="#1a237e").pack(pady=(0, 20))

        stats_frame = Frame(main_frame, bg="white")
        stats_frame.pack(fill="both", expand=True, padx=20)

       #Styles
        title_style = {"font": ("Arial", 12, "bold"), "bg": "white", "fg": "#4a148c"}
        value_style = {"font": ("Arial", 12), "bg": "white", "fg": "#1a237e"}

        #keeps all stats in a respective list that we will make look cool with styling 
        stats = [
            ("League", team_stats['response']['league']['name']),
            ("Season", team_stats['response']['league']['season']),
            ("Matches Played", team_stats['response']['fixtures']['played']['total']),
            ("Wins", team_stats['response']['fixtures']['wins']['total']),
            ("Draws", team_stats['response']['fixtures']['draws']['total']),
            ("Losses", team_stats['response']['fixtures']['loses']['total']),
            ("Goals For", team_stats['response']['goals']['for']['total']['total']),
            ("Goals Against", team_stats['response']['goals']['against']['total']['total'])
        ]
        #two columns, adds the style to the list
        for i, (title, value) in enumerate(stats):
            row = i // 2
            col = i % 2
            Label(stats_frame, text=f"{title}:", **title_style).grid(row=row, column=col*2, sticky="e", pady=5, padx=(0, 5))
            Label(stats_frame, text=str(value), **value_style).grid(row=row, column=col*2+1, sticky="w", pady=5)




    #\GETTERS AND SETTERS/#


    #loads Image of the desired team 
    def get_image_from_url(self, url, size):
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img = img.resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    def on_team_select(self, widget):
        team_name = widget.cget("text")
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, team_name)
        self.get_analysis()


    def get_analysis(self):
        analysis_request = self.analysis_text.get("1.0", tk.END).strip()
        if analysis_request:
            #look for the team ID
            team_id = None
            for team in self.current_standings:
                if team['team']['name'].lower() == analysis_request.lower():
                    team_id = team['team']['id']
                    break
            #error if you dont fidn
            if team_id is None:
                messagebox.showerror("Error", f"Team '{analysis_request}' not found in the current standings.")
                return

            
            conn = http.client.HTTPSConnection("v3.football.api-sports.io")
            endpoint = f"/teams/statistics?season={self.current_season}&team={team_id}&league={self.selected_league}"
            
            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            conn.close()

            if res.status == 200:
                team_stats = json.loads(data)
                self.display_team_stats(team_stats)
            else:
                messagebox.showerror("Error", f"Failed to fetch team statistics: {res.status} {res.reason}")
        else:
            messagebox.showwarning("Empty Request", "Please enter a team name.")

    def get_league_name(self):
        
        for name, info in leagues_info.items():
            if info['id'] == self.selected_league:
                return name
        return "Unknown League"
    
        #store it in dictionary makes iot easyg to access
    def get_league_colors(self):
        league_colors = {
            "39": {  # Premier League
                "bg": "#3D195B", "gradient_end": "#7F54B3", "header_fg": "#FFFFFF", "text": "#000000"
            },
            "140": {  # La Liga
                "bg": "#EE8707", "gradient_end": "#FFC300", "header_fg": "#FFFFFF", "text": "#000000"
            },
            "61": {  # Ligue 1
                "bg": "#091C3E", "gradient_end": "#1C4F9C", "header_fg": "#FFFFFF", "text": "#000000"
            },
            "135": {  # Serie A
                "bg": "#008FD7", "gradient_end": "#60C8FF", "header_fg": "#FFFFFF", "text": "#000000"
            },
            "78": {  # Bundesliga
                "bg": "#D20515", "gradient_end": "#FF4D4D", "header_fg": "#FFFFFF", "text": "#000000"
            }
        }
        return league_colors.get(self.selected_league, league_colors["39"]) #defaults to premioer League 

    def get_league_logo(self):
        #simple loop that looks for our logo
        for name, info in leagues_info.items():
            if info['id'] == self.selected_league:
                return info['logo']
        return None

if __name__ == "__main__":
    root = tk.Tk()
    app = LeagueGUI(root)
    root.mainloop()